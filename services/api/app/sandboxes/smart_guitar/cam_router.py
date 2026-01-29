"""
Smart Guitar CAM Router (SG-SBX-0.1)
====================================

Manufacturing projection endpoints for Smart Guitar.
Mounted at: /api/cam/smart-guitar/*
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from .planner import generate_plan
from .geometry_resolver import resolve_geometry, generate_combined_dxf
from .schemas import SmartGuitarSpec, Handedness
from .generate_gcode import generate_smart_guitar_gcode, GCodeConfig, GCodeEmitter


router = APIRouter()


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class TemplatesResponse(BaseModel):
    """Available CAM templates response."""
    cavities: List[str]
    brackets: List[str]
    channels: List[str]
    notes: List[str]


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/templates", response_model=TemplatesResponse)
def templates():
    """
    Get available CAM template IDs.
    
    v0.1: Returns known template ids.
    Future: Will return geometry parameters.
    """
    return TemplatesResponse(
        cavities=[
            "cavity_bass_main_v1",
            "cavity_treble_main_v1",
            "cavity_tail_wing_v1",
            "pod_rh_v1",
            "pod_lh_v1",
        ],
        brackets=[
            "bracket_pi5_v1",
            "bracket_arduino_uno_r4_v1",
            "bracket_hifiberry_dac_adc_v1",
            "bracket_battery_pack_v1",
            "bracket_fan_40mm_v1",
        ],
        channels=[
            "wire_routes_rh_v1",
            "wire_routes_lh_v1",
            "drill_passages_rh_v1",
            "drill_passages_lh_v1",
        ],
        notes=["Templates are intent-level in v0.1; no DXF export yet."],
    )


@router.post("/plan")
def plan(spec: SmartGuitarSpec):
    """
    Generate a CAM plan from a Smart Guitar specification.
    
    The plan includes:
    - Cavity definitions with depths and template references
    - Bracket mounting templates for each electronics component
    - Wire channel routes (routed and drilled)
    - Toolpath operations with conservative defaults
    
    Returns:
        SmartCamPlan with all manufacturing data, plus validation warnings/errors
    """
    return generate_plan(spec).model_dump()


@router.get("/health")
def health():
    """CAM subsystem health check."""
    return {
        "ok": True,
        "subsystem": "smart_guitar_cam",
        "model_id": "smart_guitar",
        "contract_version": "1.0",
        "capabilities": [
            "plan",
            "templates",
            "geometry",
            "gcode",
        ],
        "notes": ["v1.0: Full CAM pipeline with G-code generation."],
    }


# =============================================================================
# GEOMETRY ENDPOINTS
# =============================================================================


class GeometryRequest(BaseModel):
    """Request for geometry resolution."""
    handedness: str = Field("RH", description="RH or LH")


@router.post("/geometry")
def geometry(req: GeometryRequest):
    """
    Resolve Smart Guitar geometry from templates.

    Returns positioned cavity geometry based on handedness.
    """
    spec = SmartGuitarSpec(
        handedness=Handedness.RH if req.handedness == "RH" else Handedness.LH
    )
    plan = generate_plan(spec)
    resolved = resolve_geometry(plan)
    return resolved.to_dict()


# =============================================================================
# G-CODE GENERATION ENDPOINTS
# =============================================================================


class GCodeRequest(BaseModel):
    """Request for G-code generation."""
    handedness: str = Field("RH", description="RH or LH")
    post_processor: str = Field("GRBL", description="GRBL, Mach4, or LinuxCNC")
    safe_z_mm: float = Field(10.0, description="Safe Z height in mm")
    units: str = Field("mm", description="mm or inch")


class GCodeResponse(BaseModel):
    """G-code generation response."""
    ok: bool
    lines: int
    operations: List[str]
    tools_used: List[str]
    gcode: str
    notes: List[str]


@router.post("/gcode", response_model=GCodeResponse)
def gcode(req: GCodeRequest):
    """
    Generate complete G-code for Smart Guitar manufacturing.

    Full pipeline: SmartGuitarSpec → SmartCamPlan → ResolvedGeometry → G-code

    Returns G-code program with all cavity operations.
    """
    from .generate_gcode import (
        generate_pocket_spiral,
        generate_contour_path,
        generate_drill_path,
        TOOL_LIBRARY,
    )

    # Create spec
    spec = SmartGuitarSpec(
        handedness=Handedness.RH if req.handedness == "RH" else Handedness.LH
    )

    # Generate plan
    plan = generate_plan(spec)

    # Resolve geometry
    geometry = resolve_geometry(plan)

    # Generate G-code
    config = GCodeConfig(
        safe_z=req.safe_z_mm,
        units=req.units,
        post_processor=req.post_processor,
    )
    emitter = GCodeEmitter(config)

    # Header
    emitter.header("SMART_GUITAR_API")
    emitter.comment(f"Handedness: {req.handedness}")
    emitter.comment(f"Body: {geometry.body_width_mm:.1f} x {geometry.body_height_mm:.1f} mm")
    emitter.blank_line()

    operations_run = []
    tools_used = set()

    # Process operations
    for op in plan.ops:
        emitter.comment(f"=== {op.op_id}: {op.title} ===")
        emitter.tool_change(op.tool)
        tools_used.add(op.tool)
        operations_run.append(f"{op.op_id}: {op.title}")

        tool = TOOL_LIBRARY[op.tool]
        tool_dia = tool["diameter_mm"]
        stepover = op.stepover_in * 25.4
        stepdown = op.max_stepdown_in * 25.4
        depth = op.depth_in * 25.4

        # Process cavities for this operation
        if op.op_id in ["OP10", "OP20", "OP50"]:
            for cavity in plan.cavities:
                template_id = cavity.template_id
                if template_id in geometry.cavities:
                    cavity_data = geometry.cavities[template_id]
                    if cavity_data.get("status") != "resolved":
                        continue

                    points = cavity_data.get("geometry", {}).get("points", [])
                    if not points:
                        continue

                    emitter.comment(f"Cavity: {template_id}")
                    passes = generate_pocket_spiral(points, tool_dia, stepover, depth, stepdown)

                    for pass_points in passes:
                        if not pass_points:
                            continue
                        emitter.rapid_to(pass_points[0][0], pass_points[0][1])
                        emitter.plunge_to(pass_points[0][2])
                        for pt in pass_points[1:]:
                            emitter.cut_to(pt[0], pt[1], pt[2])
                        emitter.retract()

        elif op.op_id == "OP30":
            for channel in plan.channels:
                template_id = channel.template_id
                if template_id in geometry.cavities:
                    channel_data = geometry.cavities[template_id]
                    if channel_data.get("status") != "resolved":
                        continue

                    points = channel_data.get("geometry", {}).get("points", [])
                    if not points:
                        continue

                    emitter.comment(f"Channel: {template_id}")
                    passes = generate_contour_path(points, depth, stepdown)

                    for pass_points in passes:
                        if not pass_points:
                            continue
                        emitter.rapid_to(pass_points[0][0], pass_points[0][1])
                        emitter.plunge_to(pass_points[0][2])
                        for pt in pass_points[1:]:
                            emitter.cut_to(pt[0], pt[1], pt[2])
                        emitter.retract()

        emitter.blank_line()

    emitter.footer()
    program = emitter.get_program()

    return GCodeResponse(
        ok=True,
        lines=len(program.split("\n")),
        operations=operations_run,
        tools_used=list(tools_used),
        gcode=program,
        notes=[
            f"Generated for {req.handedness} handedness",
            f"Post-processor: {req.post_processor}",
            f"Units: {req.units}",
        ],
    )


@router.post("/gcode.nc")
def gcode_download(req: GCodeRequest):
    """
    Generate and download G-code as .nc file.
    """
    result = gcode(req)
    return PlainTextResponse(
        content=result.gcode,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=smart_guitar_{req.handedness}.nc",
            "X-Lines": str(result.lines),
            "X-Operations": str(len(result.operations)),
        }
    )
