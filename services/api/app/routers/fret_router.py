"""
Fret Design Router - Consolidated Fret Geometry and Calculations

Component router for all fret-related design calculations:
- Fret position computation (equal temperament)
- Fretboard outline and slot geometry
- Fan-fret (multi-scale) calculations
- Compound radius interpolation
- Staggered fret positions for alternative temperaments

Follows the component router pattern: neck_router, bridge_router, archtop_router, stratocaster_router.

CAM/G-code operations remain in cam_fret_slots_router and cam_fret_slots_export_router.
"""

from typing import List, Optional, Dict, Any
from math import pi
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from enum import Enum

# Import core fret calculation modules
from ..instrument_geometry.neck import (
    compute_fret_positions_mm,
    compute_compound_radius_at_fret,
    FretboardSpec,
)
from ..instrument_geometry.neck.fret_math import (
    compute_fan_fret_positions,
    validate_fan_fret_geometry,
    FAN_FRET_PRESETS,
)
from ..instrument_geometry.body import (
    compute_fretboard_outline,
    compute_fret_slot_lines,
)

# Import temperament calculations
from ..calculators.alternative_temperaments import (
    compute_staggered_fret_positions,
    TemperamentSystem,
    NOTE_NAMES,
    StaggeredFret as StaggeredFretData,
)

# Import LTB calculator for additional fret utilities
from ..ltb_calculators.luthier_calculator import LTBLuthierCalculator

router = APIRouter(prefix="/fret", tags=["Fret Design"])

# ============================================================================
# ENUMS
# ============================================================================

class TemperamentEnum(str, Enum):
    """Temperament systems for fret calculations."""
    EQUAL = "12-TET"
    JUST_MAJOR = "just_major"
    JUST_MINOR = "just_minor"
    PYTHAGOREAN = "pythagorean"
    MEANTONE = "meantone_1/4"

# ============================================================================
# REQUEST MODELS
# ============================================================================

class FretPositionRequest(BaseModel):
    """Request for single fret position calculation."""
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    fret_number: int = Field(..., ge=1, le=36, description="Fret number (1-36)")

class FretTableRequest(BaseModel):
    """Request for complete fret table generation."""
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    num_frets: int = Field(22, ge=1, le=36, description="Number of frets")
    compensation_mm: float = Field(0.0, ge=0, description="Bridge compensation in mm")

class FretboardOutlineRequest(BaseModel):
    """Request for fretboard outline calculation."""
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    nut_width_mm: float = Field(42.0, gt=0, description="Width at nut in mm")
    heel_width_mm: float = Field(56.0, gt=0, description="Width at heel/12th fret in mm")
    num_frets: int = Field(22, ge=1, le=36, description="Number of frets")
    extension_mm: float = Field(10.0, ge=0, description="Extension past last fret in mm")
    overhang_mm: float = Field(2.0, ge=0, description="Edge overhang on each side in mm")

class FretSlotsRequest(BaseModel):
    """Request for fret slot line calculation."""
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    nut_width_mm: float = Field(42.0, gt=0, description="Width at nut in mm")
    heel_width_mm: float = Field(56.0, gt=0, description="Width at heel in mm")
    num_frets: int = Field(22, ge=1, le=36, description="Number of frets")

class FanFretCalculateRequest(BaseModel):
    """Request for fan-fret (multi-scale) position calculation."""
    treble_scale_mm: float = Field(..., gt=0, description="Treble side scale length in mm")
    bass_scale_mm: float = Field(..., gt=0, description="Bass side scale length in mm")
    num_frets: int = Field(24, ge=1, le=36, description="Number of frets")
    nut_width_mm: float = Field(42.0, gt=0, description="Nut width in mm")
    heel_width_mm: float = Field(56.0, gt=0, description="Heel width in mm")
    perpendicular_fret: int = Field(7, ge=0, le=24, description="Fret that remains perpendicular")

class FanFretValidateRequest(BaseModel):
    """Request for fan-fret geometry validation."""
    treble_scale_mm: float = Field(..., gt=0, description="Treble side scale length")
    bass_scale_mm: float = Field(..., gt=0, description="Bass side scale length")
    num_frets: int = Field(24, ge=1, le=36, description="Number of frets")
    perpendicular_fret: int = Field(7, ge=0, description="Perpendicular fret number")

class CompoundRadiusRequest(BaseModel):
    """Request for compound radius at specific fret."""
    nut_radius_mm: float = Field(..., gt=0, description="Radius at nut in mm")
    heel_radius_mm: float = Field(..., gt=0, description="Radius at heel in mm")
    fret_number: int = Field(..., ge=0, description="Fret number to calculate radius at")
    total_frets: int = Field(22, ge=1, le=36, description="Total number of frets")

class StaggeredFretsRequest(BaseModel):
    """Request for staggered (angled) fret calculation."""
    scale_length_mm: float = Field(648.0, gt=0, description="Scale length in mm")
    fret_count: int = Field(22, ge=12, le=36, description="Number of frets")
    string_count: int = Field(6, ge=4, le=12, description="Number of strings")
    tuning_semitones: List[int] = Field(
        default=[0, 5, 10, 15, 19, 24],
        description="Open string tuning in semitones from lowest"
    )
    target_key: str = Field("C", description="Target key for optimization")
    temperament: TemperamentEnum = Field(TemperamentEnum.JUST_MAJOR, description="Temperament system")
    nut_width_mm: float = Field(42.0, gt=0, description="Nut width in mm")
    fret_width_mm: float = Field(2.4, gt=0, description="Fret wire width in mm")

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class FretPositionResponse(BaseModel):
    """Single fret position response."""
    fret_number: int
    distance_from_nut_mm: float
    spacing_from_previous_mm: float
    remaining_to_bridge_mm: float

class FretTableResponse(BaseModel):
    """Complete fret table response."""
    scale_length_mm: float
    num_frets: int
    compensation_mm: float
    frets: List[FretPositionResponse]
    spacings_mm: List[float]

class OutlinePoint(BaseModel):
    """2D point for outline geometry."""
    x: float
    y: float

class FretboardOutlineResponse(BaseModel):
    """Fretboard outline geometry response."""
    points: List[OutlinePoint]
    fretboard_length_mm: float
    nut_width_mm: float
    heel_width_mm: float

class FretSlot(BaseModel):
    """Single fret slot geometry."""
    fret_number: int
    distance_from_nut_mm: float
    left: OutlinePoint
    right: OutlinePoint
    slot_width_mm: float = 0.6

class FretSlotsResponse(BaseModel):
    """Fret slot positions response."""
    scale_length_mm: float
    num_frets: int
    slots: List[FretSlot]

class FanFretPoint(BaseModel):
    """Single fan-fret position data."""
    fret_number: int
    treble_pos_mm: float
    bass_pos_mm: float
    angle_rad: float
    angle_deg: float
    center_x: float
    center_y: float
    is_perpendicular: bool

class FanFretCalculateResponse(BaseModel):
    """Fan-fret calculation response."""
    treble_scale_mm: float
    bass_scale_mm: float
    perpendicular_fret: int
    num_frets: int
    fret_points: List[FanFretPoint]
    max_angle_deg: float

class FanFretValidateResponse(BaseModel):
    """Fan-fret validation response."""
    valid: bool
    message: str
    warnings: Optional[List[str]] = None

class CompoundRadiusResponse(BaseModel):
    """Compound radius calculation response."""
    fret_number: int
    radius_mm: float
    radius_inches: float
    nut_radius_mm: float
    heel_radius_mm: float

class StaggeredFretPosition(BaseModel):
    """Single string position within a staggered fret."""
    string_index: int
    x_mm: float
    y_mm: float

class StaggeredFret(BaseModel):
    """Single staggered fret with per-string positions."""
    fret_number: int
    string_positions: List[StaggeredFretPosition]
    endpoints: List[List[float]]

class StaggeredFretsResponse(BaseModel):
    """Staggered frets calculation response."""
    scale_length_mm: float
    target_key: str
    temperament: str
    string_count: int
    fret_count: int
    frets: List[StaggeredFret]

# ============================================================================
# ENDPOINTS: Basic Fret Calculations
# ============================================================================

@router.post("/position", response_model=FretPositionResponse)
async def calculate_fret_position(request: FretPositionRequest):
    """
    Calculate single fret position using 12-TET equal temperament.

    Returns distance from nut, spacing from previous fret, and remaining distance to bridge.
    Uses formula: position = scale_length * (1 - 2^(-fret/12))
    """
    calc = LTBLuthierCalculator()
    position = calc.fret_position(request.scale_length_mm, request.fret_number)
    spacing = calc.fret_spacing(request.scale_length_mm, request.fret_number)

    return FretPositionResponse(
        fret_number=request.fret_number,
        distance_from_nut_mm=round(position, 4),
        spacing_from_previous_mm=round(spacing, 4),
        remaining_to_bridge_mm=round(request.scale_length_mm - position, 4),
    )

@router.post("/table", response_model=FretTableResponse)
async def generate_fret_table(request: FretTableRequest):
    """
    Generate complete fret position table.

    Returns all fret positions with spacings for the specified scale length.
    Includes compensation offset for bridge placement reference.
    """
    positions = compute_fret_positions_mm(
        scale_length_mm=request.scale_length_mm,
        fret_count=request.num_frets,
    )

    # Calculate spacings
    spacings = [positions[0]]  # First fret spacing from nut
    for i in range(1, len(positions)):
        spacings.append(positions[i] - positions[i - 1])

    # Build fret responses
    frets = []
    for i, pos in enumerate(positions, start=1):
        prev_spacing = spacings[i - 1] if i <= len(spacings) else 0
        frets.append(FretPositionResponse(
            fret_number=i,
            distance_from_nut_mm=round(pos, 4),
            spacing_from_previous_mm=round(prev_spacing, 4),
            remaining_to_bridge_mm=round(request.scale_length_mm - pos, 4),
        ))

    return FretTableResponse(
        scale_length_mm=request.scale_length_mm,
        num_frets=request.num_frets,
        compensation_mm=request.compensation_mm,
        frets=frets,
        spacings_mm=[round(s, 4) for s in spacings],
    )

# ============================================================================
# ENDPOINTS: Fretboard Geometry
# ============================================================================

@router.post("/board/outline", response_model=FretboardOutlineResponse)
async def calculate_fretboard_outline(request: FretboardOutlineRequest):
    """
    Calculate fretboard outline as a tapered polygon.

    Returns corner points for a trapezoid that tapers from nut width to heel width.
    The fretboard extends from the nut to the last fret position plus extension.
    """
    outline = compute_fretboard_outline(
        nut_width_mm=request.nut_width_mm,
        heel_width_mm=request.heel_width_mm,
        scale_length_mm=request.scale_length_mm,
        fret_count=request.num_frets,
        extension_mm=request.extension_mm,
    )

    # Calculate fretboard length
    frets = compute_fret_positions_mm(request.scale_length_mm, request.num_frets)
    fretboard_length = frets[-1] + request.extension_mm if frets else 0

    return FretboardOutlineResponse(
        points=[OutlinePoint(x=round(p[0], 4), y=round(p[1], 4)) for p in outline],
        fretboard_length_mm=round(fretboard_length, 4),
        nut_width_mm=request.nut_width_mm,
        heel_width_mm=request.heel_width_mm,
    )

@router.post("/board/slots", response_model=FretSlotsResponse)
async def calculate_fret_slots(request: FretSlotsRequest):
    """
    Calculate fret slot endpoints for CNC machining.

    Returns left and right endpoints for each fret slot,
    accounting for fretboard taper from nut to heel.
    """
    spec = FretboardSpec(
        nut_width_mm=request.nut_width_mm,
        heel_width_mm=request.heel_width_mm,
        scale_length_mm=request.scale_length_mm,
        fret_count=request.num_frets,
    )

    slots_data = compute_fret_slot_lines(spec)
    fret_positions = compute_fret_positions_mm(request.scale_length_mm, request.num_frets)

    slots = []
    for i, slot_line in enumerate(slots_data):
        # Each slot_line is ((x1, y1), (x2, y2))
        bass_pt, treble_pt = slot_line
        dist = fret_positions[i] if i < len(fret_positions) else 0

        slots.append(FretSlot(
            fret_number=i + 1,
            distance_from_nut_mm=round(dist, 4),
            left=OutlinePoint(x=round(bass_pt[0], 4), y=round(bass_pt[1], 4)),
            right=OutlinePoint(x=round(treble_pt[0], 4), y=round(treble_pt[1], 4)),
        ))

    return FretSlotsResponse(
        scale_length_mm=request.scale_length_mm,
        num_frets=request.num_frets,
        slots=slots,
    )

# ============================================================================
# ENDPOINTS: Compound Radius
# ============================================================================

@router.post("/radius/compound", response_model=CompoundRadiusResponse)
async def calculate_compound_radius(request: CompoundRadiusRequest):
    """
    Calculate fretboard radius at a specific fret for compound radius necks.

    Interpolates between nut and heel radius based on fret position.
    Common compound profiles: 10"-16", 9.5"-14", 12"-16".
    """
    radius_mm = compute_compound_radius_at_fret(
        fret_index=request.fret_number,
        total_frets=request.total_frets,
        start_radius_mm=request.nut_radius_mm,
        end_radius_mm=request.heel_radius_mm,
    )

    return CompoundRadiusResponse(
        fret_number=request.fret_number,
        radius_mm=round(radius_mm, 4),
        radius_inches=round(radius_mm / 25.4, 4),
        nut_radius_mm=request.nut_radius_mm,
        heel_radius_mm=request.heel_radius_mm,
    )

@router.get("/radius/presets")
async def get_compound_radius_presets():
    """
    Get common compound radius presets.

    Returns popular fretboard radius combinations used by major manufacturers.
    """
    return {
        "presets": [
            {"name": "Fender Modern", "nut_inches": 9.5, "heel_inches": 14.0, "nut_mm": 241.3, "heel_mm": 355.6},
            {"name": "Gibson Compound", "nut_inches": 10.0, "heel_inches": 16.0, "nut_mm": 254.0, "heel_mm": 406.4},
            {"name": "PRS Pattern", "nut_inches": 10.0, "heel_inches": 11.0, "nut_mm": 254.0, "heel_mm": 279.4},
            {"name": "Ibanez SRTM", "nut_inches": 12.0, "heel_inches": 16.0, "nut_mm": 304.8, "heel_mm": 406.4},
            {"name": "Jackson Compound", "nut_inches": 12.0, "heel_inches": 16.0, "nut_mm": 304.8, "heel_mm": 406.4},
            {"name": "Warmoth Compound", "nut_inches": 10.0, "heel_inches": 16.0, "nut_mm": 254.0, "heel_mm": 406.4},
        ],
        "count": 6,
    }

# ============================================================================
# ENDPOINTS: Fan-Fret (Multi-Scale)
# ============================================================================

@router.post("/fan/calculate", response_model=FanFretCalculateResponse)
async def calculate_fan_fret(request: FanFretCalculateRequest):
    """
    Calculate fan-fret (multi-scale) fret positions.

    Returns position data for each fret including:
    - Treble and bass side positions
    - Slot angle in radians and degrees
    - Center point coordinates
    - Perpendicular fret marker

    Common configurations:
    - 7-string standard: treble=648mm (25.5"), bass=686mm (27"), perp=7
    - 8-string extended: treble=648mm, bass=711mm (28"), perp=8
    """
    fret_points = compute_fan_fret_positions(
        treble_scale_mm=request.treble_scale_mm,
        bass_scale_mm=request.bass_scale_mm,
        fret_count=request.num_frets,
        nut_width_mm=request.nut_width_mm,
        heel_width_mm=request.heel_width_mm,
        perpendicular_fret=request.perpendicular_fret,
        scale_length_reference_mm=request.treble_scale_mm,
    )

    response_points = []
    max_angle_deg = 0.0

    for fp in fret_points:
        angle_deg = fp.angle_rad * 180.0 / pi
        is_perp = abs(fp.angle_rad) < 0.001

        response_points.append(FanFretPoint(
            fret_number=fp.fret_number,
            treble_pos_mm=round(fp.treble_pos_mm, 4),
            bass_pos_mm=round(fp.bass_pos_mm, 4),
            angle_rad=round(fp.angle_rad, 6),
            angle_deg=round(angle_deg, 4),
            center_x=round(fp.center_x, 4),
            center_y=round(fp.center_y, 4),
            is_perpendicular=is_perp,
        ))

        max_angle_deg = max(max_angle_deg, abs(angle_deg))

    return FanFretCalculateResponse(
        treble_scale_mm=request.treble_scale_mm,
        bass_scale_mm=request.bass_scale_mm,
        perpendicular_fret=request.perpendicular_fret,
        num_frets=request.num_frets,
        fret_points=response_points,
        max_angle_deg=round(max_angle_deg, 4),
    )

@router.post("/fan/validate", response_model=FanFretValidateResponse)
async def validate_fan_fret(request: FanFretValidateRequest):
    """
    Validate fan-fret geometry parameters.

    Checks:
    - Bass scale >= treble scale
    - Scale lengths in reasonable range (500-900mm)
    - Perpendicular fret within valid range
    - Angle not too extreme for playability

    Returns validation status with detailed message.
    """
    result = validate_fan_fret_geometry(
        treble_scale_mm=request.treble_scale_mm,
        bass_scale_mm=request.bass_scale_mm,
        fret_count=request.num_frets,
        perpendicular_fret=request.perpendicular_fret,
    )

    return FanFretValidateResponse(
        valid=result["valid"],
        message=result["message"],
        warnings=result.get("warnings"),
    )

@router.get("/fan/presets")
async def get_fan_fret_presets():
    """
    Get predefined fan-fret configurations.

    Returns presets for common multi-scale instruments:
    - 7-string standard (25.5"-27")
    - 8-string extended (25.5"-28")
    - Baritone 6-string (26"-27")
    """
    return {
        "presets": FAN_FRET_PRESETS,
        "count": len(FAN_FRET_PRESETS),
    }

# ============================================================================
# ENDPOINTS: Staggered Frets (Alternative Temperaments)
# ============================================================================

@router.post("/staggered", response_model=StaggeredFretsResponse)
async def calculate_staggered_frets(request: StaggeredFretsRequest):
    """
    Compute staggered (angled) fret positions for key-optimized intonation.

    Staggered frets allow each string to have a different fret position,
    enabling pure intervals for a specific key while maintaining playability.

    This is the "Smart Guitar" concept - frets optimized for a single key
    that produce mathematically perfect intervals.

    Supported temperaments:
    - equal: Standard 12-TET
    - just_major: Pure major thirds and fifths
    - just_minor: Pure minor thirds and fifths
    - pythagorean: Pure fifths, wolf intervals elsewhere
    - meantone: Compromise between just and equal
    - well: Historical well-temperament
    """
    if request.target_key.upper() not in NOTE_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid key '{request.target_key}'. Use one of: {NOTE_NAMES}"
        )

    # Map enum to TemperamentSystem
    temperament_map = {
        TemperamentEnum.EQUAL: TemperamentSystem.EQUAL_12TET,
        TemperamentEnum.JUST_MAJOR: TemperamentSystem.JUST_MAJOR,
        TemperamentEnum.JUST_MINOR: TemperamentSystem.JUST_MINOR,
        TemperamentEnum.PYTHAGOREAN: TemperamentSystem.PYTHAGOREAN,
        TemperamentEnum.MEANTONE: TemperamentSystem.MEANTONE_QUARTER,
    }

    frets = compute_staggered_fret_positions(
        scale_length_mm=request.scale_length_mm,
        fret_count=request.fret_count,
        string_count=request.string_count,
        tuning_semitones=request.tuning_semitones,
        target_key=request.target_key,
        temperament=temperament_map[request.temperament],
        nut_width_mm=request.nut_width_mm,
        fret_width_mm=request.fret_width_mm,
    )

    fret_responses = []
    for f in frets:
        # string_positions is List[float] (distance from nut for each string)
        positions = [
            StaggeredFretPosition(string_index=i, x_mm=round(pos, 4), y_mm=0.0)
            for i, pos in enumerate(f.string_positions)
        ]
        fret_responses.append(StaggeredFret(
            fret_number=f.fret_number,
            string_positions=positions,
            endpoints=[[round(p, 4) for p in ep] for ep in f.endpoints],
        ))

    return StaggeredFretsResponse(
        scale_length_mm=request.scale_length_mm,
        target_key=request.target_key,
        temperament=request.temperament.value,
        string_count=request.string_count,
        fret_count=request.fret_count,
        frets=fret_responses,
    )

@router.get("/temperaments")
async def list_temperaments():
    """
    List available temperament systems for staggered fret calculation.

    Returns descriptions and use cases for each temperament type.
    """
    return {
        "temperaments": [
            {
                "id": "equal",
                "name": "Equal Temperament (12-TET)",
                "description": "Standard Western tuning. All semitones equal. Best for playing in any key.",
            },
            {
                "id": "just_major",
                "name": "Just Intonation (Major)",
                "description": "Pure major thirds (5:4) and perfect fifths (3:2). Best for major key music.",
            },
            {
                "id": "just_minor",
                "name": "Just Intonation (Minor)",
                "description": "Pure minor thirds (6:5) and perfect fifths. Best for minor key music.",
            },
            {
                "id": "pythagorean",
                "name": "Pythagorean",
                "description": "Pure fifths throughout. Very bright. Historical tuning for medieval music.",
            },
            {
                "id": "meantone",
                "name": "Quarter-Comma Meantone",
                "description": "Pure major thirds, slightly flat fifths. Renaissance/Baroque music.",
            },
            {
                "id": "well",
                "name": "Well Temperament",
                "description": "Each key has distinct character. Baroque keyboard music.",
            },
        ],
        "count": 6,
    }

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/scales/presets")
async def get_scale_length_presets():
    """
    Get common scale length presets.

    Returns scale lengths used by major guitar manufacturers.
    """
    return {
        "presets": [
            {"name": "Fender Standard", "inches": 25.5, "mm": 647.7, "instruments": ["Stratocaster", "Telecaster", "Jazzmaster"]},
            {"name": "Gibson Standard", "inches": 24.75, "mm": 628.65, "instruments": ["Les Paul", "SG", "ES-335"]},
            {"name": "PRS Standard", "inches": 25.0, "mm": 635.0, "instruments": ["Custom 24", "McCarty"]},
            {"name": "Rickenbacker", "inches": 24.0, "mm": 609.6, "instruments": ["330", "360"]},
            {"name": "Baritone Short", "inches": 27.0, "mm": 685.8, "instruments": ["Baritone guitars"]},
            {"name": "Baritone Long", "inches": 28.5, "mm": 723.9, "instruments": ["Extended range baritones"]},
            {"name": "Classical", "inches": 25.6, "mm": 650.0, "instruments": ["Classical guitar"]},
            {"name": "Short Scale Bass", "inches": 30.0, "mm": 762.0, "instruments": ["Hofner Violin Bass"]},
            {"name": "Standard Bass", "inches": 34.0, "mm": 863.6, "instruments": ["Precision Bass", "Jazz Bass"]},
            {"name": "Extra Long Bass", "inches": 35.0, "mm": 889.0, "instruments": ["5-string basses"]},
        ],
        "count": 10,
    }

