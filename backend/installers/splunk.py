"""
Splunk Enterprise Installer
Installs Splunk Enterprise on hosts via SSH
"""
import asyncio
import logging
from typing import Dict, Any, Optional
import os

from backend.automation.ssh_client import get_ssh_client
from backend.models import Host
from backend.automation.splunk.splunk_installer import (
    get_all_download_urls,
    test_connectivity_to_splunk,
    create_download_script,
)
from backend.automation.ssh_client import AsyncSSHClient
from backend.models import Job

logger = logging.getLogger(__name__)


async def _ensure_tmux_installed(ssh) -> None:
    """Ensure tmux is installed on the remote host (best-effort)."""
    check_tmux = await ssh.run("which tmux")
    if check_tmux.returncode == 0:
        return

    # Detect package manager and install tmux
    # Avoid failing the whole install if tmux cannot be installed
    install_cmds = [
        "sudo apt-get update -y && sudo apt-get install -y tmux",
        "sudo yum install -y tmux",
        "sudo dnf install -y tmux",
        "sudo zypper install -y tmux",
        "sudo apk add --no-cache tmux",
    ]
    
    # Try RedHat 9 specific approach first
    try:
        # Check if it's RedHat 9
        os_check = await ssh.run("cat /etc/redhat-release")
        if os_check.returncode == 0 and "Red Hat Enterprise Linux release 9" in os_check.stdout:
            logger.info("Detected RedHat 9, trying alternative tmux installation methods")
            
            # Try to enable EPEL repository
            epel_result = await ssh.run("sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm")
            if epel_result.returncode == 0:
                logger.info("EPEL repository enabled successfully")
                # Try to install tmux from EPEL
                tmux_result = await ssh.run("sudo dnf install -y tmux")
                if tmux_result.returncode == 0:
                    logger.info("Installed tmux from EPEL repository")
                    return
                else:
                    logger.warning("Failed to install tmux from EPEL: %s", tmux_result.stderr)
            
            # Try to compile tmux from source if package installation fails
            logger.info("Attempting to compile tmux from source")
            compile_cmds = [
                "sudo dnf install -y gcc make ncurses-devel libevent-devel",
                "cd /tmp && curl -L -o tmux-3.3a.tar.gz https://github.com/tmux/tmux/releases/download/3.3a/tmux-3.3a.tar.gz",
                "cd /tmp && tar -xzf tmux-3.3a.tar.gz",
                "cd /tmp/tmux-3.3a && ./configure --prefix=/usr/local",
                "cd /tmp/tmux-3.3a && make && sudo make install",
                "sudo ln -sf /usr/local/bin/tmux /usr/bin/tmux"
            ]
            
            for cmd in compile_cmds:
                result = await ssh.run(cmd)
                if result.returncode != 0:
                    logger.warning("Compilation step failed: %s - %s", cmd, result.stderr)
                    break
            else:
                # Check if tmux was successfully compiled
                check_compiled = await ssh.run("which tmux")
                if check_compiled.returncode == 0:
                    logger.info("Successfully compiled and installed tmux from source")
                    return
    except Exception as e:
        logger.warning("RedHat 9 specific tmux installation failed: %s", str(e))
    
    # Fall back to standard package manager approach
    for cmd in install_cmds:
        result = await ssh.run(cmd)
        if result.returncode == 0:
            logger.info("Installed tmux using: %s", cmd)
            break
    else:
        logger.warning("Unable to install tmux on remote host; continuing without it")


async def install_splunk_enterprise(host: Host, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Install Splunk Enterprise on a host via SSH
    
    Args:
        host: The host object containing connection information
        params: Dictionary of installation parameters
            - version: Splunk Enterprise version to install
            - architecture: System architecture (default: x86_64)
            - install_dir: Installation directory (default: /opt)
            - admin_password: Admin password for Splunk Web
            - user: User to run Splunk as (default: splunk)
            - group: Group to run Splunk as (default: splunk)
            - is_dry_run: If True, only simulate the installation
            - cluster_name: Name of the cluster for configuration files
            - cluster_role: Role of the component in the cluster
        
    Returns:
        Dictionary with installation results
    """
    # Extract parameters with defaults
    version: Optional[str] = params.get("version")
    architecture: str = params.get("architecture", "x86_64")
    install_dir: str = params.get("install_dir", "/opt")
    admin_password: Optional[str] = params.get("admin_password")
    user: str = params.get("user", "splunk")
    group: str = params.get("group", "splunk")
    is_dry_run: bool = params.get("is_dry_run", False)
    cluster_name: Optional[str] = params.get("cluster_name")
    cluster_role: Optional[str] = params.get("cluster_role")

    # Validate required parameters
    if not version:
        return {"success": False, "message": "Splunk version is required"}
    if not admin_password:
        return {"success": False, "message": "Admin password is required"}

    # Get all possible download URLs for the specified version and architecture
    download_urls = get_all_download_urls(version, architecture, "splunk_enterprise")
    if not download_urls:
        return {
            "success": False,
            "message": f"No download URL available for Splunk Enterprise version {version} architecture {architecture}",
        }

    logger.info(
        "Primary download URL for Splunk Enterprise %s (%s): %s",
        version,
        architecture,
        download_urls[0],
    )
    if len(download_urls) > 1:
        logger.info("Found %d potential download URLs to try", len(download_urls))

    # Connect to the host via SSH
    async with get_ssh_client(host) as ssh:
        if not ssh:
            return {"success": False, "message": "Could not establish SSH connection"}

        logger.info("Connected to %s for Splunk Enterprise installation", host.hostname)

        # Copy cluster configuration files if cluster information is provided
        if cluster_name and cluster_role:
            try:
                from backend.automation.cluster_file_manager import ClusterFileManager
                
                cluster_manager = ClusterFileManager()
                if cluster_manager.validate_cluster_exists(cluster_name):
                    logger.info(f"Copying cluster configuration files for {cluster_role} from cluster {cluster_name}")
                    
                    # Map cluster role to component type
                    component_type = f"splunk_{cluster_role}"
                    
                    # Use the new direct copy method that avoids EOF and copies entire directory structure
                    logger.info(f"Using direct directory copy method for {component_type} configuration")
                    copy_result = await cluster_manager.copy_component_configs_direct(
                        ssh, cluster_name, component_type, f"{install_dir}/splunk/etc/apps", host.ip_address
                    )
                    
                    if copy_result["success"]:
                        logger.info(f"Successfully copied {copy_result['files_copied']} configuration files using direct method")
                        if copy_result.get('method') and 'direct' in copy_result.get('method', ''):
                            logger.info(f"Configuration copied using: {copy_result.get('method', 'unknown')}")
                            if copy_result.get('app_name'):
                                logger.info(f"Configuration copied to app: {copy_result.get('app_name', 'unknown')}")
                                logger.info(f"Configuration app path: {copy_result.get('app_path', 'unknown')}")
                        else:
                            logger.info(f"Configuration copied using {copy_result.get('method', 'unknown')} method")
                    else:
                        logger.warning(f"Direct copy method failed: {copy_result['message']}")
                        if copy_result.get('errors'):
                            for error in copy_result['errors']:
                                logger.warning(f"Copy error: {error}")
                        
                        # Fall back to legacy method if direct copy fails
                        logger.info("Falling back to legacy copy method")
                        fallback_result = await cluster_manager.copy_component_configs_to_host(
                            ssh, cluster_name, component_type, f"{install_dir}/splunk/etc/apps"
                        )
                        if fallback_result["success"]:
                            logger.info(f"Legacy method successful: {fallback_result['files_copied']} files copied")
                        else:
                            logger.warning(f"Legacy method also failed: {fallback_result['message']}")
                else:
                    logger.warning(f"Cluster {cluster_name} not found, skipping configuration file copy")
            except Exception as e:
                logger.warning(f"Failed to copy cluster configuration files: {str(e)}")
                # Continue with installation even if config copy fails
        else:
            logger.info("No cluster information provided, skipping configuration file copy")

        # Best-effort: ensure tmux on target host and stage a remote runner
        try:
            await _ensure_tmux_installed(ssh)
            # Build env and upload alongside enterprise_runner.py
            import json
            env_data = {
                "version": version,
                "architecture": architecture,
                "install_dir": install_dir,
                "admin_password": admin_password,
                "user": user,
                "group": group,
                "download_urls": download_urls,
            }
            remote_tmp_dir = "/tmp/siemply_splunk"
            await ssh.run(f"sudo mkdir -p {remote_tmp_dir}")
            await ssh.upload_bytes(f"{remote_tmp_dir}/env.json", json.dumps(env_data, indent=2).encode("utf-8"), 0o644)

            # Read local runner template and upload it
            try:
                local_runner_path = os.path.join(os.path.dirname(__file__), "..", "automation", "splunk", "enterprise_runner.py")
                local_runner_path = os.path.abspath(local_runner_path)
                with open(local_runner_path, "rb") as f:
                    runner_bytes = f.read()
                await ssh.upload_bytes(f"{remote_tmp_dir}/splunk_enterprise.py", runner_bytes, 0o755)
                # Kick off tmux session to run the script and clean up after
                session_name = f"siemply_ent_{os.getpid()}"
                rc_dir = "/tmp/siemply_sessions"
                rc_path = f"{rc_dir}/{session_name}.rc"
                await ssh.run(f"sudo mkdir -p {rc_dir}")
                # Pipe both stdout and stderr to the runner.log file in the remote tmp dir
                run_cmd = (
                    f"tmux new-session -d -s {session_name} \""
                    f"python3 {remote_tmp_dir}/splunk_enterprise.py >> {remote_tmp_dir}/runner.log 2>&1; rc=$?; "
                    f"echo $rc | sudo tee {rc_path} >/dev/null; exit $rc\""
                )
                start_tmux = await ssh.run(run_cmd)
                if start_tmux.returncode == 0:
                    logger.info("Started tmux session: %s", session_name)
                    # Return immediately; monitoring will complete the job
                    return {
                        "success": True,
                        "started_in_tmux": True,
                        "tmux_session": session_name,
                        "rc_path": rc_path,
                        "status_note": "Started Splunk Enterprise install in tmux",
                        "actual_status": "running",
                    }
                else:
                    logger.warning("Failed to start tmux session; inline fallback will be used")
            except Exception as e:
                logger.warning("Failed to stage tmux runner: %s", str(e))
        except Exception as tmux_err:
            logger.warning("tmux staging step failed (ignored): %s", str(tmux_err))

        # Dry run support
        if is_dry_run:
            return {
                "success": True,
                "message": f"Dry run - would have installed Splunk Enterprise {version} ({architecture})",
                "is_dry_run": True,
                "version": version,
                "architecture": architecture,
                "install_dir": install_dir,
            }

        try:
            # Prepare installation directory
            result = await ssh.run(f"sudo mkdir -p {install_dir}")
            if result.returncode != 0:
                return {"success": False, "message": f"Failed to create installation directory: {result.stderr}"}

            # Check if already installed
            check_cmd = f"test -d {install_dir}/splunk && echo 'exists' || echo 'not exists'"
            check_result = await ssh.run(check_cmd)
            if check_result.stdout.strip() == "exists":
                return {
                    "success": False,
                    "message": f"Splunk Enterprise is already installed at {install_dir}/splunk",
                }

            # Create temp directory for legacy inline flow (fallback only)
            await ssh.run("sudo mkdir -p /tmp/splunk_install")

            # Determine extract parent directory
            actual_extract_dir = install_dir[:-1] if install_dir.endswith("/") else install_dir
            if install_dir.endswith("/splunk"):
                logger.info("Using exact install path as specified: %s", install_dir)

            # Ensure download tool exists
            curl_check = await ssh.run("which curl")
            has_curl = curl_check.returncode == 0
            wget_check = await ssh.run("which wget")
            has_wget = wget_check.returncode == 0
            if not has_curl and not has_wget:
                return {
                    "success": False,
                    "message": "Neither curl nor wget is available on the target host. Please install one of these tools.",
                }

            # Download with retries across URLs; prefer running in tmux
            download_success = False
            errors: list[str] = []
            has_tmux = (await ssh.run("which tmux")).returncode == 0
            for url_index, url in enumerate(download_urls):
                session_name = f"siemply_dl_ent_{os.getpid()}_{url_index}"
                if has_curl and not download_success:
                    base_cmd = f"cd /tmp/splunk_install && sudo curl -L -o splunk.tgz '{url}' 2>&1"
                    if has_tmux:
                        logger.info("Attempting download with curl in tmux from URL #%d: %s", url_index + 1, url)
                        rc_file = f"/tmp/splunk_install/{session_name}.rc"
                        wrapped = f"bash -lc '{base_cmd}; echo $? | sudo tee {rc_file} >/dev/null'"
                        start = await ssh.run(f"tmux new-session -d -s {session_name} \"{wrapped}\"")
                        if start.returncode == 0:
                            # Poll
                            elapsed = 0
                            while elapsed < 1800:
                                check = await ssh.run("test -s /tmp/splunk_install/splunk.tgz && echo ok || echo no")
                                if "ok" in check.stdout:
                                    download_success = True
                                    break
                                rc = await ssh.run(f"test -f {rc_file} && cat {rc_file} || echo none")
                                if rc.stdout.strip().isdigit():
                                    break
                                await asyncio.sleep(5)
                                elapsed += 5
                    else:
                        logger.info("Attempting download with curl (no tmux) from URL #%d: %s", url_index + 1, url)
                        dl = await ssh.run(base_cmd)
                        download_success = dl.returncode == 0
                    if download_success:
                        break
                    errors.append(f"curl error (URL #{url_index+1})")

                if has_wget and not download_success:
                    base_cmd = f"cd /tmp/splunk_install && sudo wget -O splunk.tgz '{url}' 2>&1"
                    if has_tmux:
                        logger.info("Attempting download with wget in tmux from URL #%d: %s", url_index + 1, url)
                        rc_file = f"/tmp/splunk_install/{session_name}.rc"
                        wrapped = f"bash -lc '{base_cmd}; echo $? | sudo tee {rc_file} >/dev/null'"
                        start = await ssh.run(f"tmux new-session -d -s {session_name} \"{wrapped}\"")
                        if start.returncode == 0:
                            elapsed = 0
                            while elapsed < 1800:
                                check = await ssh.run("test -s /tmp/splunk_install/splunk.tgz && echo ok || echo no")
                                if "ok" in check.stdout:
                                    download_success = True
                                    break
                                rc = await ssh.run(f"test -f {rc_file} && cat {rc_file} || echo none")
                                if rc.stdout.strip().isdigit():
                                    break
                                await asyncio.sleep(5)
                                elapsed += 5
                    else:
                        logger.info("Attempting download with wget (no tmux) from URL #%d: %s", url_index + 1, url)
                        dl = await ssh.run(base_cmd)
                        download_success = dl.returncode == 0
                    if download_success:
                        break
                    errors.append(f"wget error (URL #{url_index+1})")

            if not download_success:
                # Try custom script fallback
                can_connect, connection_output = await test_connectivity_to_splunk(ssh)
                logger.info("Connectivity to download.splunk.com: %s; %s", can_connect, connection_output)
                for url_index, url in enumerate(download_urls):
                    script_path = await create_download_script(ssh, url, "/tmp/splunk_install/splunk.tgz")
                    if script_path:
                        res = await ssh.run(f"cd /tmp/splunk_install && sudo bash {script_path}")
                        check = await ssh.run("test -s /tmp/splunk_install/splunk.tgz && echo success || echo failed")
                        if "success" in check.stdout:
                            download_success = True
                            break
                        errors.append(f"custom script failed (URL #{url_index+1})")

            if not download_success:
                net_check = await ssh.run("ping -c 1 download.splunk.com")
                if net_check.returncode != 0:
                    return {
                        "success": False,
                        "message": "Cannot reach download.splunk.com. Please check network connectivity.\n" + ", ".join(errors),
                    }
                return {"success": False, "message": "Failed to download Splunk Enterprise. " + ", ".join(errors)}

            # Verify download exists
            verify = await ssh.run("ls -la /tmp/splunk_install/splunk.tgz")
            if verify.returncode != 0 or "No such file" in verify.stderr:
                return {"success": False, "message": "Downloaded Splunk package not found after download"}

            # Extract Splunk Enterprise
            logger.info("Extracting Splunk Enterprise on %s", host.hostname)
            extract = await ssh.run(f"cd {actual_extract_dir} && sudo tar -xzf /tmp/splunk_install/splunk.tgz")
            if extract.returncode != 0:
                return {"success": False, "message": f"Failed to extract Splunk Enterprise: {extract.stderr}"}

            # Create user and group
            await ssh.run(f"id -u {user} &>/dev/null || sudo useradd -m -s /bin/bash {user}")
            await ssh.run(f"getent group {group} || sudo groupadd {group}")
            if user != group:
                await ssh.run(f"sudo usermod -a -G {group} {user}")

            # Set ownership and permissions
            await ssh.run(f"sudo chown -R {user}:{group} {actual_extract_dir}/splunk")
            await ssh.run(f"sudo chmod -R 755 {actual_extract_dir}/splunk && sudo chmod 755 {actual_extract_dir}/splunk/bin/splunk")

            # Ensure etc paths exist and create user-seed.conf
            await ssh.run(f"sudo -u {user} mkdir -p {actual_extract_dir}/splunk/etc/system/local")
            seed_dir = f"{actual_extract_dir}/splunk/etc/system/local"
            seed_content = f"""[user_info]
USERNAME = admin
PASSWORD = {admin_password}"""
            seed_cmd = (
                "sudo -u {user} bash -c 'cat > {seed_dir}/user-seed.conf << \"EOF\"\n{seed_content}\nEOF'"
                .format(user=user, seed_dir=seed_dir, seed_content=seed_content)
            )
            seed_res = await ssh.run(seed_cmd)
            if seed_res.returncode != 0:
                # Fallback as root
                fb = await ssh.run(
                    f"sudo bash -c 'cat > {seed_dir}/user-seed.conf << \"EOF\"\n{seed_content}\nEOF'"
                )
                if fb.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Failed to create user-seed.conf: {seed_res.stderr}; fallback: {fb.stderr}",
                    }
                # Fix ownership and permissions
                await ssh.run(
                    f"sudo chown {user}:{group} {seed_dir}/user-seed.conf && sudo chmod 600 {seed_dir}/user-seed.conf"
                )

            # Stop any existing Splunk processes and clear locks
            await ssh.run(f"sudo -u {user} {actual_extract_dir}/splunk/bin/splunk stop 2>/dev/null || true")
            await ssh.run("sudo pkill -f splunk 2>/dev/null || true")
            await asyncio.sleep(3)
            await ssh.run(f"sudo rm -f {actual_extract_dir}/splunk/var/run/splunk/splunkd.pid 2>/dev/null || true")
            await ssh.run(f"sudo rm -f {actual_extract_dir}/splunk/var/run/splunk/splunkd.lock 2>/dev/null || true")

            # Start Splunk
            logger.info("Starting Splunk Enterprise as user %s...", user)
            start_cmd = f"sudo -u {user} {actual_extract_dir}/splunk/bin/splunk start --accept-license --no-prompt --answer-yes"
            start_res = await ssh.run(start_cmd)
            if start_res.returncode != 0:
                # Try fix perms and retry
                await ssh.run(
                    f"""sudo chown -R {user}:{group} {actual_extract_dir}/splunk && \
                    sudo chmod -R 755 {actual_extract_dir}/splunk && \
                    sudo chmod 755 {actual_extract_dir}/splunk/bin/splunk"""
                )
                await ssh.run(f"sudo rm -f {actual_extract_dir}/splunk/var/run/splunk/splunkd.pid 2>/dev/null || true")
                await ssh.run(f"sudo rm -f {actual_extract_dir}/splunk/var/run/splunk/splunkd.lock 2>/dev/null || true")
                start_res = await ssh.run(start_cmd)
                if start_res.returncode != 0:
                    log_tail = await ssh.run(
                        f"sudo tail -20 {actual_extract_dir}/splunk/var/log/splunk/splunkd.log 2>/dev/null || echo 'No log file found'"
                    )
                    logger.error("Splunk start failed: %s", start_res.stderr)
                    logger.error("Splunk logs: %s", log_tail.stdout)
                    return {"success": False, "message": f"Failed to start Splunk: {start_res.stderr}"}

            await asyncio.sleep(5)
            status_res = await ssh.run(f"sudo -u {user} {actual_extract_dir}/splunk/bin/splunk status")
            if "splunkd is running" not in status_res.stdout:
                log_tail = await ssh.run(
                    f"sudo tail -20 {actual_extract_dir}/splunk/var/log/splunk/splunkd.log 2>/dev/null || echo 'No log file found'"
                )
                logger.error("Splunk failed to start properly; logs: %s", log_tail.stdout)
                return {"success": False, "message": "Splunk failed to start properly. Check logs for details."}

            # Enable boot-start
            boot_cmd = f"sudo {actual_extract_dir}/splunk/bin/splunk enable boot-start -user {user} --accept-license --no-prompt --answer-yes"
            await ssh.run(boot_cmd)

            # Enable systemd service if present
            systemd_check = await ssh.run("test -f /etc/systemd/system/Splunkd.service && echo 'exists' || echo 'not exists'")
            if "exists" in systemd_check.stdout:
                await ssh.run("sudo systemctl daemon-reload")
                await ssh.run("sudo systemctl enable Splunkd.service")

            # Final ownership pass
            await ssh.run(f"sudo chown -R {user}:{group} {actual_extract_dir}/splunk")

            # Cleanup
            await ssh.run("sudo rm -rf /tmp/splunk_install")

            return {
                "success": True,
                "message": f"Successfully installed Splunk Enterprise {version} ({architecture}) on {host.hostname}",
                "version": version,
                "architecture": architecture,
                "install_dir": f"{actual_extract_dir}/splunk",
                "user": user,
            }

        except Exception as e:
            logger.error("Error installing Splunk Enterprise on %s: %s", host.hostname, str(e))
            return {"success": False, "message": f"Installation error: {str(e)}"}


async def install_splunk_uf_tmux(host: Host, params: Dict[str, Any], job: Job) -> Dict[str, Any]:
    """Start a Splunk UF installation under tmux using the UF runner."""
    logger.info("Starting Splunk UF installation for host %s", host.hostname)
    
    version: Optional[str] = params.get("version")
    architecture: str = params.get("architecture", "x86_64")
    install_dir: str = params.get("install_dir", "/opt")
    admin_password: Optional[str] = params.get("admin_password")
    user: str = params.get("user", "splunk")
    group: str = params.get("group", "splunk")
    deployment_server = params.get("deployment_server")
    deployment_app = params.get("deployment_app")
    
    if not version:
        return {"success": False, "message": "Splunk version is required"}
    if not admin_password:
        return {"success": False, "message": "Admin password is required"}
        
    download_urls = get_all_download_urls(version, architecture, "splunk_uf")
    if not download_urls:
        return {"success": False, "message": f"No download URL for UF version {version} arch {architecture}"}

    async with get_ssh_client(host) as ssh:
        if not ssh:
            return {"success": False, "message": "Could not establish SSH connection"}
        try:
            await _ensure_tmux_installed(ssh)
            import json
            env_data = {
                "version": version,
                "architecture": architecture,
                "install_dir": install_dir,
                "admin_password": admin_password,
                "user": user,
                "group": group,
                "deployment_server": deployment_server,
                "deployment_app": deployment_app,
                "download_urls": download_urls,
            }
            
            # Create remote directory first
            remote_dir = "/tmp/siemply_splunk_uf"
            await ssh.run(f"sudo mkdir -p {remote_dir}")
            await ssh.run(f"sudo chmod 755 {remote_dir}")

            # Create env.json locally and then upload it
            env_json_content = json.dumps(env_data, indent=2)
            local_env_path = f"/tmp/{job.job_id}_env.json"
            with open(local_env_path, "w") as f:
                f.write(env_json_content)

            logger.info("Uploading environment configuration from local file")
            remote_env_path = f"{remote_dir}/env.json"
            upload_success = await ssh.upload_file(local_env_path, remote_env_path)
            
            os.remove(local_env_path) # Clean up local temp file

            if not upload_success:
                return {"success": False, "message": "Failed to upload environment configuration file"}
            
            await ssh.run(f"sudo chmod 644 {remote_env_path}")
            
            # Find and upload the runner script
            runner_local_path = os.path.join(os.path.dirname(__file__), "..", "automation", "splunk", "uf_runner.py")
            runner_local_path = os.path.abspath(runner_local_path)
            logger.info(f"Resolved local runner path: {runner_local_path}")
            
            if not os.path.exists(runner_local_path):
                return {"success": False, "message": f"UF runner script not found at {runner_local_path}"}
            
            remote_runner_path = f"{remote_dir}/uf_runner.py"
            await ssh.upload_file(runner_local_path, remote_runner_path)
            await ssh.run(f"chmod +x {remote_runner_path}")
            
            # Generate unique session name
            import random
            session_id = random.randint(100000, 999999)
            session_name = f"siemply_uf_{session_id}"
            
            # Start tmux session with the runner
            logger.info(f"Starting tmux session: {session_name}")
            log_file_path = f"{remote_dir}/runner.log"
            rc_path = f"/tmp/siemply_sessions/{session_name}.rc"
            tmux_cmd = f'tmux new-session -d -s {session_name} "python3 {remote_runner_path} >> {log_file_path} 2>&1; rc=$?; echo $rc | sudo tee {rc_path} >/dev/null; exit $rc"'
            
            # Create sessions directory
            await ssh.run("sudo mkdir -p /tmp/siemply_sessions")
            
            result = await ssh.run(tmux_cmd)
            if result.returncode != 0:
                return {"success": False, "message": f"Failed to start tmux session: {result.stderr}"}
            
            logger.info(f"Started tmux session: {session_name}")
            
            return {
                "success": True,
                "message": f"Splunk UF installation started in background session: {session_name}",
                "session_name": session_name,
                "version": version,
                "architecture": architecture,
            }
            
        except Exception as e:
            logger.error(f"Error starting UF installation on {host.hostname}: {str(e)}")
            return {"success": False, "message": f"Installation error: {str(e)}"}


async def upgrade_splunk_uf_tmux(host: Host, params: Dict[str, Any], job: Job) -> Dict[str, Any]:
    """Start a Splunk UF upgrade under tmux using the UF upgrade runner."""
    logger.info("Starting Splunk UF upgrade for host %s", host.hostname)
    
    version: Optional[str] = params.get("version")
    architecture: str = params.get("architecture", "x86_64")
    install_dir: str = params.get("install_dir", "/opt")
    admin_password: Optional[str] = params.get("admin_password")
    user: str = params.get("user", "splunk")
    group: str = params.get("group", "splunk")
    deployment_server = params.get("deployment_server")
    deployment_app = params.get("deployment_app")
    
    if not version:
        return {"success": False, "message": "Target version is required"}
    if not admin_password:
        return {"success": False, "message": "Admin password is required"}
        
    # Get single download URL for upgrade (not multiple URLs like install)
    from backend.automation.splunk.splunk_installer import get_package_download_url
    download_url = get_package_download_url(version, architecture, "splunk_uf")
    logger.info(f"Generated download URL for UF {version} {architecture}: {download_url}")
    if not download_url:
        logger.error(f"No download URL found for UF version {version} arch {architecture}")
        return {"success": False, "message": f"No download URL for UF version {version} arch {architecture}"}

    async with get_ssh_client(host) as ssh:
        if not ssh:
            return {"success": False, "message": "Could not establish SSH connection"}
        try:
            await _ensure_tmux_installed(ssh)
            import json
            env_data = {
                "version": version,
                "architecture": architecture,
                "install_dir": install_dir,
                "admin_password": admin_password,
                "user": user,
                "group": group,
                "deployment_server": deployment_server,
                "deployment_app": deployment_app,
                "download_url": download_url,
            }
            
            # Create remote directory first
            remote_dir = "/tmp/siemply_splunk_uf_upgrade"
            await ssh.run(f"sudo mkdir -p {remote_dir}")
            await ssh.run(f"sudo chmod 755 {remote_dir}")

            # Upload env.json directly using upload_bytes (more reliable than file upload)
            env_json_content = json.dumps(env_data, indent=2)
            remote_env_path = f"{remote_dir}/env.json"
            logger.info("Uploading environment configuration using upload_bytes")
            await ssh.upload_bytes(remote_env_path, env_json_content.encode("utf-8"), 0o644)
            
            await ssh.run(f"sudo chmod 644 {remote_env_path}")
            
            # Find and upload the upgrade runner script
            runner_local_path = os.path.join(os.path.dirname(__file__), "..", "automation", "splunk", "upgrade_uf_runner.py")
            runner_local_path = os.path.abspath(runner_local_path)
            logger.info(f"Resolved local runner path: {runner_local_path}")
            
            if not os.path.exists(runner_local_path):
                return {"success": False, "message": f"UF upgrade runner script not found at {runner_local_path}"}
            
            # Upload runner script using upload_bytes (more reliable)
            with open(runner_local_path, "rb") as f:
                runner_bytes = f.read()
            remote_runner_path = f"{remote_dir}/upgrade_uf_runner.py"
            logger.info("Uploading upgrade runner script using upload_bytes")
            await ssh.upload_bytes(remote_runner_path, runner_bytes, 0o755)
            
            # Generate unique session name
            import random
            session_id = random.randint(100000, 999999)
            session_name = f"siemply_uf_upgrade_{session_id}"
            
            # Start tmux session with the upgrade runner
            logger.info(f"Starting tmux session: {session_name}")
            log_file_path = f"{remote_dir}/upgrade_runner.log"
            rc_path = f"/tmp/siemply_sessions/{session_name}.rc"
            tmux_cmd = f'tmux new-session -d -s {session_name} "python3 {remote_runner_path} >> {log_file_path} 2>&1; rc=$?; echo $rc | sudo tee {rc_path} >/dev/null; exit $rc"'
            
            # Create sessions directory
            await ssh.run("sudo mkdir -p /tmp/siemply_sessions")
            
            result = await ssh.run(tmux_cmd)
            if result.returncode != 0:
                return {"success": False, "message": f"Failed to start tmux session: {result.stderr}"}
            
            logger.info(f"Started tmux session: {session_name}")
            
            return {
                "success": True,
                "message": f"Splunk UF upgrade started in background session: {session_name}",
                "session_name": session_name,
                "version": version,
                "architecture": architecture,
            }
            
        except Exception as e:
            logger.error(f"Error starting UF upgrade on {host.hostname}: {str(e)}")
            return {"success": False, "message": f"Upgrade error: {str(e)}"}


async def upgrade_splunk_enterprise(host: Host, params: Dict[str, Any]) -> Dict[str, Any]:
    """Start a Splunk Enterprise upgrade under tmux using the upgrade runner."""
    logger.info("Starting Splunk Enterprise upgrade for host %s", host.hostname)
    
    version: Optional[str] = params.get("version")
    architecture: str = params.get("architecture", "x86_64")
    install_dir: str = params.get("install_dir", "/opt")
    user: str = params.get("user", "splunk")
    group: str = params.get("group", "splunk")
    if not version:
        return {"success": False, "message": "Target version is required"}
    download_urls = get_all_download_urls(version, architecture, "splunk_enterprise")
    if not download_urls:
        return {"success": False, "message": f"No download URL for version {version} arch {architecture}"}

    async with get_ssh_client(host) as ssh:
        if not ssh:
            return {"success": False, "message": "Could not establish SSH connection"}
        try:
            await _ensure_tmux_installed(ssh)
            import json
            env_data = {
                "version": version,
                "architecture": architecture,
                "install_dir": install_dir,
                "user": user,
                "group": group,
                "download_urls": download_urls,
            }
            remote_tmp_dir = "/tmp/siemply_splunk_upgrade"
            logger.info("Creating remote directory: %s", remote_tmp_dir)
            await ssh.run(f"sudo mkdir -p {remote_tmp_dir}")
            await ssh.upload_bytes(f"{remote_tmp_dir}/env.json", json.dumps(env_data, indent=2).encode("utf-8"), 0o644)

            try:
                local_runner_path = os.path.join(os.path.dirname(__file__), "..", "automation", "splunk", "upgrade_enterprise_runner.py")
                local_runner_path = os.path.abspath(local_runner_path)
                logger.info("Local runner path: %s", local_runner_path)
                
                if not os.path.exists(local_runner_path):
                    logger.error("Upgrade runner file not found: %s", local_runner_path)
                    return {"success": False, "message": f"Upgrade runner file not found: {local_runner_path}"}
                
                with open(local_runner_path, "rb") as f:
                    runner_bytes = f.read()
                logger.info("Uploading upgrade runner to: %s/upgrade_enterprise.py", remote_tmp_dir)
                await ssh.upload_bytes(f"{remote_tmp_dir}/upgrade_enterprise.py", runner_bytes, 0o755)
                
                session_name = f"siemply_ent_upgrade_{os.getpid()}"
                rc_dir = "/tmp/siemply_sessions"
                rc_path = f"{rc_dir}/{session_name}.rc"
                await ssh.run(f"sudo mkdir -p {rc_dir}")
                
                run_cmd = (
                    f"tmux new-session -d -s {session_name} \""
                    f"python3 {remote_tmp_dir}/upgrade_enterprise.py >> {remote_tmp_dir}/upgrade_runner.log 2>&1; rc=$?; "
                    f"echo $rc | sudo tee {rc_path} >/dev/null; exit $rc\""
                )
                logger.info("Starting tmux session: %s", session_name)
                start_tmux = await ssh.run(run_cmd)
                if start_tmux.returncode == 0:
                    logger.info("Successfully started upgrade tmux session: %s", session_name)
                    return {
                        "success": True,
                        "started_in_tmux": True,
                        "tmux_session": session_name,
                        "rc_path": rc_path,
                        "status_note": "Started Splunk Enterprise upgrade in tmux",
                        "actual_status": "running",
                    }
                else:
                    logger.error("Failed to start tmux session for upgrade: %s", start_tmux.stderr)
                    return {"success": False, "message": f"Failed to start tmux session: {start_tmux.stderr}"}
            except Exception as e:
                logger.error("Failed to stage upgrade runner: %s", str(e))
                return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error("Upgrade error: %s", str(e))
            return {"success": False, "message": str(e)}