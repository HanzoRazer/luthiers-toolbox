"""Vise squareness check probe endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...cam import probe_patterns
from ...cam.probe_service import create_governed_probe_response
from ...schemas.probe_schemas import ViseSquareProbeIn, ProbeOut

router = APIRouter(tags=["probe"])


@router.post("/vise_square/gcode", response_model=ProbeOut)
async def generate_vise_square_probe(body: ViseSquareProbeIn) -> ProbeOut:
    """Generate G-code for vise squareness check."""
    try:
        gcode = probe_patterns.generate_vise_square_probe(
            vise_jaw_height=body.vise_jaw_height,
            probe_spacing=body.probe_spacing,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z
        )

        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = "vise_square"
        stats["probe_spacing"] = body.probe_spacing

        return ProbeOut(gcode=gcode, stats=stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vise_square/gcode/download")
async def download_vise_square_probe(body: ViseSquareProbeIn) -> Response:
    """
    Download vise squareness check G-code as .nc file (DRAFT lane).

    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution with full audit trail, use /vise_square/gcode/download_governed.
    """
    try:
        gcode = probe_patterns.generate_vise_square_probe(
            vise_jaw_height=body.vise_jaw_height,
            probe_spacing=body.probe_spacing,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z
        )

        filename = "vise_squareness_check.nc"

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


@router.post("/vise_square/gcode/download_governed")
async def download_vise_square_probe_governed(body: ViseSquareProbeIn) -> Response:
    """
    Download vise squareness check G-code as .nc file (GOVERNED lane).

    Same toolpath as /vise_square/gcode/download but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    try:
        gcode = probe_patterns.generate_vise_square_probe(
            vise_jaw_height=body.vise_jaw_height,
            probe_spacing=body.probe_spacing,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z
        )

        filename = "vise_squareness_check.nc"

        return create_governed_probe_response(
            gcode=gcode,
            body=body,
            tool_id="vise_square_probe_gcode",
            event_type="vise_square_probe_gcode_execution",
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
