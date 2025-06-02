import logging
from typing import Union, Optional, Dict, Any, List
from azure.core.credentials_async import AsyncTokenCredential

from .config import DataSourceConfig
from .listfilestrategy import (
    ListFileStrategy,
    LocalListFileStrategy,
    AzureBlobListFileStrategy,
    ADLSGen2ListFileStrategy,
)

# New plugin architecture imports
from .plugin_base import (
    DataSourceConnector, 
    PluginRegistry, 
    get_plugin_registry,
    MultiDataSourceConnector as NewMultiDataSourceConnector
)
from .plugins.legacy_adapters import register_legacy_plugins

logger = logging.getLogger("scripts")

# Register legacy plugins on module import
register_legacy_plugins()


class ListFileStrategyAdapter:
    """
    Adapter that makes a DataSourceConnector compatible with the ListFileStrategy interface.
    This ensures backward compatibility for existing code.
    """
    
    def __init__(self, connector: DataSourceConnector):
        self.connector = connector
    
    async def list(self):
        """List files using the connector"""
        async for file in self.connector.list_files():
            yield file
    
    async def list_paths(self):
        """List file paths using the connector"""
        async for path in self.connector.list_paths():
            yield path


class DataSourceConnectorFactory:
    """
    Factory for creating data source connectors.
    Updated to use the new plugin architecture while maintaining backward compatibility.
    """
    
    @staticmethod
    def create_connector(
        config: Union[DataSourceConfig, Dict[str, Any]],
        azure_credential: Optional[AsyncTokenCredential] = None,
        use_plugin_architecture: bool = True
    ) -> ListFileStrategy:
        """
        Create a data source connector based on configuration.
        
        Args:
            config: Configuration object or dictionary
            azure_credential: Azure credentials
            use_plugin_architecture: Whether to use the new plugin architecture (default: True)
            
        Returns:
            ListFileStrategy-compatible connector
        """
        
        # Convert DataSourceConfig to dict if needed
        if isinstance(config, DataSourceConfig):
            config_dict = DataSourceConnectorFactory._dataclass_to_dict(config)
        else:
            config_dict = config
        
        if use_plugin_architecture:
            return DataSourceConnectorFactory._create_plugin_connector(config_dict, azure_credential)
        else:
            return DataSourceConnectorFactory._create_legacy_connector(config, azure_credential)
    
    @staticmethod
    def _create_plugin_connector(
        config: Dict[str, Any], 
        azure_credential: Optional[AsyncTokenCredential] = None
    ) -> ListFileStrategy:
        """Create a connector using the new plugin architecture"""
        registry = get_plugin_registry()
        
        try:
            # Create connector using plugin registry
            connector = registry.create_connector(config, azure_credential)
            
            # Wrap in adapter to maintain ListFileStrategy compatibility
            return ListFileStrategyAdapter(connector)
            
        except Exception as e:
            logger.error(f"Failed to create plugin connector: {e}")
            raise
    
    @staticmethod
    def _create_legacy_connector(
        config: Union[DataSourceConfig, Dict[str, Any]],
        azure_credential: Optional[AsyncTokenCredential] = None
    ) -> ListFileStrategy:
        """Create a connector using the legacy approach (for fallback)"""
        
        # Handle both dict and DataSourceConfig
        if isinstance(config, dict):
            connector_type = config.get("type")
            if connector_type == "local":
                if not config.get("path"):
                    raise ValueError("Local data source requires a path")
                return LocalListFileStrategy(path_pattern=config["path"])
            
            elif connector_type == "azure_blob":
                if not config.get("storage_account") or not config.get("container"):
                    raise ValueError("Azure Blob data source requires storage_account and container")
                
                credential = DataSourceConnectorFactory._get_credential_from_dict(config, azure_credential)
                
                return AzureBlobListFileStrategy(
                    storage_account=config["storage_account"],
                    container=config["container"],
                    blob_prefix=config.get("blob_prefix"),
                    credential=credential
                )
            
            elif connector_type == "adls_gen2":
                if not config.get("storage_account") or not config.get("filesystem"):
                    raise ValueError("ADLS Gen2 data source requires storage_account and filesystem")
                
                credential = DataSourceConnectorFactory._get_credential_from_dict(config, azure_credential)
                
                return ADLSGen2ListFileStrategy(
                    data_lake_storage_account=config["storage_account"],
                    data_lake_filesystem=config["filesystem"],
                    data_lake_path=config.get("path", ""),
                    credential=credential
                )
            
            else:
                raise ValueError(f"Unsupported data source type: {connector_type}")
        
        # Original DataSourceConfig logic
        if config.type == "local":
            if not config.path:
                raise ValueError("Local data source requires a path")
            return LocalListFileStrategy(path_pattern=config.path)
        
        elif config.type == "azure_blob":
            if not config.storage_account or not config.container:
                raise ValueError("Azure Blob data source requires storage_account and container")
            
            credential = DataSourceConnectorFactory._get_credential(config, azure_credential)
            
            return AzureBlobListFileStrategy(
                storage_account=config.storage_account,
                container=config.container,
                blob_prefix=config.blob_prefix,
                credential=credential
            )
        
        elif config.type == "adls_gen2":
            if not config.storage_account or not config.filesystem:
                raise ValueError("ADLS Gen2 data source requires storage_account and filesystem")
            
            credential = DataSourceConnectorFactory._get_credential(config, azure_credential)
            
            return ADLSGen2ListFileStrategy(
                data_lake_storage_account=config.storage_account,
                data_lake_filesystem=config.filesystem,
                data_lake_path=config.path or "",
                credential=credential
            )
        
        else:
            raise ValueError(f"Unsupported data source type: {config.type}")
    
    @staticmethod
    def _dataclass_to_dict(config: DataSourceConfig) -> Dict[str, Any]:
        """Convert DataSourceConfig to dictionary"""
        return {
            "type": config.type,
            "path": config.path,
            "storage_account": config.storage_account,
            "container": config.container,
            "blob_prefix": config.blob_prefix,
            "filesystem": config.filesystem,
            "connection_string": config.connection_string,
            "account_key": config.account_key,
            "sas_token": config.sas_token,
            "metadata": config.metadata
        }
    
    @staticmethod
    def _get_credential_from_dict(
        config: Dict[str, Any],
        azure_credential: Optional[AsyncTokenCredential]
    ) -> Union[AsyncTokenCredential, str, None]:
        """Determine the appropriate credential to use from dictionary config"""
        
        if config.get("connection_string"):
            return config["connection_string"]
        
        if config.get("account_key"):
            return config["account_key"]
        
        if config.get("sas_token"):
            return config["sas_token"]
        
        if azure_credential:
            return azure_credential
        
        return None
    
    @staticmethod
    def _get_credential(
        config: DataSourceConfig,
        azure_credential: Optional[AsyncTokenCredential]
    ) -> Union[AsyncTokenCredential, str, None]:
        """Determine the appropriate credential to use for Azure services"""
        
        # Priority order:
        # 1. Connection string (if provided)
        # 2. Account key (if provided)
        # 3. SAS token (if provided)
        # 4. Azure credential (managed identity/service principal)
        
        if config.connection_string:
            return config.connection_string
        
        if config.account_key:
            return config.account_key
        
        if config.sas_token:
            return config.sas_token
        
        if azure_credential:
            return azure_credential
        
        # Return None to use default credential chain
        return None
    
    @staticmethod
    def validate_config(config: Union[DataSourceConfig, Dict[str, Any]]) -> bool:
        """Validate a data source configuration"""
        
        if isinstance(config, dict):
            connector_type = config.get("type")
            if connector_type == "local":
                return config.get("path") is not None
            elif connector_type == "azure_blob":
                return (
                    config.get("storage_account") is not None and
                    config.get("container") is not None
                )
            elif connector_type == "adls_gen2":
                return (
                    config.get("storage_account") is not None and
                    config.get("filesystem") is not None
                )
            return False
        
        # Original DataSourceConfig validation
        if config.type == "local":
            return config.path is not None
        
        elif config.type == "azure_blob":
            return (
                config.storage_account is not None and
                config.container is not None
            )
        
        elif config.type == "adls_gen2":
            return (
                config.storage_account is not None and
                config.filesystem is not None
            )
        
        return False
    
    @staticmethod
    def get_supported_types() -> List[str]:
        """Get list of supported data source types"""
        registry = get_plugin_registry()
        plugin_types = registry.list_plugin_names()
        
        # Always include legacy types for backward compatibility
        legacy_types = ["local", "azure_blob", "adls_gen2"]
        
        # Combine and deduplicate
        all_types = list(set(plugin_types + legacy_types))
        return sorted(all_types)


class MultiDataSourceConnector:
    """
    Connector that can handle multiple data sources.
    Updated to use the new plugin architecture with backward compatibility.
    """
    
    def __init__(
        self,
        configs: List[Union[DataSourceConfig, Dict[str, Any]]],
        azure_credential: Optional[AsyncTokenCredential] = None,
        use_plugin_architecture: bool = True
    ):
        self.configs = configs
        self.azure_credential = azure_credential
        self.use_plugin_architecture = use_plugin_architecture
        self.connectors: List[ListFileStrategy] = []
        
        # If using plugin architecture and all configs are dicts, use the new connector
        if use_plugin_architecture and all(isinstance(config, dict) for config in configs):
            self.new_connector = NewMultiDataSourceConnector(
                configs=configs,  # type: ignore
                azure_credential=azure_credential
            )
        else:
            self.new_connector = None
            self._initialize_legacy_connectors()
    
    def _initialize_legacy_connectors(self) -> None:
        """Initialize connectors for each configuration using the legacy approach"""
        for config in self.configs:
            if not DataSourceConnectorFactory.validate_config(config):
                config_type = getattr(config, 'type', None) or config.get('type', 'unknown')
                logger.warning(f"Invalid configuration for data source type {config_type}, skipping")
                continue
            
            try:
                connector = DataSourceConnectorFactory.create_connector(
                    config, 
                    self.azure_credential,
                    use_plugin_architecture=self.use_plugin_architecture
                )
                self.connectors.append(connector)
                config_type = getattr(config, 'type', None) or config.get('type', 'unknown')
                logger.info(f"Created connector for {config_type} data source")
            except Exception as e:
                config_type = getattr(config, 'type', None) or config.get('type', 'unknown')
                logger.error(f"Failed to create connector for {config_type}: {e}")
    
    async def list_all_files(self):
        """List files from all configured data sources"""
        if self.new_connector:
            async for file in self.new_connector.list_all_files():
                yield file
        else:
            for connector in self.connectors:
                async for file in connector.list():
                    yield file
    
    async def list_all_paths(self):
        """List file paths from all configured data sources"""
        if self.new_connector:
            async for path in self.new_connector.list_all_paths():
                yield path
        else:
            for connector in self.connectors:
                async for path in connector.list_paths():
                    yield path
    
    def get_primary_connector(self) -> Optional[ListFileStrategy]:
        """Get the first (primary) connector"""
        if self.new_connector:
            primary = self.new_connector.get_primary_connector()
            return ListFileStrategyAdapter(primary) if primary else None
        else:
            return self.connectors[0] if self.connectors else None 