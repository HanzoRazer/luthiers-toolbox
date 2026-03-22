"""
soundhole_extended.py — Two-cavity model, body volume from dimensions, plate–air coupling.

Split from soundhole_calc.py (DECOMP-002 Phase 6) to keep soundhole_calc.py compact.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional

from .soundhole_physics import GAMMA, K0, PLATE_MASS_FACTOR, hz_to_note
from .soundhole_presets import TOP_SPECIES_THICKNESS

if TYPE_CHECKING:
    from .soundhole_calc import PortSpec


def compute_two_cavity_helmholtz(
    volume_main_m3: float,
    main_ports: List["PortSpec"],
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
    from .soundhole_calc import PortSpec, compute_helmholtz_multiport

    f_H1, port_details = compute_helmholtz_multiport(
        volume_main_m3, main_ports, k0, gamma, plate_mass_factor
    )

    aperture_port = PortSpec(
        area_m2=aperture_area_m2,
        perim_m=aperture_perim_m,
        location="top",
        thickness_m=aperture_thickness_m,
    )
    f_H2_raw, _ = compute_helmholtz_multiport(
        volume_internal_m3, [aperture_port], k0, gamma, plate_mass_factor=1.0
    )

    delta = abs(f_H1 - f_H2_raw) * 0.1
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
    waist_len = L * 0.25
    upper_len = L * 0.35

    avg_depth = (depth_endblock_mm + depth_neck_mm) / 2.0

    lower_area = math.pi * (lower_bout_mm / 2) * (depth_endblock_mm / 2) * shape_factor
    waist_area = math.pi * (waist_mm / 2) * (avg_depth / 2) * shape_factor
    upper_area = math.pi * (upper_bout_mm / 2) * (depth_neck_mm / 2) * shape_factor

    V_lower = (lower_area + waist_area) / 2.0 * lower_len
    V_waist = waist_area * waist_len
    V_upper = (waist_area + upper_area) / 2.0 * upper_len

    total_mm3 = V_lower + V_waist + V_upper
    total_L = total_mm3 / 1e6

    CALIBRATION_FACTOR = 1.83
    calibrated_L = total_L * CALIBRATION_FACTOR

    return {
        "volume_liters": round(calibrated_L, 2),
        "volume_computed_L": round(total_L, 2),
        "calibration_factor": CALIBRATION_FACTOR,
        "volume_cubic_inches": round(calibrated_L * 61.024, 2),
        "lower_bout_liters": round(V_lower / 1e6 * CALIBRATION_FACTOR, 2),
        "waist_liters": round(V_waist / 1e6 * CALIBRATION_FACTOR, 2),
        "upper_bout_liters": round(V_upper / 1e6 * CALIBRATION_FACTOR, 2),
        "shape_factor": shape_factor,
        "note": (
            "Elliptical cross-section model × calibration factor 1.83 "
            "(calibrated against Martin OM, D-28, Gibson J-45 measured volumes). "
            f"Computed volume: {total_L:.2f}L × {CALIBRATION_FACTOR} = {calibrated_L:.2f}L. "
            "Accuracy ±1.5L. Override with measured value if known."
        ),
    }


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
    species_key: str
    thickness_mm: float
    plate_length_mm: float
    plate_width_mm: float
    f_H_hz: float

    f_plate_estimated_hz: float
    separation_hz: float
    status: str

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
