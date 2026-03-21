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


# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONS — Inverse solver, two-cavity model, side port extensions
# ═══════════════════════════════════════════════════════════════════════════════

# ── Side port position taxonomy ───────────────────────────────────────────────

SIDE_PORT_POSITIONS: Dict[str, Dict] = {
    "upper_treble": {
        "label":       "Upper treble bout",
        "radiation":   "Directed toward player's right ear and slightly upward. "
                       "Strong monitor effect — the most common position for performer comfort. "
                       "Minimal change to audience-facing projection.",
        "coupling":    "low",    # low coupling to monopole mode
        "f_H_shift":   "+3–6 Hz",
        "structural":  "Clear of main X-brace intersection. Min 40mm from neck block. "
                       "Check for transverse brace ends.",
    },
    "upper_bass": {
        "label":       "Upper bass bout",
        "radiation":   "Directed toward player's left arm and toward ceiling. "
                       "Useful for balanced monitoring in small rooms. "
                       "Common on OM + side port builds.",
        "coupling":    "low",
        "f_H_shift":   "+3–6 Hz",
        "structural":  "Clear of neck block. Min 40mm. May intersect with upper transverse brace end.",
    },
    "lower_treble": {
        "label":       "Lower treble bout",
        "radiation":   "Directed toward floor and slightly sideways. "
                       "Strong coupling to lower bout volume — larger Helmholtz shift. "
                       "Used when f_H tuning is the primary goal rather than monitor sound.",
        "coupling":    "high",
        "f_H_shift":   "+8–15 Hz",
        "structural":  "Min 40mm from tail block. Clear of lower X-brace leg.",
    },
    "lower_bass": {
        "label":       "Lower bass bout",
        "radiation":   "Directed toward floor on the bass side. "
                       "Maximum coupling to body volume — largest Helmholtz shift of any side position. "
                       "Stoll Guitars and others use this to raise f_H without changing top geometry.",
        "coupling":    "high",
        "f_H_shift":   "+8–15 Hz",
        "structural":  "Min 40mm from tail block. Clear of lower X-brace leg (bass side).",
    },
    "waist": {
        "label":       "Waist (narrowest point)",
        "radiation":   "Exits at 90° to body centerline. "
                       "Unusual position — limited by narrow rim depth at waist. "
                       "Low coupling to both upper and lower bout modes.",
        "coupling":    "minimal",
        "f_H_shift":   "+1–4 Hz",
        "structural":  "Waist rim typically only 70–80mm deep — may limit port diameter to <25mm. "
                       "Avoid binding ledge and kerfing thickness.",
    },
    "symmetric_pair": {
        "label":       "Symmetric pair (both upper bouts)",
        "radiation":   "Exits toward both player ears simultaneously. "
                       "Stereo-like monitor experience — both ears receive direct sound. "
                       "Total area doubles vs single port, so Helmholtz shift is larger.",
        "coupling":    "low",
        "f_H_shift":   "+6–12 Hz (doubled area)",
        "structural":  "Two ports, each min 40mm from neck block, min 30mm separation from each other.",
    },
}


SIDE_PORT_TYPES: Dict[str, Dict] = {
    "round": {
        "label":       "Round",
        "description": "Standard circular hole. Simplest to cut — forstner bit or hole saw. "
                       "Perimeter correction is minimal (P/√A = 3.54 for circle).",
        "perim_factor": 1.0,   # multiplier on circular perimeter
    },
    "oval": {
        "label":       "Oval",
        "description": "Elliptical opening. Slightly higher perimeter than round for same area, "
                       "raising L_eff by ~5%. Cut with router jig or file from round pilot hole.",
        "perim_factor": 1.15,
    },
    "slot": {
        "label":       "Slot / rectangular",
        "description": "Row of slots or single rectangular slot. High perimeter-to-area ratio — "
                       "L_eff is significantly longer than round, lowering f_H for same area. "
                       "Common on ukuleles. Cut with router or oscillating tool.",
        "perim_factor": 2.2,   # typical for slot aspect ratio 3:1
    },
    "chambered": {
        "label":       "Chambered (tubed)",
        "description": "Port opens into an internal routed channel before exiting the rim. "
                       "The channel length adds directly to L_eff, allowing deliberate tuning "
                       "of port resonance independent of visible hole size. "
                       "Rare — found on some custom instruments.",
        "perim_factor": 1.0,   # tube length handled separately via tube_length_mm
    },
}


@dataclass
class SidePortSpec:
    """
    Extended specification for a side-of-body port.

    Extends basic PortSpec with position, type, and structural context
    that affects radiation pattern and structural validity checks.

    Attributes:
        area_m2:          Opening area (m²)
        perim_m:          Perimeter of the opening (m)
        thickness_m:      Rim thickness at the port (m) — typically 0.0023m (2.3mm)
        position:         Where on the rim the port sits (see SIDE_PORT_POSITIONS)
        port_type:        Shape/construction type (see SIDE_PORT_TYPES)
        tube_length_mm:   Added internal channel length for chambered ports (mm)
        label:            Display name
    """
    area_m2: float
    perim_m: float
    thickness_m: float = 0.0023
    position: str = "upper_bass"        # key from SIDE_PORT_POSITIONS
    port_type: str = "round"            # key from SIDE_PORT_TYPES
    tube_length_mm: float = 0.0         # for chambered ports
    label: str = "Side port"

    @classmethod
    def from_circle_mm(
        cls,
        diameter_mm: float,
        position: str = "upper_bass",
        port_type: str = "round",
        rim_thickness_mm: float = 2.3,
        tube_length_mm: float = 0.0,
        label: str = "Side port",
    ) -> "SidePortSpec":
        r = (diameter_mm / 2) / 1000.0
        # Apply perimeter factor from port type
        pf = SIDE_PORT_TYPES.get(port_type, {}).get("perim_factor", 1.0)
        return cls(
            area_m2=math.pi * r * r,
            perim_m=2 * math.pi * r * pf,
            thickness_m=rim_thickness_mm / 1000.0,
            position=position,
            port_type=port_type,
            tube_length_mm=tube_length_mm,
            label=label,
        )

    def to_port_spec(self, k0: float = K0, gamma: float = GAMMA) -> PortSpec:
        """
        Convert to PortSpec for Helmholtz calculation.
        Tube length adds directly to effective neck length.
        """
        # Effective thickness includes any added tube length
        effective_thickness_m = self.thickness_m + (self.tube_length_mm / 1000.0)
        return PortSpec(
            area_m2=self.area_m2,
            perim_m=self.perim_m,
            location="side",
            thickness_m=effective_thickness_m,
            label=self.label,
        )

    @property
    def position_info(self) -> Dict:
        return SIDE_PORT_POSITIONS.get(self.position, SIDE_PORT_POSITIONS["upper_bass"])

    @property
    def type_info(self) -> Dict:
        return SIDE_PORT_TYPES.get(self.port_type, SIDE_PORT_TYPES["round"])

    @property
    def diameter_equiv_mm(self) -> float:
        return 2 * math.sqrt(self.area_m2 / math.pi) * 1000.0


@dataclass
class SidePortResult:
    """Analysis result for a side port."""
    port: SidePortSpec
    f_H_shift_hz: float            # Predicted Helmholtz shift from this port
    radiation_description: str
    structural_clearance: str
    coupling_level: str            # "low" | "high" | "minimal"
    f_H_shift_label: str
    warnings: List[str]


def analyze_side_port(
    port: SidePortSpec,
    body_volume_m3: float,
    main_ports: List[PortSpec],
    rim_depth_at_position_mm: float = 90.0,
    k0: float = K0,
    gamma: float = GAMMA,
) -> SidePortResult:
    """
    Analyze a single side port — Helmholtz contribution, radiation, structural check.

    Args:
        port:                     The SidePortSpec to analyze
        body_volume_m3:           Guitar body volume
        main_ports:               Top/main ports (for baseline f_H comparison)
        rim_depth_at_position_mm: Rim depth where port sits (constrains max diameter)
        k0, gamma:                Helmholtz constants

    Returns:
        SidePortResult with radiation description and structural guidance
    """
    warnings: List[str] = []
    pos_info = port.position_info
    type_info = port.type_info

    # Baseline f_H (without this side port)
    if main_ports:
        f_base, _ = compute_helmholtz_multiport(body_volume_m3, main_ports, k0, gamma)
    else:
        f_base = 0.0

    # f_H with this port added
    all_ports = main_ports + [port.to_port_spec(k0, gamma)]
    f_with, _ = compute_helmholtz_multiport(body_volume_m3, all_ports, k0, gamma)
    shift = f_with - f_base

    # Structural checks
    diam_mm = port.diameter_equiv_mm
    if diam_mm > rim_depth_at_position_mm * 0.75:
        warnings.append(
            f"Port diameter {diam_mm:.0f}mm exceeds 75% of rim depth {rim_depth_at_position_mm:.0f}mm "
            f"at this position — risk of structural weakness in the rim."
        )

    if port.position == "waist" and diam_mm > 25:
        warnings.append(
            f"Waist rim is narrow. Port diameter {diam_mm:.0f}mm may be too large — "
            "waist depth is typically 70–80mm. Keep ports here ≤25mm diameter."
        )

    if port.tube_length_mm > 0:
        warnings.append(
            f"Chambered port: {port.tube_length_mm:.0f}mm tube adds to L_eff. "
            "Route channel before installing kerfing. Verify internal clearance."
        )

    return SidePortResult(
        port=port,
        f_H_shift_hz=round(shift, 1),
        radiation_description=pos_info["radiation"],
        structural_clearance=pos_info["structural"],
        coupling_level=pos_info["coupling"],
        f_H_shift_label=pos_info["f_H_shift"],
        warnings=warnings,
    )


# ── Inverse solver ────────────────────────────────────────────────────────────

def solve_for_diameter_mm(
    target_f_hz: float,
    volume_m3: float,
    thickness_m: float = 0.0025,
    k0: float = K0,
    gamma: float = GAMMA,
    plate_mass_factor: float = PLATE_MASS_FACTOR,
    min_mm: float = 40.0,
    max_mm: float = 150.0,
) -> Dict:
    """
    Inverse Helmholtz solver — find the diameter needed to hit a target f_H.

    Since f ∝ √A and A = πr², and f is linear in √A, the analytical inverse is:

        A_needed = (f_target/PMF × 2π/c)² × V × L_eff

    But L_eff itself depends on r (via k × r_eq), making this implicit.
    We use a simple bisection search (converges in <20 iterations for ±0.01Hz).

    Args:
        target_f_hz:       Target assembled-instrument air resonance (Hz)
        volume_m3:         Body internal volume (m³)
        thickness_m:       Top plate thickness at hole (m)
        k0, gamma:         End-correction constants
        plate_mass_factor: Coupling correction (default 0.92)
        min_mm, max_mm:    Search bounds for diameter (mm)

    Returns:
        Dict with diameter_mm, achieved_f_hz, area_cm2, warnings
    """
    warnings: List[str] = []

    def predict(diam_mm: float) -> float:
        r = (diam_mm / 2) / 1000.0
        p = PortSpec(
            area_m2=math.pi * r * r,
            perim_m=2 * math.pi * r,
            location="top",
            thickness_m=thickness_m,
        )
        f, _ = compute_helmholtz_multiport(volume_m3, [p], k0, gamma, plate_mass_factor)
        return f

    # Bisection search
    lo, hi = min_mm, max_mm
    for _ in range(60):
        mid = (lo + hi) / 2.0
        f_mid = predict(mid)
        if f_mid < target_f_hz:
            lo = mid
        else:
            hi = mid
        if (hi - lo) < 0.01:
            break

    result_diam = (lo + hi) / 2.0
    achieved_f = predict(result_diam)

    if result_diam <= min_mm + 0.1:
        warnings.append(
            f"Target {target_f_hz:.0f} Hz requires diameter below {min_mm:.0f}mm — "
            "consider smaller body volume or thicker top."
        )
    elif result_diam >= max_mm - 0.1:
        warnings.append(
            f"Target {target_f_hz:.0f} Hz requires diameter above {max_mm:.0f}mm — "
            "consider larger body volume or thinner top."
        )

    r_mm = result_diam / 2.0
    return {
        "diameter_mm": round(result_diam, 1),
        "radius_mm": round(r_mm, 1),
        "achieved_f_hz": round(achieved_f, 1),
        "error_hz": round(achieved_f - target_f_hz, 2),
        "area_cm2": round(math.pi * (r_mm / 10.0) ** 2, 2),
        "warnings": warnings,
    }


def solve_for_diameter_with_side_port_mm(
    target_f_hz: float,
    volume_m3: float,
    side_port_diameter_mm: float,
    thickness_m: float = 0.0025,
    rim_thickness_m: float = 0.0023,
    k0: float = K0,
    gamma: float = GAMMA,
) -> Dict:
    """
    Inverse solver when a side port is already planned.
    Returns the main hole diameter needed to hit target f_H given the side port.
    """
    side_r = (side_port_diameter_mm / 2) / 1000.0
    side_port = PortSpec(
        area_m2=math.pi * side_r * side_r,
        perim_m=2 * math.pi * side_r,
        location="side",
        thickness_m=rim_thickness_m,
    )

    def predict_total(main_diam_mm: float) -> float:
        r = (main_diam_mm / 2) / 1000.0
        main_port = PortSpec(
            area_m2=math.pi * r * r,
            perim_m=2 * math.pi * r,
            location="top",
            thickness_m=thickness_m,
        )
        f, _ = compute_helmholtz_multiport(volume_m3, [main_port, side_port], k0, gamma)
        return f

    lo, hi = 40.0, 140.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if predict_total(mid) < target_f_hz:
            lo = mid
        else:
            hi = mid
        if (hi - lo) < 0.01:
            break

    result_diam = (lo + hi) / 2.0
    return {
        "main_diameter_mm": round(result_diam, 1),
        "side_port_diameter_mm": round(side_port_diameter_mm, 1),
        "achieved_f_hz": round(predict_total(result_diam), 1),
    }


# ── Sensitivity curve ─────────────────────────────────────────────────────────

def compute_sensitivity_curve(
    volume_m3: float,
    current_diameter_mm: float,
    thickness_m: float = 0.0025,
    k0: float = K0,
    gamma: float = GAMMA,
    plate_mass_factor: float = PLATE_MASS_FACTOR,
    range_mm: float = 25.0,
    steps: int = 20,
) -> List[Dict]:
    """
    Compute f_H vs diameter curve around the current design point.

    Returns a list of {diameter_mm, f_hz} dicts spanning
    current_diameter ± range_mm in `steps` increments.

    Useful for showing how sensitive f_H is to small changes in diameter —
    a steep curve means careful sizing is critical; a flat curve means
    more design freedom.
    """
    d_min = max(40.0, current_diameter_mm - range_mm)
    d_max = min(150.0, current_diameter_mm + range_mm)
    step = (d_max - d_min) / (steps - 1)
    curve = []
    for i in range(steps):
        d = d_min + i * step
        r = (d / 2) / 1000.0
        p = PortSpec(
            area_m2=math.pi * r * r,
            perim_m=2 * math.pi * r,
            location="top",
            thickness_m=thickness_m,
        )
        f, _ = compute_helmholtz_multiport(volume_m3, [p], k0, gamma, plate_mass_factor)
        curve.append({"diameter_mm": round(d, 1), "f_hz": round(f, 1)})
    return curve


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
