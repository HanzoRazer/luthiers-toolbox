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
    CONCAVE = "concave"  # Concave dish (e.g., some bracing)
    FREEFORM = "freeform"  # Arbitrary 3D surface


class MaterialHardness(str, Enum):
    """Material hardness for feeds/speeds."""
    SOFT = "soft"  # Spruce, cedar, basswood
    MEDIUM = "medium"  # Maple, mahogany
    HARD = "hard"  # Ebony, rosewood


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

    def to_dict(self) -> dict:
        return {
            "grid_size": (self.grid_size_x, self.grid_size_y),
            "bounds_x_mm": self.bounds_x_mm,
            "bounds_y_mm": self.bounds_y_mm,
            "apex_thickness_mm": self.apex_thickness_mm,
            "edge_thickness_mm": self.edge_thickness_mm,
            "recurve_depth_mm": self.recurve_depth_mm,
            "surface_type": self.surface_type.value,
        }


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
