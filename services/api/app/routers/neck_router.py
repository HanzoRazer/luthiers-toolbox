"""
Neck Generator Router - Core Les Paul Style Neck with DXF Export

This is the main neck router that includes sub-routers for different
neck styles (Stratocaster, Telecaster, PRS) and G-code generation.

Decomposed from 1,139 LOC monolith:
- neck/schemas.py: Pydantic models
- neck/geometry.py: Pure geometry functions
- neck/export.py: DXF export
- neck/strat_router.py: Stratocaster endpoints
- neck/tele_router.py: Telecaster endpoints
- neck/prs_router.py: PRS endpoints
- neck/gcode_router.py: G-code generation
"""

from fastapi import APIRouter, HTTPException, Response

# Import schemas from decomposed module
from .neck.schemas import (
    Point2D,
    NeckParameters,
    NeckGeometryOut,
)

# Import geometry functions from decomposed module
from .neck.geometry import (
    calculate_fret_positions,
    generate_neck_profile,
    generate_fretboard_outline,
    generate_headstock_outline,
    generate_tuner_holes,
    generate_centerline,
    convert_points,
    convert_value,
)

# Import DXF export from decomposed module
from .neck.export import export_neck_dxf

# Import break angle calculator
from ..calculators.headstock_break_angle import (
    HeadstockBreakAngleInput,
    HeadstockBreakAngleResult,
    calculate_headstock_break_angle,
)

# Import sub-routers
from .neck import strat_router, tele_router, prs_router, gcode_router


# ============================================================================
# MAIN ROUTER SETUP
# ============================================================================

router = APIRouter(prefix="/neck", tags=["neck"])

# Include sub-routers for different neck styles
router.include_router(strat_router.router)
router.include_router(tele_router.router)
router.include_router(prs_router.router)
router.include_router(gcode_router.router)


# ============================================================================
# CORE LES PAUL ENDPOINTS
# ============================================================================

@router.post("/generate", response_model=NeckGeometryOut)
def generate_neck(params: NeckParameters):
    """
    Generate Les Paul neck geometry.

    Returns JSON with all geometry points.
    """
    try:
        # Calculate fret positions (in input units)
        fret_positions = calculate_fret_positions(params.scale_length, params.num_frets)

        # Generate geometry (in input units)
        profile = generate_neck_profile(params)
        fretboard = generate_fretboard_outline(params) if params.include_fretboard else None
        headstock = generate_headstock_outline(params)
        tuners = generate_tuner_holes(params)
        centerline = generate_centerline(params)

        # Convert to output units if needed
        input_units = "in"  # All params are in inches
        if params.units != input_units:
            profile = convert_points(profile, input_units, params.units)
            if fretboard:
                fretboard = convert_points(fretboard, input_units, params.units)
            headstock = convert_points(headstock, input_units, params.units)
            tuners = convert_points(tuners, input_units, params.units)
            centerline = convert_points(centerline, input_units, params.units)
            fret_positions = [convert_value(f, input_units, params.units) for f in fret_positions]
            scale_length_out = convert_value(params.scale_length, input_units, params.units)
        else:
            scale_length_out = params.scale_length

        return NeckGeometryOut(
            profile_points=profile,
            fretboard_points=fretboard,
            fret_positions=fret_positions,
            headstock_points=headstock,
            tuner_holes=tuners,
            centerline=centerline,
            units=params.units,
            scale_length=scale_length_out
        )

    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (ValueError, KeyError, TypeError, ZeroDivisionError) as e:  # WP-1: geometry calc
        raise HTTPException(500, detail=f"Error generating neck: {str(e)}")


@router.post("/export_dxf", response_class=Response)
def export_dxf(params: NeckParameters):
    """
    Generate and export neck geometry as DXF R12 file.

    Returns DXF file ready for CAM software import.
    """
    try:
        # Generate geometry first
        geometry_response = generate_neck(params)

        # Export to DXF
        dxf_bytes = export_neck_dxf(params, geometry_response)

        # Return as downloadable file
        filename = f"les_paul_neck_{params.scale_length:.2f}{params.units}.dxf"

        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except (ValueError, KeyError, TypeError, OSError) as e:  # WP-1: geometry + DXF export
        raise HTTPException(500, detail=f"Error exporting DXF: {str(e)}")


@router.get("/presets")
def get_neck_presets():
    """
    Get standard neck presets.

    Returns common Les Paul configurations.
    """
    return {
        "presets": [
            {
                "name": "Les Paul Standard (24.75\")",
                "scale_length": 24.75,
                "nut_width": 1.695,
                "neck_angle": 4.0,
                "fretboard_radius": 12.0,
                "headstock_angle": 14.0
            },
            {
                "name": "Les Paul Custom (24.75\")",
                "scale_length": 24.75,
                "nut_width": 1.695,
                "neck_angle": 5.0,
                "fretboard_radius": 12.0,
                "headstock_angle": 17.0
            },
            {
                "name": "SG (24.75\")",
                "scale_length": 24.75,
                "nut_width": 1.650,
                "neck_angle": 3.0,
                "fretboard_radius": 12.0,
                "headstock_angle": 14.0
            }
        ]
    }


# ============================================================================
# NUT BREAK ANGLE CALCULATOR
# ============================================================================

@router.post("/break-angle", response_model=HeadstockBreakAngleResult)
def compute_nut_break_angle(req: HeadstockBreakAngleInput) -> HeadstockBreakAngleResult:
    """
    Calculate string break angle at the nut.

    For angled headstocks (Gibson/PRS), computes the effective angle from
    the headstock pitch, nut-to-tuner distance, and tuner post height.

    For flat headstocks (Fender), computes the angle from string tree
    depression or returns 0 if no tree is present (with a recommendation
    to add one).

    Optimal nut break angle: 5-10 degrees.
    """
    return calculate_headstock_break_angle(req)
