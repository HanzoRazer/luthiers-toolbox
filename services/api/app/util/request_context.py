"""
Request Context - ContextVar for request ID propagation.

Allows request_id to be accessed anywhere in the call stack,
including deep helper functions and logging formatters.

This is the Python equivalent of ASP.NET Core's HttpContext.Items.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def set_request_id(request_id: Optional[str]) -> None:
    """Set the current request ID in the context."""
    _request_id.set(request_id)


def get_request_id() -> Optional[str]:
    """Get the current request ID from the context."""
    return _request_id.get()
