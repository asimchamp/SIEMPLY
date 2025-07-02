"""
Scheduler API endpoints
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.config.settings import settings
from backend.models import (
    ScheduledTask, TaskExecution, ScheduleType, TaskType, 
    User, get_db
)
from backend.api.auth import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/scheduler",
    tags=["scheduler"],
)

# Pydantic models
class TaskParameters(BaseModel):
    """Task parameters model"""
    command: Optional[str] = None
    target_dir: Optional[str] = None
    config_files: Optional[List[str]] = None
    service_name: Optional[str] = None
    install_type: Optional[str] = None
    version: Optional[str] = None
    
class ScheduledTaskBase(BaseModel):
    """Scheduled task base model"""
    name: str
    description: Optional[str] = None
    task_type: TaskType
    schedule_type: ScheduleType
    cron_expression: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    host_ids: List[int] = Field(default_factory=list)
    is_active: bool = True

class ScheduledTaskCreate(ScheduledTaskBase):
    """Scheduled task create model"""
    pass

class ScheduledTaskUpdate(BaseModel):
    """Scheduled task update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[TaskType] = None
    schedule_type: Optional[ScheduleType] = None
    cron_expression: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    host_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None

class ScheduledTaskResponse(ScheduledTaskBase):
    """Scheduled task response model"""
    id: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_user_id: int
    
    class Config:
        """Pydantic config"""
        orm_mode = True

class TaskExecutionResponse(BaseModel):
    """Task execution response model"""
    id: int
    task_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    results: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic config"""
        orm_mode = True

# Helper functions
def calculate_next_run(task: ScheduledTask) -> datetime:
    """Calculate the next run time based on the schedule"""
    now = datetime.now()
    
    if task.schedule_type == ScheduleType.DAILY:
        next_run = datetime(now.year, now.month, now.day, task.hour, task.minute)
        if next_run <= now:
            next_run += timedelta(days=1)
            
    elif task.schedule_type == ScheduleType.WEEKLY:
        # Find the next occurrence of the day of week
        days_ahead = task.day_of_week - now.weekday()
        if days_ahead < 0 or (days_ahead == 0 and now.hour > task.hour or 
                            (now.hour == task.hour and now.minute >= task.minute)):
            days_ahead += 7
        next_run = now + timedelta(days=days_ahead)
        next_run = datetime(next_run.year, next_run.month, next_run.day, 
                           task.hour, task.minute)
                           
    elif task.schedule_type == ScheduleType.MONTHLY:
        # Set for the same day next month
        if now.day > task.day_of_month:
            if now.month == 12:
                next_run = datetime(now.year + 1, 1, task.day_of_month, 
                                   task.hour, task.minute)
            else:
                next_run = datetime(now.year, now.month + 1, task.day_of_month, 
                                   task.hour, task.minute)
        else:
            next_run = datetime(now.year, now.month, task.day_of_month, 
                               task.hour, task.minute)
            if next_run <= now:
                if now.month == 12:
                    next_run = datetime(now.year + 1, 1, task.day_of_month, 
                                       task.hour, task.minute)
                else:
                    next_run = datetime(now.year, now.month + 1, task.day_of_month, 
                                       task.hour, task.minute)
    
    elif task.schedule_type == ScheduleType.ONE_TIME:
        next_run = datetime(now.year, now.month, task.day_of_month, 
                           task.hour, task.minute)
                           
    # Handle CRON separately as it requires a cron expression parser
    elif task.schedule_type == ScheduleType.CRON:
        # Simple implementation for now - just 24 hours later
        next_run = now + timedelta(hours=24)
    
    return next_run

# API Routes
@router.post("/tasks", response_model=ScheduledTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: ScheduledTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new scheduled task"""
    # Validate schedule parameters based on schedule type
    if task_data.schedule_type == ScheduleType.DAILY:
        if task_data.hour is None or task_data.minute is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Daily schedule requires hour and minute",
            )
    elif task_data.schedule_type == ScheduleType.WEEKLY:
        if task_data.day_of_week is None or task_data.hour is None or task_data.minute is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weekly schedule requires day_of_week, hour, and minute",
            )
    elif task_data.schedule_type == ScheduleType.MONTHLY:
        if task_data.day_of_month is None or task_data.hour is None or task_data.minute is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monthly schedule requires day_of_month, hour, and minute",
            )
    elif task_data.schedule_type == ScheduleType.CRON:
        if not task_data.cron_expression:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cron schedule requires cron_expression",
            )
    
    # Create new task
    task = ScheduledTask(
        name=task_data.name,
        description=task_data.description,
        task_type=task_data.task_type,
        schedule_type=task_data.schedule_type,
        cron_expression=task_data.cron_expression,
        day_of_week=task_data.day_of_week,
        day_of_month=task_data.day_of_month,
        hour=task_data.hour,
        minute=task_data.minute,
        parameters=task_data.parameters,
        host_ids=task_data.host_ids,
        is_active=task_data.is_active,
        created_by_user_id=current_user.id,
    )
    
    # Calculate next run time
    task.next_run = calculate_next_run(task)
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task

@router.get("/tasks", response_model=List[ScheduledTaskResponse])
async def get_tasks(
    is_active: Optional[bool] = None,
    task_type: Optional[TaskType] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all scheduled tasks with optional filters"""
    query = db.query(ScheduledTask)
    
    if is_active is not None:
        query = query.filter(ScheduledTask.is_active == is_active)
        
    if task_type:
        query = query.filter(ScheduledTask.task_type == task_type)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks

@router.get("/tasks/{task_id}", response_model=ScheduledTaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific scheduled task by ID"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    return task

@router.patch("/tasks/{task_id}", response_model=ScheduledTaskResponse)
async def update_task(
    task_id: int,
    task_data: ScheduledTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a scheduled task"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    # Update task fields
    for field, value in task_data.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    # Recalculate next run time if schedule changed
    schedule_fields = ["schedule_type", "cron_expression", "day_of_week", 
                      "day_of_month", "hour", "minute"]
    if any(field in task_data.dict(exclude_unset=True) for field in schedule_fields):
        task.next_run = calculate_next_run(task)
    
    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a scheduled task"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    db.delete(task)
    db.commit()
    return None

@router.post("/tasks/{task_id}/execute", response_model=TaskExecutionResponse)
async def execute_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Execute a scheduled task immediately"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    # Create task execution record
    execution = TaskExecution(
        task_id=task.id,
        started_at=datetime.now(),
        status="running",
    )
    
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # TODO: In a production system, we would queue the task for execution here
    # For now, update the status to simulate execution
    execution.status = "success"
    execution.completed_at = datetime.now()
    execution.results = {"message": "Task executed successfully (simulated)"}
    
    # Update task last run information
    task.last_run = execution.completed_at
    task.last_status = execution.status
    
    db.commit()
    db.refresh(execution)
    
    return execution

@router.get("/executions", response_model=List[TaskExecutionResponse])
async def get_executions(
    task_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get task execution history with optional filters"""
    query = db.query(TaskExecution)
    
    if task_id:
        query = query.filter(TaskExecution.task_id == task_id)
        
    if status:
        query = query.filter(TaskExecution.status == status)
    
    # Order by started_at descending (most recent first)
    query = query.order_by(TaskExecution.started_at.desc())
    
    executions = query.offset(skip).limit(limit).all()
    return executions

@router.get("/executions/{execution_id}", response_model=TaskExecutionResponse)
async def get_execution(
    execution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific task execution by ID"""
    execution = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution with ID {execution_id} not found",
        )
    return execution 