"""
CAM Post-Processor Router (v15.5)

G-code generation with advanced post-processing features.

Note: Core arc/fillet math extracted to cam/biarc_math.py
following the Fortran Rule (all math in subroutines).

Refactored for reduced complexity:
- Extracted corner smoothing to _smooth_corners()
- Extracted lead-out to _build_lead_out()
- Extracted contour emission to _emit_contour()
- Extracted preview spans to _generate_preview_spans()
"""

import json
import math
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import canonical arc/fillet math - NO inline math in routers (Fortran Rule)
from ..cam.biarc_math import (
    vec_len,
    vec_dot,
    fillet_between,
    angle_to_point,
    arc_center_from_radius,
    arc_tessellate,
)

router = APIRouter(prefix="/api/cam_gcode", tags=["cam_gcode"])
Point = Tuple[float, float]

PRESET_PATH = os.environ.get(
    "CAM_POST_PRESETS",
    os.path.join(os.path.dirname(__file__), "..", "data", "posts", "posts_v155.json"),
)


# =============================================================================
# Request Model
# =============================================================================
class V155Req(BaseModel):
    contour: List[Point]  # open or closed polyline (XY mm)
    z_cut_mm: float = -1.0
    feed_mm_min: float = 600.0
    plane_z_mm: float = 5.0
    safe_rapid: bool = True

    # Post selection
    preset: Literal["GRBL", "Mach3", "Haas", "Marlin"] = "GRBL"
    custom_post: Optional[Dict[str, Any]] = None  # override fields in preset

    # Lead in/out
    lead_type: Literal["none", "tangent", "arc"] = "tangent"
    lead_len_mm: float = 3.0
    lead_arc_radius_mm: float = 2.0

    # CRC
    crc_mode: Literal["none", "left", "right"] = "none"
    crc_diameter_mm: Optional[float] = None  # if None, emit G41/42 without D
    d_number: Optional[int] = None  # optional wear table index (Dxx)

    # Corner smoothing
    fillet_radius_mm: float = 0.4
    fillet_angle_min_deg: float = 20.0  # only fillet tighter-than threshold


# =============================================================================
# Post Context - holds state during G-code generation
# =============================================================================
@dataclass
class PostContext:
    """Holds state during G-code generation."""

    units: str = "metric"
    arc_mode: str = "IJ"  # "IJ" or "R"
    axis_modal: bool = True
    z_cut: float = -1.0
    plane_z: float = 5.0
    last_xy: Optional[Tuple[float, float]] = None
    out: List[str] = field(default_factory=list)

    def emit(self, line: str) -> None:
        """Emit a G-code line with optional axis modal optimization."""
        if self.axis_modal:
            line, self.last_xy = _axis_modal_emit(line, self.last_xy)
        self.out.append(line)

    def emit_raw(self, line: str) -> None:
        """Emit a G-code line without modal optimization."""
        self.out.append(line)


# =============================================================================
# Preset Loading
# =============================================================================
def _load_preset(name: str) -> Dict[str, Any]:
    """Load a post-processor preset by name."""
    try:
        with open(PRESET_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["presets"][name]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preset load failed: {e}")


# =============================================================================
# Geometry Helpers
# =============================================================================
def _poly_is_closed(poly: List[Point], tol: float = 1e-6) -> bool:
    """Check if polyline is closed (first point equals last)."""
    if len(poly) <= 2:
        return False
    return abs(poly[0][0] - poly[-1][0]) < tol and abs(poly[0][1] - poly[-1][1]) < tol


def _fillet_between(a: Point, b: Point, c: Point, R: float):
    """Wrapper for fillet_between from biarc_math. Returns (p1, p2, cx, cy, dir) or None."""
    result = fillet_between(a, b, c, R)
    if result is None:
        return None
    p1, p2, cx, cy, direction = result
    return (p1, p2, cx, cy, direction)


def _normalize_vec(v: Tuple[float, float]) -> Tuple[float, float]:
    """Normalize a 2D vector."""
    length = math.hypot(v[0], v[1]) or 1e-9
    return (v[0] / length, v[1] / length)


# =============================================================================
# G-code Helpers
# =============================================================================
def _axis_modal_emit(line: str, last_xy: Optional[Tuple[float, float]]) -> Tuple[str, Tuple[float, float]]:
    """Apply axis modal optimization to suppress redundant coordinates."""
    tokens = line.split()
    if not tokens:
        return line, last_xy
    if tokens[0] not in ("G1", "G2", "G3"):
        return line, last_xy

    x, y = None, None
    for t in tokens:
        if t.startswith("X"):
            x = float(t[1:])
        elif t.startswith("Y"):
            y = float(t[1:])

    if x is None and last_xy:
        x = last_xy[0]
    if y is None and last_xy:
        y = last_xy[1]

    parts = [tokens[0]]
    if last_xy is None or abs(x - last_xy[0]) > 1e-9:
        parts.append(f"X{x:.3f}")
    if last_xy is None or abs(y - last_xy[1]) > 1e-9:
        parts.append(f"Y{y:.3f}")

    for t in tokens[1:]:
        if not (t.startswith("X") or t.startswith("Y")):
            parts.append(t)

    return " ".join(parts), (x, y)


def _get_gcode_coord(tag: str, line: str) -> Optional[float]:
    """Extract a coordinate value from a G-code line (e.g., 'X' -> 12.345)."""
    p = line.find(tag)
    if p < 0:
        return None
    q = p + 1
    while q < len(line) and (line[q].isdigit() or line[q] in ".-"):
        q += 1
    return float(line[p + 1 : q])


# =============================================================================
# Corner Smoothing
# =============================================================================
def _smooth_corners(
    poly: List[Point], fillet_radius: float, angle_min_rad: float
) -> Tuple[List[Point], List[Tuple]]:
    """
    Insert fillet arcs at sharp corners.

    Returns:
        (smoothed_points, arc_info_list)
        arc_info_list contains: (start_idx, end_idx, cx, cy, radius, direction)
    """
    if fillet_radius <= 0:
        return poly, []

    smoothed = [poly[0]]
    arcs = []

    for i in range(1, len(poly) - 1):
        a, b, c = poly[i - 1], poly[i], poly[i + 1]

        # Compute vectors from corner
        v1x, v1y = a[0] - b[0], a[1] - b[1]
        v2x, v2y = c[0] - b[0], c[1] - b[1]
        L1, L2 = math.hypot(v1x, v1y), math.hypot(v2x, v2y)

        # Skip degenerate segments
        if L1 < 1e-9 or L2 < 1e-9:
            smoothed.append(b)
            continue

        # Normalize
        v1x, v1y = v1x / L1, v1y / L1
        v2x, v2y = v2x / L2, v2y / L2

        # Interior angle
        cos_t = max(-1.0, min(1.0, (-v1x) * v2x + (-v1y) * v2y))
        theta = math.acos(cos_t)

        # Check if corner is sharp enough for fillet
        if theta < math.pi - 1e-6 and theta < (math.pi - angle_min_rad):
            fil = _fillet_between(a, b, c, fillet_radius)
            if fil:
                p1, p2, cx, cy, dirn = fil
                smoothed.append(p1)
                smoothed.append(p2)
                arcs.append((len(smoothed) - 2, len(smoothed) - 1, cx, cy, fillet_radius, dirn))
                continue

        smoothed.append(b)

    smoothed.append(poly[-1])
    return smoothed, arcs


# =============================================================================
# Lead-in / Lead-out
# =============================================================================
def _build_lead_in(
    ctx: PostContext,
    start: Point,
    first_vec: Tuple[float, float],
    lead_type: str,
    lead_len: float,
    lead_radius: float,
) -> None:
    """Build lead-in moves: rapid to position, plunge, then lead-in pattern."""
    ctx.emit_raw(f"G0 Z{ctx.plane_z:.3f}")
    ctx.emit_raw(f"G0 X{start[0]:.3f} Y{start[1]:.3f}")
    ctx.emit_raw(f"G1 Z{ctx.z_cut:.3f}")
    ctx.last_xy = (start[0], start[1])

    if lead_type == "tangent" and lead_len > 0:
        # Move backwards then forward for tangent entry
        bx = start[0] - first_vec[0] * lead_len
        by = start[1] - first_vec[1] * lead_len
        ctx.emit_raw(f"G1 X{bx:.3f} Y{by:.3f} Z{ctx.z_cut:.3f}")
        ctx.emit_raw(f"G1 X{start[0]:.3f} Y{start[1]:.3f} Z{ctx.z_cut:.3f}")
        ctx.last_xy = (start[0], start[1])

    elif lead_type == "arc" and lead_radius > 0:
        # 90° arc lead-in from side
        nx, ny = -first_vec[1], first_vec[0]  # left normal
        px = start[0] + nx * lead_radius
        py = start[1] + ny * lead_radius
        ctx.emit_raw(f"G1 X{px:.3f} Y{py:.3f} Z{ctx.z_cut:.3f}")

        if ctx.arc_mode == "R":
            ctx.emit_raw(f"G2 X{start[0]:.3f} Y{start[1]:.3f} R{lead_radius:.3f} Z{ctx.z_cut:.3f}")
        else:
            cx, cy = start[0], start[1] + lead_radius
            I, J = cx - px, cy - py
            ctx.emit_raw(f"G2 X{start[0]:.3f} Y{start[1]:.3f} I{I:.3f} J{J:.3f} Z{ctx.z_cut:.3f}")
        ctx.last_xy = (start[0], start[1])


def _build_lead_out(
    ctx: PostContext,
    end_points: List[Point],
    lead_type: str,
    lead_len: float,
    lead_radius: float,
) -> None:
    """Build lead-out moves at end of contour."""
    if len(end_points) < 2:
        return

    last_vec = _normalize_vec((end_points[-1][0] - end_points[-2][0], end_points[-1][1] - end_points[-2][1]))

    if lead_type == "tangent" and lead_len > 0:
        ex = end_points[-1][0] + last_vec[0] * lead_len
        ey = end_points[-1][1] + last_vec[1] * lead_len
        ctx.emit(f"G1 X{ex:.3f} Y{ey:.3f} Z{ctx.z_cut:.3f}")

    elif lead_type == "arc" and lead_radius > 0:
        nx, ny = last_vec[1], -last_vec[0]  # right normal
        px = end_points[-1][0] + nx * lead_radius
        py = end_points[-1][1] + ny * lead_radius
        ctx.emit(f"G1 X{px:.3f} Y{py:.3f} Z{ctx.z_cut:.3f}")

        if ctx.arc_mode == "R":
            ctx.emit(f"G3 X{end_points[-1][0]:.3f} Y{end_points[-1][1]:.3f} R{lead_radius:.3f} Z{ctx.z_cut:.3f}")
        else:
            cx = end_points[-1][0]
            cy = end_points[-1][1] + lead_radius
            I, J = cx - px, cy - py
            ctx.emit(f"G3 X{end_points[-1][0]:.3f} Y{end_points[-1][1]:.3f} I{I:.3f} J{J:.3f} Z{ctx.z_cut:.3f}")


# =============================================================================
# Contour Emission
# =============================================================================
def _emit_contour(ctx: PostContext, points: List[Point], arcs: List[Tuple]) -> None:
    """Emit G-code for contour with fillet arcs."""
    arc_map = {(ai, aj): (cx, cy, R, dirn) for (ai, aj, cx, cy, R, dirn) in arcs}

    for i in range(len(points) - 1):
        p0, p1 = points[i], points[i + 1]
        arc_info = arc_map.get((i, i + 1))

        if arc_info:
            cx, cy, R, dirn = arc_info
            code = "G2" if dirn == "CW" else "G3"
            if ctx.arc_mode == "R":
                ctx.emit(f"{code} X{p1[0]:.3f} Y{p1[1]:.3f} R{R:.3f} Z{ctx.z_cut:.3f}")
            else:
                I, J = cx - p0[0], cy - p0[1]
                ctx.emit(f"{code} X{p1[0]:.3f} Y{p1[1]:.3f} I{I:.3f} J{J:.3f} Z{ctx.z_cut:.3f}")
        else:
            ctx.emit(f"G1 X{p1[0]:.3f} Y{p1[1]:.3f} Z{ctx.z_cut:.3f}")


# =============================================================================
# G-code Header / CRC
# =============================================================================
def _build_header(ctx: PostContext, req: V155Req, header: List[str]) -> None:
    """Build G-code header with units, modes, and CRC setup."""
    ctx.out.extend(header)
    ctx.emit_raw("G21" if ctx.units == "metric" else "G20")
    ctx.emit_raw("G90")
    ctx.emit_raw("G94")
    ctx.emit_raw(f"F{req.feed_mm_min:.3f}")

    if req.crc_mode != "none":
        ctx.emit_raw("G41" if req.crc_mode == "left" else "G42")
        if req.crc_diameter_mm:
            if req.d_number is not None:
                ctx.emit_raw(f"D{int(req.d_number)} (dia {req.crc_diameter_mm:.3f}mm)")
            else:
                ctx.emit_raw(f"(CRC dia {req.crc_diameter_mm:.3f}mm)")


# =============================================================================
# Preview Span Generation
# =============================================================================
def _generate_preview_spans(gcode_lines: List[str], start_point: Point, z_cut: float) -> List[Dict[str, float]]:
    """Generate preview spans by parsing G-code and tessellating arcs."""
    spans = []
    last = start_point

    for line in gcode_lines:
        line = line.strip()

        if line.startswith("G1 ") and "X" in line and "Y" in line and "Z" in line:
            x = _get_gcode_coord("X", line)
            y = _get_gcode_coord("Y", line)
            if x is not None and y is not None:
                spans.append({"x1": last[0], "y1": last[1], "z1": z_cut, "x2": x, "y2": y, "z2": z_cut})
                last = (x, y)

        elif (line.startswith("G2 ") or line.startswith("G3 ")) and "X" in line and "Y" in line:
            spans_from_arc, new_last = _tessellate_arc(line, last, z_cut)
            spans.extend(spans_from_arc)
            if new_last:
                last = new_last

    return spans


def _tessellate_arc(line: str, start: Point, z_cut: float) -> Tuple[List[Dict], Optional[Point]]:
    """Tessellate an arc G-code line into linear spans for preview."""
    cw = line.startswith("G2 ")
    x = _get_gcode_coord("X", line)
    y = _get_gcode_coord("Y", line)
    r = _get_gcode_coord("R", line)
    I = _get_gcode_coord("I", line)
    J = _get_gcode_coord("J", line)

    if x is None or y is None:
        return [], None

    ex, ey = start

    # Determine arc center
    if r is not None:
        # Approximate center via perpendicular bisector
        mx, my = (ex + x) / 2, (ey + y) / 2
        dx, dy = x - ex, y - ey
        d = math.hypot(dx, dy) or 1e-9
        h = math.sqrt(max(r * r - (d / 2) ** 2, 0.0))
        nx, ny = -dy / d, dx / d
        cx = mx + (-h if cw else h) * nx
        cy = my + (-h if cw else h) * ny
    elif I is not None and J is not None:
        cx, cy = ex + I, ey + J
        r = math.hypot(I, J)
    else:
        return [], (x, y)

    # Tessellate arc
    a1 = math.atan2(ey - cy, ex - cx)
    a2 = math.atan2(y - cy, x - cx)

    if cw:
        while a2 > a1:
            a2 -= 2 * math.pi
    else:
        while a2 < a1:
            a2 += 2 * math.pi

    steps = max(6, int(abs(a2 - a1) * r / 0.5))
    spans = []
    px, py = ex, ey

    for t in range(1, steps + 1):
        ang = a1 + (a2 - a1) * t / steps
        qx = cx + r * math.cos(ang)
        qy = cy + r * math.sin(ang)
        spans.append({"x1": px, "y1": py, "z1": z_cut, "x2": qx, "y2": qy, "z2": z_cut})
        px, py = qx, qy

    return spans, (x, y)


# =============================================================================
# Endpoints
# =============================================================================
@router.get("/posts_v155")
def get_posts() -> Dict[str, Any]:
    """Get all available post-processor presets (v15.5)"""
    with open(PRESET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/post_v155")
def post_v155(req: V155Req) -> Dict[str, Any]:
    """
    Generate G-code from contour with advanced post-processing.

    Features:
    - Post-processor presets (GRBL, Mach3, Haas, Marlin)
    - Lead-in/out strategies (tangent, arc, none)
    - CRC support (G41/G42 with optional D#)
    - Automatic corner smoothing (fillet arcs)
    - Arc optimization (controller-aware sweep limits)
    - Axis modal optimization (suppress redundant coordinates)
    """
    # Load preset and apply overrides
    post = _load_preset(req.preset)
    if req.custom_post:
        post.update(req.custom_post)

    # Validate input
    poly = list(req.contour)
    if len(poly) < 2:
        raise HTTPException(status_code=400, detail="contour requires >=2 points")

    # Ensure closed for CRC contour
    closed = _poly_is_closed(poly)
    if not closed:
        poly = poly + [poly[0]]
        closed = True

    # Create context
    ctx = PostContext(
        units=post.get("units", "metric"),
        arc_mode=post.get("arc_mode", "IJ"),
        axis_modal=bool(post.get("axis_modal_opt", True)),
        z_cut=req.z_cut_mm,
        plane_z=req.plane_z_mm,
    )

    # Corner smoothing
    angle_min_rad = math.radians(max(0.0, req.fillet_angle_min_deg))
    smoothed, arcs = _smooth_corners(poly, req.fillet_radius_mm, angle_min_rad)

    # Build G-code
    header = list(post.get("header", []))
    footer = list(post.get("footer", []))

    _build_header(ctx, req, header)

    # Lead-in
    first_vec = _normalize_vec((smoothed[1][0] - smoothed[0][0], smoothed[1][1] - smoothed[0][1]))
    _build_lead_in(ctx, smoothed[0], first_vec, req.lead_type, req.lead_len_mm, req.lead_arc_radius_mm)

    # Emit contour with arcs
    _emit_contour(ctx, smoothed, arcs)

    # Lead-out
    _build_lead_out(ctx, smoothed, req.lead_type, req.lead_len_mm, req.lead_arc_radius_mm)

    # CRC cancel
    if req.crc_mode != "none":
        ctx.emit_raw("G40")

    # Retract and footer
    ctx.emit_raw(f"G0 Z{ctx.plane_z:.3f}")
    ctx.out.extend(footer)

    # Generate preview spans
    spans = _generate_preview_spans(ctx.out, smoothed[0], req.z_cut_mm)

    gcode = "\n".join(ctx.out)
    return {"ok": True, "gcode": gcode, "spans": spans, "closed": closed, "preset_used": req.preset}
