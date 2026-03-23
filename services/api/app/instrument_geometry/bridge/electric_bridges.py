"""
electric_bridges.py
===================
Electric guitar bridge specifications — dimensions, post/stud geometry,
body routing, and saddle parameters for all common electric bridge types.

Coverage
--------
Fender family:
  - Stratocaster vintage 6-point synchronised tremolo
  - Stratocaster 2-point tremolo (American Series)
  - Telecaster 3-saddle ashtray bridge
  - Telecaster 6-saddle bridge
  - Jazzmaster floating tremolo

Gibson family:
  - ABR-1 Tune-o-matic
  - Nashville Tune-o-matic
  - Wraparound / stopbar
  - Stop tailpiece (pairs with TOM)

Vibrato / tailpiece:
  - Bigsby B5

Note: Floyd Rose Original is in floyd_rose_tremolo.py (separate module,
full schematic-derived dimensions). This module handles the remaining
electric bridge types using manufacturer published specs and industry-standard
measurements.

Source honesty
--------------
EXACT: Post/stud spacing values derived from published Fender and Gibson specs
  and widely verified aftermarket part fitment.
EMPIRICAL: Saddle radius values follow manufacturer specs; body routing
  clearances include standard shop tolerances.
APPROXIMATED: Jazzmaster and Bigsby mounting dimensions — these vary by
  body and installation; values given are nominal starting points.

All dimensions in mm unless noted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


# ─── Base dataclass ───────────────────────────────────────────────────────────

@dataclass
class ElectricBridgeSpec:
    """
    Complete specification for a single electric guitar bridge type.
    All linear dimensions in mm, angles in degrees.
    """
    bridge_id:         str
    full_name:         str
    family:            str     # 'fender' | 'gibson' | 'vibrato'
    bridge_class:      str     # 'fixed' | 'tremolo' | 'tailpiece' | 'floating'

    # String geometry
    string_spacing_mm: float           # E-to-e at saddles
    string_count:      int = 6

    # Post / stud mounting
    post_spacing_mm:   Optional[float] = None   # CL-to-CL of posts/studs
    post_count:        int = 2
    post_dia_mm:       Optional[float] = None   # post shank OD
    post_hole_dia_mm:  Optional[float] = None   # body hole for insert/press-fit
    post_hole_depth_mm: Optional[float] = None
    insert_thread:     Optional[str]   = None   # e.g. 'M8x0.75', '10-32'
    insert_od_mm:      Optional[float] = None

    # Screw mounting (Tele, vintage Strat top-load)
    screw_count:       int = 0
    screw_dia_mm:      Optional[float] = None
    screw_spacing_mm:  Optional[float] = None   # between adjacent screws
    screw_span_mm:     Optional[float] = None   # outermost screw CL span

    # Plate / body dimensions
    plate_length_mm:   Optional[float] = None
    plate_width_mm:    Optional[float] = None
    plate_thickness_mm: Optional[float] = None

    # Body routing / recess
    body_route_width_mm:  Optional[float] = None   # string cavity width
    body_route_depth_mm:  Optional[float] = None   # string cavity depth
    body_route_length_mm: Optional[float] = None
    body_recess_depth_mm: Optional[float] = None   # plate recess (surface mount)

    # Saddle geometry
    saddle_radius_mm:  Optional[float] = None       # None = flat or N/A
    saddle_type:       str = "individual"           # 'individual' | 'barrel' | 'rail' | 'bar'
    saddle_count:      int = 6
    saddle_hex_mm:     Optional[float] = None       # hex key for height adj

    # Tremolo / inertia block
    block_length_mm:   Optional[float] = None
    block_width_mm:    Optional[float] = None

    # Pairing
    pairs_with:        Optional[str] = None    # e.g. 'stoptail' pairs with TOM

    source_honesty:    str = "EMPIRICAL"       # source confidence
    notes:             str = ""


# ─── Bridge database ──────────────────────────────────────────────────────────

ELECTRIC_BRIDGES: Dict[str, ElectricBridgeSpec] = {

    # ── Fender Stratocaster ───────────────────────────────────────────────────

    "strat_vintage_6pt": ElectricBridgeSpec(
        bridge_id="strat_vintage_6pt",
        full_name="Fender Stratocaster vintage 6-point synchronised tremolo",
        family="fender", bridge_class="tremolo",
        string_spacing_mm=52.5,
        # 6 mounting screws on 11/32" (8.89mm) spacing
        # Outer screw CL to CL: 5 × 11.1 = 55.5mm (often cited as 2-3/16" = 55.56mm)
        screw_count=6,
        screw_dia_mm=3.0,           # #6-32 machine screw
        screw_spacing_mm=11.1,      # 7/16" nominal between adjacent screws
        screw_span_mm=55.56,        # 2-3/16" outermost screw span (EXACT: 2.1875" × 25.4)
        plate_length_mm=82.0,       # approximate plate front-to-back
        plate_width_mm=91.5,
        body_route_width_mm=57.0,   # string block cavity
        body_route_depth_mm=46.0,   # standard block
        body_route_length_mm=84.0,
        block_length_mm=55.0,       # standard inertia block
        block_width_mm=55.0,
        saddle_radius_mm=184.2,     # 7-1/4" vintage (7.25 × 25.4 = 184.15mm)
        saddle_type="bent_steel",
        saddle_hex_mm=1.5,
        source_honesty="EXACT (screw span); EMPIRICAL (routing)",
        notes=(
            "6 screws on 2-3/16\" span. Vintage radius 7.25\" (184mm). "
            "Modern reissues often use 9.5\" (241mm) saddles. "
            "Routing depth depends on block length — short blocks (38mm) "
            "for chambered bodies. Spring claw in rear cavity."
        ),
    ),

    "strat_2pt": ElectricBridgeSpec(
        bridge_id="strat_2pt",
        full_name="Fender American Series 2-point synchronised tremolo",
        family="fender", bridge_class="tremolo",
        string_spacing_mm=52.5,
        post_spacing_mm=55.56,      # 2-3/16" — same as vintage 6-point
        post_count=2,
        post_dia_mm=10.8,           # pivot post OD
        post_hole_dia_mm=10.8,
        post_hole_depth_mm=18.0,
        insert_thread="10-32",
        plate_length_mm=82.0,
        plate_width_mm=91.5,
        body_route_width_mm=57.0,
        body_route_depth_mm=46.0,
        body_route_length_mm=84.0,
        block_length_mm=55.0,
        block_width_mm=55.0,
        saddle_radius_mm=241.3,     # 9.5" standard on American Series
        saddle_type="bent_steel",
        saddle_hex_mm=1.5,
        source_honesty="EXACT (post spacing); EMPIRICAL (routing)",
        notes=(
            "2 knife-edge posts on same 2-3/16\" spacing as vintage 6-point. "
            "Better tuning stability than 6-point. "
            "9.5\" radius (241mm) standard. Routing pocket identical to vintage."
        ),
    ),

    "strat_hardtail": ElectricBridgeSpec(
        bridge_id="strat_hardtail",
        full_name="Fender Stratocaster hardtail bridge",
        family="fender", bridge_class="fixed",
        string_spacing_mm=52.5,
        screw_count=6,
        screw_dia_mm=3.0,
        screw_spacing_mm=11.1,
        screw_span_mm=55.56,        # same footprint as tremolo
        plate_length_mm=65.0,
        plate_width_mm=91.5,
        body_route_width_mm=None,   # no routing — top-load screws only
        body_route_depth_mm=None,
        saddle_radius_mm=241.3,
        saddle_type="barrel",
        saddle_hex_mm=1.5,
        notes=(
            "Same 6-screw footprint as tremolo. No body routing required — "
            "strings load through ferrules in back of body. "
            "Saddle type: barrel or bent steel depending on vintage."
        ),
    ),

    # ── Telecaster ────────────────────────────────────────────────────────────

    "telecaster_ashtray": ElectricBridgeSpec(
        bridge_id="telecaster_ashtray",
        full_name="Fender Telecaster 3-saddle ashtray bridge",
        family="fender", bridge_class="fixed",
        string_spacing_mm=52.5,
        screw_count=4,
        screw_dia_mm=3.0,
        screw_span_mm=54.0,         # outer mounting hole span (E-to-E approx)
        plate_length_mm=63.5,       # 2.5"
        plate_width_mm=47.6,        # 1-7/8"
        body_recess_depth_mm=3.2,   # plate sits in slight body ledge
        saddle_radius_mm=None,      # flat — barrel saddles not radiused
        saddle_type="barrel",
        saddle_count=3,
        saddle_hex_mm=2.5,
        source_honesty="EXACT (plate dims from Fender specs)",
        notes=(
            "3 barrel saddles, 2 strings per saddle. No individual intonation "
            "per string — pairs share a saddle. Compensated saddles (angled barrel) "
            "available for better intonation. Plate mounts in shallow body recess."
        ),
    ),

    "telecaster_6saddle": ElectricBridgeSpec(
        bridge_id="telecaster_6saddle",
        full_name="Telecaster 6-saddle bridge",
        family="fender", bridge_class="fixed",
        string_spacing_mm=52.5,
        screw_count=4,
        screw_dia_mm=3.0,
        screw_span_mm=54.0,
        plate_length_mm=63.5,
        plate_width_mm=47.6,
        body_recess_depth_mm=3.2,
        saddle_radius_mm=241.3,     # 9.5" standard
        saddle_type="individual",
        saddle_count=6,
        saddle_hex_mm=1.5,
        notes=(
            "Identical plate footprint to 3-saddle ashtray. Individual "
            "intonation and height adjustment per string. Drop-in replacement "
            "for original ashtray on standard Tele routing."
        ),
    ),

    # ── Jazzmaster / Jaguar ───────────────────────────────────────────────────

    "jazzmaster": ElectricBridgeSpec(
        bridge_id="jazzmaster",
        full_name="Fender Jazzmaster floating tremolo and bridge",
        family="fender", bridge_class="floating",
        string_spacing_mm=52.5,
        # Bridge rocks on 2 posts — not anchored screws
        post_spacing_mm=71.5,       # approximate bridge post CL span
        post_count=2,
        post_dia_mm=6.0,
        post_hole_dia_mm=6.5,
        # Tremolo unit separate from bridge
        saddle_radius_mm=241.3,
        saddle_type="rail",
        saddle_count=6,
        source_honesty="EMPIRICAL (floating post spacing varies by body)",
        notes=(
            "Bridge floats freely on 2 posts — rocks with string vibration. "
            "Separate tremolo tailpiece at rear. Common buzzing if radius "
            "mismatch or light strings. Lock the tremolo for hardtail feel."
        ),
    ),

    # ── Gibson / Tune-o-matic family ──────────────────────────────────────────

    "tom_abr1": ElectricBridgeSpec(
        bridge_id="tom_abr1",
        full_name="Gibson ABR-1 Tune-o-matic bridge",
        family="gibson", bridge_class="fixed",
        string_spacing_mm=52.0,
        post_spacing_mm=82.55,      # 3-1/4" (3.25" × 25.4 = 82.55mm) EXACT
        post_count=2,
        post_dia_mm=6.35,           # 1/4" post shank
        post_hole_dia_mm=6.5,
        post_hole_depth_mm=12.0,
        insert_thread="M8x0.75",    # fine-pitch Gibson thread
        insert_od_mm=12.7,          # 1/2" knurled insert
        saddle_radius_mm=304.8,     # 12" (12 × 25.4 = 304.8mm) EXACT
        saddle_type="individual",
        saddle_count=6,
        saddle_hex_mm=None,         # slot-head screw adjustment
        pairs_with="stoptail",
        source_honesty="EXACT (post spacing, radius); EMPIRICAL (hole depth)",
        notes=(
            "Original Gibson TOM. M8×0.75 fine-thread inserts — do not "
            "interchange with Nashville (M8×1.0). No saddle retaining wire — "
            "saddles can fall out if strings removed. 12\" radius. "
            "Post holes on 3-1/4\" (82.55mm) span."
        ),
    ),

    "tom_nashville": ElectricBridgeSpec(
        bridge_id="tom_nashville",
        full_name="Gibson Nashville Tune-o-matic bridge",
        family="gibson", bridge_class="fixed",
        string_spacing_mm=52.0,
        post_spacing_mm=82.55,      # same as ABR-1 — EXACT
        post_count=2,
        post_dia_mm=7.94,           # 5/16" post shank
        post_hole_dia_mm=10.5,
        post_hole_depth_mm=14.0,
        insert_thread="M8x1.0",     # coarser than ABR-1 — NOT interchangeable
        insert_od_mm=14.3,          # wider insert than ABR-1
        saddle_radius_mm=304.8,     # 12" — same as ABR-1
        saddle_type="individual",
        saddle_count=6,
        pairs_with="stoptail",
        source_honesty="EXACT (post spacing, thread); EMPIRICAL (insert OD)",
        notes=(
            "Wider collar insert than ABR-1. M8×1.0 coarse thread — "
            "incompatible with ABR-1 M8×0.75 inserts. Integral saddle "
            "retaining wire. Used on most post-1970s Gibson electrics. "
            "Same post spacing as ABR-1 (3-1/4\")."
        ),
    ),

    "tom_epiphone": ElectricBridgeSpec(
        bridge_id="tom_epiphone",
        full_name="Epiphone / Asian TOM (metric M8×1.25)",
        family="gibson", bridge_class="fixed",
        string_spacing_mm=52.0,
        post_spacing_mm=82.55,
        post_count=2,
        post_dia_mm=8.0,
        post_hole_dia_mm=10.5,
        insert_thread="M8x1.25",    # metric standard — different from Gibson
        insert_od_mm=11.0,
        saddle_radius_mm=304.8,
        saddle_type="individual",
        saddle_count=6,
        pairs_with="stoptail",
        source_honesty="EMPIRICAL",
        notes=(
            "M8×1.25 metric thread — standard metric pitch. NOT interchangeable "
            "with Gibson ABR-1 (M8×0.75) or Nashville (M8×1.0). "
            "Common on Epiphone, Harley Benton, and Asian-market instruments. "
            "Same post spacing as Gibson (82.55mm)."
        ),
    ),

    "wraparound": ElectricBridgeSpec(
        bridge_id="wraparound",
        full_name="Gibson wraparound bridge / stopbar",
        family="gibson", bridge_class="fixed",
        string_spacing_mm=52.0,
        post_spacing_mm=82.55,      # same as TOM — EXACT
        post_count=2,
        post_dia_mm=6.35,
        post_hole_dia_mm=6.5,
        insert_thread="M8x0.75",
        insert_od_mm=12.7,
        saddle_radius_mm=None,      # bar contour, not individual saddles
        saddle_type="bar",
        saddle_count=1,             # one bar for all strings
        source_honesty="EXACT (post spacing = TOM spacing)",
        notes=(
            "Strings wrap under and over the bar — no separate tailpiece. "
            "Limited individual intonation: bar has slight compensation angle only. "
            "Used on Les Paul Junior, SG Junior, Melody Maker, Les Paul Special. "
            "Compensated wraparounds available with notched saddle slots."
        ),
    ),

    "stoptail": ElectricBridgeSpec(
        bridge_id="stoptail",
        full_name="Gibson stop tailpiece",
        family="gibson", bridge_class="tailpiece",
        string_spacing_mm=52.0,
        post_spacing_mm=82.55,      # same as TOM — EXACT
        post_count=2,
        post_dia_mm=6.35,
        post_hole_dia_mm=6.5,
        insert_thread="M8x0.75",
        insert_od_mm=12.7,
        saddle_radius_mm=None,      # no saddles — tailpiece only
        saddle_type="none",
        saddle_count=0,
        pairs_with="tom_abr1",
        source_honesty="EXACT (post spacing)",
        notes=(
            "String anchor only — no intonation function. "
            "Always pairs with ABR-1 or Nashville TOM. "
            "Same post spacing and insert as ABR-1 (M8×0.75). "
            "Height affects break angle and tone. Lower = stiffer, more attack."
        ),
    ),

    # ── Vibrato / tailpiece ───────────────────────────────────────────────────

    "bigsby_b5": ElectricBridgeSpec(
        bridge_id="bigsby_b5",
        full_name="Bigsby B5 vibrato tailpiece (solid body)",
        family="vibrato", bridge_class="tremolo",
        string_spacing_mm=52.5,
        screw_count=3,              # 3 mounting screws on rear plate
        screw_dia_mm=4.0,
        screw_span_mm=76.2,         # 3" nominal mounting span
        plate_width_mm=90.0,
        plate_length_mm=70.0,       # approximate
        saddle_radius_mm=None,      # no saddles — pairs with separate bridge
        saddle_type="none",
        saddle_count=0,
        pairs_with="tom_abr1",      # or roller bridge
        source_honesty="EMPIRICAL (mounting dimensions vary by model year)",
        notes=(
            "Surface-mount vibrato — no body routing. "
            "Pairs with TOM, Tele bridge, or roller bridge. "
            "B5 = solid body flat-top. B6 = semi-hollow archtop. "
            "B7 = 7-string. B12 = 12-string. "
            "Low-throw vibrato — subtle pitch change compared to Floyd Rose."
        ),
    ),

    "bigsby_b3": ElectricBridgeSpec(
        bridge_id="bigsby_b3",
        full_name="Bigsby B3 vibrato tailpiece (carved top)",
        family="vibrato", bridge_class="tremolo",
        string_spacing_mm=52.5,
        screw_count=2,
        screw_dia_mm=4.0,
        screw_span_mm=57.0,
        plate_width_mm=85.0,
        source_honesty="EMPIRICAL",
        notes="For carved-top archtops (ES-335 style, 335-depth). Mounts to body surface.",
    ),

}


# ─── Accessor functions ───────────────────────────────────────────────────────

def list_electric_bridges(family: Optional[str] = None) -> List[str]:
    """Return list of bridge IDs, optionally filtered by family."""
    if family:
        return [k for k, v in ELECTRIC_BRIDGES.items() if v.family == family]
    return list(ELECTRIC_BRIDGES.keys())


def get_bridge_spec(bridge_id: str) -> ElectricBridgeSpec:
    """Return the spec for a bridge by ID. Raises ValueError if not found."""
    if bridge_id not in ELECTRIC_BRIDGES:
        raise ValueError(
            f"Unknown bridge '{bridge_id}'. "
            f"Available: {sorted(ELECTRIC_BRIDGES.keys())}"
        )
    return ELECTRIC_BRIDGES[bridge_id]


def get_bridge_preset_dict(bridge_id: str, scale_length_mm: float = 647.7) -> dict:
    """
    Return a bridge preset dict compatible with the FamilyPreset schema
    in bridge_presets_router.py, plus full electric-specific fields.
    """
    spec = get_bridge_spec(bridge_id)

    # Compensation estimates for electric saddle bridges (EMPIRICAL)
    if spec.saddle_radius_mm is not None and spec.saddle_count == 6:
        comp_treble = 2.0
        comp_bass   = 3.5
    else:
        comp_treble = comp_bass = 0.0

    return {
        "id":           spec.bridge_id,
        "label":        spec.full_name,
        "bridge_class": spec.bridge_class,
        "family":       spec.family,
        "scaleLength":  scale_length_mm,
        "stringSpread": spec.string_spacing_mm,
        "compTreble":   comp_treble,
        "compBass":     comp_bass,
        "saddle_radius_mm": spec.saddle_radius_mm,
        "mounting": {
            "post_spacing_mm": spec.post_spacing_mm,
            "post_count":      spec.post_count,
            "post_dia_mm":     spec.post_dia_mm,
            "post_hole_dia_mm": spec.post_hole_dia_mm,
            "insert_thread":   spec.insert_thread,
            "screw_count":     spec.screw_count,
            "screw_span_mm":   spec.screw_span_mm,
        },
        "routing": {
            "width_mm":  spec.body_route_width_mm,
            "depth_mm":  spec.body_route_depth_mm,
            "length_mm": spec.body_route_length_mm,
            "recess_mm": spec.body_recess_depth_mm,
        },
        "saddle": {
            "type":    spec.saddle_type,
            "count":   spec.saddle_count,
            "radius_mm": spec.saddle_radius_mm,
            "hex_mm":  spec.saddle_hex_mm,
        },
        "pairs_with":    spec.pairs_with,
        "source":        spec.source_honesty,
        "notes":         spec.notes,
    }


def post_hole_positions(bridge_id: str) -> Optional[Tuple[float, float]]:
    """
    Return (bass_x, treble_x) post CL positions relative to string span center.

    For TOM/wraparound/stoptail, the posts are symmetric about the string center.
    For Strat-style, posts align with the screw span.

    Returns None for surface-mount bridges with no post holes.
    """
    spec = get_bridge_spec(bridge_id)
    if spec.post_spacing_mm is None:
        return None
    half = spec.post_spacing_mm / 2.0
    return (-half, +half)


def saddle_string_positions(
    bridge_id: str,
    reference_x: float = 0.0,
) -> List[Tuple[float, str]]:
    """
    Return list of (x_from_center_mm, string_name) for each string.
    X is lateral (bass negative, treble positive).
    """
    spec = get_bridge_spec(bridge_id)
    n = spec.string_count
    span = spec.string_spacing_mm
    half = span / 2.0
    spacing = span / (n - 1) if n > 1 else 0.0
    names = ["Low E", "A", "D", "G", "B", "High e"][:n]
    return [
        (reference_x - half + i * spacing, names[i])
        for i in range(n)
    ]


def compatibility_check(bridge_id: str, fingerboard_radius_mm: float) -> str:
    """Advisory on saddle radius vs fingerboard radius."""
    spec = get_bridge_spec(bridge_id)
    if spec.saddle_radius_mm is None:
        return f"{spec.full_name} has no individual saddles — radius N/A."
    diff = fingerboard_radius_mm - spec.saddle_radius_mm
    if abs(diff) < 8:
        return (f"Good match: fingerboard {fingerboard_radius_mm:.0f}mm ≈ "
                f"saddle {spec.saddle_radius_mm:.0f}mm.")
    elif diff < 0:
        return (f"Fingerboard {fingerboard_radius_mm:.0f}mm flatter than saddle "
                f"{spec.saddle_radius_mm:.0f}mm — outer strings sit high at saddle.")
    else:
        return (f"Fingerboard {fingerboard_radius_mm:.0f}mm more curved than saddle "
                f"{spec.saddle_radius_mm:.0f}mm — center strings may fret out under bends.")


# ─── Thread incompatibility guard ─────────────────────────────────────────────

THREAD_GROUPS = {
    "M8x0.75":  ["tom_abr1", "wraparound", "stoptail"],
    "M8x1.0":   ["tom_nashville"],
    "M8x1.25":  ["tom_epiphone"],
    "10-32":    ["strat_2pt"],
    "M7x0.5":   ["floyd_rose_original"],   # see floyd_rose_tremolo.py
}


def thread_compatibility(bridge_id_a: str, bridge_id_b: str) -> str:
    """Check if two bridges share the same insert thread (interchangeable posts)."""
    spec_a = get_bridge_spec(bridge_id_a)
    spec_b = get_bridge_spec(bridge_id_b)
    ta, tb = spec_a.insert_thread, spec_b.insert_thread
    if ta is None or tb is None:
        return "One or both bridges do not use threaded inserts."
    if ta == tb:
        return f"Compatible: both use {ta}."
    return (f"INCOMPATIBLE: {bridge_id_a} uses {ta}, "
            f"{bridge_id_b} uses {tb}. Do not interchange inserts.")


# ─── Summary report ───────────────────────────────────────────────────────────

def bridge_summary() -> str:
    lines = [
        "Electric Guitar Bridge Specifications",
        "=" * 60,
        f"{'ID':<25} {'Post span':>10} {'String span':>12} {'Radius':>9}  Thread",
        "─" * 70,
    ]
    for bid, spec in ELECTRIC_BRIDGES.items():
        post   = f"{spec.post_spacing_mm:.1f}" if spec.post_spacing_mm else "—"
        span   = f"{spec.string_spacing_mm:.1f}"
        radius = f"{spec.saddle_radius_mm:.0f}" if spec.saddle_radius_mm else "—"
        thread = spec.insert_thread or ("screws" if spec.screw_count else "—")
        lines.append(f"  {bid:<23} {post:>10} {span:>12} {radius:>9}  {thread}")
    return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(bridge_summary())
    print()
    print("Thread compatibility: ABR-1 vs Nashville:")
    print(" ", thread_compatibility("tom_abr1", "tom_nashville"))
    print("Thread compatibility: ABR-1 vs Wraparound:")
    print(" ", thread_compatibility("tom_abr1", "wraparound"))
    print()
    print("Radius advisory — Strat 9.5\" vs Vintage Strat bridge:")
    print(" ", compatibility_check("strat_vintage_6pt", 241.3))
    print("Radius advisory — Les Paul 12\" vs ABR-1:")
    print(" ", compatibility_check("tom_abr1", 304.8))
    print()
    print("Post positions — ABR-1 (from string center):")
    print(" ", post_hole_positions("tom_abr1"))
    print()
    print("String positions — Telecaster:")
    for x, name in saddle_string_positions("telecaster_ashtray"):
        print(f"  {name:<8} x={x:+.1f}mm")
