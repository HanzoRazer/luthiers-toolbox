"""
Drilling Intent Adapter

Bridge between CamIntentV1 and the Drilling engine's DrillConfig.

This is the only file that knows how to read a Drilling design block
and context fields to construct engine parameters.

Field mapping:
- design.hole_diameter_mm -> DrillConfig.drill_diameter_mm
- design.hole_depth_mm -> DrillConfig.hole_depth_mm
- design.peck_depth_mm -> DrillConfig.peck_depth_mm
- design.holes -> List[DrillHole]

Follows the wood-data ValueError discipline: raises structured errors
on missing required keys, never falls back to silent defaults.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.rmos.cam.schemas_intent import CamIntentV1

from .intent_schema import DrillingDesignV1, validate_drilling_design
from .peck_cycle import DrillConfig, DrillHole


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


def _extract_context_int(
    context: Dict[str, Any],
    key: str,
    *,
    default: int | None = None,
    ge: int | None = None,
    le: int | None = None,
) -> int | None:
    """
    Extract an int from context dict with optional bounds checking.

    Returns default if key is missing or None.
    Raises ValueError if value exists but is out of bounds.
    """
    value = context.get(key)
    if value is None:
        return default

    try:
        i = int(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"context.{key} must be an integer, got {type(value).__name__}") from e

    if ge is not None and i < ge:
        raise ValueError(f"context.{key} must be >= {ge}, got {i}")
    if le is not None and i > le:
        raise ValueError(f"context.{key} must be <= {le}, got {i}")

    return i


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


def _design_holes_to_drill_holes(design: DrillingDesignV1) -> List[DrillHole]:
    """Convert DrillingDesignV1 holes to DrillHole format for engine."""
    return [
        DrillHole(
            x=pt.x,
            y=pt.y,
            depth_mm=pt.depth_mm,  # Per-hole override (None uses default)
            diameter_mm=design.hole_diameter_mm,  # For documentation
            label=pt.label,
        )
        for pt in design.holes
    ]


def drilling_params_from_intent(intent: CamIntentV1) -> Tuple[List[DrillHole], DrillConfig]:
    """
    Extract DrillHoles and DrillConfig from a normalized CamIntentV1.

    Args:
        intent: A CamIntentV1 that has been normalized (units=mm).

    Returns:
        Tuple of (List[DrillHole], DrillConfig) ready for PeckDrill.

    Raises:
        ValueError: If design is missing required keys or has invalid values.
                   Follows wood-data ValueError discipline — no silent defaults.

    Field Mapping (design.field -> DrillConfig.field):
        hole_diameter_mm -> drill_diameter_mm
        hole_depth_mm -> hole_depth_mm
        peck_depth_mm -> peck_depth_mm
        peck_drilling -> use_canned_cycle (inverted: peck=True means G83)
        dwell_ms -> dwell_ms
    """
    # Validate design against DrillingDesignV1 schema
    design = validate_drilling_design(intent.design)

    # Convert holes to engine format
    holes = _design_holes_to_drill_holes(design)

    # Extract context fields with reasonable defaults
    context = intent.context or {}

    # Build DrillConfig from design + context
    config = DrillConfig(
        # From design - direct mappings
        hole_depth_mm=design.hole_depth_mm,
        peck_depth_mm=design.peck_depth_mm or design.hole_depth_mm,  # Full depth if not peck
        drill_diameter_mm=design.hole_diameter_mm,  # KEY MAPPING
        dwell_ms=design.dwell_ms,

        # G83 vs G81 - peck_drilling=True means use G83 canned cycle
        use_canned_cycle=design.peck_drilling,

        # From context (operational parameters)
        feed_rate=_extract_context_float(
            context, "feed_rate_mm_min", default=100.0, ge=10.0, le=2000.0
        ),
        rapid_rate=_extract_context_float(
            context, "rapid_rate_mm_min", default=3000.0, ge=500.0, le=10000.0
        ),
        spindle_rpm=_extract_context_int(
            context, "spindle_rpm", default=2000, ge=100, le=30000
        ),

        # Heights from context
        safe_z_mm=_extract_context_float(
            context, "safe_z_mm", default=10.0, ge=1.0, le=100.0
        ),
        retract_z_mm=_extract_context_float(
            context, "retract_z_mm", default=2.0, ge=0.5, le=50.0
        ),
    )

    return holes, config
