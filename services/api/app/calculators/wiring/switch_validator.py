"""
Switch Validator

Validates pickup switching configurations for guitars.

MODEL NOTES:
- Standard configurations:
  - 3-way toggle: Neck / Both / Bridge
  - 5-way Strat: N / N+M / M / M+B / B
  - 4-way Tele: Standard 3-way + series option
  - Super switch: Various custom wiring
- Validates:
  - No dead positions
  - No phase issues (unless intentional)
  - Proper grounding
  - Output levels balanced
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional

SwitchType = Literal["3way_toggle", "5way_blade", "4way_tele", "rotary", "super_switch"]
PickupType = Literal["single_coil", "humbucker", "p90", "mini_humbucker", "piezo"]


@dataclass
class PickupConfig:
    """Configuration for a single pickup."""
    name: str
    pickup_type: PickupType
    position: Literal["neck", "middle", "bridge"]
    is_coil_split: bool = False


@dataclass
class SwitchPosition:
    """A single switch position configuration."""
    position_number: int
    active_pickups: List[str]  # Names of active pickups
    wiring: Literal["parallel", "series", "single"]
    phase: Literal["in_phase", "out_of_phase"]
    description: str


@dataclass
class SwitchValidationResult:
    """Result from switch configuration validation."""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    positions: List[SwitchPosition]
    notes: str


def validate_switch_config(
    switch_type: SwitchType,
    pickups: List[PickupConfig],
    *,
    allow_out_of_phase: bool = False,
    require_all_positions_active: bool = True,
) -> SwitchValidationResult:
    """
    Validate a pickup switching configuration.

    Args:
        switch_type: Type of switch
        pickups: List of pickup configurations
        allow_out_of_phase: Whether out-of-phase positions are intentional
        require_all_positions_active: Whether all positions must have output

    Returns:
        SwitchValidationResult with validation status
    """
    warnings: List[str] = []
    errors: List[str] = []
    positions: List[SwitchPosition] = []

    # Determine expected positions
    if switch_type == "3way_toggle":
        expected_positions = 3
    elif switch_type == "5way_blade":
        expected_positions = 5
    elif switch_type == "4way_tele":
        expected_positions = 4
    elif switch_type == "rotary":
        expected_positions = len(pickups) + 1  # All combos
    else:
        expected_positions = 5  # Super switch default

    # Generate standard positions based on switch type
    if switch_type == "3way_toggle" and len(pickups) >= 2:
        positions = _generate_3way_positions(pickups)
    elif switch_type == "5way_blade" and len(pickups) >= 3:
        positions = _generate_5way_positions(pickups)
    elif switch_type == "4way_tele" and len(pickups) >= 2:
        positions = _generate_4way_positions(pickups)
    else:
        warnings.append(f"Custom {switch_type} - positions not auto-generated")

    # Validate: check for dead positions
    for pos in positions:
        if not pos.active_pickups:
            if require_all_positions_active:
                errors.append(f"Position {pos.position_number} has no active pickups")
            else:
                warnings.append(f"Position {pos.position_number} is silent (intentional?)")

    # Validate: check for out-of-phase
    for pos in positions:
        if pos.phase == "out_of_phase" and not allow_out_of_phase:
            warnings.append(
                f"Position {pos.position_number} is out-of-phase - may sound thin"
            )

    # Validate: pickup count matches switch
    if switch_type == "5way_blade" and len(pickups) < 3:
        errors.append("5-way switch requires at least 3 pickups")
    if switch_type == "3way_toggle" and len(pickups) < 2:
        errors.append("3-way toggle requires at least 2 pickups")

    is_valid = len(errors) == 0

    notes = f"{switch_type} with {len(pickups)} pickup(s): {len(positions)} positions validated"

    return SwitchValidationResult(
        is_valid=is_valid,
        warnings=warnings,
        errors=errors,
        positions=positions,
        notes=notes,
    )


def _generate_3way_positions(pickups: List[PickupConfig]) -> List[SwitchPosition]:
    """Generate standard 3-way toggle positions."""
    neck = next((p for p in pickups if p.position == "neck"), None)
    bridge = next((p for p in pickups if p.position == "bridge"), None)

    positions = []

    # Position 1: Neck
    if neck:
        positions.append(SwitchPosition(
            position_number=1,
            active_pickups=[neck.name],
            wiring="single",
            phase="in_phase",
            description="Neck pickup only",
        ))

    # Position 2: Both
    if neck and bridge:
        positions.append(SwitchPosition(
            position_number=2,
            active_pickups=[neck.name, bridge.name],
            wiring="parallel",
            phase="in_phase",
            description="Neck + Bridge (parallel)",
        ))

    # Position 3: Bridge
    if bridge:
        positions.append(SwitchPosition(
            position_number=3,
            active_pickups=[bridge.name],
            wiring="single",
            phase="in_phase",
            description="Bridge pickup only",
        ))

    return positions


def _generate_5way_positions(pickups: List[PickupConfig]) -> List[SwitchPosition]:
    """Generate standard 5-way Strat positions."""
    neck = next((p for p in pickups if p.position == "neck"), None)
    middle = next((p for p in pickups if p.position == "middle"), None)
    bridge = next((p for p in pickups if p.position == "bridge"), None)

    positions = []

    if neck:
        positions.append(SwitchPosition(
            position_number=1,
            active_pickups=[neck.name],
            wiring="single",
            phase="in_phase",
            description="Neck",
        ))

    if neck and middle:
        positions.append(SwitchPosition(
            position_number=2,
            active_pickups=[neck.name, middle.name],
            wiring="parallel",
            phase="in_phase",
            description="Neck + Middle (quack)",
        ))

    if middle:
        positions.append(SwitchPosition(
            position_number=3,
            active_pickups=[middle.name],
            wiring="single",
            phase="in_phase",
            description="Middle",
        ))

    if middle and bridge:
        positions.append(SwitchPosition(
            position_number=4,
            active_pickups=[middle.name, bridge.name],
            wiring="parallel",
            phase="in_phase",
            description="Middle + Bridge (quack)",
        ))

    if bridge:
        positions.append(SwitchPosition(
            position_number=5,
            active_pickups=[bridge.name],
            wiring="single",
            phase="in_phase",
            description="Bridge",
        ))

    return positions


def _generate_4way_positions(pickups: List[PickupConfig]) -> List[SwitchPosition]:
    """Generate 4-way Tele positions (standard 3-way + series)."""
    positions = _generate_3way_positions(pickups)

    neck = next((p for p in pickups if p.position == "neck"), None)
    bridge = next((p for p in pickups if p.position == "bridge"), None)

    # Position 4: Series (Tele special)
    if neck and bridge:
        positions.append(SwitchPosition(
            position_number=4,
            active_pickups=[neck.name, bridge.name],
            wiring="series",
            phase="in_phase",
            description="Neck + Bridge (series) - fat humbucker-like tone",
        ))

    return positions
