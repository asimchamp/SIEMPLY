# Database Corruption Fix Guide

## Problem

You may encounter this error during setup:
```
sqlite3.DatabaseError: file is not a database
✗ Failed to initialize database
```

## Root Cause

This error occurs when:
1. A previous setup attempt failed or was interrupted
2. The database file (`backend/siemply.db`) exists but is corrupted or empty
3. The file isn't a valid SQLite database format

## Solution (Automatic)

The `setup.sh` script now **automatically handles this issue**! 🎉

Just run the setup again:
```bash
cd /opt/SIEMPLY
sudo ./setup.sh
```

## What the Script Does Automatically

### Step 1: Detection
```
Step 7: Initializing database...
Existing database file found. Validating...
```

### Step 2: Validation
The script checks if the database is valid using:
```bash
sqlite3 siemply.db "PRAGMA integrity_check;"
```

### Step 3: Action

**If Corrupted:**
```
⚠ Database file is corrupted or invalid
Backing up and removing corrupted database...
✓ Corrupted database backed up as: siemply.db.corrupted.20251029_150523.bak
```

**If Valid:**
```
Database file exists and appears valid. Backing up...
✓ Database backed up as: siemply.db.backup.20251029_150523
```

### Step 4: Fresh Database
```
✓ Database initialized and validated successfully
```

## Manual Fix (If Needed)

If you want to manually fix before running setup:

### Quick Fix - Remove Database
```bash
cd /opt/SIEMPLY
rm -f backend/siemply.db
sudo ./setup.sh
```

### Safe Fix - Backup Then Remove
```bash
cd /opt/SIEMPLY
# Backup the corrupted file
cp backend/siemply.db backend/siemply.db.backup
# Remove it
rm -f backend/siemply.db
# Run setup
sudo ./setup.sh
```

## Understanding the Validation Process

### 1. Pre-Initialization Check
```bash
# The script checks if database file exists
if [ -f "$SCRIPT_DIR/backend/siemply.db" ]; then
    # Validate it
    sqlite3 "$DB_FILE" "PRAGMA integrity_check;"
fi
```

### 2. Corruption Detection
If validation fails:
- File is moved to: `siemply.db.corrupted.TIMESTAMP.bak`
- Fresh database will be created

### 3. Post-Initialization Validation
```bash
# Verify database is valid
sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;"
```

## Backup Files

Backup files are created with timestamps:

**Corrupted Database:**
```
backend/siemply.db.corrupted.20251029_150523.bak
```

**Valid Database:**
```
backend/siemply.db.backup.20251029_150523
```

These backups are kept so you can:
- Review what went wrong
- Recover any data if needed
- Compare with the new database

## Preventing Database Corruption

### Best Practices

1. **Always use sudo:**
   ```bash
   sudo ./setup.sh
   ```

2. **Don't interrupt setup:**
   - Let the script complete fully
   - Don't press Ctrl+C during database initialization

3. **Check disk space:**
   ```bash
   df -h /opt/SIEMPLY
   ```

4. **Check permissions:**
   ```bash
   ls -la /opt/SIEMPLY/backend/
   ```

5. **Use fresh environment:**
   - If multiple setup attempts failed, clean up first:
   ```bash
   rm -f /opt/SIEMPLY/backend/siemply.db*
   ```

## Troubleshooting

### Problem: Script says sqlite3 not found

**Solution:** The script now installs sqlite3 automatically!
```bash
sudo ./setup.sh
```

It will install:
- **RHEL/CentOS:** `sudo dnf install sqlite`
- **Ubuntu/Debian:** `sudo apt install sqlite3`

### Problem: Permission denied on database file

**Fix permissions:**
```bash
sudo chown -R $USER:$USER /opt/SIEMPLY/backend/
```

Or run setup as root:
```bash
sudo ./setup.sh
```

### Problem: Disk is full

**Check disk space:**
```bash
df -h /opt/SIEMPLY
```

**Clean up old backups:**
```bash
cd /opt/SIEMPLY/backend
ls -lh siemply.db.*
# Remove old backups
rm -f siemply.db.corrupted.*.bak
rm -f siemply.db.backup.*
```

### Problem: Database still fails after automatic fix

**Nuclear option - complete reset:**
```bash
cd /opt/SIEMPLY
# Remove all database files
sudo rm -f backend/siemply.db*
# Remove virtual environment (will be recreated)
sudo rm -rf venv/
# Run setup fresh
sudo ./setup.sh
```

## What's in the Database?

The SIEMply database contains:
- **hosts** - Managed host inventory
- **users** - User accounts and authentication
- **jobs** - Job execution history
- **playbook_executions** - Playbook run records
- **server_classes** - Host groupings
- **packages** - Software package inventory

## Checking Database Health

After successful setup, verify database:

```bash
cd /opt/SIEMPLY

# Check if database exists
ls -lh backend/siemply.db

# Check database integrity
sqlite3 backend/siemply.db "PRAGMA integrity_check;"
# Should output: ok

# List tables
sqlite3 backend/siemply.db ".tables"
# Should show: hosts, users, jobs, etc.

# Check if admin user exists
sqlite3 backend/siemply.db "SELECT username FROM users;"
# Should show: admin
```

## Error Messages Explained

### "file is not a database"
- The file exists but isn't a valid SQLite database
- Usually empty file or corrupted
- **Fix:** Script automatically removes and recreates

### "database is locked"
- Another process is using the database
- **Fix:** Stop other processes or wait

### "unable to open database file"
- Permission issues
- **Fix:** Check file permissions

## Technical Details

### SQLite3 Validation Command
```bash
# Check integrity
sqlite3 siemply.db "PRAGMA integrity_check;"

# Output if valid:
ok

# Output if corrupted:
# (Returns non-zero exit code)
```

### Retry Logic
If initialization fails:
1. Script removes the database file
2. Retries initialization once
3. If still fails, exits with error

### Validation After Creation
```bash
# Check if tables exist
sqlite3 siemply.db "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;"

# If successful, database is valid
# If fails, database creation failed
```

## Summary

✅ **Automatic Detection** - Script finds corrupted databases  
✅ **Automatic Backup** - Corrupted files are backed up with timestamps  
✅ **Automatic Fix** - Fresh database created automatically  
✅ **Automatic Validation** - Verifies database works after creation  
✅ **Retry Logic** - Attempts to fix if initialization fails  

**You don't need to do anything manually - just run:**
```bash
sudo ./setup.sh
```

The script handles everything! 🚀

## Support

If you continue to have database issues after running the enhanced setup script:

1. Check logs: `/opt/SIEMPLY/logs/`
2. Review backup files: `/opt/SIEMPLY/backend/siemply.db.*`
3. Try nuclear option (complete reset)
4. Check disk space and permissions

For persistent issues, ensure:
- You have write permissions to `/opt/SIEMPLY/backend/`
- Sufficient disk space available
- No other processes accessing the database
- sqlite3 is installed (script installs automatically)

