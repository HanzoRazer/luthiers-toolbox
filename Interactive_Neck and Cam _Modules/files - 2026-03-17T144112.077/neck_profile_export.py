"""
Production Shop — Neck Profile Export Service
FastAPI router that generates neck back profile DXF and G-code,
with crown compensation baked in from the fretboard spec.

back_depth(n) = target_depth(n)
              - fret_wire_height
              - fretboard_thickness
              - sagitta(radius_at_fret(n), board_width_at_fret(n))

Three endpoints:
  POST /api/neck/dxf          — layered DXF with profile cross-sections
  POST /api/neck/gcode        — back profile sweep G-code for BCAM 2030A
  POST /api/neck/stations     — JSON station table with coupling breakdown

Add to main.py:
    from neck_profile_export import router as neck_router
    app.include_router(neck_router, prefix="/api/neck")
"""

from __future__ import annotations

import io
import math
from typing import Optional

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel

router = APIRouter(tags=["neck"])

INCH = 25.4

# ─── Layer names ──────────────────────────────────────────────────────────────

LAYER_NUT_PROFILE  = "NK_PROFILE_NUT"
LAYER_12TH_PROFILE = "NK_PROFILE_12TH"
LAYER_PROFILE_LAST = "NK_PROFILE_LAST"
LAYER_TOOLPATH     = "NK_TOOLPATH"
LAYER_DIMENSION    = "NK_DIMENSION"
LAYER_ANNOTATION   = "NK_ANNOTATION"

# ─── Models ───────────────────────────────────────────────────────────────────

class ProfileStation(BaseModel):
    fret:           int
    position_mm:    float
    target_mm:      float
    crown_comp_mm:  float
    back_depth_mm:  float
    width_mm:       float

class NeckRequest(BaseModel):
    shape:             str   = "C"      # C|D|U|V|asymC|slim
    depth_1st_mm:      float = 21.0
    depth_12th_mm:     float = 23.0
    shoulder_width_mm: float = 43.0
    asym_bass_add_mm:  float = 0.0

    # Fretboard coupling
    fb_thickness_mm:   float = 6.0
    fret_wire_mm:      float = 1.0
    radius_type:       str   = "single"   # single|compound
    r1_inch:           float = 12.0
    r2_inch:           float = 16.0
    fret_count:        int   = 22
    nut_width_mm:      float = 43.0
    width_12th_mm:     float = 56.0
    scale_length_mm:   float = 628.0

    # CNC
    ball_nose_mm:      float = 12.0
    stepover_pct:      float = 20.0
    feed_mm_min:       float = 1500.0
    depth_of_cut_mm:   float = 0.5

    # Pre-computed stations (optional — server computes if absent)
    profile_stations:  list[ProfileStation] = []
    label:             str = "Neck profile"

# ─── Geometry ─────────────────────────────────────────────────────────────────

def fret_position(n: int, scale: float) -> float:
    return scale - scale / (2 ** (n / 12))


def radius_at_fret(n: int, fret_count: int, r1: float, r2: float, rtype: str) -> float:
    if rtype == "single":
        return r1
    return r1 + (r2 - r1) * (n / fret_count)


def board_width_at_fret(n: int, fret_count: int, nut_w: float, w12: float) -> float:
    t = n / fret_count
    return nut_w + (w12 - nut_w) * t * 2


def sagitta(r_inch: float, w_mm: float) -> float:
    r = r_inch * INCH
    half = w_mm / 2
    if r < half:
        return 0.0
    return r - math.sqrt(r * r - half * half)


def crown_comp(n: int, req: NeckRequest) -> float:
    r = radius_at_fret(n, req.fret_count, req.r1_inch, req.r2_inch, req.radius_type)
    w = board_width_at_fret(n, req.fret_count, req.nut_width_mm, req.width_12th_mm)
    return sagitta(r, w)


def target_depth(n: int, req: NeckRequest) -> float:
    if n <= 12:
        return req.depth_1st_mm + (req.depth_12th_mm - req.depth_1st_mm) * (n / 12)
    return req.depth_12th_mm


def back_depth(n: int, req: NeckRequest) -> float:
    return (target_depth(n, req)
            - req.fret_wire_mm
            - req.fb_thickness_mm
            - crown_comp(n, req))


def neck_width_at(n: int, req: NeckRequest) -> float:
    w_last = req.shoulder_width_mm + (56 - req.shoulder_width_mm) * 2
    return req.shoulder_width_mm + (w_last - req.shoulder_width_mm) * (n / req.fret_count)


def shape_y(x_norm: float, depth: float, shape: str, asym_add: float = 0.0) -> float:
    """Y-offset from spine. Negative = into the neck (below top face)."""
    a = abs(x_norm)
    if shape == "C":
        return -depth * (1 - a ** 1.6)
    elif shape == "D":
        return -depth * (1 - a ** 2.4)
    elif shape == "U":
        return -depth * (1 - a ** 1.1)
    elif shape == "V":
        return -depth * (1 - a * 0.85)
    elif shape == "asymC":
        boost = asym_add if x_norm < 0 else 0.0
        return -(depth + boost) * (1 - a ** 1.6)
    elif shape == "slim":
        return -depth * (1 - a ** 3.2)
    return -depth * (1 - a ** 1.6)


def sample_profile(
    back_d: float, half_w: float,
    shape: str, asym_add: float = 0.0,
    steps: int = 64,
) -> list[tuple[float, float]]:
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (t - 0.5) * half_w * 2
        xn = x / half_w if half_w > 0 else 0
        y = shape_y(xn, back_d, shape, asym_add)
        pts.append((x, y))
    return pts


def stepover(ball: float, pct: float) -> float:
    return ball * pct / 100


def pass_count(width: float, ball: float, pct: float) -> int:
    step = stepover(ball, pct)
    return math.ceil((width + ball) / step) + 1

# ─── Build stations ────────────────────────────────────────────────────────────

def build_stations(req: NeckRequest) -> list[ProfileStation]:
    if req.profile_stations:
        return req.profile_stations
    return [
        ProfileStation(
            fret=n,
            position_mm=0.0 if n == 0 else fret_position(n, req.scale_length_mm),
            target_mm=target_depth(n, req),
            crown_comp_mm=crown_comp(n, req),
            back_depth_mm=back_depth(n, req),
            width_mm=neck_width_at(n, req),
        )
        for n in range(req.fret_count + 1)
    ]

# ─── DXF builder ──────────────────────────────────────────────────────────────

def build_neck_dxf(req: NeckRequest) -> ezdxf.document.Drawing:
    doc = ezdxf.new(dxfversion="R2010")
    doc.units = units.MM
    msp = doc.modelspace()

    for lname, col in [
        (LAYER_NUT_PROFILE,  1),
        (LAYER_12TH_PROFILE, 4),
        (LAYER_PROFILE_LAST, 3),
        (LAYER_TOOLPATH,     8),
        (LAYER_DIMENSION,    2),
        (LAYER_ANNOTATION,   9),
    ]:
        doc.layers.add(name=lname, color=col)

    stations = build_stations(req)
    nut  = stations[0]
    f12  = next((s for s in stations if s.fret == 12), stations[-1])
    last = stations[-1]

    layer_map = {nut.fret: LAYER_NUT_PROFILE, f12.fret: LAYER_12TH_PROFILE}

    for st in [nut, f12, last]:
        hw   = st.width_mm / 2
        bd   = st.back_depth_mm
        pts  = sample_profile(bd, hw, req.shape, req.asym_bass_add_mm)
        y    = st.position_mm
        lyr  = layer_map.get(st.fret, LAYER_PROFILE_LAST)

        # Profile cross-section polyline at this Y station
        # (XZ plane — X = width, Z = depth)
        dxf_pts = [(x, y, z) for x, z in pts]
        msp.add_polyline3d(dxf_pts, dxfattribs={"layer": lyr})

        # Closing lines (edges, Z=0 top face)
        msp.add_line((-hw, y, 0), (hw, y, 0), dxfattribs={"layer": lyr})

        # Dimension: back depth at spine
        msp.add_text(
            f"{'Nut' if st.fret == 0 else f'Fret {st.fret}'}  "
            f"back={bd:.3f}mm  crown_comp={st.crown_comp_mm:.4f}mm  "
            f"w={st.width_mm:.2f}mm",
            dxfattribs={"layer": LAYER_ANNOTATION, "height": 1.5},
        ).set_placement((hw + 3, y), align=TextEntityAlignment.LEFT)

    # Toolpath passes — one line per station, showing pass centreline
    for st in stations:
        hw    = st.width_mm / 2
        bd    = st.back_depth_mm
        y     = st.position_mm
        bn_r  = req.ball_nose_mm / 2
        step  = stepover(req.ball_nose_mm, req.stepover_pct)
        n_passes = pass_count(st.width_mm, req.ball_nose_mm, req.stepover_pct)

        for i in range(n_passes):
            x = -(hw + bn_r) + i * step
            xn = x / hw if hw > 0 else 0
            z_back = shape_y(min(1, max(-1, xn)), bd, req.shape, req.asym_bass_add_mm)
            z_tool = z_back - bn_r
            # Mark tool position as a short line in Z
            msp.add_line(
                (x, y, z_tool),
                (x, y, z_tool - 0.3),
                dxfattribs={"layer": LAYER_TOOLPATH},
            )

    # Title
    msp.add_text(
        f"{req.label}  {req.shape}-profile  "
        f"1st={req.depth_1st_mm}mm  12th={req.depth_12th_mm}mm  "
        f"coupling: {req.radius_type} r={req.r1_inch}\""
        + (f"→{req.r2_inch}\"" if req.radius_type == "compound" else ""),
        dxfattribs={"layer": LAYER_ANNOTATION, "height": 2.5},
    ).set_placement((0, -15), align=TextEntityAlignment.CENTER)

    return doc

# ─── G-code generator ─────────────────────────────────────────────────────────

def generate_neck_gcode(req: NeckRequest) -> str:
    stations  = build_stations(req)
    step      = stepover(req.ball_nose_mm, req.stepover_pct)
    lines = [
        f"; Production Shop — Neck back profile G-code",
        f"; Shape: {req.shape}  d1={req.depth_1st_mm}mm  d12={req.depth_12th_mm}mm",
        f"; FB coupling: thickness={req.fb_thickness_mm}mm  fret wire={req.fret_wire_mm}mm",
        f"; Radius: {req.radius_type} {req.r1_inch}\""
        + (f"→{req.r2_inch}\"" if req.radius_type == "compound" else ""),
        f"; Ball-nose Ø{req.ball_nose_mm}mm  step {step:.2f}mm  DOC {req.depth_of_cut_mm}mm",
        f"",
        f"G21 ; mm", f"G90 ; absolute", f"G00 Z5.000", f"",
    ]

    for st in stations:
        hw       = st.width_mm / 2
        bd       = st.back_depth_mm
        y        = st.position_mm
        bn_r     = req.ball_nose_mm / 2
        n_passes = pass_count(st.width_mm, req.ball_nose_mm, req.stepover_pct)

        lines += [
            f"; === {'NUT' if st.fret == 0 else f'Fret {st.fret}'}  Y={y:.3f}mm ===",
            f"; target={st.target_mm:.3f}mm  crown_comp={st.crown_comp_mm:.4f}mm  back={bd:.4f}mm",
            f"; {n_passes} passes",
            f"G00 Y{y:.3f}",
        ]

        for i in range(n_passes):
            x   = -(hw + bn_r) + i * step
            xn  = max(-1.0, min(1.0, x / hw)) if hw > 0 else 0.0
            z_s = shape_y(xn, bd, req.shape, req.asym_bass_add_mm)
            z_t = z_s - bn_r

            if i == 0:
                lines += [
                    f"G00 X{x:.3f} Z{z_t + 5:.4f}",
                    f"G01 Z{z_t:.4f} F{req.feed_mm_min * 0.4:.0f}  ; plunge",
                ]
            else:
                lines.append(f"G01 X{x:.3f} Y{y:.3f} Z{z_t:.4f} F{req.feed_mm_min:.0f}")

        lines += [f"G00 Z5.000", ""]

    lines.append("M30  ; end of program")
    return "\n".join(lines)

# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/dxf")
async def neck_profile_dxf(req: NeckRequest):
    """Generate neck back profile DXF with cross-sections and toolpath layer."""
    try:
        doc = build_neck_dxf(req)
    except Exception as e:
        raise HTTPException(422, f"DXF error: {e}")
    buf = io.BytesIO()
    doc.write(buf); buf.seek(0)
    fn = req.label.lower().replace(" ", "-") or "neck-profile"
    return StreamingResponse(buf, media_type="application/dxf",
                             headers={"Content-Disposition": f'attachment; filename="{fn}.dxf"'})


@router.post("/gcode")
async def neck_profile_gcode(req: NeckRequest):
    """Generate back profile sweep G-code for BCAM 2030A."""
    try:
        code = generate_neck_gcode(req)
    except Exception as e:
        raise HTTPException(422, f"G-code error: {e}")
    fn = req.label.lower().replace(" ", "-") or "neck-profile"
    return PlainTextResponse(code,
                             headers={"Content-Disposition": f'attachment; filename="{fn}.nc"'})


@router.post("/stations")
async def neck_stations(req: NeckRequest):
    """Return per-fret station table with full coupling breakdown."""
    stations = build_stations(req)
    return {
        "stations": [s.dict() for s in stations],
        "coupling_note": (
            "back_depth = target_total - fret_wire - fb_thickness - crown_compensation. "
            f"Crown varies {crown_comp(0, req):.4f}mm (nut) → "
            f"{crown_comp(req.fret_count, req):.4f}mm (body end) "
            f"for {req.radius_type} radius."
        ),
    }
