"""Corner probe pattern endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...cam import probe_patterns
from ...cam.probe_service import create_governed_probe_response
from ...schemas.probe_schemas import CornerProbeIn, ProbeOut

router = APIRouter(tags=["probe"])


@router.post("/corner/gcode", response_model=ProbeOut)
async def generate_corner_probe(body: CornerProbeIn) -> ProbeOut:
    """
    Generate G-code for corner probing pattern.

    Returns G-code with G31 probes and G10 L20 offset setting.
    """
    try:
        gcode = probe_patterns.generate_corner_probe(
            pattern=body.pattern,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset
        )

        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = body.pattern
        stats["work_offset"] = f"G{53 + body.work_offset}"

        return ProbeOut(gcode=gcode, stats=stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/corner/gcode/download")
async def download_corner_probe(body: CornerProbeIn) -> Response:
    """
    Download corner probe G-code as .nc file (DRAFT lane).

    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution, use /corner/gcode/download_governed.
    """
    try:
        gcode = probe_patterns.generate_corner_probe(
            pattern=body.pattern,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset
        )

        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"corner_{body.pattern}_{wcs}.nc"

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


@router.post("/corner/gcode/download_governed")
async def download_corner_probe_governed(body: CornerProbeIn) -> Response:
    """
    Download corner probe G-code as .nc file (GOVERNED lane).

    Same toolpath as /corner/gcode/download but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    try:
        gcode = probe_patterns.generate_corner_probe(
            pattern=body.pattern,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset
        )

        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"corner_{body.pattern}_{wcs}.nc"

        return create_governed_probe_response(
            gcode=gcode,
            body=body,
            tool_id="corner_probe_gcode",
            event_type="corner_probe_gcode_execution",
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
