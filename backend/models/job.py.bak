"""
Job Model
Defines job database model for tracking installation and configuration operations
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from .database import Base

class JobStatus(str, Enum):
    """Enumeration of possible job statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class JobType(str, Enum):
    """Enumeration of possible job types"""
    SPLUNK_UF_INSTALL = "splunk_uf_install"
    SPLUNK_ENT_INSTALL = "splunk_enterprise_install"
    CRIBL_WORKER_INSTALL = "cribl_worker_install"
    CRIBL_LEADER_INSTALL = "cribl_leader_install"
    CONFIG_PUSH = "config_push"
    HEALTH_CHECK = "health_check"
    CUSTOM_COMMAND = "custom_command"

class Job(Base):
    """Job database model"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    
    # Job metadata
    host_id = Column(Integer, ForeignKey("hosts.id"))
    job_type = Column(String)
    status = Column(String, default="pending")
    is_dry_run = Column(Boolean, default=False)
    
    # Job parameters and results
    parameters = Column(JSON, nullable=True)  # Store job parameters as JSON
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    return_code = Column(Integer, nullable=True)
    result = Column(JSON, nullable=True)  # Store job result as JSON
    
    # Timestamps for tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    host = relationship("Host", back_populates="jobs")
    
# Pydantic models for API
class JobBase(BaseModel):
    """Base job schema"""
    host_id: int
    job_type: str
    is_dry_run: bool = False
    parameters: Optional[Dict[str, Any]] = None

class JobCreate(JobBase):
    """Schema for creating a job"""
    pass

class JobUpdate(BaseModel):
    """Schema for updating a job"""
    status: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class JobResponse(JobBase):
    """Schema for job response"""
    id: int
    job_id: str
    status: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True 