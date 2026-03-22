"""
soundhole_facade.py — Public router-facing soundhole API (DECOMP-002 Phase 6).

Entry points used by instrument_geometry routers: SoundholeSpec, analyze_soundhole,
compute_soundhole_spec, check_soundhole_position, list_body_styles, get_standard_diameter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from .soundhole_physics import GAMMA, K0, hz_to_note
from .soundhole_presets import (
    POSITION_MAX_FRACTION,
    POSITION_MIN_FRACTION,
    STANDARD_DIAMETERS_MM,
    STANDARD_POSITION_FRACTION,
    get_standard_diameter,
    list_body_styles,
)

if TYPE_CHECKING:
    from .soundhole_calc import PortSpec, SoundholeResult


@dataclass
class SoundholeSpec:
    """Soundhole specification with placement and sizing."""

    diameter_mm: float
    position_from_neck_block_mm: float
    body_style: str
    gate: str  # GREEN, YELLOW, RED
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "diameter_mm": self.diameter_mm,
            "position_from_neck_block_mm": self.position_from_neck_block_mm,
            "body_style": self.body_style,
            "gate": self.gate,
            "notes": self.notes,
        }


def compute_soundhole_spec(
    body_style: str,
    body_length_mm: float,
    custom_diameter_mm: Optional[float] = None,
) -> SoundholeSpec:
    """
    Compute soundhole specification for a given body style.

    Args:
        body_style: Guitar body style (dreadnought, om_000, parlor, etc.)
        body_length_mm: Body length from neck block to tail block
        custom_diameter_mm: Override standard diameter if provided

    Returns:
        SoundholeSpec with diameter, position, and gate status
    """
    notes: List[str] = []
    gate = "GREEN"

    # Normalize body style
    style_key = body_style.lower().replace("-", "_").replace(" ", "_")

    # Handle archtop separately
    if style_key == "archtop":
        return SoundholeSpec(
            diameter_mm=0.0,
            position_from_neck_block_mm=0.0,
            body_style=body_style,
            gate="YELLOW",
            notes=["Archtop uses f-holes; use f-hole calculator instead"],
        )

    # Get standard diameter
    if style_key in STANDARD_DIAMETERS_MM:
        standard_diameter = STANDARD_DIAMETERS_MM[style_key]
    else:
        # Unknown style, use average
        standard_diameter = 95.0
        notes.append(f"Unknown body style '{body_style}'; using default 95mm diameter")
        gate = "YELLOW"

    # Use custom diameter if provided
    diameter_mm = custom_diameter_mm if custom_diameter_mm is not None else standard_diameter

    # Validate diameter range
    if diameter_mm < 75.0:
        notes.append(f"Diameter {diameter_mm}mm below typical minimum (75mm)")
        gate = "RED"
    elif diameter_mm < 80.0:
        notes.append(f"Diameter {diameter_mm}mm is small; may affect bass response")
        gate = "YELLOW" if gate == "GREEN" else gate
    elif diameter_mm > 110.0:
        notes.append(f"Diameter {diameter_mm}mm exceeds typical maximum (110mm)")
        gate = "RED"
    elif diameter_mm > 105.0:
        notes.append(f"Diameter {diameter_mm}mm is large; ensure adequate ring width")
        gate = "YELLOW" if gate == "GREEN" else gate

    # Calculate position
    position_fraction = STANDARD_POSITION_FRACTION.get(style_key, 0.50)
    position_mm = body_length_mm * position_fraction

    # Validate position against body length
    if position_mm < body_length_mm * POSITION_MIN_FRACTION:
        notes.append("Position is too close to neck block")
        gate = "RED"
    elif position_mm > body_length_mm * POSITION_MAX_FRACTION:
        notes.append("Position is too close to bridge area")
        gate = "RED"

    # Check that soundhole fits within body (rough check)
    if position_mm - (diameter_mm / 2) < 20:
        notes.append("Soundhole edge too close to neck block")
        gate = "RED"

    return SoundholeSpec(
        diameter_mm=diameter_mm,
        position_from_neck_block_mm=round(position_mm, 1),
        body_style=body_style,
        gate=gate,
        notes=notes,
    )


def check_soundhole_position(
    diameter_mm: float,
    position_mm: float,
    body_length_mm: float,
) -> str:
    """
    Check if soundhole position is valid for given body length.

    Args:
        diameter_mm: Soundhole diameter in mm
        position_mm: Center position from neck block in mm
        body_length_mm: Total body length in mm

    Returns:
        Gate status: GREEN, YELLOW, or RED
    """
    if body_length_mm <= 0:
        return "RED"

    position_fraction = position_mm / body_length_mm

    # Check position fraction
    if position_fraction < 0.40 or position_fraction > 0.60:
        return "RED"
    elif position_fraction < POSITION_MIN_FRACTION or position_fraction > POSITION_MAX_FRACTION:
        return "YELLOW"

    # Check soundhole edges
    front_edge = position_mm - (diameter_mm / 2)
    rear_edge = position_mm + (diameter_mm / 2)

    # Front edge should be at least 20mm from neck block
    if front_edge < 20:
        return "RED"
    elif front_edge < 30:
        return "YELLOW"

    # Rear edge should leave room for bracing (at least 40mm from end)
    if rear_edge > body_length_mm - 40:
        return "RED"
    elif rear_edge > body_length_mm - 60:
        return "YELLOW"

    return "GREEN"


def analyze_soundhole(
    volume_m3: float,
    ports: List["PortSpec"],
    ring_width_mm: float,
    x_from_neck_mm: float,
    body_length_mm: float,
    k0: float = K0,
    gamma: float = GAMMA,
) -> "SoundholeResult":
    """
    Complete soundhole analysis.

    Runs Helmholtz computation, ring-width check, and placement validation
    in one call, returning a fully annotated result with construction guidance.

    Args:
        volume_m3:        Body internal volume (m³)
        ports:            List of PortSpec objects (one or more openings)
        ring_width_mm:    Width of wood ring at narrowest point (mm)
        x_from_neck_mm:   Soundhole center distance from neck block (mm)
        body_length_mm:   Internal body length (mm)
        k0, gamma:        End-correction constants

    Returns:
        SoundholeResult with all checks, predictions, and guidance
    """
    # Late import avoids circular dependency with soundhole_calc (core types).
    from .soundhole_calc import (
        SoundholeResult,
        check_ring_width,
        compute_helmholtz_multiport,
        validate_placement,
    )

    warnings: List[str] = []
    notes: List[str] = []

    # Air resonance
    f_H, port_details = compute_helmholtz_multiport(volume_m3, ports, k0, gamma)

    # Ring width — use largest port's equivalent radius as the reference
    if ports:
        main_port = max(ports, key=lambda p: p.area_m2)
        radius_ref = main_port.diameter_equiv_mm / 2.0
    else:
        radius_ref = 0.0
    ring_check = check_ring_width(radius_ref, ring_width_mm)

    # Placement
    placement_check = validate_placement(x_from_neck_mm, body_length_mm)

    # Assemble warnings and notes
    if ring_check.status == "RED":
        warnings.append(ring_check.message)
        notes.append(ring_check.construction_note)
    elif ring_check.status == "YELLOW":
        warnings.append(ring_check.message)
        notes.append(ring_check.construction_note)

    if not placement_check.valid:
        warnings.append(placement_check.message)
        notes.append(placement_check.construction_note)

    if f_H < 70:
        warnings.append(f"Air resonance {f_H:.0f} Hz is very low — check body volume and port area")
    elif f_H > 160:
        warnings.append(f"Air resonance {f_H:.0f} Hz is very high — consider larger body or smaller hole")

    side_ports = [p for p in ports if p.location == "side"]
    if side_ports:
        notes.append(
            f"{len(side_ports)} side port(s) detected. Side ports primarily affect radiation "
            "pattern and player-ear presence. Helmholtz shift from side ports is typically "
            "small (+3-8 Hz) unless port area is large (> 8 cm²)."
        )

    notes.append(
        f"Helmholtz prediction accuracy: ±10-15 Hz before calibration of GAMMA constant. "
        "Calibrate by measuring f_H on 3+ known instruments and fitting GAMMA to minimize error."
    )

    total_area = sum(p.area_m2 for p in ports)

    return SoundholeResult(
        f_helmholtz_hz=round(f_H, 1),
        f_helmholtz_note=hz_to_note(f_H),
        ports=ports,
        port_details=port_details,
        ring_width=ring_check,
        placement=placement_check,
        total_area_cm2=round(total_area * 10000, 2),
        total_area_m2=total_area,
        body_volume_liters=round(volume_m3 * 1000, 2),
        warnings=warnings,
        construction_notes=notes,
    )
