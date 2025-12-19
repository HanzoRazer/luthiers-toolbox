"""
Request Utilities - Helpers for request correlation.

Provides a defensive helper to assert that RequestIdMiddleware is installed.
"""

from __future__ import annotations

from fastapi import Request


def require_request_id(request: Request) -> str:
    """
    Require that request.state.request_id exists.

    If middleware ran -> returns the request ID
    If middleware did not run -> raises AssertionError (good for tests)

    Usage:
        req_id = require_request_id(request)
    """
    assert hasattr(request.state, "request_id"), "RequestIdMiddleware not installed"
    return request.state.request_id
