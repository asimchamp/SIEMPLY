#!/usr/bin/env python3
"""
Splunk Enterprise Upgrade Runner.
Reads env.json from the same directory and upgrades an existing Splunk Enterprise install.
"""
import json
import os
import subprocess
import sys

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(THIS_DIR, 'upgrade_runner.log')

def log(msg: str):
    with open(LOG_FILE, 'a') as lf:
        lf.write(msg.rstrip() + "\n")
    print(msg)

def run(cmd: str):
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode(), p.stderr.decode()

def main() -> int:
    env_path = os.path.join(THIS_DIR, 'env.json')
    if not os.path.exists(env_path):
        log('env.json not found')
        return 99
    with open(env_path, 'r') as f:
        env = json.load(f)

    target_version = env.get('version')
    arch = env.get('architecture', 'x86_64')
    install_dir = env.get('install_dir', '/opt')
    user = env.get('user', 'splunk')
    group = env.get('group', 'splunk')
    urls = env.get('download_urls', [])

    splunk_root = os.path.join(install_dir.rstrip('/'), 'splunk')
    splunk_bin = os.path.join(splunk_root, 'bin/splunk')

    log('[1/7] Validating existing install')
    if not os.path.exists(splunk_bin):
        log('SPLUNK_NOT_INSTALLED')
        return 2

    log('[2/7] Stopping Splunk')
    run(f"sudo -u {user} '{splunk_bin}' stop || true")

    tmp = THIS_DIR
    pkg_path = os.path.join(tmp, 'splunk_upgrade.tgz')

    log('[3/7] Ensuring prerequisites (curl/wget)')
    run("which curl >/dev/null 2>&1 || which wget >/dev/null 2>&1 || sudo apt-get update -y && sudo apt-get install -y curl || sudo yum install -y curl || true")

    log('[4/7] Downloading upgrade package')
    ok = False
    for u in urls:
        log(f'Attempting URL: {u}')
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
        return 3

    log('[5/7] Extracting upgrade package')
    rc, out, err = run(f"cd '{install_dir.rstrip('/')}' && sudo tar -xzf '{pkg_path}'")
    if rc != 0:
        log('EXTRACT_FAILED')
        if err:
            log(err)
        return 4

    log('[6/7] Fixing permissions')
    run(f"sudo chown -R {user}:{group} '{splunk_root}'")
    run(f"sudo chmod -R 755 '{splunk_root}' && sudo chmod 755 '{splunk_bin}'")

    log('[7/7] Starting Splunk')
    rc, out, err = run(f"sudo -u {user} '{splunk_bin}' start --accept-license --answer-yes --no-prompt")
    if rc != 0:
        log('START_FAILED')
        if err:
            log(err)
        return 5

    try:
        os.remove(pkg_path)
    except Exception:
        pass

    log('OK')
    return 0

if __name__ == '__main__':
    sys.exit(main())

