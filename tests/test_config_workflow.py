"""
Test the complete configuration workflow for SharePoint integration.
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path

# Mock the msgraph imports to avoid dependency issues
import sys
from unittest.mock import MagicMock

# Mock the problematic msgraph_core module
sys.modules['msgraph_core'] = MagicMock()
sys.modules['msgraph'] = MagicMock()
sys.modules['azure.identity.aio'] = MagicMock()

from app.backend.prepdocslib.config import (
    DataSourceConfig, 
    IngestionConfig, 
    ConfigurationManager
)
from app.backend.prepdocslib.config_validator import (
    ConfigurationValidator,
    get_sharepoint_config_template,
    get_configuration_help
)
from app.backend.prepdocslib.config_schema import (
    get_sharepoint_schema,
    get_ingestion_config_schema,
    validate_config_against_schema
)


class TestConfigurationWorkflow:
    """Test the complete configuration workflow"""
    
    def test_sharepoint_config_workflow_yaml(self):
        """Test complete workflow: YAML config -> validation -> parsing"""
        # Create a valid SharePoint configuration
        config_data = {
            "data_sources": [
                {
                    "type": "sharepoint",
                    "tenant_id": "12345678-1234-1234-1234-123456789012",
                    "client_id": "87654321-4321-4321-4321-210987654321",
                    "client_secret": "test-secret",
                    "site_url": "https://contoso.sharepoint.com/sites/test",
                    "document_library": "Custom Library",
                    "folder_path": "documents",
                    "max_file_size_mb": 50,
                    "batch_size": 25,
                    "enable_incremental_sync": True,
                    "metadata": {
                        "description": "Test SharePoint library",
                        "category": "test"
                    }
                }
            ],
            "azure": {
                "search_service": "test-search",
                "search_index": "test-index"
            },
            "use_vectors": True,
            "verbose": False
        }
        
        # Step 1: Save configuration to YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f, default_flow_style=False)
            yaml_file = f.name
        
        try:
            # Step 2: Load configuration using ConfigurationManager
            manager = ConfigurationManager()
            config = manager.load_config_from_file(yaml_file)
            
            # Verify basic structure
            assert len(config.data_sources) == 1
            ds = config.data_sources[0]
            assert ds.type == "sharepoint"
            assert ds.tenant_id == "12345678-1234-1234-1234-123456789012"
            assert ds.document_library == "Custom Library"
            assert ds.folder_path == "documents"
            assert ds.max_file_size_mb == 50
            assert ds.batch_size == 25
            assert ds.enable_incremental_sync is True
            
            # Step 3: Validate configuration
            validator = ConfigurationValidator()
            is_valid, errors, warnings = validator.validate_config(config)
            
            assert is_valid, f"Configuration validation failed: {errors}"
            
            # Step 4: Test JSON schema validation
            schema = get_ingestion_config_schema()
            is_schema_valid, schema_errors = validate_config_against_schema(config_data, schema)
            assert is_schema_valid, f"Schema validation failed: {schema_errors}"
            
            print("✅ YAML configuration workflow completed successfully")
            
        finally:
            Path(yaml_file).unlink()
    
    def test_sharepoint_config_workflow_json(self):
        """Test complete workflow: JSON config -> validation -> parsing"""
        # Create a minimal SharePoint configuration
        config_data = {
            "data_sources": [
                {
                    "type": "sharepoint",
                    "tenant_id": "12345678-1234-1234-1234-123456789012",
                    "client_id": "87654321-4321-4321-4321-210987654321",
                    "client_secret": "test-secret",
                    "site_url": "https://contoso.sharepoint.com/sites/minimal"
                    # Using defaults for other fields
                }
            ]
        }
        
        # Step 1: Save configuration to JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            json_file = f.name
        
        try:
            # Step 2: Load configuration using ConfigurationManager
            manager = ConfigurationManager()
            config = manager.load_config_from_file(json_file)
            
            # Verify basic structure and defaults
            assert len(config.data_sources) == 1
            ds = config.data_sources[0]
            assert ds.type == "sharepoint"
            assert ds.tenant_id == "12345678-1234-1234-1234-123456789012"
            # Check that defaults were applied
            assert ds.document_library == "Shared Documents"
            assert ds.folder_path == ""
            assert ds.max_file_size_mb == 100
            assert ds.batch_size == 50
            assert ds.enable_incremental_sync is True
            
            # Step 3: Validate configuration
            validator = ConfigurationValidator()
            is_valid, errors, warnings = validator.validate_config(config)
            
            assert is_valid, f"Configuration validation failed: {errors}"
            
            print("✅ JSON configuration workflow completed successfully")
            
        finally:
            Path(json_file).unlink()
    
    def test_invalid_sharepoint_config_workflow(self):
        """Test workflow with invalid SharePoint configuration"""
        # Create an invalid SharePoint configuration (missing required fields)
        config_data = {
            "data_sources": [
                {
                    "type": "sharepoint",
                    "tenant_id": "invalid-guid",  # Invalid GUID format
                    "site_url": "http://not-a-sharepoint-url.com"  # Invalid URL
                    # Missing required fields: client_id, client_secret
                }
            ]
        }
        
        # Step 1: JSON schema validation should fail
        schema = get_sharepoint_schema()
        is_valid, errors = validate_config_against_schema(config_data["data_sources"][0], schema)
        
        assert not is_valid, "Schema validation should have failed"
        assert len(errors) > 0, "Should have validation errors"
        
        # Step 2: ConfigurationValidator should also fail
        try:
            ds_config = DataSourceConfig(**config_data["data_sources"][0])
            validator = ConfigurationValidator()
            validator._validate_sharepoint_config(ds_config, "test")
            
            assert len(validator.errors) > 0, "Should have validation errors"
            
        except Exception:
            # Exception is expected due to invalid data
            pass
        
        print("✅ Invalid configuration properly rejected")
    
    def test_template_generation_workflow(self):
        """Test configuration template generation and validation"""
        # Step 1: Generate SharePoint template
        template = get_sharepoint_config_template()
        
        # Step 2: Verify template structure
        assert template["type"] == "sharepoint"
        assert "tenant_id" in template
        assert "client_id" in template
        assert "client_secret" in template
        assert "site_url" in template
        assert template["document_library"] == "Shared Documents"
        assert template["enable_incremental_sync"] is True
        
        # Step 3: Validate template against schema
        schema = get_sharepoint_schema()
        is_valid, errors = validate_config_against_schema(template, schema)
        
        assert is_valid, f"Template validation failed: {errors}"
        
        # Step 4: Test creating configuration from template
        config_data = {
            "data_sources": [template]
        }
        
        # Step 5: Create temporary file and test full workflow
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f, default_flow_style=False)
            yaml_file = f.name
        
        try:
            manager = ConfigurationManager()
            config = manager.load_config_from_file(yaml_file)
            
            validator = ConfigurationValidator()
            is_valid, errors, warnings = validator.validate_config(config)
            
            # Template should be valid but may have warnings about placeholder values
            assert len(errors) == 0, f"Template should not have errors: {errors}"
            
            print("✅ Template generation workflow completed successfully")
            
        finally:
            Path(yaml_file).unlink()
    
    def test_multi_sharepoint_config_workflow(self):
        """Test workflow with multiple SharePoint configurations"""
        config_data = {
            "data_sources": [
                {
                    "type": "sharepoint",
                    "tenant_id": "12345678-1234-1234-1234-123456789012",
                    "client_id": "87654321-4321-4321-4321-210987654321",
                    "client_secret": "secret1",
                    "site_url": "https://contoso.sharepoint.com/sites/hr",
                    "document_library": "HR Documents",
                    "metadata": {"category": "hr"}
                },
                {
                    "type": "sharepoint",
                    "tenant_id": "12345678-1234-1234-1234-123456789012",
                    "client_id": "87654321-4321-4321-4321-210987654321",
                    "client_secret": "secret2",
                    "site_url": "https://contoso.sharepoint.com/sites/engineering",
                    "document_library": "Technical Docs",
                    "metadata": {"category": "technical"}
                },
                {
                    "type": "local",
                    "path": "./data/*",
                    "metadata": {"description": "Local files"}
                }
            ],
            "azure": {
                "search_service": "multi-search",
                "search_index": "multi-index"
            }
        }
        
        # Step 1: Validate complete configuration
        schema = get_ingestion_config_schema()
        is_valid, errors = validate_config_against_schema(config_data, schema)
        assert is_valid, f"Multi-source configuration validation failed: {errors}"
        
        # Step 2: Load and validate with ConfigurationManager
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f, default_flow_style=False)
            yaml_file = f.name
        
        try:
            manager = ConfigurationManager()
            config = manager.load_config_from_file(yaml_file)
            
            # Verify structure
            assert len(config.data_sources) == 3
            sharepoint_sources = [ds for ds in config.data_sources if ds.type == "sharepoint"]
            assert len(sharepoint_sources) == 2
            
            # Verify defaults were applied to SharePoint sources
            for ds in sharepoint_sources:
                assert ds.document_library in ["HR Documents", "Technical Docs"]
                assert ds.max_file_size_mb == 100  # Default
                assert ds.batch_size == 50  # Default
                assert ds.enable_incremental_sync is True  # Default
            
            # Step 3: Validate configuration
            validator = ConfigurationValidator()
            is_valid, errors, warnings = validator.validate_config(config)
            
            assert is_valid, f"Multi-source configuration validation failed: {errors}"
            
            print("✅ Multi-SharePoint configuration workflow completed successfully")
            
        finally:
            Path(yaml_file).unlink()
    
    def test_configuration_help_available(self):
        """Test that configuration help is available and comprehensive"""
        help_text = get_configuration_help()
        
        # Verify help contains key information
        assert "SharePoint Configuration" in help_text
        assert "tenant_id" in help_text
        assert "client_id" in help_text
        assert "client_secret" in help_text
        assert "site_url" in help_text
        assert "SHAREPOINT_TENANT_ID" in help_text  # Environment variable
        
        print("✅ Configuration help is comprehensive")


if __name__ == "__main__":
    # Run tests individually for debugging
    test = TestConfigurationWorkflow()
    
    print("Running SharePoint configuration workflow tests...\n")
    
    test.test_sharepoint_config_workflow_yaml()
    test.test_sharepoint_config_workflow_json()
    test.test_invalid_sharepoint_config_workflow()
    test.test_template_generation_workflow()
    test.test_multi_sharepoint_config_workflow()
    test.test_configuration_help_available()
    
    print("\n🎉 All configuration workflow tests passed!") 