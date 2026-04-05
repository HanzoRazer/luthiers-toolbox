# app/cam/machines.py

"""
CNC Machine Specification Module

Defines BCamMachineSpec for machine-specific parameters that affect
G-code generation, travel limits, and safety constraints.

Usage:
    from app.cam.machines import BCamMachineSpec, MACHINE_PRESETS

    # Use a preset
    machine = MACHINE_PRESETS["shapeoko_xxl"]

    # Or create custom
    machine = BCamMachineSpec(
        machine_id="custom_router",
        travel_x_mm=800,
        travel_y_mm=800,
        travel_z_mm=120,
        max_spindle_rpm=24000,
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Literal


class ControllerType(str, Enum):
    """CNC controller types."""
    GRBL = "GRBL"
    MACH3 = "Mach3"
    MACH4 = "Mach4"
    LINUXCNC = "LinuxCNC"
    HAAS = "Haas"
    FANUC = "Fanuc"
    CENTROID = "Centroid"


class SpindleType(str, Enum):
    """Spindle motor types."""
    ROUTER = "router"           # Trim router (Makita, DeWalt)
    VFD_SPINDLE = "vfd"         # VFD-controlled spindle
    SERVO_SPINDLE = "servo"     # Servo spindle with orient
    AIR_SPINDLE = "air"         # Air-powered spindle


@dataclass
class BCamMachineSpec:
    """
    CNC machine specification for CAM generation.

    Defines physical limits, controller type, and capabilities that
    affect G-code output and safety validation.

    Attributes:
        machine_id: Unique identifier for this machine configuration
        name: Human-readable machine name
        controller: Controller type (affects G-code dialect)

        # Travel limits
        travel_x_mm: X-axis travel (mm)
        travel_y_mm: Y-axis travel (mm)
        travel_z_mm: Z-axis travel (mm)

        # Spindle
        spindle_type: Type of spindle
        min_spindle_rpm: Minimum spindle RPM
        max_spindle_rpm: Maximum spindle RPM
        spindle_ramp_time_ms: Time for spindle to reach speed

        # Feed rates
        max_feed_xy_mm_min: Maximum XY feed rate (mm/min)
        max_feed_z_mm_min: Maximum Z feed rate (mm/min)
        rapid_feed_mm_min: Rapid traverse rate (mm/min)

        # Safety
        safe_z_mm: Default safe Z height
        work_z_min_mm: Minimum working Z (e.g., -50 for spoilboard)
        home_on_start: Whether machine homes on startup
        soft_limits: Whether soft limits are enabled

        # Tool changer
        has_atc: Automatic tool changer present
        max_tools: Number of tool positions
        tool_change_position: XYZ for tool change (if manual)

        # Probing
        has_probe: Touch probe installed
        probe_feed_mm_min: Probing feed rate
    """
    machine_id: str
    name: str = ""
    controller: ControllerType = ControllerType.GRBL

    # Travel limits
    travel_x_mm: float = 400.0
    travel_y_mm: float = 400.0
    travel_z_mm: float = 80.0

    # Spindle
    spindle_type: SpindleType = SpindleType.ROUTER
    min_spindle_rpm: int = 8000
    max_spindle_rpm: int = 24000
    spindle_ramp_time_ms: int = 2000

    # Feed rates
    max_feed_xy_mm_min: float = 5000.0
    max_feed_z_mm_min: float = 2000.0
    rapid_feed_mm_min: float = 8000.0

    # Safety
    safe_z_mm: float = 25.0
    work_z_min_mm: float = -25.0
    home_on_start: bool = True
    soft_limits: bool = True

    # Tool changer
    has_atc: bool = False
    max_tools: int = 1
    tool_change_position: Optional[tuple] = None  # (x, y, z)

    # Probing
    has_probe: bool = False
    probe_feed_mm_min: float = 100.0

    # Aliases for router compatibility
    @property
    def max_x_mm(self) -> float:
        return self.travel_x_mm

    @property
    def max_y_mm(self) -> float:
        return self.travel_y_mm

    @property
    def max_z_mm(self) -> float:
        return self.travel_z_mm

    @property
    def max_rpm(self) -> int:
        return self.max_spindle_rpm

    @property
    def max_feed_xy(self) -> float:
        return self.max_feed_xy_mm_min

    @property
    def label(self) -> str:
        return self.name or self.machine_id

    @property
    def post_dialect(self) -> str:
        return self.controller.value

    def validate_position(self, x: float, y: float, z: float) -> bool:
        """Check if position is within machine travel limits."""
        if x < 0 or x > self.travel_x_mm:
            return False
        if y < 0 or y > self.travel_y_mm:
            return False
        if z < self.work_z_min_mm or z > self.travel_z_mm:
            return False
        return True

    def validate_spindle_rpm(self, rpm: int) -> int:
        """Clamp RPM to valid range, return clamped value."""
        return max(self.min_spindle_rpm, min(self.max_spindle_rpm, rpm))

    def validate_feed_rate(self, feed: float, is_z: bool = False) -> float:
        """Clamp feed rate to valid range."""
        max_feed = self.max_feed_z_mm_min if is_z else self.max_feed_xy_mm_min
        return max(1.0, min(max_feed, feed))

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "machine_id": self.machine_id,
            "name": self.name,
            "controller": self.controller.value,
            "travel_x_mm": self.travel_x_mm,
            "travel_y_mm": self.travel_y_mm,
            "travel_z_mm": self.travel_z_mm,
            "spindle_type": self.spindle_type.value,
            "min_spindle_rpm": self.min_spindle_rpm,
            "max_spindle_rpm": self.max_spindle_rpm,
            "max_feed_xy_mm_min": self.max_feed_xy_mm_min,
            "max_feed_z_mm_min": self.max_feed_z_mm_min,
            "safe_z_mm": self.safe_z_mm,
            "has_atc": self.has_atc,
            "has_probe": self.has_probe,
        }


# =============================================================================
# MACHINE PRESETS
# =============================================================================

MACHINE_PRESETS: Dict[str, BCamMachineSpec] = {
    "shapeoko_3": BCamMachineSpec(
        machine_id="shapeoko_3",
        name="Carbide3D Shapeoko 3",
        controller=ControllerType.GRBL,
        travel_x_mm=425,
        travel_y_mm=425,
        travel_z_mm=75,
        spindle_type=SpindleType.ROUTER,
        max_spindle_rpm=30000,
        max_feed_xy_mm_min=5000,
        max_feed_z_mm_min=2000,
    ),
    "shapeoko_xxl": BCamMachineSpec(
        machine_id="shapeoko_xxl",
        name="Carbide3D Shapeoko XXL",
        controller=ControllerType.GRBL,
        travel_x_mm=838,
        travel_y_mm=838,
        travel_z_mm=75,
        spindle_type=SpindleType.ROUTER,
        max_spindle_rpm=30000,
        max_feed_xy_mm_min=5000,
        max_feed_z_mm_min=2000,
    ),
    "x_carve_1000": BCamMachineSpec(
        machine_id="x_carve_1000",
        name="Inventables X-Carve 1000mm",
        controller=ControllerType.GRBL,
        travel_x_mm=750,
        travel_y_mm=750,
        travel_z_mm=65,
        spindle_type=SpindleType.ROUTER,
        max_spindle_rpm=30000,
        max_feed_xy_mm_min=8000,
        max_feed_z_mm_min=500,
    ),
    "avid_cnc_4x4": BCamMachineSpec(
        machine_id="avid_cnc_4x4",
        name="Avid CNC Pro 4x4",
        controller=ControllerType.MACH4,
        travel_x_mm=1219,
        travel_y_mm=1219,
        travel_z_mm=200,
        spindle_type=SpindleType.VFD_SPINDLE,
        min_spindle_rpm=6000,
        max_spindle_rpm=24000,
        max_feed_xy_mm_min=12000,
        max_feed_z_mm_min=3000,
        has_probe=True,
        probe_feed_mm_min=150,
    ),
    "laguna_iq": BCamMachineSpec(
        machine_id="laguna_iq",
        name="Laguna IQ",
        controller=ControllerType.MACH3,
        travel_x_mm=610,
        travel_y_mm=610,
        travel_z_mm=114,
        spindle_type=SpindleType.VFD_SPINDLE,
        min_spindle_rpm=6000,
        max_spindle_rpm=18000,
        max_feed_xy_mm_min=7620,
        max_feed_z_mm_min=2540,
    ),
    "haas_vf2": BCamMachineSpec(
        machine_id="haas_vf2",
        name="Haas VF-2",
        controller=ControllerType.HAAS,
        travel_x_mm=762,
        travel_y_mm=406,
        travel_z_mm=508,
        spindle_type=SpindleType.SERVO_SPINDLE,
        min_spindle_rpm=0,
        max_spindle_rpm=8100,
        max_feed_xy_mm_min=25400,
        max_feed_z_mm_min=25400,
        rapid_feed_mm_min=35560,
        has_atc=True,
        max_tools=20,
        has_probe=True,
    ),
    "bcam_2030a": BCamMachineSpec(
        machine_id="bcam_2030a",
        name="BCAMCNC 2030A Lutherie Router",
        controller=ControllerType.GRBL,
        travel_x_mm=600,
        travel_y_mm=900,
        travel_z_mm=120,
        spindle_type=SpindleType.VFD_SPINDLE,
        min_spindle_rpm=6000,
        max_spindle_rpm=24000,
        max_feed_xy_mm_min=8000,
        max_feed_z_mm_min=3000,
        safe_z_mm=25.0,
        has_probe=True,
        probe_feed_mm_min=100,
    ),
}

# Default BCAM machine for lutherie
BCAM_2030A = MACHINE_PRESETS["bcam_2030a"]


def list_machines() -> List[BCamMachineSpec]:
    """Return all available machine presets."""
    return list(MACHINE_PRESETS.values())


def get_machine(machine_id: str) -> BCamMachineSpec:
    """
    Get machine spec by ID.

    Args:
        machine_id: Machine identifier (preset name or custom ID)

    Returns:
        BCamMachineSpec for the machine

    Raises:
        KeyError: If machine_id not found in presets
    """
    if machine_id in MACHINE_PRESETS:
        return MACHINE_PRESETS[machine_id]
    raise KeyError(f"Unknown machine: {machine_id}. Available: {list(MACHINE_PRESETS.keys())}")


__all__ = [
    "BCamMachineSpec",
    "ControllerType",
    "SpindleType",
    "MACHINE_PRESETS",
    "BCAM_2030A",
    "get_machine",
    "list_machines",
]
