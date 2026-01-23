"""
CAM Fret Slots Schemas

Pydantic models for fret slot CAM export operations.

Phase E Implementation (December 2025)
PATCH-001: Add intonation_model for explicit 12-TET default + opt-in custom ratios (January 2026)
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


# Intonation model choice - explicit default preserves existing behavior
IntonationModel = Literal["equal_temperament_12", "custom_ratios"]


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

    # PATCH-001: Intonation model selection
    # Default preserves existing behavior: compute_fret_positions_mm() (12-TET)
    intonation_model: IntonationModel = Field(
        default="equal_temperament_12",
        description="Fret position calculation model. Default 12-TET for standard guitars.",
    )

    # PATCH-001: Ratio-based fret placement (opt-in only)
    # If intonation_model == "custom_ratios", caller must provide:
    #   - ratio_set_id (maps to known tables), OR
    #   - ratios[] (explicit per-fret frequency ratios, length == fret_count)
    #
    # Ratio semantics:
    #   ratios[n-1] = frequency_ratio for fret n relative to open string
    #   position = scale_length * (1 - 1/ratio)
    ratio_set_id: Optional[str] = Field(
        default=None,
        description="Named ratio set (JUST_MAJOR, PYTHAGOREAN, MEANTONE). Only used when intonation_model=custom_ratios.",
    )
    ratios: Optional[List[float]] = Field(
        default=None,
        description="Explicit per-fret frequency ratios (len == fret_count). Only used when intonation_model=custom_ratios.",
    )

    @model_validator(mode="after")
    def _validate_intonation(self):
        """Validate custom_ratios requirements."""
        if self.intonation_model != "custom_ratios":
            return self

        # custom_ratios requires ratio_set_id or ratios[]
        if not self.ratio_set_id and not self.ratios:
            raise ValueError("custom_ratios requires ratio_set_id or ratios[]")

        # Validate explicit ratios if provided
        if self.ratios is not None:
            if len(self.ratios) != self.fret_count:
                raise ValueError(f"ratios[] must have len == fret_count ({self.fret_count}), got {len(self.ratios)}")
            for i, r in enumerate(self.ratios):
                if r <= 1.0:
                    raise ValueError(f"ratios[{i}] must be > 1.0 for fretted notes, got {r}")

        return self

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
                "intonation_model": "equal_temperament_12",
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
