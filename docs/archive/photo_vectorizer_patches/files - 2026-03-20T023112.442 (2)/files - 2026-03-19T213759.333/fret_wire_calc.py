# services/api/app/calculators/fret_wire_calc.py
"""
Fret Wire Selection Calculator — GEOMETRY-006

Covers fret wire profile selection, playability characteristics, wear rates,
leveling headroom, material hardness, slot requirements, and fretboard
thickness interaction.

Physical model
==============

A fret wire has four critical dimensions:

    Crown width (W):  lateral dimension across the fretboard
    Crown height (H): vertical dimension above the fretboard surface
    Tang depth (D):   how deep the tang penetrates the fret slot
    Tang width (T):   kerf the tang occupies (sets slot width requirement)

The crown geometry defines a circular arc. The radius of that arc determines
the width of the string contact zone — critical for intonation precision:

    R_crown = (W/2)² / (2H) + H/2     [chord-sagitta formula]

Narrower contact = more precise intonation but faster groove formation.

Leveling headroom
=================

Crown height above the fretboard minus a minimum safe crown height gives the
usable material for leveling passes:

    usable = H - H_min           H_min = 0.015\" (0.38mm) empirical minimum
    passes ≈ usable / 0.006\"    average 0.006\" removed per leveling pass

Action interaction
==================

String height above the fret crown is what matters for playing comfort.
A taller crown reduces the required saddle/nut action to achieve the same
string-to-crown clearance:

    clearance = action_at_fret - H_crown

This is why tall-narrow wire allows lower action settings while maintaining
playability — the crown itself contributes to the effective string height.

Material hardness
=================

    Nickel-Silver (18%): HV 130  — standard, easy to work
    EVO Gold (Jescar):   HV 350  — ~2.7× harder, titanium alloy
    Stainless Steel:     HV 500  — ~3.8× harder, requires carbide tooling

Sources:
    - Dunlop Manufacturing fret wire catalog
    - Jescar Fastener Technologies EVO Gold specifications
    - StewMac fret wire catalog
    - Gore & Gilet, Vol. 1, fretboard geometry
    - Siminoff, "The Luthier's Handbook" (fret installation)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Physical constants
# ─────────────────────────────────────────────────────────────────────────────

# Minimum safe crown height after leveling (below this the fret is dead)
H_MIN_CROWN_IN: float = 0.015   # inches  (0.38 mm)

# Average material removed per leveling pass
H_PER_PASS_IN: float = 0.006    # inches  (0.15 mm)

# Minimum wood below tang for structural integrity of fretboard
MIN_WOOD_BELOW_TANG_IN: float = 0.040   # inches  (1.02 mm)

# Slot clearance per side (tang fits with this much room to spare)
SLOT_CLEARANCE_EACH_SIDE_IN: float = 0.0015  # inches

# Contact depth used for crown contact-width calculation
# Approximation: string indent = half of string diameter for light gauge
STRING_CONTACT_DEPTH_IN: float = 0.001  # inches


# ─────────────────────────────────────────────────────────────────────────────
# Material definitions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FretMaterial:
    """Fret wire material properties."""
    key: str
    label: str
    hardness_HV: int         # Vickers hardness
    relative_hardness: float  # vs nickel-silver = 1.0
    tooling_notes: str
    wear_multiplier: float    # 1.0 = nickel-silver baseline longevity


FRET_MATERIALS: Dict[str, FretMaterial] = {
    "nickel_silver": FretMaterial(
        key="nickel_silver",
        label="Nickel-Silver (18%)",
        hardness_HV=130,
        relative_hardness=1.0,
        tooling_notes=(
            "Standard fret files work well. Easy to level, crown, and polish. "
            "Compatible with all standard fret tools."
        ),
        wear_multiplier=1.0,
    ),
    "evo_gold": FretMaterial(
        key="evo_gold",
        label="EVO Gold (Jescar)",
        hardness_HV=350,
        relative_hardness=2.7,
        tooling_notes=(
            "Standard files still work but dull faster. Diamond or carbide-coated "
            "files recommended for leveling and crowning. More spring-back during "
            "installation — prebend radius must be accurate."
        ),
        wear_multiplier=3.0,
    ),
    "stainless_steel": FretMaterial(
        key="stainless_steel",
        label="Stainless Steel",
        hardness_HV=500,
        relative_hardness=3.8,
        tooling_notes=(
            "WARNING: Standard fret files are destroyed on first contact. "
            "Carbide or diamond tooling required for all operations. "
            "Work hardens during hammering — precise slot prep is mandatory. "
            "Generates significant heat; risk of finish damage on acoustic guitars. "
            "Not recommended for acoustic instrument builders without stainless experience."
        ),
        wear_multiplier=10.0,
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Profile definitions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FretProfile:
    """
    Fret wire profile geometry.

    All dimensions in inches — the lutherie industry standard.
    Millimeter conversions are computed properties.

    The crown is the curved portion above the fretboard.
    The tang is the portion that penetrates the fret slot.
    """
    key: str
    label: str
    family: str               # "vintage" | "medium" | "tall"

    # Crown geometry
    crown_width_in: float     # W: lateral width of crown
    crown_height_in: float    # H: height above fretboard surface

    # Tang geometry
    tang_depth_in: float      # D: penetration into fret slot
    tang_width_in: float      # T: width of tang (kerf)

    # Slot specification
    slot_width_in: float      # recommended slot width (tang + clearance)
    slot_depth_in: float      # recommended slot depth (tang + seating margin)

    # Catalog references
    dunlop: str = ""
    stewmac: str = ""
    jescar: str = ""

    # Characterization
    playability: str = ""
    wear_notes: str = ""
    leveling_notes: str = ""
    install_notes: str = ""

    @property
    def crown_width_mm(self) -> float:
        return round(self.crown_width_in * 25.4, 2)

    @property
    def crown_height_mm(self) -> float:
        return round(self.crown_height_in * 25.4, 2)

    @property
    def tang_depth_mm(self) -> float:
        return round(self.tang_depth_in * 25.4, 2)

    @property
    def crown_radius_in(self) -> float:
        """Radius of curvature of crown arc (chord-sagitta formula)."""
        w = self.crown_width_in
        h = self.crown_height_in
        return (w / 2) ** 2 / (2 * h) + h / 2

    @property
    def contact_width_in(self) -> float:
        """Approximate string contact width at surface of crown."""
        R = self.crown_radius_in
        d = STRING_CONTACT_DEPTH_IN
        return 2 * math.sqrt(max(0.0, 2 * R * d - d ** 2))

    @property
    def leveling_headroom_in(self) -> float:
        """Usable material for leveling passes."""
        return max(0.0, self.crown_height_in - H_MIN_CROWN_IN)

    @property
    def leveling_passes(self) -> int:
        """Approximate number of leveling passes before refret."""
        return max(0, int(self.leveling_headroom_in / H_PER_PASS_IN))


FRET_PROFILES: Dict[str, FretProfile] = {

    # ── Vintage family ────────────────────────────────────────────────────────
    "vintage_narrow": FretProfile(
        key="vintage_narrow",
        label="Vintage Narrow",
        family="vintage",
        crown_width_in=0.082,
        crown_height_in=0.036,
        tang_depth_in=0.050,
        tang_width_in=0.020,
        slot_width_in=0.023,
        slot_depth_in=0.055,
        dunlop="6230",
        playability=(
            "Wide, low profile. Closest to vintage Gibson construction. "
            "Strings sit in a shallow groove — the finger touches the fretboard "
            "through the string, giving a tactile 'vintage feel.' "
            "Bending is comfortable for chord players. Lead bending requires more "
            "finger force. Not favored for very low action setups."
        ),
        wear_notes=(
            "Lowest leveling headroom of all profiles. "
            "Grooves form quickly with medium or heavy playing — expect 2-3 years "
            "before level/crown is needed on a frequently played instrument."
        ),
        leveling_notes=(
            "Only ~3 leveling passes before refret. Plan to refret rather than "
            "repeatedly redress. Initial installation quality is critical."
        ),
        install_notes=(
            "Easy to seat. Low crown height means less tendency to spring back. "
            "Prebend to fretboard radius. Standard hammer or arbor press installation."
        ),
    ),

    "vintage_medium": FretProfile(
        key="vintage_medium",
        label="Vintage Medium",
        family="vintage",
        crown_width_in=0.102,
        crown_height_in=0.042,
        tang_depth_in=0.050,
        tang_width_in=0.020,
        slot_width_in=0.023,
        slot_depth_in=0.055,
        dunlop="6150",
        stewmac="148",
        playability=(
            "The Fender American standard for decades. Slightly taller than 6230 "
            "but still in the vintage feel range. Wide crown provides stable "
            "intonation contact. String does not notch as deeply into the crown. "
            "Good balance for mixed acoustic/electric players."
        ),
        wear_notes=(
            "Similar to vintage narrow but slightly more headroom. "
            "Nickel-silver will show grooves within 2-4 years of daily play."
        ),
        leveling_notes="~4 leveling passes possible. Better longevity than vintage narrow.",
        install_notes="Standard installation. No special tooling required.",
    ),

    # ── Medium family ─────────────────────────────────────────────────────────
    "medium": FretProfile(
        key="medium",
        label="Medium",
        family="medium",
        crown_width_in=0.102,
        crown_height_in=0.045,
        tang_depth_in=0.050,
        tang_width_in=0.020,
        slot_width_in=0.023,
        slot_depth_in=0.055,
        dunlop="6160",
        stewmac="150",
        playability=(
            "Balanced profile. Enough crown height for smooth bending without the "
            "fatigue of tall wire on chord work. "
            "Wide crown provides stable string guidance. "
            "Good all-purpose choice for acoustic flatpicking and chord/melody work. "
            "Recommended for first fret jobs — forgiving to dress and crown."
        ),
        wear_notes="3-5 years before grooving with regular play in nickel-silver.",
        leveling_notes="~5 leveling passes if initial installation is clean.",
        install_notes="Standard installation. Most forgiving profile for new builders.",
    ),

    "medium_jumbo": FretProfile(
        key="medium_jumbo",
        label="Medium-Jumbo",
        family="medium",
        crown_width_in=0.106,
        crown_height_in=0.036,
        tang_depth_in=0.050,
        tang_width_in=0.020,
        slot_width_in=0.023,
        slot_depth_in=0.055,
        dunlop="6130",
        stewmac="155",
        playability=(
            "Wide but not tall — the 'modern vintage' compromise. "
            "Players transitioning from vintage to modern wire like this profile. "
            "Bending feels easier than vintage narrow despite similar height, "
            "because the wider crown distributes string pressure. "
            "Very common on production instruments."
        ),
        wear_notes=(
            "Wide crown distributes wear — similar longevity to medium. "
            "However, low crown height limits leveling headroom as with vintage profiles."
        ),
        leveling_notes=(
            "Same headroom as vintage narrow (~3 passes) despite wider crown. "
            "The height, not the width, determines leveling headroom."
        ),
        install_notes="Standard installation.",
    ),

    # ── Tall family ───────────────────────────────────────────────────────────
    "tall_narrow": FretProfile(
        key="tall_narrow",
        label="Tall-Narrow (6105)",
        family="tall",
        crown_width_in=0.090,
        crown_height_in=0.055,
        tang_depth_in=0.055,
        tang_width_in=0.021,
        slot_width_in=0.023,
        slot_depth_in=0.060,
        dunlop="6105",
        playability=(
            "The player's fret. Narrow crown makes the string contact point precise — "
            "intonation is excellent. Bending effort is reduced because the string "
            "does not have to climb over a wide crown surface. "
            "Tall height means the string rides higher above the fretboard, "
            "allowing nut and saddle action to be reduced while maintaining "
            "the same string-to-crown clearance. "
            "Some players experience chord fatigue because the taller crown "
            "requires more conscious left-hand pressure control to avoid fretting sharp. "
            "Preferred by lead players; less favored for heavy chord work."
        ),
        wear_notes=(
            "Excellent leveling headroom. Narrow contact point concentrates "
            "wear in a smaller zone — grooves may form faster per unit area "
            "than jumbo despite similar height. "
            "In nickel-silver: 4-6 years before noticeable grooving."
        ),
        leveling_notes=(
            "~7 leveling passes possible — the best leveling profile. "
            "Tall crown accommodates repeated redressing better than any low profile."
        ),
        install_notes=(
            "Deeper tang (0.055\") requires adequate fretboard thickness. "
            "Verify fretboard thickness before ordering. "
            "Requires more seating force than vintage profiles. "
            "Prebend radius accuracy is more important at this height."
        ),
    ),

    "jumbo": FretProfile(
        key="jumbo",
        label="Jumbo",
        family="tall",
        crown_width_in=0.110,
        crown_height_in=0.055,
        tang_depth_in=0.055,
        tang_width_in=0.023,
        slot_width_in=0.025,
        slot_depth_in=0.060,
        dunlop="6100",
        playability=(
            "Maximum height and width. Very pronounced feel under the fingers. "
            "Bending is effortless but the wide crown requires precision fretting — "
            "pressing too hard pushes the note sharp. "
            "Favored in high-gain electric contexts. "
            "Not recommended for acoustic fingerstyle or acoustic rhythm guitar — "
            "the wide crown can widen the string contact point beyond compensation "
            "range, introducing intonation error across the fretboard."
        ),
        wear_notes=(
            "Maximum leveling headroom and wide crown distributes wear. "
            "Best wear characteristics of all nickel-silver profiles."
        ),
        leveling_notes=(
            "~7 leveling passes possible. Most service-friendly profile. "
            "Wider tang requires correct slot width — check with 0.025\" saw."
        ),
        install_notes=(
            "Wider tang (0.023\") needs 0.025\" slot — do not use 0.023\" saw. "
            "Verify slot saw width before installation."
        ),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FretboardCompatibility:
    """
    Compatibility check: fret profile vs fretboard thickness.

    Tang must fit within fretboard without breaking through.
    Minimum wood below tang = 0.040\" for structural integrity.
    """
    fretboard_thickness_in: float
    tang_depth_in: float
    wood_below_tang_in: float
    adequate: bool
    margin_in: float


@dataclass
class ActionAnalysis:
    """
    String height analysis: how crown height affects action setup.

    The fret crown height is additive to effective string height.
    Taller frets allow lower nut/saddle settings while maintaining
    the same string-to-crown clearance.
    """
    action_at_12th_in: float           # string height above fretboard at 12th
    crown_height_in: float
    clearance_above_crown_in: float    # string clearance above crown
    clearance_above_crown_mm: float
    action_reduction_possible_in: float  # vs vintage narrow (0.036\" baseline)
    notes: str


@dataclass
class FretWireSpec:
    """
    Complete fret wire specification for a given profile and material.
    """
    profile: FretProfile
    material: FretMaterial

    # Derived geometry
    crown_radius_in: float
    contact_width_in: float
    contact_width_thou: float        # thousandths of an inch

    # Leveling
    leveling_headroom_in: float
    leveling_headroom_mm: float
    leveling_passes: int

    # Slot specification
    required_slot_width_in: float
    required_slot_depth_in: float

    # Action
    action_analysis: Optional[ActionAnalysis]

    # Fretboard compatibility
    compatibility: Optional[FretboardCompatibility]

    # Warnings
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Core calculation
# ─────────────────────────────────────────────────────────────────────────────

def analyze_fret_wire(
    profile_key: str,
    material_key: str = "nickel_silver",
    fretboard_thickness_in: float = 0.240,
    action_at_12th_in: float = 0.070,
) -> FretWireSpec:
    """
    Complete fret wire analysis for a given profile and material combination.

    Args:
        profile_key:           Key from FRET_PROFILES dict
        material_key:          Key from FRET_MATERIALS dict
        fretboard_thickness_in: Fretboard thickness at the nut end (inches)
        action_at_12th_in:     String height above fretboard at 12th fret (inches)
                               Typical acoustic: 0.070-0.090\"
                               Typical electric:  0.050-0.070\"

    Returns:
        FretWireSpec with all geometry, compatibility, and advisory notes.
    """
    profile = FRET_PROFILES.get(profile_key)
    material = FRET_MATERIALS.get(material_key)

    if profile is None:
        raise ValueError(f"Unknown fret profile: {profile_key!r}. "
                         f"Available: {list(FRET_PROFILES.keys())}")
    if material is None:
        raise ValueError(f"Unknown fret material: {material_key!r}. "
                         f"Available: {list(FRET_MATERIALS.keys())}")

    warnings: List[str] = []
    notes: List[str] = []

    # ── Crown geometry ─────────────────────────────────────────────────────
    crown_radius = profile.crown_radius_in
    contact_width = profile.contact_width_in

    # ── Leveling headroom ──────────────────────────────────────────────────
    headroom = profile.leveling_headroom_in
    passes = profile.leveling_passes

    if passes <= 3:
        warnings.append(
            f"Low leveling headroom ({headroom:.3f}\" = ~{passes} passes). "
            f"Plan to refret rather than repeatedly dress. "
            f"Precision initial installation is critical for this profile."
        )

    # ── Slot specification ─────────────────────────────────────────────────
    slot_width = profile.slot_width_in
    slot_depth = profile.slot_depth_in

    # ── Fretboard compatibility ────────────────────────────────────────────
    wood_below = fretboard_thickness_in - profile.tang_depth_in
    compat_ok = wood_below >= MIN_WOOD_BELOW_TANG_IN

    compatibility = FretboardCompatibility(
        fretboard_thickness_in=fretboard_thickness_in,
        tang_depth_in=profile.tang_depth_in,
        wood_below_tang_in=round(wood_below, 3),
        adequate=compat_ok,
        margin_in=round(wood_below - MIN_WOOD_BELOW_TANG_IN, 3),
    )

    if not compat_ok:
        warnings.append(
            f"Fretboard too thin for this tang depth. "
            f"Only {wood_below:.3f}\" below tang (minimum {MIN_WOOD_BELOW_TANG_IN:.3f}\"). "
            f"Risk of fretboard splitting at tang tips. "
            f"Choose a shallower tang profile or use a thicker fretboard."
        )

    # ── Action analysis ────────────────────────────────────────────────────
    clearance = action_at_12th_in - profile.crown_height_in
    baseline_crown = 0.036   # vintage narrow baseline
    action_reduction = profile.crown_height_in - baseline_crown

    action_analysis = ActionAnalysis(
        action_at_12th_in=action_at_12th_in,
        crown_height_in=profile.crown_height_in,
        clearance_above_crown_in=round(clearance, 3),
        clearance_above_crown_mm=round(clearance * 25.4, 2),
        action_reduction_possible_in=round(action_reduction, 3),
        notes=(
            f"String clears crown by {clearance:.3f}\" ({clearance*25.4:.2f}mm). "
            + (
                f"This profile is {action_reduction:.3f}\" taller than vintage narrow — "
                f"nut and saddle action can be reduced by up to {action_reduction:.3f}\" "
                f"while maintaining equivalent playing clearance."
                if action_reduction > 0 else
                "Vintage-height profile — action set conventionally."
            )
        ),
    )

    if clearance < 0.010:
        warnings.append(
            f"String clearance above crown ({clearance:.3f}\") is very low. "
            f"Risk of string buzzing against adjacent frets during aggressive playing. "
            f"Lower the action or choose a shorter crown profile."
        )

    # ── Material-specific notes ────────────────────────────────────────────
    if material_key == "stainless_steel":
        warnings.append(
            "Stainless steel requires carbide/diamond tooling for all fret work. "
            "Standard fret files are destroyed on first contact. "
            "Work hardening during installation is significant — "
            "do not attempt without stainless-specific experience and tooling."
        )
        notes.append(
            f"Stainless hardness (HV {material.hardness_HV}) is "
            f"{material.relative_hardness:.1f}× nickel-silver. "
            f"Expected longevity: {material.wear_multiplier:.0f}× before grooving. "
            f"Effectively permanent with normal playing."
        )
    elif material_key == "evo_gold":
        notes.append(
            f"EVO Gold hardness (HV {material.hardness_HV}) is "
            f"{material.relative_hardness:.1f}× nickel-silver. "
            f"Expected longevity: {material.wear_multiplier:.0f}× before grooving. "
            f"Diamond or carbide files recommended for leveling."
        )

    return FretWireSpec(
        profile=profile,
        material=material,
        crown_radius_in=round(crown_radius, 4),
        contact_width_in=round(contact_width, 4),
        contact_width_thou=round(contact_width * 1000, 1),
        leveling_headroom_in=round(headroom, 3),
        leveling_headroom_mm=round(headroom * 25.4, 2),
        leveling_passes=passes,
        required_slot_width_in=slot_width,
        required_slot_depth_in=slot_depth,
        action_analysis=action_analysis,
        compatibility=compatibility,
        warnings=warnings,
        notes=notes,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Comparison utility
# ─────────────────────────────────────────────────────────────────────────────

def compare_profiles(
    profile_keys: Optional[List[str]] = None,
    material_key: str = "nickel_silver",
    fretboard_thickness_in: float = 0.240,
    action_at_12th_in: float = 0.070,
) -> List[FretWireSpec]:
    """
    Compare multiple fret profiles side by side.

    Args:
        profile_keys:  List of profile keys to compare. Defaults to all profiles.
        material_key:  Material for all profiles in comparison.
        fretboard_thickness_in: Fretboard thickness for compatibility check.
        action_at_12th_in:     Action height for clearance analysis.

    Returns:
        List of FretWireSpec, one per profile.
    """
    keys = profile_keys or list(FRET_PROFILES.keys())
    return [
        analyze_fret_wire(k, material_key, fretboard_thickness_in, action_at_12th_in)
        for k in keys
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Preset factory
# ─────────────────────────────────────────────────────────────────────────────

def fret_preset(instrument_style: str) -> FretWireSpec:
    """
    Return a recommended fret wire spec for a standard instrument style.

    Styles:
        "acoustic_fingerstyle"  — medium, nickel-silver
        "acoustic_flatpick"     — medium or tall-narrow, nickel-silver
        "electric_vintage"      — vintage medium, nickel-silver
        "electric_modern"       — tall-narrow, nickel-silver or EVO
        "electric_heavy"        — jumbo, nickel-silver
        "acoustic_durable"      — medium, EVO gold (best acoustic durability)
        "electric_permanent"    — tall-narrow, stainless (if tooling available)
    """
    presets = {
        "acoustic_fingerstyle": ("medium", "nickel_silver", 0.240, 0.080),
        "acoustic_flatpick":    ("tall_narrow", "nickel_silver", 0.240, 0.075),
        "electric_vintage":     ("vintage_medium", "nickel_silver", 0.200, 0.065),
        "electric_modern":      ("tall_narrow", "nickel_silver", 0.200, 0.060),
        "electric_heavy":       ("jumbo", "nickel_silver", 0.200, 0.055),
        "acoustic_durable":     ("medium", "evo_gold", 0.240, 0.080),
        "electric_permanent":   ("tall_narrow", "stainless_steel", 0.200, 0.060),
    }
    if instrument_style not in presets:
        raise ValueError(
            f"Unknown preset: {instrument_style!r}. "
            f"Available: {list(presets.keys())}"
        )
    profile_key, material_key, fb_thick, action = presets[instrument_style]
    return analyze_fret_wire(profile_key, material_key, fb_thick, action)
