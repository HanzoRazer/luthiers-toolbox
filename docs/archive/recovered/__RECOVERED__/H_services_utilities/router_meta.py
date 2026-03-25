from __future__ import annotations

from typing import Callable, Optional
from .endpoint_registry import EndpointStatus


def endpoint_meta(
    *,
    status: EndpointStatus,
    replacement: Optional[str] = None,
    notes: Optional[str] = None,
) -> Callable:
    """
    Annotate a FastAPI endpoint with governance metadata.

    Example:
        @router.get("/old-path")
        @endpoint_meta(status=EndpointStatus.LEGACY, replacement="/api/new-path")
        def old(): ...
    """
    def decorator(func: Callable) -> Callable:
        setattr(func, "__endpoint_status__", str(status.value))
        setattr(func, "__endpoint_replacement__", replacement)
        setattr(func, "__endpoint_notes__", notes)
        return func
    return decorator
