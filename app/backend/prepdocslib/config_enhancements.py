"""
Configuration enhancements for async processing features.

This module provides configuration support for the enhanced processing features:
- Enhanced file strategy configuration
- Concurrent processing settings
- Advanced SharePoint connector configuration
- Performance tuning parameters
"""

import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger("scripts")


@dataclass
class ProcessingConfig:
    """Configuration for enhanced processing features"""
    
    # File processing configuration
    enable_enhanced_processing: bool = False
    max_concurrent_files: int = 5
    max_concurrent_downloads: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_metrics: bool = True
    chunk_size: int = 8192
    
    # Performance tuning
    download_timeout: float = 300.0  # 5 minutes
    connection_pool_size: int = 20
    max_memory_mb: int = 100
    
    # SharePoint specific enhancements
    enable_sharepoint_enhancements: bool = False
    enable_change_tracking: bool = True
    change_tracking_window_days: int = 30
    enable_deleted_file_tracking: bool = True
    
    # Advanced features
    enable_streaming_processing: bool = False
    streaming_threshold_mb: int = 50


@dataclass
class SharePointEnhancedConfig:
    """Enhanced configuration for SharePoint connectors"""
    
    # Connection settings
    max_concurrent_downloads: int = 10
    download_timeout: float = 300.0
    connection_pool_size: int = 20
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Sync enhancements
    enable_change_tracking: bool = True
    change_tracking_window_days: int = 30
    enable_deleted_file_tracking: bool = True
    
    # Performance settings
    batch_size: int = 50
    max_file_size_mb: int = 100
    supported_extensions: list = field(default_factory=lambda: [
        ".pdf", ".docx", ".doc", ".pptx", ".ppt", 
        ".xlsx", ".xls", ".txt", ".md", ".html"
    ])


class ConfigurationEnhancer:
    """Utility class for enhancing configuration with async processing features"""
    
    @staticmethod
    def get_default_processing_config() -> ProcessingConfig:
        """Get default processing configuration"""
        return ProcessingConfig()
    
    @staticmethod
    def get_default_sharepoint_enhanced_config() -> SharePointEnhancedConfig:
        """Get default enhanced SharePoint configuration"""
        return SharePointEnhancedConfig()
    
    @staticmethod
    def enhance_data_source_config(
        data_source_config: Dict[str, Any], 
        processing_config: Optional[ProcessingConfig] = None
    ) -> Dict[str, Any]:
        """
        Enhance a data source configuration with async processing features
        
        Args:
            data_source_config: Original data source configuration
            processing_config: Processing configuration to apply
            
        Returns:
            Enhanced data source configuration
        """
        if processing_config is None:
            processing_config = ConfigurationEnhancer.get_default_processing_config()
        
        enhanced_config = data_source_config.copy()
        
        # Add general processing enhancements
        if processing_config.enable_enhanced_processing:
            enhanced_config.update({
                "max_concurrent_downloads": processing_config.max_concurrent_downloads,
                "download_timeout": processing_config.download_timeout,
                "connection_pool_size": processing_config.connection_pool_size,
                "retry_attempts": processing_config.retry_attempts,
                "retry_delay": processing_config.retry_delay,
            })
        
        # Add SharePoint specific enhancements
        if (data_source_config.get("type") == "sharepoint" and 
            processing_config.enable_sharepoint_enhancements):
            
            sharepoint_config = ConfigurationEnhancer.get_default_sharepoint_enhanced_config()
            enhanced_config.update({
                "enable_change_tracking": sharepoint_config.enable_change_tracking,
                "change_tracking_window_days": sharepoint_config.change_tracking_window_days,
                "enable_deleted_file_tracking": sharepoint_config.enable_deleted_file_tracking,
            })
        
        return enhanced_config
    
    @staticmethod
    def create_enhanced_sharepoint_config(
        tenant_id: str,
        client_id: str,
        client_secret: str,
        site_url: str,
        document_library: str = "Shared Documents",
        folder_path: str = "",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an enhanced SharePoint configuration with best practices
        
        Args:
            tenant_id: Azure tenant ID
            client_id: Azure app client ID
            client_secret: Azure app client secret
            site_url: SharePoint site URL
            document_library: Document library name
            folder_path: Folder path within the library
            custom_config: Additional custom configuration
            
        Returns:
            Complete enhanced SharePoint configuration
        """
        base_config = {
            "type": "enhanced_sharepoint",
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "site_url": site_url,
            "document_library": document_library,
            "folder_path": folder_path,
        }
        
        # Add enhanced defaults
        enhanced_defaults = ConfigurationEnhancer.get_default_sharepoint_enhanced_config()
        base_config.update({
            "max_concurrent_downloads": enhanced_defaults.max_concurrent_downloads,
            "download_timeout": enhanced_defaults.download_timeout,
            "connection_pool_size": enhanced_defaults.connection_pool_size,
            "retry_attempts": enhanced_defaults.retry_attempts,
            "retry_delay": enhanced_defaults.retry_delay,
            "enable_change_tracking": enhanced_defaults.enable_change_tracking,
            "change_tracking_window_days": enhanced_defaults.change_tracking_window_days,
            "enable_deleted_file_tracking": enhanced_defaults.enable_deleted_file_tracking,
            "batch_size": enhanced_defaults.batch_size,
            "max_file_size_mb": enhanced_defaults.max_file_size_mb,
            "supported_extensions": enhanced_defaults.supported_extensions,
            "enable_incremental_sync": True,
        })
        
        # Apply custom overrides
        if custom_config:
            base_config.update(custom_config)
        
        return base_config
    
    @staticmethod
    def get_performance_recommendations(
        file_count_estimate: int,
        average_file_size_mb: float,
        available_memory_gb: float
    ) -> ProcessingConfig:
        """
        Get performance recommendations based on workload characteristics
        
        Args:
            file_count_estimate: Estimated number of files to process
            average_file_size_mb: Average file size in MB
            available_memory_gb: Available memory in GB
            
        Returns:
            Recommended processing configuration
        """
        config = ConfigurationEnhancer.get_default_processing_config()
        
        # Adjust concurrent processing based on file count
        if file_count_estimate > 1000:
            config.max_concurrent_files = min(10, int(available_memory_gb / 2))
            config.max_concurrent_downloads = min(20, file_count_estimate // 50)
        elif file_count_estimate > 100:
            config.max_concurrent_files = min(8, int(available_memory_gb / 1.5))
            config.max_concurrent_downloads = min(15, file_count_estimate // 20)
        else:
            config.max_concurrent_files = min(5, int(available_memory_gb))
            config.max_concurrent_downloads = min(10, file_count_estimate // 10)
        
        # Adjust based on file size
        if average_file_size_mb > 10:
            # Large files - reduce concurrency
            config.max_concurrent_files = max(1, config.max_concurrent_files // 2)
            config.max_concurrent_downloads = max(2, config.max_concurrent_downloads // 2)
            config.enable_streaming_processing = True
            config.streaming_threshold_mb = int(average_file_size_mb * 0.8)
        elif average_file_size_mb < 1:
            # Small files - increase concurrency
            config.max_concurrent_files = min(15, config.max_concurrent_files * 2)
            config.max_concurrent_downloads = min(30, config.max_concurrent_downloads * 2)
        
        # Memory management
        estimated_memory_usage = (
            config.max_concurrent_files * average_file_size_mb * 2  # Processing buffer
        )
        
        if estimated_memory_usage > available_memory_gb * 1024 * 0.8:  # 80% memory limit
            # Reduce concurrency to fit in memory
            memory_ratio = (available_memory_gb * 1024 * 0.8) / estimated_memory_usage
            config.max_concurrent_files = max(1, int(config.max_concurrent_files * memory_ratio))
        
        logger.info(f"Performance recommendations:")
        logger.info(f"  Max concurrent files: {config.max_concurrent_files}")
        logger.info(f"  Max concurrent downloads: {config.max_concurrent_downloads}")
        logger.info(f"  Streaming enabled: {config.enable_streaming_processing}")
        logger.info(f"  Estimated memory usage: {estimated_memory_usage:.1f} MB")
        
        return config
    
    @staticmethod
    def validate_enhanced_config(config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate enhanced configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate numeric parameters
        numeric_fields = {
            "max_concurrent_files": (1, 50),
            "max_concurrent_downloads": (1, 100),
            "retry_attempts": (1, 10),
            "retry_delay": (0.1, 60.0),
            "download_timeout": (10.0, 3600.0),
            "connection_pool_size": (1, 100),
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in config:
                value = config[field]
                if not isinstance(value, (int, float)):
                    errors.append(f"{field} must be a number")
                elif value < min_val or value > max_val:
                    errors.append(f"{field} must be between {min_val} and {max_val}")
        
        # Validate boolean parameters
        boolean_fields = [
            "enable_enhanced_processing",
            "enable_metrics",
            "enable_sharepoint_enhancements",
            "enable_change_tracking",
            "enable_deleted_file_tracking",
            "enable_streaming_processing",
        ]
        
        for field in boolean_fields:
            if field in config and not isinstance(config[field], bool):
                errors.append(f"{field} must be a boolean")
        
        # Validate list parameters
        if "supported_extensions" in config:
            extensions = config["supported_extensions"]
            if not isinstance(extensions, list):
                errors.append("supported_extensions must be a list")
            elif not all(isinstance(ext, str) and ext.startswith('.') for ext in extensions):
                errors.append("supported_extensions must be a list of file extensions starting with '.'")
        
        # Resource validation
        if ("max_concurrent_files" in config and 
            "max_concurrent_downloads" in config):
            files = config["max_concurrent_files"]
            downloads = config["max_concurrent_downloads"]
            
            if downloads < files:
                errors.append("max_concurrent_downloads should be >= max_concurrent_files")
        
        return len(errors) == 0, errors


def get_enhanced_config_template() -> Dict[str, Any]:
    """Get a template for enhanced configuration"""
    return {
        "data_sources": [
            {
                "type": "enhanced_sharepoint",
                "tenant_id": "${SHAREPOINT_TENANT_ID}",
                "client_id": "${SHAREPOINT_CLIENT_ID}",
                "client_secret": "${SHAREPOINT_CLIENT_SECRET}",
                "site_url": "https://yourtenant.sharepoint.com/sites/yoursite",
                "document_library": "Shared Documents",
                "folder_path": "",
                
                # Enhanced processing settings
                "max_concurrent_downloads": 10,
                "download_timeout": 300,
                "connection_pool_size": 20,
                "retry_attempts": 3,
                "retry_delay": 1.0,
                
                # Advanced sync settings
                "enable_incremental_sync": True,
                "enable_change_tracking": True,
                "change_tracking_window_days": 30,
                "enable_deleted_file_tracking": True,
                
                # File filtering
                "max_file_size_mb": 100,
                "supported_extensions": [
                    ".pdf", ".docx", ".doc", ".pptx", ".ppt",
                    ".xlsx", ".xls", ".txt", ".md", ".html"
                ],
                "batch_size": 50
            }
        ],
        
        # Global processing configuration
        "processing": {
            "enable_enhanced_processing": True,
            "max_concurrent_files": 5,
            "enable_metrics": True,
            "chunk_size": 8192,
            "enable_streaming_processing": False,
            "streaming_threshold_mb": 50
        },
        
        # Azure configuration (unchanged)
        "azure": {
            "search_service": "your-search-service",
            "search_index": "documents-index",
            "storage_account": "yourstorageaccount",
            "storage_container": "content",
            "openai_service": "your-openai-service"
        },
        
        "use_vectors": True,
        "use_gpt_vision": False,
        "verbose": True
    } 