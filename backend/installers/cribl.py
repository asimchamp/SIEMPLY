"""
Cribl Installer Module
Contains functions for installing and configuring Cribl components
"""
import os
import logging
from typing import Dict, Any, Optional

from backend.models import Host
from backend.automation.utils import run_command_with_timeout

logger = logging.getLogger(__name__)

# Default installation parameters
DEFAULT_CRIBL_VERSION = "3.4.1"  # Latest version as of script creation
DEFAULT_INSTALL_DIR = "/opt"
DEFAULT_CRIBL_USER = "cribl"
DEFAULT_CRIBL_GROUP = "cribl"
DEFAULT_CRIBL_ADMIN_PASSWORD = "admin123"  # Default Cribl password
DEFAULT_CRIBL_API_PORT = 9000  # Default Cribl UI/API port
DEFAULT_CRIBL_WORKER_PORT = 4200  # Default Cribl worker connection port


async def install_cribl_leader(
    host: Host, 
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Install Cribl Stream Leader on a host
    
    Args:
        host: Host model instance
        parameters: Optional parameters dictionary with the following keys:
            - version: Cribl version to install (default: 3.4.1)
            - install_dir: Directory to install Cribl (default: /opt)
            - admin_password: Cribl admin password (default: admin)
            - user: User to run Cribl as (default: cribl)
            - group: Group to run Cribl as (default: cribl)
            - api_port: API/UI port (default: 9000)
            - is_dry_run: Do not make changes, just show commands (default: False)
            
    Returns:
        Dict with installation result
    """
    # Merge provided parameters with defaults
    params = {
        "version": DEFAULT_CRIBL_VERSION,
        "install_dir": DEFAULT_INSTALL_DIR,
        "admin_password": DEFAULT_CRIBL_ADMIN_PASSWORD,
        "user": DEFAULT_CRIBL_USER,
        "group": DEFAULT_CRIBL_GROUP,
        "api_port": DEFAULT_CRIBL_API_PORT,
        "is_dry_run": False,
    }
    
    if parameters:
        params.update(parameters)
    
    is_dry_run = params.get("is_dry_run", False)
    version = params["version"]
    install_dir = params["install_dir"]
    admin_password = params["admin_password"]
    user = params["user"]
    group = params["group"]
    api_port = params["api_port"]
    
    # Log the parameters
    logger.info(f"Installing Cribl Stream Leader {version} on {host.hostname}")
    
    # Base result with host info
    result = {
        "success": False,
        "host_id": host.id,
        "hostname": host.hostname,
        "is_dry_run": is_dry_run,
        "parameters": params,
        "commands": []
    }
    
    # Check if Cribl is already installed
    check_cmd = f"[ -d {install_dir}/cribl ] && echo 'Found' || echo 'Not Found'"
    check_result = await run_command_with_timeout(host, check_cmd)
    
    if "Found" in check_result.get("stdout", ""):
        result["success"] = True
        result["message"] = "Cribl appears to be already installed"
        result["skipped"] = True
        return result
    
    # Create temporary directory
    temp_dir_cmd = "mkdir -p /tmp/cribl_install"
    result["commands"].append(temp_dir_cmd)
    
    if not is_dry_run:
        temp_result = await run_command_with_timeout(host, temp_dir_cmd)
        if not temp_result["success"]:
            result["message"] = "Failed to create temporary directory"
            result.update(temp_result)
            return result
    
    # Download Cribl installer
    download_url = f"https://cdn.cribl.io/dl/cribl-{version}-linux-x64.tgz"
    download_cmd = f"cd /tmp/cribl_install && wget -O cribl.tgz '{download_url}'"
    result["commands"].append(download_cmd)
    
    if not is_dry_run:
        download_result = await run_command_with_timeout(
            host, download_cmd, timeout=300  # Allow 5 minutes for download
        )
        if not download_result["success"]:
            result["message"] = "Failed to download Cribl installer"
            result.update(download_result)
            return result
    
    # Create user and group if they don't exist
    create_user_cmd = f"getent group {group} || groupadd {group}; getent passwd {user} || useradd -m -g {group} {user}"
    result["commands"].append(create_user_cmd)
    
    if not is_dry_run:
        user_result = await run_command_with_timeout(host, create_user_cmd)
        if not user_result["success"]:
            result["message"] = "Failed to create Cribl user/group"
            result.update(user_result)
            return result
    
    # Extract Cribl
    extract_cmd = f"cd {install_dir} && tar -xzf /tmp/cribl_install/cribl.tgz"
    result["commands"].append(extract_cmd)
    
    if not is_dry_run:
        extract_result = await run_command_with_timeout(
            host, extract_cmd, timeout=120  # Allow 2 minutes for extraction
        )
        if not extract_result["success"]:
            result["message"] = "Failed to extract Cribl"
            result.update(extract_result)
            return result
    
    # Set ownership
    chown_cmd = f"chown -R {user}:{group} {install_dir}/cribl"
    result["commands"].append(chown_cmd)
    
    if not is_dry_run:
        chown_result = await run_command_with_timeout(host, chown_cmd)
        if not chown_result["success"]:
            result["message"] = "Failed to set ownership on Cribl directory"
            result.update(chown_result)
            return result
    
    # Configure as leader
    leader_cmd = f"cd {install_dir}/cribl && ./bin/cribl mode-master"
    result["commands"].append(leader_cmd)
    
    if not is_dry_run:
        leader_result = await run_command_with_timeout(host, leader_cmd)
        if not leader_result["success"]:
            result["message"] = "Failed to configure Cribl as leader"
            result.update(leader_result)
            return result
    
    # Configure admin password if provided
    if admin_password:
        passwd_cmd = f"cd {install_dir}/cribl && ./bin/cribl users create -u admin -p '{admin_password}' -r admin"
        result["commands"].append(passwd_cmd)
        
        if not is_dry_run:
            passwd_result = await run_command_with_timeout(host, passwd_cmd)
            if not passwd_result["success"]:
                result["message"] = "Failed to set admin password"
                result.update(passwd_result)
                # Continue even if password setting fails
    
    # Configure port if different from default
    if api_port != DEFAULT_CRIBL_API_PORT:
        port_cmd = f"""cat > {install_dir}/cribl/local/_system/instance.yml << EOF
api:
  host: 0.0.0.0
  port: {api_port}
EOF
"""
        result["commands"].append(port_cmd)
        
        if not is_dry_run:
            port_result = await run_command_with_timeout(host, port_cmd)
            if not port_result["success"]:
                result["message"] = "Failed to configure API port"
                result.update(port_result)
                return result
    
    # Setup systemd service
    systemd_cmd = f"""cat > /etc/systemd/system/cribl.service << EOF
[Unit]
Description=Cribl Stream Leader
After=network.target

[Service]
Type=forking
User={user}
Group={group}
ExecStart={install_dir}/cribl/bin/cribl start
ExecStop={install_dir}/cribl/bin/cribl stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
"""
    result["commands"].append(systemd_cmd)
    
    if not is_dry_run:
        systemd_result = await run_command_with_timeout(host, systemd_cmd)
        if not systemd_result["success"]:
            result["message"] = "Failed to create systemd service"
            result.update(systemd_result)
            return result
        
        # Reload systemd and enable service
        systemctl_cmd = "systemctl daemon-reload && systemctl enable cribl.service"
        result["commands"].append(systemctl_cmd)
        
        systemctl_result = await run_command_with_timeout(host, systemctl_cmd)
        if not systemctl_result["success"]:
            result["message"] = "Failed to enable Cribl service"
            result.update(systemctl_result)
            # Continue even if systemctl fails
    
    # Start Cribl service
    start_cmd = "systemctl start cribl.service"
    result["commands"].append(start_cmd)
    
    if not is_dry_run:
        start_result = await run_command_with_timeout(
            host, start_cmd, timeout=180  # Allow 3 minutes for startup
        )
        if not start_result["success"]:
            result["message"] = "Failed to start Cribl service"
            result.update(start_result)
            return result
    
    # Verify installation
    if not is_dry_run:
        verify_cmd = "systemctl status cribl.service"
        verify_result = await run_command_with_timeout(host, verify_cmd)
        result["verification"] = verify_result
        
        if not verify_result["success"]:
            result["message"] = "Installation completed but verification failed"
            return result
    
    # Clean up
    cleanup_cmd = "rm -rf /tmp/cribl_install"
    result["commands"].append(cleanup_cmd)
    
    if not is_dry_run:
        await run_command_with_timeout(host, cleanup_cmd)
    
    result["success"] = True
    result["message"] = "Cribl Stream Leader installed successfully"
    
    # Add Cribl Leader role to host if not present
    current_roles = host.roles or []
    if "cribl_leader" not in current_roles:
        current_roles.append("cribl_leader")
        host.roles = current_roles
    
    return result


async def install_cribl_worker(
    host: Host, 
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Install Cribl Stream Worker on a host
    
    Args:
        host: Host model instance
        parameters: Optional parameters dictionary with the following keys:
            - version: Cribl version to install (default: 3.4.1)
            - install_dir: Directory to install Cribl (default: /opt)
            - user: User to run Cribl as (default: cribl)
            - group: Group to run Cribl as (default: cribl)
            - leader_host: Leader hostname/IP (required)
            - leader_port: Leader port for worker connections (default: 4200)
            - authentication_token: Leader authentication token (required)
            - is_dry_run: Do not make changes, just show commands (default: False)
            
    Returns:
        Dict with installation result
    """
    # Merge provided parameters with defaults
    params = {
        "version": DEFAULT_CRIBL_VERSION,
        "install_dir": DEFAULT_INSTALL_DIR,
        "user": DEFAULT_CRIBL_USER,
        "group": DEFAULT_CRIBL_GROUP,
        "leader_port": DEFAULT_CRIBL_WORKER_PORT,
        "is_dry_run": False,
    }
    
    if parameters:
        params.update(parameters)
    
    is_dry_run = params.get("is_dry_run", False)
    version = params["version"]
    install_dir = params["install_dir"]
    user = params["user"]
    group = params["group"]
    
    # Check required parameters
    if "leader_host" not in params:
        return {
            "success": False,
            "message": "Missing required parameter: leader_host",
            "host_id": host.id,
            "hostname": host.hostname,
            "is_dry_run": is_dry_run
        }
    
    if "authentication_token" not in params:
        return {
            "success": False,
            "message": "Missing required parameter: authentication_token",
            "host_id": host.id,
            "hostname": host.hostname,
            "is_dry_run": is_dry_run
        }
    
    leader_host = params["leader_host"]
    leader_port = params["leader_port"]
    auth_token = params["authentication_token"]
    
    # Log the parameters
    logger.info(f"Installing Cribl Stream Worker {version} on {host.hostname}")
    
    # Base result with host info
    result = {
        "success": False,
        "host_id": host.id,
        "hostname": host.hostname,
        "is_dry_run": is_dry_run,
        "parameters": params,
        "commands": []
    }
    
    # Check if Cribl is already installed
    check_cmd = f"[ -d {install_dir}/cribl ] && echo 'Found' || echo 'Not Found'"
    check_result = await run_command_with_timeout(host, check_cmd)
    
    if "Found" in check_result.get("stdout", ""):
        result["success"] = True
        result["message"] = "Cribl appears to be already installed"
        result["skipped"] = True
        return result
    
    # Create temporary directory
    temp_dir_cmd = "mkdir -p /tmp/cribl_install"
    result["commands"].append(temp_dir_cmd)
    
    if not is_dry_run:
        temp_result = await run_command_with_timeout(host, temp_dir_cmd)
        if not temp_result["success"]:
            result["message"] = "Failed to create temporary directory"
            result.update(temp_result)
            return result
    
    # Download Cribl installer
    download_url = f"https://cdn.cribl.io/dl/cribl-{version}-linux-x64.tgz"
    download_cmd = f"cd /tmp/cribl_install && wget -O cribl.tgz '{download_url}'"
    result["commands"].append(download_cmd)
    
    if not is_dry_run:
        download_result = await run_command_with_timeout(
            host, download_cmd, timeout=300  # Allow 5 minutes for download
        )
        if not download_result["success"]:
            result["message"] = "Failed to download Cribl installer"
            result.update(download_result)
            return result
    
    # Create user and group if they don't exist
    create_user_cmd = f"getent group {group} || groupadd {group}; getent passwd {user} || useradd -m -g {group} {user}"
    result["commands"].append(create_user_cmd)
    
    if not is_dry_run:
        user_result = await run_command_with_timeout(host, create_user_cmd)
        if not user_result["success"]:
            result["message"] = "Failed to create Cribl user/group"
            result.update(user_result)
            return result
    
    # Extract Cribl
    extract_cmd = f"cd {install_dir} && tar -xzf /tmp/cribl_install/cribl.tgz"
    result["commands"].append(extract_cmd)
    
    if not is_dry_run:
        extract_result = await run_command_with_timeout(
            host, extract_cmd, timeout=120  # Allow 2 minutes for extraction
        )
        if not extract_result["success"]:
            result["message"] = "Failed to extract Cribl"
            result.update(extract_result)
            return result
    
    # Set ownership
    chown_cmd = f"chown -R {user}:{group} {install_dir}/cribl"
    result["commands"].append(chown_cmd)
    
    if not is_dry_run:
        chown_result = await run_command_with_timeout(host, chown_cmd)
        if not chown_result["success"]:
            result["message"] = "Failed to set ownership on Cribl directory"
            result.update(chown_result)
            return result
    
    # Configure as worker
    worker_cmd = f"cd {install_dir}/cribl && ./bin/cribl mode-worker -H {leader_host}:{leader_port} -u {auth_token}"
    result["commands"].append(worker_cmd)
    
    if not is_dry_run:
        worker_result = await run_command_with_timeout(host, worker_cmd)
        if not worker_result["success"]:
            result["message"] = "Failed to configure Cribl as worker"
            result.update(worker_result)
            return result
    
    # Setup systemd service
    systemd_cmd = f"""cat > /etc/systemd/system/cribl.service << EOF
[Unit]
Description=Cribl Stream Worker
After=network.target

[Service]
Type=forking
User={user}
Group={group}
ExecStart={install_dir}/cribl/bin/cribl start
ExecStop={install_dir}/cribl/bin/cribl stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
"""
    result["commands"].append(systemd_cmd)
    
    if not is_dry_run:
        systemd_result = await run_command_with_timeout(host, systemd_cmd)
        if not systemd_result["success"]:
            result["message"] = "Failed to create systemd service"
            result.update(systemd_result)
            return result
        
        # Reload systemd and enable service
        systemctl_cmd = "systemctl daemon-reload && systemctl enable cribl.service"
        result["commands"].append(systemctl_cmd)
        
        systemctl_result = await run_command_with_timeout(host, systemctl_cmd)
        if not systemctl_result["success"]:
            result["message"] = "Failed to enable Cribl service"
            result.update(systemctl_result)
            # Continue even if systemctl fails
    
    # Start Cribl service
    start_cmd = "systemctl start cribl.service"
    result["commands"].append(start_cmd)
    
    if not is_dry_run:
        start_result = await run_command_with_timeout(
            host, start_cmd, timeout=180  # Allow 3 minutes for startup
        )
        if not start_result["success"]:
            result["message"] = "Failed to start Cribl service"
            result.update(start_result)
            return result
    
    # Verify installation
    if not is_dry_run:
        verify_cmd = "systemctl status cribl.service"
        verify_result = await run_command_with_timeout(host, verify_cmd)
        result["verification"] = verify_result
        
        if not verify_result["success"]:
            result["message"] = "Installation completed but verification failed"
            return result
    
    # Clean up
    cleanup_cmd = "rm -rf /tmp/cribl_install"
    result["commands"].append(cleanup_cmd)
    
    if not is_dry_run:
        await run_command_with_timeout(host, cleanup_cmd)
    
    result["success"] = True
    result["message"] = "Cribl Stream Worker installed successfully"
    
    # Add Cribl Worker role to host if not present
    current_roles = host.roles or []
    if "cribl_worker" not in current_roles:
        current_roles.append("cribl_worker")
        host.roles = current_roles
    
    return result 