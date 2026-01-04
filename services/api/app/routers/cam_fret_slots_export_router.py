"""
CAM Fret Slots Export Router

API endpoints for fret slot G-code export with multiple post-processor support.

Phase E Implementation (December 2025)

Endpoints:
- POST /api/cam/fret_slots/export - Export single post-processor
- POST /api/cam/fret_slots/export_multi - Export to multiple post-processors
- GET  /api/cam/fret_slots/post_processors - List available post-processors
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response
from typing import List

# Import RMOS run artifact persistence (OPERATION lane requirement)
from ..rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

from ..schemas.cam_fret_slots import (
    PostProcessor,
    FretSlotExportRequest,
    FretSlotExportResponse,
    MultiExportRequest,
    MultiExportResponse,
)
from ..calculators.fret_slots_export import (
    export_fret_slots,
    export_fret_slots_multi,
)


router = APIRouter(prefix="/api/cam/fret_slots", tags=["CAM", "Fret Slots", "Export"])


@router.get("/post_processors", response_model=List[str])
async def list_post_processors():
    """
    List available G-code post-processors.
    
    GET /api/cam/fret_slots/post_processors
    
    Returns:
        ["GRBL", "Mach3", "Mach4", "LinuxCNC", "PathPilot", "MASSO", "Fanuc", "Haas"]
    """
    return [p.value for p in PostProcessor]


@router.post("/export", response_model=FretSlotExportResponse)
async def export_fret_slot_gcode(request: FretSlotExportRequest):
    """
    Export fret slot G-code for a single post-processor.
    
    POST /api/cam/fret_slots/export
    
    Request body:
    ```json
    {
      "scale_length_mm": 648.0,
      "fret_count": 22,
      "nut_width_mm": 42.0,
      "heel_width_mm": 56.0,
      "slot_depth_mm": 3.0,
      "post_processor": "GRBL"
    }
    ```
    
    Returns G-code, slot data, and statistics.
    """
    try:
        return export_fret_slots(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/export_multi", response_model=MultiExportResponse)
async def export_fret_slot_gcode_multi(request: MultiExportRequest):
    """
    Export fret slot G-code to multiple post-processors.
    
    POST /api/cam/fret_slots/export_multi
    
    Request body:
    ```json
    {
      "base_request": {
        "scale_length_mm": 648.0,
        "fret_count": 22,
        "post_processor": "GRBL"
      },
      "post_processors": ["GRBL", "Mach4", "LinuxCNC"]
    }
    ```
    
    Returns exports for each requested post-processor.
    """
    try:
        exports = export_fret_slots_multi(
            request.base_request,
            request.post_processors,
        )
        
        failed = [k for k, v in exports.items() if "ERROR" in v.gcode]
        
        return MultiExportResponse(
            exports=exports,
            total_exports=len(exports),
            failed_exports=failed,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-export failed: {str(e)}")


# =============================================================================
# Draft Lane: Fast preview, no RMOS tracking
# =============================================================================

@router.post("/export/raw", response_class=PlainTextResponse)
async def export_fret_slot_gcode_raw(request: FretSlotExportRequest):
    """
    Export raw G-code text (no JSON wrapper) - DRAFT lane.
    
    POST /api/cam/fret_slots/export/raw
    
    Returns plain text G-code suitable for direct file download.
    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution, use /export/raw_governed.
    """
    try:
        response = export_fret_slots(request)
        resp = PlainTextResponse(
            content=response.gcode,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=fret_slots_{request.post_processor.value}.nc"
            }
        )
        resp.headers["X-ToolBox-Lane"] = "draft"
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Governed Lane: Full RMOS artifact persistence and audit trail
# =============================================================================

@router.post("/export/raw_governed", response_class=Response)
async def export_fret_slot_gcode_raw_governed(request: FretSlotExportRequest):
    """
    Export raw G-code text with RMOS governance - GOVERNED lane.
    
    POST /api/cam/fret_slots/export/raw_governed
    
    Same toolpath as /export/raw but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    try:
        response = export_fret_slots(request)
        program = response.gcode
        
        now = datetime.now(timezone.utc).isoformat()
        request_hash = sha256_of_obj(request.model_dump(mode="json"))
        gcode_hash = sha256_of_text(program)
        
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="fret_slots_export",
            workflow_mode="fret_slots",
            event_type="fret_slots_gcode_execution",
            status="OK",
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)
        
        resp = Response(
            content=program,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=fret_slots_{request.post_processor.value}.nc"
            }
        )
        resp.headers["X-Run-ID"] = run_id
        resp.headers["X-GCode-SHA256"] = gcode_hash
        resp.headers["X-ToolBox-Lane"] = "governed"
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
