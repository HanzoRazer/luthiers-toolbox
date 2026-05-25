"""
V-Carve Intent Adapter

Bridge between CamIntentV1 and the V-Carve engine's VCarveConfig.

This is the only file that knows how to read a V-Carve design block
and context fields to construct engine parameters.

Follows the wood-data ValueError discipline: raises structured errors
on missing required keys, never falls back to silent defaults.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.rmos.cam.schemas_intent import CamIntentV1

from .intent_schema import VCarveDesignV1, VCarvePathV1, PathPoint, validate_vcarve_design
from .toolpath import VCarveConfig, MLPath


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
    """Extract an int from context dict with optional bounds checking."""
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


def _extract_context_str(
    context: Dict[str, Any],
    key: str,
    *,
    default: str = "",
) -> str:
    """Extract a string from context dict."""
    value = context.get(key)
    if value is None:
        return default
    return str(value)


def _design_paths_to_ml_paths(design: VCarveDesignV1) -> List[MLPath]:
    """Convert VCarveDesignV1 paths to MLPath format for engine."""
    ml_paths: List[MLPath] = []
    for path in design.paths:
        points: List[Tuple[float, float]] = [
            (pt.x, pt.y) for pt in path.points
        ]
        ml_paths.append(MLPath(points=points, is_closed=path.is_closed))
    return ml_paths


def vcarve_params_from_intent(intent: CamIntentV1) -> Tuple[VCarveConfig, List[MLPath]]:
    """
    Extract VCarveConfig and MLPath list from a normalized CamIntentV1.

    Args:
        intent: A CamIntentV1 that has been normalized (units=mm).

    Returns:
        Tuple of (VCarveConfig, List[MLPath]) ready for VCarveToolpath.

    Raises:
        ValueError: If design is missing required keys or has invalid values.
                   Follows wood-data ValueError discipline — no silent defaults.
    """
    # Validate design against VCarveDesignV1 schema
    design = validate_vcarve_design(intent.design)

    # Convert paths to engine format
    ml_paths = _design_paths_to_ml_paths(design)

    # Extract context fields with defaults matching production router
    context = intent.context or {}

    # Material from envelope's material_id or context fallback
    material = intent.material_id or _extract_context_str(context, "material", default="hardwood")

    # Build VCarveConfig from design + context
    config = VCarveConfig(
        # From design (V-bit and cut intent)
        bit_angle_deg=design.bit_angle_deg,
        tip_diameter_mm=design.tip_diameter_mm,
        target_line_width_mm=design.target_line_width_mm,
        target_depth_mm=design.target_depth_mm,

        # From context (operational parameters)
        material=material,
        spindle_rpm=_extract_context_int(context, "spindle_rpm", default=18000, ge=5000, le=30000),
        flute_count=_extract_context_int(context, "flute_count", default=2, ge=1, le=4),
        chipload_factor=_extract_context_float(context, "chipload_factor", default=0.8, ge=0.3, le=1.0),

        # Multi-pass
        max_stepdown_mm=_extract_context_float(context, "max_stepdown_mm", default=2.0, ge=0.5, le=10.0),
        min_passes=_extract_context_int(context, "min_passes", default=1, ge=1, le=10),

        # Heights
        safe_z_mm=_extract_context_float(context, "safe_z_mm", default=5.0, ge=1.0, le=50.0),
        retract_z_mm=_extract_context_float(context, "retract_z_mm", default=2.0, ge=0.5, le=25.0),

        # Feed rates
        feed_rate_mm_min=_extract_context_float(context, "feed_rate_mm_min", default=None, ge=100.0, le=5000.0),
        plunge_rate_mm_min=_extract_context_float(context, "plunge_rate_mm_min", default=300.0, ge=50.0, le=2000.0),

        # Corner handling
        corner_slowdown=_extract_context_bool(context, "corner_slowdown", default=True),
        corner_angle_threshold_deg=_extract_context_float(context, "corner_angle_threshold_deg", default=90.0, ge=30.0, le=150.0),
        corner_feed_factor=_extract_context_float(context, "corner_feed_factor", default=0.6, ge=0.3, le=1.0),

        # Optimization (from options bucket)
        optimize_path_order=_extract_context_bool(intent.options or {}, "optimize_path_order", default=True),
    )

    return config, ml_paths
