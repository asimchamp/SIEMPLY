#!/usr/bin/env python3
"""
Execution Models
Database models for tracking playbook executions
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class PlaybookExecution(Base):
    """Model for tracking playbook executions"""
    __tablename__ = "playbook_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(255), unique=True, index=True, nullable=False)
    playbook_id = Column(String(500), nullable=False)
    playbook_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="queued")  # queued, running, completed, failed, cancelled
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    total_jobs = Column(Integer, default=0)
    completed_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_log = Column(JSON, nullable=True)  # Detailed execution log
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    job_executions = relationship("JobExecution", back_populates="playbook_execution", cascade="all, delete-orphan")

class JobExecution(Base):
    """Model for tracking individual job executions within a playbook"""
    __tablename__ = "playbook_job_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(255), ForeignKey("playbook_executions.execution_id"), nullable=False)
    job_id = Column(String(255), nullable=False)
    job_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed, skipped
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    target_hosts = Column(JSON, nullable=True)  # List of target hosts
    completed_hosts = Column(Integer, default=0)
    failed_hosts = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_log = Column(JSON, nullable=True)  # Detailed job execution log
    
    # Relationships
    playbook_execution = relationship("PlaybookExecution", back_populates="job_executions")
    task_executions = relationship("PlaybookTaskExecution", back_populates="job_execution", cascade="all, delete-orphan")

class PlaybookTaskExecution(Base):
    """Model for tracking individual task executions within a job"""
    __tablename__ = "playbook_task_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_execution_id = Column(Integer, ForeignKey("playbook_job_executions.id"), nullable=False)
    task_name = Column(String(255), nullable=False)
    module = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed, skipped
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    host = Column(String(255), nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    return_code = Column(Integer, nullable=True)
    changed = Column(Boolean, default=False)  # Whether the task made changes
    error_message = Column(Text, nullable=True)
    
    # Relationships
    job_execution = relationship("JobExecution", back_populates="task_executions") 