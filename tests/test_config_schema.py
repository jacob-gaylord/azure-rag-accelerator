"""
Test the SharePoint configuration schema independently.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add backend path
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "backend"))

from prepdocslib.config_schema import (
    get_sharepoint_schema,
    get_ingestion_config_schema,
    validate_config_against_schema
)
from prepdocslib.config_validator import (
    get_sharepoint_config_template,
    get_configuration_help
)


def test_sharepoint_schema_validation():
    """Test SharePoint schema validation with valid configurations"""
    print("Testing SharePoint schema validation...")
    
    # Test 1: Valid SharePoint configuration
    valid_config = {
        "type": "sharepoint",
        "tenant_id": "12345678-1234-1234-1234-123456789012",
        "client_id": "87654321-4321-4321-4321-210987654321",
        "client_secret": "test-secret",
        "site_url": "https://contoso.sharepoint.com/sites/test",
        "document_library": "Shared Documents",
        "folder_path": "documents",
        "max_file_size_mb": 100,
        "supported_extensions": [".pdf", ".docx"],
        "batch_size": 50,
        "enable_incremental_sync": True,
        "metadata": {
            "description": "Test library"
        }
    }
    
    schema = get_sharepoint_schema()
    is_valid, errors = validate_config_against_schema(valid_config, schema)
    
    assert is_valid, f"Valid SharePoint configuration failed validation: {errors}"
    print("✅ Valid SharePoint configuration passed schema validation")
    
    # Test 2: Invalid SharePoint configuration (missing required fields)
    invalid_config = {
        "type": "sharepoint",
        "tenant_id": "invalid-guid",  # Invalid GUID
        "site_url": "http://not-sharepoint.com"  # Invalid URL
        # Missing client_id and client_secret
    }
    
    is_valid, errors = validate_config_against_schema(invalid_config, schema)
    
    assert not is_valid, "Invalid SharePoint configuration should fail validation"
    assert len(errors) > 0, "Should have validation errors"
    print("✅ Invalid SharePoint configuration properly rejected")
    
    # Test 3: SharePoint configuration with defaults
    minimal_config = {
        "type": "sharepoint",
        "tenant_id": "12345678-1234-1234-1234-123456789012",
        "client_id": "87654321-4321-4321-4321-210987654321",
        "client_secret": "test-secret",
        "site_url": "https://contoso.sharepoint.com/sites/minimal"
        # Other fields should use defaults
    }
    
    is_valid, errors = validate_config_against_schema(minimal_config, schema)
    assert is_valid, f"Minimal SharePoint configuration failed validation: {errors}"
    print("✅ Minimal SharePoint configuration passed schema validation")


def test_ingestion_config_schema():
    """Test complete ingestion configuration schema"""
    print("\nTesting complete ingestion configuration schema...")
    
    valid_config = {
        "data_sources": [
            {
                "type": "sharepoint",
                "tenant_id": "12345678-1234-1234-1234-123456789012",
                "client_id": "87654321-4321-4321-4321-210987654321",
                "client_secret": "test-secret",
                "site_url": "https://contoso.sharepoint.com/sites/test"
            },
            {
                "type": "local",
                "path": "./data/*",
                "metadata": {"description": "Local files"}
            }
        ],
        "azure": {
            "search_service": "test-search",
            "search_index": "test-index"
        },
        "use_vectors": True,
        "verbose": False
    }
    
    schema = get_ingestion_config_schema()
    is_valid, errors = validate_config_against_schema(valid_config, schema)
    
    assert is_valid, f"Valid ingestion configuration failed validation: {errors}"
    print("✅ Complete ingestion configuration passed schema validation")


def test_template_generation():
    """Test SharePoint template generation"""
    print("\nTesting SharePoint template generation...")
    
    template = get_sharepoint_config_template()
    
    # Verify template structure
    assert template["type"] == "sharepoint"
    assert "tenant_id" in template
    assert "client_id" in template
    assert "client_secret" in template
    assert "site_url" in template
    assert template["document_library"] == "Shared Documents"
    assert template["enable_incremental_sync"] is True
    
    # Validate template against schema
    schema = get_sharepoint_schema()
    is_valid, errors = validate_config_against_schema(template, schema)
    
    assert is_valid, f"Generated template failed validation: {errors}"
    print("✅ Generated SharePoint template passed schema validation")


def test_configuration_help():
    """Test configuration help generation"""
    print("\nTesting configuration help...")
    
    help_text = get_configuration_help()
    
    # Verify help contains key information
    assert "SharePoint Configuration" in help_text
    assert "tenant_id" in help_text
    assert "client_id" in help_text
    assert "client_secret" in help_text
    assert "site_url" in help_text
    assert "SHAREPOINT_TENANT_ID" in help_text
    
    print("✅ Configuration help is comprehensive and available")


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\nTesting edge cases...")
    
    schema = get_sharepoint_schema()
    
    # Test case 1: Maximum file size boundary
    config_max_size = {
        "type": "sharepoint",
        "tenant_id": "12345678-1234-1234-1234-123456789012",
        "client_id": "87654321-4321-4321-4321-210987654321",
        "client_secret": "test-secret",
        "site_url": "https://contoso.sharepoint.com/sites/test",
        "max_file_size_mb": 1000  # Maximum allowed
    }
    
    is_valid, errors = validate_config_against_schema(config_max_size, schema)
    assert is_valid, f"Max file size boundary test failed: {errors}"
    
    # Test case 2: Invalid file extensions
    config_invalid_ext = {
        "type": "sharepoint",
        "tenant_id": "12345678-1234-1234-1234-123456789012",
        "client_id": "87654321-4321-4321-4321-210987654321",
        "client_secret": "test-secret",
        "site_url": "https://contoso.sharepoint.com/sites/test",
        "supported_extensions": ["pdf", "docx"]  # Missing dots
    }
    
    is_valid, errors = validate_config_against_schema(config_invalid_ext, schema)
    assert not is_valid, "Invalid file extensions should fail validation"
    
    # Test case 3: Different SharePoint domains
    sharepoint_domains = [
        "https://contoso.sharepoint.com/sites/test",
        "https://contoso.sharepoint.us/sites/test",
        "https://contoso.sharepoint.de/sites/test"
    ]
    
    for domain in sharepoint_domains:
        config = {
            "type": "sharepoint",
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            "client_id": "87654321-4321-4321-4321-210987654321",
            "client_secret": "test-secret",
            "site_url": domain
        }
        
        is_valid, errors = validate_config_against_schema(config, schema)
        assert is_valid, f"SharePoint domain {domain} should be valid: {errors}"
    
    print("✅ Edge cases handled correctly")


def main():
    """Run all tests"""
    print("Running SharePoint configuration schema tests...\n")
    
    try:
        test_sharepoint_schema_validation()
        test_ingestion_config_schema()
        test_template_generation()
        test_configuration_help()
        test_edge_cases()
        
        print("\n🎉 All configuration schema tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 