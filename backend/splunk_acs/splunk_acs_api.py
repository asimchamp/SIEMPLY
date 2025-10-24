"""
Splunk ACS API Router
Main API endpoints for Splunk Cloud ACS integration
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from backend.models import get_db
from backend.api.auth import get_current_active_user
from .splunk_acs_models import (
    SplunkCloudConfigCreate,
    SplunkCloudConfigUpdate,
    SplunkCloudConfigResponse,
    ChangeRequestCreate,
    ChangeRequestUpdate,
    ChangeRequestResponse,
    ConfigurationVersionResponse,
    ApprovalWorkflowResponse
)
from .splunk_acs_services import ACSService
from .splunk_acs_validators import validate_ip_allow_list, validate_index_config
from .splunk_acs_monitoring import get_acs_monitoring_service

router = APIRouter(prefix="/splunk-acs", tags=["splunk-acs"])


# Configuration Management
@router.get("/config", response_model=List[SplunkCloudConfigResponse])
async def get_splunk_cloud_configs(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all Splunk Cloud configurations"""
    service = ACSService(db)
    return await service.get_configs()


@router.post("/config", response_model=SplunkCloudConfigResponse)
async def create_splunk_cloud_config(
    config_data: SplunkCloudConfigCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create new Splunk Cloud configuration"""
    service = ACSService(db)
    return await service.create_config(config_data, current_user.id)


@router.get("/config/{config_id}", response_model=SplunkCloudConfigResponse)
async def get_splunk_cloud_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get specific Splunk Cloud configuration"""
    service = ACSService(db)
    return await service.get_config(config_id)


@router.put("/config/{config_id}", response_model=SplunkCloudConfigResponse)
async def update_splunk_cloud_config(
    config_id: int,
    config_data: SplunkCloudConfigUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update Splunk Cloud configuration"""
    service = ACSService(db)
    return await service.update_config(config_id, config_data, current_user.id)


@router.delete("/config/{config_id}")
async def delete_splunk_cloud_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete Splunk Cloud configuration"""
    service = ACSService(db)
    await service.delete_config(config_id, current_user.id)
    return {"message": "Configuration deleted successfully"}


# IP Allow Lists
@router.get("/config/{config_id}/ip-allow-lists")
async def get_ip_allow_lists(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get IP allow lists for a configuration"""
    service = ACSService(db)
    return await service.get_ip_allow_lists(config_id)


@router.post("/config/{config_id}/ip-allow-lists")
async def create_ip_allow_list(
    config_id: int,
    list_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create new IP allow list"""
    # Validate input
    validated_data = validate_ip_allow_list(list_data)
    
    service = ACSService(db)
    return await service.create_ip_allow_list(config_id, validated_data, current_user.id)


@router.put("/config/{config_id}/ip-allow-lists/{list_id}")
async def update_ip_allow_list(
    config_id: int,
    list_id: str,
    list_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update existing IP allow list"""
    validated_data = validate_ip_allow_list(list_data)
    
    service = ACSService(db)
    return await service.update_ip_allow_list(config_id, list_id, validated_data, current_user.id)


@router.delete("/config/{config_id}/ip-allow-lists/{list_id}")
async def delete_ip_allow_list(
    config_id: int,
    list_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete IP allow list"""
    service = ACSService(db)
    await service.delete_ip_allow_list(config_id, list_id, current_user.id)
    return {"message": "IP allow list deleted successfully"}


# Outbound Ports
@router.get("/config/{config_id}/outbound-ports")
async def get_outbound_ports(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get outbound port configuration"""
    service = ACSService(db)
    return await service.get_outbound_ports(config_id)


@router.put("/config/{config_id}/outbound-ports")
async def update_outbound_ports(
    config_id: int,
    port_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update outbound port configuration"""
    service = ACSService(db)
    return await service.update_outbound_ports(config_id, port_data, current_user.id)


# Indexes
@router.get("/config/{config_id}/indexes")
async def get_indexes(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get indexes for a configuration"""
    service = ACSService(db)
    return await service.get_indexes(config_id)


@router.post("/config/{config_id}/indexes")
async def create_index(
    config_id: int,
    index_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create new index"""
    validated_data = validate_index_config(index_data)
    
    service = ACSService(db)
    return await service.create_index(config_id, validated_data, current_user.id)


@router.put("/config/{config_id}/indexes/{index_name}")
async def update_index(
    config_id: int,
    index_name: str,
    index_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update existing index"""
    validated_data = validate_index_config(index_data)
    
    service = ACSService(db)
    return await service.update_index(config_id, index_name, validated_data, current_user.id)


@router.delete("/config/{config_id}/indexes/{index_name}")
async def delete_index(
    config_id: int,
    index_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete index"""
    service = ACSService(db)
    await service.delete_index(config_id, index_name, current_user.id)
    return {"message": "Index deleted successfully"}


# Apps
@router.get("/config/{config_id}/apps")
async def get_apps(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get apps for a configuration"""
    service = ACSService(db)
    return await service.get_apps(config_id)


@router.post("/config/{config_id}/apps/{app_name}/export")
async def export_app(
    config_id: int,
    app_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export app"""
    service = ACSService(db)
    return await service.export_app(config_id, app_name, current_user.id)


@router.put("/config/{config_id}/apps/{app_name}/permissions")
async def update_app_permissions(
    config_id: int,
    app_name: str,
    permissions: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update app permissions"""
    service = ACSService(db)
    return await service.update_app_permissions(config_id, app_name, permissions, current_user.id)


# Users and Roles
@router.get("/config/{config_id}/users")
async def get_users(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get users for a configuration"""
    service = ACSService(db)
    return await service.get_users(config_id)


@router.post("/config/{config_id}/users")
async def create_user(
    config_id: int,
    user_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create new user"""
    service = ACSService(db)
    return await service.create_user(config_id, user_data, current_user.id)


@router.put("/config/{config_id}/users/{user_id}")
async def update_user(
    config_id: int,
    user_id: str,
    user_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update existing user"""
    service = ACSService(db)
    return await service.update_user(config_id, user_id, user_data, current_user.id)


@router.delete("/config/{config_id}/users/{user_id}")
async def delete_user(
    config_id: int,
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete user"""
    service = ACSService(db)
    await service.delete_user(config_id, user_id, current_user.id)
    return {"message": "User deleted successfully"}


# Authentication Tokens
@router.get("/config/{config_id}/auth-tokens")
async def get_auth_tokens(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get authentication tokens"""
    service = ACSService(db)
    return await service.get_auth_tokens(config_id)


@router.post("/config/{config_id}/auth-tokens")
async def create_auth_token(
    config_id: int,
    token_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create new authentication token"""
    service = ACSService(db)
    return await service.create_auth_token(config_id, token_data, current_user.id)


@router.delete("/config/{config_id}/auth-tokens/{token_id}")
async def revoke_auth_token(
    config_id: int,
    token_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Revoke authentication token"""
    service = ACSService(db)
    await service.revoke_auth_token(config_id, token_id, current_user.id)
    return {"message": "Token revoked successfully"}


# Maintenance Windows
@router.get("/config/{config_id}/maintenance-windows")
async def get_maintenance_windows(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get maintenance windows"""
    service = ACSService(db)
    return await service.get_maintenance_windows(config_id)


@router.post("/config/{config_id}/maintenance-windows")
async def create_maintenance_window(
    config_id: int,
    window_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create new maintenance window"""
    service = ACSService(db)
    return await service.create_maintenance_window(config_id, window_data, current_user.id)


@router.put("/config/{config_id}/maintenance-windows/{window_id}")
async def update_maintenance_window(
    config_id: int,
    window_id: str,
    window_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update existing maintenance window"""
    service = ACSService(db)
    return await service.update_maintenance_window(config_id, window_id, window_data, current_user.id)


@router.delete("/config/{config_id}/maintenance-windows/{window_id}")
async def delete_maintenance_window(
    config_id: int,
    window_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete maintenance window"""
    service = ACSService(db)
    await service.delete_maintenance_window(config_id, window_id, current_user.id)
    return {"message": "Maintenance window deleted successfully"}


# HEC Tokens
@router.get("/config/{config_id}/hec-tokens")
async def get_hec_tokens(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get HEC tokens"""
    service = ACSService(db)
    return await service.get_hec_tokens(config_id)


@router.post("/config/{config_id}/hec-tokens")
async def create_hec_token(
    config_id: int,
    token_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create new HEC token"""
    service = ACSService(db)
    return await service.create_hec_token(config_id, token_data, current_user.id)


@router.put("/config/{config_id}/hec-tokens/{token_id}")
async def update_hec_token(
    config_id: int,
    token_id: str,
    token_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update existing HEC token"""
    service = ACSService(db)
    return await service.update_hec_token(config_id, token_id, token_data, current_user.id)


@router.delete("/config/{config_id}/hec-tokens/{token_id}")
async def delete_hec_token(
    config_id: int,
    token_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete HEC token"""
    service = ACSService(db)
    await service.delete_hec_token(config_id, token_id, current_user.id)
    return {"message": "HEC token deleted successfully"}


# Limits.conf Configuration
@router.get("/config/{config_id}/limits-conf")
async def get_limits_conf(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get limits.conf configuration"""
    service = ACSService(db)
    return await service.get_limits_conf(config_id)


@router.put("/config/{config_id}/limits-conf")
async def update_limits_conf(
    config_id: int,
    limits_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update limits.conf configuration"""
    service = ACSService(db)
    return await service.update_limits_conf(config_id, limits_data, current_user.id)


# DDSS Storage
@router.get("/config/{config_id}/ddss-storage")
async def get_ddss_storage(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get DDSS storage configuration"""
    service = ACSService(db)
    return await service.get_ddss_storage(config_id)


@router.put("/config/{config_id}/ddss-storage")
async def update_ddss_storage(
    config_id: int,
    storage_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update DDSS storage configuration"""
    service = ACSService(db)
    return await service.update_ddss_storage(config_id, storage_data, current_user.id)


# Health Check
@router.get("/config/{config_id}/health")
async def health_check(
    config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Check Splunk Cloud API health"""
    service = ACSService(db)
    return await service.health_check(config_id)


# Change Management
@router.get("/change-requests", response_model=List[ChangeRequestResponse])
async def get_change_requests(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
    status: Optional[str] = Query(None, description="Filter by status"),
    change_type: Optional[str] = Query(None, description="Filter by change type"),
    priority: Optional[str] = Query(None, description="Filter by priority")
):
    """Get change requests with optional filters"""
    service = ACSService(db)
    return await service.get_change_requests(status, change_type, priority)


@router.post("/change-requests", response_model=ChangeRequestResponse)
async def create_change_request(
    change_data: ChangeRequestCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create new change request"""
    service = ACSService(db)
    return await service.create_change_request(change_data, current_user.id)


@router.get("/change-requests/{request_id}", response_model=ChangeRequestResponse)
async def get_change_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get specific change request"""
    service = ACSService(db)
    return await service.get_change_request(request_id)


@router.put("/change-requests/{request_id}", response_model=ChangeRequestResponse)
async def update_change_request(
    request_id: str,
    change_data: ChangeRequestUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update change request"""
    service = ACSService(db)
    return await service.update_change_request(request_id, change_data, current_user.id)


@router.delete("/change-requests/{request_id}")
async def delete_change_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete change request"""
    service = ACSService(db)
    await service.delete_change_request(request_id, current_user.id)
    return {"message": "Change request deleted successfully"}


@router.post("/change-requests/{request_id}/approve")
async def approve_change_request(
    request_id: str,
    level: int = Query(..., description="Approval level"),
    comments: Optional[str] = Query(None, description="Approval comments"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Approve change request at specific level"""
    service = ACSService(db)
    return await service.approve_change_request(request_id, level, current_user.id, comments)


@router.post("/change-requests/{request_id}/reject")
async def reject_change_request(
    request_id: str,
    level: int = Query(..., description="Rejection level"),
    comments: str = Query(..., description="Rejection reason"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Reject change request at specific level"""
    service = ACSService(db)
    return await service.reject_change_request(request_id, level, current_user.id, comments)


@router.post("/change-requests/{request_id}/implement")
async def implement_change_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Implement approved change request"""
    service = ACSService(db)
    return await service.implement_change_request(request_id, current_user.id)


# Version Control
@router.get("/versions", response_model=List[ConfigurationVersionResponse])
async def get_configuration_versions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID")
):
    """Get configuration versions with optional filters"""
    service = ACSService(db)
    return await service.get_configuration_versions(resource_type, resource_id)


@router.get("/versions/{resource_type}/{resource_id}", response_model=List[ConfigurationVersionResponse])
async def get_resource_versions(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get versions for specific resource"""
    service = ACSService(db)
    return await service.get_resource_versions(resource_type, resource_id)


@router.post("/versions/{version_id}/rollback")
async def rollback_to_version(
    version_id: str,
    reason: str = Query(..., description="Rollback reason"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Rollback to specific version"""
    service = ACSService(db)
    return await service.rollback_to_version(version_id, current_user.id, reason)


@router.get("/versions/{version_id}/diff")
async def get_version_diff(
    version_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get diff for specific version"""
    service = ACSService(db)
    return await service.get_version_diff(version_id)


# Approval Workflow
@router.get("/approvals", response_model=List[ApprovalWorkflowResponse])
async def get_approvals(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
    status: Optional[str] = Query(None, description="Filter by status"),
    level: Optional[int] = Query(None, description="Filter by approval level")
):
    """Get approval workflows with optional filters"""
    service = ACSService(db)
    return await service.get_approvals(status, level)


@router.post("/approvals/{request_id}/level/{level}")
async def create_approval_workflow(
    request_id: int,
    level: int,
    approver_role: str = Query(..., description="Approver role"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create approval workflow level"""
    service = ACSService(db)
    return await service.create_approval_workflow(request_id, level, approver_role, current_user.id)


@router.put("/approvals/{request_id}/level/{level}")
async def update_approval_workflow(
    request_id: int,
    level: int,
    status: str = Query(..., description="Approval status"),
    comments: Optional[str] = Query(None, description="Approval comments"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update approval workflow level"""
    service = ACSService(db)
    return await service.update_approval_workflow(request_id, level, status, current_user.id, comments)


# Monitoring & Health Check
@router.get("/health")
async def get_acs_health(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get comprehensive ACS system health status"""
    monitoring_service = get_acs_monitoring_service(db)
    return await monitoring_service.get_health_check_endpoint()


@router.get("/metrics")
async def get_acs_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get comprehensive ACS operational metrics"""
    monitoring_service = get_acs_monitoring_service(db)
    return await monitoring_service.get_operational_metrics()


@router.get("/metrics/export")
async def export_acs_metrics(
    format: str = Query("json", description="Export format (json or csv)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export ACS metrics in specified format"""
    monitoring_service = get_acs_monitoring_service(db)
    return await monitoring_service.export_metrics(format)


@router.post("/metrics/reset")
async def reset_acs_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Reset all ACS monitoring metrics"""
    monitoring_service = get_acs_monitoring_service(db)
    await monitoring_service.reset_metrics()
    return {"message": "All ACS metrics have been reset successfully"}
