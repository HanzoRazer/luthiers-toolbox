"""
Neck Generator Router - Les Paul Style Neck with DXF Export
Generates neck profiles, fretboard geometry, and fret slot positions
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import io

# Import canonical fret math - NO inline math in routers (Fortran Rule)
from ..instrument_geometry.neck.fret_math import compute_fret_positions_mm

try:
    import ezdxf
    from ezdxf import units as dxf_units
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


router = APIRouter(prefix="/neck", tags=["neck"])


# ============================================================================
# MODELS
# ============================================================================

class Point2D(BaseModel):
    x: float
    y: float


class NeckParameters(BaseModel):
    """Les Paul neck generation parameters"""
    # Blank dimensions (inches)
    blank_length: float = Field(28.0, description="Blank length (in)")
    blank_width: float = Field(3.5, description="Blank width (in)")
    blank_thickness: float = Field(1.0, description="Blank thickness (in)")
    
    # Scale and dimensions (inches)
    scale_length: float = Field(24.75, description="Scale length (in)")
    nut_width: float = Field(1.695, description="Nut width (in)")
    heel_width: float = Field(2.25, description="Heel width (in)")
    neck_length: float = Field(17.0, description="Neck length from nut to heel (in)")
    neck_angle: float = Field(4.0, description="Neck angle (degrees)")
    
    # Fretboard (inches)
    fretboard_radius: float = Field(12.0, description="Fretboard radius (in)")
    fretboard_offset: float = Field(0.0, description="Fretboard offset from centerline (in)")
    include_fretboard: bool = Field(True, description="Include fretboard geometry")
    num_frets: int = Field(22, description="Number of frets")
    
    # Profile (C-shape) (inches)
    thickness_1st_fret: float = Field(0.82, description="Thickness at 1st fret (in)")
    thickness_12th_fret: float = Field(0.92, description="Thickness at 12th fret (in)")
    radius_at_1st: float = Field(0.85, description="Profile radius at 1st fret (in)")
    radius_at_12th: float = Field(0.90, description="Profile radius at 12th fret (in)")
    
    # Headstock (inches)
    headstock_angle: float = Field(14.0, description="Headstock angle (degrees)")
    headstock_length: float = Field(7.0, description="Headstock length (in)")
    headstock_thickness: float = Field(0.625, description="Headstock thickness (in)")
    tuner_layout: float = Field(2.5, description="Tuner spacing (in)")
    tuner_diameter: float = Field(0.375, description="Tuner hole diameter (in)")
    
    # Options
    alignment_pin_holes: bool = Field(False, description="Add alignment pin holes")
    units: Literal["mm", "in"] = Field("in", description="Output units")


class NeckGeometryOut(BaseModel):
    """Generated neck geometry"""
    profile_points: List[Point2D]
    fretboard_points: Optional[List[Point2D]] = None
    fret_positions: List[float]  # Distance from nut
    headstock_points: List[Point2D]
    tuner_holes: List[Point2D]
    centerline: List[Point2D]
    units: str
    scale_length: float


# ============================================================================
# FRET CALCULATIONS - Delegated to fret_math.py (Fortran Rule)
# ============================================================================

def calculate_fret_positions(scale_length_in: float, num_frets: int = 22) -> List[float]:
    """
    Calculate fret positions using equal temperament formula.
    Returns distance from nut to each fret in inches.

    Delegates to canonical compute_fret_positions_mm() from fret_math.py.
    """
    # Convert inches to mm, call canonical function, convert back
    scale_length_mm = scale_length_in * 25.4
    positions_mm = compute_fret_positions_mm(scale_length_mm, num_frets)
    return [pos / 25.4 for pos in positions_mm]


# ============================================================================
# NECK GEOMETRY GENERATION
# ============================================================================

def generate_neck_profile(params: NeckParameters) -> List[Point2D]:
    """
    Generate neck profile outline (side view).
    
    Simplified C-profile with linear taper from nut to heel.
    """
    profile = []
    
    # Nut end (0, 0)
    profile.append(Point2D(x=0.0, y=0.0))
    
    # Neck length at bottom
    profile.append(Point2D(x=params.neck_length, y=0.0))
    
    # Heel width
    profile.append(Point2D(x=params.neck_length, y=params.heel_width / 2))
    
    # Nut width
    profile.append(Point2D(x=0.0, y=params.nut_width / 2))
    
    # Close path
    profile.append(Point2D(x=0.0, y=0.0))
    
    return profile


def generate_fretboard_outline(params: NeckParameters) -> List[Point2D]:
    """
    Generate fretboard outline (top view).
    
    Rectangle with width taper from nut to neck join.
    """
    fretboard = []
    
    # Fretboard typically extends ~2" past neck join on Les Paul
    fretboard_length = params.neck_length + 2.0
    
    # Width at nut
    nut_w = params.nut_width
    # Width at body (slightly wider)
    body_w = params.heel_width * 0.95
    
    # Rectangle outline
    fretboard.append(Point2D(x=0.0, y=-nut_w / 2))
    fretboard.append(Point2D(x=fretboard_length, y=-body_w / 2))
    fretboard.append(Point2D(x=fretboard_length, y=body_w / 2))
    fretboard.append(Point2D(x=0.0, y=nut_w / 2))
    fretboard.append(Point2D(x=0.0, y=-nut_w / 2))
    
    return fretboard


def generate_headstock_outline(params: NeckParameters) -> List[Point2D]:
    """
    Generate headstock outline (Gibson-style angled).
    """
    headstock = []
    
    # Simplified Les Paul headstock shape
    width = params.blank_width
    length = params.headstock_length
    
    # Starting at nut (0, 0), extends backward
    headstock.append(Point2D(x=0.0, y=-width / 2))
    headstock.append(Point2D(x=-length, y=-width / 2))
    headstock.append(Point2D(x=-length, y=width / 2))
    headstock.append(Point2D(x=0.0, y=width / 2))
    headstock.append(Point2D(x=0.0, y=-width / 2))
    
    return headstock


def generate_tuner_holes(params: NeckParameters) -> List[Point2D]:
    """
    Generate tuner hole positions (3+3 layout).
    """
    holes = []
    
    # 3+3 layout: 3 on treble side, 3 on bass side
    spacing = params.tuner_layout
    x_start = -params.headstock_length + 1.5  # 1.5" from headstock end
    
    # Treble side (top 3)
    for i in range(3):
        holes.append(Point2D(
            x=x_start,
            y=(params.blank_width / 4) + (i * spacing / 3)
        ))
    
    # Bass side (bottom 3)
    for i in range(3):
        holes.append(Point2D(
            x=x_start,
            y=-(params.blank_width / 4) - (i * spacing / 3)
        ))
    
    return holes


def generate_centerline(params: NeckParameters) -> List[Point2D]:
    """Generate centerline reference."""
    return [
        Point2D(x=-params.headstock_length, y=0.0),
        Point2D(x=params.neck_length + 3.0, y=0.0)
    ]


# ============================================================================
# UNIT CONVERSION
# ============================================================================

def convert_point(point: Point2D, from_units: str, to_units: str) -> Point2D:
    """Convert point between inches and millimeters."""
    if from_units == to_units:
        return point
    
    if from_units == "in" and to_units == "mm":
        factor = 25.4
    elif from_units == "mm" and to_units == "in":
        factor = 1.0 / 25.4
    else:
        return point
    
    return Point2D(x=point.x * factor, y=point.y * factor)


def convert_points(points: List[Point2D], from_units: str, to_units: str) -> List[Point2D]:
    """Convert list of points."""
    return [convert_point(p, from_units, to_units) for p in points]


def convert_value(value: float, from_units: str, to_units: str) -> float:
    """Convert scalar value."""
    if from_units == to_units:
        return value
    
    if from_units == "in" and to_units == "mm":
        return value * 25.4
    elif from_units == "mm" and to_units == "in":
        return value / 25.4
    else:
        return value


# ============================================================================
# DXF EXPORT
# ============================================================================

def export_neck_dxf(params: NeckParameters, geometry: NeckGeometryOut) -> bytes:
    """
    Export neck geometry to DXF R12 format.
    
    Layers:
    - NECK_PROFILE: Side view profile
    - FRETBOARD: Top view fretboard outline
    - FRET_SLOTS: Fret slot positions
    - HEADSTOCK: Headstock outline
    - TUNER_HOLES: Tuner hole positions
    - CENTERLINE: Reference line
    """
    if not EZDXF_AVAILABLE:
        raise HTTPException(500, detail="ezdxf library not installed")
    
    # Create DXF document (R12 format for maximum compatibility)
    doc = ezdxf.new('R12', setup=True)
    # Note: R12 format doesn't support doc.units attribute
    msp = doc.modelspace()
    
    # Layer definitions with colors
    layers = {
        'NECK_PROFILE': 1,      # Red
        'FRETBOARD': 2,         # Yellow
        'FRET_SLOTS': 3,        # Green
        'HEADSTOCK': 4,         # Cyan
        'TUNER_HOLES': 5,       # Blue
        'CENTERLINE': 8         # Gray
    }
    
    for layer_name, color in layers.items():
        doc.layers.new(name=layer_name, dxfattribs={'color': color})
    
    # Add neck profile (side view)
    profile_pts = [(p.x, p.y) for p in geometry.profile_points]
    if len(profile_pts) >= 2:
        # R12 uses POLYLINE, not LWPOLYLINE
        msp.add_polyline2d(
            profile_pts,
            dxfattribs={'layer': 'NECK_PROFILE'}
        )
    
    # Add fretboard outline (top view)
    if geometry.fretboard_points:
        fretboard_pts = [(p.x, p.y) for p in geometry.fretboard_points]
        if len(fretboard_pts) >= 2:
            msp.add_polyline2d(
                fretboard_pts,
                dxfattribs={'layer': 'FRETBOARD'}
            )
    
    # Add fret slots (lines across fretboard)
    if geometry.fretboard_points:
        fb_width = params.nut_width if params.units == "in" else params.nut_width * 25.4
        for fret_pos in geometry.fret_positions:
            msp.add_line(
                (fret_pos, -fb_width / 2),
                (fret_pos, fb_width / 2),
                dxfattribs={'layer': 'FRET_SLOTS'}
            )
    
    # Add headstock outline
    headstock_pts = [(p.x, p.y) for p in geometry.headstock_points]
    if len(headstock_pts) >= 2:
        msp.add_polyline2d(
            headstock_pts,
            dxfattribs={'layer': 'HEADSTOCK'}
        )
    
    # Add tuner holes (circles)
    tuner_radius = (params.tuner_diameter / 2) if params.units == "in" else (params.tuner_diameter * 25.4 / 2)
    for hole in geometry.tuner_holes:
        msp.add_circle(
            (hole.x, hole.y),
            radius=tuner_radius,
            dxfattribs={'layer': 'TUNER_HOLES'}
        )
    
    # Add centerline
    centerline_pts = [(p.x, p.y) for p in geometry.centerline]
    if len(centerline_pts) >= 2:
        msp.add_line(
            centerline_pts[0],
            centerline_pts[1],
            dxfattribs={'layer': 'CENTERLINE'}
        )
    
    # Add metadata text
    msp.add_text(
        f"Les Paul Neck - Scale: {geometry.scale_length:.3f}{geometry.units}",
        dxfattribs={
            'layer': 'CENTERLINE',
            'height': 0.25 if params.units == "in" else 6.0,
            'insert': (0, -3 if params.units == "in" else -75)
        }
    )
    
    # Write to bytes
    stream = io.StringIO()
    doc.write(stream, fmt='asc')  # ASCII format for R12
    stream.seek(0)
    dxf_content = stream.getvalue()
    return dxf_content.encode('utf-8')  # Convert to bytes


# ============================================================================
# API ENDPOINTS
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
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
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
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
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
