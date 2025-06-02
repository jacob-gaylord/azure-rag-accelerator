"""
Configuration validation utilities for data source configurations.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from .config import DataSourceConfig, IngestionConfig

# Import JSON schema validation if available
try:
    from .config_schema import (
        get_ingestion_config_schema,
        validate_config_against_schema
    )
    HAS_JSON_SCHEMA = True
except ImportError:
    HAS_JSON_SCHEMA = False


class ConfigurationValidator:
    """Validates data source configurations"""
    
    def __init__(self, use_json_schema: bool = True):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.use_json_schema = use_json_schema and HAS_JSON_SCHEMA
    
    def validate_config(self, config: IngestionConfig) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the entire ingestion configuration
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # First run JSON schema validation if available
        if self.use_json_schema:
            try:
                config_dict = self._config_to_dict(config)
                schema = get_ingestion_config_schema()
                is_valid, schema_errors = validate_config_against_schema(config_dict, schema)
                
                if not is_valid:
                    self.errors.extend([f"Schema validation: {error}" for error in schema_errors])
            except Exception as e:
                self.warnings.append(f"JSON schema validation failed: {str(e)}")
        
        # Validate data sources
        if not config.data_sources:
            self.errors.append("No data sources configured")
        else:
            for i, ds in enumerate(config.data_sources):
                self._validate_data_source(ds, f"data_sources[{i}]")
        
        # Validate Azure configuration
        self._validate_azure_config(config)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _config_to_dict(self, config: IngestionConfig) -> Dict[str, Any]:
        """Convert IngestionConfig to dictionary for schema validation"""
        # This is a simplified conversion - in practice, you might want
        # to use dataclasses.asdict() or implement a proper serialization method
        return {
            "data_sources": [
                {
                    "type": ds.type,
                    "path": ds.path,
                    "storage_account": ds.storage_account,
                    "container": ds.container,
                    "blob_prefix": ds.blob_prefix,
                    "filesystem": ds.filesystem,
                    "tenant_id": ds.tenant_id,
                    "client_id": ds.client_id,
                    "client_secret": ds.client_secret,
                    "site_url": ds.site_url,
                    "document_library": ds.document_library,
                    "folder_path": ds.folder_path,
                    "max_file_size_mb": ds.max_file_size_mb,
                    "supported_extensions": ds.supported_extensions,
                    "batch_size": ds.batch_size,
                    "enable_incremental_sync": ds.enable_incremental_sync,
                    "sync_state_file": ds.sync_state_file,
                    "connection_string": ds.connection_string,
                    "account_key": ds.account_key,
                    "sas_token": ds.sas_token,
                    "metadata": ds.metadata
                }
                for ds in config.data_sources
            ],
            "azure": {
                "search_service": config.azure.search_service,
                "search_index": config.azure.search_index,
                "storage_account": config.azure.storage_account,
                "storage_container": config.azure.storage_container,
                "openai_service": config.azure.openai_service,
                "openai_endpoint": config.azure.openai_endpoint,
                "openai_deployment": config.azure.openai_deployment,
                "openai_model": config.azure.openai_model,
                "openai_api_version": config.azure.openai_api_version,
                "document_intelligence_service": config.azure.document_intelligence_service,
                "subscription_id": config.azure.subscription_id,
                "tenant_id": config.azure.tenant_id
            },
            "use_integrated_vectorization": config.use_integrated_vectorization,
            "use_gpt_vision": config.use_gpt_vision,
            "use_acls": config.use_acls,
            "use_vectors": config.use_vectors,
            "use_local_pdf_parser": config.use_local_pdf_parser,
            "use_local_html_parser": config.use_local_html_parser,
            "disable_batch_vectors": config.disable_batch_vectors,
            "default_category": config.default_category,
            "skip_blobs": config.skip_blobs,
            "verbose": config.verbose
        }
    
    def _validate_data_source(self, ds: DataSourceConfig, context: str):
        """Validate a single data source configuration"""
        if not ds.type:
            self.errors.append(f"{context}: 'type' is required")
            return
        
        if ds.type == "local":
            self._validate_local_config(ds, context)
        elif ds.type == "azure_blob":
            self._validate_azure_blob_config(ds, context)
        elif ds.type == "adls_gen2":
            self._validate_adls_gen2_config(ds, context)
        elif ds.type == "sharepoint":
            self._validate_sharepoint_config(ds, context)
        else:
            self.errors.append(f"{context}: Unknown data source type '{ds.type}'")
    
    def _validate_local_config(self, ds: DataSourceConfig, context: str):
        """Validate local file configuration"""
        if not ds.path:
            self.errors.append(f"{context}: 'path' is required for local data sources")
    
    def _validate_azure_blob_config(self, ds: DataSourceConfig, context: str):
        """Validate Azure Blob Storage configuration"""
        if not ds.storage_account:
            self.errors.append(f"{context}: 'storage_account' is required for Azure Blob Storage")
        
        if not ds.container:
            self.errors.append(f"{context}: 'container' is required for Azure Blob Storage")
        
        # Check authentication
        auth_methods = [ds.connection_string, ds.account_key, ds.sas_token]
        if not any(auth_methods):
            self.errors.append(f"{context}: At least one authentication method required (connection_string, account_key, or sas_token)")
    
    def _validate_adls_gen2_config(self, ds: DataSourceConfig, context: str):
        """Validate Azure Data Lake Gen2 configuration"""
        if not ds.storage_account:
            self.errors.append(f"{context}: 'storage_account' is required for ADLS Gen2")
        
        if not ds.filesystem:
            self.errors.append(f"{context}: 'filesystem' is required for ADLS Gen2")
        
        # Check authentication
        auth_methods = [ds.connection_string, ds.account_key]
        if not any(auth_methods):
            self.errors.append(f"{context}: At least one authentication method required (connection_string or account_key)")
    
    def _validate_sharepoint_config(self, ds: DataSourceConfig, context: str):
        """Validate SharePoint configuration"""
        # Required fields
        required_fields = {
            'tenant_id': ds.tenant_id,
            'client_id': ds.client_id,
            'client_secret': ds.client_secret,
            'site_url': ds.site_url
        }
        
        for field_name, field_value in required_fields.items():
            if not field_value:
                self.errors.append(f"{context}: '{field_name}' is required for SharePoint")
        
        # Validate tenant_id format (GUID)
        if ds.tenant_id and not self._is_valid_guid(ds.tenant_id):
            self.errors.append(f"{context}: 'tenant_id' must be a valid GUID")
        
        # Validate client_id format (GUID)
        if ds.client_id and not self._is_valid_guid(ds.client_id):
            self.errors.append(f"{context}: 'client_id' must be a valid GUID")
        
        # Validate site_url format
        if ds.site_url:
            if not self._is_valid_sharepoint_url(ds.site_url):
                self.errors.append(f"{context}: 'site_url' must be a valid SharePoint URL")
        
        # Validate optional fields
        if ds.max_file_size_mb is not None:
            if ds.max_file_size_mb <= 0:
                self.errors.append(f"{context}: 'max_file_size_mb' must be positive")
            elif ds.max_file_size_mb > 1000:
                self.warnings.append(f"{context}: 'max_file_size_mb' is very large ({ds.max_file_size_mb}MB)")
        
        if ds.batch_size is not None:
            if ds.batch_size <= 0:
                self.errors.append(f"{context}: 'batch_size' must be positive")
            elif ds.batch_size > 1000:
                self.warnings.append(f"{context}: 'batch_size' is very large ({ds.batch_size})")
        
        # Validate supported_extensions
        if ds.supported_extensions:
            for ext in ds.supported_extensions:
                if not ext.startswith('.'):
                    self.errors.append(f"{context}: File extension '{ext}' must start with '.'")
        
        # Validate document_library name
        if ds.document_library and len(ds.document_library.strip()) == 0:
            self.errors.append(f"{context}: 'document_library' cannot be empty")
    
    def _validate_azure_config(self, config: IngestionConfig):
        """Validate Azure service configuration"""
        azure = config.azure
        
        # Check for required Azure services based on processing options
        if config.use_vectors and not azure.openai_service and not azure.openai_endpoint:
            self.warnings.append("Vector processing enabled but no OpenAI service configured")
        
        if not azure.search_service:
            self.warnings.append("No Azure Search service configured")
        
        if not azure.storage_account:
            self.warnings.append("No Azure Storage account configured for processed content")
        
        # Validate OpenAI endpoint format
        if azure.openai_endpoint:
            parsed = urlparse(azure.openai_endpoint)
            if not parsed.scheme or not parsed.netloc:
                self.errors.append("Invalid OpenAI endpoint URL format")
    
    def _is_valid_guid(self, guid_string: str) -> bool:
        """Check if string is a valid GUID format"""
        guid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(guid_pattern.match(guid_string))
    
    def _is_valid_sharepoint_url(self, url: str) -> bool:
        """Check if URL is a valid SharePoint URL format"""
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Must be HTTPS
            if parsed.scheme.lower() != 'https':
                return False
            
            # Must be a SharePoint domain
            netloc_lower = parsed.netloc.lower()
            if not (netloc_lower.endswith('.sharepoint.com') or 
                   netloc_lower.endswith('.sharepoint.us') or
                   netloc_lower.endswith('.sharepoint.de')):
                return False
            
            return True
            
        except Exception:
            return False


def validate_sharepoint_config(config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate a SharePoint configuration dictionary
    
    Args:
        config: SharePoint configuration dictionary
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = ConfigurationValidator()
    
    # Create a temporary DataSourceConfig for validation
    try:
        ds_config = DataSourceConfig(type="sharepoint", **config)
        validator._validate_sharepoint_config(ds_config, "sharepoint_config")
    except Exception as e:
        validator.errors.append(f"Configuration parsing error: {str(e)}")
    
    return len(validator.errors) == 0, validator.errors, validator.warnings


def get_sharepoint_config_template() -> Dict[str, Any]:
    """Get a template for SharePoint configuration"""
    return {
        "type": "sharepoint",
        "tenant_id": "12345678-1234-1234-1234-123456789012",
        "client_id": "87654321-4321-4321-4321-210987654321",
        "client_secret": "your-client-secret",
        "site_url": "https://yourtenant.sharepoint.com/sites/yoursite",
        "document_library": "Shared Documents",
        "folder_path": "",
        "max_file_size_mb": 100,
        "supported_extensions": [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".txt", ".md"],
        "batch_size": 50,
        "enable_incremental_sync": True,
        "metadata": {
            "description": "SharePoint document library"
        }
    }


def get_configuration_help() -> str:
    """Get help text for configuration"""
    return """
Configuration Help
==================

Data Source Types:
- local: Local file system
- azure_blob: Azure Blob Storage
- adls_gen2: Azure Data Lake Storage Gen2
- sharepoint: SharePoint Online

SharePoint Configuration:
- tenant_id: Azure AD tenant ID (GUID format)
- client_id: Azure AD app registration client ID (GUID format)
- client_secret: Azure AD app registration client secret
- site_url: SharePoint site URL (https://tenant.sharepoint.com/sites/sitename)
- document_library: Document library name (default: "Shared Documents")
- folder_path: Specific folder path within library (optional)
- max_file_size_mb: Maximum file size in MB (default: 100)
- supported_extensions: List of allowed file extensions
- batch_size: Number of files to process in batches (default: 50)
- enable_incremental_sync: Enable incremental synchronization (default: true)

Environment Variables:
- SHAREPOINT_TENANT_ID
- SHAREPOINT_CLIENT_ID
- SHAREPOINT_CLIENT_SECRET
- SHAREPOINT_SITE_URL
- SHAREPOINT_DOCUMENT_LIBRARY
- SHAREPOINT_FOLDER_PATH
- SHAREPOINT_MAX_FILE_SIZE_MB
- SHAREPOINT_ENABLE_INCREMENTAL_SYNC

For more information, see docs/sharepoint_configuration.md
""" 