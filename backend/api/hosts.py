"""
Host API Router
Handles all host management operations including tagging with roles
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.models import get_db, Host, HostCreate, HostUpdate, HostResponse, HostRole
from backend.automation.utils import validate_ssh_connection
from backend.automation.system_metrics import get_system_metrics
from backend.automation.package_checker import check_host_packages, install_host_packages
from backend.automation.service_checker import check_all_services, fix_sftp_connectivity, install_syslog_ng, start_syslog_ng
import logging

router = APIRouter(
    prefix="/hosts",
    tags=["hosts"],
    responses={404: {"description": "Host not found"}},
)

logger = logging.getLogger(__name__)


@router.get("/", response_model=List[HostResponse])
async def get_hosts(
    skip: int = 0, 
    limit: int = 100, 
    role: Optional[str] = Query(None, description="Filter hosts by role"),
    status: Optional[str] = Query(None, description="Filter hosts by status"),
    db: Session = Depends(get_db)
):
    """
    Get all hosts with optional filtering by role and status
    """
    query = db.query(Host)
    
    if role:
        # Filter hosts that have the specified role in their roles JSON array
        query = query.filter(Host.roles.contains([role]))
    
    if status:
        query = query.filter(Host.status == status)
    
    hosts = query.offset(skip).limit(limit).all()
    return hosts


@router.post("/", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
async def create_host(host: HostCreate, db: Session = Depends(get_db)):
    """
    Create a new host
    """
    # Create new host from the request data
    db_host = Host(**host.dict())
    
    # Initial status is unknown until validated
    db_host.status = "unknown"
    
    db.add(db_host)
    db.commit()
    db.refresh(db_host)
    
    # Test connection immediately after creation
    try:
        # Test SSH connection
        connection_result = await validate_ssh_connection(db_host)
        
        # Update host status based on connection result
        db_host.status = "online" if connection_result["success"] else "offline"
        db.commit()
        db.refresh(db_host)
    except Exception as e:
        # Log the error but don't fail the host creation
        logger.error(f"Error testing connection to new host {db_host.hostname}: {e}")
    
    return db_host


@router.get("/{host_id}", response_model=HostResponse)
async def get_host(host_id: int, db: Session = Depends(get_db)):
    """
    Get a host by ID
    """
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    return host


@router.patch("/{host_id}", response_model=HostResponse)
async def update_host(host_id: int, host_update: HostUpdate, db: Session = Depends(get_db)):
    """
    Update a host
    """
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Update host attributes
    update_data = host_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_host, key, value)
    
    db.commit()
    db.refresh(db_host)
    return db_host


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(host_id: int, db: Session = Depends(get_db)):
    """
    Delete a host
    """
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    db.delete(db_host)
    db.commit()
    return None


@router.post("/{host_id}/roles/{role}", response_model=HostResponse)
async def add_host_role(
    host_id: int, 
    role: str, 
    db: Session = Depends(get_db)
):
    """
    Add role to a host
    """
    # Validate role
    try:
        host_role = HostRole(role)
    except ValueError:
        valid_roles = [r.value for r in HostRole]
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid role. Valid roles are: {', '.join(valid_roles)}"
        )
    
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Add role if not already present
    current_roles = db_host.roles or []
    if host_role.value not in current_roles:
        current_roles.append(host_role.value)
        db_host.roles = current_roles
        db.commit()
        db.refresh(db_host)
    
    return db_host


@router.delete("/{host_id}/roles/{role}", response_model=HostResponse)
async def remove_host_role(
    host_id: int, 
    role: str, 
    db: Session = Depends(get_db)
):
    """
    Remove role from a host
    """
    # Validate role
    try:
        host_role = HostRole(role)
    except ValueError:
        valid_roles = [r.value for r in HostRole]
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid role. Valid roles are: {', '.join(valid_roles)}"
        )
    
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Remove role if present
    current_roles = db_host.roles or []
    if host_role.value in current_roles:
        current_roles.remove(host_role.value)
        db_host.roles = current_roles
        db.commit()
        db.refresh(db_host)
    
    return db_host


@router.post("/{host_id}/test-connection", response_model=dict)
async def test_host_connection(host_id: int, db: Session = Depends(get_db)):
    """
    Test SSH connection to a host
    """
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Test connection
    connection_result = await validate_ssh_connection(db_host)
    
    # Update host status based on connection result
    db_host.status = "online" if connection_result["success"] else "offline"
    db.commit()
    
    return connection_result


@router.get("/{host_id}/system-metrics", response_model=dict)
async def get_host_system_metrics(host_id: int, db: Session = Depends(get_db)):
    """
    Get system metrics for a host (CPU, RAM, storage, etc.)
    """
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Get system metrics
        metrics = await get_system_metrics(db_host)
        return metrics
    except Exception as e:
        logger.error(f"Error getting system metrics for host {db_host.hostname}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.get("/{host_id}/packages", response_model=dict)
async def get_host_packages(host_id: int, db: Session = Depends(get_db)):
    """
    Check the status of required packages on a host
    """
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Check packages
        packages = await check_host_packages(db_host)
        
        # Convert to serializable format
        package_list = []
        for pkg in packages:
            package_list.append({
                "name": pkg.name,
                "installed": pkg.installed,
                "version": pkg.version,
                "path": pkg.path,
                "error": pkg.error
            })
        
        return {
            "host_id": host_id,
            "hostname": db_host.hostname,
            "packages": package_list
        }
    except Exception as e:
        logger.error(f"Error checking packages for host {db_host.hostname}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check packages: {str(e)}")


@router.post("/{host_id}/packages/install", response_model=dict)
async def install_host_packages_endpoint(host_id: int, db: Session = Depends(get_db)):
    """
    Install all missing packages on a host
    """
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Install packages
        result = await install_host_packages(db_host)
        return result
    except Exception as e:
        logger.error(f"Error installing packages for host {db_host.hostname}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to install packages: {str(e)}")


@router.post("/{host_id}/packages/install/{package_name}", response_model=dict)
async def install_specific_package(
    host_id: int, 
    package_name: str, 
    db: Session = Depends(get_db)
):
    """
    Install a specific package on a host
    """
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Install specific package
        result = await install_host_packages(db_host, [package_name])
        return result
    except Exception as e:
        logger.error(f"Error installing package {package_name} for host {db_host.hostname}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to install package: {str(e)}")


@router.get("/{host_id}/services", response_model=dict)
async def get_host_services(host_id: int, db: Session = Depends(get_db)):
    """
    Check the status of important services on a host
    """
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Check services
        from backend.automation.ssh_client import get_ssh_client
        async with get_ssh_client(db_host) as ssh:
            if not ssh:
                raise HTTPException(status_code=500, detail="Could not establish SSH connection")
            
            services = await check_all_services(ssh)
            
            # Convert to serializable format
            service_list = []
            for service in services:
                service_list.append({
                    "name": service.name,
                    "status": service.status,
                    "required": service.required,
                    "details": service.details
                })
            
            return {
                "host_id": host_id,
                "hostname": db_host.hostname,
                "services": service_list
            }
    except Exception as e:
        logger.error(f"Error checking services for host {db_host.hostname}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check services: {str(e)}")


@router.post("/{host_id}/services/fix-sftp", response_model=dict)
async def fix_host_sftp(host_id: int, db: Session = Depends(get_db)):
    """
    Attempt to fix SFTP connectivity issues on a host
    """
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Fix SFTP
        from backend.automation.ssh_client import get_ssh_client
        async with get_ssh_client(db_host) as ssh:
            if not ssh:
                raise HTTPException(status_code=500, detail="Could not establish SSH connection")
            
            success, message = await fix_sftp_connectivity(ssh)
            
            return {
                "host_id": host_id,
                "hostname": db_host.hostname,
                "success": success,
                "message": message
            }
    except Exception as e:
        logger.error(f"Error fixing SFTP for host {db_host.hostname}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fix SFTP: {str(e)}")


@router.post("/{host_id}/services/install-syslog-ng", response_model=dict)
async def install_host_syslog_ng(host_id: int, db: Session = Depends(get_db)):
    """
    Install syslog-ng service on a host
    """
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Install syslog-ng
        from backend.automation.ssh_client import get_ssh_client
        async with get_ssh_client(db_host) as ssh:
            if not ssh:
                raise HTTPException(status_code=500, detail="Could not establish SSH connection")
            
            success, message = await install_syslog_ng(ssh)
            
            return {
                "host_id": host_id,
                "hostname": db_host.hostname,
                "success": success,
                "message": message
            }
    except Exception as e:
        logger.error(f"Error installing syslog-ng for host {db_host.hostname}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to install syslog-ng: {str(e)}")


@router.post("/{host_id}/services/start-syslog-ng", response_model=dict)
async def start_host_syslog_ng(host_id: int, db: Session = Depends(get_db)):
    """
    Start syslog-ng service on a host
    """
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Start syslog-ng
        from backend.automation.ssh_client import get_ssh_client
        async with get_ssh_client(db_host) as ssh:
            if not ssh:
                raise HTTPException(status_code=500, detail="Could not establish SSH connection")
            
            success, message = await start_syslog_ng(ssh)
            
            return {
                "host_id": host_id,
                "hostname": db_host.hostname,
                "success": success,
                "message": message
            }
    except Exception as e:
        logger.error(f"Error starting syslog-ng for host {db_host.hostname}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start syslog-ng: {str(e)}") 


@router.get("/{host_id}/services/debug", response_model=dict)
async def debug_host_services(host_id: int, db: Session = Depends(get_db)):
    """
    Debug endpoint to check services with detailed output
    """
    # Get host
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Check services with detailed logging
        from backend.automation.ssh_client import get_ssh_client
        async with get_ssh_client(db_host) as ssh:
            if not ssh:
                raise HTTPException(status_code=500, detail="Could not establish SSH connection")
            
            # Test basic SSH connectivity first
            ssh_test = await ssh.run("echo 'SSH_TEST_SUCCESS'")
            ssh_status = "working" if "SSH_TEST_SUCCESS" in ssh_test.stdout else "failed"
            
            # Check services
            services = await check_all_services(ssh)
            
            # Convert to serializable format
            service_list = []
            for service in services:
                service_list.append({
                    "name": service.name,
                    "status": service.status,
                    "required": service.required,
                    "details": service.details
                })
            
            return {
                "host_id": host_id,
                "hostname": db_host.hostname,
                "ssh_status": ssh_status,
                "ssh_test_output": ssh_test.stdout.strip(),
                "services": service_list,
                "debug_info": {
                    "os_info": await ssh.run("cat /etc/os-release 2>/dev/null || echo 'OS_INFO_NOT_AVAILABLE'"),
                    "ssh_config": await ssh.run("grep -i 'Subsystem sftp' /etc/ssh/sshd_config 2>/dev/null || echo 'SFTP_CONFIG_NOT_FOUND'"),
                    "sshd_status": await ssh.run("systemctl is-active sshd 2>/dev/null || systemctl is-active ssh 2>/dev/null || service sshd status 2>/dev/null || service ssh status 2>/dev/null || echo 'SSHD_STATUS_UNKNOWN'")
                }
            }
    except Exception as e:
        logger.error(f"Error debugging services for host {db_host.hostname}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to debug services: {str(e)}") 