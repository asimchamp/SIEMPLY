"""
Host Inventory Model
Defines the host database model and related schemas
"""
from datetime import datetime
from typing import List, Optional
from enum import Enum
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, IPvAnyAddress

from .database import Base

class HostRole(str, Enum):
    """Enumeration of possible host roles"""
    SPLUNK_UF = "splunk_uf"
    SPLUNK_ENTERPRISE = "splunk_enterprise"
    CRIBL_WORKER = "cribl_worker"
    CRIBL_LEADER = "cribl_leader"
    LINUX_HOST = "linux_host"
    WINDOWS_HOST = "windows_host"
    OTHER = "other"

class Host(Base):
    """Host inventory database model"""
    __tablename__ = "hosts"
    
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, index=True)
    ip_address = Column(String, index=True)
    port = Column(Integer, default=22)
    username = Column(String)
    password = Column(String, nullable=True)  # Optional, prefer SSH keys
    ssh_key_path = Column(String, nullable=True)
    roles = Column(JSON, default=list)  # Store list of roles
    os_type = Column(String, default="linux")
    os_version = Column(String, nullable=True)
    status = Column(String, default="unknown")  # unknown, online, offline, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    jobs = relationship("Job", back_populates="host")
    
# Pydantic models for API
class HostBase(BaseModel):
    """Base Host schema with common attributes"""
    hostname: str
    ip_address: str
    port: int = 22
    username: str
    roles: List[str] = []
    os_type: str = "linux"
    os_version: Optional[str] = None

class HostCreate(HostBase):
    """Schema for creating a host"""
    password: Optional[str] = None
    ssh_key_path: Optional[str] = None

class HostUpdate(BaseModel):
    """Schema for updating a host"""
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key_path: Optional[str] = None
    roles: Optional[List[str]] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

class HostResponse(HostBase):
    """Schema for host response"""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    model_config = {"from_attributes": True} 