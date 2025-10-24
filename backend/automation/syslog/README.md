# SIEMply Syslog-NG Module

This module provides syslog-ng installation and configuration functionality for the SIEMply platform.

## Features

- **Cross-platform installation**: Supports Ubuntu/Debian and Red Hat/CentOS/Fedora systems
- **User management**: Allows additional users to manage syslog-ng service (start/stop/restart/status)
- **Centralized logging**: Configures syslog-ng to collect logs from network sources
- **Firewall configuration**: Automatically opens required ports (UDP/TCP 514)
- **Service management**: Enables and starts syslog-ng service

## Installation Parameters

The syslog installer accepts the following parameters:

- `user`: User to run syslog-ng as (default: "syslog")
- `group`: Group to run syslog-ng as (default: "syslog")
- `port`: Syslog port (default: 514)
- `log_dir`: Directory for centralized logs (default: "/var/log/centralized")
- `additional_users`: Comma-separated list of additional users who can manage syslog-ng
- `is_dry_run`: Do not make changes, just show commands (default: False)

## User Management

The installer creates a sudoers file (`/etc/sudoers.d/syslog-ng`) that allows:
- The syslog user to manage the service
- Additional users (specified in `additional_users`) to manage the service

Users can run:
- `sudo systemctl start syslog-ng`
- `sudo systemctl stop syslog-ng`
- `sudo systemctl restart syslog-ng`
- `sudo systemctl status syslog-ng`

## Configuration

The installer creates a basic syslog-ng configuration that:
- Listens on UDP and TCP port 514
- Collects local system logs
- Collects network syslog messages
- Stores centralized logs in `/var/log/centralized/{HOST}/{YEAR}-{MONTH}-{DAY}.log`

## Usage

### Frontend Integration

The syslog installation is available in the Root card of the "/jobs/new" page as "Enable Syslog-NG".

### Backend API

```python
from backend.automation.syslog.syslog_installer import install_syslog_ng

# Install syslog-ng with default settings
result = await install_syslog_ng(host, {})

# Install with custom settings
result = await install_syslog_ng(host, {
    "user": "syslog",
    "port": 514,
    "log_dir": "/var/log/centralized",
    "additional_users": "splunk,admin,user1"
})
```

### Job API Endpoint

```
POST /jobs/install/syslog
```

Parameters:
- `host_id`: Target host ID
- `parameters`: Installation parameters
- `is_dry_run`: Optional dry run flag

## Files

- `syslog_installer.py`: Main installation logic
- `__init__.py`: Module initialization
- `README.md`: This documentation

## Dependencies

- `paramiko`: SSH connectivity
- `tempfile`: Temporary file handling
- `os`: Operating system operations 