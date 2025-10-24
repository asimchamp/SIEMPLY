"""
Package Checker Module
Checks and installs required packages on remote hosts via SSH
"""
import asyncio
import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from backend.automation.ssh_client import get_ssh_client
from backend.models import Host

logger = logging.getLogger(__name__)

@dataclass
class PackageInfo:
    name: str
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None

class PackageChecker:
    """Package checker for remote hosts"""
    
    def __init__(self, host: Host):
        self.host = host
        
    async def check_packages(self) -> List[PackageInfo]:
        """Check the status of required packages on the host"""
        packages = []
        
        try:
            async with get_ssh_client(self.host) as ssh:
                if not ssh:
                    logger.error(f"Could not establish SSH connection to {self.host.hostname}")
                    return self._create_failed_packages("SSH connection failed")
                
                # Get OS information to determine package manager
                os_info = await self._get_os_info(ssh)
                package_manager = self._determine_package_manager(os_info)
                
                # Define required packages based on OS
                required_packages = self._get_required_packages(os_info)
                
                # Check each package
                for package_name in required_packages:
                    package_info = await self._check_single_package(ssh, package_name, package_manager)
                    packages.append(package_info)
                    
        except Exception as e:
            logger.error(f"Error checking packages on {self.host.hostname}: {str(e)}")
            return self._create_failed_packages(f"Error: {str(e)}")
            
        return packages
    
    async def install_packages(self, package_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Install missing packages on the host"""
        try:
            async with get_ssh_client(self.host) as ssh:
                if not ssh:
                    return {"success": False, "message": "SSH connection failed"}
                
                # Get OS information
                os_info = await self._get_os_info(ssh)
                package_manager = self._determine_package_manager(os_info)
                
                # If no specific packages specified, install all missing
                if package_names is None:
                    required_packages = self._get_required_packages(os_info)
                    current_packages = await self.check_packages()
                    missing_packages = [pkg.name for pkg in current_packages if not pkg.installed]
                    package_names = missing_packages
                
                if not package_names:
                    return {"success": True, "message": "No packages to install"}
                
                # Install packages
                results = []
                for package_name in package_names:
                    result = await self._install_single_package(ssh, package_name, package_manager)
                    results.append(result)
                
                success_count = sum(1 for r in results if r["success"])
                total_count = len(results)
                
                return {
                    "success": success_count == total_count,
                    "message": f"Installed {success_count}/{total_count} packages",
                    "results": results
                }
                
        except Exception as e:
            logger.error(f"Error installing packages on {self.host.hostname}: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def _get_os_info(self, ssh) -> Dict[str, str]:
        """Get OS information from the host"""
        os_info = {}
        
        try:
            # Try to get OS release info
            result = await ssh.run("cat /etc/os-release")
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os_info[key] = value.strip('"')
            
            # Get kernel info
            kernel_result = await ssh.run("uname -r")
            if kernel_result.returncode == 0:
                os_info['kernel'] = kernel_result.stdout.strip()
                
        except Exception as e:
            logger.warning(f"Could not get OS info: {str(e)}")
            
        return os_info
    
    def _determine_package_manager(self, os_info: Dict[str, str]) -> str:
        """Determine the package manager to use based on OS"""
        os_id = os_info.get('ID', '').lower()
        
        if os_id in ['ubuntu', 'debian']:
            return 'apt'
        elif os_id in ['rhel', 'centos', 'fedora', 'rocky', 'alma']:
            return 'yum'
        elif os_id in ['suse', 'opensuse']:
            return 'zypper'
        else:
            # Default to apt for unknown distributions
            return 'apt'
    
    def _get_required_packages(self, os_info: Dict[str, str]) -> List[str]:
        """Get list of required packages based on OS"""
        os_id = os_info.get('ID', '').lower()
        
        base_packages = ['curl', 'wget', 'tmux', 'git', 'unzip', 'tar', 'gzip']
        
        if os_id in ['ubuntu', 'debian']:
            return base_packages + [
                'python3',
                'python3-pip',
                'build-essential',
                'libssl-dev',
                'libffi-dev',
                'python3-dev',
                'ca-certificates',
                'apt-transport-https',
                'software-properties-common'
            ]
        elif os_id in ['rhel', 'centos', 'fedora', 'rocky', 'alma']:
            return base_packages + [
                'python3',
                'python3-pip',
                'gcc',
                'make',
                'openssl-devel',
                'libffi-devel',
                'python3-devel',
                'ca-certificates',
                'yum-utils'
            ]
        elif os_id in ['suse', 'opensuse']:
            return base_packages + [
                'python3',
                'python3-pip',
                'gcc',
                'make',
                'libopenssl-devel',
                'libffi-devel',
                'python3-devel',
                'ca-certificates'
            ]
        else:
            return base_packages
    
    async def _check_single_package(self, ssh, package_name: str, package_manager: str) -> PackageInfo:
        """Check if a single package is installed"""
        try:
            # Try to find the package
            if package_manager == 'apt':
                # Check if package is installed
                result = await ssh.run(f"dpkg -l | grep -E '^ii\\s+{package_name}\\b'")
                if result.returncode == 0:
                    # Extract version
                    version_match = re.search(rf'^ii\s+{package_name}\s+(\S+)', result.stdout)
                    version = version_match.group(1) if version_match else None
                    
                    # Get path
                    path_result = await ssh.run(f"which {package_name}")
                    path = path_result.stdout.strip() if path_result.returncode == 0 else None
                    
                    return PackageInfo(
                        name=package_name,
                        installed=True,
                        version=version,
                        path=path
                    )
            elif package_manager == 'yum':
                # Check if package is installed
                result = await ssh.run(f"rpm -q {package_name}")
                if result.returncode == 0:
                    # Extract version
                    version_match = re.search(rf'{package_name}-(\S+)', result.stdout)
                    version = version_match.group(1) if version_match else None
                    
                    # Get path
                    path_result = await ssh.run(f"which {package_name}")
                    path = path_result.stdout.strip() if path_result.returncode == 0 else None
                    
                    return PackageInfo(
                        name=package_name,
                        installed=True,
                        version=version,
                        path=path
                    )
            
            # Package not found
            return PackageInfo(
                name=package_name,
                installed=False
            )
            
        except Exception as e:
            logger.warning(f"Error checking package {package_name}: {str(e)}")
            return PackageInfo(
                name=package_name,
                installed=False,
                error=str(e)
            )
    
    async def _install_single_package(self, ssh, package_name: str, package_manager: str) -> Dict[str, Any]:
        """Install a single package"""
        try:
            if package_manager == 'apt':
                # Update package list first
                await ssh.run("sudo apt update")
                
                # Install package
                result = await ssh.run(f"sudo apt install -y {package_name}")
                if result.returncode == 0:
                    return {"success": True, "package": package_name, "message": "Installed successfully"}
                else:
                    return {"success": False, "package": package_name, "message": result.stderr}
                    
            elif package_manager == 'yum':
                # Install package
                result = await ssh.run(f"sudo yum install -y {package_name}")
                if result.returncode == 0:
                    return {"success": True, "package": package_name, "message": "Installed successfully"}
                else:
                    return {"success": False, "package": package_name, "message": result.stderr}
                    
            else:
                return {"success": False, "package": package_name, "message": f"Unsupported package manager: {package_manager}"}
                
        except Exception as e:
            logger.error(f"Error installing package {package_name}: {str(e)}")
            return {"success": False, "package": package_name, "message": f"Error: {str(e)}"}
    
    def _create_failed_packages(self, error_message: str) -> List[PackageInfo]:
        """Create package info for failed checks"""
        base_packages = ['curl', 'wget', 'tmux', 'git', 'unzip', 'tar', 'gzip']
        return [
            PackageInfo(
                name=package_name,
                installed=False,
                error=error_message
            )
            for package_name in base_packages
        ]

async def check_host_packages(host: Host) -> List[PackageInfo]:
    """Convenience function to check packages on a host"""
    checker = PackageChecker(host)
    return await checker.check_packages()

async def install_host_packages(host: Host, package_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convenience function to install packages on a host"""
    checker = PackageChecker(host)
    return await checker.install_packages(package_names)
