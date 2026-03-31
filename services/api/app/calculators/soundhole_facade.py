"""
soundhole_facade.py — Public router-facing soundhole API (DECOMP-002 Phase 6).

Entry points used by instrument_geometry routers: SoundholeSpec, analyze_soundhole,
compute_soundhole_spec, check_soundhole_position, list_body_styles, get_standard_diameter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Literal, Optional

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


class SoundholeType(str, Enum):
    """Supported soundhole types for the soundhole generator dropdown."""
    ROUND = "round"
    OVAL = "oval"
    SPIRAL = "spiral"
    FHOLE = "fhole"


# Default spiral parameters (from Williams 2019 acoustic research)
SPIRAL_DEFAULTS: Dict[str, float] = {
    "slot_width_mm": 14.0,      # P:A = 0.143 — above 0.10 threshold
    "start_radius_mm": 10.0,
    "growth_rate_k": 0.18,
    "turns": 1.1,
}


@dataclass
class SpiralParams:
    """Parameters for spiral soundhole geometry."""
    slot_width_mm: float = 14.0
    start_radius_mm: float = 10.0
    growth_rate_k: float = 0.18
    turns: float = 1.1
    rotation_deg: float = 0.0
    center_x_mm: float = 0.0
    center_y_mm: float = 0.0

    def to_dict(self) -> dict:
        return {
            "slot_width_mm": self.slot_width_mm,
            "start_radius_mm": self.start_radius_mm,
            "growth_rate_k": self.growth_rate_k,
            "turns": self.turns,
            "rotation_deg": self.rotation_deg,
            "center_x_mm": self.center_x_mm,
            "center_y_mm": self.center_y_mm,
        }


@dataclass
class SoundholeSpec:
    """Soundhole specification with placement and sizing."""

    diameter_mm: float
    position_from_neck_block_mm: float
    body_style: str
    gate: str  # GREEN, YELLOW, RED
    notes: List[str] = field(default_factory=list)
    soundhole_type: SoundholeType = SoundholeType.ROUND
    # Spiral-specific params (only populated for spiral type)
    spiral_params: Optional[SpiralParams] = None
    # Computed metrics (populated for all types)
    area_mm2: Optional[float] = None
    perimeter_mm: Optional[float] = None
    pa_ratio_mm_inv: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {
            "diameter_mm": self.diameter_mm,
            "position_from_neck_block_mm": self.position_from_neck_block_mm,
            "body_style": self.body_style,
            "gate": self.gate,
            "notes": self.notes,
            "soundhole_type": self.soundhole_type.value,
        }
        if self.spiral_params:
            result["spiral_params"] = self.spiral_params.to_dict()
        if self.area_mm2 is not None:
            result["area_mm2"] = round(self.area_mm2, 2)
        if self.perimeter_mm is not None:
            result["perimeter_mm"] = round(self.perimeter_mm, 2)
        if self.pa_ratio_mm_inv is not None:
            result["pa_ratio_mm_inv"] = round(self.pa_ratio_mm_inv, 4)
        return result


def compute_soundhole_spec(
    body_style: str,
    body_length_mm: float,
    custom_diameter_mm: Optional[float] = None,
    soundhole_type: SoundholeType = SoundholeType.ROUND,
    spiral_params: Optional[SpiralParams] = None,
) -> SoundholeSpec:
    """
    Compute soundhole specification for a given body style and type.

    Args:
        body_style: Guitar body style (dreadnought, om_000, parlor, etc.)
        body_length_mm: Body length from neck block to tail block
        custom_diameter_mm: Override standard diameter if provided (for round/oval)
        soundhole_type: Type of soundhole (round, oval, spiral, fhole)
        spiral_params: Optional parameters for spiral soundholes

    Returns:
        SoundholeSpec with diameter, position, gate status, and type-specific geometry
    """
    import math
    notes: List[str] = []
    gate = "GREEN"

    # Normalize body style
    style_key = body_style.lower().replace("-", "_").replace(" ", "_")

    # Handle archtop / f-holes separately
    if style_key == "archtop" or soundhole_type == SoundholeType.FHOLE:
        return SoundholeSpec(
            diameter_mm=0.0,
            position_from_neck_block_mm=0.0,
            body_style=body_style,
            gate="YELLOW",
            notes=["F-hole design uses separate f-hole calculator"],
            soundhole_type=SoundholeType.FHOLE,
        )

    # Handle spiral type
    if soundhole_type == SoundholeType.SPIRAL:
        params = spiral_params or SpiralParams()

        # Closed-form spiral geometry
        theta_end = params.turns * 2 * math.pi
        r_end = params.start_radius_mm * math.exp(params.growth_rate_k * theta_end)
        alpha = math.atan(1.0 / params.growth_rate_k)
        one_wall_length = (r_end - params.start_radius_mm) / math.sin(alpha)

        perim_mm = 2.0 * one_wall_length
        area_mm2 = params.slot_width_mm * one_wall_length
        pa_ratio = perim_mm / area_mm2 if area_mm2 > 0 else 0.0

        # Equivalent diameter for position calculations
        equiv_diameter = 2 * math.sqrt(area_mm2 / math.pi)

        # P:A threshold check (Williams 2019)
        if pa_ratio >= 0.10:
            notes.append(f"P:A = {pa_ratio:.3f} mm⁻¹ — above Williams threshold (0.10). Good acoustic efficiency.")
        else:
            notes.append(f"P:A = {pa_ratio:.3f} mm⁻¹ — below threshold. Increase slot width for efficiency gain.")
            gate = "YELLOW"

        # Slot width validation
        if params.slot_width_mm < 10.0:
            notes.append(f"Slot width {params.slot_width_mm}mm is narrow (min practical CNC: 8-10mm)")
            gate = "YELLOW" if gate == "GREEN" else gate
        elif params.slot_width_mm > 25.0:
            notes.append(f"Slot width {params.slot_width_mm}mm is very wide; P:A will be low")
            gate = "YELLOW" if gate == "GREEN" else gate

        # Growth rate validation
        if params.growth_rate_k > 0.35:
            notes.append(f"Growth rate k={params.growth_rate_k} is high — spiral expands rapidly")
            gate = "YELLOW" if gate == "GREEN" else gate
        elif params.growth_rate_k < 0.08:
            notes.append(f"Growth rate k={params.growth_rate_k} is low — spiral is nearly circular")

        # Calculate position (spiral typically positioned like traditional soundhole)
        position_fraction = STANDARD_POSITION_FRACTION.get(style_key, 0.50)
        position_mm = body_length_mm * position_fraction

        return SoundholeSpec(
            diameter_mm=round(equiv_diameter, 1),
            position_from_neck_block_mm=round(position_mm, 1),
            body_style=body_style,
            gate=gate,
            notes=notes,
            soundhole_type=SoundholeType.SPIRAL,
            spiral_params=params,
            area_mm2=area_mm2,
            perimeter_mm=perim_mm,
            pa_ratio_mm_inv=pa_ratio,
        )

    # Handle oval type
    if soundhole_type == SoundholeType.OVAL:
        # For oval, custom_diameter_mm represents the major axis
        width_mm = custom_diameter_mm if custom_diameter_mm else 80.0
        height_mm = width_mm * 1.375  # 80×110mm Selmer ratio

        a = width_mm / 2
        b = height_mm / 2
        area_mm2 = math.pi * a * b
        # Ramanujan's approximation for ellipse perimeter
        h = ((a - b) ** 2) / ((a + b) ** 2)
        perim_mm = math.pi * (a + b) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h)))
        pa_ratio = perim_mm / area_mm2 if area_mm2 > 0 else 0.0
        equiv_diameter = 2 * math.sqrt(area_mm2 / math.pi)

        notes.append(f"Oval soundhole {width_mm:.0f}×{height_mm:.0f}mm (Selmer/Maccaferri style)")

        position_fraction = STANDARD_POSITION_FRACTION.get(style_key, 0.50)
        position_mm = body_length_mm * position_fraction

        return SoundholeSpec(
            diameter_mm=round(equiv_diameter, 1),
            position_from_neck_block_mm=round(position_mm, 1),
            body_style=body_style,
            gate=gate,
            notes=notes,
            soundhole_type=SoundholeType.OVAL,
            area_mm2=area_mm2,
            perimeter_mm=perim_mm,
            pa_ratio_mm_inv=pa_ratio,
        )

    # Default: round soundhole
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

    # Calculate round hole area/perimeter
    radius_mm = diameter_mm / 2
    area_mm2 = math.pi * radius_mm ** 2
    perim_mm = 2 * math.pi * radius_mm
    pa_ratio = perim_mm / area_mm2 if area_mm2 > 0 else 0.0

    return SoundholeSpec(
        diameter_mm=diameter_mm,
        position_from_neck_block_mm=round(position_mm, 1),
        body_style=body_style,
        gate=gate,
        notes=notes,
        soundhole_type=SoundholeType.ROUND,
        area_mm2=area_mm2,
        perimeter_mm=perim_mm,
        pa_ratio_mm_inv=pa_ratio,
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


def list_soundhole_types() -> List[Dict]:
    """Return list of supported soundhole types with descriptions."""
    return [
        {
            "type": SoundholeType.ROUND.value,
            "label": "Round",
            "description": "Traditional circular soundhole. Standard for most acoustic guitars.",
        },
        {
            "type": SoundholeType.OVAL.value,
            "label": "Oval",
            "description": "Oval/elliptical soundhole. Selmer/Maccaferri gypsy jazz style.",
        },
        {
            "type": SoundholeType.SPIRAL.value,
            "label": "Spiral",
            "description": "Logarithmic spiral slot. High P:A ratio for acoustic efficiency (Williams 2019).",
        },
        {
            "type": SoundholeType.FHOLE.value,
            "label": "F-hole",
            "description": "Archtop f-holes. Use dedicated f-hole calculator.",
        },
    ]
