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

from ....instrument_geometry.dxf_authority import ManufacturingAuthorityBlocked
from ..._project_gcode_common import (
    _generate_timestamp,
    _get_project_or_404,
    _make_nc_response,
    _parse_design_state_or_422,
    _readiness_gate,
)
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

    _readiness_gate("stratocaster_body")
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

    _readiness_gate("les_paul_body")
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

    except ManufacturingAuthorityBlocked as e:
        # The catalog says this asset may not be manufactured from. Deterministic
        # client refusal with the asset's catalog-relative name, never a filesystem path.
        raise HTTPException(status_code=422, detail=e.as_detail())
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

    _readiness_gate("flying_v_body")
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
                "cam_ready": False,
                "note": "Generator readiness BLOCKED; no manufacturing emission permitted",
            },
            "les_paul": {
                "endpoint": "/les_paul/body/gcode",
                "from_project": True,
                "cam_ready": False,
                "note": "Delegates to DXF asset authority; currently blocked there",
            },
            "flying_v": {
                "endpoint": "/flying_v/body/gcode",
                "from_project": False,  # Uses existing toolpath generators
                "cam_ready": False,
                "note": "Generator readiness REVIEW_REQUIRED; no manufacturing emission permitted"
            },
            "neck": {
                "endpoint": "/{model_id}/neck/gcode",
                "from_project": True,
                "cam_ready": False,
                "note": "Generator readiness REVIEW_REQUIRED; no manufacturing emission permitted"
            },
        },
        "gen4_status": "complete",
        "requires_auth": True,
        "requires_design_complete": True,
    }


__all__ = ["router"]
