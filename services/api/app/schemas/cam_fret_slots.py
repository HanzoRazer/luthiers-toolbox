"""
CAM Fret Slots Schemas

Pydantic models for fret slot CAM export operations.

Phase E Implementation (December 2025)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class PostProcessor(str, Enum):
    """Supported G-code post-processors."""
    GRBL = "GRBL"
    MACH3 = "Mach3"
    MACH4 = "Mach4"
    LINUXCNC = "LinuxCNC"
    PATHPILOT = "PathPilot"
    MASSO = "MASSO"
    FANUC = "Fanuc"
    HAAS = "Haas"


class FretSlotExportRequest(BaseModel):
    """Request for fret slot G-code export."""
    
    # Fretboard parameters
    scale_length_mm: float = Field(..., description="Scale length in mm", gt=0)
    fret_count: int = Field(22, description="Number of frets", ge=1, le=36)
    nut_width_mm: float = Field(42.0, description="Fretboard width at nut")
    heel_width_mm: float = Field(56.0, description="Fretboard width at heel")
    
    # Optional compound radius
    base_radius_mm: Optional[float] = Field(None, description="Radius at nut (mm)")
    end_radius_mm: Optional[float] = Field(None, description="Radius at heel (mm)")
    
    # CAM parameters
    slot_depth_mm: float = Field(3.0, description="Fret slot depth", gt=0, le=10)
    slot_width_mm: float = Field(0.58, description="Fret slot width (kerf)")
    safe_z_mm: float = Field(5.0, description="Safe retract height")
    
    # Post-processor selection
    post_processor: PostProcessor = Field(PostProcessor.GRBL, description="Target controller")
    
    # Optional overrides
    feed_rate_mmpm: Optional[float] = Field(None, description="Override feed rate")
    plunge_rate_mmpm: Optional[float] = Field(None, description="Override plunge rate")
    
    class Config:
        schema_extra = {
            "example": {
                "scale_length_mm": 648.0,
                "fret_count": 22,
                "nut_width_mm": 42.0,
                "heel_width_mm": 56.0,
                "base_radius_mm": 241.3,
                "end_radius_mm": 304.8,
                "slot_depth_mm": 3.0,
                "post_processor": "GRBL",
            }
        }


class FretSlotData(BaseModel):
    """Data for a single fret slot."""
    fret_number: int
    position_mm: float = Field(..., description="Distance from nut")
    width_mm: float = Field(..., description="Slot width at this position")
    depth_mm: float = Field(..., description="Slot cutting depth")
    bass_x: float
    bass_y: float
    treble_x: float
    treble_y: float


class FretSlotExportResponse(BaseModel):
    """Response containing exported G-code and metadata."""
    
    # G-code output
    gcode: str = Field(..., description="Complete G-code program")
    
    # DXF output (optional)
    dxf: Optional[str] = Field(None, description="DXF file content")
    
    # Metadata
    post_processor: str
    slot_count: int
    total_cutting_length_mm: float
    estimated_time_min: float
    
    # Per-slot data
    slots: List[FretSlotData]
    
    # Warnings/recommendations
    warnings: List[str] = Field(default_factory=list)


class MultiExportRequest(BaseModel):
    """Request for exporting to multiple post-processors at once."""
    
    base_request: FretSlotExportRequest
    post_processors: List[PostProcessor] = Field(
        ..., 
        description="List of post-processors to export to",
        min_items=1,
        max_items=8,
    )


class MultiExportResponse(BaseModel):
    """Response containing exports for multiple post-processors."""
    
    exports: Dict[str, FretSlotExportResponse] = Field(
        ...,
        description="Map of post-processor name to export response"
    )
    
    # Summary
    total_exports: int
    failed_exports: List[str] = Field(default_factory=list)


class ExportStatistics(BaseModel):
    """Statistics for an export operation."""
    
    slot_count: int
    total_cutting_length_mm: float
    total_plunge_depth_mm: float
    estimated_time_min: float
    estimated_time_s: float
    rapid_distance_mm: float
    cutting_distance_mm: float
    
    # Feed rates used
    feed_rate_mmpm: float
    plunge_rate_mmpm: float
    rapid_rate_mmpm: float = 3000.0
