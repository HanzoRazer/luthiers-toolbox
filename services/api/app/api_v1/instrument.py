"""
Instrument Design API v1

Design calculations for guitar and bass construction:

1. GET  /instrument/scale-lengths - Common scale length reference
2. POST /instrument/neck-profile - Calculate neck profile dimensions
3. POST /instrument/body-geometry - Body outline calculations
4. GET  /instrument/wood-species - Wood properties database
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/instrument", tags=["Instrument Design"])


# =============================================================================
# SCHEMAS
# =============================================================================

class V1Response(BaseModel):
    """Standard v1 response wrapper."""
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    hint: Optional[str] = None


class NeckProfileRequest(BaseModel):
    """Request neck profile calculations."""
    scale_length_mm: float = Field(..., description="Scale length")
    nut_width_mm: float = Field(43.0, description="Width at nut")
    heel_width_mm: float = Field(56.0, description="Width at heel/body joint")
    fret_count: int = Field(22, description="Number of frets")
    neck_joint_fret: int = Field(16, description="Fret at body joint")
    profile_shape: str = Field("C", description="Profile shape: C, D, V, U, asymmetric")
    thickness_at_1st_mm: float = Field(20.0, description="Thickness at 1st fret")
    thickness_at_12th_mm: float = Field(22.0, description="Thickness at 12th fret")


class NeckProfileResponse(V1Response):
    """Neck profile dimensions."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{
            "fret_widths": [{"fret": 1, "width_mm": 43.5}],
            "profile_depths": [{"fret": 1, "depth_mm": 20.0}],
        }],
    )


class BodyGeometryRequest(BaseModel):
    """Request body geometry calculations."""
    body_style: str = Field("dreadnought", description="Style: dreadnought, om, parlor, classical, les_paul, strat")
    scale_length_mm: float = Field(648.0, description="Scale length for bridge placement")
    body_length_mm: Optional[float] = Field(None, description="Override body length")
    lower_bout_mm: Optional[float] = Field(None, description="Override lower bout width")
    upper_bout_mm: Optional[float] = Field(None, description="Override upper bout width")
    waist_mm: Optional[float] = Field(None, description="Override waist width")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/scale-lengths")
def list_scale_lengths() -> V1Response:
    """
    Reference list of common scale lengths.

    Scale length is measured from nut to saddle (12th fret is halfway).
    """
    scales = [
        # Guitars
        {
            "name": "Fender Standard",
            "mm": 648.0,
            "inches": 25.5,
            "category": "electric_guitar",
            "examples": ["Stratocaster", "Telecaster", "Most Fender models"],
        },
        {
            "name": "Gibson Standard",
            "mm": 628.65,
            "inches": 24.75,
            "category": "electric_guitar",
            "examples": ["Les Paul", "SG", "ES-335"],
        },
        {
            "name": "PRS Standard",
            "mm": 635.0,
            "inches": 25.0,
            "category": "electric_guitar",
            "examples": ["PRS Custom 24", "Most PRS models"],
        },
        {
            "name": "Classical Guitar",
            "mm": 650.0,
            "inches": 25.6,
            "category": "classical",
            "examples": ["Traditional nylon string"],
        },
        {
            "name": "Martin Dreadnought",
            "mm": 645.16,
            "inches": 25.4,
            "category": "acoustic",
            "examples": ["Martin D-28", "Most dreadnoughts"],
        },
        {
            "name": "Parlor Guitar",
            "mm": 609.6,
            "inches": 24.0,
            "category": "acoustic",
            "examples": ["Small body acoustics"],
        },
        # Basses
        {
            "name": "Fender Bass",
            "mm": 863.6,
            "inches": 34.0,
            "category": "bass",
            "examples": ["Precision Bass", "Jazz Bass"],
        },
        {
            "name": "Short Scale Bass",
            "mm": 762.0,
            "inches": 30.0,
            "category": "bass",
            "examples": ["Mustang Bass", "Hofner Violin Bass"],
        },
        {
            "name": "Medium Scale Bass",
            "mm": 812.8,
            "inches": 32.0,
            "category": "bass",
            "examples": ["Some Gibsons", "Danelectro"],
        },
        # Other
        {
            "name": "Baritone Guitar",
            "mm": 698.5,
            "inches": 27.5,
            "category": "baritone",
            "examples": ["Extended range guitars"],
        },
        {
            "name": "Mandolin",
            "mm": 355.6,
            "inches": 14.0,
            "category": "mandolin",
            "examples": ["Standard mandolin"],
        },
    ]

    return V1Response(
        ok=True,
        data={
            "scale_lengths": scales,
            "note": "Scale length affects tone (longer = more tension, brighter) and playability",
        },
    )


@router.post("/neck-profile", response_model=NeckProfileResponse)
def calculate_neck_profile(req: NeckProfileRequest) -> NeckProfileResponse:
    """
    Calculate neck taper and profile dimensions.

    Returns width and depth at each fret position for carving/CNC.
    """
    if req.scale_length_mm <= 0:
        return NeckProfileResponse(
            ok=False,
            error="Scale length must be positive",
        )

    if req.nut_width_mm >= req.heel_width_mm:
        return NeckProfileResponse(
            ok=False,
            error="Heel width must be greater than nut width",
            hint="Typical taper: 43mm nut → 56mm heel",
        )

    # Calculate taper
    taper_per_fret = (req.heel_width_mm - req.nut_width_mm) / req.neck_joint_fret

    # Calculate fret positions using 12-TET
    fret_positions = []
    for n in range(req.fret_count + 1):  # Include nut (fret 0)
        pos = req.scale_length_mm * (1 - 2 ** (-n / 12)) if n > 0 else 0
        fret_positions.append(pos)

    # Calculate widths and depths
    fret_widths = []
    profile_depths = []

    for n in range(req.fret_count + 1):
        # Width tapers linearly to heel, then stays constant
        if n <= req.neck_joint_fret:
            width = req.nut_width_mm + (n * taper_per_fret)
        else:
            width = req.heel_width_mm

        fret_widths.append({
            "fret": n,
            "position_mm": round(fret_positions[n], 2),
            "width_mm": round(width, 2),
        })

        # Depth interpolation (linear from 1st to 12th)
        if n <= 12:
            t = n / 12
            depth = req.thickness_at_1st_mm + t * (req.thickness_at_12th_mm - req.thickness_at_1st_mm)
        else:
            # Beyond 12th, continue slight increase
            depth = req.thickness_at_12th_mm + (n - 12) * 0.1

        profile_depths.append({
            "fret": n,
            "depth_mm": round(depth, 2),
            "profile_shape": req.profile_shape,
        })

    return NeckProfileResponse(
        ok=True,
        data={
            "scale_length_mm": req.scale_length_mm,
            "taper_per_fret_mm": round(taper_per_fret, 3),
            "fret_widths": fret_widths,
            "profile_depths": profile_depths,
            "profile_shape": req.profile_shape,
            "neck_joint_fret": req.neck_joint_fret,
        },
    )


@router.post("/body-geometry")
def calculate_body_geometry(req: BodyGeometryRequest) -> V1Response:
    """
    Calculate body outline dimensions for a given style.

    Returns key measurements for body template creation.
    """
    # Standard dimensions by style
    styles = {
        "dreadnought": {
            "body_length_mm": 508,
            "lower_bout_mm": 396,
            "upper_bout_mm": 292,
            "waist_mm": 279,
            "body_depth_mm": 100,
        },
        "om": {
            "body_length_mm": 489,
            "lower_bout_mm": 381,
            "upper_bout_mm": 273,
            "waist_mm": 241,
            "body_depth_mm": 100,
        },
        "parlor": {
            "body_length_mm": 457,
            "lower_bout_mm": 343,
            "upper_bout_mm": 241,
            "waist_mm": 216,
            "body_depth_mm": 95,
        },
        "classical": {
            "body_length_mm": 489,
            "lower_bout_mm": 370,
            "upper_bout_mm": 280,
            "waist_mm": 241,
            "body_depth_mm": 95,
        },
        "les_paul": {
            "body_length_mm": 445,
            "lower_bout_mm": 330,
            "upper_bout_mm": 270,
            "waist_mm": 305,  # Minimal waist
            "body_depth_mm": 45,
        },
        "strat": {
            "body_length_mm": 400,
            "lower_bout_mm": 318,
            "upper_bout_mm": 267,
            "waist_mm": 254,
            "body_depth_mm": 45,
        },
    }

    if req.body_style not in styles:
        return V1Response(
            ok=False,
            error=f"Unknown body style: {req.body_style}",
            hint=f"Available: {', '.join(styles.keys())}",
        )

    dims = styles[req.body_style].copy()

    # Apply overrides
    if req.body_length_mm:
        dims["body_length_mm"] = req.body_length_mm
    if req.lower_bout_mm:
        dims["lower_bout_mm"] = req.lower_bout_mm
    if req.upper_bout_mm:
        dims["upper_bout_mm"] = req.upper_bout_mm
    if req.waist_mm:
        dims["waist_mm"] = req.waist_mm

    # Calculate bridge position from scale length
    # Bridge is at scale_length from nut, nut is at neck/body joint
    # Typical neck length to body joint is ~350-380mm for guitars
    neck_to_body = 365  # Approximate
    bridge_from_body_top = req.scale_length_mm - neck_to_body

    return V1Response(
        ok=True,
        data={
            "style": req.body_style,
            "dimensions": dims,
            "bridge_position": {
                "from_body_top_mm": round(bridge_from_body_top, 1),
                "from_lower_bout_mm": round(dims["body_length_mm"] - bridge_from_body_top, 1),
            },
            "scale_length_mm": req.scale_length_mm,
        },
    )


@router.get("/wood-species")
def list_wood_species() -> V1Response:
    """
    Wood properties database for instrument building.

    Includes acoustic properties and machining recommendations.
    """
    woods = [
        {
            "name": "Sitka Spruce",
            "category": "top",
            "density_kg_m3": 400,
            "hardness": "soft",
            "acoustic_properties": "Bright, articulate, good dynamic range",
            "machining": {"feed_mult": 1.0, "spindle_mult": 1.0},
        },
        {
            "name": "Western Red Cedar",
            "category": "top",
            "density_kg_m3": 350,
            "hardness": "soft",
            "acoustic_properties": "Warm, responsive, quick to open up",
            "machining": {"feed_mult": 1.1, "spindle_mult": 0.9},
        },
        {
            "name": "Indian Rosewood",
            "category": "back_sides",
            "density_kg_m3": 850,
            "hardness": "hard",
            "acoustic_properties": "Rich overtones, strong bass",
            "machining": {"feed_mult": 0.7, "spindle_mult": 1.2},
        },
        {
            "name": "Mahogany",
            "category": "back_sides",
            "density_kg_m3": 550,
            "hardness": "medium",
            "acoustic_properties": "Warm, focused midrange",
            "machining": {"feed_mult": 0.9, "spindle_mult": 1.0},
        },
        {
            "name": "Maple",
            "category": "back_sides",
            "density_kg_m3": 700,
            "hardness": "hard",
            "acoustic_properties": "Bright, reflective, clear",
            "machining": {"feed_mult": 0.8, "spindle_mult": 1.1},
        },
        {
            "name": "Ebony",
            "category": "fretboard",
            "density_kg_m3": 1100,
            "hardness": "very_hard",
            "acoustic_properties": "Bright attack, sustain",
            "machining": {"feed_mult": 0.5, "spindle_mult": 1.3},
        },
        {
            "name": "Rosewood (Fretboard)",
            "category": "fretboard",
            "density_kg_m3": 850,
            "hardness": "hard",
            "acoustic_properties": "Warm, slightly compressed",
            "machining": {"feed_mult": 0.7, "spindle_mult": 1.2},
        },
    ]

    return V1Response(
        ok=True,
        data={
            "woods": woods,
            "categories": ["top", "back_sides", "neck", "fretboard", "bridge"],
            "note": "Machining multipliers are relative to baseline softwood settings",
        },
    )
