"""
SSH API Router
Handles SSH key management operations
"""
import os
import subprocess
import logging
import time
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.config.settings import settings
from backend.api.auth import get_current_active_user
from backend.models import User

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ssh",
    tags=["ssh"],
    responses={404: {"description": "SSH key not found"}},
)

# Pydantic models
class SSHKeyGenerateRequest(BaseModel):
    type: str = "rsa"
    bits: int = 4096
    password: str = ""

class SSHKeyResponse(BaseModel):
    exists: bool
    public_key: str = ""
    private_key_path: str = ""
    message: str = ""

@router.get("/check-key", response_model=SSHKeyResponse)
async def check_ssh_key(current_user: User = Depends(get_current_active_user)):
    """
    Check if SSH key pair exists
    """
    try:
        # Get SSH key paths
        ssh_dir = Path.home() / ".ssh"
        private_key_path = ssh_dir / "id_rsa"
        public_key_path = ssh_dir / "id_rsa.pub"
        
        # Check if both files exist
        if private_key_path.exists() and public_key_path.exists():
            # Read public key
            try:
                with open(public_key_path, 'r') as f:
                    public_key = f.read().strip()
                
                logger.info(f"SSH key found for user {current_user.username}")
                return SSHKeyResponse(
                    exists=True,
                    public_key=public_key,
                    private_key_path=str(private_key_path),
                    message="SSH key pair found"
                )
            except Exception as e:
                logger.error(f"Error reading public key: {e}")
                return SSHKeyResponse(
                    exists=False,
                    message=f"Error reading public key: {str(e)}"
                )
        else:
            logger.info(f"No SSH key found for user {current_user.username}")
            return SSHKeyResponse(
                exists=False,
                message="No SSH key pair found"
            )
            
    except Exception as e:
        logger.error(f"Error checking SSH key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check SSH key: {str(e)}"
        )

@router.post("/generate-key", response_model=SSHKeyResponse)
async def generate_ssh_key(
    request: SSHKeyGenerateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a new SSH key pair
    """
    try:
        # Get SSH directory
        ssh_dir = Path.home() / ".ssh"
        private_key_path = ssh_dir / "id_rsa"
        public_key_path = ssh_dir / "id_rsa.pub"
        
        # Create .ssh directory if it doesn't exist
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        # Check if key already exists
        if private_key_path.exists() or public_key_path.exists():
            # Backup existing keys
            backup_dir = ssh_dir / "backup"
            backup_dir.mkdir(exist_ok=True)
            
            if private_key_path.exists():
                backup_private = backup_dir / f"id_rsa.backup.{int(time.time())}"
                private_key_path.rename(backup_private)
                logger.info(f"Backed up existing private key to {backup_private}")
            
            if public_key_path.exists():
                backup_public = backup_dir / f"id_rsa.pub.backup.{int(time.time())}"
                public_key_path.rename(backup_public)
                logger.info(f"Backed up existing public key to {backup_public}")
        
        # Generate SSH key using ssh-keygen
        cmd = [
            "ssh-keygen",
            "-t", request.type,
            "-b", str(request.bits),
            "-f", str(private_key_path),
            "-N", request.password  # Empty string for no passphrase
        ]
        
        logger.info(f"Generating SSH key with command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(ssh_dir)
        )
        
        if result.returncode != 0:
            logger.error(f"SSH key generation failed: {result.stderr}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate SSH key: {result.stderr}"
            )
        
        # Set proper permissions
        os.chmod(private_key_path, 0o600)
        os.chmod(public_key_path, 0o644)
        
        # Read the generated public key
        with open(public_key_path, 'r') as f:
            public_key = f.read().strip()
        
        logger.info(f"Successfully generated SSH key for user {current_user.username}")
        
        return SSHKeyResponse(
            exists=True,
            public_key=public_key,
            private_key_path=str(private_key_path),
            message="SSH key generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error generating SSH key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SSH key: {str(e)}"
        )

@router.get("/public-key", response_model=SSHKeyResponse)
async def get_public_key(current_user: User = Depends(get_current_active_user)):
    """
    Get the current public key
    """
    try:
        public_key_path = Path.home() / ".ssh" / "id_rsa.pub"
        
        if not public_key_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Public key not found"
            )
        
        with open(public_key_path, 'r') as f:
            public_key = f.read().strip()
        
        return SSHKeyResponse(
            exists=True,
            public_key=public_key,
            message="Public key retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading public key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read public key: {str(e)}"
        )
