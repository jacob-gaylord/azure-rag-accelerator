"""
Unit tests for SharePoint configuration schema and validation.
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.backend.prepdocslib.config import (
    DataSourceConfig, 
    IngestionConfig, 
    ConfigurationManager
)
from app.backend.prepdocslib.config_validator import (
    ConfigurationValidator,
    validate_sharepoint_config,
    get_sharepoint_config_template,
    get_configuration_help
)


class TestDataSourceConfig:
    """Test DataSourceConfig class with SharePoint support"""
    
    def test_sharepoint_config_creation(self):
        """Test creating a SharePoint configuration"""
        config = DataSourceConfig(
            type="sharepoint",
            tenant_id="12345678-1234-1234-1234-123456789012",
            client_id="87654321-4321-4321-4321-210987654321",
            client_secret="test-secret",
            site_url="https://contoso.sharepoint.com/sites/test"
        )
        
        assert config.type == "sharepoint"
        assert config.tenant_id == "12345678-1234-1234-1234-123456789012"
        assert config.client_id == "87654321-4321-4321-4321-210987654321"
        assert config.client_secret == "test-secret"
        assert config.site_url == "https://contoso.sharepoint.com/sites/test"
    
    def test_sharepoint_config_validation_valid(self):
        """Test validation of valid SharePoint configuration"""
        config = DataSourceConfig(
            type="sharepoint",
            tenant_id="12345678-1234-1234-1234-123456789012",
            client_id="87654321-4321-4321-4321-210987654321",
            client_secret="test-secret",
            site_url="https://contoso.sharepoint.com/sites/test"
        )
        
        assert config.validate() is True
    
    def test_sharepoint_config_validation_missing_fields(self):
        """Test validation with missing required fields"""
        # Missing tenant_id
        config = DataSourceConfig(
            type="sharepoint",
            client_id="87654321-4321-4321-4321-210987654321",
            client_secret="test-secret",
            site_url="https://contoso.sharepoint.com/sites/test"
        )
        assert config.validate() is False
        
        # Missing client_id
        config = DataSourceConfig(
            type="sharepoint",
            tenant_id="12345678-1234-1234-1234-123456789012",
            client_secret="test-secret",
            site_url="https://contoso.sharepoint.com/sites/test"
        )
        assert config.validate() is False
    
    def test_sharepoint_defaults(self):
        """Test SharePoint default values"""
        config = DataSourceConfig(type="sharepoint")
        defaults = config.get_sharepoint_defaults()
        
        assert defaults["document_library"] == "Shared Documents"
        assert defaults["folder_path"] == ""
        assert defaults["max_file_size_mb"] == 100
        assert defaults["batch_size"] == 50
        assert defaults["enable_incremental_sync"] is True
        assert ".pdf" in defaults["supported_extensions"]
        assert ".docx" in defaults["supported_extensions"]
    
    def test_other_data_source_validation(self):
        """Test validation of other data source types"""
        # Local
        local_config = DataSourceConfig(type="local", path="./data/*")
        assert local_config.validate() is True
        
        local_config_invalid = DataSourceConfig(type="local")
        assert local_config_invalid.validate() is False
        
        # Azure Blob
        blob_config = DataSourceConfig(
            type="azure_blob",
            storage_account="test",
            container="test",
            account_key="test"
        )
        assert blob_config.validate() is True


class TestConfigurationManager:
    """Test ConfigurationManager with SharePoint support"""
    
    def test_parse_sharepoint_config_from_dict(self):
        """Test parsing SharePoint configuration from dictionary"""
        config_data = {
            "data_sources": [
                {
                    "type": "sharepoint",
                    "tenant_id": "12345678-1234-1234-1234-123456789012",
                    "client_id": "87654321-4321-4321-4321-210987654321",
                    "client_secret": "test-secret",
                    "site_url": "https://contoso.sharepoint.com/sites/test"
                }
            ],
            "azure": {
                "search_service": "test-search"
            }
        }
        
        manager = ConfigurationManager()
        config = manager._parse_config_data(config_data)
        
        assert len(config.data_sources) == 1
        ds = config.data_sources[0]
        assert ds.type == "sharepoint"
        assert ds.tenant_id == "12345678-1234-1234-1234-123456789012"
        assert ds.document_library == "Shared Documents"  # Default applied
        assert ds.enable_incremental_sync is True  # Default applied
    
    def test_parse_sharepoint_config_with_custom_values(self):
        """Test parsing SharePoint configuration with custom values"""
        config_data = {
            "data_sources": [
                {
                    "type": "sharepoint",
                    "tenant_id": "12345678-1234-1234-1234-123456789012",
                    "client_id": "87654321-4321-4321-4321-210987654321",
                    "client_secret": "test-secret",
                    "site_url": "https://contoso.sharepoint.com/sites/test",
                    "document_library": "Custom Library",
                    "folder_path": "custom/path",
                    "max_file_size_mb": 50,
                    "batch_size": 25
                }
            ]
        }
        
        manager = ConfigurationManager()
        config = manager._parse_config_data(config_data)
        
        ds = config.data_sources[0]
        assert ds.document_library == "Custom Library"
        assert ds.folder_path == "custom/path"
        assert ds.max_file_size_mb == 50
        assert ds.batch_size == 25
    
    @patch.dict('os.environ', {
        'SHAREPOINT_TENANT_ID': '12345678-1234-1234-1234-123456789012',
        'SHAREPOINT_CLIENT_ID': '87654321-4321-4321-4321-210987654321',
        'SHAREPOINT_CLIENT_SECRET': 'test-secret',
        'SHAREPOINT_SITE_URL': 'https://contoso.sharepoint.com/sites/test',
        'SHAREPOINT_DOCUMENT_LIBRARY': 'Custom Library',
        'SHAREPOINT_MAX_FILE_SIZE_MB': '75'
    })
    def test_load_from_environment_sharepoint(self):
        """Test loading SharePoint configuration from environment variables"""
        manager = ConfigurationManager()
        config = manager._load_from_environment()
        
        # Should have SharePoint as first data source
        assert len(config.data_sources) >= 1
        sharepoint_ds = None
        for ds in config.data_sources:
            if ds.type == "sharepoint":
                sharepoint_ds = ds
                break
        
        assert sharepoint_ds is not None
        assert sharepoint_ds.tenant_id == "12345678-1234-1234-1234-123456789012"
        assert sharepoint_ds.client_id == "87654321-4321-4321-4321-210987654321"
        assert sharepoint_ds.client_secret == "test-secret"
        assert sharepoint_ds.site_url == "https://contoso.sharepoint.com/sites/test"
        assert sharepoint_ds.document_library == "Custom Library"
        assert sharepoint_ds.max_file_size_mb == 75
    
    def test_save_and_load_sharepoint_config_json(self):
        """Test saving and loading SharePoint configuration as JSON"""
        config = IngestionConfig(
            data_sources=[
                DataSourceConfig(
                    type="sharepoint",
                    tenant_id="12345678-1234-1234-1234-123456789012",
                    client_id="87654321-4321-4321-4321-210987654321",
                    client_secret="test-secret",
                    site_url="https://contoso.sharepoint.com/sites/test",
                    document_library="Test Library",
                    max_file_size_mb=75
                )
            ]
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            manager = ConfigurationManager()
            manager.save_config(config, temp_path)
            
            # Load and verify
            loaded_config = manager._load_from_file(temp_path)
            
            assert len(loaded_config.data_sources) == 1
            ds = loaded_config.data_sources[0]
            assert ds.type == "sharepoint"
            assert ds.tenant_id == "12345678-1234-1234-1234-123456789012"
            assert ds.document_library == "Test Library"
            assert ds.max_file_size_mb == 75
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_save_and_load_sharepoint_config_yaml(self):
        """Test saving and loading SharePoint configuration as YAML"""
        config = IngestionConfig(
            data_sources=[
                DataSourceConfig(
                    type="sharepoint",
                    tenant_id="12345678-1234-1234-1234-123456789012",
                    client_id="87654321-4321-4321-4321-210987654321",
                    client_secret="test-secret",
                    site_url="https://contoso.sharepoint.com/sites/test",
                    supported_extensions=[".pdf", ".docx"]
                )
            ]
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            manager = ConfigurationManager()
            manager.save_config(config, temp_path)
            
            # Load and verify
            loaded_config = manager._load_from_file(temp_path)
            
            assert len(loaded_config.data_sources) == 1
            ds = loaded_config.data_sources[0]
            assert ds.type == "sharepoint"
            assert ds.supported_extensions == [".pdf", ".docx"]
            
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestConfigurationValidator:
    """Test configuration validation"""
    
    def test_valid_sharepoint_config(self):
        """Test validation of valid SharePoint configuration"""
        config = IngestionConfig(
            data_sources=[
                DataSourceConfig(
                    type="sharepoint",
                    tenant_id="12345678-1234-1234-1234-123456789012",
                    client_id="87654321-4321-4321-4321-210987654321",
                    client_secret="test-secret",
                    site_url="https://contoso.sharepoint.com/sites/test"
                )
            ]
        )
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_config(config)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_sharepoint_config_missing_fields(self):
        """Test validation with missing required fields"""
        config = IngestionConfig(
            data_sources=[
                DataSourceConfig(
                    type="sharepoint",
                    tenant_id="12345678-1234-1234-1234-123456789012",
                    # Missing client_id, client_secret, site_url
                )
            ]
        )
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_config(config)
        
        assert is_valid is False
        assert len(errors) >= 3  # Missing client_id, client_secret, site_url
        assert any("client_id" in error for error in errors)
        assert any("client_secret" in error for error in errors)
        assert any("site_url" in error for error in errors)
    
    def test_invalid_sharepoint_config_bad_guid(self):
        """Test validation with invalid GUID format"""
        config = IngestionConfig(
            data_sources=[
                DataSourceConfig(
                    type="sharepoint",
                    tenant_id="invalid-guid",
                    client_id="also-invalid",
                    client_secret="test-secret",
                    site_url="https://contoso.sharepoint.com/sites/test"
                )
            ]
        )
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_config(config)
        
        assert is_valid is False
        assert any("tenant_id" in error and "GUID" in error for error in errors)
        assert any("client_id" in error and "GUID" in error for error in errors)
    
    def test_invalid_sharepoint_config_bad_url(self):
        """Test validation with invalid SharePoint URL"""
        config = IngestionConfig(
            data_sources=[
                DataSourceConfig(
                    type="sharepoint",
                    tenant_id="12345678-1234-1234-1234-123456789012",
                    client_id="87654321-4321-4321-4321-210987654321",
                    client_secret="test-secret",
                    site_url="http://invalid-url.com"  # Not HTTPS SharePoint URL
                )
            ]
        )
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_config(config)
        
        assert is_valid is False
        assert any("site_url" in error and "SharePoint URL" in error for error in errors)
    
    def test_sharepoint_config_warnings(self):
        """Test validation warnings for SharePoint configuration"""
        config = IngestionConfig(
            data_sources=[
                DataSourceConfig(
                    type="sharepoint",
                    tenant_id="12345678-1234-1234-1234-123456789012",
                    client_id="87654321-4321-4321-4321-210987654321",
                    client_secret="test-secret",
                    site_url="https://contoso.sharepoint.com/sites/test",
                    max_file_size_mb=2000,  # Very large
                    batch_size=5000  # Very large
                )
            ]
        )
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_config(config)
        
        assert is_valid is True
        assert len(warnings) >= 2
        assert any("max_file_size_mb" in warning for warning in warnings)
        assert any("batch_size" in warning for warning in warnings)
    
    def test_validate_sharepoint_config_function(self):
        """Test standalone SharePoint config validation function"""
        # Valid config
        valid_config = {
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            "client_id": "87654321-4321-4321-4321-210987654321",
            "client_secret": "test-secret",
            "site_url": "https://contoso.sharepoint.com/sites/test"
        }
        
        is_valid, errors, warnings = validate_sharepoint_config(valid_config)
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid config
        invalid_config = {
            "tenant_id": "invalid-guid",
            "site_url": "http://invalid.com"
        }
        
        is_valid, errors, warnings = validate_sharepoint_config(invalid_config)
        assert is_valid is False
        assert len(errors) > 0
    
    def test_get_sharepoint_config_template(self):
        """Test SharePoint configuration template"""
        template = get_sharepoint_config_template()
        
        assert template["type"] == "sharepoint"
        assert "tenant_id" in template
        assert "client_id" in template
        assert "client_secret" in template
        assert "site_url" in template
        assert template["document_library"] == "Shared Documents"
        assert template["enable_incremental_sync"] is True
        assert isinstance(template["supported_extensions"], list)
    
    def test_get_configuration_help(self):
        """Test configuration help text"""
        help_text = get_configuration_help()
        
        assert "SharePoint Configuration" in help_text
        assert "tenant_id" in help_text
        assert "SHAREPOINT_TENANT_ID" in help_text
        assert "sharepoint_configuration.md" in help_text


class TestSharePointURLValidation:
    """Test SharePoint URL validation specifically"""
    
    def test_valid_sharepoint_urls(self):
        """Test various valid SharePoint URL formats"""
        validator = ConfigurationValidator()
        
        valid_urls = [
            "https://contoso.sharepoint.com/sites/test",
            "https://contoso.sharepoint.com",
            "https://contoso-my.sharepoint.com/personal/user",
            "https://contoso.sharepoint.us/sites/test",
            "https://contoso.sharepoint.de/sites/test"
        ]
        
        for url in valid_urls:
            assert validator._is_valid_sharepoint_url(url), f"URL should be valid: {url}"
    
    def test_invalid_sharepoint_urls(self):
        """Test various invalid SharePoint URL formats"""
        validator = ConfigurationValidator()
        
        invalid_urls = [
            "http://contoso.sharepoint.com/sites/test",  # HTTP instead of HTTPS
            "https://contoso.com/sites/test",  # Not SharePoint domain
            "ftp://contoso.sharepoint.com/sites/test",  # Wrong protocol
            "not-a-url",  # Not a URL at all
            "",  # Empty string
            "https://",  # Incomplete URL
        ]
        
        for url in invalid_urls:
            assert not validator._is_valid_sharepoint_url(url), f"URL should be invalid: {url}"


class TestGUIDValidation:
    """Test GUID validation"""
    
    def test_valid_guids(self):
        """Test various valid GUID formats"""
        validator = ConfigurationValidator()
        
        valid_guids = [
            "12345678-1234-1234-1234-123456789012",
            "87654321-4321-4321-4321-210987654321",
            "00000000-0000-0000-0000-000000000000",
            "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF",
            "abcdef12-3456-7890-abcd-ef1234567890"
        ]
        
        for guid in valid_guids:
            assert validator._is_valid_guid(guid), f"GUID should be valid: {guid}"
            assert validator._is_valid_guid(guid.upper()), f"Uppercase GUID should be valid: {guid.upper()}"
            assert validator._is_valid_guid(guid.lower()), f"Lowercase GUID should be valid: {guid.lower()}"
    
    def test_invalid_guids(self):
        """Test various invalid GUID formats"""
        validator = ConfigurationValidator()
        
        invalid_guids = [
            "12345678-1234-1234-1234-12345678901",  # Too short
            "12345678-1234-1234-1234-1234567890123",  # Too long
            "12345678-1234-1234-1234-123456789012-extra",  # Extra characters
            "12345678_1234_1234_1234_123456789012",  # Wrong separators
            "1234567812341234123412345678901",  # No separators
            "not-a-guid-at-all",  # Not a GUID
            "",  # Empty string
            "12345678-1234-1234-1234-12345678901G",  # Invalid character
        ]
        
        for guid in invalid_guids:
            assert not validator._is_valid_guid(guid), f"GUID should be invalid: {guid}"


if __name__ == "__main__":
    pytest.main([__file__]) 