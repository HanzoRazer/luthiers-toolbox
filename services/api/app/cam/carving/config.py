# app/cam/carving/config.py

"""
3D Surface Carving Configuration (BEN-GAP-08)

Configuration dataclasses for archtop top/back carving operations.
Supports graduated thickness carving from thickness maps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal, Tuple
from enum import Enum


class CarvingStrategy(str, Enum):
    """Toolpath strategy for 3D surface carving."""
    PARALLEL_PLANE = "parallel_plane"  # Horizontal slices at Z levels
    RASTER_X = "raster_x"  # Back-and-forth along X axis
    RASTER_Y = "raster_y"  # Back-and-forth along Y axis
    SPIRAL = "spiral"  # Spiral inward from perimeter
    CONTOUR_FOLLOW = "contour_follow"  # Follow thickness contours


class SurfaceType(str, Enum):
    """Type of carved surface."""
    ARCHTOP = "archtop"  # Convex domed surface (guitar top/back)
    ARCHTOP_ASYMMETRIC = "archtop_asymmetric"  # Asymmetric carved top (LP-GAP-05)
    CONCAVE = "concave"  # Concave dish (e.g., some bracing)
    FREEFORM = "freeform"  # Arbitrary 3D surface


class MaterialHardness(str, Enum):
    """Material hardness for feeds/speeds."""
    SOFT = "soft"  # Spruce, cedar, basswood
    MEDIUM = "medium"  # Maple, mahogany
    HARD = "hard"  # Ebony, rosewood


@dataclass
class AsymmetricCarveProfile:
    """
    Asymmetric carved top profile configuration (LP-GAP-05).

    Captures authentic 1959 Les Paul carved top characteristics:
    - Peak offset from center (typically toward neck)
    - Compound radius (different X and Y radii)
    - Variable slopes across different zones
    - Binding ledge at perimeter

    Based on measurements from Les-Paul-Isolines.pdf and
    Les-Paul-Front-Front-Side-Profile-Carved-Top.pdf.
    """
    # Peak position offset from center (mm)
    peak_offset_x_mm: float = 0.0  # Offset along width (typically 0)
    peak_offset_y_mm: float = 30.0  # Offset toward neck (~30mm for 1959 LP)

    # Compound radius (elliptical dome)
    major_radius_mm: float = 508.0  # 20" across width
    minor_radius_mm: float = 381.0  # 15" along length

    # Surface heights
    total_rise_mm: float = 7.8  # Height from binding to peak

    # Variable slope zones (degrees)
    slope_crown_deg: float = 1.5  # Gentle slope at crown
    slope_average_deg: float = 3.2  # Average slope
    slope_cutaway_deg: float = 6.0  # Steeper at cutaway transitions
    slope_lower_bout_deg: float = 4.5  # Lower bout slope

    # Zone boundaries (normalized 0-1)
    crown_zone_radius: float = 0.3  # Central crown zone
    cutaway_zone_x_min: float = 0.5  # X threshold for cutaway zone
    cutaway_zone_y_max: float = 0.7  # Y threshold for cutaway zone

    # Edge treatment
    binding_ledge_mm: float = 1.5  # Flat ledge at perimeter for binding

    def to_dict(self) -> dict:
        return {
            "peak_offset_mm": (self.peak_offset_x_mm, self.peak_offset_y_mm),
            "compound_radius_mm": (self.major_radius_mm, self.minor_radius_mm),
            "total_rise_mm": self.total_rise_mm,
            "slopes_deg": {
                "crown": self.slope_crown_deg,
                "average": self.slope_average_deg,
                "cutaway": self.slope_cutaway_deg,
                "lower_bout": self.slope_lower_bout_deg,
            },
            "binding_ledge_mm": self.binding_ledge_mm,
        }


@dataclass
class CarvingToolSpec:
    """Tool specification for carving operations."""
    tool_number: int
    name: str
    diameter_mm: float
    type: Literal["ball_end", "bull_nose", "flat_end"]
    corner_radius_mm: float = 0.0  # For bull nose
    flute_count: int = 2
    rpm: int = 18000
    feed_mm_min: float = 1500.0
    plunge_mm_min: float = 500.0
    stepdown_mm: float = 2.0
    stepover_percent: float = 30.0  # Percentage of diameter

    @property
    def stepover_mm(self) -> float:
        return self.diameter_mm * (self.stepover_percent / 100)

    @property
    def effective_radius_mm(self) -> float:
        """Effective cutting radius for ball/bull nose."""
        if self.type == "ball_end":
            return self.diameter_mm / 2
        elif self.type == "bull_nose":
            return self.corner_radius_mm
        else:
            return 0.0

    def to_dict(self) -> dict:
        return {
            "tool_number": self.tool_number,
            "name": self.name,
            "diameter_mm": self.diameter_mm,
            "type": self.type,
            "rpm": self.rpm,
            "feed_mm_min": self.feed_mm_min,
            "stepdown_mm": self.stepdown_mm,
            "stepover_mm": self.stepover_mm,
        }


# Default tool library for carving operations
DEFAULT_CARVING_TOOLS: Dict[int, CarvingToolSpec] = {
    1: CarvingToolSpec(
        tool_number=1,
        name="1/2\" Ball End - Roughing",
        diameter_mm=12.7,
        type="ball_end",
        rpm=16000,
        feed_mm_min=2000.0,
        plunge_mm_min=800.0,
        stepdown_mm=4.0,
        stepover_percent=40.0,
    ),
    2: CarvingToolSpec(
        tool_number=2,
        name="1/4\" Ball End - Semi-Finish",
        diameter_mm=6.35,
        type="ball_end",
        rpm=18000,
        feed_mm_min=1500.0,
        plunge_mm_min=600.0,
        stepdown_mm=2.0,
        stepover_percent=25.0,
    ),
    3: CarvingToolSpec(
        tool_number=3,
        name="1/8\" Ball End - Finish",
        diameter_mm=3.175,
        type="ball_end",
        rpm=20000,
        feed_mm_min=1200.0,
        plunge_mm_min=400.0,
        stepdown_mm=1.0,
        stepover_percent=10.0,
    ),
    4: CarvingToolSpec(
        tool_number=4,
        name="3/8\" Bull Nose - Rough/Finish",
        diameter_mm=9.525,
        type="bull_nose",
        corner_radius_mm=3.175,
        rpm=17000,
        feed_mm_min=1800.0,
        plunge_mm_min=700.0,
        stepdown_mm=3.0,
        stepover_percent=20.0,
    ),
}


@dataclass
class GraduationMapConfig:
    """Configuration for graduation thickness map."""
    # Grid dimensions
    grid_size_x: int = 64  # Points along X
    grid_size_y: int = 64  # Points along Y

    # Physical bounds (mm)
    bounds_x_mm: Tuple[float, float] = (-250.0, 250.0)  # Min, max X
    bounds_y_mm: Tuple[float, float] = (-200.0, 200.0)  # Min, max Y

    # Thickness reference
    apex_thickness_mm: float = 7.0  # Maximum thickness at dome apex
    edge_thickness_mm: float = 3.5  # Minimum at perimeter
    recurve_depth_mm: float = 1.5  # Depth of edge recurve (archtop only)

    # Surface properties
    surface_type: SurfaceType = SurfaceType.ARCHTOP
    reference_plane_z_mm: float = 0.0  # Z of flat reference plane

    # Asymmetric profile (LP-GAP-05)
    asymmetric_profile: Optional[AsymmetricCarveProfile] = None

    def to_dict(self) -> dict:
        result = {
            "grid_size": (self.grid_size_x, self.grid_size_y),
            "bounds_x_mm": self.bounds_x_mm,
            "bounds_y_mm": self.bounds_y_mm,
            "apex_thickness_mm": self.apex_thickness_mm,
            "edge_thickness_mm": self.edge_thickness_mm,
            "recurve_depth_mm": self.recurve_depth_mm,
            "surface_type": self.surface_type.value,
        }
        if self.asymmetric_profile:
            result["asymmetric_profile"] = self.asymmetric_profile.to_dict()
        return result


@dataclass
class RoughingConfig:
    """Configuration for roughing passes."""
    stepdown_mm: float = 4.0  # Z depth per pass
    stepover_percent: float = 40.0  # Tool overlap
    finish_allowance_mm: float = 1.0  # Stock left for finishing
    strategy: CarvingStrategy = CarvingStrategy.PARALLEL_PLANE
    climb_milling: bool = True
    ramp_angle_deg: float = 15.0  # Helix ramp entry angle

    def to_dict(self) -> dict:
        return {
            "stepdown_mm": self.stepdown_mm,
            "stepover_percent": self.stepover_percent,
            "finish_allowance_mm": self.finish_allowance_mm,
            "strategy": self.strategy.value,
            "climb_milling": self.climb_milling,
        }


@dataclass
class FinishingConfig:
    """Configuration for finishing passes."""
    stepover_percent: float = 10.0  # Tight overlap for smooth surface
    scallop_height_mm: float = 0.05  # Target surface finish quality
    strategy: CarvingStrategy = CarvingStrategy.RASTER_X
    climb_milling: bool = True
    spring_passes: int = 0  # Extra light passes for deflection

    def to_dict(self) -> dict:
        return {
            "stepover_percent": self.stepover_percent,
            "scallop_height_mm": self.scallop_height_mm,
            "strategy": self.strategy.value,
            "spring_passes": self.spring_passes,
        }


@dataclass
class CarvingConfig:
    """Complete configuration for 3D surface carving."""
    # Graduation map
    graduation_map: GraduationMapConfig = field(default_factory=GraduationMapConfig)

    # Pass configurations
    roughing: RoughingConfig = field(default_factory=RoughingConfig)
    finishing: FinishingConfig = field(default_factory=FinishingConfig)

    # Tools
    tools: Dict[int, CarvingToolSpec] = field(
        default_factory=lambda: DEFAULT_CARVING_TOOLS.copy()
    )
    rough_tool_number: int = 1
    finish_tool_number: int = 3

    # Stock
    stock_thickness_mm: float = 25.0  # Initial blank thickness
    stock_allowance_mm: float = 2.0  # Safety margin from workholding

    # Material
    material: MaterialHardness = MaterialHardness.SOFT  # Spruce default

    # Machine limits
    safe_z_mm: float = 50.0
    retract_z_mm: float = 10.0

    # Output
    output_units: Literal["mm", "inch"] = "mm"

    def to_dict(self) -> dict:
        return {
            "graduation_map": self.graduation_map.to_dict(),
            "roughing": self.roughing.to_dict(),
            "finishing": self.finishing.to_dict(),
            "stock_thickness_mm": self.stock_thickness_mm,
            "material": self.material.value,
            "rough_tool": self.tools[self.rough_tool_number].to_dict()
            if self.rough_tool_number in self.tools else None,
            "finish_tool": self.tools[self.finish_tool_number].to_dict()
            if self.finish_tool_number in self.tools else None,
        }


# =============================================================================
# PRESETS
# =============================================================================

def create_benedetto_17_config() -> CarvingConfig:
    """Create Benedetto 17" archtop carving configuration."""
    return CarvingConfig(
        graduation_map=GraduationMapConfig(
            grid_size_x=64,
            grid_size_y=64,
            bounds_x_mm=(-215.9, 215.9),  # 17" = 431.8mm width
            bounds_y_mm=(-254.0, 254.0),  # ~20" length
            apex_thickness_mm=7.0,
            edge_thickness_mm=3.5,
            recurve_depth_mm=1.5,
            surface_type=SurfaceType.ARCHTOP,
        ),
        roughing=RoughingConfig(
            stepdown_mm=4.0,
            stepover_percent=40.0,
            finish_allowance_mm=1.0,
            strategy=CarvingStrategy.PARALLEL_PLANE,
        ),
        finishing=FinishingConfig(
            stepover_percent=10.0,
            scallop_height_mm=0.05,
            strategy=CarvingStrategy.RASTER_X,
        ),
        stock_thickness_mm=25.4,  # 1" blank
        material=MaterialHardness.SOFT,  # Spruce top
    )


def create_les_paul_top_config() -> CarvingConfig:
    """Create Les Paul carved maple top configuration."""
    return CarvingConfig(
        graduation_map=GraduationMapConfig(
            grid_size_x=48,
            grid_size_y=64,
            bounds_x_mm=(-165.0, 165.0),  # ~13" width
            bounds_y_mm=(-220.0, 220.0),  # ~17" length
            apex_thickness_mm=19.05,  # 3/4" at center
            edge_thickness_mm=12.7,  # 1/2" at edge
            recurve_depth_mm=0.0,  # No recurve on Les Paul
            surface_type=SurfaceType.ARCHTOP,
        ),
        roughing=RoughingConfig(
            stepdown_mm=3.0,
            stepover_percent=35.0,
            finish_allowance_mm=0.75,
            strategy=CarvingStrategy.PARALLEL_PLANE,
        ),
        finishing=FinishingConfig(
            stepover_percent=12.0,
            scallop_height_mm=0.08,
            strategy=CarvingStrategy.RASTER_Y,
        ),
        stock_thickness_mm=22.0,  # ~7/8" blank
        material=MaterialHardness.MEDIUM,  # Maple
    )


def create_les_paul_1959_asymmetric_config() -> CarvingConfig:
    """
    Create 1959 Les Paul asymmetric carved maple top configuration (LP-GAP-05).

    This preset captures the authentic 1959 carved top profile:
    - Peak offset ~30mm toward neck
    - Compound radius (508mm major / 381mm minor)
    - Variable slope: 1.5 deg at crown, 6 deg at cutaway transitions
    - Total rise 7.8mm from binding to peak

    Based on measurements from:
    - Les-Paul-Isolines.pdf
    - Les-Paul-Front-Front-Side-Profile-Carved-Top.pdf
    """
    return CarvingConfig(
        graduation_map=GraduationMapConfig(
            grid_size_x=64,
            grid_size_y=80,
            bounds_x_mm=(-165.0, 165.0),  # ~13" width
            bounds_y_mm=(-222.0, 222.0),  # ~17.5" length
            apex_thickness_mm=12.7,  # 1/2" at peak
            edge_thickness_mm=5.0,  # ~3/16" at binding
            recurve_depth_mm=0.0,  # No recurve on Les Paul
            surface_type=SurfaceType.ARCHTOP_ASYMMETRIC,
            asymmetric_profile=AsymmetricCarveProfile(
                peak_offset_x_mm=0.0,
                peak_offset_y_mm=30.0,  # Peak 30mm toward neck
                major_radius_mm=508.0,  # 20" across width
                minor_radius_mm=381.0,  # 15" along length
                total_rise_mm=7.8,
                slope_crown_deg=1.5,
                slope_average_deg=3.2,
                slope_cutaway_deg=6.0,
                slope_lower_bout_deg=4.5,
                crown_zone_radius=0.3,
                cutaway_zone_x_min=0.5,
                cutaway_zone_y_max=0.7,
                binding_ledge_mm=1.5,
            ),
        ),
        roughing=RoughingConfig(
            stepdown_mm=2.5,
            stepover_percent=30.0,
            finish_allowance_mm=0.75,
            strategy=CarvingStrategy.PARALLEL_PLANE,
        ),
        finishing=FinishingConfig(
            stepover_percent=8.0,
            scallop_height_mm=0.05,
            strategy=CarvingStrategy.RASTER_Y,
        ),
        stock_thickness_mm=19.05,  # 3/4" blank
        material=MaterialHardness.MEDIUM,  # Maple
    )
