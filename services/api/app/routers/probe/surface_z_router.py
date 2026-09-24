"""Surface Z Probe Router - Surface Z touch-off patterns.

Provides:
- POST /surface_z/gcode - Generate surface Z probe G-code after manufacturing authority
- POST /surface_z/gcode/download - Download after manufacturing authority
- POST /surface_z/gcode/download_governed - Download after manufacturing authority

All three routes use tool id surface_z_probe_gcode. Event types stay distinct.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from ...cam import probe_patterns
from ...cam.probe_service import (
    create_governed_probe_response,
    persist_authorized_probe_program,
    require_probe_manufacturing_authority,
)
from ...schemas.probe_schemas import SurfaceZProbeIn, ProbeOut

router = APIRouter(tags=["probe", "surface_z"])


@router.post("/surface_z/gcode", response_model=ProbeOut)
async def generate_surface_z_probe(body: SurfaceZProbeIn, response: Response) -> ProbeOut:
    """Generate G-code for surface Z touch-off."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="surface_z_probe_gcode",
            event_type="surface_z_probe_gcode_json",
            request_summary=body.model_dump(mode="json"),
        )
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset,
        )
        gcode_hash = persist_authorized_probe_program(gcode, authority_context=authority)
        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = "surface_z"
        stats["work_offset"] = f"G{53 + body.work_offset}"
        response.headers["X-ToolBox-Lane"] = "governed"
        response.headers["X-Run-ID"] = authority.run_id
        response.headers["X-GCode-SHA256"] = gcode_hash
        return ProbeOut(gcode=gcode, stats=stats)
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surface_z/gcode/download", response_class=Response)
async def download_surface_z_probe(body: SurfaceZProbeIn) -> Response:
    """Download surface Z probe G-code as .nc file after manufacturing authority."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="surface_z_probe_gcode",
            event_type="surface_z_probe_gcode_download",
            request_summary=body.model_dump(mode="json"),
        )
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
            gcode,
            filename=filename,
            authority_context=authority,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surface_z/gcode/download_governed", response_class=Response)
async def download_surface_z_probe_governed(body: SurfaceZProbeIn) -> Response:
    """Download surface Z probe G-code after manufacturing authority permits it."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="surface_z_probe_gcode",
            event_type="surface_z_probe_gcode",
            request_summary=body.model_dump(mode="json"),
        )
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
            gcode,
            filename=filename,
            authority_context=authority,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
