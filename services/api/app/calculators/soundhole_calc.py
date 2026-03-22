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
    hz_to_note,
    compute_two_cavity_helmholtz as compute_two_cavity_helmholtz_physics,
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


# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONS — Inverse solver, two-cavity model, side port extensions
# (Side port / F-hole symbols re-exported from soundhole_ports at top of file)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Sensitivity curve ─────────────────────────────────────────────────────────
# compute_sensitivity_curve() moved to soundhole_resonator.py (DECOMP-002 Phase 2)
# Backward compat re-export is imported at the top of this file.


# ── Two-cavity (Selmer/Maccaferri) model ─────────────────────────────────────

def compute_two_cavity_helmholtz(
    # Main body cavity
    volume_main_m3: float,
    main_ports: List[PortSpec],
    # Internal resonator cavity
    volume_internal_m3: float,
    aperture_area_m2: float,
    aperture_perim_m: float,
    aperture_thickness_m: float = 0.003,
    k0: float = K0,
    gamma: float = GAMMA,
    plate_mass_factor: float = PLATE_MASS_FACTOR,
) -> Dict:
    """
    Two-cavity Helmholtz model for Selmer/Maccaferri instruments with internal resonator.

    The Maccaferri original used an internal resonator — a second air chamber
    connected to the main body cavity via an aperture. This produces two distinct
    air resonance peaks rather than one.

    Model (approximate — two uncoupled resonators):
        f_H1 = main body resonance (D-hole/oval → outside air)
        f_H2 = internal resonator (internal volume → body via aperture)

    The true coupled system requires a 2×2 eigenvalue solution. This approximation
    predicts the two peaks within ~10 Hz, which is sufficient for design purposes.

    Args:
        volume_main_m3:       Main body cavity volume (m³)
        main_ports:           Ports from main cavity to outside
        volume_internal_m3:   Internal resonator volume (m³)
                              Typical Maccaferri: 0.0003–0.0006 m³ (0.3–0.6 L)
        aperture_area_m2:     Area of aperture from resonator to main cavity (m²)
        aperture_perim_m:     Perimeter of that aperture (m)
        aperture_thickness_m: Wall thickness at aperture (m)

    Returns:
        Dict with f_H1, f_H2, descriptions, and design guidance
    """
    # f_H1: main body resonance (same as standard model)
    f_H1, port_details = compute_helmholtz_multiport(
        volume_main_m3, main_ports, k0, gamma, plate_mass_factor
    )

    # f_H2: internal resonator — resonator volume + aperture (opening into body)
    aperture_port = PortSpec(
        area_m2=aperture_area_m2,
        perim_m=aperture_perim_m,
        location="top",
        thickness_m=aperture_thickness_m,
    )
    # Internal resonator resonates between its own volume and the main body cavity
    # Treat main body as the "outside" for the internal resonator
    f_H2_raw, _ = compute_helmholtz_multiport(
        volume_internal_m3, [aperture_port], k0, gamma, plate_mass_factor=1.0
    )

    # Coupling between the two cavities shifts both peaks slightly
    # Simple coupling correction: peaks repel each other
    delta = abs(f_H1 - f_H2_raw) * 0.1   # ~10% repulsion (empirical)
    if f_H1 < f_H2_raw:
        f_H1_coupled = f_H1 - delta / 2
        f_H2_coupled = f_H2_raw + delta / 2
    else:
        f_H1_coupled = f_H1 + delta / 2
        f_H2_coupled = f_H2_raw - delta / 2

    return {
        "f_H1_hz": round(f_H1_coupled, 1),
        "f_H2_hz": round(f_H2_coupled, 1),
        "f_H1_note": hz_to_note(f_H1_coupled),
        "f_H2_note": hz_to_note(f_H2_coupled),
        "f_H1_description": "Main body air resonance (D-hole/oval opening to outside air)",
        "f_H2_description": "Internal resonator peak (resonator cavity coupled to main body)",
        "separation_hz": round(abs(f_H2_coupled - f_H1_coupled), 1),
        "port_details": port_details,
        "design_note": (
            "Two distinct air peaks broaden the bass response region. "
            f"f_H1 ({f_H1_coupled:.0f} Hz) = standard Helmholtz for this hole size and volume. "
            f"f_H2 ({f_H2_coupled:.0f} Hz) depends on internal resonator volume and aperture. "
            "To tune f_H2: increase aperture area to raise it, decrease internal volume to raise it. "
            "Typical Maccaferri separation: 20–40 Hz."
        ),
    }


# ── Body dimensions → volume ──────────────────────────────────────────────────

def volume_from_dimensions(
    lower_bout_mm: float,
    upper_bout_mm: float,
    waist_mm: float,
    body_length_mm: float,
    depth_endblock_mm: float,
    depth_neck_mm: float,
    shape_factor: float = 0.85,
) -> Dict:
    """
    Compute body volume from physical dimensions.

    Mirrors acoustic_body_volume.calculate_body_volume() exactly.
    Uses elliptical cross-section integration divided into three sections.

    Args:
        lower_bout_mm:     Width at widest point (lower bout)
        upper_bout_mm:     Width at upper bout
        waist_mm:          Width at narrowest point (waist)
        body_length_mm:    Heel-to-endblock internal length
        depth_endblock_mm: Rim depth at endblock (deepest)
        depth_neck_mm:     Rim depth at neck joint
        shape_factor:      Body shape correction (0.80–0.90, default 0.85)

    Returns:
        Dict with volume_liters, volume_cubic_inches, section_volumes
    """
    L = body_length_mm
    lower_len = L * 0.40
    waist_len  = L * 0.25
    upper_len  = L * 0.35

    avg_depth = (depth_endblock_mm + depth_neck_mm) / 2.0

    # Elliptical cross-sections: π × (w/2) × (d/2) × shape_factor
    lower_area = math.pi * (lower_bout_mm / 2) * (depth_endblock_mm / 2) * shape_factor
    waist_area  = math.pi * (waist_mm / 2)     * (avg_depth / 2)          * shape_factor
    upper_area  = math.pi * (upper_bout_mm / 2) * (depth_neck_mm / 2)     * shape_factor

    V_lower = (lower_area + waist_area) / 2.0 * lower_len   # trapezoidal
    V_waist = waist_area * waist_len
    V_upper = (waist_area + upper_area) / 2.0 * upper_len

    total_mm3 = V_lower + V_waist + V_upper
    total_L   = total_mm3 / 1e6

    # Calibration: the elliptical integration model systematically underestimates
    # real guitar body volumes by ~1.8-1.9× due to body taper, plate curvature,
    # and the non-elliptical waist transition. Calibration derived from:
    #   Martin OM:   computed 9.72L → measured 17.5L → factor 1.80×
    #   Martin D-28: computed 11.8L → measured 22.0L → factor 1.86×
    #   Gibson J-45: computed 11.3L → measured 21.0L → factor 1.86×
    CALIBRATION_FACTOR = 1.83   # mean across three calibration instruments
    calibrated_L = total_L * CALIBRATION_FACTOR

    return {
        "volume_liters":         round(calibrated_L, 2),
        "volume_computed_L":     round(total_L, 2),
        "calibration_factor":    CALIBRATION_FACTOR,
        "volume_cubic_inches":   round(calibrated_L * 61.024, 2),
        "lower_bout_liters":     round(V_lower / 1e6 * CALIBRATION_FACTOR, 2),
        "waist_liters":          round(V_waist / 1e6 * CALIBRATION_FACTOR, 2),
        "upper_bout_liters":     round(V_upper / 1e6 * CALIBRATION_FACTOR, 2),
        "shape_factor":          shape_factor,
        "note": (
            "Elliptical cross-section model × calibration factor 1.83 "
            "(calibrated against Martin OM, D-28, Gibson J-45 measured volumes). "
            f"Computed volume: {total_L:.2f}L × {CALIBRATION_FACTOR} = {calibrated_L:.2f}L. "
            "Accuracy ±1.5L. Override with measured value if known."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ITEM 8 — PLATE-AIR COUPLING WARNING
# Estimates the top plate fundamental mode frequency from species properties
# and current thickness, then compares to f_H.
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class PlateAirCouplingResult:
    """
    Plate-air coupling assessment for a specific top plate and soundhole design.

    When the top plate's fundamental (1,1) mode frequency is close to the
    Helmholtz air resonance, the two oscillators repel each other in frequency
    (avoided crossing). This broadens the combined acoustic response but makes
    voicing less predictable.

    Physics:
        Two coupled oscillators with uncoupled frequencies f_plate and f_H:
        - Far apart (>25 Hz): minimal interaction, both modes well-defined
        - Moderate (10-25 Hz): noticeable frequency shift, slight broadening
        - Close (<10 Hz): strong repulsion, both modes shift significantly,
          response curve has a plateau rather than two distinct peaks

        Coupling strength depends on the plate-cavity coupling coefficient,
        which in turn depends on plate mass, plate area, and cavity volume.
        The PMF=0.92 correction in the Helmholtz formula is a first-order
        approximation of this coupling.

    Status:
        "clear":    separation > 25 Hz — no significant interaction
        "moderate": separation 10-25 Hz — coupling noticeable, manageable
        "strong":   separation < 10 Hz — strong repulsion, voicing affected

    Note:
        f_plate is estimated from species moduli and current thickness using
        plate_modal_frequency(). This is a free-plate estimate; the in-box
        frequency is typically lower by 5-15% (captured by the gamma transfer
        coefficient). The coupling warning uses the free-plate estimate as a
        conservative indicator.
    """
    # Inputs
    species_key: str
    thickness_mm: float
    plate_length_mm: float
    plate_width_mm: float
    f_H_hz: float

    # Computed
    f_plate_estimated_hz: float   # free-plate estimate
    separation_hz: float          # |f_plate - f_H|
    status: str                   # "clear" | "moderate" | "strong"

    # Output
    warning: Optional[str]
    design_note: str


def estimate_plate_air_coupling(
    species_key: str,
    thickness_mm: float,
    plate_length_mm: float,
    plate_width_mm: float,
    f_H_hz: float,
) -> PlateAirCouplingResult:
    """
    Estimate top plate fundamental frequency and assess plate-air coupling.

    Uses species moduli from TOP_SPECIES_THICKNESS table and current top
    thickness to estimate where the plate's (1,1) mode sits relative to f_H.

    Args:
        species_key:       Key from TOP_SPECIES_THICKNESS (e.g. "sitka_spruce")
        thickness_mm:      Current top plate thickness (assembled, mm)
        plate_length_mm:   Plate length along grain (mm) — typically body length
        plate_width_mm:    Plate width across grain (mm) — typically lower bout
        f_H_hz:            Helmholtz resonance from soundhole analysis (Hz)

    Returns:
        PlateAirCouplingResult with estimated f_plate and coupling status
    """
    species = TOP_SPECIES_THICKNESS.get(species_key)
    if species is None:
        # Unknown species — return neutral result
        return PlateAirCouplingResult(
            species_key=species_key, thickness_mm=thickness_mm,
            plate_length_mm=plate_length_mm, plate_width_mm=plate_width_mm,
            f_H_hz=f_H_hz, f_plate_estimated_hz=0.0,
            separation_hz=999.0, status="clear",
            warning=None, design_note="Unknown species — plate mode not estimated.",
        )

    h_m = thickness_mm / 1000.0
    a_m = plate_length_mm / 1000.0
    b_m = plate_width_mm / 1000.0
    E_L = species["E_L_GPa"] * 1e9
    E_C = species["E_C_GPa"] * 1e9
    rho = species["rho_kg_m3"]

    term_L = E_L / (a_m ** 4)
    term_C = E_C / (b_m ** 4)
    f_plate = (math.pi / 2.0) * math.sqrt((term_L + term_C) / rho) * h_m

    separation = abs(f_plate - f_H_hz)

    if separation > 25.0:
        status = "clear"
        warning = None
        design_note = (
            f"Plate mode ~{f_plate:.0f} Hz, Helmholtz {f_H_hz:.0f} Hz — "
            f"{separation:.0f} Hz separation. No significant interaction expected."
        )
    elif separation > 10.0:
        status = "moderate"
        warning = (
            f"Plate mode ~{f_plate:.0f} Hz is within {separation:.0f} Hz of f_H "
            f"({f_H_hz:.0f} Hz). Moderate coupling — expect slight frequency shift "
            f"and mild response broadening near f_H."
        )
        design_note = (
            "To reduce coupling: increase hole diameter slightly (raises f_H) "
            "or thin the plate (lowers f_plate). "
            "To increase coupling deliberately: converge both frequencies."
        )
    else:
        status = "strong"
        warning = (
            f"Strong coupling: plate mode ~{f_plate:.0f} Hz is within "
            f"{separation:.0f} Hz of f_H ({f_H_hz:.0f} Hz). "
            "The two modes repel each other — both shift away from their "
            "uncoupled values, producing a broad plateau in the bass response "
            "rather than a single Helmholtz peak. This is acoustically valid "
            "but makes voicing less predictable."
        )
        design_note = (
            "This is the coupled regime described by Caldersmith (1978) and Gore. "
            "Western Red Cedar tops at 2mm thickness frequently reach this condition. "
            "To separate the modes: increase f_H by enlarging the soundhole "
            "or add a side port."
        )

    return PlateAirCouplingResult(
        species_key=species_key,
        thickness_mm=thickness_mm,
        plate_length_mm=plate_length_mm,
        plate_width_mm=plate_width_mm,
        f_H_hz=f_H_hz,
        f_plate_estimated_hz=round(f_plate, 1),
        separation_hz=round(separation, 1),
        status=status,
        warning=warning,
        design_note=design_note,
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
