# File: models/sim_metrics.py
# Request/response models for simulation metrics with energy model (thermal budget)

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field, field_validator


Units = Literal["mm", "inch"]


class Move(BaseModel):
    """
    Minimal G-code-like move used by pipeline:
    - code: "G0" (rapid), "G1" (linear), "G2"/"G3" (arcs)
    - x,y,z: absolute coordinates (units given by `units`)
    - f: feed in units/min (optional; for G0 rapid we use machine rapid if provided or fallback)
    """
    code: Literal["G0", "G1", "G2", "G3"]
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    f: Optional[float] = None


class SimMaterial(BaseModel):
    """
    Specific cutting energy (SCE) approximations (J/mm^3). Defaults tuned for common lutherie woods.
    These values are heuristic—meant for first-order estimates.
    """
    name: str = "hardwood_generic"
    sce_j_per_mm3: float = 1.4  # J/mm^3 (≈ oak/maple range)
    chip_fraction: float = 0.60  # portion of energy to chip formation
    tool_fraction: float = 0.25  # into tool (heat)
    work_fraction: float = 0.15  # into workpiece (heat)

    @field_validator("chip_fraction", "tool_fraction", "work_fraction")
    @classmethod
    def _clamp_fraction(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    def normalized_splits(self) -> Tuple[float, float, float]:
        s = self.chip_fraction + self.tool_fraction + self.work_fraction
        if s <= 0:
            return (1.0, 0.0, 0.0)
        return (self.chip_fraction / s, self.tool_fraction / s, self.work_fraction / s)


class MachineCaps(BaseModel):
    """
    Optional machine limits to compute feed deviation and time @ rapid.
    """
    feed_xy_max: Optional[float] = None  # units/min
    rapid_xy: Optional[float] = None     # units/min
    accel_xy: Optional[float] = None     # units/s^2 (reserved)


class EngagementModel(BaseModel):
    """
    Engagement approximation for 2D profile/adaptive paths.
    """
    stepover_frac: float = Field(0.45, description="fraction of tool_d engaged (0..1)")
    stepdown: float = Field(2.0, description="axial depth per pass in units")
    engagement_pct: float = Field(0.6, description="chip thickness / slotting proxy (0..1)")
    climb: bool = True

    @field_validator("stepover_frac", "engagement_pct")
    @classmethod
    def _clamp_01(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class SimMetricsIn(BaseModel):
    """
    Input for /cam/sim/metrics:
    - Provide either `gcode_text` or `moves`.
    - Provide `tool_d` and an EngagementModel to approximate material removal rate (MRR).
    """
    units: Units = "mm"
    gcode_text: Optional[str] = None
    moves: Optional[List[Move]] = None

    # Tool / process
    tool_d: float = 6.0                        # mm or inch depending on units
    rpm: Optional[int] = None                  # optional, not required for energy (v1)
    material: SimMaterial = SimMaterial()
    engagement: EngagementModel = EngagementModel()

    # Machine (optional)
    machine: Optional[MachineCaps] = None

    # Options
    include_timeseries: bool = False           # include per-segment metrics in output


class SegTS(BaseModel):
    """Per-segment timeseries entry (when include_timeseries=True)."""
    idx: int
    code: str
    length_mm: float
    feed_u_per_min: float
    time_s: float
    power_w: float
    energy_j: float


class SimMetricsOut(BaseModel):
    total_time_s: float
    total_length_mm: float
    avg_feed_u_per_min: float

    total_energy_j: float
    chip_energy_j: float
    tool_energy_j: float
    work_energy_j: float

    peak_power_w: float
    mean_power_w: float

    # feed compliance
    feed_limited_pct: float

    # optional TS
    timeseries: Optional[List[SegTS]] = None

    # echoes
    units: Units
    tool_d: float
    stepdown: float
    stepover_frac: float
    engagement_pct: float
    material_name: str
