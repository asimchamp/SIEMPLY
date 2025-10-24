"""
Runbook API Router
Handles runbook management and execution operations
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Form
from sqlalchemy.orm import Session

from backend.models import (
    get_db, User,
    Runbook, RunbookExecution, RunbookTaskExecution,
    RunbookCreate, RunbookUpdate, RunbookResponse,
    RunbookExecutionCreate, RunbookExecutionResponse, RunbookTaskExecutionResponse,
    RunbookStatus, TaskStatus
)
from backend.api.auth import get_current_active_user
from backend.services.runbook_service import RunbookService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/runbooks",
    tags=["runbooks"],
    responses={404: {"description": "Runbook not found"}},
)

@router.get("/", response_model=List[RunbookResponse])
async def get_runbooks(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all runbooks with optional filtering
    """
    query = db.query(Runbook)
    
    if is_active is not None:
        query = query.filter(Runbook.is_active == is_active)
    
    # Order by name
    query = query.order_by(Runbook.name)
    
    runbooks = query.offset(skip).limit(limit).all()
    return runbooks

@router.get("/{runbook_id}", response_model=RunbookResponse)
async def get_runbook(
    runbook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a runbook by ID
    """
    runbook = db.query(Runbook).filter(Runbook.id == runbook_id).first()
    if runbook is None:
        raise HTTPException(status_code=404, detail="Runbook not found")
    return runbook

@router.post("/", response_model=RunbookResponse)
async def create_runbook(
    runbook_data: RunbookCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new runbook
    """
    try:
        # Check if runbook with same name already exists
        existing_runbook = db.query(Runbook).filter(Runbook.name == runbook_data.name).first()
        if existing_runbook:
            raise HTTPException(status_code=400, detail="Runbook with this name already exists")
        
        # Validate YAML content if provided
        if runbook_data.yaml_content:
            service = RunbookService(db)
            service.parse_yaml_content(runbook_data.yaml_content)
        
        # Create runbook
        runbook = Runbook(
            name=runbook_data.name,
            description=runbook_data.description,
            yaml_file_path=runbook_data.yaml_file_path,
            yaml_content=runbook_data.yaml_content,
            created_by_user_id=current_user.id
        )
        
        db.add(runbook)
        db.commit()
        db.refresh(runbook)
        
        logger.info(f"User {current_user.username} created runbook '{runbook_data.name}'")
        return runbook
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating runbook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{runbook_id}", response_model=RunbookResponse)
async def update_runbook(
    runbook_id: int,
    runbook_data: RunbookUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a runbook
    """
    try:
        runbook = db.query(Runbook).filter(Runbook.id == runbook_id).first()
        if runbook is None:
            raise HTTPException(status_code=404, detail="Runbook not found")
        
        # Validate YAML content if provided
        if runbook_data.yaml_content:
            service = RunbookService(db)
            service.parse_yaml_content(runbook_data.yaml_content)
        
        # Update fields
        if runbook_data.description is not None:
            runbook.description = runbook_data.description
        if runbook_data.yaml_file_path is not None:
            runbook.yaml_file_path = runbook_data.yaml_file_path
        if runbook_data.yaml_content is not None:
            runbook.yaml_content = runbook_data.yaml_content
        if runbook_data.is_active is not None:
            runbook.is_active = runbook_data.is_active
        
        runbook.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(runbook)
        
        logger.info(f"User {current_user.username} updated runbook '{runbook.name}'")
        return runbook
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating runbook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{runbook_id}")
async def delete_runbook(
    runbook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a runbook
    """
    try:
        runbook = db.query(Runbook).filter(Runbook.id == runbook_id).first()
        if runbook is None:
            raise HTTPException(status_code=404, detail="Runbook not found")
        
        # Check if there are any executions for this runbook
        executions = db.query(RunbookExecution).filter(RunbookExecution.runbook_id == runbook_id).count()
        if executions > 0:
            raise HTTPException(status_code=400, detail="Cannot delete runbook with existing executions")
        
        db.delete(runbook)
        db.commit()
        
        logger.info(f"User {current_user.username} deleted runbook '{runbook.name}'")
        return {"message": "Runbook deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting runbook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{runbook_id}/validate")
async def validate_runbook_yaml(
    runbook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate runbook YAML content
    """
    try:
        runbook = db.query(Runbook).filter(Runbook.id == runbook_id).first()
        if runbook is None:
            raise HTTPException(status_code=404, detail="Runbook not found")
        
        if not runbook.yaml_content:
            raise HTTPException(status_code=400, detail="Runbook has no YAML content to validate")
        
        service = RunbookService(db)
        parsed_data = service.parse_yaml_content(runbook.yaml_content)
        
        # Get target information
        target_info = []
        for job_item in parsed_data.get("automation_playbook", []):
            job = job_item.get("job", {})
            targets = job.get("targets", {})
            
            if "server_class" in targets:
                server_class_name = targets["server_class"]
                server_class = service.serverclass_service.get_server_class(server_class_name)
                if server_class:
                    target_info.append({
                        "type": "server_class",
                        "name": server_class_name,
                        "host_count": len(server_class.get("host_ids", [])),
                        "hosts": server_class.get("hostnames", [])
                    })
                else:
                    target_info.append({
                        "type": "server_class",
                        "name": server_class_name,
                        "error": "Server class not found"
                    })
            elif "hosts" in targets:
                host_list = targets["hosts"]
                if isinstance(host_list, list):
                    target_info.append({
                        "type": "hosts",
                        "host_ids": host_list,
                        "host_count": len(host_list)
                    })
        
        return {
            "valid": True,
            "message": "YAML is valid",
            "jobs_count": len(parsed_data.get("automation_playbook", [])),
            "targets": target_info
        }
        
    except ValueError as e:
        return {
            "valid": False,
            "message": str(e),
            "jobs_count": 0,
            "targets": []
        }
    except Exception as e:
        logger.error(f"Error validating runbook YAML: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{runbook_id}/execute", response_model=RunbookExecutionResponse)
async def execute_runbook(
    runbook_id: int,
    execution_data: RunbookExecutionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Execute a runbook
    """
    try:
        runbook = db.query(Runbook).filter(Runbook.id == runbook_id).first()
        if runbook is None:
            raise HTTPException(status_code=404, detail="Runbook not found")
        
        if not runbook.is_active:
            raise HTTPException(status_code=400, detail="Cannot execute inactive runbook")
        
        if not runbook.yaml_content:
            raise HTTPException(status_code=400, detail="Runbook has no YAML content to execute")
        
        # Create execution record
        service = RunbookService(db)
        execution = service.create_runbook_execution(
            runbook_id=runbook_id,
            triggered_by_user_id=current_user.id,
            parameters=execution_data.parameters
        )
        
        # Start execution in background
        background_tasks.add_task(
            _execute_runbook_background,
            execution.id,
            current_user.id,
            db
        )
        
        logger.info(f"User {current_user.username} started execution of runbook '{runbook.name}' (execution_id: {execution.execution_id})")
        return execution
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing runbook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/executions", response_model=List[RunbookExecutionResponse])
async def get_runbook_executions(
    runbook_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get runbook executions with optional filtering
    """
    query = db.query(RunbookExecution)
    
    if runbook_id:
        query = query.filter(RunbookExecution.runbook_id == runbook_id)
    
    if status:
        query = query.filter(RunbookExecution.status == status)
    
    # Order by started_at descending (newest first)
    query = query.order_by(RunbookExecution.started_at.desc())
    
    executions = query.offset(skip).limit(limit).all()
    return executions

@router.get("/executions/{execution_id}", response_model=RunbookExecutionResponse)
async def get_runbook_execution(
    execution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific runbook execution
    """
    execution = db.query(RunbookExecution).filter(RunbookExecution.id == execution_id).first()
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution

@router.get("/executions/{execution_id}/tasks", response_model=List[RunbookTaskExecutionResponse])
async def get_execution_tasks(
    execution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get tasks for a specific execution
    """
    tasks = db.query(RunbookTaskExecution).filter(
        RunbookTaskExecution.execution_id == execution_id
    ).order_by(RunbookTaskExecution.id).all()
    return tasks

@router.post("/from-file")
async def create_runbook_from_file(
    file_path: str = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a runbook from a file in the files system
    """
    try:
        from backend.api.files import FILES_BASE_DIR
        
        # Construct full file path
        full_path = FILES_BASE_DIR / file_path
        
        # Security check
        if not str(full_path.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if full_path.is_dir():
            raise HTTPException(status_code=400, detail="Cannot create runbook from directory")
        
        # Read file content
        with open(full_path, "r", encoding="utf-8") as f:
            yaml_content = f.read()
        
        # Validate YAML content
        service = RunbookService(db)
        service.parse_yaml_content(yaml_content)
        
        # Check if runbook with same name already exists
        existing_runbook = db.query(Runbook).filter(Runbook.name == name).first()
        if existing_runbook:
            raise HTTPException(status_code=400, detail="Runbook with this name already exists")
        
        # Create runbook
        runbook = Runbook(
            name=name,
            description=description,
            yaml_file_path=file_path,
            yaml_content=yaml_content,
            created_by_user_id=current_user.id
        )
        
        db.add(runbook)
        db.commit()
        db.refresh(runbook)
        
        logger.info(f"User {current_user.username} created runbook '{name}' from file '{file_path}'")
        return RunbookResponse.from_orm(runbook)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating runbook from file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def _execute_runbook_background(execution_id: int, user_id: int, db: Session):
    """Execute runbook in background"""
    try:
        # Get execution record
        execution = db.query(RunbookExecution).filter(RunbookExecution.id == execution_id).first()
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return
        
        runbook = db.query(Runbook).filter(Runbook.id == execution.runbook_id).first()
        if not runbook:
            logger.error(f"Runbook {execution.runbook_id} not found")
            return
        
        # Update status to running
        service = RunbookService(db)
        service.update_execution_status(execution_id, RunbookStatus.RUNNING.value)
        
        # Parse YAML content
        try:
            parsed_data = service.parse_yaml_content(runbook.yaml_content)
        except ValueError as e:
            service.update_execution_status(execution_id, RunbookStatus.FAILED.value, error_message=str(e))
            return
        
        # Execute each job
        overall_results = []
        overall_success = True
        
        for job_item in parsed_data.get("automation_playbook", []):
            job = job_item.get("job", {})
            job_id = job.get("id")
            job_name = job.get("name")
            targets = job.get("targets", {})
            tasks = job.get("tasks", [])
            execution_options = job.get("execution_options", {})
            
            logger.info(f"Executing job '{job_name}' (ID: {job_id})")
            
            # Get target hosts
            try:
                hosts = service.get_target_hosts(targets)
                if not hosts:
                    logger.warning(f"No hosts found for job '{job_name}'")
                    continue
            except ValueError as e:
                logger.error(f"Error getting target hosts for job '{job_name}': {e}")
                overall_success = False
                continue
            
            # Execute each task
            job_results = []
            job_success = True
            
            for task in tasks:
                task_name = task.get("name", "Unknown Task")
                logger.info(f"Executing task '{task_name}' in job '{job_name}'")
                
                # Create task execution record
                task_execution = service.create_task_execution(
                    execution_id=execution_id,
                    task_name=task_name,
                    task_type="unknown",  # Will be determined by service
                    target_hosts=[host.id for host in hosts],
                    parameters=task
                )
                
                # Update task status to running
                service.update_task_execution_status(task_execution.id, TaskStatus.RUNNING.value)
                
                try:
                    # Execute task
                    task_result = service.execute_task(task, hosts, execution_options)
                    
                    # Update task execution record
                    task_status = TaskStatus.COMPLETED.value if task_result["overall_success"] else TaskStatus.FAILED.value
                    service.update_task_execution_status(
                        task_execution.id,
                        task_status,
                        result=task_result,
                        error_message=task_result.get("error_message")
                    )
                    
                    job_results.append(task_result)
                    if not task_result["overall_success"]:
                        job_success = False
                        
                except Exception as e:
                    logger.error(f"Error executing task '{task_name}': {e}")
                    service.update_task_execution_status(
                        task_execution.id,
                        TaskStatus.FAILED.value,
                        error_message=str(e)
                    )
                    job_success = False
            
            overall_results.append({
                "job_id": job_id,
                "job_name": job_name,
                "success": job_success,
                "results": job_results
            })
            
            if not job_success:
                overall_success = False
        
        # Update execution status
        final_status = RunbookStatus.COMPLETED.value if overall_success else RunbookStatus.FAILED.value
        service.update_execution_status(execution_id, final_status, results=overall_results)
        
        logger.info(f"Runbook execution {execution_id} completed with status: {final_status}")
        
    except Exception as e:
        logger.error(f"Error in background runbook execution {execution_id}: {e}")
        try:
            service = RunbookService(db)
            service.update_execution_status(execution_id, RunbookStatus.FAILED.value, error_message=str(e))
        except:
            pass 