"""
Probing pattern generation and SVG setup sheets.

REST API for CNC work offset establishment using touch probes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..cam import probe_patterns, probe_svg

# Import RMOS run artifact persistence (OPERATION lane requirement)
from ..rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

router = APIRouter()


class ProbePointIn(BaseModel):
    """Single probe point definition for custom patterns."""
    x: float
    y: float
    z: float
    label: str = ""


class CornerProbeIn(BaseModel):
    """Corner find pattern input."""
    pattern: Literal["corner_outside", "corner_inside"] = "corner_outside"
    approach_distance: float = Field(20.0, ge=5.0, le=50.0, description="Distance to start probe from edge (mm)")
    retract_distance: float = Field(2.0, ge=0.5, le=10.0, description="Retract after each probe (mm)")
    feed_probe: float = Field(100.0, ge=10.0, le=500.0, description="Probing feed rate (mm/min)")
    safe_z: float = Field(10.0, ge=5.0, le=50.0, description="Safe Z height (mm)")
    work_offset: int = Field(1, ge=1, le=6, description="G54-G59 offset number (1-6)")


class BossProbeIn(BaseModel):
    """Boss/hole find pattern input."""
    pattern: Literal["boss_circular", "hole_circular"] = "boss_circular"
    estimated_diameter: float = Field(50.0, ge=5.0, le=500.0, description="Estimated feature diameter (mm)")
    estimated_center_x: float = Field(0.0, description="Estimated center X (mm)")
    estimated_center_y: float = Field(0.0, description="Estimated center Y (mm)")
    probe_count: int = Field(4, ge=4, le=12, description="Number of probe points (4, 6, 8, 12)")
    approach_distance: float = Field(5.0, ge=2.0, le=20.0, description="Distance beyond edge to start (mm)")
    retract_distance: float = Field(5.0, ge=2.0, le=20.0, description="Retract after each probe (mm)")
    feed_probe: float = Field(100.0, ge=10.0, le=500.0, description="Probing feed rate (mm/min)")
    safe_z: float = Field(10.0, ge=5.0, le=50.0, description="Safe Z height (mm)")
    work_offset: int = Field(1, ge=1, le=6, description="G54-G59 offset number (1-6)")


class SurfaceZProbeIn(BaseModel):
    """Surface Z touch-off input."""
    approach_z: float = Field(10.0, ge=5.0, le=50.0, description="Z position to start probe from (mm)")
    probe_depth: float = Field(-20.0, le=-5.0, description="Maximum depth to probe (negative, mm)")
    feed_probe: float = Field(50.0, ge=10.0, le=200.0, description="Probing feed rate (mm/min)")
    retract_distance: float = Field(5.0, ge=2.0, le=20.0, description="Retract after touch (mm)")
    work_offset: int = Field(1, ge=1, le=6, description="G54-G59 offset number (1-6)")


class PocketProbeIn(BaseModel):
    """Pocket/inside corner find input."""
    pocket_width: float = Field(100.0, ge=10.0, le=500.0, description="Estimated pocket width (mm)")
    pocket_height: float = Field(60.0, ge=10.0, le=500.0, description="Estimated pocket height (mm)")
    approach_distance: float = Field(10.0, ge=5.0, le=50.0, description="Distance from center to start (mm)")
    retract_distance: float = Field(2.0, ge=0.5, le=10.0, description="Retract after each probe (mm)")
    feed_probe: float = Field(100.0, ge=10.0, le=500.0, description="Probing feed rate (mm/min)")
    safe_z: float = Field(10.0, ge=5.0, le=50.0, description="Safe Z height (mm)")
    work_offset: int = Field(1, ge=1, le=6, description="G54-G59 offset number (1-6)")
    origin_corner: Literal["lower_left", "lower_right", "upper_left", "upper_right", "center"] = "center"


class ViseSquareProbeIn(BaseModel):
    """Vise squareness check input."""
    vise_jaw_height: float = Field(50.0, ge=10.0, le=200.0, description="Z height of vise jaw (mm)")
    probe_spacing: float = Field(100.0, ge=50.0, le=300.0, description="Y distance between probes (mm)")
    approach_distance: float = Field(20.0, ge=5.0, le=50.0, description="Distance to start probe from jaw (mm)")
    retract_distance: float = Field(5.0, ge=2.0, le=20.0, description="Retract after each probe (mm)")
    feed_probe: float = Field(100.0, ge=10.0, le=500.0, description="Probing feed rate (mm/min)")
    safe_z: float = Field(10.0, ge=5.0, le=50.0, description="Safe Z height (mm)")


class SetupSheetIn(BaseModel):
    """Setup sheet generation input."""
    pattern: Literal[
        "corner_outside", "corner_inside",
        "boss_circular", "hole_circular",
        "pocket_inside", "surface_z"
    ]
    part_width: Optional[float] = Field(100.0, description="Part width for corner/pocket (mm)")
    part_height: Optional[float] = Field(60.0, description="Part height for corner/pocket (mm)")
    feature_diameter: Optional[float] = Field(50.0, description="Boss/hole diameter (mm)")
    probe_offset: Optional[float] = Field(20.0, description="Probe offset from edge (mm)")
    origin_corner: Optional[str] = Field("lower_left", description="Origin location for pocket")


class ProbeOut(BaseModel):
    """Probe G-code output."""
    gcode: str
    stats: Dict[str, Any]


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
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Draft Lane: Fast preview, no RMOS tracking
# =============================================================================

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
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        resp.headers["X-ToolBox-Lane"] = "draft"
        return resp
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Governed Lane: Full RMOS artifact persistence and audit trail
# =============================================================================

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
        
        now = datetime.now(timezone.utc).isoformat()
        request_hash = sha256_of_obj(body.model_dump(mode="json"))
        gcode_hash = sha256_of_text(gcode)
        
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="corner_probe_gcode",
            workflow_mode="probing",
            event_type="corner_probe_gcode_execution",
            status="OK",
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)
        
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"corner_{body.pattern}_{wcs}.nc"
        
        resp = Response(
            content=gcode,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        resp.headers["X-Run-ID"] = run_id
        resp.headers["X-GCode-SHA256"] = gcode_hash
        resp.headers["X-ToolBox-Lane"] = "governed"
        return resp
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        resp.headers["X-ToolBox-Lane"] = "draft"
        return resp
    
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
        
        now = datetime.now(timezone.utc).isoformat()
        request_hash = sha256_of_obj(body.model_dump(mode="json"))
        gcode_hash = sha256_of_text(gcode)
        
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="boss_probe_gcode",
            workflow_mode="probing",
            event_type="boss_probe_gcode_execution",
            status="OK",
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)
        
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"boss_{body.pattern}_{wcs}.nc"
        
        resp = Response(
            content=gcode,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        resp.headers["X-Run-ID"] = run_id
        resp.headers["X-GCode-SHA256"] = gcode_hash
        resp.headers["X-ToolBox-Lane"] = "governed"
        return resp
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surface_z/gcode", response_model=ProbeOut)
async def generate_surface_z_probe(body: SurfaceZProbeIn) -> ProbeOut:
    """Generate G-code for surface Z touch-off."""
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset
        )
        
        stats = probe_patterns.get_statistics(gcode)
        stats["pattern"] = "surface_z"
        stats["work_offset"] = f"G{53 + body.work_offset}"
        
        return ProbeOut(gcode=gcode, stats=stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surface_z/gcode/download")
async def download_surface_z_probe(body: SurfaceZProbeIn) -> Response:
    """
    Download surface Z probe G-code as .nc file (DRAFT lane).
    
    This is the draft/preview lane - no RMOS artifact persistence.
    For governed execution with full audit trail, use /surface_z/gcode/download_governed.
    """
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset
        )
        
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"surface_z_{wcs}.nc"
        
        resp = Response(
            content=gcode,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        resp.headers["X-ToolBox-Lane"] = "draft"
        return resp
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surface_z/gcode/download_governed")
async def download_surface_z_probe_governed(body: SurfaceZProbeIn) -> Response:
    """
    Download surface Z probe G-code as .nc file (GOVERNED lane).
    
    Same toolpath as /surface_z/gcode/download but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    try:
        gcode = probe_patterns.generate_surface_z_probe(
            approach_z=body.approach_z,
            probe_depth=body.probe_depth,
            feed_probe=body.feed_probe,
            retract_distance=body.retract_distance,
            work_offset=body.work_offset
        )
        
        now = datetime.now(timezone.utc).isoformat()
        request_hash = sha256_of_obj(body.model_dump(mode="json"))
        gcode_hash = sha256_of_text(gcode)
        
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="surface_z_probe_gcode",
            workflow_mode="probing",
            event_type="surface_z_probe_gcode_execution",
            status="OK",
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)
        
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"surface_z_{wcs}.nc"
        
        resp = Response(
            content=gcode,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        resp.headers["X-Run-ID"] = run_id
        resp.headers["X-GCode-SHA256"] = gcode_hash
        resp.headers["X-ToolBox-Lane"] = "governed"
        return resp
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        resp.headers["X-ToolBox-Lane"] = "draft"
        return resp
    
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
        
        now = datetime.now(timezone.utc).isoformat()
        request_hash = sha256_of_obj(body.model_dump(mode="json"))
        gcode_hash = sha256_of_text(gcode)
        
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="pocket_probe_gcode",
            workflow_mode="probing",
            event_type="pocket_probe_gcode_execution",
            status="OK",
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)
        
        wcs = f"g{54 + body.work_offset - 1}"
        filename = f"pocket_inside_{wcs}.nc"
        
        resp = Response(
            content=gcode,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        resp.headers["X-Run-ID"] = run_id
        resp.headers["X-GCode-SHA256"] = gcode_hash
        resp.headers["X-ToolBox-Lane"] = "governed"
        return resp
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        resp.headers["X-ToolBox-Lane"] = "draft"
        return resp
    
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
        
        now = datetime.now(timezone.utc).isoformat()
        request_hash = sha256_of_obj(body.model_dump(mode="json"))
        gcode_hash = sha256_of_text(gcode)
        
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="vise_square_probe_gcode",
            workflow_mode="probing",
            event_type="vise_square_probe_gcode_execution",
            status="OK",
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)
        
        filename = "vise_squareness_check.nc"
        
        resp = Response(
            content=gcode,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        resp.headers["X-Run-ID"] = run_id
        resp.headers["X-GCode-SHA256"] = gcode_hash
        resp.headers["X-ToolBox-Lane"] = "governed"
        return resp
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup_sheet/svg")
async def generate_setup_sheet(body: SetupSheetIn) -> Response:
    """
    Generate SVG setup sheet for probing pattern.
    
    Returns SVG document with part outline, probe points, and dimensions.
    """
    try:
        if body.pattern in ["corner_outside", "corner_inside"]:
            svg = probe_svg.generate_corner_outside_sheet(
                part_width=body.part_width or 100.0,
                part_height=body.part_height or 60.0,
                probe_offset=body.probe_offset or 20.0
            )
        
        elif body.pattern in ["boss_circular", "hole_circular"]:
            svg = probe_svg.generate_boss_circular_sheet(
                boss_diameter=body.feature_diameter or 50.0
            )
        
        elif body.pattern == "pocket_inside":
            svg = probe_svg.generate_pocket_inside_sheet(
                pocket_width=body.part_width or 100.0,
                pocket_height=body.part_height or 60.0,
                origin_corner=body.origin_corner or "center"
            )
        
        elif body.pattern == "surface_z":
            svg = probe_svg.generate_surface_z_sheet()
        
        else:
            raise ValueError(f"Pattern '{body.pattern}' not implemented")
        
        filename = f"setup_{body.pattern}.svg"
        
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def list_probe_patterns() -> Dict[str, Any]:
    """List all available probing patterns with metadata."""
    return {
        "patterns": probe_patterns.get_probe_patterns()
    }
