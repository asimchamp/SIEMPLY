"""
Splunk ACS Module
Admin Config Service (ACS) integration for Splunk Cloud
"""

__version__ = "1.0.0"
__author__ = "SIEMply Team"

# Core models
from .splunk_acs_models import (
    SplunkCloudConfig,
    ACSOperation,
    ChangeRequest,
    ConfigurationVersion,
    ApprovalWorkflow,
    # Pydantic models
    SplunkCloudConfigCreate,
    SplunkCloudConfigUpdate,
    SplunkCloudConfigResponse,
    ChangeRequestCreate,
    ChangeRequestUpdate,
    ChangeRequestResponse,
    ConfigurationVersionResponse,
    ApprovalWorkflowResponse
)

# Core services
from .splunk_acs_services import ACSService
from .splunk_acs_client import SplunkCloudClient
from .splunk_acs_workflow import ChangeRequestWorkflow
from .splunk_acs_versioning import ConfigurationVersionControl
from .splunk_acs_notifications import NotificationService

# Utilities
from .splunk_acs_utils import (
    CredentialManager,
    ACSConfigValidator,
    ACSRateLimiter,
    ACSMetricsCollector,
    credential_manager,
    acs_config_validator,
    acs_rate_limiter,
    acs_metrics_collector
)

# Validators
from .splunk_acs_validators import (
    validate_ip_allow_list,
    validate_index_config,
    validate_user_config,
    validate_maintenance_window,
    validate_hec_token
)

# API router
from .splunk_acs_api import router as splunk_acs_router

__all__ = [
    # Models
    'SplunkCloudConfig',
    'ACSOperation',
    'ChangeRequest',
    'ConfigurationVersion',
    'ApprovalWorkflow',
    'SplunkCloudConfigCreate',
    'SplunkCloudConfigUpdate',
    'SplunkCloudConfigResponse',
    'ChangeRequestCreate',
    'ChangeRequestUpdate',
    'ChangeRequestResponse',
    'ConfigurationVersionResponse',
    'ApprovalWorkflowResponse',
    
    # Services
    'ACSService',
    'SplunkCloudClient',
    'ChangeRequestWorkflow',
    'ConfigurationVersionControl',
    'NotificationService',
    
    # Utilities
    'CredentialManager',
    'ACSConfigValidator',
    'ACSRateLimiter',
    'ACSMetricsCollector',
    'credential_manager',
    'acs_config_validator',
    'acs_rate_limiter',
    'acs_metrics_collector',
    
    # Validators
    'validate_ip_allow_list',
    'validate_index_config',
    'validate_user_config',
    'validate_maintenance_window',
    'validate_hec_token',
    
    # API Router
    'splunk_acs_router',
]
