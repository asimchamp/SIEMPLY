#!/usr/bin/env python3
"""
Splunk Search Head Cluster (SHC) Setup Script
Automates the SHC setup process according to Splunk best practices
"""
import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from backend.automation.ssh_client import AsyncSSHClient
from backend.automation.cluster_file_manager import ClusterFileManager

logger = logging.getLogger(__name__)

class SHCSetupManager:
    """Manages Splunk Search Head Cluster setup process"""
    
    def __init__(self, cluster_name: str = "Splunk_Clus"):
        self.cluster_name = cluster_name
        self.cluster_manager = ClusterFileManager()
        self.shc_label = f"sh-{cluster_name}"
        self.pass4symm_key = "9PsTPvgT!QrnRahhhBoGJvCVHW$q8MPl"
        self.replication_port = 8181
        self.replication_factor = 2
        
    async def setup_shcluster(self, deployer_host: str, search_heads: List[str]) -> Dict[str, Any]:
        """
        Setup complete Search Head Cluster following Splunk best practices
        
        Args:
            deployer_host: IP address of the deployer
            search_heads: List of search head IP addresses
            
        Returns:
            Dictionary with setup results
        """
        try:
            logger.info(f"Starting SHC setup for cluster: {self.cluster_name}")
            logger.info(f"Deployer: {deployer_host}")
            logger.info(f"Search Heads: {search_heads}")
            
            results = {
                'cluster_name': self.cluster_name,
                'deployer_host': deployer_host,
                'search_heads': search_heads,
                'steps_completed': [],
                'errors': [],
                'warnings': []
            }
            
            # Step 1: Validate prerequisites
            await self._validate_prerequisites(deployer_host, search_heads, results)
            
            # Step 2: Configure Deployer
            await self._configure_deployer(deployer_host, results)
            
            # Step 3: Configure Search Heads
            await self._configure_search_heads(search_heads, deployer_host, results)
            
            # Step 4: Bootstrap the Cluster
            if len(search_heads) > 0:
                await self._bootstrap_cluster(search_heads, deployer_host, results)
            
            # Step 5: Connect to Indexers
            await self._connect_to_indexers(search_heads, results)
            
            logger.info(f"SHC setup completed for {self.cluster_name}")
            return results
            
        except Exception as e:
            error_msg = f"Failed to setup SHC: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
    
    async def _validate_prerequisites(self, deployer_host: str, search_heads: List[str], results: Dict[str, Any]):
        """Validate prerequisites for SHC setup"""
        logger.info("Validating prerequisites...")
        
        # Check if deployer is accessible
        try:
            ssh = AsyncSSHClient(deployer_host, "root")
            await ssh.connect()
            await ssh.run("sudo -u splunk /opt/splunk/bin/splunk status")
            await ssh.disconnect()
            results['steps_completed'].append("Prerequisites validation")
        except Exception as e:
            error_msg = f"Deployer validation failed: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        # Check if search heads are accessible
        for sh_ip in search_heads:
            try:
                ssh = AsyncSSHClient(sh_ip, "root")
                await ssh.connect()
                await ssh.run("sudo -u splunk /opt/splunk/bin/splunk status")
                await ssh.disconnect()
            except Exception as e:
                warning_msg = f"Search head {sh_ip} validation failed: {str(e)}"
                results['warnings'].append(warning_msg)
                logger.warning(warning_msg)
    
    async def _configure_deployer(self, deployer_host: str, results: Dict[str, Any]):
        """Configure the deployer according to Splunk SHC best practices"""
        logger.info(f"Configuring deployer: {deployer_host}")
        
        try:
            ssh = AsyncSSHClient(deployer_host, "root")
            await ssh.connect()
            
            # Create deployer app directory structure
            deployer_app_dir = f"/opt/splunk/etc/shcluster/apps/siemply_{self.cluster_name}_deployer"
            await ssh.run(f"sudo mkdir -p {deployer_app_dir}/default")
            
            # Copy deployer configuration
            deployer_config = self.cluster_manager.get_dynamic_component_config(
                self.cluster_name, 'splunk_deployer', deployer_host
            )
            
            if deployer_config:
                # Copy configuration files
                for file_name, content in deployer_config.items():
                    file_path = f"{deployer_app_dir}/default/{file_name}"
                    await ssh.upload_bytes(file_path, content.encode('utf-8'), 0o644)
                    await ssh.run(f"sudo chown splunk:splunk {file_path}")
                
                # Set proper permissions
                await ssh.run(f"sudo chown -R splunk:splunk {deployer_app_dir}")
                await ssh.run(f"sudo chmod -R 644 {deployer_app_dir}")
                await ssh.run(f"sudo find {deployer_app_dir} -type d -exec chmod 755 {{}} \\;")
                
                # Restart Splunk to apply configuration
                await ssh.run("sudo -u splunk /opt/splunk/bin/splunk restart --answer-yes --no-prompt")
                
                results['steps_completed'].append("Deployer configuration")
                logger.info("Deployer configured successfully")
            else:
                error_msg = "Failed to get deployer configuration"
                results['errors'].append(error_msg)
                logger.error(error_msg)
            
            await ssh.disconnect()
            
        except Exception as e:
            error_msg = f"Deployer configuration failed: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
    
    async def _configure_search_heads(self, search_heads: List[str], deployer_host: str, results: Dict[str, Any]):
        """Configure search heads according to Splunk SHC best practices"""
        logger.info(f"Configuring {len(search_heads)} search heads...")
        
        for i, sh_ip in enumerate(search_heads):
            try:
                logger.info(f"Configuring search head {i+1}: {sh_ip}")
                ssh = AsyncSSHClient(sh_ip, "root")
                await ssh.connect()
                
                # Create search head app directory structure
                sh_app_dir = f"/opt/splunk/etc/apps/siemply_{self.cluster_name}_sh"
                await ssh.run(f"sudo mkdir -p {sh_app_dir}/default")
                
                # Copy search head configuration with dynamic variables
                sh_config = self.cluster_manager.get_dynamic_component_config(
                    self.cluster_name, 'splunk_search_head', sh_ip
                )
                
                if sh_config:
                    # Copy configuration files
                    for file_name, content in sh_config.items():
                        file_path = f"{sh_app_dir}/default/{file_name}"
                        await ssh.upload_bytes(file_path, content.encode('utf-8'), 0o644)
                        await ssh.run(f"sudo chown splunk:splunk {file_path}")
                    
                    # Set proper permissions
                    await ssh.run(f"sudo chown -R splunk:splunk {sh_app_dir}")
                    await ssh.run(f"sudo chmod -R 644 {sh_app_dir}")
                    await ssh.run(f"sudo find {sh_app_dir} -type d -exec chmod 755 {{}} \\;")
                    
                    # Restart Splunk to apply configuration
                    await ssh.run("sudo -u splunk /opt/splunk/bin/splunk restart --answer-yes --no-prompt")
                    
                    logger.info(f"Search head {sh_ip} configured successfully")
                else:
                    error_msg = f"Failed to get search head configuration for {sh_ip}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
                
                await ssh.disconnect()
                
            except Exception as e:
                error_msg = f"Search head {sh_ip} configuration failed: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        results['steps_completed'].append("Search head configuration")
    
    async def _bootstrap_cluster(self, search_heads: List[str], deployer_host: str, results: Dict[str, Any]):
        """Bootstrap the Search Head Cluster"""
        logger.info("Bootstrapping Search Head Cluster...")
        
        if len(search_heads) == 0:
            logger.warning("No search heads to bootstrap")
            return
        
        try:
            # Bootstrap first search head
            first_sh = search_heads[0]
            ssh = AsyncSSHClient(first_sh, "root")
            await ssh.connect()
            
            # Initialize SHC configuration on first member
            init_cmd = f"""sudo -u splunk /opt/splunk/bin/splunk init shcluster-config \\
                -auth admin:changeme \\
                -mgmt_uri https://{first_sh}:8089 \\
                -replication_port {self.replication_port} \\
                -replication_factor {self.replication_factor} \\
                -conf_deploy_fetch_url https://{deployer_host}:8089 \\
                -secret {self.pass4symm_key} \\
                -shcluster_label {self.shc_label}"""
            
            result = await ssh.run(init_cmd)
            if result.returncode == 0:
                logger.info(f"SHC initialized on {first_sh}")
                
                # Restart first search head
                await ssh.run("sudo -u splunk /opt/splunk/bin/splunk restart --answer-yes --no-prompt")
                
                # Wait for restart
                await asyncio.sleep(30)
                
                # Join other search heads to cluster
                for sh_ip in search_heads[1:]:
                    try:
                        sh_ssh = AsyncSSHClient(sh_ip, "root")
                        await sh_ssh.connect()
                        
                        join_cmd = f"""sudo -u splunk /opt/splunk/bin/splunk init shcluster-config \\
                            -auth admin:changeme \\
                            -mgmt_uri https://{sh_ip}:8089 \\
                            -replication_port {self.replication_port} \\
                            -secret {self.pass4symm_key} \\
                            -shcluster_label {self.shc_label}"""
                        
                        join_result = await sh_ssh.run(join_cmd)
                        if join_result.returncode == 0:
                            logger.info(f"SHC joined on {sh_ip}")
                            await sh_ssh.run("sudo -u splunk /opt/splunk/bin/splunk restart --answer-yes --no-prompt")
                        else:
                            logger.warning(f"Failed to join SHC on {sh_ip}: {join_result.stderr}")
                        
                        await sh_ssh.disconnect()
                        
                    except Exception as e:
                        logger.warning(f"Failed to join {sh_ip} to SHC: {str(e)}")
                
                # Wait for all members to join
                await asyncio.sleep(60)
                
                # Elect captain from first search head
                servers_list = ",".join([f"https://{sh}:8089" for sh in search_heads])
                captain_cmd = f"""sudo -u splunk /opt/splunk/bin/splunk bootstrap shcluster-captain \\
                    -servers_list "{servers_list}" \\
                    -auth admin:changeme"""
                
                captain_result = await ssh.run(captain_cmd)
                if captain_result.returncode == 0:
                    logger.info("SHC captain elected successfully")
                    results['steps_completed'].append("Cluster bootstrapping")
                else:
                    logger.warning(f"Failed to elect captain: {captain_result.stderr}")
                
            else:
                error_msg = f"Failed to initialize SHC on {first_sh}: {result.stderr}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
            
            await ssh.disconnect()
            
        except Exception as e:
            error_msg = f"SHC bootstrapping failed: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
    
    async def _connect_to_indexers(self, search_heads: List[str], results: Dict[str, Any]):
        """Connect search heads to indexers"""
        logger.info("Connecting search heads to indexers...")
        
        # For now, we'll use the cluster manager as the indexer
        # In production, you'd want to get the actual indexer list
        indexer_uri = "https://13.61.123.93:8089"  # Cluster Manager as indexer
        
        for sh_ip in search_heads:
            try:
                ssh = AsyncSSHClient(sh_ip, "root")
                await ssh.connect()
                
                # Add search server (indexer)
                add_server_cmd = f"""sudo -u splunk /opt/splunk/bin/splunk add search-server {indexer_uri} -auth admin:changeme"""
                result = await ssh.run(add_server_cmd)
                
                if result.returncode == 0:
                    logger.info(f"Connected {sh_ip} to indexer {indexer_uri}")
                else:
                    logger.warning(f"Failed to connect {sh_ip} to indexer: {result.stderr}")
                
                await ssh.disconnect()
                
            except Exception as e:
                logger.warning(f"Failed to connect {sh_ip} to indexers: {str(e)}")
        
        results['steps_completed'].append("Indexer connection")
    
    async def verify_shcluster_status(self, search_heads: List[str]) -> Dict[str, Any]:
        """Verify SHC status on all members"""
        logger.info("Verifying SHC status...")
        
        status_results = {}
        
        for sh_ip in search_heads:
            try:
                ssh = AsyncSSHClient(sh_ip, "root")
                await ssh.connect()
                
                # Check SHC status
                status_cmd = "sudo -u splunk /opt/splunk/bin/splunk show shcluster-status -auth admin:changeme"
                result = await ssh.run(status_cmd)
                
                if result.returncode == 0:
                    status_results[sh_ip] = {
                        'status': 'success',
                        'output': result.stdout
                    }
                else:
                    status_results[sh_ip] = {
                        'status': 'error',
                        'error': result.stderr
                    }
                
                await ssh.disconnect()
                
            except Exception as e:
                status_results[sh_ip] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return status_results

async def main():
    """Main function to run SHC setup"""
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize SHC setup manager
    shc_manager = SHCSetupManager("Splunk_Clus")
    
    # Define hosts
    deployer_host = "51.21.186.250"
    search_heads = ["51.21.31.241", "16.171.114.44"]
    
    # Run SHC setup
    results = await shc_manager.setup_shcluster(deployer_host, search_heads)
    
    # Print results
    print("\n" + "="*50)
    print("SHC SETUP RESULTS")
    print("="*50)
    print(f"Cluster: {results['cluster_name']}")
    print(f"Deployer: {results['deployer_host']}")
    print(f"Search Heads: {results['search_heads']}")
    print(f"\nSteps Completed: {len(results['steps_completed'])}")
    for step in results['steps_completed']:
        print(f"  ✓ {step}")
    
    if results['errors']:
        print(f"\nErrors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  ✗ {error}")
    
    if results['warnings']:
        print(f"\nWarnings: {len(results['warnings'])}")
        for warning in results['warnings']:
            print(f"  ⚠ {warning}")
    
    # Verify final status
    print("\nVerifying SHC status...")
    status_results = await shc_manager.verify_shcluster_status(search_heads)
    
    for sh_ip, status in status_results.items():
        print(f"\n{sh_ip}:")
        if status['status'] == 'success':
            print("  ✓ SHC status retrieved successfully")
        else:
            print(f"  ✗ Failed to get status: {status['error']}")

if __name__ == "__main__":
    asyncio.run(main())
