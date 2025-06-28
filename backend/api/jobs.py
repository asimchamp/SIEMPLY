"""
Job API Router
Handles job operations including triggering installations
"""
import uuid
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session

from backend.models import get_db, Job, JobCreate, JobUpdate, JobResponse, JobType, JobStatus
from backend.models import Host
from backend.installers.splunk import install_splunk_universal_forwarder, install_splunk_enterprise
from backend.installers.cribl import install_cribl_worker, install_cribl_leader
from backend.automation.utils import run_command_with_timeout

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    responses={404: {"description": "Job not found"}},
)


@router.get("/", response_model=List[JobResponse])
async def get_jobs(
    skip: int = 0, 
    limit: int = 100, 
    host_id: Optional[int] = None,
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all jobs with optional filtering
    """
    query = db.query(Job)
    
    if host_id:
        query = query.filter(Job.host_id == host_id)
    
    if job_type:
        query = query.filter(Job.job_type == job_type)
    
    if status:
        query = query.filter(Job.status == status)
    
    # Order by created_at descending (newest first)
    query = query.order_by(Job.created_at.desc())
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get a job by ID
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/by-job-id/{unique_job_id}", response_model=JobResponse)
async def get_job_by_unique_id(unique_job_id: str, db: Session = Depends(get_db)):
    """
    Get a job by unique job ID
    """
    job = db.query(Job).filter(Job.job_id == unique_job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def _run_job(job_id: int, db: Session):
    """Run a job in the background"""
    # Get job from database
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        logger.error(f"Job {job_id} not found")
        return
    
    # Get host from database
    host = db.query(Host).filter(Host.id == job.host_id).first()
    if host is None:
        logger.error(f"Host {job.host_id} not found")
        job.status = JobStatus.FAILED.value
        job.stderr = "Host not found"
        db.commit()
        return
    
    # Update job status to running
    job.status = JobStatus.RUNNING.value
    job.started_at = datetime.utcnow()
    db.commit()
    
    # Execute job based on type
    try:
        result = None
        
        if job.job_type == JobType.SPLUNK_UF_INSTALL.value:
            result = await install_splunk_universal_forwarder(host, job.parameters)
        
        elif job.job_type == JobType.SPLUNK_ENT_INSTALL.value:
            result = await install_splunk_enterprise(host, job.parameters)
        
        elif job.job_type == JobType.CRIBL_WORKER_INSTALL.value:
            result = await install_cribl_worker(host, job.parameters)
        
        elif job.job_type == JobType.CRIBL_LEADER_INSTALL.value:
            result = await install_cribl_leader(host, job.parameters)
        
        elif job.job_type == JobType.CUSTOM_COMMAND.value:
            # Handle custom command or script
            parameters = job.parameters or {}
            is_dry_run = job.is_dry_run
            user = parameters.get("user", "root")
            command = parameters.get("command", "")
            
            if not command:
                raise ValueError("No command specified for custom job")
            
            # For bash scripts, create a temporary script file and execute it
            if "bash_script" in job.job_type:
                # Create temp script file
                script_cmd = f"""
                cat > /tmp/siemply_script.sh << 'EOF'
{command}
EOF
                chmod +x /tmp/siemply_script.sh
                sudo -u {user} /tmp/siemply_script.sh
                rm -f /tmp/siemply_script.sh
                """
                command = script_cmd
            else:
                # For regular commands, just execute as the specified user
                if user != "root":
                    command = f"sudo -u {user} {command}"
            
            # Log the command for dry runs
            if is_dry_run:
                result = {
                    "success": True,
                    "is_dry_run": True,
                    "command": command,
                    "message": "Dry run - command would be executed"
                }
            else:
                # Execute the command
                result = await run_command_with_timeout(host, command)
        
        # Update job with result
        if result:
            job.return_code = result.get("return_code")
            job.stdout = result.get("stdout", "")
            job.stderr = result.get("stderr", "")
            job.result = result
            
            # Set status based on return code
            if result.get("success"):
                job.status = JobStatus.COMPLETED.value
            else:
                job.status = JobStatus.FAILED.value
    
    except Exception as e:
        # Update job with error
        job.status = JobStatus.FAILED.value
        job.stderr = f"Error executing job: {str(e)}"
    
    # Mark job as completed
    job.completed_at = datetime.utcnow()
    db.commit()


@router.post("/install/splunk-uf", response_model=JobResponse)
async def create_splunk_uf_install_job(
    host_id: int,
    parameters: Dict[str, Any],
    is_dry_run: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a job to install Splunk Universal Forwarder
    """
    # Log received parameters
    logger.info(f"Received Splunk UF install request: host_id={host_id}, parameters={parameters}, is_dry_run={is_dry_run}")
    
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        logger.error(f"Host not found: {host_id}")
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Validate required parameters
    required_params = ["version", "user"]
    missing_params = [param for param in required_params if param not in parameters]
    
    if missing_params:
        logger.error(f"Missing required parameters: {missing_params}. Received: {parameters}")
        raise HTTPException(
            status_code=422, 
            detail=f"Missing required parameters: {', '.join(missing_params)}. Received: {parameters}"
        )
    
    # Create job
    job = Job(
        job_id=f"splunk-uf-{uuid.uuid4()}",
        host_id=host_id,
        job_type=JobType.SPLUNK_UF_INSTALL.value,
        status=JobStatus.PENDING.value,
        is_dry_run=is_dry_run,
        parameters=parameters
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Run job in background
    background_tasks.add_task(_run_job, job.id, db)
    
    logger.info(f"Created Splunk UF install job: {job.job_id}")
    return job


@router.post("/install/splunk-enterprise", response_model=JobResponse)
async def create_splunk_enterprise_install_job(
    host_id: int,
    parameters: Dict[str, Any],
    is_dry_run: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a job to install Splunk Enterprise
    """
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Create job
    job = Job(
        job_id=f"splunk-ent-{uuid.uuid4()}",
        host_id=host_id,
        job_type=JobType.SPLUNK_ENT_INSTALL.value,
        status=JobStatus.PENDING.value,
        is_dry_run=is_dry_run,
        parameters=parameters
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Run job in background
    background_tasks.add_task(_run_job, job.id, db)
    
    return job


@router.post("/install/cribl-worker", response_model=JobResponse)
async def create_cribl_worker_install_job(
    host_id: int,
    parameters: Dict[str, Any],
    is_dry_run: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a job to install Cribl Worker
    """
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Create job
    job = Job(
        job_id=f"cribl-worker-{uuid.uuid4()}",
        host_id=host_id,
        job_type=JobType.CRIBL_WORKER_INSTALL.value,
        status=JobStatus.PENDING.value,
        is_dry_run=is_dry_run,
        parameters=parameters
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Run job in background
    background_tasks.add_task(_run_job, job.id, db)
    
    return job


@router.post("/install/cribl-leader", response_model=JobResponse)
async def create_cribl_leader_install_job(
    host_id: int,
    parameters: Dict[str, Any],
    is_dry_run: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a job to install Cribl Leader
    """
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Create job
    job = Job(
        job_id=f"cribl-leader-{uuid.uuid4()}",
        host_id=host_id,
        job_type=JobType.CRIBL_LEADER_INSTALL.value,
        status=JobStatus.PENDING.value,
        is_dry_run=is_dry_run,
        parameters=parameters
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Run job in background
    background_tasks.add_task(_run_job, job.id, db)
    
    return job


@router.post("/custom", response_model=JobResponse)
async def create_custom_job(
    host_id: int,
    job_type: str,
    parameters: Dict[str, Any],
    is_dry_run: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a custom job to run user-defined commands or scripts
    """
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Validate job type
    if job_type not in ["custom_command", "bash_script"]:
        raise HTTPException(status_code=400, detail="Invalid job type for custom job")
    
    # Create job
    job = Job(
        job_id=f"custom-{uuid.uuid4()}",
        host_id=host_id,
        job_type=JobType.CUSTOM_COMMAND.value,
        status=JobStatus.PENDING.value,
        is_dry_run=is_dry_run,
        parameters=parameters
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Run job in background
    background_tasks.add_task(_run_job, job.id, db)
    
    return job


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: int, db: Session = Depends(get_db)):
    """
    Cancel a job if it's pending
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Can only cancel pending jobs
    if job.status != JobStatus.PENDING.value:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job with status {job.status}"
        )
    
    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    
    return job 