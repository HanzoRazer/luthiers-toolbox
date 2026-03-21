"""
Production Shop — Headstock Transition & Volute Export Service
==============================================================

Generates:
  1. DXF with transition zone cross-sections at key Y stations
     — Layers: HS_TRANS_NECK, HS_TRANS_BLEND, HS_TRANS_HEAD, HS_VOLUTE, HS_ANNOTATION
  2. G-code for the BCAM 2030A 3-axis finishing pass across the transition zone
     — Ball-nose sweep following the blended 3D surface
     — Volute bump or scallop added to Z values per station

Coordinate convention (VINE-05):
    Y = 0   at nut centreline
    +Y      toward bridge/body
    -Y      toward headstock tip
    X = 0   centreline
    Z = 0   top face (fretboard surface)
    -Z      into the neck back

Geometry:
    headstock plane:  Z_hs(y)  = -hs_thickness + (-y) × tan(pitch_angle)
    neck back:        Z_neck   = -neck_depth_mm  (constant)
    blend:            Z_blend(y) = hermite(Z_neck, Z_hs, t) where t = smoothstep(y)
    volute:           Z_vol(y)   = height × exp(-(y - y_centre)² / (2σ²))
    total:            Z(y) = Z_blend(y) + Z_vol(y)

Add to main.py:
    from headstock_transition_export import router as trans_router
    app.include_router(trans_router, prefix="/api/headstock/transition")
"""

from __future__ import annotations

import io
import math
from typing import Optional

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["headstock-transition"])

# ─── Layer names ──────────────────────────────────────────────────────────────

LAYER_NECK    = "HS_TRANS_NECK"
LAYER_BLEND   = "HS_TRANS_BLEND"
LAYER_HEAD    = "HS_TRANS_HEAD"
LAYER_VOLUTE  = "HS_VOLUTE"
LAYER_ANNOT   = "HS_ANNOTATION"

# ─── Request model ────────────────────────────────────────────────────────────

class TransitionRequest(BaseModel):
    headstock_type:     str   = Field("angled", description="angled | flat")
    pitch_angle_deg:    float = Field(14.0,  ge=0, le=17)
    hs_thickness_mm:    float = Field(14.0,  gt=0)
    neck_depth_mm:      float = Field(21.0,  gt=0)
    nut_width_mm:       float = Field(43.0,  gt=0)

    blend_length_mm:    float = Field(22.0,  gt=0)
    blend_centre_mm:    float = Field(5.0)       # +ve=body side of nut
    blend_tension:      float = Field(50.0, ge=0, le=100)  # 0=linear, 100=smoothstep

    volute_type:        str   = Field("none", description="none | gibson | martin | custom | scallop")
    volute_height_mm:   float = Field(4.0,   ge=0)
    volute_position_mm: float = Field(-12.0)     # -ve = toward headstock
    vol_sigma_mm:       float = Field(12.0,  gt=0)
    # Martin tent/pyramid parameters (used when volute_type == "martin")
    vol_half_width_mm:  float = Field(14.0,  gt=0)   # mm each side of ridge
    vol_sharpness:      float = Field(0.8,   gt=0)   # 1.0=pyramid, <1=flared, >1=steep

    ball_nose_mm:       float = Field(9.525, gt=0)   # 3/8" repo T3
    stepover_pct:       float = Field(12.0,  gt=0, le=50)
    feed_mm_min:        float = Field(1200.0,gt=0)

    y_margin_mm:        float = Field(5.0,   ge=0)  # overrun each side of blend zone
    label:              str   = "HS_Transition"

# ─── Pure geometry ────────────────────────────────────────────────────────────

def _hs_plane_z(y: float, r: TransitionRequest) -> float:
    ang = math.radians(r.pitch_angle_deg)
    return -r.hs_thickness_mm + (-y) * math.tan(ang)


def _neck_z(r: TransitionRequest) -> float:
    return -r.neck_depth_mm


def _blend_z(y: float, r: TransitionRequest) -> float:
    start = r.blend_centre_mm - r.blend_length_mm / 2
    end   = r.blend_centre_mm + r.blend_length_mm / 2
    t     = max(0.0, min(1.0, (y - start) / r.blend_length_mm))
    k     = r.blend_tension / 100
    ts    = t * t * (3 - 2 * t) * k + t * (1 - k)
    return _neck_z(r) * (1 - ts) + _hs_plane_z(y, r) * ts


def _volute_z(y: float, r: TransitionRequest) -> float:
    """
    Volute Z contribution at position Y.

    Types:
      gibson / custom   — Gaussian bell curve (smooth swell)
        Z = h × exp(-(y - y_c)² / 2σ²)

      martin            — Faceted tent / truncated pyramid
        The classic pre-war Martin diamond volute: two faces meeting at
        a ridge, with sharpness controlling the face angle.
          t = max(0, 1 - |y - y_c| / half_width)
          Z = h × t^sharpness
        sharpness=1.0 → true linear pyramid
        sharpness<1.0 → flared base (typical Martin: 0.7–0.9)
        sharpness>1.0 → steep narrow crown

      scallop           — Inverted Gaussian (concave decorative hollow)
    """
    if r.volute_type == "none":
        return 0.0

    dy = y - r.volute_position_mm

    if r.volute_type == "martin":
        t = max(0.0, 1.0 - abs(dy) / r.vol_half_width_mm)
        return r.volute_height_mm * (t ** r.vol_sharpness)

    g = math.exp(-dy * dy / (2.0 * r.vol_sigma_mm * r.vol_sigma_mm))
    if r.volute_type == "scallop":
        return -r.volute_height_mm * g * 0.6
    return r.volute_height_mm * g


def _surface_z(y: float, r: TransitionRequest) -> float:
    start = r.blend_centre_mm - r.blend_length_mm / 2
    end   = r.blend_centre_mm + r.blend_length_mm / 2
    if y < start:
        base = _hs_plane_z(y, r)
    elif y <= end:
        base = _blend_z(y, r)
    else:
        base = _neck_z(r)
    return base + _volute_z(y, r)


def _region(y: float, r: TransitionRequest) -> str:
    start = r.blend_centre_mm - r.blend_length_mm / 2
    end   = r.blend_centre_mm + r.blend_length_mm / 2
    if y < start: return "headstock"
    if y <= end:  return "blend"
    return "neck"


def _thin_point_mm(r: TransitionRequest) -> float:
    y = r.volute_position_mm if r.volute_type != "none" else -10.0
    return -_hs_plane_z(y, r)


def _shape_z(x_norm: float, back_depth: float, shape: str = "C") -> float:
    """Profile Z at normalised X position. Returns depth below back surface."""
    a = abs(x_norm)
    if shape == "D": return -back_depth * (1 - a ** 2.4)
    if shape == "U": return -back_depth * (1 - a ** 1.1)
    if shape == "V": return -back_depth * (1 - a * 0.85)
    return -back_depth * (1 - a ** 1.6)   # default C

# ─── DXF builder ─────────────────────────────────────────────────────────────

def build_transition_dxf(r: TransitionRequest) -> ezdxf.document.Drawing:
    doc = ezdxf.new(dxfversion="R2010")
    doc.units = units.MM
    msp = doc.modelspace()

    for name, col in [(LAYER_NECK,1),(LAYER_BLEND,4),(LAYER_HEAD,5),(LAYER_VOLUTE,3),(LAYER_ANNOT,9)]:
        doc.layers.add(name=name, color=col)

    y_start = r.blend_centre_mm - r.blend_length_mm / 2 - r.y_margin_mm
    y_end   = r.blend_centre_mm + r.blend_length_mm / 2 + r.y_margin_mm
    n_stations = 20

    for i in range(n_stations + 1):
        y   = y_start + (y_end - y_start) * i / n_stations
        hw  = r.nut_width_mm / 2 + max(0.0, y) * 0.07
        sz  = _surface_z(y, r)
        reg = _region(y, r)
        lyr = {
            "headstock": LAYER_HEAD,
            "blend":     LAYER_BLEND,
            "neck":      LAYER_NECK,
        }[reg]

        # Cross-section polyline at this Y station (XZ plane)
        pts = []
        for xi in range(33):
            xn = (xi / 32) * 2 - 1
            x  = xn * hw
            z  = _shape_z(xn, -sz) + sz + _volute_z(y, r)
            pts.append((x, y, z))

        msp.add_polyline3d(pts, dxfattribs={"layer": lyr})
        # Close top edge
        msp.add_line((-hw, y, 0.0), (hw, y, 0.0), dxfattribs={"layer": lyr})

        # Volute layer for volute-affected stations
        if r.volute_type != "none" and abs(_volute_z(y, r)) > 0.01:
            pts_v = []
            for xi in range(17):
                xn = (xi / 16) * 2 - 1
                x  = xn * hw
                z  = _surface_z(y, r)
                pts_v.append((x, y, z))
            msp.add_polyline3d(pts_v, dxfattribs={"layer": LAYER_VOLUTE})

    # Annotations
    thin = _thin_point_mm(r)
    msp.add_text(
        f"{r.label}  {r.headstock_type}  {r.pitch_angle_deg}°  "
        f"blend {r.blend_length_mm}mm  volute:{r.volute_type}  "
        f"thin_point={thin:.2f}mm",
        dxfattribs={"layer": LAYER_ANNOT, "height": 2.0},
    ).set_placement((0.0, r.blend_centre_mm - 20), align=TextEntityAlignment.CENTER)

    return doc

# ─── G-code generator ─────────────────────────────────────────────────────────

def build_transition_gcode(r: TransitionRequest) -> str:
    y_start  = r.blend_centre_mm - r.blend_length_mm / 2 - r.y_margin_mm
    y_end    = r.blend_centre_mm + r.blend_length_mm / 2 + r.y_margin_mm
    hw       = r.nut_width_mm / 2 + 3.0
    bn_r     = r.ball_nose_mm / 2
    step     = r.ball_nose_mm * r.stepover_pct / 100
    n_passes = math.ceil((hw * 2 + r.ball_nose_mm) / step) + 1
    y_stations = 20

    lines = [
        f"; Headstock Transition Zone — Production Shop",
        f"; {r.label}  {r.headstock_type}  {r.pitch_angle_deg}°",
        f"; Y: {y_start:.1f}mm → {y_end:.1f}mm  (VINE-05: Y=0 at nut)",
        f"; Blend: {r.blend_length_mm}mm centred at Y={r.blend_centre_mm}mm",
        f"; Volute: {r.volute_type}"
        + (f" h={r.volute_height_mm}mm @ Y={r.volute_position_mm}mm σ={r.vol_sigma_mm}mm"
           if r.volute_type != "none" else ""),
        f"; Ball-nose Ø{r.ball_nose_mm}mm  step {step:.2f}mm  {n_passes} passes/station",
        f"; Thin point: {_thin_point_mm(r):.2f}mm",
        "", "G21  ; mm", "G90  ; absolute", "G00 Z5.000", "",
    ]

    for si in range(y_stations + 1):
        y   = y_start + (y_end - y_start) * si / y_stations
        sz  = _surface_z(y, r)
        reg = _region(y, r)
        hw_y = r.nut_width_mm / 2 + max(0.0, y) * 0.07

        lines += [
            f"; === Y={y:.3f}mm  region:{reg}  surface_z={sz:.4f}mm ===",
            f"G00 Y{y:.3f}",
        ]

        for i in range(n_passes):
            x   = -(hw_y + bn_r) + i * step
            xn  = max(-1.0, min(1.0, x / hw_y)) if hw_y > 0 else 0.0
            # Back surface Z at this station, profile-shaped in X
            back_depth = -sz
            z_profile  = _shape_z(xn, back_depth) + sz + _volute_z(y, r)
            z_tool     = z_profile - bn_r   # tool centre

            if i == 0:
                lines += [
                    f"G00 X{x:.3f} Z{z_tool + 5:.4f}",
                    f"G01 Z{z_tool:.4f} F{r.feed_mm_min * 0.4:.0f}  ; plunge",
                ]
            else:
                lines.append(f"G01 X{x:.3f} Y{y:.3f} Z{z_tool:.4f} F{r.feed_mm_min:.0f}")

        lines += ["G00 Z5.000", ""]

    lines.append("M30  ; end transition zone")
    return "\n".join(lines)

# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/dxf")
async def transition_dxf(r: TransitionRequest):
    """
    Generate headstock transition zone DXF with cross-section layers.

    Layers:
      HS_TRANS_NECK  — neck back region cross-sections
      HS_TRANS_BLEND — transition blend region
      HS_TRANS_HEAD  — headstock plane region
      HS_VOLUTE      — volute-affected stations
      HS_ANNOTATION  — dimensions and notes
    """
    try:
        doc = build_transition_dxf(r)
    except Exception as e:
        raise HTTPException(422, f"DXF error: {e}")
    buf = io.BytesIO(); doc.write(buf); buf.seek(0)
    fn = r.label.lower().replace(" ", "-") or "hs-transition"
    return StreamingResponse(buf, media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{fn}.dxf"'})


@router.post("/gcode")
async def transition_gcode(r: TransitionRequest):
    """
    Generate BCAM 3-axis ball-nose G-code for the headstock transition zone.
    Crown compensation is not applied here — this surfaces the geometric
    interface between neck profile and headstock plane.
    """
    try:
        code = build_transition_gcode(r)
    except Exception as e:
        raise HTTPException(422, f"G-code error: {e}")
    fn = r.label.lower().replace(" ", "-") or "hs-transition"
    return PlainTextResponse(code,
        headers={"Content-Disposition": f'attachment; filename="{fn}.nc"'})


@router.post("/analysis")
async def transition_analysis(r: TransitionRequest):
    """
    Return full geometry analysis: thin point, blend delta, volute contribution,
    and gate results — without generating DXF or G-code.
    """
    thin = _thin_point_mm(r)
    ang  = math.radians(r.pitch_angle_deg)
    gates = []

    if r.headstock_type == "angled":
        if thin < 8:
            gates.append({"key":"thin","status":"fail","label":f"Thin point {thin:.2f}mm — below 8mm minimum. Grain failure risk."})
        elif thin < 12:
            gates.append({"key":"thin","status":"warn","label":f"Thin point {thin:.2f}mm — volute recommended for {r.pitch_angle_deg}° pitch."})
        else:
            gates.append({"key":"thin","status":"pass","label":f"Thin point {thin:.2f}mm — adequate."})
    else:
        gates.append({"key":"thin","status":"pass","label":"Flat headstock — no grain weakness."})

    if r.volute_type != "none" and r.headstock_type == "angled":
        if r.volute_height_mm < 3 and r.pitch_angle_deg > 12:
            gates.append({"key":"vol","status":"warn","label":f"Volute {r.volute_height_mm}mm may be marginal for {r.pitch_angle_deg}° — use 4–6mm."})
        else:
            gates.append({"key":"vol","status":"pass","label":f"Volute +{r.volute_height_mm}mm reinforces grain at weak point."})

    # Sample stations
    stations = []
    y_range = range(int(r.blend_centre_mm - r.blend_length_mm/2 - r.y_margin_mm),
                    int(r.blend_centre_mm + r.blend_length_mm/2 + r.y_margin_mm) + 1, 2)
    for y in y_range:
        stations.append({
            "y_mm":          y,
            "region":        _region(y, r),
            "surface_z_mm":  round(_surface_z(y, r), 4),
            "volute_z_mm":   round(_volute_z(y, r), 4),
            "hs_plane_z_mm": round(_hs_plane_z(y, r), 4),
        })

    return JSONResponse({
        "thin_point_mm":      round(thin, 2),
        "hs_drop_at_30mm":    round(30 * math.tan(ang), 2),
        "blend_entry_z_mm":   round(_surface_z(r.blend_centre_mm - r.blend_length_mm/2, r), 3),
        "blend_exit_z_mm":    round(_surface_z(r.blend_centre_mm + r.blend_length_mm/2, r), 3),
        "volute_peak_z_mm":   round(_volute_z(r.volute_position_mm, r), 3) if r.volute_type != "none" else 0,
        "gates":              gates,
        "stations":           stations,
    })
