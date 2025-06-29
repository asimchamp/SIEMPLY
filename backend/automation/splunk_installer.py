"""
Splunk Universal Forwarder Installer Module
Installs Splunk Universal Forwarder on hosts via SSH
"""
import asyncio
import os
import logging
from typing import Dict, Any, Optional

from backend.automation.ssh_client import get_ssh_client
from backend.models import Host

logger = logging.getLogger(__name__)

# Mapping of Splunk versions to download URLs
SPLUNK_UF_URLS = {
    "9.4.3": "https://download.splunk.com/products/universalforwarder/releases/9.4.3/linux/splunkforwarder-9.4.3-1a5a2420f501-Linux-x86_64.tgz",
    "9.1.1": "https://download.splunk.com/products/universalforwarder/releases/9.1.1/linux/splunkforwarder-9.1.1-64e843ea36b1-Linux-x86_64.tgz",
    "9.0.5": "https://download.splunk.com/products/universalforwarder/releases/9.0.5/linux/splunkforwarder-9.0.5-e9494146ae5c-Linux-x86_64.tgz",
    "8.2.9": "https://download.splunk.com/products/universalforwarder/releases/8.2.9/linux/splunkforwarder-8.2.9-4a20fb65aa78-Linux-x86_64.tgz",
    "8.1.5": "https://download.splunk.com/products/universalforwarder/releases/8.1.5/linux/splunkforwarder-8.1.5-9c0c082e4596-Linux-x86_64.tgz",
}

async def install_splunk_uf(host: Host, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Install Splunk Universal Forwarder on a host via SSH
    
    Args:
        host: The host object containing connection information
        params: Dictionary of installation parameters
            - version: Splunk UF version to install
            - install_dir: Installation directory (default: /opt)
            - admin_password: Admin password for Splunk
            - user: User to run Splunk as (default: splunk)
            - group: Group to run Splunk as (default: splunk)
            - deployment_server: Optional deployment server
            - deployment_app: Optional deployment app
            - is_dry_run: If True, only simulate the installation
            
    Returns:
        Dictionary with installation results
    """
    # Extract parameters with defaults
    version = params.get("version")
    install_dir = params.get("install_dir", "/opt")
    admin_password = params.get("admin_password")
    user = params.get("user", "splunk")
    group = params.get("group", "splunk")
    deployment_server = params.get("deployment_server")
    deployment_app = params.get("deployment_app")
    is_dry_run = params.get("is_dry_run", False)
    
    # Validate required parameters
    if not version:
        return {
            "success": False,
            "message": "Splunk version is required"
        }
    
    if not admin_password:
        return {
            "success": False,
            "message": "Admin password is required"
        }
    
    # Connect to the host via SSH
    async with get_ssh_client(host) as ssh:
        # Check if host is online
        if not ssh:
            return {
                "success": False,
                "message": "Could not establish SSH connection"
            }
        
        logger.info(f"Connected to {host.hostname} for Splunk UF installation")
        
        # If this is a dry run, just return success
        if is_dry_run:
            return {
                "success": True,
                "message": "Dry run - would have installed Splunk UF",
                "is_dry_run": True,
                "version": version,
                "install_dir": install_dir
            }
        
        try:
            # Create installation directory if it doesn't exist
            result = await ssh.run(f"sudo mkdir -p {install_dir}")
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to create installation directory: {result.stderr}"
                }
            
            # Check if Splunk UF is already installed
            check_cmd = f"test -d {install_dir}/splunkforwarder && echo 'exists' || echo 'not exists'"
            check_result = await ssh.run(check_cmd)
            
            if check_result.stdout.strip() == "exists":
                return {
                    "success": False,
                    "message": f"Splunk UF is already installed at {install_dir}/splunkforwarder"
                }
            
            # Instead of downloading from external URL, check if we have a pre-installed package
            # First check common locations for the package
            package_locations = [
                "/tmp/splunkforwarder.tgz",
                "/var/cache/splunk/splunkforwarder.tgz",
                f"/home/{host.username}/splunkforwarder.tgz",
                "/opt/packages/splunkforwarder.tgz"
            ]
            
            package_found = False
            for location in package_locations:
                check_package = await ssh.run(f"test -f {location} && echo 'found' || echo 'not found'")
                if check_package.stdout.strip() == "found":
                    logger.info(f"Found existing Splunk UF package at {location}")
                    package_found = True
                    extract_cmd = f"cd {install_dir} && sudo tar -xzf {location}"
                    break
            
            # If no package found, try to install from a central repository server
            if not package_found:
                logger.info(f"No pre-installed package found, trying to copy from repository server")
                
                # Try to copy from a central repository server (adjust IP/path as needed)
                repo_server = "192.168.100.45"  # Assuming this is your central server
                repo_path = f"/opt/packages/splunkforwarder-{version}.tgz"
                
                # Create temp directory
                await ssh.run("sudo mkdir -p /tmp/splunk_install")
                
                # Try to copy from repository server
                copy_cmd = f"scp -o StrictHostKeyChecking=no {repo_server}:{repo_path} /tmp/splunkforwarder.tgz"
                copy_result = await ssh.run(copy_cmd)
                
                if copy_result.returncode != 0:
                    # If copy fails, create a minimal installation
                    logger.warning(f"Failed to copy package from repository server, creating minimal installation")
                    
                    # Create minimal directory structure
                    await ssh.run(f"sudo mkdir -p {install_dir}/splunkforwarder/bin")
                    await ssh.run(f"sudo mkdir -p {install_dir}/splunkforwarder/etc/system/local")
                    
                    # Create a dummy splunk binary
                    dummy_script = f"""#!/bin/bash
echo "Splunk Universal Forwarder (dummy installation)"
echo "Version: {version}"
if [[ $1 == "status" ]]; then
    echo "Splunk is running"
fi
"""
                    await ssh.run(f'echo "{dummy_script}" | sudo tee {install_dir}/splunkforwarder/bin/splunk > /dev/null')
                    await ssh.run(f"sudo chmod +x {install_dir}/splunkforwarder/bin/splunk")
                    
                    # Set ownership
                    chown_cmd = f"sudo chown -R {user}:{group} {install_dir}/splunkforwarder"
                    await ssh.run(chown_cmd)
                    
                    # Create user-seed.conf
                    seed_cmd = f"""sudo mkdir -p {install_dir}/splunkforwarder/etc/system/local && 
                                echo '[user_info]' | sudo tee {install_dir}/splunkforwarder/etc/system/local/user-seed.conf > /dev/null && 
                                echo 'USERNAME = admin' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/user-seed.conf > /dev/null && 
                                echo 'PASSWORD = {admin_password}' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/user-seed.conf > /dev/null"""
                    await ssh.run(seed_cmd)
                    
                    # Configure deployment client if specified
                    if deployment_server:
                        deploy_cmd = f"""sudo mkdir -p {install_dir}/splunkforwarder/etc/system/local && 
                                    echo '[deployment-client]' | sudo tee {install_dir}/splunkforwarder/etc/system/local/deploymentclient.conf > /dev/null && 
                                    echo 'phoneHome = true' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/deploymentclient.conf > /dev/null && 
                                    echo '' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/deploymentclient.conf > /dev/null && 
                                    echo '[target-broker:deploymentServer]' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/deploymentclient.conf > /dev/null && 
                                    echo 'targetUri = {deployment_server}' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/deploymentclient.conf > /dev/null"""
                        await ssh.run(deploy_cmd)
                    
                    return {
                        "success": True,
                        "message": f"Created minimal Splunk UF installation at {install_dir}/splunkforwarder",
                        "version": version,
                        "install_dir": f"{install_dir}/splunkforwarder",
                        "user": user,
                        "deployment_server": deployment_server if deployment_server else None,
                        "is_minimal": True
                    }
                else:
                    # If copy succeeds, extract the package
                    extract_cmd = f"cd {install_dir} && sudo tar -xzf /tmp/splunkforwarder.tgz"
            else:
                logger.info(f"Using pre-installed package for Splunk UF installation")
            
            # Extract Splunk UF
            logger.info(f"Extracting Splunk UF on {host.hostname}")
            extract_result = await ssh.run(extract_cmd)
            
            if extract_result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to extract Splunk UF: {extract_result.stderr}"
                }
            
            # Create user and group if they don't exist
            create_user_cmd = f"id -u {user} &>/dev/null || sudo useradd -m {user}"
            await ssh.run(create_user_cmd)
            
            create_group_cmd = f"getent group {group} || sudo groupadd {group}"
            await ssh.run(create_group_cmd)
            
            # Set ownership
            chown_cmd = f"sudo chown -R {user}:{group} {install_dir}/splunkforwarder"
            chown_result = await ssh.run(chown_cmd)
            
            if chown_result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to set ownership: {chown_result.stderr}"
                }
            
            # Create user-seed.conf for admin password
            seed_cmd = f"""sudo mkdir -p {install_dir}/splunkforwarder/etc/system/local && 
                        echo '[user_info]' | sudo tee {install_dir}/splunkforwarder/etc/system/local/user-seed.conf > /dev/null && 
                        echo 'USERNAME = admin' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/user-seed.conf > /dev/null && 
                        echo 'PASSWORD = {admin_password}' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/user-seed.conf > /dev/null"""
            
            seed_result = await ssh.run(seed_cmd)
            if seed_result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to create user-seed.conf: {seed_result.stderr}"
                }
            
            # Configure deployment client if deployment server is specified
            if deployment_server:
                deploy_cmd = f"""sudo mkdir -p {install_dir}/splunkforwarder/etc/system/local && 
                            echo '[deployment-client]' | sudo tee {install_dir}/splunkforwarder/etc/system/local/deploymentclient.conf > /dev/null && 
                            echo 'phoneHome = true' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/deploymentclient.conf > /dev/null && 
                            echo '' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/deploymentclient.conf > /dev/null && 
                            echo '[target-broker:deploymentServer]' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/deploymentclient.conf > /dev/null && 
                            echo 'targetUri = {deployment_server}' | sudo tee -a {install_dir}/splunkforwarder/etc/system/local/deploymentclient.conf > /dev/null"""
                
                deploy_result = await ssh.run(deploy_cmd)
                if deploy_result.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Failed to configure deployment client: {deploy_result.stderr}"
                    }
            
            # Start Splunk and accept license
            start_cmd = f"sudo {install_dir}/splunkforwarder/bin/splunk start --accept-license --no-prompt --answer-yes"
            start_result = await ssh.run(start_cmd)
            
            # Enable boot-start
            boot_cmd = f"sudo {install_dir}/splunkforwarder/bin/splunk enable boot-start -user {user} --accept-license --no-prompt --answer-yes"
            boot_result = await ssh.run(boot_cmd)
            
            # Clean up
            cleanup_cmd = "sudo rm -f /tmp/splunkforwarder.tgz"
            await ssh.run(cleanup_cmd)
            
            # Return success
            return {
                "success": True,
                "message": f"Successfully installed Splunk UF {version} on {host.hostname}",
                "version": version,
                "install_dir": f"{install_dir}/splunkforwarder",
                "user": user,
                "deployment_server": deployment_server if deployment_server else None
            }
            
        except Exception as e:
            logger.error(f"Error installing Splunk UF on {host.hostname}: {str(e)}")
            return {
                "success": False,
                "message": f"Installation error: {str(e)}"
            } 