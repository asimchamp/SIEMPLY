"""
Config Push API endpoints
"""
import os
import tempfile
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import yaml

from backend.config.settings import settings
from backend.models import User, get_db, Host
from backend.api.auth import get_current_active_user, get_current_admin_user
from backend.automation.ssh_client import SIEMplySSHClient, create_ssh_client_from_host
from backend.automation.cluster_file_manager import ClusterFileManager

router = APIRouter(
    prefix="/configs",
    tags=["configs"],
)

# Schemas
class ConfigPushItem(Dict[str, Any]):
    """Config push item model"""
    pass

class ConfigPushRequest(Dict[str, Any]):
    """Config push request model"""
    pass

class SplunkAppConfig(Dict[str, Any]):
    """Splunk app configuration model"""
    pass

# API Routes
@router.post("/push/splunk/{host_id}")
async def push_splunk_configs(
    host_id: int,
    files: List[UploadFile] = File(...),
    target_dir: str = "/opt/splunk/etc/system/local",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Push Splunk configuration files to a host
    """
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found",
        )
    
    # Verify host is active
    if not host.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot push configs to inactive host",
        )
    
    results = []
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create SSH client
        ssh_client = create_ssh_client_from_host(host)
        
        # Process each uploaded file
        for file in files:
            try:
                # Save file to temp directory
                file_path = os.path.join(temp_dir, file.filename)
                contents = await file.read()
                with open(file_path, "wb") as f:
                    f.write(contents)
                
                # Create target directory if it doesn't exist
                ssh_client.execute_command(f"mkdir -p {target_dir}")
                
                # Copy file to host using SCP (need to implement file upload)
                remote_path = f"{target_dir}/{file.filename}"
                # For now, use cat to create the file
                with open(file_path, "r") as f:
                    file_content = f.read()
                    ssh_client.execute_command(f"cat > {remote_path} << 'EOF'\n{file_content}\nEOF")
                
                # Set permissions
                ssh_client.execute_command(f"chmod 644 {remote_path}")
                
                # If we're pushing to Splunk, restart splunk if file is not a .conf.example
                if "splunk" in target_dir and not file.filename.endswith(".conf.example"):
                    restart_cmd = "sudo -u splunk /opt/splunk/bin/splunk restart"
                    try:
                        ssh_client.execute_command(restart_cmd)
                    except Exception as e:
                        results.append({
                            "filename": file.filename,
                            "status": "warning", 
                            "message": f"File uploaded but Splunk restart failed: {str(e)}",
                        })
                        continue
                
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "message": f"File uploaded to {remote_path}",
                })
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"Failed to upload: {str(e)}",
                })
    
    return {"results": results}


@router.post("/splunk/apps/{host_id}")
async def deploy_splunk_app_config(
    host_id: int,
    cluster_name: str,
    component_type: str,
    target_base_dir: str = "/opt/splunk/etc/apps",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Deploy Splunk configuration as a proper app structure
    """
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found",
        )
    
    # Verify host is active
    if not host.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot push configs to inactive host",
        )
    
    try:
        # Create SSH client
        ssh_client = create_ssh_client_from_host(host)
        
        # Initialize cluster file manager
        cluster_manager = ClusterFileManager()
        
        if not cluster_manager.validate_cluster_exists(cluster_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cluster {cluster_name} not found",
            )
        
        # Use the new direct copy method that avoids EOF and copies entire directory structure
        logger.info(f"Using direct directory copy method for {component_type} configuration")
        copy_result = await cluster_manager.copy_component_configs_direct(
            ssh_client, cluster_name, component_type, target_base_dir, host.ip_address
        )
        
        if not copy_result["success"]:
            logger.warning(f"Direct copy method failed: {copy_result['message']}")
            # Fall back to legacy SCP method
            copy_result = await cluster_manager.copy_component_configs_via_scp(
                ssh_client, cluster_name, component_type, target_base_dir
            )
            
            if not copy_result["success"]:
                # Fall back to individual file copy as last resort
                copy_result = await cluster_manager.copy_component_configs_to_host(
                    ssh_client, cluster_name, component_type, target_base_dir
                )
        
        if copy_result["success"]:
            # Restart Splunk to pick up new configuration
            restart_cmd = "sudo -u splunk /opt/splunk/bin/splunk restart"
            try:
                ssh_client.execute_command(restart_cmd)
                copy_result["splunk_restarted"] = True
            except Exception as e:
                copy_result["splunk_restart_warning"] = f"Splunk restart failed: {str(e)}"
        
        return copy_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy Splunk app config: {str(e)}",
        )


@router.get("/splunk/apps/{host_id}")
async def list_splunk_apps(
    host_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List all Splunk configuration apps on a host
    """
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found",
        )
    
    try:
        # Create SSH client
        ssh_client = create_ssh_client_from_host(host)
        
        # List apps directory
        apps_dir = "/opt/splunk/etc/apps"
        list_cmd = f"ls -la {apps_dir}"
        result = ssh_client.execute_command(list_cmd)
        
        if result.return_code != 0:
            return {"apps": [], "error": f"Failed to list apps: {result.stderr}"}
        
        # Parse the output to get app names
        lines = result.stdout.strip().split('\n')
        apps = []
        
        for line in lines[2:]:  # Skip header lines
            if line.strip() and not line.startswith('total'):
                parts = line.split()
                if len(parts) >= 9:
                    app_name = parts[-1]
                    if app_name not in ['.', '..']:
                        # Get app details
                        app_path = f"{apps_dir}/{app_name}"
                        app_conf_path = f"{app_path}/default/app.conf"
                        
                        # Check if it's a SIEMply app
                        is_siemply = app_name.startswith('siemply_')
                        
                        apps.append({
                            "name": app_name,
                            "path": app_path,
                            "is_siemply": is_siemply,
                            "has_app_conf": ssh_client.execute_command(f"test -f {app_conf_path}").return_code == 0
                        })
        
        return {"apps": apps}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list Splunk apps: {str(e)}",
        )


@router.delete("/splunk/apps/{host_id}/{app_name}")
async def remove_splunk_app(
    host_id: int,
    app_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Remove a Splunk configuration app from a host
    """
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found",
        )
    
    try:
        # Create SSH client
        ssh_client = create_ssh_client_from_host(host)
        
        # Remove the app directory
        app_path = f"/opt/splunk/etc/apps/{app_name}"
        remove_cmd = f"sudo rm -rf {app_path}"
        result = ssh_client.execute_command(remove_cmd)
        
        if result.return_code != 0:
            return {"success": False, "error": f"Failed to remove app: {result.stderr}"}
        
        # Restart Splunk to pick up changes
        restart_cmd = "sudo -u splunk /opt/splunk/bin/splunk restart"
        try:
            ssh_client.execute_command(restart_cmd)
            restart_success = True
        except Exception as e:
            restart_success = False
            restart_error = str(e)
        
        return {
            "success": True,
            "message": f"App {app_name} removed successfully",
            "splunk_restarted": restart_success,
            "restart_error": restart_error if not restart_success else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove Splunk app: {str(e)}",
        )


@router.post("/push/cribl/{host_id}")
async def push_cribl_configs(
    host_id: int,
    files: List[UploadFile] = File(...),
    target_dir: str = "/opt/cribl/local",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Push Cribl configuration files to a host
    """
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found",
        )
    
    # Verify host is active
    if not host.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot push configs to inactive host",
        )
    
    # Verify host has cribl role
    if not any(role in host.roles for role in ["cribl_worker", "cribl_leader"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target host must have a Cribl role",
        )
    
    results = []
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create SSH client
        ssh_client = create_ssh_client_from_host(host)
        
        # Process each uploaded file
        for file in files:
            try:
                # Save file to temp directory
                file_path = os.path.join(temp_dir, file.filename)
                contents = await file.read()
                with open(file_path, "wb") as f:
                    f.write(contents)
                
                # Validate YAML files
                if file.filename.endswith((".yml", ".yaml")):
                    try:
                        yaml.safe_load(contents)
                    except yaml.YAMLError:
                        results.append({
                            "filename": file.filename,
                            "status": "error",
                            "message": "Invalid YAML file",
                        })
                        continue
                
                # Create target directory if it doesn't exist
                ssh_client.execute_command(f"mkdir -p {target_dir}")
                
                # Copy file to host using the execute_command method
                remote_path = f"{target_dir}/{file.filename}"
                # For now, use cat to create the file
                with open(file_path, "r") as f:
                    file_content = f.read()
                    ssh_client.execute_command(f"cat > {remote_path} << 'EOF'\n{file_content}\nEOF")
                
                # Set permissions
                ssh_client.execute_command(f"chmod 644 {remote_path}")
                
                # Restart Cribl service
                restart_cmd = "systemctl restart cribl"
                try:
                    ssh_client.execute_command(restart_cmd)
                    results.append({
                        "filename": file.filename,
                        "status": "success",
                        "message": f"File uploaded to {remote_path} and Cribl restarted",
                    })
                except Exception as e:
                    results.append({
                        "filename": file.filename,
                        "status": "warning",
                        "message": f"File uploaded but Cribl restart failed: {str(e)}",
                    })
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"Failed to upload: {str(e)}",
                })
    
    return {"results": results} 