"""
Splunk API Router
Handles Splunk installation and management operations
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator

from backend.models import get_db, Host
from backend.automation.splunk_installer import install_splunk_uf, repair_splunk_permissions
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
    architecture: str = "x86_64"
    install_dir: str = "/opt"
    admin_password: str
    user: str = "splunk"
    group: str = "splunk"
    deployment_server: Optional[str] = None
    deployment_app: Optional[str] = None
    is_dry_run: bool = False
    
    @validator('version')
    def version_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('version cannot be empty')
        return v
    
    @validator('admin_password')
    def password_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('admin_password cannot be empty')
        return v

class SplunkRepairParams(BaseModel):
    """Parameters for Splunk UF permission repair"""
    install_dir: str = "/opt/splunkforwarder"
    user: str = "splunk"
    group: str = "splunk"

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
        logger.error(f"Host not found: {host_id}")
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Log the parameters
        logger.info(f"Installing Splunk UF on host {host.hostname} with parameters: {params.dict()}")
        
        # Convert params to dictionary
        parameters = params.dict()
        
        # Install Splunk UF using the dedicated module
        result = await install_splunk_uf(host, parameters)
        
        # If installation was successful, update host in database
        if result.get("success") and not params.is_dry_run:
            current_roles = getattr(host, 'roles', None) or []
            if "splunk_uf" not in current_roles:
                current_roles.append("splunk_uf")
                setattr(host, 'roles', current_roles)
                db.commit()
                logger.info(f"Updated host {host.hostname} with splunk_uf role")
        
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error installing Splunk UF on host {host.hostname}: {error_msg}")
        
        # Provide more detailed error message
        if "Could not establish SSH connection" in error_msg:
            raise HTTPException(
                status_code=503, 
                detail=f"Failed to connect to host {host.hostname} via SSH. Please check SSH credentials and connectivity."
            )
        elif "version cannot be empty" in error_msg or "admin_password cannot be empty" in error_msg:
            raise HTTPException(
                status_code=422, 
                detail=f"Validation error: {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to install Splunk UF: {error_msg}"
            )

@router.post("/{host_id}/repair-permissions", response_model=Dict[str, Any])
async def repair_permissions(
    host_id: int, 
    params: SplunkRepairParams,
    db: Session = Depends(get_db)
):
    """
    Repair permission issues on an existing Splunk UF installation
    
    This endpoint fixes ownership and permission issues that may occur after installation
    """
    # Get host
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        logger.error(f"Host not found: {host_id}")
        raise HTTPException(status_code=404, detail="Host not found")
    
    try:
        # Log the parameters
        logger.info(f"Repairing Splunk UF permissions on host {host.hostname} with parameters: {params.dict()}")
        
        # Convert params to dictionary
        parameters = params.dict()
        
        # Repair Splunk UF permissions using the dedicated function
        result = await repair_splunk_permissions(host, parameters)
        
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error repairing Splunk UF permissions on host {host.hostname}: {error_msg}")
        
        # Provide more detailed error message
        if "Could not establish SSH connection" in error_msg:
            raise HTTPException(
                status_code=503, 
                detail=f"Failed to connect to host {host.hostname} via SSH. Please check SSH credentials and connectivity."
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to repair Splunk UF permissions: {error_msg}"
            ) 