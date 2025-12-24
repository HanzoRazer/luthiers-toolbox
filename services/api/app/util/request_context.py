"""
Request Context - ContextVar for request ID propagation.

Allows request_id to be accessed anywhere in the call stack,
including deep helper functions and logging formatters.

This is the Python equivalent of ASP.NET Core's HttpContext.Items.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Optional

_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def new_request_id() -> str:
    """Generate a new request ID with 'req_' prefix."""
    return f"req_{uuid.uuid4().hex[:16]}"


def set_request_id(request_id: Optional[str]) -> None:
    """Set the current request ID in the context."""
    _request_id.set(request_id)


def get_request_id() -> Optional[str]:
    """Get the current request ID from the context."""
    return _request_id.get()


def require_request_id() -> str:
    """
    Get request_id or raise AssertionError if not set.

    Use in invariant checks where request_id must exist.
    """
    rid = _request_id.get()
    assert rid, "request_id missing (middleware/fixture not installed)"
    return rid


def clear_request_id() -> None:
    """Clear the current request ID (alias for set_request_id(None))."""
    _request_id.set(None)
