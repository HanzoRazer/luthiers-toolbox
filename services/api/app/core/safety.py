"""
Safety-critical function decorator for RMOS manufacturing operations.

Functions decorated with @safety_critical:
- Never swallow exceptions silently
- Log CRITICAL level on any unhandled exception
- Always re-raise (fail-closed behavior)

Apply to: feasibility computation, G-code generation, feeds/speeds, risk bucketing.
"""

from __future__ import annotations

import functools
import logging
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger("safety")


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
        - On success: returns normally
        - On exception: logs CRITICAL with full traceback, then re-raises
        - Never swallows exceptions
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except Exception:  # WP-3: intentional — safety-critical logger must catch all exceptions
            logger.critical(
                "SAFETY-CRITICAL FAILURE in %s",
                func.__qualname__,
                exc_info=True,
            )
            raise  # never swallow

    return wrapper
