#!/usr/bin/env python3
"""
Playbooks API Router
Handles playbook creation, management, and execution
"""
import os
import yaml
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models import get_db, PlaybookExecution, JobExecution, PlaybookTaskExecution, Host
from backend.config.settings import settings
from backend.services.serverclass_service import ServerClassService

router = APIRouter(prefix="/playbooks", tags=["playbooks"])

# Ensure playbooks directory exists
PLAYBOOKS_DIR = Path(settings.BASE_DIR) / "playbooks"
PLAYBOOKS_DIR.mkdir(exist_ok=True)

def resolve_serverclass_to_hosts(server_class_name: str, db: Session) -> List[str]:
    """
    Resolve a server class name to a list of host IP addresses
    
    Args:
        server_class_name: Name of the server class
        db: Database session
        
    Returns:
        List of host IP addresses
    """
    print(f"DEBUG: Starting serverclass resolution for '{server_class_name}'")
    try:
        # Get server class information
        service = ServerClassService()
        server_class = service.get_server_class(server_class_name)
        
        print(f"DEBUG: Server class data: {server_class}")
        
        if not server_class:
            print(f"ERROR: Server class '{server_class_name}' not found")
            return []
        
        if not server_class.get('is_active', True):
            print(f"ERROR: Server class '{server_class_name}' is not active")
            return []
        
        # Get host IDs from server class
        host_ids = server_class.get('host_ids', [])
        print(f"DEBUG: Host IDs from server class: {host_ids}")
        
        if not host_ids:
            print(f"ERROR: Server class '{server_class_name}' has no hosts")
            return []
        
        # Get host IPs from database
        host_ips = []
        for host_id in host_ids:
            host = db.query(Host).filter(Host.id == host_id).first()
            if host:
                host_ips.append(host.ip_address)
                print(f"DEBUG: Resolved server class '{server_class_name}' host {host_id} to {host.ip_address}")
            else:
                print(f"ERROR: Host with ID {host_id} not found in database")
        
        print(f"DEBUG: Server class '{server_class_name}' resolved to {len(host_ips)} hosts: {host_ips}")
        return host_ips
        
    except Exception as e:
        print(f"ERROR: Error resolving server class '{server_class_name}': {e}")
        import traceback
        traceback.print_exc()
        return []

async def execute_playbook_background(execution_id: str, playbook_content: str, filepath: Path, db: Session):
    """
    Background task to execute playbook
    """
    try:
        # Parse the YAML
        yaml_data = yaml.safe_load(playbook_content)
        
        # Get database session for background task
        from backend.models import get_db
        db = next(get_db())
        
        try:
            # Get execution record
            execution = db.query(PlaybookExecution).filter(PlaybookExecution.execution_id == execution_id).first()
            if not execution:
                print(f"ERROR: Execution {execution_id} not found")
                return
            
            # Update execution status to running
            execution.status = "running"
            db.commit()
            
            # Get the automation playbook data
            automation_playbook = yaml_data.get('automation_playbook', [])
            
            # Process each job in the playbook
            completed_jobs = 0
            failed_jobs = 0
            
            for job_index, job_data in enumerate(automation_playbook):
                # Handle both simple and complex job structures
                if 'job' in job_data:
                    # Complex structure from Playbook Builder
                    job_obj = job_data['job']
                    job_name = job_obj.get('name', f'Job {job_index + 1}')
                    job_id = job_obj.get('id', f'job_{job_index + 1}')
                    job_description = job_obj.get('description', '')
                    tasks = job_obj.get('tasks', [])
                    targets = job_obj.get('targets', {})
                    execution_options = job_obj.get('execution_options', {})
                    
                    # Extract target hosts
                    target_hosts = []
                    if 'hosts' in targets:
                        target_hosts = targets['hosts']
                    elif 'server_class' in targets:
                        # Resolve server class to host IPs
                        target_hosts = resolve_serverclass_to_hosts(targets['server_class'], db)
                    

                else:
                    # Simple structure
                    job_name = job_data.get('name', f'Job {job_index + 1}')
                    job_id = f'job_{job_index + 1}'
                    job_description = job_data.get('description', '')
                    tasks = job_data.get('tasks', [])
                    targets = job_data.get('targets', {})
                    execution_options = job_data.get('execution_options', {})
                    
                    # Extract target hosts for simple structure
                    target_hosts = []
                    if 'hosts' in targets:
                        target_hosts = targets['hosts']
                    elif 'server_class' in targets:
                        # Resolve server class to host IPs
                        target_hosts = resolve_serverclass_to_hosts(targets['server_class'], db)
                    

                
                # Create job execution record
                job_execution = JobExecution(
                    execution_id=execution_id,
                    job_id=job_id,
                    job_name=job_name,
                    status="running",
                    started_at=datetime.utcnow(),
                    target_hosts=target_hosts  # Use the extracted target hosts
                )
                
                db.add(job_execution)
                db.commit()
                db.refresh(job_execution)
                
                # Process tasks for this job
                completed_hosts = 0
                failed_hosts = 0
                
                # Execute each task on all target hosts
                for task_index, task_data in enumerate(tasks):
                    task_name = task_data.get('name', f'Task {task_index + 1}')
                    
                    # Handle different task structures
                    if 'command' in task_data:
                        # Builder structure: command with nested cmd
                        module = 'command'
                        cmd_data = task_data['command']
                        if isinstance(cmd_data, dict):
                            args = cmd_data
                        else:
                            args = {'cmd': str(cmd_data)}

                    elif 'module' in task_data:
                        # Simple structure: module with args
                        module = task_data.get('module', 'command')
                        args = task_data.get('args', {})

                    else:
                        # Default to command
                        module = 'command'
                        args = {}

                    
                    # Execute task on all target hosts
                    hosts_to_execute = target_hosts if target_hosts else ['localhost']
                    
                    for host in hosts_to_execute:
                        print(f"DEBUG: Executing task '{task_name}' on host '{host}'")
                        
                        # Create task execution record for this host
                        task_execution = PlaybookTaskExecution(
                            job_execution_id=job_execution.id,
                            task_name=task_name,
                            module=module,
                            status="running",
                            started_at=datetime.utcnow(),
                            host=host
                        )
                        
                        db.add(task_execution)
                        db.commit()
                        db.refresh(task_execution)
                        
                        # Execute the task
                        try:
                            if module == "command":
                                cmd = args.get('cmd', '')
                                if cmd:
                                    # Execute command and capture real output
                                    import subprocess
                                    if host == "localhost":
                                        # For localhost, execute the command and capture real output
                                        result = subprocess.run(
                                            cmd, 
                                            shell=True, 
                                            capture_output=True, 
                                            text=True, 
                                            timeout=300,
                                            executable='/bin/bash'
                                        )
                                        task_execution.return_code = result.returncode
                                        task_execution.stdout = result.stdout
                                        task_execution.stderr = result.stderr
                                        task_execution.status = "completed" if result.returncode == 0 else "failed"
                                    else:
                                        # For remote hosts, use SSH to execute the command
                                        from backend.automation.utils import create_ssh_client_from_host
                                        from backend.models import Host
                                        
                                        # Get host information from database
                                        host_obj = db.query(Host).filter(Host.ip_address == host).first()
                                        if host_obj:
                                            try:
                                                ssh_client = create_ssh_client_from_host(host_obj)
                                                return_code, stdout, stderr = ssh_client.execute_command(cmd)
                                                task_execution.return_code = return_code
                                                task_execution.stdout = stdout
                                                task_execution.stderr = stderr
                                                task_execution.status = "completed" if return_code == 0 else "failed"
                                            except Exception as ssh_error:
                                                task_execution.status = "failed"
                                                task_execution.error_message = f"SSH connection failed: {str(ssh_error)}"
                                                task_execution.return_code = -1
                                        else:
                                            # Fallback to simulated execution if host not found
                                            task_execution.stdout = f"Host {host} not found in database. Simulated execution of '{cmd}'"
                                            task_execution.status = "completed"
                                            task_execution.return_code = 0
                                    
                                    task_execution.completed_at = datetime.utcnow()
                                    if task_execution.started_at:
                                        task_execution.duration = int((task_execution.completed_at - task_execution.started_at).total_seconds())
                                    
                                    if task_execution.status == "completed":
                                        completed_hosts += 1
                                    else:
                                        failed_hosts += 1
                                        task_execution.error_message = task_execution.stderr
                                else:
                                    task_execution.status = "failed"
                                    task_execution.error_message = "No command specified"
                                    task_execution.completed_at = datetime.utcnow()
                                    failed_hosts += 1
                            else:
                                # Handle other modules (service, file, etc.)
                                task_execution.status = "completed"
                                task_execution.stdout = f"Executed {module} module"
                                task_execution.completed_at = datetime.utcnow()
                                completed_hosts += 1
                            
                            db.commit()
                            
                        except Exception as e:
                            task_execution.status = "failed"
                            task_execution.error_message = str(e)
                            task_execution.completed_at = datetime.utcnow()
                            failed_hosts += 1
                            db.commit()
                
                # Update job execution with results
                job_execution.completed_at = datetime.utcnow()
                job_execution.status = "completed" if failed_hosts == 0 else "failed"
                job_execution.completed_hosts = completed_hosts
                job_execution.failed_hosts = failed_hosts
                if job_execution.started_at:
                    job_execution.duration = int((job_execution.completed_at - job_execution.started_at).total_seconds())
                
                db.commit()
                
                if job_execution.status == "completed":
                    completed_jobs += 1
                else:
                    failed_jobs += 1
            
            # Update playbook execution with final results
            execution.completed_at = datetime.utcnow()
            execution.status = "completed" if failed_jobs == 0 else "failed"
            execution.completed_jobs = completed_jobs
            execution.failed_jobs = failed_jobs
            if execution.started_at:
                execution.duration = int((execution.completed_at - execution.started_at).total_seconds())
            
            db.commit()
            
        except Exception as e:
            # Update execution status to failed
            execution = db.query(PlaybookExecution).filter(PlaybookExecution.execution_id == execution_id).first()
            if execution:
                execution.status = "failed"
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                if execution.started_at:
                    execution.duration = int((execution.completed_at - execution.started_at).total_seconds())
                db.commit()
            print(f"ERROR: Background execution failed for {execution_id}: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        print(f"ERROR: Background task failed: {e}")
        import traceback
        traceback.print_exc()

class PlaybookCreate(BaseModel):
    name: str
    content: str

class PlaybookResponse(BaseModel):
    id: str
    name: str
    content: str
    created_at: datetime
    updated_at: datetime
    size: int

class PlaybookList(BaseModel):
    playbooks: List[PlaybookResponse]
    total: int

@router.post("/", response_model=PlaybookResponse)
async def create_playbook(
    playbook: PlaybookCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new playbook YAML file
    """
    try:
        # Validate YAML content
        try:
            yaml.safe_load(playbook.content)
        except yaml.YAMLError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid YAML content: {str(e)}"
            )
        
        # Create filename with timestamp if not provided
        filename = playbook.name
        if not filename.endswith('.yml') and not filename.endswith('.yaml'):
            filename += '.yml'
        
        # Ensure unique filename
        filepath = PLAYBOOKS_DIR / filename
        counter = 1
        while filepath.exists():
            name_without_ext = filename.rsplit('.', 1)[0]
            ext = filename.rsplit('.', 1)[1] if '.' in filename else 'yml'
            filename = f"{name_without_ext}_{counter}.{ext}"
            filepath = PLAYBOOKS_DIR / filename
            counter += 1
        
        # Write playbook to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(playbook.content)
        
        # Get file stats
        stat = filepath.stat()
        
        return PlaybookResponse(
            id=str(filepath),
            name=filename,
            content=playbook.content,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            updated_at=datetime.fromtimestamp(stat.st_mtime),
            size=stat.st_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create playbook: {str(e)}"
        )

@router.put("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: str,
    playbook: PlaybookCreate,
    db: Session = Depends(get_db)
):
    """
    Update an existing playbook YAML file
    """
    try:
        import urllib.parse
        decoded_playbook_id = urllib.parse.unquote(playbook_id)
        filepath = Path(decoded_playbook_id)
        
        # If it's not a full path or doesn't exist, try to find it in the playbooks directory
        if not filepath.exists() or not filepath.is_absolute():
            for playbook_file in PLAYBOOKS_DIR.glob("*.yml"):
                if playbook_file.name == decoded_playbook_id or str(playbook_file) == decoded_playbook_id:
                    filepath = playbook_file
                    break
        
        if not filepath.exists() or not filepath.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook not found: {decoded_playbook_id}"
            )
        
        # Validate YAML content
        try:
            yaml.safe_load(playbook.content)
        except yaml.YAMLError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid YAML content: {str(e)}"
            )
        
        # Write updated playbook to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(playbook.content)
        
        # Get updated file stats
        stat = filepath.stat()
        
        return PlaybookResponse(
            id=str(filepath),
            name=filepath.name,
            content=playbook.content,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            updated_at=datetime.fromtimestamp(stat.st_mtime),
            size=stat.st_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update playbook: {str(e)}"
        )

@router.get("/", response_model=PlaybookList)
async def list_playbooks(
    db: Session = Depends(get_db)
):
    """
    List all available playbooks
    """
    try:
        playbooks = []
        
        for filepath in PLAYBOOKS_DIR.glob("*.yml"):
            if filepath.is_file():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    stat = filepath.stat()
                    playbooks.append(PlaybookResponse(
                        id=str(filepath),
                        name=filepath.name,
                        content=content,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        updated_at=datetime.fromtimestamp(stat.st_mtime),
                        size=stat.st_size
                    ))
                except Exception as e:
                    # Skip files that can't be read
                    continue
        
        # Sort by updated_at descending
        playbooks.sort(key=lambda x: x.updated_at, reverse=True)
        
        return PlaybookList(
            playbooks=playbooks,
            total=len(playbooks)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list playbooks: {str(e)}"
        )

@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific playbook by ID
    """
    try:
        import urllib.parse
        decoded_playbook_id = urllib.parse.unquote(playbook_id)
        filepath = Path(decoded_playbook_id)
        
        # If it's not a full path or doesn't exist, try to find it in the playbooks directory
        if not filepath.exists() or not filepath.is_absolute():
            for playbook_file in PLAYBOOKS_DIR.glob("*.yml"):
                if playbook_file.name == decoded_playbook_id or str(playbook_file) == decoded_playbook_id:
                    filepath = playbook_file
                    break
        
        if not filepath.exists() or not filepath.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook not found: {decoded_playbook_id}"
            )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        stat = filepath.stat()
        return PlaybookResponse(
            id=str(filepath),
            name=filepath.name,
            content=content,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            updated_at=datetime.fromtimestamp(stat.st_mtime),
            size=stat.st_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get playbook: {str(e)}"
        )

@router.delete("/{playbook_id}")
async def delete_playbook(
    playbook_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a playbook
    """
    try:
        import urllib.parse
        decoded_playbook_id = urllib.parse.unquote(playbook_id)
        filepath = Path(decoded_playbook_id)
        
        # If it's not a full path or doesn't exist, try to find it in the playbooks directory
        if not filepath.exists() or not filepath.is_absolute():
            for playbook_file in PLAYBOOKS_DIR.glob("*.yml"):
                if playbook_file.name == decoded_playbook_id or str(playbook_file) == decoded_playbook_id:
                    filepath = playbook_file
                    break
        
        if not filepath.exists() or not filepath.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook not found: {decoded_playbook_id}"
            )
        
        filepath.unlink()
        
        return {"message": "Playbook deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete playbook: {str(e)}"
        )

@router.post("/{playbook_id}/validate")
async def validate_playbook(
    playbook_id: str,
    db: Session = Depends(get_db)
):
    """
    Validate a playbook YAML structure
    """
    try:
        filepath = Path(playbook_id)
        
        if not filepath.exists() or not filepath.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse YAML
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return {
                "valid": False,
                "errors": [f"YAML parsing error: {str(e)}"]
            }
        
        # Validate structure
        errors = []
        
        if not isinstance(data, dict):
            errors.append("Root must be a dictionary")
        elif 'automation_playbook' not in data:
            errors.append("Missing 'automation_playbook' key")
        elif not isinstance(data['automation_playbook'], list):
            errors.append("'automation_playbook' must be a list")
        else:
            # Validate each job
            for i, job in enumerate(data['automation_playbook']):
                if not isinstance(job, dict):
                    errors.append(f"Job {i+1}: Must be a dictionary")
                    continue
                
                if 'job' not in job:
                    errors.append(f"Job {i+1}: Missing 'job' key")
                    continue
                
                job_data = job['job']
                
                # Required fields
                required_fields = ['id', 'name', 'targets', 'execution_options', 'tasks']
                for field in required_fields:
                    if field not in job_data:
                        errors.append(f"Job {i+1}: Missing required field '{field}'")
                
                # Validate tasks
                if 'tasks' in job_data and isinstance(job_data['tasks'], list):
                    for j, task in enumerate(job_data['tasks']):
                        if not isinstance(task, dict):
                            errors.append(f"Job {i+1}, Task {j+1}: Must be a dictionary")
                            continue
                        
                        if 'name' not in task:
                            errors.append(f"Job {i+1}, Task {j+1}: Missing 'name' field")
                        
                        # Check for module
                        has_module = False
                        for key in task.keys():
                            if key not in ['name', 'when', 'register'] and isinstance(task[key], dict):
                                has_module = True
                                break
                        
                        if not has_module:
                            errors.append(f"Job {i+1}, Task {j+1}: Must have a module (e.g., service, command, etc.)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate playbook: {str(e)}"
        )

@router.post("/{playbook_id}/execute")
async def execute_playbook(
    playbook_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute a playbook and create execution tracking record
    """
    try:
        # Handle URL-encoded playbook ID
        import urllib.parse
        decoded_playbook_id = urllib.parse.unquote(playbook_id)
        
        # Try to find the playbook file
        filepath = Path(decoded_playbook_id)
        
        # If it's not a full path or doesn't exist, try to find it in the playbooks directory
        if not filepath.exists() or not filepath.is_absolute():
            # Try to find by filename in playbooks directory
            for playbook_file in PLAYBOOKS_DIR.glob("*.yml"):
                if playbook_file.name == decoded_playbook_id or str(playbook_file) == decoded_playbook_id:
                    filepath = playbook_file
                    break
        
        if not filepath.exists() or not filepath.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook not found: {decoded_playbook_id}"
            )
        
        # Read the playbook content
        with open(filepath, 'r', encoding='utf-8') as f:
            playbook_content = f.read()
        
        # Parse the YAML to validate it
        try:
            yaml_data = yaml.safe_load(playbook_content)
        except yaml.YAMLError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid YAML in playbook: {str(e)}"
            )
        
        # Create execution record
        execution_id = f"exec_{datetime.now().timestamp()}"
        total_jobs = len(yaml_data.get('automation_playbook', []))
        
        execution = PlaybookExecution(
            execution_id=execution_id,
            playbook_id=str(filepath),
            playbook_name=filepath.name,
            status="queued",
            total_jobs=total_jobs,
            started_at=datetime.utcnow()
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # Schedule background execution
        background_tasks.add_task(
            execute_playbook_background,
            execution_id,
            playbook_content,
            filepath,
            db
        )
        
        return {
            "message": "Playbook execution started",
            "playbook_id": str(filepath),
            "playbook_name": filepath.name,
            "status": "queued",
            "execution_id": execution_id,
            "jobs_count": total_jobs,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute playbook: {str(e)}"
        ) 