# services/api/app/calculators/headstock_break_angle_calc.py
"""
Headstock Break Angle Calculator — GEOMETRY-009

Connects tuner post height, wrap count, and string tree geometry to
per-string nut break angle, downforce, and tuning stability.

Physical model and derivation
==============================

The break angle at the nut is the angle the string makes as it bends
over the nut from the fretboard plane downward to the first anchor point
behind the nut (string tree if present, otherwise the tuner post).

COORDINATE SYSTEM
    Origin: nut exit point N = (0, 0)
    x: along neck centerline, positive toward headstock
    y: perpendicular to neck plane, positive DOWNWARD (away from player)

    y > 0: point is below nut exit plane → creates downforce at nut ✓
    y < 0: point is above nut exit plane → string lifts at nut ✗

KEY POINTS
    N = (0, 0)                  — nut exit reference
    A = (x_P, y_A)              — effective string anchor on tuner post
    T = (x_T, y_T)              — string tree contact (if present)

ANCHOR HEIGHT FROM POST GEOMETRY
    The headstock surface sits below the nut exit plane by:
        y_headstock = headstock_depth_mm  (positive = below nut)

    The tuner string hole is at height h_hole above the headstock surface:
        y_hole = y_headstock - h_hole

    String wraps DOWN from the hole. The w-th wrap center is at:
        y_A = y_hole + (w - 0.5) × d_s     [from source geometry]

    where d_s = string diameter.

    headstock_depth is approximately:
        - Fretboard thickness (~5-6mm) + headstock relief drop (~8-10mm)
        - Total: ~13-16mm for a typical flat (Fender-style) headstock
        - For angled headstocks, increases with distance from nut:
          headstock_depth(x) = x × tan(headstock_angle) + fretboard_thickness

BREAK ANGLE
    Without string tree:
        θ_nut = arctan(y_A / x_P)

    With string tree (tree is the first anchor the nut "sees"):
        θ_nut  = arctan(y_T / x_T)        — nut to tree angle
        θ_tree = arctan((y_T - y_A) / (x_P - x_T))  — tree to post angle

    The nut only "sees" its immediate downstream anchor. For strings with
    a tree, θ_nut is set by the tree position; the string-tree-to-post
    angle affects tension distribution and adds a second friction point.

DOWNFORCE AT NUT
    For a string at tension T bent through angle θ:
        F_perp = 2T × sin(θ/2)    [exact]
               ≈ T × θ             [small-angle, θ in radians]

FRICTION — EULER CAPSTAN EQUATION
    The tension ratio across a bend with friction coefficient μ and
    contact angle θ (in radians):
        T_tight / T_slack = exp(μ × θ)

    This gives the minimum pitch change the string can sustain in the
    slot before friction is overcome — i.e., tuning lag:
        Δcents ≈ (1200 / ln2) × (exp(μθ) - 1) / 2

    A string "pings" when it finally overcomes friction. Higher μ or
    larger θ both increase lag. String trees add a second capstan contact.

HEADSTOCK TYPE COMPARISON
    Angled (Gibson/Martin ~14-17°):
        - Headstock tilt generates depth automatically
        - depth(x) = x × tan(angle) + fretboard_thickness
        - Break angle ≈ headstock angle for most strings (8-17°)
        - Trees not normally needed
        - Risk: too steep (>15°) on treble strings with unlubricated nut

    Straight (Fender 0°):
        - All depth comes from headstock_depth (fretboard + relief)
        - Break angle 4-8° with typical post heights and wraps
        - Treble strings (B, e) often need string trees to reach >4°
        - Staggered tuners (varying h_hole by string) reduce/eliminate
          need for string trees

TUNING STABILITY FLAG THRESHOLDS
    < 3°:    Risk of string lifting from nut slot; open-string buzz behind nut
    3-4°:    Marginal; acceptable for wound bass strings, risky for plain trebles
    4-9°:    Good range; string seated, low friction
    10-14°:  Steep; more downforce, friction increases
    > 15°:   Binding risk on non-locking nuts; string sticks, "ping" on release
             Compounded if also passing through a string tree

Source attribution — what each source actually contributes
===========================================================

GEOMETRY AND FRICTION FORMULAS (derived, not empirical):
    Coordinate model, anchor height formula, break angle formula:
        Derived in this module from first principles. The geometry is
        Euclidean; no empirical constants anywhere in the formulas.
        Independently confirmed by:
        - Premier Guitar "Bass Bench" column (break angle geometry)
        - hazeguitars.com "String Break Angle at the Nut" (tree geometry)
        - ANZLF forum thread (tuner layout, fretboard thickness variables)

    Euler capstan equation (T_tight/T_slack = exp(μθ)):
        Classical mechanics. Standard textbook result.

    Downforce formula F_perp = 2T×sin(θ/2):
        Classical mechanics. Standard result for a string bent over a point.

DESIGN THRESHOLD RANGES (empirical — practitioner consensus):
    The 3° lower bound (buzz risk) and 15° upper bound (binding risk) are
    NOT derivable from the capstan equation alone. They come from the
    accumulated experience of builders observing failures at both extremes.

    Lower bound (3-4°) calibration:
        - Ormsby Guitars and PRS both use 9° as standard — establishing
          that 9° is well into the acceptable zone. (ANZLF forum, Ormsby
          post confirming production spec.)
        - Builder consensus of 12° as comfortable, 10° as marginal, from
          the same ANZLF thread (kiwigeo, demonx, jeffhigh).
        - MIMF forum: documented cases of buzz below 3-4° on plain strings.
          (http://www.mimf.com/phpbb/viewtopic.php?t=1505)

    Upper bound (>15° binding risk) calibration:
        - Premier Guitar "Bass Bench": strings sticking and "pinging" at
          steep angles, particularly at string trees on flat headstocks.
          (https://www.premierguitar.com/bass-bench-give-me-a-break)
        - Hazeguitars: steep angle + string tree compounds friction —
          empirical observation of tuning instability at combined high angles.
          (https://hazeguitars.com/blog/string-break-angle-at-nut-a-primer)
        - Gibson G-string binding: widely documented consequence of 17°
          headstock on an unlubricated bone nut. The module flags STEEP
          correctly at 17°; this is not a bug in the thresholds.

    Variable identification (jeffhigh, ANZLF forum):
        "10 will work if you have an appropriate tuner layout, a 1/4 inch
        fretboard, and don't have excess tuner post protrusion."
        This is the exact parameter set of the model: headstock_angle,
        fretboard_thickness_mm, h_hole_above_headstock_mm. The forum
        confirms the parameterization matches how experienced builders
        actually reason about the problem.

FRICTION COEFFICIENTS:
    Steel, brass, bone: material science literature (Rabinowicz,
    Friction and Wear of Materials, 2nd ed.).
    TUSQ/GraphTech: manufacturer published data.
    Practical values confirmed against luthier experience (MIMF, Premier Guitar).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Design thresholds
# ─────────────────────────────────────────────────────────────────────────────

ANGLE_BUZZ_RISK_DEG: float      = 3.0   # below this → string lifts, buzz risk
ANGLE_MARGINAL_MIN_DEG: float   = 4.0   # marginal lower bound
ANGLE_GOOD_MIN_DEG: float       = 4.0   # acceptable lower bound
ANGLE_GOOD_MAX_DEG: float       = 9.0   # acceptable upper bound
ANGLE_STEEP_MAX_DEG: float      = 15.0  # above this → binding risk (non-locking nut)


# ─────────────────────────────────────────────────────────────────────────────
# Material friction coefficients
# ─────────────────────────────────────────────────────────────────────────────

NUT_FRICTION: Dict[str, float] = {
    "bone_dry":         0.10,
    "bone_lubricated":  0.05,
    "tusq":             0.04,
    "graphtech":        0.04,
    "graphite":         0.05,
    "brass_dry":        0.25,
    "steel_dry":        0.30,
    "roller":           0.02,   # roller tree / locking nut (near-zero)
}


# ─────────────────────────────────────────────────────────────────────────────
# Geometry functions
# ─────────────────────────────────────────────────────────────────────────────

def headstock_depth_at(
    x_from_nut_mm: float,
    headstock_angle_deg: float,
    fretboard_thickness_mm: float,
    headstock_relief_drop_mm: float = 8.0,
) -> float:
    """
    Depth of headstock surface below the nut exit plane at longitudinal
    position x from the nut.

    For a STRAIGHT (0°) headstock:
        depth = fretboard_thickness + headstock_relief_drop
        (constant regardless of x)

    For an ANGLED headstock:
        depth(x) = x × tan(angle) + fretboard_thickness
        (increases with distance from nut as headstock tilts away)

    Args:
        x_from_nut_mm:          Distance from nut to tuner post (mm)
        headstock_angle_deg:    Headstock tilt angle (degrees, 0 for Fender)
        fretboard_thickness_mm: Fretboard thickness at nut (mm)
        headstock_relief_drop_mm: Additional drop of headstock surface vs
                                  neck plane on flat headstocks (mm)

    Returns:
        Depth below nut exit plane (mm, positive = below nut)
    """
    if headstock_angle_deg > 0:
        tilt = x_from_nut_mm * math.tan(math.radians(headstock_angle_deg))
        return tilt + fretboard_thickness_mm
    else:
        return fretboard_thickness_mm + headstock_relief_drop_mm


def anchor_y(
    y_hole_from_nut: float,
    wrap_count: int,
    string_dia_mm: float,
) -> float:
    """
    Vertical position of string anchor (wrap center) below nut exit.

    y_A = y_hole + (w - 0.5) × d_s

    String winds downward from the hole. Each complete wrap adds one
    string diameter of depth below the hole entry point.

    Args:
        y_hole_from_nut: Hole position relative to nut (mm, positive = below)
        wrap_count:      Number of wraps below the hole
        string_dia_mm:   String diameter (mm)

    Returns:
        Anchor y-coordinate (mm, positive = below nut)
    """
    return y_hole_from_nut + (wrap_count - 0.5) * string_dia_mm


def break_angle_deg(
    x_from_nut_mm: float,
    y_anchor_from_nut_mm: float,
) -> float:
    """
    Break angle at the nut: angle of string below nut exit plane.

        θ = arctan(y_anchor / x_anchor)

    Positive = string goes downward from nut → correct downforce direction.
    Negative = string goes upward from nut → insufficient or reversed downforce.

    Args:
        x_from_nut_mm:        Horizontal distance nut to anchor (mm)
        y_anchor_from_nut_mm: Vertical depth of anchor below nut (mm)

    Returns:
        Break angle in degrees (positive = downward)
    """
    if x_from_nut_mm <= 0:
        return 0.0
    return math.degrees(math.atan2(y_anchor_from_nut_mm, x_from_nut_mm))


def downforce_N(tension_N: float, theta_deg: float) -> float:
    """
    Perpendicular downforce at the nut.

        F_perp = 2T × sin(θ/2)     [exact form]

    Args:
        tension_N: String tension (N)
        theta_deg: Break angle at nut (degrees)

    Returns:
        Downforce (N)
    """
    theta_rad = math.radians(abs(theta_deg))
    return 2.0 * tension_N * math.sin(theta_rad / 2.0)


def tuning_lag_cents(mu: float, theta_deg: float) -> float:
    """
    Pitch change the string can sustain in the nut slot before friction
    is overcome (Euler capstan equation).

        T_tight / T_slack = exp(μ × θ_rad)
        Δcents ≈ (1200 / ln2) × (T_ratio - 1) / 2

    This is the "tuning lag" — how many cents of pitch change occur
    before the string slips through the nut slot.

    Args:
        mu:        Friction coefficient of nut material
        theta_deg: Contact angle at nut (degrees)

    Returns:
        Tuning lag in cents (higher = worse tuning stability)
    """
    theta_rad = math.radians(abs(theta_deg))
    ratio = math.exp(mu * theta_rad)
    delta_f_frac = (ratio - 1.0) / 2.0   # Δf/f ≈ ΔT/(2T)
    return (1200.0 / math.log(2)) * delta_f_frac


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TunerPost:
    """
    A single tuner post specification.

    h_hole_above_headstock_mm is the critical parameter: it is the height
    of the string hole above the headstock surface. This is what determines
    the anchor height, not the total post protrusion.

    For most Kluson/Gotoh/Schaller-style tuners:
        h_hole ≈ post_visible_length - 2 to 4mm
    """
    x_from_nut_mm: float          # distance from nut to post center (mm)
    h_hole_above_headstock_mm: float  # string hole height above headstock surface (mm)
    string_name: str = ""
    string_dia_mm: float = 0.406  # default .016" B string


@dataclass
class StringTree:
    """
    A string tree or retainer bar.

    The tree inserts an intermediate anchor between the nut and the tuner.
    The nut only "sees" the nut-to-tree angle.
    The tree-to-tuner angle adds a second capstan contact point.

    applies_to: list of string names this tree contacts.
    """
    x_from_nut_mm: float              # longitudinal position (mm from nut)
    y_below_nut_mm: float             # depth below nut exit plane (mm, positive = below)
    applies_to: List[str] = field(default_factory=list)
    material: str = "steel_dry"       # key into NUT_FRICTION


@dataclass
class StringBreakResult:
    """Per-string break angle analysis result."""
    string_name: str
    string_dia_mm: float

    # Geometry
    x_anchor_mm: float          # x of effective anchor (tree or post)
    y_anchor_mm: float          # y of effective anchor (tree or post)
    x_post_mm: float            # x of tuner post
    y_post_mm: float            # y of tuner post anchor

    # Angles
    theta_nut_deg: float        # nut break angle (nut → first anchor)
    theta_post_deg: float       # post angle (nut → post, ignoring tree)

    # Tree
    has_tree: bool
    tree_contact_angle_deg: float = 0.0  # tree to post angle (friction source)

    # Forces
    tension_N: float = 70.0
    downforce_N: float = 0.0

    # Friction (at nut material, then tree material if present)
    nut_material: str = "bone_dry"
    tuning_lag_nut_cents: float = 0.0
    tuning_lag_tree_cents: float = 0.0
    tuning_lag_total_cents: float = 0.0

    # Status
    status: str = "OK"        # "OK" | "SHALLOW" | "MARGINAL" | "STEEP" | "BINDING_RISK"
    notes: List[str] = field(default_factory=list)

    @property
    def active_angle_deg(self) -> float:
        """The angle that determines downforce at the nut."""
        return self.theta_nut_deg


@dataclass
class HeadstockBreakSpec:
    """
    Complete headstock break angle specification for all strings.
    """
    headstock_angle_deg: float
    headstock_type: str           # "straight" | "angled"
    fretboard_thickness_mm: float
    nut_material: str

    strings: List[StringBreakResult]

    # Summary
    any_shallow: bool = False
    any_binding_risk: bool = False
    tree_recommendation: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Core analyzer
# ─────────────────────────────────────────────────────────────────────────────

def analyze_string(
    post: TunerPost,
    wrap_count: int,
    tension_N: float,
    headstock_angle_deg: float,
    fretboard_thickness_mm: float,
    headstock_relief_drop_mm: float,
    nut_material: str = "bone_dry",
    tree: Optional[StringTree] = None,
    tree_material: str = "steel_dry",
) -> StringBreakResult:
    """
    Compute break angle, downforce, and tuning stability for a single string.

    Args:
        post:                   TunerPost specification
        wrap_count:             Number of wraps around the post below the hole
        tension_N:              Open string tension at pitch (N)
        headstock_angle_deg:    Headstock tilt angle (0 for straight)
        fretboard_thickness_mm: Fretboard thickness at nut
        headstock_relief_drop_mm: Headstock drop below neck plane (straight only)
        nut_material:           Key into NUT_FRICTION
        tree:                   StringTree if present for this string
        tree_material:          Friction material of string tree

    Returns:
        StringBreakResult
    """
    # Headstock depth at post x-position
    depth = headstock_depth_at(
        post.x_from_nut_mm,
        headstock_angle_deg,
        fretboard_thickness_mm,
        headstock_relief_drop_mm,
    )

    # Hole y-position (below nut exit)
    y_hole = depth - post.h_hole_above_headstock_mm

    # Anchor y-position after wrapping
    y_post_anchor = anchor_y(y_hole, wrap_count, post.string_dia_mm)

    # Direct nut-to-post angle (ignoring tree)
    theta_post = break_angle_deg(post.x_from_nut_mm, y_post_anchor)

    # Determine effective nut break angle
    notes: List[str] = []

    if tree is not None:
        # Nut sees nut-to-tree angle
        theta_nut = break_angle_deg(tree.x_from_nut_mm, tree.y_below_nut_mm)
        # Tree-to-post angle (additional friction contact)
        dx_tree_to_post = post.x_from_nut_mm - tree.x_from_nut_mm
        dy_tree_to_post = y_post_anchor - tree.y_below_nut_mm
        theta_tree_contact = math.degrees(math.atan2(dy_tree_to_post, dx_tree_to_post))
        has_tree = True

        # Friction analysis
        mu_nut  = NUT_FRICTION.get(nut_material, 0.10)
        mu_tree = NUT_FRICTION.get(tree_material, 0.25)
        lag_nut  = tuning_lag_cents(mu_nut,  theta_nut)
        lag_tree = tuning_lag_cents(mu_tree, abs(theta_tree_contact))
        lag_total = lag_nut + lag_tree

        notes.append(
            f"String tree at x={tree.x_from_nut_mm:.0f}mm, "
            f"depth={tree.y_below_nut_mm:.1f}mm. "
            f"Nut sees only the nut-to-tree segment ({theta_nut:.1f}°). "
            f"Tree-to-post adds a second friction contact ({abs(theta_tree_contact):.1f}°). "
            f"Tree material ({tree_material}) friction compounds nut friction."
        )
    else:
        theta_nut = theta_post
        theta_tree_contact = 0.0
        has_tree = False

        mu_nut = NUT_FRICTION.get(nut_material, 0.10)
        lag_nut   = tuning_lag_cents(mu_nut, theta_nut)
        lag_tree  = 0.0
        lag_total = lag_nut

    # Downforce
    F_perp = downforce_N(tension_N, theta_nut)

    # Status and flags
    if theta_nut < ANGLE_BUZZ_RISK_DEG:
        status = "SHALLOW"
        notes.append(
            f"Break angle {theta_nut:.1f}° is below {ANGLE_BUZZ_RISK_DEG}°. "
            f"Risk of string lifting from nut slot — open-string buzz behind nut. "
            f"Test: damp strings behind nut; if buzz disappears, angle is the cause. "
            f"Fix: lower post (reduce h_hole), add more wraps, or install string tree."
        )
    elif theta_nut < ANGLE_MARGINAL_MIN_DEG:
        status = "MARGINAL"
        notes.append(
            f"Break angle {theta_nut:.1f}° is marginal. Acceptable for wound strings "
            f"but risky for plain trebles. Consider adding wraps or a string tree."
        )
    elif theta_nut > ANGLE_STEEP_MAX_DEG:
        if has_tree:
            status = "BINDING_RISK"
            notes.append(
                f"Break angle {theta_nut:.1f}° plus tree contact ({abs(theta_tree_contact):.1f}° "
                f"at tree) creates high friction. String may bind and 'ping' on tuning. "
                f"Total tuning lag ≈ {lag_total:.1f}¢. "
                f"Use low-friction tree material (GraphTech, roller) or reposition tree "
                f"further from the nut to reduce the nut break angle."
            )
        else:
            status = "STEEP"
            notes.append(
                f"Break angle {theta_nut:.1f}° exceeds {ANGLE_STEEP_MAX_DEG}° maximum. "
                f"High friction ({lag_nut:.1f}¢ tuning lag). String may stick in nut slot. "
                f"For non-locking nuts, lubricate slot or reduce angle."
            )
    else:
        status = "OK"

    return StringBreakResult(
        string_name=post.string_name,
        string_dia_mm=post.string_dia_mm,
        x_anchor_mm=tree.x_from_nut_mm if tree else post.x_from_nut_mm,
        y_anchor_mm=tree.y_below_nut_mm if tree else y_post_anchor,
        x_post_mm=post.x_from_nut_mm,
        y_post_mm=y_post_anchor,
        theta_nut_deg=round(theta_nut, 2),
        theta_post_deg=round(theta_post, 2),
        has_tree=has_tree,
        tree_contact_angle_deg=round(theta_tree_contact, 2),
        tension_N=tension_N,
        downforce_N=round(F_perp, 2),
        nut_material=nut_material,
        tuning_lag_nut_cents=round(lag_nut, 1),
        tuning_lag_tree_cents=round(lag_tree, 1),
        tuning_lag_total_cents=round(lag_total, 1),
        status=status,
        notes=notes,
    )


def analyze_headstock(
    posts: List[TunerPost],
    wrap_counts: List[int],
    tensions_N: List[float],
    headstock_angle_deg: float = 0.0,
    fretboard_thickness_mm: float = 6.0,
    headstock_relief_drop_mm: float = 8.0,
    nut_material: str = "bone_dry",
    trees: Optional[List[Optional[StringTree]]] = None,
    tree_material: str = "steel_dry",
) -> HeadstockBreakSpec:
    """
    Analyze all strings on a headstock.

    Args:
        posts:                   List of TunerPost (one per string)
        wrap_counts:             List of wrap counts (one per string)
        tensions_N:              List of string tensions (one per string)
        headstock_angle_deg:     Headstock tilt (0 for Fender-style)
        fretboard_thickness_mm:  Fretboard thickness at nut
        headstock_relief_drop_mm: Drop of headstock surface (for flat headstocks)
        nut_material:            Nut material key
        trees:                   Optional list of StringTree per string (None = no tree)
        tree_material:           String tree material key

    Returns:
        HeadstockBreakSpec with all string results and summary flags.
    """
    if trees is None:
        trees = [None] * len(posts)

    headstock_type = "angled" if headstock_angle_deg > 0 else "straight"

    string_results = []
    for post, wraps, tension, tree in zip(posts, wrap_counts, tensions_N, trees):
        result = analyze_string(
            post=post,
            wrap_count=wraps,
            tension_N=tension,
            headstock_angle_deg=headstock_angle_deg,
            fretboard_thickness_mm=fretboard_thickness_mm,
            headstock_relief_drop_mm=headstock_relief_drop_mm,
            nut_material=nut_material,
            tree=tree,
            tree_material=tree_material,
        )
        string_results.append(result)

    any_shallow      = any(r.status == "SHALLOW" for r in string_results)
    any_binding_risk = any(r.status in ("BINDING_RISK", "STEEP") for r in string_results)

    # Tree recommendation for flat headstocks
    tree_rec = None
    if headstock_type == "straight":
        need_tree = [r for r in string_results
                     if r.status == "SHALLOW" and not r.has_tree]
        if need_tree:
            names = ", ".join(r.string_name for r in need_tree)
            tree_rec = (
                f"Strings {names} have insufficient break angle. "
                f"Options: (1) Install string tree between nut and tuner for these "
                f"strings — position tree so break angle reaches 4-7°. "
                f"(2) Use staggered tuners with lower post holes for treble strings. "
                f"Use low-friction tree material (GraphTech, roller) to minimize "
                f"the additional friction contact the tree introduces."
            )

    return HeadstockBreakSpec(
        headstock_angle_deg=headstock_angle_deg,
        headstock_type=headstock_type,
        fretboard_thickness_mm=fretboard_thickness_mm,
        nut_material=nut_material,
        strings=string_results,
        any_shallow=any_shallow,
        any_binding_risk=any_binding_risk,
        tree_recommendation=tree_rec,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Standard presets
# ─────────────────────────────────────────────────────────────────────────────

def preset_fender_strat(
    nut_material: str = "bone_dry",
    use_trees: bool = True,
    wrap_counts: Optional[List[int]] = None,
) -> HeadstockBreakSpec:
    """
    Standard Fender Stratocaster headstock geometry.

    Straight headstock (0°), non-staggered posts, B and High e use
    string tree at approximately 40mm from nut, 7mm below nut exit.
    """
    wraps = wrap_counts or [2, 2, 2, 2, 3, 3]

    posts = [
        TunerPost(x_from_nut_mm=45,  h_hole_above_headstock_mm=10, string_name="Low E",  string_dia_mm=1.346),
        TunerPost(x_from_nut_mm=55,  h_hole_above_headstock_mm=9,  string_name="A",      string_dia_mm=1.067),
        TunerPost(x_from_nut_mm=65,  h_hole_above_headstock_mm=8,  string_name="D",      string_dia_mm=0.813),
        TunerPost(x_from_nut_mm=75,  h_hole_above_headstock_mm=7,  string_name="G",      string_dia_mm=0.610),
        TunerPost(x_from_nut_mm=85,  h_hole_above_headstock_mm=6,  string_name="B",      string_dia_mm=0.406),
        TunerPost(x_from_nut_mm=95,  h_hole_above_headstock_mm=5,  string_name="High e", string_dia_mm=0.305),
    ]

    tensions = [84.4, 78.7, 72.6, 63.1, 49.0, 71.7]  # N, light gauge

    tree = StringTree(x_from_nut_mm=40, y_below_nut_mm=7.0,
                      applies_to=["B", "High e"], material="steel_dry")
    trees = [None, None, None, None,
             tree if use_trees else None,
             tree if use_trees else None]

    return analyze_headstock(
        posts=posts,
        wrap_counts=wraps,
        tensions_N=tensions,
        headstock_angle_deg=0.0,
        fretboard_thickness_mm=5.5,
        headstock_relief_drop_mm=8.5,
        nut_material=nut_material,
        trees=trees,
        tree_material="steel_dry",
    )


def preset_gibson_lp(
    nut_material: str = "bone_dry",
    headstock_angle_deg: float = 17.0,
    wrap_counts: Optional[List[int]] = None,
) -> HeadstockBreakSpec:
    """
    Standard Gibson Les Paul headstock geometry.

    Angled headstock (~17°), uniform post heights.
    Break angle comes from headstock tilt — no trees needed.
    """
    wraps = wrap_counts or [2, 2, 2, 2, 2, 2]

    posts = [
        TunerPost(x_from_nut_mm=50,  h_hole_above_headstock_mm=8, string_name="Low E",  string_dia_mm=1.346),
        TunerPost(x_from_nut_mm=60,  h_hole_above_headstock_mm=8, string_name="A",      string_dia_mm=1.067),
        TunerPost(x_from_nut_mm=70,  h_hole_above_headstock_mm=8, string_name="D",      string_dia_mm=0.813),
        TunerPost(x_from_nut_mm=80,  h_hole_above_headstock_mm=8, string_name="G",      string_dia_mm=0.610),
        TunerPost(x_from_nut_mm=90,  h_hole_above_headstock_mm=8, string_name="B",      string_dia_mm=0.406),
        TunerPost(x_from_nut_mm=100, h_hole_above_headstock_mm=8, string_name="High e", string_dia_mm=0.305),
    ]

    tensions = [84.4, 78.7, 72.6, 63.1, 49.0, 71.7]

    return analyze_headstock(
        posts=posts,
        wrap_counts=wraps,
        tensions_N=tensions,
        headstock_angle_deg=headstock_angle_deg,
        fretboard_thickness_mm=6.0,
        headstock_relief_drop_mm=0.0,  # angled — relief not used
        nut_material=nut_material,
    )


def preset_martin_acoustic(
    nut_material: str = "bone_dry",
    headstock_angle_deg: float = 14.0,
    wrap_counts: Optional[List[int]] = None,
) -> HeadstockBreakSpec:
    """
    Martin-style acoustic headstock.

    Angled headstock (~14°), slotted headstock tuners.
    Posts are lower to headstock (slotted peghead).
    """
    wraps = wrap_counts or [3, 3, 3, 3, 3, 3]

    posts = [
        TunerPost(x_from_nut_mm=45,  h_hole_above_headstock_mm=6, string_name="Low E",  string_dia_mm=1.346),
        TunerPost(x_from_nut_mm=55,  h_hole_above_headstock_mm=6, string_name="A",      string_dia_mm=1.067),
        TunerPost(x_from_nut_mm=65,  h_hole_above_headstock_mm=6, string_name="D",      string_dia_mm=0.813),
        TunerPost(x_from_nut_mm=75,  h_hole_above_headstock_mm=6, string_name="G",      string_dia_mm=0.610),
        TunerPost(x_from_nut_mm=85,  h_hole_above_headstock_mm=6, string_name="B",      string_dia_mm=0.406),
        TunerPost(x_from_nut_mm=95,  h_hole_above_headstock_mm=6, string_name="High e", string_dia_mm=0.305),
    ]

    tensions = [84.4, 78.7, 72.6, 63.1, 49.0, 71.7]

    return analyze_headstock(
        posts=posts,
        wrap_counts=wraps,
        tensions_N=tensions,
        headstock_angle_deg=headstock_angle_deg,
        fretboard_thickness_mm=6.0,
        headstock_relief_drop_mm=0.0,
        nut_material=nut_material,
    )


def preset_fender_staggered(
    nut_material: str = "bone_dry",
    wrap_counts: Optional[List[int]] = None,
) -> HeadstockBreakSpec:
    """
    Fender with staggered tuners (e.g. Gotoh SD91 staggered).

    Staggered posts have progressively lower holes for treble strings,
    eliminating the need for string trees on most installations.
    """
    wraps = wrap_counts or [2, 2, 2, 2, 2, 2]

    # Staggered: hole heights decrease from bass to treble
    posts = [
        TunerPost(x_from_nut_mm=45,  h_hole_above_headstock_mm=11, string_name="Low E",  string_dia_mm=1.346),
        TunerPost(x_from_nut_mm=55,  h_hole_above_headstock_mm=10, string_name="A",      string_dia_mm=1.067),
        TunerPost(x_from_nut_mm=65,  h_hole_above_headstock_mm=8,  string_name="D",      string_dia_mm=0.813),
        TunerPost(x_from_nut_mm=75,  h_hole_above_headstock_mm=6,  string_name="G",      string_dia_mm=0.610),
        TunerPost(x_from_nut_mm=85,  h_hole_above_headstock_mm=4,  string_name="B",      string_dia_mm=0.406),
        TunerPost(x_from_nut_mm=95,  h_hole_above_headstock_mm=3,  string_name="High e", string_dia_mm=0.305),
    ]

    tensions = [84.4, 78.7, 72.6, 63.1, 49.0, 71.7]

    return analyze_headstock(
        posts=posts,
        wrap_counts=wraps,
        tensions_N=tensions,
        headstock_angle_deg=0.0,
        fretboard_thickness_mm=5.5,
        headstock_relief_drop_mm=8.5,
        nut_material=nut_material,
        trees=None,   # staggered posts eliminate tree requirement
    )
