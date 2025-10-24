"""
Server Class Service
Manages server class configurations stored in data.conf/serverclass.conf files
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ServerClassService:
    def __init__(self, data_conf_path: str = "data.conf"):
        """
        Initialize ServerClassService
        
        Args:
            data_conf_path: Path to the data.conf directory
        """
        self.data_conf_path = Path(data_conf_path)
        self.serverclass_conf_path = self.data_conf_path / "serverclass.conf"
        self.serverclass_metadata_path = self.data_conf_path / "serverclass_metadata.json"
        
        # Ensure data.conf directory exists
        self.data_conf_path.mkdir(exist_ok=True)
        
        # Initialize serverclass.conf if it doesn't exist
        if not self.serverclass_conf_path.exists():
            self._create_default_serverclass_conf()
    
    def _create_default_serverclass_conf(self):
        """Create default serverclass.conf file"""
        default_content = """# Server Class Configuration
# This file contains server class definitions for host grouping
# Format: [serverClass:<class_name>]
#         whitelist.<n> = <hostname_or_ip>
#         blacklist.<n> = <hostname_or_ip>

# Example:
# [serverClass:web_servers]
# whitelist.0 = web-server-01
# whitelist.1 = web-server-02
# 
# [serverClass:database_servers]
# whitelist.0 = db-server-01
# whitelist.1 = db-server-02

"""
        with open(self.serverclass_conf_path, 'w') as f:
            f.write(default_content)
        
        logger.info(f"Created default serverclass.conf at {self.serverclass_conf_path}")
    
    def _create_default_metadata_file(self):
        """Create default metadata file"""
        default_metadata = {
            "server_classes": {},
            "version": "1.0",
            "last_updated": None
        }
        with open(self.serverclass_metadata_path, 'w') as f:
            json.dump(default_metadata, f, indent=2)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load server class metadata"""
        if not self.serverclass_metadata_path.exists():
            self._create_default_metadata_file()
        
        try:
            with open(self.serverclass_metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return {"server_classes": {}, "version": "1.0", "last_updated": None}
    
    def _save_metadata(self, metadata: Dict[str, Any]):
        """Save server class metadata"""
        try:
            with open(self.serverclass_metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise
    
    def _parse_serverclass_conf(self) -> Dict[str, List[str]]:
        """Parse serverclass.conf file and extract server classes"""
        server_classes = {}
        current_class = None
        
        try:
            with open(self.serverclass_conf_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Check for server class definition
                    if line.startswith('[serverClass:') and line.endswith(']'):
                        current_class = line[13:-1]  # Remove [serverClass: and ]
                        server_classes[current_class] = []
                    
                    # Check for whitelist entries
                    elif current_class and line.startswith('whitelist.'):
                        host = line.split('=', 1)[1].strip()
                        if host and host not in server_classes[current_class]:
                            server_classes[current_class].append(host)
        
        except Exception as e:
            logger.error(f"Error parsing serverclass.conf: {e}")
        
        return server_classes
    
    def _write_serverclass_conf(self, server_classes: Dict[str, List[str]]):
        """Write server classes to serverclass.conf file"""
        content = """# Server Class Configuration
# This file contains server class definitions for host grouping
# Format: [serverClass:<class_name>]
#         whitelist.<n> = <hostname_or_ip>
#         blacklist.<n> = <hostname_or_ip>

"""
        
        for class_name, hosts in server_classes.items():
            content += f"[serverClass:{class_name}]\n"
            for i, host in enumerate(hosts):
                content += f"whitelist.{i} = {host}\n"
            content += "\n"
        
        try:
            with open(self.serverclass_conf_path, 'w') as f:
                f.write(content)
            logger.info(f"Updated serverclass.conf with {len(server_classes)} server classes")
        except Exception as e:
            logger.error(f"Error writing serverclass.conf: {e}")
            raise
    
    def create_server_class(self, name: str, description: str, host_ids: List[int], 
                           tags: List[str] = None, is_active: bool = True, 
                           created_by: str = "admin") -> Dict[str, Any]:
        """
        Create a new server class
        
        Args:
            name: Server class name
            description: Server class description
            host_ids: List of host IDs to include
            tags: List of tags
            is_active: Whether the server class is active
            created_by: User who created the server class
            
        Returns:
            Server class data
        """
        try:
            # Load current metadata
            metadata = self._load_metadata()
            
            # Check if server class already exists
            if name in metadata["server_classes"]:
                raise ValueError(f"Server class '{name}' already exists")
            
            # Get host information from database
            from backend.models import get_db, Host
            from sqlalchemy.orm import Session
            
            # Create a database session
            db = next(get_db())
            hosts = []
            hostnames = []
            
            for host_id in host_ids:
                try:
                    host = db.query(Host).filter(Host.id == host_id).first()
                    if host:
                        hosts.append(host)
                        hostnames.append(host.hostname)
                    else:
                        logger.warning(f"Host with ID {host_id} not found")
                except Exception as e:
                    logger.warning(f"Error getting host with ID {host_id}: {e}")
            
            # Close the database session
            db.close()
            
            # Create server class data
            server_class_data = {
                "id": f"sc_{len(metadata['server_classes']) + 1}",
                "name": name,
                "description": description,
                "host_ids": host_ids,
                "hostnames": hostnames,
                "host_count": len(hosts),
                "tags": tags or [],
                "is_active": is_active,
                "created_by": created_by,
                "created_at": self._get_current_timestamp(),
                "updated_at": self._get_current_timestamp()
            }
            
            # Add to metadata
            metadata["server_classes"][name] = server_class_data
            metadata["last_updated"] = self._get_current_timestamp()
            
            # Save metadata
            self._save_metadata(metadata)
            
            # Update serverclass.conf
            self._update_serverclass_conf()
            
            logger.info(f"Created server class '{name}' with {len(hosts)} hosts")
            return server_class_data
            
        except Exception as e:
            logger.error(f"Error creating server class: {e}")
            raise
    
    def get_server_class(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get server class by name
        
        Args:
            name: Server class name
            
        Returns:
            Server class data or None if not found
        """
        try:
            metadata = self._load_metadata()
            return metadata["server_classes"].get(name)
        except Exception as e:
            logger.error(f"Error getting server class '{name}': {e}")
            return None
    
    def get_all_server_classes(self) -> List[Dict[str, Any]]:
        """
        Get all server classes
        
        Returns:
            List of server class data
        """
        try:
            metadata = self._load_metadata()
            return list(metadata["server_classes"].values())
        except Exception as e:
            logger.error(f"Error getting all server classes: {e}")
            return []
    
    def update_server_class(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Update server class
        
        Args:
            name: Server class name
            **kwargs: Fields to update
            
        Returns:
            Updated server class data
        """
        try:
            metadata = self._load_metadata()
            
            if name not in metadata["server_classes"]:
                raise ValueError(f"Server class '{name}' not found")
            
            server_class = metadata["server_classes"][name]
            
            # Update allowed fields
            allowed_fields = ["description", "host_ids", "tags", "is_active"]
            for field, value in kwargs.items():
                if field in allowed_fields:
                    server_class[field] = value
            
            # Update host information if host_ids changed
            if "host_ids" in kwargs:
                from backend.models import get_db, Host
                
                # Create a database session
                db = next(get_db())
                hosts = []
                hostnames = []
                
                for host_id in kwargs["host_ids"]:
                    try:
                        host = db.query(Host).filter(Host.id == host_id).first()
                        if host:
                            hosts.append(host)
                            hostnames.append(host.hostname)
                        else:
                            logger.warning(f"Host with ID {host_id} not found")
                    except Exception as e:
                        logger.warning(f"Error getting host with ID {host_id}: {e}")
                
                # Close the database session
                db.close()
                
                server_class["hostnames"] = hostnames
                server_class["host_count"] = len(hosts)
            
            server_class["updated_at"] = self._get_current_timestamp()
            metadata["last_updated"] = self._get_current_timestamp()
            
            # Save metadata
            self._save_metadata(metadata)
            
            # Update serverclass.conf
            self._update_serverclass_conf()
            
            logger.info(f"Updated server class '{name}'")
            return server_class
            
        except Exception as e:
            logger.error(f"Error updating server class '{name}': {e}")
            raise
    
    def delete_server_class(self, name: str) -> bool:
        """
        Delete server class
        
        Args:
            name: Server class name
            
        Returns:
            True if deleted successfully
        """
        try:
            metadata = self._load_metadata()
            
            if name not in metadata["server_classes"]:
                raise ValueError(f"Server class '{name}' not found")
            
            # Remove from metadata
            del metadata["server_classes"][name]
            metadata["last_updated"] = self._get_current_timestamp()
            
            # Save metadata
            self._save_metadata(metadata)
            
            # Update serverclass.conf
            self._update_serverclass_conf()
            
            logger.info(f"Deleted server class '{name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting server class '{name}': {e}")
            raise
    
    def _update_serverclass_conf(self):
        """Update serverclass.conf file with current server classes"""
        try:
            metadata = self._load_metadata()
            server_classes = {}
            
            for name, data in metadata["server_classes"].items():
                if data.get("is_active", True):
                    server_classes[name] = data.get("hostnames", [])
            
            self._write_serverclass_conf(server_classes)
            
        except Exception as e:
            logger.error(f"Error updating serverclass.conf: {e}")
            raise
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def get_serverclass_conf_content(self) -> str:
        """
        Get the content of serverclass.conf file
        
        Returns:
            Content of serverclass.conf file
        """
        try:
            with open(self.serverclass_conf_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading serverclass.conf: {e}")
            return ""
    
    def validate_server_class_name(self, name: str) -> bool:
        """
        Validate server class name
        
        Args:
            name: Server class name to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check if name is empty or contains invalid characters
        if not name or not name.strip():
            return False
        
        # Check for invalid characters (similar to Splunk's naming rules)
        invalid_chars = ['[', ']', '=', ' ', '\t', '\n', '\r']
        for char in invalid_chars:
            if char in name:
                return False
        
        return True 