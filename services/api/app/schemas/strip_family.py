from __future__ import annotations

from typing import Optional, List, Literal

from pydantic import BaseModel, Field

# MM-0: Mixed-Material Extensions
MaterialType = Literal["wood", "metal", "shell", "paper", "foil", "charred", "resin", "composite"]


class MaterialVisual(BaseModel):
    """Visual rendering properties for a material (MM-1)."""
    base_color: Optional[str] = None
    reflectivity: Optional[float] = None
    iridescence: Optional[bool] = None
    texture_map: Optional[str] = None
    grain_angle_deg: Optional[float] = None
    burn_gradient: Optional[bool] = None
    repeat_pattern: Optional[bool] = None


class MaterialSpec(BaseModel):
    """Specification for a single material in a strip family."""
    key: str = Field(..., description="Material identifier key")
    type: MaterialType = Field(..., description="Material type")
    species: Optional[str] = Field(None, description="Species or material name")
    thickness_mm: Optional[float] = Field(None, description="Thickness in mm")
    finish: Optional[str] = Field(None, description="Surface finish")
    cam_profile: Optional[str] = Field(None, description="CAM profile identifier (MM-2)")
    visual: Optional[MaterialVisual] = Field(None, description="Visual rendering data")


class StripFamilyBase(BaseModel):
    id: str = Field(..., description="Unique family id (e.g. 'bw_checker_main')")
    name: str = Field(..., description="Human readable name")
    color_hex: Optional[str] = Field("#999999", description="UI color swatch")
    default_tile_length_mm: Optional[float] = Field(
        None, description="Optional override for tile length"
    )
    default_slice_angle_deg: Optional[float] = Field(
        None, description="Default slice angle override"
    )
    notes: Optional[str] = None
    
    # MM-0: Mixed-material extensions
    default_width_mm: Optional[float] = Field(None, description="Default strip width (mm)")
    sequence: Optional[List[int]] = Field([], description="Material sequence indices")
    materials: Optional[List[MaterialSpec]] = Field([], description="Material specifications")
    lane: Optional[str] = Field("experimental", description="Quality lane")


class StripFamilyInDB(StripFamilyBase):
    """Internal storage representation."""


class StripFamilyCreate(StripFamilyBase):
    pass


class StripFamilyUpdate(BaseModel):
    name: Optional[str] = None
    color_hex: Optional[str] = None
    default_tile_length_mm: Optional[float] = None
    default_slice_angle_deg: Optional[float] = None
    notes: Optional[str] = None
    
    # MM-0: Mixed-material extensions
    default_width_mm: Optional[float] = None
    sequence: Optional[List[int]] = None
    materials: Optional[List[MaterialSpec]] = None
    lane: Optional[str] = None


# MM-0: Template model for JSON deserialization
class StripFamilyTemplate(BaseModel):
    """Strip family template from JSON file."""
    id: str
    name: str
    description: Optional[str] = None
    default_width_mm: Optional[float] = None
    sequence: List[int] = []
    materials: List[MaterialSpec] = []
    notes: Optional[str] = None


# Alias for backward compatibility with imports expecting 'StripFamily'
StripFamily = StripFamilyBase
