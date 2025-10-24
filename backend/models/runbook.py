"""
Runbook Model
Defines the runbook database model and related schemas
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from .database import Base

class RunbookStatus(str, Enum):
    """Enumeration of possible runbook execution statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskStatus(str, Enum):
    """Enumeration of possible task execution statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class Runbook(Base):
    """Runbook database model"""
    __tablename__ = "runbooks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    yaml_file_path = Column(String, nullable=True)  # Path to YAML file in files system
    yaml_content = Column(Text, nullable=True)  # Cached YAML content
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    created_by = relationship("User")
    executions = relationship("RunbookExecution", back_populates="runbook")

class RunbookExecution(Base):
    """Runbook execution history model"""
    __tablename__ = "runbook_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    runbook_id = Column(Integer, ForeignKey("runbooks.id"))
    execution_id = Column(String, unique=True, index=True)  # UUID for tracking
    status = Column(String, default=RunbookStatus.PENDING.value)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    triggered_by_user_id = Column(Integer, ForeignKey("users.id"))
    parameters = Column(JSON, nullable=True)  # Execution parameters
    results = Column(JSON, nullable=True)  # Execution results
    error_message = Column(Text, nullable=True)
    
    # Relationships
    runbook = relationship("Runbook", back_populates="executions")
    triggered_by = relationship("User")
    tasks = relationship("RunbookTaskExecution", back_populates="execution")

class RunbookTaskExecution(Base):
    """Individual task execution within a runbook"""
    __tablename__ = "runbook_task_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("runbook_executions.id"))
    job_id = Column(String, nullable=True)  # Reference to job if created
    task_name = Column(String)
    task_type = Column(String)  # service, command, script, etc.
    target_hosts = Column(JSON, nullable=True)  # List of host IDs or server class
    parameters = Column(JSON, nullable=True)
    status = Column(String, default=TaskStatus.PENDING.value)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    execution = relationship("RunbookExecution", back_populates="tasks")

# Pydantic models for API
class RunbookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    yaml_file_path: Optional[str] = None
    yaml_content: Optional[str] = None

class RunbookUpdate(BaseModel):
    description: Optional[str] = None
    yaml_file_path: Optional[str] = None
    yaml_content: Optional[str] = None
    is_active: Optional[bool] = None

class RunbookResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    yaml_file_path: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    
    class Config:
        from_attributes = True

class RunbookExecutionCreate(BaseModel):
    runbook_id: int
    parameters: Optional[Dict[str, Any]] = None

class RunbookExecutionResponse(BaseModel):
    id: int
    runbook_id: int
    execution_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    triggered_by_user_id: int
    parameters: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

class RunbookTaskExecutionResponse(BaseModel):
    id: int
    execution_id: int
    job_id: Optional[str]
    task_name: str
    task_type: str
    target_hosts: Optional[List[int]]
    parameters: Optional[Dict[str, Any]]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True 