"""
Pocketing Intent Adapter

Bridge between CamIntentV1 and the L.1 adaptive-core pocketing engine.

Reads a Pocketing design block + context and produces a PocketIntentAdaptation
(loops + engine params) for plan_adaptive_l1 / to_toolpath. Maps; does not generate.

Follows the wood-data ValueError discipline. Reconstructed from preserved bytecode.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Tuple

from app.rmos.cam.schemas_intent import CamIntentV1

from .intent_schema import PocketDesignV1, validate_pocket_design


@dataclass
class PocketIntentAdaptation:
    """Engine-ready parameters extracted from a CamIntentV1 for L.1 pocketing."""

    loops: List[List[Tuple[float, float]]]  # [boundary, *islands]
    tool_d: float
    stepover: float  # FRACTION (0.3-0.7) for plan_adaptive_l1
    stepdown: float
    margin: float
    strategy: Literal["Spiral", "Lanes"]
    smoothing_radius: float
    feed_xy: float
    plunge_rate: float
    safe_z: float
    retract_z: float
    pocket_depth_mm: float
    finish_pass: bool
    finish_allowance_mm: float
    issues: List[Dict[str, str]] = field(default_factory=list)


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


def _extract_context_str(
    context: Dict[str, Any],
    key: str,
    *,
    default: str | None = None,
    allowed: List[str] | None = None,
) -> str | None:
    """Extract a string from context, optionally restricted to an allowed set."""
    value = context.get(key)
    if value is None:
        return default
    value = str(value)
    if allowed is not None and value not in allowed:
        raise ValueError(f"context.{key} must be one of {allowed}, got {value}")
    return value


def _design_points_to_tuples(points: List[Any]) -> List[Tuple[float, float]]:
    """Convert PocketPointV1 list to coordinate tuples for L.1."""
    return [(pt.x, pt.y) for pt in points]


def pocket_params_from_intent(intent: CamIntentV1) -> PocketIntentAdaptation:
    """
    Extract a PocketIntentAdaptation from a normalized CamIntentV1.

    Raises:
        ValueError: invalid design or out-of-bounds context (no silent design defaults).
    """
    design: PocketDesignV1 = validate_pocket_design(intent.design)

    boundary = _design_points_to_tuples(design.boundary)
    islands = [_design_points_to_tuples(isl.boundary) for isl in design.islands]
    loops = [boundary] + islands

    context = intent.context or {}

    # stepover: schema percent (30-70) -> fraction (0.3-0.7) for plan_adaptive_l1
    stepover = design.stepover_percent / 100.0

    stepdown = _extract_context_float(context, "stepdown_mm", default=2.0, ge=0.1, le=20.0)
    margin = _extract_context_float(context, "margin_mm", default=0.0, ge=0.0, le=25.0)
    strategy = _extract_context_str(context, "strategy", default="Spiral", allowed=["Spiral", "Lanes"])
    smoothing_radius = _extract_context_float(context, "smoothing_radius_mm", default=0.5, ge=0.05, le=1.0)
    feed_xy = _extract_context_float(context, "feed_rate_mm_min", default=1500.0, ge=100.0, le=10000.0)
    plunge_rate = _extract_context_float(context, "plunge_rate_mm_min", default=500.0, ge=50.0, le=2000.0)
    safe_z = _extract_context_float(context, "safe_z_mm", default=5.0, ge=1.0, le=50.0)
    retract_z = _extract_context_float(context, "retract_z_mm", default=2.0, ge=0.5, le=25.0)

    return PocketIntentAdaptation(
        loops=loops,
        tool_d=design.tool_diameter_mm,
        stepover=stepover,
        stepdown=stepdown,
        margin=margin,
        strategy=strategy,  # type: ignore[arg-type]
        smoothing_radius=smoothing_radius,
        feed_xy=feed_xy,
        plunge_rate=plunge_rate,
        safe_z=safe_z,
        retract_z=retract_z,
        pocket_depth_mm=design.pocket_depth_mm,
        finish_pass=design.finish_pass,
        finish_allowance_mm=design.finish_allowance_mm,
        issues=[],
    )
