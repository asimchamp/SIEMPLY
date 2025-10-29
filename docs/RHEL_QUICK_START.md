# RHEL Quick Start Guide

Quick reference for running SIEMply on Red Hat Enterprise Linux 9.6

## One-Line Setup

```bash
cd /opt/SIEMPLY && sudo ./setup.sh
```

That's it! Everything is automatic now. ✅

## What It Does Automatically

1. ✅ Detects RHEL 9.6
2. ✅ Installs curl (if missing)
3. ✅ Installs sqlite3 (if missing)
4. ✅ Installs Python 3 + pip + devel (if missing)
5. ✅ Installs Node.js 18 + npm (if missing)
6. ✅ Creates virtual environment
7. ✅ Installs Python dependencies
8. ✅ Installs Node.js dependencies
9. ✅ Creates .env files
10. ✅ **Validates/fixes corrupted database**
11. ✅ Initializes fresh database
12. ✅ Creates admin user (admin/admin123)
13. ✅ Builds frontend for production
14. ✅ Creates systemctl services
15. ✅ Optionally starts services

## Expected Output

```
======================================
  SIEMply Setup Script               
======================================
Running as root - will install systemctl services

Detected OS: Red Hat Enterprise Linux 9.6 (Plow)
✓ RedHat-based system detected (using dnf)

Server IP address: 10.128.14.71

Step 1: Checking system dependencies...
✓ sqlite3 is installed
✓ Python 3.9.21 is installed
Installing Node.js automatically...
✓ Node.js v18.19.0 installed successfully

Step 2: Setting up Python virtual environment...
✓ Virtual environment created

Step 3: Installing Python dependencies...
✓ Python dependencies installed

Step 4: Installing Node.js dependencies...
✓ Node.js dependencies installed

Step 5: Creating .env file...
✓ New .env file created with SECRET_KEY

Step 6: Creating frontend .env file...
✓ Frontend .env file created

Step 7: Initializing database...
Existing database file found. Validating...
⚠ Database file is corrupted or invalid
Backing up and removing corrupted database...
✓ Corrupted database backed up as: siemply.db.corrupted.20251029_150523.bak
✓ Database initialized and validated successfully

Step 8: Creating admin user...
✓ Admin user created

Step 8.5: Building frontend for production...
✓ Frontend built successfully

Step 9: Creating systemctl service files...
✓ Backend service file created
✓ Frontend service file created
✓ Combined service file created

Do you want to enable and start the systemctl services now? (y/n)
y

✓ Services enabled and started

======================================
      Setup Complete!                 
======================================

✓ Services are running!
```

## After Setup

Access the application:
```
URL: http://10.128.14.71:8500
Username: admin
Password: admin123
```

## Service Management

```bash
# Check status
sudo systemctl status siemply-backend
sudo systemctl status siemply-frontend

# Restart
sudo systemctl restart siemply-backend
sudo systemctl restart siemply-frontend

# Stop
sudo systemctl stop siemply-backend
sudo systemctl stop siemply-frontend

# View logs
sudo journalctl -u siemply-backend -f
sudo journalctl -u siemply-frontend -f
```

## Troubleshooting

### Database Error Fixed Automatically

If you see:
```
⚠ Database file is corrupted or invalid
```

**Don't worry!** The script automatically:
- Backs up the corrupted file
- Removes it
- Creates a fresh database
- Validates it works

### If Setup Fails

Run it again:
```bash
cd /opt/SIEMPLY
sudo ./setup.sh
```

The script is idempotent - safe to run multiple times.

### Check Services

```bash
sudo systemctl status siemply-backend
```

If not running:
```bash
sudo systemctl start siemply-backend
sudo systemctl start siemply-frontend
```

### Firewall

Open ports if needed:
```bash
sudo firewall-cmd --permanent --add-port=5050/tcp
sudo firewall-cmd --permanent --add-port=8500/tcp
sudo firewall-cmd --reload
```

### SELinux

Check if SELinux is blocking:
```bash
sudo ausearch -m avc -ts recent | grep siemply
```

If issues, see: `SYSTEMCTL_SERVICES.md`

## Quick Commands

```bash
# Setup
sudo ./setup.sh

# Check what's running
sudo systemctl status siemply-*

# Restart everything
sudo systemctl restart siemply-backend siemply-frontend

# View live logs
sudo journalctl -u siemply-backend -u siemply-frontend -f

# Check Node.js version
node --version

# Check Python version
python3 --version

# Check database
ls -lh /opt/SIEMPLY/backend/siemply.db
sqlite3 /opt/SIEMPLY/backend/siemply.db "PRAGMA integrity_check;"
```

## Clean Start

If you want to completely reset:
```bash
cd /opt/SIEMPLY

# Stop services
sudo systemctl stop siemply-backend siemply-frontend

# Remove everything
sudo rm -rf venv/
sudo rm -f backend/siemply.db*
sudo rm -rf frontend/node_modules/
sudo rm -rf frontend/dist/

# Fresh setup
sudo ./setup.sh
```

## Documentation

- **Setup Guide:** `SETUP_GUIDE.md`
- **Service Management:** `SYSTEMCTL_SERVICES.md`
- **Auto-Install:** `AUTO_DEPENDENCY_INSTALL.md`
- **Database Issues:** `DATABASE_FIX_GUIDE.md`
- **Complete Changes:** `SESSION_CHANGES_SUMMARY.md`

## Support Checklist

Before asking for help:

1. ✅ Ran `sudo ./setup.sh` (not just `./setup.sh`)
2. ✅ Let it complete fully (didn't interrupt)
3. ✅ Checked service status: `sudo systemctl status siemply-backend`
4. ✅ Checked logs: `sudo journalctl -u siemply-backend -n 50`
5. ✅ Verified firewall: ports 5050 and 8500 open
6. ✅ Checked SELinux: `sudo ausearch -m avc -ts recent`

## Key Features for RHEL

✅ **Automatic Node.js Installation**
- Uses `dnf install nodejs npm` from default RHEL 9 repos
- No external repositories needed
- Installs Node.js 18 (LTS)

✅ **Database Corruption Handling**
- Detects invalid database files
- Backs up with timestamp
- Creates fresh database automatically

✅ **Systemctl Services**
- Production-ready service files
- Auto-restart on failure
- Centralized logging with journalctl

✅ **SELinux Compatible**
- Works with SELinux enforcing
- See `SYSTEMCTL_SERVICES.md` for policy setup

✅ **Firewalld Integration**
- Easy port management
- Standard RHEL firewall

## Version Information

- **RHEL Version Tested:** 9.6 (Plow)
- **Python Version:** 3.9.21
- **Node.js Version:** 18.x (LTS)
- **Package Manager:** dnf

## Success Indicators

After setup, verify:

```bash
# Services are running
systemctl is-active siemply-backend  # Should show: active

# Database is valid
sqlite3 /opt/SIEMPLY/backend/siemply.db "PRAGMA integrity_check;"  # Should show: ok

# Can reach backend
curl http://localhost:5050/health  # Should return JSON

# Admin user exists
sqlite3 /opt/SIEMPLY/backend/siemply.db "SELECT username FROM users;"  # Should show: admin
```

If all checks pass: **✅ Installation Successful!**

Access at: `http://10.128.14.71:8500`

---

**Remember:** The setup script now handles everything automatically. Just run:

```bash
sudo ./setup.sh
```

And answer 'y' when asked to enable services. Done! 🚀

