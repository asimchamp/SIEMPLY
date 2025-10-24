#!/usr/bin/env python3
"""
UF runner script to be uploaded to the remote host and executed under tmux.
Reads env.json from the same directory and performs the full Splunk UF install.
"""
import json
import os
import subprocess
import sys
import time

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(THIS_DIR, 'runner.log')

def log(msg: str):
    with open(LOG_FILE, 'a') as lf:
        lf.write(msg.rstrip() + "\n")
    print(msg)

def run(cmd: str) -> tuple[int, str, str]:
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode(), p.stderr.decode()

def main() -> int:
    env_path = os.path.join(THIS_DIR, 'env.json')
    # When uploaded to remote, THIS_DIR will be the remote temp dir
    if not os.path.exists(env_path):
        # Fallback: try ../env.json if script uploaded without folder structure
        alt = os.path.join(os.path.dirname(THIS_DIR), 'env.json')
        if os.path.exists(alt):
            env_path = alt
        else:
            print('env.json not found', file=sys.stderr)
            return 99

    log(f"Using env: {env_path}")
    with open(env_path, 'r') as f:
        env = json.load(f)

    version = env.get('version')
    arch = env.get('architecture', 'x86_64')
    install_dir = env.get('install_dir', '/opt')
    admin_password = env.get('admin_password')
    user = env.get('user', 'splunk')
    group = env.get('group', 'splunk')
    deployment_server = env.get('deployment_server')
    deployment_app = env.get('deployment_app')
    urls = env.get('download_urls', [])

    tmp = THIS_DIR
    os.makedirs(tmp, exist_ok=True)
    pkg_path = os.path.join(tmp, 'splunkforwarder.tgz')

    if not version or not admin_password:
        log("ERROR: Missing required parameters (version, admin_password)")
        return 1

    # Check if UF is already installed
    actual_extract_dir = install_dir
    if install_dir.endswith("/splunkforwarder"):
        log(f"Using exact install path as specified: {install_dir}")
    else:
        if actual_extract_dir.endswith("/"):
            actual_extract_dir = actual_extract_dir[:-1]
        log(f"Will extract to parent directory: {actual_extract_dir}")

    rc, out, err = run(f"test -d {actual_extract_dir}/splunkforwarder && echo 'exists' || echo 'not exists'")
    if "exists" in out:
        log(f"WARNING: Splunk UF is already installed at {actual_extract_dir}/splunkforwarder")
        log(f"Checking if it's running and stopping it...")
        # Stop existing UF if running
        run(f"sudo -u {user} {actual_extract_dir}/splunkforwarder/bin/splunk stop 2>/dev/null || true")
        log(f"Continuing with installation (will overwrite existing installation)")
        # Don't return error, continue with installation

    # Create installation directory
    log(f"Creating installation directory: {install_dir}")
    rc, out, err = run(f"sudo mkdir -p {install_dir}")
    if rc != 0:
        log(f"ERROR: Failed to create installation directory: {err}")
        return 1

    # Download Splunk UF
    log(f"Starting Splunk UF {version} download...")
    download_success = False
    
    # Check available tools
    rc_curl, _, _ = run("which curl")
    rc_wget, _, _ = run("which wget")
    has_curl = rc_curl == 0
    has_wget = rc_wget == 0

    if not has_curl and not has_wget:
        log("ERROR: Neither curl nor wget is available")
        return 1

    # Try each download URL
    for i, url in enumerate(urls):
        log(f"Attempting download from URL #{i+1}: {url}")
        
        if has_curl:
            rc, out, err = run(f"cd {tmp} && sudo curl -L -o splunkforwarder.tgz '{url}' 2>&1")
            if rc == 0:
                download_success = True
                log(f"Successfully downloaded with curl from URL #{i+1}")
                break
            else:
                log(f"Curl failed for URL #{i+1}: {err}")
        
        if not download_success and has_wget:
            rc, out, err = run(f"cd {tmp} && sudo wget -v -O splunkforwarder.tgz '{url}' 2>&1")
            if rc == 0:
                download_success = True
                log(f"Successfully downloaded with wget from URL #{i+1}")
                break
            else:
                log(f"Wget failed for URL #{i+1}: {err}")

    if not download_success:
        log("ERROR: Failed to download Splunk UF from any URL")
        return 1

    # Verify download
    rc, out, err = run(f"ls -la {pkg_path}")
    if rc != 0:
        log(f"ERROR: Downloaded package not found: {err}")
        return 1

    log(f"Download verified: {out.strip()}")

    # Extract Splunk UF
    log(f"Extracting Splunk UF to {actual_extract_dir}...")
    rc, out, err = run(f"cd {actual_extract_dir} && sudo tar -xzf {pkg_path}")
    if rc != 0:
        log(f"ERROR: Failed to extract Splunk UF: {err}")
        return 1

    log("Extraction completed successfully")

    # Create user and group
    log(f"Creating user/group: {user}/{group}")
    run(f"id -u {user} &>/dev/null || sudo useradd -m -s /bin/bash {user}")
    run(f"getent group {group} || sudo groupadd {group}")
    if user != group:
        run(f"sudo usermod -a -G {group} {user}")

    # Set ownership and permissions
    log("Setting ownership and permissions...")
    rc, out, err = run(f"sudo chown -R {user}:{group} {actual_extract_dir}/splunkforwarder")
    if rc != 0:
        log(f"WARNING: Failed to set ownership: {err}")

    rc, out, err = run(f"sudo chmod -R 755 {actual_extract_dir}/splunkforwarder && sudo chmod 755 {actual_extract_dir}/splunkforwarder/bin/splunk")
    if rc != 0:
        log(f"WARNING: Failed to set permissions: {err}")

    # Create user-seed.conf
    log("Creating user-seed.conf...")
    rc, out, err = run(f"sudo -u {user} mkdir -p {actual_extract_dir}/splunkforwarder/etc/system/local")
    seed_dir = f"{actual_extract_dir}/splunkforwarder/etc/system/local"
    seed_content = f"""[user_info]
USERNAME = admin
PASSWORD = {admin_password}"""

    seed_cmd = f"""sudo -u {user} bash -c 'cat > {seed_dir}/user-seed.conf << "EOF"
{seed_content}
EOF'"""
    rc, out, err = run(seed_cmd)
    if rc != 0:
        # Fallback as root
        log("Fallback: creating user-seed.conf as root...")
        fallback_cmd = f"""sudo bash -c 'cat > {seed_dir}/user-seed.conf << "EOF"
{seed_content}
EOF'"""
        rc2, out2, err2 = run(fallback_cmd)
        if rc2 != 0:
            log(f"ERROR: Failed to create user-seed.conf: {err2}")
            return 1

    # Configure deployment server if provided
    if deployment_server:
        log(f"Configuring deployment server: {deployment_server}")
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
            log(f"WARNING: Failed to configure deployment client: {err}")

    # Start Splunk UF for first time (accepts license and creates initial config)
    log("Starting Splunk UF for first time...")
    rc, out, err = run(f"sudo -u {user} {actual_extract_dir}/splunkforwarder/bin/splunk start --accept-license --answer-yes --no-prompt")
    if rc != 0:
        log(f"ERROR: Failed to start Splunk UF: {err}")
        return 1

    log("Splunk UF started successfully")

    # Wait a moment for startup
    time.sleep(5)

    # Enable boot-start
    log("Enabling boot-start...")
    rc, out, err = run(f"sudo {actual_extract_dir}/splunkforwarder/bin/splunk enable boot-start -user {user}")
    if rc != 0:
        log(f"WARNING: Failed to enable boot-start: {err}")

    # Check status
    rc, out, err = run(f"sudo -u {user} {actual_extract_dir}/splunkforwarder/bin/splunk status")
    log(f"Final status: {out}")

    # Cleanup
    log("Cleaning up temporary files...")
    run(f"sudo rm -rf {tmp}/splunkforwarder.tgz")

    log(f"Splunk UF {version} installation completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())