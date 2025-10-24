"""
Splunk ACS Utilities
Utility functions for credential encryption and other ACS operations
"""
import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manages encryption and decryption of sensitive credentials"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize credential manager
        
        Args:
            encryption_key: Optional encryption key. If not provided, will use environment variable
                          or generate a new one
        """
        self.encryption_key = encryption_key or self._get_or_generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_generate_key(self) -> bytes:
        """Get encryption key from environment or generate a new one"""
        key = os.getenv('SIEMPLY_ENCRYPTION_KEY')
        
        if key:
            try:
                # Try to decode existing key
                return base64.urlsafe_b64decode(key)
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
                # Generate new key if existing one is invalid
                pass
        
        # Generate new key
        new_key = Fernet.generate_key()
        
        # Save to environment variable for future use
        os.environ['SIEMPLY_ENCRYPTION_KEY'] = base64.urlsafe_b64encode(new_key).decode()
        
        logger.info("Generated new encryption key for SIEMply")
        return new_key
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data
        
        Args:
            data: String data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        try:
            encrypted_bytes = self.cipher.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise ValueError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted string data
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise ValueError(f"Decryption failed: {e}")
    
    def rotate_key(self) -> str:
        """
        Rotate encryption key (for security purposes)
        
        Returns:
            New encryption key as base64 string
        """
        new_key = Fernet.generate_key()
        os.environ['SIEMPLY_ENCRYPTION_KEY'] = base64.urlsafe_b64encode(new_key).decode()
        
        logger.info("Rotated encryption key for SIEMply")
        return base64.urlsafe_b64encode(new_key).decode()


class ACSConfigValidator:
    """Validates Splunk Cloud configuration data"""
    
    @staticmethod
    def validate_stack_id(stack_id: str) -> bool:
        """Validate Splunk Cloud stack ID format"""
        if not stack_id or not isinstance(stack_id, str):
            return False
        
        # Stack ID should be alphanumeric with possible hyphens
        if not stack_id.replace('-', '').replace('_', '').isalnum():
            return False
        
        # Stack ID should be reasonable length
        if len(stack_id) < 3 or len(stack_id) > 50:
            return False
        
        return True
    
    @staticmethod
    def validate_region(region: str) -> bool:
        """Validate Splunk Cloud region format"""
        if not region or not isinstance(region, str):
            return False
        
        # Common Splunk Cloud regions
        valid_regions = [
            'us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
            'ca-central-1', 'sa-east-1', 'af-south-1'
        ]
        
        return region.lower() in valid_regions
    
    @staticmethod
    def validate_environment(environment: str) -> bool:
        """Validate environment value"""
        if not environment or not isinstance(environment, str):
            return False
        
        valid_environments = ['prod', 'dev', 'staging', 'test']
        return environment.lower() in valid_environments


class ACSRateLimiter:
    """Simple rate limiter for Splunk Cloud API calls"""
    
    def __init__(self, max_calls: int = 100, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_make_call(self) -> bool:
        """Check if a call can be made"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.time_window)
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if call_time > cutoff]
        
        # Check if we can make another call
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def get_wait_time(self) -> int:
        """Get time to wait before next call can be made"""
        if not self.calls:
            return 0
        
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        oldest_call = min(self.calls)
        next_available = oldest_call + timedelta(seconds=self.time_window)
        
        if next_available > now:
            return int((next_available - now).total_seconds())
        
        return 0


class ACSMetricsCollector:
    """Collects metrics for ACS operations"""
    
    def __init__(self):
        self.operation_counts = {}
        self.error_counts = {}
        self.response_times = []
    
    def record_operation(self, operation_type: str, success: bool, response_time: float):
        """Record operation metrics"""
        # Count operations
        if operation_type not in self.operation_counts:
            self.operation_counts[operation_type] = {'total': 0, 'success': 0, 'failed': 0}
        
        self.operation_counts[operation_type]['total'] += 1
        
        if success:
            self.operation_counts[operation_type]['success'] += 1
        else:
            self.operation_counts[operation_type]['failed'] += 1
            
            # Count errors
            if operation_type not in self.error_counts:
                self.error_counts[operation_type] = 0
            self.error_counts[operation_type] += 1
        
        # Record response time
        self.response_times.append(response_time)
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_metrics(self) -> dict:
        """Get collected metrics"""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            'operation_counts': self.operation_counts,
            'error_counts': self.error_counts,
            'response_times': {
                'average': avg_response_time,
                'min': min(self.response_times) if self.response_times else 0,
                'max': max(self.response_times) if self.response_times else 0,
                'total_operations': len(self.response_times)
            }
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.operation_counts = {}
        self.error_counts = {}
        self.response_times = []


# Global instances
credential_manager = CredentialManager()
acs_config_validator = ACSConfigValidator()
acs_rate_limiter = ACSRateLimiter()
acs_metrics_collector = ACSMetricsCollector()
