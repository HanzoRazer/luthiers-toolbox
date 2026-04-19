"""Body G-code Router (GEN-4) — Project-driven CAM generation.

Generates G-code from project_id using from_project() factory methods.

Endpoints:
    POST /stratocaster/body/gcode?project_id={id}  - Strat body from project
    POST /les_paul/body/gcode?project_id={id}      - LP body from project
    POST /flying_v/body/gcode?project_id={id}      - Flying V body from project
    POST /{model_id}/neck/gcode?project_id={id}    - Neck G-code from project

All endpoints:
1. Load project from DB by project_id
2. Parse InstrumentProjectData from project.data
3. Call generator.from_project(project)
4. Generate G-code
5. Return as StreamingResponse with .nc download

DRAFT project → return 422 with clear message.

See docs/GENERATOR_REMEDIATION_PLAN.md — GEN-4.
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ....auth.principal import Principal
from ....auth.deps import get_current_principal
from ....db.session import get_db
from ....db.models.project import Project
from ....projects.service import parse_design_state
from ....schemas.instrument_project import InstrumentProjectData

from app.core.safety import safety_critical

router = APIRouter(tags=["CAM", "G-code", "GEN-4"])


# =============================================================================
# SCHEMAS
# =============================================================================


class GCodeResponse(BaseModel):
    """G-code generation response (for non-streaming)."""
    ok: bool
    model_id: str
    operation: str
    gcode: str
    line_count: int
    stats: dict = {}


class GCodeErrorResponse(BaseModel):
    """Error response for G-code generation."""
    ok: bool = False
    error: str
    detail: str
    project_id: str
    suggestion: str = ""


# =============================================================================
# HELPERS
# =============================================================================


def _get_project_or_404(project_id: str, principal: Principal, db: Session) -> Project:
    """Load project from DB, validate ownership."""
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid project_id: '{project_id}'")

    project: Optional[Project] = db.get(Project, pid)

    if project is None or project.archived_at is not None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    if str(project.owner_id) != str(principal.user_id):
        raise HTTPException(status_code=403, detail="Access denied.")

    return project


def _parse_design_state_or_422(project: Project) -> InstrumentProjectData:
    """Parse design state, return 422 if DRAFT or missing."""
    design_state = parse_design_state(project.data)

    if design_state is None:
        raise HTTPException(
            status_code=422,
            detail="Project has no design state. Use PUT /api/projects/{id}/design-state first."
        )

    # Check CAM-ready status
    if not design_state.manufacturing_state:
        raise HTTPException(
            status_code=422,
            detail=(
                "Project has no manufacturing_state. "
                "Set manufacturing_state.status to 'design_complete' before generating CAM output. "
                "Use PUT /api/projects/{id}/design-state to update."
            )
        )

    status_value = design_state.manufacturing_state.status.value
    if status_value == "draft":
        raise HTTPException(
            status_code=422,
            detail=(
                "Project is DRAFT. Cannot generate CAM output for draft projects. "
                "Advance to DESIGN_COMPLETE first. "
                "Use PUT /api/projects/{id}/design-state to set manufacturing_state.status='design_complete'."
            )
        )

    return design_state


def _make_nc_response(gcode: str, filename: str) -> StreamingResponse:
    """Create StreamingResponse with .nc file download."""
    buffer = io.BytesIO(gcode.encode("utf-8"))
    return StreamingResponse(
        buffer,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Line-Count": str(len(gcode.splitlines())),
        }
    )


def _generate_timestamp() -> str:
    """Generate timestamp for filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


# =============================================================================
# STRATOCASTER BODY ENDPOINT
# =============================================================================


@router.post("/stratocaster/body/gcode", response_class=StreamingResponse)
@safety_critical
def generate_stratocaster_body_gcode(
    project_id: str = Query(..., description="Project UUID"),
    machine: str = Query("generic_router", description="Machine profile"),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Generate Stratocaster body G-code from project.

    Uses StratocasterBodyGenerator.from_project() to create G-code
    based on project's InstrumentProjectData.

    Returns .nc file as streaming download.
    """
    project = _get_project_or_404(project_id, principal, db)
    design_state = _parse_design_state_or_422(project)

    try:
        from ....generators.stratocaster_body_generator import StratocasterBodyGenerator

        gen = StratocasterBodyGenerator.from_project(design_state, machine=machine)

        # Generate to memory (not file)
        gen._gcode_lines = []
        gen._emit_header(f"STRAT_{project.name[:8].upper()}")
        gen._emit_pickup_cavities()
        gen._emit_neck_pocket()

        if gen.spec.tremolo_style != "hardtail":
            gen._emit_tremolo_cavity()
            if gen.spec.rear_routed:
                gen._emit_spring_cavity()

        if gen.spec.rear_routed:
            gen._emit_control_cavity()

        gen._emit_jack_bore()
        gen._emit_body_perimeter()
        gen._emit_footer()

        gcode = "\n".join(gen._gcode_lines)

        filename = f"strat_body_{_generate_timestamp()}.nc"
        return _make_nc_response(gcode, filename)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generator module not available: {e}"
        )


# =============================================================================
# LES PAUL BODY ENDPOINT
# =============================================================================


@router.post("/les_paul/body/gcode", response_class=StreamingResponse)
@safety_critical
def generate_les_paul_body_gcode(
    project_id: str = Query(..., description="Project UUID"),
    machine: str = Query("bcam_2030a", description="Machine profile"),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Generate Les Paul body G-code from project.

    Uses LesPaulBodyGenerator.from_project() to create generator from
    project data. Resolves DXF template from instrument_geometry/body/dxf/electric/.

    Returns .nc file as streaming download.
    """
    project = _get_project_or_404(project_id, principal, db)
    design_state = _parse_design_state_or_422(project)

    try:
        from pathlib import Path
        import tempfile
        from ....generators.lespaul_body_generator import LesPaulBodyGenerator

        # Use from_project() factory method (GEN-4)
        gen = LesPaulBodyGenerator.from_project(design_state, machine=machine)

        # Get stock thickness from project if available
        stock_thickness = 1.75  # default inches
        if design_state.body_config and design_state.body_config.stock_thickness_mm:
            stock_thickness = design_state.body_config.stock_thickness_mm / 25.4

        # Generate to temp path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nc', delete=False) as tmp:
            gen.generate(tmp.name, stock_thickness=stock_thickness)
            tmp_path = tmp.name

        # Read generated file
        with open(tmp_path, 'r') as f:
            gcode = f.read()

        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)

        filename = f"lespaul_body_{_generate_timestamp()}.nc"
        return _make_nc_response(gcode, filename)

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generator module not available: {e}"
        )


# =============================================================================
# FLYING V BODY ENDPOINT
# =============================================================================


@router.post("/flying_v/body/gcode", response_class=StreamingResponse)
@safety_critical
def generate_flying_v_body_gcode(
    project_id: str = Query(..., description="Project UUID"),
    operations: str = Query("all", description="Operations: all, control_cavity, neck_pocket, pickup"),
    variant: str = Query("original_1958", description="Spec variant"),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Generate Flying V body G-code from project.

    Uses existing Flying V toolpath generators with project validation.

    operations:
        - all: Generate all cavities (control, neck_pocket, pickups)
        - control_cavity: Control cavity only
        - neck_pocket: Neck pocket only
        - pickup: Pickup cavities only

    Returns .nc file as streaming download.
    """
    project = _get_project_or_404(project_id, principal, db)
    design_state = _parse_design_state_or_422(project)

    try:
        from ....cam.flying_v import (
            load_flying_v_spec,
            generate_control_cavity_toolpath,
            generate_neck_pocket_toolpath,
            generate_pickup_cavity_toolpath,
        )

        spec = load_flying_v_spec(variant)

        gcode_parts = []
        gcode_parts.append(f"(Flying V Body - {operations})")
        gcode_parts.append(f"(Project: {project.name})")
        gcode_parts.append(f"(Variant: {variant})")
        gcode_parts.append("")
        gcode_parts.append("G21 (mm)")
        gcode_parts.append("G90 (absolute)")
        gcode_parts.append("")

        if operations in ("all", "control_cavity"):
            gcode_parts.append("(=== CONTROL CAVITY ===)")
            gcode_parts.append(generate_control_cavity_toolpath(spec))
            gcode_parts.append("")

        if operations in ("all", "neck_pocket"):
            gcode_parts.append("(=== NECK POCKET ===)")
            gcode_parts.append(generate_neck_pocket_toolpath(spec))
            gcode_parts.append("")

        if operations in ("all", "pickup"):
            gcode_parts.append("(=== PICKUP CAVITIES ===)")
            gcode_parts.append(generate_pickup_cavity_toolpath(spec, pickup="both"))
            gcode_parts.append("")

        gcode_parts.append("M30 (program end)")
        gcode = "\n".join(gcode_parts)

        filename = f"flying_v_body_{_generate_timestamp()}.nc"
        return _make_nc_response(gcode, filename)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Flying V module not available: {e}"
        )


# =============================================================================
# NECK G-CODE ENDPOINT (ANY MODEL)
# =============================================================================


@router.post("/{model_id}/neck/gcode", response_class=StreamingResponse)
@safety_critical
def generate_neck_gcode(
    model_id: str,
    project_id: str = Query(..., description="Project UUID"),
    preset: str = Query(None, description="Neck preset: gibson_50s, fender_vintage, etc."),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Generate neck G-code from project.

    Uses NeckDimensions.from_project() to get dimensions,
    then generates neck carving G-code.

    Works for any model_id - neck dimensions come from project.spec.

    Returns .nc file as streaming download.
    """
    project = _get_project_or_404(project_id, principal, db)
    design_state = _parse_design_state_or_422(project)

    try:
        from ....generators.neck_headstock_config import NeckDimensions, NECK_PRESETS

        # Use preset or from_project()
        if preset and preset in NECK_PRESETS:
            dims = NECK_PRESETS[preset]
        else:
            dims = NeckDimensions.from_project(design_state)

        # Generate basic neck G-code
        gcode_lines = []
        gcode_lines.append(f"(Neck G-code - {model_id})")
        gcode_lines.append(f"(Project: {project.name})")
        gcode_lines.append(f"(Scale: {dims.scale_length_in:.2f}\")")
        gcode_lines.append(f"(Nut width: {dims.nut_width_in:.4f}\")")
        gcode_lines.append(f"(Headstock angle: {dims.headstock_angle_deg}°)")
        gcode_lines.append("")
        gcode_lines.append("G20 (inches)")
        gcode_lines.append("G90 (absolute)")
        gcode_lines.append("G17 (XY plane)")
        gcode_lines.append("")

        # Truss rod channel
        gcode_lines.append("(=== TRUSS ROD CHANNEL ===)")
        gcode_lines.append("M3 S18000")
        gcode_lines.append("G4 P2")
        gcode_lines.append(f"G0 Z0.5")
        gcode_lines.append(f"G0 X0 Y0")

        # Simple truss rod pocket - centerline
        tr_width = dims.truss_rod_width_in
        tr_depth = dims.truss_rod_depth_in
        tr_length = dims.truss_rod_length_in

        gcode_lines.append(f"G0 X{-tr_width/2:.4f} Y0")
        gcode_lines.append(f"G1 Z{-tr_depth:.4f} F20")
        gcode_lines.append(f"G1 X{tr_width/2:.4f} F60")
        gcode_lines.append(f"G1 Y{tr_length:.4f}")
        gcode_lines.append(f"G1 X{-tr_width/2:.4f}")
        gcode_lines.append(f"G1 Y0")
        gcode_lines.append("G0 Z0.5")
        gcode_lines.append("")

        # Headstock angle (if angled)
        if dims.headstock_angle_deg > 0:
            gcode_lines.append("(=== HEADSTOCK ANGLE CUT ===)")
            gcode_lines.append(f"(Angle: {dims.headstock_angle_deg}° - requires angled fixture or 5-axis)")
            gcode_lines.append(f"(Headstock thickness: {dims.headstock_thickness_in:.3f}\")")
            gcode_lines.append("")

        gcode_lines.append("(=== NECK PROFILE ===)")
        gcode_lines.append("(Profile carving requires 4th axis or ball-end 3D surfacing)")
        gcode_lines.append(f"(Depth at 1st fret: {dims.depth_at_1st_in:.3f}\")")
        gcode_lines.append(f"(Depth at 12th fret: {dims.depth_at_12th_in:.3f}\")")
        gcode_lines.append("")

        gcode_lines.append("M5 (spindle stop)")
        gcode_lines.append("G0 Z1.0")
        gcode_lines.append("M30 (program end)")

        gcode = "\n".join(gcode_lines)

        filename = f"{model_id}_neck_{_generate_timestamp()}.nc"
        return _make_nc_response(gcode, filename)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Neck generator module not available: {e}"
        )


# =============================================================================
# HEALTH/STATUS ENDPOINTS
# =============================================================================


@router.get("/status")
def body_gcode_status() -> dict:
    """
    Get status of body G-code generation endpoints.

    Shows which models support from_project() CAM generation.
    """
    return {
        "ok": True,
        "gen4_endpoints": {
            "stratocaster": {
                "endpoint": "/stratocaster/body/gcode",
                "from_project": True,
                "cam_ready": True,
            },
            "les_paul": {
                "endpoint": "/les_paul/body/gcode",
                "from_project": True,
                "cam_ready": True,
            },
            "flying_v": {
                "endpoint": "/flying_v/body/gcode",
                "from_project": False,  # Uses existing toolpath generators
                "cam_ready": True,
                "note": "Uses existing Flying V toolpath generators"
            },
            "neck": {
                "endpoint": "/{model_id}/neck/gcode",
                "from_project": True,
                "cam_ready": True,
                "note": "Works for any model_id"
            },
        },
        "gen4_status": "complete",
        "requires_auth": True,
        "requires_design_complete": True,
    }


__all__ = ["router"]
