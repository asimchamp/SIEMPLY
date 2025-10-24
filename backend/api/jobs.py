"""
Job API Router
Handles job operations including triggering installations
"""
import uuid
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session

from backend.models import get_db, Job, JobCreate, JobUpdate, JobResponse, JobType, JobStatus
from backend.models import Host
from backend.automation.ssh_client import get_ssh_client
from backend.installers.splunk import install_splunk_enterprise
from backend.installers.splunk import upgrade_splunk_enterprise
from backend.installers.splunk import install_splunk_uf_tmux, upgrade_splunk_uf_tmux
from backend.installers.cribl import install_cribl_worker, install_cribl_leader
from backend.automation.syslog.syslog_installer import install_syslog_ng
from backend.automation.utils import run_command_with_timeout

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    responses={404: {"description": "Job not found"}},
)





async def _monitor_tmux_session(job_db_id: int, host_id: int, session_name: str, rc_path: str, log_file_path: str = "/tmp/siemply_splunk/runner.log"):
    """Monitor a remote tmux session and mark the job complete when finished."""
    from backend.models import get_db
    db = next(get_db())
    try:
        host = db.query(Host).filter(Host.id == host_id).first()
        if not host:
            logger.error(f"Monitor: host not found: {host_id}")
            return
        from backend.automation.ssh_client import get_ssh_client
        async with get_ssh_client(host) as ssh:
            if not ssh:
                logger.error("Monitor: SSH connection failed")
                return
            # Poll until rc file appears or session disappears or timeout
            rc = None
            elapsed = 0
            interval = 5
            timeout_seconds = 3 * 60 * 60  # 3 hours safety timeout
            while elapsed < timeout_seconds:
                # Ensure we see latest job status across sessions
                try:
                    db.expire_all()
                except Exception:
                    pass
                # If job has been cancelled, stop monitoring
                job_check = db.query(Job).filter(Job.id == job_db_id).first()
                if job_check and job_check.status == JobStatus.CANCELLED.value:
                    logger.info(f"Monitor: job {job_db_id} marked cancelled; stopping monitor")
                    return
                # If rc file exists and has a code, finish
                res = await ssh.run(f"test -f {rc_path} && cat {rc_path} || echo none")
                content = res.stdout.strip()
                if content.isdigit():
                    rc = int(content)
                    # Attempt to fetch and store runner log
                    try:
                        # Check if log file exists and get its content
                        log_check = await ssh.run(f"ls -la {log_file_path} 2>/dev/null || echo 'LOG_FILE_NOT_FOUND'")
                        logger.info(f"Log file check for {log_file_path}: {log_check.stdout}")
                        
                        log_res = await ssh.run(f"test -f {log_file_path} && cat {log_file_path} || echo 'NO_LOG_CONTENT'")
                        job_log = log_res.stdout.strip() if log_res.stdout else ""
                        
                        logger.info(f"Log content length: {len(job_log)} characters")
                        
                        job = db.query(Job).filter(Job.id == job_db_id).first()
                        if job:
                            logger.info(f"DEBUG: About to copy logs for job {job.job_id} with type {job.job_type}")
                            # Use the new log copying functionality
                            from backend.automation.ssh_client import copy_splunk_job_logs
                            
                            logger.info(f"DEBUG: Calling copy_splunk_job_logs for {job.job_id}")
                            copy_successful = await copy_splunk_job_logs(host, job.job_id, job.job_type)
                            logger.info(f"DEBUG: copy_splunk_job_logs returned: {copy_successful}")
                            
                            if copy_successful:
                                logger.info(f"Successfully copied job logs for {job.job_id}")
                                
                                # Read the JSON log file to get stdout content
                                local_log_dir = Path(__file__).parent.parent / "logs" / datetime.now().strftime("%Y-%m")
                                local_log_file = local_log_dir / f"{job.job_id}.json"
                                
                                try:
                                    with open(local_log_file, 'r') as f:
                                        log_data = json.load(f)
                                        
                                    # Extract the main runner log content for stdout
                                    if "upgrade" in job.job_type.lower():
                                        main_log = log_data.get("logs", {}).get("upgrade_runner.log", "No upgrade runner log found")
                                    else:
                                        main_log = log_data.get("logs", {}).get("runner.log", "No runner log found")
                                    
                                    job.stdout = main_log
                                    
                                    # Update result metadata
                                    if job.result:
                                        job.result["local_log_path"] = str(local_log_file)
                                        job.result["log_data"] = log_data
                                    else:
                                        job.result = {
                                            "local_log_path": str(local_log_file),
                                            "log_data": log_data
                                        }
                                        
                                except Exception as e:
                                    logger.error(f"Failed to read collected log file: {str(e)}")
                                    job.stdout = f"Logs collected but failed to read: {str(e)}"
                            else:
                                logger.warning(f"Failed to copy job logs for {job.job_id}")
                                job.stdout = f"Failed to copy job logs from remote host"
                                
                            db.commit()
                        
                        # Cleanup all temp directories after capturing logs
                        await ssh.run("sudo rm -rf /tmp/siemply_splunk")
                        await ssh.run("sudo rm -rf /tmp/siemply_splunk_upgrade")
                        await ssh.run("sudo rm -rf /tmp/siemply_splunk_uf")
                        await ssh.run("sudo rm -rf /tmp/siemply_splunk_uf_upgrade")
                        await ssh.run("sudo rm -rf /tmp/siemply_sessions")
                        logger.info("Cleaned up remote temp directories")
                    except Exception as e:
                        logger.error(f"Failed to fetch logs or cleanup: {e}")
                    break
                # If tmux session no longer exists and no rc file, consider failure
                has = await ssh.run(f"tmux has-session -t {session_name} 2>/dev/null || echo missing")
                if "missing" in has.stdout:
                    # Session ended but no rc yet; infer success by checking install artifacts
                    job_now = db.query(Job).filter(Job.id == job_db_id).first()
                    install_dir = "/opt"
                    try:
                        params = job_now.parameters or {}
                        install_dir = params.get("install_dir", "/opt")
                    except Exception:
                        pass
                    # Check for appropriate Splunk binary based on job type
                    if job_now and job_now.job_type and "uf" in job_now.job_type.lower():
                        # UF jobs check for splunkforwarder
                        check = await ssh.run(f"test -x {install_dir.rstrip('/')}/splunkforwarder/bin/splunk && echo ok || echo no")
                    else:
                        # Enterprise jobs check for splunk
                        check = await ssh.run(f"test -x {install_dir.rstrip('/')}/splunk/bin/splunk && echo ok || echo no")
                    rc = 0 if "ok" in check.stdout else 1
                    
                    # Also copy logs in this completion path
                    if job_now:
                        logger.info(f"DEBUG: Session missing path - copying logs for job {job_now.job_id}")
                        try:
                            from backend.automation.ssh_client import copy_splunk_job_logs
                            host_obj = db.query(Host).filter(Host.id == host_id).first()
                            if host_obj:
                                copy_successful = await copy_splunk_job_logs(host_obj, job_now.job_id, job_now.job_type)
                                logger.info(f"DEBUG: Session missing path - copy result: {copy_successful}")
                                if copy_successful:
                                    logger.info(f"Successfully copied job logs for {job_now.job_id} (session missing path)")
                                    
                                    # Read the JSON log file to get stdout content
                                    local_log_dir = Path(__file__).parent.parent / "logs" / datetime.now().strftime("%Y-%m")
                                    local_log_file = local_log_dir / f"{job_now.job_id}.json"
                                    
                                    try:
                                        with open(local_log_file, 'r') as f:
                                            log_data = json.load(f)
                                            
                                        # Extract the main runner log content for stdout
                                        if "upgrade" in job_now.job_type.lower():
                                            main_log = log_data.get("logs", {}).get("upgrade_runner.log", "No upgrade runner log found")
                                        else:
                                            main_log = log_data.get("logs", {}).get("runner.log", "No runner log found")
                                        
                                        job_now.stdout = main_log
                                        
                                        # Update result metadata
                                        if job_now.result:
                                            job_now.result["local_log_path"] = str(local_log_file)
                                            job_now.result["log_data"] = log_data
                                        else:
                                            job_now.result = {
                                                "local_log_path": str(local_log_file),
                                                "log_data": log_data
                                            }
                                            
                                    except Exception as e:
                                        logger.error(f"Failed to read collected log file in session missing path: {str(e)}")
                                        job_now.stdout = f"Logs collected but failed to read: {str(e)}"
                                else:
                                    logger.warning(f"Failed to copy job logs for {job_now.job_id} (session missing path)")
                                    
                                db.commit()
                        except Exception as e:
                            logger.error(f"Error copying logs in session missing path: {str(e)}")
                    
                    # Cleanup temp directories after log copying (session missing path)
                    try:
                        await ssh.run("sudo rm -rf /tmp/siemply_splunk")
                        await ssh.run("sudo rm -rf /tmp/siemply_splunk_upgrade")
                        await ssh.run("sudo rm -rf /tmp/siemply_splunk_uf")
                        await ssh.run("sudo rm -rf /tmp/siemply_splunk_uf_upgrade")
                        await ssh.run("sudo rm -rf /tmp/siemply_sessions")
                        logger.info("Cleaned up remote temp directories (session missing path)")
                    except Exception as cleanup_e:
                        logger.error(f"Failed to cleanup temp directories in session missing path: {cleanup_e}")
                    break
                await asyncio.sleep(interval)
                elapsed += interval
            if rc is None:
                rc = 124  # timeout
                # Cleanup temp directories for timeout scenario
                try:
                    host_timeout = db.query(Host).filter(Host.id == host_id).first()
                    if host_timeout:
                        async with get_ssh_client(host_timeout) as ssh_timeout:
                            if ssh_timeout:
                                await ssh_timeout.run("sudo rm -rf /tmp/siemply_splunk")
                                await ssh_timeout.run("sudo rm -rf /tmp/siemply_splunk_upgrade")
                                await ssh_timeout.run("sudo rm -rf /tmp/siemply_splunk_uf")
                                await ssh_timeout.run("sudo rm -rf /tmp/siemply_splunk_uf_upgrade")
                                await ssh_timeout.run("sudo rm -rf /tmp/siemply_sessions")
                                logger.info("Cleaned up remote temp directories (timeout)")
                except Exception as timeout_cleanup_e:
                    logger.error(f"Failed to cleanup temp directories for timeout: {timeout_cleanup_e}")
        # Update job based on rc
        job = db.query(Job).filter(Job.id == job_db_id).first()
        if not job:
            return
        job.completed_at = datetime.utcnow()
        if rc == 0:
            job.status = JobStatus.COMPLETED.value
            job.result = {
                "success": True,
                "status_note": "Completed via tmux",
                "actual_status": "completed",
                "tmux_session": session_name,
            }
        else:
            job.status = JobStatus.FAILED.value
            job.result = {
                "success": False,
                "status_note": "Failed via tmux",
                "actual_status": "failed",
                "tmux_session": session_name,
                "return_code": rc,
            }
            
            # Also copy logs for failed jobs to help with debugging
            try:
                from backend.automation.ssh_client import copy_splunk_job_logs
                host = db.query(Host).filter(Host.id == host_id).first()
                if host:
                    copy_successful = await copy_splunk_job_logs(host, job.job_id, job.job_type)
                    if copy_successful:
                        logger.info(f"Successfully copied failure logs for job {job.job_id}")
                        # Update result with log path
                        local_log_dir = Path(__file__).parent.parent / "logs" / datetime.now().strftime("%Y-%m")
                        local_log_file = local_log_dir / f"{job.job_id}.json"
                        job.result["local_log_path"] = str(local_log_file)
                    
                    # Cleanup temp directories after copying failure logs
                    try:
                        async with get_ssh_client(host) as ssh_cleanup:
                            if ssh_cleanup:
                                await ssh_cleanup.run("sudo rm -rf /tmp/siemply_splunk")
                                await ssh_cleanup.run("sudo rm -rf /tmp/siemply_splunk_upgrade")
                                await ssh_cleanup.run("sudo rm -rf /tmp/siemply_splunk_uf")
                                await ssh_cleanup.run("sudo rm -rf /tmp/siemply_splunk_uf_upgrade")
                                await ssh_cleanup.run("sudo rm -rf /tmp/siemply_sessions")
                                logger.info("Cleaned up remote temp directories (failed job)")
                    except Exception as cleanup_e:
                        logger.error(f"Failed to cleanup temp directories for failed job: {cleanup_e}")
            except Exception as e:
                logger.error(f"Failed to copy failure logs for job {job.job_id}: {str(e)}")
        db.commit()
        logger.info(f"Job {job.job_id} finished via tmux with rc={rc}")
    except Exception as e:
        logger.error(f"Monitor error: {e}")
    finally:
        db.close()

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
    
    # Filter out jobs with null host_id to prevent validation errors
    query = query.filter(Job.host_id.isnot(None))
    
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
    job = db.query(Job).filter(Job.id == job_id).filter(Job.host_id.isnot(None)).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
@router.delete("/by-job-id/{unique_job_id}", response_model=Dict[str, Any])
async def delete_job_by_unique_id(unique_job_id: str, db: Session = Depends(get_db)):
    """Cancel a job using its unique job_id. If a tmux session is tracked, attempt to kill it."""
    job = db.query(Job).filter(Job.job_id == unique_job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Try to kill tmux session if present in result
    try:
        session_name = None
        rc_path = None
        if isinstance(job.result, dict):
            session_name = job.result.get("tmux_session") or job.result.get("session")
            rc_path = job.result.get("rc_path")
        host = db.query(Host).filter(Host.id == job.host_id).first()
        if host and session_name:
            from backend.automation.ssh_client import get_ssh_client
            async with get_ssh_client(host) as ssh:
                if ssh:
                    await ssh.run(f"tmux kill-session -t {session_name} 2>/dev/null || true")
                    if rc_path:
                        await ssh.run(f"sudo rm -f {rc_path} 2>/dev/null || true")
    except Exception as e:
        logger.warning(f"Error attempting to kill tmux session for job {unique_job_id}: {e}")

    # Mark as cancelled rather than hard-deleting
    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.utcnow()
    db.commit()
    return {"deleted": True, "job_id": unique_job_id, "status": job.status}


@router.post("/cleanup-duplicates", response_model=Dict[str, Any])
async def cleanup_duplicate_jobs(db: Session = Depends(get_db)):
    """Clean up duplicate jobs for the same host and type, keeping only the most recent one."""
    try:
        # Find duplicate jobs
        duplicate_jobs = db.query(Job).filter(
            Job.job_type.in_([JobType.SPLUNK_ENT_INSTALL.value, JobType.SPLUNK_UF_INSTALL.value]),
            Job.status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value])
        ).all()
        
        # Group by host_id and job_type
        job_groups = {}
        for job in duplicate_jobs:
            key = (job.host_id, job.job_type)
            if key not in job_groups:
                job_groups[key] = []
            job_groups[key].append(job)
        
        cleaned_count = 0
        for (host_id, job_type), jobs in job_groups.items():
            if len(jobs) > 1:
                # Sort by created_at, keep the most recent one
                jobs.sort(key=lambda x: x.created_at, reverse=True)
                jobs_to_cancel = jobs[1:]  # Cancel all but the most recent
                
                for job in jobs_to_cancel:
                    job.status = JobStatus.CANCELLED.value
                    job.completed_at = datetime.utcnow()
                    cleaned_count += 1
                
                logger.info(f"Cleaned up {len(jobs_to_cancel)} duplicate jobs for host {host_id}, type {job_type}")
        
        if cleaned_count > 0:
            db.commit()
            return {
                "success": True,
                "message": f"Cleaned up {cleaned_count} duplicate jobs",
                "cleaned_count": cleaned_count
            }
        else:
            return {
                "success": True,
                "message": "No duplicate jobs found",
                "cleaned_count": 0
            }
            
    except Exception as e:
        logger.error(f"Failed to cleanup duplicate jobs: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/by-job-id/{unique_job_id}", response_model=JobResponse)
async def get_job_by_unique_id(unique_job_id: str, db: Session = Depends(get_db)):
    """
    Get a job by unique job ID
    """
    job = db.query(Job).filter(Job.job_id == unique_job_id).filter(Job.host_id.isnot(None)).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/live-logs/{unique_job_id}", response_model=dict)
async def get_live_logs(
    unique_job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get logs from local logs/ folder or job stdout
    """
    job = db.query(Job).filter(Job.job_id == unique_job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Only try to fetch logs if job is running or recently completed
    if job.status not in [JobStatus.RUNNING.value, JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
        return {"logs": "", "status": job.status, "message": "Job not in a state that produces logs"}
    
    try:
        # First, try to read from local logs/ folder
        logs_dir = Path(__file__).parent.parent / "logs"
        
        # Check current month and previous month for the log file
        current_month = datetime.now().strftime("%Y-%m")
        previous_month_date = datetime.now().replace(day=1) - timedelta(days=1)
        previous_month = previous_month_date.strftime("%Y-%m")
        
        local_log_file = None
        for month in [current_month, previous_month]:
            potential_file = logs_dir / month / f"{unique_job_id}.json"
            if potential_file.exists():
                local_log_file = potential_file
                break
        
        # For completed or failed jobs, the local log file is the source of truth.
        if job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
            if local_log_file:
                with open(local_log_file, 'r') as f:
                    log_content = f.read()
                    # Attempt to parse as JSON, but fall back to raw content
                    try:
                        log_data = json.loads(log_content)
                        log_output = log_data.get("logs", "Could not parse logs from JSON.")
                    except json.JSONDecodeError:
                        log_output = log_content

                    return {
                        "logs": log_output,
                        "status": job.status,
                        "source": "local_file"
                    }
            # If local file is missing for a completed job, check stdout as a backup
            elif job.stdout:
                return {"logs": job.stdout, "status": job.status, "source": "job_stdout_fallback"}
            else:
                return {"logs": "Log file not found for this completed job.", "status": job.status, "source": "none"}
        
        # For running jobs, stream from the remote host
        if job.status == JobStatus.RUNNING.value and job.host:
            try:
                async with get_ssh_client(job.host) as ssh:
                    if ssh:
                        # Determine log file path based on job type
                        if job.job_type == JobType.SPLUNK_ENT_UPGRADE.value:
                            log_file_path = "/tmp/siemply_splunk_upgrade/upgrade_runner.log"
                        elif job.job_type == JobType.SPLUNK_UF_INSTALL.value:
                            log_file_path = "/tmp/siemply_splunk_uf/runner.log"
                        elif job.job_type == JobType.SPLUNK_UF_UPGRADE.value:
                            log_file_path = "/tmp/siemply_splunk_uf_upgrade/upgrade_runner.log"
                        else:
                            # Default to Enterprise install path
                            log_file_path = "/tmp/siemply_splunk/runner.log"
                        
                        log_res = await ssh.run(f"test -f {log_file_path} && cat {log_file_path} || echo 'Waiting for logs...'")
                        return {
                            "logs": log_res.stdout,
                            "status": job.status,
                            "source": "remote_stream"
                        }
            except Exception as e:
                logger.warning(f"Failed to fetch remote logs for running job {unique_job_id}: {e}")
                return {"logs": "Connecting to host to fetch logs...", "status": job.status, "source": "remote_error"}
        
        return {"logs": "No logs available for this job state.", "status": job.status, "source": "none"}
        
    except Exception as e:
        logger.error(f"Failed to fetch logs for job {unique_job_id}: {e}")
        return {"logs": "", "status": job.status, "error": str(e)}


async def _run_job(job_id: int, background_tasks: BackgroundTasks, db_session: Session = None):
    """Run a job in the background"""
    # Create a new database session for the background task
    from backend.models import get_db
    from contextlib import asynccontextmanager
    
    # Use the provided session if available, otherwise create a new one
    if db_session is None:
        db = next(get_db())
    else:
        db = db_session
    
    try:
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
            
            logger.info(f"Processing job type: '{job.job_type}' for job {job.job_id}")
            logger.info(f"JobType.SPLUNK_ENT_INSTALL.value = '{JobType.SPLUNK_ENT_INSTALL.value}'")
            logger.info(f"JobType.SPLUNK_ENT_UPGRADE.value = '{JobType.SPLUNK_ENT_UPGRADE.value}'")
            
            if job.job_type == JobType.SPLUNK_UF_INSTALL.value:
                logger.info("Executing Splunk UF install job with tmux")
                result = await install_splunk_uf_tmux(host, job.parameters, job)
                
                # If tmux session started successfully, begin monitoring
                if result.get("success") and "session_name" in result:
                    job.status = JobStatus.RUNNING.value
                    db.commit()
                    
                    # Determine log file path for UF install
                    log_file_path = "/tmp/siemply_splunk_uf/runner.log"
                    
                    # Use the background_tasks object to run the monitor reliably
                    rc_path = f"/tmp/siemply_sessions/{result['session_name']}.rc"
                    background_tasks.add_task(
                        _monitor_tmux_session,
                        job_db_id=job.id,
                        host_id=host.id,
                        session_name=result["session_name"],
                        rc_path=rc_path,
                        log_file_path=log_file_path
                    )
                    
                    logger.info(f"Scheduled tmux monitor for job {job.job_id} with session {result['session_name']}")
                    return {"message": f"Job {job.job_id} started successfully in tmux session {result['session_name']}"}
                
                # If tmux failed, try direct installation as fallback
                logger.warning("Tmux installation failed, trying direct installation as fallback")
                try:
                    from backend.automation.splunk.splunk_installer import install_splunk_uf
                    logger.info("Executing Splunk UF install job directly (fallback)")
                    result = await install_splunk_uf(host, job.parameters)
                    
                    if result.get("success"):
                        job.status = JobStatus.COMPLETED.value
                        job.result = {
                            "success": True,
                            "status_note": "Completed via direct installation (tmux fallback)",
                            "actual_status": "completed",
                            "fallback_method": "direct_installation"
                        }
                        logger.info(f"Job {job.job_id} completed successfully via direct installation fallback")
                    else:
                        job.status = JobStatus.FAILED.value
                        job.result = {
                            "success": False,
                            "status_note": "Failed via direct installation fallback",
                            "actual_status": "failed",
                            "fallback_method": "direct_installation",
                            "error": result.get("message", "Unknown error")
                        }
                        logger.error(f"Job {job.job_id} failed via direct installation fallback: {result.get('message')}")
                    
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Direct installation fallback also failed for job {job.job_id}: {str(fallback_error)}")
                    job.status = JobStatus.FAILED.value
                    job.result = {
                        "success": False,
                        "status_note": "Both tmux and direct installation failed",
                        "actual_status": "failed",
                        "tmux_error": "Tmux installation failed",
                        "fallback_error": str(fallback_error)
                    }
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    return {"success": False, "message": f"Both tmux and direct installation failed: {str(fallback_error)}"}
            
            elif job.job_type == JobType.SPLUNK_UF_UPGRADE.value:
                logger.info("Executing Splunk UF upgrade job with tmux")
                result = await upgrade_splunk_uf_tmux(host, job.parameters, job)
                
                # If tmux session started successfully, begin monitoring
                if result.get("success") and "session_name" in result:
                    job.status = JobStatus.RUNNING.value
                    db.commit()
                    
                    # Determine log file path for UF upgrade
                    log_file_path = "/tmp/siemply_splunk_uf_upgrade/upgrade_runner.log"
                    
                    # Use the background_tasks object to run the monitor reliably
                    rc_path = f"/tmp/siemply_sessions/{result['session_name']}.rc"
                    background_tasks.add_task(
                        _monitor_tmux_session,
                        job_db_id=job.id,
                        host_id=host.id,
                        session_name=result["session_name"],
                        rc_path=rc_path,
                        log_file_path=log_file_path
                    )
                    
                    logger.info(f"Scheduled tmux monitor for job {job.job_id} with session {result['session_name']}")
                    return {"message": f"Job {job.job_id} started successfully in tmux session {result['session_name']}"}
                
                # If tmux failed, try direct upgrade as fallback
                logger.warning("Tmux upgrade failed, trying direct upgrade as fallback")
                try:
                    # For upgrade fallback, we need to create a proper upgrade function
                    # Since there's no direct upgrade function, we'll create a simple upgrade logic
                    logger.info("Executing Splunk UF upgrade job directly (fallback)")
                    
                    # Import the necessary functions for upgrade
                    from backend.automation.splunk.splunk_installer import get_package_download_url
                    from backend.automation.ssh_client import get_ssh_client
                    
                    # Get download URL for the target version
                    download_url = get_package_download_url(job.parameters.get("version"), job.parameters.get("architecture", "x86_64"), "splunk_uf")
                    if not download_url:
                        raise Exception(f"No download URL available for version {job.parameters.get('version')}")
                    
                    # Perform direct upgrade
                    async with get_ssh_client(host) as ssh:
                        if not ssh:
                            raise Exception("Could not establish SSH connection")
                        
                        # Check if UF is installed
                        check_cmd = f"test -d {job.parameters.get('install_dir', '/opt')}/splunkforwarder && echo 'exists' || echo 'not exists'"
                        check_result = await ssh.run(check_cmd)
                        if check_result.stdout.strip() != "exists":
                            raise Exception("Splunk UF is not installed - cannot upgrade")
                        
                        # Stop Splunk UF
                        await ssh.run(f"{job.parameters.get('install_dir', '/opt')}/splunkforwarder/bin/splunk stop --answer-yes --no-prompt 2>&1 || true")
                        await asyncio.sleep(5)
                        
                        # Download new version
                        await ssh.run("sudo mkdir -p /tmp/splunk_uf_upgrade")
                        download_cmd = f"cd /tmp/splunk_uf_upgrade && sudo curl -L -o splunkforwarder.tgz '{download_url}'"
                        dl_result = await ssh.run(download_cmd)
                        if dl_result.returncode != 0:
                            raise Exception(f"Failed to download new version: {dl_result.stderr}")
                        
                        # Backup current config
                        backup_dir = f"{job.parameters.get('install_dir', '/opt')}/splunkforwarder/etc.backup.{int(time.time())}"
                        await ssh.run(f"sudo cp -r {job.parameters.get('install_dir', '/opt')}/splunkforwarder/etc {backup_dir}")
                        
                        # Extract new version
                        extract_cmd = f"cd {job.parameters.get('install_dir', '/opt')} && sudo tar -xzf /tmp/splunk_uf_upgrade/splunkforwarder.tgz"
                        extract_result = await ssh.run(extract_cmd)
                        if extract_result.returncode != 0:
                            raise Exception(f"Failed to extract new version: {extract_result.stderr}")
                        
                        # Restore config
                        await ssh.run(f"sudo rm -rf {job.parameters.get('install_dir', '/opt')}/splunkforwarder/etc")
                        await ssh.run(f"sudo mv {backup_dir} {job.parameters.get('install_dir', '/opt')}/splunkforwarder/etc")
                        
                        # Set ownership
                        await ssh.run(f"sudo chown -R {job.parameters.get('user', 'splunk')}:{job.parameters.get('group', 'splunk')} {job.parameters.get('install_dir', '/opt')}/splunkforwarder")
                        
                        # Start upgraded UF
                        start_cmd = f"sudo -u {job.parameters.get('user', 'splunk')} {job.parameters.get('install_dir', '/opt')}/splunkforwarder/bin/splunk start --accept-license --answer-yes --no-prompt"
                        start_result = await ssh.run(start_cmd)
                        if start_result.returncode != 0:
                            raise Exception(f"Failed to start upgraded UF: {start_result.stderr}")
                        
                        # Cleanup
                        await ssh.run("sudo rm -rf /tmp/splunk_uf_upgrade")
                    
                    result = {"success": True, "message": f"Successfully upgraded Splunk UF to version {job.parameters.get('version')}"}
                    
                    if result.get("success"):
                        job.status = JobStatus.COMPLETED.value
                        job.result = {
                            "success": True,
                            "status_note": "Completed via direct upgrade (tmux fallback)",
                            "actual_status": "completed",
                            "fallback_method": "direct_upgrade"
                        }
                        logger.info(f"Job {job.job_id} completed successfully via direct upgrade fallback")
                    else:
                        job.status = JobStatus.FAILED.value
                        job.result = {
                            "success": False,
                            "status_note": "Failed via direct upgrade fallback",
                            "actual_status": "failed",
                            "fallback_method": "direct_upgrade",
                            "error": result.get("message", "Unknown error")
                        }
                        logger.error(f"Job {job.job_id} failed via direct upgrade fallback: {result.get('message')}")
                    
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Direct upgrade fallback also failed for job {job.job_id}: {str(fallback_error)}")
                    job.status = JobStatus.FAILED.value
                    job.result = {
                        "success": False,
                        "status_note": "Both tmux and direct upgrade failed",
                        "actual_status": "failed",
                        "tmux_error": "Tmux upgrade failed",
                        "fallback_error": str(fallback_error)
                    }
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    return {"success": False, "message": f"Both tmux and direct upgrade failed: {str(fallback_error)}"}
                
            
            elif job.job_type == JobType.SPLUNK_ENT_INSTALL.value:
                logger.info("Executing Splunk Enterprise install job")
                result = await install_splunk_enterprise(host, job.parameters)
            elif job.job_type == JobType.SPLUNK_ENT_UPGRADE.value:
                logger.info("Executing Splunk Enterprise upgrade job")
                result = await upgrade_splunk_enterprise(host, job.parameters)
            
            elif job.job_type == JobType.CRIBL_WORKER_INSTALL.value:
                result = await install_cribl_worker(host, job.parameters)
            
            elif job.job_type == JobType.CRIBL_LEADER_INSTALL.value:
                result = await install_cribl_leader(host, job.parameters)
            
            elif job.job_type == JobType.SYSLOG_INSTALL.value:
                result = await install_syslog_ng(host, job.parameters)
            
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
                
                # If job started a tmux session, hand off monitoring and keep status running
                if result.get("started_in_tmux") and result.get("tmux_session"):
                    job.status = JobStatus.RUNNING.value
                    db.commit()
                    
                    # Determine log file path based on job type
                    log_file_path = "/tmp/siemply_splunk/runner.log"
                    if job.job_type == JobType.SPLUNK_ENT_UPGRADE.value:
                        log_file_path = "/tmp/siemply_splunk_upgrade/upgrade_runner.log"
                    
                    # Use the background_tasks object to run the monitor reliably
                    background_tasks.add_task(
                        _monitor_tmux_session,
                        job_db_id=job.id,
                        host_id=job.host_id,
                        session_name=result.get("tmux_session"),
                        rc_path=result.get("rc_path"),
                        log_file_path=log_file_path
                    )
                    logger.info(f"Scheduled tmux monitor for job {job.job_id} with session {result.get('tmux_session')}")
                    return
                
                # Set status based on result details for non-tmux flows
                if result.get("success"):
                    job.status = JobStatus.COMPLETED.value
                    
                    # Add special handling for skipped installations
                    if result.get("skipped"):
                        # Update the result message to be clearer about skipped status
                        if job.result:
                            job.result["status_note"] = "Software already installed - no changes made"
                            job.result["actual_status"] = "skipped"
                        else:
                            job.result = {
                                "status_note": "Software already installed - no changes made",
                                "actual_status": "skipped"
                            }
                        # Update stdout to include skipped information
                        if not job.stdout or job.stdout.strip() == "":
                            job.stdout = f"Installation skipped: {result.get('message', 'Software already installed')}"
                        else:
                            job.stdout = f"Installation skipped: {result.get('message', 'Software already installed')}\n\n{job.stdout}"
                            
                else:
                    # Check if this is actually a "skipped" scenario (software already installed)
                    error_message = result.get("message", "").lower()
                    if "already installed" in error_message or "already exists" in error_message:
                        # Treat as successful but skipped
                        job.status = JobStatus.COMPLETED.value
                        job.result = {
                            "success": True,
                            "status_note": "Software already installed - no changes made",
                            "actual_status": "skipped",
                            "message": result.get("message", "Software already installed")
                        }
                        # Update stdout to include skipped information
                        job.stdout = f"Installation skipped: {result.get('message', 'Software already installed')}"
                        # Clear stderr since this isn't really an error
                        job.stderr = ""
                    else:
                        # This is a real failure
                        job.status = JobStatus.FAILED.value
                        
                        # Ensure error details are captured properly
                        if not job.stderr and result.get("message"):
                            job.stderr = result.get("message", "Installation failed")
                        
                        # Add failure details to result
                        if job.result:
                            job.result["status_note"] = "Installation failed"
                            job.result["actual_status"] = "failed"
                        else:
                            job.result = {
                                "status_note": "Installation failed", 
                                "actual_status": "failed"
                            }
                
                # Mark job as completed and commit
                job.completed_at = datetime.utcnow()
                db.commit()
                logger.info(f"Job {job.job_id} completed with status: {job.status}")
        
        except Exception as e:
            # Update job with error
            job.status = JobStatus.FAILED.value
            job.stderr = f"Error executing job: {str(e)}"
            job.result = {
                "success": False,
                "status_note": "Job execution failed due to an error",
                "actual_status": "failed",
                "error": str(e)
            }
            job.completed_at = datetime.utcnow()
            db.commit()
            logger.error(f"Job {job.job_id} failed with exception: {str(e)}")
    
    except Exception as e:
        # Update job with error
        job.status = JobStatus.FAILED.value
        job.stderr = f"Error executing job: {str(e)}"
        job.result = {
            "success": False,
            "status_note": "Job execution failed due to an error",
            "actual_status": "failed",
            "error": str(e)
        }
        job.completed_at = datetime.utcnow()
        db.commit()
        logger.error(f"Job {job.job_id} failed with exception: {str(e)}")
        
    finally:
        # Close the database session if we created it
        if db_session is None:
            db.close()


@router.post("/install/splunk-uf", response_model=JobResponse)
async def create_splunk_uf_install_job(
    parameters: Dict[str, Any],
    host_id: Optional[int] = None,
    server_class_name: Optional[str] = None,
    is_dry_run: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a job to install Splunk Universal Forwarder
    """
    # Log received parameters
    logger.info(f"Received Splunk UF install request: host_id={host_id}, server_class_name={server_class_name}, parameters={parameters}, is_dry_run={is_dry_run}")
    
    # Validate that either host_id or server_class_name is provided
    if host_id is None and server_class_name is None:
        raise HTTPException(status_code=422, detail="Either host_id or server_class_name must be provided")
    
    if host_id is not None and server_class_name is not None:
        raise HTTPException(status_code=422, detail="Only one of host_id or server_class_name should be provided")
    
    # Handle server class installation
    if server_class_name is not None:
        from backend.services.serverclass_service import ServerClassService
        
        server_class_service = ServerClassService()
        server_class = server_class_service.get_server_class(server_class_name)
        
        if server_class is None:
            logger.error(f"Server class not found: {server_class_name}")
            raise HTTPException(status_code=404, detail="Server class not found")
        
        if not server_class.get("is_active", True):
            logger.error(f"Server class is inactive: {server_class_name}")
            raise HTTPException(status_code=400, detail="Server class is inactive")
        
        host_ids = server_class.get("host_ids", [])
        if not host_ids:
            logger.error(f"Server class has no hosts: {server_class_name}")
            raise HTTPException(status_code=400, detail="Server class has no hosts")
        
        # Create jobs for all hosts in the server class
        jobs = []
        for host_id in host_ids:
            host = db.query(Host).filter(Host.id == host_id).first()
            if host is None:
                logger.warning(f"Host not found: {host_id}")
                continue
            
            # Create job for this host
            job = Job(
                job_id=f"splunk-uf-{uuid.uuid4()}",
                host_id=host_id,
                job_type=JobType.SPLUNK_UF_INSTALL.value,
                status=JobStatus.PENDING.value,
                is_dry_run=is_dry_run,
                parameters=parameters
            )
            
            db.add(job)
            jobs.append(job)
        
        db.commit()
        
        # Start background tasks for all jobs
        for job in jobs:
            background_tasks.add_task(_run_job, job.id, background_tasks, None)
            logger.info(f"Created Splunk UF install job for host {job.host_id}: {job.job_id}")
        
        # Return the first job as the main response
        return jobs[0] if jobs else None
    
    # Handle single host installation
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        logger.error(f"Host not found: {host_id}")
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Check for existing pending or running jobs for the same host and type
    existing_job = db.query(Job).filter(
        Job.host_id == host_id,
        Job.job_type == JobType.SPLUNK_UF_INSTALL.value,
        Job.status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value])
    ).first()
    
    if existing_job:
        logger.warning(f"Duplicate UF install job request for host {host_id}: existing job {existing_job.job_id} with status {existing_job.status}")
        raise HTTPException(
            status_code=409, 
            detail=f"UF install job already exists for this host: {existing_job.job_id} (status: {existing_job.status})"
        )
    
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
    background_tasks.add_task(_run_job, job.id, background_tasks, None)
    logger.info(f"Created Splunk UF install job: {job.job_id}")
    return job


@router.post("/upgrade/splunk-uf", response_model=JobResponse)
async def create_splunk_uf_upgrade_job(
    parameters: Dict[str, Any],
    host_id: Optional[int] = None,
    server_class_name: Optional[str] = None,
    is_dry_run: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a job to upgrade Splunk Universal Forwarder
    """
    # Log received parameters
    logger.info(f"Received Splunk UF upgrade request: host_id={host_id}, server_class_name={server_class_name}, parameters={parameters}, is_dry_run={is_dry_run}")
    
    # Validate that either host_id or server_class_name is provided
    if host_id is None and server_class_name is None:
        raise HTTPException(status_code=422, detail="Either host_id or server_class_name must be provided")
    
    if host_id is not None and server_class_name is not None:
        raise HTTPException(status_code=422, detail="Only one of host_id or server_class_name should be provided")
    
    # Handle server class upgrade
    if server_class_name is not None:
        from backend.services.serverclass_service import ServerClassService
        
        server_class_service = ServerClassService()
        server_class = server_class_service.get_server_class(server_class_name)
        
        if server_class is None:
            logger.error(f"Server class not found: {server_class_name}")
            raise HTTPException(status_code=404, detail="Server class not found")
        
        if not server_class.get("is_active", True):
            logger.error(f"Server class is inactive: {server_class_name}")
            raise HTTPException(status_code=400, detail="Server class is inactive")
        
        host_ids = server_class.get("host_ids", [])
        if not host_ids:
            logger.error(f"Server class has no hosts: {server_class_name}")
            raise HTTPException(status_code=400, detail="Server class has no hosts")
        
        # Create jobs for all hosts in the server class
        jobs = []
        for host_id in host_ids:
            host = db.query(Host).filter(Host.id == host_id).first()
            if host is None:
                logger.warning(f"Host not found: {host_id}")
                continue
            
            # Create job for this host
            job = Job(
                job_id=f"splunk-uf-upgrade-{uuid.uuid4()}",
                host_id=host_id,
                job_type=JobType.SPLUNK_UF_UPGRADE.value,
                status=JobStatus.PENDING.value,
                is_dry_run=is_dry_run,
                parameters=parameters
            )
            
            db.add(job)
            jobs.append(job)
        
        db.commit()
        
        # Start background tasks for all jobs
        for job in jobs:
            background_tasks.add_task(_run_job, job.id, background_tasks, None)
            logger.info(f"Created Splunk UF upgrade job for host {job.host_id}: {job.job_id}")
        
        # Return the first job as the main response
        return jobs[0] if jobs else None
    
    # Handle single host upgrade
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
        job_id=f"splunk-uf-upgrade-{uuid.uuid4()}",
        host_id=host_id,
        job_type=JobType.SPLUNK_UF_UPGRADE.value,
        status=JobStatus.PENDING.value,
        is_dry_run=is_dry_run,
        parameters=parameters
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Run job in background
    background_tasks.add_task(_run_job, job.id, background_tasks, None)
    logger.info(f"Created Splunk UF upgrade job: {job.job_id}")
    return job


@router.post("/install/splunk-enterprise", response_model=JobResponse)
async def create_splunk_enterprise_install_job(
    parameters: Dict[str, Any],
    host_id: Optional[int] = None,
    server_class_name: Optional[str] = None,
    is_dry_run: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a job to install Splunk Enterprise
    Supports single host (host_id) or server class (server_class_name) similar to UF flow.
    """
    logger.info(
        f"Received Splunk Enterprise install request: host_id={host_id}, server_class_name={server_class_name}, parameters={parameters}, is_dry_run={is_dry_run}"
    )

    # Validate that either host_id or server_class_name is provided (but not both)
    if host_id is None and server_class_name is None:
        raise HTTPException(status_code=422, detail="Either host_id or server_class_name must be provided")
    if host_id is not None and server_class_name is not None:
        raise HTTPException(status_code=422, detail="Only one of host_id or server_class_name should be provided")

    # Validate required parameters
    required_params = ["version", "user", "admin_password"]
    missing_params = [param for param in required_params if param not in parameters]
    if missing_params:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required parameters: {', '.join(missing_params)}. Received: {parameters}",
        )

    # Check for existing pending or running jobs for the same host and type
    if host_id is not None:
        existing_job = db.query(Job).filter(
            Job.host_id == host_id,
            Job.job_type == JobType.SPLUNK_ENT_INSTALL.value,
            Job.status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value])
        ).first()
        
        if existing_job:
            logger.warning(f"Duplicate job request for host {host_id}: existing job {existing_job.job_id} with status {existing_job.status}")
            raise HTTPException(
                status_code=409, 
                detail=f"Job already exists for this host: {existing_job.job_id} (status: {existing_job.status})"
            )

    # Handle server class installation
    if server_class_name is not None:
        from backend.services.serverclass_service import ServerClassService

        server_class_service = ServerClassService()
        server_class = server_class_service.get_server_class(server_class_name)

        if server_class is None:
            logger.error(f"Server class not found: {server_class_name}")
            raise HTTPException(status_code=404, detail="Server class not found")

        if not server_class.get("is_active", True):
            logger.error(f"Server class is inactive: {server_class_name}")
            raise HTTPException(status_code=400, detail="Server class is inactive")

        host_ids = server_class.get("host_ids", [])
        if not host_ids:
            logger.error(f"Server class has no hosts: {server_class_name}")
            raise HTTPException(status_code=400, detail="Server class has no hosts")

        jobs = []
        for sc_host_id in host_ids:
            host = db.query(Host).filter(Host.id == sc_host_id).first()
            if host is None:
                logger.warning(f"Host not found: {sc_host_id}")
                continue

            job = Job(
                job_id=f"splunk-ent-{uuid.uuid4()}",
                host_id=sc_host_id,
                job_type=JobType.SPLUNK_ENT_INSTALL.value,
                status=JobStatus.PENDING.value,
                is_dry_run=is_dry_run,
                parameters=parameters,
            )
            db.add(job)
            jobs.append(job)

        db.commit()
        for job in jobs:
            background_tasks.add_task(_run_job, job.id, background_tasks, None)
            logger.info(f"Created Splunk Enterprise install job for host {job.host_id}: {job.job_id}")
        return jobs[0] if jobs else None

    # Handle single host installation
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        logger.error(f"Host not found: {host_id}")
        raise HTTPException(status_code=404, detail="Host not found")

    job = Job(
        job_id=f"splunk-ent-{uuid.uuid4()}",
        host_id=host_id,
        job_type=JobType.SPLUNK_ENT_INSTALL.value,
        status=JobStatus.PENDING.value,
        is_dry_run=is_dry_run,
        parameters=parameters,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_job, job.id, background_tasks, None)
    logger.info(f"Created Splunk Enterprise install job: {job.job_id}")
    return job


@router.post("/upgrade/splunk-enterprise", response_model=JobResponse)
async def create_splunk_enterprise_upgrade_job(
    parameters: Dict[str, Any],
    host_id: Optional[int] = None,
    server_class_name: Optional[str] = None,
    is_dry_run: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a job to upgrade Splunk Enterprise (single host or server class)
    """
    logger.info(
        f"Received Splunk Enterprise upgrade request: host_id={host_id}, server_class_name={server_class_name}, parameters={parameters}, is_dry_run={is_dry_run}"
    )
    if host_id is None and server_class_name is None:
        raise HTTPException(status_code=422, detail="Either host_id or server_class_name must be provided")
    if host_id is not None and server_class_name is not None:
        raise HTTPException(status_code=422, detail="Only one of host_id or server_class_name should be provided")

    required_params = ["version", "user"]
    missing = [p for p in required_params if p not in parameters]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required parameters: {', '.join(missing)}")

    if server_class_name is not None:
        from backend.services.serverclass_service import ServerClassService
        scs = ServerClassService()
        server_class = scs.get_server_class(server_class_name)
        if not server_class:
            raise HTTPException(status_code=404, detail="Server class not found")
        host_ids = server_class.get("host_ids", [])
        if not host_ids:
            raise HTTPException(status_code=400, detail="Server class has no hosts")
        jobs = []
        for hid in host_ids:
            host = db.query(Host).filter(Host.id == hid).first()
            if not host:
                continue
            job = Job(
                job_id=f"splunk-ent-upgrade-{uuid.uuid4()}",
                host_id=hid,
                job_type=JobType.SPLUNK_ENT_UPGRADE.value,
                status=JobStatus.PENDING.value,
                is_dry_run=is_dry_run,
                parameters=parameters,
            )
            db.add(job)
            jobs.append(job)
        db.commit()
        for job in jobs:
            background_tasks.add_task(_run_job, job.id, background_tasks, None)
        return jobs[0] if jobs else None

    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    job = Job(
        job_id=f"splunk-ent-upgrade-{uuid.uuid4()}",
        host_id=host_id,
        job_type=JobType.SPLUNK_ENT_UPGRADE.value,
        status=JobStatus.PENDING.value,
        is_dry_run=is_dry_run,
        parameters=parameters,
    )
    logger.info(f"Creating upgrade job with job_type: '{JobType.SPLUNK_ENT_UPGRADE.value}'")
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(_run_job, job.id, background_tasks, None)
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
    background_tasks.add_task(_run_job, job.id, background_tasks, None)
    
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
    background_tasks.add_task(_run_job, job.id, background_tasks, None)
    
    return job


@router.post("/install/syslog", response_model=JobResponse)
async def create_syslog_install_job(
    host_id: int,
    parameters: Dict[str, Any],
    is_dry_run: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a job to install syslog-ng
    """
    # Log received parameters
    logger.info(f"Received syslog install request: host_id={host_id}, parameters={parameters}, is_dry_run={is_dry_run}")
    
    # Check if host exists
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        logger.error(f"Host not found: {host_id}")
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Create job
    job = Job(
        job_id=f"syslog-{uuid.uuid4()}",
        host_id=host_id,
        job_type=JobType.SYSLOG_INSTALL.value,
        status=JobStatus.PENDING.value,
        is_dry_run=is_dry_run,
        parameters=parameters
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Run job in background
    background_tasks.add_task(_run_job, job.id, background_tasks, None)
    
    logger.info(f"Created syslog install job: {job.job_id}")
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
    background_tasks.add_task(_run_job, job.id, background_tasks, None)
    
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


@router.post("/test-background", response_model=JobResponse)
async def test_background_job(
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Test endpoint to verify background job execution
    """
    # Create a test job
    job = Job(
        job_id=f"test-{uuid.uuid4()}",
        host_id=1,  # Use first available host
        job_type=JobType.CUSTOM_COMMAND.value,
        status=JobStatus.PENDING.value,
        is_dry_run=True,
        parameters={"command": "sleep 10 && echo 'Test completed'", "user": "root"}
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Add to background tasks
    background_tasks.add_task(_run_job, job.id, background_tasks, None)
    
    logger.info(f"Created test background job: {job.job_id}")
    return job 