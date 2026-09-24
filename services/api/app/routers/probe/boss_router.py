"""Boss/Hole Probe Router - Circular boss and hole probing patterns.

Provides:
- POST /boss/gcode - Generate boss probe G-code after manufacturing authority
- POST /boss/gcode/download - Download after manufacturing authority
- POST /boss/gcode/download_governed - Download after manufacturing authority

All three routes use tool id boss_probe_gcode. Event types stay distinct.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from ...cam import probe_patterns
from ...cam.probe_service import (
    create_governed_probe_response,
    persist_authorized_probe_program,
    require_probe_manufacturing_authority,
)
from ...schemas.probe_schemas import BossProbeIn, ProbeOut

router = APIRouter(tags=["probe", "boss"])


@router.post("/boss/gcode", response_model=ProbeOut)
async def generate_boss_probe(body: BossProbeIn, response: Response) -> ProbeOut:
    """Generate G-code for circular boss/hole probing."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="boss_probe_gcode",
            event_type="boss_probe_gcode_json",
            request_summary=body.model_dump(mode="json"),
        )
        gcode = probe_patterns.generate_boss_probe(
            pattern=body.pattern,
            estimated_diameter=body.estimated_diameter,
            estimated_center=(body.estimated_center_x, body.estimated_center_y),
            probe_count=body.probe_count,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
        )
        gcode_hash = persist_authorized_probe_program(gcode, authority_context=authority)
        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = body.pattern
        stats["estimated_diameter"] = body.estimated_diameter
        stats["probe_count"] = body.probe_count
        stats["work_offset"] = f"G{53 + body.work_offset}"
        response.headers["X-ToolBox-Lane"] = "governed"
        response.headers["X-Run-ID"] = authority.run_id
        response.headers["X-GCode-SHA256"] = gcode_hash
        return ProbeOut(gcode=gcode, stats=stats)
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/boss/gcode/download", response_class=Response)
async def download_boss_probe(body: BossProbeIn) -> Response:
    """Download boss/hole probe G-code as .nc file after manufacturing authority."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="boss_probe_gcode",
            event_type="boss_probe_gcode_download",
            request_summary=body.model_dump(mode="json"),
        )
        gcode = probe_patterns.generate_boss_probe(
            pattern=body.pattern,
            estimated_diameter=body.estimated_diameter,
            estimated_center=(body.estimated_center_x, body.estimated_center_y),
            probe_count=body.probe_count,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
        )
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"boss_{body.pattern}_{wcs}.nc"
        return create_governed_probe_response(
            gcode,
            filename=filename,
            authority_context=authority,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/boss/gcode/download_governed", response_class=Response)
async def download_boss_probe_governed(body: BossProbeIn) -> Response:
    """Download boss/hole probe G-code after manufacturing authority permits it."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="boss_probe_gcode",
            event_type="boss_probe_gcode",
            request_summary=body.model_dump(mode="json"),
        )
        gcode = probe_patterns.generate_boss_probe(
            pattern=body.pattern,
            estimated_diameter=body.estimated_diameter,
            estimated_center=(body.estimated_center_x, body.estimated_center_y),
            probe_count=body.probe_count,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
        )
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"boss_{body.pattern}_{wcs}.nc"
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
