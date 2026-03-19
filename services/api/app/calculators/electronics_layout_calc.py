"""
Electronics Physical Layout Calculator (CONSTRUCTION-008)
=========================================================

Electronic component placement and cavity sizing for electric guitars.

Standard cavity depths:
    humbucker: 50mm × 40mm × 45mm deep
    single_coil: 90mm × 15mm × 45mm deep
    p90: 90mm × 50mm × 45mm deep
    mini_humbucker: 67mm × 34mm × 40mm deep

Control cavity: 120mm × 80mm × 40mm typical
Switch cavity: 40mm × 20mm × 35mm typical
Jack cavity: 35mm diameter × 40mm deep

Includes:
- Pot spacing (minimum 19mm center-to-center)
- Jack placement relative to strap button
- Control cavity routing paths
- Shielding area calculation
- Switch placement geometry
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Literal, Optional
import math


# ─── CavitySpec Dataclass ─────────────────────────────────────────────────────

@dataclass
class CavitySpec:
    """Specification for a routed cavity."""
    component: str           # pickup type, "control", "switch", "jack"
    length_mm: float         # longest dimension
    width_mm: float          # shorter dimension
    depth_mm: float          # routing depth
    position_x_mm: float     # from centerline (+ = treble side)
    position_y_mm: float     # from bridge (+ = toward neck)
    clearance_mm: float      # wall thickness required
    gate: str                # GREEN, YELLOW, RED
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Pickup Cavity Dimensions ────────────────────────────────────────────────

PICKUP_CAVITY_SPECS: Dict[str, Dict[str, float]] = {
    "humbucker": {
        "length_mm": 50.0,
        "width_mm": 40.0,
        "depth_mm": 45.0,
        "clearance_mm": 3.0,
    },
    "single_coil": {
        "length_mm": 90.0,
        "width_mm": 15.0,
        "depth_mm": 45.0,
        "clearance_mm": 2.5,
    },
    "p90": {
        "length_mm": 90.0,
        "width_mm": 50.0,
        "depth_mm": 45.0,
        "clearance_mm": 3.0,
    },
    "mini_humbucker": {
        "length_mm": 67.0,
        "width_mm": 34.0,
        "depth_mm": 40.0,
        "clearance_mm": 2.5,
    },
    "filtertron": {
        "length_mm": 70.0,
        "width_mm": 38.0,
        "depth_mm": 42.0,
        "clearance_mm": 3.0,
    },
    "lipstick": {
        "length_mm": 85.0,
        "width_mm": 20.0,
        "depth_mm": 35.0,
        "clearance_mm": 2.0,
    },
    "jazzmaster": {
        "length_mm": 95.0,
        "width_mm": 45.0,
        "depth_mm": 40.0,
        "clearance_mm": 3.0,
    },
}

# ─── Pickup Position from Bridge (mm) ────────────────────────────────────────

PICKUP_POSITIONS_MM: Dict[str, Dict[str, float]] = {
    # Standard Strat-style positions
    "stratocaster": {
        "bridge": 30.0,
        "middle": 95.0,
        "neck": 165.0,
    },
    # Les Paul style (humbucker)
    "les_paul": {
        "bridge": 25.0,
        "neck": 150.0,
    },
    # Telecaster
    "telecaster": {
        "bridge": 15.0,
        "neck": 165.0,
    },
    # SG
    "sg": {
        "bridge": 25.0,
        "neck": 145.0,
    },
    # Default (generic)
    "default": {
        "bridge": 25.0,
        "middle": 90.0,
        "neck": 160.0,
    },
}


# ─── Control Cavity Specs ────────────────────────────────────────────────────

CONTROL_CAVITY_SPECS: Dict[str, Dict[str, float]] = {
    "les_paul": {
        "length_mm": 120.0,
        "width_mm": 80.0,
        "depth_mm": 40.0,
        "position_x_mm": 50.0,   # offset from centerline (treble side)
        "position_y_mm": 100.0,  # from bridge
    },
    "stratocaster": {
        "length_mm": 150.0,
        "width_mm": 100.0,
        "depth_mm": 40.0,
        "position_x_mm": 0.0,    # centered
        "position_y_mm": 80.0,
    },
    "telecaster": {
        "length_mm": 90.0,
        "width_mm": 60.0,
        "depth_mm": 35.0,
        "position_x_mm": 40.0,
        "position_y_mm": 60.0,
    },
    "sg": {
        "length_mm": 110.0,
        "width_mm": 75.0,
        "depth_mm": 40.0,
        "position_x_mm": 45.0,
        "position_y_mm": 95.0,
    },
    "default": {
        "length_mm": 120.0,
        "width_mm": 80.0,
        "depth_mm": 40.0,
        "position_x_mm": 45.0,
        "position_y_mm": 90.0,
    },
}

# ─── Switch Specs ────────────────────────────────────────────────────────────

SWITCH_SPECS: Dict[str, Dict[str, float]] = {
    "3way_toggle": {
        "length_mm": 40.0,
        "width_mm": 20.0,
        "depth_mm": 35.0,
        "mounting_hole_mm": 12.0,  # toggle shaft hole
    },
    "5way_blade": {
        "length_mm": 45.0,
        "width_mm": 25.0,
        "depth_mm": 25.0,  # shallower, fits in pickguard
        "mounting_hole_mm": 0.0,   # plate-mounted
    },
    "rotary": {
        "length_mm": 35.0,
        "width_mm": 35.0,
        "depth_mm": 30.0,
        "mounting_hole_mm": 10.0,
    },
}

# ─── Jack Specs ──────────────────────────────────────────────────────────────

JACK_SPECS: Dict[str, Dict[str, float]] = {
    "side": {
        "diameter_mm": 35.0,
        "depth_mm": 40.0,
        "position_offset_mm": 25.0,  # from body edge
    },
    "top": {
        "diameter_mm": 25.0,
        "depth_mm": 35.0,
        "position_offset_mm": 0.0,   # in control cavity
    },
    "endpin": {
        "diameter_mm": 15.0,  # just the endpin hole
        "depth_mm": 30.0,
        "position_offset_mm": 0.0,
    },
}


# ─── Constants ───────────────────────────────────────────────────────────────

MIN_POT_SPACING_MM = 19.0  # Minimum center-to-center for standard knobs
POT_DIAMETER_MM = 24.0     # Standard pot body diameter
POT_HOLE_MM = 9.5          # Standard pot shaft hole


# ─── Gate Logic ──────────────────────────────────────────────────────────────

def _compute_cavity_gate(
    depth_mm: float,
    body_thickness_mm: float,
    min_clearance_mm: float = 5.0,
) -> tuple[str, List[str]]:
    """
    Determine gate for cavity depth vs body thickness.

    GREEN: depth + clearance <= body thickness
    YELLOW: borderline (clearance < min but > 2mm)
    RED: breakthrough risk
    """
    notes: List[str] = []
    remaining = body_thickness_mm - depth_mm

    if remaining >= min_clearance_mm:
        return "GREEN", ["Adequate material remaining beneath cavity"]
    elif remaining >= 2.0:
        notes.append(f"Only {remaining:.1f}mm remaining - borderline clearance")
        return "YELLOW", notes
    else:
        notes.append(f"DANGER: Only {remaining:.1f}mm remaining - breakthrough risk")
        return "RED", notes


# ─── Core Functions ──────────────────────────────────────────────────────────

def compute_pickup_cavity(
    pickup_type: str,
    position: str = "bridge",
    body_thickness_mm: float = 45.0,
    body_style: str = "default",
) -> CavitySpec:
    """
    Compute pickup cavity dimensions.

    Args:
        pickup_type: "humbucker" | "single_coil" | "p90" | "mini_humbucker" | "filtertron" | "lipstick" | "jazzmaster"
        position: "neck" | "middle" | "bridge"
        body_thickness_mm: Body thickness at pickup location
        body_style: "les_paul" | "stratocaster" | "telecaster" | "sg" | "default"

    Returns:
        CavitySpec with dimensions and position
    """
    # Normalize inputs
    pickup_type = pickup_type.lower().strip().replace("-", "_").replace(" ", "_")
    position = position.lower().strip()
    body_style = body_style.lower().strip().replace("-", "_").replace(" ", "_")

    # Get cavity dimensions
    specs = PICKUP_CAVITY_SPECS.get(pickup_type, PICKUP_CAVITY_SPECS["humbucker"])

    # Get position from bridge
    positions = PICKUP_POSITIONS_MM.get(body_style, PICKUP_POSITIONS_MM["default"])
    position_y_mm = positions.get(position, positions.get("bridge", 25.0))

    # Pickups are centered on body
    position_x_mm = 0.0

    # Compute gate
    gate, notes = _compute_cavity_gate(
        depth_mm=specs["depth_mm"],
        body_thickness_mm=body_thickness_mm,
    )

    return CavitySpec(
        component=pickup_type,
        length_mm=specs["length_mm"],
        width_mm=specs["width_mm"],
        depth_mm=specs["depth_mm"],
        position_x_mm=position_x_mm,
        position_y_mm=position_y_mm,
        clearance_mm=specs["clearance_mm"],
        gate=gate,
        notes=notes,
    )


def compute_control_layout(
    pot_count: int = 4,
    switch_type: str = "3way_toggle",
    jack_type: str = "side",
    body_style: str = "les_paul",
    body_thickness_mm: float = 45.0,
) -> List[CavitySpec]:
    """
    Compute control cavity layout including pots, switch, and jack.

    Args:
        pot_count: Number of potentiometers (1-6)
        switch_type: "3way_toggle" | "5way_blade" | "rotary"
        jack_type: "side" | "top" | "endpin"
        body_style: "les_paul" | "stratocaster" | "telecaster" | "sg" | "default"
        body_thickness_mm: Body thickness

    Returns:
        List of CavitySpec for control cavity, switch cavity (if separate), and jack cavity
    """
    # Normalize inputs
    switch_type = switch_type.lower().strip().replace("-", "_").replace(" ", "_")
    jack_type = jack_type.lower().strip()
    body_style = body_style.lower().strip().replace("-", "_").replace(" ", "_")

    cavities: List[CavitySpec] = []

    # ─── Control Cavity ──────────────────────────────────────────────────────
    control_specs = CONTROL_CAVITY_SPECS.get(body_style, CONTROL_CAVITY_SPECS["default"])

    # Adjust cavity size based on pot count
    # Pots need MIN_POT_SPACING_MM center-to-center
    min_length_for_pots = max(pot_count - 1, 1) * MIN_POT_SPACING_MM + POT_DIAMETER_MM
    adjusted_length = max(control_specs["length_mm"], min_length_for_pots + 20)

    gate, notes = _compute_cavity_gate(
        depth_mm=control_specs["depth_mm"],
        body_thickness_mm=body_thickness_mm,
    )

    # Add pot layout info
    if pot_count > 1:
        pot_spacing = adjusted_length / (pot_count + 1)
        if pot_spacing < MIN_POT_SPACING_MM:
            notes.append(f"WARNING: Pot spacing {pot_spacing:.1f}mm below minimum {MIN_POT_SPACING_MM}mm")
            gate = "YELLOW" if gate == "GREEN" else gate

    # Shielding area calculation
    shielding_area_mm2 = adjusted_length * control_specs["width_mm"]
    notes.append(f"Shielding area: {shielding_area_mm2:.0f}mm² ({adjusted_length:.0f}×{control_specs['width_mm']:.0f})")

    cavities.append(CavitySpec(
        component="control",
        length_mm=adjusted_length,
        width_mm=control_specs["width_mm"],
        depth_mm=control_specs["depth_mm"],
        position_x_mm=control_specs["position_x_mm"],
        position_y_mm=control_specs["position_y_mm"],
        clearance_mm=5.0,
        gate=gate,
        notes=notes,
    ))

    # ─── Switch Cavity ───────────────────────────────────────────────────────
    switch_specs = SWITCH_SPECS.get(switch_type, SWITCH_SPECS["3way_toggle"])

    # Switch position varies by body style
    if body_style == "les_paul":
        switch_x = -60.0  # bass side upper bout
        switch_y = 280.0
    elif body_style == "stratocaster":
        switch_x = 0.0  # in pickguard
        switch_y = 120.0
    elif body_style == "telecaster":
        switch_x = 55.0  # treble side
        switch_y = 45.0
    else:
        switch_x = -55.0
        switch_y = 250.0

    switch_gate, switch_notes = _compute_cavity_gate(
        depth_mm=switch_specs["depth_mm"],
        body_thickness_mm=body_thickness_mm,
    )

    cavities.append(CavitySpec(
        component=f"switch_{switch_type}",
        length_mm=switch_specs["length_mm"],
        width_mm=switch_specs["width_mm"],
        depth_mm=switch_specs["depth_mm"],
        position_x_mm=switch_x,
        position_y_mm=switch_y,
        clearance_mm=3.0,
        gate=switch_gate,
        notes=switch_notes,
    ))

    # ─── Jack Cavity ─────────────────────────────────────────────────────────
    jack_specs = JACK_SPECS.get(jack_type, JACK_SPECS["side"])

    # Jack position varies by type
    if jack_type == "side":
        jack_x = 80.0   # body edge, treble side
        jack_y = 20.0   # near strap button
    elif jack_type == "top":
        # Inside control cavity
        jack_x = control_specs["position_x_mm"]
        jack_y = control_specs["position_y_mm"] - 30
    else:  # endpin
        jack_x = 0.0
        jack_y = 0.0    # body end

    jack_gate, jack_notes = _compute_cavity_gate(
        depth_mm=jack_specs["depth_mm"],
        body_thickness_mm=body_thickness_mm,
    )

    cavities.append(CavitySpec(
        component=f"jack_{jack_type}",
        length_mm=jack_specs["diameter_mm"],  # circular cavity
        width_mm=jack_specs["diameter_mm"],
        depth_mm=jack_specs["depth_mm"],
        position_x_mm=jack_x,
        position_y_mm=jack_y,
        clearance_mm=3.0,
        gate=jack_gate,
        notes=jack_notes,
    ))

    return cavities


def check_cavity_clearance(
    cavities: List[CavitySpec],
    body_thickness_mm: float,
) -> str:
    """
    Check overall clearance for all cavities.

    Args:
        cavities: List of CavitySpec to check
        body_thickness_mm: Body thickness

    Returns:
        Overall gate: GREEN if all OK, YELLOW if any borderline, RED if any critical
    """
    overall = "GREEN"

    for cavity in cavities:
        remaining = body_thickness_mm - cavity.depth_mm

        if remaining < 2.0:
            return "RED"  # Any breakthrough risk is RED
        elif remaining < 5.0:
            overall = "YELLOW"  # Borderline downgrades to YELLOW

    return overall


def compute_shielding_area(cavities: List[CavitySpec]) -> float:
    """
    Calculate total shielding paint/foil area needed.

    Args:
        cavities: List of cavities to shield

    Returns:
        Total area in mm²
    """
    total = 0.0
    for cavity in cavities:
        # Floor area
        floor_area = cavity.length_mm * cavity.width_mm
        # Wall area (perimeter × depth)
        perimeter = 2 * (cavity.length_mm + cavity.width_mm)
        wall_area = perimeter * cavity.depth_mm
        total += floor_area + wall_area
    return total


def compute_wire_run_length(
    pickup_positions: List[float],
    control_position_y: float,
    jack_position_y: float,
) -> float:
    """
    Estimate total wire run length for routing channels.

    Args:
        pickup_positions: Y positions of pickups (from bridge)
        control_position_y: Y position of control cavity
        jack_position_y: Y position of jack

    Returns:
        Total wire run length in mm (approximate)
    """
    total = 0.0

    # Pickup to control cavity runs
    for pos in pickup_positions:
        # Assume X offset of 40mm average
        run_length = abs(pos - control_position_y) + 40
        total += run_length

    # Control to jack run
    total += abs(control_position_y - jack_position_y) + 20

    # Add 20% for slack and connections
    return total * 1.2


# ─── List Functions ──────────────────────────────────────────────────────────

def list_pickup_types() -> List[str]:
    """Return list of supported pickup types."""
    return list(PICKUP_CAVITY_SPECS.keys())


def list_switch_types() -> List[str]:
    """Return list of supported switch types."""
    return list(SWITCH_SPECS.keys())


def list_jack_types() -> List[str]:
    """Return list of supported jack types."""
    return list(JACK_SPECS.keys())


def list_body_styles() -> List[str]:
    """Return list of supported body styles."""
    return list(CONTROL_CAVITY_SPECS.keys())


def get_pickup_spec(pickup_type: str) -> Optional[Dict[str, float]]:
    """Get cavity spec for a pickup type."""
    return PICKUP_CAVITY_SPECS.get(pickup_type.lower().strip())


def get_control_spec(body_style: str) -> Optional[Dict[str, float]]:
    """Get control cavity spec for a body style."""
    return CONTROL_CAVITY_SPECS.get(body_style.lower().strip())
