"""Corner Probe Router - Outside/inside corner probing patterns.

Provides:
- POST /corner/gcode - Generate corner probe G-code after manufacturing authority
- POST /corner/gcode/download - Download after manufacturing authority
- POST /corner/gcode/download_governed - Download after manufacturing authority

All three routes use tool id corner_probe_gcode. Event types stay distinct.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from ...cam import probe_patterns
from ...cam.probe_service import (
    create_governed_probe_response,
    persist_authorized_probe_program,
    require_probe_manufacturing_authority,
)
from ...schemas.probe_schemas import CornerProbeIn, ProbeOut

router = APIRouter(tags=["probe", "corner"])


@router.post("/corner/gcode", response_model=ProbeOut)
async def generate_corner_probe(body: CornerProbeIn, response: Response) -> ProbeOut:
    """Generate G-code for corner probing pattern."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="corner_probe_gcode",
            event_type="corner_probe_gcode_json",
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
        gcode_hash = persist_authorized_probe_program(gcode, authority_context=authority)
        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = body.pattern
        stats["work_offset"] = f"G{53 + body.work_offset}"
        response.headers["X-ToolBox-Lane"] = "governed"
        response.headers["X-Run-ID"] = authority.run_id
        response.headers["X-GCode-SHA256"] = gcode_hash
        return ProbeOut(gcode=gcode, stats=stats)
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/corner/gcode/download", response_class=Response)
async def download_corner_probe(body: CornerProbeIn) -> Response:
    """Download corner probe G-code as .nc file after manufacturing authority."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="corner_probe_gcode",
            event_type="corner_probe_gcode_download",
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
