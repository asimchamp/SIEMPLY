"""
Splunk Installer Module
Contains functions for installing and configuring Splunk components
"""
import os
import logging
from typing import Dict, Any, Optional

from backend.models import Host
from backend.automation.utils import run_command_with_timeout

logger = logging.getLogger(__name__)

# Default installation parameters
DEFAULT_SPLUNK_UF_VERSION = "9.1.1"
DEFAULT_SPLUNK_ENT_VERSION = "9.1.1"
DEFAULT_INSTALL_DIR = "/opt"
DEFAULT_SPLUNK_USER = "splunk"
DEFAULT_SPLUNK_GROUP = "splunk"
DEFAULT_SPLUNK_ADMIN_PASSWORD = "changeme"
DEFAULT_SPLUNK_WEB_PORT = 8000  # Default web interface port


async def install_splunk_universal_forwarder(
    host: Host, 
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Install Splunk Universal Forwarder on a host
    
    Args:
        host: Host model instance
        parameters: Optional parameters dictionary with the following keys:
            - version: Splunk UF version to install (default: 9.1.1)
            - install_dir: Directory to install Splunk UF (default: /opt)
            - admin_password: Splunk admin password (default: changeme)
            - user: User to run Splunk as (default: splunk)
            - group: Group to run Splunk as (default: splunk)
            - is_dry_run: Do not make changes, just show commands (default: False)
            
    Returns:
        Dict with installation result
    """
    # Merge provided parameters with defaults
    params = {
        "version": DEFAULT_SPLUNK_UF_VERSION,
        "install_dir": DEFAULT_INSTALL_DIR,
        "admin_password": DEFAULT_SPLUNK_ADMIN_PASSWORD,
        "user": DEFAULT_SPLUNK_USER,
        "group": DEFAULT_SPLUNK_GROUP,
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
    
    # Log the parameters
    logger.info(f"Installing Splunk Universal Forwarder {version} on {host.hostname}")
    
    # Base result with host info
    result = {
        "success": False,
        "host_id": host.id,
        "hostname": host.hostname,
        "is_dry_run": is_dry_run,
        "parameters": params,
        "commands": []
    }
    
    # Check if Splunk UF is already installed
    check_cmd = f"[ -d {install_dir}/splunkforwarder ] && echo 'Found' || echo 'Not Found'"
    check_result = await run_command_with_timeout(host, check_cmd)
    
    if "Found" in check_result.get("stdout", ""):
        result["success"] = True
        result["message"] = "Splunk Universal Forwarder is already installed"
        result["skipped"] = True
        return result
    
    # Create temporary directory
    temp_dir_cmd = "mkdir -p /tmp/splunk_install"
    result["commands"].append(temp_dir_cmd)
    
    if not is_dry_run:
        temp_result = await run_command_with_timeout(host, temp_dir_cmd)
        if not temp_result["success"]:
            result["message"] = "Failed to create temporary directory"
            result.update(temp_result)
            return result
    
    # Download Splunk UF installer
    download_url = f"https://download.splunk.com/products/universalforwarder/releases/{version}/linux/splunkforwarder-{version}-f74036626f0c-Linux-x86_64.tgz"
    download_cmd = f"cd /tmp/splunk_install && wget -O splunkforwarder.tgz '{download_url}'"
    result["commands"].append(download_cmd)
    
    if not is_dry_run:
        download_result = await run_command_with_timeout(
            host, download_cmd, timeout=300  # Allow 5 minutes for download
        )
        if not download_result["success"]:
            result["message"] = "Failed to download Splunk UF installer"
            result.update(download_result)
            return result
    
    # Create user and group if they don't exist
    create_user_cmd = f"getent group {group} || groupadd {group}; getent passwd {user} || useradd -m -g {group} {user}"
    result["commands"].append(create_user_cmd)
    
    if not is_dry_run:
        user_result = await run_command_with_timeout(host, create_user_cmd)
        if not user_result["success"]:
            result["message"] = "Failed to create Splunk user/group"
            result.update(user_result)
            return result
    
    # Extract Splunk UF
    extract_cmd = f"cd {install_dir} && tar -xzf /tmp/splunk_install/splunkforwarder.tgz"
    result["commands"].append(extract_cmd)
    
    if not is_dry_run:
        extract_result = await run_command_with_timeout(
            host, extract_cmd, timeout=120  # Allow 2 minutes for extraction
        )
        if not extract_result["success"]:
            result["message"] = "Failed to extract Splunk UF"
            result.update(extract_result)
            return result
    
    # Set ownership
    chown_cmd = f"chown -R {user}:{group} {install_dir}/splunkforwarder"
    result["commands"].append(chown_cmd)
    
    if not is_dry_run:
        chown_result = await run_command_with_timeout(host, chown_cmd)
        if not chown_result["success"]:
            result["message"] = "Failed to set ownership on Splunk UF directory"
            result.update(chown_result)
            return result
    
    # Create user-seed.conf for admin password
    seed_cmd = f"""cat > {install_dir}/splunkforwarder/etc/system/local/user-seed.conf << EOF
[user_info]
USERNAME = admin
PASSWORD = {admin_password}
EOF
"""
    result["commands"].append(seed_cmd)
    
    if not is_dry_run:
        seed_result = await run_command_with_timeout(host, seed_cmd)
        if not seed_result["success"]:
            result["message"] = "Failed to create user-seed.conf"
            result.update(seed_result)
            return result
    
    # Start Splunk and accept license
    start_cmd = f"cd {install_dir}/splunkforwarder && ./bin/splunk start --accept-license --no-prompt --answer-yes"
    result["commands"].append(start_cmd)
    
    if not is_dry_run:
        start_result = await run_command_with_timeout(
            host, start_cmd, timeout=180  # Allow 3 minutes for startup
        )
        if not start_result["success"]:
            result["message"] = "Failed to start Splunk UF"
            result.update(start_result)
            return result
    
    # Enable boot-start
    boot_cmd = f"cd {install_dir}/splunkforwarder && ./bin/splunk enable boot-start -user {user}"
    result["commands"].append(boot_cmd)
    
    if not is_dry_run:
        boot_result = await run_command_with_timeout(host, boot_cmd)
        if not boot_result["success"]:
            result["message"] = "Failed to enable boot-start"
            result.update(boot_result)
            return result
    
    # Verify installation
    if not is_dry_run:
        verify_cmd = f"{install_dir}/splunkforwarder/bin/splunk status"
        verify_result = await run_command_with_timeout(host, verify_cmd)
        if not verify_result["success"]:
            result["message"] = "Installation completed but verification failed"
            result.update(verify_result)
            return result
        
        result["verification"] = verify_result
    
    # Clean up
    cleanup_cmd = "rm -rf /tmp/splunk_install"
    result["commands"].append(cleanup_cmd)
    
    if not is_dry_run:
        await run_command_with_timeout(host, cleanup_cmd)
    
    result["success"] = True
    result["message"] = "Splunk Universal Forwarder installed successfully"
    
    # Add Splunk UF role to host if not present
    current_roles = host.roles or []
    if "splunk_uf" not in current_roles:
        current_roles.append("splunk_uf")
        host.roles = current_roles
    
    return result


async def install_splunk_enterprise(
    host: Host, 
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Install Splunk Enterprise on a host
    
    Args:
        host: Host model instance
        parameters: Optional parameters dictionary with the following keys:
            - version: Splunk Enterprise version to install (default: 9.1.1)
            - install_dir: Directory to install Splunk (default: /opt)
            - admin_password: Splunk admin password (default: changeme)
            - user: User to run Splunk as (default: splunk)
            - group: Group to run Splunk as (default: splunk)
            - web_port: Web interface port (default: 8000)
            - is_dry_run: Do not make changes, just show commands (default: False)
            
    Returns:
        Dict with installation result
    """
    # Merge provided parameters with defaults
    params = {
        "version": DEFAULT_SPLUNK_ENT_VERSION,
        "install_dir": DEFAULT_INSTALL_DIR,
        "admin_password": DEFAULT_SPLUNK_ADMIN_PASSWORD,
        "user": DEFAULT_SPLUNK_USER,
        "group": DEFAULT_SPLUNK_GROUP,
        "web_port": DEFAULT_SPLUNK_WEB_PORT,
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
    web_port = params["web_port"]
    
    # Log the parameters
    logger.info(f"Installing Splunk Enterprise {version} on {host.hostname}")
    
    # Base result with host info
    result = {
        "success": False,
        "host_id": host.id,
        "hostname": host.hostname,
        "is_dry_run": is_dry_run,
        "parameters": params,
        "commands": []
    }
    
    # Check if Splunk Enterprise is already installed
    check_cmd = f"[ -d {install_dir}/splunk ] && echo 'Found' || echo 'Not Found'"
    check_result = await run_command_with_timeout(host, check_cmd)
    
    if "Found" in check_result.get("stdout", ""):
        result["success"] = True
        result["message"] = "Splunk Enterprise is already installed"
        result["skipped"] = True
        return result
    
    # Create temporary directory
    temp_dir_cmd = "mkdir -p /tmp/splunk_install"
    result["commands"].append(temp_dir_cmd)
    
    if not is_dry_run:
        temp_result = await run_command_with_timeout(host, temp_dir_cmd)
        if not temp_result["success"]:
            result["message"] = "Failed to create temporary directory"
            result.update(temp_result)
            return result
    
    # Download Splunk Enterprise installer
    download_url = f"https://download.splunk.com/products/splunk/releases/{version}/linux/splunk-{version}-f74036626f0c-Linux-x86_64.tgz"
    download_cmd = f"cd /tmp/splunk_install && wget -O splunk.tgz '{download_url}'"
    result["commands"].append(download_cmd)
    
    if not is_dry_run:
        download_result = await run_command_with_timeout(
            host, download_cmd, timeout=300  # Allow 5 minutes for download
        )
        if not download_result["success"]:
            result["message"] = "Failed to download Splunk Enterprise installer"
            result.update(download_result)
            return result
    
    # Create user and group if they don't exist
    create_user_cmd = f"getent group {group} || groupadd {group}; getent passwd {user} || useradd -m -g {group} {user}"
    result["commands"].append(create_user_cmd)
    
    if not is_dry_run:
        user_result = await run_command_with_timeout(host, create_user_cmd)
        if not user_result["success"]:
            result["message"] = "Failed to create Splunk user/group"
            result.update(user_result)
            return result
    
    # Extract Splunk Enterprise
    extract_cmd = f"cd {install_dir} && tar -xzf /tmp/splunk_install/splunk.tgz"
    result["commands"].append(extract_cmd)
    
    if not is_dry_run:
        extract_result = await run_command_with_timeout(
            host, extract_cmd, timeout=180  # Allow 3 minutes for extraction
        )
        if not extract_result["success"]:
            result["message"] = "Failed to extract Splunk Enterprise"
            result.update(extract_result)
            return result
    
    # Set ownership
    chown_cmd = f"chown -R {user}:{group} {install_dir}/splunk"
    result["commands"].append(chown_cmd)
    
    if not is_dry_run:
        chown_result = await run_command_with_timeout(host, chown_cmd)
        if not chown_result["success"]:
            result["message"] = "Failed to set ownership on Splunk directory"
            result.update(chown_result)
            return result
    
    # Create user-seed.conf for admin password
    seed_cmd = f"""cat > {install_dir}/splunk/etc/system/local/user-seed.conf << EOF
[user_info]
USERNAME = admin
PASSWORD = {admin_password}
EOF
"""
    result["commands"].append(seed_cmd)
    
    if not is_dry_run:
        seed_result = await run_command_with_timeout(host, seed_cmd)
        if not seed_result["success"]:
            result["message"] = "Failed to create user-seed.conf"
            result.update(seed_result)
            return result
    
    # Configure web port if different from default
    if web_port != DEFAULT_SPLUNK_WEB_PORT:
        web_conf_cmd = f"""cat > {install_dir}/splunk/etc/system/local/web.conf << EOF
[settings]
httpport = {web_port}
EOF
"""
        result["commands"].append(web_conf_cmd)
        
        if not is_dry_run:
            web_result = await run_command_with_timeout(host, web_conf_cmd)
            if not web_result["success"]:
                result["message"] = "Failed to configure web port"
                result.update(web_result)
                return result
    
    # Start Splunk and accept license
    start_cmd = f"cd {install_dir}/splunk && ./bin/splunk start --accept-license --no-prompt --answer-yes"
    result["commands"].append(start_cmd)
    
    if not is_dry_run:
        start_result = await run_command_with_timeout(
            host, start_cmd, timeout=300  # Allow 5 minutes for startup
        )
        if not start_result["success"]:
            result["message"] = "Failed to start Splunk Enterprise"
            result.update(start_result)
            return result
    
    # Enable boot-start
    boot_cmd = f"cd {install_dir}/splunk && ./bin/splunk enable boot-start -user {user}"
    result["commands"].append(boot_cmd)
    
    if not is_dry_run:
        boot_result = await run_command_with_timeout(host, boot_cmd)
        if not boot_result["success"]:
            result["message"] = "Failed to enable boot-start"
            result.update(boot_result)
            return result
    
    # Verify installation
    if not is_dry_run:
        verify_cmd = f"{install_dir}/splunk/bin/splunk status"
        verify_result = await run_command_with_timeout(host, verify_cmd)
        if not verify_result["success"]:
            result["message"] = "Installation completed but verification failed"
            result.update(verify_result)
            return result
        
        result["verification"] = verify_result
    
    # Clean up
    cleanup_cmd = "rm -rf /tmp/splunk_install"
    result["commands"].append(cleanup_cmd)
    
    if not is_dry_run:
        await run_command_with_timeout(host, cleanup_cmd)
    
    result["success"] = True
    result["message"] = "Splunk Enterprise installed successfully"
    
    # Add Splunk Enterprise role to host if not present
    current_roles = host.roles or []
    if "splunk_enterprise" not in current_roles:
        current_roles.append("splunk_enterprise")
        host.roles = current_roles
    
    return result 