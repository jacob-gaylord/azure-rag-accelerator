import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union

from azure.core.credentials_async import AsyncTokenCredential

from .listfilestrategy import File

logger = logging.getLogger("scripts")


@dataclass
class DataSourceMetadata:
    """Metadata for a data source connector plugin"""
    name: str
    description: str
    version: str = "1.0.0"
    supported_schemes: List[str] = field(default_factory=list)
    required_config_fields: List[str] = field(default_factory=list)
    optional_config_fields: List[str] = field(default_factory=list)
    supports_incremental_sync: bool = False
    supports_metadata_extraction: bool = False
    supports_authentication: bool = False


@dataclass
class ConnectionInfo:
    """Information about a data source connection"""
    source_id: str
    source_type: str
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataSourceConnector(ABC):
    """
    Abstract base class for all data source connectors.
    This defines the interface that all data source plugins must implement.
    """
    
    def __init__(self, config: Dict[str, Any], azure_credential: Optional[AsyncTokenCredential] = None):
        self.config = config
        self.azure_credential = azure_credential
        self._connection_info: Optional[ConnectionInfo] = None
    
    @property
    @abstractmethod
    def metadata(self) -> DataSourceMetadata:
        """Return metadata about this connector"""
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate the configuration for this connector"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the data source"""
        pass
    
    @abstractmethod
    async def list_files(self) -> AsyncGenerator[File, None]:
        """List all files from the data source"""
        if False:  # pragma: no cover - this is necessary for mypy to type check
            yield
    
    @abstractmethod
    async def list_paths(self) -> AsyncGenerator[str, None]:
        """List all file paths from the data source"""
        if False:  # pragma: no cover - this is necessary for mypy to type check
            yield
    
    async def get_connection_info(self) -> ConnectionInfo:
        """Get connection information for this data source"""
        if self._connection_info is None:
            self._connection_info = ConnectionInfo(
                source_id=self.config.get("id", "unknown"),
                source_type=self.metadata.name,
                endpoint=self.config.get("endpoint"),
                metadata=self.config.get("metadata", {})
            )
        return self._connection_info
    
    async def supports_incremental_sync(self) -> bool:
        """Check if this connector supports incremental synchronization"""
        return self.metadata.supports_incremental_sync
    
    async def get_last_sync_timestamp(self) -> Optional[str]:
        """Get the timestamp of the last successful sync (if supported)"""
        if not await self.supports_incremental_sync():
            return None
        # Default implementation - subclasses should override
        return None
    
    async def set_last_sync_timestamp(self, timestamp: str) -> None:
        """Set the timestamp of the last successful sync (if supported)"""
        if not await self.supports_incremental_sync():
            return
        # Default implementation - subclasses should override
        pass
    
    async def close(self) -> None:
        """Clean up resources"""
        pass


class DataSourcePlugin(ABC):
    """
    Abstract base class for data source plugin implementations.
    Plugins are responsible for creating and managing connectors.
    """
    
    @property
    @abstractmethod
    def metadata(self) -> DataSourceMetadata:
        """Return metadata about this plugin"""
        pass
    
    @abstractmethod
    def create_connector(
        self, 
        config: Dict[str, Any], 
        azure_credential: Optional[AsyncTokenCredential] = None
    ) -> DataSourceConnector:
        """Create a connector instance from configuration"""
        pass
    
    @abstractmethod
    def validate_config_schema(self, config: Dict[str, Any]) -> bool:
        """Validate the configuration schema for this plugin"""
        pass
    
    def get_config_template(self) -> Dict[str, Any]:
        """Return a configuration template for this plugin"""
        template = {
            "type": self.metadata.name,
            "description": self.metadata.description
        }
        
        # Add required fields with placeholder values
        for field in self.metadata.required_config_fields:
            template[field] = f"<{field}>"
        
        # Add optional fields as comments in the template
        if self.metadata.optional_config_fields:
            template["_optional_fields"] = {
                field: f"<optional_{field}>" 
                for field in self.metadata.optional_config_fields
            }
        
        return template


class PluginRegistry:
    """Registry for managing data source plugins"""
    
    def __init__(self):
        self._plugins: Dict[str, DataSourcePlugin] = {}
        self._aliases: Dict[str, str] = {}
    
    def register_plugin(self, plugin: DataSourcePlugin, aliases: Optional[List[str]] = None) -> None:
        """Register a plugin with optional aliases"""
        plugin_name = plugin.metadata.name
        
        if plugin_name in self._plugins:
            logger.warning(f"Plugin {plugin_name} is already registered, overriding")
        
        self._plugins[plugin_name] = plugin
        logger.info(f"Registered data source plugin: {plugin_name}")
        
        # Register aliases
        if aliases:
            for alias in aliases:
                if alias in self._aliases:
                    logger.warning(f"Alias {alias} is already registered, overriding")
                self._aliases[alias] = plugin_name
                logger.debug(f"Registered alias {alias} -> {plugin_name}")
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister a plugin and its aliases"""
        if plugin_name not in self._plugins:
            raise ValueError(f"Plugin {plugin_name} is not registered")
        
        # Remove plugin
        del self._plugins[plugin_name]
        
        # Remove aliases
        aliases_to_remove = [alias for alias, name in self._aliases.items() if name == plugin_name]
        for alias in aliases_to_remove:
            del self._aliases[alias]
        
        logger.info(f"Unregistered plugin: {plugin_name}")
    
    def get_plugin(self, name_or_alias: str) -> Optional[DataSourcePlugin]:
        """Get a plugin by name or alias"""
        # Check direct name match first
        if name_or_alias in self._plugins:
            return self._plugins[name_or_alias]
        
        # Check aliases
        if name_or_alias in self._aliases:
            plugin_name = self._aliases[name_or_alias]
            return self._plugins[plugin_name]
        
        return None
    
    def list_plugins(self) -> List[DataSourcePlugin]:
        """List all registered plugins"""
        return list(self._plugins.values())
    
    def list_plugin_names(self) -> List[str]:
        """List all registered plugin names"""
        return list(self._plugins.keys())
    
    def get_plugin_for_scheme(self, scheme: str) -> Optional[DataSourcePlugin]:
        """Get a plugin that supports the given scheme"""
        for plugin in self._plugins.values():
            if scheme in plugin.metadata.supported_schemes:
                return plugin
        return None
    
    def create_connector(
        self, 
        config: Dict[str, Any], 
        azure_credential: Optional[AsyncTokenCredential] = None
    ) -> DataSourceConnector:
        """Create a connector from configuration"""
        connector_type = config.get("type")
        if not connector_type:
            raise ValueError("Configuration must specify a 'type' field")
        
        plugin = self.get_plugin(connector_type)
        if not plugin:
            available_types = ", ".join(self.list_plugin_names())
            raise ValueError(f"Unknown connector type: {connector_type}. Available types: {available_types}")
        
        # Validate configuration
        if not plugin.validate_config_schema(config):
            raise ValueError(f"Invalid configuration for connector type: {connector_type}")
        
        return plugin.create_connector(config, azure_credential)


# Global plugin registry instance
_global_registry = PluginRegistry()


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry"""
    return _global_registry


def register_data_source_plugin(plugin: DataSourcePlugin, aliases: Optional[List[str]] = None) -> None:
    """Register a data source plugin globally"""
    _global_registry.register_plugin(plugin, aliases)


class MultiDataSourceConnector:
    """
    Connector that manages multiple data source connectors and provides
    a unified interface for processing files from all sources.
    """
    
    def __init__(
        self,
        configs: List[Dict[str, Any]],
        azure_credential: Optional[AsyncTokenCredential] = None,
        registry: Optional[PluginRegistry] = None
    ):
        self.configs = configs
        self.azure_credential = azure_credential
        self.registry = registry or get_plugin_registry()
        self.connectors: List[DataSourceConnector] = []
        self._initialize_connectors()
    
    def _initialize_connectors(self) -> None:
        """Initialize connectors for each configuration"""
        for config in self.configs:
            try:
                connector = self.registry.create_connector(config, self.azure_credential)
                self.connectors.append(connector)
                logger.info(f"Created connector for {config.get('type', 'unknown')} data source")
            except Exception as e:
                logger.error(f"Failed to create connector for {config.get('type', 'unknown')}: {e}")
    
    async def validate_all_connections(self) -> Dict[str, bool]:
        """Test connections for all connectors"""
        results = {}
        for i, connector in enumerate(self.connectors):
            try:
                is_valid = await connector.test_connection()
                connection_info = await connector.get_connection_info()
                results[connection_info.source_id] = is_valid
            except Exception as e:
                logger.error(f"Failed to validate connector {i}: {e}")
                results[f"connector_{i}"] = False
        return results
    
    async def list_all_files(self) -> AsyncGenerator[File, None]:
        """List files from all configured data sources"""
        tasks = []
        for connector in self.connectors:
            tasks.append(self._list_files_from_connector(connector))
        
        # Execute all connector tasks concurrently
        for task in asyncio.as_completed(tasks):
            async for file in await task:
                yield file
    
    async def _list_files_from_connector(self, connector: DataSourceConnector) -> AsyncGenerator[File, None]:
        """List files from a single connector"""
        try:
            async for file in connector.list_files():
                yield file
        except Exception as e:
            connection_info = await connector.get_connection_info()
            logger.error(f"Error listing files from {connection_info.source_type}: {e}")
    
    async def list_all_paths(self) -> AsyncGenerator[str, None]:
        """List file paths from all configured data sources"""
        for connector in self.connectors:
            try:
                async for path in connector.list_paths():
                    yield path
            except Exception as e:
                connection_info = await connector.get_connection_info()
                logger.error(f"Error listing paths from {connection_info.source_type}: {e}")
    
    def get_primary_connector(self) -> Optional[DataSourceConnector]:
        """Get the first (primary) connector"""
        return self.connectors[0] if self.connectors else None
    
    async def close_all(self) -> None:
        """Close all connectors"""
        for connector in self.connectors:
            try:
                await connector.close()
            except Exception as e:
                logger.error(f"Error closing connector: {e}") 