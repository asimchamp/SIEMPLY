"""
Runbook Service
Handles runbook YAML parsing, validation, and execution logic
"""
import yaml
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session

from backend.models import (
    Runbook, RunbookExecution, RunbookTaskExecution,
    RunbookStatus, TaskStatus, Host, Job, JobType, JobStatus
)
from backend.services.serverclass_service import ServerClassService
from backend.automation.utils import run_command_with_timeout
from backend.automation.ssh_client import create_ssh_client_from_host

logger = logging.getLogger(__name__)

class RunbookService:
    """Service for managing runbooks and their execution"""
    
    def __init__(self, db: Session):
        self.db = db
        self.serverclass_service = ServerClassService()
    
    def parse_yaml_content(self, yaml_content: str) -> Dict[str, Any]:
        """Parse YAML content and validate structure"""
        try:
            data = yaml.safe_load(yaml_content)
            if not data:
                raise ValueError("YAML content is empty")
            
            # Validate basic structure
            if not isinstance(data, dict):
                raise ValueError("YAML must contain a dictionary at the root level")
            
            # Check for automation_playbook key
            if "automation_playbook" not in data:
                raise ValueError("YAML must contain 'automation_playbook' key")
            
            playbook = data["automation_playbook"]
            if not isinstance(playbook, list):
                raise ValueError("automation_playbook must be a list of jobs")
            
            # Validate each job
            for job in playbook:
                self._validate_job(job)
            
            return data
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing YAML: {str(e)}")
    
    def _validate_job(self, job: Dict[str, Any]) -> None:
        """Validate a job definition"""
        if not isinstance(job, dict):
            raise ValueError("Each job must be a dictionary")
        
        if "job" not in job:
            raise ValueError("Each job must contain a 'job' key")
        
        job_data = job["job"]
        if not isinstance(job_data, dict):
            raise ValueError("Job data must be a dictionary")
        
        # Required fields
        required_fields = ["id", "name", "targets", "tasks"]
        for field in required_fields:
            if field not in job_data:
                raise ValueError(f"Job must contain '{field}' field")
        
        # Validate targets
        targets = job_data["targets"]
        if not isinstance(targets, dict):
            raise ValueError("Job targets must be a dictionary")
        
        if "server_class" not in targets and "hosts" not in targets:
            raise ValueError("Job targets must contain either 'server_class' or 'hosts'")
        
        # Validate tasks
        tasks = job_data["tasks"]
        if not isinstance(tasks, list):
            raise ValueError("Job tasks must be a list")
        
        for task in tasks:
            self._validate_task(task)
    
    def _validate_task(self, task: Dict[str, Any]) -> None:
        """Validate a task definition"""
        if not isinstance(task, dict):
            raise ValueError("Each task must be a dictionary")
        
        if "name" not in task:
            raise ValueError("Each task must contain a 'name' field")
        
        # Check for at least one task type
        task_types = ["service", "command", "script", "git", "package", "debug", "reboot"]
        found_type = False
        
        for task_type in task_types:
            if task_type in task:
                found_type = True
                break
        
        if not found_type:
            raise ValueError(f"Task must contain one of: {', '.join(task_types)}")
    
    def get_target_hosts(self, targets: Dict[str, Any]) -> List[Host]:
        """Get list of hosts based on targets configuration"""
        hosts = []
        
        if "server_class" in targets:
            server_class_name = targets["server_class"]
            server_class = self.serverclass_service.get_server_class(server_class_name)
            
            if not server_class:
                raise ValueError(f"Server class '{server_class_name}' not found")
            
            if not server_class.get("is_active", True):
                raise ValueError(f"Server class '{server_class_name}' is inactive")
            
            host_ids = server_class.get("host_ids", [])
            for host_id in host_ids:
                host = self.db.query(Host).filter(Host.id == host_id).first()
                if host:
                    hosts.append(host)
        
        elif "hosts" in targets:
            host_list = targets["hosts"]
            if isinstance(host_list, list):
                for host_id in host_list:
                    host = self.db.query(Host).filter(Host.id == host_id).first()
                    if host:
                        hosts.append(host)
            elif isinstance(host_list, str):
                # Handle comma-separated host IDs or hostnames
                host_items = [item.strip() for item in host_list.split(",")]
                for item in host_items:
                    try:
                        host_id = int(item)
                        host = self.db.query(Host).filter(Host.id == host_id).first()
                        if host:
                            hosts.append(host)
                    except ValueError:
                        # Try to find by hostname
                        host = self.db.query(Host).filter(Host.hostname == item).first()
                        if host:
                            hosts.append(host)
        
        return hosts
    
    def execute_task(self, task: Dict[str, Any], hosts: List[Host], execution_options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task on target hosts"""
        task_name = task.get("name", "Unknown Task")
        task_result = {
            "task_name": task_name,
            "host_results": [],
            "overall_success": True,
            "error_message": None
        }
        
        try:
            # Determine task type and parameters
            task_type, task_params = self._extract_task_params(task)
            
            # Execute on each host
            for host in hosts:
                host_result = {
                    "host_id": host.id,
                    "hostname": host.hostname,
                    "success": False,
                    "result": None,
                    "error": None
                }
                
                try:
                    if task_type == "service":
                        result = self._execute_service_task(host, task_params, execution_options)
                    elif task_type == "command":
                        result = self._execute_command_task(host, task_params, execution_options)
                    elif task_type == "script":
                        result = self._execute_script_task(host, task_params, execution_options)
                    elif task_type == "git":
                        result = self._execute_git_task(host, task_params, execution_options)
                    elif task_type == "package":
                        result = self._execute_package_task(host, task_params, execution_options)
                    elif task_type == "debug":
                        result = self._execute_debug_task(host, task_params, execution_options)
                    elif task_type == "reboot":
                        result = self._execute_reboot_task(host, task_params, execution_options)
                    else:
                        raise ValueError(f"Unsupported task type: {task_type}")
                    
                    host_result["success"] = result.get("success", False)
                    host_result["result"] = result
                    
                except Exception as e:
                    host_result["error"] = str(e)
                    task_result["overall_success"] = False
                
                task_result["host_results"].append(host_result)
            
        except Exception as e:
            task_result["overall_success"] = False
            task_result["error_message"] = str(e)
        
        return task_result
    
    def _extract_task_params(self, task: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Extract task type and parameters from task definition"""
        task_types = ["service", "command", "script", "git", "package", "debug", "reboot"]
        
        for task_type in task_types:
            if task_type in task:
                return task_type, task[task_type] if isinstance(task[task_type], dict) else {}
        
        raise ValueError("No valid task type found")
    
    def _execute_service_task(self, host: Host, params: Dict[str, Any], execution_options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a service task"""
        service_name = params.get("name")
        state = params.get("state", "started")
        enabled = params.get("enabled", False)
        
        if not service_name:
            raise ValueError("Service name is required")
        
        # Build service command
        if state == "started":
            cmd = f"systemctl start {service_name}"
        elif state == "stopped":
            cmd = f"systemctl stop {service_name}"
        elif state == "restarted":
            cmd = f"systemctl restart {service_name}"
        else:
            raise ValueError(f"Unsupported service state: {state}")
        
        if enabled:
            cmd += f" && systemctl enable {service_name}"
        
        return self._run_command_on_host(host, cmd, execution_options)
    
    def _execute_command_task(self, host: Host, params: Dict[str, Any], execution_options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command task"""
        command = params.get("command")
        if not command:
            raise ValueError("Command is required")
        
        return self._run_command_on_host(host, command, execution_options)
    
    def _execute_script_task(self, host: Host, params: Dict[str, Any], execution_options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a script task"""
        script_path = params.get("script")
        if not script_path:
            raise ValueError("Script path is required")
        
        # Check if script exists and is executable
        cmd = f"test -f {script_path} && test -x {script_path} && {script_path}"
        return self._run_command_on_host(host, cmd, execution_options)
    
    def _execute_git_task(self, host: Host, params: Dict[str, Any], execution_options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a git task"""
        repo = params.get("repo")
        dest = params.get("dest")
        version = params.get("version")
        
        if not repo or not dest:
            raise ValueError("Git repo and dest are required")
        
        # Build git command
        cmd = f"cd {dest} && git clone {repo} ."
        if version:
            cmd += f" && git checkout {version}"
        
        return self._run_command_on_host(host, cmd, execution_options)
    
    def _execute_package_task(self, host: Host, params: Dict[str, Any], execution_options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a package task"""
        name = params.get("name")
        state = params.get("state", "present")
        
        if not name:
            raise ValueError("Package name is required")
        
        # Determine package manager and build command
        # This is a simplified version - in production you'd detect the OS
        if state == "present":
            cmd = f"apt-get update && apt-get install -y {name}"
        elif state == "latest":
            cmd = f"apt-get update && apt-get install -y {name}"
        elif state == "absent":
            cmd = f"apt-get remove -y {name}"
        else:
            raise ValueError(f"Unsupported package state: {state}")
        
        return self._run_command_on_host(host, cmd, execution_options)
    
    def _execute_debug_task(self, host: Host, params: Dict[str, Any], execution_options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a debug task"""
        msg = params.get("msg", "")
        return {
            "success": True,
            "stdout": f"Debug message: {msg}",
            "stderr": "",
            "return_code": 0
        }
    
    def _execute_reboot_task(self, host: Host, params: Dict[str, Any], execution_options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a reboot task"""
        reboot_timeout = params.get("reboot_timeout", 300)
        
        # Note: In production, you'd want to handle reboot more carefully
        # This is a simplified version
        cmd = "reboot"
        return self._run_command_on_host(host, cmd, execution_options)
    
    def _run_command_on_host(self, host: Host, command: str, execution_options: Dict[str, Any]) -> Dict[str, Any]:
        """Run a command on a host using SSH"""
        try:
            # Create SSH client
            ssh_client = create_ssh_client_from_host(host)
            
            # Apply execution options
            user = execution_options.get("remote_user", "root")
            if user != "root":
                command = f"sudo -u {user} {command}"
            
            # Execute command
            return_code, stdout, stderr = ssh_client.execute_command(command)
            
            return {
                "success": return_code == 0,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": return_code
            }
            
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            }
    
    def create_runbook_execution(self, runbook_id: int, triggered_by_user_id: int, parameters: Optional[Dict[str, Any]] = None) -> RunbookExecution:
        """Create a new runbook execution record"""
        execution = RunbookExecution(
            runbook_id=runbook_id,
            execution_id=str(uuid.uuid4()),
            status=RunbookStatus.PENDING.value,
            triggered_by_user_id=triggered_by_user_id,
            parameters=parameters or {}
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        return execution
    
    def create_task_execution(self, execution_id: int, task_name: str, task_type: str, target_hosts: List[int], parameters: Optional[Dict[str, Any]] = None) -> RunbookTaskExecution:
        """Create a new task execution record"""
        task_execution = RunbookTaskExecution(
            execution_id=execution_id,
            task_name=task_name,
            task_type=task_type,
            target_hosts=target_hosts,
            parameters=parameters or {}
        )
        
        self.db.add(task_execution)
        self.db.commit()
        self.db.refresh(task_execution)
        
        return task_execution
    
    def update_execution_status(self, execution_id: int, status: str, results: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None) -> None:
        """Update execution status"""
        execution = self.db.query(RunbookExecution).filter(RunbookExecution.id == execution_id).first()
        if execution:
            execution.status = status
            if status in [RunbookStatus.COMPLETED.value, RunbookStatus.FAILED.value, RunbookStatus.CANCELLED.value]:
                execution.completed_at = datetime.utcnow()
            if results:
                execution.results = results
            if error_message:
                execution.error_message = error_message
            
            self.db.commit()
    
    def update_task_execution_status(self, task_execution_id: int, status: str, result: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None) -> None:
        """Update task execution status"""
        task_execution = self.db.query(RunbookTaskExecution).filter(RunbookTaskExecution.id == task_execution_id).first()
        if task_execution:
            task_execution.status = status
            if status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.SKIPPED.value]:
                task_execution.completed_at = datetime.utcnow()
            if result:
                task_execution.result = result
            if error_message:
                task_execution.error_message = error_message
            
            self.db.commit() 