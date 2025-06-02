import logging
from typing import Union, Optional
from azure.core.credentials_async import AsyncTokenCredential

from .config import DataSourceConfig
from .listfilestrategy import (
    ListFileStrategy,
    LocalListFileStrategy,
    AzureBlobListFileStrategy,
    ADLSGen2ListFileStrategy,
)

logger = logging.getLogger("scripts")


class DataSourceConnectorFactory:
    """Factory for creating data source connectors based on configuration"""
    
    @staticmethod
    def create_connector(
        config: DataSourceConfig,
        azure_credential: Optional[AsyncTokenCredential] = None
    ) -> ListFileStrategy:
        """Create a data source connector based on configuration"""
        
        if config.type == "local":
            if not config.path:
                raise ValueError("Local data source requires a path")
            return LocalListFileStrategy(path_pattern=config.path)
        
        elif config.type == "azure_blob":
            if not config.storage_account or not config.container:
                raise ValueError("Azure Blob data source requires storage_account and container")
            
            # Determine credential to use
            credential = DataSourceConnectorFactory._get_credential(
                config, azure_credential
            )
            
            return AzureBlobListFileStrategy(
                storage_account=config.storage_account,
                container=config.container,
                blob_prefix=config.blob_prefix,
                credential=credential
            )
        
        elif config.type == "adls_gen2":
            if not config.storage_account or not config.filesystem:
                raise ValueError("ADLS Gen2 data source requires storage_account and filesystem")
            
            # Determine credential to use
            credential = DataSourceConnectorFactory._get_credential(
                config, azure_credential
            )
            
            return ADLSGen2ListFileStrategy(
                data_lake_storage_account=config.storage_account,
                data_lake_filesystem=config.filesystem,
                data_lake_path=config.path or "",
                credential=credential
            )
        
        else:
            raise ValueError(f"Unsupported data source type: {config.type}")
    
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
    def validate_config(config: DataSourceConfig) -> bool:
        """Validate a data source configuration"""
        
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
    def get_supported_types() -> list[str]:
        """Get list of supported data source types"""
        return ["local", "azure_blob", "adls_gen2"]


class MultiDataSourceConnector:
    """Connector that can handle multiple data sources"""
    
    def __init__(
        self,
        configs: list[DataSourceConfig],
        azure_credential: Optional[AsyncTokenCredential] = None
    ):
        self.configs = configs
        self.azure_credential = azure_credential
        self.connectors: list[ListFileStrategy] = []
        
        # Create connectors for each configuration
        for config in configs:
            if not DataSourceConnectorFactory.validate_config(config):
                logger.warning(f"Invalid configuration for data source type {config.type}, skipping")
                continue
            
            try:
                connector = DataSourceConnectorFactory.create_connector(config, azure_credential)
                self.connectors.append(connector)
                logger.info(f"Created connector for {config.type} data source")
            except Exception as e:
                logger.error(f"Failed to create connector for {config.type}: {e}")
    
    async def list_all_files(self):
        """List files from all configured data sources"""
        for connector in self.connectors:
            async for file in connector.list():
                yield file
    
    async def list_all_paths(self):
        """List file paths from all configured data sources"""
        for connector in self.connectors:
            async for path in connector.list_paths():
                yield path
    
    def get_primary_connector(self) -> Optional[ListFileStrategy]:
        """Get the first (primary) connector"""
        return self.connectors[0] if self.connectors else None 