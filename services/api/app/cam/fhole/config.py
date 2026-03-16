# app/cam/fhole/config.py

"""
F-Hole Routing Configuration (BEN-GAP-09)

Configuration dataclasses for archtop F-hole routing operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Optional, Dict, Any


class FHoleStyle(str, Enum):
    """F-hole shape styles."""
    TRADITIONAL_ARCHTOP = "traditional_archtop"  # Classic violin/archtop shape
    CONTEMPORARY = "contemporary"  # Modern simplified curves
    VENETIAN = "venetian"  # Elongated with pointed tips


class PlungeStrategy(str, Enum):
    """Plunge entry strategy for interior cuts."""
    HELICAL = "helical"  # Spiral plunge at start point
    RAMP = "ramp"  # Ramped entry along first segment
    DRILL = "drill"  # Pre-drilled hole (requires separate operation)


@dataclass
class FHoleToolSpec:
    """Tool specification for F-hole routing."""

    tool_number: int = 1
    name: str = "1/8 inch Spiral Upcut"
    diameter_mm: float = 3.175  # 1/8" - common for F-holes
    flute_length_mm: float = 12.0
    shank_diameter_mm: float = 6.35

    # Feeds and speeds (conservative for carved spruce top)
    spindle_rpm: int = 18000
    feed_rate_mm_min: float = 800.0  # Reduced for tight curves
    plunge_rate_mm_min: float = 200.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_number": self.tool_number,
            "name": self.name,
            "diameter_mm": self.diameter_mm,
            "flute_length_mm": self.flute_length_mm,
            "spindle_rpm": self.spindle_rpm,
            "feed_rate_mm_min": self.feed_rate_mm_min,
            "plunge_rate_mm_min": self.plunge_rate_mm_min,
        }


@dataclass
class FHoleGeometryConfig:
    """
    Parametric F-hole geometry configuration.

    F-holes are traditionally shaped like elongated 'f' characters
    with curved upper and lower bouts connected by a narrow waist.
    """

    # Overall dimensions
    length_mm: float = 101.6  # 4" - Benedetto standard
    width_mm: float = 25.4  # 1" at widest point

    # Shape parameters
    style: FHoleStyle = FHoleStyle.TRADITIONAL_ARCHTOP

    # Bout proportions (as fraction of length)
    upper_bout_position: float = 0.2  # Distance from top to upper bout center
    lower_bout_position: float = 0.8  # Distance from top to lower bout center

    # Bout widths (as fraction of max width)
    upper_bout_width_ratio: float = 0.7
    lower_bout_width_ratio: float = 0.85
    waist_width_ratio: float = 0.3  # Narrow waist

    # Tip sharpness (0 = round, 1 = pointed)
    tip_sharpness: float = 0.6

    # Curve resolution
    points_per_curve: int = 24  # Higher = smoother

    def to_dict(self) -> Dict[str, Any]:
        return {
            "length_mm": self.length_mm,
            "width_mm": self.width_mm,
            "style": self.style.value,
            "upper_bout_position": self.upper_bout_position,
            "lower_bout_position": self.lower_bout_position,
            "upper_bout_width_ratio": self.upper_bout_width_ratio,
            "lower_bout_width_ratio": self.lower_bout_width_ratio,
            "waist_width_ratio": self.waist_width_ratio,
            "tip_sharpness": self.tip_sharpness,
            "points_per_curve": self.points_per_curve,
        }


@dataclass
class FHolePositionConfig:
    """
    F-hole positioning on the guitar body.

    Positions are relative to body center (0, 0) where:
    - X: positive = treble side (right), negative = bass side (left)
    - Y: positive = toward bridge, negative = toward neck
    """

    # X offset from centerline (distance to F-hole center)
    x_offset_mm: float = 65.0  # Typical archtop F-hole lateral position

    # Y offset from body center
    y_offset_mm: float = -20.0  # Slightly toward neck from body center

    # Rotation angle (degrees, positive = clockwise when viewed from top)
    rotation_deg: float = 8.0  # Slight outward tilt is traditional

    # Mirror for left/right F-holes
    mirror_x: bool = True  # True = symmetric pair

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x_offset_mm": self.x_offset_mm,
            "y_offset_mm": self.y_offset_mm,
            "rotation_deg": self.rotation_deg,
            "mirror_x": self.mirror_x,
        }


@dataclass
class FHoleRoutingConfig:
    """
    Complete configuration for F-hole routing operation.
    """

    # Geometry
    geometry: FHoleGeometryConfig = field(default_factory=FHoleGeometryConfig)
    position: FHolePositionConfig = field(default_factory=FHolePositionConfig)

    # Tool
    tool: FHoleToolSpec = field(default_factory=FHoleToolSpec)

    # Cut parameters
    top_thickness_mm: float = 7.0  # Carved top thickness at F-hole region
    cut_depth_mm: float = 8.0  # Through-cut (top thickness + margin)
    stepdown_mm: float = 2.0  # Depth per pass

    # Plunge strategy
    plunge_strategy: PlungeStrategy = PlungeStrategy.HELICAL
    helical_diameter_mm: float = 4.0  # For helical plunge
    helical_pitch_mm: float = 1.0  # Descent per revolution

    # Offsets and safety
    finish_allowance_mm: float = 0.1  # Leave for finish pass
    safe_z_mm: float = 10.0
    retract_z_mm: float = 3.0

    # Output
    output_units: str = "mm"  # "mm" or "inch"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "geometry": self.geometry.to_dict(),
            "position": self.position.to_dict(),
            "tool": self.tool.to_dict(),
            "top_thickness_mm": self.top_thickness_mm,
            "cut_depth_mm": self.cut_depth_mm,
            "stepdown_mm": self.stepdown_mm,
            "plunge_strategy": self.plunge_strategy.value,
            "safe_z_mm": self.safe_z_mm,
            "output_units": self.output_units,
        }


# Preset configurations
def create_benedetto_17_fhole_config() -> FHoleRoutingConfig:
    """Create configuration for Benedetto 17" archtop F-holes."""
    return FHoleRoutingConfig(
        geometry=FHoleGeometryConfig(
            length_mm=101.6,  # 4"
            width_mm=25.4,  # 1"
            style=FHoleStyle.TRADITIONAL_ARCHTOP,
            tip_sharpness=0.65,
        ),
        position=FHolePositionConfig(
            x_offset_mm=65.0,
            y_offset_mm=-20.0,
            rotation_deg=8.0,
        ),
        tool=FHoleToolSpec(
            diameter_mm=3.175,  # 1/8" for detail
            spindle_rpm=18000,
            feed_rate_mm_min=800.0,
        ),
        top_thickness_mm=7.0,
        cut_depth_mm=8.5,  # Through-cut with margin
        stepdown_mm=2.0,
    )


def create_les_paul_fhole_config() -> FHoleRoutingConfig:
    """Create configuration for Les Paul f-hole style (if applicable)."""
    # Les Paul typically doesn't have F-holes, but ES-335 does
    return FHoleRoutingConfig(
        geometry=FHoleGeometryConfig(
            length_mm=115.0,  # ES-335 style, slightly longer
            width_mm=28.0,
            style=FHoleStyle.TRADITIONAL_ARCHTOP,
            tip_sharpness=0.5,  # Rounder tips than Benedetto
        ),
        position=FHolePositionConfig(
            x_offset_mm=70.0,
            y_offset_mm=-15.0,
            rotation_deg=5.0,
        ),
        tool=FHoleToolSpec(
            diameter_mm=3.175,
            spindle_rpm=16000,
            feed_rate_mm_min=700.0,
        ),
        top_thickness_mm=6.0,  # Laminate top
        cut_depth_mm=7.0,
        stepdown_mm=1.5,
    )


def create_jumbo_archtop_fhole_config() -> FHoleRoutingConfig:
    """Create configuration for larger jumbo archtop F-holes."""
    return FHoleRoutingConfig(
        geometry=FHoleGeometryConfig(
            length_mm=110.0,
            width_mm=28.0,
            style=FHoleStyle.TRADITIONAL_ARCHTOP,
            tip_sharpness=0.6,
        ),
        position=FHolePositionConfig(
            x_offset_mm=75.0,  # Wider body
            y_offset_mm=-25.0,
            rotation_deg=10.0,
        ),
        top_thickness_mm=7.5,
        cut_depth_mm=9.0,
        stepdown_mm=2.0,
    )
