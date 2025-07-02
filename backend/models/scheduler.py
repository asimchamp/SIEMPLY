"""
Scheduler models for task scheduling
"""
from enum import Enum
from typing import Dict, Any, Optional, List
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .database import Base


class ScheduleType(str, Enum):
    """Schedule type enum"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"
    ONE_TIME = "one_time"


class TaskType(str, Enum):
    """Task type enum"""
    INSTALL_CHECK = "install_check"
    STATUS_CHECK = "status_check"
    CONFIG_PUSH = "config_push"
    RESTART_SERVICE = "restart_service"
    CUSTOM_COMMAND = "custom_command"


class ScheduledTask(Base):
    """Scheduled task model"""
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    task_type = Column(String(50), nullable=False)
    schedule_type = Column(String(50), nullable=False)
    
    # Schedule parameters
    cron_expression = Column(String(100))
    day_of_week = Column(Integer)  # 0-6 (Monday-Sunday)
    day_of_month = Column(Integer)  # 1-31
    hour = Column(Integer)  # 0-23
    minute = Column(Integer)  # 0-59
    
    # Task parameters
    parameters = Column(JSON, nullable=False, default={})
    
    # Host relations
    host_ids = Column(JSON, nullable=False, default=[])  # List of host IDs
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    last_status = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # User who created the task
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "schedule_type": self.schedule_type,
            "cron_expression": self.cron_expression,
            "day_of_week": self.day_of_week,
            "day_of_month": self.day_of_month,
            "hour": self.hour,
            "minute": self.minute,
            "parameters": self.parameters,
            "host_ids": self.host_ids,
            "is_active": self.is_active,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "last_status": self.last_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by_user_id": self.created_by_user_id,
        }


class TaskExecution(Base):
    """Task execution history model"""
    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id"))
    task = relationship("ScheduledTask")
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="running")  # running, success, failed
    
    # Results for each host
    results = Column(JSON, default={})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "results": self.results,
        } 