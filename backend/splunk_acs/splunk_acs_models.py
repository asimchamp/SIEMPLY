"""
Splunk ACS Data Models
Database models for Splunk Cloud configuration management
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.models.database import Base


class SplunkCloudConfig(Base):
    """Splunk Cloud configuration storage"""
    __tablename__ = "splunk_cloud_configs"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    stack_id = Column(String(100), nullable=False)
    auth_token = Column(String(500), nullable=False)  # Encrypted
    region = Column(String(50), nullable=False)
    environment = Column(String(20), default="prod")  # prod, dev, staging
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    change_requests = relationship("ChangeRequest", back_populates="config")
    operations = relationship("ACSOperation", back_populates="config")


class ACSOperation(Base):
    """Audit trail for ACS operations"""
    __tablename__ = "acs_operations"
    
    id = Column(Integer, primary_key=True)
    operation_type = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    configuration = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    config_id = Column(Integer, ForeignKey("splunk_cloud_configs.id"))
    status = Column(String(20), default="pending")  # pending, success, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    config = relationship("SplunkCloudConfig", back_populates="operations")


class ChangeRequest(Base):
    """Change request workflow management"""
    __tablename__ = "change_requests"
    
    id = Column(Integer, primary_key=True)
    request_id = Column(String(50), unique=True, index=True)  # CR-2024-001
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    change_type = Column(String(50), nullable=False)  # configuration, emergency, scheduled
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(String(20), default="draft")  # draft, pending, approved, implemented
    requester_id = Column(Integer, ForeignKey("users.id"))
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    config_id = Column(Integer, ForeignKey("splunk_cloud_configs.id"))
    resource_type = Column(String(100), nullable=False)  # ip_allow_list, index, app, etc.
    resource_id = Column(String(100), nullable=True)
    proposed_changes = Column(JSON, nullable=False)
    risk_assessment = Column(String(20), default="low")  # low, medium, high
    implementation_plan = Column(Text, nullable=True)
    rollback_plan = Column(Text, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    implemented_at = Column(DateTime, nullable=True)

    # Relationships
    config = relationship("SplunkCloudConfig", back_populates="change_requests")
    approval_workflows = relationship("ApprovalWorkflow", back_populates="change_request")
    versions = relationship("ConfigurationVersion", back_populates="change_request")


class ConfigurationVersion(Base):
    """Version control for configuration changes"""
    __tablename__ = "configuration_versions"
    
    id = Column(Integer, primary_key=True)
    version_id = Column(String(50), unique=True, index=True)  # v1.0.0
    change_request_id = Column(Integer, ForeignKey("change_requests.id"))
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=False)
    previous_config = Column(JSON, nullable=True)  # Previous configuration
    new_config = Column(JSON, nullable=False)     # New configuration
    diff_summary = Column(Text, nullable=True)    # Human-readable change summary
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    can_rollback = Column(Boolean, default=True)

    # Relationships
    change_request = relationship("ChangeRequest", back_populates="versions")


class ApprovalWorkflow(Base):
    """Multi-level approval workflow"""
    __tablename__ = "approval_workflows"
    
    id = Column(Integer, primary_key=True)
    change_request_id = Column(Integer, ForeignKey("change_requests.id"))
    level = Column(Integer, nullable=False)  # 1, 2, 3 (User, Team Lead, Admin)
    approver_role = Column(String(50), nullable=False)  # team_lead, admin, security_team
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    comments = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    change_request = relationship("ChangeRequest", back_populates="approval_workflows")


# Pydantic models for API requests/responses
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class SplunkCloudConfigCreate(BaseModel):
    """Create Splunk Cloud configuration"""
    name: str = Field(..., min_length=1, max_length=100)
    stack_id: str = Field(..., min_length=1, max_length=100)
    auth_token: str = Field(..., min_length=1, max_length=500)
    region: str = Field(..., min_length=1, max_length=50)
    environment: str = Field(default="prod", pattern="^(prod|dev|staging)$")


class SplunkCloudConfigUpdate(BaseModel):
    """Update Splunk Cloud configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    stack_id: Optional[str] = Field(None, min_length=1, max_length=100)
    auth_token: Optional[str] = Field(None, min_length=1, max_length=500)
    region: Optional[str] = Field(None, min_length=1, max_length=50)
    environment: Optional[str] = Field(None, pattern="^(prod|dev|staging)$")
    is_active: Optional[bool] = None


class SplunkCloudConfigResponse(BaseModel):
    """Splunk Cloud configuration response"""
    id: int
    name: str
    stack_id: str
    region: str
    environment: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChangeRequestCreate(BaseModel):
    """Create change request"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    change_type: str = Field(..., pattern="^(configuration|emergency|scheduled)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    resource_type: str = Field(..., min_length=1, max_length=100)
    resource_id: Optional[str] = None
    proposed_changes: Dict[str, Any] = Field(...)
    risk_assessment: str = Field(default="low", pattern="^(low|medium|high)$")
    implementation_plan: Optional[str] = None
    rollback_plan: Optional[str] = None
    scheduled_date: Optional[datetime] = None


class ChangeRequestUpdate(BaseModel):
    """Update change request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    change_type: Optional[str] = Field(None, pattern="^(configuration|emergency|scheduled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    resource_type: Optional[str] = Field(None, min_length=1, max_length=100)
    resource_id: Optional[str] = None
    proposed_changes: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    implementation_plan: Optional[str] = None
    rollback_plan: Optional[str] = None
    scheduled_date: Optional[datetime] = None


class ChangeRequestResponse(BaseModel):
    """Change request response"""
    id: int
    request_id: str
    title: str
    description: Optional[str]
    change_type: str
    priority: str
    status: str
    requester_id: int
    approver_id: Optional[int]
    resource_type: str
    resource_id: Optional[str]
    proposed_changes: Dict[str, Any]
    risk_assessment: str
    implementation_plan: Optional[str]
    rollback_plan: Optional[str]
    scheduled_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime]
    implemented_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConfigurationVersionResponse(BaseModel):
    """Configuration version response"""
    id: int
    version_id: str
    change_request_id: int
    resource_type: str
    resource_id: str
    previous_config: Optional[Dict[str, Any]]
    new_config: Dict[str, Any]
    diff_summary: Optional[str]
    created_by: int
    created_at: datetime
    is_active: bool
    can_rollback: bool

    class Config:
        from_attributes = True


class ApprovalWorkflowResponse(BaseModel):
    """Approval workflow response"""
    id: int
    change_request_id: int
    level: int
    approver_role: str
    approver_id: Optional[int]
    status: str
    comments: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
