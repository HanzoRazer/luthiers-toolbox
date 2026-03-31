"""
soundhole_spiral.py
Logarithmic spiral soundhole geometry engine for the Production Shop.

Physics:
  Centerline: r(θ) = r0 * exp(k * θ)
  Wall offsets: ±(slot_width/2) perpendicular to tangent
  Perimeter (closed form): P = 2 * (r_end - r0) / sin(atan(1/k))
  Area (closed form):      A = slot_width * (r_end - r0) / sin(atan(1/k))
  P:A ratio:               P/A = 2 / slot_width  (independent of k, turns, size)

Coordinate system: origin at bridge centerline.
  x positive = treble side
  y positive = toward tail block
  Units: millimetres

DXF layers:
  SPIRAL_CENTERLINE   — reference only, not cut
  SPIRAL_OUTER_WALL   — CNC cut path
  SPIRAL_INNER_WALL   — CNC cut path
  BODY_REFERENCE      — body outline reference, not cut
  BRACE_KEEPOUT       — brace zone reference, not cut
"""

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass, field


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class SpiralSpec:
    """Parameters for a single logarithmic spiral soundhole."""
    center_x_mm: float        # x position of spiral center (mm)
    center_y_mm: float        # y position of spiral center (mm)
    start_radius_mm: float    # r0 — inner starting radius (mm)
    growth_rate_k: float      # k — logarithmic growth rate per radian
    turns: float              # number of full turns
    slot_width_mm: float      # width of the slot (mm)
    rotation_deg: float       # rotation offset of spiral start (degrees)
    label: str = ""           # descriptive label


@dataclass
class SpiralGeometry:
    """Computed geometry for a single spiral."""
    centerline: List[Tuple[float, float]] = field(default_factory=list)
    outer_wall: List[Tuple[float, float]] = field(default_factory=list)
    inner_wall: List[Tuple[float, float]] = field(default_factory=list)
    area_mm2: float = 0.0
    perimeter_mm: float = 0.0
    pa_ratio_mm_inv: float = 0.0
    end_radius_mm: float = 0.0
    total_length_mm: float = 0.0
    spec: Optional[SpiralSpec] = None


@dataclass
class DualSpiralSpec:
    """Full dual-spiral soundhole specification for Carlos Jumbo body."""
    upper: SpiralSpec
    lower: SpiralSpec
    body_type: str = "carlos_jumbo"
    notes: str = ""


@dataclass
class DualSpiralGeometry:
    upper: SpiralGeometry
    lower: SpiralGeometry
    total_area_mm2: float = 0.0
    round_ref_area_mm2: float = 0.0   # 4" round hole reference
    area_ratio_pct: float = 0.0


# ── Default Carlos Jumbo spec ─────────────────────────────────────────────────

def default_carlos_jumbo_spec() -> DualSpiralSpec:
    """
    Default dual-spiral specification for the Carlos Jumbo body.
    Upper: bass side, clockwise (opens toward neck).
    Lower: treble side, counterclockwise (opens toward bridge).
    Coordinates relative to bridge centerline origin.
    """
    return DualSpiralSpec(
        upper=SpiralSpec(
            center_x_mm=-88.0,
            center_y_mm=-62.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.1,
            slot_width_mm=14.0,
            rotation_deg=270.0,
            label="Upper bass-side spiral"
        ),
        lower=SpiralSpec(
            center_x_mm=78.0,
            center_y_mm=112.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.1,
            slot_width_mm=14.0,
            rotation_deg=90.0,
            label="Lower treble-side spiral"
        ),
        body_type="carlos_jumbo",
        notes="Displaced f-hole logic. Upper follows rim toward neck, lower toward bridge."
    )


# ── Geometry computation ──────────────────────────────────────────────────────

def _spiral_points(
    cx: float, cy: float,
    r0: float, k: float,
    turns: float, rot_deg: float,
    n_steps: int = 300
) -> List[Tuple[float, float]]:
    """Compute centerline points of the logarithmic spiral."""
    theta_end = turns * 2 * math.pi
    rot_rad = math.radians(rot_deg)
    pts = []
    for i in range(n_steps + 1):
        theta = i / n_steps * theta_end
        r = r0 * math.exp(k * theta)
        angle = theta + rot_rad
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts


def _spiral_walls(
    cx: float, cy: float,
    r0: float, k: float,
    turns: float, rot_deg: float,
    slot_w: float,
    n_steps: int = 300
) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """
    Compute inner and outer wall points by offsetting ±(slot_w/2)
    perpendicular to the spiral tangent at each point.
    """
    theta_end = turns * 2 * math.pi
    rot_rad = math.radians(rot_deg)
    half = slot_w / 2.0
    outer, inner = [], []

    for i in range(n_steps + 1):
        theta = i / n_steps * theta_end
        r = r0 * math.exp(k * theta)
        angle = theta + rot_rad

        # Radial direction
        rx = math.cos(angle)
        ry = math.sin(angle)

        # Tangent direction: d/dθ [r·cos(angle), r·sin(angle)]
        # = r·k·[cos,sin] + r·[-sin,cos]
        # Normalise to get unit tangent
        tx_raw = k * math.cos(angle) - math.sin(angle)
        ty_raw = k * math.sin(angle) + math.cos(angle)
        t_len = math.sqrt(tx_raw**2 + ty_raw**2)
        tx = tx_raw / t_len
        ty = ty_raw / t_len

        # Normal = rotate tangent 90°
        nx = -ty
        ny = tx

        px = cx + r * rx
        py = cy + r * ry

        outer.append((px + nx * half, py + ny * half))
        inner.append((px - nx * half, py - ny * half))

    return outer, inner


def _closed_form_stats(r0: float, k: float, turns: float, slot_w: float) -> dict:
    """
    Closed-form P, A, P:A for a logarithmic spiral slot.

    Arc length of one wall: L = (r_end - r0) / sin(atan(1/k))
    Perimeter (two walls):  P = 2 * L
    Area:                   A = slot_w * L
    P:A:                    2 / slot_w  (independent of k, turns, r0)
    """
    theta_end = turns * 2 * math.pi
    r_end = r0 * math.exp(k * theta_end)
    alpha = math.atan(1.0 / k)
    one_wall = (r_end - r0) / math.sin(alpha)
    perim = 2.0 * one_wall
    area = slot_w * one_wall
    pa = perim / area if area > 0 else 0.0
    return {
        "r_end": r_end,
        "one_wall_length": one_wall,
        "perimeter_mm": perim,
        "area_mm2": area,
        "pa_ratio_mm_inv": pa,
    }


def compute_spiral_geometry(spec: SpiralSpec, n_steps: int = 300) -> SpiralGeometry:
    """Compute full geometry for a single spiral spec."""
    cx, cy = spec.center_x_mm, spec.center_y_mm
    r0 = spec.start_radius_mm
    k = spec.growth_rate_k
    turns = spec.turns
    rot = spec.rotation_deg
    w = spec.slot_width_mm

    stats = _closed_form_stats(r0, k, turns, w)
    centerline = _spiral_points(cx, cy, r0, k, turns, rot, n_steps)
    outer, inner = _spiral_walls(cx, cy, r0, k, turns, rot, w, n_steps)

    return SpiralGeometry(
        centerline=centerline,
        outer_wall=outer,
        inner_wall=inner,
        area_mm2=round(stats["area_mm2"], 2),
        perimeter_mm=round(stats["perimeter_mm"], 2),
        pa_ratio_mm_inv=round(stats["pa_ratio_mm_inv"], 4),
        end_radius_mm=round(stats["r_end"], 2),
        total_length_mm=round(stats["one_wall_length"], 2),
        spec=spec,
    )


def compute_dual_geometry(dual: DualSpiralSpec) -> DualSpiralGeometry:
    """Compute geometry for both spirals and combined stats."""
    upper_geo = compute_spiral_geometry(dual.upper)
    lower_geo = compute_spiral_geometry(dual.lower)

    total_area = upper_geo.area_mm2 + lower_geo.area_mm2
    round_ref = math.pi * (50.8 / 2) ** 2  # 4" round hole
    ratio_pct = (total_area / round_ref * 100) if round_ref > 0 else 0

    return DualSpiralGeometry(
        upper=upper_geo,
        lower=lower_geo,
        total_area_mm2=round(total_area, 2),
        round_ref_area_mm2=round(round_ref, 2),
        area_ratio_pct=round(ratio_pct, 1),
    )


# ── DXF export ────────────────────────────────────────────────────────────────

def generate_dxf(dual_spec: DualSpiralSpec, output_path: str) -> str:
    """
    Generate a DXF R2000 file from a DualSpiralSpec.
    Returns the output path on success.

    Layers:
      SPIRAL_CENTERLINE  — reference, not cut
      SPIRAL_OUTER_WALL  — CNC cut path
      SPIRAL_INNER_WALL  — CNC cut path
      BODY_REFERENCE     — body outline, not cut
      BRACE_KEEPOUT      — brace zone reference, not cut
    """
    try:
        import ezdxf
    except ImportError:
        raise RuntimeError(
            "ezdxf is required for DXF export. "
            "Install with: pip install ezdxf --break-system-packages"
        )

    doc = ezdxf.new(dxfversion="R2000")
    msp = doc.modelspace()

    # Define layers
    layer_defs = [
        ("SPIRAL_OUTER_WALL", 1, "CONTINUOUS"),
        ("SPIRAL_INNER_WALL", 2, "CONTINUOUS"),
        ("SPIRAL_CENTERLINE", 3, "DASHED"),
        ("BODY_REFERENCE",    5, "DASHED"),
        ("BRACE_KEEPOUT",     6, "DASHED"),
    ]
    for name, color, lt in layer_defs:
        if name not in doc.layers:
            doc.layers.new(name=name, dxfattribs={"color": color, "linetype": lt})

    def write_polyline(pts, layer):
        if len(pts) < 2:
            return
        msp.add_lwpolyline(
            [(p[0], p[1]) for p in pts],
            dxfattribs={"layer": layer}
        )

    # Both spirals
    for spec in [dual_spec.upper, dual_spec.lower]:
        geo = compute_spiral_geometry(spec)
        write_polyline(geo.centerline, "SPIRAL_CENTERLINE")
        write_polyline(geo.outer_wall, "SPIRAL_OUTER_WALL")
        write_polyline(geo.inner_wall, "SPIRAL_INNER_WALL")

    # Carlos Jumbo body reference (simplified outline)
    _write_body_reference(msp)

    # Brace keepout zones
    _write_brace_keepout(msp)

    doc.saveas(output_path)
    return output_path


def _write_body_reference(msp):
    """Write simplified Carlos Jumbo body outline as DXF reference."""
    try:
        import ezdxf
    except ImportError:
        return

    # Approximate outline using spline control points (mm, origin at bridge)
    body_pts = []
    lower_w, upper_w, waist_w = 194, 147, 107
    lower_h, upper_h = 242, 163

    for i in range(401):
        t = i / 400
        a = t * 2 * math.pi
        if t < 0.5:
            s = t / 0.5
            if s < 0.44:
                ss = s / 0.44
                r = upper_w * (0.68 + 0.32 * math.sin(ss * math.pi))
                x = r * math.sin(a)
                y = -upper_h + upper_h * (1 - ss * 0.83)
            elif s < 0.56:
                tt = (s - 0.44) / 0.12
                r = upper_w * (1 - tt) + waist_w * tt
                x = r * math.sin(a)
                y = (tt - 0.5) * 20
            else:
                ss = (s - 0.56) / 0.44
                r = waist_w + (lower_w - waist_w) * math.sin(ss * math.pi * 0.9)
                x = r * math.sin(a)
                y = ss * lower_h * 0.92
        else:
            s = (t - 0.5) / 0.5
            if s < 0.44:
                ss = s / 0.44
                r = lower_w - (lower_w - waist_w) * math.sin(ss * math.pi * 0.9)
                x = -r * math.sin(a - math.pi)
                y = lower_h * 0.92 * (1 - ss)
            elif s < 0.56:
                tt = (s - 0.44) / 0.12
                r = waist_w + (upper_w - waist_w) * tt
                x = -r * math.sin(a - math.pi)
                y = (0.5 - tt) * 20
            else:
                ss = (s - 0.56) / 0.44
                r = upper_w * (0.68 + 0.32 * math.sin((1 - ss) * math.pi))
                x = -r * math.sin(a - math.pi)
                y = -ss * upper_h * 0.83
        body_pts.append((x, y))

    if body_pts:
        msp.add_lwpolyline(
            body_pts,
            close=True,
            dxfattribs={"layer": "BODY_REFERENCE"}
        )


def _write_brace_keepout(msp):
    """Write brace keepout zones as DXF reference circles and lines."""
    try:
        import ezdxf
    except ImportError:
        return

    layer = "BRACE_KEEPOUT"

    # Bridge plate zone
    msp.add_circle((0, 0), radius=32, dxfattribs={"layer": layer})

    # X-brace diagonals (approximate crossing at origin)
    msp.add_line((-85, -85), (85, 85), dxfattribs={"layer": layer})
    msp.add_line((-85, 85), (85, -85), dxfattribs={"layer": layer})

    # Upper transverse brace
    msp.add_line((-155, -32), (155, -32), dxfattribs={"layer": layer})


# ── Serialisation helpers ─────────────────────────────────────────────────────

def spec_to_dict(spec: SpiralSpec) -> dict:
    return {
        "center_x_mm": spec.center_x_mm,
        "center_y_mm": spec.center_y_mm,
        "start_radius_mm": spec.start_radius_mm,
        "growth_rate_k": spec.growth_rate_k,
        "turns": spec.turns,
        "slot_width_mm": spec.slot_width_mm,
        "rotation_deg": spec.rotation_deg,
        "label": spec.label,
    }


def spec_from_dict(d: dict) -> SpiralSpec:
    return SpiralSpec(**d)


def geo_to_dict(geo: SpiralGeometry) -> dict:
    return {
        "centerline": geo.centerline,
        "outer_wall": geo.outer_wall,
        "inner_wall": geo.inner_wall,
        "area_mm2": geo.area_mm2,
        "perimeter_mm": geo.perimeter_mm,
        "pa_ratio_mm_inv": geo.pa_ratio_mm_inv,
        "end_radius_mm": geo.end_radius_mm,
        "total_length_mm": geo.total_length_mm,
    }


def dual_geo_to_dict(dg: DualSpiralGeometry) -> dict:
    return {
        "upper": geo_to_dict(dg.upper),
        "lower": geo_to_dict(dg.lower),
        "total_area_mm2": dg.total_area_mm2,
        "round_ref_area_mm2": dg.round_ref_area_mm2,
        "area_ratio_pct": dg.area_ratio_pct,
        "pa_threshold_upper": dg.upper.pa_ratio_mm_inv >= 0.10,
        "pa_threshold_lower": dg.lower.pa_ratio_mm_inv >= 0.10,
        "williams_2019_note": (
            "P:A > 0.10 mm⁻¹ required for significant efficiency gain over round hole. "
            "P:A = 2/slot_width for constant-width spiral. "
            "Source: Williams (2019), mwguitars.com.au Parts 7-8."
        ),
    }
