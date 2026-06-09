"""
Drilling Intent Adapter

Bridge between CamIntentV1 and the drilling engine's DrillConfig + DrillHole list.

This is the only file that knows how to read a Drilling design block + context
fields to construct engine parameters. It preserves the proven peck-drilling
runtime — it maps, it does not generate G-code.

Follows the wood-data ValueError discipline: raises structured errors on invalid
values, never falls back to silent defaults for design fields.
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
    """Extract a float from context with optional bounds. Default if missing/None."""
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


def _design_holes_to_engine(design: DrillingDesignV1) -> List[DrillHole]:
    """Convert DrillingDesignV1 holes to engine DrillHole list."""
    return [
        DrillHole(
            x=pt.x,
            y=pt.y,
            depth_mm=pt.depth_mm,  # None => engine uses config.hole_depth_mm
            diameter_mm=design.hole_diameter_mm,
            label=pt.label,
        )
        for pt in design.holes
    ]


def drilling_params_from_intent(intent: CamIntentV1) -> Tuple[List[DrillHole], DrillConfig]:
    """
    Extract (holes, DrillConfig) from a normalized CamIntentV1.

    Args:
        intent: A CamIntentV1 that has been normalized (units=mm).

    Returns:
        Tuple of (DrillHole list, DrillConfig) ready for PeckDrill.

    Raises:
        ValueError: If design is missing required keys or context has invalid values.
                   No silent defaults for design fields (wood-data discipline).
    """
    # Validate design against DrillingDesignV1 schema
    design = validate_drilling_design(intent.design)

    # Holes from design geometry
    holes = _design_holes_to_engine(design)

    # Operational params from context (with production-matching defaults)
    context = intent.context or {}

    feed_rate = _extract_context_float(context, "feed_rate_mm_min", default=100.0, ge=10.0, le=1000.0)
    rapid_rate = _extract_context_float(context, "rapid_rate_mm_min", default=3000.0, ge=100.0, le=10000.0)
    spindle = _extract_context_float(context, "spindle_rpm", default=2000.0, ge=1.0, le=30000.0)
    safe_z = _extract_context_float(context, "safe_z_mm", default=10.0, ge=1.0, le=50.0)
    # accept either retract_z_mm or retract_height_mm
    retract_z = (
        _extract_context_float(context, "retract_z_mm", default=None, ge=0.5, le=25.0)
        if context.get("retract_z_mm") is not None
        else _extract_context_float(context, "retract_height_mm", default=2.0, ge=0.5, le=25.0)
    )
    dwell = _extract_context_float(context, "dwell_ms", default=0.0, ge=0.0, le=10000.0)

    config = DrillConfig(
        # From design (the "what")
        hole_depth_mm=design.hole_depth_mm,
        peck_depth_mm=design.peck_depth_mm,
        drill_diameter_mm=design.hole_diameter_mm,
        use_canned_cycle=design.peck_drilling,
        # From context (operational "how")
        safe_z_mm=safe_z,
        retract_z_mm=retract_z,
        feed_rate=feed_rate,
        rapid_rate=rapid_rate,
        spindle_rpm=int(spindle),
        dwell_ms=int(dwell),
    )

    return holes, config
