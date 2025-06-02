"""
Enhanced observability module for Azure RAG Accelerator.

This module provides comprehensive telemetry tracking for:
- Chat interactions and user behavior
- Feedback submission and quality metrics
- Performance monitoring and diagnostics
- Custom business metrics and KPIs
"""

import os
import time
from typing import Any, Dict, Optional
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
from opentelemetry.metrics import CallbackOptions, Observation

# Initialize OpenTelemetry tracer and meter
tracer = trace.get_tracer("azure-rag-accelerator")
meter = metrics.get_meter("azure-rag-accelerator")

# Create metrics instruments
chat_requests_counter = meter.create_counter(
    name="chat_requests_total",
    description="Total number of chat requests",
    unit="1"
)

ask_requests_counter = meter.create_counter(
    name="ask_requests_total", 
    description="Total number of ask requests",
    unit="1"
)

feedback_submissions_counter = meter.create_counter(
    name="feedback_submissions_total",
    description="Total number of feedback submissions",
    unit="1"
)

response_time_histogram = meter.create_histogram(
    name="response_time_seconds",
    description="Response time in seconds",
    unit="s"
)

feedback_rating_histogram = meter.create_histogram(
    name="feedback_rating",
    description="User feedback ratings (1-5 scale)",
    unit="1"
)

search_results_histogram = meter.create_histogram(
    name="search_results_count",
    description="Number of search results returned",
    unit="1"
)

token_usage_counter = meter.create_counter(
    name="token_usage_total",
    description="Total tokens used by OpenAI models",
    unit="1"
)

citation_clicks_counter = meter.create_counter(
    name="citation_clicks_total",
    description="Total number of citation clicks",
    unit="1"
)

# Create gauges for real-time metrics
active_sessions_gauge = meter.create_up_down_counter(
    name="active_sessions",
    description="Number of active chat sessions",
    unit="1"
)


class RAGTelemetry:
    """Enhanced telemetry tracking for RAG system."""
    
    @staticmethod
    def track_chat_request(user_id: str, session_id: str, message_count: int, 
                          approach: str = "chat", use_gpt4v: bool = False):
        """Track chat/ask request with context."""
        attributes = {
            "user_id": user_id,
            "session_id": session_id,
            "message_count": message_count,
            "approach": approach,
            "use_gpt4v": use_gpt4v,
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }
        
        if approach == "chat":
            chat_requests_counter.add(1, attributes)
        else:
            ask_requests_counter.add(1, attributes)
    
    @staticmethod
    def track_response_time(duration_seconds: float, approach: str, success: bool,
                          user_id: Optional[str] = None):
        """Track response time metrics."""
        attributes = {
            "approach": approach,
            "success": success,
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }
        if user_id:
            attributes["user_id"] = user_id
            
        response_time_histogram.record(duration_seconds, attributes)
    
    @staticmethod
    def track_search_results(count: int, approach: str, user_id: Optional[str] = None):
        """Track number of search results returned."""
        attributes = {
            "approach": approach,
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }
        if user_id:
            attributes["user_id"] = user_id
            
        search_results_histogram.record(count, attributes)
    
    @staticmethod
    def track_token_usage(prompt_tokens: int, completion_tokens: int, 
                         model: str, user_id: Optional[str] = None):
        """Track OpenAI token usage."""
        attributes = {
            "model": model,
            "token_type": "prompt",
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }
        if user_id:
            attributes["user_id"] = user_id
            
        token_usage_counter.add(prompt_tokens, attributes)
        
        attributes["token_type"] = "completion"
        token_usage_counter.add(completion_tokens, attributes)
    
    @staticmethod
    def track_feedback_submission(rating: int, has_comment: bool, user_id: str,
                                session_id: str, message_id: str):
        """Track feedback submission with quality metrics."""
        attributes = {
            "rating": rating,
            "has_comment": has_comment,
            "user_id": user_id,
            "session_id": session_id,
            "rating_category": "positive" if rating >= 4 else "negative" if rating <= 2 else "neutral",
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }
        
        feedback_submissions_counter.add(1, attributes)
        feedback_rating_histogram.record(rating, attributes)
    
    @staticmethod
    def track_citation_click(source: str, user_id: str, session_id: str,
                           citation_type: str = "standard"):
        """Track citation clicks for content engagement."""
        attributes = {
            "source": source,
            "user_id": user_id,
            "session_id": session_id,
            "citation_type": citation_type,
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }
        
        citation_clicks_counter.add(1, attributes)
    
    @staticmethod
    def track_session_activity(session_id: str, user_id: str, action: str):
        """Track session lifecycle events."""
        attributes = {
            "session_id": session_id,
            "user_id": user_id,
            "action": action,  # "start", "end", "extend"
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }
        
        if action == "start":
            active_sessions_gauge.add(1, attributes)
        elif action == "end":
            active_sessions_gauge.add(-1, attributes)
    
    @staticmethod
    def create_custom_span(name: str, operation: str = "rag_operation"):
        """Create a custom span for detailed tracing."""
        return tracer.start_span(
            name=name,
            attributes={
                "operation": operation,
                "environment": os.getenv("ENVIRONMENT", "unknown")
            }
        )
    
    @staticmethod
    def track_error(error: Exception, context: Dict[str, Any], user_id: Optional[str] = None):
        """Track errors with context for debugging."""
        with tracer.start_span("error_tracking") as span:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.set_attributes({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": str(context),
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                **({"user_id": user_id} if user_id else {})
            })


class PerformanceTracker:
    """Context manager for tracking operation performance."""
    
    def __init__(self, operation_name: str, approach: str, user_id: Optional[str] = None):
        self.operation_name = operation_name
        self.approach = approach
        self.user_id = user_id
        self.start_time = None
        self.span = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.span = RAGTelemetry.create_custom_span(self.operation_name, self.approach)
        self.span.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            success = exc_type is None
            
            RAGTelemetry.track_response_time(
                duration, self.approach, success, self.user_id
            )
            
            if self.span:
                if not success and exc_val:
                    self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                    self.span.set_attribute("error_type", type(exc_val).__name__)
                
                self.span.set_attribute("duration_seconds", duration)
                self.span.set_attribute("success", success)
                self.span.__exit__(exc_type, exc_val, exc_tb)


# Custom event tracking functions for specific RAG operations
def track_document_retrieval(query: str, num_results: int, retrieval_score: float,
                           user_id: Optional[str] = None):
    """Track document retrieval performance."""
    with tracer.start_span("document_retrieval") as span:
        span.set_attributes({
            "query_length": len(query),
            "num_results": num_results,
            "retrieval_score": retrieval_score,
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            **({"user_id": user_id} if user_id else {})
        })


def track_llm_generation(model: str, prompt_length: int, response_length: int,
                        generation_time: float, user_id: Optional[str] = None):
    """Track LLM generation metrics."""
    with tracer.start_span("llm_generation") as span:
        span.set_attributes({
            "model": model,
            "prompt_length": prompt_length,
            "response_length": response_length,
            "generation_time": generation_time,
            "tokens_per_second": response_length / generation_time if generation_time > 0 else 0,
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            **({"user_id": user_id} if user_id else {})
        })


def track_user_satisfaction_metrics():
    """Generate user satisfaction metrics from feedback data."""
    # This would typically query the feedback database and create metrics
    # Implementation depends on your data access patterns
    pass


# Application Insights custom events for business intelligence
def log_custom_event(event_name: str, properties: Dict[str, Any], measurements: Dict[str, float] = None):
    """Log custom events to Application Insights."""
    with tracer.start_span(f"custom_event_{event_name}") as span:
        for key, value in properties.items():
            span.set_attribute(f"event.{key}", str(value))
        
        if measurements:
            for key, value in measurements.items():
                span.set_attribute(f"metric.{key}", value)


# Initialize observability when module is imported
def initialize_observability():
    """Initialize observability components."""
    if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        print("Enhanced observability initialized for Azure RAG Accelerator")


# Call initialization
initialize_observability() 