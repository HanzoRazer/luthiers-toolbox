"""Surface Z probe pattern endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...cam import probe_patterns
from ...cam.probe_service import create_governed_probe_response
from ...schemas.probe_schemas import SurfaceZProbeIn, ProbeOut

router = APIRouter(tags=["probe"])


@router.post("/surface_z/gcode", response_model=ProbeOut)
async def generate_surface_z_probe(body: SurfaceZProbeIn) -> ProbeOut:
    """Generate G-code for surface Z touch-off."""
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset
        )

        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = "surface_z"
        stats["work_offset"] = f"G{53 + body.work_offset}"

        return ProbeOut(gcode=gcode, stats=stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surface_z/gcode/download")
async def download_surface_z_probe(body: SurfaceZProbeIn) -> Response:
    """
    Download surface Z probe G-code as .nc file (DRAFT lane).

    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution with full audit trail, use /surface_z/gcode/download_governed.
    """
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset
        )

        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"surface_z_{wcs}.nc"

        resp = Response(
            content=gcode,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        resp.headers["X-ToolBox-Lane"] = "draft"
        return resp

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surface_z/gcode/download_governed")
async def download_surface_z_probe_governed(body: SurfaceZProbeIn) -> Response:
    """
    Download surface Z probe G-code as .nc file (GOVERNED lane).

    Same toolpath as /surface_z/gcode/download but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
