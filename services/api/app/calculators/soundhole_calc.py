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


def _hz_to_note(freq_hz: float) -> str:
    """Convert frequency to nearest musical note name."""
    if freq_hz <= 0:
        return "—"
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    semitones = 12 * math.log2(freq_hz / 440.0) + 69   # MIDI note
    midi_round = round(semitones)
    octave = (midi_round // 12) - 1
    note = note_names[midi_round % 12]
    return f"{note}{octave}"


# ── High-Level Analysis ────────────────────────────────────────────────────────

def analyze_soundhole(
    volume_m3: float,
    ports: List[PortSpec],
    ring_width_mm: float,
    x_from_neck_mm: float,
    body_length_mm: float,
    k0: float = K0,
    gamma: float = GAMMA,
) -> SoundholeResult:
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
        f_helmholtz_note=_hz_to_note(f_H),
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


# ── Presets ───────────────────────────────────────────────────────────────────

PRESETS: Dict[str, Dict] = {
    "martin_om": {
        "label": "Martin OM (Orchestra Model)",
        "volume_liters": 17.5,
        "ports": [PortSpec.from_circle_mm(96, label="Round soundhole")],
        "ring_width_mm": 8.0,
        "x_from_neck_fraction": 0.333,
        "body_length_mm": 495,
        "target_f_hz": 108,
        "notes": "Standard fingerstyle. Balanced bass/treble. X-brace with soundhole patch.",
    },
    "martin_d28": {
        "label": "Martin D-28 (Dreadnought)",
        "volume_liters": 22.0,
        "ports": [PortSpec.from_circle_mm(100, label="Round soundhole")],
        "ring_width_mm": 8.0,
        "x_from_neck_fraction": 0.333,
        "body_length_mm": 508,
        "target_f_hz": 98,
        "notes": "High-volume projection. Scalloped X-brace. Lower f_H from larger body volume.",
    },
    "gibson_j45": {
        "label": "Gibson J-45 (Slope Shoulder)",
        "volume_liters": 21.0,
        "ports": [PortSpec.from_circle_mm(98, label="Round soundhole")],
        "ring_width_mm": 8.0,
        "x_from_neck_fraction": 0.330,
        "body_length_mm": 502,
        "target_f_hz": 100,
        "notes": "Mahogany top variant available. Ladder-braced version exists but X-brace is standard.",
    },
    "classical": {
        "label": "Classical Guitar",
        "volume_liters": 19.0,
        "ports": [PortSpec.from_circle_mm(85, thickness_mm=2.0, label="Round soundhole")],
        "ring_width_mm": 9.0,
        "x_from_neck_fraction": 0.340,
        "body_length_mm": 480,
        "target_f_hz": 96,
        "notes": "Thinner top (2mm cedar or spruce). Fan bracing. 85mm hole typical for cedar tops. "
                 "Classical body volume ~18-21L when accurately measured.",
    },
    "selmer_oval": {
        "label": "Selmer / Maccaferri Oval",
        "volume_liters": 20.0,
        "ports": [PortSpec.from_oval_mm(80, 110, label="Oval soundhole")],
        "ring_width_mm": 10.0,
        "x_from_neck_fraction": 0.280,
        "body_length_mm": 480,
        "target_f_hz": 100,
        "notes": "Django sound. Hole sits higher on the top (nearer neck). "
                 "80×110mm oval is typical original Maccaferri dimension.",
    },
    "om_side_port": {
        "label": "OM + Side Port",
        "volume_liters": 17.5,
        "ports": [
            PortSpec.from_circle_mm(90, location="top", label="Main soundhole"),
            PortSpec.from_circle_mm(30, location="side", thickness_mm=2.3, label="Side port (upper bass)"),
        ],
        "ring_width_mm": 8.0,
        "x_from_neck_fraction": 0.333,
        "body_length_mm": 495,
        "target_f_hz": 112,
        "notes": "Side port boosts player-ear response. f_H shift from side port is modest (+3-8 Hz).",
    },
    "benedetto_17": {
        "label": "Benedetto 17\" Archtop (F-holes)",
        "volume_liters": 24.0,
        "ports": [
            PortSpec.from_oval_mm(23, 110, location="top", thickness_mm=5.0, label="F-hole left"),
            PortSpec.from_oval_mm(23, 110, location="top", thickness_mm=5.0, label="F-hole right"),
        ],
        "ring_width_mm": 15.0,
        "x_from_neck_fraction": 0.500,
        "body_length_mm": 520,
        "target_f_hz": 90,
        "notes": "F-hole archtop air resonance is lower than equivalent round-hole area because the elongated "
                 "shape dramatically increases effective neck length (L_eff ≈ 52mm vs ~10mm for round). "
                 "Measured archtop f_H is typically 85–100 Hz — NOT 120 Hz as sometimes quoted. "
                 "F-holes are placed flanking the bridge line; inner notches bracket bridge feet.",
    },
}


def get_preset(name: str) -> Optional[Dict]:
    """Return preset config by name, or None if not found."""
    return PRESETS.get(name.lower().replace(" ", "_").replace("-", "_"))


def list_presets() -> List[Dict]:
    """Return summary of all available presets."""
    return [
        {
            "id": k,
            "label": v["label"],
            "target_f_hz": v["target_f_hz"],
            "volume_liters": v["volume_liters"],
            "notes": v["notes"],
        }
        for k, v in PRESETS.items()
    ]


def analyze_preset(preset_name: str) -> Optional[SoundholeResult]:
    """Run full analysis on a named preset."""
    preset = get_preset(preset_name)
    if not preset:
        return None
    x_mm = preset["x_from_neck_fraction"] * preset["body_length_mm"]
    return analyze_soundhole(
# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONS — Inverse solver, two-cavity model, side port extensions
# Side port / F-hole calculations: soundhole_ports.py (DECOMP-002 Phase 3)
# ═══════════════════════════════════════════════════════════════════════════════

from .soundhole_ports import (
    SIDE_PORT_POSITIONS,
    SIDE_PORT_TYPES,
    SidePortResult,
    SidePortSpec,
    analyze_side_port,
    solve_for_diameter_mm,
    solve_for_diameter_with_side_port_mm,
)



    result_diam = (lo + hi) / 2.0
    return {
        "main_diameter_mm": round(result_diam, 1),
        "side_port_diameter_mm": round(side_port_diameter_mm, 1),
        "achieved_f_hz": round(predict_total(result_diam), 1),
    }


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
        "f_H1_note": _hz_to_note(f_H1_coupled),
        "f_H2_note": _hz_to_note(f_H2_coupled),
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


BODY_DIMENSION_PRESETS: Dict[str, Dict] = {
    "martin_om": {
        "label": "Martin OM / 000",
        "lower_bout_mm": 381.0, "upper_bout_mm": 299.7, "waist_mm": 241.3,
        "body_length_mm": 495.3, "depth_endblock_mm": 105.4, "depth_neck_mm": 95.3,
    },
    "martin_d28": {
        "label": "Martin Dreadnought",
        "lower_bout_mm": 396.9, "upper_bout_mm": 292.1, "waist_mm": 273.1,
        "body_length_mm": 508.0, "depth_endblock_mm": 121.9, "depth_neck_mm": 107.9,
    },
    "gibson_j45": {
        "label": "Gibson J-45 / SJ",
        "lower_bout_mm": 406.4, "upper_bout_mm": 304.8, "waist_mm": 266.7,
        "body_length_mm": 501.7, "depth_endblock_mm": 120.7, "depth_neck_mm": 101.6,
    },
    "gibson_l00": {
        "label": "Gibson L-00 / LG",
        "lower_bout_mm": 342.9, "upper_bout_mm": 276.2, "waist_mm": 228.6,
        "body_length_mm": 464.8, "depth_endblock_mm": 104.8, "depth_neck_mm": 88.9,
    },
    "classical_650": {
        "label": "Classical (650mm scale)",
        "lower_bout_mm": 370.0, "upper_bout_mm": 290.0, "waist_mm": 235.0,
        "body_length_mm": 480.0, "depth_endblock_mm": 100.0, "depth_neck_mm": 90.0,
    },
    "parlor": {
        "label": "Parlor (small body)",
        "lower_bout_mm": 330.2, "upper_bout_mm": 254.0, "waist_mm": 215.9,
        "body_length_mm": 444.5, "depth_endblock_mm": 95.3, "depth_neck_mm": 85.0,
    },
    "benedetto_17": {
        "label": "Benedetto 17\" Archtop",
        "lower_bout_mm": 431.8, "upper_bout_mm": 330.2, "waist_mm": 279.4,
        "body_length_mm": 520.7, "depth_endblock_mm": 88.9, "depth_neck_mm": 76.2,
        "shape_factor": 0.75,   # carved top reduces effective volume
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# TOP PLATE STIFFNESS REDUCTION — Option C implementation
# Connects soundhole geometry to plate_modal_frequency() from plate_design
# ═══════════════════════════════════════════════════════════════════════════════

# Calibration constant K — derived from Gore & Gilet empirical data
# Calibration: K = 0.798 gives 6.0% frequency drop for standard OM config
#   (96mm hole, 165mm from neck block, 495×380mm plate, no bracing)
#   which matches Gore's reported 5-8% range for soundhole cutting.
# Single calibration point — update this constant when measured instrument
# data becomes available. See LUTHERIE_MATH.md §12 and §26.
_STIFFNESS_K: float = 0.798

# Bracing restoration factor — what fraction of the hole's stiffness loss
# is recovered by the soundhole patch and radial braces.
# 0.70 = standard flat-top: soundhole patch + 2 radial braces restores ~70%
# 0.00 = unbraced (free plate, pre-brace tap tone measurement)
# 0.90 = very heavily braced / archtop (practically no net loss)
_BRACING_RESTORE_DEFAULT: float = 0.70


@dataclass
class StiffnessResult:
    """
    Top plate stiffness analysis — effect of soundhole on plate modal frequency.

    Physics basis:
        The soundhole removes material from the top plate, reducing both mass
        and stiffness in the region of the hole. The net effect on the plate's
        fundamental (1,1) mode frequency depends on:
        1. How much area is removed (area_ratio)
        2. Where in the mode shape the hole sits (mode_coupling)
        3. How much stiffness the bracing restores (bracing_restore)

        Formula (Leissa/Gore calibrated power law):
            raw_reduction = K × (A_hole/A_plate)^0.75 × sin(π × x/body_length)
            net_reduction = raw_reduction × (1 - bracing_restore)
            freq_ratio    = 1 - net_reduction

    Calibration:
        K = 0.798, calibrated to Gore & Gilet empirical data:
        ~6% frequency drop for 96mm hole at 165mm on standard OM (no bracing).
        Bracing restoration factor 0.70 typical for soundhole patch + radial braces.

    Status:
        Single-point calibration. Accuracy improves with measured instrument data.
        See LUTHERIE_MATH.md §12 for derivation and §26 for calibration history.
    """
    # Inputs
    plate_area_m2: float
    hole_area_m2: float
    x_from_neck_mm: float
    body_length_mm: float
    bracing_restore: float

    # Intermediate
    area_ratio: float
    mode_coupling: float            # sin(π × x/body_length)
    raw_reduction_pct: float        # before bracing restoration
    bracing_recovered_pct: float    # stiffness bracing gives back

    # Outputs
    net_reduction_pct: float        # actual net drop in plate modal frequency
    freq_ratio: float               # f_with_hole / f_no_hole
    status: str                     # "minimal" | "moderate" | "significant"

    # Optional: actual frequencies if material properties supplied
    f_plate_no_hole_hz: Optional[float] = None
    f_plate_with_hole_hz: Optional[float] = None

    @property
    def construction_note(self) -> str:
        if self.status == "minimal":
            return (
                f"Net stiffness reduction {self.net_reduction_pct:.1f}% — "
                "standard soundhole patch adequate. No additional radial braces required."
            )
        elif self.status == "moderate":
            return (
                f"Net stiffness reduction {self.net_reduction_pct:.1f}% — "
                "soundhole patch required. Consider 2 short radial braces flanking the hole "
                "to restore longitudinal stiffness in the neck-to-bridge band."
            )
        else:
            return (
                f"Net stiffness reduction {self.net_reduction_pct:.1f}% — "
                "significant. Soundhole patch plus radial braces mandatory. "
                "Consider reducing hole diameter by 5–10mm or moving hole "
                "closer to neck block to reduce mode coupling."
            )


def compute_top_stiffness_reduction(
    hole_area_m2: float,
    x_from_neck_mm: float,
    body_length_mm: float,
    plate_length_mm: float,
    plate_width_mm: float,
    bracing_restore: float = _BRACING_RESTORE_DEFAULT,
    K: float = _STIFFNESS_K,
    # Optional: material properties for absolute frequency output
    E_L_Pa: Optional[float] = None,
    E_C_Pa: Optional[float] = None,
    rho_kg_m3: Optional[float] = None,
    thickness_mm: Optional[float] = None,
    eta: float = 1.0,
) -> StiffnessResult:
    """
    Compute the effect of a soundhole on the top plate's fundamental modal frequency.

    Uses a power-law stiffness reduction model calibrated against Gore & Gilet
    empirical measurements. Optionally computes absolute frequencies if material
    properties are supplied.

    The model treats the entire plate (neck block to tail block) as the reference
    plate, with the soundhole position expressed as a fraction of body length.
    This choice of reference length matches Gore's measurement convention and
    gives the correct mode coupling values for the traditional 1/3 placement.

    Args:
        hole_area_m2:      Total port area (top ports only — side ports excluded)
        x_from_neck_mm:    Soundhole center distance from neck block (mm)
        body_length_mm:    Total internal body length (mm)
        plate_length_mm:   Top plate length along grain (mm) — typically = body_length
        plate_width_mm:    Top plate width across grain (mm) — typically = lower bout
        bracing_restore:   Fraction of stiffness loss recovered by bracing (0–1)
                           Default 0.70 = soundhole patch + 2 radial braces
                           Use 0.00 for free plate (pre-brace tap tone measurement)
        K:                 Calibration constant (default 0.798, Gore-calibrated)
        E_L_Pa:            Longitudinal Young's modulus (Pa) — optional
        E_C_Pa:            Cross-grain Young's modulus (Pa) — optional
        rho_kg_m3:         Wood density (kg/m³) — optional
        thickness_mm:      Plate thickness (mm) — optional
        eta:               Boundary condition factor (default 1.0 free plate)

    Returns:
        StiffnessResult with reduction percentages, freq_ratio, and construction note
    """
    plate_area_m2 = (plate_length_mm / 1000.0) * (plate_width_mm / 1000.0)
    area_ratio = hole_area_m2 / plate_area_m2 if plate_area_m2 > 0 else 0.0

    # Mode coupling: sin(π × x_hole / body_length)
    # This uses body_length (not effective plate length) because Gore's calibration
    # data measures from the neck block. At the traditional 1/3 position:
    # sin(π × 0.333) = 0.866 — matching the calibration point.
    x_frac = x_from_neck_mm / body_length_mm if body_length_mm > 0 else 0.333
    x_frac = max(0.0, min(1.0, x_frac))
    mode_coupling = math.sin(math.pi * x_frac)

    # Raw stiffness reduction (no bracing, free plate)
    raw_reduction = K * (area_ratio ** 0.75) * mode_coupling if area_ratio > 0 else 0.0

    # Net reduction after bracing restoration
    bracing_recovered = raw_reduction * bracing_restore
    net_reduction = raw_reduction * (1.0 - bracing_restore)

    freq_ratio = 1.0 - net_reduction
    freq_ratio = max(0.5, freq_ratio)  # physical floor

    # Status classification
    if net_reduction * 100 < 1.5:
        status = "minimal"
    elif net_reduction * 100 < 3.0:
        status = "moderate"
    else:
        status = "significant"

    # Optional absolute frequencies
    f_no_hole: Optional[float] = None
    f_with_hole: Optional[float] = None

    if all(v is not None for v in [E_L_Pa, E_C_Pa, rho_kg_m3, thickness_mm]):
        try:
            # Import here to avoid circular dependency if plate_design not available
            from .plate_design.thickness_calculator import plate_modal_frequency
            h_m = thickness_mm / 1000.0  # type: ignore[operator]
            a_m = plate_length_mm / 1000.0
            b_m = plate_width_mm / 1000.0
            f_no_hole = plate_modal_frequency(
                E_L_Pa, E_C_Pa, rho_kg_m3, h_m, a_m, b_m, eta=eta  # type: ignore[arg-type]
            )
            f_with_hole = f_no_hole * freq_ratio
        except ImportError:
            pass  # plate_design not available — freq values remain None

    return StiffnessResult(
        plate_area_m2=round(plate_area_m2, 4),
        hole_area_m2=round(hole_area_m2, 6),
        x_from_neck_mm=x_from_neck_mm,
        body_length_mm=body_length_mm,
        bracing_restore=bracing_restore,
        area_ratio=round(area_ratio, 4),
        mode_coupling=round(mode_coupling, 4),
        raw_reduction_pct=round(raw_reduction * 100, 2),
        bracing_recovered_pct=round(bracing_recovered * 100, 2),
        net_reduction_pct=round(net_reduction * 100, 2),
        freq_ratio=round(freq_ratio, 4),
        status=status,
        f_plate_no_hole_hz=round(f_no_hole, 1) if f_no_hole else None,
        f_plate_with_hole_hz=round(f_with_hole, 1) if f_with_hole else None,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TWO-CAVITY ANALYSIS — Moved to soundhole_resonator.py (DECOMP-002 Phase 2)
# TwoCavityResult, analyze_two_cavity, and related functions are now imported
# from soundhole_resonator.py for modularity. Backward compat re-exports above.
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# BRACING IMPLICATION INDICATOR
# Translates stiffness reduction percentage into specific construction prescription.
# Connects compute_top_stiffness_reduction() output to actionable bracing guidance.
# ═══════════════════════════════════════════════════════════════════════════════

# Prescription thresholds based on raw_reduction_pct (free plate, no bracing)
# These are calibrated to the K=0.798 model at the standard 1/3 body position.
# The raw_reduction (not net) drives the prescription because the builder is
# deciding what bracing to INSTALL — before bracing is in place.
#
# Calibration source: standard lutherie practice cross-referenced against
# Gore & Gilet Vol.1, typical flat-top brace dimensions, and the stiffness
# reduction thresholds from compute_top_stiffness_reduction().

_BRACING_PRESCRIPTIONS: List[Dict] = [
    {
        "raw_reduction_max_pct": 3.0,
        "level": "none",
        "status": "OK",
        "label": "No reinforcement required",
        "patch_required": False,
        "radial_braces": 0,
        "brace_spec": None,
        "description": (
            "Hole removes less than 3% of plate stiffness — within the natural "
            "variation of tap-tuned tops. No soundhole patch or radial braces needed. "
            "Standard rosette glue joint provides adequate edge support."
        ),
        "construction": [
            "Cut rosette channel, glue rosette, level flush.",
            "Cut soundhole. Clean edge with sharp chisel.",
            "Rosette glue joint provides sufficient ring support.",
        ],
    },
    {
        "raw_reduction_max_pct": 5.0,
        "level": "patch",
        "status": "RECOMMENDED",
        "label": "Soundhole patch recommended",
        "patch_required": False,
        "radial_braces": 0,
        "brace_spec": None,
        "description": (
            "Hole removes 3–5% of plate stiffness. A soundhole patch is recommended "
            "but not strictly required — omitting it on a thin or soft top may produce "
            "gradual top bellying near the soundhole over time. Classical guitars and "
            "cedar tops in this range should always use a patch."
        ),
        "construction": [
            "Soundhole patch: 1.5mm spruce ring, grain parallel to top grain.",
            "Width 15–18mm, glued flush to underside around full perimeter.",
            "Patch restores approximately 30–35% of lost stiffness.",
        ],
    },
    {
        "raw_reduction_max_pct": 6.5,
        "level": "patch_braces_light",
        "status": "REQUIRED",
        "label": "Patch + 2 radial braces required",
        "patch_required": True,
        "radial_braces": 2,
        "brace_spec": {"width_mm": 5.0, "height_mm": 5.0, "length_mm": 70.0, "profile": "parabolic"},
        "description": (
            "Standard acoustic guitar range (90–105mm holes). Patch alone is insufficient — "
            "2 short radial braces flanking the hole in the upper and lower positions "
            "are required to restore longitudinal stiffness in the neck-to-bridge band. "
            "This is the construction used on all standard Martin and Gibson flat-tops."
        ),
        "construction": [
            "Soundhole patch: 1.5–2mm spruce ring, 15mm wide, full perimeter.",
            "2 radial braces: 5mm wide × 5mm tall × 70mm long, parabolic profile.",
            "Position: one above the hole (toward neck), one below (toward tail).",
            "Braces run along the top's grain direction, centered on the hole.",
            "Patch + 2 braces restores approximately 60–70% of lost stiffness.",
        ],
    },
    {
        "raw_reduction_max_pct": 8.0,
        "level": "patch_braces_heavy",
        "status": "REQUIRED",
        "label": "Patch + 2 tall radial braces required",
        "patch_required": True,
        "radial_braces": 2,
        "brace_spec": {"width_mm": 5.0, "height_mm": 8.0, "length_mm": 80.0, "profile": "parabolic"},
        "description": (
            "Larger holes (105–120mm). Taller braces needed for adequate stiffness "
            "restoration. Consider whether the hole size is justified — at this range "
            "the bracing adds significant mass that partially offsets the acoustic "
            "benefit of the larger opening. Some builders prefer 2 side braces + "
            "2 end braces (4 total in a cross pattern) at this diameter."
        ),
        "construction": [
            "Soundhole patch: 2mm spruce ring, 18mm wide, full perimeter.",
            "2 radial braces: 5mm wide × 8mm tall × 80mm long, parabolic profile.",
            "Optional: additional cross-grain brace on upper side of hole.",
            "Patch + 2 tall braces restores approximately 65–75% of lost stiffness.",
        ],
    },
    {
        "raw_reduction_max_pct": 999.0,
        "level": "full_reinforcement",
        "status": "CRITICAL",
        "label": "Full reinforcement required",
        "patch_required": True,
        "radial_braces": 4,
        "brace_spec": {"width_mm": 6.0, "height_mm": 8.0, "length_mm": 80.0, "profile": "parabolic"},
        "description": (
            "Hole exceeds 120mm or sits in a high-mode-coupling position (>40% of body length). "
            "Full reinforcement required: patch ring plus 4 radial braces in a cross pattern, "
            "OR a doubler plate (thin spruce plate glued over the entire upper bout interior). "
            "At this level, consider whether the acoustic benefit of the larger opening "
            "outweighs the structural and mass consequences. Side-port + smaller main hole "
            "may be a better design choice."
        ),
        "construction": [
            "Soundhole patch: 2.5mm spruce ring, 20mm wide, full perimeter.",
            "4 radial braces: 6mm wide × 8mm tall × 80mm long, parabolic profile.",
            "Braces at 12, 3, 6, and 9 o'clock positions around hole.",
            "OR: doubler plate (1.5mm spruce sheet covering full soundhole region).",
            "Consider redesigning with smaller main hole + side port(s).",
        ],
    },
]


@dataclass
class BracingIndicatorResult:
    """
    Bracing prescription for a soundhole based on stiffness reduction analysis.

    Derived from compute_top_stiffness_reduction() raw_reduction_pct —
    the free-plate stiffness loss before any bracing is installed.
    This drives the prescription because the builder chooses bracing BEFORE
    installing it, not after.

    Connection to bracing_calc.py:
        brace_spec dimensions (width_mm, height_mm, length_mm) are compatible
        with BracingCalcInput fields in calculators/bracing_calc.py.
        To compute brace section area: BracingCalcInput(**brace_spec, profile_type='parabolic')
        To compute brace mass: estimate_mass_grams(BracingCalcInput(**brace_spec))
        This connection is intentionally not made here to avoid the Pydantic
        dependency — the caller can bridge to bracing_calc.py if needed.
    """
    # Inputs
    hole_diameter_equiv_mm: float
    raw_reduction_pct: float         # stiffness loss without bracing
    x_from_neck_mm: float
    body_length_mm: float

    # Prescription
    level: str                        # "none" | "patch" | "patch_braces_light" | etc.
    status: str                       # "OK" | "RECOMMENDED" | "REQUIRED" | "CRITICAL"
    label: str
    patch_required: bool
    radial_braces: int
    brace_spec: Optional[Dict]        # width_mm, height_mm, length_mm, profile

    # Text
    description: str
    construction_steps: List[str]

    # Cross-reference to bracing_calc.py
    bracing_calc_compatible: bool = True
    bracing_calc_note: str = (
        "brace_spec dimensions are compatible with BracingCalcInput. "
        "Call calculate_brace_section(BracingCalcInput(**brace_spec)) "
        "for cross-section area, or estimate_mass_grams() for brace mass."
    )

    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "label": self.label,
            "patch_required": self.patch_required,
            "radial_braces": self.radial_braces,
            "brace_spec": self.brace_spec,
            "raw_reduction_pct": self.raw_reduction_pct,
            "construction_steps": self.construction_steps,
        }


def get_bracing_implication(
    stiffness: "StiffnessResult",
    main_port_diameter_equiv_mm: Optional[float] = None,
) -> BracingIndicatorResult:
    """
    Derive bracing prescription from a StiffnessResult.

    Uses raw_reduction_pct (free plate, no bracing) to determine
    what bracing is needed. The prescription is independent of the
    bracing_restore parameter used in compute_top_stiffness_reduction() —
    the builder is deciding what to install, not evaluating what they have.

    Args:
        stiffness:                   Output from compute_top_stiffness_reduction()
        main_port_diameter_equiv_mm: Optional — equivalent circular diameter of
                                     main port, for display. If None, derived
                                     from hole_area_m2.

    Returns:
        BracingIndicatorResult with prescription and construction steps
    """
    raw_pct = stiffness.raw_reduction_pct

    # Find the right prescription tier
    prescription = _BRACING_PRESCRIPTIONS[-1]   # default to most severe
    for p in _BRACING_PRESCRIPTIONS:
        if raw_pct <= p["raw_reduction_max_pct"]:
            prescription = p
            break

    # Derive equivalent diameter if not supplied
    if main_port_diameter_equiv_mm is None:
        main_port_diameter_equiv_mm = 2.0 * math.sqrt(
            stiffness.hole_area_m2 / math.pi
        ) * 1000.0

    return BracingIndicatorResult(
        hole_diameter_equiv_mm=round(main_port_diameter_equiv_mm, 1),
        raw_reduction_pct=round(raw_pct, 2),
        x_from_neck_mm=stiffness.x_from_neck_mm,
        body_length_mm=stiffness.body_length_mm,
        level=prescription["level"],
        status=prescription["status"],
        label=prescription["label"],
        patch_required=prescription["patch_required"],
        radial_braces=prescription["radial_braces"],
        brace_spec=prescription["brace_spec"],
        description=prescription["description"],
        construction_steps=prescription["construction"],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ITEM 7 — TOP SPECIES THICKNESS TABLE
# Typical finished top plate thicknesses by species, sourced from
# lutherie practice. These are assembled-guitar values, NOT free-plate
# tap-tone target thicknesses.
# ═══════════════════════════════════════════════════════════════════════════════

TOP_SPECIES_THICKNESS: Dict[str, Dict] = {
    "sitka_spruce": {
        "label": "Sitka Spruce",
        "thick_mm": 2.5,
        "range_mm": (2.2, 2.8),
        "E_L_GPa": 12.5,
        "E_C_GPa": 0.85,
        "rho_kg_m3": 450,   # slightly denser than raw average for finished plate
        "note": "Most common flat-top top wood. Stiff and light — tolerates thinner graduation.",
    },
    "adirondack_spruce": {
        "label": "Adirondack (Red) Spruce",
        "thick_mm": 2.5,
        "range_mm": (2.2, 2.8),
        "E_L_GPa": 13.5,
        "E_C_GPa": 0.90,
        "rho_kg_m3": 430,
        "note": "Stiffer than Sitka. Can be graduated slightly thinner for same tap tone.",
    },
    "engelmann_spruce": {
        "label": "Engelmann Spruce",
        "thick_mm": 2.4,
        "range_mm": (2.2, 2.7),
        "E_L_GPa": 11.0,
        "E_C_GPa": 0.80,
        "rho_kg_m3": 380,
        "note": "Softer than Sitka. Typically graduated slightly thicker to compensate.",
    },
    "european_spruce": {
        "label": "European (Alpine) Spruce",
        "thick_mm": 2.4,
        "range_mm": (2.0, 2.6),
        "E_L_GPa": 14.0,
        "E_C_GPa": 0.75,
        "rho_kg_m3": 440,
        "note": "High stiffness-to-weight. Classical guitar standard.",
    },
    "western_red_cedar": {
        "label": "Western Red Cedar",
        "thick_mm": 2.0,
        "range_mm": (1.8, 2.4),
        "E_L_GPa": 8.5,
        "E_C_GPa": 0.70,
        "rho_kg_m3": 350,
        "note": "Lower MOE — must be graduated thinner for equivalent response. "
                "Ring width minimum applies strictly; cedar cracks more readily than spruce.",
    },
    "redwood": {
        "label": "Redwood",
        "thick_mm": 2.2,
        "range_mm": (2.0, 2.5),
        "E_L_GPa": 9.0,
        "E_C_GPa": 0.65,
        "rho_kg_m3": 360,
        "note": "Similar to cedar. Old-growth redwood has higher stiffness than plantation stock.",
    },
    "mahogany": {
        "label": "Mahogany (top)",
        "thick_mm": 2.8,
        "range_mm": (2.5, 3.2),
        "E_L_GPa": 10.2,
        "E_C_GPa": 0.65,
        "rho_kg_m3": 540,
        "note": "Dense and isotropic. Typically graduated thicker than spruce. "
                "Common on 13-fret all-mahogany instruments (Martin 000-17, etc.).",
    },
    "koa": {
        "label": "Koa (top)",
        "thick_mm": 3.0,
        "range_mm": (2.8, 3.5),
        "E_L_GPa": 11.5,
        "E_C_GPa": 0.85,
        "rho_kg_m3": 600,
        "note": "Heavy and dense — graduated noticeably thicker. "
                "Valued for midrange warmth and sustain.",
    },
    "archtop_carved": {
        "label": "Archtop (carved spruce)",
        "thick_mm": 5.5,
        "range_mm": (4.5, 7.0),
        "E_L_GPa": 12.5,
        "E_C_GPa": 0.85,
        "rho_kg_m3": 430,
        "note": "Carved archtop — apex thickness 5.5–7mm, edge 3–4mm. "
                "This field represents approximate midpoint. "
                "Actual graduation varies across the plate per archtop_graduation_template.",
    },
}


def get_species_thickness(species_key: str) -> Optional[Dict]:
    """Return species entry from TOP_SPECIES_THICKNESS table, or None."""
    return TOP_SPECIES_THICKNESS.get(species_key)


def list_top_species() -> List[Dict]:
    """Return list of all top species with label, thick_mm, range_mm, note."""
    return [
        {"key": k, **{fk: v[fk] for fk in ("label", "thick_mm", "range_mm", "note")}}
        for k, v in TOP_SPECIES_THICKNESS.items()
    ]


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


# ═══════════════════════════════════════════════════════════════════════════════
# ITEM 9 — HUMIDITY/SEASONAL RING WIDTH NOTE
# Ring width check already handles structural minimum. This extension adds
# climate-specific guidance for high-humidity-swing environments.
# ═══════════════════════════════════════════════════════════════════════════════

# Climate zones by representative annual RH swing (high - low)
# Used to adjust ring width recommendation
_CLIMATE_ZONES: Dict[str, Dict] = {
    "arid":       {"label": "Arid / Desert",           "rh_swing": 25,  "example": "Tucson AZ, Denver CO"},
    "temperate":  {"label": "Temperate",                "rh_swing": 35,  "example": "Seattle WA, Portland OR"},
    "continental":{"label": "Continental",              "rh_swing": 45,  "example": "Chicago IL, Minneapolis MN"},
    "humid":      {"label": "Humid Subtropical",        "rh_swing": 55,  "example": "Houston TX, New Orleans LA"},
    "tropical":   {"label": "Tropical / Coastal",       "rh_swing": 65,  "example": "Miami FL, Honolulu HI"},
}

# Ring width addition per 10% RH swing above the 35% base
# Based on: Δdim = plate_width × MC_change_pct × grain_factor / 100
# where MC_change_pct ≈ RH_swing × 0.18 (simplified EMC relationship)
# and grain_factor ≈ 0.003 (radial movement for spruce)
# For 400mm wide plate: Δ ≈ 400 × (swing × 0.18) × 0.003 = 0.216 × swing mm
# But we only need the ring to accommodate the edge movement, not full plate:
# Edge zone ≈ 15mm wide → Δedge ≈ Δ × (15/400) = negligible
# The real driver is shear stress at the glue line of the ring itself.
# Empirical recommendation: add 0.5mm to min_ring per 10% RH swing above base 35%
_RING_WIDTH_HUMIDITY_ADDITION_PER_10PCT_SWING = 0.5  # mm


def get_ring_width_humidity_note(
    soundhole_radius_mm: float,
    ring_width_mm: float,
    climate_key: str = "temperate",
) -> Dict:
    """
    Seasonal humidity note for ring width check.

    Extends check_ring_width() with climate-specific guidance.
    The standard 6mm absolute minimum assumes temperate conditions (~35% RH swing).
    High-humidity-swing climates (Houston: 50-55% swing) need larger rings.

    Args:
        soundhole_radius_mm: Soundhole radius (mm)
        ring_width_mm:       Actual ring width at narrowest point (mm)
        climate_key:         Key from _CLIMATE_ZONES (default "temperate")

    Returns:
        Dict with adjusted_min_mm, climate_note, and seasonal_guidance
    """
    climate = _CLIMATE_ZONES.get(climate_key, _CLIMATE_ZONES["temperate"])
    swing = climate["rh_swing"]

    # Base minimum (from check_ring_width)
    base_min = max(soundhole_radius_mm * RING_WIDTH_RADIUS_FRACTION, RING_WIDTH_ABSOLUTE_MIN_MM)

    # Climate adjustment — addition above base for high-swing environments
    swing_above_base = max(0, swing - 35)
    humidity_addition = (swing_above_base / 10.0) * _RING_WIDTH_HUMIDITY_ADDITION_PER_10PCT_SWING
    adjusted_min = base_min + humidity_addition

    if ring_width_mm >= adjusted_min * 1.3:
        seasonal_status = "adequate"
        seasonal_note = (
            f"Ring width {ring_width_mm:.1f}mm is adequate for {climate['label']} "
            f"conditions (~{swing}% annual RH swing)."
        )
    elif ring_width_mm >= adjusted_min:
        seasonal_status = "marginal"
        seasonal_note = (
            f"Ring width {ring_width_mm:.1f}mm meets adjusted minimum "
            f"({adjusted_min:.1f}mm) for {climate['label']} conditions "
            f"(~{swing}% RH swing) but is marginal. Consider 12–15mm if possible."
        )
    else:
        seasonal_status = "insufficient"
        seasonal_note = (
            f"Ring width {ring_width_mm:.1f}mm is below the climate-adjusted "
            f"minimum of {adjusted_min:.1f}mm for {climate['label']} conditions "
            f"(~{swing}% annual RH swing, e.g. {climate['example']}). "
            f"Tops in this climate move significantly with seasonal humidity — "
            f"thin rings at the soundhole edge are the most common crack initiation "
            f"point. Reduce hole diameter or move hole toward body center."
        )

    # Full humidity guidance text
    # MC change ≈ swing × 0.18%; radial movement ≈ 0.2% per 1% MC change
    plate_width = soundhole_radius_mm * 6  # rough estimate of plate width from hole size
    estimated_movement_mm = plate_width * (swing * 0.18 * 0.002)

    return {
        "climate": climate["label"],
        "rh_swing_pct": swing,
        "base_min_mm": round(base_min, 1),
        "humidity_addition_mm": round(humidity_addition, 1),
        "adjusted_min_mm": round(adjusted_min, 1),
        "seasonal_status": seasonal_status,
        "seasonal_note": seasonal_note,
        "estimated_seasonal_movement_mm": round(estimated_movement_mm, 1),
        "guidance": (
            f"Annual humidity swing ~{swing}%. "
            f"For a top ~{plate_width:.0f}mm wide this creates an estimated "
            f"seasonal movement of ~{estimated_movement_mm:.1f}mm across the grain. "
            f"Recommend ring width ≥ {adjusted_min:.0f}mm for this climate zone."
        ),
    }


def list_climate_zones() -> List[Dict]:
    """Return list of climate zones for UI dropdown."""
    return [{"key": k, **v} for k, v in _CLIMATE_ZONES.items()]

# ═══════════════════════════════════════════════════════════════════════════════
# GEOMETRY-002 — Soundhole placement & sizing (router / tests)
# Preserved from previous app.calculators.soundhole_calc API.
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Standard Diameters by Body Style ────────────────────────────────────────

STANDARD_DIAMETERS_MM = {
    "dreadnought": 100.0,
    "om_000": 98.0,
    "jumbo": 102.0,
    "parlor": 85.0,
    "classical": 85.0,
    "concert": 90.0,
    "auditorium": 95.0,
    "archtop": None,  # Uses f-holes, different calculation
}

# Position as fraction of body length from neck block
STANDARD_POSITION_FRACTION = {
    "dreadnought": 0.50,
    "om_000": 0.48,
    "jumbo": 0.52,
    "parlor": 0.47,
    "classical": 0.50,
    "concert": 0.48,
    "auditorium": 0.49,
    "archtop": None,
}

# Valid position range (fraction of body length)
POSITION_MIN_FRACTION = 0.45
POSITION_MAX_FRACTION = 0.55


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


def list_body_styles() -> List[str]:
    """Return list of supported body styles."""
    return [k for k in STANDARD_DIAMETERS_MM.keys() if k != "archtop"]


def get_standard_diameter(body_style: str) -> Optional[float]:
    """Get standard soundhole diameter for a body style."""
    style_key = body_style.lower().replace("-", "_").replace(" ", "_")
    return STANDARD_DIAMETERS_MM.get(style_key)
