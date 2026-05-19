"""
Production Shop — Fretboard Radius Export Service
FastAPI router that generates:

  1. Fretboard DXF with:
     - Outline with taper (nut width → body width)
     - Fret slot positions and widths on correct layer
     - Radius arc annotations at nut, 12th, and last fret
     - Nut slot positions and depths

  2. Ball-nose toolpath G-code for the BCAMCNC 2030A:
     - Per-fret-station passes following the radius arc
     - Compound radius support (linearly interpolated)
     - Configurable step-over, feed, depth of cut

Add to main.py:
    from fretboard_export import router as fb_router
    app.include_router(fb_router, prefix="/api/fretboard")
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

router = APIRouter(tags=["fretboard"])

INCH = 25.4

# ─── Layer names ──────────────────────────────────────────────────────────────

LAYER_OUTLINE    = "FB_OUTLINE"
LAYER_FRET_SLOTS = "FB_FRET_SLOTS"
LAYER_NUT_SLOT   = "FB_NUT_SLOT"
LAYER_RADIUS_ARC = "FB_RADIUS_ARC"
LAYER_TOOLPATH   = "FB_TOOLPATH"
LAYER_ANNOTATION = "FB_ANNOTATION"

# ─── Pydantic models ──────────────────────────────────────────────────────────

class FretStation(BaseModel):
    fret:         int
    position_mm:  float
    radius_inch:  float
    width_mm:     float
    crown_mm:     float

class NutSlot(BaseModel):
    string:    int
    depth_mm:  float
    width_mm:  float

class FretboardRequest(BaseModel):
    radius_type:      str   = "single"    # "single" | "compound"
    r1_inch:          float = 12.0
    r2_inch:          float = 16.0
    scale_length_mm:  float = 628.0
    fret_count:       int   = 22
    nut_width_mm:     float = 43.0
    width_12th_mm:    float = 56.0
    thickness_mm:     float = 6.0
    fret_slot_depth:  float = 0.55        # mm (fret tang depth)
    fret_slot_width:  float = 0.56        # mm (standard tang width)
    ball_nose_mm:     float = 6.0
    stepover_pct:     float = 15.0
    feed_mm_min:      float = 1200.0
    depth_of_cut_mm:  float = 0.3
    fret_stations:    list[FretStation] = []
    nut_slots:        list[NutSlot]     = []
    label:            str   = "Fretboard"

# ─── Geometry helpers ─────────────────────────────────────────────────────────

def fret_position(n: int, scale: float) -> float:
    """Equal temperament fret position from nut (mm)."""
    return scale - scale / (2 ** (n / 12))


def board_width_at_fret(n: int, fret_count: int, nut_w: float, w12: float) -> float:
    """Linear taper nut→body (extrapolated from 12th fret width)."""
    t = n / fret_count
    return nut_w + (w12 - nut_w) * t * 2


def radius_at_fret(n: int, fret_count: int, r1: float, r2: float, rtype: str) -> float:
    if rtype == "single":
        return r1
    t = n / fret_count
    return r1 + (r2 - r1) * t


def sagitta(r_inch: float, w_mm: float) -> float:
    """Crown height h = r - sqrt(r² - (w/2)²)."""
    r = r_inch * INCH
    half = w_mm / 2
    if r < half:
        return 0.0
    return r - math.sqrt(r * r - half * half)


def stepover_mm(ball_nose: float, pct: float) -> float:
    return ball_nose * pct / 100


def pass_count(width: float, ball_nose: float, pct: float) -> int:
    step = stepover_mm(ball_nose, pct)
    return math.ceil((width + ball_nose) / step) + 1

# ─── Build fret station list (server-side if not provided by client) ──────────

def build_fret_stations(req: FretboardRequest) -> list[FretStation]:
    if req.fret_stations:
        return req.fret_stations
    stations = []
    for i in range(req.fret_count + 1):
        pos   = 0.0 if i == 0 else fret_position(i, req.scale_length_mm)
        r     = radius_at_fret(i, req.fret_count, req.r1_inch, req.r2_inch, req.radius_type)
        w     = board_width_at_fret(i, req.fret_count, req.nut_width_mm, req.width_12th_mm)
        crown = sagitta(r, w)
        stations.append(FretStation(fret=i, position_mm=pos, radius_inch=r, width_mm=w, crown_mm=crown))
    return stations

# ─── DXF builder ─────────────────────────────────────────────────────────────

def build_fretboard_dxf(req: FretboardRequest) -> ezdxf.document.Drawing:
    doc = ezdxf.new(dxfversion="R2010")
    doc.units = units.MM
    msp = doc.modelspace()

    # Layers
    doc.layers.add(LAYER_OUTLINE,    color=1)   # red
    doc.layers.add(LAYER_FRET_SLOTS, color=3)   # green
    doc.layers.add(LAYER_NUT_SLOT,   color=5)   # blue
    doc.layers.add(LAYER_RADIUS_ARC, color=4)   # cyan
    doc.layers.add(LAYER_TOOLPATH,   color=8)   # gray
    doc.layers.add(LAYER_ANNOTATION, color=9)

    stations = build_fret_stations(req)
    nut = stations[0]
    last = stations[-1]

    # ── Fretboard outline (trapezoidal taper) ─────────────────────────────────
    nut_w  = req.nut_width_mm
    last_w = last.width_mm
    length = last.position_mm

    outline = [
        (-nut_w / 2,    0.0),
        ( nut_w / 2,    0.0),
        ( last_w / 2,   length),
        (-last_w / 2,   length),
    ]
    msp.add_lwpolyline(outline, close=True,
                       dxfattribs={"layer": LAYER_OUTLINE})

    # ── Fret slots ────────────────────────────────────────────────────────────
    for st in stations[1:]:   # skip nut (station 0)
        y   = st.position_mm
        hw  = st.width_mm / 2
        # Slot line (full width of board at that fret)
        msp.add_line(
            (-hw, y), (hw, y),
            dxfattribs={"layer": LAYER_FRET_SLOTS},
        )
        # Slot width annotation on every 3rd fret
        if st.fret % 3 == 0:
            msp.add_text(
                f"{st.fret}",
                dxfattribs={"layer": LAYER_ANNOTATION, "height": 1.5},
            ).set_placement((hw + 2, y), align=TextEntityAlignment.LEFT)

    # ── Nut slot ──────────────────────────────────────────────────────────────
    msp.add_line(
        (-nut_w / 2, 0.0), (nut_w / 2, 0.0),
        dxfattribs={"layer": LAYER_NUT_SLOT},
    )

    # ── Radius arc annotations (nut, 12th, last) ──────────────────────────────
    annotation_frets = [0, 12, req.fret_count]
    for fn in annotation_frets:
        if fn >= len(stations):
            continue
        st = stations[fn]
        r_mm = st.radius_inch * INCH
        w    = st.width_mm
        y    = st.position_mm
        # Draw the arc centred below the board surface
        # Arc spans the full board width at this fret
        half_chord = w / 2
        if r_mm >= half_chord:
            start_angle = math.degrees(math.asin(half_chord / r_mm))
            # Centre of arc is r_mm below the surface
            cx_arc = 0.0
            cy_arc = y - r_mm   # below surface (positive Z = up in DXF)
            msp.add_arc(
                center=(cx_arc, cy_arc),
                radius=r_mm,
                start_angle=90 - start_angle,
                end_angle=90 + start_angle,
                dxfattribs={"layer": LAYER_RADIUS_ARC},
            )
        msp.add_text(
            f'r={st.radius_inch:.2f}"  crown={st.crown_mm:.4f}mm',
            dxfattribs={"layer": LAYER_ANNOTATION, "height": 1.5},
        ).set_placement((last_w / 2 + 4, y), align=TextEntityAlignment.LEFT)

    # ── Toolpath preview lines on TOOLPATH layer (one pass stripe per station) ─
    for st in stations:
        y    = st.position_mm
        w    = st.width_mm
        r_mm = st.radius_inch * INCH
        step = stepover_mm(req.ball_nose_mm, req.stepover_pct)
        n    = pass_count(w, req.ball_nose_mm, req.stepover_pct)
        bn_r = req.ball_nose_mm / 2

        for i in range(n):
            x = -(w / 2 + bn_r) + i * step
            # Annotate first pass of nut and 12th only
            if st.fret in (0, 12) and i == 0:
                msp.add_text(
                    f"{n} passes",
                    dxfattribs={"layer": LAYER_TOOLPATH, "height": 1.2},
                ).set_placement((-w / 2 - bn_r - 8, y), align=TextEntityAlignment.RIGHT)
            # Tool centre path line (tiny dash at each pass centre)
            msp.add_line((x, y - 0.5), (x, y + 0.5),
                         dxfattribs={"layer": LAYER_TOOLPATH})

    # ── Title block ───────────────────────────────────────────────────────────
    msp.add_text(
        f"{req.label}  {req.radius_type.title()} radius  {req.r1_inch}\""
        + (f"→{req.r2_inch}\"" if req.radius_type == "compound" else "")
        + f"  scale {req.scale_length_mm}mm  {req.fret_count} frets",
        dxfattribs={"layer": LAYER_ANNOTATION, "height": 2.5},
    ).set_placement((-nut_w / 2, -12), align=TextEntityAlignment.LEFT)

    return doc

# ─── G-code generator ─────────────────────────────────────────────────────────

def generate_gcode(req: FretboardRequest) -> str:
    stations = build_fret_stations(req)
    lines = [
        f"; Production Shop — Fretboard radius sweep G-code",
        f"; {req.label}  {req.radius_type} radius  r1={req.r1_inch}\"",
        f"; Scale {req.scale_length_mm}mm  {req.fret_count} frets",
        f"; Ball-nose Ø{req.ball_nose_mm}mm  Step {stepover_mm(req.ball_nose_mm, req.stepover_pct):.2f}mm  DOC {req.depth_of_cut_mm}mm",
        f"; Feed {req.feed_mm_min}mm/min",
        f"",
        f"G21  ; mm",
        f"G90  ; absolute",
        f"G00 Z5.000",
        f"",
    ]

    for st in stations:
        r_mm = st.radius_inch * INCH
        w    = st.width_mm
        y    = st.position_mm
        bn_r = req.ball_nose_mm / 2
        step = stepover_mm(req.ball_nose_mm, req.stepover_pct)
        n    = pass_count(w, req.ball_nose_mm, req.stepover_pct)

        lines += [
            f"; === {'NUT' if st.fret == 0 else f'Fret {st.fret}'}  Y={y:.3f}mm ===",
            f"; r={st.radius_inch:.3f}\"  w={w:.2f}mm  crown={st.crown_mm:.4f}mm  {n} passes",
            f"G00 Y{y:.3f}",
        ]

        for i in range(n):
            x = -(w / 2 + bn_r) + i * step
            # Ball-nose centre Z following the radius arc
            if abs(x) <= r_mm:
                z_arc = -(r_mm - math.sqrt(r_mm * r_mm - x * x))
            else:
                z_arc = 0.0
            z_tool = z_arc + bn_r   # tool centre above surface

            if i == 0:
                lines += [
                    f"G00 X{x:.3f} Z{z_tool + 5:.4f}",
                    f"G01 Z{z_tool:.4f} F{req.feed_mm_min * 0.4:.0f}  ; plunge",
                ]
            else:
                lines.append(f"G01 X{x:.3f} Z{z_tool:.4f} F{req.feed_mm_min:.0f}")

        lines += [f"G00 Z5.000", ""]

    lines.append(f"M30  ; end of program")
    return "\n".join(lines)

# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/dxf")
async def fretboard_dxf(req: FretboardRequest):
    """Generate fretboard DXF with outline, fret slots, radius arcs, toolpath layer."""
    try:
        doc = build_fretboard_dxf(req)
    except Exception as e:
        raise HTTPException(422, f"DXF error: {e}")
    buf = io.BytesIO()
    doc.write(buf)
    buf.seek(0)
    fn = req.label.lower().replace(" ", "-") or "fretboard"
    return StreamingResponse(buf, media_type="application/dxf",
                             headers={"Content-Disposition": f'attachment; filename="{fn}.dxf"'})


@router.post("/gcode")
async def fretboard_gcode(req: FretboardRequest):
    """Generate ball-nose sweep G-code for BCAMCNC 2030A."""
    try:
        gcode = generate_gcode(req)
    except Exception as e:
        raise HTTPException(422, f"G-code error: {e}")
    fn = req.label.lower().replace(" ", "-") or "fretboard"
    return PlainTextResponse(gcode,
                             headers={"Content-Disposition": f'attachment; filename="{fn}.nc"'})


@router.post("/stations")
async def fretboard_stations(req: FretboardRequest):
    """Return fret station table (position, radius, width, crown) as JSON."""
    stations = build_fret_stations(req)
    return {
        "stations": [s.dict() for s in stations],
        "derived": {
            "crown_nut_mm":   stations[0].crown_mm  if stations else 0,
            "crown_12th_mm":  next((s.crown_mm for s in stations if s.fret == 12), 0),
            "crown_last_mm":  stations[-1].crown_mm if stations else 0,
            "max_width_mm":   stations[-1].width_mm if stations else 0,
            "total_passes_last": pass_count(
                stations[-1].width_mm if stations else 0,
                req.ball_nose_mm, req.stepover_pct
            ),
        },
    }
