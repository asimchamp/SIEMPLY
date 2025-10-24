"""
Splunk ACS Validators
Validation functions for ACS configuration data
"""
import re
import ipaddress
from typing import Dict, Any, List
from fastapi import HTTPException


def validate_ip_allow_list(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate IP allow list configuration data"""
    required_fields = ['name', 'ip_ranges']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    # Validate name
    name = data['name']
    if not isinstance(name, str) or len(name.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Name must be a non-empty string"
        )
    
    if len(name) > 100:
        raise HTTPException(
            status_code=400,
            detail="Name must be 100 characters or less"
        )
    
    # Validate IP ranges
    ip_ranges = data['ip_ranges']
    if not isinstance(ip_ranges, list) or len(ip_ranges) == 0:
        raise HTTPException(
            status_code=400,
            detail="IP ranges must be a non-empty list"
        )
    
    validated_ranges = []
    for ip_range in ip_ranges:
        if not isinstance(ip_range, str):
            raise HTTPException(
                status_code=400,
                detail="Each IP range must be a string"
            )
        
        # Validate IP range format (CIDR notation or single IP)
        try:
            if '/' in ip_range:
                # CIDR notation
                ipaddress.ip_network(ip_range, strict=False)
            else:
                # Single IP
                ipaddress.ip_address(ip_range)
            validated_ranges.append(ip_range)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid IP range format: {ip_range}"
            )
    
    # Validate description if provided
    if 'description' in data:
        description = data['description']
        if description is not None and not isinstance(description, str):
            raise HTTPException(
                status_code=400,
                detail="Description must be a string or null"
            )
        
        if description and len(description) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Description must be 1000 characters or less"
            )
    
    # Return validated data
    validated_data = {
        'name': name.strip(),
        'ip_ranges': validated_ranges
    }
    
    if 'description' in data:
        validated_data['description'] = description
    
    return validated_data


def validate_index_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate index configuration data"""
    required_fields = ['name']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    # Validate name
    name = data['name']
    if not isinstance(name, str) or len(name.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Index name must be a non-empty string"
        )
    
    if len(name) > 100:
        raise HTTPException(
            status_code=400,
            detail="Index name must be 100 characters or less"
        )
    
    # Validate index name format (alphanumeric, hyphens, underscores only)
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise HTTPException(
            status_code=400,
            detail="Index name can only contain alphanumeric characters, hyphens, and underscores"
        )
    
    # Validate maxTotalDataSizeMB if provided
    if 'maxTotalDataSizeMB' in data:
        max_size = data['maxTotalDataSizeMB']
        if max_size is not None:
            if not isinstance(max_size, int) or max_size <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="maxTotalDataSizeMB must be a positive integer"
                )
            
            if max_size > 1000000:  # 1TB limit
                raise HTTPException(
                    status_code=400,
                    detail="maxTotalDataSizeMB cannot exceed 1,000,000 MB (1TB)"
                )
    
    # Validate frozenTimePeriodInSecs if provided
    if 'frozenTimePeriodInSecs' in data:
        frozen_time = data['frozenTimePeriodInSecs']
        if frozen_time is not None:
            if not isinstance(frozen_time, int) or frozen_time < 0:
                raise HTTPException(
                    status_code=400,
                    detail="frozenTimePeriodInSecs must be a non-negative integer"
                )
            
            if frozen_time > 31536000:  # 1 year limit
                raise HTTPException(
                    status_code=400,
                    detail="frozenTimePeriodInSecs cannot exceed 31,536,000 seconds (1 year)"
                )
    
    # Validate homePath if provided
    if 'homePath' in data:
        home_path = data['homePath']
        if home_path is not None and not isinstance(home_path, str):
            raise HTTPException(
                status_code=400,
                detail="homePath must be a string or null"
            )
    
    # Validate coldPath if provided
    if 'coldPath' in data:
        cold_path = data['coldPath']
        if cold_path is not None and not isinstance(cold_path, str):
            raise HTTPException(
                status_code=400,
                detail="coldPath must be a string or null"
            )
    
    # Validate thawedPath if provided
    if 'thawedPath' in data:
        thawed_path = data['thawedPath']
        if thawed_path is not None and not isinstance(thawed_path, str):
            raise HTTPException(
                status_code=400,
                detail="thawedPath must be a string or null"
            )
    
    # Return validated data
    validated_data = {
        'name': name.strip()
    }
    
    # Add optional fields if they exist and are valid
    optional_fields = ['maxTotalDataSizeMB', 'frozenTimePeriodInSecs', 'homePath', 'coldPath', 'thawedPath']
    for field in optional_fields:
        if field in data and data[field] is not None:
            validated_data[field] = data[field]
    
    return validated_data


def validate_user_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user configuration data"""
    required_fields = ['username', 'email']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    # Validate username
    username = data['username']
    if not isinstance(username, str) or len(username.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Username must be a non-empty string"
        )
    
    if len(username) > 50:
        raise HTTPException(
            status_code=400,
            detail="Username must be 50 characters or less"
        )
    
    # Validate username format (alphanumeric, hyphens, underscores only)
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise HTTPException(
            status_code=400,
            detail="Username can only contain alphanumeric characters, hyphens, and underscores"
        )
    
    # Validate email
    email = data['email']
    if not isinstance(email, str) or len(email.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Email must be a non-empty string"
        )
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email format"
        )
    
    # Validate roles if provided
    if 'roles' in data:
        roles = data['roles']
        if not isinstance(roles, list):
            raise HTTPException(
                status_code=400,
                detail="Roles must be a list"
            )
        
        for role in roles:
            if not isinstance(role, str) or len(role.strip()) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Each role must be a non-empty string"
                )
    
    # Validate full_name if provided
    if 'full_name' in data:
        full_name = data['full_name']
        if full_name is not None and not isinstance(full_name, str):
            raise HTTPException(
                status_code=400,
                detail="Full name must be a string or null"
            )
        
        if full_name and len(full_name) > 100:
            raise HTTPException(
                status_code=400,
                detail="Full name must be 100 characters or less"
            )
    
    # Return validated data
    validated_data = {
        'username': username.strip(),
        'email': email.strip()
    }
    
    # Add optional fields if they exist and are valid
    optional_fields = ['roles', 'full_name']
    for field in optional_fields:
        if field in data and data[field] is not None:
            validated_data[field] = data[field]
    
    return validated_data


def validate_maintenance_window(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate maintenance window configuration data"""
    required_fields = ['name', 'start_time', 'end_time']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    # Validate name
    name = data['name']
    if not isinstance(name, str) or len(name.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Name must be a non-empty string"
        )
    
    if len(name) > 100:
        raise HTTPException(
            status_code=400,
            detail="Name must be 100 characters or less"
        )
    
    # Validate start_time and end_time (should be ISO 8601 format)
    start_time = data['start_time']
    end_time = data['end_time']
    
    if not isinstance(start_time, str) or not isinstance(end_time, str):
        raise HTTPException(
            status_code=400,
            detail="Start time and end time must be strings in ISO 8601 format"
        )
    
    try:
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        if start_dt >= end_dt:
            raise HTTPException(
                status_code=400,
                detail="Start time must be before end time"
            )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid datetime format. Use ISO 8601 format (e.g., 2024-01-01T00:00:00Z)"
        )
    
    # Validate description if provided
    if 'description' in data:
        description = data['description']
        if description is not None and not isinstance(description, str):
            raise HTTPException(
                status_code=400,
                detail="Description must be a string or null"
            )
        
        if description and len(description) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Description must be 1000 characters or less"
            )
    
    # Return validated data
    validated_data = {
        'name': name.strip(),
        'start_time': start_time,
        'end_time': end_time
    }
    
    if 'description' in data:
        validated_data['description'] = description
    
    return validated_data


def validate_hec_token(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate HEC token configuration data"""
    required_fields = ['name', 'token']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    # Validate name
    name = data['name']
    if not isinstance(name, str) or len(name.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Name must be a non-empty string"
        )
    
    if len(name) > 100:
        raise HTTPException(
            status_code=400,
            detail="Name must be 100 characters or less"
        )
    
    # Validate token
    token = data['token']
    if not isinstance(token, str) or len(token.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Token must be a non-empty string"
        )
    
    # Validate token format (should be a valid UUID or similar format)
    if not re.match(r'^[a-zA-Z0-9\-_]+$', token):
        raise HTTPException(
            status_code=400,
            detail="Token contains invalid characters"
        )
    
    # Validate description if provided
    if 'description' in data:
        description = data['description']
        if description is not None and not isinstance(description, str):
            raise HTTPException(
                status_code=400,
                detail="Description must be a string or null"
            )
        
        if description and len(description) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Description must be 1000 characters or less"
            )
    
    # Return validated data
    validated_data = {
        'name': name.strip(),
        'token': token.strip()
    }
    
    if 'description' in data:
        validated_data['description'] = description
    
    return validated_data
