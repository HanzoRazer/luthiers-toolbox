# N16.7 - Hardware-tuned machine profiles for G-code posts
#
# This module defines machine-level presets that sit on top of
# the more abstract MachineProfile (GRBL / FANUC).
#
# Each MachineConfig captures:
#   - profile:       GRBL or FANUC
#   - human label:   for UI usage
#   - default safe Z
#   - default tool ID
#   - optional program number (FANUC O-number)
#
# The idea is that "BCM 2030CA" vs "Fanuc Demo Mill" can share
# the same basic post style but differ in header/footer details.

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .cnc_gcode_exporter import MachineProfile


@dataclass(frozen=True)
class MachineConfig:
    machine_id: str           # stable identifier used in API / UI
    label: str                # human-readable name
    profile: MachineProfile   # GRBL / FANUC, etc.
    default_safe_z_mm: float  # clearance / retract height
    default_tool_id: int      # default T-number
    default_program_number: int | None = None
    description: str | None = None


_MACHINE_CONFIGS: Dict[str, MachineConfig] = {}


def _init_machine_configs() -> None:
    """
    Initialize a small set of hardware-tuned machine configs.

    Adjust these to match your actual shop hardware. They are
    intentionally conservative and can be extended over time.
    """
    global _MACHINE_CONFIGS
    if _MACHINE_CONFIGS:
        return

    # Example: BCM 2030CA router running GRBL-style control
    _MACHINE_CONFIGS["bcm_2030ca"] = MachineConfig(
        machine_id="bcm_2030ca",
        label="BCM 2030CA Router (GRBL-style)",
        profile=MachineProfile.GRBL,
        default_safe_z_mm=10.0,
        default_tool_id=1,
        default_program_number=None,
        description=(
            "BCM 2030CA 2000x3000 router. GRBL-style program with "
            "10mm safe Z and T1 as primary rosette tool."
        ),
    )

    # Example: Fanuc demo vertical mill
    _MACHINE_CONFIGS["fanuc_demo"] = MachineConfig(
        machine_id="fanuc_demo",
        label="Fanuc Demo Mill",
        profile=MachineProfile.FANUC,
        default_safe_z_mm=5.0,
        default_tool_id=1,
        default_program_number=1001,
        description=(
            "Generic Fanuc-style VMC demo profile, O1001 default program number."
        ),
    )


def get_machine_config(machine_id: str) -> MachineConfig | None:
    if not _MACHINE_CONFIGS:
        _init_machine_configs()
    return _MACHINE_CONFIGS.get(machine_id)


def list_machine_configs() -> List[MachineConfig]:
    if not _MACHINE_CONFIGS:
        _init_machine_configs()
    return list(_MACHINE_CONFIGS.values())
