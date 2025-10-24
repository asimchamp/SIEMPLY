#!/usr/bin/env python3
"""
UF upgrade runner script to be uploaded to the remote host and executed under tmux.
Reads env.json from the same directory and performs the full Splunk UF upgrade.
"""
import json
import os
import subprocess
import sys
import time

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(THIS_DIR, 'upgrade_runner.log')

def log(msg: str):
    with open(LOG_FILE, 'a') as lf:
        lf.write(msg.rstrip() + "\n")
    print(msg)

def run(cmd: str) -> tuple[int, str, str]:
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode(), p.stderr.decode()

def main() -> int:
    print("=== MAIN FUNCTION STARTING ===", flush=True)
    try:
        env_path = os.path.join(THIS_DIR, 'env.json')
        print(f"Looking for env.json at: {env_path}", flush=True)
        # When uploaded to remote, THIS_DIR will be the remote temp dir
        if not os.path.exists(env_path):
            print(f"env.json not found at {env_path}, trying fallback", flush=True)
            # Fallback: try ../env.json if script uploaded without folder structure
            alt = os.path.join(os.path.dirname(THIS_DIR), 'env.json')
            if os.path.exists(alt):
                env_path = alt
                print(f"Found env.json at fallback location: {env_path}", flush=True)
            else:
                print('env.json not found', file=sys.stderr)
                return 99

        log(f"Using env: {env_path}")
        with open(env_path, 'r') as f:
            env = json.load(f)
        print(f"Loaded environment data: {env}", flush=True)
    except Exception as e:
        print(f"ERROR: Failed to load environment: {e}", file=sys.stderr)
        return 1

    version = env.get('version')
    arch = env.get('architecture', 'x86_64')
    install_dir = env.get('install_dir', '/opt')
    # Note: admin_password not required for upgrades as password is already set
    user = env.get('user', 'splunk')
    group = env.get('group', 'splunk')
    deployment_server = env.get('deployment_server')
    deployment_app = env.get('deployment_app')
    download_url = env.get('download_url')

    tmp = THIS_DIR
    os.makedirs(tmp, exist_ok=True)
    pkg_path = os.path.join(tmp, 'splunkforwarder.tgz')

    if not version or not download_url:
        log("ERROR: Missing required parameters (version, download_url)")
        return 1

    # Check if UF is installed
    log(f"Checking for existing Splunk UF installation at {install_dir}/splunkforwarder...")
    rc, out, err = run(f"test -d {install_dir}/splunkforwarder && echo 'exists' || echo 'not exists'")
    if "not exists" in out:
        log(f"ERROR: Splunk UF is not installed at {install_dir}/splunkforwarder")
        return 1

    # Get current version
    log("Checking current Splunk UF version...")
    rc, out, err = run(f"sudo -u {user} {install_dir}/splunkforwarder/bin/splunk version 2>/dev/null || echo 'unknown'")
    current_version = "unknown"
    if "Splunk Universal Forwarder" in out:
        for line in out.split('\n'):
            if 'Splunk Universal Forwarder' in line:
                parts = line.split()
                if len(parts) >= 4:
                    current_version = parts[3]
                    break
    
    log(f"Current version: {current_version}, Target version: {version}")

    # Stop Splunk UF
    log("Stopping Splunk UF...")
    rc, out, err = run(f"{install_dir}/splunkforwarder/bin/splunk stop --answer-yes --no-prompt 2>&1 || true")
    log(f"Stop result: {out}")

    # Wait for shutdown
    time.sleep(3)

    # Ensure Splunk processes are stopped using Splunk CLI (avoid pkill)
    log("Ensuring all Splunk processes are stopped via Splunk CLI...")
    max_wait_seconds = 60
    waited_seconds = 0
    while waited_seconds < max_wait_seconds:
        rc_status, out_status, err_status = run(f"{install_dir}/splunkforwarder/bin/splunk status 2>&1 || true")
        log(f"Status check: rc={rc_status}, out={out_status.strip()}")
        lower_out = out_status.lower()
        if ("is not running" in lower_out) or ("not running" in lower_out):
            break
        time.sleep(2)
        waited_seconds += 2
    if waited_seconds >= max_wait_seconds:
        log("WARNING: Splunk did not report 'not running' within timeout; proceeding with upgrade")

    # Create temp directory
    log("Creating temporary directory...")
    print(f"About to create directory: {tmp}", flush=True)
    rc, out, err = run(f"sudo mkdir -p {tmp}")
    print(f"mkdir completed with rc={rc}, out={repr(out)}, err={repr(err)}", flush=True)
    if rc != 0:
        log(f"ERROR: Failed to create temp directory: {err}")
        return 1
    log(f"Temporary directory created: {tmp}")

    # Check available tools
    log("Checking for download tools...")
    rc_curl, _, _ = run("which curl")
    rc_wget, _, _ = run("which wget")
    has_curl = rc_curl == 0
    has_wget = rc_wget == 0
    log(f"Available tools - curl: {has_curl}, wget: {has_wget}")

    if not has_curl and not has_wget:
        log("ERROR: Neither curl nor wget is available")
        return 1

    # Download new version
    log(f"Downloading Splunk UF {version} from: {download_url}")
    download_success = False

    if has_curl:
        log("Attempting download with curl...")
        rc, out, err = run(f"cd {tmp} && sudo curl -L -o splunkforwarder.tgz '{download_url}' 2>&1")
        log(f"Curl command result - RC: {rc}, Output: {out[:200]}, Error: {err[:200]}")
        if rc == 0:
            download_success = True
            log("Successfully downloaded with curl")
        else:
            log(f"Curl failed with return code {rc}: {err}")

    if not download_success and has_wget:
        log("Attempting download with wget...")
        rc, out, err = run(f"cd {tmp} && sudo wget -O splunkforwarder.tgz '{download_url}' 2>&1")
        log(f"Wget command result - RC: {rc}, Output: {out[:200]}, Error: {err[:200]}")
        if rc == 0:
            download_success = True
            log("Successfully downloaded with wget")
        else:
            log(f"Wget failed with return code {rc}: {err}")

    if not download_success:
        log("ERROR: Failed to download Splunk UF package from all methods")
        log(f"Final download URL was: {download_url}")
        return 1

    # Verify download
    rc, out, err = run(f"ls -la {pkg_path}")
    if rc != 0:
        log(f"ERROR: Downloaded package not found: {err}")
        return 1

    log(f"Download verified: {out.strip()}")

    # Backup current configuration
    log("Backing up current configuration...")
    backup_timestamp = time.strftime("%Y%m%d_%H%M%S")
    rc, out, err = run(f"sudo cp -r {install_dir}/splunkforwarder/etc {install_dir}/splunkforwarder/etc.backup.{backup_timestamp}")
    if rc != 0:
        log(f"WARNING: Failed to backup configuration: {err}")
    else:
        log(f"Configuration backed up to etc.backup.{backup_timestamp}")

    # Extract new version to temporary location
    log("Extracting new version...")
    rc, out, err = run(f"cd {tmp} && sudo tar -xzf splunkforwarder.tgz")
    if rc != 0:
        log(f"ERROR: Failed to extract new version: {err}")
        return 1

    # Stop any services
    log("Stopping any Splunk services...")
    run("sudo systemctl stop Splunkd 2>/dev/null || true")
    run("sudo systemctl stop SplunkForwarder 2>/dev/null || true")

    # Replace the installation (preserve etc directory)
    log("Replacing Splunk UF installation...")
    
    # Move current etc to temp location
    rc, out, err = run(f"sudo mv {install_dir}/splunkforwarder/etc {tmp}/etc.preserve")
    if rc != 0:
        log(f"ERROR: Failed to preserve etc directory: {err}")
        return 1

    # Remove old installation
    rc, out, err = run(f"sudo rm -rf {install_dir}/splunkforwarder")
    if rc != 0:
        log(f"ERROR: Failed to remove old installation: {err}")
        return 1

    # Move new installation into place
    rc, out, err = run(f"sudo mv {tmp}/splunkforwarder {install_dir}/")
    if rc != 0:
        log(f"ERROR: Failed to move new installation: {err}")
        return 1

    # Restore preserved etc directory
    rc, out, err = run(f"sudo rm -rf {install_dir}/splunkforwarder/etc")
    if rc != 0:
        log(f"WARNING: Failed to remove new etc directory: {err}")
    
    rc, out, err = run(f"sudo mv {tmp}/etc.preserve {install_dir}/splunkforwarder/etc")
    if rc != 0:
        log(f"ERROR: Failed to restore preserved etc directory: {err}")
        return 1

    log("Installation replacement completed")

    # Set ownership and permissions
    log("Setting ownership and permissions...")
    rc, out, err = run(f"sudo chown -R {user}:{group} {install_dir}/splunkforwarder")
    if rc != 0:
        log(f"WARNING: Failed to set ownership: {err}")

    rc, out, err = run(f"sudo chmod -R 755 {install_dir}/splunkforwarder && sudo chmod 755 {install_dir}/splunkforwarder/bin/splunk")
    if rc != 0:
        log(f"WARNING: Failed to set permissions: {err}")

    # Update deployment server configuration if provided
    if deployment_server:
        log(f"Updating deployment server configuration: {deployment_server}")
        seed_dir = f"{install_dir}/splunkforwarder/etc/system/local"
        deploymentclient_conf = f"""[deployment-client]

[target-broker:deploymentServer]
targetUri = {deployment_server}"""
        
        if deployment_app:
            deploymentclient_conf += f"""

[deployment-client]
repositoryLocation = $SPLUNK_HOME/etc/{deployment_app}"""

        deploymentclient_cmd = f"""sudo -u {user} bash -c 'cat > {seed_dir}/deploymentclient.conf << "EOF"
{deploymentclient_conf}
EOF'"""
        rc, out, err = run(deploymentclient_cmd)
        if rc != 0:
            log(f"WARNING: Failed to update deployment client configuration: {err}")

    # Start Splunk UF
    log("Starting upgraded Splunk UF...")
    rc, out, err = run(f"sudo -u {user} {install_dir}/splunkforwarder/bin/splunk start --accept-license --answer-yes --no-prompt")
    if rc != 0:
        log(f"ERROR: Failed to start upgraded Splunk UF: {err}")
        return 1

    log("Upgraded Splunk UF started successfully")

    # Wait for startup
    time.sleep(5)

    # Verify new version
    log("Verifying upgrade...")
    rc, out, err = run(f"sudo -u {user} {install_dir}/splunkforwarder/bin/splunk version")
    if rc == 0:
        log(f"Upgrade verification: {out}")
    else:
        log(f"WARNING: Could not verify upgrade: {err}")

    # Check status
    rc, out, err = run(f"sudo -u {user} {install_dir}/splunkforwarder/bin/splunk status")
    log(f"Final status: {out}")

    # Cleanup
    log("Cleaning up temporary files...")
    run(f"sudo rm -rf {tmp}/splunkforwarder.tgz")
    run(f"sudo rm -rf {tmp}/splunkforwarder")

    log(f"Splunk UF upgrade to {version} completed successfully!")
    return 0

if __name__ == "__main__":
    print("=== UPGRADE UF RUNNER STARTING ===", flush=True)
    try:
        result = main()
        print(f"=== UPGRADE UF RUNNER COMPLETED WITH CODE {result} ===", flush=True)
        sys.exit(result)
    except Exception as e:
        import traceback
        print(f"FATAL ERROR: {e}", flush=True)
        print(f"Traceback: {traceback.format_exc()}", flush=True)
        sys.exit(1)