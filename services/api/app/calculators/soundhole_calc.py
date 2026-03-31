"""
soundhole_calc.py — Acoustic Guitar Soundhole Calculator
=========================================================
Option B: standalone module covering Helmholtz air resonance (multi-port,
perimeter-corrected), structural ring-width safety check, placement
validation, and calibrated family presets.

Connects to:
  calculators/acoustic_body_volume.py  — calculate_body_volume() provides V
  calculators/plate_design/calibration.py — AIR_SPEED_OF_SOUND_M_S
  instrument_geometry/models/*.json    — body specs with soundhole_diameter_mm

Physics references:
  Gore & Gilet, Contemporary Acoustic Guitar Design and Build, Vol. 1
  Fletcher & Rossing, The Physics of Musical Instruments, Ch. 9-10
  Caldersmith, Designing a Guitar Family, 1978

All dimensions in SI units internally (m, m², m³).
External API accepts mm and converts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple

# ── Pure physics extracted to soundhole_physics.py (DECOMP-002 Phase 1) ───────
# These imports make the physics functions available from either module.
# Local definitions below are retained for backward compatibility.
from .soundhole_physics import (
    PortSpec as PortSpecPhysics,
    compute_port_neck_length as compute_port_neck_length_physics,
    compute_helmholtz_multiport as compute_helmholtz_multiport_physics,
    exact_coupled_eigenfreq,
)

# ── Two-cavity resonator extracted to soundhole_resonator.py (DECOMP-002 Phase 2)
# These imports provide backward compatibility for existing code.
from .soundhole_resonator import (
    TwoCavityResult,
    analyze_two_cavity,
    compute_sensitivity_curve,
)

# ── Stiffness reduction extracted to soundhole_stiffness.py (DECOMP-002 Phase 4)
# These imports provide backward compatibility for existing code.
from .soundhole_stiffness import (
    STIFFNESS_K,
    BRACING_RESTORE_DEFAULT,
    StiffnessResult,
    compute_top_stiffness_reduction,
    BRACING_PRESCRIPTIONS,
    BracingIndicatorResult,
    get_bracing_implication,
)

# ── Climate and humidity corrections (DECOMP-002 Phase 5) ─────────────────────
from .soundhole_climate import (
    CLIMATE_ZONES,
    get_ring_width_humidity_note,
    list_climate_zones,
    get_climate_zone,
    estimate_seasonal_movement,
)

# ── Side ports / F-hole (DECOMP-002 Phase 3) ────────────────────────────────────
from .soundhole_ports import (
    SIDE_PORT_POSITIONS,
    SIDE_PORT_TYPES,
    SidePortResult,
    SidePortSpec,
    analyze_side_port,
    solve_for_diameter_mm,
    solve_for_diameter_with_side_port_mm,
)

# ── Preset tables (DECOMP-002 Phase 5) ────────────────────────────────────────
from .soundhole_presets import (
    BODY_DIMENSION_PRESETS,
    PRESETS,
    TOP_SPECIES_THICKNESS,
    analyze_preset,
    get_preset,
    get_species_thickness,
    list_presets,
    list_top_species,
)

# ── Constants ─────────────────────────────────────────────────────────────────

C_AIR: float = 343.0       # Speed of sound in air at 20°C (m/s)
K0: float = 1.7            # Round-hole end-correction baseline (dimensionless)
GAMMA: float = 0.02        # Perimeter sensitivity constant (calibrate from measurements)
                            # Expected error before calibration: ±10-15 Hz
                            # Expected error after calibration: ±3-5 Hz

# Structural safety constants
RING_WIDTH_RADIUS_FRACTION: float = 0.15  # min ring = 15% of soundhole radius
RING_WIDTH_ABSOLUTE_MIN_MM: float = 6.0   # hard floor regardless of hole size

# Placement safety fractions (fraction of body length from neck block)
PLACEMENT_X_MIN_FRACTION: float = 0.20   # clear of neck block
PLACEMENT_X_MAX_FRACTION: float = 0.70   # clear of tail block / lower structure


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class PortSpec:
    """
    One opening in the guitar body.

    A guitar can have multiple ports: main soundhole, side port(s), back port.
    Each is computed independently then combined via area-weighted averaging.

    Attributes:
        area_m2:            Opening area in m²
        perim_m:            Opening perimeter in m
        location:           Where on the body the port sits
        thickness_m:        Plate thickness at the opening (drives L_eff)
        label:              Human-readable name for UI display
    """
    area_m2: float
    perim_m: float
    location: Literal["top", "side", "back"] = "top"
    thickness_m: float = 0.0025         # 2.5mm default top thickness
    label: str = "Main soundhole"

    @classmethod
    def from_circle_mm(
        cls,
        diameter_mm: float,
        location: Literal["top", "side", "back"] = "top",
        thickness_mm: float = 2.5,
        label: str = "Round soundhole",
    ) -> "PortSpec":
        """Convenience constructor for circular holes."""
        r = (diameter_mm / 2) / 1000.0   # mm → m
        return cls(
            area_m2=math.pi * r * r,
            perim_m=2 * math.pi * r,
            location=location,
            thickness_m=thickness_mm / 1000.0,
            label=label,
        )

    @classmethod
    def from_oval_mm(
        cls,
        width_mm: float,
        height_mm: float,
        location: Literal["top", "side", "back"] = "top",
        thickness_mm: float = 2.5,
        label: str = "Oval soundhole",
    ) -> "PortSpec":
        """Convenience constructor for oval/elliptical holes."""
        a = (width_mm / 2) / 1000.0
        b = (height_mm / 2) / 1000.0
        area = math.pi * a * b
        # Ramanujan's approximation for ellipse perimeter
        h = ((a - b) ** 2) / ((a + b) ** 2)
        perim = math.pi * (a + b) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h)))
        return cls(
            area_m2=area,
            perim_m=perim,
            location=location,
            thickness_m=thickness_mm / 1000.0,
            label=label,
        )

    @classmethod
    def from_spiral_mm(
        cls,
        slot_width_mm: float,
        start_radius_mm: float = 10.0,
        growth_rate_k: float = 0.18,
        turns: float = 1.1,
        location: Literal["top", "side", "back"] = "top",
        thickness_mm: float = 2.5,
        label: str = "Spiral soundhole",
    ) -> "PortSpec":
        """
        Convenience constructor for logarithmic spiral soundholes.

        Closed-form geometry for constant-width spiral slot:
            r(θ) = r0 × e^(k×θ)
            Arc length: L = (r_end - r0) / sin(atan(1/k))
            Perimeter: P = 2 × L (two walls)
            Area: A = slot_width × L
            P:A ratio: 2/slot_width (independent of k, turns, r0)

        P:A > 0.10 mm⁻¹ required for acoustic efficiency gain over round hole.
        For 14mm slot: P:A = 0.143 mm⁻¹ — well above threshold.

        Args:
            slot_width_mm:    Width of the spiral slot (14-20mm optimal)
            start_radius_mm:  Inner starting radius r0 (typically 8-12mm)
            growth_rate_k:    Logarithmic growth rate per radian (0.12-0.25)
            turns:            Number of full turns (0.8-1.5 typical)
            location:         Where on the body ("top", "side", "back")
            thickness_mm:     Plate thickness at the opening
            label:            Human-readable name

        Returns:
            PortSpec with calculated area and perimeter
        """
        if growth_rate_k <= 0:
            raise ValueError("growth_rate_k must be positive")
        if slot_width_mm <= 0 or start_radius_mm <= 0 or turns <= 0:
            raise ValueError("slot_width_mm, start_radius_mm, and turns must be positive")

        # Closed-form calculation
        theta_end = turns * 2 * math.pi
        r_end = start_radius_mm * math.exp(growth_rate_k * theta_end)
        alpha = math.atan(1.0 / growth_rate_k)
        one_wall_length = (r_end - start_radius_mm) / math.sin(alpha)

        # Perimeter = 2 walls, Area = slot_width × arc_length
        perim_mm = 2.0 * one_wall_length
        area_mm2 = slot_width_mm * one_wall_length

        # Convert to m and m²
        return cls(
            area_m2=area_mm2 / 1e6,
            perim_m=perim_mm / 1000.0,
            location=location,
            thickness_m=thickness_mm / 1000.0,
            label=label,
        )

    @property
    def diameter_equiv_mm(self) -> float:
        """Equivalent circular diameter for display purposes."""
        return 2 * math.sqrt(self.area_m2 / math.pi) * 1000.0

    @property
    def area_cm2(self) -> float:
        return self.area_m2 * 10000.0


@dataclass
class RingWidthCheck:
    """Result of the structural ring-width safety check."""
    status: Literal["GREEN", "YELLOW", "RED"]
    ring_width_mm: float
    ring_width_min_mm: float
    margin_mm: float            # positive = safe margin, negative = deficit
    message: str
    construction_note: str


@dataclass
class PlacementCheck:
    """Result of soundhole placement validation."""
    valid: bool
    x_from_neck_mm: float
    x_min_mm: float
    x_max_mm: float
    fraction_of_body: float     # 0–1
    message: str
    construction_note: str


@dataclass
class SoundholeResult:
    """
    Complete soundhole analysis result.

    The Helmholtz frequency prediction accuracy depends on calibration of GAMMA.
    Before calibration: ±10-15 Hz. After calibration with 3+ measured instruments: ±3-5 Hz.
    """
    # Air resonance
    f_helmholtz_hz: float
    f_helmholtz_note: str           # e.g. "G#2" — nearest musical note

    # Individual port contributions
    ports: List[PortSpec]
    port_details: List[Dict]        # per-port L_eff, area fraction

    # Structural checks
    ring_width: RingWidthCheck
    placement: PlacementCheck

    # Aggregates
    total_area_cm2: float
    total_area_m2: float
    body_volume_liters: float

    # Guidance
    warnings: List[str] = field(default_factory=list)
    construction_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "f_helmholtz_hz": round(self.f_helmholtz_hz, 1),
            "f_helmholtz_note": self.f_helmholtz_note,
            "total_area_cm2": round(self.total_area_cm2, 2),
            "body_volume_liters": round(self.body_volume_liters, 2),
            "ring_width_status": self.ring_width.status,
            "ring_width_mm": round(self.ring_width.ring_width_mm, 1),
            "ring_width_min_mm": round(self.ring_width.ring_width_min_mm, 1),
            "placement_valid": self.placement.valid,
            "x_from_neck_mm": round(self.placement.x_from_neck_mm, 1),
            "warnings": self.warnings,
            "construction_notes": self.construction_notes,
        }


# ── Core Physics Functions ─────────────────────────────────────────────────────

def compute_port_neck_length(
    area_m2: float,
    perim_m: float,
    thickness_m: float,
    k0: float = K0,
    gamma: float = GAMMA,
) -> float:
    """
    Compute effective acoustic neck length for a single port.

    The port acts as a short tube. Its effective length is:
        L_eff = thickness + k × r_eq

    where k is the end-correction factor, modified by the perimeter-to-area
    ratio to account for non-circular shapes:
        k = k0 × (1 + γ × P / √A)

    This perimeter correction explains why:
    - Two small holes of equal total area resonate LOWER than one large hole
    - Oval and D-shaped holes resonate slightly lower than circular equivalents
    - F-holes resonate lower than round holes of equal total area

    Args:
        area_m2:    Port opening area (m²)
        perim_m:    Port perimeter (m)
        thickness_m: Plate thickness at the port (m)
        k0:         Baseline end-correction coefficient (default 1.7 for round)
        gamma:      Perimeter sensitivity (default 0.02 — calibrate from measurements)

    Returns:
        L_eff in metres
    """
    if area_m2 <= 0:
        return thickness_m

    r_eq = math.sqrt(area_m2 / math.pi)                    # equivalent radius
    k = k0 * (1.0 + gamma * perim_m / math.sqrt(area_m2))  # perimeter-corrected
    L_eff = thickness_m + k * r_eq
    return L_eff


# Plate-air coupling correction
# The Helmholtz formula gives the UNCOUPLED air resonance.
# In an assembled instrument the top plate's mass shifts the resonance DOWN
# by approximately 5-10%. A plate_mass_factor of 0.92 corrects this.
# Calibrated against Martin OM (117→108 Hz), D-28 (107→98 Hz), J-45 (108→100 Hz).
PLATE_MASS_FACTOR: float = 0.92


def compute_helmholtz_multiport(
    volume_m3: float,
    ports: List[PortSpec],
    k0: float = K0,
    gamma: float = GAMMA,
    plate_mass_factor: float = PLATE_MASS_FACTOR,
) -> Tuple[float, List[Dict]]:
    """
    Compute Helmholtz resonance frequency for any number of ports.

    Multi-port formula: ports act as parallel acoustic masses.
        A_total = Σ Aᵢ
        L_eff_weighted = Σ(Aᵢ × L_eff_i) / Σ Aᵢ
        f_H = (c / 2π) × √(A_total / (V × L_eff_weighted))

    This is the Gore-style modified Helmholtz equation used by professional
    acoustic guitar designers. It handles round holes, ovals, side ports,
    f-holes, and combinations thereof through the same formula.

    Args:
        volume_m3:  Body internal volume (m³)
        ports:      List of PortSpec — each opening
        k0, gamma:  End-correction constants (see compute_port_neck_length)

    Returns:
        (f_helmholtz_hz, port_details_list)
    """
    if volume_m3 <= 0 or not ports:
        return 0.0, []

    total_area = sum(p.area_m2 for p in ports)
    if total_area <= 0:
        return 0.0, []

    weighted_L = 0.0
    port_details = []

    for p in ports:
        L_eff = compute_port_neck_length(p.area_m2, p.perim_m, p.thickness_m, k0, gamma)
        weighted_L += p.area_m2 * L_eff
        port_details.append({
            "label": p.label,
            "location": p.location,
            "area_cm2": round(p.area_m2 * 10000, 2),
            "area_fraction": round(p.area_m2 / total_area, 3),
            "L_eff_mm": round(L_eff * 1000, 2),
            "equiv_diameter_mm": round(p.diameter_equiv_mm, 1),
        })

    L_eff_weighted = weighted_L / total_area
    f_uncoupled = (C_AIR / (2 * math.pi)) * math.sqrt(total_area / (volume_m3 * L_eff_weighted))
    f_H = f_uncoupled * plate_mass_factor   # plate-air coupling correction

    return f_H, port_details


def check_ring_width(
    soundhole_radius_mm: float,
    ring_width_mm: float,
) -> RingWidthCheck:
    """
    Check structural adequacy of the ring of wood surrounding the soundhole.

    The ring of top material between the soundhole edge and the nearest structural
    element (brace, binding ledge, body edge) must be wide enough to resist splitting
    under string tension and seasonal humidity movement.

    Minimum ring width formula:
        min_ring = max(soundhole_radius × 0.15, 6.0 mm)

    The 15% of radius rule comes from thin-shell structural analysis.
    The 6.0 mm absolute minimum is empirical — thinner than this and tops
    split during seasonal humidity cycles (humidity swings in Houston alone
    can move a 400mm top 3-6mm seasonally).

    Status thresholds:
        GREEN:  ring_width ≥ min_ring × 1.5
        YELLOW: min_ring ≤ ring_width < min_ring × 1.5
        RED:    ring_width < min_ring

    Args:
        soundhole_radius_mm: Radius of the soundhole (or equivalent radius for ovals)
        ring_width_mm:       Measured width of wood ring at narrowest point

    Returns:
        RingWidthCheck with status and construction guidance
    """
    min_ring = max(soundhole_radius_mm * RING_WIDTH_RADIUS_FRACTION, RING_WIDTH_ABSOLUTE_MIN_MM)
    margin = ring_width_mm - min_ring

    if ring_width_mm >= min_ring * 1.5:
        status = "GREEN"
        message = f"Ring width {ring_width_mm:.1f}mm — adequate ({margin:.1f}mm margin)"
        note = "No additional reinforcement required."
    elif ring_width_mm >= min_ring:
        status = "YELLOW"
        message = f"Ring width {ring_width_mm:.1f}mm — marginal (min {min_ring:.1f}mm)"
        note = "Consider adding a thin soundhole patch (2mm spruce) glued to the inside of the top around the hole perimeter."
    else:
        status = "RED"
        deficit = min_ring - ring_width_mm
        message = f"Ring width {ring_width_mm:.1f}mm — below minimum ({min_ring:.1f}mm required, deficit {deficit:.1f}mm)"
        note = f"Reduce soundhole diameter by {deficit * 2:.1f}mm OR add a soundhole patch and short radial braces. Do not cut at this diameter without reinforcement."

    return RingWidthCheck(
        status=status,
        ring_width_mm=ring_width_mm,
        ring_width_min_mm=round(min_ring, 1),
        margin_mm=round(margin, 1),
        message=message,
        construction_note=note,
    )


def validate_placement(
    x_from_neck_mm: float,
    body_length_mm: float,
) -> PlacementCheck:
    """
    Validate soundhole center position along the body length axis.

    Safe zone: between 20% and 70% of body length from neck block.
    - Below 20%: too close to neck block — structural interference, poor acoustics
    - Above 70%: too close to tail block — poor coupling to top modes

    The traditional 1/3 body length placement (33%) is both historically derived
    and acoustically valid: it places the hole near the antinode of the top's
    fundamental longitudinal mode.

    Args:
        x_from_neck_mm:  Distance of soundhole center from neck block (mm)
        body_length_mm:  Total internal body length (mm)

    Returns:
        PlacementCheck with validity, bounds, and construction guidance
    """
    x_min = body_length_mm * PLACEMENT_X_MIN_FRACTION
    x_max = body_length_mm * PLACEMENT_X_MAX_FRACTION
    fraction = x_from_neck_mm / body_length_mm
    traditional = body_length_mm * 0.333

    valid = x_min <= x_from_neck_mm <= x_max

    if valid:
        deviation = x_from_neck_mm - traditional
        if abs(deviation) < 10:
            message = f"Placement at {x_from_neck_mm:.0f}mm — traditional position (1/3 body length = {traditional:.0f}mm)"
            note = "Classic placement aligns hole with top's fundamental longitudinal mode antinode."
        elif deviation < 0:
            message = f"Placement at {x_from_neck_mm:.0f}mm — shifted {abs(deviation):.0f}mm toward neck vs traditional"
            note = "Slightly forward placement. May reduce bass response slightly. Verify bracing pattern allows this position."
        else:
            message = f"Placement at {x_from_neck_mm:.0f}mm — shifted {deviation:.0f}mm toward tail vs traditional"
            note = "Shifted toward lower bout. Lower bout placement can increase bass response but may conflict with X-brace intersection."
    else:
        if x_from_neck_mm < x_min:
            message = f"Placement at {x_from_neck_mm:.0f}mm — too close to neck block (min {x_min:.0f}mm)"
            note = "Move soundhole at least to 20% of body length from neck block to clear structural zone."
        else:
            message = f"Placement at {x_from_neck_mm:.0f}mm — too close to tail block (max {x_max:.0f}mm)"
            note = "Move soundhole toward neck end — current position interferes with tail block structural zone."

    return PlacementCheck(
        valid=valid,
        x_from_neck_mm=round(x_from_neck_mm, 1),
        x_min_mm=round(x_min, 1),
        x_max_mm=round(x_max, 1),
        fraction_of_body=round(fraction, 3),
        message=message,
        construction_note=note,
    )


# ── Extended helpers (two-cavity, volume-from-dimensions, plate–air coupling) ─
from .soundhole_extended import (
    PlateAirCouplingResult,
    compute_two_cavity_helmholtz,
    estimate_plate_air_coupling,
    volume_from_dimensions,
)

# ── Public router façade (DECOMP-002 Phase 6) ──────────────────────────────────
# GEOMETRY-002 — placement & sizing API; re-exported for backward compatibility.
from .soundhole_facade import (
    STANDARD_DIAMETERS_MM,
    SoundholeSpec,
    analyze_soundhole,
    check_soundhole_position,
    compute_soundhole_spec,
    get_standard_diameter,
    list_body_styles,
)
