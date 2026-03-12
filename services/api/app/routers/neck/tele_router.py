"""
Telecaster neck router - Fender Tele-specific endpoints.

Extracted from neck_router.py.
"""
from fastapi import APIRouter, HTTPException
from typing import List

from .schemas import TeleNeckParameters, NeckGeometryOut, NeckParameters, Point2D
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

router = APIRouter(tags=["neck", "telecaster"])


def _resolve_tele_dims(params: TeleNeckParameters) -> NeckDimensions:
    """Resolve TeleNeckParameters using Fender presets."""
    preset_key = f"fender_{params.variant}"
    base = NECK_PRESETS.get(preset_key)
    if base is None:
        raise ValueError(f"Unknown Tele variant: {params.variant}")
    dims = NeckDimensions(
        blank_length_in=base.blank_length_in,
        blank_width_in=base.blank_width_in,
        blank_thickness_in=base.blank_thickness_in,
        nut_width_in=params.nut_width if params.nut_width is not None else base.nut_width_in,
        heel_width_in=base.heel_width_in,
        depth_at_1st_in=base.depth_at_1st_in,
        depth_at_12th_in=base.depth_at_12th_in,
        scale_length_in=params.scale_length if params.scale_length is not None else base.scale_length_in,
        headstock_angle_deg=0.0,
        headstock_thickness_in=base.headstock_thickness_in,
        headstock_length_in=base.headstock_length_in,
    )
    return dims


@router.post("/generate/telecaster", response_model=NeckGeometryOut)
def generate_telecaster_neck(params: TeleNeckParameters):
    """Generate Telecaster neck geometry with Telecaster headstock."""
    try:
        dims = _resolve_tele_dims(params)
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
            fretboard_radius=7.25 if params.variant == "vintage" else 9.5,
            include_fretboard=params.include_fretboard,
            num_frets=params.num_frets,
            thickness_1st_fret=dims.depth_at_1st_in,
            thickness_12th_fret=dims.depth_at_12th_in,
            headstock_angle=0.0,
            headstock_length=dims.headstock_length_in,
            headstock_thickness=dims.headstock_thickness_in,
            tuner_layout=0.9,
            tuner_diameter=0.375,
            units=params.units,
        )
        profile = generate_neck_profile(neck_params)
        fretboard = generate_fretboard_outline(neck_params) if params.include_fretboard else None

        outline = config_headstock_outline(HeadstockStyle.FENDER_TELE, dims)
        headstock = [Point2D(x=p[0], y=p[1]) for p in outline]
        positions = config_tuner_positions(HeadstockStyle.FENDER_TELE, dims)
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
        raise HTTPException(500, detail=f"Error generating Telecaster neck: {str(e)}")


@router.get("/telecaster/presets")
def get_telecaster_presets():
    """Get Telecaster neck presets."""
    return {
        "presets": [
            {
                "name": "Vintage 52 Telecaster",
                "variant": "vintage",
                "scale_length": 25.5,
                "nut_width": 1.625,
                "num_frets": 21,
                "fretboard_radius": 7.25,
                "description": "Classic 50s specs: U-profile, 1-5/8 in nut"
            },
            {
                "name": "American Telecaster",
                "variant": "modern",
                "scale_length": 25.5,
                "nut_width": 1.6875,
                "num_frets": 22,
                "fretboard_radius": 9.5,
                "description": "Modern C-profile, 1-11/16 in nut"
            }
        ]
    }
