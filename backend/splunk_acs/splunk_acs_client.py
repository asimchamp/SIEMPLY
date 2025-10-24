"""
Splunk Cloud ACS API Client
Handles communication with Splunk Cloud Admin Config Service API
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class SplunkCloudClient:
    """Client for interacting with Splunk Cloud ACS API"""
    
    def __init__(self, stack_id: str, auth_token: str, region: str):
        self.stack_id = stack_id
        self.auth_token = auth_token
        self.region = region
        self.base_url = f"https://admin.splunk.com/{region}/adminconfig/v2"
        self.session = None
        
        # API endpoints
        self.endpoints = {
            'ip_allow_lists': 'ip-allow-lists',
            'outbound_ports': 'outbound-ports',
            'private_connectivity': 'private-connectivity',
            'apps': 'apps',
            'indexes': 'indexes',
            'users': 'users',
            'roles': 'roles',
            'auth_tokens': 'auth-tokens',
            'maintenance_windows': 'maintenance-windows',
            'hec_tokens': 'hec-tokens',
            'limits_conf': 'limits-conf',
            'ddss_storage': 'ddss-storage'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json",
                "User-Agent": "SIEMply-ACS-Client/1.0"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Splunk Cloud API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with self.session.request(
                method, 
                url, 
                json=data, 
                params=params
            ) as response:
                
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=response.status, 
                        detail=f"Splunk Cloud API error: {error_text}"
                    )
                
                if response.status == 204:  # No content
                    return {"success": True}
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise HTTPException(
                status_code=503, 
                detail=f"Network error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Unexpected error: {str(e)}"
            )
    
    # IP Allow Lists
    async def get_ip_allow_lists(self) -> List[Dict[str, Any]]:
        """Retrieve IP allow lists"""
        response = await self._make_request("GET", self.endpoints['ip_allow_lists'])
        return response.get('data', [])
    
    async def create_ip_allow_list(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new IP allow list"""
        return await self._make_request("POST", self.endpoints['ip_allow_lists'], data)
    
    async def update_ip_allow_list(self, list_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing IP allow list"""
        endpoint = f"{self.endpoints['ip_allow_lists']}/{list_id}"
        return await self._make_request("PUT", endpoint, data)
    
    async def delete_ip_allow_list(self, list_id: str) -> Dict[str, Any]:
        """Delete IP allow list"""
        endpoint = f"{self.endpoints['ip_allow_lists']}/{list_id}"
        return await self._make_request("DELETE", endpoint)
    
    # Outbound Ports
    async def get_outbound_ports(self) -> List[Dict[str, Any]]:
        """Retrieve outbound port configurations"""
        response = await self._make_request("GET", self.endpoints['outbound_ports'])
        return response.get('data', [])
    
    async def update_outbound_ports(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update outbound port configuration"""
        return await self._make_request("PUT", self.endpoints['outbound_ports'], data)
    
    # Private Connectivity
    async def get_private_connectivity_status(self) -> Dict[str, Any]:
        """Get private connectivity status"""
        response = await self._make_request("GET", self.endpoints['private_connectivity'])
        return response
    
    async def enable_private_connectivity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enable private connectivity"""
        return await self._make_request("POST", self.endpoints['private_connectivity'], data)
    
    # Apps Management
    async def get_apps(self) -> List[Dict[str, Any]]:
        """Retrieve apps"""
        response = await self._make_request("GET", self.endpoints['apps'])
        return response.get('data', [])
    
    async def export_app(self, app_name: str) -> Dict[str, Any]:
        """Export app"""
        endpoint = f"{self.endpoints['apps']}/{app_name}/export"
        return await self._make_request("POST", endpoint)
    
    async def update_app_permissions(self, app_name: str, permissions: Dict[str, Any]) -> Dict[str, Any]:
        """Update app permissions"""
        endpoint = f"{self.endpoints['apps']}/{app_name}/permissions"
        return await self._make_request("PUT", endpoint, permissions)
    
    # Indexes Management
    async def get_indexes(self) -> List[Dict[str, Any]]:
        """Retrieve indexes"""
        response = await self._make_request("GET", self.endpoints['indexes'])
        return response.get('data', [])
    
    async def create_index(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new index"""
        return await self._make_request("POST", self.endpoints['indexes'], data)
    
    async def update_index(self, index_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing index"""
        endpoint = f"{self.endpoints['indexes']}/{index_name}"
        return await self._make_request("PUT", endpoint, data)
    
    async def delete_index(self, index_name: str) -> Dict[str, Any]:
        """Delete index"""
        endpoint = f"{self.endpoint['indexes']}/{index_name}"
        return await self._make_request("DELETE", endpoint)
    
    # Users and Roles
    async def get_users(self) -> List[Dict[str, Any]]:
        """Retrieve users"""
        response = await self._make_request("GET", self.endpoints['users'])
        return response.get('data', [])
    
    async def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user"""
        return await self._make_request("POST", self.endpoints['users'], data)
    
    async def update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing user"""
        endpoint = f"{self.endpoints['users']}/{user_id}"
        return await self._make_request("PUT", endpoint, data)
    
    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete user"""
        endpoint = f"{self.endpoints['users']}/{user_id}"
        return await self._make_request("DELETE", endpoint)
    
    async def get_roles(self) -> List[Dict[str, Any]]:
        """Retrieve roles"""
        response = await self._make_request("GET", self.endpoints['roles'])
        return response.get('data', [])
    
    # Authentication Tokens
    async def get_auth_tokens(self) -> List[Dict[str, Any]]:
        """Retrieve authentication tokens"""
        response = await self._make_request("GET", self.endpoints['auth_tokens'])
        return response.get('data', [])
    
    async def create_auth_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new authentication token"""
        return await self._make_request("POST", self.endpoints['auth_tokens'], data)
    
    async def revoke_auth_token(self, token_id: str) -> Dict[str, Any]:
        """Revoke authentication token"""
        endpoint = f"{self.endpoints['auth_tokens']}/{token_id}"
        return await self._make_request("DELETE", endpoint)
    
    # Maintenance Windows
    async def get_maintenance_windows(self) -> List[Dict[str, Any]]:
        """Retrieve maintenance windows"""
        response = await self._make_request("GET", self.endpoints['maintenance_windows'])
        return response.get('data', [])
    
    async def create_maintenance_window(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new maintenance window"""
        return await self._make_request("POST", self.endpoints['maintenance_windows'], data)
    
    async def update_maintenance_window(self, window_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing maintenance window"""
        endpoint = f"{self.endpoints['maintenance_windows']}/{window_id}"
        return await self._make_request("PUT", endpoint, data)
    
    async def delete_maintenance_window(self, window_id: str) -> Dict[str, Any]:
        """Delete maintenance window"""
        endpoint = f"{self.endpoints['maintenance_windows']}/{window_id}"
        return await self._make_request("DELETE", endpoint)
    
    # HEC Tokens
    async def get_hec_tokens(self) -> List[Dict[str, Any]]:
        """Retrieve HEC tokens"""
        response = await self._make_request("GET", self.endpoints['hec_tokens'])
        return response.get('data', [])
    
    async def create_hec_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new HEC token"""
        return await self._make_request("POST", self.endpoints['hec_tokens'], data)
    
    async def update_hec_token(self, token_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing HEC token"""
        endpoint = f"{self.endpoints['hec_tokens']}/{token_id}"
        return await self._make_request("PUT", endpoint, data)
    
    async def delete_hec_token(self, token_id: str) -> Dict[str, Any]:
        """Delete HEC token"""
        endpoint = f"{self.endpoints['hec_tokens']}/{token_id}"
        return await self._make_request("DELETE", endpoint)
    
    # Limits.conf Configuration
    async def get_limits_conf(self) -> Dict[str, Any]:
        """Retrieve limits.conf configuration"""
        response = await self._make_request("GET", self.endpoints['limits_conf'])
        return response
    
    async def update_limits_conf(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update limits.conf configuration"""
        return await self._make_request("PUT", self.endpoints['limits_conf'], data)
    
    # DDSS Storage
    async def get_ddss_storage(self) -> List[Dict[str, Any]]:
        """Retrieve DDSS storage locations"""
        response = await self._make_request("GET", self.endpoints['ddss_storage'])
        return response.get('data', [])
    
    async def update_ddss_storage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update DDSS storage configuration"""
        return await self._make_request("PUT", self.endpoints['ddss_storage'], data)
    
    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Check API health and connectivity"""
        try:
            response = await self._make_request("GET", "health")
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "response": response
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    # Utility Methods
    def get_endpoint_url(self, endpoint_name: str) -> str:
        """Get full URL for an endpoint"""
        if endpoint_name not in self.endpoints:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")
        return f"{self.base_url}/{self.endpoints[endpoint_name]}"
    
    def validate_credentials(self) -> bool:
        """Validate that credentials are properly set"""
        return all([
            self.stack_id and len(self.stack_id) > 0,
            self.auth_token and len(self.auth_token) > 0,
            self.region and len(self.region) > 0
        ])
