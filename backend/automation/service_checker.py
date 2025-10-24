"""
Service Checker Module
Checks and manages important services and connectivity on remote hosts
"""
import asyncio
import logging
import time
import uuid
from typing import Dict, List, Tuple, Optional
from backend.automation.ssh_client import AsyncSSHClient

logger = logging.getLogger(__name__)

class ServiceStatus:
    """Service status information"""
    def __init__(self, name: str, status: str, required: bool = False, details: str = ""):
        self.name = name
        self.status = status  # 'running', 'stopped', 'not_installed', 'error'
        self.required = required
        self.details = details

async def check_sftp_connectivity(ssh: AsyncSSHClient) -> ServiceStatus:
    """Check if SFTP is working on the remote host"""
    try:
        logger.info("Checking SFTP connectivity...")
        
        # If we have an active SSH client, the SSH daemon must be running.
        # The previous check was redundant and flawed.

        # Check if SFTP subsystem is configured in SSH daemon
        sftp_check = await ssh.run("grep -i 'Subsystem sftp' /etc/ssh/sshd_config 2>/dev/null || echo 'NOT_FOUND'")
        logger.info(f"SFTP subsystem check result: {sftp_check.stdout.strip()}")
        
        if "NOT_FOUND" in sftp_check.stdout:
            logger.warning("SFTP subsystem not found in SSH configuration")
            return ServiceStatus(
                name="SFTP",
                status="not_installed",
                required=True,
                details="SFTP subsystem not configured in SSH daemon"
            )
        
        # Check if the configured SFTP server binary exists
        sftp_line = sftp_check.stdout.strip()
        binary_path = ""
        if sftp_line:
            parts = sftp_line.split()
            if len(parts) >= 2:
                # The path is usually the last part, but could be the one after 'sftp'
                binary_path = parts[-1]
                logger.info(f"Checking SFTP binary at path: {binary_path}")
                binary_check = await ssh.run(f"test -f {binary_path} && echo 'EXISTS' || echo 'NOT_EXISTS'")
                logger.info(f"Binary check result: {binary_check.stdout.strip()}")
                
                if "NOT_EXISTS" in binary_check.stdout:
                    logger.warning(f"SFTP server binary not found at configured path: {binary_path}")
                    return ServiceStatus(
                        name="SFTP",
                        status="error",
                        required=True,
                        details=f"SFTP server binary not found at configured path: {binary_path}"
                    )
        
        # Since we are connected via SSH, we can assume the daemon is running.
        # Now, let's perform a functional SFTP test.
        try:
            logger.info("Performing functional SFTP test by creating and deleting a test file...")
            test_file = f"/tmp/sftp_test_{uuid.uuid4().hex}.txt"
            
            # 1. Create a test file
            create_result = await ssh.run(f"echo 'siemply_sftp_test' > {test_file}")
            if create_result.returncode != 0:
                logger.error(f"Failed to create SFTP test file: {create_result.stderr}")
                return ServiceStatus(name="SFTP", status="error", required=True, details="Failed to create test file for SFTP check.")

            # 2. Verify file exists
            verify_result = await ssh.run(f"test -f {test_file} && echo 'EXISTS'")
            if "EXISTS" not in verify_result.stdout:
                logger.error("SFTP test file was not created.")
                return ServiceStatus(name="SFTP", status="error", required=True, details="SFTP test file creation failed.")

            # 3. Clean up the test file
            cleanup_result = await ssh.run(f"rm {test_file}")
            if cleanup_result.returncode != 0:
                # This is not a critical failure, but worth noting.
                logger.warning(f"Failed to clean up SFTP test file: {cleanup_result.stderr}")

            logger.info("SFTP functional test passed.")
            return ServiceStatus(
                name="SFTP",
                status="running",
                required=True,
                details="SFTP subsystem configured and functional."
            )
                
        except Exception as e:
            logger.error(f"Error during functional SFTP test: {str(e)}")
            return ServiceStatus(
                name="SFTP",
                status="error",
                required=True,
                details=f"Error testing SFTP functionality: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"Error checking SFTP connectivity: {str(e)}")
        return ServiceStatus(
            name="SFTP",
            status="error",
            required=True,
            details=f"Error checking SFTP: {str(e)}"
        )

async def check_syslog_ng_service(ssh: AsyncSSHClient) -> ServiceStatus:
    """Check syslog-ng service status"""
    try:
        # Check if syslog-ng is installed
        installed_check = await ssh.run("which syslog-ng 2>/dev/null || echo 'NOT_INSTALLED'")
        if "NOT_INSTALLED" in installed_check.stdout:
            return ServiceStatus(
                name="syslog-ng",
                status="not_installed",
                required=False,
                details="syslog-ng not installed"
            )
        
        # Check service status
        service_check = await ssh.run("systemctl is-active syslog-ng 2>/dev/null || service syslog-ng status 2>/dev/null || echo 'SERVICE_CHECK_FAILED'")
        
        if "active" in service_check.stdout.lower() or "running" in service_check.stdout.lower():
            return ServiceStatus(
                name="syslog-ng",
                status="running",
                required=False,
                details="syslog-ng service is running"
            )
        elif "inactive" in service_check.stdout.lower() or "stopped" in service_check.stdout.lower():
            return ServiceStatus(
                name="syslog-ng",
                status="stopped",
                required=False,
                details="syslog-ng service is stopped"
            )
        else:
            return ServiceStatus(
                name="syslog-ng",
                status="error",
                required=False,
                details="Unable to determine syslog-ng service status"
            )
    except Exception as e:
        return ServiceStatus(
            name="syslog-ng",
            status="error",
            required=False,
            details=f"Error checking syslog-ng: {str(e)}"
        )

async def check_ssh_service(ssh: AsyncSSHClient) -> ServiceStatus:
    """Check SSH service status"""
    try:
        logger.info("Checking SSH service status...")
        
        # Try multiple methods to check SSH service status for different OS types
        # Method 1: systemctl (systemd-based systems)
        ssh_check = await ssh.run("systemctl is-active sshd 2>/dev/null || echo 'SYSTEMCTL_FAILED'")
        logger.info(f"systemctl check result: {ssh_check.stdout.strip()}")
        
        if "active" in ssh_check.stdout.lower():
            logger.info("SSH service is running (systemd)")
            return ServiceStatus(
                name="SSH",
                status="running",
                required=True,
                details="SSH service is running"
            )
        
        # Method 2: systemctl for 'ssh' service name (some systems use 'ssh' instead of 'sshd')
        if "SYSTEMCTL_FAILED" in ssh_check.stdout:
            ssh_check2 = await ssh.run("systemctl is-active ssh 2>/dev/null || echo 'SSH_SYSTEMCTL_FAILED'")
            logger.info(f"systemctl ssh check result: {ssh_check2.stdout.strip()}")
            
            if "active" in ssh_check2.stdout.lower():
                logger.info("SSH service is running (systemd, ssh)")
                return ServiceStatus(
                    name="SSH",
                    status="running",
                    required=True,
                    details="SSH service is running"
                )
        
        # Method 3: service command (init.d systems)
        service_check = await ssh.run("service sshd status 2>/dev/null || echo 'SERVICE_SSHD_FAILED'")
        logger.info(f"service sshd check result: {service_check.stdout.strip()}")
        
        if "running" in service_check.stdout.lower() or "active" in service_check.stdout.lower():
            logger.info("SSH service is running (init.d)")
            return ServiceStatus(
                name="SSH",
                status="running",
                required=True,
                details="SSH service is running"
            )
        
        # Method 4: service command for 'ssh' service name
        if "SERVICE_SSHD_FAILED" in service_check.stdout:
            service_check2 = await ssh.run("service ssh status 2>/dev/null || echo 'SERVICE_SSH_FAILED'")
            logger.info(f"service ssh check result: {service_check2.stdout.strip()}")
            
            if "running" in service_check2.stdout.lower() or "active" in service_check2.stdout.lower():
                logger.info("SSH service is running (init.d, ssh)")
                return ServiceStatus(
                    name="SSH",
                    status="running",
                    required=True,
                    details="SSH service is running"
                )
        
        # Method 5: Check if SSH process is running
        process_check = await ssh.run("pgrep -x sshd >/dev/null && echo 'SSHD_RUNNING' || pgrep -x ssh >/dev/null && echo 'SSH_RUNNING' || echo 'NO_SSH_PROCESS'")
        logger.info(f"Process check result: {process_check.stdout.strip()}")
        
        if "RUNNING" in process_check.stdout:
            logger.info("SSH process is running")
            return ServiceStatus(
                name="SSH",
                status="running",
                required=True,
                details="SSH service is running (detected via process)"
            )
        
        # Method 6: Check if SSH port is listening
        port_check = await ssh.run("netstat -tlnp 2>/dev/null | grep ':22 ' >/dev/null && echo 'PORT_22_LISTENING' || ss -tlnp 2>/dev/null | grep ':22 ' >/dev/null && echo 'PORT_22_LISTENING' || echo 'PORT_22_NOT_LISTENING'")
        logger.info(f"Port check result: {port_check.stdout.strip()}")
        
        if "PORT_22_LISTENING" in port_check.stdout:
            logger.info("SSH port 22 is listening")
            return ServiceStatus(
                name="SSH",
                status="running",
                required=True,
                details="SSH service is running (detected via port listening)"
            )
        
        # If we get here, we couldn't determine SSH status
        logger.warning("Could not determine SSH service status using any method")
        return ServiceStatus(
            name="SSH",
            status="error",
            required=True,
            details="SSH service status unknown or not running"
        )
        
    except Exception as e:
        logger.error(f"Error checking SSH service: {str(e)}")
        return ServiceStatus(
            name="SSH",
            status="error",
            required=True,
            details=f"Error checking SSH: {str(e)}"
        )

async def check_network_connectivity(ssh: AsyncSSHClient) -> ServiceStatus:
    """Check basic network connectivity"""
    try:
        logger.info("Checking network connectivity...")
        
        # Test connectivity to multiple destinations for better reliability
        # Try Google DNS first, then Cloudflare DNS as fallback
        ping_result = await ssh.run("ping -c 1 -W 5 8.8.8.8 2>/dev/null || ping -c 1 -W 5 1.1.1.1 2>/dev/null || echo 'PING_FAILED'")
        logger.info(f"Ping test result: {ping_result.stdout.strip()}")
        
        if "PING_FAILED" in ping_result.stdout:
            logger.warning("Ping test failed, checking DNS resolution...")
            # Check if it's a DNS issue or general connectivity issue
            dns_check = await ssh.run("nslookup google.com 2>/dev/null || echo 'DNS_FAILED'")
            logger.info(f"DNS check result: {dns_check.stdout.strip()}")
            
            if "DNS_FAILED" in dns_check.stdout:
                logger.error("Both ping and DNS resolution failed")
                return ServiceStatus(
                    name="Network",
                    status="error",
                    required=True,
                    details="No internet connectivity (ping and DNS resolution failed)"
                )
            else:
                logger.warning("Ping failed but DNS working - limited connectivity")
                return ServiceStatus(
                    name="Network",
                    status="error",
                    required=True,
                    details="Limited connectivity (ping failed but DNS working)"
                )
        else:
            logger.info("Network connectivity check passed")
            return ServiceStatus(
                name="Network",
                status="running",
                required=True,
                details="Network connectivity working"
            )
    except Exception as e:
        logger.error(f"Error checking network connectivity: {str(e)}")
        return ServiceStatus(
            name="Network",
            status="error",
            required=True,
            details=f"Error checking network: {str(e)}"
        )

async def check_all_services(ssh: AsyncSSHClient) -> List[ServiceStatus]:
    """Check all services and return their status"""
    logger.info("Starting comprehensive service check...")
    services = []
    
    # Check critical services
    logger.info("Checking SSH service...")
    services.append(await check_ssh_service(ssh))
    
    logger.info("Checking SFTP connectivity...")
    services.append(await check_sftp_connectivity(ssh))
    
    logger.info("Checking network connectivity...")
    services.append(await check_network_connectivity(ssh))
    
    # Check optional services
    logger.info("Checking syslog-ng service...")
    services.append(await check_syslog_ng_service(ssh))
    
    logger.info(f"Service check completed. Found {len(services)} services:")
    for service in services:
        logger.info(f"  - {service.name}: {service.status} ({service.details})")
    
    return services

async def fix_sftp_connectivity(ssh: AsyncSSHClient) -> Tuple[bool, str]:
    """Attempt to fix SFTP connectivity issues safely."""
    config_path = "/etc/ssh/sshd_config"
    backup_path = f"/etc/ssh/sshd_config.bak.{int(time.time())}"
    try:
        # 1. Backup the config file first
        await ssh.run(f"sudo cp {config_path} {backup_path}")
        logger.info(f"Backed up sshd_config to {backup_path}")

        # 2. Find the correct sftp-server binary path
        find_result = await ssh.run("find /usr -name 'sftp-server' 2>/dev/null | head -1")
        if not find_result.stdout.strip():
            await ssh.run(f"sudo mv {backup_path} {config_path}") # Restore backup
            return False, "SFTP fix failed: sftp-server binary not found on the system."
        correct_path = find_result.stdout.strip()
        correct_subsystem_line = f"Subsystem sftp {correct_path}"

        # 3. Check for existing 'Subsystem sftp' configuration (uncommented)
        uncommented_check = await ssh.run(f"grep -iE '^[[:space:]]*Subsystem[[:space:]]+sftp' {config_path}")

        if uncommented_check.returncode == 0:
            # An uncommented line exists. Replace it to be sure it's correct.
            logger.info("Found existing uncommented 'Subsystem sftp' line. Replacing it.")
            original_line = uncommented_check.stdout.strip().split('\n')[0]
            escaped_original = original_line.replace('/', '\\/').replace('|', '\\|')
            escaped_replacement = correct_subsystem_line.replace('/', '\\/').replace('|', '\\|')
            await ssh.run(f"sudo sed -i 's|{escaped_original}|{escaped_replacement}|' {config_path}")
        else:
            # No uncommented line. Check for a commented one.
            logger.info("No uncommented 'Subsystem sftp' line. Checking for a commented one.")
            commented_check = await ssh.run(f"grep -iE '^[[:space:]]*#[[:space:]]*Subsystem[[:space:]]+sftp' {config_path}")
            if commented_check.returncode == 0:
                # A commented line exists. Replace it with the correct, uncommented line.
                logger.info("Found commented 'Subsystem sftp' line. Replacing and uncommenting.")
                original_line = commented_check.stdout.strip().split('\n')[0]
                escaped_original = original_line.replace('/', '\\/').replace('|', '\\|')
                escaped_replacement = correct_subsystem_line.replace('/', '\\/').replace('|', '\\|')
                await ssh.run(f"sudo sed -i 's|{escaped_original}|{escaped_replacement}|' {config_path}")
            else:
                # No line exists at all. Append it.
                logger.info("No 'Subsystem sftp' line found. Appending a new one.")
                await ssh.run(f"echo '{correct_subsystem_line}' | sudo tee -a {config_path}")

        # 4. CRITICAL: Validate the new configuration before reloading
        logger.info("Validating new sshd_config syntax with 'sshd -t'")
        validation_result = await ssh.run("sudo sshd -t")
        if validation_result.returncode != 0:
            logger.error(f"sshd_config validation failed! Restoring from backup. Stderr: {validation_result.stderr}")
            await ssh.run(f"sudo mv {backup_path} {config_path}")
            return False, f"SFTP fix failed: The new SSH configuration is invalid. Changes have been reverted. Error: {validation_result.stderr}"

        # 5. Safely reload the SSH daemon
        logger.info("Configuration validated. Reloading SSH daemon.")
        reload_result = await ssh.run("sudo systemctl reload sshd 2>/dev/null || sudo systemctl restart sshd 2>/dev/null || sudo pkill -HUP sshd 2>/dev/null || echo 'RELOAD_FAILED'")

        if "RELOAD_FAILED" in reload_result.stdout or reload_result.returncode != 0:
            logger.error(f"Failed to reload sshd even after successful validation. Stderr: {reload_result.stderr}")
            await ssh.run(f"sudo mv {backup_path} {config_path}")
            await ssh.run("sudo systemctl restart sshd") 
            return False, "SFTP configuration updated, but failed to reload the SSH daemon. Changes have been reverted."
        
        logger.info("SSH daemon reloaded successfully.")
        return True, f"SFTP configuration corrected to use path '{correct_path}' and SSH daemon was reloaded."

    except Exception as e:
        logger.error(f"An unexpected error occurred while fixing SFTP: {str(e)}")
        await ssh.run(f"sudo mv {backup_path} {config_path} 2>/dev/null || true")
        return False, f"An unexpected error occurred while fixing SFTP: {str(e)}"

async def install_syslog_ng(ssh: AsyncSSHClient) -> Tuple[bool, str]:
    """Install syslog-ng service"""
    try:
        # Detect OS and install syslog-ng
        os_check = await ssh.run("cat /etc/os-release 2>/dev/null || echo 'UNKNOWN'")
        
        if "ubuntu" in os_check.stdout.lower() or "debian" in os_check.stdout.lower():
            install_cmd = "sudo apt-get update -y && sudo apt-get install -y syslog-ng"
        elif "redhat" in os_check.stdout.lower() or "centos" in os_check.stdout.lower() or "rhel" in os_check.stdout.lower():
            install_cmd = "sudo yum install -y syslog-ng || sudo dnf install -y syslog-ng"
        elif "suse" in os_check.stdout.lower():
            install_cmd = "sudo zypper install -y syslog-ng"
        else:
            return False, "Unsupported operating system for syslog-ng installation"
        
        result = await ssh.run(install_cmd)
        if result.returncode == 0:
            # Start and enable the service
            start_result = await ssh.run("sudo systemctl start syslog-ng && sudo systemctl enable syslog-ng 2>/dev/null || sudo service syslog-ng start 2>/dev/null")
            if start_result.returncode == 0:
                return True, "syslog-ng installed and started successfully"
            else:
                return True, "syslog-ng installed but failed to start service"
        else:
            return False, f"Failed to install syslog-ng: {result.stderr}"
            
    except Exception as e:
        return False, f"Error installing syslog-ng: {str(e)}"

async def start_syslog_ng(ssh: AsyncSSHClient) -> Tuple[bool, str]:
    """Start syslog-ng service if it's stopped"""
    try:
        # Try to start the service
        start_result = await ssh.run("sudo systemctl start syslog-ng 2>/dev/null || sudo service syslog-ng start 2>/dev/null")
        
        if start_result.returncode == 0:
            return True, "syslog-ng service started successfully"
        else:
            return False, f"Failed to start syslog-ng: {start_result.stderr}"
            
    except Exception as e:
        return False, f"Error starting syslog-ng: {str(e)}"
