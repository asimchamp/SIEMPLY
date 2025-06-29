"""
Splunk API Router
Handles Splunk installation and management operations
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.models import get_db, Host
from backend.installers.splunk import install_splunk_universal_forwarder
import logging

router = APIRouter(
    prefix="/splunk",
    tags=["splunk"],
    responses={404: {"description": "Host not found"}},
)

logger = logging.getLogger(__name__)

class SplunkUFInstallParams(BaseModel):
    """Parameters for Splunk UF installation"""
    version: str
    install_dir: str = "/opt"
    admin_password: str
    user: str = "splunk"
    group: str = "splunk"
    deployment_server: Optional[str] = None
    deployment_app: Optional[str] = None
    is_dry_run: bool = False

@router.post("/{host_id}/install-uf", response_model=Dict[str, Any])
async def install_uf(
    host_id: int, 
    params: SplunkUFInstallParams,
    db: Session = Depends(get_db)
):
    """
    Install Splunk Universal Forwarder directly on a host
    
    This endpoint installs Splunk UF directly via SSH without creating a job
    """
    # Get host
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Convert params to dictionary
        parameters = params.dict()
        
        # Install Splunk UF
        result = await install_splunk_universal_forwarder(host, parameters)
        
        # If installation was successful, update host in database
        if result.get("success") and not params.is_dry_run:
            current_roles = host.roles or []
            if "splunk_uf" not in current_roles:
                current_roles.append("splunk_uf")
                host.roles = current_roles
                db.commit()
        
        return result
    except Exception as e:
        logger.error(f"Error installing Splunk UF on host {host.hostname}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to install Splunk UF: {str(e)}"
        ) 