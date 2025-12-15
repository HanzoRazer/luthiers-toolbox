# services/api/app/cam/async_timeout.py
"""
Async timeout wrapper for CPU-bound geometry operations.

Runs blocking functions in a thread pool with timeout protection.
Prevents hung requests when processing malformed or overly complex DXF files.

Usage:
    from app.cam.async_timeout import run_with_timeout, GeometryTimeout
    
    try:
        result = await run_with_timeout(
            reconstruct_contours_from_dxf,
            dxf_bytes=dxf_bytes,
            layer_name="GEOMETRY",
            timeout=30.0,
        )
    except GeometryTimeout:
        raise HTTPException(504, "Operation timed out")
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import TypeVar, Callable, Any

from app.cam.dxf_limits import OPERATION_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


T = TypeVar('T')


# Shared thread pool for geometry operations
# Limited to 4 workers to prevent resource exhaustion
_geometry_executor = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="geometry_"
)


class GeometryTimeout(Exception):
    """Raised when a geometry operation exceeds its timeout."""
    
    def __init__(self, message: str, timeout: float):
        self.timeout = timeout
        super().__init__(message)


class GeometryOverload(Exception):
    """Raised when geometry exceeds processing limits."""
    
    def __init__(self, message: str, limit_name: str, limit_value: int, actual_value: int):
        self.limit_name = limit_name
        self.limit_value = limit_value
        self.actual_value = actual_value
        super().__init__(message)


async def run_with_timeout(
    func: Callable[..., T],
    *args: Any,
    timeout: float = OPERATION_TIMEOUT_SECONDS,
    **kwargs: Any,
) -> T:
    """
    Run a blocking function in a thread pool with timeout.
    
    This is the primary way to safely run CPU-bound geometry operations
    (like DXF parsing, contour reconstruction, cycle detection) without
    blocking the async event loop or hanging indefinitely.
    
    Args:
        func: The blocking function to call
        *args: Positional arguments for func
        timeout: Timeout in seconds (default from dxf_limits)
        **kwargs: Keyword arguments for func
    
    Returns:
        The function's return value
    
    Raises:
        GeometryTimeout: If operation exceeds timeout
        Exception: Any exception raised by func (re-raised as-is)
    
    Example:
        result = await run_with_timeout(
            find_cycles_dfs,
            adjacency,
            unique_points,
            timeout=30.0,
        )
    """
    loop = asyncio.get_event_loop()
    
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(
                _geometry_executor,
                partial(func, *args, **kwargs)
            ),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(
            "GEOMETRY_OPERATION_TIMEOUT",
            extra={
                "reason": "operation_timeout",
                "timeout_seconds": timeout,
                "function": func.__name__,
            }
        )
        raise GeometryTimeout(
            f"Geometry operation timed out after {timeout:.1f}s. "
            "The geometry may be too complex or malformed. "
            "Try simplifying the DXF or splitting into smaller files.",
            timeout=timeout
        )


async def run_with_timeout_or_none(
    func: Callable[..., T],
    *args: Any,
    timeout: float = OPERATION_TIMEOUT_SECONDS,
    default: T = None,
    **kwargs: Any,
) -> T:
    """
    Like run_with_timeout, but returns default value on timeout instead of raising.
    
    Useful for optional/best-effort operations.
    """
    try:
        return await run_with_timeout(func, *args, timeout=timeout, **kwargs)
    except GeometryTimeout:
        return default


def shutdown_geometry_executor():
    """Shutdown the geometry thread pool. Call on application shutdown."""
    _geometry_executor.shutdown(wait=True)
