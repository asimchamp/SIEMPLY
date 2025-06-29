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

# Function to dynamically generate download URL for any version
def get_splunk_download_url(version: str) -> str:
    """
    Generate a download URL for a given Splunk UF version.
    Falls back to the predefined URLs if available.
    """
    if version in SPLUNK_UF_URLS:
        return SPLUNK_UF_URLS[version]
    
    # For versions not in the predefined list, generate a URL based on the pattern
    # Note: This is a best guess and may not work for all versions
    return f"https://download.splunk.com/products/universalforwarder/releases/{version}/linux/splunkforwarder-{version}-Linux-x86_64.tgz"

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
    
    # Get download URL for the specified version
    download_url = get_splunk_download_url(version)
    logger.info(f"Using download URL for Splunk UF {version}: {download_url}")
    
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
            
            # Create a temp directory for downloads
            await ssh.run("sudo mkdir -p /tmp/splunk_install")
            
            # Download Splunk UF directly from the internet
            logger.info(f"Downloading Splunk UF {version} on {host.hostname} from {download_url}")
            
            # Check if curl is available
            curl_check = await ssh.run("which curl")
            has_curl = curl_check.returncode == 0
            
            # Check if wget is available
            wget_check = await ssh.run("which wget")
            has_wget = wget_check.returncode == 0
            
            if not has_curl and not has_wget:
                return {
                    "success": False,
                    "message": "Neither curl nor wget is available on the target host. Please install one of these tools."
                }
            
            download_success = False
            download_error = ""
            
            # Try curl first if available
            if has_curl:
                logger.info(f"Attempting download with curl on {host.hostname}")
                download_cmd = f"cd /tmp/splunk_install && sudo curl -L -o splunkforwarder.tgz {download_url}"
                download_result = await ssh.run(download_cmd)
                
                if download_result.returncode == 0:
                    download_success = True
                else:
                    download_error = f"Curl error: {download_result.stderr}"
                    logger.warning(f"Curl download failed on {host.hostname}: {download_error}")
            
            # Try wget if curl failed or isn't available
            if not download_success and has_wget:
                logger.info(f"Attempting download with wget on {host.hostname}")
                download_cmd = f"cd /tmp/splunk_install && sudo wget -O splunkforwarder.tgz {download_url}"
                download_result = await ssh.run(download_cmd)
                
                if download_result.returncode == 0:
                    download_success = True
                else:
                    if download_error:
                        download_error += f"\nWget error: {download_result.stderr}"
                    else:
                        download_error = f"Wget error: {download_result.stderr}"
                    logger.warning(f"Wget download failed on {host.hostname}: {download_result.stderr}")
            
            if not download_success:
                # Check for common issues
                connectivity_check = await ssh.run(f"ping -c 1 download.splunk.com")
                if connectivity_check.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Cannot reach download.splunk.com. Please check network connectivity.\nError details: {download_error}"
                    }
                
                return {
                    "success": False,
                    "message": f"Failed to download Splunk UF. Error details: {download_error}"
                }
            
            # Verify the download was successful
            verify_cmd = "ls -la /tmp/splunk_install/splunkforwarder.tgz"
            verify_result = await ssh.run(verify_cmd)
            
            if verify_result.returncode != 0 or "No such file" in verify_result.stderr:
                return {
                    "success": False,
                    "message": "Failed to verify Splunk UF download. The file does not exist after download."
                }
                
            # Check file size to ensure it's not empty
            size_check = await ssh.run("du -h /tmp/splunk_install/splunkforwarder.tgz")
            if size_check.returncode == 0:
                file_size = size_check.stdout.strip().split()[0]
                logger.info(f"Downloaded Splunk UF package size: {file_size}")
                
                # If file is suspiciously small, it might be an error page
                if "k" in file_size or file_size.startswith("0"):
                    content_check = await ssh.run("head -n 20 /tmp/splunk_install/splunkforwarder.tgz")
                    if "html" in content_check.stdout.lower() or "error" in content_check.stdout.lower():
                        return {
                            "success": False,
                            "message": "Downloaded file appears to be an HTML error page, not a Splunk package."
                        }
            
            # Extract Splunk UF
            logger.info(f"Extracting Splunk UF on {host.hostname}")
            extract_cmd = f"cd {install_dir} && sudo tar -xzf /tmp/splunk_install/splunkforwarder.tgz"
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
            cleanup_cmd = "sudo rm -rf /tmp/splunk_install"
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