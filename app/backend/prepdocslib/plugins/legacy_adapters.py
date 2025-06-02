"""
Legacy adapter plugins for existing ListFileStrategy implementations.
These adapters maintain backward compatibility while enabling the new plugin architecture.
"""

import logging
from typing import Any, Dict, Optional
from collections.abc import AsyncGenerator

from azure.core.credentials_async import AsyncTokenCredential

from ..plugin_base import DataSourceConnector, DataSourcePlugin, DataSourceMetadata
from ..listfilestrategy import File, ListFileStrategy, LocalListFileStrategy, AzureBlobListFileStrategy, ADLSGen2ListFileStrategy

logger = logging.getLogger("scripts")


class LegacyStrategyAdapter(DataSourceConnector):
    """Adapter that wraps a ListFileStrategy to work with the new plugin interface"""
    
    def __init__(
        self,
        strategy: ListFileStrategy,
        metadata: DataSourceMetadata,
        config: Dict[str, Any],
        azure_credential: Optional[AsyncTokenCredential] = None
    ):
        super().__init__(config, azure_credential)
        self.strategy = strategy
        self._metadata = metadata
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return self._metadata
    
    async def validate_config(self) -> bool:
        # For legacy adapters, we assume the strategy was created successfully
        return True
    
    async def test_connection(self) -> bool:
        """Test connection by attempting to list one file"""
        try:
            async for _ in self.strategy.list_paths():
                # If we can list at least one path, connection is good
                return True
            # If no files found, that's still a valid connection
            return True
        except Exception as e:
            logger.error(f"Connection test failed for {self.metadata.name}: {e}")
            return False
    
    async def list_files(self) -> AsyncGenerator[File, None]:
        """List files using the wrapped strategy"""
        async for file in self.strategy.list():
            yield file
    
    async def list_paths(self) -> AsyncGenerator[str, None]:
        """List paths using the wrapped strategy"""
        async for path in self.strategy.list_paths():
            yield path


class LocalFilePlugin(DataSourcePlugin):
    """Plugin for local file system data sources"""
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="local",
            description="Local file system data source",
            version="1.0.0",
            supported_schemes=["file"],
            required_config_fields=["path"],
            optional_config_fields=["pattern"],
            supports_incremental_sync=False,
            supports_metadata_extraction=True,
            supports_authentication=False
        )
    
    def create_connector(
        self, 
        config: Dict[str, Any], 
        azure_credential: Optional[AsyncTokenCredential] = None
    ) -> DataSourceConnector:
        """Create a local file connector"""
        path = config.get("path")
        if not path:
            raise ValueError("Local file connector requires 'path' configuration")
        
        # Create the legacy strategy
        strategy = LocalListFileStrategy(path_pattern=path)
        
        # Wrap it in an adapter
        return LegacyStrategyAdapter(
            strategy=strategy,
            metadata=self.metadata,
            config=config,
            azure_credential=azure_credential
        )
    
    def validate_config_schema(self, config: Dict[str, Any]) -> bool:
        """Validate configuration for local file connector"""
        return isinstance(config.get("path"), str) and config["path"].strip() != ""


class AzureBlobPlugin(DataSourcePlugin):
    """Plugin for Azure Blob Storage data sources"""
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="azure_blob",
            description="Azure Blob Storage data source",
            version="1.0.0",
            supported_schemes=["https", "azure"],
            required_config_fields=["storage_account", "container"],
            optional_config_fields=["blob_prefix", "connection_string", "account_key", "sas_token"],
            supports_incremental_sync=True,
            supports_metadata_extraction=True,
            supports_authentication=True
        )
    
    def create_connector(
        self, 
        config: Dict[str, Any], 
        azure_credential: Optional[AsyncTokenCredential] = None
    ) -> DataSourceConnector:
        """Create an Azure Blob Storage connector"""
        storage_account = config.get("storage_account")
        container = config.get("container")
        
        if not storage_account or not container:
            raise ValueError("Azure Blob Storage connector requires 'storage_account' and 'container'")
        
        # Determine credential to use
        credential = self._get_credential(config, azure_credential)
        
        # Create the legacy strategy
        strategy = AzureBlobListFileStrategy(
            storage_account=storage_account,
            container=container,
            blob_prefix=config.get("blob_prefix"),
            credential=credential
        )
        
        # Wrap it in an adapter
        return LegacyStrategyAdapter(
            strategy=strategy,
            metadata=self.metadata,
            config=config,
            azure_credential=azure_credential
        )
    
    def validate_config_schema(self, config: Dict[str, Any]) -> bool:
        """Validate configuration for Azure Blob Storage connector"""
        storage_account = config.get("storage_account")
        container = config.get("container")
        
        return (
            isinstance(storage_account, str) and storage_account.strip() != "" and
            isinstance(container, str) and container.strip() != ""
        )
    
    def _get_credential(self, config: Dict[str, Any], azure_credential: Optional[AsyncTokenCredential]):
        """Determine the appropriate credential to use"""
        # Priority order:
        # 1. Connection string (if provided)
        # 2. Account key (if provided)  
        # 3. SAS token (if provided)
        # 4. Azure credential (managed identity/service principal)
        
        if config.get("connection_string"):
            return config["connection_string"]
        
        if config.get("account_key"):
            return config["account_key"]
        
        if config.get("sas_token"):
            return config["sas_token"]
        
        if azure_credential:
            return azure_credential
        
        # Return None to use default credential chain
        return None


class ADLSGen2Plugin(DataSourcePlugin):
    """Plugin for Azure Data Lake Storage Gen2 data sources"""
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="adls_gen2",
            description="Azure Data Lake Storage Gen2 data source",
            version="1.0.0",
            supported_schemes=["https", "azure", "adls"],
            required_config_fields=["storage_account", "filesystem"],
            optional_config_fields=["path", "connection_string", "account_key", "sas_token"],
            supports_incremental_sync=True,
            supports_metadata_extraction=True,
            supports_authentication=True
        )
    
    def create_connector(
        self, 
        config: Dict[str, Any], 
        azure_credential: Optional[AsyncTokenCredential] = None
    ) -> DataSourceConnector:
        """Create an ADLS Gen2 connector"""
        storage_account = config.get("storage_account")
        filesystem = config.get("filesystem")
        
        if not storage_account or not filesystem:
            raise ValueError("ADLS Gen2 connector requires 'storage_account' and 'filesystem'")
        
        # Determine credential to use
        credential = self._get_credential(config, azure_credential)
        
        # Create the legacy strategy
        strategy = ADLSGen2ListFileStrategy(
            data_lake_storage_account=storage_account,
            data_lake_filesystem=filesystem,
            data_lake_path=config.get("path", ""),
            credential=credential
        )
        
        # Wrap it in an adapter
        return LegacyStrategyAdapter(
            strategy=strategy,
            metadata=self.metadata,
            config=config,
            azure_credential=azure_credential
        )
    
    def validate_config_schema(self, config: Dict[str, Any]) -> bool:
        """Validate configuration for ADLS Gen2 connector"""
        storage_account = config.get("storage_account")
        filesystem = config.get("filesystem")
        
        return (
            isinstance(storage_account, str) and storage_account.strip() != "" and
            isinstance(filesystem, str) and filesystem.strip() != ""
        )
    
    def _get_credential(self, config: Dict[str, Any], azure_credential: Optional[AsyncTokenCredential]):
        """Determine the appropriate credential to use"""
        # Priority order:
        # 1. Connection string (if provided)
        # 2. Account key (if provided)
        # 3. SAS token (if provided)
        # 4. Azure credential (managed identity/service principal)
        
        if config.get("connection_string"):
            return config["connection_string"]
        
        if config.get("account_key"):
            return config["account_key"]
        
        if config.get("sas_token"):
            return config["sas_token"]
        
        if azure_credential:
            return azure_credential
        
        # Return None to use default credential chain
        return None


def register_legacy_plugins():
    """Register all legacy adapter plugins"""
    from ..plugin_base import register_data_source_plugin
    
    # Register plugins with their original names as aliases for backward compatibility
    register_data_source_plugin(LocalFilePlugin(), aliases=["local_files"])
    register_data_source_plugin(AzureBlobPlugin(), aliases=["blob", "azure_storage"])
    register_data_source_plugin(ADLSGen2Plugin(), aliases=["adls", "data_lake"])
    
    logger.info("Registered legacy adapter plugins") 