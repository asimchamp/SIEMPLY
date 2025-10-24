"""
Server Class API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
import logging

from backend.services.serverclass_service import ServerClassService
from backend.api.auth import get_current_user
from backend.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/serverclass", tags=["serverclass"])

# Pydantic models for request/response
class CreateServerClassRequest(BaseModel):
    name: str
    description: str
    host_ids: List[int]
    tags: List[str] = []
    is_active: bool = True

class UpdateServerClassRequest(BaseModel):
    description: str = None
    host_ids: List[int] = None
    tags: List[str] = None
    is_active: bool = None

class ServerClassResponse(BaseModel):
    id: str
    name: str
    description: str
    host_ids: List[int]
    hostnames: List[str]
    host_count: int
    tags: List[str]
    is_active: bool
    created_by: str
    created_at: str
    updated_at: str

@router.post("/", response_model=ServerClassResponse)
async def create_server_class(
    request: CreateServerClassRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new server class
    """
    try:
        service = ServerClassService()
        
        # Validate server class name
        if not service.validate_server_class_name(request.name):
            raise HTTPException(
                status_code=400, 
                detail="Invalid server class name. Name cannot contain spaces, brackets, or equals signs."
            )
        
        # Create server class
        server_class = service.create_server_class(
            name=request.name,
            description=request.description,
            host_ids=request.host_ids,
            tags=request.tags,
            is_active=request.is_active,
            created_by=current_user.username
        )
        
        logger.info(f"User {current_user.username} created server class '{request.name}'")
        return ServerClassResponse(**server_class)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating server class: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[ServerClassResponse])
async def get_all_server_classes(
    current_user: User = Depends(get_current_user)
):
    """
    Get all server classes
    """
    try:
        service = ServerClassService()
        server_classes = service.get_all_server_classes()
        
        return [ServerClassResponse(**sc) for sc in server_classes]
        
    except Exception as e:
        logger.error(f"Error getting server classes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{name}", response_model=ServerClassResponse)
async def get_server_class(
    name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get server class by name
    """
    try:
        service = ServerClassService()
        server_class = service.get_server_class(name)
        
        if not server_class:
            raise HTTPException(status_code=404, detail="Server class not found")
        
        return ServerClassResponse(**server_class)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting server class '{name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{name}", response_model=ServerClassResponse)
async def update_server_class(
    name: str,
    request: UpdateServerClassRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update server class
    """
    try:
        service = ServerClassService()
        
        # Prepare update data
        update_data = {}
        if request.description is not None:
            update_data["description"] = request.description
        if request.host_ids is not None:
            update_data["host_ids"] = request.host_ids
        if request.tags is not None:
            update_data["tags"] = request.tags
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        
        # Update server class
        server_class = service.update_server_class(name, **update_data)
        
        logger.info(f"User {current_user} updated server class '{name}'")
        return ServerClassResponse(**server_class)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating server class '{name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{name}")
async def delete_server_class(
    name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete server class
    """
    try:
        service = ServerClassService()
        success = service.delete_server_class(name)
        
        if success:
            logger.info(f"User {current_user} deleted server class '{name}'")
            return {"message": f"Server class '{name}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Server class not found")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting server class '{name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/config/content")
async def get_serverclass_conf_content(
    current_user: User = Depends(get_current_user)
):
    """
    Get the content of serverclass.conf file
    """
    try:
        service = ServerClassService()
        content = service.get_serverclass_conf_content()
        
        return {
            "content": content,
            "filename": "serverclass.conf"
        }
        
    except Exception as e:
        logger.error(f"Error getting serverclass.conf content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/validate-name")
async def validate_server_class_name(
    name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Validate server class name
    """
    try:
        service = ServerClassService()
        is_valid = service.validate_server_class_name(name)
        
        return {
            "name": name,
            "is_valid": is_valid
        }
        
    except Exception as e:
        logger.error(f"Error validating server class name: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 