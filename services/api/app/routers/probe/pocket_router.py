"""Pocket probe pattern endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...cam import probe_patterns
from ...cam.probe_service import create_governed_probe_response
from ...schemas.probe_schemas import PocketProbeIn, ProbeOut

router = APIRouter(tags=["probe"])


@router.post("/pocket/gcode", response_model=ProbeOut)
async def generate_pocket_probe(body: PocketProbeIn) -> ProbeOut:
    """Generate G-code for pocket/inside corner probing."""
    try:
        gcode = probe_patterns.generate_pocket_probe(
            pocket_width=body.pocket_width,
            pocket_height=body.pocket_height,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
            origin_corner=body.origin_corner
        )

        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = "pocket_inside"
        stats["pocket_width"] = body.pocket_width
        stats["pocket_height"] = body.pocket_height
        stats["origin_corner"] = body.origin_corner
        stats["work_offset"] = f"G{53 + body.work_offset}"

        return ProbeOut(gcode=gcode, stats=stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pocket/gcode/download")
async def download_pocket_probe(body: PocketProbeIn) -> Response:
    """
    Download pocket probe G-code as .nc file (DRAFT lane).

    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution with full audit trail, use /pocket/gcode/download_governed.
    """
    try:
        gcode = probe_patterns.generate_pocket_probe(
            pocket_width=body.pocket_width,
            pocket_height=body.pocket_height,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
            origin_corner=body.origin_corner
        )

        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"pocket_inside_{wcs}.nc"

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


@router.post("/pocket/gcode/download_governed")
async def download_pocket_probe_governed(body: PocketProbeIn) -> Response:
    """
    Download pocket probe G-code as .nc file (GOVERNED lane).

    Same toolpath as /pocket/gcode/download but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    try:
        gcode = probe_patterns.generate_pocket_probe(
            pocket_width=body.pocket_width,
            pocket_height=body.pocket_height,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
            origin_corner=body.origin_corner
        )

        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"pocket_inside_{wcs}.nc"

        return create_governed_probe_response(
            gcode=gcode,
            body=body,
            tool_id="pocket_probe_gcode",
            event_type="pocket_probe_gcode_execution",
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
