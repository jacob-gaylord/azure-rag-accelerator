"""
SharePoint connector plugin for the data source system.
Uses Microsoft Graph API to access SharePoint Online document libraries.
"""

import asyncio
import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from collections.abc import AsyncGenerator
from urllib.parse import urlparse, unquote

from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import ClientSecretCredential, DefaultAzureCredential
from msgraph_core import BaseGraphRequestAdapter, AzureIdentityAuthenticationProvider
from msgraph import GraphServiceClient

from ..plugin_base import DataSourceConnector, DataSourcePlugin, DataSourceMetadata, ConnectionInfo
from ..listfilestrategy import File

logger = logging.getLogger("scripts")


class SharePointFile(File):
    """Extended File class for SharePoint files with additional metadata"""
    
    def __init__(
        self,
        content,
        acls: Optional[dict] = None,
        url: Optional[str] = None,
        sharepoint_metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(content, acls, url)
        self.sharepoint_metadata = sharepoint_metadata or {}
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get SharePoint-specific metadata"""
        return self.sharepoint_metadata


class SharePointConnector(DataSourceConnector):
    """SharePoint data source connector using Microsoft Graph API"""
    
    def __init__(self, config: Dict[str, Any], azure_credential: Optional[AsyncTokenCredential] = None):
        super().__init__(config, azure_credential)
        self.client: Optional[GraphServiceClient] = None
        self._site_id: Optional[str] = None
        self._drive_id: Optional[str] = None
        self._last_sync_file: Optional[str] = None
        
        # Configuration validation
        self.tenant_id = config.get("tenant_id")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.site_url = config.get("site_url")
        self.document_library = config.get("document_library", "Shared Documents")
        self.folder_path = config.get("folder_path", "")
        
        # Optional configuration
        self.max_file_size = config.get("max_file_size_mb", 100) * 1024 * 1024  # Convert to bytes
        self.supported_extensions = config.get("supported_extensions", [
            ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".txt", ".md"
        ])
        self.batch_size = config.get("batch_size", 50)
        
        # Incremental sync
        self.enable_incremental_sync = config.get("enable_incremental_sync", True)
        self.sync_state_file = config.get("sync_state_file", f".sharepoint_sync_{hash(self.site_url)}.json")
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="sharepoint",
            description="SharePoint Online document library data source",
            version="1.0.0",
            supported_schemes=["https", "sharepoint"],
            required_config_fields=["tenant_id", "client_id", "client_secret", "site_url"],
            optional_config_fields=[
                "document_library", "folder_path", "max_file_size_mb", 
                "supported_extensions", "batch_size", "enable_incremental_sync"
            ],
            supports_incremental_sync=True,
            supports_metadata_extraction=True,
            supports_authentication=True
        )
    
    async def validate_config(self) -> bool:
        """Validate SharePoint configuration"""
        required_fields = ["tenant_id", "client_id", "client_secret", "site_url"]
        
        for field in required_fields:
            if not self.config.get(field):
                logger.error(f"Missing required SharePoint configuration field: {field}")
                return False
        
        # Validate site URL format
        parsed_url = urlparse(self.site_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.error(f"Invalid site URL format: {self.site_url}")
            return False
        
        return True
    
    async def _initialize_client(self) -> GraphServiceClient:
        """Initialize Microsoft Graph client"""
        if self.client:
            return self.client
        
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
            request_adapter = BaseGraphRequestAdapter(auth_provider)
            
            # Create Graph client
            self.client = GraphServiceClient(request_adapter)
            
            logger.info("Successfully initialized Microsoft Graph client")
            return self.client
            
        except Exception as e:
            logger.error(f"Failed to initialize Microsoft Graph client: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to SharePoint"""
        try:
            client = await self._initialize_client()
            
            # Try to get site information
            site = await self._get_site_info(client)
            if not site:
                return False
            
            logger.info(f"Successfully connected to SharePoint site: {site.web_url}")
            return True
            
        except Exception as e:
            logger.error(f"SharePoint connection test failed: {e}")
            return False
    
    async def _get_site_info(self, client: GraphServiceClient):
        """Get SharePoint site information"""
        try:
            # Parse site URL to get hostname and path
            parsed_url = urlparse(self.site_url)
            hostname = parsed_url.netloc
            site_path = parsed_url.path.rstrip('/')
            
            if site_path:
                # Get site by hostname and path
                site = await client.sites.by_site_id(f"{hostname}:{site_path}").get()
            else:
                # Get root site
                site = await client.sites.by_site_id(hostname).get()
            
            self._site_id = site.id
            logger.info(f"Found SharePoint site: {site.display_name} (ID: {site.id})")
            return site
            
        except Exception as e:
            logger.error(f"Failed to get SharePoint site info: {e}")
            raise
    
    async def _get_document_library(self, client: GraphServiceClient):
        """Get document library drive"""
        try:
            if not self._site_id:
                await self._get_site_info(client)
            
            # Get site drives
            drives = await client.sites.by_site_id(self._site_id).drives.get()
            
            # Find the specified document library
            for drive in drives.value:
                if drive.name == self.document_library:
                    self._drive_id = drive.id
                    logger.info(f"Found document library: {drive.name} (ID: {drive.id})")
                    return drive
            
            # If not found by name, try to use the default drive
            if not self._drive_id and drives.value:
                default_drive = drives.value[0]
                self._drive_id = default_drive.id
                logger.warning(f"Document library '{self.document_library}' not found, using default: {default_drive.name}")
                return default_drive
            
            raise ValueError(f"Document library '{self.document_library}' not found")
            
        except Exception as e:
            logger.error(f"Failed to get document library: {e}")
            raise
    
    async def _get_folder_items(self, client: GraphServiceClient, folder_path: str = "", last_modified_after: Optional[datetime] = None):
        """Get items from a SharePoint folder with pagination"""
        try:
            if not self._drive_id:
                await self._get_document_library(client)
            
            # Build the request path
            if folder_path:
                # Use folder path
                items_request = client.sites.by_site_id(self._site_id).drives.by_drive_id(self._drive_id).root.item_with_path(folder_path).children
            else:
                # Use root folder
                items_request = client.sites.by_site_id(self._site_id).drives.by_drive_id(self._drive_id).root.children
            
            # Add query parameters for filtering and pagination
            request_config = items_request.get()
            
            all_items = []
            page_count = 0
            
            while True:
                page_count += 1
                logger.debug(f"Fetching page {page_count} from folder: {folder_path or 'root'}")
                
                response = await request_config
                
                if not response or not response.value:
                    break
                
                # Filter items based on last modified date if specified
                for item in response.value:
                    if item.file:  # Only process files, not folders
                        # Check if file was modified after the specified date
                        if last_modified_after and item.last_modified_date_time:
                            if item.last_modified_date_time <= last_modified_after:
                                continue
                        
                        # Check file extension
                        if self.supported_extensions:
                            file_ext = os.path.splitext(item.name)[1].lower()
                            if file_ext not in self.supported_extensions:
                                logger.debug(f"Skipping file with unsupported extension: {item.name}")
                                continue
                        
                        # Check file size
                        if item.size and item.size > self.max_file_size:
                            logger.warning(f"Skipping large file ({item.size} bytes): {item.name}")
                            continue
                        
                        all_items.append(item)
                        
                        # Yield items in batches to avoid memory issues
                        if len(all_items) >= self.batch_size:
                            for batch_item in all_items:
                                yield batch_item
                            all_items = []
                    
                    elif item.folder:  # Recursively process subfolders
                        subfolder_path = f"{folder_path}/{item.name}" if folder_path else item.name
                        async for subfolder_item in self._get_folder_items(client, subfolder_path, last_modified_after):
                            yield subfolder_item
                
                # Check for next page
                if not hasattr(response, 'odata_next_link') or not response.odata_next_link:
                    break
                
                # Prepare for next page
                request_config = request_config.with_url(response.odata_next_link)
            
            # Yield remaining items
            for item in all_items:
                yield item
                
        except Exception as e:
            logger.error(f"Failed to get folder items from {folder_path}: {e}")
            raise
    
    async def list_paths(self) -> AsyncGenerator[str, None]:
        """List file paths from SharePoint"""
        try:
            client = await self._initialize_client()
            
            # Get last sync timestamp for incremental sync
            last_modified_after = None
            if self.enable_incremental_sync:
                last_modified_after = await self.get_last_sync_timestamp()
                if last_modified_after:
                    last_modified_after = datetime.fromisoformat(last_modified_after.replace('Z', '+00:00'))
                    logger.info(f"Performing incremental sync since: {last_modified_after}")
            
            async for item in self._get_folder_items(client, self.folder_path, last_modified_after):
                if item.file:
                    # Construct the full path
                    folder_prefix = f"{self.folder_path}/" if self.folder_path else ""
                    yield f"sharepoint://{self.site_url}/{self.document_library}/{folder_prefix}{item.name}"
                    
        except Exception as e:
            logger.error(f"Failed to list SharePoint paths: {e}")
            raise
    
    async def list_files(self) -> AsyncGenerator[File, None]:
        """List files from SharePoint with content"""
        try:
            client = await self._initialize_client()
            
            # Get last sync timestamp for incremental sync
            last_modified_after = None
            if self.enable_incremental_sync:
                last_modified_after = await self.get_last_sync_timestamp()
                if last_modified_after:
                    last_modified_after = datetime.fromisoformat(last_modified_after.replace('Z', '+00:00'))
                    logger.info(f"Performing incremental sync since: {last_modified_after}")
            
            file_count = 0
            async for item in self._get_folder_items(client, self.folder_path, last_modified_after):
                if item.file:
                    try:
                        file_count += 1
                        logger.info(f"Processing SharePoint file {file_count}: {item.name}")
                        
                        # Download file content
                        temp_file = await self._download_file_content(client, item)
                        
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
                        
                        yield sharepoint_file
                        
                    except Exception as file_error:
                        logger.error(f"Failed to process SharePoint file {item.name}: {file_error}")
                        continue
            
            # Update last sync timestamp
            if self.enable_incremental_sync:
                current_time = datetime.now(timezone.utc).isoformat()
                await self.set_last_sync_timestamp(current_time)
                
        except Exception as e:
            logger.error(f"Failed to list SharePoint files: {e}")
            raise
    
    async def _download_file_content(self, client: GraphServiceClient, item) -> tempfile.NamedTemporaryFile:
        """Download file content from SharePoint"""
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
                # If it's a stream
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
    
    async def get_last_sync_timestamp(self) -> Optional[str]:
        """Get the timestamp of the last successful sync"""
        try:
            if os.path.exists(self.sync_state_file):
                with open(self.sync_state_file, 'r') as f:
                    import json
                    sync_state = json.load(f)
                    return sync_state.get('last_sync_timestamp')
        except Exception as e:
            logger.warning(f"Failed to read sync state file: {e}")
        return None
    
    async def set_last_sync_timestamp(self, timestamp: str) -> None:
        """Set the timestamp of the last successful sync"""
        try:
            import json
            sync_state = {
                'last_sync_timestamp': timestamp,
                'site_url': self.site_url,
                'document_library': self.document_library
            }
            with open(self.sync_state_file, 'w') as f:
                json.dump(sync_state, f)
            logger.debug(f"Updated sync timestamp to: {timestamp}")
        except Exception as e:
            logger.warning(f"Failed to write sync state file: {e}")
    
    async def close(self) -> None:
        """Clean up resources"""
        if self.client:
            # Close any connections if needed
            self.client = None


class SharePointPlugin(DataSourcePlugin):
    """Plugin for SharePoint Online data sources"""
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="sharepoint",
            description="SharePoint Online document library data source",
            version="1.0.0",
            supported_schemes=["https", "sharepoint"],
            required_config_fields=["tenant_id", "client_id", "client_secret", "site_url"],
            optional_config_fields=[
                "document_library", "folder_path", "max_file_size_mb", 
                "supported_extensions", "batch_size", "enable_incremental_sync"
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
        """Create a SharePoint connector"""
        return SharePointConnector(config, azure_credential)
    
    def validate_config_schema(self, config: Dict[str, Any]) -> bool:
        """Validate configuration for SharePoint connector"""
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
        
        return True


def register_sharepoint_plugin():
    """Register the SharePoint plugin"""
    from ..plugin_base import register_data_source_plugin
    
    register_data_source_plugin(SharePointPlugin(), aliases=["sharepoint_online", "spo"])
    logger.info("Registered SharePoint plugin") 