"""
Request ID Propagation

Provides ContextVar-based request ID tracking for correlation
across AI operations and logging.
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Optional, Callable

# Context variable for request ID propagation
_request_id_var: ContextVar[Optional[str]] = ContextVar("ai_request_id", default=None)


def generate_request_id() -> str:
    """Generate a new unique request ID."""
    return f"ai-{uuid.uuid4().hex[:12]}"


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        Current request ID or None if not set
    """
    return _request_id_var.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set the request ID in context.

    Args:
        request_id: Request ID to set (generates one if None)

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = generate_request_id()
    _request_id_var.set(request_id)
    return request_id


def clear_request_id() -> None:
    """Clear the request ID from context."""
    _request_id_var.set(None)


class RequestIdMiddleware:
    """
    ASGI middleware for request ID propagation.

    Automatically sets a request ID for each incoming request
    and adds it to response headers.

    Usage with FastAPI:
        app = FastAPI()
        app.add_middleware(RequestIdMiddleware)
    """

    def __init__(
        self,
        app,
        header_name: str = "X-Request-ID",
        generate_if_missing: bool = True,
    ):
        self.app = app
        self.header_name = header_name.lower()
        self.generate_if_missing = generate_if_missing

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract request ID from headers or generate new one
        headers = dict(scope.get("headers", []))
        request_id = headers.get(self.header_name.encode())

        if request_id:
            request_id = request_id.decode()
        elif self.generate_if_missing:
            request_id = generate_request_id()

        # Set in context
        token = _request_id_var.set(request_id)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add request ID to response headers
                headers = list(message.get("headers", []))
                headers.append((self.header_name.encode(), request_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            _request_id_var.reset(token)


def with_request_id(func: Callable) -> Callable:
    """
    Decorator to ensure a request ID exists for the duration of a function.

    Usage:
        @with_request_id
        async def my_ai_operation():
            request_id = get_request_id()
            # request_id is guaranteed to exist
    """
    import functools
    import asyncio

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        if get_request_id() is None:
            set_request_id()
        return func(*args, **kwargs)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        if get_request_id() is None:
            set_request_id()
        return await func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
