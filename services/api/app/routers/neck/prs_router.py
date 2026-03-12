"""
PRS neck router - PRS-style neck endpoints.

Extracted from neck_router.py.
"""
from fastapi import APIRouter, HTTPException
from typing import List

from .schemas import PRSNeckParameters, NeckGeometryOut, NeckParameters, Point2D
from .geometry import (
    calculate_fret_positions,
    generate_neck_profile,
    generate_fretboard_outline,
    generate_centerline,
    convert_points,
    convert_value,
)

from ...generators.neck_headstock_config import (
    HeadstockStyle,
    NeckDimensions,
    NECK_PRESETS,
    generate_headstock_outline as config_headstock_outline,
    generate_tuner_positions as config_tuner_positions,
)

router = APIRouter(tags=["neck", "prs"])


@router.post("/generate/prs", response_model=NeckGeometryOut)
def generate_prs_neck(params: PRSNeckParameters):
    """Generate PRS-style neck geometry with PRS headstock."""
    try:
        base = NECK_PRESETS.get("prs")
        if base is None:
            raise ValueError("PRS preset not found")

        dims = NeckDimensions(
            blank_length_in=base.blank_length_in,
            blank_width_in=base.blank_width_in,
            blank_thickness_in=base.blank_thickness_in,
            nut_width_in=params.nut_width,
            heel_width_in=base.heel_width_in,
            depth_at_1st_in=base.depth_at_1st_in,
            depth_at_12th_in=base.depth_at_12th_in,
            scale_length_in=params.scale_length,
            headstock_angle_deg=base.headstock_angle_deg,
            headstock_thickness_in=base.headstock_thickness_in,
            headstock_length_in=base.headstock_length_in,
        )
        fret_positions = calculate_fret_positions(dims.scale_length_in, params.num_frets)

        neck_params = NeckParameters(
            blank_length=dims.blank_length_in,
            blank_width=dims.blank_width_in,
            blank_thickness=dims.blank_thickness_in,
            scale_length=dims.scale_length_in,
            nut_width=dims.nut_width_in,
            heel_width=dims.heel_width_in,
            neck_length=17.0,
            neck_angle=0.0,
            fretboard_radius=10.0,
            include_fretboard=params.include_fretboard,
            num_frets=params.num_frets,
            thickness_1st_fret=dims.depth_at_1st_in,
            thickness_12th_fret=dims.depth_at_12th_in,
            headstock_angle=dims.headstock_angle_deg,
            headstock_length=dims.headstock_length_in,
            headstock_thickness=dims.headstock_thickness_in,
            tuner_layout=2.0,
            tuner_diameter=0.375,
            units=params.units,
        )
        profile = generate_neck_profile(neck_params)
        fretboard = generate_fretboard_outline(neck_params) if params.include_fretboard else None

        outline = config_headstock_outline(HeadstockStyle.PRS, dims)
        headstock = [Point2D(x=p[0], y=p[1]) for p in outline]
        positions = config_tuner_positions(HeadstockStyle.PRS, dims)
        tuners = [Point2D(x=p[0], y=p[1]) for p in positions]
        centerline = generate_centerline(neck_params)

        if params.units != "in":
            profile = convert_points(profile, "in", params.units)
            if fretboard:
                fretboard = convert_points(fretboard, "in", params.units)
            headstock = convert_points(headstock, "in", params.units)
            tuners = convert_points(tuners, "in", params.units)
            centerline = convert_points(centerline, "in", params.units)
            fret_positions = [convert_value(f, "in", params.units) for f in fret_positions]
            scale_out = convert_value(dims.scale_length_in, "in", params.units)
        else:
            scale_out = dims.scale_length_in

        return NeckGeometryOut(
            profile_points=profile,
            fretboard_points=fretboard,
            fret_positions=fret_positions,
            headstock_points=headstock,
            tuner_holes=tuners,
            centerline=centerline,
            units=params.units,
            scale_length=scale_out,
        )
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(500, detail=f"Error generating PRS neck: {str(e)}")


@router.get("/prs/presets")
def get_prs_presets():
    """Get PRS neck presets."""
    return {
        "presets": [
            {
                "name": "PRS Custom 24",
                "scale_length": 25.0,
                "nut_width": 1.6875,
                "num_frets": 24,
                "fretboard_radius": 10.0,
                "headstock_angle": 10.0,
                "description": "PRS signature 25 in scale, Pattern neck"
            },
            {
                "name": "PRS McCarty 594",
                "scale_length": 24.594,
                "nut_width": 1.6875,
                "num_frets": 22,
                "fretboard_radius": 10.0,
                "headstock_angle": 10.0,
                "description": "Vintage-inspired shorter scale"
            }
        ]
    }
