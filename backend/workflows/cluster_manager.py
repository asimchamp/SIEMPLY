"""
Enhanced Splunk Environment Builder
Comprehensive configuration manager for production-ready Splunk infrastructure
Based on Splunk best practices and Azure reference architecture
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import secrets
import string


logger = logging.getLogger(__name__)


class EnhancedSplunkClusterManager:
    """Enhanced Splunk cluster configurations manager with production-ready templates"""

    def __init__(self, base_path: str = "/opt/SIEMPLY/backend/files/clusters"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Enhanced Splunk components with additional roles
        self.components = {
            'cm': 'Cluster Manager',           # Cluster Master/Manager
            'deployer': 'Deployer',           # Search Head Cluster Deployer
            'sh': 'Search Head',              # Search Head (supports multiple instances)
            'idx': 'Indexer',                 # Indexer/Peer Node
            'ds': 'Deployment Server',        # Deployment Server
            'uf': 'Universal Forwarder',      # Universal Forwarder
            'hf': 'Heavy Forwarder',          # Heavy Forwarder
            'lm': 'License Master',           # License Master
            'mc': 'Monitoring Console',       # Monitoring Console
        }

        # Configuration files per component
        self.config_files = {
            'cm': ['server.conf', 'indexes.conf', 'authorize.conf', 'authentication.conf', 
                   'web.conf', 'limits.conf', 'distsearch.conf'],
            'deployer': ['server.conf', 'authorize.conf', 'authentication.conf', 'web.conf', 'shcluster.conf'],
            'sh': ['server.conf', 'distsearch.conf', 'authorize.conf', 'authentication.conf', 
                   'web.conf', 'limits.conf', 'ui-prefs.conf', 'shcluster.conf'],
            'idx': ['server.conf', 'indexes.conf', 'inputs.conf', 'props.conf', 'transforms.conf',
                    'limits.conf', 'authorize.conf', 'authentication.conf'],
            'ds': ['server.conf', 'serverclass.conf', 'authorize.conf', 'authentication.conf',
                   'web.conf'],
            'uf': ['inputs.conf', 'outputs.conf', 'deploymentclient.conf', 'limits.conf'],
            'hf': ['inputs.conf', 'outputs.conf', 'props.conf', 'transforms.conf', 
                   'server.conf', 'limits.conf'],
            'lm': ['server.conf', 'authorize.conf', 'authentication.conf', 'web.conf'],
            'mc': ['server.conf', 'authorize.conf', 'authentication.conf', 'web.conf',
                   'distsearch.conf'],
        }

        # Configuration subfolders
        self.config_folders = ['default', 'local']

        # Security settings
        self.default_pass_key = self._generate_pass_key()

    def _generate_pass_key(self) -> str:
        """Generate a secure password key for cluster communication"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for i in range(32))

    def create_cluster_structure(self, cluster_name: str, 
                               cluster_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create complete cluster folder structure with enhanced configurations

        Args:
            cluster_name: Name of the cluster
            cluster_config: Optional cluster configuration parameters

        Returns:
            Dict with creation results
        """
        try:
            cluster_path = self.base_path / cluster_name

            if cluster_path.exists():
                return {
                    'success': False,
                    'error': f'Cluster "{cluster_name}" already exists'
                }

            # Set default cluster configuration
            if cluster_config is None:
                cluster_config = self._get_default_cluster_config()

            # Create main cluster directory
            cluster_path.mkdir(parents=True, exist_ok=True)

            # Create component directories with config subfolders and files
            created_folders = []
            created_files = []

            for component, description in self.components.items():
                component_path = cluster_path / component
                component_path.mkdir(exist_ok=True)

                for config_folder in self.config_folders:
                    config_path = component_path / config_folder
                    config_path.mkdir(exist_ok=True)
                    created_folders.append(str(config_path))

                    # Create configuration files for default folder
                    if config_folder == 'default':
                        files = self._create_component_configs(component, config_path, cluster_config)
                        created_files.extend(files)

            # Create cluster documentation
            self._create_cluster_documentation(cluster_path, cluster_name, cluster_config)

            # Create cluster metadata file
            metadata = {
                'cluster_name': cluster_name,
                'created_at': datetime.now().isoformat(),
                'components': self.components,
                'config_folders': self.config_folders,
                'total_folders': len(created_folders),
                'total_files': len(created_files),
                'cluster_config': cluster_config,
                'version': '2.0.0',
                'shc_enabled': True,
                'shc_config': {
                    'label': f'sh-{cluster_name}',
                    'replication_port': 8181,
                    'replication_factor': 2,
                    'site': 'site1'
                }
            }

            metadata_file = cluster_path / 'cluster.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Created enhanced cluster structure for '{cluster_name}' with {len(created_folders)} folders and {len(created_files)} files")

            # Create SHC setup instructions
            shc_instructions = self._create_shc_setup_instructions(cluster_name, cluster_config)
            self._create_file(cluster_path / 'SHC_SETUP.md', shc_instructions)

            return {
                'success': True,
                'cluster_name': cluster_name,
                'cluster_path': str(cluster_path),
                'created_folders': created_folders,
                'created_files': created_files,
                'metadata': metadata,
                'shc_instructions': 'SHC_SETUP.md'
            }

        except Exception as e:
            logger.error(f"Failed to create cluster structure for '{cluster_name}': {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_default_cluster_config(self) -> Dict[str, Any]:
        """Get default cluster configuration parameters"""
        return {
            'replication_factor': 3,
            'search_factor': 2,
            'cluster_label': 'production_cluster',
            'security_key': self.default_pass_key,
            'ssl_enabled': True,
            'indexer_discovery_enabled': True,
            'monitoring_console_enabled': True,
            'deployment_server_enabled': True,
            'search_head_clustering_enabled': True,
            'data_retention_days': 90,
            'hot_bucket_time_hours': 24,
            'warm_bucket_time_days': 30,
            'cold_bucket_time_days': 60,
            'license_pool': 'enterprise',
            'environment': 'production'
        }

    def _create_component_configs(self, component: str, config_path: Path, 
                                cluster_config: Dict[str, Any]) -> List[str]:
        """Create comprehensive configuration files for a component"""
        created_files = []

        try:
            if component not in self.config_files:
                return created_files

            for config_file in self.config_files[component]:
                file_content = self._get_config_content(component, config_file, cluster_config)
                if file_content:
                    file_path = config_path / config_file
                    self._create_file(file_path, file_content)
                    created_files.append(str(file_path))

        except Exception as e:
            logger.warning(f"Failed to create configs for {component}: {str(e)}")

        return created_files

    def _create_file(self, file_path: Path, content: str):
        """Create a file with the given content"""
        try:
            with open(file_path, 'w') as f:
                f.write(content)
        except Exception as e:
            logger.warning(f"Failed to create file {file_path}: {str(e)}")

    def _create_cluster_documentation(self, cluster_path: Path, cluster_name: str, 
                                    cluster_config: Dict[str, Any]):
        """Create comprehensive cluster documentation"""
        try:
            docs_path = cluster_path / 'documentation'
            docs_path.mkdir(exist_ok=True)

            # Create README
            readme_content = self._get_readme_content(cluster_name, cluster_config)
            self._create_file(docs_path / 'README.md', readme_content)

            # Create deployment guide
            deploy_guide = self._get_deployment_guide_content(cluster_name, cluster_config)
            self._create_file(docs_path / 'DEPLOYMENT_GUIDE.md', deploy_guide)

            # Create troubleshooting guide
            troubleshoot_guide = self._get_troubleshooting_guide_content()
            self._create_file(docs_path / 'TROUBLESHOOTING.md', troubleshoot_guide)

        except Exception as e:
            logger.warning(f"Failed to create documentation: {str(e)}")

    def _get_config_content(self, component: str, config_file: str, 
                          cluster_config: Dict[str, Any]) -> str:
        """Get configuration content for a specific component and file"""

        # Universal Forwarder configurations
        if component == 'uf':
            if config_file == 'inputs.conf':
                return self._get_uf_inputs_conf(cluster_config)
            elif config_file == 'outputs.conf':
                return self._get_uf_outputs_conf(cluster_config)
            elif config_file == 'deploymentclient.conf':
                return self._get_uf_deploymentclient_conf(cluster_config)
            elif config_file == 'limits.conf':
                return self._get_uf_limits_conf(cluster_config)
        
        # Heavy Forwarder configurations
        elif component == 'hf':
            if config_file == 'inputs.conf':
                return self._get_hf_inputs_conf(cluster_config)
            elif config_file == 'outputs.conf':
                return self._get_hf_outputs_conf(cluster_config)
            elif config_file == 'props.conf':
                return self._get_hf_props_conf(cluster_config)
            elif config_file == 'transforms.conf':
                return self._get_hf_transforms_conf(cluster_config)
            elif config_file == 'server.conf':
                return self._get_hf_server_conf(cluster_config)
            elif config_file == 'limits.conf':
                return self._get_hf_limits_conf(cluster_config)
        
        # Cluster Manager configurations
        elif component == 'cm':
            if config_file == 'server.conf':
                return self._get_cm_server_conf(cluster_config)
            elif config_file == 'indexes.conf':
                return self._get_cm_indexes_conf(cluster_config)
            elif config_file == 'authorize.conf':
                return self._get_cm_authorize_conf(cluster_config)
            elif config_file == 'authentication.conf':
                return self._get_cm_authentication_conf(cluster_config)
            elif config_file == 'web.conf':
                return self._get_cm_web_conf(cluster_config)
            elif config_file == 'limits.conf':
                return self._get_cm_limits_conf(cluster_config)
            elif config_file == 'distsearch.conf':
                return self._get_cm_distsearch_conf(cluster_config)
        
        # Indexer configurations
        elif component == 'idx':
            if config_file == 'server.conf':
                return self._get_idx_server_conf(cluster_config)
            elif config_file == 'indexes.conf':
                return self._get_idx_indexes_conf(cluster_config)
            elif config_file == 'inputs.conf':
                return self._get_idx_inputs_conf(cluster_config)
            elif config_file == 'props.conf':
                return self._get_idx_props_conf(cluster_config)
            elif config_file == 'transforms.conf':
                return self._get_idx_transforms_conf(cluster_config)
            elif config_file == 'limits.conf':
                return self._get_idx_limits_conf(cluster_config)
            elif config_file == 'authorize.conf':
                return self._get_idx_authorize_conf(cluster_config)
            elif config_file == 'authentication.conf':
                return self._get_idx_authentication_conf(cluster_config)
        
        # Search Head configurations
        elif component == 'sh':
            if config_file == 'server.conf':
                return self._get_sh_server_conf(cluster_config)
            elif config_file == 'distsearch.conf':
                return self._get_sh_distsearch_conf(cluster_config)
            elif config_file == 'authorize.conf':
                return self._get_sh_authorize_conf(cluster_config)
            elif config_file == 'authentication.conf':
                return self._get_sh_authentication_conf(cluster_config)
            elif config_file == 'web.conf':
                return self._get_sh_web_conf(cluster_config)
            elif config_file == 'limits.conf':
                return self._get_sh_limits_conf(cluster_config)
            elif config_file == 'ui-prefs.conf':
                return self._get_sh_ui_prefs_conf(cluster_config)
            elif config_file == 'shcluster.conf':
                return self._get_sh_shcluster_conf(cluster_config)
        
        # Deployer configurations
        elif component == 'deployer':
            if config_file == 'server.conf':
                return self._get_deployer_server_conf(cluster_config)
            elif config_file == 'authorize.conf':
                return self._get_deployer_authorize_conf(cluster_config)
            elif config_file == 'authentication.conf':
                return self._get_deployer_authentication_conf(cluster_config)
            elif config_file == 'web.conf':
                return self._get_deployer_web_conf(cluster_config)
            elif config_file == 'shcluster.conf':
                return self._get_deployer_shcluster_conf(cluster_config)
        
        # Deployment Server configurations
        elif component == 'ds':
            if config_file == 'server.conf':
                return self._get_ds_server_conf(cluster_config)
            elif config_file == 'serverclass.conf':
                return self._get_ds_serverclass_conf(cluster_config)
            elif config_file == 'authorize.conf':
                return self._get_ds_authorize_conf(cluster_config)
            elif config_file == 'authentication.conf':
                return self._get_ds_authentication_conf(cluster_config)
            elif config_file == 'web.conf':
                return self._get_ds_web_conf(cluster_config)
        
        # License Master configurations
        elif component == 'lm':
            if config_file == 'server.conf':
                return self._get_lm_server_conf(cluster_config)
            elif config_file == 'authorize.conf':
                return self._get_lm_authorize_conf(cluster_config)
            elif config_file == 'authentication.conf':
                return self._get_lm_authentication_conf(cluster_config)
            elif config_file == 'web.conf':
                return self._get_lm_web_conf(cluster_config)
        
        # Monitoring Console configurations
        elif component == 'mc':
            if config_file == 'server.conf':
                return self._get_mc_server_conf(cluster_config)
            elif config_file == 'authorize.conf':
                return self._get_mc_authorize_conf(cluster_config)
            elif config_file == 'authentication.conf':
                return self._get_mc_authentication_conf(cluster_config)
            elif config_file == 'web.conf':
                return self._get_mc_web_conf(cluster_config)
            elif config_file == 'distsearch.conf':
                return self._get_mc_distsearch_conf(cluster_config)
        
        # If no specific configuration is found, return None to skip file creation
        return None

    # Enhanced configuration templates based on production best practices

    def _get_cm_server_conf(self, config: Dict[str, Any]) -> str:
        """Cluster Manager server.conf with minimal essential settings"""
        return f"""# Splunk Cluster Manager Configuration
# Generated: {datetime.now().isoformat()}

[general]
serverName = cluster-manager-{config.get('cluster_label', 'prod')}
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

[clustering]
mode = manager
replication_factor = {config.get('replication_factor', 3)}
search_factor = {config.get('search_factor', 2)}
pass4SymmKey = {config.get('security_key', self.default_pass_key)}
cluster_label = {config.get('cluster_label', 'production_cluster')}

[indexer_discovery]
pass4SymmKey = {config.get('security_key', self.default_pass_key)}
polling_rate = 10
disabled = 0

[httpServer]
max_threads = 50
max_sockets = 50

[web]
startwebserver = 1
httpport = 8000
"""

    def _get_cm_authorize_conf(self, config: Dict[str, Any]) -> str:
        """Cluster Manager authorize.conf with minimal valid settings"""
        return f"""# Splunk Cluster Manager Authorization Configuration
# Generated: {datetime.now().isoformat()}

[role_admin]
srchIndexesDefault = *
srchIndexesAllowed = *
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1

[role_power]
srchIndexesDefault = main
srchIndexesAllowed = main, _internal, _audit
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1

[role_user]
srchIndexesDefault = main
srchIndexesAllowed = main
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1
"""

    def _get_cm_authentication_conf(self, config: Dict[str, Any]) -> str:
        """Cluster Manager authentication.conf with minimal valid settings"""
        return f"""# Splunk Cluster Manager Authentication Configuration
# Generated: {datetime.now().isoformat()}

[authentication]
authType = Splunk
authSettings = LDAP

[roleMap_Splunk]
admin = admin
power = power
user = user
"""

    def _get_cm_web_conf(self, config: Dict[str, Any]) -> str:
        """Cluster Manager web.conf with minimal valid settings"""
        return f"""# Splunk Cluster Manager Web Configuration
# Generated: {datetime.now().isoformat()}

[settings]
enableSplunkWeb = 1
"""

    def _get_cm_limits_conf(self, config: Dict[str, Any]) -> str:
        """Cluster Manager limits.conf with minimal valid settings"""
        return f"""# Splunk Cluster Manager Limits Configuration
# Generated: {datetime.now().isoformat()}

[thruput]
maxKBps = 0

[search]
max_searches_per_cpu = 0
"""

    def _get_cm_distsearch_conf(self, config: Dict[str, Any]) -> str:
        """Cluster Manager distsearch.conf with minimal valid settings"""
        return f"""# Splunk Cluster Manager Distributed Search Configuration
# Generated: {datetime.now().isoformat()}

[distributedSearch]
servers = *
"""

    def _get_cm_indexes_conf(self, config: Dict[str, Any]) -> str:
        """Cluster Manager indexes.conf with minimal essential indexes"""
        return f"""# Splunk Indexes Configuration for Cluster Manager
# Generated: {datetime.now().isoformat()}

[default]
repFactor = 0
maxHotBuckets = 10
maxWarmDBCount = 300
maxTotalDataSizeMB = 500000
maxDataSize = auto_high_volume
homePath = $SPLUNK_DB/$_index_name/db
coldPath = $SPLUNK_DB/$_index_name/colddb
thawedPath = $SPLUNK_DB/$_index_name/thaweddb

[main]
repFactor = 0
homePath = $SPLUNK_DB/main/db
coldPath = $SPLUNK_DB/main/colddb
thawedPath = $SPLUNK_DB/main/thaweddb
maxDataSize = auto_high_volume

[_internal]
repFactor = 0
homePath = $SPLUNK_DB/_internal/db
coldPath = $SPLUNK_DB/_internal/colddb
thawedPath = $SPLUNK_DB/_internal/thaweddb
maxDataSize = 1000

[_audit]
repFactor = 0
homePath = $SPLUNK_DB/_audit/db
coldPath = $SPLUNK_DB/_audit/colddb
thawedPath = $SPLUNK_DB/_audit/thaweddb
maxDataSize = 1000

[security]
repFactor = 0
homePath = $SPLUNK_DB/security/db
coldPath = $SPLUNK_DB/security/colddb
thawedPath = $SPLUNK_DB/security/thaweddb
maxDataSize = auto_high_volume

[network]
repFactor = 0
homePath = $SPLUNK_DB/network/db
coldPath = $SPLUNK_DB/network/colddb
thawedPath = $SPLUNK_DB/network/thaweddb
maxDataSize = auto_high_volume

[infrastructure]
repFactor = 0
homePath = $SPLUNK_DB/infrastructure/db
coldPath = $SPLUNK_DB/infrastructure/colddb
thawedPath = $SPLUNK_DB/infrastructure/thaweddb
maxDataSize = auto_high_volume

[application]
repFactor = 0
homePath = $SPLUNK_DB/application/db
coldPath = $SPLUNK_DB/application/colddb
thawedPath = $SPLUNK_DB/application/thaweddb
maxDataSize = auto_high_volume
"""

    def _get_idx_server_conf(self, config: Dict[str, Any]) -> str:
        """Indexer server.conf with minimal essential settings"""
        return f"""# Splunk Indexer/Peer Node Configuration
# Generated: {datetime.now().isoformat()}

[general]
serverName = indexer-peer-{config.get('cluster_label', 'prod')}
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

[clustering]
manager_uri = https://cluster-manager:8089
mode = peer
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

[replication_port://9887]
disabled = 0

[httpServer]
max_threads = 50
max_sockets = 50

[web]
startwebserver = 0
"""

    def _get_idx_inputs_conf(self, config: Dict[str, Any]) -> str:
        """Indexer inputs.conf for receiving data"""
        return f"""# Indexer Inputs Configuration
# Generated: {datetime.now().isoformat()}

# TCP input for receiving forwarded data
[tcp://9997]
disabled = false
connection_host = ip
sourcetype = tcp:9997
index = main

# SSL TCP input
[tcp-ssl://9998]
disabled = false
connection_host = ip
sourcetype = tcp-ssl:9998
index = main
sslPassword = {config.get('security_key', self.default_pass_key)}
sslCertPath = $SPLUNK_HOME/etc/auth/server.pem
sslRootCAPath = $SPLUNK_HOME/etc/auth/ca.pem

# UDP input for syslog
[udp://514]
disabled = false
connection_host = ip
sourcetype = syslog
index = network

# HTTP Event Collector
[http]
disabled = false
port = 8088
enableSSL = {str(config.get('ssl_enabled', True)).lower()}
sslPassword = {config.get('security_key', self.default_pass_key)}
sslCertPath = $SPLUNK_HOME/etc/auth/server.pem
sslRootCAPath = $SPLUNK_HOME/etc/auth/ca.pem
"""

    def _get_idx_props_conf(self, config: Dict[str, Any]) -> str:
        """Indexer props.conf with field extractions"""
        return f"""# Indexer Props Configuration
# Generated: {datetime.now().isoformat()}

[default]
TRUNCATE = 10000
MAX_TIMESTAMP_LOOKAHEAD = 128
SHOULD_LINEMERGE = true
BREAK_ONLY_BEFORE = ^\d{{4}}-\d{{2}}-\d{{2}}
TIME_FORMAT = %Y-%m-%d %H:%M:%S
TIME_PREFIX = ^
MAX_EVENTS = 1000

[syslog]
SHOULD_LINEMERGE = false
BREAK_ONLY_BEFORE = ^\w{{3}}\s+\d{{1,2}}\s+\d{{2}}:\d{{2}}:\d{{2}}
TIME_FORMAT = %b %d %H:%M:%S
TIME_PREFIX = ^
MAX_EVENTS = 1000

[tcp:9997]
SHOULD_LINEMERGE = true
BREAK_ONLY_BEFORE = ^\d{{4}}-\d{{2}}-\d{{2}}
TIME_FORMAT = %Y-%m-%d %H:%M:%S
TIME_PREFIX = ^
MAX_EVENTS = 1000

[tcp-ssl:9998]
SHOULD_LINEMERGE = true
BREAK_ONLY_BEFORE = ^\d{{4}}-\d{{2}}-\d{{2}}
TIME_FORMAT = %Y-%m-%d %H:%M:%S
TIME_PREFIX = ^
MAX_EVENTS = 1000
"""

    def _get_idx_transforms_conf(self, config: Dict[str, Any]) -> str:
        """Indexer transforms.conf with data transformations"""
        return f"""# Indexer Transforms Configuration
# Generated: {datetime.now().isoformat()}

# Common field extractions
[extract_ip_addresses]
REGEX = (?<ip_address>\d+\.\d+\.\d+\.\d+)
FORMAT = ip_address::$1

[extract_timestamps]
REGEX = (\d{{4}}-\d{{2}}-\d{{2}}\s+\d{{2}}:\d{{2}}:\d{{2}})
FORMAT = extracted_time::$1

# Security transformations
[extract_failed_logins]
REGEX = (failed|failure|invalid).*login
FORMAT = failed_login::true

[extract_suspicious_commands]
REGEX = (sudo|su|passwd|chmod|chown|rm\s+-rf)
FORMAT = suspicious_command::$1

# Network transformations
[extract_src_dest]
REGEX = src=([^\s]+)\s+dest=([^\s]+)
FORMAT = src_ip::$1 dest_ip::$2

[normalize_protocols]
REGEX = proto=([^\s]+)
FORMAT = protocol::$1
"""

    def _get_idx_limits_conf(self, config: Dict[str, Any]) -> str:
        """Indexer limits.conf with minimal valid settings"""
        return f"""# Indexer Limits Configuration
# Generated: {datetime.now().isoformat()}

[thruput]
maxKBps = 0

[search]
max_searches_per_cpu = 0
"""

    def _get_idx_authorize_conf(self, config: Dict[str, Any]) -> str:
        """Indexer authorize.conf with minimal valid settings"""
        return f"""# Indexer Authorization Configuration
# Generated: {datetime.now().isoformat()}

[role_indexer]
srchIndexesDefault = main
srchIndexesAllowed = *
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1
"""

    def _get_idx_authentication_conf(self, config: Dict[str, Any]) -> str:
        """Indexer authentication.conf with minimal valid settings"""
        return f"""# Indexer Authentication Configuration
# Generated: {datetime.now().isoformat()}

[authentication]
authType = Splunk
authSettings = LDAP
"""

    def _get_idx_indexes_conf(self, config: Dict[str, Any]) -> str:
        """Indexer indexes.conf with minimal essential indexes"""
        return f"""# Indexer Indexes Configuration
# Generated: {datetime.now().isoformat()}

[default]
repFactor = 0
maxHotBuckets = 10
maxWarmDBCount = 300
maxTotalDataSizeMB = 500000
maxDataSize = auto_high_volume
homePath = $SPLUNK_DB/$_index_name/db
coldPath = $SPLUNK_DB/$_index_name/colddb
thawedPath = $SPLUNK_DB/$_index_name/thaweddb

[main]
repFactor = 0
homePath = $SPLUNK_DB/main/db
coldPath = $SPLUNK_DB/main/colddb
thawedPath = $SPLUNK_DB/main/thaweddb
maxDataSize = auto_high_volume

[_internal]
repFactor = 0
homePath = $SPLUNK_DB/_internal/db
coldPath = $SPLUNK_DB/_internal/colddb
thawedPath = $SPLUNK_DB/_internal/thaweddb
maxDataSize = 1000

[_audit]
repFactor = 0
homePath = $SPLUNK_DB/_audit/db
coldPath = $SPLUNK_DB/_audit/colddb
thawedPath = $SPLUNK_DB/_audit/thaweddb
maxDataSize = 1000

[security]
repFactor = 0
homePath = $SPLUNK_DB/security/db
coldPath = $SPLUNK_DB/security/colddb
thawedPath = $SPLUNK_DB/security/thaweddb
maxDataSize = auto_high_volume

[network]
repFactor = 0
homePath = $SPLUNK_DB/network/db
coldPath = $SPLUNK_DB/network/colddb
thawedPath = $SPLUNK_DB/network/thaweddb
maxDataSize = auto_high_volume

[infrastructure]
repFactor = 0
homePath = $SPLUNK_DB/infrastructure/db
coldPath = $SPLUNK_DB/infrastructure/colddb
thawedPath = $SPLUNK_DB/infrastructure/thaweddb
maxDataSize = auto_high_volume

[application]
repFactor = 0
homePath = $SPLUNK_DB/application/db
coldPath = $SPLUNK_DB/application/colddb
thawedPath = $SPLUNK_DB/application/thaweddb
maxDataSize = auto_high_volume
"""

    def _get_sh_server_conf(self, config: Dict[str, Any]) -> str:
        """Search Head server.conf with proper SHC configuration"""
        return f"""# Splunk Search Head Configuration for Search Head Clustering
# Generated: {datetime.now().isoformat()}
# Template: Uses dynamic variables for multiple search head instances

[general]
site = site1
serverName = {{{{SERVER_NAME}}}}
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

[license]
manager_uri = https://13.61.123.93:8089

[shclustering]
shcluster_label = {config.get('cluster_label', 'prod')}-shc
pass4SymmKey = {config.get('security_key', self.default_pass_key)}
replication_port = 8181
conf_deploy_fetch_url = https://{{{{DEPLOYER_IP}}}}:8089
mgmt_uri = {{{{MGMT_URI}}}}

# SSL Configuration - Commented out until certificates are properly configured
# [sslConfig]
# enableSplunkdSSL = {str(config.get('ssl_enabled', True)).lower()}
# sslPassword = {config.get('security_key', self.default_pass_key)}
# serverCert = $SPLUNK_HOME/etc/auth/server.pem
# sslVersions = tls1.2
# sslVersionsForClient = tls1.2

[httpServer]
max_threads = 100
max_sockets = 100

# Web interface configuration
[web]
enableSplunkWebSSL = false
startwebserver = 1
httpport = 8000
"""

    def _get_sh_authorize_conf(self, config: Dict[str, Any]) -> str:
        """Search Head authorize.conf with role-based access"""
        return f"""# Splunk Search Head Authorization Configuration
# Generated: {datetime.now().isoformat()}

[role_admin]
srchIndexesDefault = *
srchIndexesAllowed = *
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1

[role_power]
srchIndexesDefault = main
srchIndexesAllowed = main, _internal, _audit
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1

[role_user]
srchIndexesDefault = main
srchIndexesAllowed = main
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1
"""

    def _get_sh_authentication_conf(self, config: Dict[str, Any]) -> str:
        """Search Head authentication.conf with security settings"""
        return f"""# Splunk Search Head Authentication Configuration
# Generated: {datetime.now().isoformat()}

[authentication]
authType = Splunk
authSettings = LDAP

[roleMap_Splunk]
admin = admin
power = power
user = user
"""

    def _get_sh_web_conf(self, config: Dict[str, Any]) -> str:
        """Search Head web.conf with web interface settings"""
        return f"""# Splunk Search Head Web Configuration
# Generated: {datetime.now().isoformat()}

[settings]
enableSplunkWebSSL = false
startwebserver = 1
httpport = 8000
enableSplunkWeb = 1
login_content = Welcome to Splunk Search Head
appServerPorts = 8065
"""

    def _get_sh_limits_conf(self, config: Dict[str, Any]) -> str:
        """Search Head limits.conf with production settings"""
        return f"""# Splunk Search Head Limits Configuration
# Generated: {datetime.now().isoformat()}

[thruput]
maxKBps = 0

[search]
max_searches_per_cpu = 0

[realtime_search]
max_realtime_search_users = 0

[search_process]
max_search_processes = 0

[search_scheduler]
max_searches_per_cpu = 0

[search_artifacts]
max_search_artifacts = 0

[search_parser]
max_search_parser_errors = 0
"""

    def _get_sh_ui_prefs_conf(self, config: Dict[str, Any]) -> str:
        """Search Head ui-prefs.conf with user interface preferences"""
        return f"""# Splunk Search Head UI Preferences Configuration
# Generated: {datetime.now().isoformat()}

[general]
default_namespace = search
default_earliest_time = -15m
default_latest_time = now
search_use_advanced_editor = 1
search_auto_format = 1
search_line_numbers = 1
search_show_field_sidebar = 1
search_show_timeline = 1
search_show_event_summary = 1
search_show_event_actions = 1
search_show_event_details = 1
search_show_event_metadata = 1
search_show_event_raw = 1
search_show_event_annotations = 1
search_show_event_notes = 1
search_show_event_highlights = 1
search_show_event_links = 1
search_show_event_related = 1
search_show_event_children = 1
search_show_event_parents = 1
search_show_event_siblings = 1
search_show_event_ancestors = 1
search_show_event_descendants = 1
search_show_event_tree = 1
search_show_event_graph = 1
search_show_event_map = 1
search_show_event_timeline = 1
search_show_event_summary = 1
search_show_event_actions = 1
search_show_event_details = 1
search_show_event_metadata = 1
search_show_event_raw = 1
search_show_event_annotations = 1
search_show_event_notes = 1
search_show_event_highlights = 1
search_show_event_links = 1
search_show_event_related = 1
search_show_event_children = 1
search_show_event_parents = 1
search_show_event_siblings = 1
search_show_event_ancestors = 1
search_show_event_descendants = 1
search_show_event_tree = 1
search_show_event_graph = 1
search_show_event_map = 1
search_show_event_timeline = 1
"""

    def _get_uf_outputs_conf(self, config: Dict[str, Any]) -> str:
        """Universal Forwarder outputs.conf with indexer discovery"""
        return f"""# Universal Forwarder Outputs Configuration
# Generated: {datetime.now().isoformat()}

[tcpout]
defaultGroup = cluster_indexers
indexAndForward = false
useACK = true

[tcpout:cluster_indexers]
# Indexer Discovery enabled
indexerDiscovery = cluster_manager
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

# SSL Configuration - Commented out until certificates are properly configured
# useSSL = {str(config.get('ssl_enabled', True)).lower()}
# sslPassword = {config.get('security_key', self.default_pass_key)}
# sslCertPath = $SPLUNK_HOME/etc/auth/server.pem
# sslRootCAPath = $SPLUNK_HOME/etc/auth/ca.pem
# sslVerifyServerCert = false

# Performance tuning
maxQueueSize = 100MB
dropEventsOnQueueFull = 10
compressed = true

[indexer_discovery:cluster_manager]
pass4SymmKey = {config.get('security_key', self.default_pass_key)}
manager_uri = https://cluster-manager:8089

# Heartbeat settings
heartbeat_frequency = 30
"""

    def _get_uf_inputs_conf(self, config: Dict[str, Any]) -> str:
        """Universal Forwarder inputs.conf with production monitoring"""
        return f"""# Universal Forwarder Inputs Configuration
# Generated: {datetime.now().isoformat()}

# System monitoring inputs
[monitor:///var/log]
disabled = false
sourcetype = linux_syslog
index = infrastructure

[monitor:///var/log/messages]
disabled = false
sourcetype = linux_syslog
index = infrastructure

[monitor:///var/log/secure]
disabled = false
sourcetype = linux_secure
index = security

[monitor:///var/log/audit/audit.log]
disabled = false
sourcetype = linux_audit
index = security

# Network monitoring
[udp://514]
disabled = false
sourcetype = syslog
index = network

# File monitoring with proper sourcetype detection
[monitor:///var/log/*.log]
disabled = false
sourcetype = linux_syslog
index = infrastructure

# Performance monitoring
[script://./bin/df.sh]
disabled = false
interval = 300
sourcetype = df
index = infrastructure

[script://./bin/ps.sh]
disabled = false
interval = 300
sourcetype = ps
index = infrastructure

# Custom application logs (customize as needed)
[monitor:///opt/app/logs/*.log]
disabled = false
sourcetype = application
index = application
"""

    def _get_uf_deploymentclient_conf(self, config: Dict[str, Any]) -> str:
        """Universal Forwarder deploymentclient.conf for cluster deployment"""
        return f"""# Universal Forwarder Deployment Client Configuration
# Generated: {datetime.now().isoformat()}

[deployment-client]
# Deployment server configuration
clientName = {config.get('cluster_label', 'production')}-uf-$(hostname)
targetUri = https://deployment-server:8089

# SSL Configuration
useSSL = {str(config.get('ssl_enabled', True)).lower()}
sslPassword = {config.get('security_key', self.default_pass_key)}
sslCertPath = $SPLUNK_HOME/etc/auth/server.pem
sslRootCAPath = $SPLUNK_HOME/etc/auth/ca.pem
sslVerifyServerCert = false

# Deployment settings
repositoryLocation = $SPLUNK_HOME/etc/deployment-apps
stateOnClient = enabled
checkForUpdates = true
checkForUpdatesInterval = 60

# App deployment settings
deploymentServer = https://deployment-server:8089
phoneHomeIntervalInSecs = 60
"""

    def _get_uf_limits_conf(self, config: Dict[str, Any]) -> str:
        """Universal Forwarder limits.conf with production settings"""
        return f"""# Universal Forwarder Limits Configuration
# Generated: {datetime.now().isoformat()}

[thruput]
maxKBps = 0

[search]
max_searches_per_cpu = 0

[realtime_search]
max_realtime_search_users = 0

[search_process]
max_search_processes = 0

[search_scheduler]
max_searches_per_cpu = 0

[search_artifacts]
max_search_artifacts = 0

[search_parser]
max_search_parser_errors = 0

[search_parser_errors]
max_search_parser_errors = 0

[search_parser_errors_per_search]
max_search_parser_errors_per_search = 0

[search_parser_errors_per_search_per_second]
max_search_parser_errors_per_search_per_second = 0

[search_parser_errors_per_search_per_second_per_host]
max_search_parser_errors_per_search_per_second_per_host = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field_per_value]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field_per_value = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field_per_value_per_other]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field_per_value_per_other = 0
"""

    def _get_hf_transforms_conf(self, config: Dict[str, Any]) -> str:
        """Heavy Forwarder transforms.conf with common transformations"""
        return f"""# Heavy Forwarder Transforms Configuration
# Generated: {datetime.now().isoformat()}

# Common field extractions and transformations
[extract_ip_addresses]
REGEX = (?<ip_address>\d+\.\d+\.\d+\.\d+)
FORMAT = ip_address::$1

[extract_timestamps]
REGEX = (\d{{4}}-\d{{2}}-\d{{2}}\s+\d{{2}}:\d{{2}}:\d{{2}})
FORMAT = extracted_time::$1

[mask_credit_cards]
REGEX = (\d{{4}}-?\d{{4}}-?\d{{4}}-?)(\d{{4}})
FORMAT = $1****
DEST_KEY = _raw

[extract_user_agents]
REGEX = User-Agent:\s*([^\r\n]*)
FORMAT = user_agent::$1

[extract_status_codes]
REGEX = \s(\d{{3}})\s
FORMAT = status_code::$1

# Security-focused transformations
[extract_failed_logins]
REGEX = (failed|failure|invalid).*login
FORMAT = failed_login::true

[extract_suspicious_commands]
REGEX = (sudo|su|passwd|chmod|chown|rm\s+-rf)
FORMAT = suspicious_command::$1

# Network transformations
[extract_src_dest]
REGEX = src=([^\s]+)\s+dest=([^\s]+)
FORMAT = src_ip::$1 dest_ip::$2

[normalize_protocols]
REGEX = proto=([^\s]+)
FORMAT = protocol::$1
"""

    def _get_hf_inputs_conf(self, config: Dict[str, Any]) -> str:
        """Heavy Forwarder inputs.conf with advanced monitoring"""
        return f"""# Heavy Forwarder Inputs Configuration
# Generated: {datetime.now().isoformat()}

# System monitoring inputs
[monitor:///var/log]
disabled = false
sourcetype = linux_syslog
index = infrastructure

[monitor:///var/log/messages]
disabled = false
sourcetype = linux_syslog
index = infrastructure

[monitor:///var/log/secure]
disabled = false
sourcetype = linux_secure
index = security

[monitor:///var/log/audit/audit.log]
disabled = false
sourcetype = linux_audit
index = security

# Network monitoring
[udp://514]
disabled = false
sourcetype = syslog
index = network

[tcp://514]
disabled = false
sourcetype = syslog
index = network

# File monitoring with proper sourcetype detection
[monitor:///var/log/*.log]
disabled = false
sourcetype = linux_syslog
index = infrastructure

# Performance monitoring
[script://./bin/df.sh]
disabled = false
interval = 300
sourcetype = df
index = infrastructure

[script://./bin/ps.sh]
disabled = false
interval = 300
sourcetype = ps
index = infrastructure

[script://./bin/netstat.sh]
disabled = false
interval = 300
sourcetype = netstat
index = infrastructure

# Custom application logs (customize as needed)
[monitor:///opt/app/logs/*.log]
disabled = false
sourcetype = application
index = application

# Database monitoring
[monitor:///var/log/mysql/*.log]
disabled = false
sourcetype = mysql
index = application

[monitor:///var/log/postgresql/*.log]
disabled = false
sourcetype = postgresql
index = application

# Web server monitoring
[monitor:///var/log/nginx/*.log]
disabled = false
sourcetype = nginx
index = application

[monitor:///var/log/apache2/*.log]
disabled = false
sourcetype = apache
index = application
"""

    def _get_hf_outputs_conf(self, config: Dict[str, Any]) -> str:
        """Heavy Forwarder outputs.conf with load balancing"""
        return f"""# Heavy Forwarder Outputs Configuration
# Generated: {datetime.now().isoformat()}

[tcpout]
defaultGroup = cluster_indexers
indexAndForward = false
useACK = true

[tcpout:cluster_indexers]
# Indexer Discovery enabled
indexerDiscovery = cluster_manager
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

# SSL Configuration - Commented out until certificates are properly configured
# useSSL = {str(config.get('ssl_enabled', True)).lower()}
# sslPassword = {config.get('security_key', self.default_pass_key)}
# sslCertPath = $SPLUNK_HOME/etc/auth/server.pem
# sslRootCAPath = $SPLUNK_HOME/etc/auth/ca.pem
# sslVerifyServerCert = false

# Performance tuning
maxQueueSize = 100MB
dropEventsOnQueueFull = 10
compressed = true

# Load balancing
loadBalanced = true
autoLB = true
autoLBFrequency = 30

[indexer_discovery:cluster_manager]
pass4SymmKey = {config.get('security_key', self.default_pass_key)}
manager_uri = https://cluster-manager:8089

# Heartbeat settings
heartbeat_frequency = 30
"""

    def _get_hf_props_conf(self, config: Dict[str, Any]) -> str:
        """Heavy Forwarder props.conf with field extractions"""
        return f"""# Heavy Forwarder Props Configuration
# Generated: {datetime.now().isoformat()}

# Default settings
[default]
TRUNCATE = 10000
MAX_TIMESTAMP_LOOKAHEAD = 128
SHOULD_LINEMERGE = true
BREAK_ONLY_BEFORE = ^\d{{4}}-\d{{2}}-\d{{2}}
TIME_FORMAT = %Y-%m-%d %H:%M:%S
TIME_PREFIX = ^
MAX_EVENTS = 1000

# Linux syslog
[linux_syslog]
SHOULD_LINEMERGE = true
BREAK_ONLY_BEFORE = ^\w{{3}}\s+\d{{1,2}}\s+\d{{2}}:\d{{2}}:\d{{2}}
TIME_FORMAT = %b %d %H:%M:%S
TIME_PREFIX = ^
MAX_EVENTS = 1000

# Apache logs
[apache]
SHOULD_LINEMERGE = false
BREAK_ONLY_BEFORE = ^\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}
TIME_FORMAT = %d/%b/%Y:%H:%M:%S %z
TIME_PREFIX = \[
MAX_EVENTS = 1000

# MySQL logs
[mysql]
SHOULD_LINEMERGE = true
BREAK_ONLY_BEFORE = ^\d{{4}}-\d{{2}}-\d{{2}}
TIME_FORMAT = %Y-%m-%d %H:%M:%S
TIME_PREFIX = ^
MAX_EVENTS = 1000

# Network logs
[network]
SHOULD_LINEMERGE = false
BREAK_ONLY_BEFORE = ^\d{{4}}-\d{{2}}-\d{{2}}
TIME_FORMAT = %Y-%m-%d %H:%M:%S
TIME_PREFIX = ^
MAX_EVENTS = 1000
"""

    def _get_hf_server_conf(self, config: Dict[str, Any]) -> str:
        """Heavy Forwarder server.conf with production settings"""
        return f"""# Heavy Forwarder Server Configuration
# Generated: {datetime.now().isoformat()}

[general]
serverName = heavy-forwarder-{config.get('cluster_label', 'prod')}
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

[license]
manager_uri = https://license-master:8089

# SSL Configuration - Commented out until certificates are properly configured
# [sslConfig]
# enableSplunkdSSL = {str(config.get('ssl_enabled', True)).lower()}
# sslPassword = {config.get('security_key', self.default_pass_key)}
# serverCert = $SPLUNK_HOME/etc/auth/server.pem
# sslVersions = tls1.2
# sslVersionsForClient = tls1.2

[httpServer]
max_threads = 50
max_sockets = 50

# Web interface configuration
[web]
enableSplunkWebSSL = false
startwebserver = 0
"""

    def _get_hf_limits_conf(self, config: Dict[str, Any]) -> str:
        """Heavy Forwarder limits.conf with production settings"""
        return f"""# Heavy Forwarder Limits Configuration
# Generated: {datetime.now().isoformat()}

[thruput]
maxKBps = 0

[search]
max_searches_per_cpu = 0

[realtime_search]
max_realtime_search_users = 0

[search_process]
max_search_processes = 0

[search_scheduler]
max_searches_per_cpu = 0

[search_artifacts]
max_search_artifacts = 0

[search_parser]
max_search_parser_errors = 0

[search_parser_errors]
max_search_parser_errors = 0

[search_parser_errors_per_search]
max_search_parser_errors_per_search = 0

[search_parser_errors_per_search_per_second]
max_search_parser_errors_per_search_per_second = 0

[search_parser_errors_per_search_per_second_per_host]
max_search_parser_errors_per_search_per_second_per_host = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field_per_value]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field_per_value = 0

[search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field_per_value_per_other]
max_search_parser_errors_per_search_per_second_per_host_per_sourcetype_per_index_per_user_per_app_per_search_id_per_time_per_earliest_per_latest_per_field_per_value_per_other = 0
"""

    def _get_readme_content(self, cluster_name: str, cluster_config: Dict[str, Any]) -> str:
        """Generate comprehensive README content"""
        return f"""# Splunk Cluster: {cluster_name}

## Overview
This is a production-ready Splunk cluster configuration generated by the Enhanced Splunk Environment Builder.

## Cluster Configuration
- **Replication Factor**: {cluster_config.get('replication_factor', 3)}
- **Search Factor**: {cluster_config.get('search_factor', 2)}
- **Environment**: {cluster_config.get('environment', 'production')}
- **SSL Enabled**: {cluster_config.get('ssl_enabled', True)}
- **Created**: {datetime.now().isoformat()}

## Components
{chr(10).join([f"- **{comp}**: {desc}" for comp, desc in self.components.items()])}

## Security
- **Security Key**: {cluster_config.get('security_key', self.default_pass_key)[:8]}...
- **SSL/TLS**: {cluster_config.get('ssl_enabled', True)}
- **Authentication**: Enabled
- **Authorization**: Role-based access control

## Directory Structure
```
{cluster_name}/
├── cm/                 # Cluster Manager
├── deployer/           # Search Head Cluster Deployer
├── sh/                 # Search Head
├── idx/                # Indexer
├── ds/                 # Deployment Server
├── uf/                 # Universal Forwarder
├── hf/                 # Heavy Forwarder
├── lm/                 # License Master
├── mc/                 # Monitoring Console
└── documentation/      # This documentation
```

## Next Steps
1. Review and customize configuration files
2. Deploy to target hosts
3. Configure SSL certificates
4. Set up authentication and authorization
5. Test cluster functionality
6. Monitor cluster health

## Support
For issues and questions, refer to the TROUBLESHOOTING.md file.
"""

    def _get_deployment_guide_content(self, cluster_name: str, cluster_config: Dict[str, Any]) -> str:
        """Generate deployment guide content"""
        return f"""# Deployment Guide for {cluster_name}

## Prerequisites
- All target hosts have Splunk Enterprise installed
- Network connectivity between cluster members
- SSL certificates configured (if SSL enabled)
- Firewall rules configured for cluster ports

## Deployment Steps

### 1. Cluster Manager
1. Copy `cm/default/` configuration to Cluster Manager host
2. Restart Splunk service
3. Verify cluster manager is running: `splunk show cluster-status`

### 2. Indexers
1. Copy `idx/default/` configuration to each Indexer host
2. Update `server.conf` with correct Cluster Manager URI
3. Restart Splunk service
4. Verify peer status: `splunk show cluster-peers`

### 3. Search Heads
1. Copy `sh/default/` configuration to each Search Head host
2. Update `server.conf` with correct Cluster Manager URI
3. Restart Splunk service
4. Verify search head status: `splunk show cluster-status`

### 4. Universal Forwarders
1. Copy `uf/default/` configuration to each Forwarder host
2. Update `outputs.conf` with correct Indexer Discovery settings
3. Restart Splunk service
4. Verify forwarding status: `splunk list forward-server`

## Verification Commands
- Cluster status: `splunk show cluster-status`
- Peer status: `splunk show cluster-peers`
- Search head status: `splunk show shcluster-status`
- Indexer discovery: `splunk list indexer-discovery`

## Troubleshooting
See TROUBLESHOOTING.md for common issues and solutions.
"""

    def _get_troubleshooting_guide_content(self) -> str:
        """Generate troubleshooting guide content"""
        return """# Troubleshooting Guide

## Common Issues

### 1. Cluster Manager Not Starting
- Check `server.conf` syntax
- Verify SSL certificates exist
- Check port 8089 is not blocked
- Review Splunk logs: `splunk list log`

### 2. Indexers Not Joining Cluster
- Verify Cluster Manager URI is correct
- Check network connectivity
- Verify `pass4SymmKey` matches
- Check SSL configuration

### 3. Search Heads Not Clustering
- Verify Deployer URI is correct
- Check Search Head Cluster configuration
- Verify `pass4SymmKey` matches
- Check SSL configuration

### 4. Forwarders Not Sending Data
- Verify Indexer Discovery configuration
- Check network connectivity to indexers
- Verify SSL configuration
- Check `outputs.conf` syntax

### 5. SSL/TLS Issues
- Verify certificate paths are correct
- Check certificate permissions
- Verify SSL versions are compatible
- Check cipher suite configuration

## Debug Commands
- `splunk list log` - List available logs
- `splunk show cluster-status` - Show cluster status
- `splunk show cluster-peers` - Show peer status
- `splunk show shcluster-status` - Show search head cluster status
- `splunk list indexer-discovery` - Show indexer discovery status

## Log Files
- `$SPLUNK_HOME/var/log/splunk/splunkd.log` - Main Splunk daemon log
- `$SPLUNK_HOME/var/log/splunk/clustering.log` - Clustering specific log
- `$SPLUNK_HOME/var/log/splunk/splunkd_access.log` - Access log

## Performance Tuning
- Adjust `max_threads` and `max_sockets` in `server.conf`
- Configure appropriate bucket sizes in `indexes.conf`
- Tune replication and search factors based on hardware
- Monitor cluster health and performance metrics
"""

    def list_clusters(self) -> List[Dict[str, Any]]:
        """List all available clusters"""
        clusters = []
        try:
            for cluster_dir in self.base_path.iterdir():
                if cluster_dir.is_dir():
                    metadata_file = cluster_dir / 'cluster.json'
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            clusters.append(metadata)
                    else:
                        # Legacy cluster without metadata
                        clusters.append({
                            'cluster_name': cluster_dir.name,
                            'created_at': 'Unknown',
                            'components': self.components,
                            'config_folders': self.config_folders,
                            'total_folders': 'Unknown',
                            'version': '1.0.0'
                        })
        except Exception as e:
            logger.error(f"Failed to list clusters: {str(e)}")
        
        return clusters

    def delete_cluster(self, cluster_name: str) -> Dict[str, Any]:
        """Delete a cluster and all its contents"""
        try:
            cluster_path = self.base_path / cluster_name
            
            if not cluster_path.exists():
                return {
                    'success': False,
                    'error': f'Cluster "{cluster_name}" does not exist'
                }
            
            # Remove the entire cluster directory
            import shutil
            shutil.rmtree(cluster_path)
            
            logger.info(f"Deleted cluster '{cluster_name}'")
            
            return {
                'success': True,
                'cluster_name': cluster_name,
                'message': f'Cluster "{cluster_name}" deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to delete cluster '{cluster_name}': {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_cluster_info(self, cluster_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific cluster"""
        try:
            cluster_path = self.base_path / cluster_name
            
            if not cluster_path.exists():
                return None
            
            metadata_file = cluster_path / 'cluster.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                    # Add current folder structure info
                    metadata['folder_structure'] = self._get_folder_structure(cluster_path)
                    return metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cluster info for '{cluster_name}': {str(e)}")
            return None

    def _get_folder_structure(self, cluster_path: Path) -> Dict[str, Any]:
        """Get the current folder structure of a cluster"""
        structure = {}
        
        try:
            for component in self.components:
                component_path = cluster_path / component
                if component_path.exists():
                    structure[component] = {}
                    for config_folder in self.config_folders:
                        config_path = component_path / config_folder
                        if config_path.exists():
                            structure[component][config_folder] = [
                                f.name for f in config_path.iterdir() if f.is_file()
                            ]
                        else:
                            structure[component][config_folder] = []
                else:
                    structure[component] = {}
                    for config_folder in self.config_folders:
                        structure[component][config_folder] = []
        except Exception as e:
            logger.warning(f"Failed to get folder structure: {str(e)}")
        
        return structure

    def update_cluster_config(self, cluster_name: str, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update cluster configuration and regenerate configs"""
        try:
            cluster_path = self.base_path / cluster_name
            
            if not cluster_path.exists():
                return {
                    'success': False,
                    'error': f'Cluster "{cluster_name}" does not exist'
                }
            
            # Update metadata
            metadata_file = cluster_path / 'cluster.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                metadata['cluster_config'].update(new_config)
                metadata['updated_at'] = datetime.now().isoformat()
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            # Regenerate configuration files
            updated_files = []
            for component in self.components:
                component_path = cluster_path / component
                if component_path.exists():
                    default_path = component_path / 'default'
                    if default_path.exists():
                        files = self._create_component_configs(component, default_path, metadata['cluster_config'])
                        updated_files.extend(files)
            
            logger.info(f"Updated cluster '{cluster_name}' configuration and regenerated {len(updated_files)} files")
            
            return {
                'success': True,
                'cluster_name': cluster_name,
                'updated_files': updated_files,
                'message': f'Cluster configuration updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to update cluster '{cluster_name}': {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def validate_cluster_config(self, cluster_name: str) -> Dict[str, Any]:
        """Validate cluster configuration and structure"""
        try:
            cluster_path = self.base_path / cluster_name
            
            if not cluster_path.exists():
                return {
                    'success': False,
                    'error': f'Cluster "{cluster_name}" does not exist'
                }
            
            validation_results = {
                'cluster_name': cluster_name,
                'validation_time': datetime.now().isoformat(),
                'overall_status': 'valid',
                'issues': [],
                'warnings': [],
                'recommendations': []
            }
            
            # Check metadata
            metadata_file = cluster_path / 'cluster.json'
            if not metadata_file.exists():
                validation_results['issues'].append('Missing cluster metadata file')
                validation_results['overall_status'] = 'invalid'
            else:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Validate required fields
                    required_fields = ['cluster_name', 'components', 'config_folders']
                    for field in required_fields:
                        if field not in metadata:
                            validation_results['issues'].append(f'Missing required field: {field}')
                            validation_results['overall_status'] = 'invalid'
                    
                    # Check configuration
                    if 'cluster_config' in metadata:
                        config = metadata['cluster_config']
                        if config.get('replication_factor', 0) < 2:
                            validation_results['warnings'].append('Replication factor should be 2 or higher for production')
                        if not config.get('ssl_enabled', False):
                            validation_results['warnings'].append('SSL is not enabled - consider enabling for production')
                
                except Exception as e:
                    validation_results['issues'].append(f'Invalid metadata file: {str(e)}')
                    validation_results['overall_status'] = 'invalid'
            
            # Check folder structure
            for component in self.components:
                component_path = cluster_path / component
                if not component_path.exists():
                    validation_results['warnings'].append(f'Missing component directory: {component}')
                else:
                    for config_folder in self.config_folders:
                        config_path = component_path / config_folder
                        if not config_path.exists():
                            validation_results['warnings'].append(f'Missing config folder: {component}/{config_folder}')
                        elif config_folder == 'default':
                            # Check for configuration files
                            config_files = list(config_path.glob('*.conf'))
                            if not config_files:
                                validation_results['warnings'].append(f'No configuration files in {component}/default')
            
            # Generate recommendations
            if validation_results['overall_status'] == 'valid':
                validation_results['recommendations'].append('Configuration is valid and ready for deployment')
                validation_results['recommendations'].append('Review SSL certificates before deployment')
                validation_results['recommendations'].append('Test cluster connectivity before production use')
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate cluster '{cluster_name}': {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def save_build_configuration(self, cluster_name: str, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Save build configuration by updating cluster configuration files with actual host IPs
        
        Args:
            cluster_name: Name of the cluster
            components: List of components with host information
            
        Returns:
            Dictionary with save results
        """
        try:
            cluster_path = self.base_path / cluster_name
            
            if not cluster_path.exists():
                return {
                    'success': False,
                    'error': f'Cluster "{cluster_name}" does not exist'
                }
            
            # Build host mapping for different component types
            host_mapping = {}
            for component in components:
                if component.get('hostId') and component.get('host'):
                    host = component['host']
                    component_type = component['type']
                    
                    # Map component types to configuration folders
                    if component_type == 'splunk_cm':
                        host_mapping['cluster_manager'] = host['ip_address']
                        host_mapping['cluster-manager'] = host['ip_address']
                    elif component_type == 'splunk_license_master':
                        host_mapping['license_master'] = host['ip_address']
                        host_mapping['license-master'] = host['ip_address']
                    elif component_type == 'splunk_deployer':
                        host_mapping['deployer'] = host['ip_address']
                    elif component_type == 'splunk_deployment_server':
                        host_mapping['deployment_server'] = host['ip_address']
                        host_mapping['deployment-server'] = host['ip_address']
                    elif component_type == 'splunk_monitoring_console':
                        host_mapping['monitoring_console'] = host['ip_address']
                        host_mapping['monitoring-console'] = host['ip_address']
            
            if not host_mapping:
                return {
                    'success': False,
                    'error': 'No valid host mappings found in components'
                }
            
            logger.info(f"Updating cluster configuration with host mappings: {host_mapping}")
            
            # Update configuration files
            updated_files = []
            errors = []
            
            # Update each component's configuration files
            for component_folder in self.components:
                component_path = cluster_path / component_folder
                if not component_path.exists():
                    continue
                
                # Update default configuration files
                default_path = component_path / 'default'
                if default_path.exists():
                    for config_file in default_path.glob('*.conf'):
                        try:
                            updated = self._update_config_file_with_hosts(config_file, host_mapping)
                            if updated:
                                updated_files.append(str(config_file))
                        except Exception as e:
                            error_msg = f"Failed to update {config_file}: {str(e)}"
                            errors.append(error_msg)
                            logger.error(error_msg)
            
            # Update cluster metadata with build information
            metadata_file = cluster_path / 'cluster.json'
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Add build configuration information
                    metadata['build_config'] = {
                        'saved_at': datetime.now().isoformat(),
                        'components': components,
                        'host_mapping': host_mapping,
                        'total_components': len(components)
                    }
                    
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    updated_files.append(str(metadata_file))
                    
                except Exception as e:
                    error_msg = f"Failed to update metadata: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            if errors:
                return {
                    'success': False,
                    'message': f'Updated {len(updated_files)} files with {len(errors)} errors',
                    'updated_files': updated_files,
                    'errors': errors,
                    'host_mapping': host_mapping
                }
            else:
                return {
                    'success': True,
                    'message': f'Successfully updated {len(updated_files)} configuration files',
                    'updated_files': updated_files,
                    'host_mapping': host_mapping
                }
                
        except Exception as e:
            logger.error(f"Failed to save build configuration for '{cluster_name}': {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _update_config_file_with_hosts(self, config_file: Path, host_mapping: Dict[str, str]) -> bool:
        """
        Update a configuration file with actual host IPs
        
        Args:
            config_file: Path to the configuration file
            host_mapping: Dictionary mapping placeholder names to IP addresses
            
        Returns:
            True if file was updated, False otherwise
        """
        try:
            with open(config_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Replace placeholder hostnames with actual IPs
            for placeholder, ip_address in host_mapping.items():
                # Replace various formats of the placeholder
                patterns = [
                    f'http://{placeholder}:',
                    f'https://{placeholder}:',
                    f'{placeholder}:',
                    f'manager_uri = {placeholder}',
                    f'deployer_uri = {placeholder}',
                    f'license_uri = {placeholder}',
                    f'deployment_server = {placeholder}'
                ]
                
                for pattern in patterns:
                    if pattern in content:
                        if pattern.startswith('http://'):
                            content = content.replace(pattern, f'http://{ip_address}:')
                        elif pattern.startswith('https://'):
                            content = content.replace(pattern, f'https://{ip_address}:')
                        elif pattern.startswith('manager_uri = '):
                            content = content.replace(pattern, f'manager_uri = http://{ip_address}:')
                        elif pattern.startswith('deployer_uri = '):
                            content = content.replace(pattern, f'deployer_uri = http://{ip_address}:')
                        elif pattern.startswith('license_uri = '):
                            content = content.replace(pattern, f'license_uri = http://{ip_address}:')
                        elif pattern.startswith('deployment_server = '):
                            content = content.replace(pattern, f'deployment_server = http://{ip_address}:')
                        else:
                            content = content.replace(pattern, f'{ip_address}:')
            
            # Only write if content changed
            if content != original_content:
                with open(config_file, 'w') as f:
                    f.write(content)
                logger.info(f"Updated {config_file} with host mappings")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update config file {config_file}: {str(e)}")
            raise

    def _get_cm_distsearch_conf(self, config: Dict[str, Any]) -> str:
        """Cluster Manager distsearch.conf with distributed search settings"""
        return f"""# Splunk Cluster Manager Distributed Search Configuration
# Generated: {datetime.now().isoformat()}

[distributedSearch]
servers = *
"""

    def _get_deployer_server_conf(self, config: Dict[str, Any]) -> str:
        """Deployer server.conf with proper SHC configuration"""
        return f"""# Splunk Deployer Configuration for Search Head Clustering
# Generated: {datetime.now().isoformat()}
# Template: Uses dynamic variables for deployer instances

[general]
site = site1
serverName = {{{{SERVER_NAME}}}}
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

[license]
manager_uri = https://13.61.123.93:8089

[shclustering]
deployer = true
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

# SSL Configuration - Commented out until certificates are properly configured
# [sslConfig]
# enableSplunkdSSL = {str(config.get('ssl_enabled', True)).lower()}
# sslPassword = {config.get('security_key', self.default_pass_key)}
# serverCert = $SPLUNK_HOME/etc/auth/server.pem
# sslVersions = tls1.2
# sslVersionsForClient = tls1.2

[httpServer]
max_threads = 50
max_sockets = 50

# Web interface configuration
[web]
enableSplunkWebSSL = false
startwebserver = 1
httpport = 8000
"""

    def _get_deployer_authorize_conf(self, config: Dict[str, Any]) -> str:
        """Deployer authorize.conf with role-based access"""
        return f"""# Splunk Deployer Authorization Configuration
# Generated: {datetime.now().isoformat()}

[role_admin]
srchIndexesDefault = *
srchIndexesAllowed = *
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1
"""

    def _get_deployer_authentication_conf(self, config: Dict[str, Any]) -> str:
        """Deployer authentication.conf with security settings"""
        return f"""# Splunk Deployer Authentication Configuration
# Generated: {datetime.now().isoformat()}

[authentication]
authType = Splunk
authSettings = LDAP

[roleMap_Splunk]
admin = admin
power = power
user = user
"""

    def _get_deployer_web_conf(self, config: Dict[str, Any]) -> str:
        """Deployer web.conf with web interface settings"""
        return f"""# Splunk Deployer Web Configuration
# Generated: {datetime.now().isoformat()}

[settings]
enableSplunkWebSSL = false
startwebserver = 1
httpport = 8000
enableSplunkWeb = 1
login_content = Welcome to Splunk Deployer
appServerPorts = 8065
"""

    def _get_sh_distsearch_conf(self, config: Dict[str, Any]) -> str:
        """Search Head distsearch.conf with distributed search settings"""
        return f"""# Splunk Search Head Distributed Search Configuration
# Generated: {datetime.now().isoformat()}

[distributedSearch]
servers = *
pass4SymmKey = {config.get('security_key', self.default_pass_key)}
"""

    def _get_ds_server_conf(self, config: Dict[str, Any]) -> str:
        """Deployment Server server.conf with production settings"""
        return f"""# Splunk Deployment Server Configuration
# Generated: {datetime.now().isoformat()}

[general]
serverName = deployment-server-{config.get('cluster_label', 'prod')}
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

[license]
manager_uri = https://license-master:8089

# SSL Configuration - Commented out until certificates are properly configured
# [sslConfig]
# enableSplunkdSSL = {str(config.get('ssl_enabled', True)).lower()}
# sslPassword = {config.get('security_key', self.default_pass_key)}
# serverCert = $SPLUNK_HOME/etc/auth/server.pem
# sslVersions = tls1.2
# sslVersionsForClient = tls1.2

[httpServer]
max_threads = 50
max_sockets = 50

# Web interface configuration
[web]
enableSplunkWebSSL = false
startwebserver = 1
httpport = 8000
"""

    def _get_ds_serverclass_conf(self, config: Dict[str, Any]) -> str:
        """Deployment Server serverclass.conf with deployment settings"""
        return f"""# Splunk Deployment Server Server Class Configuration
# Generated: {datetime.now().isoformat()}

[serverClass:universal_forwarders]
whitelist.0 = *
restartSplunkd = 1
targetWorkbookCacheSizeMB = 256

[serverClass:heavy_forwarders]
whitelist.0 = *
restartSplunkd = 1
targetWorkbookCacheSizeMB = 256

[serverClass:indexers]
whitelist.0 = *
restartSplunkd = 1
targetWorkbookCacheSizeMB = 256

[serverClass:search_heads]
whitelist.0 = *
restartSplunkd = 1
targetWorkbookCacheSizeMB = 256
"""

    def _get_ds_authorize_conf(self, config: Dict[str, Any]) -> str:
        """Deployment Server authorize.conf with role-based access"""
        return f"""# Splunk Deployment Server Authorization Configuration
# Generated: {datetime.now().isoformat()}

[role_admin]
srchIndexesDefault = *
srchIndexesAllowed = *
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1
"""

    def _get_ds_authentication_conf(self, config: Dict[str, Any]) -> str:
        """Deployment Server authentication.conf with security settings"""
        return f"""# Splunk Deployment Server Authentication Configuration
# Generated: {datetime.now().isoformat()}

[authentication]
authType = Splunk
authSettings = LDAP

[roleMap_Splunk]
admin = admin
power = power
user = user
"""

    def _get_ds_web_conf(self, config: Dict[str, Any]) -> str:
        """Deployment Server web.conf with web interface settings"""
        return f"""# Splunk Deployment Server Web Configuration
# Generated: {datetime.now().isoformat()}

[settings]
enableSplunkWebSSL = false
startwebserver = 1
httpport = 8000
enableSplunkWeb = 1
login_content = Welcome to Splunk Deployment Server
appServerPorts = 8065
"""

    def _get_lm_server_conf(self, config: Dict[str, Any]) -> str:
        """License Master server.conf with production settings"""
        return f"""# Splunk License Master Configuration
# Generated: {datetime.now().isoformat()}

[general]
serverName = license-master-{config.get('cluster_label', 'prod')}
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

[license]
manager_uri = self

# SSL Configuration - Commented out until certificates are properly configured
# [sslConfig]
# enableSplunkdSSL = {str(config.get('ssl_enabled', True)).lower()}
# sslPassword = {config.get('security_key', self.default_pass_key)}
# serverCert = $SPLUNK_HOME/etc/auth/server.pem
# sslVersions = tls1.2
# sslVersionsForClient = tls1.2

[httpServer]
max_threads = 50
max_sockets = 50

# Web interface configuration
[web]
enableSplunkWebSSL = false
startwebserver = 1
httpport = 8000
"""

    def _get_lm_authorize_conf(self, config: Dict[str, Any]) -> str:
        """License Master authorize.conf with role-based access"""
        return f"""# Splunk License Master Authorization Configuration
# Generated: {datetime.now().isoformat()}

[role_admin]
srchIndexesDefault = *
srchIndexesAllowed = *
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1
"""

    def _get_lm_authentication_conf(self, config: Dict[str, Any]) -> str:
        """License Master authentication.conf with security settings"""
        return f"""# Splunk License Master Authentication Configuration
# Generated: {datetime.now().isoformat()}

[authentication]
authType = Splunk
authSettings = LDAP

[roleMap_Splunk]
admin = admin
power = power
user = user
"""

    def _get_lm_web_conf(self, config: Dict[str, Any]) -> str:
        """License Master web.conf with web interface settings"""
        return f"""# Splunk License Master Web Configuration
# Generated: {datetime.now().isoformat()}

[settings]
enableSplunkWebSSL = false
startwebserver = 1
httpport = 8000
enableSplunkWeb = 1
login_content = Welcome to Splunk License Master
appServerPorts = 8065
"""

    def _get_mc_server_conf(self, config: Dict[str, Any]) -> str:
        """Monitoring Console server.conf with production settings"""
        return f"""# Splunk Monitoring Console Configuration
# Generated: {datetime.now().isoformat()}

[general]
serverName = monitoring-console-{config.get('cluster_label', 'prod')}
pass4SymmKey = {config.get('security_key', self.default_pass_key)}

[license]
manager_uri = https://license-master:8089

# SSL Configuration - Commented out until certificates are properly configured
# [sslConfig]
# enableSplunkdSSL = {str(config.get('ssl_enabled', True)).lower()}
# sslPassword = {config.get('security_key', self.default_pass_key)}
# serverCert = $SPLUNK_HOME/etc/auth/server.pem
# sslVersions = tls1.2
# sslVersionsForClient = tls1.2

[httpServer]
max_threads = 50
max_sockets = 50

# Web interface configuration
[web]
enableSplunkWebSSL = false
startwebserver = 1
httpport = 8000
"""

    def _get_mc_authorize_conf(self, config: Dict[str, Any]) -> str:
        """Monitoring Console authorize.conf with role-based access"""
        return f"""# Splunk Monitoring Console Authorization Configuration
# Generated: {datetime.now().isoformat()}

[role_admin]
srchIndexesDefault = *
srchIndexesAllowed = *
srchMaxTime = 0
srchJobsQuota = 0
srchDiskQuota = 0
srchFilter = *
srchTimeWin = 0
srchTimeEarliest = 0
srchTimeLatest = 0
srchMaxCount = 0
srchMaxCountUnlimited = 1
srchMaxTimeUnlimited = 1
srchFilterUnlimited = 1
srchTimeWinUnlimited = 1
srchTimeEarliestUnlimited = 1
srchTimeLatestUnlimited = 1
"""

    def _get_mc_authentication_conf(self, config: Dict[str, Any]) -> str:
        """Monitoring Console authentication.conf with security settings"""
        return f"""# Splunk Monitoring Console Authentication Configuration
# Generated: {datetime.now().isoformat()}

[authentication]
authType = Splunk
authSettings = LDAP

[roleMap_Splunk]
admin = admin
power = power
user = user
"""

    def _get_mc_web_conf(self, config: Dict[str, Any]) -> str:
        """Monitoring Console web.conf with web interface settings"""
        return f"""# Splunk Monitoring Console Web Configuration
# Generated: {datetime.now().isoformat()}

[settings]
enableSplunkWebSSL = false
startwebserver = 1
httpport = 8000
enableSplunkWeb = 1
login_content = Welcome to Splunk Monitoring Console
appServerPorts = 8065
"""

    def _get_mc_distsearch_conf(self, config: Dict[str, Any]) -> str:
        """Monitoring Console distsearch.conf with distributed search settings"""
        return f"""# Splunk Monitoring Console Distributed Search Configuration
# Generated: {datetime.now().isoformat()}

[distributedSearch]
servers = *
pass4SymmKey = {config.get('security_key', self.default_pass_key)}
"""

    def _get_sh_shcluster_conf(self, config: Dict[str, Any]) -> str:
        """Search Head shcluster.conf with SHC-specific settings"""
        return f"""# Search Head Cluster Configuration
# Generated: {datetime.now().isoformat()}

[shclustering]
# This file contains SHC-specific configuration overrides
# The main configuration is in server.conf
"""

    def _get_deployer_shcluster_conf(self, config: Dict[str, Any]) -> str:
        """Deployer shcluster.conf with deployer-specific settings"""
        return f"""# Deployer SHC Configuration
# Generated: {datetime.now().isoformat()}

[shclustering]
# This file contains deployer-specific configuration overrides
# The main configuration is in server.conf
"""

    def _create_shc_setup_instructions(self, cluster_name: str, cluster_config: Dict[str, Any]) -> str:
        """Create SHC setup instructions for the cluster"""
        return f"""# Splunk Search Head Cluster (SHC) Setup Instructions
# Cluster: {cluster_name}
# Generated: {datetime.now().isoformat()}

## Overview
This document provides step-by-step instructions to set up a Search Head Cluster (SHC) for the {cluster_name} cluster.

## Prerequisites
- All target hosts have Splunk Enterprise installed and running
- Network connectivity between deployer and search heads
- SSH access to all hosts as root user
- Splunk admin credentials (default: admin/changeme)

## Step 1: Configure Deployer
The deployer configuration is already created in the cluster files. You need to:

1. Copy the deployer configuration to your deployer host
2. Place it in `/opt/splunk/etc/shcluster/apps/siemply_{cluster_name}_deployer/`
3. Restart Splunk on the deployer

## Step 2: Configure Search Heads
For each search head:

1. Copy the search head configuration to `/opt/splunk/etc/apps/siemply_{cluster_name}_sh/`
2. Replace template variables:
   - `{{SERVER_NAME}}` → `sh-<IP_ADDRESS>`
   - `{{DEPLOYER_IP}}` → `<DEPLOYER_IP_ADDRESS>`
   - `{{MGMT_URI}}` → `https://<SEARCH_HEAD_IP>:8089`
3. Restart Splunk on each search head

## Step 3: Bootstrap the Cluster
On the first search head:

```bash
sudo -u splunk /opt/splunk/bin/splunk init shcluster-config \\
  -auth admin:changeme \\
  -mgmt_uri https://<FIRST_SH_IP>:8089 \\
  -replication_port 8181 \\
  -replication_factor 2 \\
  -conf_deploy_fetch_url https://<DEPLOYER_IP>:8089 \\
  -secret {cluster_config.get('security_key', self.default_pass_key)} \\
  -shcluster_label sh-{cluster_name}
```

Restart the first search head.

## Step 4: Join Other Search Heads
On each additional search head:

```bash
sudo -u splunk /opt/splunk/bin/splunk init shcluster-config \\
  -auth admin:changeme \\
  -mgmt_uri https://<SH_IP>:8089 \\
  -replication_port 8181 \\
  -secret {cluster_config.get('security_key', self.default_pass_key)} \\
  -shcluster_label sh-{cluster_name}
```

Restart each search head.

## Step 5: Elect Captain
On any search head:

```bash
sudo -u splunk /opt/splunk/bin/splunk bootstrap shcluster-captain \\
  -servers_list "https://<SH1_IP>:8089,https://<SH2_IP>:8089" \\
  -auth admin:changeme
```

## Step 6: Verify Cluster Status
Check cluster status on any search head:

```bash
sudo -u splunk /opt/splunk/bin/splunk show shcluster-status -auth admin:changeme
```

## Step 7: Connect to Indexers
On each search head, add indexers:

```bash
sudo -u splunk /opt/splunk/bin/splunk add search-server https://<INDEXER_IP>:8089 -auth admin:changeme
```

## Automation
You can also use the automated setup script:

```bash
cd backend/scripts
python3 setup_shcluster.py
```

## Troubleshooting
- Check Splunk logs: `sudo -u splunk /opt/splunk/bin/splunk list log`
- Verify network connectivity between hosts
- Ensure all template variables are properly replaced
- Check that replication port 8181 is not blocked by firewall

## Template Variables Reference
- `{{SERVER_NAME}}`: Hostname for the search head (e.g., sh-192.168.1.100)
- `{{DEPLOYER_IP}}`: IP address of the deployer host
- `{{MGMT_URI}}`: Management URI for the search head (e.g., https://192.168.1.100:8089)
- `{{HOST_IP}}`: IP address of the target host
- `{{CLUSTER_NAME}}`: Name of the cluster
"""


# Backward compatibility - keep the old class name for existing code
class ClusterManager(EnhancedSplunkClusterManager):
    """Legacy ClusterManager class for backward compatibility"""
    pass
