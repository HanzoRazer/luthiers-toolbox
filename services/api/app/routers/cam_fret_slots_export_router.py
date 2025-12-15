"""
CAM Fret Slots Export Router

API endpoints for fret slot G-code export with multiple post-processor support.

Phase E Implementation (December 2025)

Endpoints:
- POST /api/cam/fret_slots/export - Export single post-processor
- POST /api/cam/fret_slots/export_multi - Export to multiple post-processors
- GET  /api/cam/fret_slots/post_processors - List available post-processors
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List

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


@router.post("/export/raw", response_class=PlainTextResponse)
async def export_fret_slot_gcode_raw(request: FretSlotExportRequest):
    """
    Export raw G-code text (no JSON wrapper).
    
    POST /api/cam/fret_slots/export/raw
    
    Returns plain text G-code suitable for direct file download.
    """
    try:
        response = export_fret_slots(request)
        return PlainTextResponse(
            content=response.gcode,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=fret_slots_{request.post_processor.value}.nc"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
