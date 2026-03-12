"""
Neck G-code router - CNC G-code generation endpoints.

Extracted from neck_router.py.
OM-GAP-07: Wraps NeckGCodeGenerator class in HTTP endpoints.
"""
from fastapi import APIRouter, HTTPException, Response

from .schemas import NeckGcodeRequest, NeckGcodeResponse

from ...generators.neck_headstock_config import (
    HeadstockStyle,
    NeckProfile,
    NeckDimensions,
    NECK_PRESETS,
    NECK_TOOLS,
)
from ...generators.neck_headstock_generator import NeckGCodeGenerator

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
    """
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
    """
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
