"""WP-3: Les Paul CNC configuration — tool library and machine profiles.

Extracted from lespaul_body_generator.py to reduce god-object size.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ToolConfig:
    """Tool configuration from your Fusion360 setup."""
    number: int
    name: str
    diameter_in: float
    rpm: int
    feed_ipm: float
    plunge_ipm: float
    stepdown_in: float
    stepover_pct: float

    @property
    def stepover_in(self) -> float:
        return self.diameter_in * (self.stepover_pct / 100)


@dataclass
class MachineConfig:
    """Machine configuration."""
    name: str
    max_x_in: float
    max_y_in: float
    max_z_in: float
    safe_z_in: float = 0.75
    retract_z_in: float = 0.25
    rapid_rate: float = 200.0  # IPM


# Default tool library (from your Tool_List_LP.csv, converted to inches)
TOOLS = {
    1: ToolConfig(1, "10mm Flat End Mill", 0.394, 18000, 220, 31, 0.22, 45),
    2: ToolConfig(2, "6mm Flat End Mill", 0.236, 18000, 150, 24, 0.06, 18),
    3: ToolConfig(3, "3mm Flat/Drill", 0.118, 20000, 60, 16, 0.03, 20),
}

# Machine configurations
MACHINES = {
    "txrx_router": MachineConfig("TXRX Labs Router", 48, 48, 4, 0.75, 0.25),
    "bcamcnc_2030ca": MachineConfig("BCAMCNC 2030CA", 48, 24, 4, 0.6, 0.2),
}
