"""Surface Z Probe Router - Surface Z touch-off patterns.

Provides:
- POST /surface_z/gcode - Generate surface Z probe G-code
- POST /surface_z/gcode/download - Download (DRAFT lane)
- POST /surface_z/gcode/download_governed - Download (GOVERNED lane with RMOS)

Total: 3 routes for surface Z probing.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...cam import probe_patterns
from ...cam.probe_service import create_governed_probe_response
from ...schemas.probe_schemas import SurfaceZProbeIn, ProbeOut

router = APIRouter(tags=["probe", "surface_z"])


@router.post("/surface_z/gcode", response_model=ProbeOut)
async def generate_surface_z_probe(body: SurfaceZProbeIn) -> ProbeOut:
    """Generate G-code for surface Z touch-off."""
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset,
        )
        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = "surface_z"
        stats["work_offset"] = f"G{53 + body.work_offset}"
        return ProbeOut(gcode=gcode, stats=stats)
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surface_z/gcode/download", response_class=Response)
async def download_surface_z_probe(body: SurfaceZProbeIn) -> Response:
    """Download surface Z probe G-code as .nc file (DRAFT lane)."""
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset,
        )
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"surface_z_{wcs}.nc"
        resp = Response(
            content=gcode,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
        resp.headers["X-ToolBox-Lane"] = "draft"
        return resp
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surface_z/gcode/download_governed", response_class=Response)
async def download_surface_z_probe_governed(body: SurfaceZProbeIn) -> Response:
    """Download surface Z probe G-code (GOVERNED lane with RMOS persistence)."""
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset,
        )
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"surface_z_{wcs}.nc"
        return create_governed_probe_response(
            gcode=gcode,
            body=body,
            tool_id="surface_z_probe_gcode",
            event_type="surface_z_probe_gcode_execution",
            filename=filename,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
