"""
Splunk Universal Forwarder Installer Module
Installs Splunk Universal Forwarder on hosts via SSH
"""
import asyncio
import os
import logging
from typing import Dict, Any, Optional

from backend.automation.ssh_client import get_ssh_client
from backend.models import Host, SoftwarePackage
from backend.models.database import SessionLocal
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def get_package_download_url(version: str, architecture: str = "x86_64", package_type: str = "splunk_uf") -> Optional[str]:
    """
    Get download URL from Package Inventory based on version and architecture.
    
    Args:
        version: Splunk version (e.g., "9.4.3")
        architecture: System architecture (e.g., "x86_64", "arm64") 
        package_type: Package type ("splunk_uf" or "splunk_enterprise")
        
    Returns:
        Download URL string if found, None otherwise
    """
    try:
        # Get database session
        db = SessionLocal()
        try:
            # Query for the specific package
            package = db.query(SoftwarePackage).filter(
                SoftwarePackage.package_type == package_type,
                SoftwarePackage.version == version,
                SoftwarePackage.status == "active"
            ).first()
            
            if not package:
                logger.warning(f"No package found for {package_type} version {version}")
                return None
            
            # Check if package has new downloads structure
            downloads = getattr(package, 'downloads', None) or []
            if downloads and len(downloads) > 0:
                # Find download entry for the specified architecture
                for download in downloads:
                    if isinstance(download, dict) and download.get('architecture') == architecture:
                        url = download.get('download_url')
                        if url:
                            logger.info(f"Found download URL for {package_type} {version} {architecture}: {url}")
                            return url
                
                # If exact architecture not found, try x86_64 as fallback
                if architecture != "x86_64":
                    for download in downloads:
                        if isinstance(download, dict) and download.get('architecture') == "x86_64":
                            url = download.get('download_url')
                            if url:
                                logger.warning(f"Architecture {architecture} not found, using x86_64 fallback: {url}")
                                return url
            
            # Fallback to legacy download_url field
            legacy_url = getattr(package, 'download_url', None)
            if legacy_url:
                logger.info(f"Using legacy download URL for {package_type} {version}: {legacy_url}")
                return legacy_url
            
            logger.error(f"No download URL found for {package_type} version {version} architecture {architecture}")
            return None
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error querying package inventory: {str(e)}")
        return None

# Legacy function for backward compatibility - now uses Package Inventory
def get_splunk_download_url(version: str, architecture: str = "x86_64") -> str:
    """
    Generate a download URL for a given Splunk UF version and architecture.
    Now uses Package Inventory instead of hardcoded URLs.
    """
    url = get_package_download_url(version, architecture, "splunk_uf")
    if url:
        return url
    
    # If not found in Package Inventory, log error
    logger.error(f"No download URL found in Package Inventory for Splunk UF version {version} architecture {architecture}")
    raise ValueError(f"Splunk UF version {version} for architecture {architecture} not found in Package Inventory. Please add it to the database first.")

# Function to get all possible download URLs for a specific version and architecture
def get_all_download_urls(version: str, architecture: str = "x86_64", package_type: str = "splunk_uf") -> list:
    """
    Returns a list of download URLs for the given version and architecture from Package Inventory.
    """
    url = get_package_download_url(version, architecture, package_type)
    if url:
        return [url]
    
    # Try to find alternative architectures if specified architecture not found
    urls = []
    try:
        db = SessionLocal()
        try:
            package = db.query(SoftwarePackage).filter(
                SoftwarePackage.package_type == package_type,
                SoftwarePackage.version == version,
                SoftwarePackage.status == "active"
            ).first()
            
            if package:
                downloads = getattr(package, 'downloads', None) or []
                if downloads:
                    # Get all available download URLs for this package
                    for download in downloads:
                        if isinstance(download, dict):
                            url = download.get('download_url')
                            if url:
                                urls.append(url)
                                logger.info(f"Alternative download URL: {url} (architecture: {download.get('architecture')})")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error getting alternative download URLs: {str(e)}")
    
    if not urls:
        logger.error(f"No download URLs found for {package_type} version {version}")
    
    return urls

async def install_splunk_uf(host: Host, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Install Splunk Universal Forwarder on a host via SSH
    
    Args:
        host: The host object containing connection information
        params: Dictionary of installation parameters
            - version: Splunk UF version to install
            - architecture: System architecture (default: x86_64)
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
    architecture = params.get("architecture", "x86_64")
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
    
    # Get all possible download URLs for the specified version and architecture
    download_urls = get_all_download_urls(version, architecture, "splunk_uf")
    if not download_urls:
        return {
            "success": False,
            "message": f"No download URL available for Splunk UF version {version} architecture {architecture}"
        }
    
    # Log primary URL
    logger.info(f"Primary download URL for Splunk UF {version} ({architecture}): {download_urls[0]}")
    if len(download_urls) > 1:
        logger.info(f"Found {len(download_urls)} potential download URLs to try")
    
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
                "message": f"Dry run - would have installed Splunk UF {version} ({architecture})",
                "is_dry_run": True,
                "version": version,
                "architecture": architecture,
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
            
            # Check if the installation directory was manually set to include "splunkforwarder"
            actual_extract_dir = install_dir
            if install_dir.endswith("/splunkforwarder"):
                # User already specified the full path including splunkforwarder
                logger.info(f"Using exact install path as specified: {install_dir}")
            else:
                # Make sure installation directory doesn't end with a slash
                if actual_extract_dir.endswith("/"):
                    actual_extract_dir = actual_extract_dir[:-1]
                logger.info(f"Will extract to parent directory: {actual_extract_dir}")
            
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
            
            # Try downloading from each URL until one succeeds
            download_success = False
            all_download_errors = []
            
            for url_index, download_url in enumerate(download_urls):
                # Try curl first if available
                if has_curl:
                    logger.info(f"Attempting download with curl from URL #{url_index+1}: {download_url}")
                    download_cmd = f"cd /tmp/splunk_install && sudo curl -v -L -o splunkforwarder.tgz '{download_url}' 2>&1"
                    download_result = await ssh.run(download_cmd)
                    
                    if download_result.returncode == 0:
                        logger.info(f"Curl command stdout: {download_result.stdout[:200]}...")
                        download_success = True
                        logger.info(f"Successfully downloaded from {download_url}")
                        break
                    else:
                        error = f"Curl error with URL #{url_index+1}: {download_result.stderr}"
                        logger.error(f"Full curl error: {download_result.stderr}")
                        logger.error(f"Curl command output: {download_result.stdout}")
                        all_download_errors.append(error)
                        logger.warning(error)
                
                # Try wget if curl failed or isn't available
                if not download_success and has_wget:
                    logger.info(f"Attempting download with wget from URL #{url_index+1}: {download_url}")
                    download_cmd = f"cd /tmp/splunk_install && sudo wget -v -O splunkforwarder.tgz '{download_url}' 2>&1"
                    download_result = await ssh.run(download_cmd)
                    
                    if download_result.returncode == 0:
                        logger.info(f"Wget command stdout: {download_result.stdout[:200]}...")
                        download_success = True
                        logger.info(f"Successfully downloaded from {download_url}")
                        break
                    else:
                        error = f"Wget error with URL #{url_index+1}: {download_result.stderr}"
                        logger.error(f"Full wget error: {download_result.stderr}")
                        logger.error(f"Wget command output: {download_result.stdout}")
                        all_download_errors.append(error)
                        logger.warning(error)
            
            # If standard methods failed, try our custom download script
            if not download_success:
                logger.info("Standard download methods failed, trying custom download script")
                
                # Test direct connectivity to Splunk's servers
                can_connect, connection_output = await test_connectivity_to_splunk(ssh)
                logger.info(f"Direct connectivity to Splunk servers: {can_connect}, Output: {connection_output}")
                
                # Try each URL with our custom script
                for url_index, download_url in enumerate(download_urls):
                    logger.info(f"Trying custom download script with URL #{url_index+1}: {download_url}")
                    
                    # Create our custom download script
                    script_path = await create_download_script(ssh, download_url, "/tmp/splunk_install/splunkforwarder.tgz")
                    if script_path:
                        # Run the script
                        script_result = await ssh.run(f"cd /tmp/splunk_install && sudo bash {script_path}")
                        logger.info(f"Custom script output: {script_result.stdout}")
                        
                        # Check if file exists and has content
                        check_cmd = "test -s /tmp/splunk_install/splunkforwarder.tgz && echo 'success' || echo 'failed'"
                        check_result = await ssh.run(check_cmd)
                        
                        if "success" in check_result.stdout:
                            download_success = True
                            logger.info(f"Successfully downloaded using custom script from {download_url}")
                            break
                        else:
                            error = f"Custom script failed with URL #{url_index+1}"
                            all_download_errors.append(error)
                            logger.warning(error)
                
                # If we've tried everything and still failed
                if not download_success:
                    # Check for common issues
                    connectivity_check = await ssh.run("ping -c 1 download.splunk.com")
                    if connectivity_check.returncode != 0:
                        return {
                            "success": False,
                            "message": f"Cannot reach download.splunk.com. Please check network connectivity.\nError details: {', '.join(all_download_errors)}"
                        }
                    
                    return {
                        "success": False,
                        "message": f"Failed to download Splunk UF after trying all methods. Error details: {', '.join(all_download_errors)}"
                    }
            
            # Verify the download was successful
            verify_cmd = "ls -la /tmp/splunk_install/splunkforwarder.tgz"
            verify_result = await ssh.run(verify_cmd)
            
            if verify_result.returncode != 0 or "No such file" in verify_result.stderr:
                return {
                    "success": False,
                    "message": "Failed to verify Splunk UF download. The file does not exist after download."
                }
            
            logger.info(f"Download verification output: {verify_result.stdout}")
                
            # Validate the downloaded file is actually a valid gzip archive
            valid_file = True  # Start by assuming it's valid since we successfully downloaded
            
            # Check file exists and has reasonable size
            size_check = await ssh.run("du -h /tmp/splunk_install/splunkforwarder.tgz")
            if size_check.returncode == 0:
                file_size = size_check.stdout.strip().split()[0]
                logger.info(f"Downloaded Splunk UF package size: {file_size}")
                
                # If file is suspiciously small, it might be an error page
                if "k" in file_size or file_size.startswith("0"):
                    valid_file = False
                    logger.warning(f"File size is suspiciously small: {file_size}")
            
            # Try to check file type but don't fail if command not found
            gzip_check = await ssh.run("which file > /dev/null && file /tmp/splunk_install/splunkforwarder.tgz || echo 'file command not found'")
            logger.info(f"File type check result: {gzip_check.stdout}")
            
            # Skip validation if commands aren't available
            if "command not found" not in gzip_check.stdout:
                valid_file = False
                for valid_type in ["gzip compressed data", "tar archive", "data", "ASCII text"]:
                    if valid_type.lower() in gzip_check.stdout.lower():
                        valid_file = True
                        logger.info(f"File appears to be valid: {valid_type} detected")
                        break
            
            # Only proceed with more validation if we've determined the file is invalid
            if not valid_file:
                # Try a simple check - if tar can list contents, it's probably valid
                tar_check = await ssh.run("tar -tzf /tmp/splunk_install/splunkforwarder.tgz > /dev/null 2>&1")
                if tar_check.returncode == 0:
                    logger.info("File validated with tar command")
                    valid_file = True
                else:
                    # Try to get more detailed information without requiring hexdump
                    head_check = await ssh.run("head -c 100 /tmp/splunk_install/splunkforwarder.tgz | strings")
                    logger.info(f"First few strings in file: {head_check.stdout}")
                    
                    # Try direct extraction as a last resort
                    logger.info("Attempting direct extraction to validate archive...")
                    extract_check = await ssh.run(f"cd {actual_extract_dir} && sudo tar -xzf /tmp/splunk_install/splunkforwarder.tgz")
                    if extract_check.returncode == 0:
                        logger.info("Extraction successful - archive is valid")
                        valid_file = True
            
            if not valid_file:
                return {
                    "success": False,
                    "message": "Downloaded file does not appear to be a valid archive. Please try again or contact support."
                }
            
            # Extract Splunk UF
            logger.info(f"Extracting Splunk UF on {host.hostname}")
            extract_cmd = f"cd {actual_extract_dir} && sudo tar -xzf /tmp/splunk_install/splunkforwarder.tgz"
            extract_result = await ssh.run(extract_cmd)
            
            if extract_result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to extract Splunk UF: {extract_result.stderr}"
                }
            
            # Create user and group if they don't exist
            create_user_cmd = f"id -u {user} &>/dev/null || sudo useradd -m -s /bin/bash {user}"
            user_result = await ssh.run(create_user_cmd)
            logger.info(f"Create user result: {user_result.stdout}")
            
            create_group_cmd = f"getent group {group} || sudo groupadd {group}"
            group_result = await ssh.run(create_group_cmd)
            logger.info(f"Create group result: {group_result.stdout}")
            
            # Add user to group if they're different
            if user != group:
                add_to_group_cmd = f"sudo usermod -a -G {group} {user}"
                await ssh.run(add_to_group_cmd)
            
            # Set initial ownership and permissions
            logger.info("Setting initial ownership and permissions...")
            initial_perms_cmd = f"""sudo chown -R {user}:{group} {actual_extract_dir}/splunkforwarder && 
                               sudo chmod -R 755 {actual_extract_dir}/splunkforwarder"""
            initial_perms_result = await ssh.run(initial_perms_cmd)
            
            if initial_perms_result.returncode != 0:
                logger.warning(f"Initial permissions warning: {initial_perms_result.stderr}")
            
            # Create configuration directory with proper permissions as splunk user
            config_dir_cmd = f"sudo -u {user} mkdir -p {actual_extract_dir}/splunkforwarder/etc/system/local"
            config_dir_result = await ssh.run(config_dir_cmd)
            
            if config_dir_result.returncode != 0:
                logger.error(f"Failed to create config directory: {config_dir_result.stderr}")
                # Try as root and then fix ownership
                await ssh.run(f"sudo mkdir -p {actual_extract_dir}/splunkforwarder/etc/system/local")
                await ssh.run(f"sudo chown -R {user}:{group} {actual_extract_dir}/splunkforwarder/etc")
                await ssh.run(f"sudo chmod -R 755 {actual_extract_dir}/splunkforwarder/etc")
            
            # Create user-seed.conf as the splunk user
            seed_content = f"""[user_info]
USERNAME = admin
PASSWORD = {admin_password}"""
            
            # First, ensure the target directory has proper permissions
            seed_dir = f"{actual_extract_dir}/splunkforwarder/etc/system/local"
            await ssh.run(f"sudo chmod 755 {seed_dir}")
            
            seed_cmd = f"""sudo -u {user} bash -c 'cat > {seed_dir}/user-seed.conf << \"EOF\"
{seed_content}
EOF'"""
            
            seed_result = await ssh.run(seed_cmd)
            if seed_result.returncode != 0:
                logger.error(f"Failed to create user-seed.conf as {user}: {seed_result.stderr}")
                # Fallback: create as root and fix ownership
                logger.info("Attempting fallback: creating user-seed.conf as root")
                fallback_cmd = f"""sudo bash -c 'cat > {seed_dir}/user-seed.conf << \"EOF\"
{seed_content}
EOF'"""
                fallback_result = await ssh.run(fallback_cmd)
                
                if fallback_result.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Failed to create user-seed.conf: {seed_result.stderr}. Fallback also failed: {fallback_result.stderr}",
                        "status_note": "Installation failed",
                        "actual_status": "failed"
                    }
                
                # Fix ownership of the created file
                await ssh.run(f"sudo chown {user}:{group} {seed_dir}/user-seed.conf")
                await ssh.run(f"sudo chmod 600 {seed_dir}/user-seed.conf")
                logger.info("Successfully created user-seed.conf using fallback method")
            
            # Configure deployment client if deployment server is specified
            if deployment_server:
                deploy_content = f"""[deployment-client]
phoneHome = true

[target-broker:deploymentServer]
targetUri = {deployment_server}"""
                
                deploy_cmd = f"""sudo -u {user} bash -c 'cat > {actual_extract_dir}/splunkforwarder/etc/system/local/deploymentclient.conf << \"EOF\"
{deploy_content}
EOF'"""
                
                deploy_result = await ssh.run(deploy_cmd)
                if deploy_result.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Failed to configure deployment client: {deploy_result.stderr}"
                    }
            
            # Fix ownership of all config files
            config_perms_cmd = f"sudo chown -R {user}:{group} {actual_extract_dir}/splunkforwarder/etc"
            await ssh.run(config_perms_cmd)
            
            # Start Splunk as the splunk user (this is critical!)
            logger.info(f"Starting Splunk UF as user {user}...")
            start_cmd = f"sudo -u {user} {actual_extract_dir}/splunkforwarder/bin/splunk start --accept-license --no-prompt --answer-yes"
            start_result = await ssh.run(start_cmd)
            
            if start_result.returncode != 0:
                logger.error(f"Splunk start failed: {start_result.stderr}")
                # Try to fix permissions and start again
                logger.info("Attempting to fix permissions and restart...")
                fix_perms_cmd = f"""sudo chown -R {user}:{group} {actual_extract_dir}/splunkforwarder && 
                               sudo chmod 755 {actual_extract_dir}/splunkforwarder/bin/splunk && 
                               sudo chmod -R 755 {actual_extract_dir}/splunkforwarder/var"""
                await ssh.run(fix_perms_cmd)
                
                # Try starting again
                start_result = await ssh.run(start_cmd)
                if start_result.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Failed to start Splunk UF: {start_result.stderr}"
                    }
            
            # Enable boot-start as splunk user
            boot_cmd = f"sudo {actual_extract_dir}/splunkforwarder/bin/splunk enable boot-start -user {user} --accept-license --no-prompt --answer-yes"
            boot_result = await ssh.run(boot_cmd)
            
            # Final ownership and permission fix
            logger.info("Applying final ownership and permission fixes...")
            final_perms_cmd = f"""sudo chown -R {user}:{group} {actual_extract_dir}/splunkforwarder && 
                             sudo chmod -R u+rwX,g+rX,o+rX {actual_extract_dir}/splunkforwarder && 
                             sudo chmod -R u+rw {actual_extract_dir}/splunkforwarder/var && 
                             sudo chmod -R u+rw {actual_extract_dir}/splunkforwarder/etc"""
            final_perms_result = await ssh.run(final_perms_cmd)
            
            # Verify Splunk is running
            status_cmd = f"sudo -u {user} {actual_extract_dir}/splunkforwarder/bin/splunk status"
            status_result = await ssh.run(status_cmd)
            logger.info(f"Splunk status check: {status_result.stdout}")
            
            if "splunkd is running" not in status_result.stdout:
                logger.warning("Splunk may not be running properly after installation")
            
            # Clean up
            cleanup_cmd = "sudo rm -rf /tmp/splunk_install"
            await ssh.run(cleanup_cmd)
            
            # Return success
            return {
                "success": True,
                "message": f"Successfully installed Splunk UF {version} ({architecture}) on {host.hostname}",
                "version": version,
                "architecture": architecture,
                "install_dir": f"{actual_extract_dir}/splunkforwarder",
                "user": user,
                "deployment_server": deployment_server if deployment_server else None
            }
            
        except Exception as e:
            logger.error(f"Error installing Splunk UF on {host.hostname}: {str(e)}")
            return {
                "success": False,
                "message": f"Installation error: {str(e)}"
            }

# Function to test direct connectivity to Splunk's download servers
async def test_connectivity_to_splunk(ssh):
    """Test direct connectivity to Splunk's download servers"""
    test_cmd = "curl -I https://download.splunk.com 2>/dev/null | head -n 1"
    result = await ssh.run(test_cmd)
    if result.returncode == 0 and "HTTP" in result.stdout:
        return True, result.stdout
    return False, result.stdout

# Function to create a download script that uses multiple methods
async def create_download_script(ssh, download_url, output_path):
    """Create a shell script on the remote host to download a file using multiple methods"""
    script_content = f'''#!/bin/bash
echo "Attempting to download {download_url}"
echo "Using multiple methods..."

# Function to check if a tool exists
has_tool() {{
  command -v "$1" >/dev/null 2>&1
}}

# Try curl
if has_tool curl; then
  echo "Trying curl..."
  curl -L -o "{output_path}" "{download_url}"
  if [ $? -eq 0 ] && [ -s "{output_path}" ]; then
    echo "Download successful with curl"
    exit 0
  else
    echo "Curl download failed"
  fi
fi

# Try wget
if has_tool wget; then
  echo "Trying wget..."
  wget -O "{output_path}" "{download_url}"
  if [ $? -eq 0 ] && [ -s "{output_path}" ]; then
    echo "Download successful with wget"
    exit 0
  else
    echo "Wget download failed"
  fi
fi

# Try Python
if has_tool python3 || has_tool python; then
  echo "Trying Python..."
  PY_CMD=$(command -v python3 || command -v python)
  $PY_CMD -c "
import urllib.request
import ssl

try:
    # Create an SSL context that doesn't verify certificates
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Open the URL with the SSL context
    with urllib.request.urlopen('{download_url}', context=ctx) as response, open('{output_path}', 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    print('Download successful with Python')
    exit(0)
except Exception as e:
    print(f'Python download error: {{e}}')
    exit(1)
"
  if [ $? -eq 0 ] && [ -s "{output_path}" ]; then
    echo "Download successful with Python"
    exit 0
  fi
fi

echo "All download methods failed"
exit 1
'''

    # Create the script
    script_path = "/tmp/splunk_install/download.sh"
    create_script_cmd = f'''cat > {script_path} << 'EOF'
{script_content}
EOF
chmod +x {script_path}
'''
    result = await ssh.run(create_script_cmd)
    return script_path if result.returncode == 0 else None 

async def repair_splunk_permissions(host: Host, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Repair permission issues on an existing Splunk UF installation
    
    Args:
        host: The host object containing connection information
        params: Dictionary of repair parameters
            - install_dir: Splunk installation directory (default: /opt/splunkforwarder)
            - user: User to run Splunk as (default: splunk)
            - group: Group to run Splunk as (default: splunk)
            
    Returns:
        Dictionary with repair results
    """
    # Extract parameters with defaults
    install_dir = params.get("install_dir", "/opt/splunkforwarder")
    user = params.get("user", "splunk")
    group = params.get("group", "splunk")
    
    logger.info(f"Repairing Splunk UF permissions on {host.hostname}")
    
    # Connect to the host via SSH
    async with get_ssh_client(host) as ssh:
        if not ssh:
            return {
                "success": False,
                "message": "Could not establish SSH connection"
            }
        
        try:
            # Check if Splunk directory exists
            check_cmd = f"test -d {install_dir}"
            check_result = await ssh.run(check_cmd)
            
            if check_result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Splunk installation directory {install_dir} not found"
                }
            
            # Stop Splunk if it's running (as root to ensure we can stop it)
            logger.info("Stopping Splunk UF...")
            stop_cmd = f"sudo {install_dir}/bin/splunk stop"
            stop_result = await ssh.run(stop_cmd)
            logger.info(f"Stop result: {stop_result.stdout}")
            
            # Ensure user and group exist
            create_user_cmd = f"id -u {user} &>/dev/null || sudo useradd -m -s /bin/bash {user}"
            await ssh.run(create_user_cmd)
            
            create_group_cmd = f"getent group {group} || sudo groupadd {group}"
            await ssh.run(create_group_cmd)
            
            # Add user to group if they're different
            if user != group:
                add_to_group_cmd = f"sudo usermod -a -G {group} {user}"
                await ssh.run(add_to_group_cmd)
            
            # Fix ownership recursively
            logger.info("Fixing ownership...")
            chown_cmd = f"sudo chown -R {user}:{group} {install_dir}"
            chown_result = await ssh.run(chown_cmd)
            
            if chown_result.returncode != 0:
                logger.warning(f"Chown warning: {chown_result.stderr}")
            
            # Fix permissions - directories should be 755, files should be 644 with exceptions
            logger.info("Fixing permissions...")
            
            # Set base permissions
            base_perms_cmd = f"""sudo find {install_dir} -type d -exec chmod 755 {{}} \\; && 
                           sudo find {install_dir} -type f -exec chmod 644 {{}} \\;"""
            await ssh.run(base_perms_cmd)
            
            # Set executable permissions for binaries
            bin_perms_cmd = f"""sudo chmod 755 {install_dir}/bin/* && 
                          sudo chmod -R u+rwx {install_dir}/var && 
                          sudo chmod -R u+rwx {install_dir}/etc"""
            await ssh.run(bin_perms_cmd)
            
            # Special permissions for specific directories
            special_perms_cmd = f"""sudo chmod 700 {install_dir}/etc/auth 2>/dev/null || true && 
                              sudo chmod -R 755 {install_dir}/var/run 2>/dev/null || true && 
                              sudo chmod -R 755 {install_dir}/var/log 2>/dev/null || true"""
            await ssh.run(special_perms_cmd)
            
            # Remove any lock files or PID files that might be owned by root
            cleanup_cmd = f"""sudo rm -f {install_dir}/var/run/splunk/splunkd.pid && 
                        sudo rm -f {install_dir}/var/run/splunk/*.lock && 
                        sudo rm -f {install_dir}/var/lib/splunk/kvstore/mongo/*.lock"""
            await ssh.run(cleanup_cmd)
            
            # Create necessary directories with correct ownership
            create_dirs_cmd = f"""sudo -u {user} mkdir -p {install_dir}/var/run/splunk && 
                            sudo -u {user} mkdir -p {install_dir}/var/log/splunk && 
                            sudo -u {user} mkdir -p {install_dir}/var/lib/splunk"""
            await ssh.run(create_dirs_cmd)
            
            # Final ownership pass to make sure everything is correct
            final_chown_cmd = f"sudo chown -R {user}:{group} {install_dir}"
            await ssh.run(final_chown_cmd)
            
            # Start Splunk as the correct user
            logger.info(f"Starting Splunk UF as user {user}...")
            start_cmd = f"sudo -u {user} {install_dir}/bin/splunk start --no-prompt"
            start_result = await ssh.run(start_cmd)
            
            # Check if Splunk started successfully
            if start_result.returncode != 0:
                logger.error(f"Failed to start Splunk: {start_result.stderr}")
                return {
                    "success": False,
                    "message": f"Permission repair completed but failed to start Splunk: {start_result.stderr}"
                }
            
            # Verify Splunk status
            status_cmd = f"sudo -u {user} {install_dir}/bin/splunk status"
            status_result = await ssh.run(status_cmd)
            
            logger.info(f"Splunk status after repair: {status_result.stdout}")
            
            return {
                "success": True,
                "message": f"Successfully repaired Splunk UF permissions on {host.hostname}",
                "install_dir": install_dir,
                "user": user,
                "status": status_result.stdout.strip()
            }
            
        except Exception as e:
            logger.error(f"Error repairing Splunk UF permissions on {host.hostname}: {str(e)}")
            return {
                "success": False,
                "message": f"Permission repair error: {str(e)}"
            } 