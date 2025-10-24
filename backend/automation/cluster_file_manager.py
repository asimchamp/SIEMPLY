"""
Cluster File Manager
Handles copying cluster configuration files to target hosts during Splunk installation
"""
import os
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from backend.automation.ssh_client import AsyncSSHClient
from backend.models import Host

logger = logging.getLogger(__name__)

class ClusterFileManager:
    """Manages copying cluster configuration files to target hosts"""
    
    def __init__(self, base_cluster_path: str = None):
        """
        Initialize the cluster file manager
        
        Args:
            base_cluster_path: Base path to cluster configurations (default: backend/files/clusters)
        """
        if base_cluster_path is None:
            # Default to backend/files/clusters relative to this file
            current_file = Path(__file__)
            self.base_cluster_path = current_file.parent.parent.parent / "files" / "clusters"
            # Alternative: try current working directory
            if not self.base_cluster_path.exists():
                self.base_cluster_path = Path.cwd() / "files" / "clusters"
        else:
            self.base_cluster_path = Path(base_cluster_path)
    
    def get_component_config_path(self, cluster_name: str, component_type: str) -> Optional[Path]:
        """
        Get the path to component configuration files
        
        Args:
            cluster_name: Name of the cluster
            component_type: Type of Splunk component (e.g., 'cm', 'idx', 'sh')
            
        Returns:
            Path to component configuration directory or None if not found
        """
        # Map component types to folder names
        component_folder_map = {
            'splunk_cm': 'cm',
            'splunk_deployer': 'deployer', 
            'splunk_license_master': 'lm',
            'splunk_monitoring_console': 'mc',
            'splunk_deployment_server': 'ds',
            'splunk_search_head': 'sh',
            'splunk_indexer': 'idx',
            'splunk_hf': 'hf',
            'splunk_uf': 'uf',
            'splunk_enterprise': 'standalone'
        }
        
        folder_name = component_folder_map.get(component_type)
        if not folder_name:
            logger.warning(f"Unknown component type: {component_type}")
            return None
        
        component_path = self.base_cluster_path / cluster_name / folder_name
        if not component_path.exists():
            logger.warning(f"Component configuration path does not exist: {component_path}")
            return None
        
        return component_path
    
    def get_dynamic_component_config(self, cluster_name: str, component_type: str, host_ip: str = None) -> Dict[str, Any]:
        """
        Get dynamic component configuration that can be customized per instance
        
        Args:
            cluster_name: Name of the cluster
            component_type: Type of Splunk component
            host_ip: IP address of the target host for dynamic configuration
            
        Returns:
            Dictionary with dynamic configuration content
        """
        # Get base configuration files
        config_files = self.get_component_config_files(cluster_name, component_type)
        if not config_files:
            return {}
        
        dynamic_config = {}
        
        for file_path in config_files:
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Apply dynamic replacements based on component type and host IP
                    if component_type == 'splunk_search_head' and host_ip:
                        # Replace template variables in search head config
                        content = self._apply_search_head_dynamic_config(content, host_ip, cluster_name)
                    elif component_type == 'splunk_deployer' and host_ip:
                        # Replace template variables in deployer config
                        content = self._apply_deployer_dynamic_config(content, host_ip, cluster_name)
                    
                    dynamic_config[file_path.name] = content
                    
                except Exception as e:
                    logger.warning(f"Failed to read config file {file_path}: {str(e)}")
        
        return dynamic_config
    
    def _apply_search_head_dynamic_config(self, content: str, host_ip: str, cluster_name: str) -> str:
        """
        Apply dynamic configuration for search head instances
        
        Args:
            content: Original configuration content
            host_ip: IP address of the search head
            cluster_name: Name of the cluster
            
        Returns:
            Updated configuration content
        """
        # Get deployer IP from cluster configuration
        deployer_ip = self._get_deployer_ip_from_cluster(cluster_name)
        
        # Replace template variables with actual values
        replacements = {
            '{{HOST_IP}}': host_ip,
            '{{CLUSTER_NAME}}': cluster_name,
            '{{SERVER_NAME}}': f'sh-{host_ip}',
            '{{MGMT_URI}}': f'https://{host_ip}:8089',
            '{{DEPLOYER_IP}}': deployer_ip or '51.21.186.250'  # Default deployer IP
        }
        
        for template_var, value in replacements.items():
            content = content.replace(template_var, value)
        
        return content
    
    def _apply_deployer_dynamic_config(self, content: str, host_ip: str, cluster_name: str) -> str:
        """
        Apply dynamic configuration for deployer instances
        
        Args:
            content: Original configuration content
            host_ip: IP address of the deployer
            cluster_name: Name of the cluster
            
        Returns:
            Updated configuration content
        """
        # Replace template variables with actual values
        replacements = {
            '{{HOST_IP}}': host_ip,
            '{{CLUSTER_NAME}}': cluster_name,
            '{{SERVER_NAME}}': f'deployer-{host_ip}'
        }
        
        for template_var, value in replacements.items():
            content = content.replace(template_var, value)
        
        return content
    
    def _get_deployer_ip_from_cluster(self, cluster_name: str) -> Optional[str]:
        """
        Get deployer IP address from cluster configuration
        
        Args:
            cluster_name: Name of the cluster
            
        Returns:
            Deployer IP address or None if not found
        """
        try:
            # Try to read cluster metadata to get deployer IP
            cluster_path = self.base_cluster_path / cluster_name
            metadata_file = cluster_path / 'cluster.json'
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Check if we have build configuration with host mappings
                if 'build_config' in metadata and 'host_mapping' in metadata['build_config']:
                    host_mapping = metadata['build_config']['host_mapping']
                    # Look for deployer IP in various possible keys
                    for key in ['deployer', 'deployer_ip', 'deployer_fqdn']:
                        if key in host_mapping:
                            return host_mapping[key]
            
            # Fallback: try to find deployer in cluster directory
            deployer_path = cluster_path / 'deployer'
            if deployer_path.exists():
                # This is a simple fallback - in production you'd want to parse the actual config
                return '51.21.186.250'  # Default deployer IP
                
        except Exception as e:
            logger.warning(f"Failed to get deployer IP from cluster {cluster_name}: {str(e)}")
        
        return None
    
    def get_component_config_files(self, cluster_name: str, component_type: str) -> List[Path]:
        """
        Get list of configuration files for a component
        
        Args:
            cluster_name: Name of the cluster
            component_type: Type of Splunk component
            
        Returns:
            List of configuration file paths
        """
        component_path = self.get_component_config_path(cluster_name, component_type)
        if not component_path:
            return []
        
        config_files = []
        
        # Look for configuration files in local and default directories
        for config_dir in ['local', 'default']:
            config_path = component_path / config_dir
            if config_path.exists() and config_path.is_dir():
                for file_path in config_path.rglob('*'):
                    if file_path.is_file():
                        config_files.append(file_path)
        
        return config_files
    
    async def copy_component_configs_to_host(
        self, 
        ssh: AsyncSSHClient, 
        cluster_name: str, 
        component_type: str,
        target_base_dir: str = "/opt/splunk/etc/apps"
    ) -> Dict[str, Any]:
        """
        Copy component configuration files to a target host using efficient methods
        
        Args:
            ssh: SSH client for the target host
            cluster_name: Name of the cluster
            component_type: Type of Splunk component
            target_base_dir: Base directory on target host for Splunk configs (default: /opt/splunk/etc/apps)
            
        Returns:
            Dictionary with copy results
        """
        config_files = self.get_component_config_files(cluster_name, component_type)
        if not config_files:
            logger.warning(f"No configuration files found for {component_type} in cluster {cluster_name}")
            return {
                "success": False,
                "message": f"No configuration files found for {component_type}",
                "files_copied": 0
            }
        
        copied_files = 0
        errors = []
        
        # Determine if we're using the old system path or new apps path
        is_legacy_system = "/etc/apps" in target_base_dir
        is_apps_path = "/etc/apps" in target_base_dir
        
        try:
            if is_apps_path:
                # Create app directory structure
                app_name = f"siemply_{cluster_name}_{component_type.replace('splunk_', '')}"
                app_dir = f"{target_base_dir}/{app_name}"
                
                # Create main app directory
                result = await ssh.run(f"sudo mkdir -p {app_dir}")
                if result.returncode != 0:
                    logger.error(f"Failed to create app directory {app_dir}: {result.stderr}")
                    return {
                        "success": False,
                        "message": f"Failed to create app directory: {result.stderr}",
                        "files_copied": 0
                    }
                
                # Create default and local directories
                for config_dir in ['default', 'local']:
                    target_dir = f"{app_dir}/{config_dir}"
                    result = await ssh.run(f"sudo mkdir -p {target_dir}")
                    if result.returncode != 0:
                        logger.warning(f"Failed to create directory {target_dir}: {result.stderr}")
                
                # Copy each configuration file
                for file_path in config_files:
                    try:
                        # Determine target path - preserve the local/default structure
                        if 'local' in str(file_path):
                            target_path = f"{app_dir}/local/{file_path.name}"
                        elif 'default' in str(file_path):
                            target_path = f"{app_dir}/default/{file_path.name}"
                        else:
                            target_path = f"{app_dir}/{file_path.name}"
                        
                        # Create target directory if needed
                        target_dir = os.path.dirname(target_path)
                        await ssh.run(f"sudo mkdir -p {target_dir}")
                        
                        # Read and copy file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        
                        # Use cat to create the file on remote host
                        copy_cmd = f"cat > {target_path} << 'EOF'\n{file_content}\nEOF"
                        result = await ssh.run(copy_cmd)
                        
                        if result.returncode == 0:
                            # Set proper permissions
                            await ssh.run(f"sudo chmod 644 {target_path}")
                            await ssh.run(f"sudo chown splunk:splunk {target_path}")
                            copied_files += 1
                            logger.info(f"Copied {file_path.name} to {target_path}")
                        else:
                            error_msg = f"Failed to copy {file_path.name}: {result.stderr}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                            
                    except Exception as e:
                        error_msg = f"Error copying {file_path.name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                # Create app.conf file for Splunk app metadata
                app_conf_content = f"""[package]
id = {app_name}
name = SIEMply {cluster_name} {component_type.replace('splunk_', '').upper()} Configuration
version = 1.0.0
description = Configuration files for {component_type} in cluster {cluster_name}

[install]
is_configured = true
state = enabled
"""
                
                app_conf_path = f"{app_dir}/default/app.conf"
                app_conf_cmd = f"cat > {app_conf_path} << 'EOF'\n{app_conf_content}\nEOF"
                result = await ssh.run(app_conf_cmd)
                
                if result.returncode == 0:
                    await ssh.run(f"sudo chmod 644 {app_conf_path}")
                    await ssh.run(f"sudo chown splunk:splunk {app_conf_path}")
                    copied_files += 1
                    logger.info(f"Created app.conf for {app_name}")
                else:
                    logger.warning(f"Failed to create app.conf: {result.stderr}")
                
                if errors:
                    return {
                        "success": False,
                        "message": f"Copied {copied_files} files with {len(errors)} errors",
                        "files_copied": copied_files,
                        "errors": errors,
                        "app_name": app_name,
                        "app_path": app_dir,
                        "method": "app_based"
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Successfully copied {copied_files} configuration files to app {app_name}",
                        "files_copied": copied_files,
                        "app_name": app_name,
                        "app_path": app_dir,
                        "method": "app_based"
                    }
            
            else:
                # Legacy system path copying (maintains backward compatibility)
                # Create target directories
                for config_dir in ['local', 'default']:
                    target_dir = f"{target_base_dir}/{config_dir}"
                    result = await ssh.run(f"sudo mkdir -p {target_dir}")
                    if result.returncode != 0:
                        logger.warning(f"Failed to create directory {target_dir}: {result.stderr}")
                
                # Copy each configuration file
                for file_path in config_files:
                    try:
                        # Determine target path - preserve the local/default structure
                        if 'local' in str(file_path):
                            target_path = f"{target_base_dir}/local/{file_path.name}"
                        elif 'default' in str(file_path):
                            target_path = f"{target_base_dir}/default/{file_path.name}"
                        else:
                            target_path = f"{target_base_dir}/{file_path.name}"
                        
                        # Create target directory if needed
                        target_dir = os.path.dirname(target_path)
                        await ssh.run(f"sudo mkdir -p {target_dir}")
                        
                        # Read and copy file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        
                        # Use cat to create the file on remote host
                        copy_cmd = f"cat > {target_path} << 'EOF'\n{file_content}\nEOF"
                        result = await ssh.run(copy_cmd)
                        
                        if result.returncode == 0:
                            # Set proper permissions
                            await ssh.run(f"sudo chmod 644 {target_path}")
                            await ssh.run(f"sudo chown splunk:splunk {target_path}")
                            copied_files += 1
                            logger.info(f"Copied {file_path.name} to {target_path}")
                        else:
                            error_msg = f"Failed to copy {file_path.name}: {result.stderr}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                            
                    except Exception as e:
                        error_msg = f"Error copying {file_path.name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                if errors:
                    return {
                        "success": False,
                        "message": f"Copied {copied_files} files with {len(errors)} errors",
                        "files_copied": copied_files,
                        "errors": errors,
                        "method": "legacy_system"
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Successfully copied {copied_files} configuration files to system path",
                        "files_copied": copied_files,
                        "method": "legacy_system"
                    }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to copy configuration files: {str(e)}",
                "files_copied": copied_files,
                "errors": [str(e)]
            }
    
    async def copy_component_configs_via_scp(
        self,
        ssh: AsyncSSHClient,
        cluster_name: str,
        component_type: str,
        target_base_dir: str = "/opt/splunk/etc/apps"
    ) -> Dict[str, Any]:
        """
        Alternative method: Copy component configuration files using SCP for better performance
        
        Args:
            ssh: SSH client for the target host
            cluster_name: Name of the cluster
            component_type: Type of Splunk component
            target_base_dir: Base directory on target host for Splunk configs
            
        Returns:
            Dictionary with copy results
        """
        component_path = self.get_component_config_path(cluster_name, component_type)
        if not component_path:
            return {
                "success": False,
                "message": f"No configuration path found for {component_type}",
                "files_copied": 0
            }
        
        # Determine if we're using the old system path or new apps path
        is_legacy_system = "/etc/apps" in target_base_dir
        is_apps_path = "/etc/apps" in target_base_dir
        
        try:
            if is_apps_path:
                # Create app directory structure
                app_name = f"siemply_{cluster_name}_{component_type.replace('splunk_', '')}"
                app_dir = f"{target_base_dir}/{app_name}"
                
                # Create main app directory
                result = await ssh.run(f"sudo mkdir -p {app_dir}")
                if result.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Failed to create app directory: {result.stderr}",
                        "files_copied": 0
                    }
                
                # Use rsync if available, otherwise fall back to individual file copy
                rsync_check = await ssh.run("which rsync")
                if rsync_check.returncode == 0:
                    # Use rsync for efficient copying
                    rsync_cmd = f"rsync -av --delete {component_path}/ {app_dir}/"
                    result = await ssh.run(rsync_cmd)
                    
                    if result.returncode == 0:
                        # Set proper permissions recursively
                        await ssh.run(f"sudo chown -R splunk:splunk {app_dir}")
                        await ssh.run(f"sudo chmod -R 644 {app_dir}")
                        await ssh.run(f"sudo find {app_dir} -type d -exec chmod 755 {{}} \\;")
                        
                        # Count copied files
                        file_count_result = await ssh.run(f"find {app_dir} -type f | wc -l")
                        copied_files = int(file_count_result.stdout.strip()) if file_count_result.returncode == 0 else 0
                        
                        return {
                            "success": True,
                            "message": f"Successfully copied configuration files using rsync to app {app_name}",
                            "files_copied": copied_files,
                            "app_name": app_name,
                            "app_path": app_dir,
                            "method": "rsync_app_based"
                        }
                    else:
                        logger.warning(f"rsync failed, falling back to individual file copy: {result.stderr}")
                else:
                    logger.info("rsync not available, using individual file copy method")
                
                # Fall back to individual file copy method
                return await self.copy_component_configs_to_host(ssh, cluster_name, component_type, target_base_dir)
            
            else:
                # For legacy system paths, fall back to individual file copy
                logger.info("Using legacy system path, falling back to individual file copy method")
                return await self.copy_component_configs_to_host(ssh, cluster_name, component_type, target_base_dir)
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to copy configuration files via SCP: {str(e)}",
                "files_copied": 0,
                "errors": [str(e)]
            }
    
    async def copy_component_configs_direct(
        self,
        ssh: AsyncSSHClient,
        cluster_name: str,
        component_type: str,
        target_base_dir: str = "/opt/splunk/etc/apps",
        host_ip: str = None
    ) -> Dict[str, Any]:
        """
        Direct copy method: Copy entire configuration directory structure using SCP/rsync
        This method avoids sending files as EOF content and directly copies the folder structure
        Supports dynamic configuration for multiple instances of the same component type
        
        Args:
            ssh: SSH client for the target host
            cluster_name: Name of the cluster
            component_type: Type of Splunk component
            target_base_dir: Base directory on target host for Splunk configs
            host_ip: IP address of the target host for dynamic configuration
            
        Returns:
            Dictionary with copy results
        """
        component_path = self.get_component_config_path(cluster_name, component_type)
        if not component_path:
            return {
                "success": False,
                "message": f"No configuration path found for {component_type}",
                "files_copied": 0
            }
        
        # Determine if we're using the old system path or new apps path
        is_apps_path = "/etc/apps" in target_base_dir
        
        try:
            if is_apps_path:
                # Create app directory structure
                app_name = f"siemply_{cluster_name}_{component_type.replace('splunk_', '')}"
                app_dir = f"{target_base_dir}/{app_name}"
                
                # Create main app directory
                result = await ssh.run(f"sudo mkdir -p {app_dir}")
                if result.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Failed to create app directory: {result.stderr}",
                        "files_copied": 0
                    }
                
                # Get dynamic configuration if host IP is provided
                if host_ip:
                    dynamic_config = self.get_dynamic_component_config(cluster_name, component_type, host_ip)
                    if dynamic_config:
                        logger.info(f"Using dynamic configuration for {component_type} on {host_ip}")
                        return await self._copy_dynamic_config_files(ssh, dynamic_config, app_dir, app_name)
                
                # Use rsync if available for efficient directory copying
                rsync_check = await ssh.run("which rsync")
                if rsync_check.returncode == 0:
                    logger.info(f"Using rsync to copy configuration directory from {component_path} to {app_dir}")
                    
                    # Create a temporary tar archive of the configuration directory
                    temp_tar_path = f"/tmp/{cluster_name}_{component_type.replace('splunk_', '')}_configs.tar"
                    
                    # Create tar archive locally and upload it
                    import tarfile
                    import tempfile
                    
                    with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as temp_tar:
                        with tarfile.open(temp_tar.name, 'w') as tar:
                            tar.add(component_path, arcname=os.path.basename(component_path))
                        
                        # Upload the tar file to the remote host
                        with open(temp_tar.name, 'rb') as f:
                            tar_content = f.read()
                        
                        await ssh.upload_bytes(temp_tar_path, tar_content, 0o644)
                        
                        # Clean up local temp file
                        os.unlink(temp_tar.name)
                    
                    # Extract the tar file on the remote host
                    extract_cmd = f"cd {app_dir} && sudo tar -xf {temp_tar_path} --strip-components=1"
                    result = await ssh.run(extract_cmd)
                    
                    if result.returncode == 0:
                        # Set proper permissions recursively
                        await ssh.run(f"sudo chown -R splunk:splunk {app_dir}")
                        await ssh.run(f"sudo chmod -R 644 {app_dir}")
                        await ssh.run(f"sudo find {app_dir} -type d -exec chmod 755 {{}} \\;")
                        
                        # Clean up temporary tar file
                        await ssh.run(f"sudo rm -f {temp_tar_path}")
                        
                        # Count copied files
                        file_count_result = await ssh.run(f"find {app_dir} -type f | wc -l")
                        copied_files = int(file_count_result.stdout.strip()) if file_count_result.returncode == 0 else 0
                        
                        # Create app.conf file for Splunk app metadata
                        app_conf_content = f"""[package]
id = {app_name}
name = SIEMply {cluster_name} {component_type.replace('splunk_', '').upper()} Configuration
version = 1.0.0
description = Configuration files for {component_type} in cluster {cluster_name}

[install]
is_configured = true
state = enabled
"""
                        
                        app_conf_path = f"{app_dir}/default/app.conf"
                        app_conf_cmd = f"cat > {app_conf_path} << 'EOF'\n{app_conf_content}\nEOF"
                        await ssh.run(app_conf_cmd)
                        await ssh.run(f"sudo chmod 644 {app_conf_path}")
                        await ssh.run(f"sudo chown splunk:splunk {app_conf_path}")
                        
                        return {
                            "success": True,
                            "message": f"Successfully copied configuration directory using direct method to app {app_name}",
                            "files_copied": copied_files,
                            "app_name": app_name,
                            "app_path": app_dir,
                            "method": "direct_directory_copy"
                        }
                    else:
                        # Clean up temporary tar file on failure
                        await ssh.run(f"sudo rm -f {temp_tar_path}")
                        return {
                            "success": False,
                            "message": f"Failed to extract configuration files: {result.stderr}",
                            "files_copied": 0
                        }
                else:
                    logger.info("rsync not available, using direct file copy method")
                    # Fall back to direct file copy without EOF
                    return await self._copy_files_direct(ssh, component_path, app_dir, app_name)
            
            else:
                # For legacy system paths, use direct copy to system directories
                logger.info("Using legacy system path with direct copy method")
                return await self._copy_files_direct(ssh, component_path, target_base_dir, None)
            
        except Exception as e:
            logger.error(f"Failed to copy configuration files directly: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to copy configuration files directly: {str(e)}",
                "errors": [str(e)]
            }
    
    async def _copy_files_direct(
        self,
        ssh: AsyncSSHClient,
        source_path: Path,
        target_base_dir: str,
        app_name: Optional[str]
    ) -> Dict[str, Any]:
        """
        Helper method to copy files directly without EOF method
        
        Args:
            ssh: SSH client for the target host
            source_path: Source configuration directory path
            target_base_dir: Target base directory on remote host
            app_name: App name if using apps path
            
        Returns:
            Dictionary with copy results
        """
        copied_files = 0
        errors = []
        
        try:
            # Create target directories
            for config_dir in ['local', 'default']:
                target_dir = f"{target_base_dir}/{config_dir}"
                result = await ssh.run(f"sudo mkdir -p {target_dir}")
                if result.returncode != 0:
                    logger.warning(f"Failed to create directory {target_dir}: {result.stderr}")
            
            # Copy each configuration file using direct file upload
            for file_path in source_path.rglob('*'):
                if file_path.is_file():
                    try:
                        # Determine target path - preserve the local/default structure
                        if 'local' in str(file_path):
                            target_path = f"{target_base_dir}/local/{file_path.name}"
                        elif 'default' in str(file_path):
                            target_path = f"{target_base_dir}/default/{file_path.name}"
                        else:
                            target_path = f"{target_base_dir}/{file_path.name}"
                        
                        # Create target directory if needed
                        target_dir = os.path.dirname(target_path)
                        await ssh.run(f"sudo mkdir -p {target_dir}")
                        
                        # Read file content and upload directly
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        
                        # Use direct file upload instead of EOF
                        await ssh.upload_bytes(target_path, file_content.encode('utf-8'), 0o644)
                        
                        # Set proper permissions
                        await ssh.run(f"sudo chmod 644 {target_path}")
                        await ssh.run(f"sudo chown splunk:splunk {target_path}")
                        copied_files += 1
                        logger.info(f"Copied {file_path.name} to {target_path}")
                        
                    except Exception as e:
                        error_msg = f"Error copying {file_path.name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            
            # Create app.conf if using apps path
            if app_name:
                app_conf_content = f"""[package]
id = {app_name}
name = SIEMply Configuration
version = 1.0.0
description = Configuration files

[install]
is_configured = true
state = enabled
"""
                
                app_conf_path = f"{target_base_dir}/default/app.conf"
                await ssh.upload_bytes(app_conf_path, app_conf_content.encode('utf-8'), 0o644)
                await ssh.run(f"sudo chmod 644 {app_conf_path}")
                await ssh.run(f"sudo chown splunk:splunk {app_conf_path}")
                copied_files += 1
            
            if errors:
                return {
                    "success": False,
                    "message": f"Copied {copied_files} files with {len(errors)} errors",
                    "files_copied": copied_files,
                    "errors": errors,
                    "method": "direct_file_copy"
                }
            else:
                return {
                    "success": True,
                    "message": f"Successfully copied {copied_files} configuration files using direct method",
                    "files_copied": copied_files,
                    "method": "direct_file_copy"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to copy files directly: {str(e)}",
                "files_copied": copied_files,
                "errors": [str(e)]
            }
    
    def validate_cluster_exists(self, cluster_name: str) -> bool:
        """
        Check if a cluster configuration exists
        
        Args:
            cluster_name: Name of the cluster to check
            
        Returns:
            True if cluster exists, False otherwise
        """
        cluster_path = self.base_cluster_path / cluster_name
        return cluster_path.exists() and cluster_path.is_dir()
    
    async def _copy_dynamic_config_files(
        self,
        ssh: AsyncSSHClient,
        dynamic_config: Dict[str, str],
        app_dir: str,
        app_name: str
    ) -> Dict[str, Any]:
        """
        Copy dynamic configuration files to the target host
        
        Args:
            ssh: SSH client for the target host
            dynamic_config: Dictionary of file names and their dynamic content
            app_dir: Target app directory on remote host
            app_name: Name of the Splunk app
            
        Returns:
            Dictionary with copy results
        """
        copied_files = 0
        errors = []
        
        try:
            # Create default and local directories
            for config_dir in ['default', 'local']:
                target_dir = f"{app_dir}/{config_dir}"
                result = await ssh.run(f"sudo mkdir -p {target_dir}")
                if result.returncode != 0:
                    logger.warning(f"Failed to create directory {target_dir}: {result.stderr}")
            
            # Copy each dynamic configuration file
            for file_name, file_content in dynamic_config.items():
                try:
                    # Determine if it's a default or local config based on file name
                    if 'local' in file_name.lower():
                        target_path = f"{app_dir}/local/{file_name}"
                    else:
                        target_path = f"{app_dir}/default/{file_name}"
                    
                    # Create target directory if needed
                    target_dir = os.path.dirname(target_path)
                    await ssh.run(f"sudo mkdir -p {target_dir}")
                    
                    # Upload the dynamic content directly
                    await ssh.upload_bytes(target_path, file_content.encode('utf-8'), 0o644)
                    
                    # Set proper permissions
                    await ssh.run(f"sudo chmod 644 {target_path}")
                    await ssh.run(f"sudo chown splunk:splunk {target_path}")
                    copied_files += 1
                    logger.info(f"Copied dynamic config {file_name} to {target_path}")
                    
                except Exception as e:
                    error_msg = f"Error copying dynamic config {file_name}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Create app.conf file for Splunk app metadata
            app_conf_content = f"""[package]
id = {app_name}
name = SIEMply Dynamic Configuration
version = 1.0.0
description = Dynamic configuration files

[install]
is_configured = true
state = enabled
"""
            
            app_conf_path = f"{app_dir}/default/app.conf"
            await ssh.upload_bytes(app_conf_path, app_conf_content.encode('utf-8'), 0o644)
            await ssh.run(f"sudo chmod 644 {app_conf_path}")
            await ssh.run(f"sudo chown splunk:splunk {app_conf_path}")
            copied_files += 1
            
            if errors:
                return {
                    "success": False,
                    "message": f"Copied {copied_files} dynamic config files with {len(errors)} errors",
                    "files_copied": copied_files,
                    "errors": errors,
                    "method": "dynamic_config_copy"
                }
            else:
                return {
                    "success": True,
                    "message": f"Successfully copied {copied_files} dynamic configuration files",
                    "files_copied": copied_files,
                    "method": "dynamic_config_copy"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to copy dynamic configuration files: {str(e)}",
                "files_copied": copied_files,
                "errors": [str(e)]
            }
    
    def list_available_clusters(self) -> List[str]:
        """
        List all available clusters
        
        Returns:
            List of cluster names
        """
        clusters = []
        if self.base_cluster_path.exists():
            for item in self.base_cluster_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    clusters.append(item.name)
        return clusters
