"""
Safety-critical function decorator for RMOS manufacturing operations.

Functions decorated with @safety_critical:
- Never swallow exceptions silently
- Log CRITICAL level on any unhandled exception
- Always re-raise (fail-closed behavior)
- Preserve function signature for FastAPI dependency injection
- Mark wrapper with _is_safety_critical for fence checker detection

Apply to: feasibility computation, G-code generation, feeds/speeds, risk bucketing.

This is the CANONICAL implementation. Import from here:
    from app.core.safety import safety_critical

The app.safety module re-exports this for backward compatibility.
"""

from __future__ import annotations

import functools
import inspect
import logging
import os
from typing import Callable, TypeVar, ParamSpec, Any

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger("safety")

# Enable DEBUG entry/exit logging via environment variable
_DEBUG_SAFETY = os.getenv("SAFETY_DEBUG", "0").lower() in ("1", "true", "yes")


def safety_critical(func: Callable[P, R]) -> Callable[P, R]:
    """
    Mark a function as safety-critical.

    Disables broad exception swallowing — any unhandled exception
    propagates to the caller. Logs the failure path at CRITICAL level.

    Usage:
        @safety_critical
        def compute_feasibility(...):
            ...

    Behavior:
        - On success: returns normally (DEBUG log if SAFETY_DEBUG=1)
        - On exception: logs CRITICAL with full traceback, then re-raises
        - Never swallows exceptions
        - Preserves function signature for FastAPI
        - Marks wrapper with _is_safety_critical = True for fence checker
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        func_name = f"{func.__module__}.{func.__qualname__}"

        if _DEBUG_SAFETY:
            logger.debug("SAFETY_ENTER: %s", func_name)

        try:
            result = func(*args, **kwargs)
            if _DEBUG_SAFETY:
                logger.debug("SAFETY_EXIT: %s (success)", func_name)
            return result
        except Exception:  # WP-3: intentional — safety-critical logger must catch all exceptions  # AUDITED 2026-03: always re-raises
            logger.critical(
                "SAFETY-CRITICAL FAILURE in %s",
                func_name,
                exc_info=True,
            )
            raise  # never swallow

    # Mark function for fence checker detection
    wrapper._is_safety_critical = True  # type: ignore[attr-defined]
    wrapper._original_func = func  # type: ignore[attr-defined]

    # CRITICAL: Preserve function signature for FastAPI dependency injection
    # FastAPI uses inspect.signature() which checks __signature__ first
    wrapper.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]

    return wrapper  # type: ignore[return-value]


def is_safety_critical(func: Callable[..., Any]) -> bool:
    """Check if a function is marked as safety-critical."""
    return getattr(func, "_is_safety_critical", False)


# Mark the decorator itself for introspection
safety_critical._is_safety_critical = True  # type: ignore[attr-defined]
