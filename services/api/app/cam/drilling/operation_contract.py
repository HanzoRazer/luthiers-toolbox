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


def _reason_list(spec_fields: dict) -> tuple[str, ...]:
    reasons: list[str] = []
    if spec_fields["units"] != "mm":
        reasons.append("unsupported_units")
    holes: tuple[DrillingHoleSpec, ...] = spec_fields["holes"]
    if not holes:
        reasons.append("missing_holes")
    if spec_fields["hole_diameter_mm"] is None:
        reasons.append("missing_hole_diameter_mm")
    elif spec_fields["hole_diameter_mm"] <= 0:
        reasons.append("invalid_hole_diameter_mm")
    if spec_fields["hole_depth_mm"] is None:
        reasons.append("missing_hole_depth_mm")
    elif spec_fields["hole_depth_mm"] <= 0:
        reasons.append("invalid_hole_depth_mm")
    if spec_fields["surface_z_mm"] is None:
        reasons.append("missing_surface_z_mm")
    if spec_fields["spindle_rpm"] is None:
        reasons.append("missing_spindle_rpm")
    if spec_fields["safe_z_mm"] is None:
        reasons.append("missing_safe_z_mm")
    if spec_fields["retract_z_mm"] is None:
        reasons.append("missing_retract_z_mm")
    if spec_fields["peck_drilling"] and spec_fields["peck_depth_mm"] is None:
        reasons.append("missing_peck_depth_mm")
    feeds = [h.feed_mm_min for h in holes]
    if any(f is None for f in feeds):
        reasons.append("missing_feed")
    elif len(feeds) > 1:
        try:
            invariant_feed_mm_min([float(f) for f in feeds if f is not None])
        except HeterogeneousFeedError:
            reasons.append("heterogeneous_feed")
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
    hole_specs = []
    depths: list[Optional[float]] = []
    for x, y, z, feed in holes:
        x_mm = length_to_mm(x, units)
        y_mm = length_to_mm(y, units)
        z_mm = length_to_mm(z, units)
        feed_mm = feed_to_mm_min(feed, units)
        depth = None
        if surface_z is not None and z_mm is not None:
            surface_mm = length_to_mm(surface_z, units)
            if surface_mm is not None:
                candidate = physical_depth_mm(surface_z_mm=surface_mm, target_z_mm=z_mm)
                if candidate > 0:
                    depth = candidate
        depths.append(depth)
        hole_specs.append(
            DrillingHoleSpec(
                x_mm=x_mm if x_mm is not None else float(x),
                y_mm=y_mm if y_mm is not None else float(y),
                target_z_mm=z_mm,
                depth_mm=depth,
                feed_mm_min=feed_mm,
            )
        )
    diameter = length_to_mm(hole_diameter, units) if hole_diameter is not None else None
    surface_mm = length_to_mm(surface_z, units) if surface_z is not None else None
    r_value = r_clear if r_clear is not None else MODAL_DEFAULT_R_CLEAR
    peck = peck_drilling_from_cycle(cycle)
    peck_depth = None
    if peck:
        peck_depth = length_to_mm(
            peck_q if peck_q is not None else MODAL_DEFAULT_PECK_Q, units
        )
    else:
        peck_depth = 0.0
    op_depth = depths[0] if depths and all(d == depths[0] for d in depths) else None
    if depths and any(d is None for d in depths):
        op_depth = None
    return _build_spec(
        units=stored_units,
        holes=tuple(hole_specs),
        hole_depth_mm=op_depth,
        hole_diameter_mm=diameter,
        surface_z_mm=surface_mm,
        tool_number=tool,
        spindle_rpm=float(rpm) if rpm is not None else None,
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
