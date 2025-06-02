"""
SharePoint monitoring, logging, and progress tracking system.

This module provides comprehensive monitoring capabilities for SharePoint operations,
including structured logging, progress tracking, health checks, and metrics export.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Union
from pathlib import Path

from .sharepoint_errors import SharePointErrorCategory, sharepoint_error_handler

logger = logging.getLogger("scripts")


class OperationType(Enum):
    """Types of SharePoint operations being monitored"""
    CONNECTION_TEST = "connection_test"
    AUTHENTICATION = "authentication"
    FILE_DISCOVERY = "file_discovery"
    FILE_DOWNLOAD = "file_download"
    FILE_PROCESSING = "file_processing"
    INCREMENTAL_SYNC = "incremental_sync"
    FULL_SYNC = "full_sync"
    HEALTH_CHECK = "health_check"


class ProgressStage(Enum):
    """Stages of SharePoint operations for progress tracking"""
    INITIALIZING = "initializing"
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    DISCOVERING_FILES = "discovering_files"
    DOWNLOADING_FILES = "downloading_files"
    PROCESSING_FILES = "processing_files"
    UPDATING_INDEX = "updating_index"
    CLEANUP = "cleanup"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressUpdate:
    """Progress update for SharePoint operations"""
    stage: ProgressStage
    current: int = 0
    total: int = 0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total == 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "stage": self.stage.value,
            "current": self.current,
            "total": self.total,
            "percentage": self.percentage,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for SharePoint operations"""
    operation_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    operation_timings: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    throughput_metrics: Dict[str, float] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    
    def record_operation(self, operation: str, duration: float, success: bool = True):
        """Record an operation with timing"""
        self.operation_counts[f"{operation}_total"] += 1
        if success:
            self.operation_counts[f"{operation}_success"] += 1
            self.operation_timings[operation].append(duration)
        else:
            self.operation_counts[f"{operation}_failed"] += 1
    
    def get_average_timing(self, operation: str) -> float:
        """Get average timing for an operation"""
        timings = self.operation_timings.get(operation, [])
        return sum(timings) / len(timings) if timings else 0.0
    
    def get_success_rate(self, operation: str) -> float:
        """Get success rate for an operation"""
        total = self.operation_counts.get(f"{operation}_total", 0)
        success = self.operation_counts.get(f"{operation}_success", 0)
        return (success / total * 100) if total > 0 else 0.0
    
    def calculate_throughput(self, operation: str, time_window_minutes: int = 60) -> float:
        """Calculate operations per minute"""
        # This is a simplified calculation - in practice you'd track timestamps
        recent_ops = self.operation_counts.get(f"{operation}_total", 0)
        return recent_ops / time_window_minutes if time_window_minutes > 0 else 0.0


@dataclass
class HealthStatus:
    """Health status for SharePoint services"""
    is_healthy: bool = True
    last_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    error_rate: float = 0.0
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_healthy": self.is_healthy,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "response_time_ms": self.response_time_ms,
            "error_rate": self.error_rate,
            "issues": self.issues
        }


class SharePointStructuredLogger:
    """Structured logger for SharePoint operations with contextual information"""
    
    def __init__(self, base_logger: Optional[logging.Logger] = None):
        self.logger = base_logger or logger
        self.context_stack = []
    
    def push_context(self, **kwargs):
        """Push context for nested operations"""
        self.context_stack.append(kwargs)
    
    def pop_context(self):
        """Pop the last context"""
        if self.context_stack:
            self.context_stack.pop()
    
    def _get_current_context(self) -> Dict[str, Any]:
        """Get merged context from the stack"""
        context = {}
        for ctx in self.context_stack:
            context.update(ctx)
        return context
    
    def log_operation_start(self, operation: OperationType, **kwargs):
        """Log the start of an operation"""
        context = self._get_current_context()
        context.update(kwargs)
        context.update({
            "operation": operation.value,
            "operation_status": "started",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        self.logger.info(f"SharePoint operation started: {operation.value}", extra=context)
    
    def log_operation_success(self, operation: OperationType, duration: float, **kwargs):
        """Log successful completion of an operation"""
        context = self._get_current_context()
        context.update(kwargs)
        context.update({
            "operation": operation.value,
            "operation_status": "success",
            "duration_ms": duration * 1000,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        self.logger.info(f"SharePoint operation completed: {operation.value} ({duration:.2f}s)", extra=context)
    
    def log_operation_failure(self, operation: OperationType, error: Exception, duration: float, **kwargs):
        """Log failed operation"""
        context = self._get_current_context()
        context.update(kwargs)
        context.update({
            "operation": operation.value,
            "operation_status": "failed",
            "duration_ms": duration * 1000,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        self.logger.error(f"SharePoint operation failed: {operation.value} ({duration:.2f}s): {error}", extra=context)
    
    def log_progress_update(self, progress: ProgressUpdate, **kwargs):
        """Log progress update"""
        context = self._get_current_context()
        context.update(kwargs)
        context.update({
            "stage": progress.stage.value,
            "progress_percentage": progress.percentage,
            "current": progress.current,
            "total": progress.total,
            "timestamp": progress.timestamp.isoformat()
        })
        
        self.logger.info(f"Progress: {progress.stage.value} - {progress.percentage:.1f}% ({progress.current}/{progress.total}) - {progress.message}", extra=context)
    
    def log_rate_limit_hit(self, retry_after: Optional[int] = None, **kwargs):
        """Log rate limit encounter"""
        context = self._get_current_context()
        context.update(kwargs)
        context.update({
            "event_type": "rate_limit",
            "retry_after_seconds": retry_after,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        message = f"SharePoint rate limit hit"
        if retry_after:
            message += f", retry after {retry_after}s"
        
        self.logger.warning(message, extra=context)
    
    def log_authentication_event(self, event: str, success: bool, **kwargs):
        """Log authentication events"""
        context = self._get_current_context()
        context.update(kwargs)
        context.update({
            "event_type": "authentication",
            "auth_event": event,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, f"SharePoint authentication {event}: {'success' if success else 'failed'}", extra=context)


class ProgressTracker:
    """Advanced progress tracking for SharePoint operations"""
    
    def __init__(self, total_stages: int = 0):
        self.current_stage = ProgressStage.INITIALIZING
        self.stage_progress: Dict[ProgressStage, ProgressUpdate] = {}
        self.overall_progress = 0.0
        self.start_time = datetime.now(timezone.utc)
        self.callbacks: List[Callable[[ProgressUpdate], None]] = []
        self.history: deque = deque(maxlen=1000)  # Keep last 1000 updates
    
    def add_callback(self, callback: Callable[[ProgressUpdate], None]):
        """Add progress callback"""
        self.callbacks.append(callback)
    
    def update_stage(self, stage: ProgressStage, current: int = 0, total: int = 0, message: str = "", **details):
        """Update progress for a specific stage"""
        progress = ProgressUpdate(
            stage=stage,
            current=current,
            total=total,
            message=message,
            details=details
        )
        
        self.current_stage = stage
        self.stage_progress[stage] = progress
        self.history.append(progress)
        
        # Calculate overall progress based on stage weights
        self._calculate_overall_progress()
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def _calculate_overall_progress(self):
        """Calculate overall progress percentage"""
        # Stage weights (can be customized based on operation type)
        stage_weights = {
            ProgressStage.INITIALIZING: 5,
            ProgressStage.CONNECTING: 5,
            ProgressStage.AUTHENTICATING: 10,
            ProgressStage.DISCOVERING_FILES: 15,
            ProgressStage.DOWNLOADING_FILES: 35,
            ProgressStage.PROCESSING_FILES: 25,
            ProgressStage.UPDATING_INDEX: 5,
            ProgressStage.CLEANUP: 0,
            ProgressStage.COMPLETED: 0
        }
        
        total_weight = sum(stage_weights.values())
        weighted_progress = 0.0
        
        for stage, weight in stage_weights.items():
            if stage in self.stage_progress:
                stage_prog = self.stage_progress[stage].percentage
                weighted_progress += (stage_prog * weight) / 100
        
        self.overall_progress = min(100.0, (weighted_progress / total_weight) * 100)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current progress status"""
        elapsed = datetime.now(timezone.utc) - self.start_time
        current_update = self.stage_progress.get(self.current_stage)
        
        return {
            "overall_progress": self.overall_progress,
            "current_stage": self.current_stage.value,
            "elapsed_seconds": elapsed.total_seconds(),
            "current_stage_progress": current_update.to_dict() if current_update else None,
            "start_time": self.start_time.isoformat()
        }
    
    def mark_completed(self):
        """Mark operation as completed"""
        self.update_stage(ProgressStage.COMPLETED, 1, 1, "Operation completed successfully")
        self.overall_progress = 100.0
    
    def mark_failed(self, error_message: str):
        """Mark operation as failed"""
        self.update_stage(ProgressStage.FAILED, 0, 1, f"Operation failed: {error_message}")


class SharePointHealthChecker:
    """Health checker for SharePoint connectivity and performance"""
    
    def __init__(self, connector_factory: Callable = None):
        self.connector_factory = connector_factory
        self.health_history: deque = deque(maxlen=100)
        self.last_health_check: Optional[datetime] = None
    
    async def check_health(self, config: Dict[str, Any]) -> HealthStatus:
        """Perform comprehensive health check"""
        start_time = time.time()
        issues = []
        is_healthy = True
        
        try:
            # Basic connectivity test
            if self.connector_factory:
                connector = self.connector_factory(config)
                
                # Test authentication
                auth_start = time.time()
                try:
                    await connector.validate_config()
                    auth_time = (time.time() - auth_start) * 1000
                    
                    if auth_time > 10000:  # 10 seconds
                        issues.append(f"Slow authentication response: {auth_time:.0f}ms")
                
                except Exception as e:
                    is_healthy = False
                    issues.append(f"Authentication failed: {str(e)}")
                
                # Test file listing (sample)
                try:
                    file_count = 0
                    async for file in connector.list_files():
                        file_count += 1
                        if file_count >= 5:  # Just test first few files
                            break
                    
                    if file_count == 0:
                        issues.append("No files found - check permissions or library path")
                
                except Exception as e:
                    issues.append(f"File listing failed: {str(e)}")
                
                await connector.close()
        
        except Exception as e:
            is_healthy = False
            issues.append(f"Health check failed: {str(e)}")
        
        response_time = (time.time() - start_time) * 1000
        
        # Check error rates
        error_summary = sharepoint_error_handler.get_error_summary()
        error_rate = error_summary.get("error_rate_last_hour", 0.0)
        
        if error_rate > 10:  # More than 10 errors per hour
            issues.append(f"High error rate: {error_rate:.1f} errors/hour")
            if error_rate > 30:
                is_healthy = False
        
        health_status = HealthStatus(
            is_healthy=is_healthy,
            last_check=datetime.now(timezone.utc),
            response_time_ms=response_time,
            error_rate=error_rate,
            issues=issues
        )
        
        self.health_history.append(health_status)
        self.last_health_check = health_status.last_check
        
        return health_status
    
    def get_health_trend(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trend over specified hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        recent_checks = [
            check for check in self.health_history
            if check.last_check and check.last_check >= cutoff_time
        ]
        
        if not recent_checks:
            return {"trend": "no_data", "checks": 0}
        
        healthy_count = sum(1 for check in recent_checks if check.is_healthy)
        avg_response_time = sum(check.response_time_ms or 0 for check in recent_checks) / len(recent_checks)
        
        return {
            "trend": "improving" if healthy_count > len(recent_checks) * 0.8 else "degrading",
            "checks": len(recent_checks),
            "health_percentage": (healthy_count / len(recent_checks)) * 100,
            "avg_response_time_ms": avg_response_time,
            "last_check": recent_checks[-1].last_check.isoformat()
        }


class SharePointMonitor:
    """Main monitoring class that orchestrates all monitoring components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.structured_logger = SharePointStructuredLogger()
        self.metrics = PerformanceMetrics()
        self.health_checker = SharePointHealthChecker()
        self.active_trackers: Dict[str, ProgressTracker] = {}
        
        # Monitoring configuration
        self.enable_health_checks = config.get("enable_health_monitoring", True)
        self.health_check_interval = config.get("health_check_interval_minutes", 60)
        self.metrics_export_path = config.get("metrics_export_path", ".sharepoint_metrics.json")
        
        # Start background tasks if enabled
        if self.enable_health_checks:
            asyncio.create_task(self._periodic_health_check())
    
    def create_progress_tracker(self, operation_id: str) -> ProgressTracker:
        """Create a new progress tracker for an operation"""
        tracker = ProgressTracker()
        
        # Add logging callback
        def log_progress(progress: ProgressUpdate):
            self.structured_logger.log_progress_update(progress, operation_id=operation_id)
        
        tracker.add_callback(log_progress)
        self.active_trackers[operation_id] = tracker
        
        return tracker
    
    def get_progress_tracker(self, operation_id: str) -> Optional[ProgressTracker]:
        """Get existing progress tracker"""
        return self.active_trackers.get(operation_id)
    
    def remove_progress_tracker(self, operation_id: str):
        """Remove completed progress tracker"""
        self.active_trackers.pop(operation_id, None)
    
    async def _periodic_health_check(self):
        """Periodic health check background task"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval * 60)
                await self.health_checker.check_health(self.config)
            except Exception as e:
                logger.error(f"Periodic health check failed: {e}")
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all monitoring metrics"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "performance_metrics": {
                "operation_counts": dict(self.metrics.operation_counts),
                "operation_timings": {k: list(v) for k, v in self.metrics.operation_timings.items()},
                "throughput_metrics": self.metrics.throughput_metrics,
            },
            "error_summary": sharepoint_error_handler.get_error_summary(),
            "health_status": self.health_checker.health_history[-1].to_dict() if self.health_checker.health_history else None,
            "active_operations": {
                op_id: tracker.get_current_status() 
                for op_id, tracker in self.active_trackers.items()
            }
        }
    
    def save_metrics_to_file(self, file_path: Optional[str] = None):
        """Save metrics to file"""
        file_path = file_path or self.metrics_export_path
        
        try:
            metrics_data = self.export_metrics()
            with open(file_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            logger.info(f"Metrics exported to {file_path}")
        
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get high-level monitoring summary"""
        error_summary = sharepoint_error_handler.get_error_summary()
        health_trend = self.health_checker.get_health_trend()
        
        return {
            "status": "healthy" if health_trend.get("health_percentage", 0) > 80 else "degraded",
            "active_operations": len(self.active_trackers),
            "total_errors": error_summary.get("total_errors", 0),
            "error_rate_per_hour": error_summary.get("error_rate_last_hour", 0),
            "last_health_check": self.health_checker.last_health_check.isoformat() if self.health_checker.last_health_check else None,
            "health_trend": health_trend
        }


# Global monitor instance (initialized when needed)
_sharepoint_monitor: Optional[SharePointMonitor] = None

def get_sharepoint_monitor(config: Dict[str, Any]) -> SharePointMonitor:
    """Get or create global SharePoint monitor"""
    global _sharepoint_monitor
    if _sharepoint_monitor is None:
        _sharepoint_monitor = SharePointMonitor(config)
    return _sharepoint_monitor 