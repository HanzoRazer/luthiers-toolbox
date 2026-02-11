"""
Safety-critical function decorators and utilities.

Functions marked with @safety_critical are identified as having
direct impact on physical machine operations (G-code generation,
feeds/speeds calculation, feasibility decisions).

These functions:
1. Must never silently swallow exceptions
2. Are logged for audit purposes
3. Are tracked by fence_checker_v2 for coverage
"""
from __future__ import annotations

import logging
import functools
from typing import Callable, TypeVar, Any

F = TypeVar("F", bound=Callable[..., Any])

_safety_logger = logging.getLogger("safety_critical")


def safety_critical(func: F) -> F:
    """
    Mark a function as safety-critical.

    Safety-critical functions have direct impact on physical machine
    operations. This decorator:

    1. Logs function entry/exit for audit trail
    2. Ensures exceptions are never silently swallowed
    3. Re-raises all exceptions after logging

    Usage:
        @safety_critical
        def generate_gcode(params: CamParams) -> str:
            ...

        @safety_critical
        def compute_feasibility(input: FeasibilityInput) -> FeasibilityResult:
            ...
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = f"{func.__module__}.{func.__name__}"
        _safety_logger.debug(f"SAFETY_ENTER: {func_name}")
        try:
            result = func(*args, **kwargs)
            _safety_logger.debug(f"SAFETY_EXIT: {func_name} (success)")
            return result
        except Exception as e:
            _safety_logger.error(
                f"SAFETY_FAIL: {func_name} raised {type(e).__name__}: {e}",
                exc_info=True
            )
            raise  # Always re-raise, never swallow

    # Mark function for fence checker detection
    wrapper._is_safety_critical = True
    wrapper._original_func = func

    return wrapper  # type: ignore[return-value]


def is_safety_critical(func: Callable[..., Any]) -> bool:
    """Check if a function is marked as safety-critical."""
    return getattr(func, "_is_safety_critical", False)
