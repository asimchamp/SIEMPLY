"""
Software Package Model
Defines the software package database model for inventory management
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from sqlalchemy import Boolean, Column, Integer, String, DateTime, JSON, Text, Float
from pydantic import BaseModel, Field

from .database import Base

class PackageType(str, Enum):
    """Enumeration of possible package types"""
    SPLUNK_UF = "splunk_uf"
    SPLUNK_ENTERPRISE = "splunk_enterprise"
    CRIBL_STREAM_LEADER = "cribl_stream_leader"
    CRIBL_STREAM_WORKER = "cribl_stream_worker"
    CRIBL_EDGE = "cribl_edge"

class PackageStatus(str, Enum):
    """Enumeration of possible package statuses"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    BETA = "beta"
    ARCHIVED = "archived"

# Pydantic model for download entries
class DownloadEntry(BaseModel):
    """Download entry for different architectures"""
    architecture: str = "x86_64"  # x86_64, arm64, aarch64, etc.
    download_url: str
    file_size: Optional[float] = None  # Size in MB
    checksum: Optional[str] = None  # SHA256 checksum
    os_compatibility: List[str] = ["linux"]  # ["linux", "windows", "macos"]
    
class SoftwarePackage(Base):
    """Software package database model"""
    __tablename__ = "software_packages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    package_type = Column(String, index=True)
    version = Column(String, index=True)
    description = Column(Text, nullable=True)
    vendor = Column(String, default="Splunk Inc.")  # Splunk Inc. or Cribl Inc.
    
    # Multiple download entries for different architectures
    downloads = Column(JSON, default=list)  # List of DownloadEntry objects
    
    # Legacy fields for backward compatibility (will be migrated to downloads)
    download_url = Column(String, nullable=True)
    file_size = Column(Float, nullable=True)  # Size in MB
    checksum = Column(String, nullable=True)  # SHA256 checksum
    architecture = Column(String, default="x86_64")  # x86_64, arm64, etc.
    os_compatibility = Column(JSON, default=["linux"])  # ["linux", "windows", "macos"]
    
    # Installation details
    install_command = Column(Text, nullable=True)
    default_install_dir = Column(String, default="/opt")
    default_user = Column(String, default="splunk")
    default_group = Column(String, default="splunk")
    
    # Configuration
    default_ports = Column(JSON, nullable=True)  # {"web": 8000, "management": 8089}
    min_requirements = Column(JSON, nullable=True)  # {"ram": 4096, "disk": 20480}
    installation_notes = Column(Text, nullable=True)
    
    # Status and metadata
    status = Column(String, default="active")
    is_default = Column(Boolean, default=False)  # Mark as default version for type
    release_date = Column(DateTime, nullable=True)
    support_end_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic models for API
class PackageBase(BaseModel):
    """Base Package schema with common attributes"""
    name: str
    package_type: str
    version: str
    description: Optional[str] = None
    vendor: str = "Splunk Inc."
    downloads: List[DownloadEntry] = []
    
    # Legacy fields for backward compatibility
    download_url: Optional[str] = None
    file_size: Optional[float] = None
    checksum: Optional[str] = None
    architecture: str = "x86_64"
    os_compatibility: List[str] = ["linux"]
    
    install_command: Optional[str] = None
    default_install_dir: str = "/opt"
    default_user: str = "splunk"
    default_group: str = "splunk"
    default_ports: Optional[Dict[str, Any]] = None
    min_requirements: Optional[Dict[str, Any]] = None
    installation_notes: Optional[str] = None
    status: str = "active"
    is_default: bool = False
    release_date: Optional[datetime] = None
    support_end_date: Optional[datetime] = None

class PackageCreate(BaseModel):
    """Schema for creating a new package"""
    name: str
    package_type: str
    version: str
    description: Optional[str] = None
    vendor: str = "Splunk Inc."
    downloads: List[DownloadEntry] = []
    install_command: Optional[str] = None
    default_install_dir: str = "/opt"
    default_user: str = "splunk"
    default_group: str = "splunk"
    default_ports: Optional[Dict[str, Any]] = None
    min_requirements: Optional[Dict[str, Any]] = None
    installation_notes: Optional[str] = None
    status: str = "active"
    is_default: bool = False
    release_date: Optional[datetime] = None
    support_end_date: Optional[datetime] = None

class PackageUpdate(BaseModel):
    """Schema for updating a package"""
    name: Optional[str] = None
    description: Optional[str] = None
    vendor: Optional[str] = None
    downloads: Optional[List[DownloadEntry]] = None
    install_command: Optional[str] = None
    default_install_dir: Optional[str] = None
    default_user: Optional[str] = None
    default_group: Optional[str] = None
    default_ports: Optional[Dict[str, Any]] = None
    min_requirements: Optional[Dict[str, Any]] = None
    installation_notes: Optional[str] = None
    status: Optional[str] = None
    is_default: Optional[bool] = None
    release_date: Optional[datetime] = None
    support_end_date: Optional[datetime] = None

class PackageResponse(BaseModel):
    """Schema for package response"""
    id: int
    name: str
    package_type: str
    version: str
    description: Optional[str] = None
    vendor: str
    downloads: List[DownloadEntry] = []
    
    # Legacy fields for backward compatibility
    download_url: Optional[str] = None
    file_size: Optional[float] = None
    checksum: Optional[str] = None
    architecture: str = "x86_64"
    os_compatibility: List[str] = ["linux"]
    
    install_command: Optional[str] = None
    default_install_dir: str
    default_user: str
    default_group: str
    default_ports: Optional[Dict[str, Any]] = None
    min_requirements: Optional[Dict[str, Any]] = None
    installation_notes: Optional[str] = None
    status: str
    is_default: bool
    release_date: Optional[datetime] = None
    support_end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 