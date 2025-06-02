"""
SharePoint-specific error handling and classification.

This module provides comprehensive error handling for SharePoint operations,
including error categorization, retry strategies, and structured error reporting.
"""

import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, Type, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json

logger = logging.getLogger("scripts")


class SharePointErrorCategory(Enum):
    """Categories of SharePoint errors for different handling strategies"""
    
    # Authentication and authorization errors
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    TOKEN_EXPIRED = "token_expired"
    
    # Rate limiting and throttling
    RATE_LIMITED = "rate_limited"
    THROTTLED = "throttled"
    
    # Network and connectivity issues
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    
    # SharePoint API specific errors
    RESOURCE_NOT_FOUND = "resource_not_found"
    INVALID_SITE_URL = "invalid_site_url"
    DOCUMENT_LIBRARY_NOT_FOUND = "document_library_not_found"
    PERMISSION_DENIED = "permission_denied"
    
    # File processing errors
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    FILE_CORRUPTED = "file_corrupted"
    DOWNLOAD_FAILED = "download_failed"
    
    # API and service errors
    SERVICE_UNAVAILABLE = "service_unavailable"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    BAD_REQUEST = "bad_request"
    
    # Configuration errors
    INVALID_CONFIGURATION = "invalid_configuration"
    MISSING_PERMISSIONS = "missing_permissions"
    
    # Unknown/unclassified errors
    UNKNOWN = "unknown"


@dataclass
class ErrorMetrics:
    """Metrics for tracking errors over time"""
    
    total_errors: int = 0
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    recent_errors: List[Dict[str, Any]] = field(default_factory=list)
    max_recent_errors: int = 100
    
    def add_error(self, category: SharePointErrorCategory, error_details: Dict[str, Any]):
        """Add an error to the metrics"""
        self.total_errors += 1
        category_str = category.value
        self.errors_by_category[category_str] = self.errors_by_category.get(category_str, 0) + 1
        
        # Add to recent errors with timestamp
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category_str,
            **error_details
        }
        
        self.recent_errors.append(error_entry)
        
        # Keep only the most recent errors
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors = self.recent_errors[-self.max_recent_errors:]
    
    def get_error_rate(self, category: Optional[SharePointErrorCategory] = None, 
                      time_window_minutes: int = 60) -> float:
        """Get error rate for a category within a time window"""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (time_window_minutes * 60)
        
        relevant_errors = []
        for error in self.recent_errors:
            error_time = datetime.fromisoformat(error["timestamp"].replace('Z', '+00:00')).timestamp()
            if error_time >= cutoff_time:
                if category is None or error["category"] == category.value:
                    relevant_errors.append(error)
        
        # Return errors per minute
        return len(relevant_errors) / time_window_minutes if time_window_minutes > 0 else 0


@dataclass
class SharePointError:
    """Structured SharePoint error with categorization and context"""
    
    category: SharePointErrorCategory
    message: str
    original_exception: Optional[Exception] = None
    error_code: Optional[str] = None
    status_code: Optional[int] = None
    retry_after: Optional[int] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_retryable(self) -> bool:
        """Determine if this error should trigger a retry"""
        retryable_categories = {
            SharePointErrorCategory.RATE_LIMITED,
            SharePointErrorCategory.THROTTLED,
            SharePointErrorCategory.NETWORK_ERROR,
            SharePointErrorCategory.TIMEOUT,
            SharePointErrorCategory.CONNECTION_ERROR,
            SharePointErrorCategory.SERVICE_UNAVAILABLE,
            SharePointErrorCategory.INTERNAL_SERVER_ERROR,
        }
        return self.category in retryable_categories
    
    def get_retry_delay(self, attempt: int, base_delay: float = 1.0) -> float:
        """Calculate retry delay based on error type and attempt number"""
        if not self.is_retryable():
            return 0
        
        # Use Retry-After header if available (rate limiting)
        if self.retry_after:
            return float(self.retry_after)
        
        # Different strategies based on error category
        if self.category in [SharePointErrorCategory.RATE_LIMITED, SharePointErrorCategory.THROTTLED]:
            # Aggressive backoff for rate limiting
            return min(base_delay * (3 ** attempt), 300)  # Max 5 minutes
        
        elif self.category in [SharePointErrorCategory.NETWORK_ERROR, SharePointErrorCategory.TIMEOUT]:
            # Moderate backoff for network issues
            return min(base_delay * (2 ** attempt), 60)  # Max 1 minute
        
        else:
            # Standard exponential backoff
            return min(base_delay * (1.5 ** attempt), 30)  # Max 30 seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            "category": self.category.value,
            "message": self.message,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "retry_after": self.retry_after,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "is_retryable": self.is_retryable(),
            "original_exception_type": type(self.original_exception).__name__ if self.original_exception else None
        }


class SharePointErrorClassifier:
    """Classifies exceptions into SharePoint error categories"""
    
    @staticmethod
    def classify_exception(exception: Exception, context: Optional[Dict[str, Any]] = None) -> SharePointError:
        """Classify an exception into a SharePoint error"""
        context = context or {}
        
        # Get exception details
        error_message = str(exception)
        exception_type = type(exception).__name__
        
        # Default values
        category = SharePointErrorCategory.UNKNOWN
        error_code = None
        status_code = None
        retry_after = None
        
        # HTTP/API response errors
        if hasattr(exception, 'response') and exception.response is not None:
            status_code = getattr(exception.response, 'status_code', None)
            
            # Extract retry-after header
            if hasattr(exception.response, 'headers'):
                retry_after = exception.response.headers.get('Retry-After')
                if retry_after:
                    try:
                        retry_after = int(retry_after)
                    except ValueError:
                        retry_after = None
            
            # Classify by status code
            if status_code == 401:
                category = SharePointErrorCategory.AUTHENTICATION
            elif status_code == 403:
                if "rate limit" in error_message.lower() or "throttl" in error_message.lower():
                    category = SharePointErrorCategory.RATE_LIMITED
                else:
                    category = SharePointErrorCategory.AUTHORIZATION
            elif status_code == 404:
                category = SharePointErrorCategory.RESOURCE_NOT_FOUND
            elif status_code == 429:
                category = SharePointErrorCategory.RATE_LIMITED
            elif status_code >= 500:
                category = SharePointErrorCategory.SERVICE_UNAVAILABLE
            elif status_code >= 400:
                category = SharePointErrorCategory.BAD_REQUEST
        
        # Classification by exception type
        elif "timeout" in exception_type.lower() or "timeout" in error_message.lower():
            category = SharePointErrorCategory.TIMEOUT
        
        elif "connection" in exception_type.lower() or "network" in exception_type.lower():
            category = SharePointErrorCategory.CONNECTION_ERROR
        
        elif "authentication" in error_message.lower() or "token" in error_message.lower():
            if "expired" in error_message.lower():
                category = SharePointErrorCategory.TOKEN_EXPIRED
            else:
                category = SharePointErrorCategory.AUTHENTICATION
        
        # Message-based classification
        elif any(keyword in error_message.lower() for keyword in ["rate limit", "throttl", "too many requests"]):
            category = SharePointErrorCategory.RATE_LIMITED
        
        elif "file too large" in error_message.lower() or "size limit" in error_message.lower():
            category = SharePointErrorCategory.FILE_TOO_LARGE
        
        elif "unsupported" in error_message.lower() and "file" in error_message.lower():
            category = SharePointErrorCategory.UNSUPPORTED_FILE_TYPE
        
        elif "invalid site" in error_message.lower() or "site not found" in error_message.lower():
            category = SharePointErrorCategory.INVALID_SITE_URL
        
        elif "document library" in error_message.lower() and "not found" in error_message.lower():
            category = SharePointErrorCategory.DOCUMENT_LIBRARY_NOT_FOUND
        
        # Extract error code if available
        if hasattr(exception, 'error_code'):
            error_code = exception.error_code
        elif hasattr(exception, 'code'):
            error_code = exception.code
        
        return SharePointError(
            category=category,
            message=error_message,
            original_exception=exception,
            error_code=error_code,
            status_code=status_code,
            retry_after=retry_after,
            context=context
        )


class CircuitBreaker:
    """Circuit breaker pattern implementation for SharePoint operations"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def __call__(self, func):
        """Decorator to apply circuit breaker to a function"""
        async def wrapper(*args, **kwargs):
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half_open"
                else:
                    raise SharePointError(
                        category=SharePointErrorCategory.SERVICE_UNAVAILABLE,
                        message=f"Circuit breaker is open. Service unavailable for {self.recovery_timeout}s",
                        context={"circuit_breaker_state": self.state}
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful operation"""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        """Handle failure in circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class SharePointErrorHandler:
    """Central error handler for SharePoint operations"""
    
    def __init__(self):
        self.metrics = ErrorMetrics()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def handle_error(self, 
                    exception: Exception, 
                    operation: str = "unknown",
                    context: Optional[Dict[str, Any]] = None) -> SharePointError:
        """Handle and classify a SharePoint error"""
        
        # Classify the error
        sp_error = SharePointErrorClassifier.classify_exception(exception, context)
        
        # Add operation context
        sp_error.context["operation"] = operation
        
        # Update metrics
        self.metrics.add_error(sp_error.category, sp_error.to_dict())
        
        # Log the error with structured data
        self._log_error(sp_error, operation)
        
        return sp_error
    
    def _log_error(self, error: SharePointError, operation: str):
        """Log error with appropriate level and structured data"""
        
        log_data = {
            "operation": operation,
            "error_category": error.category.value,
            "error_code": error.error_code,
            "status_code": error.status_code,
            "is_retryable": error.is_retryable(),
            "context": error.context
        }
        
        # Choose log level based on error category
        if error.category in [SharePointErrorCategory.RATE_LIMITED, SharePointErrorCategory.THROTTLED]:
            logger.warning(f"SharePoint rate limited: {error.message}", extra=log_data)
        
        elif error.category in [SharePointErrorCategory.AUTHENTICATION, SharePointErrorCategory.AUTHORIZATION]:
            logger.error(f"SharePoint authentication/authorization error: {error.message}", extra=log_data)
        
        elif error.category in [SharePointErrorCategory.NETWORK_ERROR, SharePointErrorCategory.TIMEOUT]:
            logger.warning(f"SharePoint network error: {error.message}", extra=log_data)
        
        elif error.category == SharePointErrorCategory.RESOURCE_NOT_FOUND:
            logger.info(f"SharePoint resource not found: {error.message}", extra=log_data)
        
        elif error.is_retryable():
            logger.warning(f"SharePoint retryable error: {error.message}", extra=log_data)
        
        else:
            logger.error(f"SharePoint error: {error.message}", extra=log_data)
    
    def get_circuit_breaker(self, endpoint: str) -> CircuitBreaker:
        """Get or create circuit breaker for an endpoint"""
        if endpoint not in self.circuit_breakers:
            self.circuit_breakers[endpoint] = CircuitBreaker()
        return self.circuit_breakers[endpoint]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary for monitoring"""
        return {
            "total_errors": self.metrics.total_errors,
            "errors_by_category": self.metrics.errors_by_category,
            "error_rate_last_hour": self.metrics.get_error_rate(time_window_minutes=60),
            "recent_error_count": len(self.metrics.recent_errors),
            "circuit_breaker_states": {
                endpoint: breaker.state 
                for endpoint, breaker in self.circuit_breakers.items()
            }
        }


# Global error handler instance
sharepoint_error_handler = SharePointErrorHandler() 