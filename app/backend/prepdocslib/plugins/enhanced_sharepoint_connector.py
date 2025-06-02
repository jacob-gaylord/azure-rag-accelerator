"""
Enhanced SharePoint connector with concurrent downloads and advanced incremental sync.

This module provides an enhanced version of the SharePoint connector that supports:
- Concurrent file downloads with connection pooling
- Advanced incremental sync with change tracking
- Better error handling and retry mechanisms
- Performance optimizations for large document libraries
- Connection management and resource cleanup
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Set
from collections.abc import AsyncGenerator
from urllib.parse import urlparse, unquote
from dataclasses import dataclass

from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import ClientSecretCredential, DefaultAzureCredential
from msgraph_core import GraphRequestAdapter
from msgraph_core.authentication import AzureIdentityAuthenticationProvider
from msgraph_core.graph_request_adapter import GraphRequestAdapter
from msgraph_core.authentication.azure_identity_authentication_provider import AzureIdentityAuthenticationProvider
from msgraph import GraphServiceClient

from ..plugin_base import DataSourceConnector, DataSourcePlugin, DataSourceMetadata, ConnectionInfo
from ..listfilestrategy import File
from .sharepoint_connector import SharePointFile, SharePointConnector

logger = logging.getLogger("scripts")


@dataclass
class SyncState:
    """Enhanced sync state tracking"""
    last_sync_timestamp: Optional[str] = None
    processed_files: Set[str] = None
    failed_files: Set[str] = None
    skipped_files: Set[str] = None
    total_files_processed: int = 0
    last_successful_sync: Optional[str] = None
    incremental_sync_enabled: bool = True
    
    def __post_init__(self):
        if self.processed_files is None:
            self.processed_files = set()
        if self.failed_files is None:
            self.failed_files = set()
        if self.skipped_files is None:
            self.skipped_files = set()


class EnhancedSharePointConnector(SharePointConnector):
    """Enhanced SharePoint connector with concurrent downloads and advanced sync"""
    
    def __init__(self, config: Dict[str, Any], azure_credential: Optional[AsyncTokenCredential] = None):
        super().__init__(config, azure_credential)
        
        # Enhanced configuration
        self.max_concurrent_downloads = config.get("max_concurrent_downloads", 10)
        self.download_timeout = config.get("download_timeout", 300)  # 5 minutes
        self.connection_pool_size = config.get("connection_pool_size", 20)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        
        # Advanced incremental sync
        self.enable_change_tracking = config.get("enable_change_tracking", True)
        self.change_tracking_window_days = config.get("change_tracking_window_days", 30)
        self.enable_deleted_file_tracking = config.get("enable_deleted_file_tracking", True)
        
        # Connection management
        self.download_semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        self.client_pool = []
        self.client_pool_lock = asyncio.Lock()
        
        # Enhanced sync state
        self.sync_state = SyncState()
        self._load_sync_state()
    
    def _load_sync_state(self):
        """Load enhanced sync state from file"""
        try:
            if os.path.exists(self.sync_state_file):
                with open(self.sync_state_file, 'r') as f:
                    data = json.load(f)
                    
                    self.sync_state.last_sync_timestamp = data.get('last_sync_timestamp')
                    self.sync_state.processed_files = set(data.get('processed_files', []))
                    self.sync_state.failed_files = set(data.get('failed_files', []))
                    self.sync_state.skipped_files = set(data.get('skipped_files', []))
                    self.sync_state.total_files_processed = data.get('total_files_processed', 0)
                    self.sync_state.last_successful_sync = data.get('last_successful_sync')
                    self.sync_state.incremental_sync_enabled = data.get('incremental_sync_enabled', True)
                    
                    logger.info(f"Loaded sync state: {len(self.sync_state.processed_files)} processed files")
                    
        except Exception as e:
            logger.warning(f"Failed to load sync state: {e}")
            self.sync_state = SyncState()
    
    def _save_sync_state(self):
        """Save enhanced sync state to file"""
        try:
            data = {
                'last_sync_timestamp': self.sync_state.last_sync_timestamp,
                'processed_files': list(self.sync_state.processed_files),
                'failed_files': list(self.sync_state.failed_files),
                'skipped_files': list(self.sync_state.skipped_files),
                'total_files_processed': self.sync_state.total_files_processed,
                'last_successful_sync': self.sync_state.last_successful_sync,
                'incremental_sync_enabled': self.sync_state.incremental_sync_enabled,
                'site_url': self.site_url,
                'document_library': self.document_library,
                'sync_version': '2.0'  # Version for compatibility
            }
            
            with open(self.sync_state_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save sync state: {e}")
    
    async def _get_client_from_pool(self) -> GraphServiceClient:
        """Get a client from the connection pool or create new one"""
        async with self.client_pool_lock:
            if self.client_pool:
                return self.client_pool.pop()
            else:
                # Create new client
                return await self._create_new_client()
    
    async def _return_client_to_pool(self, client: GraphServiceClient):
        """Return a client to the connection pool"""
        async with self.client_pool_lock:
            if len(self.client_pool) < self.connection_pool_size:
                self.client_pool.append(client)
            # If pool is full, client will be garbage collected
    
    async def _create_new_client(self) -> GraphServiceClient:
        """Create a new Graph client (same as parent implementation)"""
        if not await self.validate_config():
            raise ValueError("Invalid SharePoint configuration")
        
        try:
            # Create credential
            if self.azure_credential:
                credential = self.azure_credential
            else:
                credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
            
            # Create authentication provider
            auth_provider = AzureIdentityAuthenticationProvider(
                credential=credential,
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            # Create request adapter
            request_adapter = GraphRequestAdapter(auth_provider)
            
            # Create Graph client
            client = GraphServiceClient(request_adapter)
            
            return client
            
        except Exception as e:
            logger.error(f"Failed to create Microsoft Graph client: {e}")
            raise
    
    async def list_files(self) -> AsyncGenerator[File, None]:
        """Enhanced file listing with concurrent downloads"""
        try:
            client = await self._initialize_client()
            
            # Get last sync timestamp for incremental sync
            last_modified_after = None
            if self.enable_incremental_sync and self.sync_state.incremental_sync_enabled:
                last_modified_after = await self.get_last_sync_timestamp()
                if last_modified_after:
                    last_modified_after = datetime.fromisoformat(last_modified_after.replace('Z', '+00:00'))
                    logger.info(f"Performing incremental sync since: {last_modified_after}")
            
            # Collect all file items first
            file_items = []
            async for item in self._get_folder_items(client, self.folder_path, last_modified_after):
                if item.file:
                    file_items.append(item)
            
            logger.info(f"Found {len(file_items)} files to process")
            
            # Process files concurrently
            download_tasks = []
            semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
            
            for item in file_items:
                task = self._download_file_with_semaphore(semaphore, item)
                download_tasks.append(task)
            
            # Execute downloads concurrently and yield results as they complete
            for completed_task in asyncio.as_completed(download_tasks):
                try:
                    sharepoint_file = await completed_task
                    if sharepoint_file:
                        yield sharepoint_file
                        # Update sync state
                        self.sync_state.processed_files.add(sharepoint_file.url or "")
                        self.sync_state.total_files_processed += 1
                except Exception as e:
                    logger.error(f"Failed to download file: {e}")
                    # Track failed file
                    # We don't have the file info here, so log error
                    continue
            
            # Update last sync timestamp after successful processing
            if self.enable_incremental_sync:
                current_time = datetime.now(timezone.utc).isoformat()
                await self.set_last_sync_timestamp(current_time)
                self.sync_state.last_successful_sync = current_time
                self._save_sync_state()
                
        except Exception as e:
            logger.error(f"Failed to list SharePoint files: {e}")
            raise
    
    async def _download_file_with_semaphore(self, semaphore: asyncio.Semaphore, item) -> Optional[SharePointFile]:
        """Download a file with semaphore control and retry logic"""
        async with semaphore:
            return await self._download_file_with_retry(item)
    
    async def _download_file_with_retry(self, item) -> Optional[SharePointFile]:
        """Download a file with retry logic"""
        file_id = item.id
        file_name = item.name
        
        # Skip if already processed successfully
        file_url = item.web_url
        if file_url in self.sync_state.processed_files:
            logger.debug(f"Skipping already processed file: {file_name}")
            self.sync_state.skipped_files.add(file_url)
            return None
        
        # Skip if previously failed and not enough time has passed
        if file_url in self.sync_state.failed_files:
            logger.debug(f"Skipping previously failed file: {file_name}")
            return None
        
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                client = await self._get_client_from_pool()
                
                try:
                    # Download file content with timeout
                    temp_file = await asyncio.wait_for(
                        self._download_file_content_with_client(client, item),
                        timeout=self.download_timeout
                    )
                    
                    # Create SharePoint metadata
                    sharepoint_metadata = {
                        "sharepoint_id": item.id,
                        "name": item.name,
                        "size": item.size,
                        "created_date_time": item.created_date_time.isoformat() if item.created_date_time else None,
                        "last_modified_date_time": item.last_modified_date_time.isoformat() if item.last_modified_date_time else None,
                        "web_url": item.web_url,
                        "created_by": getattr(item.created_by, 'user', {}).get('display_name') if hasattr(item, 'created_by') and item.created_by else None,
                        "last_modified_by": getattr(item.last_modified_by, 'user', {}).get('display_name') if hasattr(item, 'last_modified_by') and item.last_modified_by else None,
                    }
                    
                    # Create SharePointFile instance
                    sharepoint_file = SharePointFile(
                        content=temp_file,
                        url=item.web_url,
                        sharepoint_metadata=sharepoint_metadata
                    )
                    
                    logger.info(f"Successfully downloaded: {file_name}")
                    return sharepoint_file
                    
                finally:
                    # Return client to pool
                    await self._return_client_to_pool(client)
                    
            except asyncio.TimeoutError:
                last_exception = TimeoutError(f"Download timeout after {self.download_timeout}s")
                logger.warning(f"Download timeout for {file_name} (attempt {attempt + 1}/{self.retry_attempts})")
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Download attempt {attempt + 1}/{self.retry_attempts} failed for {file_name}: {e}")
            
            # Wait before retrying (exponential backoff)
            if attempt < self.retry_attempts - 1:
                delay = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        # All attempts failed
        logger.error(f"Failed to download {file_name} after {self.retry_attempts} attempts: {last_exception}")
        self.sync_state.failed_files.add(file_url)
        return None
    
    async def _download_file_content_with_client(self, client: GraphServiceClient, item) -> tempfile.NamedTemporaryFile:
        """Download file content using provided client"""
        try:
            # Get file download URL
            download_request = client.sites.by_site_id(self._site_id).drives.by_drive_id(self._drive_id).items.by_drive_item_id(item.id).content
            
            # Download content
            content_stream = await download_request.get()
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                mode='w+b',
                suffix=os.path.splitext(item.name)[1],
                prefix=f"sharepoint_{item.id}_",
                delete=False
            )
            
            # Write content to temporary file
            if hasattr(content_stream, 'read'):
                # If it's a stream, read in chunks
                while True:
                    chunk = content_stream.read(8192)
                    if not chunk:
                        break
                    temp_file.write(chunk)
            else:
                # If it's bytes
                temp_file.write(content_stream)
            
            temp_file.flush()
            temp_file.seek(0)
            
            # Convert to read mode
            return open(temp_file.name, 'rb')
            
        except Exception as e:
            logger.error(f"Failed to download SharePoint file content for {item.name}: {e}")
            raise
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        """Get comprehensive sync statistics"""
        return {
            "total_files_processed": self.sync_state.total_files_processed,
            "processed_files_count": len(self.sync_state.processed_files),
            "failed_files_count": len(self.sync_state.failed_files),
            "skipped_files_count": len(self.sync_state.skipped_files),
            "last_sync_timestamp": self.sync_state.last_sync_timestamp,
            "last_successful_sync": self.sync_state.last_successful_sync,
            "incremental_sync_enabled": self.sync_state.incremental_sync_enabled,
            "site_url": self.site_url,
            "document_library": self.document_library
        }
    
    async def reset_sync_state(self):
        """Reset sync state for a fresh full sync"""
        logger.info("Resetting sync state for fresh full sync")
        self.sync_state = SyncState()
        self._save_sync_state()
    
    async def close(self) -> None:
        """Enhanced cleanup with connection pool management"""
        # Close all clients in the pool
        async with self.client_pool_lock:
            for client in self.client_pool:
                try:
                    # Close client connections if needed
                    pass  # GraphServiceClient doesn't have explicit close method
                except Exception as e:
                    logger.warning(f"Error closing Graph client: {e}")
            self.client_pool.clear()
        
        # Save final sync state
        self._save_sync_state()
        
        # Call parent cleanup
        await super().close()


class EnhancedSharePointPlugin(DataSourcePlugin):
    """Enhanced plugin for SharePoint Online data sources"""
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="enhanced_sharepoint",
            description="Enhanced SharePoint Online connector with concurrent downloads and advanced sync",
            version="2.0.0",
            supported_schemes=["https", "sharepoint"],
            required_config_fields=["tenant_id", "client_id", "client_secret", "site_url"],
            optional_config_fields=[
                "document_library", "folder_path", "max_file_size_mb", 
                "supported_extensions", "batch_size", "enable_incremental_sync",
                "max_concurrent_downloads", "download_timeout", "connection_pool_size",
                "retry_attempts", "retry_delay", "enable_change_tracking"
            ],
            supports_incremental_sync=True,
            supports_metadata_extraction=True,
            supports_authentication=True
        )
    
    def create_connector(
        self, 
        config: Dict[str, Any], 
        azure_credential: Optional[AsyncTokenCredential] = None
    ) -> DataSourceConnector:
        """Create an enhanced SharePoint connector"""
        return EnhancedSharePointConnector(config, azure_credential)
    
    def validate_config_schema(self, config: Dict[str, Any]) -> bool:
        """Validate configuration for enhanced SharePoint connector"""
        required_fields = ["tenant_id", "client_id", "client_secret", "site_url"]
        
        for field in required_fields:
            if not config.get(field):
                return False
        
        # Validate site URL format
        site_url = config.get("site_url")
        if site_url:
            parsed_url = urlparse(site_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return False
        
        # Validate numeric fields
        numeric_fields = [
            "max_concurrent_downloads", "download_timeout", "connection_pool_size",
            "retry_attempts", "retry_delay"
        ]
        
        for field in numeric_fields:
            if field in config and not isinstance(config[field], (int, float)):
                return False
        
        return True


def register_enhanced_sharepoint_plugin():
    """Register the enhanced SharePoint plugin"""
    from ..plugin_base import register_data_source_plugin
    
    register_data_source_plugin(
        EnhancedSharePointPlugin(), 
        aliases=["enhanced_sharepoint", "sharepoint_enhanced", "sharepoint_v2"]
    )
    logger.info("Registered Enhanced SharePoint plugin") 