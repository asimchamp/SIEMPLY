# Fix "Unable to Open Database File" Error - IMMEDIATE FIX

## Your Error

```
sqlite3.OperationalError: unable to open database file
```

This happens because the database was created by root and your application can't access it.

## Quick Fix - Run This Now on Your RHEL Server

```bash
cd /opt/SIEMPLY
sudo ./fix_permissions.sh
```

That's it! This will fix all file permissions.

## What It Does

1. ✅ Changes database ownership from root to your user
2. ✅ Sets correct permissions (664) on database file
3. ✅ Fixes backend, logs, playbooks directories
4. ✅ Tests database accessibility

## After Running fix_permissions.sh

Start the application:

```bash
# If using systemctl services:
sudo systemctl restart siemply-backend
sudo systemctl restart siemply-frontend

# Or if using start.sh:
./start.sh
```

## Expected Output from fix_permissions.sh

```
======================================
  SIEMply Permission Fix             
======================================

Current permissions:
-rw-r--r-- 1 root root 12345 Oct 29 19:00 backend/siemply.db

Setting ownership to: youruser
✓ Ownership set to youruser

New permissions:
-rw-rw-r-- 1 youruser youruser 12345 Oct 29 19:00 backend/siemply.db

Testing database access...
✓ Database is accessible

======================================
  Permission Fix Complete!           
======================================
```

## Verify It Worked

```bash
# Check database ownership
ls -la /opt/SIEMPLY/backend/siemply.db

# Should show your username, not root
# Example: -rw-rw-r-- 1 youruser youruser 123456 Oct 29 19:00 siemply.db

# Test database access
sqlite3 /opt/SIEMPLY/backend/siemply.db "SELECT 1;"

# Should return: 1
```

## If Still Not Working

### Option 1: More Permissive (Quick Fix)
```bash
cd /opt/SIEMPLY
sudo chmod 666 backend/siemply.db
sudo chmod -R 777 backend/
sudo chmod -R 777 logs/
```

Then restart:
```bash
sudo systemctl restart siemply-backend
```

### Option 2: Check Service User

Your systemctl service runs as a specific user. Check:
```bash
sudo systemctl status siemply-backend | grep "Main PID"
```

Then ensure that user owns the files:
```bash
# If service runs as 'siemply' user:
sudo chown -R siemply:siemply /opt/SIEMPLY/backend
sudo chown -R siemply:siemply /opt/SIEMPLY/logs

# Or check the service file:
grep User /etc/systemd/system/siemply-backend.service
```

### Option 3: Run as Root (Not Recommended)

Edit service file:
```bash
sudo nano /etc/systemd/system/siemply-backend.service
```

Change:
```ini
User=youruser
```

To:
```ini
#User=youruser  # Commented out - runs as root
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart siemply-backend
```

⚠️ **Warning:** Running as root is not secure for production!

## Prevention for Future Setups

Always use `sudo` when running setup (not logging in as root):

```bash
# Good ✅
sudo ./setup.sh

# Bad ❌ (creates permission issues)
su - root
./setup.sh
```

When you use `sudo`, the script can detect your real username and set permissions correctly.

## Understanding the Problem

1. **Setup ran as root:** Files created with root ownership
2. **Application tries to run as user:** Can't read root's files
3. **Result:** "unable to open database file"

**Solution:** Change file ownership from root to application user.

## Manual Permission Fix

If `fix_permissions.sh` doesn't work, manually fix:

```bash
cd /opt/SIEMPLY

# Find your username
whoami

# Set ownership (replace 'youruser' with your username)
sudo chown -R youruser:youruser backend/
sudo chown -R youruser:youruser logs/
sudo chown -R youruser:youruser playbooks/
sudo chown -R youruser:youruser venv/

# Set permissions
sudo chmod 664 backend/siemply.db
sudo chmod 775 backend/
sudo chmod 775 logs/

# Verify
ls -la backend/siemply.db
```

## Check Service Configuration

Your systemctl service should run as the same user that owns the files:

```bash
# Check service user
grep "User=" /etc/systemd/system/siemply-backend.service

# Check file owner
ls -la /opt/SIEMPLY/backend/siemply.db

# They should match!
```

## Test Database Access

```bash
cd /opt/SIEMPLY

# As your user
sqlite3 backend/siemply.db "SELECT username FROM users;"

# Should show: admin
```

If this works, the application will work too!

## Summary

**Immediate fix:**
```bash
cd /opt/SIEMPLY && sudo ./fix_permissions.sh
```

**Then restart:**
```bash
sudo systemctl restart siemply-backend siemply-frontend
```

**Verify:**
```bash
sudo systemctl status siemply-backend
curl http://localhost:5050/health
```

**Access:**
```
http://10.128.14.71:8500
Username: admin
Password: admin123
```

Done! 🚀

## Still Having Issues?

1. Check logs:
   ```bash
   sudo journalctl -u siemply-backend -n 50
   ```

2. Check file permissions:
   ```bash
   ls -laR /opt/SIEMPLY/backend/
   ```

3. Check SELinux (RHEL):
   ```bash
   sudo ausearch -m avc -ts recent | grep siemply
   ```

4. Try running backend manually:
   ```bash
   cd /opt/SIEMPLY
   source venv/bin/activate
   python backend/main.py --port 5050
   ```

The error message will show exactly what's wrong!

