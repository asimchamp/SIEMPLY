"""
System Metrics Collection Module
Collects system metrics from hosts via SSH
"""
import asyncio
import re
from typing import Dict, Any

from backend.automation.ssh_client import get_ssh_client
from backend.models import Host


async def get_system_metrics(host: Host) -> Dict[str, Any]:
    """
    Get system metrics from a host via SSH
    Returns CPU, RAM, disk usage, and other system information
    """
    # Connect to the host via SSH
    async with get_ssh_client(host) as ssh:
        # Check if host is online
        if not ssh:
            return {
                "status": "offline",
                "error": "Could not establish SSH connection"
            }
        
        # Prepare result dictionary
        metrics = {
            "status": "online",
            "hostname": host.hostname,
            "os": {},
            "cpu": {},
            "memory": {},
            "disk": {},
            "network": {},
            "uptime": {}
        }
        
        # Get OS information
        try:
            os_info = await ssh.run("cat /etc/os-release")
            if os_info.returncode == 0:
                # Parse OS info
                os_name = re.search(r'PRETTY_NAME="(.*)"', os_info.stdout)
                if os_name:
                    metrics["os"]["name"] = os_name.group(1)
                
                os_version = re.search(r'VERSION="(.*)"', os_info.stdout)
                if os_version:
                    metrics["os"]["version"] = os_version.group(1)
                
                os_id = re.search(r'ID=(.*)', os_info.stdout)
                if os_id:
                    metrics["os"]["id"] = os_id.group(1).strip('"')
        except Exception as e:
            metrics["os"]["error"] = str(e)
        
        # Get kernel version
        try:
            kernel = await ssh.run("uname -r")
            if kernel.returncode == 0:
                metrics["os"]["kernel"] = kernel.stdout.strip()
        except Exception as e:
            metrics["os"]["kernel_error"] = str(e)
        
        # Get CPU information
        try:
            # Get CPU model
            cpu_info = await ssh.run("cat /proc/cpuinfo | grep 'model name' | head -1")
            if cpu_info.returncode == 0:
                model = re.search(r'model name\s+:\s+(.*)', cpu_info.stdout)
                if model:
                    metrics["cpu"]["model"] = model.group(1)
            
            # Get CPU cores
            cpu_cores = await ssh.run("nproc --all")
            if cpu_cores.returncode == 0:
                metrics["cpu"]["cores"] = int(cpu_cores.stdout.strip())
            
            # Get CPU usage
            cpu_usage = await ssh.run("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'")
            if cpu_usage.returncode == 0:
                try:
                    metrics["cpu"]["usage_percent"] = float(cpu_usage.stdout.strip())
                except ValueError:
                    metrics["cpu"]["usage_percent"] = None
        except Exception as e:
            metrics["cpu"]["error"] = str(e)
        
        # Get memory information
        try:
            mem_info = await ssh.run("free -m")
            if mem_info.returncode == 0:
                # Parse memory info
                mem_lines = mem_info.stdout.strip().split('\n')
                if len(mem_lines) > 1:
                    mem_values = mem_lines[1].split()
                    if len(mem_values) >= 7:
                        metrics["memory"]["total_mb"] = int(mem_values[1])
                        metrics["memory"]["used_mb"] = int(mem_values[2])
                        metrics["memory"]["free_mb"] = int(mem_values[3])
                        metrics["memory"]["usage_percent"] = round((int(mem_values[2]) / int(mem_values[1])) * 100, 2)
        except Exception as e:
            metrics["memory"]["error"] = str(e)
        
        # Get disk information
        try:
            disk_info = await ssh.run("df -h /")
            if disk_info.returncode == 0:
                # Parse disk info
                disk_lines = disk_info.stdout.strip().split('\n')
                if len(disk_lines) > 1:
                    disk_values = disk_lines[1].split()
                    if len(disk_values) >= 6:
                        metrics["disk"]["filesystem"] = disk_values[0]
                        metrics["disk"]["total"] = disk_values[1]
                        metrics["disk"]["used"] = disk_values[2]
                        metrics["disk"]["available"] = disk_values[3]
                        metrics["disk"]["usage_percent"] = disk_values[4]
                        metrics["disk"]["mount_point"] = disk_values[5]
        except Exception as e:
            metrics["disk"]["error"] = str(e)
        
        # Get uptime information
        try:
            uptime_info = await ssh.run("uptime -p")
            if uptime_info.returncode == 0:
                metrics["uptime"]["pretty"] = uptime_info.stdout.strip()
                
            uptime_seconds = await ssh.run("cat /proc/uptime | awk '{print $1}'")
            if uptime_seconds.returncode == 0:
                try:
                    metrics["uptime"]["seconds"] = float(uptime_seconds.stdout.strip())
                except ValueError:
                    metrics["uptime"]["seconds"] = None
        except Exception as e:
            metrics["uptime"]["error"] = str(e)
        
        # Get load average
        try:
            load_avg = await ssh.run("cat /proc/loadavg")
            if load_avg.returncode == 0:
                load_values = load_avg.stdout.strip().split()
                if len(load_values) >= 3:
                    metrics["cpu"]["load_1min"] = float(load_values[0])
                    metrics["cpu"]["load_5min"] = float(load_values[1])
                    metrics["cpu"]["load_15min"] = float(load_values[2])
        except Exception as e:
            metrics["cpu"]["load_error"] = str(e)
        
        return metrics 