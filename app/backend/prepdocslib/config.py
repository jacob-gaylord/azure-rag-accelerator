import json
import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from pathlib import Path


@dataclass
class DataSourceConfig:
    """Configuration for a data source"""
    type: str  # "local", "azure_blob", "adls_gen2", "sharepoint"
    path: Optional[str] = None
    
    # Azure Blob Storage specific
    storage_account: Optional[str] = None
    container: Optional[str] = None
    blob_prefix: Optional[str] = None
    
    # ADLS Gen2 specific
    filesystem: Optional[str] = None
    
    # SharePoint specific
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    site_url: Optional[str] = None
    document_library: Optional[str] = None
    folder_path: Optional[str] = None
    max_file_size_mb: Optional[int] = None
    supported_extensions: Optional[List[str]] = None
    batch_size: Optional[int] = None
    enable_incremental_sync: Optional[bool] = None
    sync_state_file: Optional[str] = None
    
    # Authentication (common)
    connection_string: Optional[str] = None
    account_key: Optional[str] = None
    sas_token: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate configuration based on data source type"""
        if self.type == "local":
            return self.path is not None
        elif self.type == "azure_blob":
            return (self.storage_account is not None and 
                    self.container is not None and
                    (self.connection_string or self.account_key or self.sas_token))
        elif self.type == "adls_gen2":
            return (self.storage_account is not None and 
                    self.filesystem is not None and
                    (self.connection_string or self.account_key))
        elif self.type == "sharepoint":
            required_fields = [self.tenant_id, self.client_id, self.client_secret, self.site_url]
            return all(field is not None for field in required_fields)
        else:
            return False
    
    def get_sharepoint_defaults(self) -> Dict[str, Any]:
        """Get default values for SharePoint configuration"""
        return {
            "document_library": "Shared Documents",
            "folder_path": "",
            "max_file_size_mb": 100,
            "supported_extensions": [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".txt", ".md"],
            "batch_size": 50,
            "enable_incremental_sync": True,
            "sync_state_file": f".sharepoint_sync_{hash(self.site_url) if self.site_url else 'default'}.json"
        }


@dataclass
class AzureConfig:
    """Azure service configuration"""
    # Search service
    search_service: Optional[str] = None
    search_index: Optional[str] = None
    search_key: Optional[str] = None
    
    # Storage
    storage_account: Optional[str] = None
    storage_container: Optional[str] = None
    storage_key: Optional[str] = None
    storage_resource_group: Optional[str] = None
    
    # OpenAI
    openai_service: Optional[str] = None
    openai_endpoint: Optional[str] = None
    openai_key: Optional[str] = None
    openai_deployment: Optional[str] = None
    openai_model: Optional[str] = None
    openai_api_version: Optional[str] = None
    
    # Document Intelligence
    document_intelligence_service: Optional[str] = None
    document_intelligence_key: Optional[str] = None
    
    # Subscription and tenant
    subscription_id: Optional[str] = None
    tenant_id: Optional[str] = None


@dataclass
class IngestionConfig:
    """Main configuration for data ingestion"""
    data_sources: List[DataSourceConfig] = field(default_factory=list)
    azure: AzureConfig = field(default_factory=AzureConfig)
    
    # Processing options
    use_integrated_vectorization: bool = False
    use_gpt_vision: bool = False
    use_acls: bool = False
    use_vectors: bool = True
    use_local_pdf_parser: bool = False
    use_local_html_parser: bool = False
    
    # Batch processing
    disable_batch_vectors: bool = False
    
    # Categories and metadata
    default_category: Optional[str] = None
    
    # File processing
    skip_blobs: bool = False
    
    # Logging
    verbose: bool = False


class ConfigurationManager:
    """Manages configuration loading from files and environment variables"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config: Optional[IngestionConfig] = None
    
    def load_config(self) -> IngestionConfig:
        """Load configuration from file or environment variables"""
        if self._config is not None:
            return self._config
            
        # Try to load from file first
        if self.config_path and os.path.exists(self.config_path):
            self._config = self._load_from_file(self.config_path)
        else:
            # Look for default config files
            for default_path in ["accelerator_config.json", "accelerator_config.yaml", "accelerator_config.yml"]:
                if os.path.exists(default_path):
                    self._config = self._load_from_file(default_path)
                    break
        
        # If no file found, create from environment variables
        if self._config is None:
            self._config = self._load_from_environment()
        
        # Always overlay environment variables (they take precedence)
        self._overlay_environment_variables(self._config)
        
        return self._config
    
    def _load_from_file(self, file_path: str) -> IngestionConfig:
        """Load configuration from JSON or YAML file"""
        path = Path(file_path)
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return self._parse_config_data(data)
    
    def _load_from_environment(self) -> IngestionConfig:
        """Load configuration from environment variables (legacy support)"""
        # Create data source from environment
        data_sources = []
        
        # Check for SharePoint configuration
        if os.getenv("SHAREPOINT_TENANT_ID"):
            sharepoint_config = DataSourceConfig(
                type="sharepoint",
                tenant_id=os.getenv("SHAREPOINT_TENANT_ID"),
                client_id=os.getenv("SHAREPOINT_CLIENT_ID"),
                client_secret=os.getenv("SHAREPOINT_CLIENT_SECRET"),
                site_url=os.getenv("SHAREPOINT_SITE_URL"),
                document_library=os.getenv("SHAREPOINT_DOCUMENT_LIBRARY", "Shared Documents"),
                folder_path=os.getenv("SHAREPOINT_FOLDER_PATH", ""),
                max_file_size_mb=int(os.getenv("SHAREPOINT_MAX_FILE_SIZE_MB", "100")),
                enable_incremental_sync=os.getenv("SHAREPOINT_ENABLE_INCREMENTAL_SYNC", "true").lower() == "true"
            )
            data_sources.append(sharepoint_config)
        
        # Check for ADLS Gen2 configuration
        if os.getenv("AZURE_ADLS_GEN2_STORAGE_ACCOUNT"):
            data_sources.append(DataSourceConfig(
                type="adls_gen2",
                storage_account=os.getenv("AZURE_ADLS_GEN2_STORAGE_ACCOUNT"),
                filesystem=os.getenv("AZURE_ADLS_GEN2_FILESYSTEM"),
                path=os.getenv("AZURE_ADLS_GEN2_FILESYSTEM_PATH"),
                account_key=os.getenv("AZURE_ADLS_GEN2_KEY")
            ))
        
        # Check for Azure Blob Storage configuration
        if os.getenv("AZURE_STORAGE_ACCOUNT") and os.getenv("AZURE_STORAGE_CONTAINER"):
            data_sources.append(DataSourceConfig(
                type="azure_blob",
                storage_account=os.getenv("AZURE_STORAGE_ACCOUNT"),
                container=os.getenv("AZURE_STORAGE_CONTAINER"),
                blob_prefix=os.getenv("AZURE_STORAGE_BLOB_PREFIX"),
                connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
                account_key=os.getenv("AZURE_STORAGE_KEY"),
                sas_token=os.getenv("AZURE_STORAGE_SAS_TOKEN")
            ))
        
        # Default to local files if no other source specified
        if not data_sources:
            data_sources.append(DataSourceConfig(
                type="local",
                path="./data/*"  # Default path
            ))
        
        # Create Azure configuration
        azure_config = AzureConfig(
            search_service=os.getenv("AZURE_SEARCH_SERVICE"),
            search_index=os.getenv("AZURE_SEARCH_INDEX"),
            storage_account=os.getenv("AZURE_STORAGE_ACCOUNT"),
            storage_container=os.getenv("AZURE_STORAGE_CONTAINER"),
            storage_resource_group=os.getenv("AZURE_STORAGE_RESOURCE_GROUP"),
            openai_service=os.getenv("AZURE_OPENAI_SERVICE"),
            openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_deployment=os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT"),
            openai_model=os.getenv("AZURE_OPENAI_EMB_MODEL_NAME"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
            document_intelligence_service=os.getenv("AZURE_DOCUMENTINTELLIGENCE_SERVICE"),
            subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
            tenant_id=os.getenv("AZURE_TENANT_ID")
        )
        
        # Create main configuration
        return IngestionConfig(
            data_sources=data_sources,
            azure=azure_config,
            use_integrated_vectorization=os.getenv("USE_FEATURE_INT_VECTORIZATION", "").lower() == "true",
            use_gpt_vision=os.getenv("USE_GPT4V", "").lower() == "true",
            use_acls=os.getenv("AZURE_ENFORCE_ACCESS_CONTROL") is not None,
            use_vectors=os.getenv("USE_VECTORS", "").lower() != "false",
            use_local_pdf_parser=os.getenv("USE_LOCAL_PDF_PARSER", "").lower() == "true",
            use_local_html_parser=os.getenv("USE_LOCAL_HTML_PARSER", "").lower() == "true"
        )
    
    def _parse_config_data(self, data: Dict[str, Any]) -> IngestionConfig:
        """Parse configuration data from dictionary"""
        # Parse data sources
        data_sources = []
        for ds_data in data.get("data_sources", []):
            # Create DataSourceConfig with defaults applied for SharePoint
            if ds_data.get("type") == "sharepoint":
                # Apply SharePoint defaults
                sharepoint_defaults = {
                    "document_library": "Shared Documents",
                    "folder_path": "",
                    "max_file_size_mb": 100,
                    "supported_extensions": [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".txt", ".md"],
                    "batch_size": 50,
                    "enable_incremental_sync": True
                }
                # Merge defaults with provided config
                merged_config = {**sharepoint_defaults, **ds_data}
                # Generate sync state file if not provided
                if "sync_state_file" not in merged_config and merged_config.get("site_url"):
                    merged_config["sync_state_file"] = f".sharepoint_sync_{hash(merged_config['site_url'])}.json"
                data_sources.append(DataSourceConfig(**merged_config))
            else:
                data_sources.append(DataSourceConfig(**ds_data))
        
        # Parse Azure configuration
        azure_data = data.get("azure", {})
        azure_config = AzureConfig(**azure_data)
        
        # Parse main configuration
        config_data = {k: v for k, v in data.items() if k not in ["data_sources", "azure"]}
        config = IngestionConfig(
            data_sources=data_sources,
            azure=azure_config,
            **config_data
        )
        
        return config
    
    def _overlay_environment_variables(self, config: IngestionConfig):
        """Overlay environment variables on top of file configuration"""
        # Azure service overrides
        if os.getenv("AZURE_SEARCH_SERVICE"):
            config.azure.search_service = os.getenv("AZURE_SEARCH_SERVICE")
        if os.getenv("AZURE_SEARCH_INDEX"):
            config.azure.search_index = os.getenv("AZURE_SEARCH_INDEX")
        if os.getenv("AZURE_STORAGE_ACCOUNT"):
            config.azure.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        if os.getenv("AZURE_STORAGE_CONTAINER"):
            config.azure.storage_container = os.getenv("AZURE_STORAGE_CONTAINER")
        if os.getenv("AZURE_OPENAI_SERVICE"):
            config.azure.openai_service = os.getenv("AZURE_OPENAI_SERVICE")
        if os.getenv("AZURE_OPENAI_ENDPOINT"):
            config.azure.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        # SharePoint data source overrides
        for ds in config.data_sources:
            if ds.type == "sharepoint":
                if os.getenv("SHAREPOINT_TENANT_ID"):
                    ds.tenant_id = os.getenv("SHAREPOINT_TENANT_ID")
                if os.getenv("SHAREPOINT_CLIENT_ID"):
                    ds.client_id = os.getenv("SHAREPOINT_CLIENT_ID")
                if os.getenv("SHAREPOINT_CLIENT_SECRET"):
                    ds.client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET")
                if os.getenv("SHAREPOINT_SITE_URL"):
                    ds.site_url = os.getenv("SHAREPOINT_SITE_URL")
                if os.getenv("SHAREPOINT_DOCUMENT_LIBRARY"):
                    ds.document_library = os.getenv("SHAREPOINT_DOCUMENT_LIBRARY")
                if os.getenv("SHAREPOINT_FOLDER_PATH"):
                    ds.folder_path = os.getenv("SHAREPOINT_FOLDER_PATH")
                if os.getenv("SHAREPOINT_MAX_FILE_SIZE_MB"):
                    ds.max_file_size_mb = int(os.getenv("SHAREPOINT_MAX_FILE_SIZE_MB"))
                if os.getenv("SHAREPOINT_ENABLE_INCREMENTAL_SYNC"):
                    ds.enable_incremental_sync = os.getenv("SHAREPOINT_ENABLE_INCREMENTAL_SYNC", "").lower() == "true"
        
        # Processing option overrides
        if os.getenv("USE_FEATURE_INT_VECTORIZATION"):
            config.use_integrated_vectorization = os.getenv("USE_FEATURE_INT_VECTORIZATION", "").lower() == "true"
        if os.getenv("USE_GPT4V"):
            config.use_gpt_vision = os.getenv("USE_GPT4V", "").lower() == "true"
        if os.getenv("AZURE_ENFORCE_ACCESS_CONTROL"):
            config.use_acls = True
        if os.getenv("USE_VECTORS"):
            config.use_vectors = os.getenv("USE_VECTORS", "").lower() != "false"
    
    def save_config(self, config: IngestionConfig, file_path: str):
        """Save configuration to file"""
        # Convert to dictionary
        config_dict = {
            "data_sources": [
                {
                    "type": ds.type,
                    "path": ds.path,
                    # Azure Blob Storage fields
                    "storage_account": ds.storage_account,
                    "container": ds.container,
                    "blob_prefix": ds.blob_prefix,
                    # ADLS Gen2 fields
                    "filesystem": ds.filesystem,
                    # SharePoint fields
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
                    # Authentication fields
                    "connection_string": ds.connection_string,
                    "account_key": ds.account_key,
                    "sas_token": ds.sas_token,
                    # Metadata
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
        
        # Remove None values
        config_dict = self._remove_none_values(config_dict)
        
        path = Path(file_path)
        with open(path, 'w', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_dict, f, indent=2)
    
    def _remove_none_values(self, obj):
        """Recursively remove None values from dictionary"""
        if isinstance(obj, dict):
            return {k: self._remove_none_values(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [self._remove_none_values(item) for item in obj if item is not None]
        else:
            return obj


def get_configuration_manager(config_path: Optional[str] = None) -> ConfigurationManager:
    """Get a configuration manager instance"""
    return ConfigurationManager(config_path) 