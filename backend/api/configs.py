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
from backend.automation.ssh_client import SshClient

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
        ssh_client = SshClient(
            host.ip_address,
            host.port,
            host.username,
            password=host.password,
            key_filename=host.ssh_key_path,
        )
        
        # Process each uploaded file
        for file in files:
            try:
                # Save file to temp directory
                file_path = os.path.join(temp_dir, file.filename)
                contents = await file.read()
                with open(file_path, "wb") as f:
                    f.write(contents)
                
                # Create target directory if it doesn't exist
                ssh_client.exec_command(f"mkdir -p {target_dir}")
                
                # Copy file to host
                remote_path = f"{target_dir}/{file.filename}"
                ssh_client.upload_file(file_path, remote_path)
                
                # Set permissions
                ssh_client.exec_command(f"chmod 644 {remote_path}")
                
                # If we're pushing to Splunk, restart splunk if file is not a .conf.example
                if "splunk" in target_dir and not file.filename.endswith(".conf.example"):
                    restart_cmd = "sudo -u splunk /opt/splunk/bin/splunk restart"
                    try:
                        ssh_client.exec_command(restart_cmd, timeout=60)
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
        ssh_client = SshClient(
            host.ip_address,
            host.port,
            host.username,
            password=host.password,
            key_filename=host.ssh_key_path,
        )
        
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
                ssh_client.exec_command(f"mkdir -p {target_dir}")
                
                # Copy file to host
                remote_path = f"{target_dir}/{file.filename}"
                ssh_client.upload_file(file_path, remote_path)
                
                # Set permissions
                ssh_client.exec_command(f"chmod 644 {remote_path}")
                
                # Restart Cribl service
                restart_cmd = "systemctl restart cribl"
                try:
                    ssh_client.exec_command(restart_cmd, timeout=60)
                except Exception as e:
                    results.append({
                        "filename": file.filename,
                        "status": "warning", 
                        "message": f"File uploaded but Cribl service restart failed: {str(e)}",
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