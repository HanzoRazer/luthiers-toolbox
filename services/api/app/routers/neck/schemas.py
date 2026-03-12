"""
Neck router schemas - shared Pydantic models.

Extracted from neck_router.py for reuse across sub-routers.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Point2D(BaseModel):
    """2D point for geometry output."""
    x: float
    y: float


class NeckParameters(BaseModel):
    """Les Paul neck generation parameters."""
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
    """Generated neck geometry output."""
    profile_points: List[Point2D]
    fretboard_points: Optional[List[Point2D]] = None
    fret_positions: List[float]  # Distance from nut
    headstock_points: List[Point2D]
    tuner_holes: List[Point2D]
    centerline: List[Point2D]
    units: str
    scale_length: float


class StratNeckParameters(BaseModel):
    """Stratocaster neck generation parameters."""
    variant: Literal["vintage", "modern", "24fret"] = Field(
        "modern", description="Preset variant: 'vintage' (pre-CBS), 'modern' (American Standard), or '24fret' (extended range)"
    )
    scale_length: Optional[float] = Field(None, description="Scale length override (in)")
    nut_width: Optional[float] = Field(None, description="Nut width override (in)")
    num_frets: int = Field(22, description="Number of frets")
    include_fretboard: bool = Field(True, description="Include fretboard geometry")
    units: Literal["mm", "in"] = Field("in", description="Output units")


class TeleNeckParameters(BaseModel):
    """Telecaster neck generation parameters."""
    variant: Literal["vintage", "modern"] = Field(
        "modern", description="Preset variant: vintage (50s) or modern (American)"
    )
    scale_length: Optional[float] = Field(None, description="Scale length override (in)")
    nut_width: Optional[float] = Field(None, description="Nut width override (in)")
    num_frets: int = Field(22, description="Number of frets")
    include_fretboard: bool = Field(True, description="Include fretboard geometry")
    units: Literal["mm", "in"] = Field("in", description="Output units")


class PRSNeckParameters(BaseModel):
    """PRS neck generation parameters."""
    scale_length: float = Field(25.0, description="Scale length (in)")
    nut_width: float = Field(1.6875, description="Nut width (in)")
    num_frets: int = Field(24, description="Number of frets")
    include_fretboard: bool = Field(True, description="Include fretboard geometry")
    units: Literal["mm", "in"] = Field("in", description="Output units")


class NeckGcodeRequest(BaseModel):
    """Request for neck G-code generation."""
    preset: Optional[str] = Field(
        None, description="Preset name (gibson_standard, fender_vintage, fender_modern, prs)"
    )
    headstock_style: str = Field(
        "paddle", description="Headstock style: gibson_open, gibson_solid, fender_strat, fender_tele, prs, classical, martin, benedetto, paddle"
    )
    profile: str = Field(
        "c", description="Neck profile: c, d, v, u, asymmetric, compound"
    )
    scale_length: Optional[float] = Field(None, description="Scale length override (in)")
    nut_width: Optional[float] = Field(None, description="Nut width override (in)")
    heel_width: Optional[float] = Field(None, description="Heel width override (in)")
    job_name: str = Field("Neck_Program", description="Job name in G-code header")


class NeckGcodeResponse(BaseModel):
    """Response with generated neck G-code."""
    gcode: str
    line_count: int
    operations: List[dict]
    headstock_style: str
    profile: str
    scale_length: float
    nut_width: float
