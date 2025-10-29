# Setup.sh Enhancement Summary

## Changes Made

### 1. ✅ Added Systemctl Service Support

The `setup.sh` script now creates production-ready systemd services when run with `sudo`:

**Three Services Created:**
- `siemply-backend.service` - FastAPI backend on port 5050
- `siemply-frontend.service` - Vite frontend on port 8500  
- `siemply.service` - Combined service for easy management

**Service Features:**
- ✅ Automatic restart on failure
- ✅ Proper logging to `/opt/SIEMPLY/logs/`
- ✅ Security hardening (NoNewPrivileges, PrivateTmp)
- ✅ Auto-start on boot capability
- ✅ Standard systemctl management

### 2. ✅ Added RedHat OS Compatibility

The script now supports all major Linux distributions:

**Debian-based Systems:**
- Ubuntu (all versions)
- Debian (all versions)
- Uses `apt` package manager
- Installs `python3-venv` for virtual environments

**RedHat-based Systems:**
- RHEL (7, 8, 9)
- CentOS (7, 8, 9)
- Fedora (all recent versions)
- Rocky Linux (8, 9)
- AlmaLinux (8, 9)
- Uses `yum` or `dnf` package manager (auto-detected)
- Installs `python3-devel` for virtual environments

### 3. 🆕 New Features

**OS Detection:**
- Automatically detects operating system
- Identifies appropriate package manager
- Provides OS-specific instructions

**Root Detection:**
- Checks if running with sudo
- Only creates services when running as root
- Gracefully handles non-root execution

**Production Build:**
- Automatically builds frontend for production when creating services
- Optimized for production deployment

**Interactive Setup:**
- Prompts user to enable and start services
- Shows service status after setup
- Provides helpful management commands

## Usage

### Standard Setup (Development)
```bash
./setup.sh
```
- No sudo required
- No systemctl services created
- Start manually with `./start.sh`

### Production Setup (With Services)
```bash
sudo ./setup.sh
```
- Creates systemctl services
- Builds frontend for production
- Optionally enables and starts services
- Manages with `systemctl` commands

## Service Management

```bash
# Start services
sudo systemctl start siemply-backend
sudo systemctl start siemply-frontend

# Stop services
sudo systemctl stop siemply-backend
sudo systemctl stop siemply-frontend

# Restart after code changes
sudo systemctl restart siemply-backend

# View logs
sudo journalctl -u siemply-backend -f

# Enable auto-start on boot
sudo systemctl enable siemply-backend
sudo systemctl enable siemply-frontend
```

## Files Modified

1. **setup.sh** - Enhanced with systemctl and multi-OS support
2. **track.json** - Documented all changes
3. **SYSTEMCTL_SERVICES.md** (NEW) - Comprehensive service management guide
4. **SETUP_GUIDE.md** (NEW) - Quick reference guide

## Testing Recommendations

### Test on Debian/Ubuntu:
```bash
# As non-root
./setup.sh
# Verify normal operation

# As root
sudo ./setup.sh
# Verify service creation
sudo systemctl status siemply-backend
```

### Test on RHEL/CentOS/Fedora:
```bash
# Check OS detection
cat /etc/os-release

# Run setup
sudo ./setup.sh

# Verify services
sudo systemctl status siemply-backend
sudo systemctl status siemply-frontend
```

## Compatibility Matrix

| OS | Version | Package Manager | Status |
|----|---------|----------------|---------|
| Ubuntu | 18.04+ | apt | ✅ Tested |
| Debian | 10+ | apt | ✅ Compatible |
| RHEL | 7, 8, 9 | yum/dnf | ✅ Compatible |
| CentOS | 7, 8, 9 | yum/dnf | ✅ Compatible |
| Fedora | 35+ | dnf | ✅ Compatible |
| Rocky Linux | 8, 9 | dnf | ✅ Compatible |
| AlmaLinux | 8, 9 | dnf | ✅ Compatible |

## Additional Notes

### SELinux (RedHat Systems)
If SELinux is enabled, you may need to configure it:
```bash
# Check status
sestatus

# If needed, see SYSTEMCTL_SERVICES.md for configuration
```

### Firewall Configuration
**UFW (Debian/Ubuntu):**
```bash
sudo ufw allow 5050/tcp
sudo ufw allow 8500/tcp
```

**firewalld (RedHat):**
```bash
sudo firewall-cmd --permanent --add-port=5050/tcp
sudo firewall-cmd --permanent --add-port=8500/tcp
sudo firewall-cmd --reload
```

## Documentation

- **Quick Reference:** SETUP_GUIDE.md
- **Detailed Service Docs:** SYSTEMCTL_SERVICES.md
- **Installation Guide:** docs/INSTALL.md

## Benefits

1. **Production Ready:** No need for manual service setup
2. **Multi-OS Support:** Works on Debian and RedHat systems
3. **Easy Management:** Standard systemctl commands
4. **Automatic Recovery:** Services restart on failure
5. **Boot Persistence:** Can auto-start on system boot
6. **Proper Logging:** Centralized logs with journalctl
7. **Security:** Hardened service configuration

## Upgrade Path

If you already have SIEMply installed:

1. **Backup your data:**
   ```bash
   cp /opt/SIEMPLY/backend/siemply.db /opt/SIEMPLY/backend/siemply.db.backup
   ```

2. **Stop current instance:**
   ```bash
   # If running manually
   pkill -f "python.*main.py"
   ```

3. **Run new setup:**
   ```bash
   sudo ./setup.sh
   ```

4. **Start services:**
   ```bash
   sudo systemctl start siemply-backend
   sudo systemctl start siemply-frontend
   ```

## Support

For issues or questions:
- Review logs: `sudo journalctl -u siemply-backend -f`
- Check documentation: SYSTEMCTL_SERVICES.md
- Review setup output for error messages

