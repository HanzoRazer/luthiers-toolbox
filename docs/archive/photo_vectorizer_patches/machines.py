"""
services/api/app/cam/machines.py
=================================
Canonical BCAM 2030A machine specification.

Supersedes two scattered definitions that tracked orthogonal concerns
and used different unit systems:
  - generators/lespaul_config.MachineConfig  (inches, work envelope only)
  - cam/rosette/cnc/cnc_machine_profiles.MachineConfig  (mm, post dialect only)

Neither definition had spindle RPM limits or max feed rates.
The two safe_z values disagreed: 0.6 in (15.24mm) vs 10mm (52% difference).
This file is the single source of truth for all three tiers:
  Tier 1 (calculators) — max_z_mm enforced in evaluate gate
  Tier 2 (G-code engines) — safe_z_mm, retract_z_mm threaded into generators
  Tier 3 (post-processor) — post_dialect, tool_change_pause
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class BCamMachineSpec:
    """
    Complete machine specification for CNC router.

    All dimensions in mm.
    Spindle limits apply to router spindle (not servo axes).
    """

    machine_id:         str   = "bcam_2030a"
    label:              str   = "BCAM 2030A"

    # Post-processor dialect
    post_dialect:       str   = "grbl"           # "grbl" | "linuxcnc" | "fanuc"
    units:              str   = "mm"             # always mm for this machine

    # ── Work envelope (mm) ────────────────────────────────────────────────────
    # Source: lespaul_config.py max_x_in=48, max_y_in=24, max_z_in=4
    # 48" × 24" × 4" converted: 1219.2 × 609.6 × 101.6 mm
    max_x_mm:           float = 1219.2           # 48"
    max_y_mm:           float = 609.6            # 24"
    max_z_mm:           float = 101.6            # 4" — hard ceiling, enforced in gate

    # ── Motion limits (mm/min) ────────────────────────────────────────────────
    # Source: lespaul_config.py rapid_rate=200.0 IPM → 5080 mm/min
    # Max cutting feeds from tool presets (T1=220 IPM → 5588, conservative 3000)
    rapid_mm_min:       float = 5080.0           # 200 IPM
    max_feed_xy:        float = 3000.0           # conservative ceiling across all ops
    max_feed_z:         float = 500.0            # plunge limit

    # ── Spindle ───────────────────────────────────────────────────────────────
    # Source: lespaul_config.py TOOLS: T1/T2 = 18000, T3 = 20000 RPM
    min_rpm:            int   = 8000
    max_rpm:            int   = 24000

    # ── Safety heights (mm) ───────────────────────────────────────────────────
    # safe_z: cnc_machine_profiles used 10mm (more conservative than lespaul 15.24mm)
    # retract_z: lespaul retract_z_in=0.2" = 5.08mm, rounded to 5.0
    safe_z_mm:          float = 10.0
    retract_z_mm:       float = 5.0

    # ── Tool change behaviour ─────────────────────────────────────────────────
    # M1 = optional stop — operator changes tool, presses cycle start to resume.
    # BCAM 2030A has no ATC. M1 is mandatory for multi-tool programs.
    # ToolChangeMode.M0 would be a hard block; M1 lets a confident operator skip.
    tool_change_pause:  str   = "M1"             # "M1" | "M0" | "none"
    dwell_after_spindle_ms: int = 2000           # 2s ramp-up before cutting


# ── Default instance ──────────────────────────────────────────────────────────
# Import this directly: from app.cam.machines import BCAM_2030A
BCAM_2030A = BCamMachineSpec()


# ── Registry for future multi-machine support ─────────────────────────────────
MACHINE_REGISTRY: dict[str, BCamMachineSpec] = {
    BCAM_2030A.machine_id: BCAM_2030A,
}


def get_machine(machine_id: str) -> BCamMachineSpec | None:
    """Return machine spec by id, or None if not registered."""
    return MACHINE_REGISTRY.get(machine_id)


def list_machines() -> list[BCamMachineSpec]:
    """Return all registered machine specs."""
    return list(MACHINE_REGISTRY.values())
