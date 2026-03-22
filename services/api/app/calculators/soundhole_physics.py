"""
soundhole_physics.py — Pure Helmholtz Physics for Acoustic Guitar Soundholes
=============================================================================

Extracted from soundhole_calc.py as part of DECOMP-002 modularization.

This module contains:
- Physical constants (speed of sound, end-correction factors)
- PortSpec dataclass for representing openings
- Core Helmholtz resonance formulas
- Multi-port and two-cavity calculations
- Frequency-to-note conversion

Zero external dependencies beyond Python stdlib.
All dimensions in SI units internally (m, m², m³).

Physics references:
  Gore & Gilet, Contemporary Acoustic Guitar Design and Build, Vol. 1
  Fletcher & Rossing, The Physics of Musical Instruments, Ch. 9-10
  Caldersmith, Designing a Guitar Family, 1978
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple


# ── Physical Constants ────────────────────────────────────────────────────────

C_AIR: float = 343.0       # Speed of sound in air at 20°C (m/s)
K0: float = 1.7            # Round-hole end-correction baseline (dimensionless)
GAMMA: float = 0.02        # Perimeter sensitivity constant (calibrate from measurements)
                            # Expected error before calibration: ±10-15 Hz
                            # Expected error after calibration: ±3-5 Hz

# Plate-air coupling correction
# The Helmholtz formula gives the UNCOUPLED air resonance.
# In an assembled instrument the top plate's mass shifts the resonance DOWN
# by approximately 5-10%. A plate_mass_factor of 0.92 corrects this.
# Calibrated against Martin OM (117→108 Hz), D-28 (107→98 Hz), J-45 (108→100 Hz).
PLATE_MASS_FACTOR: float = 0.92


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


# ── Core Physics Functions ────────────────────────────────────────────────────

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
        plate_mass_factor: Plate-air coupling correction (default 0.92)

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


def hz_to_note(freq_hz: float) -> str:
    """Convert frequency to nearest musical note name."""
    if freq_hz <= 0:
        return "—"
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    semitones = 12 * math.log2(freq_hz / 440.0) + 69   # MIDI note
    midi_round = round(semitones)
    octave = (midi_round // 12) - 1
    note = note_names[midi_round % 12]
    return f"{note}{octave}"


# Keep private alias for backward compatibility
_hz_to_note = hz_to_note


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


def exact_coupled_eigenfreq(
    f1_hz: float,
    f2_hz: float,
    V1_m3: float,
    V2_m3: float,
    A_ap_m2: float,
    L_eff_ap_m: float,
) -> Tuple[float, float, float]:
    """
    Exact 2×2 eigenvalue solution for two coupled Helmholtz resonators.

    Characteristic equation:  (ω² - ω₁²)(ω² - ω₂²) = κ⁴

    Analytic solution:
        ω±² = (ω₁² + ω₂²)/2 ± √(((ω₁² - ω₂²)/2)² + κ⁴)

    Coupling coefficient:
        κ² = c² × A_ap / (L_eff_ap × √(V₁ × V₂))

    Args:
        f1_hz:       Uncoupled main cavity frequency (Hz)
        f2_hz:       Uncoupled resonator frequency (Hz)
        V1_m3:       Main cavity volume (m³)
        V2_m3:       Resonator volume (m³)
        A_ap_m2:     Aperture area (m²)
        L_eff_ap_m:  Aperture effective neck length (m)

    Returns:
        (f_lower, f_upper, kappa_hz) in Hz
    """
    w1_sq = (2 * math.pi * f1_hz) ** 2
    w2_sq = (2 * math.pi * f2_hz) ** 2

    # Coupling coefficient κ² (rad²/s²)
    kappa_sq = C_AIR ** 2 * A_ap_m2 / (L_eff_ap_m * math.sqrt(V1_m3 * V2_m3))
    kappa_4 = kappa_sq ** 2

    # Eigenvalues
    mean_sq = (w1_sq + w2_sq) / 2.0
    half_diff_sq = (w1_sq - w2_sq) / 2.0
    discriminant = math.sqrt(half_diff_sq ** 2 + kappa_4)

    w_plus_sq  = mean_sq + discriminant
    w_minus_sq = max(0.0, mean_sq - discriminant)

    f_upper = math.sqrt(w_plus_sq)  / (2 * math.pi)
    f_lower = math.sqrt(w_minus_sq) / (2 * math.pi)
    kappa_hz = math.sqrt(kappa_sq)  / (2 * math.pi)

    return f_lower, f_upper, kappa_hz


# Keep private alias for backward compatibility
_exact_coupled_eigenfreq = exact_coupled_eigenfreq
