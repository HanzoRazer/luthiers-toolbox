"""
CAM Intent Normalization Helper (H7.1.1)

Provides non-breaking normalization and validation for CamIntentV1 payloads:
- Units conversion (inch <-> mm)
- Type coercion for numeric fields
- Soft validation with issue reporting
- Optional strict mode for enterprise endpoints
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.rmos.cam.schemas_intent import CamIntentV1, CamModeV1, CamUnitsV1


@dataclass(frozen=True)
class CamIntentIssue:
    """
    A non-fatal issue discovered during normalization/validation.
    """

    code: str
    message: str
    path: str = ""


class CamIntentValidationError(ValueError):
    """
    Fatal validation error for CAM intents (should become 422 at HTTP boundary).
    """

    def __init__(self, message: str, *, issues: Optional[List[CamIntentIssue]] = None):
        super().__init__(message)
        self.issues = issues or []


def _as_float(v: Any, *, path: str, issues: List[CamIntentIssue]) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        issues.append(CamIntentIssue(code="type_error", message=f"Expected number at {path}", path=path))
        return None


def _as_int(v: Any, *, path: str, issues: List[CamIntentIssue]) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        issues.append(CamIntentIssue(code="type_error", message=f"Expected integer at {path}", path=path))
        return None


def _ensure_dict(value: Any, *, field: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    raise CamIntentValidationError(f"{field} must be an object/dict")


def _convert_inch_to_mm(x: float) -> float:
    return x * 25.4


def _convert_mm_to_inch(x: float) -> float:
    return x / 25.4


def _convert_length_fields_in_place(
    d: Dict[str, Any],
    *,
    from_units: CamUnitsV1,
    to_units: CamUnitsV1,
    length_keys: Tuple[str, ...],
    prefix_path: str,
    issues: List[CamIntentIssue],
) -> None:
    """
    Convert numeric scalar fields in-place if present and coercible.
    Only touches keys listed in `length_keys`.
    """
    if from_units == to_units:
        return

    for k in length_keys:
        if k not in d:
            continue
        path = f"{prefix_path}.{k}" if prefix_path else k
        v = _as_float(d.get(k), path=path, issues=issues)
        if v is None:
            continue
        if from_units == CamUnitsV1.INCH and to_units == CamUnitsV1.MM:
            d[k] = _convert_inch_to_mm(v)
        elif from_units == CamUnitsV1.MM and to_units == CamUnitsV1.INCH:
            d[k] = _convert_mm_to_inch(v)


def _normalize_router_3axis_design(
    design: Dict[str, Any],
    *,
    units_in: CamUnitsV1,
    units_out: CamUnitsV1,
    issues: List[CamIntentIssue],
) -> Dict[str, Any]:
    """
    Minimal, non-breaking normalization for router_3axis intents.

    Expectations (soft):
      - design.geometry exists and is a dict
      - if geometry.type == "polyline", points is list[[x,y],...]
      - numeric depth fields are coerced when possible
    """
    out = dict(design)

    geom = out.get("geometry")
    if geom is None:
        issues.append(
            CamIntentIssue(
                code="missing_field",
                message="router_3axis design should include `geometry` (object).",
                path="design.geometry",
            )
        )
        return out
    if not isinstance(geom, dict):
        raise CamIntentValidationError("design.geometry must be an object/dict")

    # Convert common length-like keys (if present)
    _convert_length_fields_in_place(
        out,
        from_units=units_in,
        to_units=units_out,
        length_keys=("depth_mm", "safe_z_mm", "stepdown_mm", "stock_thickness_mm"),
        prefix_path="design",
        issues=issues,
    )

    # Also convert geometry keys if present
    _convert_length_fields_in_place(
        geom,
        from_units=units_in,
        to_units=units_out,
        length_keys=("radius_mm",),
        prefix_path="design.geometry",
        issues=issues,
    )

    gtype = (geom.get("type") or "").lower()
    if gtype == "polyline":
        pts = geom.get("points")
        if pts is None:
            issues.append(
                CamIntentIssue(
                    code="missing_field",
                    message="polyline geometry should include `points`.",
                    path="design.geometry.points",
                )
            )
        elif not isinstance(pts, list):
            raise CamIntentValidationError("design.geometry.points must be a list")
        else:
            # convert points if numeric
            new_pts = []
            for i, p in enumerate(pts):
                if not (isinstance(p, (list, tuple)) and len(p) == 2):
                    issues.append(
                        CamIntentIssue(
                            code="shape_error",
                            message=f"point {i} must be [x,y]",
                            path=f"design.geometry.points[{i}]",
                        )
                    )
                    continue
                x = _as_float(p[0], path=f"design.geometry.points[{i}][0]", issues=issues)
                y = _as_float(p[1], path=f"design.geometry.points[{i}][1]", issues=issues)
                if x is None or y is None:
                    continue
                if units_in != units_out:
                    if units_in == CamUnitsV1.INCH and units_out == CamUnitsV1.MM:
                        x, y = _convert_inch_to_mm(x), _convert_inch_to_mm(y)
                    elif units_in == CamUnitsV1.MM and units_out == CamUnitsV1.INCH:
                        x, y = _convert_mm_to_inch(x), _convert_mm_to_inch(y)
                new_pts.append([x, y])
            geom["points"] = new_pts

    out["geometry"] = geom
    return out


def _normalize_saw_design(
    design: Dict[str, Any],
    *,
    units_in: CamUnitsV1,
    units_out: CamUnitsV1,
    issues: List[CamIntentIssue],
) -> Dict[str, Any]:
    """
    Minimal, non-breaking normalization for saw intents.

    Soft expectations:
      - `kerf_width_mm` and `stock_thickness_mm` should be present (or derivable)
      - `cuts` list should exist for multi-cut designs (optional)
    """
    out = dict(design)

    # Convert common saw lengths if present
    _convert_length_fields_in_place(
        out,
        from_units=units_in,
        to_units=units_out,
        length_keys=("kerf_width_mm", "stock_thickness_mm", "cut_depth_mm", "cut_length_mm"),
        prefix_path="design",
        issues=issues,
    )

    if "kerf_width_mm" not in out:
        issues.append(
            CamIntentIssue(
                code="missing_field",
                message="saw design should include `kerf_width_mm` (or provide via context/options).",
                path="design.kerf_width_mm",
            )
        )
    if "stock_thickness_mm" not in out:
        issues.append(
            CamIntentIssue(
                code="missing_field",
                message="saw design should include `stock_thickness_mm` (or provide via context/options).",
                path="design.stock_thickness_mm",
            )
        )

    # Normalize cuts list (if present)
    cuts = out.get("cuts")
    if cuts is not None:
        if not isinstance(cuts, list):
            raise CamIntentValidationError("design.cuts must be a list")
        for i, c in enumerate(cuts):
            if not isinstance(c, dict):
                issues.append(
                    CamIntentIssue(
                        code="type_error",
                        message="each cut must be an object/dict",
                        path=f"design.cuts[{i}]",
                    )
                )
                continue
            _convert_length_fields_in_place(
                c,
                from_units=units_in,
                to_units=units_out,
                length_keys=("length_mm", "depth_mm", "offset_mm"),
                prefix_path=f"design.cuts[{i}]",
                issues=issues,
            )

    return out


def normalize_cam_intent_v1(
    intent: CamIntentV1,
    *,
    normalize_to_units: CamUnitsV1 = CamUnitsV1.MM,
    strict: bool = False,
) -> Tuple[CamIntentV1, List[CamIntentIssue]]:
    """
    Normalize a CamIntentV1 into a canonical form (defaults to mm).

    - Converts known length fields from inches<->mm when possible
    - Coerces common numeric fields
    - Emits non-fatal issues for missing "recommended" keys

    If `strict=True`, missing recommended keys become fatal.
    """
    issues: List[CamIntentIssue] = []

    design = _ensure_dict(intent.design, field="design")
    context = _ensure_dict(intent.context, field="context")
    options = _ensure_dict(intent.options, field="options")

    units_in = intent.units
    units_out = normalize_to_units

    # Mode-specific normalization
    if intent.mode == CamModeV1.ROUTER_3AXIS:
        norm_design = _normalize_router_3axis_design(design, units_in=units_in, units_out=units_out, issues=issues)
    elif intent.mode == CamModeV1.SAW:
        norm_design = _normalize_saw_design(design, units_in=units_in, units_out=units_out, issues=issues)
    else:
        # Should not happen because enum, but keep safe for forward compat
        raise CamIntentValidationError(f"Unsupported mode: {intent.mode}")

    # Normalize a couple of common context keys (feed/spindle) without committing to schema.
    # These are "best effort" and do not error if absent.
    # (Keeps this non-breaking while still getting useful canonicalization.)
    _ = _as_float(context.get("feed_rate_mm_min") or context.get("feed_rate"), path="context.feed_rate", issues=issues)
    _ = _as_int(context.get("spindle_rpm") or context.get("max_rpm"), path="context.spindle_rpm", issues=issues)

    if strict:
        fatal_missing = [i for i in issues if i.code == "missing_field"]
        if fatal_missing:
            raise CamIntentValidationError("CAM intent failed strict validation", issues=fatal_missing)

    normalized = CamIntentV1(
        intent_id=intent.intent_id,
        mode=intent.mode,
        units=units_out,
        tool_id=intent.tool_id,
        material_id=intent.material_id,
        machine_id=intent.machine_id,
        design=norm_design,
        context=context,
        options=options,
        requested_by=intent.requested_by,
        created_at_utc=intent.created_at_utc,
    )
    return normalized, issues
