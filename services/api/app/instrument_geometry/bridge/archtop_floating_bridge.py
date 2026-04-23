"""
Archtop floating bridge geometry (Benedetto-style).

Canonical implementation for archtop floating bridge in this codebase — use this
module (and its API routes under ``/floating-bridge/archtop/``) rather than any
duplicate helpers.

Sagitta-based arch radius, foot profile mating to arched top, post holes,
saddle slots with plain/wound compensation, and optional DXF (R2000, 5 layers).
"""

from __future__ import annotations

import io
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple

# ─── Defaults (Benedetto 17" class) ────────────────────────────────────────────


@dataclass(frozen=True)
class Benedetto17Defaults:
    """Nominal Benedetto-style floating bridge dimensions (mm).

    Floating bridge Rev 2 (canonical): base length 155, foot 4.5, saddle radius 381,
    M4 posts, base thickness 10.5, saddle blank 8.
    """

    base_length_mm: float = 155.0
    base_width_mm: float = 30.0
    foot_thickness_mm: float = 4.5
    saddle_radius_mm: float = 381.0
    base_thickness_mm: float = 10.5
    saddle_blank_mm: float = 8.0
    post_spacing_mm: float = 74.6
    post_hole_diameter_mm: float = 4.2  # M4 clearance
    e_to_e_string_spacing_mm: float = 52.0
    nominal_top_span_mm: float = 3048.0  # ~10' — prefer measured span+sagitta


BENEDETTO_17 = Benedetto17Defaults()


# ─── Arch radius (sagitta) ───────────────────────────────────────────────────


def resolve_arch_radius_from_sagitta(span_mm: float, sagitta_mm: float) -> float:
    """
    Circle radius from chord span ``s`` and sagitta ``h`` (rise from chord to arc).

    R = (s² / 8h) + (h/2)

    Prefer measured span and sagitta on the actual top over nominal 3048 mm.
    """
    if span_mm <= 0 or sagitta_mm <= 0:
        raise ValueError("span_mm and sagitta_mm must be positive")
    return (span_mm**2) / (8.0 * sagitta_mm) + (sagitta_mm / 2.0)


# ─── Foot / post / saddle ────────────────────────────────────────────────────


@dataclass
class FootArchGeometry:
    """Foot underside arc mating to a cylindrical top arch (local bridge coords)."""

    arch_radius_mm: float
    chord_length_mm: float
    sagitta_mm: float
    center_xy: Tuple[float, float]
    notes: str = ""


def compute_foot_arch_geometry(
    arch_radius_mm: float,
    chord_length_mm: float,
) -> FootArchGeometry:
    """
    Foot contact arc: chord = bridge footprint length along strings (``chord_length_mm``).

    Sagitta from chord to arc (concave foot): h = R - sqrt(R² - (c/2)²).
    """
    r = arch_radius_mm
    c = chord_length_mm
    if r <= 0 or c <= 0:
        raise ValueError("arch_radius_mm and chord_length_mm must be positive")
    if c > 2 * r:
        raise ValueError("Chord exceeds diameter for given arch radius")

    half = c / 2.0
    sagitta = r - math.sqrt(max(0.0, r * r - half * half))
    # Center of circle below chord (Y down negative): cy = -(R - sagitta) = -sqrt(R² - (c/2)²)
    cy = -math.sqrt(r * r - half * half)
    return FootArchGeometry(
        arch_radius_mm=r,
        chord_length_mm=c,
        sagitta_mm=sagitta,
        center_xy=(0.0, cy),
        notes="Foot bottom assumed cylindrical section matching top arch radius.",
    )


@dataclass
class PostHolePlacement:
    """Two thumbwheel / post holes in bridge coordinates (X along strings, Y across)."""

    positions_mm: List[Tuple[float, float]]
    diameter_mm: float
    spacing_mm: float


def compute_post_hole_positions(
    post_spacing_mm: float,
    *,
    center_x: float = 0.0,
    center_y: float = 0.0,
) -> PostHolePlacement:
    """Symmetric posts on centerline: ±spacing/2 on X."""
    half = post_spacing_mm / 2.0
    return PostHolePlacement(
        positions_mm=[(center_x - half, center_y), (center_x + half, center_y)],
        diameter_mm=BENEDETTO_17.post_hole_diameter_mm,
        spacing_mm=post_spacing_mm,
    )


@dataclass
class SaddleSlotSpec:
    """Per-string saddle slot with compensation depth (plain vs wound)."""

    string_index: int  # 1 = high E
    x_mm: float
    compensation_depth_mm: float
    label: str


def compute_saddle_slot(
    e_to_e_spacing_mm: float,
    saddle_radius_mm: float,
    *,
    plain_comp_mm: float = 1.5,
    wound_comp_mm: float = 2.5,
    string_count: int = 6,
) -> List[SaddleSlotSpec]:
    """
    String positions along a circular saddle arc; compensation depth by string type.

    Strings 1–3 (high E, B, G): plain; 4–6 (D, A, low E): wound — typical archtop set.
    """
    if string_count < 1:
        return []
    xs: List[float] = []
    half = e_to_e_spacing_mm / 2.0
    if string_count == 1:
        xs = [0.0]
    else:
        step = e_to_e_spacing_mm / (string_count - 1)
        xs = [-half + i * step for i in range(string_count)]

    labels = ["E", "B", "G", "D", "A", "E"]
    out: List[SaddleSlotSpec] = []
    for i, x in enumerate(xs):
        idx = i + 1
        is_wound = idx >= 4
        comp = wound_comp_mm if is_wound else plain_comp_mm
        lab = labels[i] if i < len(labels) else str(idx)
        out.append(
            SaddleSlotSpec(
                string_index=idx,
                x_mm=x,
                compensation_depth_mm=comp,
                label=lab + (" wound" if is_wound else " plain"),
            )
        )
    _ = saddle_radius_mm  # reserved for arc-length slot layout / CNC
    return out


# ─── DXF export ──────────────────────────────────────────────────────────────

LAYERS = (
    "BRIDGE_OUTLINE",
    "FOOT_PROFILE",
    "SADDLE_SLOT",
    "POST_HOLES",
    "CENTERLINE",
)

_LAYER_COLOR = {
    "BRIDGE_OUTLINE": 7,
    "FOOT_PROFILE": 1,
    "SADDLE_SLOT": 3,
    "POST_HOLES": 4,
    "CENTERLINE": 5,
}


def generate_dxf(
    *,
    arch_radius_mm: float,
    base_length_mm: float = BENEDETTO_17.base_length_mm,
    base_width_mm: float = BENEDETTO_17.base_width_mm,
    foot_thickness_mm: float = BENEDETTO_17.foot_thickness_mm,
    saddle_radius_mm: float = BENEDETTO_17.saddle_radius_mm,
    post_spacing_mm: float = BENEDETTO_17.post_spacing_mm,
    post_hole_diameter_mm: float = BENEDETTO_17.post_hole_diameter_mm,
    e_to_e_string_spacing_mm: float = BENEDETTO_17.e_to_e_string_spacing_mm,
) -> bytes:
    """
    Generate DXF R12 with five layers (bridge plan, top view).

    Migrated to dxf_writer.py (Sprint 3) - R12 LINE-only output.
    """
    from ...cam.dxf_writer import DxfWriter, LayerDef

    layers = [LayerDef(name, color=_LAYER_COLOR[name]) for name in LAYERS]
    writer = DxfWriter(layers=layers)

    hx = base_length_mm / 2.0
    hy = base_width_mm / 2.0
    # BRIDGE_OUTLINE: rectangle centered at origin
    pts = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    writer.add_polyline("BRIDGE_OUTLINE", pts, closed=True)

    foot = compute_foot_arch_geometry(arch_radius_mm, base_length_mm)
    cx, cy = foot.center_xy
    r = arch_radius_mm
    # FOOT_PROFILE: chord along X at y=0, arc below (concave foot / top arch)
    a1 = math.degrees(math.atan2(0.0 - cy, -hx - cx))
    a2 = math.degrees(math.atan2(0.0 - cy, hx - cx))
    writer.add_arc("FOOT_PROFILE", (cx, cy), r, a1, a2)

    # CENTERLINE
    writer.add_line("CENTERLINE", (-hx - 10, 0), (hx + 10, 0))

    # POST_HOLES
    posts = compute_post_hole_positions(post_spacing_mm)
    r_h = post_hole_diameter_mm / 2.0
    for px, py in posts.positions_mm:
        writer.add_circle("POST_HOLES", (px, py), r_h)

    # SADDLE_SLOT: short line segments at front edge (y = +hy)
    slots = compute_saddle_slot(e_to_e_string_spacing_mm, saddle_radius_mm)
    for s in slots:
        x0 = s.x_mm
        writer.add_line("SADDLE_SLOT", (x0, hy - 2), (x0, hy + 2))

    return writer.to_bytes()


@dataclass
class ArchtopFloatingBridgeReport:
    """Full geometry report for API / JSON."""

    arch_radius_mm: float
    span_mm: float
    sagitta_mm: float
    foot: Dict[str, Any]
    posts: Dict[str, Any]
    saddle_slots: List[Dict[str, Any]]
    defaults: Dict[str, Any] = field(default_factory=lambda: asdict(BENEDETTO_17))


def build_archtop_bridge_report(
    *,
    span_mm: float,
    sagitta_mm: float,
    base_length_mm: float = BENEDETTO_17.base_length_mm,
    base_width_mm: float = BENEDETTO_17.base_width_mm,
    e_to_e_string_spacing_mm: float = BENEDETTO_17.e_to_e_string_spacing_mm,
    post_spacing_mm: float = BENEDETTO_17.post_spacing_mm,
    saddle_radius_mm: float = BENEDETTO_17.saddle_radius_mm,
) -> ArchtopFloatingBridgeReport:
    """Resolve R from measured span+sagitta and compute foot, posts, saddle slots."""
    r_arch = resolve_arch_radius_from_sagitta(span_mm, sagitta_mm)
    foot = compute_foot_arch_geometry(r_arch, base_length_mm)
    posts = compute_post_hole_positions(post_spacing_mm)
    slots = compute_saddle_slot(e_to_e_string_spacing_mm, saddle_radius_mm)
    return ArchtopFloatingBridgeReport(
        arch_radius_mm=r_arch,
        span_mm=span_mm,
        sagitta_mm=sagitta_mm,
        foot=asdict(foot),
        posts={
            "positions_mm": posts.positions_mm,
            "diameter_mm": posts.diameter_mm,
            "spacing_mm": posts.spacing_mm,
        },
        saddle_slots=[asdict(s) for s in slots],
        defaults=asdict(BENEDETTO_17),
    )


def archtop_report_to_dict(rep: ArchtopFloatingBridgeReport) -> Dict[str, Any]:
    d = asdict(rep)
    return d
