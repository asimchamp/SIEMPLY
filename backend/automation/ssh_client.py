"""
SIEMply SSH Client Module
Provides secure SSH connectivity with retry logic and timeout handling
"""
import os
import time
import logging
from typing import Optional, Tuple, Dict, Any, List, AsyncIterator
import paramiko
from contextlib import asynccontextmanager
from paramiko.client import SSHClient

from backend.config.settings import settings
from backend.models import Host

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSHClientError(Exception):
    """Base SSH client error"""
    pass

class SSHConnectionError(SSHClientError):
    """SSH connection error"""
    pass

class SSHCommandError(SSHClientError):
    """SSH command execution error"""
    pass

class SSHTimeoutError(SSHClientError):
    """SSH timeout error"""
    pass

class SIEMplySSHClient:
    """
    SSH client for SIEMply with retry logic and timeout handling
    """
    
    def __init__(
        self, 
        host: str, 
        port: int = 22, 
        username: str = None, 
        password: str = None, 
        key_path: str = None, 
        timeout: int = None,
        retries: int = None
    ):
        """Initialize SSH client for a host
        
        Args:
            host: Hostname or IP address
            port: SSH port, defaults to 22
            username: SSH username
            password: SSH password, optional
            key_path: Path to SSH key, optional (preferred over password)
            timeout: Connection timeout in seconds
            retries: Number of connection retry attempts
        """
        self.host = host
        self.port = port
        self.username = username or settings.SSH_DEFAULT_USER
        self.password = password
        self.key_path = key_path or settings.SSH_KEY_PATH
        self.timeout = timeout or settings.SSH_TIMEOUT
        self.retries = retries or settings.SSH_RETRIES
        self.client = None
    
    def _expand_path(self, path: str) -> str:
        """Expand ~ in path to user's home directory"""
        return os.path.expanduser(path)
    
    def connect(self) -> SSHClient:
        """Connect to the host with retry logic
        
        Returns:
            SSHClient: Connected SSH client
            
        Raises:
            SSHConnectionError: If connection fails after retries
        """
        start_time = time.time()
        logger.info(f"Connecting to {self.username}@{self.host}:{self.port}")
        
        retries_left = self.retries
        last_exception = None
        
        while retries_left > 0:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                connect_kwargs = {
                    "hostname": self.host,
                    "port": self.port,
                    "username": self.username,
                    "timeout": self.timeout
                }
                
                # Use key-based authentication if key path is provided
                if self.key_path:
                    key_path = self._expand_path(self.key_path)
                    if os.path.exists(key_path):
                        connect_kwargs["key_filename"] = key_path
                    else:
                        logger.warning(f"SSH key not found at {key_path}, falling back to password")
                        if self.password:
                            connect_kwargs["password"] = self.password
                # Fall back to password authentication
                elif self.password:
                    connect_kwargs["password"] = self.password
                    
                client.connect(**connect_kwargs)
                self.client = client
                logger.info(f"Connected to {self.host} successfully")
                return client
                
            except Exception as e:
                last_exception = e
                retries_left -= 1
                logger.warning(f"Connection attempt failed: {str(e)}. Retries left: {retries_left}")
                if retries_left > 0:
                    # Exponential backoff: 1s, 2s, 4s, ...
                    backoff = 2 ** (self.retries - retries_left - 1)
                    logger.info(f"Retrying in {backoff} seconds...")
                    time.sleep(backoff)
        
        # All retries failed
        elapsed_time = time.time() - start_time
        error_msg = f"Failed to connect to {self.host} after {self.retries} attempts ({elapsed_time:.2f}s)"
        logger.error(error_msg)
        raise SSHConnectionError(f"{error_msg}: {str(last_exception)}")
    
    def disconnect(self):
        """Safely disconnect SSH client"""
        if self.client:
            logger.info(f"Disconnecting from {self.host}")
            self.client.close()
            self.client = None
    
    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """Execute command on the remote host
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (return_code, stdout, stderr)
            
        Raises:
            SSHConnectionError: If not connected
            SSHCommandError: If command execution fails
            SSHTimeoutError: If command execution times out
        """
        if not self.client:
            self.connect()
            
        logger.info(f"Executing command on {self.host}: {command}")
        start_time = time.time()
        
        try:
            # Execute command
            stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout)
            
            # Get command output
            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')
            return_code = stdout.channel.recv_exit_status()
            
            elapsed_time = time.time() - start_time
            logger.info(f"Command completed in {elapsed_time:.2f}s with return code {return_code}")
            
            if return_code != 0:
                logger.warning(f"Command returned non-zero exit code: {return_code}")
                logger.debug(f"Command stderr: {stderr_str}")
            
            return return_code, stdout_str, stderr_str
            
        except paramiko.SSHException as e:
            raise SSHCommandError(f"SSH error while executing command: {str(e)}")
        except TimeoutError:
            raise SSHTimeoutError(f"Command timed out after {self.timeout} seconds")

    def upload_bytes(self, remote_path: str, data: bytes, mode: int = 0o644) -> None:
        """Upload bytes to remote path using SFTP.
        Raises SSHClientError on failure.
        """
        if not self.client:
            self.connect()
        try:
            sftp = self.client.open_sftp()
            # Ensure remote directory exists (best-effort)
            remote_dir = os.path.dirname(remote_path)
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                # Try to create single-level directory
                try:
                    sftp.mkdir(remote_dir)
                except Exception:
                    pass
            with sftp.file(remote_path, 'wb') as f:
                f.write(data)
                f.flush()
            sftp.chmod(remote_path, mode)
            sftp.close()
        except Exception as e:
            raise SSHClientError(f"SFTP upload_bytes failed: {str(e)}")

    def upload_file(self, local_path: str, remote_path: str, mode: int = 0o644) -> None:
        """Upload a local file to remote path using SFTP."""
        if not self.client:
            self.connect()
        try:
            sftp = self.client.open_sftp()
            remote_dir = os.path.dirname(remote_path)
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                try:
                    sftp.mkdir(remote_dir)
                except Exception:
                    pass
            sftp.put(local_path, remote_path)
            sftp.chmod(remote_path, mode)
            sftp.close()
        except Exception as e:
            raise SSHClientError(f"SFTP upload_file failed: {str(e)}")

    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download a remote file to a local path using SFTP.
        Raises SSHClientError on failure.
        """
        if not self.client:
            self.connect()
        try:
            sftp = self.client.open_sftp()
            # Ensure local directory exists
            local_dir = os.path.dirname(local_path)
            if not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
            
            sftp.get(remote_path, local_path)
            sftp.close()
            logger.info(f"Downloaded {remote_path} to {local_path}")
        except FileNotFoundError:
            raise SSHClientError(f"SFTP download failed: remote file not found at {remote_path}")
        except Exception as e:
            raise SSHClientError(f"SFTP download_file failed: {str(e)}")
            
    def __enter__(self):
        """Context manager enter"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


def create_ssh_client_from_host(host_model: Host) -> SIEMplySSHClient:
    """Factory function to create SSH client from Host model
    
    Args:
        host_model: Host database model
        
    Returns:
        SIEMplySSHClient instance
    """
    # Use the local SSH key path from settings, not the host's ssh_key_path
    # The host's ssh_key_path field is for future use (e.g., different keys per host)
    # For now, we use the default local key path
    return SIEMplySSHClient(
        host=host_model.ip_address,
        port=host_model.port,
        username=host_model.username,
        password=host_model.password,
        key_path=settings.SSH_KEY_PATH  # Use local key path, not host's
    ) 

class CommandResult:
    """Result of a command execution"""
    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class AsyncSSHClient:
    """Async wrapper for SIEMplySSHClient"""
    def __init__(self, client: SIEMplySSHClient):
        self.client = client
        
    async def run(self, command: str) -> CommandResult:
        """Run a command asynchronously"""
        try:
            returncode, stdout, stderr = self.client.execute_command(command)
            return CommandResult(returncode, stdout, stderr)
        except Exception as e:
            logger.error(f"Error running command: {str(e)}")
            return CommandResult(1, "", str(e))

    async def upload_bytes(self, remote_path: str, data: bytes, mode: int = 0o644) -> bool:
        """Upload bytes with retry logic and better error handling"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.client.upload_bytes(remote_path, data, mode)
                logger.info(f"Successfully uploaded bytes to {remote_path}")
                return True
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Upload bytes attempt {attempt + 1}/{max_retries} failed: {error_msg}")
                
                if attempt < max_retries - 1:
                    # Wait before retry
                    import asyncio
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    
                    # Try to reconnect if it's a connection issue
                    if "EOF during negotiation" in error_msg or "Connection lost" in error_msg:
                        try:
                            logger.info("Attempting to reconnect SSH client")
                            self.client.disconnect()
                            self.client.connect()
                        except Exception as reconnect_e:
                            logger.warning(f"Reconnection attempt failed: {str(reconnect_e)}")
                else:
                    logger.error(f"All upload bytes attempts failed for {remote_path}: {error_msg}")
                    return False
        
        return False

    async def upload_file(self, local_path: str, remote_path: str, mode: int = 0o644) -> bool:
        """Upload a file with retry logic and better error handling"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.client.upload_file(local_path, remote_path, mode)
                logger.info(f"Successfully uploaded {local_path} to {remote_path}")
                return True
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Upload attempt {attempt + 1}/{max_retries} failed: {error_msg}")
                
                if attempt < max_retries - 1:
                    # Wait before retry
                    import asyncio
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    
                    # Try to reconnect if it's a connection issue
                    if "EOF during negotiation" in error_msg or "Connection lost" in error_msg:
                        try:
                            logger.info("Attempting to reconnect SSH client")
                            self.client.disconnect()
                            self.client.connect()
                        except Exception as reconnect_e:
                            logger.warning(f"Reconnection attempt failed: {str(reconnect_e)}")
                else:
                    logger.error(f"All upload attempts failed for {local_path} to {remote_path}: {error_msg}")
                    return False
        
        return False

    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Asynchronously download a remote file to a local path."""
        try:
            self.client.download_file(remote_path, local_path)
            return True
        except Exception as e:
            logger.error(f"Error downloading file from {remote_path}: {str(e)}")
            return False


async def copy_job_logs_to_local(host: Host, job_id: str, log_file_paths: List[str]) -> bool:
    """
    Copy job log files from remote host to local backend/logs directory
    
    Args:
        host: Host model instance
        job_id: Unique job identifier
        log_file_paths: List of remote log file paths to copy
        
    Returns:
        bool: True if all logs copied successfully, False otherwise
    """
    import json
    from datetime import datetime
    from pathlib import Path
    
    try:
        # Determine local log directory (backend/logs/YYYY-MM/)
        current_date = datetime.now()
        local_log_dir = Path(__file__).parent.parent / "logs" / current_date.strftime("%Y-%m")
        local_log_dir.mkdir(parents=True, exist_ok=True)
        local_log_file = local_log_dir / f"{job_id}.json"
        
        # Create SSH client
        ssh_client = create_ssh_client_from_host(host)
        
        # Collect all log contents
        collected_logs = {
            "job_id": job_id,
            "timestamp": current_date.isoformat(),
            "host": host.hostname,
            "logs": {}
        }
        
        async with get_ssh_client(host) as ssh:
            if not ssh:
                logger.error(f"Failed to connect to {host.hostname} for log collection")
                return False
                
            for remote_log_path in log_file_paths:
                try:
                    # Check if remote log file exists
                    check_result = await ssh.run(f"test -f {remote_log_path} && echo 'exists' || echo 'missing'")
                    
                    if "exists" in check_result.stdout:
                        # Read the log file content
                        cat_result = await ssh.run(f"cat {remote_log_path}")
                        if cat_result.returncode == 0:
                            log_name = Path(remote_log_path).name
                            collected_logs["logs"][log_name] = cat_result.stdout
                            logger.info(f"Collected log content from {remote_log_path}")
                        else:
                            logger.warning(f"Failed to read log file {remote_log_path}: {cat_result.stderr}")
                    else:
                        logger.warning(f"Log file not found: {remote_log_path}")
                        
                except Exception as e:
                    logger.error(f"Error collecting log from {remote_log_path}: {str(e)}")
                    continue
        
        # Save collected logs to local JSON file
        with open(local_log_file, 'w') as f:
            json.dump(collected_logs, f, indent=2)
            
        logger.info(f"Successfully saved job logs to {local_log_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to copy job logs for job {job_id}: {str(e)}")
        return False


async def copy_splunk_job_logs(host: Host, job_id: str, job_type: str) -> bool:
    """
    Copy Splunk job logs based on job type
    
    Args:
        host: Host model instance
        job_id: Unique job identifier
        job_type: Type of job (install/upgrade, enterprise/uf)
        
    Returns:
        bool: True if logs copied successfully, False otherwise
    """
    log_paths = []
    
    # Determine paths based on job type
    if "uf" in job_type.lower():
        # Universal Forwarder jobs
        if "upgrade" in job_type.lower():
            log_paths = [
                "/tmp/siemply_splunk_uf_upgrade/upgrade_runner.log",
                "/tmp/siemply_splunk_uf_upgrade/env.json"
            ]
        else:
            log_paths = [
                "/tmp/siemply_splunk_uf/runner.log",
                "/tmp/siemply_splunk_uf/env.json"
            ]
    else:
        # Enterprise jobs
        if "upgrade" in job_type.lower():
            log_paths = [
                "/tmp/siemply_splunk_upgrade/upgrade_runner.log",
                "/tmp/siemply_splunk_upgrade/env.json"
            ]
        else:
            log_paths = [
                "/tmp/siemply_splunk/runner.log",
                "/tmp/siemply_splunk/env.json"
            ]
    
    return await copy_job_logs_to_local(host, job_id, log_paths)


async def cleanup_remote_temp_directories(host: Host) -> bool:
    """
    Clean up all SIEMPLY temporary directories on remote host
    
    Args:
        host: Host model instance
        
    Returns:
        bool: True if cleanup successful, False otherwise
    """
    try:
        async with get_ssh_client(host) as ssh:
            if not ssh:
                logger.error(f"Failed to connect to {host.hostname} for cleanup")
                return False
            
            # Remove all temporary directories
            cleanup_commands = [
                "sudo rm -rf /tmp/siemply_splunk",
                "sudo rm -rf /tmp/siemply_splunk_upgrade",
                "sudo rm -rf /tmp/siemply_splunk_uf",
                "sudo rm -rf /tmp/siemply_splunk_uf_upgrade",
                "sudo rm -rf /tmp/siemply_sessions"
            ]
            
            for cmd in cleanup_commands:
                try:
                    result = await ssh.run(cmd)
                    if result.returncode != 0:
                        logger.warning(f"Cleanup command failed: {cmd} - {result.stderr}")
                except Exception as e:
                    logger.warning(f"Error running cleanup command {cmd}: {str(e)}")
            
            logger.info(f"Successfully cleaned up remote temp directories on {host.hostname}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to cleanup remote temp directories on {host.hostname}: {str(e)}")
        return False


@asynccontextmanager
async def get_ssh_client(host: Host) -> AsyncIterator[Optional[AsyncSSHClient]]:
    """Get an SSH client for a host as an async context manager
    
    Args:
        host: Host model instance
        
    Yields:
        AsyncSSHClient instance or None if connection fails
    """
    ssh_client = create_ssh_client_from_host(host)
    async_client = None
    
    try:
        # Try to connect
        ssh_client.connect()
        async_client = AsyncSSHClient(ssh_client)
        yield async_client
    except Exception as e:
        logger.error(f"Failed to connect to {host.hostname}: {str(e)}")
        yield None
    finally:
        # Always disconnect
        if ssh_client:
            ssh_client.disconnect() 