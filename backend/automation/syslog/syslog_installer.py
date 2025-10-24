"""
SIEMply Syslog-NG Installer
Provides syslog-ng installation and configuration with user management
"""
import logging
import tempfile
import os
from typing import Dict, Any, Optional, List

try:
    from backend.models import Host
    from backend.automation.ssh_client import create_ssh_client_from_host
except ImportError:
    # For testing purposes
    Host = None
    create_ssh_client_from_host = None

logger = logging.getLogger(__name__)

# Default installation parameters
DEFAULT_SYSLOG_USER = "syslog"
DEFAULT_SYSLOG_GROUP = "syslog"
DEFAULT_SYSLOG_PORT = 514
DEFAULT_LOG_DIR = "/var/log/centralized"


async def install_syslog_ng(
    host: Host, 
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Install and configure syslog-ng on a host
    
    Args:
        host: Host model instance
        parameters: Optional parameters dictionary with the following keys:
            - user: User to run syslog-ng as (default: syslog)
            - group: Group to run syslog-ng as (default: syslog)
            - port: Syslog port (default: 514)
            - log_dir: Directory for centralized logs (default: /var/log/centralized)
            - additional_users: List of additional users who can manage syslog-ng (optional)
            - is_dry_run: Do not make changes, just show commands (default: False)
            
    Returns:
        Dict with installation result
    """
    # Merge provided parameters with defaults
    params = {
        "user": DEFAULT_SYSLOG_USER,
        "group": DEFAULT_SYSLOG_GROUP,
        "port": DEFAULT_SYSLOG_PORT,
        "log_dir": DEFAULT_LOG_DIR,
        "additional_users": [],
        "is_dry_run": False,
    }
    
    if parameters:
        params.update(parameters)
    
    is_dry_run = params.get("is_dry_run", False)
    user = params["user"]
    group = params["group"]
    port = params["port"]
    log_dir = params["log_dir"]
    additional_users_raw = params.get("additional_users", "")
    # Convert comma-separated string to list
    additional_users = [user.strip() for user in additional_users_raw.split(",") if user.strip()] if additional_users_raw else []
    
    result = {
        "success": False,
        "message": "",
        "host_id": host.id,
        "hostname": host.hostname,
        "is_dry_run": is_dry_run,
        "commands": [],
        "stdout": "",
        "stderr": ""
    }
    
    try:
        # Create SSH client
        ssh_client = create_ssh_client_from_host(host)
        
        with ssh_client:
            # Step 1: Create syslog user and group if they don't exist
            logger.info(f"Creating syslog user and group on {host.hostname}")
            
            # Check if user exists
            check_user_cmd = f"id {user} 2>/dev/null || echo 'user_not_found'"
            check_result = ssh_client.execute_command(check_user_cmd)
            
            if check_result[0] != 0 or "user_not_found" in check_result[1]:
                # Create user and group
                create_user_cmd = f"groupadd -r {group} 2>/dev/null || true && useradd -r -g {group} -s /bin/false -d /var/lib/{user} {user} 2>/dev/null || true"
                result["commands"].append(create_user_cmd)
                
                if not is_dry_run:
                    user_result = ssh_client.execute_command(create_user_cmd)
                    if user_result[0] != 0:
                        result["message"] = f"Failed to create user {user}"
                        result["stderr"] = user_result[2]
                        return result
                    logger.info(f"Created user {user} and group {group}")
            
            # Step 2: Create the installation script
            install_script = _create_install_script(user, group, port, log_dir, additional_users)
            
            # Step 3: Upload and execute the script
            logger.info(f"Installing syslog-ng on {host.hostname}")
            
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
                temp_file.write(install_script)
                temp_file_path = temp_file.name
            
            try:
                # Upload script using base64 encoding to avoid heredoc issues
                import base64
                script_base64 = base64.b64encode(install_script.encode('utf-8')).decode('utf-8')
                upload_cmd = f'echo "{script_base64}" | base64 -d > /tmp/syslog_install.sh'
                
                result["commands"].append(upload_cmd)
                
                if not is_dry_run:
                    upload_result = ssh_client.execute_command(upload_cmd)
                    if upload_result[0] != 0:
                        result["message"] = "Failed to upload installation script"
                        result["stderr"] = upload_result[2]
                        return result
                
                # Make script executable and run it
                chmod_cmd = "chmod +x /tmp/syslog_install.sh"
                result["commands"].append(chmod_cmd)
                
                if not is_dry_run:
                    chmod_result = ssh_client.execute_command(chmod_cmd)
                    if chmod_result[0] != 0:
                        result["message"] = "Failed to make script executable"
                        result["stderr"] = chmod_result[2]
                        return result
                
                execute_cmd = "/tmp/syslog_install.sh"
                result["commands"].append(execute_cmd)
                
                if not is_dry_run:
                    execute_result = ssh_client.execute_command(execute_cmd)
                    result["stdout"] = execute_result[1]
                    result["stderr"] = execute_result[2]
                    
                    if execute_result[0] != 0:
                        result["message"] = "Syslog-ng installation failed"
                        return result
                    
                    logger.info(f"Syslog-ng installed successfully on {host.hostname}")
                
                # Step 4: Verify installation
                verify_cmd = "systemctl status syslog-ng.service 2>/dev/null || systemctl status syslog-ng 2>/dev/null || pgrep syslog-ng || echo 'Service verification failed'"
                result["commands"].append(verify_cmd)
                
                if not is_dry_run:
                    verify_result = ssh_client.execute_command(verify_cmd)
                    if "Service verification failed" in verify_result[1]:
                        result["message"] = "Installation completed but service verification failed"
                        result["stderr"] += f"\nVerification failed: {verify_result[2]}"
                        # Don't return error, just log warning
                        logger.warning(f"Syslog-ng service verification failed on {host.hostname}")
                    else:
                        logger.info(f"Syslog-ng service verification successful on {host.hostname}")
                
                # Step 5: Clean up
                cleanup_cmd = "rm -f /tmp/syslog_install.sh"
                result["commands"].append(cleanup_cmd)
                
                if not is_dry_run:
                    ssh_client.execute_command(cleanup_cmd)
                
                result["success"] = True
                result["message"] = "Syslog-ng installed and configured successfully"
                
                # Add syslog role to host if not present
                current_roles = host.roles or []
                if "syslog" not in current_roles:
                    current_roles.append("syslog")
                    host.roles = current_roles
                    # Note: We can't commit here as we don't have db session
                    logger.info(f"Added syslog role to host {host.hostname}")
                
            finally:
                # Clean up local temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error installing syslog-ng on {host.hostname}: {str(e)}")
        result["message"] = f"Installation failed: {str(e)}"
        result["stderr"] = str(e)
    
    return result


def _create_install_script(user: str, group: str, port: int, log_dir: str, additional_users: List[str]) -> str:
    """
    Create the syslog-ng installation script
    
    Args:
        user: User to run syslog-ng as
        group: Group to run syslog-ng as
        port: Syslog port
        log_dir: Directory for centralized logs
        additional_users: List of additional users who can manage syslog-ng
        
    Returns:
        The installation script content
    """
    # Prepare additional users string for script
    additional_users_str = " ".join(additional_users) if additional_users else ""
    
    script = f"""#!/bin/bash

set -e

# Detect OS type
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS. Exiting."
    exit 1
fi

echo "Detected OS: $OS"

# Install syslog-ng
case "$OS" in
    ubuntu|debian)
        echo "Installing syslog-ng on Debian/Ubuntu..."
        apt-get update
        # Stop any existing syslog service first
        systemctl stop syslog-ng.service 2>/dev/null || true
        systemctl stop rsyslog.service 2>/dev/null || true
        
        # Install syslog-ng with force-yes to handle configuration issues
        DEBIAN_FRONTEND=noninteractive apt-get install -y --force-yes syslog-ng
        
        # If installation failed due to service issues, try to fix
        if dpkg -l | grep -q syslog-ng; then
            echo "Syslog-ng installed, configuring..."
        else
            echo "Installation failed, trying alternative approach..."
            apt-get install -y --force-yes syslog-ng-core
            apt-get install -y --force-yes syslog-ng
        fi
        ;;
    rhel|centos|fedora)
        echo "Installing syslog-ng on Red Hat/CentOS/Fedora..."
        systemctl stop syslog-ng.service 2>/dev/null || true
        systemctl stop rsyslog.service 2>/dev/null || true
        yum install -y syslog-ng
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 2
        ;;
esac

# Backup configuration
SYSLOG_CONF="/etc/syslog-ng/syslog-ng.conf"
if [ -f "$SYSLOG_CONF" ]; then
    cp "$SYSLOG_CONF" "${{SYSLOG_CONF}}.backup_$(date +%F_%T)"
    echo "Backed up existing syslog-ng.conf"
fi

# Create basic server config
cat > "$SYSLOG_CONF" <<EOF
@version: 3.5
@include "scl.conf"

source s_local {{
    system();
    internal();
}};

source s_network {{
    syslog(ip(0.0.0.0) port({port}) transport("udp"));
    syslog(ip(0.0.0.0) port({port}) transport("tcp"));
}};

destination d_local {{
    file("/var/log/messages");
}};

destination d_centralized {{
    file("{log_dir}/${{HOST}}/${{YEAR}}-${{MONTH}}-${{DAY}}.log" create_dirs(yes));
}};

log {{
    source(s_local);
    destination(d_local);
}};
log {{
    source(s_network);
    destination(d_centralized);
}};
EOF

echo "Wrote new syslog-ng.conf"

# Ensure directory exists and set permissions
mkdir -p {log_dir}
chown {user}:{group} {log_dir}
chmod 755 {log_dir}

# Add syslog-ng commands to existing sudoers for additional users
if [ -n "{additional_users_str}" ]; then
    for user in {additional_users_str}; do
        # Add syslog-ng commands to sudoers for each user
        echo "$user ALL=(root) NOPASSWD: /usr/bin/systemctl start syslog-ng.service" >> /etc/sudoers
        echo "$user ALL=(root) NOPASSWD: /usr/bin/systemctl stop syslog-ng.service" >> /etc/sudoers
        echo "$user ALL=(root) NOPASSWD: /usr/bin/systemctl restart syslog-ng.service" >> /etc/sudoers
        echo "$user ALL=(root) NOPASSWD: /usr/bin/systemctl status syslog-ng.service" >> /etc/sudoers
        echo "$user ALL=(root) NOPASSWD: /usr/bin/systemctl start syslog-ng" >> /etc/sudoers
        echo "$user ALL=(root) NOPASSWD: /usr/bin/systemctl stop syslog-ng" >> /etc/sudoers
        echo "$user ALL=(root) NOPASSWD: /usr/bin/systemctl restart syslog-ng" >> /etc/sudoers
        echo "$user ALL=(root) NOPASSWD: /usr/bin/systemctl status syslog-ng" >> /etc/sudoers
    done
fi

# Also add for the main syslog user
echo "{user} ALL=(root) NOPASSWD: /usr/bin/systemctl start syslog-ng.service" >> /etc/sudoers
echo "{user} ALL=(root) NOPASSWD: /usr/bin/systemctl stop syslog-ng.service" >> /etc/sudoers
echo "{user} ALL=(root) NOPASSWD: /usr/bin/systemctl restart syslog-ng.service" >> /etc/sudoers
echo "{user} ALL=(root) NOPASSWD: /usr/bin/systemctl status syslog-ng.service" >> /etc/sudoers
echo "{user} ALL=(root) NOPASSWD: /usr/bin/systemctl start syslog-ng" >> /etc/sudoers
echo "{user} ALL=(root) NOPASSWD: /usr/bin/systemctl stop syslog-ng" >> /etc/sudoers
echo "{user} ALL=(root) NOPASSWD: /usr/bin/systemctl restart syslog-ng" >> /etc/sudoers
echo "{user} ALL=(root) NOPASSWD: /usr/bin/systemctl status syslog-ng" >> /etc/sudoers

# Open firewall for port {port} (if firewall-cmd exists)
if [ -x "$(command -v firewall-cmd)" ]; then
    firewall-cmd --add-port={port}/udp --permanent || true
    firewall-cmd --add-port={port}/tcp --permanent || true
    firewall-cmd --reload || true
fi

# Restart and enable syslog-ng
if [ -x "$(command -v systemctl)" ]; then
    # Stop any conflicting services first
    systemctl stop rsyslog.service 2>/dev/null || true
    
    # Try different service names
    if systemctl list-unit-files | grep -q syslog-ng.service; then
        echo "Starting syslog-ng.service..."
        systemctl daemon-reload
        systemctl enable syslog-ng.service
        systemctl start syslog-ng.service || {{
            echo "Failed to start syslog-ng.service, checking configuration..."
            syslog-ng -s
            systemctl start syslog-ng.service
        }}
    elif systemctl list-unit-files | grep -q syslog-ng; then
        echo "Starting syslog-ng..."
        systemctl daemon-reload
        systemctl enable syslog-ng
        systemctl start syslog-ng || {{
            echo "Failed to start syslog-ng, checking configuration..."
            syslog-ng -s
            systemctl start syslog-ng
        }}
    else
        echo "Warning: syslog-ng service not found, trying to start manually"
        # Try to start the daemon directly
        if [ -f /usr/sbin/syslog-ng ]; then
            /usr/sbin/syslog-ng -F &
        elif [ -f /usr/local/sbin/syslog-ng ]; then
            /usr/local/sbin/syslog-ng -F &
        fi
    fi
else
    # For older systems without systemctl
    if [ -f /etc/init.d/syslog-ng ]; then
        /etc/init.d/syslog-ng restart
        chkconfig syslog-ng on
    elif [ -f /etc/init.d/syslog ]; then
        /etc/init.d/syslog restart
        chkconfig syslog on
    else
        echo "Warning: syslog-ng init script not found"
    fi
fi

echo "syslog-ng installation and basic configuration complete!"
if [ -n "{additional_users_str}" ]; then
    echo "Users who can manage syslog-ng: {user} {additional_users_str}"
else
    echo "Users who can manage syslog-ng: {user}"
fi

# Debug: Check what services are available
echo "Available syslog services:"
systemctl list-unit-files | grep -i syslog || echo "No syslog services found in systemctl"
echo "Checking if syslog-ng process is running:"
pgrep syslog-ng || echo "syslog-ng process not found"
"""
    
    return script


async def configure_syslog_users(
    host: Host,
    users: List[str],
    action: str = "add"  # "add" or "remove"
) -> Dict[str, Any]:
    """
    Configure additional users who can manage syslog-ng
    
    Args:
        host: Host model instance
        users: List of users to add/remove
        action: "add" or "remove"
        
    Returns:
        Dict with configuration result
    """
    result = {
        "success": False,
        "message": "",
        "host_id": host.id,
        "hostname": host.hostname,
        "commands": []
    }
    
    try:
        ssh_client = create_ssh_client_from_host(host)
        
        with ssh_client:
            sudoers_file = "/etc/sudoers.d/syslog-ng"
            
            if action == "add":
                # Add users to sudoers file
                for user in users:
                    add_cmd = f"echo '{user} ALL=(ALL) NOPASSWD: /bin/systemctl start syslog-ng, /bin/systemctl stop syslog-ng, /bin/systemctl restart syslog-ng, /bin/systemctl status syslog-ng' >> {sudoers_file}"
                    result["commands"].append(add_cmd)
                    
                    add_result = ssh_client.execute_command(add_cmd)
                    if add_result[0] != 0:
                        result["message"] = f"Failed to add user {user} to sudoers"
                        result["stderr"] = add_result[2]
                        return result
                
                result["success"] = True
                result["message"] = f"Added users {', '.join(users)} to syslog-ng management"
                
            elif action == "remove":
                # Remove users from sudoers file
                for user in users:
                    remove_cmd = f"sed -i '/^{user} ALL=(ALL) NOPASSWD: \\/bin\\/systemctl/d' {sudoers_file}"
                    result["commands"].append(remove_cmd)
                    
                    remove_result = ssh_client.execute_command(remove_cmd)
                    if remove_result[0] != 0:
                        result["message"] = f"Failed to remove user {user} from sudoers"
                        result["stderr"] = remove_result[2]
                        return result
                
                result["success"] = True
                result["message"] = f"Removed users {', '.join(users)} from syslog-ng management"
    
    except Exception as e:
        logger.error(f"Error configuring syslog users on {host.hostname}: {str(e)}")
        result["message"] = f"Configuration failed: {str(e)}"
        result["stderr"] = str(e)
    
    return result 