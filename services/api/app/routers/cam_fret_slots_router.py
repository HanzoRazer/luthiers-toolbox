"""
Wave 19 Phase B/C: Fret Slots CAM Router

Provides API endpoints for fret slot CAM generation with per-fret risk analysis.
Supports both standard parallel slots and fan-fret (multi-scale) angled slots.

Wave E2: Multi-Post Fret Export
Adds multi-post G-code export with DXF/SVG bundling.
"""

import io
import zipfile
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..calculators.fret_slots_cam import (
    generate_fret_slot_cam,
    FretSlotCAMOutput,
)
from ..instrument_geometry.neck.neck_profiles import FretboardSpec
from ..instrument_geometry.models.loader import load_model_spec
from ..rmos.context import RmosContext
from ..rmos.feasibility_fusion import (
    evaluate_per_fret_feasibility,
    summarize_per_fret_risks,
    PerFretRisk,
)
from ..rmos.fret_cam_guard import run_fret_cam_guard, FretSlotSpec
from ..schemas.cam_fret_slots_export import FretSlotMultiPostExportRequest

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class FretSlotCAMRequest(BaseModel):
    """Request for fret slot CAM generation."""
    model_id: str = Field(..., description="Guitar model identifier")
    mode: Literal['standard', 'fan'] = Field('standard', description="Slot mode: standard or fan-fret")
    
    # Standard fretboard parameters
    nut_width_mm: float = Field(42.0, gt=0, description="Nut width in mm")
    heel_width_mm: float = Field(56.0, gt=0, description="Heel width in mm")
    scale_length_mm: float = Field(648.0, gt=0, description="Scale length in mm (standard mode)")
    fret_count: int = Field(22, ge=1, le=36, description="Number of frets")
    
    # Fan-fret parameters (required when mode='fan')
    treble_scale_mm: Optional[float] = Field(None, gt=0, description="Treble scale length (fan mode)")
    bass_scale_mm: Optional[float] = Field(None, gt=0, description="Bass scale length (fan mode)")
    perpendicular_fret: Optional[int] = Field(None, ge=0, description="Perpendicular fret number (fan mode)")
    
    # CAM parameters
    slot_depth_mm: float = Field(3.0, gt=0, le=5.0, description="Slot depth in mm")
    slot_width_mm: float = Field(0.58, gt=0, description="Kerf width in mm")
    safe_z_mm: float = Field(5.0, gt=0, description="Safe retract height in mm")
    post_id: str = Field("GRBL", description="Post-processor ID")
    
    # Material override (optional)
    material_id: Optional[str] = Field(None, description="Material identifier override")


class FretSlotCAMResponse(BaseModel):
    """Response with CAM output and per-fret risk analysis."""
    toolpaths: List[dict]
    dxf_content: str
    gcode_content: str
    statistics: dict
    messages: List[dict] = []  # NEW: RMOS guard messages
    per_fret_risks: Optional[List[dict]] = None
    risk_summary: Optional[dict] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/preview", response_model=FretSlotCAMResponse, tags=["CAM", "Fret Slots"])
async def generate_fret_slot_cam_preview(body: FretSlotCAMRequest):
    """
    Generate fret slot CAM toolpaths with per-fret risk analysis.
    
    Supports both standard parallel slots and fan-fret (multi-scale) angled slots.
    Returns toolpaths, DXF, G-code, and per-fret feasibility metrics.
    
    Example (Standard):
        POST /api/cam/fret_slots/preview
        {
            "model_id": "strat_25_5",
            "mode": "standard",
            "fret_count": 22
        }
    
    Example (Fan-Fret):
        POST /api/cam/fret_slots/preview
        {
            "model_id": "strat_25_5",
            "mode": "fan",
            "treble_scale_mm": 648.0,
            "bass_scale_mm": 686.0,
            "perpendicular_fret": 7,
            "fret_count": 24
        }
    """
    # Create RMOS context
    try:
        context = RmosContext.from_model_id(body.model_id)
        
        # Override material if specified
        if body.material_id:
            # Note: Material override would require extending RmosContext
            # For now, use default material from model
            pass
    except Exception as e:
        raise HTTPException(400, f"Invalid model_id: {str(e)}")
    
    # Build fretboard spec
    if body.mode == 'standard':
        spec = FretboardSpec(
            nut_width_mm=body.nut_width_mm,
            heel_width_mm=body.heel_width_mm,
            scale_length_mm=body.scale_length_mm,
            fret_count=body.fret_count,
            base_radius_mm=241.3,  # Default 9.5" radius
            end_radius_mm=304.8,   # Default 12" radius
        )
    else:  # fan mode
        if not body.treble_scale_mm or not body.bass_scale_mm or body.perpendicular_fret is None:
            raise HTTPException(
                400,
                "Fan-fret mode requires treble_scale_mm, bass_scale_mm, and perpendicular_fret"
            )
        
        # Use treble scale as reference for spec
        spec = FretboardSpec(
            nut_width_mm=body.nut_width_mm,
            heel_width_mm=body.heel_width_mm,
            scale_length_mm=body.treble_scale_mm,
            fret_count=body.fret_count,
            base_radius_mm=241.3,
            end_radius_mm=304.8,
        )
    
    # Generate CAM output
    try:
        cam_output = generate_fret_slot_cam(
            spec=spec,
            context=context,
            mode=body.mode,
            slot_depth_mm=body.slot_depth_mm,
            slot_width_mm=body.slot_width_mm,
            safe_z_mm=body.safe_z_mm,
            post_id=body.post_id,
            treble_scale_mm=body.treble_scale_mm,
            bass_scale_mm=body.bass_scale_mm,
            perpendicular_fret=body.perpendicular_fret,
        )
    except Exception as e:
        raise HTTPException(500, f"CAM generation failed: {str(e)}")
    
    # Phase C: Per-fret risk analysis
    per_fret_risks_list = None
    risk_summary = None
    
    try:
        per_fret_risks = evaluate_per_fret_feasibility(cam_output.toolpaths, context)
        risk_summary = summarize_per_fret_risks(per_fret_risks)
        
        # Convert to dict for JSON serialization
        per_fret_risks_list = [
            {
                "fret_number": r.fret_number,
                "angle_deg": round(r.angle_deg, 2),
                "chipload_risk": round(r.chipload_risk, 1),
                "heat_risk": round(r.heat_risk, 1),
                "deflection_risk": round(r.deflection_risk, 1),
                "overall_risk": r.overall_risk.value,
                "warnings": r.warnings,
            }
            for r in per_fret_risks
        ]
    except Exception as e:
        # Risk analysis is optional - don't fail if it errors
        print(f"Warning: Per-fret risk analysis failed: {e}")
    
    # Convert toolpaths to dict
    toolpaths_dict = [
        {
            "fret_number": tp.fret_number,
            "position_mm": tp.position_mm,
            "width_mm": tp.width_mm,
            "bass_point": tp.bass_point,
            "treble_point": tp.treble_point,
            "slot_depth_mm": tp.slot_depth_mm,
            "slot_width_mm": tp.slot_width_mm,
            "feed_rate_mmpm": tp.feed_rate_mmpm,
            "plunge_rate_mmpm": tp.plunge_rate_mmpm,
            "angle_rad": tp.angle_rad,
        }
        for tp in cam_output.toolpaths
    ]
    
    # NEW: Run CAM guard checks
    guard_messages = []
    try:
        slot_specs = [
            FretSlotSpec(
                fret=tp.fret_number,
                string_index=0,
                position_mm=tp.position_mm,
                slot_width_mm=tp.slot_width_mm,
                slot_depth_mm=tp.slot_depth_mm,
                bit_diameter_mm=body.slot_width_mm,  # Use slot width as bit diameter
                angle_rad=tp.angle_rad if hasattr(tp, 'angle_rad') else None,
            )
            for tp in cam_output.toolpaths
        ]
        
        messages = run_fret_cam_guard(
            model_id=body.model_id,
            slots=slot_specs,
        )
        
        guard_messages = [m.dict() for m in messages]
    except Exception as e:
        # Guard is optional - log warning but don't fail
        print(f"Warning: CAM guard check failed: {e}")
    
    return FretSlotCAMResponse(
        toolpaths=toolpaths_dict,
        dxf_content=cam_output.dxf_content,
        gcode_content=cam_output.gcode_content,
        statistics=cam_output.statistics,
        messages=guard_messages,  # NEW: Include guard messages
        per_fret_risks=per_fret_risks_list,
        risk_summary=risk_summary,
    )


# =============================================================================
# Wave E2: Multi-Post Fret Export
# =============================================================================

@router.post("/export_multi_post")
async def export_fret_slots_multi_post(
    payload: FretSlotMultiPostExportRequest,
) -> StreamingResponse:
    """
    Multi-post fret-slot export endpoint.

    Steps:
      1. Resolve instrument model.
      2. Compute fret-slot geometry (DXF/SVG basis).
      3. Generate one G-code file per post processor.
      4. Bundle all artifacts into an in-memory ZIP.
    """
    
    # 1) Load instrument model
    try:
        instrument = load_model_spec(payload.model_id)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Instrument model {payload.model_id} not found: {str(e)}",
        )

    # 2) Compute fret slots (stub - delegates to existing CAM calculator)
    # In production, this would call compute_fret_slots_for_model()
    slots = {
        "fret_count": payload.fret_count,
        "slot_depth_mm": payload.slot_depth_mm,
        "slot_width_mm": payload.slot_width_mm,
        "model_id": payload.model_id,
    }

    # Base name for files inside the ZIP
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_prefix = payload.filename_prefix or f"{payload.model_id}_frets_{timestamp}"

    # 3) Build ZIP in memory
    memfile = io.BytesIO()
    with zipfile.ZipFile(memfile, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 3a) DXF (stub)
        dxf_bytes = _generate_dxf_bytes(slots, instrument, payload)
        zf.writestr(f"{base_prefix}.dxf", dxf_bytes)

        # 3b) SVG (stub)
        svg_bytes = _generate_svg_bytes(slots, instrument, payload)
        zf.writestr(f"{base_prefix}.svg", svg_bytes)

        # 3c) One G-code file per post-processor
        for post_id in payload.post_ids:
            gcode_bytes = _generate_gcode_for_post(slots, instrument, payload, post_id)
            zf.writestr(f"{base_prefix}_{post_id}.nc", gcode_bytes)

        # 3d) Metadata JSON
        import json
        meta: Dict[str, Any] = {
            "model_id": payload.model_id,
            "fret_count": payload.fret_count,
            "post_ids": payload.post_ids,
            "target_units": payload.target_units,
            "slot_depth_mm": payload.slot_depth_mm,
            "slot_width_mm": payload.slot_width_mm,
            "generated_at": timestamp,
        }
        zf.writestr(f"{base_prefix}_meta.json", json.dumps(meta, indent=2))

    memfile.seek(0)

    headers = {
        "Content-Disposition": f'attachment; filename="{base_prefix}_multi_post.zip"'
    }

    return StreamingResponse(
        memfile,
        media_type="application/zip",
        headers=headers,
    )


# =============================================================================
# Wave E2: Internal Helper Functions (Stubs for Real CAM Integration)
# =============================================================================

def _generate_dxf_bytes(slots, instrument, payload: FretSlotMultiPostExportRequest) -> bytes:
    """
    Adapter around your actual DXF generator.
    Replace internals with a call to your existing DXF export helpers.
    """
    # Minimal valid DXF stub for R12-style:
    stub = (
        "0\nSECTION\n2\nENTITIES\n"
        "0\nLINE\n8\nFRET_SLOTS\n10\n0\n20\n0\n11\n100\n21\n0\n"
        "0\nENDSEC\n0\nEOF\n"
    )
    return stub.encode("ascii")


def _generate_svg_bytes(slots, instrument, payload: FretSlotMultiPostExportRequest) -> bytes:
    """
    Adapter around your SVG preview generator (if you have one).
    This stub just gives you a minimal valid SVG.
    """
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 50'>"
        "<line x1='10' y1='25' x2='190' y2='25' stroke='black' stroke-width='1' />"
        "<text x='100' y='15' font-size='8' text-anchor='middle'>"
        f"{payload.model_id} Fret Slots"
        "</text>"
        "</svg>"
    )
    return svg.encode("utf-8")


def _generate_gcode_for_post(
    slots,
    instrument,
    payload: FretSlotMultiPostExportRequest,
    post_id: str,
) -> bytes:
    """
    Adapter around your real post-processor.
    Replace internals with your existing CAM post layer (GRBL, Mach4, etc.).
    """
    lines: List[str] = []
    lines.append(f"(Fret slots for {payload.model_id}, post={post_id})")
    lines.append("G90   (absolute positioning)")
    if payload.target_units == "inch":
        lines.append("G20   (inches)")
    else:
        lines.append("G21   (mm)")

    lines.append("G0 Z5.000")
    lines.append("G0 X0.000 Y0.000")
    lines.append("M5")
    lines.append("M2")

    return ("\n".join(lines) + "\n").encode("ascii")
