# Automatic Dependency Installation

## Overview

The `setup.sh` script now automatically installs **all required dependencies** when run with `sudo`, eliminating manual installation steps.

## What Gets Installed Automatically

When you run `sudo ./setup.sh`, the script will automatically install:

1. **curl** - Required for downloading NodeSource repository
2. **Python 3** - Backend runtime environment
   - `python3`
   - `python3-pip`
   - `python3-venv` (Debian/Ubuntu) or `python3-devel` (RedHat)
3. **Node.js 18** - Frontend build tools
   - `nodejs`
   - `npm`

## How It Works

### Detection Phase
```
Step 1: Checking system dependencies...
✓ Checks if curl is installed
✓ Checks if Python 3 is installed  
✓ Checks if Node.js is installed
```

### Installation Phase (if missing)
```
✗ Node.js is not installed
Installing Node.js automatically...
✓ Node.js v18.x.x installed successfully
```

## Installation Methods by OS

### RHEL/CentOS 9 (like your server)
```bash
# Automatic installation
sudo dnf install -y nodejs npm
```

Node.js is available directly in the default RHEL 9 repositories!

### RHEL/CentOS 8
```bash
# Enables nodejs:18 module stream
sudo dnf module enable -y nodejs:18
sudo dnf install -y nodejs npm
```

### RHEL/CentOS 7
```bash
# Uses NodeSource RPM repository
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
sudo yum install -y nodejs
```

### Fedora
```bash
# Direct installation from default repos
sudo dnf install -y nodejs npm
```

### Ubuntu/Debian
```bash
# Uses NodeSource APT repository
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
sudo apt-get install -y nodejs
```

## Usage on Your RHEL 9.6 Server

### Before (Old Way - Manual)
```bash
# Step 1: Install Node.js manually
sudo dnf install nodejs npm

# Step 2: Run setup
./setup.sh
```

### Now (New Way - Automatic) ✨
```bash
# Just run setup with sudo - everything is automatic!
sudo ./setup.sh
```

The script will:
1. Detect RHEL 9.6
2. See that Node.js is missing
3. Automatically install Node.js 18 and npm
4. Continue with the rest of the setup
5. Create systemctl services
6. Start the application

## What You'll See

```
======================================
  SIEMply Setup Script               
======================================
Running as root - will install systemctl services

Detected OS: Red Hat Enterprise Linux 9.6 (Plow)
✓ RedHat-based system detected (using dnf)

Server IP address: 10.128.14.71

Step 1: Checking system dependencies...
✓ Python 3.9.21 is installed
✗ Node.js is not installed
Installing Node.js automatically...
Installing Node.js via dnf...
...
✓ Node.js v18.19.0 installed successfully

Step 2: Setting up Python virtual environment...
...
```

## Running Without Root

If you run without sudo:
```bash
./setup.sh
```

The script will:
1. Check for dependencies
2. **Stop and provide installation instructions** if dependencies are missing
3. Show OS-specific commands to install missing packages
4. Exit with helpful error message

## Verification

After installation, verify:
```bash
node --version
# Should show: v18.x.x

npm --version  
# Should show: 9.x.x or higher

python3 --version
# Should show: 3.x.x
```

## Troubleshooting

### Problem: Installation Fails on RHEL

**Check if you have subscription access:**
```bash
sudo dnf repolist
```

If repos are disabled, register the system:
```bash
sudo subscription-manager register
sudo subscription-manager attach --auto
```

### Problem: Network Issues

The script needs internet access to:
- Download NodeSource repository (RHEL 7, Ubuntu/Debian)
- Install packages from repos

**Check internet connectivity:**
```bash
curl -I https://www.google.com
```

### Problem: Proxy Environment

If behind a corporate proxy:
```bash
export http_proxy="http://proxy.company.com:8080"
export https_proxy="http://proxy.company.com:8080"
sudo -E ./setup.sh
```

## Benefits

✅ **One Command Setup** - Just `sudo ./setup.sh`  
✅ **No Manual Steps** - Installs everything automatically  
✅ **OS Detection** - Uses correct method for your OS  
✅ **Version Control** - Installs Node.js 18 (LTS)  
✅ **Error Handling** - Verifies installation success  
✅ **Production Ready** - Sets up systemctl services  

## Node.js Version Information

The script installs **Node.js 18.x** which is:
- ✅ LTS (Long Term Support) until April 2025
- ✅ Compatible with Vite (frontend build tool)
- ✅ Available in RHEL 9 default repositories
- ✅ Stable and production-ready

## Security Notes

The script:
- Only installs packages from official repositories
- Uses HTTPS for downloading repository configurations
- Verifies installations before proceeding
- Runs with appropriate user permissions for services

## Additional Information

For more details:
- **Service Management:** See `SYSTEMCTL_SERVICES.md`
- **Complete Setup Guide:** See `SETUP_GUIDE.md`
- **Enhancement Summary:** See `SETUP_ENHANCEMENT_SUMMARY.md`

## Summary

**Before:** Manual installation required  
**Now:** Fully automated with `sudo ./setup.sh`

Your RHEL 9.6 server setup is now as simple as:
```bash
cd /opt/SIEMPLY
sudo ./setup.sh
```

Everything else is handled automatically! 🚀

