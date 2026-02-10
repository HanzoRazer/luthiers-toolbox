"""
Pydantic schemas for probe router.

Extracted from probe_router.py (Phase 13 decomposition).
"""
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class ProbePointIn(BaseModel):
    """Single probe point definition for custom patterns."""
    x: float
    y: float
    z: float
    label: str = ""


class CornerProbeIn(BaseModel):
    """Corner find pattern input."""
    pattern: Literal["corner_outside", "corner_inside"] = "corner_outside"
    approach_distance: float = Field(20.0, ge=5.0, le=50.0)
    retract_distance: float = Field(2.0, ge=0.5, le=10.0)
    feed_probe: float = Field(100.0, ge=10.0, le=500.0)
    safe_z: float = Field(10.0, ge=5.0, le=50.0)
    work_offset: int = Field(1, ge=1, le=6)


class BossProbeIn(BaseModel):
    """Boss/hole find pattern input."""
    pattern: Literal["boss_circular", "hole_circular"] = "boss_circular"
    estimated_diameter: float = Field(50.0, ge=5.0, le=500.0)
    estimated_center_x: float = Field(0.0)
    estimated_center_y: float = Field(0.0)
    probe_count: int = Field(4, ge=4, le=12)
    approach_distance: float = Field(5.0, ge=2.0, le=20.0)
    retract_distance: float = Field(5.0, ge=2.0, le=20.0)
    feed_probe: float = Field(100.0, ge=10.0, le=500.0)
    safe_z: float = Field(10.0, ge=5.0, le=50.0)
    work_offset: int = Field(1, ge=1, le=6)


class SurfaceZProbeIn(BaseModel):
    """Surface Z touch-off input."""
    approach_z: float = Field(10.0, ge=5.0, le=50.0)
    probe_depth: float = Field(-20.0, le=-5.0)
    feed_probe: float = Field(50.0, ge=10.0, le=200.0)
    retract_distance: float = Field(5.0, ge=2.0, le=20.0)
    work_offset: int = Field(1, ge=1, le=6)


class PocketProbeIn(BaseModel):
    """Pocket/inside corner find input."""
    pocket_width: float = Field(100.0, ge=10.0, le=500.0)
    pocket_height: float = Field(60.0, ge=10.0, le=500.0)
    approach_distance: float = Field(10.0, ge=5.0, le=50.0)
    retract_distance: float = Field(2.0, ge=0.5, le=10.0)
    feed_probe: float = Field(100.0, ge=10.0, le=500.0)
    safe_z: float = Field(10.0, ge=5.0, le=50.0)
    work_offset: int = Field(1, ge=1, le=6)
    origin_corner: Literal["lower_left", "lower_right", "upper_left", "upper_right", "center"] = "center"


class ViseSquareProbeIn(BaseModel):
    """Vise squareness check input."""
    vise_jaw_height: float = Field(50.0, ge=10.0, le=200.0)
    probe_spacing: float = Field(100.0, ge=50.0, le=300.0)
    approach_distance: float = Field(20.0, ge=5.0, le=50.0)
    retract_distance: float = Field(5.0, ge=2.0, le=20.0)
    feed_probe: float = Field(100.0, ge=10.0, le=500.0)
    safe_z: float = Field(10.0, ge=5.0, le=50.0)


class SetupSheetIn(BaseModel):
    """Setup sheet generation input."""
    pattern: Literal["corner_outside", "corner_inside", "boss_circular", "hole_circular", "pocket_inside", "surface_z"]
    part_width: Optional[float] = Field(100.0)
    part_height: Optional[float] = Field(60.0)
    feature_diameter: Optional[float] = Field(50.0)
    probe_offset: Optional[float] = Field(20.0)
    origin_corner: Optional[str] = Field("lower_left")


class ProbeOut(BaseModel):
    """Probe G-code output."""
    gcode: str
    stats: Dict[str, Any]
