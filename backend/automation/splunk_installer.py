"""
Splunk Installer Automation Module
Installs Splunk components directly via SSH
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from backend.automation.ssh_client import get_ssh_client
from backend.models import Host

logger = logging.getLogger(__name__)

# Default installation parameters
DEFAULT_SPLUNK_UF_VERSION = "9.1.1"
DEFAULT_INSTALL_DIR = "/opt"
DEFAULT_SPLUNK_USER = "splunk"
DEFAULT_SPLUNK_GROUP = "splunk"
DEFAULT_SPLUNK_ADMIN_PASSWORD = "changeme"


async def install_splunk_uf(host: Host, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Install Splunk Universal Forwarder on a host via SSH
    
    Args:
        host: Host model instance
        parameters: Optional parameters dictionary with the following keys:
            - version: Splunk UF version to install (default: 9.1.1)
            - install_dir: Directory to install Splunk UF (default: /opt)
            - admin_password: Splunk admin password (default: changeme)
            - user: User to run Splunk as (default: splunk)
            - group: Group to run Splunk as (default: splunk)
            - deployment_server: Optional deployment server (format: host:port)
            - deployment_app: Optional deployment app name
            - is_dry_run: Do not make changes, just show commands (default: False)
            
    Returns:
        Dict with installation result
    """
    # Connect to the host via SSH
    async with get_ssh_client(host) as ssh:
        # Check if host is online
        if not ssh:
            return {
                "success": False,
                "host_id": host.id,
                "hostname": host.hostname,
                "message": "Could not establish SSH connection",
                "status": "offline"
            }
        
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
        deployment_server = params.get("deployment_server")
        deployment_app = params.get("deployment_app")
        
        # Base result with host info
        result = {
            "success": False,
            "host_id": host.id,
            "hostname": host.hostname,
            "ip_address": host.ip_address,
            "is_dry_run": is_dry_run,
            "parameters": params,
            "commands": [],
            "status": "online"
        }
        
        # Check if Splunk UF is already installed
        logger.info(f"Checking if Splunk UF is already installed on {host.hostname}")
        check_cmd = f"[ -d {install_dir}/splunkforwarder ] && echo 'Found' || echo 'Not Found'"
        check_result = await ssh.run(check_cmd)
        
        if check_result.returncode == 0 and "Found" in check_result.stdout:
            result["success"] = True
            result["message"] = "Splunk Universal Forwarder is already installed"
            result["skipped"] = True
            return result
        
        if is_dry_run:
            # Just return the commands that would be executed
            result["commands"] = [
                f"mkdir -p /tmp/splunk_install",
                f"cd /tmp/splunk_install && wget -O splunkforwarder.tgz 'https://download.splunk.com/products/universalforwarder/releases/{version}/linux/splunkforwarder-{version}-f74036626f0c-Linux-x86_64.tgz'",
                f"getent group {group} || groupadd {group}; getent passwd {user} || useradd -m -g {group} {user}",
                f"cd {install_dir} && tar -xzf /tmp/splunk_install/splunkforwarder.tgz",
                f"chown -R {user}:{group} {install_dir}/splunkforwarder",
                f"echo '[user_info]\\nUSERNAME = admin\\nPASSWORD = {admin_password}' > {install_dir}/splunkforwarder/etc/system/local/user-seed.conf",
                f"cd {install_dir}/splunkforwarder && ./bin/splunk start --accept-license --no-prompt --answer-yes",
                f"cd {install_dir}/splunkforwarder && ./bin/splunk enable boot-start -user {user}",
                f"rm -rf /tmp/splunk_install"
            ]
            
            # Add deployment server commands if specified
            if deployment_server:
                result["commands"].append(
                    f"cd {install_dir}/splunkforwarder && ./bin/splunk set deploy-poll {deployment_server} -auth admin:{admin_password}"
                )
            
            result["success"] = True
            result["message"] = "Dry run - commands would be executed"
            return result
        
        try:
            # Create temporary directory
            logger.info(f"Creating temporary directory on {host.hostname}")
            temp_dir_cmd = "mkdir -p /tmp/splunk_install"
            result["commands"].append(temp_dir_cmd)
            
            temp_result = await ssh.run(temp_dir_cmd)
            if temp_result.returncode != 0:
                result["message"] = "Failed to create temporary directory"
                result["error"] = temp_result.stderr
                return result
            
            # Download Splunk UF installer
            logger.info(f"Downloading Splunk UF {version} on {host.hostname}")
            download_url = f"https://download.splunk.com/products/universalforwarder/releases/{version}/linux/splunkforwarder-{version}-f74036626f0c-Linux-x86_64.tgz"
            download_cmd = f"cd /tmp/splunk_install && wget -O splunkforwarder.tgz '{download_url}'"
            result["commands"].append(download_cmd)
            
            download_result = await ssh.run(download_cmd)
            if download_result.returncode != 0:
                result["message"] = "Failed to download Splunk UF installer"
                result["error"] = download_result.stderr
                return result
            
            # Create user and group if they don't exist
            logger.info(f"Creating user {user} and group {group} on {host.hostname}")
            create_user_cmd = f"getent group {group} || groupadd {group}; getent passwd {user} || useradd -m -g {group} {user}"
            result["commands"].append(create_user_cmd)
            
            user_result = await ssh.run(create_user_cmd)
            if user_result.returncode != 0:
                result["message"] = "Failed to create Splunk user/group"
                result["error"] = user_result.stderr
                return result
            
            # Extract Splunk UF
            logger.info(f"Extracting Splunk UF to {install_dir} on {host.hostname}")
            extract_cmd = f"cd {install_dir} && tar -xzf /tmp/splunk_install/splunkforwarder.tgz"
            result["commands"].append(extract_cmd)
            
            extract_result = await ssh.run(extract_cmd)
            if extract_result.returncode != 0:
                result["message"] = "Failed to extract Splunk UF"
                result["error"] = extract_result.stderr
                return result
            
            # Set ownership
            logger.info(f"Setting ownership to {user}:{group} on {host.hostname}")
            chown_cmd = f"chown -R {user}:{group} {install_dir}/splunkforwarder"
            result["commands"].append(chown_cmd)
            
            chown_result = await ssh.run(chown_cmd)
            if chown_result.returncode != 0:
                result["message"] = "Failed to set ownership on Splunk UF directory"
                result["error"] = chown_result.stderr
                return result
            
            # Create user-seed.conf for admin password
            logger.info(f"Creating user-seed.conf on {host.hostname}")
            seed_cmd = f"""cat > {install_dir}/splunkforwarder/etc/system/local/user-seed.conf << EOF
[user_info]
USERNAME = admin
PASSWORD = {admin_password}
EOF
"""
            result["commands"].append(seed_cmd)
            
            seed_result = await ssh.run(seed_cmd)
            if seed_result.returncode != 0:
                result["message"] = "Failed to create user-seed.conf"
                result["error"] = seed_result.stderr
                return result
            
            # Start Splunk and accept license
            logger.info(f"Starting Splunk UF on {host.hostname}")
            start_cmd = f"cd {install_dir}/splunkforwarder && ./bin/splunk start --accept-license --no-prompt --answer-yes"
            result["commands"].append(start_cmd)
            
            start_result = await ssh.run(start_cmd)
            if start_result.returncode != 0:
                result["message"] = "Failed to start Splunk UF"
                result["error"] = start_result.stderr
                return result
            
            # Enable boot-start
            logger.info(f"Enabling boot-start on {host.hostname}")
            boot_cmd = f"cd {install_dir}/splunkforwarder && ./bin/splunk enable boot-start -user {user}"
            result["commands"].append(boot_cmd)
            
            boot_result = await ssh.run(boot_cmd)
            if boot_result.returncode != 0:
                result["message"] = "Failed to enable boot-start"
                result["error"] = boot_result.stderr
                return result
            
            # Configure deployment server if specified
            if deployment_server:
                logger.info(f"Configuring deployment server {deployment_server} on {host.hostname}")
                deploy_cmd = f"cd {install_dir}/splunkforwarder && ./bin/splunk set deploy-poll {deployment_server} -auth admin:{admin_password}"
                result["commands"].append(deploy_cmd)
                
                deploy_result = await ssh.run(deploy_cmd)
                if deploy_result.returncode != 0:
                    result["message"] = "Failed to configure deployment server"
                    result["error"] = deploy_result.stderr
                    return result
            
            # Verify installation
            logger.info(f"Verifying Splunk UF installation on {host.hostname}")
            verify_cmd = f"{install_dir}/splunkforwarder/bin/splunk status"
            verify_result = await ssh.run(verify_cmd)
            
            if verify_result.returncode != 0:
                result["message"] = "Installation completed but verification failed"
                result["error"] = verify_result.stderr
                return result
            
            result["verification"] = {
                "stdout": verify_result.stdout,
                "stderr": verify_result.stderr
            }
            
            # Clean up
            logger.info(f"Cleaning up temporary files on {host.hostname}")
            cleanup_cmd = "rm -rf /tmp/splunk_install"
            result["commands"].append(cleanup_cmd)
            
            await ssh.run(cleanup_cmd)
            
            result["success"] = True
            result["message"] = "Splunk Universal Forwarder installed successfully"
            
            return result
            
        except Exception as e:
            logger.error(f"Error installing Splunk UF on {host.hostname}: {str(e)}")
            result["success"] = False
            result["message"] = f"Installation failed: {str(e)}"
            result["error"] = str(e)
            return result 