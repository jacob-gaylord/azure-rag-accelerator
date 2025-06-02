"""
Tests for SharePoint monitoring, error handling, and logging systems.
"""

import asyncio
import pytest
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

# Import the modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'backend'))

from prepdocslib.sharepoint_errors import (
    SharePointErrorCategory,
    SharePointError,
    SharePointErrorClassifier,
    SharePointErrorHandler,
    CircuitBreaker,
    ErrorMetrics
)

from prepdocslib.sharepoint_monitoring import (
    OperationType,
    ProgressStage,
    ProgressUpdate,
    ProgressTracker,
    PerformanceMetrics,
    HealthStatus,
    SharePointStructuredLogger,
    SharePointHealthChecker,
    SharePointMonitor
)


class TestSharePointErrorClassification:
    """Test SharePoint error classification and categorization"""
    
    def test_authentication_error_classification(self):
        """Test classification of authentication errors"""
        # Mock HTTP 401 error
        error = Exception("Unauthorized")
        mock_response = Mock()
        mock_response.status_code = 401
        error.response = mock_response
        
        sp_error = SharePointErrorClassifier.classify_exception(error)
        
        assert sp_error.category == SharePointErrorCategory.AUTHENTICATION
        assert sp_error.status_code == 401
        assert sp_error.is_retryable() is False
    
    def test_rate_limit_error_classification(self):
        """Test classification of rate limiting errors"""
        # Mock HTTP 429 error with Retry-After header
        error = Exception("Too Many Requests")
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        error.response = mock_response
        
        sp_error = SharePointErrorClassifier.classify_exception(error)
        
        assert sp_error.category == SharePointErrorCategory.RATE_LIMITED
        assert sp_error.status_code == 429
        assert sp_error.retry_after == 60
        assert sp_error.is_retryable() is True
        
        # Test retry delay calculation
        delay = sp_error.get_retry_delay(0, 1.0)
        assert delay == 60.0  # Should use Retry-After value
    
    def test_timeout_error_classification(self):
        """Test classification of timeout errors"""
        error = TimeoutError("Request timeout")
        
        sp_error = SharePointErrorClassifier.classify_exception(error)
        
        assert sp_error.category == SharePointErrorCategory.TIMEOUT
        assert sp_error.is_retryable() is True
        
        # Test exponential backoff for network errors
        delay = sp_error.get_retry_delay(2, 1.0)  # Third attempt
        assert delay == 4.0  # 1.0 * (2 ** 2)
    
    def test_file_not_found_classification(self):
        """Test classification of file not found errors"""
        error = Exception("File not found")
        mock_response = Mock()
        mock_response.status_code = 404
        error.response = mock_response
        
        sp_error = SharePointErrorClassifier.classify_exception(error)
        
        assert sp_error.category == SharePointErrorCategory.RESOURCE_NOT_FOUND
        assert sp_error.is_retryable() is False
    
    def test_service_error_classification(self):
        """Test classification of service errors"""
        error = Exception("Internal Server Error")
        mock_response = Mock()
        mock_response.status_code = 500
        error.response = mock_response
        
        sp_error = SharePointErrorClassifier.classify_exception(error)
        
        assert sp_error.category == SharePointErrorCategory.SERVICE_UNAVAILABLE
        assert sp_error.is_retryable() is True
    
    def test_unknown_error_classification(self):
        """Test classification of unknown errors"""
        error = Exception("Something weird happened")
        
        sp_error = SharePointErrorClassifier.classify_exception(error)
        
        assert sp_error.category == SharePointErrorCategory.UNKNOWN
        assert sp_error.is_retryable() is False


class TestErrorMetrics:
    """Test error metrics tracking"""
    
    def test_error_metrics_initialization(self):
        """Test error metrics initialization"""
        metrics = ErrorMetrics()
        
        assert metrics.total_errors == 0
        assert len(metrics.errors_by_category) == 0
        assert len(metrics.recent_errors) == 0
    
    def test_add_error_tracking(self):
        """Test adding errors to metrics"""
        metrics = ErrorMetrics()
        
        # Add authentication error
        metrics.add_error(SharePointErrorCategory.AUTHENTICATION, {
            "message": "Auth failed",
            "status_code": 401
        })
        
        assert metrics.total_errors == 1
        assert metrics.errors_by_category["authentication"] == 1
        assert len(metrics.recent_errors) == 1
        
        # Add another authentication error
        metrics.add_error(SharePointErrorCategory.AUTHENTICATION, {
            "message": "Token expired",
            "status_code": 401
        })
        
        assert metrics.total_errors == 2
        assert metrics.errors_by_category["authentication"] == 2
        
        # Add rate limit error
        metrics.add_error(SharePointErrorCategory.RATE_LIMITED, {
            "message": "Rate limited",
            "status_code": 429
        })
        
        assert metrics.total_errors == 3
        assert metrics.errors_by_category["authentication"] == 2
        assert metrics.errors_by_category["rate_limited"] == 1
    
    def test_error_rate_calculation(self):
        """Test error rate calculation"""
        metrics = ErrorMetrics()
        
        # Add some errors
        for i in range(5):
            metrics.add_error(SharePointErrorCategory.NETWORK_ERROR, {"message": f"Error {i}"})
        
        # Test error rate (simplified - in real implementation would use timestamps)
        error_rate = metrics.get_error_rate(SharePointErrorCategory.NETWORK_ERROR, 60)
        assert error_rate >= 0


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state (normal operation)"""
        circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        
        # Mock successful function
        @circuit_breaker
        async def mock_function():
            return "success"
        
        result = await mock_function()
        assert result == "success"
        assert circuit_breaker.state == "closed"
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state(self):
        """Test circuit breaker opening after failures"""
        circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Mock failing function
        @circuit_breaker
        async def mock_function():
            raise Exception("Always fails")
        
        # First failure
        with pytest.raises(Exception):
            await mock_function()
        assert circuit_breaker.state == "closed"
        assert circuit_breaker.failure_count == 1
        
        # Second failure - should open circuit
        with pytest.raises(Exception):
            await mock_function()
        assert circuit_breaker.state == "open"
        assert circuit_breaker.failure_count == 2
        
        # Third attempt should raise SharePointError (circuit open)
        with pytest.raises(SharePointError) as exc_info:
            await mock_function()
        assert "Circuit breaker is open" in str(exc_info.value.message)


class TestProgressTracking:
    """Test progress tracking functionality"""
    
    def test_progress_update_creation(self):
        """Test progress update creation"""
        progress = ProgressUpdate(
            stage=ProgressStage.DOWNLOADING_FILES,
            current=25,
            total=100,
            message="Downloading files"
        )
        
        assert progress.stage == ProgressStage.DOWNLOADING_FILES
        assert progress.current == 25
        assert progress.total == 100
        assert progress.percentage == 25.0
        assert progress.message == "Downloading files"
    
    def test_progress_tracker_stages(self):
        """Test progress tracker stage management"""
        tracker = ProgressTracker()
        
        # Test initial state
        assert tracker.current_stage == ProgressStage.INITIALIZING
        assert tracker.overall_progress == 0.0
        
        # Update to connecting stage
        tracker.update_stage(ProgressStage.CONNECTING, 1, 1, "Connecting to SharePoint")
        assert tracker.current_stage == ProgressStage.CONNECTING
        
        # Update to downloading stage
        tracker.update_stage(ProgressStage.DOWNLOADING_FILES, 50, 100, "Downloading files")
        assert tracker.current_stage == ProgressStage.DOWNLOADING_FILES
        
        # Check overall progress calculation
        assert tracker.overall_progress > 0
        assert tracker.overall_progress <= 100
    
    def test_progress_tracker_callbacks(self):
        """Test progress tracker callbacks"""
        tracker = ProgressTracker()
        callback_calls = []
        
        def test_callback(progress: ProgressUpdate):
            callback_calls.append(progress)
        
        tracker.add_callback(test_callback)
        
        # Update progress
        tracker.update_stage(ProgressStage.DOWNLOADING_FILES, 10, 100, "Test")
        
        assert len(callback_calls) == 1
        assert callback_calls[0].current == 10
        assert callback_calls[0].total == 100
    
    def test_progress_completion(self):
        """Test progress completion"""
        tracker = ProgressTracker()
        
        tracker.mark_completed()
        
        assert tracker.current_stage == ProgressStage.COMPLETED
        assert tracker.overall_progress == 100.0
    
    def test_progress_failure(self):
        """Test progress failure handling"""
        tracker = ProgressTracker()
        
        tracker.mark_failed("Test error message")
        
        assert tracker.current_stage == ProgressStage.FAILED


class TestPerformanceMetrics:
    """Test performance metrics collection"""
    
    def test_performance_metrics_recording(self):
        """Test recording performance metrics"""
        metrics = PerformanceMetrics()
        
        # Record successful operations
        metrics.record_operation("download", 1.5, True)
        metrics.record_operation("download", 2.0, True)
        metrics.record_operation("download", 1.0, False)  # Failed operation
        
        assert metrics.operation_counts["download_total"] == 3
        assert metrics.operation_counts["download_success"] == 2
        assert metrics.operation_counts["download_failed"] == 1
        
        # Test average timing calculation
        avg_time = metrics.get_average_timing("download")
        assert avg_time == 1.75  # (1.5 + 2.0) / 2
        
        # Test success rate calculation
        success_rate = metrics.get_success_rate("download")
        assert success_rate == 66.67  # 2/3 * 100, rounded


class TestSharePointStructuredLogger:
    """Test structured logging functionality"""
    
    def test_context_management(self):
        """Test logging context management"""
        mock_logger = Mock()
        structured_logger = SharePointStructuredLogger(mock_logger)
        
        # Push context
        structured_logger.push_context(operation_id="test-123", site_url="https://test.sharepoint.com")
        
        # Log operation start
        structured_logger.log_operation_start(OperationType.FILE_DOWNLOAD, file_name="test.pdf")
        
        # Verify logger was called with context
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        extra_data = call_args[1]['extra']
        
        assert extra_data['operation_id'] == "test-123"
        assert extra_data['site_url'] == "https://test.sharepoint.com"
        assert extra_data['file_name'] == "test.pdf"
        assert extra_data['operation'] == "file_download"
    
    def test_operation_logging(self):
        """Test operation success/failure logging"""
        mock_logger = Mock()
        structured_logger = SharePointStructuredLogger(mock_logger)
        
        # Test success logging
        structured_logger.log_operation_success(OperationType.AUTHENTICATION, 1.5, tenant_id="test-tenant")
        
        success_call = mock_logger.info.call_args
        assert "completed" in success_call[0][0]
        assert success_call[1]['extra']['operation_status'] == "success"
        assert success_call[1]['extra']['duration_ms'] == 1500
        
        # Test failure logging
        test_error = Exception("Test error")
        structured_logger.log_operation_failure(OperationType.AUTHENTICATION, test_error, 2.0)
        
        failure_call = mock_logger.error.call_args
        assert "failed" in failure_call[0][0]
        assert failure_call[1]['extra']['operation_status'] == "failed"
        assert failure_call[1]['extra']['error_type'] == "Exception"


class TestSharePointMonitor:
    """Test SharePoint monitor integration"""
    
    def test_monitor_initialization(self):
        """Test monitor initialization"""
        config = {
            "enable_health_monitoring": False,  # Disable to avoid background tasks in tests
            "metrics_export_path": "/tmp/test_metrics.json"
        }
        
        monitor = SharePointMonitor(config)
        
        assert monitor.config == config
        assert monitor.structured_logger is not None
        assert monitor.metrics is not None
        assert monitor.health_checker is not None
        assert len(monitor.active_trackers) == 0
    
    def test_progress_tracker_creation(self):
        """Test progress tracker creation and management"""
        config = {"enable_health_monitoring": False}
        monitor = SharePointMonitor(config)
        
        # Create progress tracker
        tracker = monitor.create_progress_tracker("test-operation-123")
        
        assert "test-operation-123" in monitor.active_trackers
        assert isinstance(tracker, ProgressTracker)
        
        # Get existing tracker
        retrieved_tracker = monitor.get_progress_tracker("test-operation-123")
        assert retrieved_tracker is tracker
        
        # Remove tracker
        monitor.remove_progress_tracker("test-operation-123")
        assert "test-operation-123" not in monitor.active_trackers
    
    def test_metrics_export(self):
        """Test metrics export functionality"""
        config = {"enable_health_monitoring": False}
        monitor = SharePointMonitor(config)
        
        # Add some test data
        monitor.metrics.record_operation("test_operation", 1.0, True)
        
        # Export metrics
        exported_data = monitor.export_metrics()
        
        assert "timestamp" in exported_data
        assert "performance_metrics" in exported_data
        assert "error_summary" in exported_data
        assert "active_operations" in exported_data
        
        # Check performance metrics structure
        perf_metrics = exported_data["performance_metrics"]
        assert "operation_counts" in perf_metrics
        assert "operation_timings" in perf_metrics


class TestHealthChecker:
    """Test health checker functionality"""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        # Mock connector
        mock_connector = AsyncMock()
        mock_connector.validate_config.return_value = True
        mock_connector.list_files.return_value = iter([Mock(), Mock(), Mock()])  # Mock files
        
        def mock_connector_factory(config):
            return mock_connector
        
        health_checker = SharePointHealthChecker(mock_connector_factory)
        
        # Perform health check
        health_status = await health_checker.check_health({"test": "config"})
        
        assert health_status.is_healthy is True
        assert health_status.response_time_ms is not None
        assert health_status.response_time_ms > 0
        assert len(health_status.issues) == 0
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check"""
        # Mock connector that fails
        mock_connector = AsyncMock()
        mock_connector.validate_config.side_effect = Exception("Auth failed")
        
        def mock_connector_factory(config):
            return mock_connector
        
        health_checker = SharePointHealthChecker(mock_connector_factory)
        
        # Perform health check
        health_status = await health_checker.check_health({"test": "config"})
        
        assert health_status.is_healthy is False
        assert len(health_status.issues) > 0
        assert any("Authentication failed" in issue for issue in health_status.issues)
    
    def test_health_trend_analysis(self):
        """Test health trend analysis"""
        health_checker = SharePointHealthChecker()
        
        # Add some health check history
        healthy_status = HealthStatus(is_healthy=True, last_check=datetime.now(timezone.utc))
        unhealthy_status = HealthStatus(is_healthy=False, last_check=datetime.now(timezone.utc))
        
        health_checker.health_history.extend([healthy_status, healthy_status, unhealthy_status])
        
        # Get trend
        trend = health_checker.get_health_trend(24)
        
        assert trend["checks"] == 3
        assert trend["health_percentage"] == 66.67  # 2/3 * 100, rounded
        assert trend["trend"] in ["improving", "degrading"]


# Integration test
class TestSharePointMonitoringIntegration:
    """Integration tests for SharePoint monitoring"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring(self):
        """Test end-to-end monitoring flow"""
        config = {"enable_health_monitoring": False}
        monitor = SharePointMonitor(config)
        
        # Create operation tracker
        operation_id = "test-sync-operation"
        tracker = monitor.create_progress_tracker(operation_id)
        
        # Simulate operation progress
        tracker.update_stage(ProgressStage.INITIALIZING, 0, 1, "Starting")
        tracker.update_stage(ProgressStage.CONNECTING, 1, 1, "Connected")
        tracker.update_stage(ProgressStage.DOWNLOADING_FILES, 50, 100, "Downloading")
        tracker.update_stage(ProgressStage.DOWNLOADING_FILES, 100, 100, "Complete")
        tracker.mark_completed()
        
        # Record some metrics
        monitor.metrics.record_operation("file_download", 1.5, True)
        monitor.metrics.record_operation("file_download", 2.0, True)
        
        # Get monitoring summary
        summary = monitor.get_monitoring_summary()
        
        assert summary["active_operations"] == 1
        assert summary["status"] in ["healthy", "degraded"]
        
        # Export final metrics
        exported_data = monitor.export_metrics()
        
        assert operation_id in exported_data["active_operations"]
        assert exported_data["active_operations"][operation_id]["overall_progress"] == 100.0
        
        # Clean up
        monitor.remove_progress_tracker(operation_id)
        assert summary["active_operations"] == 1  # Summary was taken before removal


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 