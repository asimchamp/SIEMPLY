#!/usr/bin/env python3
"""
Manual test of log copying using SSH commands
"""
import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

def copy_logs_manually():
    # Job details
    job_id = "splunk-ent-upgrade-fd16018f-2363-45ef-8774-40dbcfec07bc"
    host = "192.168.100.3"
    
    # Create logs directory
    local_log_dir = Path("/opt/SIEMPLY/backend/logs") / datetime.now().strftime("%Y-%m")
    local_log_dir.mkdir(parents=True, exist_ok=True)
    local_log_file = local_log_dir / f"{job_id}.json"
    
    print(f"Copying logs for job {job_id}")
    print(f"Target file: {local_log_file}")
    
    # Collect logs using SSH
    collected_logs = {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "host": host,
        "logs": {}
    }
    
    # Define log files to copy
    log_files = [
        "/tmp/siemply_splunk_upgrade/upgrade_runner.log",
        "/tmp/siemply_splunk_upgrade/env.json"
    ]
    
    for remote_path in log_files:
        try:
            # Check if file exists
            check_cmd = f"ssh root@{host} 'test -f {remote_path} && echo exists || echo missing'"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            
            if "exists" in result.stdout:
                # Copy file content
                cat_cmd = f"ssh root@{host} 'cat {remote_path}'"
                cat_result = subprocess.run(cat_cmd, shell=True, capture_output=True, text=True)
                
                if cat_result.returncode == 0:
                    log_name = Path(remote_path).name
                    collected_logs["logs"][log_name] = cat_result.stdout
                    print(f"✓ Collected {log_name} ({len(cat_result.stdout)} chars)")
                else:
                    print(f"✗ Failed to read {remote_path}: {cat_result.stderr}")
            else:
                print(f"✗ File not found: {remote_path}")
                
        except Exception as e:
            print(f"✗ Error processing {remote_path}: {str(e)}")
    
    # Save to JSON file
    try:
        with open(local_log_file, 'w') as f:
            json.dump(collected_logs, f, indent=2)
        print(f"✓ Saved logs to {local_log_file}")
        
        # Show file size
        file_size = os.path.getsize(local_log_file)
        print(f"✓ File size: {file_size} bytes")
        
        return True
    except Exception as e:
        print(f"✗ Failed to save logs: {str(e)}")
        return False

if __name__ == "__main__":
    copy_logs_manually()