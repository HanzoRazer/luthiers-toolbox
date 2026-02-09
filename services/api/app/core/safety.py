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
        except Exception:
            logger.critical(
                "SAFETY-CRITICAL FAILURE in %s",
                func.__qualname__,
                exc_info=True,
            )
            raise  # never swallow

    return wrapper


def safety_critical_async(func: Callable[P, R]) -> Callable[P, R]:
    """
    Async version of @safety_critical for async functions.

    Usage:
        @safety_critical_async
        async def generate_gcode(...):
            ...
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return await func(*args, **kwargs)
        except Exception:
            logger.critical(
                "SAFETY-CRITICAL FAILURE in %s",
                func.__qualname__,
                exc_info=True,
            )
            raise  # never swallow

    return wrapper


# =============================================================================
# SPECIFIC EXCEPTION TYPES FOR SAFETY-CRITICAL OPERATIONS
# =============================================================================


class FeasibilityError(Exception):
    """Base exception for feasibility analysis errors."""
    pass


class FeasibilityInputError(FeasibilityError):
    """Invalid input to feasibility analysis."""
    pass


class FeasibilityRuleError(FeasibilityError):
    """Error evaluating a feasibility rule."""
    pass


class GCodeGenerationError(Exception):
    """Error during G-code generation."""
    pass


class ToolpathError(Exception):
    """Error during toolpath computation."""
    pass


class MaterialError(Exception):
    """Error related to material properties or validation."""
    pass


class MachineConfigError(Exception):
    """Error in machine configuration or limits."""
    pass


class RunArtifactError(Exception):
    """Error reading/writing run artifacts."""
    pass


class AuditTrailError(Exception):
    """Error maintaining audit trail."""
    pass


class SawLabError(Exception):
    """Error in saw lab operations."""
    pass


class DecisionIntelligenceError(Exception):
    """Error in decision intelligence service."""
    pass
