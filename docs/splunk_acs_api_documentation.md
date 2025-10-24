# Splunk ACS API Documentation

## Overview

The Splunk Admin Config Service (ACS) API is integrated into the main SIEMply application and provides comprehensive management capabilities for Splunk Cloud configurations. All endpoints are prefixed with `/splunk-acs` and require authentication.

**Base URL**: `http://192.168.100.44:5050/splunk-acs`

## Authentication

All ACS endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Configuration Management

#### Get All Configurations
```http
GET /splunk-acs/config
```

**Response**: List of SplunkCloudConfig objects
```json
[
  {
    "id": 1,
    "name": "Production Stack",
    "stack_id": "prod-stack-123",
    "region": "us-east-1",
    "environment": "prod",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

#### Create Configuration
```http
POST /splunk-acs/config
```

**Request Body**:
```json
{
  "name": "Production Stack",
  "stack_id": "prod-stack-123",
  "auth_token": "your_auth_token",
  "region": "us-east-1",
  "environment": "prod"
}
```

#### Get Configuration by ID
```http
GET /splunk-acs/config/{config_id}
```

#### Update Configuration
```http
PUT /splunk-acs/config/{config_id}
```

#### Delete Configuration
```http
DELETE /splunk-acs/config/{config_id}
```

### 2. IP Allow Lists

#### Get IP Allow Lists
```http
GET /splunk-acs/config/{config_id}/ip-allow-lists
```

#### Create IP Allow List
```http
POST /splunk-acs/config/{config_id}/ip-allow-lists
```

**Request Body**:
```json
{
  "name": "Office Network",
  "description": "Office IP ranges",
  "ip_ranges": ["192.168.1.0/24", "10.0.0.0/8"]
}
```

#### Update IP Allow List
```http
PUT /splunk-acs/config/{config_id}/ip-allow-lists/{list_id}
```

#### Delete IP Allow List
```http
DELETE /splunk-acs/config/{config_id}/ip-allow-lists/{list_id}
```

### 3. Index Management

#### Get Indexes
```http
GET /splunk-acs/config/{config_id}/indexes
```

#### Create Index
```http
POST /splunk-acs/config/{config_id}/indexes
```

**Request Body**:
```json
{
  "name": "web_logs",
  "maxTotalDataSizeMB": 10000,
  "frozenTimePeriodInSecs": 7776000
}
```

#### Update Index
```http
PUT /splunk-acs/config/{config_id}/indexes/{index_name}
```

#### Delete Index
```http
DELETE /splunk-acs/config/{config_id}/indexes/{index_name}
```

### 4. Application Management

#### Get Apps
```http
GET /splunk-acs/config/{config_id}/apps
```

#### Create App
```http
POST /splunk-acs/config/{config_id}/apps
```

**Request Body**:
```json
{
  "name": "custom_app",
  "description": "Custom application for data processing"
}
```

#### Update App
```http
PUT /splunk-acs/config/{config_id}/apps/{app_name}
```

#### Delete App
```http
DELETE /splunk-acs/config/{config_id}/apps/{app_name}
```

### 5. User Management

#### Get Users
```http
GET /splunk-acs/config/{config_id}/users
```

#### Create User
```http
POST /splunk-acs/config/{config_id}/users
```

**Request Body**:
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "role": "user",
  "real_name": "New User"
}
```

#### Update User
```http
PUT /splunk-acs/config/{config_id}/users/{username}
```

#### Delete User
```http
DELETE /splunk-acs/config/{config_id}/users/{username}
```

### 6. Change Request Management

#### Get Change Requests
```http
GET /splunk-acs/changes
```

**Query Parameters**:
- `status`: Filter by status (draft, pending, approved, implemented, rejected)
- `priority`: Filter by priority (low, medium, high, critical)
- `change_type`: Filter by type (configuration, emergency, scheduled)

#### Create Change Request
```http
POST /splunk-acs/changes
```

**Request Body**:
```json
{
  "title": "Update IP Allow List",
  "description": "Add new office IP range",
  "change_type": "configuration",
  "priority": "medium",
  "resource_type": "ip_allow_list",
  "resource_id": "list_123",
  "proposed_changes": {
    "action": "add_ip_range",
    "ip_range": "192.168.2.0/24"
  },
  "risk_assessment": "low",
  "implementation_plan": "Update during maintenance window",
  "rollback_plan": "Remove IP range if issues occur"
}
```

#### Get Change Request by ID
```http
GET /splunk-acs/changes/{request_id}
```

#### Update Change Request
```http
PUT /splunk-acs/changes/{request_id}
```

#### Approve Change Request
```http
POST /splunk-acs/changes/{request_id}/approve
```

**Request Body**:
```json
{
  "approver_id": 123,
  "comments": "Approved after security review"
}
```

#### Reject Change Request
```http
POST /splunk-acs/changes/{request_id}/reject
```

**Request Body**:
```json
{
  "rejector_id": 123,
  "reason": "Security concerns with proposed changes"
}
```

#### Implement Change Request
```http
POST /splunk-acs/changes/{request_id}/implement
```

### 7. Version Control

#### Get Version History
```http
GET /splunk-acs/config/{config_id}/versions
```

#### Get Version Details
```http
GET /splunk-acs/config/{config_id}/versions/{version_id}
```

#### Rollback to Version
```http
POST /splunk-acs/config/{config_id}/versions/{version_id}/rollback
```

**Request Body**:
```json
{
  "reason": "Performance issues with current configuration",
  "emergency": false
}
```

#### Compare Versions
```http
GET /splunk-acs/config/{config_id}/versions/compare?from={version1}&to={version2}
```

### 8. Health Check

#### Check ACS Health
```http
GET /splunk-acs/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "splunk_cloud": "connected",
    "database": "connected",
    "encryption": "active"
  }
}
```

## Error Handling

All endpoints return standard HTTP status codes and error messages:

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

#### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

#### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

The ACS API implements rate limiting to prevent abuse:
- **Standard endpoints**: 100 requests per minute
- **Configuration changes**: 10 requests per minute
- **Bulk operations**: 5 requests per minute

## Data Validation

### IP Address Validation
- Supports IPv4 and IPv6 addresses
- Supports CIDR notation (e.g., 192.168.1.0/24)
- Validates format and range

### Configuration Validation
- Stack ID format validation
- Region validation against supported regions
- Environment validation (prod, dev, staging)

### Change Request Validation
- Required field validation
- Priority and risk assessment validation
- Scheduled date validation for scheduled changes

## Security Features

### Credential Encryption
- All sensitive data (tokens, passwords) are encrypted using Fernet encryption
- Encryption keys are managed securely
- Key rotation capabilities

### Audit Logging
- All operations are logged with user, timestamp, and details
- Change tracking for compliance
- Rollback capabilities

### Access Control
- Role-based access control
- Multi-level approval workflows
- Emergency change procedures

## Usage Examples

### Python Client Example
```python
import requests

# Base configuration
base_url = "http://192.168.100.44:5050/splunk-acs"
headers = {"Authorization": "Bearer your_jwt_token"}

# Get all configurations
response = requests.get(f"{base_url}/config", headers=headers)
configs = response.json()

# Create IP allow list
allow_list_data = {
    "name": "Office Network",
    "ip_ranges": ["192.168.1.0/24"]
}
response = requests.post(
    f"{base_url}/config/{config_id}/ip-allow-lists",
    json=allow_list_data,
    headers=headers
)
```

### cURL Examples

#### Get Configurations
```bash
curl -H "Authorization: Bearer your_jwt_token" \
     http://192.168.100.44:5050/splunk-acs/config
```

#### Create Change Request
```bash
curl -X POST \
     -H "Authorization: Bearer your_jwt_token" \
     -H "Content-Type: application/json" \
     -d '{"title":"Update Config","change_type":"configuration"}' \
     http://192.168.100.44:5050/splunk-acs/changes
```

## Support

For technical support or questions about the ACS API:
- Check the SIEMply documentation
- Review the API health endpoint
- Contact the SIEMply development team

## Version History

- **v1.0.0**: Initial release with basic ACS functionality
- **v1.1.0**: Added change request workflow and version control
- **v1.2.0**: Enhanced security features and audit logging
