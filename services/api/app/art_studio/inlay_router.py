# services/api/app/art_studio/inlay_router.py

"""
Art Studio Inlay Router

Endpoints for fretboard inlay pattern generation and DXF export.
Supports dots, diamonds, blocks, and custom shapes.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..calculators.inlay_calc import (
    InlayPatternType,
    InlayCalcInput,
    InlayCalcResult,
    InlayShape,
    calculate_fretboard_inlays,
    generate_inlay_dxf_string,
    get_preset,
    list_presets,
    INLAY_PRESETS,
    fret_position_mm,
    fret_midpoint_mm,
)

# Import dxf_compat for version support
try:
    from ..util.dxf_compat import SUPPORTED_VERSIONS, validate_version
    DXF_VERSIONS_AVAILABLE = list(SUPPORTED_VERSIONS.keys())
except ImportError:
    DXF_VERSIONS_AVAILABLE = ["R12"]
    def validate_version(v: str) -> str:
        return "R12"

router = APIRouter(
    prefix="/art-studio/inlay",
    tags=["Art Studio - Inlay"],
)


# --------------------------------------------------------------------- #
# Request/Response Models
# --------------------------------------------------------------------- #

class InlayPreviewRequest(BaseModel):
    """Request model for inlay preview calculation."""
    
    pattern_type: InlayPatternType = Field(
        default=InlayPatternType.DOT,
        description="Type of inlay shape"
    )
    fret_positions: List[int] = Field(
        default_factory=lambda: [3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
        description="Fret numbers to place markers"
    )
    double_at_12: bool = Field(
        default=True,
        description="Use double markers at 12th fret"
    )
    marker_diameter_mm: float = Field(
        default=6.0,
        ge=2.0,
        le=20.0,
        description="Dot diameter or shape width"
    )
    block_width_mm: float = Field(
        default=40.0,
        description="Block inlay width"
    )
    block_height_mm: float = Field(
        default=8.0,
        description="Block inlay height"
    )
    scale_length_mm: float = Field(
        default=648.0,
        description="Guitar scale length in mm"
    )
    pocket_depth_mm: float = Field(
        default=1.5,
        ge=0.5,
        le=5.0,
        description="Routing depth for inlay pocket"
    )
    include_side_dots: bool = Field(
        default=False,
        description="Include side dot positions"
    )


class InlayPreviewResponse(BaseModel):
    """Response model for inlay preview."""
    
    result: InlayCalcResult
    preview_svg: Optional[str] = Field(
        default=None,
        description="SVG preview of the inlay pattern"
    )


class InlayDXFRequest(BaseModel):
    """Request model for inlay DXF export."""
    
    pattern_type: InlayPatternType = Field(default=InlayPatternType.DOT)
    fret_positions: List[int] = Field(
        default_factory=lambda: [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]
    )
    double_at_12: bool = Field(default=True)
    marker_diameter_mm: float = Field(default=6.0, ge=2.0, le=20.0)
    block_width_mm: float = Field(default=40.0)
    block_height_mm: float = Field(default=8.0)
    scale_length_mm: float = Field(default=648.0)
    pocket_depth_mm: float = Field(default=1.5, ge=0.5, le=5.0)
    include_side_dots: bool = Field(default=False)
    
    dxf_version: str = Field(
        default="R12",
        description="DXF version for export (R12 for max CAM compatibility)"
    )


class PresetInfo(BaseModel):
    """Information about an inlay preset."""
    name: str
    description: str
    pattern_type: InlayPatternType
    fret_count: int


class FretPositionInfo(BaseModel):
    """Information about a fret position."""
    fret_number: int
    distance_from_nut_mm: float
    midpoint_mm: float


# --------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------- #

@router.post("/preview", response_model=InlayPreviewResponse)
def preview_inlay(req: InlayPreviewRequest) -> InlayPreviewResponse:
    """
    Calculate inlay positions and return preview.
    
    This endpoint computes the X/Y positions for each inlay shape
    based on scale length and fret positions using 12-TET formula.
    """
    try:
        calc_input = InlayCalcInput(
            pattern_type=req.pattern_type,
            fret_positions=req.fret_positions,
            double_at_12=req.double_at_12,
            marker_diameter_mm=req.marker_diameter_mm,
            block_width_mm=req.block_width_mm,
            block_height_mm=req.block_height_mm,
            scale_length_mm=req.scale_length_mm,
            pocket_depth_mm=req.pocket_depth_mm,
            include_side_dots=req.include_side_dots,
        )
        
        result = calculate_fretboard_inlays(calc_input)
        
        # Generate SVG preview
        svg = _generate_preview_svg(result, req.scale_length_mm)
        
        return InlayPreviewResponse(result=result, preview_svg=svg)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export-dxf")
def export_inlay_dxf(req: InlayDXFRequest) -> Response:
    """
    Export inlay pattern as DXF file.
    
    Returns a DXF file with inlay shapes on the INLAY_OUTLINE layer
    and center points on INLAY_CENTER layer.
    
    Default is R12 format for maximum CAM software compatibility.
    """
    try:
        # Validate DXF version
        version = validate_version(req.dxf_version)
        
        calc_input = InlayCalcInput(
            pattern_type=req.pattern_type,
            fret_positions=req.fret_positions,
            double_at_12=req.double_at_12,
            marker_diameter_mm=req.marker_diameter_mm,
            block_width_mm=req.block_width_mm,
            block_height_mm=req.block_height_mm,
            scale_length_mm=req.scale_length_mm,
            pocket_depth_mm=req.pocket_depth_mm,
            include_side_dots=req.include_side_dots,
        )
        
        result = calculate_fretboard_inlays(calc_input)
        
        dxf_content = generate_inlay_dxf_string(result, dxf_version=version)
        
        filename = f"inlay_{req.pattern_type.value}_{len(req.fret_positions)}frets.dxf"
        
        return Response(
            content=dxf_content.encode("utf-8"),
            media_type="application/dxf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets", response_model=List[PresetInfo])
def get_inlay_presets() -> List[PresetInfo]:
    """
    List available inlay presets.
    
    Returns preset configurations for common inlay styles:
    - Dot (standard, vintage, classical)
    - Diamond (jazz)
    - Block (Gibson Les Paul)
    - Trapezoid (Gibson ES)
    """
    descriptions = list_presets()
    result = []
    
    for name, preset in INLAY_PRESETS.items():
        result.append(PresetInfo(
            name=name,
            description=descriptions.get(name, ""),
            pattern_type=preset.pattern_type,
            fret_count=len(preset.fret_positions),
        ))
    
    return result


@router.get("/presets/{preset_name}", response_model=InlayCalcInput)
def get_inlay_preset(preset_name: str) -> InlayCalcInput:
    """
    Get a specific inlay preset by name.
    
    Returns the full configuration for the named preset.
    """
    preset = get_preset(preset_name)
    if not preset:
        available = list(INLAY_PRESETS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{preset_name}' not found. Available: {available}"
        )
    return preset


@router.post("/preset/{preset_name}/preview", response_model=InlayPreviewResponse)
def preview_inlay_preset(preset_name: str) -> InlayPreviewResponse:
    """
    Calculate inlay using a preset configuration.
    
    Convenience endpoint to preview a standard inlay style.
    """
    preset = get_preset(preset_name)
    if not preset:
        available = list(INLAY_PRESETS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{preset_name}' not found. Available: {available}"
        )
    
    result = calculate_fretboard_inlays(preset)
    svg = _generate_preview_svg(result, preset.scale_length_mm)
    
    return InlayPreviewResponse(result=result, preview_svg=svg)


@router.get("/pattern-types", response_model=List[str])
def get_pattern_types() -> List[str]:
    """
    List available inlay pattern types.
    
    Returns: dot, diamond, block, parallelogram, split_block, crown, snowflake, custom
    """
    return [p.value for p in InlayPatternType]


@router.get("/dxf-versions", response_model=List[str])
def get_dxf_versions() -> List[str]:
    """
    List supported DXF versions for export.
    
    R12 is recommended for maximum CAM compatibility.
    """
    return DXF_VERSIONS_AVAILABLE


@router.get("/fret-positions", response_model=List[FretPositionInfo])
def get_fret_positions(
    scale_length_mm: float = Query(default=648.0, description="Scale length in mm"),
    max_fret: int = Query(default=24, ge=12, le=36, description="Maximum fret number"),
) -> List[FretPositionInfo]:
    """
    Calculate fret positions for a given scale length.
    
    Uses the 12-TET (twelve-tone equal temperament) formula:
    position = scale_length × (1 - 2^(-fret/12))
    
    Returns both the fret wire position and the midpoint where
    inlays are typically placed.
    """
    positions = []
    for fret in range(1, max_fret + 1):
        positions.append(FretPositionInfo(
            fret_number=fret,
            distance_from_nut_mm=round(fret_position_mm(fret, scale_length_mm), 3),
            midpoint_mm=round(fret_midpoint_mm(fret, scale_length_mm), 3),
        ))
    return positions


# --------------------------------------------------------------------- #
# Helper Functions
# --------------------------------------------------------------------- #

def _generate_preview_svg(result: InlayCalcResult, scale_length_mm: float) -> str:
    """Generate a simple SVG preview of the inlay pattern."""
    # Calculate SVG dimensions
    bounds = result.bounds_mm
    width = bounds["max_x"] - bounds["min_x"] + 20
    height = max(60, bounds["max_y"] - bounds["min_y"] + 40)
    
    # Scale to fit nicely
    scale = min(800 / width, 100 / height) if width > 0 else 1.0
    svg_width = int(width * scale) + 40
    svg_height = int(height * scale) + 60
    
    # Offset for centering
    offset_x = 20 - bounds["min_x"] * scale
    offset_y = svg_height / 2
    
    shapes_svg = []
    for shape in result.shapes:
        x = shape.x_mm * scale + offset_x
        y = offset_y - shape.y_mm * scale  # Flip Y for SVG
        
        if shape.pattern_type == InlayPatternType.DOT:
            r = shape.width_mm * scale / 2
            shapes_svg.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
                f'fill="#f0e6d2" stroke="#8b6914" stroke-width="1"/>'
            )
        elif shape.vertices:
            # Polygon
            points = []
            for vx, vy in shape.vertices:
                px = x + vx * scale
                py = y - vy * scale  # Flip Y
                points.append(f"{px:.1f},{py:.1f}")
            points_str = " ".join(points)
            shapes_svg.append(
                f'<polygon points="{points_str}" '
                f'fill="#f0e6d2" stroke="#8b6914" stroke-width="1"/>'
            )
    
    shapes_content = "\n  ".join(shapes_svg)
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" 
     width="{svg_width}" height="{svg_height}">
  <style>
    .fretboard {{ fill: #3d2817; }}
    .label {{ font-size: 10px; fill: #666; text-anchor: middle; }}
  </style>
  
  <!-- Fretboard background -->
  <rect x="10" y="{offset_y - 25}" width="{svg_width - 20}" height="50" class="fretboard" rx="3"/>
  
  <!-- Inlay shapes -->
  {shapes_content}
  
  <!-- Labels -->
  <text x="{svg_width/2}" y="15" class="label">
    {result.total_shapes} {result.pattern_type.value} inlays
  </text>
  <text x="{svg_width/2}" y="{svg_height - 10}" class="label">
    Scale: {scale_length_mm:.0f}mm | Depth: {result.pocket_depth_mm:.1f}mm
  </text>
</svg>'''
    
    return svg
