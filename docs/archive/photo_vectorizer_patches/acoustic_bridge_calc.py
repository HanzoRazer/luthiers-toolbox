# services/api/app/calculators/acoustic_bridge_calc.py
"""
Acoustic Bridge Geometry Calculator — GEOMETRY-004

Complete bridge geometry for pin-style acoustic guitar bridges.
Covers the physical bridge body that bridge_break_angle.py does not:

    bridge_break_angle.py  →  saddle projection & string angle over crown
    THIS MODULE            →  saddle slot location, saddle radius, string
                              spacing at saddle vs nut, bridge pin holes,
                              bridge belly profile, bridge footprint

Physical conventions (all dimensions in mm):
    - X axis: neck-to-tail (positive toward bridge)
    - Y axis: treble-to-bass (positive toward bass E string)
    - Z axis: into the top (positive downward into body)
    - Origin: saddle slot center, treble-side end

Bridge anatomy (X cross-section, looking from treble side):
    ┌───────────────────────────────────────────────────────┐
    │ ← forward wing → │ ← belly → │ ← saddle → │ ← back wing → │
    └──pin holes center─┴──ramp────┴──slot──────┴───────────────┘
         x = 0          x ≈ +9mm    x ≈ +10.5mm

Connections to existing calculators:
    - bridge_break_angle.py uses:  saddle_projection_mm, pin_to_saddle_center_mm,
                                   slot_offset_mm (which depends on belly height)
    - neck_angle_calc.py uses:     bridge_height_mm (base + projection)
    - plate_design/: bridge_plate_dimensions connects to plate modal analysis

References:
    - Gore & Gilet, Vol.1 Ch.5 (bridge geometry, string spacing)
    - Siminoff, "The Luthier's Handbook" (bridge dimensions)
    - Martin standard bridges (OM, D, 000) — measured reference instruments
    - Fretboard radius conventions: USACG, Warmoth, LMI specifications
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Standard fretboard radius values (inches → mm)
# Used for saddle crown matching
# ─────────────────────────────────────────────────────────────────────────────

FRETBOARD_RADII_MM: Dict[str, float] = {
    "7.25_vintage":   184.15,   # Vintage Fender, 1950s–1980s
    "9.5_modern":     241.30,   # Modern Fender
    "10_standard":    254.00,   # Martin, Taylor, many standard acoustics
    "12_medium":      304.80,   # Gibson, Collings, many modern acoustics
    "16_flat":        406.40,   # Very flat; archtop, some classicals
    "flat":           float("inf"),  # Classical / nylon string
}

# Standard saddle blank dimensions (bone/synthetic)
SADDLE_BLANK_WIDTH_MM: Dict[str, float] = {
    "narrow":    2.4,
    "standard":  3.0,
    "wide":      3.2,
    "classical": 2.5,
}

# Pin hole geometry
PIN_HOLE_DIAMETER_MM = 5.5   # Standard bridge pin taper (accepts 6° taper pins)
PIN_HOLE_REAMER_ANGLE_DEG = 3.0   # half-angle of bridge pin taper
PIN_HOLE_DEPTH_MM = 22.0     # Through bridge (10mm) + bridge plate (4mm) + into top (8mm)

# Minimum saddle seating depth
MIN_SADDLE_SEAT_DEPTH_MM = 3.0   # Saddle must sit at least 3mm in slot


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StringSpacingResult:
    """
    String spacing at nut vs saddle — these are different dimensions.

    Nut spacing is narrower to suit the left hand playing position.
    Saddle spacing is wider to match the body's string spread at the bridge.
    The strings diverge linearly from nut to saddle.

    Spacing conventions (all center-to-center):
        e_to_e:   distance from high-E string center to low-E string center
        per_string: uniform spacing between adjacent strings (e_to_e / (n-1))
        offsets:  list of center positions relative to centerline (treble-negative)
    """
    # Nut
    nut_e_to_e_mm: float
    nut_per_string_mm: float
    nut_string_offsets_mm: List[float]   # treble = negative

    # Saddle
    saddle_e_to_e_mm: float
    saddle_per_string_mm: float
    saddle_string_offsets_mm: List[float]

    # Spread geometry
    spread_increase_mm: float    # saddle E-to-e minus nut E-to-e
    string_count: int
    taper_angle_deg: float       # half-angle of string spread from centerline


@dataclass
class SaddleSlotSpec:
    """
    Complete saddle slot geometry relative to the bridge body.

    The saddle slot is routed into the bridge AFTER the bridge is glued.
    Its location relative to bridge edges is critical: too close to the
    back edge leaves insufficient glue surface behind the saddle.

    Slot slant angle: the slot is cut at a slight angle (typically 2-4°)
    so that wound strings (which need more compensation) have their
    saddle contact point farther back than plain strings. The slot
    angle equals the saddle slant angle derived from per-string compensation.
    """
    # Slot dimensions
    width_mm: float         # matches saddle blank width
    depth_mm: float         # saddle blank height minus projection
    length_mm: float        # full saddle length (E-to-e + overhang)
    overhang_per_side_mm: float   # saddle extends beyond outer strings

    # Slot location on bridge body
    from_back_edge_mm: float      # distance from back of bridge to rear slot wall
    from_front_edge_mm: float     # distance from front (pin side) to front slot wall
    centerline_from_back_mm: float  # slot centerline from back edge

    # Slot angle (slant)
    slant_angle_deg: float   # positive = bass end is farther back
    slant_offset_mm: float   # lateral offset: how much the slot deviates end-to-end

    # Seating check
    seat_depth_mm: float     # saddle blank height minus projection = seated depth
    seat_adequate: bool      # seat_depth >= MIN_SADDLE_SEAT_DEPTH_MM


@dataclass
class SaddleCrownSpec:
    """
    Saddle crown radius profile matching fretboard radius.

    The saddle crown must have the same radius as the fretboard so that
    string action is consistent across all strings. The crown is a
    cylindrical arc centered on the string centerline.

    Crown height: the amount the crown rises from the flat saddle top.
    At the edge strings (height = 0), the saddle is at its full height.
    At the center, the saddle is lower by crown_height_mm.

    Note: saddle action is adjusted PER STRING using this crown profile.
    The bone saddle is shaped to the crown radius on top, then individual
    string notches are cut to achieve the target action for each string.
    """
    fretboard_radius_mm: float
    saddle_e_to_e_mm: float         # must match string spread at saddle

    # Crown geometry
    crown_height_mm: float          # rise from edge to center of saddle arc
    height_at_positions_mm: List[float]   # per-string height from crown peak
    action_correction_per_string: List[float]  # action adj needed to compensate crown


@dataclass
class BridgePinSpec:
    """
    Bridge pin hole placement.

    Pin holes are drilled through the bridge, bridge plate, and into the top.
    They are positioned behind (forward of, toward nut) the saddle slot.
    The slant of the pin row matches the saddle slant angle.
    """
    count: int
    e_to_e_mm: float              # same as saddle E-to-e
    pin_to_saddle_center_mm: float   # horizontal distance from pin center to saddle centerline
    pin_offsets_mm: List[float]   # per-pin Y positions from centerline (same as saddle)
    hole_diameter_mm: float
    hole_depth_mm: float
    reamer_angle_deg: float       # half-angle of taper
    string_exit_to_saddle_mm: float  # effective distance after belly (feeds break angle calc)


@dataclass
class BellyProfile:
    """
    Bridge belly (ramp) profile between pin holes and saddle slot.

    The belly is the raised wood ramp that:
    1. Prevents the string from cutting into the bridge at the pin hole exit
    2. Controls the angle at which the string approaches the saddle
    3. Adds to the effective string exit height above the bridge surface

    The belly is defined by a circular arc from pin-hole centerline to
    the leading face of the saddle slot.

    belly_height_at_saddle_mm feeds directly into bridge_break_angle.py's
    slot_offset_mm parameter as the additional height the string exits above
    the bridge surface before reaching the saddle.
    """
    pin_to_saddle_mm: float         # horizontal span of the belly
    peak_height_mm: float           # max belly height above bridge surface
    peak_position_from_pins_mm: float  # where the peak occurs

    # Profile points (x from pin center, z height above bridge surface)
    profile_points: List[Tuple[float, float]]

    # Feed to break angle calc
    belly_height_at_saddle_mm: float   # effective string elevation at saddle face
    # This is the slot_offset_mm in BreakAngleInput (approximately)


@dataclass
class BridgeFootprint:
    """
    Complete acoustic bridge outline dimensions.

    The bridge body has:
    - Forward wings: extend beyond the saddle toward the neck
    - Saddle slot: routed through center section
    - Back wings: optional taper/shape behind saddle
    - Tie points (not applicable for pin bridges)

    The bridge is glued to the top with the center section spanning
    the bridge plate. Wings extend beyond the plate for aesthetics
    but must not extend into the X-brace zone.
    """
    # Overall dimensions
    total_length_mm: float      # neck-to-tail (X axis)
    total_width_mm: float       # treble-to-bass (Y axis)
    total_height_mm: float      # Z axis (above top surface)

    # Section widths (neck-to-tail)
    forward_section_mm: float   # from front edge to pin hole center
    pin_to_saddle_mm: float     # from pin center to saddle center
    saddle_section_mm: float    # saddle slot width
    rear_section_mm: float      # from saddle rear to back edge

    # Profile shape
    front_edge_shape: str       # "straight" | "curved" | "tapered"
    back_edge_shape: str        # "straight" | "curved" | "tapered"
    wing_taper_angle_deg: float # how much wings taper toward ends

    # Critical clearances
    saddle_to_back_edge_mm: float   # must be ≥ 6mm for structural integrity
    pin_row_to_front_edge_mm: float  # must be ≥ 4mm for pin hole integrity


@dataclass
class BridgePlateSpec:
    """
    Bridge plate dimensions (internal reinforcement under bridge).

    The bridge plate is glued to the INSIDE of the top, under the bridge.
    It distributes the string load over a larger area of the top plate.

    Material: typically spruce (matching top grain) or maple (stiffer).
    Grain: parallel to top grain (X axis) for maximum stiffness transfer.

    The plate must span:
    - The full X-brace intersection zone
    - The entire pin hole pattern (pins pass through plate into body)
    - Some margin beyond the bridge footprint
    """
    # Dimensions
    length_mm: float    # X axis, neck-to-tail
    width_mm: float     # Y axis, treble-to-bass
    thickness_mm: float # Z axis

    # Shape
    shape: str          # "rectangular" | "tapered" | "traditional"

    # Coverage
    covers_x_brace: bool      # must be True — plate must anchor X-brace area
    margin_mm: float          # extension beyond bridge footprint on each side

    # Notes
    grain_direction: str = "parallel_to_top"
    material: str = "spruce"


@dataclass
class AcousticBridgeSpec:
    """Complete acoustic pin bridge specification."""
    # Instrument context
    scale_length_mm: float
    string_count: int
    fretboard_radius_mm: float

    # All computed subsections
    string_spacing: StringSpacingResult
    saddle_slot: SaddleSlotSpec
    saddle_crown: SaddleCrownSpec
    pin_holes: BridgePinSpec
    belly: BellyProfile
    footprint: BridgeFootprint
    bridge_plate: BridgePlateSpec

    # Summary dimensions for break angle calculator
    break_angle_inputs: Dict[str, float]

    # Warnings
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# Core calculation functions
# ─────────────────────────────────────────────────────────────────────────────

def compute_string_spacing(
    nut_e_to_e_mm: float,
    saddle_e_to_e_mm: float,
    string_count: int = 6,
) -> StringSpacingResult:
    """
    Compute string spacing at nut and saddle.

    The nut is narrower (for fretting comfort) and the saddle is wider
    (to match the body's string spread). Strings diverge linearly.

    Standard reference values (6-string):
        Martin OM: nut 34.5mm, saddle 55.0mm
        Taylor:    nut 35.6mm, saddle 55.6mm
        Gibson J45: nut 37.7mm, saddle 52.5mm
        Classical: nut 51.4mm, saddle 58.0mm (nylon, different conventions)

    Args:
        nut_e_to_e_mm:    E-to-e string spread at nut (mm)
        saddle_e_to_e_mm: E-to-e string spread at saddle (mm)
        string_count:     Number of strings (default 6)

    Returns:
        StringSpacingResult with nut and saddle spacing and taper geometry.
    """
    n = string_count

    # Per-string spacing (uniform, center-to-center)
    nut_per = nut_e_to_e_mm / (n - 1) if n > 1 else 0
    sad_per = saddle_e_to_e_mm / (n - 1) if n > 1 else 0

    # String offsets from centerline (treble side negative)
    # String 1 = high E (treble), String n = low E (bass)
    nut_offsets = [(-nut_e_to_e_mm / 2 + i * nut_per) for i in range(n)]
    sad_offsets = [(-saddle_e_to_e_mm / 2 + i * sad_per) for i in range(n)]

    # Half-angle of string spread (from nut to saddle centerline)
    # Approximation: spread_angle = arctan((spread_increase/2) / scale_length)
    # We don't have scale here; provide the half-spread at bridge as taper indicator
    spread_increase = saddle_e_to_e_mm - nut_e_to_e_mm
    # taper_angle: angle each outer string makes with the centerline
    # Using nut-to-saddle distance ≈ scale_length for approximate taper
    taper_deg = 0.0   # computed in analyze_acoustic_bridge with scale length

    return StringSpacingResult(
        nut_e_to_e_mm=round(nut_e_to_e_mm, 2),
        nut_per_string_mm=round(nut_per, 3),
        nut_string_offsets_mm=[round(x, 3) for x in nut_offsets],
        saddle_e_to_e_mm=round(saddle_e_to_e_mm, 2),
        saddle_per_string_mm=round(sad_per, 3),
        saddle_string_offsets_mm=[round(x, 3) for x in sad_offsets],
        spread_increase_mm=round(spread_increase, 2),
        string_count=n,
        taper_angle_deg=taper_deg,
    )


def compute_saddle_crown(
    fretboard_radius_mm: float,
    saddle_e_to_e_mm: float,
    string_count: int = 6,
) -> SaddleCrownSpec:
    """
    Compute saddle crown radius profile matching fretboard radius.

    The saddle top is shaped as a circular arc with the same radius as
    the fretboard. This ensures string action is evenly distributed.

    Crown height formula (circular arc):
        h = R - sqrt(R² - (y)²)
    where y is lateral distance from saddle centerline (mm) and R is the
    fretboard radius. This is the drop from the center of the arc.

    For a saddle, the EDGE strings are at the crown peak (h=0), and
    the center strings are slightly lower (h > 0 means lower on the saddle,
    which means LESS saddle height needed at the center).

    Wait — convention matters here:
        Fretboard: higher at edges, lower at center (the arc bows DOWN)
        Saddle: must match, so edge strings are HIGHER than center strings
        Crown height = how much the edge strings are ABOVE center strings

    Args:
        fretboard_radius_mm: Fretboard (and saddle) radius. Use float('inf') for flat.
        saddle_e_to_e_mm:    String spread at saddle (mm)
        string_count:        Number of strings

    Returns:
        SaddleCrownSpec with height at each string position.
    """
    n = string_count
    per_string = saddle_e_to_e_mm / (n - 1) if n > 1 else 0
    offsets = [-saddle_e_to_e_mm / 2 + i * per_string for i in range(n)]

    if fretboard_radius_mm == float("inf") or fretboard_radius_mm <= 0:
        # Flat saddle
        heights = [0.0] * n
        crown_height = 0.0
    else:
        R = fretboard_radius_mm
        # Height at each string relative to the EDGE strings (edge = 0, center dips)
        # On a radiused fretboard, the center is LOWER than the edges.
        # h(y) = R - sqrt(R² - y²) gives distance from the chord to the arc
        # At edge string y = ±e_to_e/2: h = 0 (reference)
        # At center strings: h > 0 (means they're lower on the arc = less saddle height)
        half_ee = saddle_e_to_e_mm / 2
        h_edge = R - math.sqrt(max(0, R**2 - half_ee**2))
        heights = []
        for y in offsets:
            h_at_y = R - math.sqrt(max(0, R**2 - y**2))
            # Height relative to center of saddle (positive = edge is higher)
            heights.append(round(h_at_y - h_edge, 4))
        crown_height = max(heights) - min(heights)
        # Negate: we want "how much lower is center vs edge"
        # heights[i] = 0 at edges, negative at center (center is lower)
        # Reframe: positive = how much BELOW edge this string sits
        h_at_center = R - math.sqrt(max(0, R**2 - 0**2)) - h_edge
        heights = [round(h_at_y - h_edge, 4) for h_at_y in
                   [R - math.sqrt(max(0, R**2 - y**2)) for y in offsets]]
        crown_height = round(abs(heights[n//2] - heights[0]), 3)

    # Action correction: each string needs its saddle height INCREASED by
    # the amount it sits below the edge strings (to maintain uniform action)
    # Edge strings: no correction. Center strings: +crown_height correction.
    action_corr = [round(-h, 4) for h in heights]

    return SaddleCrownSpec(
        fretboard_radius_mm=fretboard_radius_mm,
        saddle_e_to_e_mm=saddle_e_to_e_mm,
        crown_height_mm=crown_height,
        height_at_positions_mm=[round(h, 3) for h in heights],
        action_correction_per_string=action_corr,
    )


def compute_saddle_slant_angle(
    compensations_mm: Dict[str, float],
    saddle_e_to_e_mm: float,
) -> float:
    """
    Compute saddle slot slant angle from per-string compensation values.

    The saddle slot is cut at an angle so that wound strings (more
    compensation) are farther back than plain strings. The slot angle
    is the arctangent of the compensation spread over the string spread.

    Convention: positive angle = bass end is farther back.

    Args:
        compensations_mm: Dict of string_id -> compensation in mm.
                         Typical: E6 = 3.0mm, E1 = 1.0mm
        saddle_e_to_e_mm: String spread at saddle (E-to-e, mm)

    Returns:
        Slant angle in degrees.
    """
    values = list(compensations_mm.values())
    if not values or saddle_e_to_e_mm <= 0:
        return 0.0
    comp_spread = max(values) - min(values)
    # Angle: compensation spread over string spread
    # (bass end is max comp, treble end is min comp)
    angle_rad = math.atan2(comp_spread, saddle_e_to_e_mm)
    return round(math.degrees(angle_rad), 2)


def compute_saddle_slot(
    saddle_blank_width_mm: float,
    saddle_blank_height_mm: float,
    saddle_projection_mm: float,
    saddle_e_to_e_mm: float,
    bridge_total_length_mm: float,
    saddle_center_from_back_mm: float,
    slant_angle_deg: float = 2.5,
    overhang_per_side_mm: float = 2.0,
) -> SaddleSlotSpec:
    """
    Compute saddle slot dimensions and location on the bridge body.

    The slot must be positioned so that:
    1. Adequate wood remains behind the slot (structural shear resistance)
    2. Adequate wood remains forward of the slot (belly and pin zone)
    3. Slot depth leaves at least MIN_SADDLE_SEAT_DEPTH_MM of saddle seated

    Args:
        saddle_blank_width_mm:     Width of saddle blank (sets slot width)
        saddle_blank_height_mm:    Total saddle blank height
        saddle_projection_mm:      How much saddle projects above bridge
        saddle_e_to_e_mm:          String spread at saddle
        bridge_total_length_mm:    Total bridge length (neck-to-tail)
        saddle_center_from_back_mm: Slot centerline from back edge of bridge
        slant_angle_deg:           Saddle slant angle (from compute_saddle_slant_angle)
        overhang_per_side_mm:      Saddle extends this much beyond outer strings

    Returns:
        SaddleSlotSpec with all slot dimensions and location.
    """
    slot_length = saddle_e_to_e_mm + 2 * overhang_per_side_mm
    slot_depth = saddle_blank_height_mm - saddle_projection_mm
    seat_depth = slot_depth   # = saddle_blank_height - projection
    seat_ok = seat_depth >= MIN_SADDLE_SEAT_DEPTH_MM

    # Slant offset: how much the slot deviates end-to-end
    slant_offset = slot_length * math.tan(math.radians(slant_angle_deg))

    # Location on bridge
    from_back = saddle_center_from_back_mm - saddle_blank_width_mm / 2
    from_front = bridge_total_length_mm - saddle_center_from_back_mm - saddle_blank_width_mm / 2

    return SaddleSlotSpec(
        width_mm=round(saddle_blank_width_mm, 2),
        depth_mm=round(slot_depth, 2),
        length_mm=round(slot_length, 2),
        overhang_per_side_mm=overhang_per_side_mm,
        from_back_edge_mm=round(from_back, 2),
        from_front_edge_mm=round(from_front, 2),
        centerline_from_back_mm=round(saddle_center_from_back_mm, 2),
        slant_angle_deg=slant_angle_deg,
        slant_offset_mm=round(slant_offset, 2),
        seat_depth_mm=round(seat_depth, 2),
        seat_adequate=seat_ok,
    )


def compute_bridge_pin_holes(
    saddle_e_to_e_mm: float,
    pin_to_saddle_mm: float,
    string_count: int = 6,
    slant_angle_deg: float = 2.5,
) -> BridgePinSpec:
    """
    Compute bridge pin hole positions.

    Pin holes are drilled at the same Y spacing as the saddle strings,
    at a fixed X distance forward of (toward the nut from) the saddle.
    The pin row has the same slant as the saddle slot.

    The string exits the pin hole and rises over the belly to the saddle.
    The effective exit distance is the horizontal span from pin center
    to saddle center (pin_to_saddle_mm) reduced by the belly overhang.

    Standard pin-to-saddle distances:
        Martin OM/D: 10.5mm
        Taylor:      10.0mm
        Gibson J45:  9.5mm

    Args:
        saddle_e_to_e_mm:  E-to-e saddle spacing
        pin_to_saddle_mm:  Center-to-center distance from pin to saddle
        string_count:      Number of strings
        slant_angle_deg:   Slant angle (same as saddle)

    Returns:
        BridgePinSpec
    """
    n = string_count
    per_string = saddle_e_to_e_mm / (n - 1) if n > 1 else 0
    pin_offsets = [-saddle_e_to_e_mm / 2 + i * per_string for i in range(n)]

    # String exit to saddle: pin_to_saddle minus a small belly correction
    # (belly raises string slightly; effective horizontal distance is unchanged
    #  but the slot_offset in break angle calc accounts for this)
    string_exit_dist = pin_to_saddle_mm

    return BridgePinSpec(
        count=n,
        e_to_e_mm=round(saddle_e_to_e_mm, 2),
        pin_to_saddle_center_mm=round(pin_to_saddle_mm, 2),
        pin_offsets_mm=[round(y, 3) for y in pin_offsets],
        hole_diameter_mm=PIN_HOLE_DIAMETER_MM,
        hole_depth_mm=PIN_HOLE_DEPTH_MM,
        reamer_angle_deg=PIN_HOLE_REAMER_ANGLE_DEG,
        string_exit_to_saddle_mm=round(string_exit_dist, 2),
    )


def compute_belly_profile(
    pin_to_saddle_mm: float,
    belly_height_mm: float = 2.0,
) -> BellyProfile:
    """
    Compute bridge belly (ramp) profile between pin holes and saddle slot.

    The belly is a raised ramp that supports the string as it exits the
    pin hole and approaches the saddle. It prevents the string from cutting
    into the bridge wood at the pin hole exit.

    The belly profile follows a cosine curve (smooth entry and exit):
        z(x) = belly_height × (1 - cos(π × x / span)) / 2
    where x is measured from pin center toward saddle (0 = pin, span = saddle face).

    The effective string elevation above the bridge surface at the saddle
    face is approximately belly_height × 0.3–0.5 (the curve has mostly
    descended by the time it reaches the saddle).

    This value feeds into bridge_break_angle.py as slot_offset_mm:
    the string exits the belly ramp slightly above bridge surface level,
    effectively reducing the horizontal distance to the saddle crown.

    Args:
        pin_to_saddle_mm:  Horizontal distance from pin center to saddle
        belly_height_mm:   Maximum belly height above bridge surface (typical: 1.5–3.0mm)

    Returns:
        BellyProfile with profile points and effective height at saddle face.
    """
    span = pin_to_saddle_mm
    n_points = 20
    points = []
    for i in range(n_points + 1):
        x = span * i / n_points
        # Cosine bell curve: peak at midpoint
        z = belly_height_mm * (1 - math.cos(math.pi * x / span)) / 2
        points.append((round(x, 2), round(z, 3)))

    # Height at saddle face (x = span): cosine curve returns to 0
    # But the string physically is still elevated by the pin hole entry geometry
    # Empirical: effective slot offset ≈ 30% of peak belly height
    belly_at_saddle = round(belly_height_mm * 0.30, 2)

    return BellyProfile(
        pin_to_saddle_mm=round(pin_to_saddle_mm, 2),
        peak_height_mm=round(belly_height_mm, 2),
        peak_position_from_pins_mm=round(span / 2, 2),
        profile_points=points,
        belly_height_at_saddle_mm=belly_at_saddle,
    )


def compute_bridge_footprint(
    total_length_mm: float,
    saddle_e_to_e_mm: float,
    bridge_height_mm: float,
    saddle_center_from_back_mm: float,
    pin_to_saddle_mm: float,
    saddle_slot_width_mm: float = 3.0,
    front_edge_shape: str = "curved",
    back_edge_shape: str = "straight",
    wing_taper_angle_deg: float = 5.0,
) -> BridgeFootprint:
    """
    Compute bridge body footprint (outline dimensions).

    Standard acoustic bridge proportions (Martin OM reference):
        Total length:     155mm
        Total width:      35mm (at saddle, narrows to ~20mm at tips)
        Height:           10mm (above top surface)
        Forward section:  22mm (front edge to pin centers)
        Pin-to-saddle:    10.5mm
        Saddle section:   3mm (slot width)
        Rear section:     8mm (saddle rear to back edge)

    The bridge width varies with string count and string spread.
    Minimum width at saddle: saddle_e_to_e + 2 × (at least 6mm per side).

    Args:
        total_length_mm:          Overall bridge length neck-to-tail
        saddle_e_to_e_mm:         String spread at saddle
        bridge_height_mm:         Bridge height above top surface
        saddle_center_from_back_mm: Saddle centerline from back edge
        pin_to_saddle_mm:         Pin center to saddle center distance
        saddle_slot_width_mm:     Saddle slot width
        front_edge_shape:         Front edge profile shape
        back_edge_shape:          Back edge profile shape
        wing_taper_angle_deg:     Taper of wings toward tips

    Returns:
        BridgeFootprint
    """
    # Section widths (neck-to-tail direction)
    rear_section = saddle_center_from_back_mm - saddle_slot_width_mm / 2
    saddle_section = saddle_slot_width_mm
    belly_section = pin_to_saddle_mm
    forward_section = total_length_mm - rear_section - saddle_section - belly_section

    # Minimum bridge body width at saddle: string spread + margins
    min_width_at_saddle = saddle_e_to_e_mm + 12.0  # 6mm per side
    total_width = max(min_width_at_saddle, saddle_e_to_e_mm + 16.0)

    return BridgeFootprint(
        total_length_mm=round(total_length_mm, 1),
        total_width_mm=round(total_width, 1),
        total_height_mm=round(bridge_height_mm, 1),
        forward_section_mm=round(max(forward_section, 15.0), 1),
        pin_to_saddle_mm=round(belly_section, 1),
        saddle_section_mm=round(saddle_section, 1),
        rear_section_mm=round(rear_section, 1),
        front_edge_shape=front_edge_shape,
        back_edge_shape=back_edge_shape,
        wing_taper_angle_deg=wing_taper_angle_deg,
        saddle_to_back_edge_mm=round(rear_section, 1),
        pin_row_to_front_edge_mm=round(max(forward_section, 15.0), 1),
    )


def compute_bridge_plate(
    bridge_total_length_mm: float,
    saddle_e_to_e_mm: float,
    top_thickness_mm: float = 2.5,
    margin_mm: float = 10.0,
) -> BridgePlateSpec:
    """
    Compute bridge plate dimensions.

    The bridge plate is the internal reinforcement glued to the inside
    of the top under the bridge. It distributes string load (transmitted
    via bridge pins pulling down on the top) over a larger top area,
    reducing stress concentration.

    Standard bridge plate sizing:
        Length: bridge length + 2 × margin (≈ 170–180mm)
        Width:  string spread + 2 × margin (≈ 75–80mm)
        Thickness: 3–4mm spruce (softer) or 2.5–3mm maple (stiffer)

    Grain direction: parallel to top grain (along X axis).
    A cross-grain plate (common in lower-cost instruments) is acceptable
    but provides less stiffness in the critical direction.

    Args:
        bridge_total_length_mm: Bridge body length
        saddle_e_to_e_mm:       String spread at saddle
        top_thickness_mm:       Top plate thickness (for proportion check)
        margin_mm:              Extension beyond bridge footprint

    Returns:
        BridgePlateSpec
    """
    length = bridge_total_length_mm + 2 * margin_mm
    width = saddle_e_to_e_mm + 2 * margin_mm + 20.0  # extra for X-brace coverage
    # Thickness: scale with top thickness but minimum 3mm
    thickness = max(3.0, top_thickness_mm * 1.2)

    return BridgePlateSpec(
        length_mm=round(length, 1),
        width_mm=round(width, 1),
        thickness_mm=round(thickness, 2),
        shape="traditional",
        covers_x_brace=True,
        margin_mm=margin_mm,
        grain_direction="parallel_to_top",
        material="spruce",
    )


# ─────────────────────────────────────────────────────────────────────────────
# High-level analysis function
# ─────────────────────────────────────────────────────────────────────────────

# Standard compensation values (mm) per string — typical 6-string acoustic
STANDARD_COMPENSATIONS_MM: Dict[str, float] = {
    "E6": 3.0,   # Low E — wound, most compensation
    "A5": 2.5,
    "D4": 2.0,
    "G3": 1.5,
    "B2": 1.5,
    "E1": 1.0,   # High E — plain, least compensation
}

# Standard nut E-to-e by instrument family
NUT_E_TO_E_MM: Dict[str, float] = {
    "martin_000":     34.5,
    "martin_om":      34.5,
    "martin_d28":     35.0,
    "taylor_standard":35.6,
    "gibson_j45":     37.7,
    "classical":      51.4,
}

# Standard saddle E-to-e by instrument family
SADDLE_E_TO_E_MM: Dict[str, float] = {
    "martin_000":     54.0,
    "martin_om":      55.0,
    "martin_d28":     55.0,
    "taylor_standard":55.6,
    "gibson_j45":     52.5,
    "classical":      58.0,
}


def analyze_acoustic_bridge(
    scale_length_mm: float = 648.0,
    fretboard_radius_in: float = 10.0,
    nut_e_to_e_mm: float = 34.5,
    saddle_e_to_e_mm: float = 55.0,
    string_count: int = 6,
    bridge_length_mm: float = 155.0,
    bridge_height_mm: float = 10.0,
    saddle_projection_mm: float = 2.5,
    saddle_blank_width_mm: float = 3.0,
    saddle_blank_height_mm: float = 12.0,
    pin_to_saddle_mm: float = 10.5,
    belly_height_mm: float = 2.0,
    saddle_center_from_back_mm: float = 8.0,
    compensations_mm: Optional[Dict[str, float]] = None,
    top_thickness_mm: float = 2.5,
) -> AcousticBridgeSpec:
    """
    Complete acoustic pin bridge geometry analysis.

    Computes all bridge geometry subsystems and their interdependencies.
    Default values are Martin OM standard dimensions.

    Args:
        scale_length_mm:          Full scale length (mm)
        fretboard_radius_in:      Fretboard radius in inches (10" default)
        nut_e_to_e_mm:            E-to-e string spread at nut (mm)
        saddle_e_to_e_mm:         E-to-e string spread at saddle (mm)
        string_count:             Number of strings
        bridge_length_mm:         Total bridge length neck-to-tail (mm)
        bridge_height_mm:         Bridge body height above top surface (mm)
        saddle_projection_mm:     Saddle height above bridge surface (mm)
        saddle_blank_width_mm:    Saddle blank width (sets slot width) (mm)
        saddle_blank_height_mm:   Saddle blank total height (mm)
        pin_to_saddle_mm:         Pin center to saddle centerline distance (mm)
        belly_height_mm:          Belly peak height above bridge surface (mm)
        saddle_center_from_back_mm: Saddle centerline from back edge (mm)
        compensations_mm:         Per-string compensations (uses standard if None)
        top_thickness_mm:         Top plate thickness for bridge plate calc

    Returns:
        AcousticBridgeSpec — complete bridge geometry specification.
    """
    warnings = []
    comps = compensations_mm or STANDARD_COMPENSATIONS_MM

    # Convert fretboard radius
    fr_mm = fretboard_radius_in * 25.4 if fretboard_radius_in > 0 else float("inf")

    # 1. String spacing
    spacing = compute_string_spacing(nut_e_to_e_mm, saddle_e_to_e_mm, string_count)
    # Add taper angle now that we have scale length
    taper_rad = math.atan2((saddle_e_to_e_mm - nut_e_to_e_mm) / 2, scale_length_mm)
    spacing.taper_angle_deg = round(math.degrees(taper_rad), 3)

    # 2. Saddle slant angle
    slant_deg = compute_saddle_slant_angle(comps, saddle_e_to_e_mm)

    # 3. Saddle crown
    crown = compute_saddle_crown(fr_mm, saddle_e_to_e_mm, string_count)

    # 4. Saddle slot
    slot = compute_saddle_slot(
        saddle_blank_width_mm, saddle_blank_height_mm, saddle_projection_mm,
        saddle_e_to_e_mm, bridge_length_mm, saddle_center_from_back_mm,
        slant_angle_deg=slant_deg,
    )
    if not slot.seat_adequate:
        warnings.append(
            f"Saddle seat depth {slot.seat_depth_mm:.1f}mm < minimum {MIN_SADDLE_SEAT_DEPTH_MM}mm. "
            "Increase saddle blank height or reduce projection."
        )
    if slot.from_back_edge_mm < 6.0:
        warnings.append(
            f"Only {slot.from_back_edge_mm:.1f}mm of wood behind saddle slot. "
            "Minimum 6mm required for shear resistance. Move slot forward."
        )

    # 5. Pin holes
    pins = compute_bridge_pin_holes(saddle_e_to_e_mm, pin_to_saddle_mm, string_count, slant_deg)

    # 6. Belly profile
    belly = compute_belly_profile(pin_to_saddle_mm, belly_height_mm)

    # 7. Bridge footprint
    footprint = compute_bridge_footprint(
        bridge_length_mm, saddle_e_to_e_mm, bridge_height_mm,
        saddle_center_from_back_mm, pin_to_saddle_mm, saddle_blank_width_mm,
    )
    if footprint.forward_section_mm < 15.0:
        warnings.append(
            f"Forward section ({footprint.forward_section_mm:.0f}mm) is short. "
            "Pin holes may be too close to front edge."
        )

    # 8. Bridge plate
    plate = compute_bridge_plate(bridge_length_mm, saddle_e_to_e_mm, top_thickness_mm)

    # 9. Summary for break angle calculator
    break_angle_inputs = {
        "pin_to_saddle_center_mm": pin_to_saddle_mm,
        "slot_offset_mm": belly.belly_height_at_saddle_mm,
        "saddle_projection_mm": saddle_projection_mm,
        "saddle_slot_depth_mm": slot.depth_mm,
        "saddle_blank_height_mm": saddle_blank_height_mm,
    }

    return AcousticBridgeSpec(
        scale_length_mm=scale_length_mm,
        string_count=string_count,
        fretboard_radius_mm=fr_mm,
        string_spacing=spacing,
        saddle_slot=slot,
        saddle_crown=crown,
        pin_holes=pins,
        belly=belly,
        footprint=footprint,
        bridge_plate=plate,
        break_angle_inputs=break_angle_inputs,
        warnings=warnings,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Preset factory
# ─────────────────────────────────────────────────────────────────────────────

def bridge_preset(style: str) -> AcousticBridgeSpec:
    """
    Return a fully computed bridge spec for a standard instrument style.

    Styles: "martin_om" | "martin_d28" | "martin_000" | "taylor_standard"
            | "gibson_j45" | "classical"
    """
    presets = {
        "martin_om": dict(
            scale_length_mm=648.0, fretboard_radius_in=10.0,
            nut_e_to_e_mm=34.5, saddle_e_to_e_mm=55.0,
            bridge_length_mm=155.0, bridge_height_mm=10.0,
            saddle_projection_mm=2.5, pin_to_saddle_mm=10.5,
        ),
        "martin_d28": dict(
            scale_length_mm=648.0, fretboard_radius_in=12.0,
            nut_e_to_e_mm=35.0, saddle_e_to_e_mm=55.0,
            bridge_length_mm=162.0, bridge_height_mm=10.0,
            saddle_projection_mm=2.5, pin_to_saddle_mm=10.5,
        ),
        "martin_000": dict(
            scale_length_mm=632.5, fretboard_radius_in=10.0,
            nut_e_to_e_mm=34.5, saddle_e_to_e_mm=54.0,
            bridge_length_mm=152.0, bridge_height_mm=10.0,
            saddle_projection_mm=2.5, pin_to_saddle_mm=10.0,
        ),
        "taylor_standard": dict(
            scale_length_mm=650.2, fretboard_radius_in=15.0,
            nut_e_to_e_mm=35.6, saddle_e_to_e_mm=55.6,
            bridge_length_mm=160.0, bridge_height_mm=10.5,
            saddle_projection_mm=2.5, pin_to_saddle_mm=10.0,
        ),
        "gibson_j45": dict(
            scale_length_mm=628.65, fretboard_radius_in=12.0,
            nut_e_to_e_mm=37.7, saddle_e_to_e_mm=52.5,
            bridge_length_mm=152.0, bridge_height_mm=10.0,
            saddle_projection_mm=2.5, pin_to_saddle_mm=9.5,
        ),
        "classical": dict(
            scale_length_mm=650.0, fretboard_radius_in=0,  # flat (inf)
            nut_e_to_e_mm=51.4, saddle_e_to_e_mm=58.0,
            bridge_length_mm=185.0, bridge_height_mm=9.0,
            saddle_projection_mm=2.0, pin_to_saddle_mm=0,  # no pins, tie block
        ),
    }
    if style not in presets:
        raise ValueError(f"Unknown bridge preset: {style!r}. "
                         f"Available: {list(presets.keys())}")
    return analyze_acoustic_bridge(**presets[style])
