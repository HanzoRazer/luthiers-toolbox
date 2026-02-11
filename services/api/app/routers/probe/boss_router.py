"""Boss/hole probe pattern endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...cam import probe_patterns
from ...cam.probe_service import create_governed_probe_response
from ...schemas.probe_schemas import BossProbeIn, ProbeOut

router = APIRouter(tags=["probe"])


@router.post("/boss/gcode", response_model=ProbeOut)
async def generate_boss_probe(body: BossProbeIn) -> ProbeOut:
    """Generate G-code for circular boss/hole probing."""
    try:
        gcode = probe_patterns.generate_boss_probe(
            pattern=body.pattern,
            estimated_diameter=body.estimated_diameter,
            estimated_center=(body.estimated_center_x, body.estimated_center_y),
            probe_count=body.probe_count,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset
        )

        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = body.pattern
        stats["estimated_diameter"] = body.estimated_diameter
        stats["probe_count"] = body.probe_count
        stats["work_offset"] = f"G{53 + body.work_offset}"

        return ProbeOut(gcode=gcode, stats=stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/boss/gcode/download")
async def download_boss_probe(body: BossProbeIn) -> Response:
    """
    Download boss/hole probe G-code as .nc file (DRAFT lane).

    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution with full audit trail, use /boss/gcode/download_governed.
    """
    try:
        gcode = probe_patterns.generate_boss_probe(
            pattern=body.pattern,
            estimated_diameter=body.estimated_diameter,
            estimated_center=(body.estimated_center_x, body.estimated_center_y),
            probe_count=body.probe_count,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset
        )

        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"boss_{body.pattern}_{wcs}.nc"

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


@router.post("/boss/gcode/download_governed")
async def download_boss_probe_governed(body: BossProbeIn) -> Response:
    """
    Download boss/hole probe G-code as .nc file (GOVERNED lane).

    Same toolpath as /boss/gcode/download but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    try:
        gcode = probe_patterns.generate_boss_probe(
            pattern=body.pattern,
            estimated_diameter=body.estimated_diameter,
            estimated_center=(body.estimated_center_x, body.estimated_center_y),
            probe_count=body.probe_count,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset
        )

        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"boss_{body.pattern}_{wcs}.nc"

        return create_governed_probe_response(
            gcode=gcode,
            body=body,
            tool_id="boss_probe_gcode",
            event_type="boss_probe_gcode_execution",
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
