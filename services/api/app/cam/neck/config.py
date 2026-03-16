# app/cam/neck/config.py

"""
Neck CNC Pipeline Configuration (LP-GAP-03)

Configuration dataclasses for neck machining operations.
All dimensions in millimeters for consistency with unified coordinate system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
from enum import Enum


class NeckProfileType(str, Enum):
    """Neck profile cross-section shapes."""
    C_SHAPE = "c_shape"
    D_SHAPE = "d_shape"
    V_SHAPE = "v_shape"
    U_SHAPE = "u_shape"
    ASYMMETRIC = "asymmetric"
    COMPOUND = "compound"  # Changes from V at nut to C at heel


class MaterialType(str, Enum):
    """Material types for feeds/speeds."""
    MAPLE = "maple"
    MAHOGANY = "mahogany"
    ROSEWOOD = "rosewood"
    EBONY = "ebony"
    WALNUT = "walnut"


@dataclass
class NeckToolSpec:
    """Tool specification for neck operations."""
    tool_number: int
    name: str
    diameter_mm: float
    type: Literal["ball_end", "flat_end", "drill", "slot"]
    flute_count: int = 2
    rpm: int = 18000
    feed_mm_min: float = 1000.0
    plunge_mm_min: float = 500.0
    stepdown_mm: float = 3.0
    stepover_percent: float = 40.0  # For profile carving

    @property
    def stepover_mm(self) -> float:
        return self.diameter_mm * (self.stepover_percent / 100)

    def to_dict(self) -> dict:
        return {
            "tool_number": self.tool_number,
            "name": self.name,
            "diameter_mm": self.diameter_mm,
            "type": self.type,
            "rpm": self.rpm,
            "feed_mm_min": self.feed_mm_min,
            "stepdown_mm": self.stepdown_mm,
        }


# Default tool library for neck operations
DEFAULT_NECK_TOOLS: Dict[int, NeckToolSpec] = {
    1: NeckToolSpec(
        tool_number=1,
        name="1/4\" Ball End - Profile Rough",
        diameter_mm=6.35,
        type="ball_end",
        rpm=18000,
        feed_mm_min=1200.0,
        plunge_mm_min=600.0,
        stepdown_mm=3.0,
        stepover_percent=40.0,
    ),
    2: NeckToolSpec(
        tool_number=2,
        name="1/8\" Flat End - Truss Rod",
        diameter_mm=3.175,
        type="flat_end",
        rpm=20000,
        feed_mm_min=800.0,
        plunge_mm_min=400.0,
        stepdown_mm=2.0,
    ),
    3: NeckToolSpec(
        tool_number=3,
        name="3/8\" Ball End - Profile Finish",
        diameter_mm=9.525,
        type="ball_end",
        rpm=16000,
        feed_mm_min=1500.0,
        plunge_mm_min=500.0,
        stepdown_mm=1.5,
        stepover_percent=15.0,
    ),
    4: NeckToolSpec(
        tool_number=4,
        name="Fret Slot Saw - 0.023\"",
        diameter_mm=0.584,  # 0.023"
        type="slot",
        rpm=10000,
        feed_mm_min=300.0,
        plunge_mm_min=150.0,
        stepdown_mm=1.0,
    ),
}


@dataclass
class TrussRodConfig:
    """Configuration for truss rod channel routing."""
    width_mm: float = 6.35  # 1/4" standard
    depth_mm: float = 9.525  # 3/8" standard
    length_mm: float = 406.4  # 16" standard (nut to ~12th fret area)
    start_offset_mm: float = 12.7  # 1/2" from nut
    access_pocket_width_mm: float = 12.7  # Wider at nut end for adjustment
    access_pocket_length_mm: float = 25.4  # 1" access pocket

    def to_dict(self) -> dict:
        return {
            "width_mm": self.width_mm,
            "depth_mm": self.depth_mm,
            "length_mm": self.length_mm,
            "start_offset_mm": self.start_offset_mm,
        }


@dataclass
class ProfileCarvingConfig:
    """Configuration for neck profile carving."""
    profile_type: NeckProfileType = NeckProfileType.C_SHAPE
    depth_at_nut_mm: float = 20.0  # Neck depth at nut
    depth_at_12th_mm: float = 22.0  # Neck depth at 12th fret
    depth_at_heel_mm: float = 25.0  # Neck depth at heel
    nut_width_mm: float = 43.0
    heel_width_mm: float = 56.0
    finish_allowance_mm: float = 0.75  # 0.030" for sanding
    station_interval_mm: float = 50.8  # 2" between profile stations
    extend_past_heel_mm: float = 25.4  # 1" past heel for blending

    def to_dict(self) -> dict:
        return {
            "profile_type": self.profile_type.value,
            "depth_at_nut_mm": self.depth_at_nut_mm,
            "depth_at_12th_mm": self.depth_at_12th_mm,
            "depth_at_heel_mm": self.depth_at_heel_mm,
            "finish_allowance_mm": self.finish_allowance_mm,
            "station_interval_mm": self.station_interval_mm,
        }


@dataclass
class FretSlotConfig:
    """Configuration for fret slot cutting."""
    slot_width_mm: float = 0.584  # 0.023" standard
    slot_depth_mm: float = 3.5  # Depth into fretboard
    fretboard_thickness_mm: float = 6.35  # 1/4" standard
    fret_count: int = 22
    compound_radius: bool = False
    radius_at_nut_mm: float = 254.0  # 10" radius
    radius_at_heel_mm: float = 406.4  # 16" radius

    def to_dict(self) -> dict:
        return {
            "slot_width_mm": self.slot_width_mm,
            "slot_depth_mm": self.slot_depth_mm,
            "fret_count": self.fret_count,
            "compound_radius": self.compound_radius,
        }


@dataclass
class NeckPipelineConfig:
    """
    Complete neck CNC pipeline configuration.

    Dimensions in millimeters for compatibility with unified coordinate system.
    Y=0 is nut centerline, +Y toward bridge (per VINE-05).
    """
    # Core dimensions
    scale_length_mm: float = 628.65  # Les Paul 24.75"
    fret_count: int = 22

    # Neck profile
    profile_type: NeckProfileType = NeckProfileType.C_SHAPE

    # Neck dimensions
    nut_width_mm: float = 43.0
    heel_width_mm: float = 56.0
    depth_at_nut_mm: float = 20.0
    depth_at_12th_mm: float = 22.0
    depth_at_heel_mm: float = 25.0

    # Body joint position (Y coordinate where neck meets body)
    body_joint_y_mm: float = 0.0  # Calculated from fret_count if 0

    # Sub-configurations
    truss_rod: TrussRodConfig = field(default_factory=TrussRodConfig)
    profile_carving: ProfileCarvingConfig = field(default_factory=ProfileCarvingConfig)
    fret_slots: FretSlotConfig = field(default_factory=FretSlotConfig)

    # Tool library
    tools: Dict[int, NeckToolSpec] = field(default_factory=lambda: DEFAULT_NECK_TOOLS.copy())

    # Material for feeds/speeds
    material: MaterialType = MaterialType.MAPLE

    # Output options
    output_units: Literal["mm", "inch"] = "mm"
    include_fret_slots: bool = True
    include_binding_channel: bool = False  # Future enhancement

    def __post_init__(self):
        # Sync sub-config values from main config
        self.profile_carving.profile_type = self.profile_type
        self.profile_carving.depth_at_nut_mm = self.depth_at_nut_mm
        self.profile_carving.depth_at_12th_mm = self.depth_at_12th_mm
        self.profile_carving.depth_at_heel_mm = self.depth_at_heel_mm
        self.profile_carving.nut_width_mm = self.nut_width_mm
        self.profile_carving.heel_width_mm = self.heel_width_mm

        self.fret_slots.fret_count = self.fret_count

        # Calculate body joint position from fret count if not set
        if self.body_joint_y_mm == 0:
            # Body joint is typically at 16th fret for 22-fret, 14th for 19-fret
            joint_fret = min(16, self.fret_count - 6)
            self.body_joint_y_mm = self._fret_position(joint_fret)

    def _fret_position(self, fret_number: int) -> float:
        """Calculate fret position in mm from nut using 12-TET formula."""
        if fret_number <= 0:
            return 0.0
        return self.scale_length_mm * (1 - (1 / (2 ** (fret_number / 12))))

    def get_station_y_positions(self) -> List[float]:
        """
        Generate Y positions for profile carving stations.

        Extends from nut (Y=0) through heel to body joint, with configurable interval.
        This resolves the "12-inch limit" problem by generating stations for full length.
        """
        stations = []
        y = 0.0
        interval = self.profile_carving.station_interval_mm
        end_y = self.body_joint_y_mm + self.profile_carving.extend_past_heel_mm

        while y <= end_y:
            stations.append(y)
            y += interval

        # Always include body joint position
        if self.body_joint_y_mm not in stations:
            stations.append(self.body_joint_y_mm)
            stations.sort()

        return stations

    def to_dict(self) -> dict:
        return {
            "scale_length_mm": self.scale_length_mm,
            "fret_count": self.fret_count,
            "profile_type": self.profile_type.value,
            "nut_width_mm": self.nut_width_mm,
            "heel_width_mm": self.heel_width_mm,
            "body_joint_y_mm": round(self.body_joint_y_mm, 2),
            "truss_rod": self.truss_rod.to_dict(),
            "profile_carving": self.profile_carving.to_dict(),
            "fret_slots": self.fret_slots.to_dict(),
            "material": self.material.value,
            "output_units": self.output_units,
        }


# =============================================================================
# PRESETS
# =============================================================================

def create_lespaul_config() -> NeckPipelineConfig:
    """Create Les Paul neck configuration."""
    return NeckPipelineConfig(
        scale_length_mm=628.65,  # 24.75"
        fret_count=22,
        profile_type=NeckProfileType.C_SHAPE,
        nut_width_mm=43.0,  # 1.695"
        heel_width_mm=54.0,
        depth_at_nut_mm=20.32,  # 0.800"
        depth_at_12th_mm=22.86,  # 0.900"
        depth_at_heel_mm=25.4,  # 1.000"
        material=MaterialType.MAHOGANY,
    )


def create_strat_config() -> NeckPipelineConfig:
    """Create Stratocaster neck configuration."""
    return NeckPipelineConfig(
        scale_length_mm=647.7,  # 25.5"
        fret_count=22,
        profile_type=NeckProfileType.C_SHAPE,
        nut_width_mm=42.86,  # 1.6875"
        heel_width_mm=56.0,
        depth_at_nut_mm=20.07,  # 0.790"
        depth_at_12th_mm=22.1,  # 0.870"
        depth_at_heel_mm=24.13,  # 0.950"
        material=MaterialType.MAPLE,
    )


def create_classical_config() -> NeckPipelineConfig:
    """Create classical guitar neck configuration."""
    return NeckPipelineConfig(
        scale_length_mm=650.0,  # 25.6"
        fret_count=19,
        profile_type=NeckProfileType.D_SHAPE,
        nut_width_mm=52.0,
        heel_width_mm=62.0,
        depth_at_nut_mm=22.0,
        depth_at_12th_mm=24.0,
        depth_at_heel_mm=26.0,
        material=MaterialType.MAHOGANY,
    )
