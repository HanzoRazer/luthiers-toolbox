"""Consolidated Guitar Neck Models Router.

Merged from:
- strat_router.py (Stratocaster)
- tele_router.py (Telecaster)
- prs_router.py (PRS)

Total: 6 routes for guitar-specific neck generation.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from .schemas import (
    StratNeckParameters,
    TeleNeckParameters,
    PRSNeckParameters,
    NeckGeometryOut,
    NeckParameters,
    Point2D,
)
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


router = APIRouter(tags=["neck", "guitar-models"])


# =============================================================================
# SHARED HELPERS
# =============================================================================


def _generate_headstock_outline(style: HeadstockStyle, dims: NeckDimensions) -> List[Point2D]:
    """Generate headstock outline as Point2D list."""
    outline = config_headstock_outline(style, dims)
    return [Point2D(x=p[0], y=p[1]) for p in outline]


def _generate_tuner_holes(style: HeadstockStyle, dims: NeckDimensions) -> List[Point2D]:
    """Generate tuner hole positions as Point2D list."""
    positions = config_tuner_positions(style, dims)
    return [Point2D(x=p[0], y=p[1]) for p in positions]


def _convert_output(
    profile, fretboard, headstock, tuners, centerline, fret_positions, scale_in, target_units
):
    """Convert all outputs to target units if needed."""
    if target_units != "in":
        profile = convert_points(profile, "in", target_units)
        if fretboard:
            fretboard = convert_points(fretboard, "in", target_units)
        headstock = convert_points(headstock, "in", target_units)
        tuners = convert_points(tuners, "in", target_units)
        centerline = convert_points(centerline, "in", target_units)
        fret_positions = [convert_value(f, "in", target_units) for f in fret_positions]
        scale_out = convert_value(scale_in, "in", target_units)
    else:
        scale_out = scale_in
    return profile, fretboard, headstock, tuners, centerline, fret_positions, scale_out


# =============================================================================
# STRATOCASTER ROUTES
# =============================================================================


def _resolve_strat_dims(params: StratNeckParameters) -> NeckDimensions:
    """Resolve StratNeckParameters into NeckDimensions using variant preset + overrides."""
    if params.variant == "24fret":
        preset_key = "strat_24fret"
    else:
        preset_key = f"fender_{params.variant}"
    base = NECK_PRESETS.get(preset_key)
    if base is None:
        raise ValueError(f"Unknown Strat variant: {params.variant}")
    return NeckDimensions(
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


@router.post("/generate/stratocaster", response_model=NeckGeometryOut)
def generate_stratocaster_neck(params: StratNeckParameters):
    """Generate Stratocaster neck geometry with Fender 6-inline headstock."""
    try:
        dims = _resolve_strat_dims(params)
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
            fretboard_radius=9.5 if params.variant == "vintage" else 12.0,
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
        headstock = _generate_headstock_outline(HeadstockStyle.FENDER_STRAT, dims)
        tuners = _generate_tuner_holes(HeadstockStyle.FENDER_STRAT, dims)
        centerline = generate_centerline(neck_params)

        profile, fretboard, headstock, tuners, centerline, fret_positions, scale_out = _convert_output(
            profile, fretboard, headstock, tuners, centerline, fret_positions, dims.scale_length_in, params.units
        )

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
        raise HTTPException(500, detail=f"Error generating Stratocaster neck: {str(e)}")


@router.get("/stratocaster/presets")
def get_stratocaster_presets():
    """Get Stratocaster neck presets."""
    return {
        "presets": [
            {
                "name": "Vintage '60s Stratocaster (25.5\")",
                "variant": "vintage",
                "scale_length": 25.5,
                "nut_width": 1.625,
                "num_frets": 21,
                "fretboard_radius": 7.25,
                "headstock_angle": 0.0,
                "description": "Pre-CBS Fender specs: 1-5/8\" nut, 7.25\" single radius",
            },
            {
                "name": "Modern Stratocaster (25.5\")",
                "variant": "modern",
                "scale_length": 25.5,
                "nut_width": 1.6875,
                "num_frets": 22,
                "fretboard_radius": 9.5,
                "headstock_angle": 0.0,
                "description": "American Standard/Professional: 1-11/16\" nut, 9.5-14\" compound radius",
            },
            {
                "name": "American Professional II (25.5\")",
                "variant": "modern",
                "scale_length": 25.5,
                "nut_width": 1.6875,
                "num_frets": 22,
                "fretboard_radius": 9.5,
                "headstock_angle": 0.0,
                "description": "Deep C profile, rolled fretboard edges",
            },
        ]
    }


# =============================================================================
# TELECASTER ROUTES
# =============================================================================


def _resolve_tele_dims(params: TeleNeckParameters) -> NeckDimensions:
    """Resolve TeleNeckParameters using Fender presets."""
    preset_key = f"fender_{params.variant}"
    base = NECK_PRESETS.get(preset_key)
    if base is None:
        raise ValueError(f"Unknown Tele variant: {params.variant}")
    return NeckDimensions(
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
        headstock = _generate_headstock_outline(HeadstockStyle.FENDER_TELE, dims)
        tuners = _generate_tuner_holes(HeadstockStyle.FENDER_TELE, dims)
        centerline = generate_centerline(neck_params)

        profile, fretboard, headstock, tuners, centerline, fret_positions, scale_out = _convert_output(
            profile, fretboard, headstock, tuners, centerline, fret_positions, dims.scale_length_in, params.units
        )

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
                "description": "Classic 50s specs: U-profile, 1-5/8 in nut",
            },
            {
                "name": "American Telecaster",
                "variant": "modern",
                "scale_length": 25.5,
                "nut_width": 1.6875,
                "num_frets": 22,
                "fretboard_radius": 9.5,
                "description": "Modern C-profile, 1-11/16 in nut",
            },
        ]
    }


# =============================================================================
# PRS ROUTES
# =============================================================================


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
        headstock = _generate_headstock_outline(HeadstockStyle.PRS, dims)
        tuners = _generate_tuner_holes(HeadstockStyle.PRS, dims)
        centerline = generate_centerline(neck_params)

        profile, fretboard, headstock, tuners, centerline, fret_positions, scale_out = _convert_output(
            profile, fretboard, headstock, tuners, centerline, fret_positions, dims.scale_length_in, params.units
        )

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
                "description": "PRS signature 25 in scale, Pattern neck",
            },
            {
                "name": "PRS McCarty 594",
                "scale_length": 24.594,
                "nut_width": 1.6875,
                "num_frets": 22,
                "fretboard_radius": 10.0,
                "headstock_angle": 10.0,
                "description": "Vintage-inspired shorter scale",
            },
        ]
    }
