"""
Custom Command and Script Installer Module
Contains functions for running custom commands and scripts
"""
import os
import logging
import tempfile
from typing import Dict, Any, Optional

from backend.models import Host
from backend.automation.utils import run_command_with_timeout

logger = logging.getLogger(__name__)

async def run_custom_command(
    host: Host, 
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run a custom command on a host
    
    Args:
        host: Host model instance
        parameters: Parameters dictionary with the following keys:
            - command: Command to execute
            - run_user: User to run command as (default: root)
            - is_dry_run: Do not make changes, just show commands (default: False)
            
    Returns:
        Dict with execution result
    """
    if not parameters or "command" not in parameters:
        return {
            "success": False,
            "message": "Command parameter is required",
            "return_code": 1
        }
    
    command = parameters.get("command")
    run_user = parameters.get("run_user", "root")
    is_dry_run = parameters.get("is_dry_run", False)
    
    # Log the parameters
    logger.info(f"Running custom command on {host.hostname} as user {run_user}")
    
    # Base result with host info
    result = {
        "success": False,
        "host_id": host.id,
        "hostname": host.hostname,
        "is_dry_run": is_dry_run,
        "parameters": parameters,
        "commands": []
    }
    
    # Prepare command to run as specified user
    if run_user == "root":
        exec_cmd = command
    else:
        # Check if user exists, create if not
        create_user_cmd = f"id -u {run_user} &>/dev/null || useradd -m {run_user}"
        result["commands"].append(create_user_cmd)
        
        if not is_dry_run:
            user_result = await run_command_with_timeout(host, create_user_cmd)
            if not user_result["success"]:
                result["message"] = f"Failed to create user {run_user}"
                result.update(user_result)
                return result
        
        # Run command as specified user
        exec_cmd = f"su - {run_user} -c '{command}'"
    
    result["commands"].append(exec_cmd)
    
    if is_dry_run:
        result["success"] = True
        result["message"] = "Dry run completed"
        return result
    
    # Execute command
    cmd_result = await run_command_with_timeout(host, exec_cmd, timeout=300)
    result.update(cmd_result)
    
    if cmd_result["success"]:
        result["message"] = "Command executed successfully"
    else:
        result["message"] = "Command execution failed"
    
    return result


async def run_bash_script(
    host: Host, 
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run a bash script on a host
    
    Args:
        host: Host model instance
        parameters: Parameters dictionary with the following keys:
            - command: Script content to execute
            - run_user: User to run script as (default: root)
            - is_dry_run: Do not make changes, just show commands (default: False)
            
    Returns:
        Dict with execution result
    """
    if not parameters:
        return {
            "success": False,
            "message": "Parameters are required",
            "return_code": 1
        }
    
    script_content = parameters.get("command", "#!/bin/bash\necho 'Empty script'")
    run_user = parameters.get("run_user", "root")
    is_dry_run = parameters.get("is_dry_run", False)
    
    # Log the parameters
    logger.info(f"Running bash script on {host.hostname} as user {run_user}")
    
    # Base result with host info
    result = {
        "success": False,
        "host_id": host.id,
        "hostname": host.hostname,
        "is_dry_run": is_dry_run,
        "parameters": parameters,
        "commands": []
    }
    
    # Create a temporary script file
    temp_script = f"/tmp/siemply_script_{os.urandom(4).hex()}.sh"
    create_script_cmd = f"cat > {temp_script} << 'EOFSCRIPT'\n{script_content}\nEOFSCRIPT\nchmod +x {temp_script}"
    result["commands"].append(create_script_cmd)
    
    if is_dry_run:
        result["success"] = True
        result["message"] = "Dry run completed"
        return result
    
    # Create script file on remote host
    script_result = await run_command_with_timeout(host, create_script_cmd)
    if not script_result["success"]:
        result["message"] = "Failed to create script file"
        result.update(script_result)
        return result
    
    # Check if user exists, create if not
    if run_user != "root":
        create_user_cmd = f"id -u {run_user} &>/dev/null || useradd -m {run_user}"
        user_result = await run_command_with_timeout(host, create_user_cmd)
        if not user_result["success"]:
            result["message"] = f"Failed to create user {run_user}"
            result.update(user_result)
            return result
    
    # Execute script as specified user
    if run_user == "root":
        exec_cmd = temp_script
    else:
        # Set ownership and execute
        chown_cmd = f"chown {run_user}:{run_user} {temp_script}"
        await run_command_with_timeout(host, chown_cmd)
        exec_cmd = f"su - {run_user} -c '{temp_script}'"
    
    result["commands"].append(exec_cmd)
    
    # Execute script
    cmd_result = await run_command_with_timeout(host, exec_cmd, timeout=300)
    result.update(cmd_result)
    
    # Clean up
    cleanup_cmd = f"rm -f {temp_script}"
    await run_command_with_timeout(host, cleanup_cmd)
    
    if cmd_result["success"]:
        result["message"] = "Script executed successfully"
    else:
        result["message"] = "Script execution failed"
    
    return result 