#!/usr/bin/env python3
"""
Cleanup script to remove orphaned jobs with null host_id values
This script should be run once to clean up existing data issues
"""
import sys
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.models import get_db, Job
from sqlalchemy import text

def cleanup_orphaned_jobs():
    """Remove jobs that have null host_id values"""
    db = next(get_db())
    
    try:
        # Count orphaned jobs
        orphaned_count = db.query(Job).filter(Job.host_id.is_(None)).count()
        print(f"Found {orphaned_count} jobs with null host_id values")
        
        if orphaned_count > 0:
            # Delete orphaned jobs
            deleted_count = db.query(Job).filter(Job.host_id.is_(None)).delete()
            db.commit()
            print(f"Deleted {deleted_count} orphaned jobs")
        else:
            print("No orphaned jobs found")
            
        # Verify cleanup
        remaining_orphaned = db.query(Job).filter(Job.host_id.is_(None)).count()
        print(f"Remaining orphaned jobs: {remaining_orphaned}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting cleanup of orphaned jobs...")
    cleanup_orphaned_jobs()
    print("Cleanup completed.")
