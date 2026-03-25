# services/api/app/calculators/neck_block_calc.py
"""
Neck Block and Tail Block Sizing Calculator — GEOMETRY-005

Structural sizing of neck and tail blocks from first principles:
string tension → joint loads → required glue area → block dimensions.

Physical model summary
======================

The neck joint carries two load types simultaneously:

1. SHEAR (primary, ~419 N for light gauge):
   String tension acts approximately parallel to the neck axis. At the
   neck joint face this is a shear load. Required glue area:

       A_min = T × SF / (τ_wood × η_glue)

   Actual block face areas (5000–9000 mm²) are 25–40× the minimum.
   The joint does NOT fail by face-glue shear under normal loads.

2. BENDING MOMENT (determines block height):
   Strings are elevated above the neck joint. The resulting moment
   attempts to rotate the neck forward. This moment is resisted by a
   compression/tension couple: compression at the fingerboard side of
   the neck block, tension at the back side. The couple force is:

       F_couple = M / d_block = (T × h_neck) / side_depth

   For OM with light gauge: 27268 N⋅mm / 95mm = 287 N = 29 kgf
   This is within normal structural limits but drives the block HEIGHT
   requirement — a taller block (deeper side) provides a longer moment
   arm and reduces the couple force.

3. JOINT TYPE determines effective shear area (critical distinction):
   The block FACE area is not the shear area for dovetail or tenon joints.
   - Dovetail: shear on angled cheeks, not block face
   - Bolt-on: friction from bolt preload + small glue area
   - Mortise-tenon: glue area on tenon faces
   - Spanish heel: integral construction, no glue joint

Tail block
==========
The tail block is NOT a primary structural member. String tension acts
forward (toward nut) — the tail block is in the opposite direction and
carries essentially no string load. Its dimensions are geometric:

    height = side_depth_at_tail (from SIDE_PROFILE)
    width  = lower_bout × 0.16  (conventional)
    depth  = 22–28mm (end pin through-hole + margin)

The end pin carries strap + guitar weight (~50 N = 5 kgf), well within
limits for any wood at any reasonable block depth.

Sources:
    - D'Addario string tension data (tension charts, .012-.053 light gauge)
    - USDA Wood Handbook Table 4-3 (shear strength parallel to grain)
    - Gore & Gilet, "Contemporary Acoustic Guitar Design and Build" Vol.1
    - NDS (National Design Specification for Wood Construction) SF=4.0
    - Siminoff, "The Luthier's Handbook" (block dimensions)
    - martin_d28_1937.py SIDE_PROFILE_WITH_KERFING_MM for reference depths
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Literal, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Material shear strengths (MPa, parallel to grain)
# Source: USDA Wood Handbook, Table 4-3, 12% MC
# ─────────────────────────────────────────────────────────────────────────────

WOOD_SHEAR_MPa: Dict[str, float] = {
    "mahogany":  9.5,   # Honduran Mahogany — standard neck block material
    "maple":    10.0,   # Hard Maple — stiffer, stronger
    "walnut":    9.5,   # Black Walnut
    "spruce":    5.5,   # Sitka Spruce — sometimes used for lightweight builds
    "basswood":  5.5,   # American Basswood
    "cedar":     5.0,   # Western Red Cedar
    "cherry":    8.9,   # Black Cherry
    "ash":      10.2,   # White Ash
}

# Glue joint efficiency factor: actual joints have stress concentrations
# and imperfect wood-to-wood contact. 0.85 is conservative.
GLUE_EFFICIENCY: float = 0.85

# Safety factor for primary wood structural joints
# NDS recommendation: 4.0; Gore & Gilet instrument practice: 3.0
# We use 4.0 for conservatism
SAFETY_FACTOR: float = 4.0

# Neck block width as fraction of upper bout width (empirical from reference instruments)
# Martin OM: 84/290=0.290, D-28: 90/292=0.308, 000: 80/279=0.287
NECK_BLOCK_WIDTH_FRACTION: float = 0.29

# Tail block width as fraction of lower bout width
# Martin OM: 64/381=0.168, D-28: 70/397=0.176, 000: 60/368=0.163
TAIL_BLOCK_WIDTH_FRACTION: float = 0.16

# Minimum tail block depth (through end pin hole + structural margin)
# End pin taper reamer: 9.5mm diameter at surface
# Minimum wood around pin: ~8mm
# → 9.5/2 + 8 + margin = minimum ~22mm
TAIL_BLOCK_DEPTH_MIN_MM: float = 22.0

# String tensions (N) at concert pitch — D'Addario data
STRING_TENSIONS_N: Dict[str, Dict[str, float]] = {
    "light_012": {
        "E1": 71.7, "B2": 49.0, "G3": 63.1, "D4": 72.6, "A5": 78.7, "E6": 84.4
    },
    "medium_013": {
        "E1": 79.1, "B2": 55.6, "G3": 71.2, "D4": 80.5, "A5": 88.5, "E6": 93.8
    },
    "light_medium_0125": {
        "E1": 75.4, "B2": 52.3, "G3": 67.1, "D4": 76.5, "A5": 83.6, "E6": 89.1
    },
    "heavy_014": {
        "E1": 89.0, "B2": 63.6, "G3": 81.1, "D4": 89.3, "A5": 96.8, "E6": 103.4
    },
    "nylon_normal": {
        "E1": 71.0, "B2": 49.0, "G3": 55.0, "D4": 63.0, "A5": 74.0, "E6": 77.0
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Joint type geometry
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class JointType:
    """
    Neck joint geometry and effective shear area parameters.

    effective_area_fraction: fraction of block face area that actively
        carries shear. The block FACE area is not the shear area for
        dovetail or tenon joints — only the joint contact surfaces count.
    """
    key: str
    label: str
    effective_area_fraction: float  # fraction of block face area
    depth_mm_typical: float         # typical joint depth along body axis
    notes: str


JOINT_TYPES: Dict[str, JointType] = {
    "dovetail": JointType(
        key="dovetail", label="Dovetail",
        effective_area_fraction=0.28,   # 2×cheeks / total block face
        depth_mm_typical=75.0,
        notes=(
            "Shear carried by angled cheek surfaces only. "
            "Two cheeks at ~30° taper: effective area = 2×(50mm×20mm) = 2000mm² "
            "for a standard Martin-style dovetail in a ~7500mm² block face. "
            "Requires precise fitting; gap-fit loses shear capacity rapidly."
        ),
    ),
    "bolt_on": JointType(
        key="bolt_on", label="Bolt-On",
        effective_area_fraction=0.35,
        depth_mm_typical=70.0,
        notes=(
            "Glue area on neck heel face + bolt clamping friction. "
            "Two bolts (M6 or 10-32) provide ~150N friction each at typical torque. "
            "Effective shear area = heel glue area + bolt friction equivalent. "
            "Most bolt-on joints rely primarily on bolt preload, not glue shear."
        ),
    ),
    "mortise_tenon": JointType(
        key="mortise_tenon", label="Mortise & Tenon (NT-style)",
        effective_area_fraction=0.65,
        depth_mm_typical=80.0,
        notes=(
            "Large glue area on all four tenon faces. "
            "Taylor NT joint: tenon ≈ 100×50mm face gives ~5000mm² contact. "
            "Bolts provide additional compression. "
            "Highest effective shear area of removable joint types."
        ),
    ),
    "spanish_heel": JointType(
        key="spanish_heel", label="Spanish Heel (integral)",
        effective_area_fraction=1.0,   # integral — no discrete shear plane
        depth_mm_typical=0.0,          # not applicable
        notes=(
            "Integral construction — sides slot into the heel block. "
            "No discrete glue joint at neck/body interface. "
            "Load transfers through continuous wood structure. "
            "Structurally superior; not removable without significant surgery."
        ),
    ),
    "butt_glue": JointType(
        key="butt_glue", label="Butt Joint (glued)",
        effective_area_fraction=1.0,   # full face area is the shear plane
        depth_mm_typical=60.0,
        notes=(
            "Simple glued butt joint: full block face is the shear plane. "
            "Adequate for the computed loads (actual area far exceeds minimum). "
            "Common in classical and some folk instruments."
        ),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ShearAnalysis:
    """
    Shear load analysis at the neck joint.

    The joint carries the full axial string tension as shear,
    plus a bending moment from the string height above the joint.
    """
    total_tension_N: float
    shear_force_N: float         # ≈ total tension (neck angle small)
    bending_moment_Nmm: float    # T × neck_height_above_joint
    couple_force_N: float        # M / side_depth (compression/tension couple)
    neck_height_mm: float        # neck + fretboard height above body top
    side_depth_mm: float


@dataclass
class GlueAreaAnalysis:
    """
    Glue area sizing from first principles.

    min_face_area_mm2 is the minimum block FACE area required if the
    entire face were the shear plane (worst case, e.g. butt joint).
    Actual required area depends on joint type via effective_area_fraction.
    """
    material: str
    shear_strength_MPa: float
    effective_shear_MPa: float       # shear_strength × glue_efficiency
    safety_factor: float

    min_face_area_mm2: float         # = shear_force × SF / τ_eff
    actual_face_area_mm2: float
    area_safety_multiple: float      # actual / required

    joint_type: str
    effective_joint_area_mm2: float  # face area × joint fraction
    joint_area_safety_multiple: float  # joint area / min_face_area

    status: str                      # "adequate" | "marginal" | "inadequate"
    notes: str


@dataclass
class NeckBlockSpec:
    """
    Complete neck block geometry specification.

    Dimensions:
        width:  Y axis (treble-to-bass), determines string spread clearance
        height: Z axis (= side depth at neck end, flush with top/back edges)
        depth:  X axis (neck-to-tail), must accommodate joint geometry
    """
    # Dimensions
    width_mm: float         # Y axis — matched to upper bout width
    height_mm: float        # Z axis — equals side depth at neck
    depth_mm: float         # X axis — along body centerline

    # Areas
    face_area_mm2: float    # width × depth (the glue/joint face)
    side_area_mm2: float    # height × depth (glued to each side)

    # Joint
    joint_type: str
    joint_depth_mm: float   # depth required by joint geometry

    # Scaling source
    upper_bout_width_mm: float
    side_depth_at_neck_mm: float

    # Structural analysis
    shear_analysis: ShearAnalysis
    glue_analysis: GlueAreaAnalysis

    # Construction notes
    grain_direction: str = "vertical"  # grain runs neck-to-tail in the block
    material: str = "mahogany"
    construction_note: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass
class TailBlockSpec:
    """
    Complete tail block geometry specification.

    Tail block is geometry-driven, not structurally critical.
    Width and height come from body geometry. Depth is the minimum
    needed for the end pin hole plus structural margin.
    """
    # Dimensions
    width_mm: float         # Y axis — matched to lower bout width
    height_mm: float        # Z axis — equals side depth at tail
    depth_mm: float         # X axis — end pin depth + margin

    # Areas
    face_area_mm2: float    # width × depth

    # End pin
    end_pin_hole_diameter_mm: float  # standard: 9.5mm (for 3° taper strap pin)
    min_wood_around_pin_mm: float    # minimum wood thickness around pin

    # Loads
    strap_load_N: float             # guitar weight + strap tension
    bearing_stress_MPa: float       # stress at pin bearing surface
    bearing_ok: bool

    # Scaling source
    lower_bout_width_mm: float
    side_depth_at_tail_mm: float

    material: str = "mahogany"
    construction_note: str = ""


@dataclass
class BlockSpec:
    """Combined neck and tail block specification."""
    neck: NeckBlockSpec
    tail: TailBlockSpec
    string_gauge: str
    total_tension_N: float
    instrument_style: str


# ─────────────────────────────────────────────────────────────────────────────
# Core calculation functions
# ─────────────────────────────────────────────────────────────────────────────

def compute_total_tension(gauge_key: str = "light_012") -> float:
    """Return total string tension (N) for a gauge set."""
    tensions = STRING_TENSIONS_N.get(gauge_key, STRING_TENSIONS_N["light_012"])
    return sum(tensions.values())


def compute_shear_analysis(
    total_tension_N: float,
    neck_height_above_joint_mm: float,
    side_depth_mm: float,
    neck_angle_deg: float = 1.5,
) -> ShearAnalysis:
    """
    Compute shear force and bending moment at neck joint.

    The neck angle is typically 1–2° for acoustic guitars with neck
    resets, and contributes negligibly to the shear component (cos(2°)=0.9994).
    The bending moment from string height is the more significant effect.

    Args:
        total_tension_N:             Total string tension from all strings
        neck_height_above_joint_mm:  Height of strings above the neck joint face.
                                     Approximately: neck thickness + fretboard +
                                     string height above fretboard ≈ 60–70mm
        side_depth_mm:               Side depth at neck end (moment arm for couple)
        neck_angle_deg:              Neck set angle (default 1.5°)

    Returns:
        ShearAnalysis with forces and moment
    """
    shear_N = total_tension_N * math.cos(math.radians(neck_angle_deg))
    moment_Nmm = total_tension_N * neck_height_above_joint_mm
    couple_N = moment_Nmm / side_depth_mm if side_depth_mm > 0 else 0

    return ShearAnalysis(
        total_tension_N=round(total_tension_N, 1),
        shear_force_N=round(shear_N, 1),
        bending_moment_Nmm=round(moment_Nmm, 0),
        couple_force_N=round(couple_N, 1),
        neck_height_mm=neck_height_above_joint_mm,
        side_depth_mm=side_depth_mm,
    )


def compute_glue_area(
    shear_N: float,
    actual_face_area_mm2: float,
    material: str = "mahogany",
    joint_type_key: str = "dovetail",
    safety_factor: float = SAFETY_FACTOR,
) -> GlueAreaAnalysis:
    """
    Compute glue area adequacy for the neck joint.

    Args:
        shear_N:              Shear force at joint (N) from shear_analysis
        actual_face_area_mm2: Block face area (width × depth) (mm²)
        material:             Block wood species from WOOD_SHEAR_MPa
        joint_type_key:       Joint type from JOINT_TYPES
        safety_factor:        Design safety factor (default 4.0)

    Returns:
        GlueAreaAnalysis with minimum required and actual areas
    """
    tau = WOOD_SHEAR_MPa.get(material, WOOD_SHEAR_MPa["mahogany"])
    tau_eff = tau * GLUE_EFFICIENCY      # MPa
    tau_eff_Pa = tau_eff * 1e6           # Pa

    # Minimum face area assuming full face is shear plane (worst case)
    A_min = (shear_N * safety_factor) / tau_eff_Pa * 1e6  # mm²

    area_multiple = actual_face_area_mm2 / A_min if A_min > 0 else float("inf")

    jt = JOINT_TYPES.get(joint_type_key, JOINT_TYPES["butt_glue"])
    effective_joint_area = actual_face_area_mm2 * jt.effective_area_fraction
    joint_multiple = effective_joint_area / A_min if A_min > 0 else float("inf")

    # Status: joint multiple is what matters
    if joint_multiple >= 4.0:
        status = "adequate"
        notes = (
            f"Joint area ({effective_joint_area:.0f}mm²) is {joint_multiple:.0f}× "
            f"the structural minimum ({A_min:.0f}mm²). "
            f"Well within limits for {material} with {jt.label} joint."
        )
    elif joint_multiple >= 2.0:
        status = "marginal"
        notes = (
            f"Joint area ({effective_joint_area:.0f}mm²) is {joint_multiple:.1f}× "
            f"structural minimum. Acceptable but consider improving joint fit."
        )
    else:
        status = "inadequate"
        notes = (
            f"Joint area ({effective_joint_area:.0f}mm²) is only {joint_multiple:.1f}× "
            f"minimum ({A_min:.0f}mm²). Increase block dimensions or change joint type."
        )

    return GlueAreaAnalysis(
        material=material,
        shear_strength_MPa=tau,
        effective_shear_MPa=round(tau_eff, 2),
        safety_factor=safety_factor,
        min_face_area_mm2=round(A_min, 0),
        actual_face_area_mm2=round(actual_face_area_mm2, 0),
        area_safety_multiple=round(area_multiple, 1),
        joint_type=jt.label,
        effective_joint_area_mm2=round(effective_joint_area, 0),
        joint_area_safety_multiple=round(joint_multiple, 1),
        status=status,
        notes=notes,
    )


def compute_neck_block(
    upper_bout_width_mm: float,
    side_depth_at_neck_mm: float,
    joint_type: str = "dovetail",
    material: str = "mahogany",
    gauge_key: str = "light_012",
    neck_height_above_joint_mm: float = 65.0,
    neck_angle_deg: float = 1.5,
    safety_factor: float = SAFETY_FACTOR,
    override_width_mm: Optional[float] = None,
    override_depth_mm: Optional[float] = None,
) -> NeckBlockSpec:
    """
    Compute neck block dimensions and structural adequacy.

    Dimensions are determined first by geometry (conventional proportions)
    then verified against structural requirements (almost always exceeded).

    Args:
        upper_bout_width_mm:        Upper bout width for block width scaling
        side_depth_at_neck_mm:      Side depth at neck end (sets block height)
        joint_type:                 Joint type key from JOINT_TYPES
        material:                   Block wood species
        gauge_key:                  String gauge set key
        neck_height_above_joint_mm: String height above joint pivot (mm)
        neck_angle_deg:             Neck set angle (degrees)
        safety_factor:              Structural safety factor
        override_width_mm:          Override computed width (mm)
        override_depth_mm:          Override computed depth (mm)

    Returns:
        NeckBlockSpec with geometry and structural analysis
    """
    warnings = []
    jt = JOINT_TYPES.get(joint_type, JOINT_TYPES["dovetail"])

    # Geometry
    width = override_width_mm if override_width_mm else \
        round(upper_bout_width_mm * NECK_BLOCK_WIDTH_FRACTION, 0)
    height = side_depth_at_neck_mm

    # Depth must accommodate the joint geometry
    joint_depth = jt.depth_mm_typical
    depth = override_depth_mm if override_depth_mm else \
        max(joint_depth + 5.0, 65.0)  # joint depth + 5mm margin, minimum 65mm

    face_area = width * depth
    side_area = height * depth

    # Structural analysis
    T_total = compute_total_tension(gauge_key)
    shear = compute_shear_analysis(T_total, neck_height_above_joint_mm,
                                   height, neck_angle_deg)
    glue = compute_glue_area(shear.shear_force_N, face_area, material,
                              joint_type, safety_factor)

    # Warnings
    if height < 85.0:
        warnings.append(
            f"Side depth at neck ({height:.0f}mm) is shallow. "
            "Bending moment couple force increases with shallower sides. "
            f"Couple force = {shear.couple_force_N:.0f}N."
        )
    if width < 70.0:
        warnings.append(
            f"Neck block width ({width:.0f}mm) is narrow. "
            "Check clearance for neck pocket routing and kerfing."
        )
    if glue.status != "adequate":
        warnings.append(f"Glue area check: {glue.status}. {glue.notes}")

    # Construction note
    note = (
        f"{jt.label} joint: effective shear area {glue.effective_joint_area_mm2:.0f}mm² "
        f"({glue.joint_area_safety_multiple:.0f}× structural minimum). "
        f"Bending couple: {shear.couple_force_N:.0f}N at {height:.0f}mm side depth. "
        f"Block: {width:.0f}×{depth:.0f}×{height:.0f}mm (W×D×H)."
    )

    return NeckBlockSpec(
        width_mm=round(width, 1),
        height_mm=round(height, 1),
        depth_mm=round(depth, 1),
        face_area_mm2=round(face_area, 0),
        side_area_mm2=round(side_area, 0),
        joint_type=joint_type,
        joint_depth_mm=round(joint_depth, 1),
        upper_bout_width_mm=upper_bout_width_mm,
        side_depth_at_neck_mm=side_depth_at_neck_mm,
        shear_analysis=shear,
        glue_analysis=glue,
        grain_direction="parallel_to_neck_axis",
        material=material,
        construction_note=note,
        warnings=warnings,
    )


def compute_tail_block(
    lower_bout_width_mm: float,
    side_depth_at_tail_mm: float,
    material: str = "mahogany",
    end_pin_diameter_mm: float = 9.5,
    strap_load_N: float = 50.0,
    override_width_mm: Optional[float] = None,
    override_depth_mm: Optional[float] = None,
) -> TailBlockSpec:
    """
    Compute tail block dimensions.

    Tail block is geometry-driven. The end pin carries ~50N (guitar + strap
    weight in worst case), well within limits. Dimensions come from body
    proportions with minimum depth set by end pin hole geometry.

    Args:
        lower_bout_width_mm:    Lower bout width for block width scaling
        side_depth_at_tail_mm:  Side depth at tail end (sets block height)
        material:               Block wood species
        end_pin_diameter_mm:    Diameter of end pin hole at surface (9.5mm standard)
        strap_load_N:           End pin design load (N)
        override_width_mm:      Override computed width
        override_depth_mm:      Override computed depth

    Returns:
        TailBlockSpec
    """
    width = override_width_mm if override_width_mm else \
        round(lower_bout_width_mm * TAIL_BLOCK_WIDTH_FRACTION, 0)
    height = side_depth_at_tail_mm

    # Minimum depth: end pin radius + wood around pin + margin
    pin_radius = end_pin_diameter_mm / 2
    min_wood = 8.0  # mm minimum wood around pin hole
    min_depth = pin_radius + min_wood + 4.0  # + 4mm margin
    depth = override_depth_mm if override_depth_mm else \
        max(min_depth, TAIL_BLOCK_DEPTH_MIN_MM)

    face_area = width * depth

    # End pin bearing check
    # Bearing area = pin circumference × depth of engagement
    # Conservative: bearing on half of pin over the block depth
    bearing_area_mm2 = math.pi * end_pin_diameter_mm / 2 * depth * 0.5
    bearing_MPa = strap_load_N / bearing_area_mm2 if bearing_area_mm2 > 0 else 0
    # Acceptable bearing stress for wood across grain: ~3-5 MPa
    bearing_ok = bearing_MPa < 3.0

    note = (
        f"Geometry-driven block: {width:.0f}×{depth:.0f}×{height:.0f}mm (W×D×H). "
        f"End pin bearing: {bearing_MPa:.3f}MPa (limit ~3MPa) — "
        f"{'OK' if bearing_ok else 'CHECK'}. "
        f"No string tension load — tail block is compressive under strap only."
    )

    return TailBlockSpec(
        width_mm=round(width, 1),
        height_mm=round(height, 1),
        depth_mm=round(depth, 1),
        face_area_mm2=round(face_area, 0),
        end_pin_hole_diameter_mm=end_pin_diameter_mm,
        min_wood_around_pin_mm=min_wood,
        strap_load_N=strap_load_N,
        bearing_stress_MPa=round(bearing_MPa, 4),
        bearing_ok=bearing_ok,
        lower_bout_width_mm=lower_bout_width_mm,
        side_depth_at_tail_mm=side_depth_at_tail_mm,
        material=material,
        construction_note=note,
    )


# ─────────────────────────────────────────────────────────────────────────────
# High-level analysis
# ─────────────────────────────────────────────────────────────────────────────

def analyze_blocks(
    upper_bout_width_mm: float,
    lower_bout_width_mm: float,
    side_depth_at_neck_mm: float,
    side_depth_at_tail_mm: float,
    joint_type: str = "dovetail",
    material: str = "mahogany",
    gauge_key: str = "light_012",
    instrument_style: str = "acoustic_6_string",
    neck_angle_deg: float = 1.5,
) -> BlockSpec:
    """
    Compute complete neck and tail block specifications.

    Args:
        upper_bout_width_mm:      Upper bout width (mm)
        lower_bout_width_mm:      Lower bout width (mm)
        side_depth_at_neck_mm:    Side depth at neck end (mm)
        side_depth_at_tail_mm:    Side depth at tail end (mm)
        joint_type:               Neck joint type
        material:                 Block wood species
        gauge_key:                String gauge set
        instrument_style:         Instrument description (for reporting)
        neck_angle_deg:           Neck set angle (degrees)

    Returns:
        BlockSpec with both blocks and all structural analysis
    """
    T_total = compute_total_tension(gauge_key)

    neck = compute_neck_block(
        upper_bout_width_mm, side_depth_at_neck_mm,
        joint_type=joint_type, material=material, gauge_key=gauge_key,
        neck_angle_deg=neck_angle_deg,
    )
    tail = compute_tail_block(
        lower_bout_width_mm, side_depth_at_tail_mm,
        material=material,
    )

    return BlockSpec(
        neck=neck,
        tail=tail,
        string_gauge=gauge_key,
        total_tension_N=round(T_total, 1),
        instrument_style=instrument_style,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Standard presets
# ─────────────────────────────────────────────────────────────────────────────

INSTRUMENT_PRESETS: Dict[str, Dict] = {
    "martin_om": dict(
        upper_bout_width_mm=290.0,
        lower_bout_width_mm=381.0,
        side_depth_at_neck_mm=95.3,   # 3.75" raw + kerfing
        side_depth_at_tail_mm=120.0,
        joint_type="dovetail",
        gauge_key="light_012",
        instrument_style="Martin OM",
    ),
    "martin_d28": dict(
        upper_bout_width_mm=292.1,    # 11.5"
        lower_bout_width_mm=396.9,    # 15.625"
        side_depth_at_neck_mm=101.6,  # 4.0" with kerfing
        side_depth_at_tail_mm=126.2,  # 4.97"
        joint_type="dovetail",
        gauge_key="medium_013",
        instrument_style="Martin D-28",
    ),
    "martin_000": dict(
        upper_bout_width_mm=279.0,
        lower_bout_width_mm=368.0,
        side_depth_at_neck_mm=88.9,
        side_depth_at_tail_mm=112.0,
        joint_type="dovetail",
        gauge_key="light_012",
        instrument_style="Martin 000",
    ),
    "taylor_nt": dict(
        upper_bout_width_mm=290.0,
        lower_bout_width_mm=381.0,
        side_depth_at_neck_mm=95.3,
        side_depth_at_tail_mm=120.0,
        joint_type="mortise_tenon",
        gauge_key="light_012",
        instrument_style="Taylor NT-style",
    ),
    "classical": dict(
        upper_bout_width_mm=279.0,
        lower_bout_width_mm=370.0,
        side_depth_at_neck_mm=92.0,
        side_depth_at_tail_mm=96.0,
        joint_type="spanish_heel",
        gauge_key="nylon_normal",
        instrument_style="Classical",
    ),
}


def block_preset(style: str) -> BlockSpec:
    """
    Return block spec for a standard instrument style.

    Styles: "martin_om" | "martin_d28" | "martin_000" | "taylor_nt" | "classical"
    """
    if style not in INSTRUMENT_PRESETS:
        raise ValueError(
            f"Unknown preset: {style!r}. Available: {list(INSTRUMENT_PRESETS.keys())}"
        )
    return analyze_blocks(**INSTRUMENT_PRESETS[style])
