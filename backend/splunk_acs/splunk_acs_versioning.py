"""
Splunk ACS Version Control
Manages configuration versioning and rollback capabilities
"""
import logging
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import and_

from .splunk_acs_models import ConfigurationVersion, ChangeRequest
from .splunk_acs_workflow import ChangeRequestWorkflow

logger = logging.getLogger(__name__)


class ConfigurationVersionControl:
    """Manages configuration versioning and rollback capabilities"""
    
    def __init__(self, db: Session):
        self.db = db
        self.workflow = ChangeRequestWorkflow(db)
    
    async def create_version_snapshot(
        self, 
        change_request: ChangeRequest,
        current_config: Optional[Dict[str, Any]] = None
    ) -> ConfigurationVersion:
        """Create a version snapshot before implementing changes"""
        try:
            # Generate semantic version
            version_id = self._generate_semantic_version(change_request.resource_type, change_request.resource_id)
            
            # Create version record
            version = ConfigurationVersion(
                version_id=version_id,
                change_request_id=change_request.id,
                resource_type=change_request.resource_type,
                resource_id=change_request.resource_id,
                previous_config=current_config,
                new_config=change_request.proposed_changes,
                diff_summary=self._generate_diff_summary(current_config, change_request.proposed_changes),
                created_by=change_request.requester_id
            )
            
            self.db.add(version)
            self.db.commit()
            self.db.refresh(version)
            
            logger.info(f"Created version snapshot {version_id} for {change_request.resource_type}/{change_request.resource_id}")
            return version
            
        except Exception as e:
            logger.error(f"Failed to create version snapshot: {e}")
            raise HTTPException(status_code=500, detail="Failed to create version snapshot")
    
    def _generate_semantic_version(self, resource_type: str, resource_id: str) -> str:
        """Generate semantic version (e.g., v1.2.3)"""
        try:
            # Get existing versions for this resource
            existing_versions = self.db.query(ConfigurationVersion).filter(
                and_(
                    ConfigurationVersion.resource_type == resource_type,
                    ConfigurationVersion.resource_id == resource_id
                )
            ).order_by(ConfigurationVersion.created_at.desc()).all()
            
            if not existing_versions:
                # First version
                return "v1.0.0"
            
            # Parse the latest version
            latest_version = existing_versions[0].version_id
            if not latest_version.startswith('v'):
                latest_version = "v1.0.0"
            
            # Extract version numbers
            try:
                version_parts = latest_version[1:].split('.')
                major = int(version_parts[0])
                minor = int(version_parts[1])
                patch = int(version_parts[2])
                
                # Increment patch version
                new_version = f"v{major}.{minor}.{patch + 1}"
                
            except (ValueError, IndexError):
                # Fallback to simple increment
                new_version = "v1.0.1"
            
            return new_version
            
        except Exception as e:
            logger.error(f"Failed to generate semantic version: {e}")
            # Fallback to timestamp-based version
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            return f"v1.0.0_{timestamp}"
    
    def _generate_diff_summary(self, old_config: Optional[Dict[str, Any]], new_config: Dict[str, Any]) -> str:
        """Generate human-readable diff summary"""
        try:
            if not old_config:
                return "Initial configuration"
            
            changes = []
            
            # Find added fields
            for key in new_config:
                if key not in old_config:
                    changes.append(f"Added: {key}")
                elif old_config[key] != new_config[key]:
                    changes.append(f"Modified: {key}")
            
            # Find removed fields
            for key in old_config:
                if key not in new_config:
                    changes.append(f"Removed: {key}")
            
            if not changes:
                return "No changes detected"
            
            return "; ".join(changes)
            
        except Exception as e:
            logger.error(f"Failed to generate diff summary: {e}")
            return "Configuration change"
    
    async def rollback_to_version(self, version_id: str, user_id: int, reason: str = None) -> ChangeRequest:
        """Rollback to a specific version with emergency approval"""
        try:
            # Get the version to rollback to
            version = self.db.query(ConfigurationVersion).filter(
                ConfigurationVersion.version_id == version_id
            ).first()
            
            if not version:
                raise HTTPException(status_code=404, detail="Version not found")
            
            if not version.can_rollback:
                raise HTTPException(status_code=400, detail="This version cannot be rolled back")
            
            # Check if there are active change requests for this resource
            active_requests = self.db.query(ChangeRequest).filter(
                and_(
                    ChangeRequest.resource_type == version.resource_type,
                    ChangeRequest.resource_id == version.resource_id,
                    ChangeRequest.status.in_(["draft", "pending", "approved"])
                )
            ).count()
            
            if active_requests > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot rollback: {active_requests} active change requests exist for this resource"
                )
            
            # Create emergency rollback change request
            rollback_data = {
                'title': f"Emergency Rollback to {version.version_id}",
                'description': f"Rollback to previous configuration. Reason: {reason or 'User requested rollback'}",
                'change_type': 'emergency_rollback',
                'priority': 'critical',
                'resource_type': version.resource_type,
                'resource_id': version.resource_id,
                'proposed_changes': version.previous_config or {},
                'risk_assessment': 'low',  # Rollback is generally low risk
                'implementation_plan': f"Rollback configuration to version {version.version_id}",
                'rollback_plan': f"Current configuration can be restored from version {version.version_id}"
            }
            
            # Create and auto-approve emergency rollback (admin only)
            rollback_request = await self.workflow.create_change_request(rollback_data, user_id)
            
            # Auto-approve emergency rollback
            await self._auto_approve_emergency_rollback(rollback_request.id)
            
            logger.info(f"Created emergency rollback request {rollback_request.request_id} to version {version_id}")
            return rollback_request
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to rollback to version {version_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to rollback to version")
    
    async def _auto_approve_emergency_rollback(self, change_request_id: int):
        """Auto-approve emergency rollback change request"""
        try:
            # Get the change request
            change_request = self.db.query(ChangeRequest).filter(
                ChangeRequest.id == change_request_id
            ).first()
            
            if not change_request:
                return
            
            # Mark as approved immediately for emergency rollbacks
            change_request.status = "approved"
            change_request.approved_at = datetime.utcnow()
            change_request.updated_at = datetime.utcnow()
            
            # Approve all workflow levels
            workflows = self.db.query(ChangeRequest).filter(
                ChangeRequest.change_request_id == change_request_id
            ).all()
            
            for workflow in workflows:
                workflow.status = "approved"
                workflow.approved_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Auto-approved emergency rollback request {change_request.request_id}")
            
        except Exception as e:
            logger.error(f"Failed to auto-approve emergency rollback: {e}")
    
    async def get_version_history(
        self, 
        resource_type: str, 
        resource_id: str,
        limit: int = 50
    ) -> List[ConfigurationVersion]:
        """Get version history for a specific resource"""
        try:
            versions = self.db.query(ConfigurationVersion).filter(
                and_(
                    ConfigurationVersion.resource_type == resource_type,
                    ConfigurationVersion.resource_id == resource_id
                )
            ).order_by(ConfigurationVersion.created_at.desc()).limit(limit).all()
            
            return versions
            
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve version history")
    
    async def get_version_details(self, version_id: str) -> ConfigurationVersion:
        """Get detailed information about a specific version"""
        try:
            version = self.db.query(ConfigurationVersion).filter(
                ConfigurationVersion.version_id == version_id
            ).first()
            
            if not version:
                raise HTTPException(status_code=404, detail="Version not found")
            
            return version
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get version details: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve version details")
    
    async def compare_versions(self, version_id_1: str, version_id_2: str) -> Dict[str, Any]:
        """Compare two versions and return differences"""
        try:
            version_1 = await self.get_version_details(version_id_1)
            version_2 = await self.get_version_details(version_id_2)
            
            # Generate detailed diff
            diff_result = self._generate_detailed_diff(
                version_1.new_config,
                version_2.new_config
            )
            
            return {
                'version_1': {
                    'id': version_1.version_id,
                    'created_at': version_1.created_at,
                    'created_by': version_1.created_by
                },
                'version_2': {
                    'id': version_2.version_id,
                    'created_at': version_2.created_at,
                    'created_by': version_2.created_by
                },
                'differences': diff_result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            raise HTTPException(status_code=500, detail="Failed to compare versions")
    
    def _generate_detailed_diff(self, config_1: Dict[str, Any], config_2: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed diff between two configurations"""
        try:
            diff_result = {
                'added': {},
                'removed': {},
                'modified': {},
                'unchanged': {}
            }
            
            # Find added and modified fields
            for key in config_2:
                if key not in config_1:
                    diff_result['added'][key] = config_2[key]
                elif config_1[key] != config_2[key]:
                    diff_result['modified'][key] = {
                        'old_value': config_1[key],
                        'new_value': config_2[key]
                    }
                else:
                    diff_result['unchanged'][key] = config_2[key]
            
            # Find removed fields
            for key in config_1:
                if key not in config_2:
                    diff_result['removed'][key] = config_1[key]
            
            return diff_result
            
        except Exception as e:
            logger.error(f"Failed to generate detailed diff: {e}")
            return {'error': 'Failed to generate diff'}
    
    async def mark_version_inactive(self, version_id: str, user_id: int, reason: str = None):
        """Mark a version as inactive (cannot be rolled back to)"""
        try:
            version = await self.get_version_details(version_id)
            
            # Check if version is currently active
            if not version.is_active:
                raise HTTPException(status_code=400, detail="Version is already inactive")
            
            # Mark as inactive
            version.is_active = False
            version.can_rollback = False
            
            self.db.commit()
            
            logger.info(f"Marked version {version_id} as inactive by user {user_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to mark version {version_id} as inactive: {e}")
            raise HTTPException(status_code=500, detail="Failed to mark version as inactive")
    
    async def get_rollback_candidates(
        self, 
        resource_type: str, 
        resource_id: str
    ) -> List[ConfigurationVersion]:
        """Get versions that can be rolled back to"""
        try:
            candidates = self.db.query(ConfigurationVersion).filter(
                and_(
                    ConfigurationVersion.resource_type == resource_type,
                    ConfigurationVersion.resource_id == resource_id,
                    ConfigurationVersion.is_active == True,
                    ConfigurationVersion.can_rollback == True
                )
            ).order_by(ConfigurationVersion.created_at.desc()).all()
            
            return candidates
            
        except Exception as e:
            logger.error(f"Failed to get rollback candidates: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve rollback candidates")
    
    async def cleanup_old_versions(
        self, 
        resource_type: str, 
        resource_id: str, 
        keep_count: int = 10
    ) -> int:
        """Clean up old versions, keeping only the specified number"""
        try:
            # Get all versions for the resource
            all_versions = self.db.query(ConfigurationVersion).filter(
                and_(
                    ConfigurationVersion.resource_type == resource_type,
                    ConfigurationVersion.resource_id == resource_id
                )
            ).order_by(ConfigurationVersion.created_at.desc()).all()
            
            if len(all_versions) <= keep_count:
                return 0  # No cleanup needed
            
            # Mark old versions as inactive
            versions_to_cleanup = all_versions[keep_count:]
            cleanup_count = 0
            
            for version in versions_to_cleanup:
                version.is_active = False
                version.can_rollback = False
                cleanup_count += 1
            
            self.db.commit()
            
            logger.info(f"Cleaned up {cleanup_count} old versions for {resource_type}/{resource_id}")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old versions: {e}")
            raise HTTPException(status_code=500, detail="Failed to cleanup old versions")
