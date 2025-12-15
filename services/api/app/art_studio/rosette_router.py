# services/api/app/art_studio/rosette_router.py

"""
Art Studio Rosette Router

Endpoints for rosette channel calculation and DXF export.
Wraps the rosette_calc façade for API access.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..calculators.rosette_calc import (
    PurflingBand,
    RosetteCalcInput,
    RosetteCalcResult,
    calculate_rosette_channel,
    generate_rosette_dxf_string,
    get_preset,
    list_presets,
    ROSETTE_PRESETS,
)

router = APIRouter(
    prefix="/art-studio/rosette",
    tags=["Art Studio - Rosette"],
)


# --------------------------------------------------------------------- #
# Request/Response Models
# --------------------------------------------------------------------- #

class RosettePreviewRequest(BaseModel):
    """Request model for rosette preview calculation."""
    
    soundhole_diameter_mm: float = Field(
        default=100.0,
        ge=50.0,
        le=150.0,
        description="Soundhole diameter in mm"
    )
    central_band_mm: float = Field(
        default=3.0,
        ge=0.0,
        le=20.0,
        description="Width of central decorative band"
    )
    inner_purfling: List[PurflingBand] = Field(
        default_factory=lambda: [PurflingBand(material="bwb", width_mm=1.5)],
        description="Purfling strips inside the central band"
    )
    outer_purfling: List[PurflingBand] = Field(
        default_factory=lambda: [PurflingBand(material="bwb", width_mm=1.5)],
        description="Purfling strips outside the central band"
    )
    channel_depth_mm: float = Field(
        default=1.5,
        ge=0.5,
        le=4.0,
        description="Channel routing depth"
    )


class RosettePreviewResponse(BaseModel):
    """Response model for rosette preview."""
    
    result: RosetteCalcResult
    preview_svg: Optional[str] = Field(
        default=None,
        description="SVG preview of the rosette (optional)"
    )


class RosetteDXFRequest(BaseModel):
    """Request model for rosette DXF export."""
    
    soundhole_diameter_mm: float = Field(default=100.0, ge=50.0, le=150.0)
    central_band_mm: float = Field(default=3.0, ge=0.0, le=20.0)
    inner_purfling: List[PurflingBand] = Field(
        default_factory=lambda: [PurflingBand(material="bwb", width_mm=1.5)]
    )
    outer_purfling: List[PurflingBand] = Field(
        default_factory=lambda: [PurflingBand(material="bwb", width_mm=1.5)]
    )
    channel_depth_mm: float = Field(default=1.5, ge=0.5, le=4.0)
    
    center_x_mm: float = Field(default=0.0, description="Soundhole center X")
    center_y_mm: float = Field(default=0.0, description="Soundhole center Y")
    include_purfling_rings: bool = Field(
        default=True,
        description="Include individual purfling ring circles"
    )


class PresetInfo(BaseModel):
    """Information about a rosette preset."""
    name: str
    description: str
    soundhole_diameter_mm: float
    central_band_mm: float
    channel_depth_mm: float


# --------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------- #

@router.post("/preview", response_model=RosettePreviewResponse)
def preview_rosette(req: RosettePreviewRequest) -> RosettePreviewResponse:
    """
    Calculate rosette channel dimensions and return preview.
    
    This endpoint computes the channel width, inner/outer radii,
    and stack breakdown for the given rosette configuration.
    """
    try:
        calc_input = RosetteCalcInput(
            soundhole_diameter_mm=req.soundhole_diameter_mm,
            central_band_mm=req.central_band_mm,
            inner_purfling=req.inner_purfling,
            outer_purfling=req.outer_purfling,
            channel_depth_mm=req.channel_depth_mm,
        )
        
        result = calculate_rosette_channel(calc_input)
        
        # Generate simple SVG preview
        svg = _generate_preview_svg(result)
        
        return RosettePreviewResponse(result=result, preview_svg=svg)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export-dxf")
def export_rosette_dxf(req: RosetteDXFRequest) -> Response:
    """
    Export rosette geometry as DXF R12 file.
    
    Returns a DXF file with circles for soundhole, channel inner/outer,
    and optionally individual purfling rings on separate layers.
    """
    try:
        calc_input = RosetteCalcInput(
            soundhole_diameter_mm=req.soundhole_diameter_mm,
            central_band_mm=req.central_band_mm,
            inner_purfling=req.inner_purfling,
            outer_purfling=req.outer_purfling,
            channel_depth_mm=req.channel_depth_mm,
        )
        
        result = calculate_rosette_channel(calc_input)
        
        dxf_content = generate_rosette_dxf_string(
            result,
            center_x=req.center_x_mm,
            center_y=req.center_y_mm,
            include_purfling_rings=req.include_purfling_rings,
        )
        
        filename = f"rosette_{req.soundhole_diameter_mm:.0f}mm.dxf"
        
        return Response(
            content=dxf_content.encode("utf-8"),
            media_type="application/dxf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/presets", response_model=List[PresetInfo])
def get_rosette_presets() -> List[PresetInfo]:
    """
    List available rosette presets.
    
    Returns preset configurations for common rosette styles:
    - Classical (simple, mosaic)
    - Steel string (standard, abalone)
    - Parlor vintage
    """
    descriptions = list_presets()
    result = []
    
    for name, preset in ROSETTE_PRESETS.items():
        result.append(PresetInfo(
            name=name,
            description=descriptions.get(name, ""),
            soundhole_diameter_mm=preset.soundhole_diameter_mm,
            central_band_mm=preset.central_band_mm,
            channel_depth_mm=preset.channel_depth_mm,
        ))
    
    return result


@router.get("/presets/{preset_name}", response_model=RosetteCalcInput)
def get_rosette_preset(preset_name: str) -> RosetteCalcInput:
    """
    Get a specific rosette preset by name.
    
    Returns the full configuration for the named preset.
    """
    preset = get_preset(preset_name)
    if not preset:
        available = list(ROSETTE_PRESETS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{preset_name}' not found. Available: {available}"
        )
    return preset


@router.post("/preset/{preset_name}/preview", response_model=RosettePreviewResponse)
def preview_rosette_preset(preset_name: str) -> RosettePreviewResponse:
    """
    Calculate rosette using a preset configuration.
    
    Convenience endpoint to preview a standard rosette style.
    """
    preset = get_preset(preset_name)
    if not preset:
        available = list(ROSETTE_PRESETS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{preset_name}' not found. Available: {available}"
        )
    
    result = calculate_rosette_channel(preset)
    svg = _generate_preview_svg(result)
    
    return RosettePreviewResponse(result=result, preview_svg=svg)


# --------------------------------------------------------------------- #
# Helper Functions
# --------------------------------------------------------------------- #

def _generate_preview_svg(result: RosetteCalcResult) -> str:
    """Generate a simple SVG preview of the rosette."""
    # Scale factor to fit in reasonable viewport
    scale = 3.0
    cx = 150  # SVG center
    cy = 150
    
    r_soundhole = result.soundhole_radius_mm * scale
    r_inner = result.channel_inner_radius_mm * scale
    r_outer = result.channel_outer_radius_mm * scale
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="300" height="300">
  <style>
    .soundhole {{ fill: #333; stroke: none; }}
    .channel {{ fill: #c4a574; stroke: #8b6914; stroke-width: 1; }}
    .channel-inner {{ fill: none; stroke: #555; stroke-width: 0.5; stroke-dasharray: 2,2; }}
  </style>
  
  <!-- Channel (donut shape) -->
  <circle cx="{cx}" cy="{cy}" r="{r_outer}" class="channel"/>
  <circle cx="{cx}" cy="{cy}" r="{r_inner}" fill="#f5f0e6"/>
  
  <!-- Soundhole -->
  <circle cx="{cx}" cy="{cy}" r="{r_soundhole}" class="soundhole"/>
  
  <!-- Inner channel line -->
  <circle cx="{cx}" cy="{cy}" r="{r_inner}" class="channel-inner"/>
  
  <!-- Labels -->
  <text x="{cx}" y="20" text-anchor="middle" font-size="12" fill="#333">
    Soundhole: {result.soundhole_diameter_mm:.1f}mm
  </text>
  <text x="{cx}" y="290" text-anchor="middle" font-size="12" fill="#333">
    Channel: {result.channel_width_mm:.2f}mm wide × {result.channel_depth_mm:.1f}mm deep
  </text>
</svg>'''
    
    return svg
