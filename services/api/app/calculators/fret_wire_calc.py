"""
Fret Wire Selection Calculator (GEOMETRY-006)
==============================================

Fret wire selection based on playing style, fretboard material,
and neck profile.

Fret wire dimensions:
    crown_width: 1.6-2.9mm (narrower = vintage, wider = modern)
    crown_height: 0.89-1.65mm (shorter = vintage, taller = jumbo)
    tang_depth: 1.5-2.0mm (must match slot depth)

Materials:
    nickel_silver: Standard, warm feel, moderate wear
    stainless: Hard, bright, very durable
    evo_gold: Gold-colored, hypoallergenic, good wear
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Literal


# ─── FretWireSpec Dataclass ───────────────────────────────────────────────────

@dataclass
class FretWireSpec:
    """Specification for a fret wire profile."""
    name: str
    crown_width_mm: float
    crown_height_mm: float
    tang_depth_mm: float
    tang_width_mm: float
    material: str           # "nickel_silver" | "stainless" | "evo_gold"
    hardness_hv: int        # Vickers hardness
    wear_factor: float      # Relative wear rate (nickel_silver = 1.0)
    recommended_for: List[str]
    gate: str               # GREEN, YELLOW
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Fret Wire Catalog ────────────────────────────────────────────────────────

FRET_WIRE_CATALOG: Dict[str, FretWireSpec] = {
    "vintage_narrow": FretWireSpec(
        name="vintage_narrow",
        crown_width_mm=1.65,
        crown_height_mm=0.89,
        tang_depth_mm=1.50,
        tang_width_mm=0.51,
        material="nickel_silver",
        hardness_hv=180,
        wear_factor=1.0,
        recommended_for=["fingerstyle", "jazz", "vintage_tone"],
        gate="GREEN",
        notes="Classic vintage feel, suits 7.25\" radius boards",
    ),
    "medium": FretWireSpec(
        name="medium",
        crown_width_mm=2.06,
        crown_height_mm=1.19,
        tang_depth_mm=1.65,
        tang_width_mm=0.53,
        material="nickel_silver",
        hardness_hv=180,
        wear_factor=1.0,
        recommended_for=["all_styles", "versatile"],
        gate="GREEN",
        notes="Most versatile choice, suits most playing styles",
    ),
    "medium_jumbo": FretWireSpec(
        name="medium_jumbo",
        crown_width_mm=2.54,
        crown_height_mm=1.40,
        tang_depth_mm=1.80,
        tang_width_mm=0.56,
        material="nickel_silver",
        hardness_hv=180,
        wear_factor=1.0,
        recommended_for=["flatpick", "rock", "bending"],
        gate="GREEN",
        notes="Good for bending, modern feel",
    ),
    "jumbo": FretWireSpec(
        name="jumbo",
        crown_width_mm=2.79,
        crown_height_mm=1.52,
        tang_depth_mm=1.90,
        tang_width_mm=0.58,
        material="nickel_silver",
        hardness_hv=180,
        wear_factor=1.0,
        recommended_for=["shred", "rock", "heavy_bending"],
        gate="GREEN",
        notes="Maximum sustain and easy bending, requires light touch",
    ),
    "extra_jumbo": FretWireSpec(
        name="extra_jumbo",
        crown_width_mm=2.90,
        crown_height_mm=1.65,
        tang_depth_mm=2.00,
        tang_width_mm=0.61,
        material="nickel_silver",
        hardness_hv=180,
        wear_factor=1.0,
        recommended_for=["shred", "metal"],
        gate="YELLOW",
        notes="Very tall frets, can cause intonation issues if pressed too hard",
    ),
    "evo_6105": FretWireSpec(
        name="evo_6105",
        crown_width_mm=2.29,
        crown_height_mm=1.14,
        tang_depth_mm=1.70,
        tang_width_mm=0.53,
        material="evo_gold",
        hardness_hv=300,
        wear_factor=0.4,
        recommended_for=["all_styles", "nickel_allergy", "durability"],
        gate="GREEN",
        notes="Gold color, hypoallergenic, 2-3x longer life than nickel",
    ),
    "stainless_6105": FretWireSpec(
        name="stainless_6105",
        crown_width_mm=2.29,
        crown_height_mm=1.14,
        tang_depth_mm=1.70,
        tang_width_mm=0.53,
        material="stainless",
        hardness_hv=400,
        wear_factor=0.2,
        recommended_for=["all_styles", "durability", "professional"],
        gate="GREEN",
        notes="Hardest option, requires carbide tools for leveling",
    ),
}


# ─── Playing Style Preferences ────────────────────────────────────────────────

STYLE_PREFERENCES: Dict[str, Dict[str, Any]] = {
    "fingerstyle": {
        "preferred_height": (0.89, 1.19),  # Lower frets for precision
        "preferred_width": (1.65, 2.30),   # Narrower for clean notes
        "weight": {"crown_height": -1, "crown_width": -1},  # Prefer smaller
    },
    "flatpick": {
        "preferred_height": (1.14, 1.52),
        "preferred_width": (2.06, 2.79),
        "weight": {"crown_height": 0.5, "crown_width": 0.5},
    },
    "shred": {
        "preferred_height": (1.40, 1.65),  # Taller for effortless bending
        "preferred_width": (2.54, 2.90),   # Wider for speed
        "weight": {"crown_height": 1, "crown_width": 1},  # Prefer larger
    },
    "jazz": {
        "preferred_height": (0.89, 1.19),  # Lower for clean articulation
        "preferred_width": (1.65, 2.30),
        "weight": {"crown_height": -0.5, "crown_width": -0.5},
    },
}

# ─── Fretboard Material Compatibility ─────────────────────────────────────────

FRETBOARD_COMPATIBILITY: Dict[str, Dict[str, Any]] = {
    "rosewood": {
        "tang_depth_range": (1.50, 2.00),  # Softer wood, standard tangs
        "notes": "Standard fret installation, glue optional",
    },
    "ebony": {
        "tang_depth_range": (1.50, 1.90),  # Dense wood, shallower slots
        "notes": "Dense wood, may need narrower tang or compression fit",
    },
    "maple": {
        "tang_depth_range": (1.50, 2.00),  # Hard maple, standard
        "notes": "Finished maple may need slot widening for tang barbs",
    },
    "pau_ferro": {
        "tang_depth_range": (1.50, 2.00),
        "notes": "Similar to rosewood, standard installation",
    },
    "richlite": {
        "tang_depth_range": (1.60, 2.00),
        "notes": "Composite material, consistent slot sizing",
    },
}

# ─── Neck Profile Preferences ─────────────────────────────────────────────────

NECK_PROFILE_PREFERENCES: Dict[str, Dict[str, Any]] = {
    "C": {
        "preferred_height_range": (0.89, 1.52),  # Most versatile
        "notes": "Standard C shape suits most fret heights",
    },
    "D": {
        "preferred_height_range": (1.14, 1.65),  # Flatter, modern
        "notes": "Flatter profile pairs well with taller frets",
    },
    "V": {
        "preferred_height_range": (0.89, 1.19),  # Vintage
        "notes": "V profile typically paired with vintage frets",
    },
    "U": {
        "preferred_height_range": (0.89, 1.40),  # Chunky
        "notes": "U profile works with lower to medium frets",
    },
}

# ─── String Gauge Influence ───────────────────────────────────────────────────

STRING_GAUGE_INFLUENCE: Dict[str, Dict[str, Any]] = {
    "light": {
        "height_bonus": 0.0,  # No adjustment
        "notes": "Light strings work with any fret height",
    },
    "medium": {
        "height_bonus": 0.1,  # Slight preference for taller
        "notes": "Medium strings benefit from slightly taller frets",
    },
    "heavy": {
        "height_bonus": 0.2,  # Prefer taller frets
        "notes": "Heavy strings need taller frets for comfortable bending",
    },
}


# ─── Core Functions ───────────────────────────────────────────────────────────

def _score_fret_for_style(
    fret: FretWireSpec,
    playing_style: str,
    string_gauge: str,
) -> float:
    """Score a fret wire based on playing style preferences."""
    style_prefs = STYLE_PREFERENCES.get(playing_style, STYLE_PREFERENCES["flatpick"])
    gauge_info = STRING_GAUGE_INFLUENCE.get(string_gauge, STRING_GAUGE_INFLUENCE["medium"])

    score = 50.0  # Base score

    # Height scoring
    min_h, max_h = style_prefs["preferred_height"]
    adjusted_min_h = min_h + gauge_info["height_bonus"]
    adjusted_max_h = max_h + gauge_info["height_bonus"]

    if adjusted_min_h <= fret.crown_height_mm <= adjusted_max_h:
        score += 20  # In preferred range
    elif fret.crown_height_mm < adjusted_min_h:
        score -= (adjusted_min_h - fret.crown_height_mm) * 15
    else:
        score -= (fret.crown_height_mm - adjusted_max_h) * 10

    # Width scoring
    min_w, max_w = style_prefs["preferred_width"]
    if min_w <= fret.crown_width_mm <= max_w:
        score += 15
    elif fret.crown_width_mm < min_w:
        score -= (min_w - fret.crown_width_mm) * 10
    else:
        score -= (fret.crown_width_mm - max_w) * 8

    # Material bonus for durability preference
    if fret.material == "stainless":
        score += 5  # Slight bonus for durability
    elif fret.material == "evo_gold":
        score += 3  # Bonus for durability + hypoallergenic

    # Recommended_for bonus
    if playing_style in fret.recommended_for or "all_styles" in fret.recommended_for:
        score += 15

    return max(0, min(100, score))


def _check_fretboard_compatibility(
    fret: FretWireSpec,
    fretboard_material: str,
) -> tuple[bool, str]:
    """Check if fret wire is compatible with fretboard material."""
    fb_info = FRETBOARD_COMPATIBILITY.get(
        fretboard_material.lower(),
        FRETBOARD_COMPATIBILITY["rosewood"]
    )
    min_tang, max_tang = fb_info["tang_depth_range"]

    if min_tang <= fret.tang_depth_mm <= max_tang:
        return True, fb_info["notes"]
    elif fret.tang_depth_mm > max_tang:
        return False, f"Tang depth {fret.tang_depth_mm}mm too deep for {fretboard_material}"
    else:
        return True, f"Tang depth {fret.tang_depth_mm}mm on shallow end for {fretboard_material}"


def _check_neck_profile_compatibility(
    fret: FretWireSpec,
    neck_profile: str,
) -> tuple[bool, str]:
    """Check if fret wire suits neck profile."""
    profile_info = NECK_PROFILE_PREFERENCES.get(
        neck_profile.upper(),
        NECK_PROFILE_PREFERENCES["C"]
    )
    min_h, max_h = profile_info["preferred_height_range"]

    if min_h <= fret.crown_height_mm <= max_h:
        return True, profile_info["notes"]
    else:
        return False, f"Crown height {fret.crown_height_mm}mm outside typical range for {neck_profile} profile"


def recommend_fret_wire(
    playing_style: str = "flatpick",
    fretboard_material: str = "rosewood",
    neck_profile: str = "C",
    string_gauge: str = "medium",
) -> List[FretWireSpec]:
    """
    Recommend fret wire based on playing style, fretboard, neck profile, and string gauge.

    Args:
        playing_style: "fingerstyle" | "flatpick" | "shred" | "jazz"
        fretboard_material: "rosewood" | "ebony" | "maple" | "pau_ferro" | "richlite"
        neck_profile: "C" | "D" | "V" | "U"
        string_gauge: "light" | "medium" | "heavy"

    Returns:
        List of FretWireSpec ranked by suitability (best first)
    """
    # Normalize inputs
    playing_style = playing_style.lower().strip()
    fretboard_material = fretboard_material.lower().strip()
    neck_profile = neck_profile.upper().strip()
    string_gauge = string_gauge.lower().strip()

    scored_frets: List[tuple[float, FretWireSpec]] = []

    for name, fret in FRET_WIRE_CATALOG.items():
        # Calculate base score from playing style
        score = _score_fret_for_style(fret, playing_style, string_gauge)

        # Check fretboard compatibility
        fb_compat, fb_note = _check_fretboard_compatibility(fret, fretboard_material)
        if not fb_compat:
            score -= 20

        # Check neck profile compatibility
        np_compat, np_note = _check_neck_profile_compatibility(fret, neck_profile)
        if not np_compat:
            score -= 15

        # Create a copy with updated notes
        updated_notes = fret.notes
        if not fb_compat:
            updated_notes += f". {fb_note}"
        if not np_compat:
            updated_notes += f". {np_note}"

        # Create updated spec
        updated_fret = FretWireSpec(
            name=fret.name,
            crown_width_mm=fret.crown_width_mm,
            crown_height_mm=fret.crown_height_mm,
            tang_depth_mm=fret.tang_depth_mm,
            tang_width_mm=fret.tang_width_mm,
            material=fret.material,
            hardness_hv=fret.hardness_hv,
            wear_factor=fret.wear_factor,
            recommended_for=fret.recommended_for,
            gate="GREEN" if score >= 60 else "YELLOW",
            notes=updated_notes,
        )

        scored_frets.append((score, updated_fret))

    # Sort by score descending
    scored_frets.sort(key=lambda x: -x[0])

    return [fret for _, fret in scored_frets]


def get_fret_wire(name: str) -> FretWireSpec | None:
    """Get a specific fret wire by name."""
    return FRET_WIRE_CATALOG.get(name.lower().strip())


def list_fret_wire_names() -> List[str]:
    """Return list of available fret wire names."""
    return list(FRET_WIRE_CATALOG.keys())


def list_fret_wire_catalog() -> List[FretWireSpec]:
    """Return full catalog as list."""
    return list(FRET_WIRE_CATALOG.values())


def list_playing_styles() -> List[str]:
    """Return list of supported playing styles."""
    return list(STYLE_PREFERENCES.keys())


def list_fretboard_materials() -> List[str]:
    """Return list of supported fretboard materials."""
    return list(FRETBOARD_COMPATIBILITY.keys())


def list_neck_profiles() -> List[str]:
    """Return list of supported neck profiles."""
    return list(NECK_PROFILE_PREFERENCES.keys())


def list_string_gauges() -> List[str]:
    """Return list of supported string gauge categories."""
    return list(STRING_GAUGE_INFLUENCE.keys())
