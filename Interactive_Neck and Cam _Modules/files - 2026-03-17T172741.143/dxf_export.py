"""
Production Shop — BCAM 2030A DXF Export Service
FastAPI router that converts normalized headstock SVG paths (200×320 canvas
units) into a BCAM-ready DXF file with:

  - Correct real-world mm scaling
  - Kerf compensation offset (outward for through-cuts)
  - Layer structure the BCAM 2030A controller expects
  - Optional dogbone fillets at concave corners
  - Separate layers for: outline, tuner holes, inlay pockets, annotations

Add to Production Shop FastAPI:
    from dxf_export import router as export_router
    app.include_router(export_router, prefix="/api/export")
"""

from __future__ import annotations

import io
import math
import re
from typing import Optional

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from ezdxf.math import Vec2

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["export"])

# ─── Canvas → real-world scale ────────────────────────────────────────────────
# The headstock canvas is 200 × 320 units.
# Typical headstock is ~43 mm wide (nut) × ~175 mm long.
# Scale factor: real_mm = canvas_unit × MM_PER_UNIT
MM_PER_UNIT = 0.215   # matches the frontend MM constant

# ─── BCAM 2030A layer naming convention ──────────────────────────────────────
LAYER_OUTLINE    = "HS_OUTLINE"       # main headstock perimeter — through cut
LAYER_TUNERS     = "HS_TUNERS"        # tuner peg holes — drill / pocket
LAYER_INLAYS     = "HS_INLAYS"        # inlay cavity pockets
LAYER_NUTS       = "HS_NUT"           # nut slot
LAYER_ANNOTATION = "HS_ANNOTATION"    # dimensions, labels — not cut

# ─── Pydantic models ──────────────────────────────────────────────────────────

class TunerHole(BaseModel):
    x: float           # canvas units
    y: float
    radius: float = 4.0   # peg hole radius, canvas units (~0.86 mm)

class InlayPocket(BaseModel):
    path_d: str        # SVG path string in canvas units
    depth:  float = 2.0   # pocket depth mm (not encoded in 2D path)
    label:  str = ""

# ── Section 7: CAM extension models (WORKSPACE_CAM_INTEGRATION) ──────────────

class TrussRod(BaseModel):
    """Truss rod channel specification for headstock DXF export."""
    access:      str   = "heel"      # "heel" | "head" (Gibson vs Fender access)
    type:        str   = "single"    # "single" | "double_action"
    width_mm:    float = 6.35        # from repo TrussRodConfig
    depth_mm:    float = 9.525
    length_mm:   float = 406.4
    end_mill_mm: float = 3.175       # 1/8" flat end — repo T2
    cx_u:        float = 100.0       # canvas X centre (units)
    start_y_u:   float = 298.0       # nut Y position (canvas units)
    end_y_u:     float = 190.0       # channel end (canvas units)

class PitchSpec(BaseModel):
    """Headstock pitch angle for DXF annotation and fixturing note."""
    style:         str   = "angled"  # "angled" | "flat"
    angle_deg:     float = 14.0
    fixture_note:  str   = ""        # printed on ANNOTATION layer

class ExportRequest(BaseModel):
    outline_path:   str                        # SVG path d= for headstock outline
    tuner_holes:    list[TunerHole] = []
    inlay_pockets:  list[InlayPocket] = []
    nut_x1:         float = 65.0              # nut line endpoints (canvas units)
    nut_x2:         float = 135.0
    nut_y:          float = 298.0
    nut_width_mm:   float = 43.0              # real nut width for dimension annotation
    kerf_mm:        float = 3.175             # 1/8" bit default
    dogbone:        bool  = True              # add dogbone fillets at concave corners
    tool_dia_mm:    float = 3.175             # used for dogbone radius
    label:          str   = "Headstock"
    scale_override: Optional[float] = None   # override MM_PER_UNIT if needed
    # ── Section 7: CAM extension fields ──────────────────────────────────────
    truss_rod:    Optional[TrussRod]   = None
    pitch:        Optional[PitchSpec]  = None
    screw_holes:  list[TunerHole]      = []   # mounting screw positions

# ─── SVG path → Vec2 list ─────────────────────────────────────────────────────

def svg_path_to_points(path_d: str, scale: float) -> list[Vec2]:
    """
    Convert a simple M/L/Z SVG path to a list of Vec2 in mm.
    Handles the resampled paths produced by the normalizePaths pipeline
    (getPointAtLength output — all M/L commands, no curves).
    Cubic bezier paths from buildParametricPath are also handled via
    a simple recursive subdivision approximation.
    """
    pts: list[Vec2] = []
    # Tokenise
    tokens = re.findall(r"[MLCZz]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", path_d)
    i, cmd = 0, 'M'
    cx_cur, cy_cur = 0.0, 0.0

    while i < len(tokens):
        tok = tokens[i]
        if tok in 'MLCZz':
            cmd = tok; i += 1; continue

        if cmd == 'M':
            cx_cur, cy_cur = float(tokens[i]), float(tokens[i+1]); i += 2
            pts.append(Vec2(cx_cur * scale, cy_cur * scale))
            cmd = 'L'   # subsequent pairs are implicit L

        elif cmd == 'L':
            cx_cur, cy_cur = float(tokens[i]), float(tokens[i+1]); i += 2
            pts.append(Vec2(cx_cur * scale, cy_cur * scale))

        elif cmd == 'C':
            # Cubic bezier — subdivide to ≤0.5mm chord error
            x1, y1 = float(tokens[i]),   float(tokens[i+1])
            x2, y2 = float(tokens[i+2]), float(tokens[i+3])
            ex, ey = float(tokens[i+4]), float(tokens[i+5])
            i += 6
            seg = _subdivide_bezier(
                (cx_cur, cy_cur), (x1, y1), (x2, y2), (ex, ey),
                scale, max_chord_mm=0.5,
            )
            pts.extend(Vec2(p[0], p[1]) for p in seg[1:])
            cx_cur, cy_cur = ex, ey

        else:
            i += 1   # skip unknown

    # Remove duplicate last point if closed
    if len(pts) > 1 and pts[0].isclose(pts[-1], abs_tol=0.01):
        pts.pop()

    return pts


def _subdivide_bezier(
    p0: tuple, p1: tuple, p2: tuple, p3: tuple,
    scale: float, max_chord_mm: float,
    depth: int = 0,
) -> list[tuple]:
    """Recursive cubic bezier subdivision to chord tolerance."""
    x0, y0 = p0[0]*scale, p0[1]*scale
    x3, y3 = p3[0]*scale, p3[1]*scale
    chord = math.hypot(x3-x0, y3-y0)
    if chord < max_chord_mm or depth > 8:
        return [p0, p3]
    # de Casteljau midpoint
    def lerp(a, b): return ((a[0]+b[0])/2, (a[1]+b[1])/2)
    m01, m12, m23 = lerp(p0,p1), lerp(p1,p2), lerp(p2,p3)
    m012, m123  = lerp(m01,m12), lerp(m12,m23)
    mid         = lerp(m012, m123)
    left  = _subdivide_bezier(p0, m01, m012, mid, scale, max_chord_mm, depth+1)
    right = _subdivide_bezier(mid, m123, m23, p3, scale, max_chord_mm, depth+1)
    return left[:-1] + right


# ─── Kerf offset (outward Minkowski sum approximation) ───────────────────────

def offset_polygon(pts: list[Vec2], offset_mm: float) -> list[Vec2]:
    """
    Simple inward/outward offset via vertex normal averaging.
    Positive offset = outward (for through-cuts).
    Not as accurate as Clipper but sufficient for guitar headstocks.
    """
    if offset_mm == 0 or len(pts) < 3:
        return pts

    n = len(pts)
    normals: list[Vec2] = []
    for i in range(n):
        a = pts[(i - 1) % n]
        b = pts[i]
        c = pts[(i + 1) % n]
        # Edge normals (pointing outward for CCW polygon)
        e1 = Vec2(b.x - a.x, b.y - a.y)
        e2 = Vec2(c.x - b.x, c.y - b.y)
        n1 = Vec2(-e1.y, e1.x).normalize()
        n2 = Vec2(-e2.y, e2.x).normalize()
        avg = Vec2(n1.x + n2.x, n1.y + n2.y)
        length = math.hypot(avg.x, avg.y)
        if length < 1e-9:
            normals.append(Vec2(0, 0))
        else:
            normals.append(Vec2(avg.x/length * offset_mm, avg.y/length * offset_mm))

    return [Vec2(pts[i].x + normals[i].x, pts[i].y + normals[i].y) for i in range(n)]


# ─── Dogbone fillets ──────────────────────────────────────────────────────────

def add_dogbones(pts: list[Vec2], tool_radius_mm: float) -> list[Vec2]:
    """
    Insert dogbone circles at concave corners so a round bit can clear
    the corner fully. Returns the augmented point list (the DXF writer
    adds the actual circles; here we just tag the corner indices).
    Returns (pts, concave_corner_indices) — caller adds CIRCLE entities.
    """
    concave: list[int] = []
    n = len(pts)
    for i in range(n):
        a = pts[(i - 1) % n]
        b = pts[i]
        c = pts[(i + 1) % n]
        cross = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
        if cross < 0:   # concave corner in CW or CCW depending on winding
            concave.append(i)
    return pts, concave   # type: ignore[return-value]


# ─── DXF builder ──────────────────────────────────────────────────────────────

def build_dxf(req: ExportRequest) -> ezdxf.document.Drawing:
    scale = req.scale_override if req.scale_override else MM_PER_UNIT
    kerf_offset = req.kerf_mm / 2   # outward offset = half kerf

    doc = ezdxf.new(dxfversion="R2010")
    doc.units = units.MM
    msp = doc.modelspace()

    # ── Layer setup ───────────────────────────────────────────────────────────
    def add_layer(name: str, color: int, linetype: str = "CONTINUOUS"):
        doc.layers.add(name=name, color=color, linetype=linetype)

    add_layer(LAYER_OUTLINE,    color=1)   # red
    add_layer(LAYER_TUNERS,     color=3)   # green
    add_layer(LAYER_INLAYS,     color=4)   # cyan
    add_layer(LAYER_NUTS,       color=5)   # blue
    add_layer(LAYER_ANNOTATION, color=8)   # gray

    # ── Headstock outline ──────────────────────────────────────────────────────
    outline_pts = svg_path_to_points(req.outline_path, scale)

    if req.kerf_mm > 0:
        outline_pts = offset_polygon(outline_pts, kerf_offset)

    if req.dogbone and req.tool_dia_mm > 0:
        outline_pts, concave_idxs = add_dogbones(outline_pts, req.tool_dia_mm / 2)
    else:
        concave_idxs = []

    if len(outline_pts) >= 2:
        msp.add_lwpolyline(
            [(p.x, p.y) for p in outline_pts],
            close=True,
            dxfattribs={"layer": LAYER_OUTLINE},
        )

    # Dogbone circles at concave corners
    for idx in concave_idxs:
        p = outline_pts[idx]
        msp.add_circle(
            center=(p.x, p.y),
            radius=req.tool_dia_mm / 2,
            dxfattribs={"layer": LAYER_OUTLINE},
        )

    # ── Tuner holes ────────────────────────────────────────────────────────────
    for t in req.tuner_holes:
        cx_mm = t.x * scale
        cy_mm = t.y * scale
        r_mm  = t.radius * scale
        msp.add_circle(
            center=(cx_mm, cy_mm),
            radius=r_mm,
            dxfattribs={"layer": LAYER_TUNERS},
        )
        # Cross-hair for drill registration
        msp.add_line((cx_mm - r_mm*0.3, cy_mm), (cx_mm + r_mm*0.3, cy_mm), dxfattribs={"layer": LAYER_TUNERS})
        msp.add_line((cx_mm, cy_mm - r_mm*0.3), (cx_mm, cy_mm + r_mm*0.3), dxfattribs={"layer": LAYER_TUNERS})

    # ── Inlay pockets ──────────────────────────────────────────────────────────
    for pocket in req.inlay_pockets:
        pocket_pts = svg_path_to_points(pocket.path_d, scale)
        if len(pocket_pts) >= 2:
            msp.add_lwpolyline(
                [(p.x, p.y) for p in pocket_pts],
                close=True,
                dxfattribs={"layer": LAYER_INLAYS},
            )
        # Depth annotation
        if pocket.label:
            if pocket_pts:
                cx_a = sum(p.x for p in pocket_pts) / len(pocket_pts)
                cy_a = sum(p.y for p in pocket_pts) / len(pocket_pts)
                msp.add_text(
                    f"{pocket.label} d={pocket.depth}mm",
                    dxfattribs={"layer": LAYER_ANNOTATION, "height": 1.5},
                ).set_placement((cx_a, cy_a), align=TextEntityAlignment.MIDDLE_CENTER)

    # ── Nut line ───────────────────────────────────────────────────────────────
    msp.add_line(
        (req.nut_x1 * scale, req.nut_y * scale),
        (req.nut_x2 * scale, req.nut_y * scale),
        dxfattribs={"layer": LAYER_NUTS},
    )

    # ── Annotations ────────────────────────────────────────────────────────────
    # Title block
    bbox_pts = svg_path_to_points(req.outline_path, scale)
    if bbox_pts:
        min_x = min(p.x for p in bbox_pts)
        max_x = max(p.x for p in bbox_pts)
        min_y = min(p.y for p in bbox_pts)
        max_y = max(p.y for p in bbox_pts)

        # Bounding box
        msp.add_lwpolyline([
            (min_x - 5, min_y - 5), (max_x + 5, min_y - 5),
            (max_x + 5, max_y + 5), (min_x - 5, max_y + 5),
        ], close=True, dxfattribs={"layer": LAYER_ANNOTATION})

        # Dimension: nut width
        msp.add_text(
            f"Nut: {req.nut_width_mm:.1f} mm",
            dxfattribs={"layer": LAYER_ANNOTATION, "height": 2.0},
        ).set_placement(
            (req.nut_x1 * scale, req.nut_y * scale - 6),
            align=TextEntityAlignment.LEFT,
        )

        # Overall dimensions
        w_mm = (max_x - min_x)
        h_mm = (max_y - min_y)
        msp.add_text(
            f"{req.label}  {w_mm:.1f} × {h_mm:.1f} mm",
            dxfattribs={"layer": LAYER_ANNOTATION, "height": 2.5},
        ).set_placement((min_x, max_y + 8), align=TextEntityAlignment.LEFT)

        msp.add_text(
            f"Kerf offset: {req.kerf_mm:.3f} mm  |  Tool: Ø{req.tool_dia_mm:.2f} mm",
            dxfattribs={"layer": LAYER_ANNOTATION, "height": 1.8},
        ).set_placement((min_x, max_y + 13), align=TextEntityAlignment.LEFT)

    # ── Section 7: Truss rod channel ─────────────────────────────────────────
    if req.truss_rod:
        rod = req.truss_rod
        rod_scale = scale
        cx_mm  = rod.cx_u * rod_scale
        sy_mm  = rod.start_y_u * rod_scale
        ey_mm  = rod.end_y_u * rod_scale
        w_mm   = rod.width_mm
        em_r   = rod.end_mill_mm / 2

        # Layer name reflects access location
        rod_layer = "HS_ROD_SLOT" if rod.access == "head" else "HS_ROD_CHANNEL"
        if rod_layer not in [l.dxf.name for l in doc.layers]:
            doc.layers.add(name=rod_layer, color=6)  # magenta

        # Rectangular channel outline
        msp.add_lwpolyline([
            (cx_mm - w_mm/2, sy_mm),
            (cx_mm + w_mm/2, sy_mm),
            (cx_mm + w_mm/2, ey_mm),
            (cx_mm - w_mm/2, ey_mm),
        ], close=True, dxfattribs={"layer": rod_layer})

        # End-mill radius arc at open end (rounded pocket terminus)
        msp.add_arc(
            center=(cx_mm, ey_mm + em_r),
            radius=em_r,
            start_angle=180, end_angle=0,
            dxfattribs={"layer": rod_layer},
        )

        # Annotation: rod dimensions
        msp.add_text(
            f"Truss rod ({rod.access}): {w_mm}×{rod.depth_mm}mm  L={rod.length_mm}mm  T2 Ø{rod.end_mill_mm}mm",
            dxfattribs={"layer": LAYER_ANNOTATION, "height": 1.5},
        ).set_placement((cx_mm - w_mm/2, sy_mm + 4), align=TextEntityAlignment.LEFT)

    # ── Section 7: Tuner mounting screws ─────────────────────────────────────
    if req.screw_holes:
        screw_layer = "HS_TUNER_SCREWS"
        if screw_layer not in [l.dxf.name for l in doc.layers]:
            doc.layers.add(name=screw_layer, color=2)  # yellow
        for sh in req.screw_holes:
            msp.add_circle(
                center=(sh.x * scale, sh.y * scale),
                radius=sh.radius * scale,
                dxfattribs={"layer": screw_layer},
            )

    # ── Section 7: Pitch angle fixturing annotation ───────────────────────────
    if req.pitch and req.pitch.angle_deg > 0:
        note = req.pitch.fixture_note or f"Headstock pitch: {req.pitch.angle_deg}° ({req.pitch.style})"
        msp.add_text(
            note,
            dxfattribs={"layer": LAYER_ANNOTATION, "height": 2.0},
        ).set_placement((10, -20), align=TextEntityAlignment.LEFT)

    return doc


# ─── Route ────────────────────────────────────────────────────────────────────

@router.post("/headstock-dxf")
async def export_headstock_dxf(req: ExportRequest):
    """
    Convert a normalized headstock outline + features to a BCAM 2030A DXF.

    POST body (JSON):
      outline_path   — SVG path d= string (200×320 canvas units)
      tuner_holes    — [{x, y, radius}] in canvas units
      inlay_pockets  — [{path_d, depth, label}]
      nut_x1/x2/y   — nut line endpoints
      kerf_mm        — half applied as outward offset to outline
      dogbone        — insert dogbone circles at concave corners
      tool_dia_mm    — bit diameter for dogbone radius
      label          — annotation string

    Returns a .dxf file download.
    """
    try:
        doc = build_dxf(req)
    except Exception as e:
        raise HTTPException(422, f"DXF build error: {e}")

    buf = io.BytesIO()
    doc.write(buf)
    buf.seek(0)

    filename = req.label.lower().replace(" ", "-") or "headstock"
    return StreamingResponse(
        buf,
        media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.dxf"'},
    )


@router.post("/headstock-dxf/preview")
async def preview_dxf_points(req: ExportRequest):
    """
    Return the processed point arrays as JSON for canvas preview
    before the user commits to a DXF download.
    """
    scale = req.scale_override if req.scale_override else MM_PER_UNIT
    outline_pts = svg_path_to_points(req.outline_path, scale)
    if req.kerf_mm > 0:
        outline_pts = offset_polygon(outline_pts, req.kerf_mm / 2)
    return {
        "outline":  [{"x": p.x, "y": p.y} for p in outline_pts],
        "tuners":   [{"x": t.x*scale, "y": t.y*scale, "r": t.radius*scale} for t in req.tuner_holes],
        "scale_mm_per_unit": scale,
        "bounding_box": {
            "w_mm": (max(p.x for p in outline_pts) - min(p.x for p in outline_pts)) if outline_pts else 0,
            "h_mm": (max(p.y for p in outline_pts) - min(p.y for p in outline_pts)) if outline_pts else 0,
        } if outline_pts else {},
    }
