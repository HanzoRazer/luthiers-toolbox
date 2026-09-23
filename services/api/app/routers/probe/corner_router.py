"""Corner Probe Router - Outside/inside corner probing patterns.

Provides:
- POST /corner/gcode - Generate corner probe G-code
- POST /corner/gcode/download - Download (DRAFT lane)
- POST /corner/gcode/download_governed - Download (GOVERNED lane with RMOS)

Total: 3 routes for corner probing.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...cam import probe_patterns
from ...cam.probe_service import (
    create_governed_probe_response,
    require_probe_manufacturing_authority,
)
from ...schemas.probe_schemas import CornerProbeIn, ProbeOut

router = APIRouter(tags=["probe", "corner"])


@router.post("/corner/gcode", response_model=ProbeOut)
async def generate_corner_probe(body: CornerProbeIn) -> ProbeOut:
    """Generate G-code for corner probing pattern."""
    try:
        gcode = probe_patterns.generate_corner_probe(
            pattern=body.pattern,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
        )
        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = body.pattern
        stats["work_offset"] = f"G{53 + body.work_offset}"
        return ProbeOut(gcode=gcode, stats=stats)
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/corner/gcode/download", response_class=Response)
async def download_corner_probe(body: CornerProbeIn) -> Response:
    """Download corner probe G-code as .nc file (DRAFT lane)."""
    try:
        gcode = probe_patterns.generate_corner_probe(
            pattern=body.pattern,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
        )
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"corner_{body.pattern}_{wcs}.nc"
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


@router.post("/corner/gcode/download_governed", response_class=Response)
async def download_corner_probe_governed(body: CornerProbeIn) -> Response:
    """Download corner probe G-code after manufacturing authority permits it."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="corner_probe_gcode",
            event_type="corner_probe_gcode",
            request_summary=body.model_dump(mode="json"),
        )
        gcode = probe_patterns.generate_corner_probe(
            pattern=body.pattern,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
        )
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"corner_{body.pattern}_{wcs}.nc"
        return create_governed_probe_response(
            gcode,
            filename=filename,
            authority_context=authority,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
