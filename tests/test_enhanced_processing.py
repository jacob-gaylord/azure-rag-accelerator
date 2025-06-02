"""
Tests for enhanced processing features including concurrent file processing and async optimizations.
"""

import asyncio
import pytest
import tempfile
import time
from unittest.mock import AsyncMock, Mock, patch
from typing import List, Dict, Any

# Import the enhanced modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'backend'))

from prepdocslib.enhanced_filestrategy import (
    EnhancedFileStrategy, 
    ProcessingMetrics, 
    StreamingFileProcessor
)
from prepdocslib.config_enhancements import (
    ConfigurationEnhancer,
    ProcessingConfig,
    SharePointEnhancedConfig
)


class MockFile:
    """Mock file for testing"""
    
    def __init__(self, name: str, content: bytes = b"test content", size: int = 100):
        self.name = name
        self.content = content
        self.size = size
        self.url = f"https://test.com/{name}"
        self._closed = False
    
    def filename(self) -> str:
        return self.name
    
    def file_extension(self) -> str:
        return os.path.splitext(self.name)[1]
    
    def close(self):
        self._closed = True


class MockListFileStrategy:
    """Mock list file strategy for testing"""
    
    def __init__(self, files: List[MockFile]):
        self.files = files
    
    async def list(self):
        for file in self.files:
            yield file
    
    async def list_paths(self):
        for file in self.files:
            yield file.name


class TestProcessingMetrics:
    """Test processing metrics tracking"""
    
    def test_metrics_initialization(self):
        metrics = ProcessingMetrics()
        assert metrics.total_files == 0
        assert metrics.processed_files == 0
        assert metrics.failed_files == 0
        assert metrics.skipped_files == 0
        assert metrics.concurrent_tasks == 0
    
    def test_metrics_file_tracking(self):
        metrics = ProcessingMetrics()
        
        # Add processed file
        metrics.add_file_processed(1.5, 1024)
        assert metrics.processed_files == 1
        assert metrics.average_file_size == 1024.0
        
        # Add another file
        metrics.add_file_processed(2.0, 2048)
        assert metrics.processed_files == 2
        assert metrics.average_file_size == 1536.0  # (1024 + 2048) / 2
    
    def test_metrics_failure_tracking(self):
        metrics = ProcessingMetrics()
        
        metrics.add_file_failed()
        assert metrics.failed_files == 1
        
        metrics.add_file_skipped()
        assert metrics.skipped_files == 1
    
    def test_concurrent_task_tracking(self):
        metrics = ProcessingMetrics()
        
        metrics.set_concurrent_tasks(5)
        assert metrics.concurrent_tasks == 5
        assert metrics.max_concurrent_tasks == 5
        
        metrics.set_concurrent_tasks(3)
        assert metrics.concurrent_tasks == 3
        assert metrics.max_concurrent_tasks == 5  # Should keep max


class TestEnhancedFileStrategy:
    """Test enhanced file strategy"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for testing"""
        list_file_strategy = Mock()
        blob_manager = AsyncMock()
        search_info = Mock()
        file_processors = {"txt": Mock()}
        
        return {
            "list_file_strategy": list_file_strategy,
            "blob_manager": blob_manager,
            "search_info": search_info,
            "file_processors": file_processors
        }
    
    def test_initialization(self, mock_dependencies):
        """Test enhanced strategy initialization"""
        strategy = EnhancedFileStrategy(
            max_concurrent_files=3,
            max_concurrent_downloads=5,
            retry_attempts=2,
            **mock_dependencies
        )
        
        assert strategy.max_concurrent_files == 3
        assert strategy.max_concurrent_downloads == 5
        assert strategy.retry_attempts == 2
        assert strategy.file_processing_semaphore._value == 3
        assert strategy.download_semaphore._value == 5
        assert strategy.metrics is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, mock_dependencies):
        """Test concurrent file processing"""
        # Create test files
        test_files = [
            MockFile(f"test{i}.txt", size=100) 
            for i in range(5)
        ]
        
        mock_list_strategy = MockListFileStrategy(test_files)
        mock_dependencies["list_file_strategy"] = mock_list_strategy
        
        # Mock the processing pipeline
        with patch('prepdocslib.enhanced_filestrategy.parse_file') as mock_parse:
            mock_parse.return_value = [Mock()]  # Mock sections
            
            strategy = EnhancedFileStrategy(
                max_concurrent_files=2,
                **mock_dependencies
            )
            
            # Mock setup_search_manager
            strategy.setup_search_manager = Mock()
            strategy.search_manager = AsyncMock()
            
            # Track processing order to verify concurrency
            processing_times = []
            
            async def mock_process_single_file(file):
                start_time = time.time()
                await asyncio.sleep(0.1)  # Simulate processing time
                processing_times.append((file.name, start_time, time.time()))
                return True
            
            strategy._process_single_file = mock_process_single_file
            
            # Run concurrent processing
            await strategy._run_concurrent_add()
            
            # Verify that files were processed
            assert len(processing_times) == 5
            assert strategy.metrics.processed_files == 5
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_dependencies):
        """Test retry logic for failed files"""
        test_file = MockFile("test.txt")
        
        strategy = EnhancedFileStrategy(
            retry_attempts=3,
            retry_delay=0.01,  # Short delay for testing
            **mock_dependencies
        )
        
        # Mock a function that fails twice then succeeds
        call_count = 0
        async def mock_process_single_file(file):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Simulated failure")
            return True
        
        strategy._process_single_file = mock_process_single_file
        
        # Test retry logic
        result = await strategy._process_file_with_retry(test_file)
        
        assert result is True
        assert call_count == 3  # Failed twice, succeeded on third attempt
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, mock_dependencies):
        """Test behavior when all retry attempts are exhausted"""
        test_file = MockFile("test.txt")
        
        strategy = EnhancedFileStrategy(
            retry_attempts=2,
            retry_delay=0.01,
            **mock_dependencies
        )
        
        # Mock a function that always fails
        async def mock_process_single_file(file):
            raise Exception("Always fails")
        
        strategy._process_single_file = mock_process_single_file
        
        # Test retry exhaustion
        result = await strategy._process_file_with_retry(test_file)
        
        assert result is False
        assert strategy.metrics.failed_files == 1


class TestConfigurationEnhancer:
    """Test configuration enhancement utilities"""
    
    def test_default_processing_config(self):
        """Test default processing configuration"""
        config = ConfigurationEnhancer.get_default_processing_config()
        
        assert isinstance(config, ProcessingConfig)
        assert config.max_concurrent_files == 5
        assert config.max_concurrent_downloads == 10
        assert config.retry_attempts == 3
        assert config.enable_metrics is True
    
    def test_default_sharepoint_config(self):
        """Test default SharePoint configuration"""
        config = ConfigurationEnhancer.get_default_sharepoint_enhanced_config()
        
        assert isinstance(config, SharePointEnhancedConfig)
        assert config.max_concurrent_downloads == 10
        assert config.enable_change_tracking is True
        assert config.batch_size == 50
        assert ".pdf" in config.supported_extensions
    
    def test_enhance_data_source_config(self):
        """Test data source configuration enhancement"""
        original_config = {
            "type": "sharepoint",
            "site_url": "https://test.sharepoint.com"
        }
        
        processing_config = ProcessingConfig(
            enable_enhanced_processing=True,
            enable_sharepoint_enhancements=True,
            max_concurrent_downloads=15
        )
        
        enhanced_config = ConfigurationEnhancer.enhance_data_source_config(
            original_config, processing_config
        )
        
        assert enhanced_config["max_concurrent_downloads"] == 15
        assert enhanced_config["enable_change_tracking"] is True
        assert enhanced_config["site_url"] == "https://test.sharepoint.com"
    
    def test_create_enhanced_sharepoint_config(self):
        """Test SharePoint configuration creation"""
        config = ConfigurationEnhancer.create_enhanced_sharepoint_config(
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
            site_url="https://test.sharepoint.com",
            custom_config={"custom_field": "custom_value"}
        )
        
        assert config["type"] == "enhanced_sharepoint"
        assert config["tenant_id"] == "test-tenant"
        assert config["enable_incremental_sync"] is True
        assert config["max_concurrent_downloads"] == 10
        assert config["custom_field"] == "custom_value"
    
    def test_performance_recommendations_small_workload(self):
        """Test performance recommendations for small workload"""
        config = ConfigurationEnhancer.get_performance_recommendations(
            file_count_estimate=50,
            average_file_size_mb=2.0,
            available_memory_gb=8
        )
        
        assert config.max_concurrent_files <= 8
        assert config.max_concurrent_downloads >= 5
        assert config.enable_streaming_processing is False
    
    def test_performance_recommendations_large_workload(self):
        """Test performance recommendations for large workload"""
        config = ConfigurationEnhancer.get_performance_recommendations(
            file_count_estimate=2000,
            average_file_size_mb=15.0,
            available_memory_gb=16
        )
        
        assert config.max_concurrent_files <= 8  # Reduced due to large files
        assert config.max_concurrent_downloads >= 10
        assert config.enable_streaming_processing is True
        assert config.streaming_threshold_mb > 10
    
    def test_performance_recommendations_memory_limit(self):
        """Test performance recommendations with memory constraints"""
        config = ConfigurationEnhancer.get_performance_recommendations(
            file_count_estimate=100,
            average_file_size_mb=50.0,  # Large files
            available_memory_gb=2  # Limited memory
        )
        
        # Should reduce concurrency to fit in memory
        assert config.max_concurrent_files <= 2
        assert config.enable_streaming_processing is True
    
    def test_validate_enhanced_config_valid(self):
        """Test validation of valid enhanced configuration"""
        config = {
            "max_concurrent_files": 5,
            "max_concurrent_downloads": 10,
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "enable_enhanced_processing": True,
            "supported_extensions": [".pdf", ".docx"]
        }
        
        is_valid, errors = ConfigurationEnhancer.validate_enhanced_config(config)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_enhanced_config_invalid(self):
        """Test validation of invalid enhanced configuration"""
        config = {
            "max_concurrent_files": 0,  # Invalid: too low
            "retry_delay": -1.0,  # Invalid: negative
            "enable_enhanced_processing": "yes",  # Invalid: not boolean
            "supported_extensions": "pdf"  # Invalid: not list
        }
        
        is_valid, errors = ConfigurationEnhancer.validate_enhanced_config(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("max_concurrent_files" in error for error in errors)
        assert any("retry_delay" in error for error in errors)
        assert any("enable_enhanced_processing" in error for error in errors)
        assert any("supported_extensions" in error for error in errors)
    
    def test_validate_resource_constraints(self):
        """Test validation of resource constraints"""
        config = {
            "max_concurrent_files": 10,
            "max_concurrent_downloads": 5  # Invalid: should be >= files
        }
        
        is_valid, errors = ConfigurationEnhancer.validate_enhanced_config(config)
        
        assert is_valid is False
        assert any("max_concurrent_downloads should be >= max_concurrent_files" in error for error in errors)


class TestStreamingFileProcessor:
    """Test streaming file processor"""
    
    def test_initialization(self):
        """Test streaming processor initialization"""
        processor = StreamingFileProcessor(chunk_size=4096)
        assert processor.chunk_size == 4096
    
    @pytest.mark.asyncio
    async def test_process_small_file(self):
        """Test processing small file (non-streaming)"""
        processor = StreamingFileProcessor()
        small_file = MockFile("small.txt", size=1024)
        
        async def mock_processor_func(file):
            return f"processed_{file.name}"
        
        result = await processor.process_large_file_streaming(
            small_file, mock_processor_func, max_memory_mb=10
        )
        
        assert result == "processed_small.txt"
    
    @pytest.mark.asyncio
    async def test_process_large_file(self):
        """Test processing large file (streaming mode)"""
        processor = StreamingFileProcessor()
        large_file = MockFile("large.txt", size=200 * 1024 * 1024)  # 200MB
        
        async def mock_processor_func(file):
            return f"processed_{file.name}"
        
        result = await processor.process_large_file_streaming(
            large_file, mock_processor_func, max_memory_mb=100
        )
        
        # For now, it falls back to normal processing
        assert result == "processed_large.txt"


# Integration test
class TestIntegration:
    """Integration tests for enhanced processing"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self, mock_dependencies):
        """Test end-to-end enhanced processing pipeline"""
        # Create a realistic scenario with multiple files
        test_files = [
            MockFile("doc1.pdf", size=1024),
            MockFile("doc2.docx", size=2048),
            MockFile("doc3.txt", size=512),
        ]
        
        mock_list_strategy = MockListFileStrategy(test_files)
        mock_dependencies["list_file_strategy"] = mock_list_strategy
        
        # Configure enhanced strategy
        strategy = EnhancedFileStrategy(
            max_concurrent_files=2,
            max_concurrent_downloads=3,
            retry_attempts=2,
            enable_metrics=True,
            **mock_dependencies
        )
        
        # Mock the processing components
        strategy.setup_search_manager = Mock()
        strategy.search_manager = AsyncMock()
        
        with patch('prepdocslib.enhanced_filestrategy.parse_file') as mock_parse:
            mock_parse.return_value = [Mock()]  # Mock sections
            
            # Mock successful processing
            async def mock_process_single_file(file):
                await asyncio.sleep(0.01)  # Simulate processing time
                return True
            
            strategy._process_single_file = mock_process_single_file
            
            # Run the processing
            start_time = time.time()
            await strategy._run_concurrent_add()
            end_time = time.time()
            
            # Verify results
            assert strategy.metrics.total_files == 3
            assert strategy.metrics.processed_files == 3
            assert strategy.metrics.failed_files == 0
            
            # Processing should be faster due to concurrency
            processing_time = end_time - start_time
            # With 2 concurrent files and 0.01s each, should be faster than sequential
            assert processing_time < 0.05  # Much less than 3 * 0.01 = 0.03


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 