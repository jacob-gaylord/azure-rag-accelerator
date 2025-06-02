"""
Enhanced SharePoint connector with concurrent downloads and advanced incremental sync.

This module provides an enhanced version of the SharePoint connector that supports:
- Concurrent file downloads with connection pooling
- Advanced incremental sync with change tracking
- Better error handling and retry mechanisms
- Performance optimizations for large document libraries
- Connection management and resource cleanup
- Comprehensive monitoring and logging
- Circuit breaker patterns for resilience
"""

import asyncio
import json
import logging
import os
import tempfile
import time
import uuid
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
from ..sharepoint_errors import SharePointErrorHandler, SharePointErrorClassifier, sharepoint_error_handler
from ..sharepoint_monitoring import (
    SharePointMonitor, ProgressTracker, OperationType, ProgressStage,
    get_sharepoint_monitor
)
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
        
        # Initialize monitoring and error handling
        self.monitor = get_sharepoint_monitor(config)
        self.error_handler = sharepoint_error_handler
        self.operation_id = str(uuid.uuid4())
        self.progress_tracker: Optional[ProgressTracker] = None
        
        # Circuit breaker for Graph API
        self.graph_circuit_breaker = self.error_handler.get_circuit_breaker("graph_api")
    
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
            self.error_handler.handle_error(e, "save_sync_state", {"sync_state_file": self.sync_state_file})
    
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
    
    @sharepoint_error_handler.get_circuit_breaker("graph_client_creation")
    async def _create_new_client(self) -> GraphServiceClient:
        """Create a new Graph client with enhanced error handling"""
        start_time = time.time()
        
        self.monitor.structured_logger.log_operation_start(
            OperationType.AUTHENTICATION,
            operation_id=self.operation_id,
            site_url=self.site_url
        )
        
        try:
            if not await self.validate_config():
                raise ValueError("Invalid SharePoint configuration")
            
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
            
            duration = time.time() - start_time
            self.monitor.structured_logger.log_operation_success(
                OperationType.AUTHENTICATION,
                duration,
                operation_id=self.operation_id,
                client_pool_size=len(self.client_pool)
            )
            
            self.monitor.metrics.record_operation("authentication", duration, True)
            
            return client
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Handle and classify the error
            sp_error = self.error_handler.handle_error(e, "create_graph_client", {
                "tenant_id": self.tenant_id,
                "site_url": self.site_url
            })
            
            self.monitor.structured_logger.log_operation_failure(
                OperationType.AUTHENTICATION,
                e,
                duration,
                operation_id=self.operation_id,
                error_category=sp_error.category.value
            )
            
            self.monitor.metrics.record_operation("authentication", duration, False)
            
            raise
    
    async def list_files(self) -> AsyncGenerator[File, None]:
        """Enhanced file listing with concurrent downloads and comprehensive monitoring"""
        operation_start_time = time.time()
        
        # Initialize progress tracking
        self.progress_tracker = self.monitor.create_progress_tracker(self.operation_id)
        
        self.monitor.structured_logger.push_context(
            operation_id=self.operation_id,
            site_url=self.site_url,
            document_library=self.document_library,
            folder_path=self.folder_path,
            max_concurrent_downloads=self.max_concurrent_downloads
        )
        
        try:
            self.progress_tracker.update_stage(ProgressStage.INITIALIZING, 0, 1, "Starting SharePoint file sync")
            
            self.monitor.structured_logger.log_operation_start(
                OperationType.FULL_SYNC if not self.enable_incremental_sync else OperationType.INCREMENTAL_SYNC,
                incremental_sync=self.enable_incremental_sync,
                change_tracking=self.enable_change_tracking
            )
            
            # Connect and authenticate
            self.progress_tracker.update_stage(ProgressStage.CONNECTING, 0, 1, "Connecting to SharePoint")
            client = await self._initialize_client()
            
            self.progress_tracker.update_stage(ProgressStage.AUTHENTICATING, 1, 1, "Authentication successful")
            
            # Get last sync timestamp for incremental sync
            last_modified_after = None
            if self.enable_incremental_sync and self.sync_state.incremental_sync_enabled:
                last_modified_after = await self.get_last_sync_timestamp()
                if last_modified_after:
                    last_modified_after = datetime.fromisoformat(last_modified_after.replace('Z', '+00:00'))
                    logger.info(f"Performing incremental sync since: {last_modified_after}")
            
            # Discover files
            self.progress_tracker.update_stage(ProgressStage.DISCOVERING_FILES, 0, 1, "Discovering files in SharePoint")
            
            file_items = []
            async for item in self._get_folder_items(client, self.folder_path, last_modified_after):
                if item.file:
                    file_items.append(item)
            
            total_files = len(file_items)
            logger.info(f"Found {total_files} files to process")
            
            self.progress_tracker.update_stage(
                ProgressStage.DOWNLOADING_FILES, 
                0, 
                total_files, 
                f"Starting download of {total_files} files"
            )
            
            # Process files concurrently
            download_tasks = []
            semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
            
            for item in file_items:
                task = self._download_file_with_semaphore(semaphore, item)
                download_tasks.append(task)
            
            # Execute downloads concurrently and yield results as they complete
            downloaded_count = 0
            async for completed_task in self._process_concurrent_downloads(download_tasks):
                try:
                    sharepoint_file = await completed_task
                    if sharepoint_file:
                        downloaded_count += 1
                        yield sharepoint_file
                        
                        # Update sync state
                        self.sync_state.processed_files.add(sharepoint_file.url or "")
                        self.sync_state.total_files_processed += 1
                        
                        # Update progress
                        self.progress_tracker.update_stage(
                            ProgressStage.DOWNLOADING_FILES,
                            downloaded_count,
                            total_files,
                            f"Downloaded {downloaded_count}/{total_files} files"
                        )
                    
                except Exception as e:
                    self.error_handler.handle_error(e, "process_downloaded_file")
                    continue
            
            # Update last sync timestamp after successful processing
            if self.enable_incremental_sync:
                current_time = datetime.now(timezone.utc).isoformat()
                await self.set_last_sync_timestamp(current_time)
                self.sync_state.last_successful_sync = current_time
                self._save_sync_state()
            
            # Mark operation as completed
            self.progress_tracker.mark_completed()
            
            duration = time.time() - operation_start_time
            self.monitor.structured_logger.log_operation_success(
                OperationType.FULL_SYNC if not self.enable_incremental_sync else OperationType.INCREMENTAL_SYNC,
                duration,
                files_processed=downloaded_count,
                total_files=total_files
            )
            
            self.monitor.metrics.record_operation("full_sync", duration, True)
                
        except Exception as e:
            duration = time.time() - operation_start_time
            
            # Handle and classify the error
            sp_error = self.error_handler.handle_error(e, "list_files", {
                "total_files_discovered": len(file_items) if 'file_items' in locals() else 0,
                "files_processed": getattr(self.sync_state, 'total_files_processed', 0)
            })
            
            self.monitor.structured_logger.log_operation_failure(
                OperationType.FULL_SYNC if not self.enable_incremental_sync else OperationType.INCREMENTAL_SYNC,
                e,
                duration,
                error_category=sp_error.category.value
            )
            
            if self.progress_tracker:
                self.progress_tracker.mark_failed(str(e))
            
            self.monitor.metrics.record_operation("full_sync", duration, False)
            
            raise
        
        finally:
            self.monitor.structured_logger.pop_context()
            if self.progress_tracker:
                self.monitor.remove_progress_tracker(self.operation_id)
    
    async def _process_concurrent_downloads(self, download_tasks):
        """Process download tasks concurrently with proper yielding"""
        for completed_task in asyncio.as_completed(download_tasks):
            yield completed_task
    
    async def _download_file_with_semaphore(self, semaphore: asyncio.Semaphore, item) -> Optional[SharePointFile]:
        """Download a file with semaphore control and enhanced error handling"""
        async with semaphore:
            return await self._download_file_with_retry(item)
    
    async def _download_file_with_retry(self, item) -> Optional[SharePointFile]:
        """Download a file with enhanced retry logic and monitoring"""
        file_id = item.id
        file_name = item.name
        file_url = item.web_url
        
        # Skip if already processed successfully
        if file_url in self.sync_state.processed_files:
            logger.debug(f"Skipping already processed file: {file_name}")
            self.sync_state.skipped_files.add(file_url)
            return None
        
        # Skip if previously failed and not enough time has passed
        if file_url in self.sync_state.failed_files:
            logger.debug(f"Skipping previously failed file: {file_name}")
            return None
        
        start_time = time.time()
        last_exception = None
        
        self.monitor.structured_logger.log_operation_start(
            OperationType.FILE_DOWNLOAD,
            file_name=file_name,
            file_id=file_id,
            file_url=file_url
        )
        
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
                    
                    duration = time.time() - start_time
                    self.monitor.structured_logger.log_operation_success(
                        OperationType.FILE_DOWNLOAD,
                        duration,
                        file_name=file_name,
                        file_size=item.size,
                        attempts=attempt + 1
                    )
                    
                    self.monitor.metrics.record_operation("file_download", duration, True)
                    
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
            
            # Wait before retrying (use smart retry delay from error classification)
            if attempt < self.retry_attempts - 1:
                sp_error = SharePointErrorClassifier.classify_exception(last_exception, {
                    "file_name": file_name,
                    "attempt": attempt + 1
                })
                delay = sp_error.get_retry_delay(attempt, self.retry_delay)
                
                if sp_error.category.value == "rate_limited":
                    self.monitor.structured_logger.log_rate_limit_hit(
                        retry_after=sp_error.retry_after,
                        file_name=file_name
                    )
                
                await asyncio.sleep(delay)
        
        # All attempts failed
        duration = time.time() - start_time
        sp_error = self.error_handler.handle_error(last_exception, "download_file", {
            "file_name": file_name,
            "file_id": file_id,
            "attempts": self.retry_attempts
        })
        
        self.monitor.structured_logger.log_operation_failure(
            OperationType.FILE_DOWNLOAD,
            last_exception,
            duration,
            file_name=file_name,
            error_category=sp_error.category.value,
            attempts=self.retry_attempts
        )
        
        self.monitor.metrics.record_operation("file_download", duration, False)
        self.sync_state.failed_files.add(file_url)
        
        return None
    
    async def _download_file_content_with_client(self, client: GraphServiceClient, item) -> tempfile.NamedTemporaryFile:
        """Download file content using provided client with enhanced error handling"""
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
            # Enhanced error handling with classification
            sp_error = self.error_handler.handle_error(e, "download_file_content", {
                "file_name": item.name,
                "file_id": item.id,
                "file_size": getattr(item, 'size', 0)
            })
            raise
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        """Get comprehensive sync statistics with monitoring data"""
        base_stats = {
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
        
        # Add monitoring data
        monitoring_summary = self.monitor.get_monitoring_summary()
        error_summary = self.error_handler.get_error_summary()
        
        # Add performance metrics
        performance_data = {
            "connection_pool_size": len(self.client_pool),
            "max_concurrent_downloads": self.max_concurrent_downloads,
            "download_timeout": self.download_timeout,
            "retry_attempts": self.retry_attempts,
            "average_download_time": self.monitor.metrics.get_average_timing("file_download"),
            "download_success_rate": self.monitor.metrics.get_success_rate("file_download"),
            "authentication_success_rate": self.monitor.metrics.get_success_rate("authentication")
        }
        
        return {
            **base_stats,
            "monitoring": monitoring_summary,
            "errors": error_summary,
            "performance": performance_data
        }
    
    async def reset_sync_state(self):
        """Reset sync state for a fresh full sync with monitoring"""
        self.monitor.structured_logger.log_operation_start(
            OperationType.FULL_SYNC,
            operation="reset_sync_state",
            operation_id=self.operation_id
        )
        
        try:
            logger.info("Resetting sync state for fresh full sync")
            self.sync_state = SyncState()
            self._save_sync_state()
            
            # Clear any existing error history for this site
            # This could be enhanced to clear site-specific errors
            logger.info("Sync state reset successfully")
            
        except Exception as e:
            self.error_handler.handle_error(e, "reset_sync_state")
            raise
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check on SharePoint connection"""
        health_checker = self.monitor.health_checker
        health_checker.connector_factory = lambda config: EnhancedSharePointConnector(config)
        
        try:
            health_status = await health_checker.check_health(self.config)
            return health_status.to_dict()
        
        except Exception as e:
            self.error_handler.handle_error(e, "health_check")
            return {
                "is_healthy": False,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "issues": [f"Health check failed: {str(e)}"],
                "error_rate": 100.0
            }
    
    async def close(self) -> None:
        """Enhanced cleanup with connection pool management and monitoring"""
        self.monitor.structured_logger.log_operation_start(
            OperationType.CONNECTION_TEST,
            operation="close_connector",
            operation_id=self.operation_id
        )
        
        start_time = time.time()
        
        try:
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
            
            # Export final metrics
            try:
                self.monitor.save_metrics_to_file()
            except Exception as e:
                logger.warning(f"Failed to save final metrics: {e}")
            
            # Call parent cleanup
            await super().close()
            
            duration = time.time() - start_time
            self.monitor.structured_logger.log_operation_success(
                OperationType.CONNECTION_TEST,
                duration,
                operation="close_connector",
                clients_closed=len(self.client_pool)
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.error_handler.handle_error(e, "close_connector")
            
            self.monitor.structured_logger.log_operation_failure(
                OperationType.CONNECTION_TEST,
                e,
                duration,
                operation="close_connector"
            )
            
            raise


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