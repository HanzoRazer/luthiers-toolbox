"""Consolidated Probe Pattern Router.

Merged from:
- boss_router.py (3 routes)
- corner_router.py (3 routes)
- pocket_router.py (3 routes)
- setup_router.py (2 routes)
- surface_z_router.py (3 routes)
- vise_square_router.py (3 routes)

Total: 17 routes for CNC probing operations.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...cam import probe_patterns, probe_svg
from ...cam.probe_service import create_governed_probe_response
from ...schemas.probe_schemas import (
    BossProbeIn,
    CornerProbeIn,
    PocketProbeIn,
    ProbeOut,
    SetupSheetIn,
    SurfaceZProbeIn,
    ViseSquareProbeIn,
)

router = APIRouter(tags=["probe"])


# =============================================================================
# BOSS/HOLE PROBE ROUTES
# =============================================================================


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
            work_offset=body.work_offset,
        )
        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = body.pattern
        stats["estimated_diameter"] = body.estimated_diameter
        stats["probe_count"] = body.probe_count
        stats["work_offset"] = f"G{53 + body.work_offset}"
        return ProbeOut(gcode=gcode, stats=stats)
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/boss/gcode/download")
async def download_boss_probe(body: BossProbeIn) -> Response:
    """Download boss/hole probe G-code as .nc file (DRAFT lane)."""
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
            work_offset=body.work_offset,
        )
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"boss_{body.pattern}_{wcs}.nc"
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


@router.post("/boss/gcode/download_governed")
async def download_boss_probe_governed(body: BossProbeIn) -> Response:
    """Download boss/hole probe G-code (GOVERNED lane with RMOS persistence)."""
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
            work_offset=body.work_offset,
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
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CORNER PROBE ROUTES
# =============================================================================


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


@router.post("/corner/gcode/download")
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


@router.post("/corner/gcode/download_governed")
async def download_corner_probe_governed(body: CornerProbeIn) -> Response:
    """Download corner probe G-code (GOVERNED lane with RMOS persistence)."""
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
        return create_governed_probe_response(
            gcode=gcode,
            body=body,
            tool_id="corner_probe_gcode",
            event_type="corner_probe_gcode_execution",
            filename=filename,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POCKET PROBE ROUTES
# =============================================================================


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
            origin_corner=body.origin_corner,
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
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pocket/gcode/download")
async def download_pocket_probe(body: PocketProbeIn) -> Response:
    """Download pocket probe G-code as .nc file (DRAFT lane)."""
    try:
        gcode = probe_patterns.generate_pocket_probe(
            pocket_width=body.pocket_width,
            pocket_height=body.pocket_height,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
            origin_corner=body.origin_corner,
        )
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"pocket_inside_{wcs}.nc"
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


@router.post("/pocket/gcode/download_governed")
async def download_pocket_probe_governed(body: PocketProbeIn) -> Response:
    """Download pocket probe G-code (GOVERNED lane with RMOS persistence)."""
    try:
        gcode = probe_patterns.generate_pocket_probe(
            pocket_width=body.pocket_width,
            pocket_height=body.pocket_height,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset,
            origin_corner=body.origin_corner,
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
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SURFACE Z PROBE ROUTES
# =============================================================================


@router.post("/surface_z/gcode", response_model=ProbeOut)
async def generate_surface_z_probe(body: SurfaceZProbeIn) -> ProbeOut:
    """Generate G-code for surface Z touch-off."""
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset,
        )
        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = "surface_z"
        stats["work_offset"] = f"G{53 + body.work_offset}"
        return ProbeOut(gcode=gcode, stats=stats)
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surface_z/gcode/download")
async def download_surface_z_probe(body: SurfaceZProbeIn) -> Response:
    """Download surface Z probe G-code as .nc file (DRAFT lane)."""
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset,
        )
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"surface_z_{wcs}.nc"
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


@router.post("/surface_z/gcode/download_governed")
async def download_surface_z_probe_governed(body: SurfaceZProbeIn) -> Response:
    """Download surface Z probe G-code (GOVERNED lane with RMOS persistence)."""
    try:
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
            gcode=gcode,
            body=body,
            tool_id="surface_z_probe_gcode",
            event_type="surface_z_probe_gcode_execution",
            filename=filename,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# VISE SQUARE PROBE ROUTES
# =============================================================================


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
            safe_z=body.safe_z,
        )
        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = "vise_square"
        stats["probe_spacing"] = body.probe_spacing
        return ProbeOut(gcode=gcode, stats=stats)
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vise_square/gcode/download")
async def download_vise_square_probe(body: ViseSquareProbeIn) -> Response:
    """Download vise squareness check G-code as .nc file (DRAFT lane)."""
    try:
        gcode = probe_patterns.generate_vise_square_probe(
            vise_jaw_height=body.vise_jaw_height,
            probe_spacing=body.probe_spacing,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
        )
        filename = "vise_squareness_check.nc"
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


@router.post("/vise_square/gcode/download_governed")
async def download_vise_square_probe_governed(body: ViseSquareProbeIn) -> Response:
    """Download vise squareness check G-code (GOVERNED lane with RMOS persistence)."""
    try:
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
            gcode=gcode,
            body=body,
            tool_id="vise_square_probe_gcode",
            event_type="vise_square_probe_gcode_execution",
            filename=filename,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SETUP SHEET AND PATTERNS LISTING
# =============================================================================


@router.post("/setup_sheet/svg")
async def generate_setup_sheet(body: SetupSheetIn) -> Response:
    """Generate SVG setup sheet for probing pattern."""
    try:
        if body.pattern in ["corner_outside", "corner_inside"]:
            svg = probe_svg.generate_corner_outside_sheet(
                part_width=body.part_width or 100.0,
                part_height=body.part_height or 60.0,
                probe_offset=body.probe_offset or 20.0,
            )
        elif body.pattern in ["boss_circular", "hole_circular"]:
            svg = probe_svg.generate_boss_circular_sheet(
                boss_diameter=body.feature_diameter or 50.0
            )
        elif body.pattern == "pocket_inside":
            svg = probe_svg.generate_pocket_inside_sheet(
                pocket_width=body.part_width or 100.0,
                pocket_height=body.part_height or 60.0,
                origin_corner=body.origin_corner or "center",
            )
        elif body.pattern == "surface_z":
            svg = probe_svg.generate_surface_z_sheet()
        else:
            raise ValueError(f"Pattern '{body.pattern}' not implemented")

        filename = f"setup_{body.pattern}.svg"
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def list_probe_patterns() -> Dict[str, Any]:
    """List all available probing patterns with metadata."""
    return {"patterns": probe_patterns.get_probe_patterns()}
