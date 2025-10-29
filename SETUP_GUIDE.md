# SIEMply Setup Guide - Quick Reference

## Overview

The `setup.sh` script now supports:
- ✅ **Ubuntu/Debian** (apt package manager)
- ✅ **RHEL/CentOS/Fedora** (yum/dnf package manager)
- ✅ **Rocky Linux / AlmaLinux**
- ✅ **Automatic systemctl service creation**
- ✅ **Auto-start on boot capability**

## Quick Start

### Option 1: Standard Setup (No systemctl services)
```bash
cd /opt/SIEMPLY
./setup.sh
```

This will:
- Install Python and Node.js dependencies
- Create virtual environment
- Build frontend
- Initialize database
- Create admin user (admin/admin123)

After setup, start manually:
```bash
./start.sh
```

### Option 2: Production Setup (With systemctl services)
```bash
cd /opt/SIEMPLY
sudo ./setup.sh
```

This will do everything from Option 1, PLUS:
- Detect your OS (Debian or RedHat-based)
- Build frontend for production
- Create 3 systemctl services:
  - `siemply-backend.service` (port 5050)
  - `siemply-frontend.service` (port 8500)
  - `siemply.service` (combined service)
- Optionally enable and start services

## Systemctl Service Management

### Start Services
```bash
sudo systemctl start siemply-backend
sudo systemctl start siemply-frontend
# Or both at once:
sudo systemctl start siemply
```

### Stop Services
```bash
sudo systemctl stop siemply-backend
sudo systemctl stop siemply-frontend
# Or both:
sudo systemctl stop siemply
```

### Restart Services
```bash
sudo systemctl restart siemply-backend
sudo systemctl restart siemply-frontend
```

### Check Status
```bash
sudo systemctl status siemply-backend
sudo systemctl status siemply-frontend
```

### Enable Auto-Start on Boot
```bash
sudo systemctl enable siemply-backend
sudo systemctl enable siemply-frontend
```

### View Logs
```bash
# Live logs via journalctl
sudo journalctl -u siemply-backend -f
sudo journalctl -u siemply-frontend -f

# Or view log files directly
tail -f /opt/SIEMPLY/logs/backend.log
tail -f /opt/SIEMPLY/logs/frontend.log
```

## OS-Specific Notes

### Debian/Ubuntu Systems
- Uses `apt` package manager
- Python virtual environment package: `python3-venv`
- Firewall: UFW
  ```bash
  sudo ufw allow 5050/tcp
  sudo ufw allow 8500/tcp
  ```

### RedHat/CentOS/Fedora/Rocky/AlmaLinux Systems
- Uses `yum` or `dnf` package manager
- Python development package: `python3-devel`
- Firewall: firewalld
  ```bash
  sudo firewall-cmd --permanent --add-port=5050/tcp
  sudo firewall-cmd --permanent --add-port=8500/tcp
  sudo firewall-cmd --reload
  ```
- May need SELinux configuration (see SYSTEMCTL_SERVICES.md)

## Default Credentials

After setup, access the application at:
- **URL:** http://YOUR_SERVER_IP:8500
- **Username:** admin
- **Password:** admin123

⚠️ **Change the default password immediately after first login!**

## Troubleshooting

### Setup Script Issues

**Problem:** Virtual environment creation fails
```bash
# Debian/Ubuntu
sudo apt install python3-venv

# RHEL/CentOS/Fedora
sudo dnf install python3-devel
```

**Problem:** Node.js not found
```bash
# Debian/Ubuntu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# RHEL/CentOS/Fedora
sudo dnf install nodejs
```

### Service Issues

**Problem:** Service won't start
```bash
# Check detailed logs
sudo journalctl -u siemply-backend -n 50 --no-pager

# Verify file permissions
sudo chown -R $USER:$USER /opt/SIEMPLY

# Test manually
cd /opt/SIEMPLY
source venv/bin/activate
python backend/main.py --port 5050
```

**Problem:** Port already in use
```bash
# Check what's using the port
sudo lsof -i :5050
sudo lsof -i :8500

# Kill the process or change port in service file
```

**Problem:** Services don't start on boot
```bash
# Enable services
sudo systemctl enable siemply-backend
sudo systemctl enable siemply-frontend

# Verify
sudo systemctl is-enabled siemply-backend
```

## File Locations

- **Main Directory:** `/opt/SIEMPLY`
- **Virtual Environment:** `/opt/SIEMPLY/venv`
- **Backend Code:** `/opt/SIEMPLY/backend`
- **Frontend Code:** `/opt/SIEMPLY/frontend`
- **Database:** `/opt/SIEMPLY/backend/siemply.db`
- **Logs:** `/opt/SIEMPLY/logs/`
- **Playbooks:** `/opt/SIEMPLY/playbooks/`
- **Service Files:** `/etc/systemd/system/siemply*.service`

## Additional Documentation

- **Detailed Service Management:** See `SYSTEMCTL_SERVICES.md`
- **Installation Guide:** See `docs/INSTALL.md`
- **General Documentation:** See `README.md`

## Uninstalling Services

To completely remove systemctl services:
```bash
sudo systemctl stop siemply-backend siemply-frontend
sudo systemctl disable siemply-backend siemply-frontend
sudo rm /etc/systemd/system/siemply*.service
sudo systemctl daemon-reload
```

To remove the entire application:
```bash
sudo rm -rf /opt/SIEMPLY
```

## Support

For detailed documentation on systemctl services, including:
- SELinux configuration
- Performance tuning
- Advanced troubleshooting
- Firewall configuration

Please refer to: **SYSTEMCTL_SERVICES.md**

