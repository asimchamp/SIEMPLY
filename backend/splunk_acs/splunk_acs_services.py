"""
Splunk ACS Services
Main business logic for ACS operations
"""
import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from fastapi import HTTPException

from .splunk_acs_models import (
    SplunkCloudConfig, ACSOperation, ChangeRequest, ConfigurationVersion, ApprovalWorkflow,
    SplunkCloudConfigCreate, SplunkCloudConfigUpdate, ChangeRequestCreate, ChangeRequestUpdate
)
from .splunk_acs_client import SplunkCloudClient
from .splunk_acs_utils import credential_manager, acs_config_validator, acs_rate_limiter, acs_metrics_collector
from .splunk_acs_workflow import ChangeRequestWorkflow
from .splunk_acs_versioning import ConfigurationVersionControl

logger = logging.getLogger(__name__)


class ACSService:
    """Main service class for ACS operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.workflow = ChangeRequestWorkflow(db)
        self.versioning = ConfigurationVersionControl(db)
    
    # Configuration Management
    async def get_configs(self) -> List[SplunkCloudConfig]:
        """Get all Splunk Cloud configurations"""
        try:
            configs = self.db.query(SplunkCloudConfig).all()
            return configs
        except Exception as e:
            logger.error(f"Failed to get configurations: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve configurations")
    
    async def get_config(self, config_id: int) -> SplunkCloudConfig:
        """Get specific Splunk Cloud configuration"""
        try:
            config = self.db.query(SplunkCloudConfig).filter(
                SplunkCloudConfig.id == config_id
            ).first()
            
            if not config:
                raise HTTPException(status_code=404, detail="Configuration not found")
            
            return config
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get configuration {config_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve configuration")
    
    async def create_config(self, config_data: SplunkCloudConfigCreate, user_id: int) -> SplunkCloudConfig:
        """Create new Splunk Cloud configuration"""
        try:
            # Validate configuration data
            if not acs_config_validator.validate_stack_id(config_data.stack_id):
                raise HTTPException(status_code=400, detail="Invalid stack ID format")
            
            if not acs_config_validator.validate_region(config_data.region):
                raise HTTPException(status_code=400, detail="Invalid region")
            
            if not acs_config_validator.validate_environment(config_data.environment):
                raise HTTPException(status_code=400, detail="Invalid environment")
            
            # Check if configuration with same name already exists
            existing_config = self.db.query(SplunkCloudConfig).filter(
                SplunkCloudConfig.name == config_data.name
            ).first()
            
            if existing_config:
                raise HTTPException(status_code=400, detail="Configuration with this name already exists")
            
            # Encrypt auth token
            encrypted_token = credential_manager.encrypt(config_data.auth_token)
            
            # Create configuration
            config = SplunkCloudConfig(
                name=config_data.name,
                stack_id=config_data.stack_id,
                auth_token=encrypted_token,
                region=config_data.region,
                environment=config_data.environment
            )
            
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            
            # Log operation
            await self._log_operation(
                operation_type="create_config",
                resource_type="splunk_cloud_config",
                resource_id=str(config.id),
                user_id=user_id,
                status="success"
            )
            
            logger.info(f"Created Splunk Cloud configuration: {config.name}")
            return config
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create configuration: {e}")
            raise HTTPException(status_code=500, detail="Failed to create configuration")
    
    async def update_config(self, config_id: int, config_data: SplunkCloudConfigUpdate, user_id: int) -> SplunkCloudConfig:
        """Update Splunk Cloud configuration"""
        try:
            config = await self.get_config(config_id)
            
            # Update fields if provided
            if config_data.name is not None:
                # Check if new name conflicts with existing config
                existing_config = self.db.query(SplunkCloudConfig).filter(
                    and_(
                        SplunkCloudConfig.name == config_data.name,
                        SplunkCloudConfig.id != config_id
                    )
                ).first()
                
                if existing_config:
                    raise HTTPException(status_code=400, detail="Configuration with this name already exists")
                
                config.name = config_data.name
            
            if config_data.stack_id is not None:
                if not acs_config_validator.validate_stack_id(config_data.stack_id):
                    raise HTTPException(status_code=400, detail="Invalid stack ID format")
                config.stack_id = config_data.stack_id
            
            if config_data.auth_token is not None:
                encrypted_token = credential_manager.encrypt(config_data.auth_token)
                config.auth_token = encrypted_token
            
            if config_data.region is not None:
                if not acs_config_validator.validate_region(config_data.region):
                    raise HTTPException(status_code=400, detail="Invalid region")
                config.region = config_data.region
            
            if config_data.environment is not None:
                if not acs_config_validator.validate_environment(config_data.environment):
                    raise HTTPException(status_code=400, detail="Invalid environment")
                config.environment = config_data.environment
            
            if config_data.is_active is not None:
                config.is_active = config_data.is_active
            
            config.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(config)
            
            # Log operation
            await self._log_operation(
                operation_type="update_config",
                resource_type="splunk_cloud_config",
                resource_id=str(config.id),
                user_id=user_id,
                status="success"
            )
            
            logger.info(f"Updated Splunk Cloud configuration: {config.name}")
            return config
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update configuration {config_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update configuration")
    
    async def delete_config(self, config_id: int, user_id: int):
        """Delete Splunk Cloud configuration"""
        try:
            config = await self.get_config(config_id)
            
            # Check if there are active change requests for this config
            active_requests = self.db.query(ChangeRequest).filter(
                and_(
                    ChangeRequest.config_id == config_id,
                    ChangeRequest.status.in_(["draft", "pending", "approved"])
                )
            ).count()
            
            if active_requests > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot delete configuration with {active_requests} active change requests"
                )
            
            self.db.delete(config)
            self.db.commit()
            
            # Log operation
            await self._log_operation(
                operation_type="delete_config",
                resource_type="splunk_cloud_config",
                resource_id=str(config_id),
                user_id=user_id,
                status="success"
            )
            
            logger.info(f"Deleted Splunk Cloud configuration: {config.name}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete configuration {config_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete configuration")
    
    # IP Allow Lists
    async def get_ip_allow_lists(self, config_id: int) -> List[Dict[str, Any]]:
        """Get IP allow lists for a configuration"""
        try:
            config = await self.get_config(config_id)
            
            # Check rate limiting
            if not acs_rate_limiter.can_make_call():
                wait_time = acs_rate_limiter.get_wait_time()
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded. Try again in {wait_time} seconds"
                )
            
            start_time = time.time()
            
            async with SplunkCloudClient(
                config.stack_id,
                credential_manager.decrypt(config.auth_token),
                config.region
            ) as client:
                result = await client.get_ip_allow_lists()
                
                response_time = time.time() - start_time
                acs_metrics_collector.record_operation("get_ip_allow_lists", True, response_time)
                
                return result
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get IP allow lists for config {config_id}: {e}")
            acs_metrics_collector.record_operation("get_ip_allow_lists", False, 0)
            raise HTTPException(status_code=500, detail="Failed to retrieve IP allow lists")
    
    async def create_ip_allow_list(self, config_id: int, list_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Create new IP allow list"""
        try:
            config = await self.get_config(config_id)
            
            # Check rate limiting
            if not acs_rate_limiter.can_make_call():
                wait_time = acs_rate_limiter.get_wait_time()
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded. Try again in {wait_time} seconds"
                )
            
            start_time = time.time()
            
            async with SplunkCloudClient(
                config.stack_id,
                credential_manager.decrypt(config.auth_token),
                config.region
            ) as client:
                result = await client.create_ip_allow_list(list_data)
                
                response_time = time.time() - start_time
                acs_metrics_collector.record_operation("create_ip_allow_list", True, response_time)
                
                # Log operation
                await self._log_operation(
                    operation_type="create_ip_allow_list",
                    resource_type="ip_allow_list",
                    resource_id=list_data.get('name'),
                    user_id=user_id,
                    status="success",
                    configuration=list_data
                )
                
                return result
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create IP allow list for config {config_id}: {e}")
            acs_metrics_collector.record_operation("create_ip_allow_list", False, 0)
            raise HTTPException(status_code=500, detail="Failed to create IP allow list")
    
    # Indexes
    async def get_indexes(self, config_id: int) -> List[Dict[str, Any]]:
        """Get indexes for a configuration"""
        try:
            config = await self.get_config(config_id)
            
            if not acs_rate_limiter.can_make_call():
                wait_time = acs_rate_limiter.get_wait_time()
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded. Try again in {wait_time} seconds"
                )
            
            start_time = time.time()
            
            async with SplunkCloudClient(
                config.stack_id,
                credential_manager.decrypt(config.auth_token),
                config.region
            ) as client:
                result = await client.get_indexes()
                
                response_time = time.time() - start_time
                acs_metrics_collector.record_operation("get_indexes", True, response_time)
                
                return result
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get indexes for config {config_id}: {e}")
            acs_metrics_collector.record_operation("get_indexes", False, 0)
            raise HTTPException(status_code=500, detail="Failed to retrieve indexes")
    
    async def create_index(self, config_id: int, index_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Create new index"""
        try:
            config = await self.get_config(config_id)
            
            if not acs_rate_limiter.can_make_call():
                wait_time = acs_rate_limiter.get_wait_time()
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded. Try again in {wait_time} seconds"
                )
            
            start_time = time.time()
            
            async with SplunkCloudClient(
                config.stack_id,
                credential_manager.decrypt(config.auth_token),
                config.region
            ) as client:
                result = await client.create_index(index_data)
                
                response_time = time.time() - start_time
                acs_metrics_collector.record_operation("create_index", True, response_time)
                
                # Log operation
                await self._log_operation(
                    operation_type="create_index",
                    resource_type="index",
                    resource_id=index_data.get('name'),
                    user_id=user_id,
                    status="success",
                    configuration=index_data
                )
                
                return result
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create index for config {config_id}: {e}")
            acs_metrics_collector.record_operation("create_index", False, 0)
            raise HTTPException(status_code=500, detail="Failed to create index")
    
    # Apps
    async def get_apps(self, config_id: int) -> List[Dict[str, Any]]:
        """Get apps for a configuration"""
        try:
            config = await self.get_config(config_id)
            
            if not acs_rate_limiter.can_make_call():
                wait_time = acs_rate_limiter.get_wait_time()
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded. Try again in {wait_time} seconds"
                )
            
            start_time = time.time()
            
            async with SplunkCloudClient(
                config.stack_id,
                credential_manager.decrypt(config.auth_token),
                config.region
            ) as client:
                result = await client.get_apps()
                
                response_time = time.time() - start_time
                acs_metrics_collector.record_operation("get_apps", True, response_time)
                
                return result
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get apps for config {config_id}: {e}")
            acs_metrics_collector.record_operation("get_apps", False, 0)
            raise HTTPException(status_code=500, detail="Failed to retrieve apps")
    
    # Users
    async def get_users(self, config_id: int) -> List[Dict[str, Any]]:
        """Get users for a configuration"""
        try:
            config = await self.get_config(config_id)
            
            if not acs_rate_limiter.can_make_call():
                wait_time = acs_rate_limiter.get_wait_time()
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded. Try again in {wait_time} seconds"
                )
            
            start_time = time.time()
            
            async with SplunkCloudClient(
                config.stack_id,
                credential_manager.decrypt(config.auth_token),
                config.region
            ) as client:
                result = await client.get_users()
                
                response_time = time.time() - start_time
                acs_metrics_collector.record_operation("get_users", True, response_time)
                
                return result
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get users for config {config_id}: {e}")
            acs_metrics_collector.record_operation("get_users", False, 0)
            raise HTTPException(status_code=500, detail="Failed to retrieve users")
    
    # Health Check
    async def health_check(self, config_id: int) -> Dict[str, Any]:
        """Check Splunk Cloud API health"""
        try:
            config = await self.get_config(config_id)
            
            if not acs_rate_limiter.can_make_call():
                wait_time = acs_rate_limiter.get_wait_time()
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded. Try again in {wait_time} seconds"
                )
            
            start_time = time.time()
            
            async with SplunkCloudClient(
                config.stack_id,
                credential_manager.decrypt(config.auth_token),
                config.region
            ) as client:
                result = await client.health_check()
                
                response_time = time.time() - start_time
                acs_metrics_collector.record_operation("health_check", True, response_time)
                
                return result
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to check health for config {config_id}: {e}")
            acs_metrics_collector.record_operation("health_check", False, 0)
            raise HTTPException(status_code=500, detail="Failed to check health")
    
    # Change Management
    async def get_change_requests(
        self, 
        status: Optional[str] = None, 
        change_type: Optional[str] = None, 
        priority: Optional[str] = None
    ) -> List[ChangeRequest]:
        """Get change requests with optional filters"""
        try:
            query = self.db.query(ChangeRequest)
            
            if status:
                query = query.filter(ChangeRequest.status == status)
            
            if change_type:
                query = query.filter(ChangeRequest.change_type == change_type)
            
            if priority:
                query = query.filter(ChangeRequest.priority == priority)
            
            return query.order_by(ChangeRequest.created_at.desc()).all()
            
        except Exception as e:
            logger.error(f"Failed to get change requests: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve change requests")
    
    async def create_change_request(self, change_data: ChangeRequestCreate, user_id: int) -> ChangeRequest:
        """Create new change request"""
        try:
            return await self.workflow.create_change_request(change_data.dict(), user_id)
        except Exception as e:
            logger.error(f"Failed to create change request: {e}")
            raise HTTPException(status_code=500, detail="Failed to create change request")
    
    async def get_change_request(self, request_id: str) -> ChangeRequest:
        """Get specific change request"""
        try:
            change_request = self.db.query(ChangeRequest).filter(
                ChangeRequest.request_id == request_id
            ).first()
            
            if not change_request:
                raise HTTPException(status_code=404, detail="Change request not found")
            
            return change_request
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get change request {request_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve change request")
    
    # Version Control
    async def get_configuration_versions(
        self, 
        resource_type: Optional[str] = None, 
        resource_id: Optional[str] = None
    ) -> List[ConfigurationVersion]:
        """Get configuration versions with optional filters"""
        try:
            query = self.db.query(ConfigurationVersion)
            
            if resource_type:
                query = query.filter(ConfigurationVersion.resource_type == resource_type)
            
            if resource_id:
                query = query.filter(ConfigurationVersion.resource_id == resource_id)
            
            return query.order_by(ConfigurationVersion.created_at.desc()).all()
            
        except Exception as e:
            logger.error(f"Failed to get configuration versions: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve configuration versions")
    
    async def rollback_to_version(self, version_id: str, user_id: int, reason: str) -> ChangeRequest:
        """Rollback to specific version"""
        try:
            return await self.versioning.rollback_to_version(version_id, user_id, reason)
        except Exception as e:
            logger.error(f"Failed to rollback to version {version_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to rollback to version")
    
    # Metrics
    async def get_metrics(self) -> Dict[str, Any]:
        """Get ACS operation metrics"""
        try:
            return acs_metrics_collector.get_metrics()
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve metrics")
    
    # Utility Methods
    async def _log_operation(
        self, 
        operation_type: str, 
        resource_type: str, 
        user_id: int,
        status: str = "pending",
        resource_id: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None
    ):
        """Log ACS operation for audit trail"""
        try:
            operation = ACSOperation(
                operation_type=operation_type,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                status=status,
                configuration=configuration
            )
            
            self.db.add(operation)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log operation: {e}")
            # Don't raise here as this is not critical to the main operation
