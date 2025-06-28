"""
Playbook Runner Module
Executes Ansible-inspired playbooks for configuration management
"""
import os
import yaml
import logging
import tempfile
import jinja2
from typing import Dict, Any, Optional, List

from backend.models import Host
from backend.automation.utils import run_command_with_timeout

logger = logging.getLogger(__name__)

class PlaybookRunner:
    """
    Executes Ansible-inspired playbooks against remote hosts
    """
    
    def __init__(self, playbook_path: str, host: Host, variables: Optional[Dict[str, Any]] = None):
        """
        Initialize the playbook runner
        
        Args:
            playbook_path: Path to the playbook YAML file
            host: Host model instance to run against
            variables: Optional variables to override playbook defaults
        """
        self.playbook_path = playbook_path
        self.host = host
        self.variables = variables or {}
        self.playbook = None
        self.result = {
            "success": False,
            "host_id": host.id,
            "hostname": host.hostname,
            "is_dry_run": self.variables.get("is_dry_run", False),
            "parameters": self.variables,
            "tasks": [],
            "commands": []
        }
        
    async def load_playbook(self) -> bool:
        """
        Load and validate the playbook
        
        Returns:
            bool: True if playbook loaded successfully
        """
        try:
            if not os.path.exists(self.playbook_path):
                self.result["message"] = f"Playbook not found: {self.playbook_path}"
                return False
                
            with open(self.playbook_path, 'r') as f:
                self.playbook = yaml.safe_load(f)
                
            # Validate playbook structure
            required_keys = ["name", "tasks"]
            for key in required_keys:
                if key not in self.playbook:
                    self.result["message"] = f"Invalid playbook: missing '{key}' section"
                    return False
            
            # Merge playbook variables with provided variables
            if "vars" in self.playbook:
                playbook_vars = self.playbook["vars"]
                # Start with playbook defaults
                merged_vars = {**playbook_vars}
                # Override with provided variables
                merged_vars.update(self.variables)
                self.variables = merged_vars
                
            return True
        except Exception as e:
            self.result["message"] = f"Error loading playbook: {str(e)}"
            return False
    
    def render_template(self, template_content: str) -> str:
        """
        Render a Jinja2 template with variables
        
        Args:
            template_content: Template content string
            
        Returns:
            str: Rendered template
        """
        try:
            template = jinja2.Template(template_content)
            return template.render(**self.variables)
        except Exception as e:
            logger.error(f"Template rendering error: {str(e)}")
            return template_content
    
    async def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single task from the playbook
        
        Args:
            task: Task definition
            
        Returns:
            Dict: Task execution result
        """
        task_name = task.get("name", "Unnamed task")
        task_result = {
            "name": task_name,
            "success": False,
            "skipped": False,
            "changed": False
        }
        
        # Check if task should be skipped based on 'when' condition
        if "when" in task:
            condition = task["when"]
            # Simple condition evaluation (for complex conditions, we'd need a proper evaluator)
            if isinstance(condition, str):
                if "!=" in condition:
                    var_name, value = condition.split("!=")
                    var_name = var_name.strip()
                    value = value.strip().strip('"\'')
                    
                    # Handle registered variables
                    if "." in var_name:
                        obj_name, attr = var_name.split(".")
                        if obj_name in self.variables and isinstance(self.variables[obj_name], dict):
                            var_value = self.variables[obj_name].get(attr)
                        else:
                            var_value = None
                    else:
                        var_value = self.variables.get(var_name)
                        
                    if str(var_value) == str(value):
                        task_result["skipped"] = True
                        return task_result
                        
                elif "==" in condition:
                    var_name, value = condition.split("==")
                    var_name = var_name.strip()
                    value = value.strip().strip('"\'')
                    
                    # Handle registered variables
                    if "." in var_name:
                        obj_name, attr = var_name.split(".")
                        if obj_name in self.variables and isinstance(self.variables[obj_name], dict):
                            var_value = self.variables[obj_name].get(attr)
                        else:
                            var_value = None
                    else:
                        var_value = self.variables.get(var_name)
                        
                    if str(var_value) != str(value):
                        task_result["skipped"] = True
                        return task_result
        
        # Handle different task types
        if "command" in task:
            # Render command template
            command = self.render_template(task["command"])
            task_result["command"] = command
            self.result["commands"].append(command)
            
            # Check if we're in dry run mode
            if self.variables.get("is_dry_run", False):
                task_result["success"] = True
                task_result["message"] = "Dry run mode - command would be executed"
                return task_result
            
            # Handle become/become_user (privilege escalation)
            if task.get("become", False) and "become_user" in task:
                become_user = task["become_user"]
                if become_user.startswith("{{") and become_user.endswith("}}"):
                    become_user = self.variables.get(become_user.strip("{} "))
                command = f"su - {become_user} -c '{command}'"
            
            # Execute command
            timeout = task.get("timeout", 60)
            cmd_result = await run_command_with_timeout(self.host, command, timeout=timeout)
            
            # Update task result
            task_result.update({
                "success": cmd_result["success"],
                "return_code": cmd_result.get("return_code"),
                "stdout": cmd_result.get("stdout", ""),
                "stderr": cmd_result.get("stderr", "")
            })
            
            # Register variables if specified
            if "register" in task:
                register_name = task["register"]
                self.variables[register_name] = {
                    "success": cmd_result["success"],
                    "return_code": cmd_result.get("return_code"),
                    "stdout": cmd_result.get("stdout", ""),
                    "stderr": cmd_result.get("stderr", "")
                }
            
            # Determine if task changed the system
            if "changed_when" in task:
                # For now, just use the provided value
                task_result["changed"] = bool(task["changed_when"])
            else:
                # By default, a successful command that returns 0 is considered a change
                task_result["changed"] = cmd_result["success"] and cmd_result.get("return_code") == 0
        
        elif "template" in task:
            template_info = task["template"]
            
            # Get template content
            if "src" in template_info and template_info["src"].startswith("templates/"):
                # Find template in playbook
                template_name = template_info["src"].split("/")[-1].replace(".j2", "")
                template_content = None
                
                if "templates" in self.playbook:
                    for tpl in self.playbook["templates"]:
                        if tpl.get("name") == template_name + ".j2":
                            template_content = tpl.get("content", "")
                            break
                
                if not template_content:
                    task_result["message"] = f"Template {template_name} not found in playbook"
                    return task_result
                
                # Render template
                rendered_content = self.render_template(template_content)
                
                # Get destination path
                dest_path = self.render_template(template_info["dest"])
                
                # In dry run mode, just log what would happen
                if self.variables.get("is_dry_run", False):
                    task_result["success"] = True
                    task_result["message"] = f"Dry run mode - would create template at {dest_path}"
                    return task_result
                
                # Create temporary file with rendered content
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(rendered_content.encode())
                    tmp_path = tmp.name
                
                try:
                    # Create directory if needed
                    dir_cmd = f"mkdir -p {os.path.dirname(dest_path)}"
                    await run_command_with_timeout(self.host, dir_cmd)
                    
                    # Copy file to destination
                    copy_cmd = f"cat > {dest_path} << 'EOF'\n{rendered_content}\nEOF"
                    copy_result = await run_command_with_timeout(self.host, copy_cmd)
                    
                    if not copy_result["success"]:
                        task_result["message"] = "Failed to create template file"
                        task_result.update(copy_result)
                        return task_result
                    
                    # Set permissions if specified
                    if "owner" in template_info or "group" in template_info or "mode" in template_info:
                        owner = template_info.get("owner", "root")
                        group = template_info.get("group", "root")
                        mode = template_info.get("mode", "0644")
                        
                        # Render variables in owner/group
                        owner = self.render_template(owner)
                        group = self.render_template(group)
                        
                        chmod_cmd = f"chmod {mode} {dest_path}"
                        chown_cmd = f"chown {owner}:{group} {dest_path}"
                        
                        await run_command_with_timeout(self.host, chmod_cmd)
                        await run_command_with_timeout(self.host, chown_cmd)
                    
                    task_result["success"] = True
                    task_result["changed"] = True
                    task_result["message"] = f"Template {template_name} created at {dest_path}"
                    
                finally:
                    # Clean up temp file
                    os.unlink(tmp_path)
            else:
                task_result["message"] = "Invalid template source"
        
        else:
            task_result["message"] = "Unsupported task type"
        
        return task_result
    
    async def run(self) -> Dict[str, Any]:
        """
        Run the playbook
        
        Returns:
            Dict: Playbook execution result
        """
        # Load playbook
        if not await self.load_playbook():
            return self.result
        
        # Check if host matches target hosts
        if "hosts" in self.playbook:
            target_hosts = self.playbook["hosts"]
            host_match = False
            
            for target in target_hosts:
                if isinstance(target, dict) and "role" in target:
                    if target["role"] in (self.host.roles or []):
                        host_match = True
                        break
            
            if not host_match:
                self.result["message"] = "Host does not match playbook target hosts"
                return self.result
        
        # Execute tasks
        for task in self.playbook["tasks"]:
            task_result = await self.run_task(task)
            self.result["tasks"].append(task_result)
            
            # Stop execution if task failed
            if not task_result["skipped"] and not task_result["success"]:
                self.result["message"] = f"Task '{task_result['name']}' failed"
                return self.result
        
        # Playbook completed successfully
        self.result["success"] = True
        self.result["message"] = f"Playbook '{self.playbook['name']}' executed successfully"
        return self.result


async def run_playbook(
    host: Host, 
    playbook_name: str,
    variables: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run a playbook against a host
    
    Args:
        host: Host model instance
        playbook_name: Name of the playbook file (without path)
        variables: Variables to pass to the playbook
        
    Returns:
        Dict: Playbook execution result
    """
    # Determine playbook path
    playbook_path = os.path.join("data", "playbooks", playbook_name)
    
    # Create and run playbook
    runner = PlaybookRunner(playbook_path, host, variables)
    return await runner.run() 