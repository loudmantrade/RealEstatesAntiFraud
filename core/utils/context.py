"""
Request context management for distributed tracing.

This module provides context management for request tracing using correlation IDs.
It uses contextvars to maintain thread-safe, async-safe context throughout the
request lifecycle.

Usage:
    from core.utils.context import get_trace_id, get_request_id, set_trace_context
    
    # Set context (typically in middleware)
    set_trace_context(trace_id="abc123", request_id="req456")
    
    # Get IDs anywhere in the request chain
    trace_id = get_trace_id()
    request_id = get_request_id()
"""

import uuid
from contextvars import ContextVar
from typing import Optional

# Context variables for storing trace and request IDs
# These are thread-safe and async-safe
_trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def generate_trace_id() -> str:
    """
    Generate a new trace ID.

    Returns:
        UUID4 string without hyphens (32 chars)
    """
    return uuid.uuid4().hex


def generate_request_id() -> str:
    """
    Generate a new request ID.

    Returns:
        UUID4 string without hyphens (32 chars)
    """
    return uuid.uuid4().hex


def get_trace_id() -> Optional[str]:
    """
    Get the current trace ID from context.

    Returns:
        Trace ID string or None if not set
    """
    return _trace_id.get()


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        Request ID string or None if not set
    """
    return _request_id.get()


def set_trace_id(trace_id: str) -> None:
    """
    Set the trace ID in context.

    Args:
        trace_id: Trace ID to set
    """
    _trace_id.set(trace_id)


def set_request_id(request_id: str) -> None:
    """
    Set the request ID in context.

    Args:
        request_id: Request ID to set
    """
    _request_id.set(request_id)


def set_trace_context(
    trace_id: Optional[str] = None, request_id: Optional[str] = None
) -> tuple[str, str]:
    """
    Set both trace and request IDs in context.

    If IDs are not provided, new ones will be generated.

    Args:
        trace_id: Optional trace ID to set
        request_id: Optional request ID to set

    Returns:
        Tuple of (trace_id, request_id)
    """
    if trace_id is None:
        trace_id = generate_trace_id()
    if request_id is None:
        request_id = generate_request_id()

    set_trace_id(trace_id)
    set_request_id(request_id)

    return trace_id, request_id


def clear_trace_context() -> None:
    """
    Clear trace and request IDs from context.

    This should be called at the end of request processing to avoid
    context leakage.
    """
    _trace_id.set(None)
    _request_id.set(None)


def get_trace_context() -> dict[str, Optional[str]]:
    """
    Get all trace context as a dictionary.

    Returns:
        Dictionary with trace_id and request_id keys
    """
    return {"trace_id": get_trace_id(), "request_id": get_request_id()}
