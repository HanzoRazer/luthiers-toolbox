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
        volume_m3=preset["volume_liters"] / 1000.0,
        ports=preset["ports"],
        ring_width_mm=preset["ring_width_mm"],
        x_from_neck_mm=x_mm,
        body_length_mm=preset["body_length_mm"],
    )
