# services/api/app/safety/cnc_preflight.py
"""
CNC Preflight Safety Checks - Fail-Closed Mode

This module provides safety validation that REFUSES to generate G-code
when parameters could result in dangerous machine operations.

CRITICAL SAFETY REQUIREMENTS:
1. Zero RPM → BLOCK (tool drags through material without cutting)
2. Zero flutes → BLOCK (division-by-zero in chipload calculation)
3. Min feed > max feed → BLOCK (nonsensical clamped values)
4. Zero/negative depth → BLOCK (no material removal defined)
5. Tool diameter = 0 → BLOCK (undefined cutting geometry)

This module implements the "fail-closed" philosophy: when in doubt,
refuse to generate rather than produce potentially dangerous G-code.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from app.safety import safety_critical

logger = logging.getLogger(__name__)


@dataclass
class CNCPreflightError:
    """A safety violation that blocks G-code generation."""
    code: str
    message: str
    severity: str = "CRITICAL"  # CRITICAL = hard block, WARNING = soft block


@dataclass
class CNCPreflightResult:
    """Result of CNC preflight safety check."""
    safe: bool
    errors: List[CNCPreflightError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.safe

    def to_dict(self) -> dict:
        return {
            "safe": self.safe,
            "errors": [{"code": e.code, "message": e.message, "severity": e.severity} for e in self.errors],
            "warnings": self.warnings,
        }


class CNCPreflightError_ZeroRPM(Exception):
    """Raised when spindle RPM is zero or negative."""
    pass


class CNCPreflightError_ZeroFlutes(Exception):
    """Raised when flute count is zero or negative."""
    pass


class CNCPreflightError_InvalidFeedRange(Exception):
    """Raised when min feed rate exceeds max feed rate."""
    pass


class CNCPreflightError_InvalidDepth(Exception):
    """Raised when depth of cut is zero or negative."""
    pass


class CNCPreflightError_InvalidToolDiameter(Exception):
    """Raised when tool diameter is zero or negative."""
    pass


@safety_critical
def validate_cnc_params(
    *,
    spindle_rpm: Optional[float] = None,
    flute_count: Optional[int] = None,
    feed_rate_min: Optional[float] = None,
    feed_rate_max: Optional[float] = None,
    depth_of_cut: Optional[float] = None,
    tool_diameter: Optional[float] = None,
    stepover_percent: Optional[float] = None,
    raise_on_error: bool = False,
) -> CNCPreflightResult:
    """
    Validate CNC parameters before G-code generation.

    This function implements FAIL-CLOSED safety:
    - If any parameter is unsafe, safe=False
    - If raise_on_error=True, raises exception immediately on first error
    - All provided parameters are validated (None = not checked)

    Args:
        spindle_rpm: Spindle speed in RPM (must be > 0)
        flute_count: Number of cutting edges (must be > 0)
        feed_rate_min: Minimum feed rate in mm/min (must be > 0)
        feed_rate_max: Maximum feed rate in mm/min (must be >= min)
        depth_of_cut: Depth per pass in mm (must be > 0)
        tool_diameter: Tool diameter in mm (must be > 0)
        stepover_percent: Stepover as percentage (must be 0 < x <= 100)
        raise_on_error: If True, raise exception on first error

    Returns:
        CNCPreflightResult with safe=True/False and error details

    Raises:
        CNCPreflightError_* when raise_on_error=True and validation fails
    """
    errors: List[CNCPreflightError] = []
    warnings: List[str] = []

    # RPM Check: Zero or negative RPM = tool drags without cutting
    if spindle_rpm is not None:
        if spindle_rpm <= 0:
            err = CNCPreflightError(
                code="ZERO_RPM",
                message=f"Spindle RPM must be > 0 (got {spindle_rpm}). Zero RPM causes tool to drag through material without cutting.",
            )
            errors.append(err)
            if raise_on_error:
                raise CNCPreflightError_ZeroRPM(err.message)
        elif spindle_rpm < 1000:
            warnings.append(f"Very low RPM ({spindle_rpm}). Most CNC operations require 8000-24000 RPM.")

    # Flute count: Zero flutes = division by zero in chipload
    if flute_count is not None:
        if flute_count <= 0:
            err = CNCPreflightError(
                code="ZERO_FLUTES",
                message=f"Flute count must be > 0 (got {flute_count}). Zero flutes causes division-by-zero in chipload calculation.",
            )
            errors.append(err)
            if raise_on_error:
                raise CNCPreflightError_ZeroFlutes(err.message)

    # Feed rate range: min > max is nonsensical
    if feed_rate_min is not None and feed_rate_max is not None:
        if feed_rate_min > feed_rate_max:
            err = CNCPreflightError(
                code="INVALID_FEED_RANGE",
                message=f"Min feed rate ({feed_rate_min}) exceeds max ({feed_rate_max}). This produces nonsensical clamped values.",
            )
            errors.append(err)
            if raise_on_error:
                raise CNCPreflightError_InvalidFeedRange(err.message)

    if feed_rate_min is not None and feed_rate_min <= 0:
        err = CNCPreflightError(
            code="ZERO_FEED_MIN",
            message=f"Minimum feed rate must be > 0 (got {feed_rate_min}).",
        )
        errors.append(err)

    if feed_rate_max is not None and feed_rate_max <= 0:
        err = CNCPreflightError(
            code="ZERO_FEED_MAX",
            message=f"Maximum feed rate must be > 0 (got {feed_rate_max}).",
        )
        errors.append(err)

    # Depth of cut: Zero or negative means no material removal
    if depth_of_cut is not None:
        if depth_of_cut <= 0:
            err = CNCPreflightError(
                code="INVALID_DEPTH",
                message=f"Depth of cut must be > 0 (got {depth_of_cut}). Zero/negative depth means no material removal.",
            )
            errors.append(err)
            if raise_on_error:
                raise CNCPreflightError_InvalidDepth(err.message)

    # Tool diameter: Zero = undefined cutting geometry
    if tool_diameter is not None:
        if tool_diameter <= 0:
            err = CNCPreflightError(
                code="INVALID_TOOL_DIAMETER",
                message=f"Tool diameter must be > 0 (got {tool_diameter}). Zero diameter means undefined cutting geometry.",
            )
            errors.append(err)
            if raise_on_error:
                raise CNCPreflightError_InvalidToolDiameter(err.message)

    # Stepover: Must be in valid range
    if stepover_percent is not None:
        if stepover_percent <= 0:
            err = CNCPreflightError(
                code="INVALID_STEPOVER",
                message=f"Stepover must be > 0% (got {stepover_percent}%). Zero stepover means infinite passes.",
            )
            errors.append(err)
        elif stepover_percent > 100:
            err = CNCPreflightError(
                code="INVALID_STEPOVER",
                message=f"Stepover must be <= 100% (got {stepover_percent}%). Over 100% leaves uncut material.",
            )
            errors.append(err)
        elif stepover_percent > 80:
            warnings.append(f"High stepover ({stepover_percent}%) may cause poor surface finish.")

    safe = len(errors) == 0
    return CNCPreflightResult(safe=safe, errors=errors, warnings=warnings)


@safety_critical
def require_safe_cnc_params(
    **kwargs,
) -> None:
    """
    Validate CNC parameters and RAISE if unsafe.

    This is the fail-closed entry point: call this before G-code generation
    to ensure no dangerous parameters are accepted.

    Usage:
        from app.safety.cnc_preflight import require_safe_cnc_params

        @safety_critical
        def generate_gcode(rpm: int, flutes: int, ...):
            # Fail-closed: raises exception if params are unsafe
            require_safe_cnc_params(
                spindle_rpm=rpm,
                flute_count=flutes,
                ...
            )
            # Only reached if params are safe
            return _do_generate(...)

    Raises:
        CNCPreflightError_* if any parameter is unsafe
    """
    result = validate_cnc_params(raise_on_error=True, **kwargs)
    # This line is only reached if no exception was raised
    if not result.safe:
        # This shouldn't happen since raise_on_error=True, but defensive
        raise ValueError(f"CNC preflight failed: {result.errors}")


def calculate_chipload_safe(
    feed_rate_mm_min: float,
    spindle_rpm: float,
    flute_count: int,
) -> float:
    """
    Calculate chipload with fail-closed safety validation.

    Unlike the original calculate_chipload() which returns 0.0 for invalid
    inputs (failing open), this function RAISES an exception.

    Args:
        feed_rate_mm_min: Feed rate in mm/min
        spindle_rpm: Spindle speed in RPM
        flute_count: Number of cutting edges

    Returns:
        Chipload in mm per tooth

    Raises:
        CNCPreflightError_ZeroRPM: If RPM <= 0
        CNCPreflightError_ZeroFlutes: If flutes <= 0
    """
    require_safe_cnc_params(
        spindle_rpm=spindle_rpm,
        flute_count=flute_count,
    )
    return feed_rate_mm_min / (spindle_rpm * flute_count)
