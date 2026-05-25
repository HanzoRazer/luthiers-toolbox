"""
Profile Intent Adapter

Bridge between CamIntentV1 and the Profile engine's ProfileConfig.

This is the only file that knows how to read a Profile design block
and context fields to construct engine parameters.

Follows the wood-data ValueError discipline: raises structured errors
on missing required keys, never falls back to silent defaults.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.rmos.cam.schemas_intent import CamIntentV1

from .intent_schema import ProfileDesignV1, ProfilePointV1, validate_profile_design
from .profile_toolpath import ProfileConfig, MillingDirection


def _extract_context_float(
    context: Dict[str, Any],
    key: str,
    *,
    default: float | None = None,
    ge: float | None = None,
    le: float | None = None,
) -> float | None:
    """
    Extract a float from context dict with optional bounds checking.

    Returns default if key is missing or None.
    Raises ValueError if value exists but is out of bounds.
    """
    value = context.get(key)
    if value is None:
        return default

    try:
        f = float(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"context.{key} must be a number, got {type(value).__name__}") from e

    if ge is not None and f < ge:
        raise ValueError(f"context.{key} must be >= {ge}, got {f}")
    if le is not None and f > le:
        raise ValueError(f"context.{key} must be <= {le}, got {f}")

    return f


def _extract_context_bool(
    context: Dict[str, Any],
    key: str,
    *,
    default: bool = True,
) -> bool:
    """Extract a bool from context dict."""
    value = context.get(key)
    if value is None:
        return default
    return bool(value)


def _design_contour_to_tuples(design: ProfileDesignV1) -> List[Tuple[float, float]]:
    """Convert ProfileDesignV1 contour to tuple format for engine."""
    return [(pt.x, pt.y) for pt in design.contour]


def profile_params_from_intent(intent: CamIntentV1) -> Tuple[List[Tuple[float, float]], ProfileConfig, bool]:
    """
    Extract outline, ProfileConfig, and is_closed from a normalized CamIntentV1.

    Args:
        intent: A CamIntentV1 that has been normalized (units=mm).

    Returns:
        Tuple of (outline points, ProfileConfig, is_closed) ready for ProfileToolpath.

    Raises:
        ValueError: If design is missing required keys or has invalid values.
                   Follows wood-data ValueError discipline — no silent defaults.
    """
    # Validate design against ProfileDesignV1 schema
    design = validate_profile_design(intent.design)

    # Convert contour to engine format
    outline = _design_contour_to_tuples(design)
    is_closed = design.is_closed

    # Extract context fields with defaults matching production router
    context = intent.context or {}

    # Map is_outside to compensation_side
    compensation_side = "outside" if design.is_outside else "inside"

    # Map climb_milling to direction enum
    climb_milling = _extract_context_bool(context, "climb_milling", default=True)
    direction = MillingDirection.CLIMB if climb_milling else MillingDirection.CONVENTIONAL

    # Build ProfileConfig from design + context
    config = ProfileConfig(
        # From design (tool and cut geometry)
        tool_diameter_mm=design.tool_diameter_mm,
        cut_depth_mm=design.cut_depth_mm,

        # From context (operational parameters) - map to actual ProfileConfig fields
        stepdown_mm=_extract_context_float(context, "stepdown_mm", default=6.0, ge=0.1, le=20.0)
        or _extract_context_float(context, "max_stepdown_mm", default=6.0, ge=0.1, le=20.0),

        # Feed rates - map from intent names to ProfileConfig names
        feed_rate_xy=_extract_context_float(context, "feed_rate_mm_min", default=1500.0, ge=100.0, le=10000.0),
        feed_rate_z=_extract_context_float(context, "feed_rate_z_mm_min", default=500.0, ge=50.0, le=2000.0),
        plunge_rate=_extract_context_float(context, "plunge_rate_mm_min", default=300.0, ge=50.0, le=2000.0),

        # Heights
        safe_z_mm=_extract_context_float(context, "safe_z_mm", default=5.0, ge=1.0, le=50.0),
        retract_z_mm=_extract_context_float(context, "retract_z_mm", default=2.0, ge=0.5, le=25.0),

        # Tabs (from design)
        tab_count=design.tab_count if design.use_tabs else 0,
        tab_width_mm=design.tab_width_mm,
        tab_height_mm=design.tab_height_mm,

        # Lead-in
        lead_in_radius_mm=_extract_context_float(context, "lead_in_radius_mm", default=5.0, ge=0.0, le=25.0),

        # Direction and compensation
        direction=direction,
        compensation_side=compensation_side,

        # Finishing (from design)
        finishing_pass=design.finishing_pass,
        finishing_allowance_mm=design.finishing_allowance_mm,
    )

    return outline, config, is_closed
