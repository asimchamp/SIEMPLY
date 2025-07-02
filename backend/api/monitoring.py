"""
Monitoring API endpoints for Splunk and Cribl
"""
import json
import requests
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.settings import settings
from backend.models import User, Host, get_db
from backend.api.auth import get_current_active_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
)

# Pydantic models
class SplunkStatus(BaseModel):
    """Splunk status model"""
    host_id: int
    hostname: str
    ip_address: str
    status: str
    version: Optional[str] = None
    uptime: Optional[str] = None
    server_roles: Optional[List[str]] = None
    indexing_rate: Optional[float] = None
    license_state: Optional[str] = None
    errors: Optional[List[str]] = None

class CriblStatus(BaseModel):
    """Cribl status model"""
    host_id: int
    hostname: str
    ip_address: str
    status: str
    version: Optional[str] = None
    uptime: Optional[str] = None
    leader_status: Optional[str] = None  # For workers
    worker_count: Optional[int] = None   # For leaders
    groups: Optional[List[str]] = None
    system_info: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

# API Routes
@router.get("/splunk/{host_id}", response_model=SplunkStatus)
async def get_splunk_status(
    host_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get status of a Splunk instance"""
    # Get host
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found",
        )
    
    # Check if host has Splunk role
    if not any(role for role in host.roles if "splunk" in role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host does not have a Splunk role",
        )
    
    try:
        # Configure Splunk API endpoint
        splunk_url = f"https://{host.ip_address}:8089"
        
        # Use credentials from settings if available, otherwise use defaults
        username = settings.SPLUNK_API_USER or "admin"
        password = settings.SPLUNK_API_PASSWORD or "changeme"
        
        # Check if server is responding
        server_info_response = requests.get(
            f"{splunk_url}/services/server/info",
            auth=(username, password),
            verify=False,  # Disable SSL verification for testing
            timeout=10,
            headers={"Accept": "application/json"},
        )
        
        if server_info_response.status_code != 200:
            return SplunkStatus(
                host_id=host.id,
                hostname=host.hostname,
                ip_address=host.ip_address,
                status="error",
                errors=[f"Failed to connect to Splunk API: HTTP {server_info_response.status_code}"]
            )
        
        # Parse server info
        server_info = server_info_response.json()
        
        # Get license information
        license_response = requests.get(
            f"{splunk_url}/services/licenser/pools",
            auth=(username, password),
            verify=False,
            timeout=10,
            headers={"Accept": "application/json"},
        )
        
        license_info = {}
        if license_response.status_code == 200:
            license_info = license_response.json()
        
        # Determine server roles
        server_roles = []
        if any(role == "splunk_indexer" for role in host.roles):
            server_roles.append("indexer")
        if any(role == "splunk_search_head" for role in host.roles):
            server_roles.append("search_head")
        if any(role == "splunk_uf" for role in host.roles):
            server_roles.append("universal_forwarder")
            
        # Return status object
        return SplunkStatus(
            host_id=host.id,
            hostname=host.hostname,
            ip_address=host.ip_address,
            status="running",
            version=server_info.get("entry", [{}])[0].get("content", {}).get("version", "unknown"),
            uptime=server_info.get("entry", [{}])[0].get("content", {}).get("startup_time", "unknown"),
            server_roles=server_roles,
            license_state=license_info.get("entry", [{}])[0].get("content", {}).get("status", "unknown") 
                          if license_info else "unknown",
            indexing_rate=server_info.get("entry", [{}])[0].get("content", {}).get("average_KBps", 0)
        )
        
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        return SplunkStatus(
            host_id=host.id,
            hostname=host.hostname,
            ip_address=host.ip_address,
            status="unreachable",
            errors=[f"Connection error: {str(e)}"]
        )
    except Exception as e:
        # Handle other errors
        logger.exception(f"Error checking Splunk status: {e}")
        return SplunkStatus(
            host_id=host.id,
            hostname=host.hostname,
            ip_address=host.ip_address,
            status="error",
            errors=[f"Error: {str(e)}"]
        )

@router.get("/cribl/{host_id}", response_model=CriblStatus)
async def get_cribl_status(
    host_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get status of a Cribl instance"""
    # Get host
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found",
        )
    
    # Check if host has Cribl role
    if not any(role for role in host.roles if "cribl" in role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host does not have a Cribl role",
        )
    
    try:
        # Determine if this is a leader or worker
        is_leader = any(role == "cribl_leader" for role in host.roles)
        
        # Configure Cribl API endpoint
        cribl_url = f"http://{host.ip_address}:9000"
        
        # Get API token (preferably from settings, otherwise would need to be provided)
        api_token = settings.CRIBL_API_TOKEN
        
        if not api_token:
            return CriblStatus(
                host_id=host.id,
                hostname=host.hostname,
                ip_address=host.ip_address,
                status="error",
                errors=["No API token available for Cribl API"]
            )
        
        # Check system health
        health_response = requests.get(
            f"{cribl_url}/api/v1/system/health",
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=10
        )
        
        if health_response.status_code != 200:
            return CriblStatus(
                host_id=host.id,
                hostname=host.hostname,
                ip_address=host.ip_address,
                status="error",
                errors=[f"Failed to connect to Cribl API: HTTP {health_response.status_code}"]
            )
        
        health_info = health_response.json()
        
        # Get system info
        info_response = requests.get(
            f"{cribl_url}/api/v1/system/info",
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=10
        )
        
        info = {}
        if info_response.status_code == 200:
            info = info_response.json()
            
        # For leaders, get worker information
        worker_count = None
        if is_leader:
            workers_response = requests.get(
                f"{cribl_url}/api/v1/master/workers",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=10
            )
            
            if workers_response.status_code == 200:
                workers = workers_response.json()
                worker_count = len(workers)
        
        # For workers, get leader connection status
        leader_status = None
        if not is_leader:
            leader_status = "connected" if health_info.get("leaderConnected") else "disconnected"
            
        # Return status object
        return CriblStatus(
            host_id=host.id,
            hostname=host.hostname,
            ip_address=host.ip_address,
            status="running" if health_info.get("healthy", False) else "error",
            version=info.get("version"),
            uptime=info.get("uptime"),
            leader_status=leader_status,
            worker_count=worker_count,
            groups=info.get("groups"),
            system_info={
                "cpu": health_info.get("cpu"),
                "memory": health_info.get("memory"),
                "disk": health_info.get("disk")
            }
        )
        
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        return CriblStatus(
            host_id=host.id,
            hostname=host.hostname,
            ip_address=host.ip_address,
            status="unreachable",
            errors=[f"Connection error: {str(e)}"]
        )
    except Exception as e:
        # Handle other errors
        logger.exception(f"Error checking Cribl status: {e}")
        return CriblStatus(
            host_id=host.id,
            hostname=host.hostname,
            ip_address=host.ip_address,
            status="error",
            errors=[f"Error: {str(e)}"]
        )

@router.get("/splunk", response_model=List[SplunkStatus])
async def get_all_splunk_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get status of all Splunk instances"""
    # Find all hosts with Splunk roles
    hosts = db.query(Host).filter(
        Host.is_active == True,
        Host.roles.contains(["splunk_uf"]) | 
        Host.roles.contains(["splunk_indexer"]) | 
        Host.roles.contains(["splunk_search_head"])
    ).all()
    
    results = []
    for host in hosts:
        try:
            status = await get_splunk_status(host.id, current_user, db)
            results.append(status)
        except Exception as e:
            results.append(SplunkStatus(
                host_id=host.id,
                hostname=host.hostname,
                ip_address=host.ip_address,
                status="error",
                errors=[f"Error: {str(e)}"]
            ))
    
    return results

@router.get("/cribl", response_model=List[CriblStatus])
async def get_all_cribl_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get status of all Cribl instances"""
    # Find all hosts with Cribl roles
    hosts = db.query(Host).filter(
        Host.is_active == True,
        Host.roles.contains(["cribl_leader"]) | Host.roles.contains(["cribl_worker"])
    ).all()
    
    results = []
    for host in hosts:
        try:
            status = await get_cribl_status(host.id, current_user, db)
            results.append(status)
        except Exception as e:
            results.append(CriblStatus(
                host_id=host.id,
                hostname=host.hostname,
                ip_address=host.ip_address,
                status="error",
                errors=[f"Error: {str(e)}"]
            ))
    
    return results 