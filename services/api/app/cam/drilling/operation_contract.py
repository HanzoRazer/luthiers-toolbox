"""Canonical drilling manufacturing-intent contract.

HTTP lanes (modal / intent / pattern) remain separate request schemas.
This module describes manufacturing semantics that
``compute_drilling_feasibility`` can evaluate without fabrication.

No RMOS dependency. No SafetyPolicy. No production gating.

Datum (intent PeckDrill proof): work-surface Z=0 in the same absolute
frame as target Z; physical depth = surface_z_mm - target_z_mm.
Hole.z / DrillParams.z is a G-code target coordinate, not depth.
``tool`` is a tool number, never diameter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

INCH_TO_MM = 25.4
_FEED_EPS = 1e-9
_MM_ALIASES = frozenset({"mm", "millimeter", "millimetre", "millimeters", "millimetres"})
_INCH_ALIASES = frozenset({"in", "inch", "inches"})

# Generator-written R-plane / Q defaults on modal and pattern lanes.
MODAL_DEFAULT_R_CLEAR = 5.0
MODAL_DEFAULT_PECK_Q = 1.0
INTENT_SURFACE_Z_MM = 0.0


class IncompleteDrillingContractError(ValueError):
    """Spec is missing semantics the evaluator requires."""

    def __init__(self, reasons: Sequence[str]) -> None:
        self.reasons = tuple(reasons)
        super().__init__("incomplete drilling contract: " + ", ".join(self.reasons))


class HeterogeneousFeedError(ValueError):
    """Per-hole feeds are not invariant; evaluator feed is singular."""


@dataclass(frozen=True)
class DrillingHoleSpec:
    """One hole in manufacturing semantics (mm)."""

    x_mm: float
    y_mm: float
    target_z_mm: Optional[float]
    depth_mm: Optional[float]
    feed_mm_min: Optional[float]


@dataclass(frozen=True)
class DrillingOperationSpec:
    """Manufacturing intent for one drilling operation.

    Always stored in millimetres after explicit normalization.
    ``incomplete_reasons`` lists why the evaluator adapter must refuse.
    """

    units: str
    holes: tuple[DrillingHoleSpec, ...]
    hole_depth_mm: Optional[float]
    hole_diameter_mm: Optional[float]
    surface_z_mm: Optional[float]
    tool_number: Optional[int]
    spindle_rpm: Optional[float]
    peck_drilling: bool
    peck_depth_mm: Optional[float]
    safe_z_mm: Optional[float]
    retract_z_mm: Optional[float]
    incomplete_reasons: tuple[str, ...]

    def is_complete_for_feasibility(self) -> bool:
        return not self.incomplete_reasons


def canonical_length_units(units: Optional[str]) -> Optional[str]:
    """Return ``mm`` or ``in``, or None if the units string is unsupported."""
    token = (units or "mm").strip().lower()
    if token in _MM_ALIASES:
        return "mm"
    if token in _INCH_ALIASES:
        return "in"
    return None


def length_to_mm(value: float, units: Optional[str]) -> Optional[float]:
    """Explicit length normalization. None if units are unsupported."""
    kind = canonical_length_units(units)
    if kind is None:
        return None
    if kind == "mm":
        return float(value)
    return float(value) * INCH_TO_MM


def feed_to_mm_min(value: float, units: Optional[str]) -> Optional[float]:
    """Feed uses the same length-unit scale (mm/min or in/min)."""
    return length_to_mm(value, units)


def physical_depth_mm(*, surface_z_mm: float, target_z_mm: float) -> float:
    """Physical hole depth from an explicit work-surface datum to target Z.

    Intent PeckDrill writes ``Z{-depth}`` with surface Z=0, so
    depth = surface_z - target_z. Negative results are not depths.
    """
    return float(surface_z_mm) - float(target_z_mm)


def peck_drilling_from_cycle(cycle: Optional[str]) -> bool:
    """G83 is peck; G81 (and the modal unknown-cycle fallback) is not."""
    return (cycle or "G81").upper().strip() == "G83"


def invariant_feed_mm_min(feeds: Sequence[float]) -> float:
    """Require a single feed. Do not collapse heterogeneous values."""
    if not feeds:
        raise IncompleteDrillingContractError(("missing_feed",))
    first = float(feeds[0])
    if any(abs(float(item) - first) > _FEED_EPS for item in feeds[1:]):
        raise HeterogeneousFeedError(
            "per-hole feeds are heterogeneous; evaluator feed_rate_mm_min is singular"
        )
    return first


_POSITIVE_FIELDS = (
    ("hole_diameter_mm", "missing_hole_diameter_mm", "invalid_hole_diameter_mm"),
    ("hole_depth_mm", "missing_hole_depth_mm", "invalid_hole_depth_mm"),
)
_PRESENT_FIELDS = (
    ("surface_z_mm", "missing_surface_z_mm"),
    ("spindle_rpm", "missing_spindle_rpm"),
    ("safe_z_mm", "missing_safe_z_mm"),
    ("retract_z_mm", "missing_retract_z_mm"),
)


def _positive_reasons(fields: dict) -> list[str]:
    reasons: list[str] = []
    for key, missing, invalid in _POSITIVE_FIELDS:
        value = fields[key]
        if value is None:
            reasons.append(missing)
        elif value <= 0:
            reasons.append(invalid)
    return reasons


def _present_reasons(fields: dict) -> list[str]:
    return [label for key, label in _PRESENT_FIELDS if fields[key] is None]


def _feed_reasons(holes: Sequence[DrillingHoleSpec]) -> list[str]:
    feeds = [h.feed_mm_min for h in holes]
    if any(item is None for item in feeds):
        return ["missing_feed"]
    if len(feeds) <= 1:
        return []
    try:
        invariant_feed_mm_min([float(item) for item in feeds])
    except HeterogeneousFeedError:
        return ["heterogeneous_feed"]
    return []


def _reason_list(spec_fields: dict) -> tuple[str, ...]:
    reasons: list[str] = []
    if spec_fields["units"] != "mm":
        reasons.append("unsupported_units")
    holes: tuple[DrillingHoleSpec, ...] = spec_fields["holes"]
    if not holes:
        reasons.append("missing_holes")
    reasons.extend(_positive_reasons(spec_fields))
    reasons.extend(_present_reasons(spec_fields))
    if spec_fields["peck_drilling"] and spec_fields["peck_depth_mm"] is None:
        reasons.append("missing_peck_depth_mm")
    reasons.extend(_feed_reasons(holes))
    return tuple(reasons)


def _build_spec(**fields: object) -> DrillingOperationSpec:
    reasons = _reason_list(fields)  # type: ignore[arg-type]
    return DrillingOperationSpec(
        units=str(fields["units"]),
        holes=tuple(fields["holes"]),  # type: ignore[arg-type]
        hole_depth_mm=fields["hole_depth_mm"],  # type: ignore[arg-type]
        hole_diameter_mm=fields["hole_diameter_mm"],  # type: ignore[arg-type]
        surface_z_mm=fields["surface_z_mm"],  # type: ignore[arg-type]
        tool_number=fields["tool_number"],  # type: ignore[arg-type]
        spindle_rpm=fields["spindle_rpm"],  # type: ignore[arg-type]
        peck_drilling=bool(fields["peck_drilling"]),
        peck_depth_mm=fields["peck_depth_mm"],  # type: ignore[arg-type]
        safe_z_mm=fields["safe_z_mm"],  # type: ignore[arg-type]
        retract_z_mm=fields["retract_z_mm"],  # type: ignore[arg-type]
        incomplete_reasons=reasons,
    )


def feasibility_kwargs(spec: DrillingOperationSpec) -> dict:
    """Map a complete spec onto ``compute_drilling_feasibility`` kwargs.

    Raises rather than fabricating missing diameter, depth, RPM, or feed.
    """
    if spec.incomplete_reasons:
        if "heterogeneous_feed" in spec.incomplete_reasons:
            raise HeterogeneousFeedError(
                "per-hole feeds are heterogeneous; evaluator feed_rate_mm_min is singular"
            )
        raise IncompleteDrillingContractError(spec.incomplete_reasons)
    feeds = [float(h.feed_mm_min) for h in spec.holes if h.feed_mm_min is not None]
    peck_depth = spec.peck_depth_mm if spec.peck_depth_mm is not None else 0.0
    return {
        "hole_depth_mm": float(spec.hole_depth_mm),
        "hole_diameter_mm": float(spec.hole_diameter_mm),
        "peck_drilling": spec.peck_drilling,
        "peck_depth_mm": float(peck_depth),
        "hole_count": len(spec.holes),
        "feed_rate_mm_min": invariant_feed_mm_min(feeds),
        "spindle_rpm": float(spec.spindle_rpm),
        "safe_z_mm": float(spec.safe_z_mm),
        "retract_z_mm": float(spec.retract_z_mm),
    }


def _or_raw(converted: Optional[float], raw: float) -> float:
    if converted is None:
        return float(raw)
    return converted


def _depth_from_datum(
    target_z_mm: Optional[float],
    surface_z: Optional[float],
    units: str,
) -> Optional[float]:
    if surface_z is None or target_z_mm is None:
        return None
    surface_mm = length_to_mm(surface_z, units)
    if surface_mm is None:
        return None
    candidate = physical_depth_mm(surface_z_mm=surface_mm, target_z_mm=target_z_mm)
    if candidate <= 0:
        return None
    return candidate


def _modal_hole(
    x: float,
    y: float,
    z: float,
    feed: float,
    units: str,
    surface_z: Optional[float],
) -> DrillingHoleSpec:
    z_mm = length_to_mm(z, units)
    return DrillingHoleSpec(
        x_mm=_or_raw(length_to_mm(x, units), x),
        y_mm=_or_raw(length_to_mm(y, units), y),
        target_z_mm=z_mm,
        depth_mm=_depth_from_datum(z_mm, surface_z, units),
        feed_mm_min=feed_to_mm_min(feed, units),
    )


def _uniform_depth(depths: Sequence[Optional[float]]) -> Optional[float]:
    if not depths or any(item is None for item in depths):
        return None
    first = depths[0]
    if any(item != first for item in depths[1:]):
        return None
    return first


def _peck_fields(cycle: str, peck_q: Optional[float], units: str) -> tuple[bool, Optional[float]]:
    peck = peck_drilling_from_cycle(cycle)
    if not peck:
        return False, 0.0
    quantity = peck_q if peck_q is not None else MODAL_DEFAULT_PECK_Q
    return True, length_to_mm(quantity, units)


def spec_from_modal(
    *,
    holes: Sequence[tuple[float, float, float, float]],
    r_clear: Optional[float],
    peck_q: Optional[float],
    cycle: str,
    safe_z: float,
    units: str,
    rpm: Optional[float],
    tool: Optional[int],
    hole_diameter: Optional[float] = None,
    surface_z: Optional[float] = None,
) -> DrillingOperationSpec:
    """Map modal DrillReq fields. Never treats z as depth or tool as diameter.

    ``r_clear`` is the canned-cycle R-plane (same word PeckDrill writes as
    ``retract_z_mm``). Generator defaults (R=5, G83 Q=1) are the values
    actually written into G-code, not invented evaluator defaults.
    """
    kind = canonical_length_units(units)
    stored_units = "mm" if kind is not None else (units or "unknown")
    hole_specs = tuple(
        _modal_hole(x, y, z, feed, units, surface_z) for x, y, z, feed in holes
    )
    peck, peck_depth = _peck_fields(cycle, peck_q, units)
    r_value = MODAL_DEFAULT_R_CLEAR if r_clear is None else r_clear
    diameter = None if hole_diameter is None else length_to_mm(hole_diameter, units)
    surface_mm = None if surface_z is None else length_to_mm(surface_z, units)
    rpm_val = None if rpm is None else float(rpm)
    return _build_spec(
        units=stored_units,
        holes=hole_specs,
        hole_depth_mm=_uniform_depth([h.depth_mm for h in hole_specs]),
        hole_diameter_mm=diameter,
        surface_z_mm=surface_mm,
        tool_number=tool,
        spindle_rpm=rpm_val,
        peck_drilling=peck,
        peck_depth_mm=peck_depth,
        safe_z_mm=length_to_mm(safe_z, units),
        retract_z_mm=length_to_mm(r_value, units),
    )


def spec_from_pattern(
    *,
    points_xy: Sequence[tuple[float, float]],
    z: float,
    feed: float,
    cycle: str,
    r_clear: Optional[float],
    peck_q: Optional[float],
    safe_z: float,
    units: str,
    rpm: Optional[float],
    tool: Optional[int],
    hole_diameter: Optional[float] = None,
    surface_z: Optional[float] = None,
) -> DrillingOperationSpec:
    """Map pattern DrillParams. Same Z/R semantics as modal. Feed is singular."""
    holes = [(x, y, z, feed) for x, y in points_xy]
    return spec_from_modal(
        holes=holes,
        r_clear=r_clear,
        peck_q=peck_q,
        cycle=cycle,
        safe_z=safe_z,
        units=units,
        rpm=rpm,
        tool=tool,
        hole_diameter=hole_diameter,
        surface_z=surface_z,
    )


def spec_from_intent(
    *,
    holes_xy: Sequence[tuple[float, float]],
    per_hole_depth_mm: Sequence[Optional[float]],
    hole_depth_mm: float,
    hole_diameter_mm: float,
    peck_drilling: bool,
    peck_depth_mm: float,
    feed_rate_mm_min: float,
    spindle_rpm: float,
    safe_z_mm: float,
    retract_z_mm: float,
) -> DrillingOperationSpec:
    """Map post-adapter intent values. Evaluator depth is the design default.

    Surface datum is Z=0 (PeckDrill ``Z = -depth``). Per-hole ``depth_mm``
    overrides are recorded on holes; they do not replace design depth in
    the evaluator mapping (existing intent-router rule).
    """
    hole_specs = []
    for idx, (x, y) in enumerate(holes_xy):
        override = per_hole_depth_mm[idx] if idx < len(per_hole_depth_mm) else None
        physical = float(override) if override is not None else float(hole_depth_mm)
        hole_specs.append(
            DrillingHoleSpec(
                x_mm=float(x),
                y_mm=float(y),
                target_z_mm=-physical,
                depth_mm=physical,
                feed_mm_min=float(feed_rate_mm_min),
            )
        )
    return _build_spec(
        units="mm",
        holes=tuple(hole_specs),
        hole_depth_mm=float(hole_depth_mm),
        hole_diameter_mm=float(hole_diameter_mm),
        surface_z_mm=INTENT_SURFACE_Z_MM,
        tool_number=None,
        spindle_rpm=float(spindle_rpm),
        peck_drilling=bool(peck_drilling),
        peck_depth_mm=float(peck_depth_mm),
        safe_z_mm=float(safe_z_mm),
        retract_z_mm=float(retract_z_mm),
    )
