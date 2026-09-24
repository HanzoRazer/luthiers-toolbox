"""Vise Square Probe Router - Vise squareness check patterns.

Provides:
- POST /vise_square/gcode - Generate vise square probe G-code after manufacturing authority
- POST /vise_square/gcode/download - Download after manufacturing authority
- POST /vise_square/gcode/download_governed - Download after manufacturing authority

All three routes use tool id vise_square_probe_gcode. Event types stay distinct.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from ...cam import probe_patterns
from ...cam.probe_service import (
    create_governed_probe_response,
    persist_authorized_probe_program,
    require_probe_manufacturing_authority,
)
from ...schemas.probe_schemas import ViseSquareProbeIn, ProbeOut

router = APIRouter(tags=["probe", "vise_square"])


@router.post("/vise_square/gcode", response_model=ProbeOut)
async def generate_vise_square_probe(body: ViseSquareProbeIn, response: Response) -> ProbeOut:
    """Generate G-code for vise squareness check."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="vise_square_probe_gcode",
            event_type="vise_square_probe_gcode_json",
            request_summary=body.model_dump(mode="json"),
        )
        gcode = probe_patterns.generate_vise_square_probe(
            vise_jaw_height=body.vise_jaw_height,
            probe_spacing=body.probe_spacing,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
        )
        gcode_hash = persist_authorized_probe_program(gcode, authority_context=authority)
        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = "vise_square"
        stats["probe_spacing"] = body.probe_spacing
        response.headers["X-ToolBox-Lane"] = "governed"
        response.headers["X-Run-ID"] = authority.run_id
        response.headers["X-GCode-SHA256"] = gcode_hash
        return ProbeOut(gcode=gcode, stats=stats)
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vise_square/gcode/download", response_class=Response)
async def download_vise_square_probe(body: ViseSquareProbeIn) -> Response:
    """Download vise squareness check G-code as .nc file after manufacturing authority."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="vise_square_probe_gcode",
            event_type="vise_square_probe_gcode_download",
            request_summary=body.model_dump(mode="json"),
        )
        gcode = probe_patterns.generate_vise_square_probe(
            vise_jaw_height=body.vise_jaw_height,
            probe_spacing=body.probe_spacing,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
        )
        filename = "vise_squareness_check.nc"
        return create_governed_probe_response(
            gcode,
            filename=filename,
            authority_context=authority,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vise_square/gcode/download_governed", response_class=Response)
async def download_vise_square_probe_governed(body: ViseSquareProbeIn) -> Response:
    """Download vise-square probe G-code after manufacturing authority permits it."""
    try:
        authority = require_probe_manufacturing_authority(
            tool_id="vise_square_probe_gcode",
            event_type="vise_square_probe_gcode",
            request_summary=body.model_dump(mode="json"),
        )
        gcode = probe_patterns.generate_vise_square_probe(
            vise_jaw_height=body.vise_jaw_height,
            probe_spacing=body.probe_spacing,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
        )
        filename = "vise_squareness_check.nc"
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
