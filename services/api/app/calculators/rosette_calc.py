# services/api/app/calculators/rosette_calc.py

"""
Rosette calculator façade for the Luthier's ToolBox.

This module centralizes access to rosette channel dimension calculations
that currently live in `pipelines.rosette.rosette_calc`.

Legacy math is preserved in that module; this layer provides a
stable, RMOS/Art Studio-friendly interface.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Import the migrated rosette functions
try:
    from ..pipelines.rosette import rosette_calc as legacy
    from ..pipelines.rosette import rosette_to_dxf
except ImportError as exc:
    raise ImportError(
        "Rosette calculator module `pipelines.rosette.rosette_calc` "
        "was not found. Ensure the migration placed it correctly."
    ) from exc


class PurflingBand(BaseModel):
    """A single purfling strip in the rosette stack."""
    material: str = Field(default="bwb", description="Material code: bwb, abalone, maple, etc.")
    width_mm: float = Field(default=1.5, description="Strip width in mm")


class RosetteCalcInput(BaseModel):
    """
    Input for rosette channel calculations.
    
    The rosette channel houses the decorative rings around the soundhole.
    """
    soundhole_diameter_mm: float = Field(
        default=100.0,
        ge=50.0,
        le=150.0,
        description="Soundhole diameter in mm (typically 100-110mm for steel string)"
    )
    central_band_mm: float = Field(
        default=3.0,
        ge=0.0,
        le=20.0,
        description="Width of central decorative band (mosaic, abalone, etc.)"
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
        description="Channel routing depth (typically 1.5mm for veneer rosettes)"
    )
    
    def to_legacy_params(self) -> Dict[str, Any]:
        """Convert to params dict expected by legacy compute()."""
        return {
            "soundhole_diameter_mm": self.soundhole_diameter_mm,
            "central_band": {"width_mm": self.central_band_mm},
            "inner_purfling": [
                {"material": p.material, "width_mm": p.width_mm}
                for p in self.inner_purfling
            ],
            "outer_purfling": [
                {"material": p.material, "width_mm": p.width_mm}
                for p in self.outer_purfling
            ],
        }


class RosetteStackInfo(BaseModel):
    """Detailed breakdown of the rosette stack construction."""
    inner_purfling_width_mm: float
    central_band_width_mm: float
    outer_purfling_width_mm: float
    total_width_mm: float


class RosetteCalcResult(BaseModel):
    """Result of rosette channel calculation."""
    
    soundhole_diameter_mm: float = Field(description="Input soundhole diameter")
    soundhole_radius_mm: float = Field(description="Soundhole radius (diameter/2)")
    channel_width_mm: float = Field(description="Total channel width to route")
    channel_depth_mm: float = Field(description="Channel routing depth")
    channel_inner_radius_mm: float = Field(description="Inner edge of channel from center")
    channel_outer_radius_mm: float = Field(description="Outer edge of channel from center")
    stack: RosetteStackInfo = Field(description="Breakdown of rosette components")
    
    # For CNC/CAM integration
    toolpath_notes: str = Field(
        default="",
        description="Notes for CNC toolpath generation"
    )


def calculate_rosette_channel(input_data: RosetteCalcInput) -> RosetteCalcResult:
    """
    Calculate rosette channel dimensions from input parameters.
    
    Calls the legacy `rosette_calc.compute()` function and transforms
    the result into our structured model.
    
    Args:
        input_data: RosetteCalcInput with soundhole and purfling specs
        
    Returns:
        RosetteCalcResult with channel dimensions and stack breakdown
    """
    params = input_data.to_legacy_params()
    result = legacy.compute(params)
    
    soundhole_r = input_data.soundhole_diameter_mm / 2.0
    channel_width = result["channel_width_mm"]
    
    # Channel is centered around the soundhole edge
    # Inner radius is where channel starts (inside soundhole edge)
    # Outer radius is where channel ends (outside soundhole edge)
    stack = result.get("stack", {})
    inner_purfling_w = stack.get("inner_purfling_mm", 0.0)
    outer_purfling_w = stack.get("outer_purfling_mm", 0.0)
    central_band_w = stack.get("central_band_mm", input_data.central_band_mm)
    
    channel_inner_r = soundhole_r - inner_purfling_w
    channel_outer_r = soundhole_r + central_band_w + outer_purfling_w
    
    return RosetteCalcResult(
        soundhole_diameter_mm=input_data.soundhole_diameter_mm,
        soundhole_radius_mm=soundhole_r,
        channel_width_mm=channel_width,
        channel_depth_mm=input_data.channel_depth_mm,
        channel_inner_radius_mm=round(channel_inner_r, 3),
        channel_outer_radius_mm=round(channel_outer_r, 3),
        stack=RosetteStackInfo(
            inner_purfling_width_mm=inner_purfling_w,
            central_band_width_mm=central_band_w,
            outer_purfling_width_mm=outer_purfling_w,
            total_width_mm=channel_width,
        ),
        toolpath_notes=f"Route {channel_width:.2f}mm channel at {input_data.channel_depth_mm}mm depth"
    )


def generate_rosette_dxf_string(
    result: RosetteCalcResult,
    center_x: float = 0.0,
    center_y: float = 0.0,
    include_purfling_rings: bool = True,
) -> str:
    """
    Generate R12 DXF string for rosette geometry.
    
    Args:
        result: RosetteCalcResult from calculate_rosette_channel()
        center_x: X coordinate of soundhole center
        center_y: Y coordinate of soundhole center
        include_purfling_rings: Whether to include individual purfling circles
        
    Returns:
        DXF R12 string content
    """
    purfling_rings = None
    if include_purfling_rings:
        # Generate intermediate rings for each purfling strip
        purfling_rings = []
        # This is a simplified approach - actual purfling ring radii
        # would need more detailed calculation from the stack
    
    return rosette_to_dxf.generate_rosette_dxf(
        soundhole_r=result.soundhole_radius_mm,
        channel_inner_r=result.channel_inner_radius_mm,
        channel_outer_r=result.channel_outer_radius_mm,
        center_x=center_x,
        center_y=center_y,
        purfling_rings=purfling_rings,
    )


# Preset rosette configurations
ROSETTE_PRESETS = {
    "classical_simple": RosetteCalcInput(
        soundhole_diameter_mm=85.0,
        central_band_mm=4.0,
        inner_purfling=[PurflingBand(material="bwb", width_mm=1.5)],
        outer_purfling=[PurflingBand(material="bwb", width_mm=1.5)],
        channel_depth_mm=1.5,
    ),
    "classical_mosaic": RosetteCalcInput(
        soundhole_diameter_mm=85.0,
        central_band_mm=12.0,  # Wide mosaic band
        inner_purfling=[
            PurflingBand(material="bwb", width_mm=1.5),
            PurflingBand(material="maple", width_mm=0.5),
        ],
        outer_purfling=[
            PurflingBand(material="maple", width_mm=0.5),
            PurflingBand(material="bwb", width_mm=1.5),
        ],
        channel_depth_mm=2.0,
    ),
    "steel_string_standard": RosetteCalcInput(
        soundhole_diameter_mm=100.0,
        central_band_mm=3.0,
        inner_purfling=[PurflingBand(material="bwb", width_mm=1.5)],
        outer_purfling=[PurflingBand(material="bwb", width_mm=1.5)],
        channel_depth_mm=1.5,
    ),
    "steel_string_abalone": RosetteCalcInput(
        soundhole_diameter_mm=102.0,
        central_band_mm=5.0,  # Abalone ring
        inner_purfling=[
            PurflingBand(material="bwb", width_mm=1.5),
            PurflingBand(material="white", width_mm=0.5),
        ],
        outer_purfling=[
            PurflingBand(material="white", width_mm=0.5),
            PurflingBand(material="bwb", width_mm=1.5),
        ],
        channel_depth_mm=1.5,
    ),
    "parlor_vintage": RosetteCalcInput(
        soundhole_diameter_mm=95.0,
        central_band_mm=2.5,
        inner_purfling=[PurflingBand(material="bwb", width_mm=1.0)],
        outer_purfling=[PurflingBand(material="bwb", width_mm=1.0)],
        channel_depth_mm=1.5,
    ),
}


def get_preset(name: str) -> Optional[RosetteCalcInput]:
    """Get a preset rosette configuration by name."""
    return ROSETTE_PRESETS.get(name)


def list_presets() -> Dict[str, str]:
    """List available rosette presets with descriptions."""
    return {
        "classical_simple": "Simple B-W-B rosette for classical guitars (85mm soundhole)",
        "classical_mosaic": "Traditional mosaic rosette for classical guitars",
        "steel_string_standard": "Standard 3-ring rosette for steel string (100mm soundhole)",
        "steel_string_abalone": "Abalone ring rosette for steel string guitars",
        "parlor_vintage": "Vintage-style rosette for parlor guitars (95mm soundhole)",
    }
