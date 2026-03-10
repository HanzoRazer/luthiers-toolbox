"""
CNC Pre-flight Validation Gate

Blocking validation that MUST pass before G-code execution.
This is the final safety check before material is cut.

Validates:
- G-code structure (units, modes, spindle, feed rates)
- Depth vs stock thickness (no cuts deeper than material)
- Bounds vs machine limits
- Safe-Z retract behavior
- Tool diameter vs feature size

Usage:
    from app.cam.preflight_gate import preflight_validate, PreflightConfig

    result = preflight_validate(
        gcode_text=gcode,
        config=PreflightConfig(stock_thickness_mm=25.0)
    )
    if not result.ok:
        raise PreflightBlockedError(result.errors)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.safety import safety_critical
from app.saw_lab.toolpaths_validate_service import (
    validate_gcode_static,
    Bounds,
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

@dataclass
class PreflightConfig:
    """Configuration for pre-flight validation."""

    # Stock parameters
    stock_thickness_mm: Optional[float] = None
    stock_width_mm: Optional[float] = None
    stock_length_mm: Optional[float] = None

    # Tool parameters
    tool_diameter_mm: Optional[float] = None
    min_feature_size_mm: Optional[float] = None

    # Machine limits
    machine_bounds_mm: Optional[Dict[str, float]] = None

    # Safety parameters
    safe_z_mm: float = 5.0
    max_depth_margin_mm: float = 1.0  # Don't cut within 1mm of stock bottom

    # Validation flags
    require_units_mm: bool = True
    require_absolute: bool = True
    require_spindle_on: bool = True
    require_feed_on_cut: bool = True

    # Strictness
    strict_mode: bool = False  # If True, warnings become errors


@dataclass
class PreflightResult:
    """Result of pre-flight validation."""
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": self.summary,
        }


class PreflightBlockedError(Exception):
    """Raised when pre-flight validation fails."""

    def __init__(self, errors: List[str], warnings: List[str] = None):
        self.errors = errors
        self.warnings = warnings or []
        super().__init__(f"Pre-flight blocked: {errors}")


# -----------------------------------------------------------------------------
# Depth Validation
# -----------------------------------------------------------------------------

def _validate_depth_vs_stock(
    bounds: Bounds,
    stock_thickness_mm: Optional[float],
    max_depth_margin_mm: float,
    errors: List[str],
    warnings: List[str],
) -> None:
    """
    Validate that cuts don't exceed stock thickness.

    Convention: Z=0 is stock top surface, negative Z is into material.
    """
    if stock_thickness_mm is None:
        warnings.append("Stock thickness not specified - depth validation skipped.")
        return

    if bounds.min_z is None:
        warnings.append("No Z movements detected - depth validation skipped.")
        return

    # min_z is the deepest cut (most negative)
    max_cut_depth = abs(bounds.min_z)
    allowable_depth = stock_thickness_mm - max_depth_margin_mm

    if max_cut_depth > stock_thickness_mm:
        errors.append(
            f"CRITICAL: Cut depth {max_cut_depth:.2f}mm exceeds stock thickness "
            f"{stock_thickness_mm:.2f}mm. Tool will cut through material!"
        )
    elif max_cut_depth > allowable_depth:
        warnings.append(
            f"Cut depth {max_cut_depth:.2f}mm is within {max_depth_margin_mm}mm of "
            f"stock bottom ({stock_thickness_mm:.2f}mm). Risk of cut-through."
        )


# -----------------------------------------------------------------------------
# Tool vs Feature Validation
# -----------------------------------------------------------------------------

def _validate_tool_vs_bounds(
    bounds: Bounds,
    tool_diameter_mm: Optional[float],
    min_feature_size_mm: Optional[float],
    errors: List[str],
    warnings: List[str],
) -> None:
    """
    Validate tool diameter against feature sizes.
    """
    if tool_diameter_mm is None:
        return

    # Check minimum feature size
    if min_feature_size_mm is not None and tool_diameter_mm > min_feature_size_mm:
        errors.append(
            f"Tool diameter {tool_diameter_mm:.2f}mm exceeds minimum feature size "
            f"{min_feature_size_mm:.2f}mm. Tool cannot fit in features."
        )

    # Check XY bounds for reasonableness
    if bounds.min_x is not None and bounds.max_x is not None:
        x_range = bounds.max_x - bounds.min_x
        if x_range < tool_diameter_mm:
            warnings.append(
                f"X range ({x_range:.2f}mm) is smaller than tool diameter "
                f"({tool_diameter_mm:.2f}mm). Verify this is intentional."
            )

    if bounds.min_y is not None and bounds.max_y is not None:
        y_range = bounds.max_y - bounds.min_y
        if y_range < tool_diameter_mm:
            warnings.append(
                f"Y range ({y_range:.2f}mm) is smaller than tool diameter "
                f"({tool_diameter_mm:.2f}mm). Verify this is intentional."
            )


# -----------------------------------------------------------------------------
# Main Pre-flight Gate
# -----------------------------------------------------------------------------

@safety_critical
def preflight_validate(
    gcode_text: str,
    config: Optional[PreflightConfig] = None,
) -> PreflightResult:
    """
    Execute pre-flight validation gate.

    This is the blocking check before G-code execution. If this returns
    ok=False, the G-code MUST NOT be executed.

    Args:
        gcode_text: The G-code program to validate
        config: Validation configuration (uses defaults if None)

    Returns:
        PreflightResult with ok=True if safe to execute, ok=False if blocked
    """
    if config is None:
        config = PreflightConfig()

    errors: List[str] = []
    warnings: List[str] = []

    # Run base G-code validation
    base_result = validate_gcode_static(
        gcode_text=gcode_text,
        safe_z_mm=config.safe_z_mm,
        bounds_mm=config.machine_bounds_mm,
        require_units_mm=config.require_units_mm,
        require_absolute=config.require_absolute,
        require_xy_plane=False,
        require_spindle_on=config.require_spindle_on,
        require_feed_on_cut=config.require_feed_on_cut,
    )

    errors.extend(base_result.get("errors", []))
    warnings.extend(base_result.get("warnings", []))
    summary = base_result.get("summary", {})

    # Extract bounds for additional checks
    bounds_dict = summary.get("bounds", {})
    bounds = Bounds(
        min_x=bounds_dict.get("min_x"),
        max_x=bounds_dict.get("max_x"),
        min_y=bounds_dict.get("min_y"),
        max_y=bounds_dict.get("max_y"),
        min_z=bounds_dict.get("min_z"),
        max_z=bounds_dict.get("max_z"),
    )

    # Depth vs stock thickness
    _validate_depth_vs_stock(
        bounds=bounds,
        stock_thickness_mm=config.stock_thickness_mm,
        max_depth_margin_mm=config.max_depth_margin_mm,
        errors=errors,
        warnings=warnings,
    )

    # Tool vs feature size
    _validate_tool_vs_bounds(
        bounds=bounds,
        tool_diameter_mm=config.tool_diameter_mm,
        min_feature_size_mm=config.min_feature_size_mm,
        errors=errors,
        warnings=warnings,
    )

    # Strict mode: promote warnings to errors
    if config.strict_mode:
        errors.extend(warnings)
        warnings = []

    # Add preflight metadata to summary
    summary["preflight"] = {
        "stock_thickness_mm": config.stock_thickness_mm,
        "tool_diameter_mm": config.tool_diameter_mm,
        "safe_z_mm": config.safe_z_mm,
        "strict_mode": config.strict_mode,
    }

    ok = len(errors) == 0

    if not ok:
        logger.warning(
            "Pre-flight validation BLOCKED: %d errors, %d warnings",
            len(errors),
            len(warnings),
        )

    return PreflightResult(
        ok=ok,
        errors=errors,
        warnings=warnings,
        summary=summary,
    )


def preflight_gate(
    gcode_text: str,
    config: Optional[PreflightConfig] = None,
) -> None:
    """
    Blocking pre-flight gate. Raises PreflightBlockedError if validation fails.

    Use this as a guard before G-code execution:

        preflight_gate(gcode, PreflightConfig(stock_thickness_mm=25.0))
        # If we get here, it's safe to execute
        execute_gcode(gcode)

    Raises:
        PreflightBlockedError: If validation fails
    """
    result = preflight_validate(gcode_text, config)
    if not result.ok:
        raise PreflightBlockedError(result.errors, result.warnings)
