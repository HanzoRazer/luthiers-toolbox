"""
Production Shop — Neck Profile Export Service  (Correction 3)
==============================================================

Delegates G-code generation to the existing cam/neck/ pipeline rather
than reimplementing it.  The NeckPipeline orchestrator in the repo
already chains:

    OP10  TrussRodChannelGenerator   (truss_rod_channel.py)
    OP40  ProfileCarvingGenerator    (profile_carving.py)  — roughing
    OP45  ProfileCarvingGenerator                          — finishing
    OP50  FretSlotGenerator          (fret_slots.py)

Coordinate convention (VINE-05 — repo standard):
    Y = 0   at nut centerline
    +Y      toward bridge
    X = 0   centerline

Back-depth coupling is computed here from the fretboard spec before
building the NeckPipelineConfig, so the crown compensation is baked in
before the pipeline sees the depth values.

Add to main.py:
    from neck_profile_export import router as neck_router
    app.include_router(neck_router, prefix="/api/neck")
"""

from __future__ import annotations

import io
import math
import sys
import os
from typing import Optional

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field

# ─── Import repo pipeline ─────────────────────────────────────────────────────
# Adjust this path to match your project layout.  The cam/neck package lives at:
#   services/api/app/cam/neck/
try:
    from app.cam.neck.config import (
        NeckPipelineConfig, NeckProfileType, MaterialType,
        TrussRodConfig, ProfileCarvingConfig, FretSlotConfig,
    )
    from app.cam.neck.orchestrator import NeckPipeline
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False   # graceful degradation — falls back to inline G-code

router = APIRouter(tags=["neck"])

INCH = 25.4

# ─── Layer names ──────────────────────────────────────────────────────────────

LAYER_PROFILE_NUT  = "NK_PROFILE_NUT"
LAYER_PROFILE_12TH = "NK_PROFILE_12TH"
LAYER_PROFILE_LAST = "NK_PROFILE_LAST"
LAYER_TOOLPATH     = "NK_TOOLPATH"
LAYER_ANNOTATION   = "NK_ANNOTATION"

# ─── Models ───────────────────────────────────────────────────────────────────

class NeckRequest(BaseModel):
    # Profile shape
    shape:             str   = Field("C", description="C|D|U|V|asymC|slim|C→V|U→C|V→C|C→D|D→U")
    depth_1st_mm:      float = 21.0
    depth_12th_mm:     float = 23.0
    shoulder_width_mm: float = 43.0
    heel_width_mm:     float = 56.0
    asym_bass_add_mm:  float = 0.0

    # Fretboard coupling (crown compensation)
    fb_thickness_mm:   float = 6.0
    fret_wire_mm:      float = 1.0
    radius_type:       str   = "single"   # single|compound
    r1_inch:           float = 12.0
    r2_inch:           float = 16.0
    fret_count:        int   = 22
    nut_width_mm:      float = 43.0
    width_12th_mm:     float = 56.0
    scale_length_mm:   float = 628.0

    # Truss rod — defaults from repo cam/neck/config.py TrussRodConfig
    rod_width_mm:      float = 6.35    # 1/4"
    rod_depth_mm:      float = 9.525   # 3/8"
    rod_length_mm:     float = 406.4   # 16"
    rod_start_offset:  float = 12.7    # 1/2" from nut

    # CNC
    ball_nose_mm:      float = 9.525   # T3: 3/8" finish ball — from repo
    stepover_pct:      float = 15.0    # Finish pass stepover
    feed_mm_min:       float = 1500.0
    depth_of_cut_mm:   float = 0.5
    material:          str   = "maple" # maple|mahogany|rosewood|ebony|walnut

    label:             str   = "Neck profile"
    include_fret_slots:bool  = False   # Typically separate operation

# ─── Geometry helpers (crown compensation) ───────────────────────────────────

def radius_at_fret(n: int, fret_count: int, r1: float, r2: float, rtype: str) -> float:
    if rtype == "single":
        return r1
    return r1 + (r2 - r1) * (n / fret_count)


def crown_comp(n: int, req: NeckRequest) -> float:
    """Sagitta height = r - sqrt(r² - (w/2)²) at fret n."""
    r = radius_at_fret(n, req.fret_count, req.r1_inch, req.r2_inch, req.radius_type) * INCH
    # Board width at fret n using distance-based formula (repo taper_math.py)
    x_f = 0.0 if n == 0 else req.scale_length_mm * (1 - 1 / (2 ** (n / 12)))
    L_N = req.scale_length_mm * (1 - 1 / (2 ** (req.fret_count / 12)))
    t = x_f / L_N if L_N > 0 else 0
    w = req.nut_width_mm + t * (req.width_12th_mm * 2 - req.nut_width_mm) / 2
    # Sagitta
    half = w / 2
    if r < half:
        return 0.0
    return r - math.sqrt(r * r - half * half)


def back_depth(n: int, req: NeckRequest) -> float:
    """
    Back wood depth after fretboard coupling:
      back = target_total - fret_wire - fb_thickness - crown_comp(n)
    """
    if n <= 12:
        target = req.depth_1st_mm + (req.depth_12th_mm - req.depth_1st_mm) * (n / 12)
    else:
        target = req.depth_12th_mm
    return target - req.fret_wire_mm - req.fb_thickness_mm - crown_comp(n, req)


def shape_y(x_norm: float, depth: float, shape: str, asym_add: float = 0.0) -> float:
    """Profile Y-offset. Negative = into neck."""
    a = abs(x_norm)
    base = shape.split("→")[0] if "→" in shape else shape
    if base == "C":     return -depth * (1 - a ** 1.6)
    elif base == "D":   return -depth * (1 - a ** 2.4)
    elif base == "U":   return -depth * (1 - a ** 1.1)
    elif base == "V":   return -depth * (1 - a * 0.85)
    elif base == "asymC":
        boost = asym_add if x_norm < 0 else 0.0
        return -(depth + boost) * (1 - a ** 1.6)
    elif base == "slim": return -depth * (1 - a ** 3.2)
    return -depth * (1 - a ** 1.6)


# ─── NeckPipelineConfig builder ───────────────────────────────────────────────

def build_pipeline_config(req: NeckRequest) -> "NeckPipelineConfig":
    """
    Map NeckRequest → NeckPipelineConfig.
    Crown compensation is applied to depth values here so the pipeline
    receives already-compensated back depths.
    """
    mat_map = {
        "maple":     "MAPLE",
        "mahogany":  "MAHOGANY",
        "rosewood":  "ROSEWOOD",
        "ebony":     "EBONY",
        "walnut":    "WALNUT",
    }
    mat_str = mat_map.get(req.material.lower(), "MAPLE")
    material = MaterialType[mat_str]

    shape_map = {
        "C": "C_SHAPE", "D": "D_SHAPE", "V": "V_SHAPE", "U": "U_SHAPE",
        "asymC": "ASYMMETRIC",
    }
    base_shape = req.shape.split("→")[0]
    profile_type_str = shape_map.get(base_shape, "C_SHAPE")
    # Compound taper maps to COMPOUND enum
    if "→" in req.shape:
        profile_type_str = "COMPOUND"
    profile_type = NeckProfileType[profile_type_str]

    tr_config = TrussRodConfig(
        width_mm=req.rod_width_mm,
        depth_mm=req.rod_depth_mm,
        length_mm=req.rod_length_mm,
        start_offset_mm=req.rod_start_offset,
    )

    cfg = NeckPipelineConfig(
        scale_length_mm=req.scale_length_mm,
        fret_count=req.fret_count,
        profile_type=profile_type,
        nut_width_mm=req.nut_width_mm,
        heel_width_mm=req.heel_width_mm,
        # Crown-compensated depths
        depth_at_nut_mm=back_depth(1, req),
        depth_at_12th_mm=back_depth(12, req),
        depth_at_heel_mm=back_depth(req.fret_count, req),
        truss_rod=tr_config,
        material=material,
        output_units="mm",
        include_fret_slots=req.include_fret_slots,
    )
    return cfg


# ─── G-code fallback (when pipeline package not importable) ──────────────────

def _fallback_gcode(req: NeckRequest) -> str:
    """Minimal G-code when the repo pipeline is not on the import path."""
    lines = [
        f"; Neck Profile — {req.shape}  (fallback — repo pipeline not found)",
        f"; d1={back_depth(1,req):.3f}mm  d12={back_depth(12,req):.3f}mm",
        f"; Crown comp nut={crown_comp(0,req):.4f}mm  12th={crown_comp(12,req):.4f}mm",
        "", "G21 ; mm", "G90 ; absolute", "G00 Z5.000", "",
    ]
    for n in range(req.fret_count + 1):
        x_f = 0.0 if n == 0 else req.scale_length_mm * (1 - 1 / (2 ** (n / 12)))
        bd = back_depth(n, req)
        hw = req.shoulder_width_mm / 2
        bn_r = req.ball_nose_mm / 2
        step = req.ball_nose_mm * req.stepover_pct / 100
        n_passes = math.ceil((hw * 2 + req.ball_nose_mm) / step) + 1
        label = "NUT" if n == 0 else f"Fret {n}"
        lines += [f"; {label}  Y={x_f:.3f}mm  back={bd:.4f}mm", f"G00 Y{x_f:.3f}"]
        for i in range(n_passes):
            x = -(hw + bn_r) + i * step
            xn = max(-1.0, min(1.0, x / hw)) if hw > 0 else 0.0
            z_s = shape_y(xn, bd, req.shape, req.asym_bass_add_mm)
            z_t = z_s - bn_r
            if i == 0:
                lines += [f"G00 X{x:.3f} Z{z_t+5:.4f}", f"G01 Z{z_t:.4f} F{req.feed_mm_min*0.4:.0f}"]
            else:
                lines.append(f"G01 X{x:.3f} Y{x_f:.3f} Z{z_t:.4f} F{req.feed_mm_min:.0f}")
        lines += ["G00 Z5.000", ""]
    lines.append("M30")
    return "\n".join(lines)


# ─── DXF builder ─────────────────────────────────────────────────────────────

def build_neck_dxf(req: NeckRequest) -> ezdxf.document.Drawing:
    doc = ezdxf.new(dxfversion="R2010")
    doc.units = units.MM
    msp = doc.modelspace()

    for lname, col in [
        (LAYER_PROFILE_NUT,   1),
        (LAYER_PROFILE_12TH,  4),
        (LAYER_PROFILE_LAST,  3),
        (LAYER_TOOLPATH,      8),
        (LAYER_ANNOTATION,    9),
    ]:
        doc.layers.add(name=lname, color=col)

    key_frets = [0, 12, req.fret_count]
    lyr_map = {0: LAYER_PROFILE_NUT, 12: LAYER_PROFILE_12TH}

    for n in key_frets:
        hw   = req.shoulder_width_mm / 2
        bd   = back_depth(n, req)
        y_pos = 0.0 if n == 0 else req.scale_length_mm * (1 - 1 / (2 ** (n / 12)))
        lyr  = lyr_map.get(n, LAYER_PROFILE_LAST)
        steps = 64
        pts_3d = []
        for i in range(steps + 1):
            t = i / steps
            x = (t - 0.5) * hw * 2
            xn = x / hw if hw > 0 else 0
            z = shape_y(xn, bd, req.shape, req.asym_bass_add_mm)
            pts_3d.append((x, y_pos, z))
        msp.add_polyline3d(pts_3d, dxfattribs={"layer": lyr})
        msp.add_line((-hw, y_pos, 0), (hw, y_pos, 0), dxfattribs={"layer": lyr})
        cr = crown_comp(n, req)
        msp.add_text(
            f"{'Nut' if n == 0 else f'Fret {n}'}  "
            f"back={bd:.3f}mm  crown_comp={cr:.4f}mm  w={hw*2:.2f}mm",
            dxfattribs={"layer": LAYER_ANNOTATION, "height": 1.5},
        ).set_placement((hw + 3, y_pos), align=TextEntityAlignment.LEFT)

    # Coupling note
    msp.add_text(
        f"{req.label}  {req.shape}  "
        f"d1={req.depth_1st_mm}mm→back={back_depth(1,req):.3f}mm  "
        f"d12={req.depth_12th_mm}mm→back={back_depth(12,req):.3f}mm  "
        f"coupling: {req.radius_type} {req.r1_inch}\""
        + (f"→{req.r2_inch}\"" if req.radius_type == "compound" else ""),
        dxfattribs={"layer": LAYER_ANNOTATION, "height": 2.5},
    ).set_placement((0, -15), align=TextEntityAlignment.CENTER)

    return doc


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/gcode")
async def neck_profile_gcode(req: NeckRequest):
    """
    Generate neck back profile G-code via the repo NeckPipeline orchestrator.
    Falls back to inline generator if the pipeline package is not importable.

    The pipeline sequence (repo cam/neck/orchestrator.py):
      OP10  Truss rod channel
      OP40  Profile roughing
      OP45  Profile finishing
      OP50  Fret slots (optional)

    Crown compensation is applied to depth values before the pipeline runs,
    so back depths already account for fretboard radius variation.
    """
    fn = req.label.lower().replace(" ", "-") or "neck-profile"
    try:
        if PIPELINE_AVAILABLE:
            cfg    = build_pipeline_config(req)
            result = NeckPipeline(cfg).generate(
                include_truss_rod=True,
                include_profile_rough=True,
                include_profile_finish=True,
                include_fret_slots=req.include_fret_slots,
            )
            code = result.get_gcode()
        else:
            code = _fallback_gcode(req)
    except Exception as e:
        raise HTTPException(422, f"G-code error: {e}")

    return PlainTextResponse(code,
        headers={"Content-Disposition": f'attachment; filename="{fn}.nc"'})


@router.post("/dxf")
async def neck_profile_dxf(req: NeckRequest):
    """
    Generate neck profile DXF with cross-sections at nut, 12th, and last fret.
    Includes crown compensation annotation per station.
    """
    try:
        doc = build_neck_dxf(req)
    except Exception as e:
        raise HTTPException(422, f"DXF error: {e}")
    buf = io.BytesIO(); doc.write(buf); buf.seek(0)
    fn = req.label.lower().replace(" ", "-") or "neck-profile"
    return StreamingResponse(buf, media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{fn}.dxf"'})


@router.post("/stations")
async def neck_stations(req: NeckRequest):
    """
    Return per-fret coupling breakdown JSON:
    target_total, crown_comp, back_depth at every station.
    """
    stations = []
    for n in range(req.fret_count + 1):
        x_f = 0.0 if n == 0 else req.scale_length_mm * (1 - 1 / (2 ** (n / 12)))
        cr  = crown_comp(n, req)
        bd  = back_depth(n, req)
        target = req.depth_1st_mm + (req.depth_12th_mm - req.depth_1st_mm) * (n / 12) if n <= 12 else req.depth_12th_mm
        stations.append({
            "fret":           n,
            "position_mm":    round(x_f, 3),
            "target_mm":      round(target, 3),
            "fret_wire_mm":   req.fret_wire_mm,
            "fb_thickness_mm":req.fb_thickness_mm,
            "crown_comp_mm":  round(cr, 4),
            "back_depth_mm":  round(bd, 4),
        })

    pipeline_status = "available" if PIPELINE_AVAILABLE else "fallback (repo path not found)"
    coupling_note = (
        f"back_depth = target - fret_wire - fb_thickness - sagitta(radius_at_fret(n), width_at_fret(n)). "
        f"Crown varies {crown_comp(0,req):.4f}mm (nut) → {crown_comp(req.fret_count,req):.4f}mm (body). "
        f"Pipeline: {pipeline_status}."
    )

    return JSONResponse({"stations": stations, "coupling_note": coupling_note})


@router.post("/pipeline/preview")
async def pipeline_preview(req: NeckRequest):
    """
    Preview what the NeckPipeline orchestrator would generate:
    station list, fret positions, operation sequence.
    Does not produce G-code.
    """
    if not PIPELINE_AVAILABLE:
        raise HTTPException(503, "NeckPipeline not available — check repo import path")
    cfg = build_pipeline_config(req)
    pipeline = NeckPipeline(cfg)
    return {
        "pipeline_available": True,
        "config": cfg.to_dict() if hasattr(cfg, "to_dict") else str(cfg),
        "profile_stations": pipeline.preview_stations(),
        "fret_positions":   pipeline.preview_fret_positions(),
        "crown_compensation_note": (
            f"Depths passed to pipeline are pre-compensated. "
            f"depth_at_nut={back_depth(1,req):.3f}mm  "
            f"depth_at_12th={back_depth(12,req):.3f}mm  "
            f"depth_at_heel={back_depth(req.fret_count,req):.3f}mm"
        ),
    }
