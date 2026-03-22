"""
soundhole_presets.py — Soundhole Preset Data and Lookup Tables
================================================================
Extracted from soundhole_calc.py as part of DECOMP-002 Phase 5.

Contains:
  - PRESETS: calibrated instrument soundhole configurations
  - BODY_DIMENSION_PRESETS: reference body dimension data
  - TOP_SPECIES_THICKNESS: top plate thickness by species
  - STANDARD_DIAMETERS_MM: standard soundhole diameters by body style
  - Lookup and registry functions for presets and species data

All preset configurations include measured/documented instrument values
for validation and calibration purposes.
"""

from __future__ import annotations

from typing import Dict, List, Optional

# Import PortSpec for type hints and preset definitions
# This creates a circular import that's resolved at runtime since
# soundhole_calc imports from this module
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .soundhole_calc import PortSpec, SoundholeResult


# ── Instrument Presets ────────────────────────────────────────────────────────

PRESETS: Dict[str, Dict] = {
    "martin_om": {
        "label": "Martin OM (Orchestra Model)",
        "volume_liters": 17.5,
        "ports": None,  # Will be populated when PortSpec is available
        "ring_width_mm": 8.0,
        "x_from_neck_fraction": 0.333,
        "body_length_mm": 495,
        "target_f_hz": 108,
        "notes": "Standard fingerstyle. Balanced bass/treble. X-brace with soundhole patch.",
    },
    "martin_d28": {
        "label": "Martin D-28 (Dreadnought)",
        "volume_liters": 22.0,
        "ports": None,  # Will be populated when PortSpec is available
        "ring_width_mm": 8.0,
        "x_from_neck_fraction": 0.333,
        "body_length_mm": 508,
        "target_f_hz": 98,
        "notes": "High-volume projection. Scalloped X-brace. Lower f_H from larger body volume.",
    },
    "gibson_j45": {
        "label": "Gibson J-45 (Slope Shoulder)",
        "volume_liters": 21.0,
        "ports": None,  # Will be populated when PortSpec is available
        "ring_width_mm": 8.0,
        "x_from_neck_fraction": 0.330,
        "body_length_mm": 502,
        "target_f_hz": 100,
        "notes": "Mahogany top variant available. Ladder-braced version exists but X-brace is standard.",
    },
    "classical": {
        "label": "Classical Guitar",
        "volume_liters": 19.0,
        "ports": None,  # Will be populated when PortSpec is available
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
        "ports": None,  # Will be populated when PortSpec is available
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
        "ports": None,  # Will be populated when PortSpec is available
        "ring_width_mm": 8.0,
        "x_from_neck_fraction": 0.333,
        "body_length_mm": 495,
        "target_f_hz": 112,
        "notes": "Side port boosts player-ear response. f_H shift from side port is modest (+3-8 Hz).",
    },
    "benedetto_17": {
        "label": "Benedetto 17\" Archtop (F-holes)",
        "volume_liters": 24.0,
        "ports": None,  # Will be populated when PortSpec is available
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


def _initialize_preset_ports():
    """
    Initialize PortSpec instances for PRESETS.
    Called after module import to avoid circular dependency.
    """
    # Import here to avoid circular import at module load time
    from .soundhole_calc import PortSpec

    PRESETS["martin_om"]["ports"] = [PortSpec.from_circle_mm(96, label="Round soundhole")]
    PRESETS["martin_d28"]["ports"] = [PortSpec.from_circle_mm(100, label="Round soundhole")]
    PRESETS["gibson_j45"]["ports"] = [PortSpec.from_circle_mm(98, label="Round soundhole")]
    PRESETS["classical"]["ports"] = [PortSpec.from_circle_mm(85, thickness_mm=2.0, label="Round soundhole")]
    PRESETS["selmer_oval"]["ports"] = [PortSpec.from_oval_mm(80, 110, label="Oval soundhole")]
    PRESETS["om_side_port"]["ports"] = [
        PortSpec.from_circle_mm(90, location="top", label="Main soundhole"),
        PortSpec.from_circle_mm(30, location="side", thickness_mm=2.3, label="Side port (upper bass)"),
    ]
    PRESETS["benedetto_17"]["ports"] = [
        PortSpec.from_oval_mm(23, 110, location="top", thickness_mm=5.0, label="F-hole left"),
        PortSpec.from_oval_mm(23, 110, location="top", thickness_mm=5.0, label="F-hole right"),
    ]


def get_preset(name: str) -> Optional[Dict]:
    """
    Return preset config by name, or None if not found.

    Lazy-initializes PortSpec instances on first access.
    """
    # Initialize ports if not already done
    if PRESETS["martin_om"]["ports"] is None:
        _initialize_preset_ports()

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


def analyze_preset(preset_name: str) -> Optional["SoundholeResult"]:
    """
    Run full analysis on a named preset.

    Returns None if preset not found.
    """
    # Import here to avoid circular import
    from .soundhole_calc import analyze_soundhole

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


# ── Body Dimension Presets ────────────────────────────────────────────────────

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


# ── Top Species Thickness Data ────────────────────────────────────────────────

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


# ── Standard Soundhole Diameters by Body Style ────────────────────────────────

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


def list_body_styles() -> List[str]:
    """Return list of supported body styles."""
    return [k for k in STANDARD_DIAMETERS_MM.keys() if k != "archtop"]


def get_standard_diameter(body_style: str) -> Optional[float]:
    """Get standard soundhole diameter for a body style."""
    style_key = body_style.lower().replace("-", "_").replace(" ", "_")
    return STANDARD_DIAMETERS_MM.get(style_key)
