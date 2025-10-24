#!/usr/bin/env python3
"""
Enterprise runner script to be uploaded to the remote host and executed under tmux.
Reads env.json from the same directory and performs the full Splunk Enterprise install.
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
    urls = env.get('download_urls', [])

    tmp = THIS_DIR
    os.makedirs(tmp, exist_ok=True)
    pkg_path = os.path.join(tmp, 'splunk.tgz')

    # Ensure prereqs
    log("[1/8] Ensuring prerequisites (curl/wget)")
    run("which curl >/dev/null 2>&1 || which wget >/dev/null 2>&1 || sudo apt-get update -y && sudo apt-get install -y curl || sudo yum install -y curl || true")

    # Download
    log("[2/8] Downloading Splunk package")
    ok = False
    for u in urls:
        log(f"Attempting URL: {u}")
        rc, out, err = run(f"curl -L -o '{pkg_path}' '{u}' 2>&1 || wget -O '{pkg_path}' '{u}' 2>&1")
        if out:
            log(out)
        if err:
            log(err)
        if rc == 0 and os.path.exists(pkg_path) and os.path.getsize(pkg_path) > 0:
            ok = True
            break
    if not ok:
        log('DOWNLOAD_FAILED')
        return 1

    # Prepare install dir
    log("[3/8] Preparing install directory")
    run(f"sudo mkdir -p '{install_dir}'")

    # Extract
    log("[4/8] Extracting package")
    rc, out, err = run(f"cd '{install_dir.rstrip('/')}' && sudo tar -xzf '{pkg_path}'")
    if rc != 0:
        log('EXTRACT_FAILED')
        if err:
            log(err)
        return 2

    # Users/groups
    log("[5/8] Creating user/group and fixing permissions")
    run(f"id -u {user} >/dev/null 2>&1 || sudo useradd -m -s /bin/bash {user}")
    run(f"getent group {group} >/dev/null 2>&1 || sudo groupadd {group}")
    if user != group:
        run(f"sudo usermod -a -G {group} {user}")

    # Permissions
    splunk_root = os.path.join(install_dir.rstrip('/'), 'splunk')
    run(f"sudo chown -R {user}:{group} '{splunk_root}'")
    run(f"sudo chmod -R 755 '{splunk_root}' && sudo chmod 755 '{splunk_root}/bin/splunk'")

    # Seed admin
    seed_dir = os.path.join(splunk_root, 'etc/system/local')
    os.makedirs(seed_dir, exist_ok=True)
    log("[6/8] Creating user-seed.conf")
    with open(os.path.join(seed_dir, 'user-seed.conf'), 'w') as f:
        f.write('[user_info]\nUSERNAME = admin\nPASSWORD = ' + (admin_password or 'changeme') + '\n')
    run(f"sudo chown {user}:{group} '{os.path.join(seed_dir, 'user-seed.conf')}' && sudo chmod 600 '{os.path.join(seed_dir, 'user-seed.conf')}'")

    # Start splunk
    splunk_bin = os.path.join(splunk_root, 'bin/splunk')
    log("[7/8] Starting Splunk")
    rc, out, err = run(f"sudo -u {user} '{splunk_bin}' start --accept-license --no-prompt --answer-yes")
    if rc != 0:
        log('START_FAILED')
        if err:
            log(err)
        return 3

    # Enable boot
    log("[8/8] Enabling boot-start")
    run(f"sudo '{splunk_bin}' enable boot-start -user {user} --accept-license --no-prompt --answer-yes")

    # Cleanup artifact
    try:
        os.remove(pkg_path)
    except Exception:
        pass

    log('OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())

