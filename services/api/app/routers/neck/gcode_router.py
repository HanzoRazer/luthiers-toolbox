"""
Neck G-code router - CNC G-code generation endpoints.

Extracted from neck_router.py.
OM-GAP-07: Wraps NeckGCodeGenerator class in HTTP endpoints.

STRUCTURAL OWNERSHIP NOTE
-------------------------
This module also hosts the project-driven guitar neck G-code route, exported as
``guitar_neck_router``. Its implementation lives here because a neck manufacturing
route belongs with neck routing, not in a body G-code router -- but its **public
URL is unchanged** and remains under the guitar CAM prefix::

    POST /api/cam/guitar/{model_id}/neck/gcode

``routers/cam/guitar/__init__`` mounts ``guitar_neck_router`` to preserve that path.
Relocating it must not create a new router module when this one already exists.

This is NOT the separately tracked neck path in ``cam_workspace_router`` that
carries the standing rapids-at-cutting-depth finding; that one is contained under
its own key by LTB-REMEDIATE-P1.

``/gcode/generate`` and ``/gcode/download`` are contained by LTB-REMEDIATE-P2
under ``neck_gcode_generator``: both reach ``NeckGCodeGenerator``, a third neck
implementation distinct from the inline handler that ``"neck"`` governs.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .schemas import NeckGcodeRequest, NeckGcodeResponse

from ...generators.neck_headstock_config import (
    HeadstockStyle,
    NeckProfile,
    NeckDimensions,
    NECK_PRESETS,
    NECK_TOOLS,
)
from ...generators.neck_headstock_generator import NeckGCodeGenerator
from ...auth.deps import get_current_principal
from ...auth.principal import Principal
from ...db.session import get_db
from app.core.safety import safety_critical

from .._project_gcode_common import (
    _generate_timestamp,
    _get_project_or_404,
    _make_nc_response,
    _parse_design_state_or_422,
    _readiness_gate,
)

router = APIRouter(prefix="/gcode", tags=["neck", "gcode"])


@router.post("/generate", response_model=NeckGcodeResponse)
def generate_neck_gcode(req: NeckGcodeRequest):
    """
    Generate G-code for neck CNC machining.

    OM-GAP-07: Wraps NeckGCodeGenerator class in HTTP endpoint.

    Operations generated:
    - OP10: Truss rod channel
    - OP20: Headstock outline
    - OP30: Tuner holes
    - OP40: Neck profile rough

    Returns G-code with operation stats.

    Contained by LTB-REMEDIATE-P2: readiness is consulted before preset
    resolution, input parsing or generator construction.
    """
    _readiness_gate("neck_gcode_generator")

    try:
        # Resolve dimensions from preset or defaults
        if req.preset and req.preset in NECK_PRESETS:
            dims = NECK_PRESETS[req.preset]
        else:
            dims = NeckDimensions()

        # Apply overrides
        if req.scale_length is not None:
            dims = NeckDimensions(
                blank_length_in=dims.blank_length_in,
                blank_width_in=dims.blank_width_in,
                blank_thickness_in=dims.blank_thickness_in,
                nut_width_in=req.nut_width if req.nut_width is not None else dims.nut_width_in,
                heel_width_in=req.heel_width if req.heel_width is not None else dims.heel_width_in,
                depth_at_1st_in=dims.depth_at_1st_in,
                depth_at_12th_in=dims.depth_at_12th_in,
                scale_length_in=req.scale_length,
                headstock_angle_deg=dims.headstock_angle_deg,
                headstock_thickness_in=dims.headstock_thickness_in,
                headstock_length_in=dims.headstock_length_in,
            )

        # Parse headstock style
        try:
            headstock_style = HeadstockStyle(req.headstock_style)
        except ValueError:
            headstock_style = HeadstockStyle.PADDLE

        # Parse profile
        try:
            profile = NeckProfile(req.profile)
        except ValueError:
            profile = NeckProfile.C_SHAPE

        # Generate G-code
        generator = NeckGCodeGenerator(
            dims=dims,
            headstock_style=headstock_style,
            profile=profile,
            tools=NECK_TOOLS,
        )

        gcode = generator.generate_full_program(req.job_name)

        return NeckGcodeResponse(
            gcode=gcode,
            line_count=len(gcode.splitlines()),
            operations=generator.stats.get("operations", []),
            headstock_style=headstock_style.value,
            profile=profile.value,
            scale_length=dims.scale_length_in,
            nut_width=dims.nut_width_in,
        )

    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        raise HTTPException(500, detail=f"Error generating neck G-code: {str(e)}")


@router.post("/download", response_class=Response)
def download_neck_gcode(req: NeckGcodeRequest):
    """
    Generate and download neck G-code as .nc file.

    Same parameters as /generate but returns a downloadable file.

    Gated here as well as in ``generate_neck_gcode``, under the same key, so the
    containment does not depend on this route continuing to delegate. Refusal
    happens before the delegated call, so nothing is generated twice.
    """
    _readiness_gate("neck_gcode_generator")

    try:
        result = generate_neck_gcode(req)
        style = result.headstock_style.replace("_", "-")
        filename = f"neck_{style}_{result.scale_length:.2f}in.nc"

        return Response(
            content=result.gcode,
            media_type="text/x-gcode",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        raise HTTPException(500, detail=f"Error downloading neck G-code: {str(e)}")


@router.get("/styles")
def get_gcode_headstock_styles():
    """Get available headstock styles for G-code generation."""
    return {
        "styles": [
            {"id": style.value, "name": style.value.replace("_", " ").title()}
            for style in HeadstockStyle
        ]
    }


@router.get("/profiles")
def get_gcode_neck_profiles():
    """Get available neck profiles for G-code generation."""
    return {
        "profiles": [
            {"id": profile.value, "name": profile.value.replace("_", " ").title()}
            for profile in NeckProfile
        ]
    }


@router.get("/tools")
def get_gcode_tool_library():
    """Get the tool library used for neck G-code generation."""
    return {
        "tools": [
            {
                "number": tool.number,
                "name": tool.name,
                "diameter_in": tool.diameter_in,
                "rpm": tool.rpm,
                "feed_ipm": tool.feed_ipm,
                "plunge_ipm": tool.plunge_ipm,
                "stepdown_in": tool.stepdown_in,
            }
            for tool in NECK_TOOLS.values()
        ]
    }

def _build_guitar_neck_router() -> APIRouter:
    """Build the router mounted by the guitar package at the unchanged public path.

    The APIRouter is named ``router`` inside this factory on purpose. The repo's
    route-count gate (``ci/router_count_gate.py``) counts decorators written
    against a router object literally named ``router``; a differently-named object
    would make this route
    invisible to that gate -- a false negative, not an improvement. Keeping the
    convention keeps the route countable by governance.

    No prefix here: ``routers/cam/guitar`` supplies it.
    """
    router = APIRouter(tags=["G-code", "Neck"])

    @router.post("/{model_id}/neck/gcode", response_class=StreamingResponse)
    @safety_critical
    def generate_guitar_neck_gcode(
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

        _readiness_gate("neck")
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

    return router


#: Mounted by routers/cam/guitar so the public path
#: /api/cam/guitar/{model_id}/neck/gcode is unchanged.
guitar_neck_router = _build_guitar_neck_router()
