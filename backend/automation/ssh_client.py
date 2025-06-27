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
    return SIEMplySSHClient(
        host=host_model.ip_address,
        port=host_model.port,
        username=host_model.username,
        password=host_model.password,
        key_path=host_model.ssh_key_path
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