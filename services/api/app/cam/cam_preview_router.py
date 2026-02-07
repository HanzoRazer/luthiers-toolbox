"""
CAM Preview Router

Wave 17→18: Phase E - CAM Preview Endpoints

Unified endpoints combining CAM toolpath generation with feasibility scoring
for real-time preview and validation in the UI.

Integrates:
- Phase C: Fretboard CAM operations (fret_slots_cam.py)
- Phase D: Feasibility fusion (feasibility_fusion.py)
- Phase B: RMOS context management (context.py)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from ..calculators.fret_slots_cam import (
    generate_fret_slot_cam,
    FretSlotCAMOutput,
)
from ..instrument_geometry.neck.neck_profiles import FretboardSpec
from ..rmos.context import RmosContext
from ..rmos.feasibility_fusion import evaluate_feasibility


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class FretSlotPreviewRequest(BaseModel):
    """Request body for fret slot CAM preview."""
    model_id: str = Field(
        ...,
        description="Guitar model identifier (e.g., 'strat_25_5', 'lp_24_75')",
        example="strat_25_5",
    )
    fretboard: Dict[str, Any] = Field(
        ...,
        description="Fretboard parameters (nut_width_mm, heel_width_mm, etc.)",
        example={
            "nut_width_mm": 42.0,
            "heel_width_mm": 56.0,
            "scale_length_mm": 648.0,
            "fret_count": 22,
            "base_radius_mm": 241.3,
            "end_radius_mm": 304.8,
        }
    )
    cam_params: Optional[Dict[str, Any]] = Field(
        None,
        description="CAM parameters (slot_depth_mm, safe_z_mm, post_id)",
        example={
            "slot_depth_mm": 3.0,
            "slot_width_mm": 0.58,
            "safe_z_mm": 5.0,
            "post_id": "GRBL",
        }
    )


class ToolpathSummary(BaseModel):
    """Summary of a single fret slot toolpath."""
    fret_number: int
    position_mm: float
    width_mm: float
    slot_depth_mm: float
    feed_rate_mmpm: float


class FretSlotPreviewResponse(BaseModel):
    """Unified CAM preview response with feasibility scoring."""
    # CAM outputs
    toolpaths: List[ToolpathSummary]
    dxf_preview: str = Field(..., description="First 500 chars of DXF")
    gcode_preview: str = Field(..., description="First 500 chars of G-code")
    statistics: Dict[str, Any]
    
    # Feasibility scoring
    feasibility_score: float = Field(..., description="Overall feasibility score (0-100)")
    feasibility_risk: str = Field(..., description="GREEN/YELLOW/RED")
    is_feasible: bool
    needs_review: bool
    recommendations: List[str]
    
    # Download URLs (for full files)
    download_urls: Dict[str, str] = Field(
        default_factory=dict,
        description="URLs for downloading full DXF/G-code files",
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/fret_slots/preview", response_model=FretSlotPreviewResponse)
async def preview_fret_slot_cam(request: FretSlotPreviewRequest):
    """
    Generate fret slot CAM preview with feasibility scoring.
    
    POST /api/cam/fret_slots/preview
    
    This endpoint combines Phase C (CAM generation) and Phase D (feasibility
    scoring) to provide a unified preview for the UI.
    
    Request body:
    ```json
    {
      "model_id": "strat_25_5",
      "fretboard": {
        "nut_width_mm": 42.0,
        "heel_width_mm": 56.0,
        "scale_length_mm": 648.0,
        "fret_count": 22,
        "base_radius_mm": 241.3,
        "end_radius_mm": 304.8
      },
      "cam_params": {
        "slot_depth_mm": 3.0,
        "slot_width_mm": 0.58,
        "safe_z_mm": 5.0,
        "post_id": "GRBL"
      }
    }
    ```
    
    Response:
    ```json
    {
      "toolpaths": [
        {"fret_number": 1, "position_mm": 36.3, "width_mm": 42.5, ...},
        ...
      ],
      "dxf_preview": "0\\nSECTION\\n2\\nHEADER...",
      "gcode_preview": "(Fret Slot Program - 22 slots)\\nG21...",
      "statistics": {
        "slot_count": 22,
        "total_cutting_length_mm": 1047.2,
        "total_time_min": 3.4
      },
      "feasibility_score": 85.3,
      "feasibility_risk": "GREEN",
      "is_feasible": true,
      "needs_review": false,
      "recommendations": ["✅ All parameters within safe operating range."]
    }
    ```
    """
    try:
        # Build FretboardSpec from request
        fb = request.fretboard
        spec = FretboardSpec(
            nut_width_mm=fb.get("nut_width_mm", 42.0),
            heel_width_mm=fb.get("heel_width_mm", 56.0),
            scale_length_mm=fb.get("scale_length_mm", 648.0),
            fret_count=fb.get("fret_count", 22),
            base_radius_mm=fb.get("base_radius_mm"),
            end_radius_mm=fb.get("end_radius_mm"),
            extension_mm=fb.get("extension_mm", 0.0),
            nut_overhang_mm=fb.get("nut_overhang_mm", 0.0),
        )
        
        # Create RMOS context
        context = RmosContext.from_model_id(request.model_id)
        
        # Extract CAM parameters
        cam_params = request.cam_params or {}
        slot_depth_mm = cam_params.get("slot_depth_mm", 3.0)
        slot_width_mm = cam_params.get("slot_width_mm", 0.58)
        safe_z_mm = cam_params.get("safe_z_mm", 5.0)
        post_id = cam_params.get("post_id", "GRBL")
        
        # Generate CAM output (Phase C)
        cam_output = generate_fret_slot_cam(
            spec=spec,
            context=context,
            slot_depth_mm=slot_depth_mm,
            slot_width_mm=slot_width_mm,
            safe_z_mm=safe_z_mm,
            post_id=post_id,
        )
        
        # Build design parameters for feasibility check
        # Use average feedrate from toolpaths
        avg_feed = sum(tp.feed_rate_mmpm for tp in cam_output.toolpaths) / len(cam_output.toolpaths)
        avg_plunge = sum(tp.plunge_rate_mmpm for tp in cam_output.toolpaths) / len(cam_output.toolpaths)
        
        design = {
            "tool_diameter_mm": slot_width_mm,  # Fret saw kerf as "tool diameter"
            "feed_rate_mmpm": avg_feed,
            "plunge_rate_mmpm": avg_plunge,
            "depth_of_cut_mm": slot_depth_mm,
            "spindle_rpm": 0,  # N/A for table saw/router operations
        }
        
        # Evaluate feasibility (Phase D)
        feasibility_report = evaluate_feasibility(design, context)
        
        # Convert toolpaths to summary format
        toolpath_summaries = [
            ToolpathSummary(
                fret_number=tp.fret_number,
                position_mm=tp.position_mm,
                width_mm=tp.width_mm,
                slot_depth_mm=tp.slot_depth_mm,
                feed_rate_mmpm=tp.feed_rate_mmpm,
            )
            for tp in cam_output.toolpaths
        ]
        
        # Create previews (first 500 chars)
        dxf_preview = cam_output.dxf_content[:500]
        gcode_preview = cam_output.gcode_content[:500]
        
        # Build response
        return FretSlotPreviewResponse(
            toolpaths=toolpath_summaries,
            dxf_preview=dxf_preview,
            gcode_preview=gcode_preview,
            statistics=cam_output.statistics,
            feasibility_score=feasibility_report.overall_score,
            feasibility_risk=feasibility_report.overall_risk.value,
            is_feasible=feasibility_report.is_feasible(),
            needs_review=feasibility_report.needs_review(),
            recommendations=feasibility_report.recommendations,
            download_urls={
                "dxf": f"/api/cam/fret_slots/download/dxf?model_id={request.model_id}",
                "gcode": f"/api/cam/fret_slots/download/gcode?model_id={request.model_id}&post_id={post_id}",
            },
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # WP-1: pass through
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=500,
            detail=f"CAM preview generation failed: {str(e)}"
        )


@router.get("/fret_slots/example")
async def get_fret_slot_example():
    """
    Get example request body for fret slot CAM preview.
    
    GET /api/cam/fret_slots/example
    
    Response:
    ```json
    {
      "strat_example": {...},
      "gibson_example": {...}
    }
    ```
    """
    return {
        "strat_example": {
            "model_id": "strat_25_5",
            "fretboard": {
                "nut_width_mm": 42.0,
                "heel_width_mm": 56.0,
                "scale_length_mm": 648.0,
                "fret_count": 22,
                "base_radius_mm": 241.3,
                "end_radius_mm": 304.8,
            },
            "cam_params": {
                "slot_depth_mm": 3.0,
                "slot_width_mm": 0.58,
                "safe_z_mm": 5.0,
                "post_id": "GRBL",
            },
        },
        "gibson_example": {
            "model_id": "lp_24_75",
            "fretboard": {
                "nut_width_mm": 43.0,
                "heel_width_mm": 56.5,
                "scale_length_mm": 628.65,
                "fret_count": 22,
                "base_radius_mm": 304.8,  # 12" constant radius
            },
            "cam_params": {
                "slot_depth_mm": 3.2,
                "slot_width_mm": 0.58,
                "safe_z_mm": 5.0,
                "post_id": "Mach4",
            },
        },
    }


@router.get("/health")
async def cam_preview_health():
    """
    Health check endpoint for CAM preview router.
    
    GET /api/cam/health
    
    Response:
    ```json
    {
      "status": "healthy",
      "phase_c_available": true,
      "phase_d_available": true,
      "phase_e_available": true
    }
    ```
    """
    # Test imports
    phase_c_ok = True
    phase_d_ok = True
    
    try:
        from ..calculators.fret_slots_cam import generate_fret_slot_cam
    except ImportError:
        phase_c_ok = False
    
    try:
        from ..rmos.feasibility_fusion import evaluate_feasibility
    except ImportError:
        phase_d_ok = False
    
    status = "healthy" if (phase_c_ok and phase_d_ok) else "degraded"
    
    return {
        "status": status,
        "phase_c_available": phase_c_ok,
        "phase_d_available": phase_d_ok,
        "phase_e_available": True,  # This endpoint itself
        "message": "CAM Preview router operational" if status == "healthy" else "Some components unavailable",
    }
