#!/usr/bin/env python3
"""
Executions API Router
Handles playbook execution tracking and management
"""
import os
import yaml
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from backend.models import get_db, PlaybookExecution, JobExecution, PlaybookTaskExecution
from backend.config.settings import settings

router = APIRouter(prefix="/executions", tags=["executions"])

# Pydantic models for API responses
class TaskExecutionResponse(BaseModel):
    id: int
    task_name: str
    module: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[int]
    host: Optional[str]
    stdout: Optional[str]
    stderr: Optional[str]
    return_code: Optional[int]
    changed: bool
    error_message: Optional[str]

    class Config:
        from_attributes = True

class JobExecutionResponse(BaseModel):
    id: int
    job_id: str
    job_name: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[int]
    target_hosts: Optional[List[str]]
    completed_hosts: int
    failed_hosts: int
    error_message: Optional[str]
    task_executions: List[TaskExecutionResponse] = []

    class Config:
        from_attributes = True

class PlaybookExecutionResponse(BaseModel):
    id: int
    execution_id: str
    playbook_id: str
    playbook_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration: Optional[int]
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    error_message: Optional[str]
    created_by: Optional[str]
    job_executions: List[JobExecutionResponse] = []

    class Config:
        from_attributes = True

class ExecutionListResponse(BaseModel):
    executions: List[PlaybookExecutionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ExecutionStatsResponse(BaseModel):
    total_executions: int
    successful_executions: int
    failed_executions: int
    running_executions: int
    average_duration: Optional[float]
    recent_executions: List[PlaybookExecutionResponse]

@router.get("/", response_model=ExecutionListResponse)
async def list_executions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    playbook_name: Optional[str] = Query(None, description="Filter by playbook name"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db)
):
    """
    List all playbook executions with pagination and filtering
    """
    try:
        # Build query
        query = db.query(PlaybookExecution)
        
        # Apply filters
        if status_filter:
            query = query.filter(PlaybookExecution.status == status_filter)
        
        if playbook_name:
            query = query.filter(PlaybookExecution.playbook_name.ilike(f"%{playbook_name}%"))
        
        if date_from:
            query = query.filter(PlaybookExecution.started_at >= date_from)
        
        if date_to:
            query = query.filter(PlaybookExecution.started_at <= date_to)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        executions = query.order_by(desc(PlaybookExecution.started_at))\
                          .offset((page - 1) * page_size)\
                          .limit(page_size)\
                          .all()
        
        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size
        
        return ExecutionListResponse(
            executions=executions,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list executions: {str(e)}"
        )

@router.get("/stats", response_model=ExecutionStatsResponse)
async def get_execution_stats(
    db: Session = Depends(get_db)
):
    """
    Get execution statistics
    """
    try:
        # Get total executions
        total_executions = db.query(PlaybookExecution).count()
        
        # Get successful executions
        successful_executions = db.query(PlaybookExecution)\
                                 .filter(PlaybookExecution.status == "completed")\
                                 .count()
        
        # Get failed executions
        failed_executions = db.query(PlaybookExecution)\
                             .filter(PlaybookExecution.status == "failed")\
                             .count()
        
        # Get running executions
        running_executions = db.query(PlaybookExecution)\
                              .filter(PlaybookExecution.status.in_(["queued", "running"]))\
                              .count()
        
        # Calculate average duration for completed executions
        completed_executions = db.query(PlaybookExecution)\
                                .filter(and_(
                                    PlaybookExecution.status == "completed",
                                    PlaybookExecution.duration.isnot(None)
                                ))\
                                .all()
        
        if completed_executions:
            average_duration = sum(execution.duration for execution in completed_executions) / len(completed_executions)
        else:
            average_duration = None
        
        # Get recent executions (last 10)
        recent_executions = db.query(PlaybookExecution)\
                             .order_by(desc(PlaybookExecution.started_at))\
                             .limit(10)\
                             .all()
        
        return ExecutionStatsResponse(
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            running_executions=running_executions,
            average_duration=average_duration,
            recent_executions=recent_executions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution stats: {str(e)}"
        )

@router.get("/{execution_id}", response_model=PlaybookExecutionResponse)
async def get_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific execution
    """
    try:
        execution = db.query(PlaybookExecution)\
                     .filter(PlaybookExecution.execution_id == execution_id)\
                     .first()
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        return execution
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution: {str(e)}"
        )

@router.get("/{execution_id}/jobs/{job_id}", response_model=JobExecutionResponse)
async def get_job_execution(
    execution_id: str,
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific job execution
    """
    try:
        job_execution = db.query(JobExecution)\
                         .filter(and_(
                             JobExecution.execution_id == execution_id,
                             JobExecution.job_id == job_id
                         ))\
                         .first()
        
        if not job_execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job execution not found"
            )
        
        return job_execution
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job execution: {str(e)}"
        )

@router.delete("/{execution_id}")
async def delete_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete an execution and all its associated data
    """
    try:
        execution = db.query(PlaybookExecution)\
                     .filter(PlaybookExecution.execution_id == execution_id)\
                     .first()
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        db.delete(execution)
        db.commit()
        
        return {"message": "Execution deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete execution: {str(e)}"
        )

@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel a running execution
    """
    try:
        execution = db.query(PlaybookExecution)\
                     .filter(PlaybookExecution.execution_id == execution_id)\
                     .first()
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        if execution.status not in ["queued", "running"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Execution cannot be cancelled in its current state"
            )
        
        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        if execution.started_at:
            execution.duration = int((execution.completed_at - execution.started_at).total_seconds())
        
        db.commit()
        
        return {"message": "Execution cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel execution: {str(e)}"
        )

@router.get("/{execution_id}/log")
async def get_execution_log(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the detailed execution log
    """
    try:
        execution = db.query(PlaybookExecution)\
                     .filter(PlaybookExecution.execution_id == execution_id)\
                     .first()
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        # Get all job executions for this playbook execution
        job_executions = db.query(JobExecution)\
                          .filter(JobExecution.execution_id == execution_id)\
                          .all()
        
        # Get all task executions for all jobs
        task_executions = db.query(PlaybookTaskExecution)\
                           .join(JobExecution)\
                           .filter(JobExecution.execution_id == execution_id)\
                           .all()
        
        log_data = {
            "execution": {
                "id": execution.execution_id,
                "playbook_name": execution.playbook_name,
                "status": execution.status,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "duration": execution.duration,
                "error_message": execution.error_message
            },
            "jobs": [
                {
                    "id": job.job_id,
                    "name": job.job_name,
                    "status": job.status,
                    "started_at": job.started_at,
                    "completed_at": job.completed_at,
                    "duration": job.duration,
                    "target_hosts": job.target_hosts,
                    "completed_hosts": job.completed_hosts,
                    "failed_hosts": job.failed_hosts,
                    "error_message": job.error_message
                }
                for job in job_executions
            ],
            "tasks": [
                {
                    "job_id": task.job_execution.job_id,
                    "task_name": task.task_name,
                    "module": task.module,
                    "status": task.status,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "duration": task.duration,
                    "host": task.host,
                    "stdout": task.stdout,
                    "stderr": task.stderr,
                    "return_code": task.return_code,
                    "changed": task.changed,
                    "error_message": task.error_message
                }
                for task in task_executions
            ]
        }
        
        return log_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution log: {str(e)}"
        ) 