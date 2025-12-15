# services/api/app/calculators/inlay_calc.py

"""
Inlay calculator for the Luthier's ToolBox.

This module provides pattern generation for decorative inlays including:
- Fretboard position markers (dots, diamonds, blocks, custom)
- Headstock inlays (logo, decorative patterns)
- Purfling patterns (herringbone, rope, checkerboard)

Unlike bracing_calc and rosette_calc which wrap legacy modules,
this is a new calculator with pattern-first design.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

# Note: Default scale length below uses hardcoded 647.7mm (Fender 25.5")
# For production use, call get_scale_from_registry() helper to get registry data
# Registry provides: fender_25_5 (647.7mm), gibson_24_75 (628.65mm), prs_25 (635mm), etc.


class InlayPatternType(str, Enum):
    """Types of inlay patterns available."""
    DOT = "dot"
    DIAMOND = "diamond"
    BLOCK = "block"
    PARALLELOGRAM = "parallelogram"
    SPLIT_BLOCK = "split_block"
    CROWN = "crown"
    SNOWFLAKE = "snowflake"
    CUSTOM = "custom"


class FretMarkerStyle(str, Enum):
    """Standard fret marker position styles."""
    STANDARD = "standard"        # 3,5,7,9,12,15,17,19,21,24
    CLASSICAL = "classical"      # 5,7,9,12
    VINTAGE_DOT = "vintage_dot"  # 3,5,7,9,12,15,17,19,21
    BIRDS = "birds"              # PRS-style at each position
    BLOCKS = "blocks"            # Gibson-style blocks
    TRAPEZOIDS = "trapezoids"    # Gibson ES-style


class InlayShape(BaseModel):
    """
    A single inlay shape with position and geometry.
    
    All dimensions in mm. Origin is typically at fret center or 
    soundhole center depending on context.
    """
    pattern_type: InlayPatternType = Field(description="Shape type")
    x_mm: float = Field(description="X position from reference origin")
    y_mm: float = Field(description="Y position from reference origin")
    width_mm: float = Field(description="Shape width")
    height_mm: float = Field(description="Shape height (for non-circular)")
    rotation_deg: float = Field(default=0.0, description="Rotation in degrees")
    depth_mm: float = Field(default=1.5, description="Pocket routing depth")
    
    # For custom shapes
    vertices: Optional[List[Tuple[float, float]]] = Field(
        default=None,
        description="Custom shape vertices as (x, y) tuples relative to position"
    )


class InlayCalcInput(BaseModel):
    """Input for inlay pattern generation."""
    
    pattern_type: InlayPatternType = Field(
        default=InlayPatternType.DOT,
        description="Type of inlay shape"
    )
    
    # For fretboard markers
    fret_positions: List[int] = Field(
        default_factory=lambda: [3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
        description="Fret numbers to place markers"
    )
    double_at_12: bool = Field(
        default=True,
        description="Use double markers at 12th fret (and 24th)"
    )
    
    # Dimensions
    marker_diameter_mm: float = Field(
        default=6.0,
        ge=2.0,
        le=20.0,
        description="Dot diameter or diamond width"
    )
    block_width_mm: float = Field(
        default=40.0,
        description="Block inlay width (for block/parallelogram types)"
    )
    block_height_mm: float = Field(
        default=8.0,
        description="Block inlay height"
    )
    
    # Fretboard geometry (for position calculation)
    scale_length_mm: float = Field(
        default=648.0,  # 25.5" = 647.7mm
        description="Guitar scale length in mm"
    )
    nut_width_mm: float = Field(
        default=43.0,
        description="Width at nut for side dot positioning"
    )
    fret_12_width_mm: float = Field(
        default=52.0,
        description="Width at 12th fret for position interpolation"
    )
    
    # Pocket depth
    pocket_depth_mm: float = Field(
        default=1.5,
        ge=0.5,
        le=5.0,
        description="Routing depth for inlay pocket"
    )
    
    # Center line markers only or include side dots
    include_side_dots: bool = Field(
        default=False,
        description="Generate side dot positions as well"
    )
    side_dot_diameter_mm: float = Field(
        default=2.0,
        description="Side dot diameter (typically smaller)"
    )


class InlayCalcResult(BaseModel):
    """Result of inlay pattern calculation."""
    
    pattern_type: InlayPatternType
    shapes: List[InlayShape] = Field(description="Generated inlay shapes")
    total_shapes: int = Field(description="Total number of shapes")
    
    # Bounds for DXF export
    bounds_mm: Dict[str, float] = Field(
        description="Bounding box: min_x, max_x, min_y, max_y"
    )
    
    # CAM metadata
    pocket_depth_mm: float
    toolpath_notes: str = Field(default="")


def fret_position_mm(fret_number: int, scale_length_mm: float) -> float:
    """
    Calculate distance from nut to fret using 12-TET formula.
    
    Position = scale_length * (1 - 2^(-fret/12))
    """
    if fret_number <= 0:
        return 0.0
    return scale_length_mm * (1.0 - pow(2, -fret_number / 12.0))


def fret_midpoint_mm(fret_number: int, scale_length_mm: float) -> float:
    """
    Calculate X position at midpoint between fret and previous fret.
    This is where inlays are typically placed.
    """
    if fret_number <= 1:
        # Midpoint between nut (0) and fret 1
        return fret_position_mm(1, scale_length_mm) / 2.0
    
    pos_before = fret_position_mm(fret_number - 1, scale_length_mm)
    pos_at = fret_position_mm(fret_number, scale_length_mm)
    return (pos_before + pos_at) / 2.0


def interpolate_width(x_mm: float, scale_length_mm: float, 
                      nut_width: float, fret_12_width: float) -> float:
    """Interpolate fretboard width at position x from nut."""
    # Linear interpolation based on distance
    fret_12_pos = fret_position_mm(12, scale_length_mm)
    if x_mm <= 0:
        return nut_width
    if x_mm >= fret_12_pos:
        return fret_12_width
    
    t = x_mm / fret_12_pos
    return nut_width + t * (fret_12_width - nut_width)


def generate_dot_shape(x: float, y: float, diameter: float, depth: float) -> InlayShape:
    """Generate a circular dot inlay shape."""
    return InlayShape(
        pattern_type=InlayPatternType.DOT,
        x_mm=x,
        y_mm=y,
        width_mm=diameter,
        height_mm=diameter,
        depth_mm=depth,
    )


def generate_diamond_shape(x: float, y: float, width: float, 
                           height: float, depth: float) -> InlayShape:
    """Generate a diamond (rotated square) inlay shape."""
    half_w = width / 2.0
    half_h = height / 2.0
    return InlayShape(
        pattern_type=InlayPatternType.DIAMOND,
        x_mm=x,
        y_mm=y,
        width_mm=width,
        height_mm=height,
        depth_mm=depth,
        vertices=[
            (0, half_h),      # top
            (half_w, 0),      # right
            (0, -half_h),     # bottom
            (-half_w, 0),     # left
        ],
    )


def generate_block_shape(x: float, y: float, width: float, 
                         height: float, depth: float) -> InlayShape:
    """Generate a rectangular block inlay shape."""
    half_w = width / 2.0
    half_h = height / 2.0
    return InlayShape(
        pattern_type=InlayPatternType.BLOCK,
        x_mm=x,
        y_mm=y,
        width_mm=width,
        height_mm=height,
        depth_mm=depth,
        vertices=[
            (-half_w, half_h),   # top-left
            (half_w, half_h),    # top-right
            (half_w, -half_h),   # bottom-right
            (-half_w, -half_h),  # bottom-left
        ],
    )


def generate_parallelogram_shape(x: float, y: float, width: float,
                                  height: float, skew_deg: float, 
                                  depth: float) -> InlayShape:
    """Generate a parallelogram (Gibson trapezoid-style) inlay shape."""
    half_w = width / 2.0
    half_h = height / 2.0
    skew = half_h * math.tan(math.radians(skew_deg))
    
    return InlayShape(
        pattern_type=InlayPatternType.PARALLELOGRAM,
        x_mm=x,
        y_mm=y,
        width_mm=width,
        height_mm=height,
        depth_mm=depth,
        vertices=[
            (-half_w + skew, half_h),   # top-left
            (half_w + skew, half_h),    # top-right
            (half_w - skew, -half_h),   # bottom-right
            (-half_w - skew, -half_h),  # bottom-left
        ],
    )


def calculate_fretboard_inlays(input_data: InlayCalcInput) -> InlayCalcResult:
    """
    Calculate fretboard inlay positions and shapes.
    
    Args:
        input_data: InlayCalcInput with pattern and dimension specs
        
    Returns:
        InlayCalcResult with positioned shapes
    """
    shapes: List[InlayShape] = []
    
    for fret in input_data.fret_positions:
        x = fret_midpoint_mm(fret, input_data.scale_length_mm)
        y = 0.0  # Center line
        
        # Check for double markers at 12 and 24
        is_double = input_data.double_at_12 and fret in (12, 24)
        
        if is_double:
            # Offset markers above and below center
            offset = input_data.marker_diameter_mm * 1.5
            y_positions = [offset, -offset]
        else:
            y_positions = [0.0]
        
        for y_pos in y_positions:
            if input_data.pattern_type == InlayPatternType.DOT:
                shape = generate_dot_shape(
                    x, y_pos, 
                    input_data.marker_diameter_mm, 
                    input_data.pocket_depth_mm
                )
            elif input_data.pattern_type == InlayPatternType.DIAMOND:
                shape = generate_diamond_shape(
                    x, y_pos,
                    input_data.marker_diameter_mm,
                    input_data.marker_diameter_mm * 1.2,  # Slightly taller
                    input_data.pocket_depth_mm
                )
            elif input_data.pattern_type == InlayPatternType.BLOCK:
                shape = generate_block_shape(
                    x, y_pos,
                    input_data.block_width_mm,
                    input_data.block_height_mm,
                    input_data.pocket_depth_mm
                )
            elif input_data.pattern_type == InlayPatternType.PARALLELOGRAM:
                shape = generate_parallelogram_shape(
                    x, y_pos,
                    input_data.block_width_mm,
                    input_data.block_height_mm,
                    15.0,  # Skew angle
                    input_data.pocket_depth_mm
                )
            else:
                # Default to dot
                shape = generate_dot_shape(
                    x, y_pos,
                    input_data.marker_diameter_mm,
                    input_data.pocket_depth_mm
                )
            
            shapes.append(shape)
    
    # Add side dots if requested
    if input_data.include_side_dots:
        for fret in input_data.fret_positions:
            x = fret_midpoint_mm(fret, input_data.scale_length_mm)
            fb_width = interpolate_width(
                x, input_data.scale_length_mm,
                input_data.nut_width_mm, input_data.fret_12_width_mm
            )
            # Side dots at edge of fretboard
            y_side = fb_width / 2.0 + input_data.side_dot_diameter_mm
            
            shapes.append(generate_dot_shape(
                x, y_side,
                input_data.side_dot_diameter_mm,
                input_data.pocket_depth_mm
            ))
    
    # Calculate bounds
    if shapes:
        min_x = min(s.x_mm - s.width_mm / 2 for s in shapes)
        max_x = max(s.x_mm + s.width_mm / 2 for s in shapes)
        min_y = min(s.y_mm - s.height_mm / 2 for s in shapes)
        max_y = max(s.y_mm + s.height_mm / 2 for s in shapes)
    else:
        min_x = max_x = min_y = max_y = 0.0
    
    return InlayCalcResult(
        pattern_type=input_data.pattern_type,
        shapes=shapes,
        total_shapes=len(shapes),
        bounds_mm={
            "min_x": round(min_x, 3),
            "max_x": round(max_x, 3),
            "min_y": round(min_y, 3),
            "max_y": round(max_y, 3),
        },
        pocket_depth_mm=input_data.pocket_depth_mm,
        toolpath_notes=f"{len(shapes)} {input_data.pattern_type.value} inlays at {input_data.pocket_depth_mm}mm depth"
    )


def generate_inlay_dxf_string(
    result: InlayCalcResult,
    dxf_version: str = "R12",
) -> str:
    """
    Generate DXF string for inlay shapes.
    
    Args:
        result: InlayCalcResult from calculate_fretboard_inlays()
        dxf_version: Target DXF version (R12 default)
        
    Returns:
        DXF string content
    """
    # Import dxf_compat for version-aware generation
    try:
        from ..util.dxf_compat import create_document, add_polyline, validate_version
    except ImportError:
        # Fallback to basic R12 generation
        return _generate_basic_r12_dxf(result)
    
    version = validate_version(dxf_version)
    doc = create_document(version)
    msp = doc.modelspace()
    
    # Create layers
    doc.layers.add("INLAY_OUTLINE", color=5)  # Blue
    doc.layers.add("INLAY_CENTER", color=1)   # Red
    
    for shape in result.shapes:
        if shape.pattern_type == InlayPatternType.DOT:
            # Circle for dots
            msp.add_circle(
                center=(shape.x_mm, shape.y_mm),
                radius=shape.width_mm / 2.0,
                dxfattribs={"layer": "INLAY_OUTLINE"}
            )
            # Center mark
            msp.add_point(
                (shape.x_mm, shape.y_mm),
                dxfattribs={"layer": "INLAY_CENTER"}
            )
        elif shape.vertices:
            # Polygon for other shapes
            pts = [(shape.x_mm + v[0], shape.y_mm + v[1]) for v in shape.vertices]
            add_polyline(msp, pts, layer="INLAY_OUTLINE", closed=True, version=version)
    
    # Write to string
    from io import StringIO
    stream = StringIO()
    doc.write(stream)
    return stream.getvalue()
    return stream.getvalue()


def _generate_basic_r12_dxf(result: InlayCalcResult) -> str:
    """Fallback basic R12 DXF generation without dxf_compat."""
    import ezdxf
    
    doc = ezdxf.new("R12")
    msp = doc.modelspace()
    
    doc.layers.add("INLAY_OUTLINE", color=5)
    doc.layers.add("INLAY_CENTER", color=1)
    
    for shape in result.shapes:
        if shape.pattern_type == InlayPatternType.DOT:
            msp.add_circle(
                center=(shape.x_mm, shape.y_mm),
                radius=shape.width_mm / 2.0,
                dxfattribs={"layer": "INLAY_OUTLINE"}
            )
        elif shape.vertices:
            # R12 doesn't support LWPOLYLINE, use LINE segments
            pts = [(shape.x_mm + v[0], shape.y_mm + v[1]) for v in shape.vertices]
            for i in range(len(pts)):
                p1 = pts[i]
                p2 = pts[(i + 1) % len(pts)]
                msp.add_line(p1, p2, dxfattribs={"layer": "INLAY_OUTLINE"})
    
    from io import StringIO
    stream = StringIO()
    doc.write(stream)
    return stream.getvalue()


# Preset configurations
INLAY_PRESETS = {
    "dot_standard": InlayCalcInput(
        pattern_type=InlayPatternType.DOT,
        fret_positions=[3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
        double_at_12=True,
        marker_diameter_mm=6.0,
    ),
    "dot_vintage": InlayCalcInput(
        pattern_type=InlayPatternType.DOT,
        fret_positions=[3, 5, 7, 9, 12, 15, 17, 19, 21],
        double_at_12=True,
        marker_diameter_mm=6.35,  # 1/4"
    ),
    "dot_classical": InlayCalcInput(
        pattern_type=InlayPatternType.DOT,
        fret_positions=[5, 7, 9, 12],
        double_at_12=True,
        marker_diameter_mm=5.0,
    ),
    "diamond_jazz": InlayCalcInput(
        pattern_type=InlayPatternType.DIAMOND,
        fret_positions=[3, 5, 7, 9, 12, 15, 17, 19, 21],
        double_at_12=False,
        marker_diameter_mm=8.0,
    ),
    "block_gibson": InlayCalcInput(
        pattern_type=InlayPatternType.BLOCK,
        fret_positions=[1, 3, 5, 7, 9, 12, 15, 17, 19, 21],
        double_at_12=False,
        block_width_mm=38.0,
        block_height_mm=9.0,
    ),
    "trapezoid_es": InlayCalcInput(
        pattern_type=InlayPatternType.PARALLELOGRAM,
        fret_positions=[1, 3, 5, 7, 9, 12, 15, 17, 19, 21],
        double_at_12=False,
        block_width_mm=35.0,
        block_height_mm=8.0,
    ),
}


def get_preset(name: str) -> Optional[InlayCalcInput]:
    """Get a preset inlay configuration by name."""
    return INLAY_PRESETS.get(name)


def list_presets() -> Dict[str, str]:
    """List available inlay presets with descriptions."""
    return {
        "dot_standard": "Standard 6mm dot markers (3,5,7,9,12,15,17,19,21,24)",
        "dot_vintage": "Vintage 1/4\" dot markers (21 frets)",
        "dot_classical": "Classical style markers (5,7,9,12 only)",
        "diamond_jazz": "Jazz-style diamond markers",
        "block_gibson": "Gibson Les Paul-style block inlays",
        "trapezoid_es": "Gibson ES-style trapezoid inlays",
    }


def get_scale_from_registry(scale_id: str = "fender_25_5", edition: str = "express") -> float:
    """
    Get scale length from data registry (system tier - available to all editions).
    
    Args:
        scale_id: Scale identifier (fender_25_5, gibson_24_75, prs_25, etc.)
        edition: Product edition (express, pro, enterprise) - defaults to express for system data
    
    Returns:
        Scale length in mm (defaults to 647.7mm if registry unavailable)
    
    Examples:
        >>> get_scale_from_registry("fender_25_5")  # 647.7mm
        >>> get_scale_from_registry("gibson_24_75")  # 628.65mm
    """
    try:
        from ..data_registry import Registry
        registry = Registry(edition=edition)
        scales = registry.get_scale_lengths()
        if scales and "scales" in scales:
            scale_data = scales["scales"].get(scale_id, {})
            return scale_data.get("length_mm", 647.7)
    except Exception:
        pass  # Fall back to default
    return 647.7  # Fender 25.5" default
