"""
Pocketing Intent Adapter

Bridge between CamIntentV1 and the L.1 adaptive pocketing engine.

This adapter maps directly to L.1's plan_adaptive_l1 function parameters,
not to a PocketConfig dataclass (which doesn't exist).

L.1 function signature:
    plan_adaptive_l1(
        loops: List[List[Tuple[float, float]]],  # [boundary, *islands]
        tool_d: float,
        stepover: float,  # fraction 0.3-0.7
        stepdown: float,
        margin: float,
        strategy: Literal["Spiral", "Lanes"],
        smoothing_radius: float,
    ) -> List[Tuple[float, float]]

Field mapping:
- design.boundary -> loops[0]
- design.islands -> loops[1:]
- design.tool_diameter_mm -> tool_d
- design.stepover_percent / 100 -> stepover (fraction)
- context.stepdown_mm -> stepdown
- context.margin_mm -> margin
- context.strategy -> strategy
- context.smoothing_radius_mm -> smoothing_radius

Follows the wood-data ValueError discipline: raises structured errors
on missing required keys, never falls back to silent defaults.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Tuple

from app.rmos.cam.schemas_intent import CamIntentV1

from .intent_schema import PocketDesignV1, validate_pocket_design


@dataclass
class PocketIntentAdaptation:
    """
    Adaptation result mapping CamIntentV1 to L.1 parameters.

    This is NOT a PocketConfig (which doesn't exist) - it's a direct
    mapping to L.1's plan_adaptive_l1 function parameters.
    """

    # Geometry (loops format for L.1)
    loops: List[List[Tuple[float, float]]]  # [boundary, *islands]

    # L.1 parameters
    tool_d: float
    stepover: float  # fraction, not percent
    stepdown: float
    margin: float
    strategy: Literal["Spiral", "Lanes"]
    smoothing_radius: float

    # Additional parameters for G-code generation (to_toolpath)
    feed_xy: float
    plunge_rate: float
    safe_z: float
    retract_z: float

    # Pocket metadata
    pocket_depth_mm: float
    finish_pass: bool
    finish_allowance_mm: float

    # Normalization issues
    issues: List[Dict[str, str]] = field(default_factory=list)


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


def _extract_context_str(
    context: Dict[str, Any],
    key: str,
    *,
    default: str | None = None,
    allowed: List[str] | None = None,
) -> str | None:
    """
    Extract a string from context dict with optional allowed values.

    Returns default if key is missing or None.
    Raises ValueError if value exists but is not in allowed list.
    """
    value = context.get(key)
    if value is None:
        return default

    s = str(value)
    if allowed is not None and s not in allowed:
        raise ValueError(f"context.{key} must be one of {allowed}, got {s}")

    return s


def _design_points_to_tuples(
    points: List[Any],
) -> List[Tuple[float, float]]:
    """Convert PocketPointV1 list to coordinate tuples for L.1."""
    return [(pt.x, pt.y) for pt in points]


def pocket_params_from_intent(intent: CamIntentV1) -> PocketIntentAdaptation:
    """
    Extract L.1 parameters from a normalized CamIntentV1.

    Args:
        intent: A CamIntentV1 that has been normalized (units=mm).

    Returns:
        PocketIntentAdaptation ready for L.1's plan_adaptive_l1.

    Raises:
        ValueError: If design is missing required keys or has invalid values.
                   Follows wood-data ValueError discipline — no silent defaults.

    Field Mapping:
        design.boundary -> loops[0]
        design.islands[].boundary -> loops[1:]
        design.tool_diameter_mm -> tool_d
        design.stepover_percent / 100 -> stepover
        design.pocket_depth_mm -> pocket_depth_mm
        design.finish_pass -> finish_pass
        design.finish_allowance_mm -> finish_allowance_mm
        context.stepdown_mm -> stepdown
        context.margin_mm -> margin
        context.strategy -> strategy
        context.smoothing_radius_mm -> smoothing_radius
        context.feed_rate_mm_min -> feed_xy
        context.plunge_rate_mm_min -> plunge_rate
        context.safe_z_mm -> safe_z
        context.retract_z_mm -> retract_z
    """
    issues: List[Dict[str, str]] = []

    # Validate design against PocketDesignV1 schema
    design = validate_pocket_design(intent.design)

    # Convert boundary to coordinate tuples
    boundary = _design_points_to_tuples(design.boundary)

    # Convert islands to coordinate tuples
    islands = [
        _design_points_to_tuples(island.boundary)
        for island in design.islands
    ]

    # Build loops list [boundary, *islands] for L.1
    loops = [boundary] + islands

    # Extract context fields
    context = intent.context or {}

    # Convert stepover_percent to fraction for L.1
    # L.1 expects 0.3-0.7, schema validates 30-70%
    stepover_fraction = design.stepover_percent / 100.0

    # Extract L.1 parameters from context
    stepdown = _extract_context_float(
        context, "stepdown_mm", default=3.0, ge=0.1, le=25.0
    )
    margin = _extract_context_float(
        context, "margin_mm", default=0.0, ge=0.0, le=10.0
    )
    strategy = _extract_context_str(
        context, "strategy", default="Spiral", allowed=["Spiral", "Lanes"]
    )
    smoothing_radius = _extract_context_float(
        context, "smoothing_radius_mm", default=0.5, ge=0.0, le=10.0
    )

    # Extract G-code generation parameters
    feed_xy = _extract_context_float(
        context, "feed_rate_mm_min", default=1500.0, ge=50.0, le=10000.0
    )
    plunge_rate = _extract_context_float(
        context, "plunge_rate_mm_min", default=500.0, ge=50.0, le=2000.0
    )
    safe_z = _extract_context_float(
        context, "safe_z_mm", default=10.0, ge=1.0, le=100.0
    )
    retract_z = _extract_context_float(
        context, "retract_z_mm", default=5.0, ge=0.5, le=50.0
    )

    return PocketIntentAdaptation(
        loops=loops,
        tool_d=design.tool_diameter_mm,
        stepover=stepover_fraction,
        stepdown=stepdown,
        margin=margin,
        strategy=strategy,
        smoothing_radius=smoothing_radius,
        feed_xy=feed_xy,
        plunge_rate=plunge_rate,
        safe_z=safe_z,
        retract_z=retract_z,
        pocket_depth_mm=design.pocket_depth_mm,
        finish_pass=design.finish_pass,
        finish_allowance_mm=design.finish_allowance_mm,
        issues=issues,
    )
