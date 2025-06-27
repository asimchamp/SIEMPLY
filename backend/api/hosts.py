"""
Host API Router
Handles all host management operations including tagging with roles
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.models import get_db, Host, HostCreate, HostUpdate, HostResponse, HostRole
from backend.automation.utils import validate_ssh_connection
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