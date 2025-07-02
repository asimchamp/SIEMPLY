"""
SIEMply Automation Utilities
Helper functions for automation tasks
"""
import asyncio
from typing import Dict, Any, Optional

from backend.models import Host
from backend.automation.ssh_client import create_ssh_client_from_host, SSHConnectionError, SSHClientError

async def validate_ssh_connection(host: Host) -> Dict[str, Any]:
    """
    Test SSH connection to a host
    
    Args:
        host: Host model instance
        
    Returns:
        Dict with connection status details
    """
    result = {
        "success": False,
        "message": "",
        "host_id": host.id,
        "hostname": host.hostname,
        "ip_address": host.ip_address
    }
    
    try:
        # Create SSH client
        ssh_client = create_ssh_client_from_host(host)
        
        # Try to connect and run a simple command
        ssh_client.connect()
        return_code, stdout, stderr = ssh_client.execute_command("echo 'SIEMply connection test successful'")
        
        if return_code == 0:
            result["success"] = True
            result["message"] = "Connection successful"
            result["output"] = stdout.strip()
        else:
            result["message"] = f"Connection established but command failed: {stderr}"
        
        # Disconnect when done
        ssh_client.disconnect()
        
    except SSHConnectionError as e:
        result["message"] = f"Connection failed: {str(e)}"
    except SSHClientError as e:
        result["message"] = f"SSH error: {str(e)}"
    except Exception as e:
        result["message"] = f"Unexpected error: {str(e)}"
    
    return result


async def run_command_with_timeout(
    host: Host, 
    command: str,
    timeout: int = 60,
    log_output: bool = True
) -> Dict[str, Any]:
    """
    Run a command on a host with timeout
    
    Args:
        host: Host model instance
        command: Command to execute
        timeout: Timeout in seconds
        log_output: Whether to include command output in result
        
    Returns:
        Dict with command execution result
    """
    result = {
        "success": False,
        "host_id": host.id,
        "command": command,
        "return_code": None,
        "timed_out": False
    }
    
    try:
        # Create SSH client
        ssh_client = create_ssh_client_from_host(host)
        
        # Connect to host
        ssh_client.connect()
        
        # Run command with timeout
        return_code, stdout, stderr = await asyncio.wait_for(
            asyncio.to_thread(ssh_client.execute_command, command),
            timeout=timeout
        )
        
        # Populate result
        result["return_code"] = return_code
        result["success"] = return_code == 0
        
        if log_output:
            result["stdout"] = stdout
            result["stderr"] = stderr
        
        # Disconnect
        ssh_client.disconnect()
        
    except asyncio.TimeoutError:
        result["timed_out"] = True
        result["message"] = f"Command timed out after {timeout} seconds"
    except SSHConnectionError as e:
        result["message"] = f"Connection failed: {str(e)}"
    except SSHClientError as e:
        result["message"] = f"SSH error: {str(e)}"
    except Exception as e:
        result["message"] = f"Unexpected error: {str(e)}"
    
    return result 