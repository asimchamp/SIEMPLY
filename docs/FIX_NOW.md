# Fix Your RHEL Server NOW! 🚀

## Quick Fix Commands

Run these commands on your RHEL 9.6 server:

```bash
cd /opt/SIEMPLY

# Remove old virtual environment (contains incompatible bcrypt)
sudo rm -rf venv/

# Remove corrupted database
sudo rm -f backend/siemply.db*

# Run the enhanced setup script
sudo ./setup.sh
```

## What This Does

1. ✅ **Removes old venv** - Gets rid of incompatible bcrypt 4.1+
2. ✅ **Removes old database** - Clears corrupted database files
3. ✅ **Runs fresh setup** - Installs everything correctly:
   - Compatible bcrypt 4.0.1
   - All dependencies
   - Fresh database with tables only
   - Admin user with correct password
   - Systemctl services

## Expected Output

```
======================================
  SIEMply Setup Script               
======================================
Running as root - will install systemctl services

Detected OS: Red Hat Enterprise Linux 9.6 (Plow)
✓ RedHat-based system detected (using dnf)

Step 1: Checking system dependencies...
✓ sqlite3 is installed
✓ Python 3.9.21 is installed
✓ Node.js v18.19.0 installed successfully

Step 3: Installing Python dependencies...
Installing compatible bcrypt version...
Successfully installed bcrypt-4.0.1
✓ bcrypt is working correctly
✓ Python dependencies installed

Step 7: Initializing database...
Creating database tables...
INFO: main : Creating database tables...
INFO: main : Database tables created successfully.
✓ Database initialized and validated successfully

Step 8: Creating admin user...
Admin user 'admin' created successfully.
✓ Admin user created

Step 9: Creating systemctl service files...
✓ Backend service file created
✓ Frontend service file created

Do you want to enable and start the systemctl services now? (y/n)
y

✓ Services enabled and started

======================================
      Setup Complete!                 
======================================

✓ Services are running!
```

## After Setup

Access SIEMply at:
```
http://10.128.14.71:8500

Username: admin
Password: admin123
```

## Verify Everything Works

```bash
# Check services
sudo systemctl status siemply-backend
sudo systemctl status siemply-frontend

# Check database
sqlite3 /opt/SIEMPLY/backend/siemply.db "SELECT username FROM users;"
# Should show: admin

# Check bcrypt version
cd /opt/SIEMPLY && source venv/bin/activate
python3 -c "import bcrypt; print('bcrypt:', bcrypt.__version__)"
# Should show: bcrypt: 4.0.1

# Test API
curl http://localhost:5050/health
# Should return JSON
```

## If Something Goes Wrong

### Setup fails at Python dependencies
```bash
sudo dnf install gcc python3-devel libffi-devel
sudo ./setup.sh
```

### Setup fails at Node.js
```bash
sudo dnf install nodejs npm
sudo ./setup.sh
```

### Database still has errors
```bash
sudo rm -f /opt/SIEMPLY/backend/siemply.db*
cd /opt/SIEMPLY
source venv/bin/activate
python backend/create_admin.py
```

### Services won't start
```bash
sudo journalctl -u siemply-backend -n 50
# Review logs and fix any errors shown
```

## Complete Nuclear Option

If nothing works, complete reset:

```bash
cd /opt/SIEMPLY

# Stop everything
sudo systemctl stop siemply-backend siemply-frontend 2>/dev/null

# Remove ALL generated files
sudo rm -rf venv/
sudo rm -rf frontend/node_modules/
sudo rm -rf frontend/dist/
sudo rm -f backend/siemply.db*
sudo rm -f .env
sudo rm -f frontend/.env

# Fresh start
sudo ./setup.sh
```

## What Was Fixed

1. **Bcrypt Compatibility** ✅
   - Now installs bcrypt 4.0.1 (compatible with passlib)
   - No more `__about__` errors
   - No more "password too long" errors

2. **Database Initialization** ✅
   - Only creates tables (no user creation)
   - No bcrypt calls during table creation
   - Corruption handling and validation

3. **Admin User** ✅
   - Created once by create_admin.py
   - Password: admin123 (not "admin")
   - No conflicts

4. **Automatic Everything** ✅
   - Node.js installation
   - sqlite3 installation
   - Python dependencies
   - Systemctl services

## Time to Complete

Total time: ~5-10 minutes depending on your network speed

Breakdown:
- Remove old files: 10 seconds
- Setup script: 3-8 minutes
  - Dependencies download: 2-5 minutes
  - Database init: 5 seconds
  - Frontend build: 1-3 minutes
  - Services setup: 10 seconds

## Success Criteria

✅ All steps complete without errors  
✅ Services are running  
✅ Can login at http://YOUR_IP:8500  
✅ Database has admin user  
✅ bcrypt version is 4.0.1  

## Need Help?

Check these guides:
- **This fix:** `BCRYPT_FIX_GUIDE.md`
- **Database issues:** `DATABASE_FIX_GUIDE.md`
- **RHEL setup:** `RHEL_QUICK_START.md`
- **Services:** `SYSTEMCTL_SERVICES.md`

## Ready? Let's Go! 🚀

```bash
cd /opt/SIEMPLY && \
sudo rm -rf venv/ && \
sudo rm -f backend/siemply.db* && \
sudo ./setup.sh
```

Answer 'y' when asked about enabling services.

That's it! Your RHEL 9.6 server will be running SIEMply in minutes!

