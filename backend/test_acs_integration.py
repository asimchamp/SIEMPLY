#!/usr/bin/env python3
"""
Test script for Splunk ACS integration
Verifies that the ACS module is properly integrated into the main SIEMply application
"""
import sys
import os
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def test_acs_imports():
    """Test that all ACS components can be imported"""
    print("🔍 Testing ACS module imports...")
    
    try:
        # Test main ACS module import
        from backend.splunk_acs import splunk_acs_router
        print("✅ ACS router imported successfully")
        
        # Test individual components
        from backend.splunk_acs.splunk_acs_models import SplunkCloudConfig, ChangeRequest
        print("✅ ACS models imported successfully")
        
        from backend.splunk_acs.splunk_acs_services import ACSService
        print("✅ ACS services imported successfully")
        
        from backend.splunk_acs.splunk_acs_client import SplunkCloudClient
        print("✅ ACS client imported successfully")
        
        from backend.splunk_acs.splunk_acs_workflow import ChangeRequestWorkflow
        print("✅ ACS workflow imported successfully")
        
        from backend.splunk_acs.splunk_acs_versioning import ConfigurationVersionControl
        print("✅ ACS versioning imported successfully")
        
        from backend.splunk_acs.splunk_acs_utils import CredentialManager
        print("✅ ACS utilities imported successfully")
        
        from backend.splunk_acs.splunk_acs_validators import validate_ip_allow_list
        print("✅ ACS validators imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_acs_router():
    """Test that the ACS router is properly configured"""
    print("\n🔍 Testing ACS router configuration...")
    
    try:
        from backend.splunk_acs import splunk_acs_router
        
        # Check router prefix
        if splunk_acs_router.prefix == "/splunk-acs":
            print("✅ Router prefix configured correctly: /splunk-acs")
        else:
            print(f"❌ Router prefix incorrect: {splunk_acs_router.prefix}")
            return False
        
        # Check router tags
        if "splunk-acs" in splunk_acs_router.tags:
            print("✅ Router tags configured correctly")
        else:
            print(f"❌ Router tags incorrect: {splunk_acs_router.tags}")
            return False
        
        # Count routes
        route_count = len(splunk_acs_router.routes)
        print(f"✅ Router has {route_count} routes configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Router test failed: {e}")
        return False

def test_credential_encryption():
    """Test credential encryption functionality"""
    print("\n🔍 Testing credential encryption...")
    
    try:
        from backend.splunk_acs.splunk_acs_utils import CredentialManager
        
        # Create credential manager
        cred_manager = CredentialManager()
        
        # Test encryption/decryption
        test_data = "test_splunk_token_12345"
        encrypted = cred_manager.encrypt(test_data)
        decrypted = cred_manager.decrypt(encrypted)
        
        if decrypted == test_data:
            print("✅ Credential encryption/decryption working correctly")
            return True
        else:
            print(f"❌ Encryption/decryption failed: {decrypted} != {test_data}")
            return False
            
    except Exception as e:
        print(f"❌ Credential encryption test failed: {e}")
        return False

def test_validation():
    """Test validation functions"""
    print("\n🔍 Testing validation functions...")
    
    try:
        from backend.splunk_acs.splunk_acs_validators import validate_ip_allow_list
        
        # Test valid IP allow list
        valid_data = {
            "name": "test_allow_list",
            "ip_ranges": ["192.168.1.0/24", "10.0.0.1"],
            "description": "Test allow list"
        }
        
        validated = validate_ip_allow_list(valid_data)
        if validated["name"] == "test_allow_list" and len(validated["ip_ranges"]) == 2:
            print("✅ IP allow list validation working correctly")
            return True
        else:
            print("❌ IP allow list validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False

def main():
    """Run all ACS integration tests"""
    print("🚀 Starting Splunk ACS Integration Tests")
    print("=" * 50)
    
    tests = [
        test_acs_imports,
        test_acs_router,
        test_credential_encryption,
        test_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"❌ Test {test.__name__} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! ACS integration is working correctly.")
        print("\n📝 Next steps:")
        print("1. Restart the SIEMply backend server to load the ACS module")
        print("2. Test ACS endpoints via API calls")
        print("3. Verify frontend ACS pages are accessible")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
