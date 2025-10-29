# SIEMply Systemctl Services Guide

This document describes how to manage SIEMply as systemd services on Linux systems.

## Supported Operating Systems

- **Debian/Ubuntu** (all versions)
- **RHEL/CentOS** (7, 8, 9)
- **Fedora** (all recent versions)
- **Rocky Linux** (8, 9)
- **AlmaLinux** (8, 9)

## Installation

### Method 1: Using Setup Script (Recommended)

Run the setup script with sudo to automatically create and configure systemctl services:

```bash
sudo ./setup.sh
```

The script will:
1. Detect your operating system (Debian-based or RedHat-based)
2. Install dependencies using the appropriate package manager (apt/dnf/yum)
3. Create virtual environment and install Python packages
4. Build the frontend for production
5. Create systemd service files
6. Optionally enable and start the services

### Method 2: Manual Installation

If you've already run setup without sudo, you can create the services manually:

1. Create the backend service file:
```bash
sudo nano /etc/systemd/system/siemply-backend.service
```

Add:
```ini
[Unit]
Description=SIEMply Backend Service
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/SIEMPLY
Environment="PATH=/opt/SIEMPLY/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/SIEMPLY"
ExecStart=/opt/SIEMPLY/venv/bin/python /opt/SIEMPLY/backend/main.py --port 5050
Restart=always
RestartSec=10
StandardOutput=append:/opt/SIEMPLY/logs/backend.log
StandardError=append:/opt/SIEMPLY/logs/backend-error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

2. Create the frontend service file:
```bash
sudo nano /etc/systemd/system/siemply-frontend.service
```

Add:
```ini
[Unit]
Description=SIEMply Frontend Service
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/SIEMPLY/frontend
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/npm run preview -- --host 0.0.0.0 --port 8500
Restart=always
RestartSec=10
StandardOutput=append:/opt/SIEMPLY/logs/frontend.log
StandardError=append:/opt/SIEMPLY/logs/frontend-error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

3. Reload systemd and enable services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable siemply-backend.service
sudo systemctl enable siemply-frontend.service
sudo systemctl start siemply-backend.service
sudo systemctl start siemply-frontend.service
```

## Service Management

### Starting Services

Start both services:
```bash
sudo systemctl start siemply-backend
sudo systemctl start siemply-frontend
```

Or start them together using the combined service:
```bash
sudo systemctl start siemply
```

### Stopping Services

Stop both services:
```bash
sudo systemctl stop siemply-backend
sudo systemctl stop siemply-frontend
```

Or:
```bash
sudo systemctl stop siemply
```

### Restarting Services

Restart backend (after code changes):
```bash
sudo systemctl restart siemply-backend
```

Restart frontend (after frontend changes):
```bash
sudo systemctl restart siemply-frontend
```

Restart both:
```bash
sudo systemctl restart siemply-backend siemply-frontend
```

### Checking Status

Check backend status:
```bash
sudo systemctl status siemply-backend
```

Check frontend status:
```bash
sudo systemctl status siemply-frontend
```

Check if services are enabled:
```bash
sudo systemctl is-enabled siemply-backend
sudo systemctl is-enabled siemply-frontend
```

### Viewing Logs

View backend logs (live):
```bash
sudo journalctl -u siemply-backend -f
```

View frontend logs (live):
```bash
sudo journalctl -u siemply-frontend -f
```

View last 100 lines of backend logs:
```bash
sudo journalctl -u siemply-backend -n 100
```

View logs since today:
```bash
sudo journalctl -u siemply-backend --since today
```

View logs from both services:
```bash
sudo journalctl -u siemply-backend -u siemply-frontend -f
```

## Log Files

In addition to journalctl, logs are also stored in files:

- Backend logs: `/opt/SIEMPLY/logs/backend.log`
- Backend errors: `/opt/SIEMPLY/logs/backend-error.log`
- Frontend logs: `/opt/SIEMPLY/logs/frontend.log`
- Frontend errors: `/opt/SIEMPLY/logs/frontend-error.log`

View log files:
```bash
tail -f /opt/SIEMPLY/logs/backend.log
tail -f /opt/SIEMPLY/logs/frontend.log
```

## Auto-Start on Boot

Enable services to start automatically on boot:
```bash
sudo systemctl enable siemply-backend
sudo systemctl enable siemply-frontend
```

Disable auto-start:
```bash
sudo systemctl disable siemply-backend
sudo systemctl disable siemply-frontend
```

## Troubleshooting

### Service Won't Start

1. Check the service status for errors:
```bash
sudo systemctl status siemply-backend
```

2. View detailed logs:
```bash
sudo journalctl -u siemply-backend -n 50 --no-pager
```

3. Verify file permissions:
```bash
ls -la /opt/SIEMPLY
ls -la /opt/SIEMPLY/backend/main.py
```

4. Test manually:
```bash
cd /opt/SIEMPLY
source venv/bin/activate
python backend/main.py --port 5050
```

### Port Already in Use

Check what's using the port:
```bash
sudo lsof -i :5050
sudo lsof -i :8500
```

Kill the process or change the port in the service file.

### Permission Denied Errors

Ensure the user specified in the service file has proper permissions:
```bash
sudo chown -R YOUR_USERNAME:YOUR_USERNAME /opt/SIEMPLY
```

### Service Fails After Reboot

1. Check if services are enabled:
```bash
sudo systemctl is-enabled siemply-backend
```

2. Enable if not enabled:
```bash
sudo systemctl enable siemply-backend siemply-frontend
```

3. Check for dependency issues:
```bash
sudo systemctl list-dependencies siemply-backend
```

## Uninstalling Services

To remove the systemctl services:

```bash
# Stop services
sudo systemctl stop siemply-backend siemply-frontend

# Disable services
sudo systemctl disable siemply-backend siemply-frontend

# Remove service files
sudo rm /etc/systemd/system/siemply-backend.service
sudo rm /etc/systemd/system/siemply-frontend.service
sudo rm /etc/systemd/system/siemply.service

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl reset-failed
```

## Advanced Configuration

### Changing Service User

Edit the service file:
```bash
sudo nano /etc/systemd/system/siemply-backend.service
```

Change the `User=` line to your desired user, then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart siemply-backend
```

### Changing Ports

Edit the service file and modify the ExecStart line:
```bash
sudo nano /etc/systemd/system/siemply-backend.service
```

Change `--port 5050` to your desired port, then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart siemply-backend
```

### Adding Environment Variables

Edit the service file and add environment variables in the `[Service]` section:
```ini
Environment="MY_VAR=value"
Environment="ANOTHER_VAR=another_value"
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart siemply-backend
```

## SELinux (RedHat-based Systems)

If you're using SELinux (RHEL/CentOS/Fedora), you may need to configure it:

Check SELinux status:
```bash
sestatus
```

If SELinux is enforcing and causing issues:

1. Check audit logs:
```bash
sudo ausearch -m avc -ts recent
```

2. Generate and apply policy:
```bash
sudo grep siemply /var/log/audit/audit.log | audit2allow -M siemply
sudo semodule -i siemply.pp
```

3. Or temporarily set to permissive (not recommended for production):
```bash
sudo setenforce 0
```

## Firewall Configuration

### UFW (Ubuntu/Debian)

```bash
sudo ufw allow 5050/tcp
sudo ufw allow 8500/tcp
sudo ufw reload
```

### firewalld (RHEL/CentOS/Fedora)

```bash
sudo firewall-cmd --permanent --add-port=5050/tcp
sudo firewall-cmd --permanent --add-port=8500/tcp
sudo firewall-cmd --reload
```

## Performance Tuning

### Increase File Descriptors

Edit the service file and add:
```ini
[Service]
LimitNOFILE=65536
```

### Resource Limits

Add to service file:
```ini
[Service]
MemoryLimit=2G
CPUQuota=200%
```

## Support

For issues or questions:
- Check logs: `sudo journalctl -u siemply-backend -f`
- Review documentation: `/opt/SIEMPLY/docs/`
- GitHub Issues: https://github.com/yourusername/SIEMPLY/issues

