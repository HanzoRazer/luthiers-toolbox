"""
Request ID middleware for request tracing.

Adds X-Request-ID header to all responses and makes it available
throughout the request lifecycle for logging and error tracking.
"""
from __future__ import annotations

import uuid
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.reliability import set_request_id, get_request_id

logger = logging.getLogger(__name__)


REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Extracts X-Request-ID from request headers (or generates one)
    2. Sets it in context for the request lifetime
    3. Adds it to response headers
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get from header or generate
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = str(uuid.uuid4())[:8]

        # Set in context
        set_request_id(request_id)

        # Store on request state for access in routes
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers[REQUEST_ID_HEADER] = request_id

        return response


def get_request_id_from_request(request: Request) -> str:
    """Helper to get request ID from request object."""
    return getattr(request.state, "request_id", None) or get_request_id() or "unknown"
