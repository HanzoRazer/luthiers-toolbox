"""
floyd_rose_tremolo.py
=====================
Floyd Rose Original Tremolo System — bridge design specification.

All dimensions extracted from the official Floyd Rose Original Schematics 2021
(FR_Original_Schematics_2021). All values in mm unless noted.

Three schematic views:
  Page 1: Plan view (top and underside of bridge plate)
  Page 2: Side/front elevation with body routing pocket
  Page 3: Side profile of knife-edge assembly + stud/insert detail

Source honesty
--------------
EXACT: All dimensions read directly from the official Floyd Rose schematic.
EMPIRICAL/DERIVED: Saddle compensation values, routing clearance tolerances,
  CNC stepover recommendations.

The Floyd Rose Original is the reference design. Schaller, Gotoh, and licensed
copies share the stud pattern (M7×0.5) and pivot geometry but may differ in
plate thickness and saddle block dimensions.

Integration point
-----------------
This module lives at:
  instrument_geometry/bridge/floyd_rose_tremolo.py

It follows the same pattern as:
  instrument_geometry/bridge/geometry.py  (acoustic bridge)
  calculators/bridge_calc.py              (GEOMETRY-004)

and is referenced by:
  routers/bridge_presets_router.py        (via TREMOLO_BRIDGE_SPECS)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


# ─── Master dimension table ───────────────────────────────────────────────────
# Source: FR_Original_Schematics_2021, all pages.
# All mm.

@dataclass(frozen=True)
class FloydRoseOriginalDimensions:
    """
    Complete dimensional record from the 2021 official schematic.
    Immutable — these are the manufacturer's published values.
    """

    # ── Page 1: Plan view ─────────────────────────────────────────────────────

    # Bridge plate
    plate_width_mm:          float = 74.3   # overall plate width, nut to tail
    plate_depth_mm:          float = 37.2   # front to back (saddle area)
    plate_width_string_span: float = 54.0   # string-to-string outer span (E to e)
    plate_max_travel:        float = 76.0   # max length including arm socket zone

    # String spacing
    string_spacing_mm:       float = 10.8   # uniform, all 6 strings
    # Proof: 5 × 10.8 = 54.0 mm = string span. ✓

    # Saddle height adjustment range
    saddle_adj_min_mm:       float = 12.0   # minimum saddle height above plate
    saddle_adj_max_mm:       float = 22.6   # maximum saddle height above plate
    # Adjustment range = 22.6 - 12.0 = 10.6 mm

    # Pivot stud post centerline positions from plate edges
    stud_offset_bass_mm:     float = 14.6   # from bass edge of plate to stud CL
    stud_offset_treble_mm:   float =  9.8   # from treble edge of plate to stud CL

    # Arm socket
    arm_socket_dia_mm:       float =  6.0   # ⌀6 — arm receiver bore

    # Hex key sizes
    hex_saddle_lock_mm:      float =  2.5   # saddle lock screw (Innensechskant 2,5)
    hex_saddle_height_mm:    float =  3.0   # saddle height adjust (Innensechskant 3,0)

    # Spring cavity plate mounting holes (bottom view)
    spring_hole_span_mm:     float = 32.4   # outer span of the 5 spring-claw holes
    spring_hole_spacing_mm:  float =  5.0   # spacing between adjacent holes
    spring_hole_center_off:  float = 10.8   # center-hole offset from one end
    spring_cavity_width:     float = 54.0   # spring cavity outer width
    spring_edge_offset_bass: float =  6.9   # spring plate edge from bass side
    spring_knife_height:     float =  3.8   # knife-edge height datum from plate bottom

    # ── Page 2: Side/front elevation + routing pocket ─────────────────────────

    body_routing_width_mm:   float = 50.0   # routing pocket width (front-back)
    body_routing_depth_std:  float = 42.0   # standard routing depth (mm)
    body_routing_depth_med:  float = 37.0   # medium routing depth variant
    body_routing_depth_low:  float = 32.0   # low-profile routing depth variant
    unit_length_mm:          float = 91.7   # overall unit length (plate + arm)

    # Pivot stud collar
    stud_collar_dia_mm:      float = 12.2   # ⌀12.2 — collar OD at knife-edge
    stud_body_dia_mm:        float = 11.0   # ⌀11 — stud shank OD
    stud_insert_pilot_mm:    float =  6.8   # ⌀6.8 — insert pilot hole in body

    # Saddle radius
    saddle_radius_mm:        float = 305.0  # R305 mm = 12" (also: matches Strat)

    # ── Page 3: Side profile + stud/insert detail ─────────────────────────────

    # Knife-edge / pivot geometry
    pivot_to_body_surface:   float = 15.9   # pivot CL height above body surface (nominal)
    pivot_adj_low:           float =  8.9   # stud above insert at lowest
    pivot_adj_mid:           float =  9.4   # stud above insert at mid
    pivot_adj_high:          float =  9.9   # stud above insert at highest
    arm_stub_width:          float = 11.0   # arm stub lateral offset from pivot CL
    arm_lateral_offset:      float = 21.8   # arm attachment offset from plate CL
    locking_nut_height:      float = 15.5   # locking nut assembly height (ref)
    knife_edge_width:        float = 12.0   # knife-edge block width

    # Stud & insert dimensions
    insert_od_mm:            float =  9.8   # ⌀9.8 — insert OD (knurled body)
    insert_seat_mm:          float = 10.1   # insert seat diameter (press-fit zone)
    insert_length_mm:        float = 20.0   # overall insert length
    insert_thread:           str   = "M7x0.5"  # internal thread spec

    stud_head_dia_mm:        float =  8.5   # ⌀8.5 — stud head OD (hex socket)
    stud_total_length_mm:    float = 26.5   # overall stud length
    stud_shank_length_mm:    float = 18.0   # threaded shank below collar
    stud_collar_to_tip:      float = 22.2   # collar bottom to tip
    stud_thread:             str   = "M7x0.5"  # thread spec (same as insert)
    stud_hex_key_mm:         float =  3.0   # hex key for stud adjustment


# Singleton — the authoritative dimension set
FR_ORIGINAL = FloydRoseOriginalDimensions()


# ─── Derived geometry ─────────────────────────────────────────────────────────

@dataclass
class FloydRoseRoutingSpec:
    """
    Body routing specification for a Floyd Rose Original installation.
    All mm. Depths are below finished top surface.
    """
    # Pocket geometry
    pocket_width_mm:    float       # front to back (toward neck)
    pocket_depth_mm:    float       # below top surface
    pocket_length_mm:   float = 54.0  # string-span direction (= plate_width_string_span)

    # Stud positions (from bridge reference point = center of string span)
    stud_cl_bass_mm:    float = 0.0   # bass stud CL, from string CL axis
    stud_cl_treble_mm:  float = 0.0   # treble stud CL, from string CL axis
    stud_spacing_mm:    float = 0.0   # bass-to-treble stud CL span

    # Stud holes
    stud_hole_dia_mm:   float = 10.1  # press-fit hole for insert (= insert_seat_mm)
    stud_hole_depth_mm: float = 22.0  # insert flush + 2mm clearance

    # Spring cavity (rear)
    spring_cav_width_mm:  float = 54.0
    spring_cav_depth_mm:  float = 0.0   # depends on body depth selection
    spring_cav_length_mm: float = 65.0  # typical; varies with spring count/angle

    notes: List[str] = field(default_factory=list)


def compute_routing_spec(
    body_depth_variant: str = "standard",
    string_span_center_from_bass_edge: Optional[float] = None,
) -> FloydRoseRoutingSpec:
    """
    Compute the body routing specification for a Floyd Rose Original.

    Parameters
    ----------
    body_depth_variant : 'standard' | 'medium' | 'low'
        Routing pocket depth. 'standard' = 42mm (full travel),
        'medium' = 37mm, 'low' = 32mm (reduced up-travel).

    string_span_center_from_bass_edge : float, optional
        Horizontal offset of the string span centerline from the
        bass edge of the routing pocket. If None, defaults to
        plate_width_string_span / 2 (centered in string span).

    Returns
    -------
    FloydRoseRoutingSpec with all dimensions filled in.
    """
    d = FR_ORIGINAL

    depth_map = {
        "standard": d.body_routing_depth_std,
        "medium":   d.body_routing_depth_med,
        "low":      d.body_routing_depth_low,
    }
    pocket_depth = depth_map.get(body_depth_variant, d.body_routing_depth_std)

    # Stud spacing: total plate width minus offsets from each edge
    # Stud CL bass  = stud_offset_bass_mm from bass edge of plate
    # Stud CL treble = stud_offset_treble_mm from treble edge of plate
    # Plate width = 74.3mm
    stud_span = d.plate_width_mm - d.stud_offset_bass_mm - d.stud_offset_treble_mm
    # = 74.3 - 14.6 - 9.8 = 49.9 mm

    # String span center relative to bass stud
    # Bass stud is 14.6mm from bass plate edge.
    # String span starts at 6mm from bass plate edge (from page 1: 6mm dim),
    # string span = 54mm, so string center = 6 + 27 = 33mm from bass plate edge.
    # Bass stud CL = 14.6mm from bass edge.
    # String center from bass stud = 33 - 14.6 = 18.4mm
    string_center_from_bass_stud = 33.0 - d.stud_offset_bass_mm  # 18.4mm

    notes = [
        f"Pocket depth variant: {body_depth_variant} ({pocket_depth}mm)",
        f"Stud spacing: {stud_span:.1f}mm (bass CL to treble CL)",
        f"Stud hole: ⌀{d.insert_seat_mm}mm press-fit, 22mm deep",
        f"Insert thread: {d.insert_thread}, stud thread: {d.stud_thread}",
        f"Saddle radius: {d.saddle_radius_mm:.0f}mm ({d.saddle_radius_mm/25.4:.0f}\")",
        "Route spring cavity to match spring count and claw position.",
        "Leave 2mm clearance around pocket for plate pivot travel.",
    ]

    return FloydRoseRoutingSpec(
        pocket_width_mm=d.body_routing_width_mm,
        pocket_depth_mm=pocket_depth,
        pocket_length_mm=d.plate_width_string_span,
        stud_cl_bass_mm=d.stud_offset_bass_mm,
        stud_cl_treble_mm=d.stud_offset_treble_mm,
        stud_spacing_mm=stud_span,
        stud_hole_dia_mm=d.insert_seat_mm,
        stud_hole_depth_mm=22.0,  # insert 20mm + 2mm clearance
        spring_cav_width_mm=d.spring_cav_width_mm if hasattr(d, 'spring_cav_width_mm') else 54.0,
        spring_cav_depth_mm=pocket_depth,
        notes=notes,
    )


# ─── Saddle position calculator ───────────────────────────────────────────────

@dataclass
class FloydRoseSaddleSpec:
    """Individual saddle position and compensation for a Floyd Rose."""
    string_num:    int
    string_name:   str
    y_from_center: float   # lateral position from string-span centerline (mm)
    compensation:  float   # saddle setback from nominal scale (mm)
    nominal_scale: float   # scale length (mm)
    saddle_pos:    float   # actual saddle CL from nut (mm) = scale + comp


def compute_saddle_positions(
    scale_length_mm: float,
    string_gauges_inch: Optional[List[float]] = None,
) -> List[FloydRoseSaddleSpec]:
    """
    Compute saddle positions for a Floyd Rose Original.

    The Floyd Rose uses individual per-string saddle blocks with
    fine-tuner screws. Each saddle can be adjusted fore/aft within
    the adjustment way of 12.0–22.6mm (plate datum).

    Compensation values are EMPIRICAL estimates — actual setup
    requires a tuner and physical adjustment.

    Parameters
    ----------
    scale_length_mm : float
        Nominal scale length (e.g. 647.7 for 25.5").
    string_gauges_inch : list of float, optional
        String gauges in inches, bass to treble [E, A, D, G, B, e].
        Defaults to standard 9-42 set.

    Returns
    -------
    List of FloydRoseSaddleSpec, one per string.
    """
    d = FR_ORIGINAL

    if string_gauges_inch is None:
        # Standard 9-42 set (typical for FR guitars)
        string_gauges_inch = [0.042, 0.032, 0.024, 0.016, 0.011, 0.009]

    strings = [
        ("Low E",  True),
        ("A",      True),
        ("D",      True),
        ("G",      False),   # plain G on 9-42
        ("B",      False),
        ("High e", False),
    ]

    # String lateral positions (y) centered on string span
    # String 1 (low E) at y = -27mm, string 6 (high e) at y = +27mm
    half_span = d.string_spacing_mm * 5 / 2.0   # = 27.0mm
    y_positions = [
        -half_span + i * d.string_spacing_mm
        for i in range(6)
    ]

    # Compensation estimates (EMPIRICAL — Fender/FR setup guides)
    # FR saddle blocks allow substantial range; these are starting points.
    base_comps = {
        0: 2.8,   # Low E wound
        1: 2.4,   # A wound
        2: 2.0,   # D wound
        3: 1.5,   # G (plain on 9-42; wound would be 2.0)
        4: 1.8,   # B plain
        5: 2.2,   # High e plain (more than B — thinner, more stretch)
    }

    result = []
    for i, ((name, wound), gauge, y) in enumerate(
        zip(strings, string_gauges_inch, y_positions)
    ):
        # Gauge correction: heavier gauge → more compensation
        gauge_factor = 1.0 + (gauge - 0.024) * 8.0
        comp = base_comps[i] * gauge_factor

        result.append(FloydRoseSaddleSpec(
            string_num=i + 1,
            string_name=name,
            y_from_center=round(y, 2),
            compensation=round(comp, 2),
            nominal_scale=scale_length_mm,
            saddle_pos=round(scale_length_mm + comp, 2),
        ))

    return result


# ─── Bridge preset for router integration ─────────────────────────────────────

def floyd_rose_bridge_preset(
    scale_length_mm: float = 647.7,    # 25.5" default
    body_depth_variant: str = "standard",
) -> Dict:
    """
    Return a complete Floyd Rose Original bridge preset dict.

    Compatible with the FamilyPreset schema in bridge_presets_router.py
    plus extended tremolo-specific fields.

    Parameters
    ----------
    scale_length_mm : float
        Scale length (default 647.7mm = 25.5").
    body_depth_variant : 'standard' | 'medium' | 'low'
        Body routing depth variant.
    """
    d = FR_ORIGINAL
    routing = compute_routing_spec(body_depth_variant)
    saddles = compute_saddle_positions(scale_length_mm)

    return {
        # FamilyPreset-compatible fields
        "id":             "floyd_rose_original",
        "label":          f"Floyd Rose Original ({scale_length_mm/25.4:.2f}\")",
        "bridge_type":    "double_locking_tremolo",
        "scaleLength":    scale_length_mm,
        "stringSpread":   d.plate_width_string_span,   # 54mm
        "stringSpacing":  d.string_spacing_mm,          # 10.8mm
        "compTreble":     saddles[-1].compensation,
        "compBass":       saddles[0].compensation,
        "saddle_radius_mm": d.saddle_radius_mm,         # 305mm / 12"

        # Floyd Rose specific
        "plate": {
            "width_mm":          d.plate_width_mm,
            "depth_mm":          d.plate_depth_mm,
            "saddle_adj_min_mm": d.saddle_adj_min_mm,
            "saddle_adj_max_mm": d.saddle_adj_max_mm,
            "arm_socket_dia_mm": d.arm_socket_dia_mm,
            "hex_saddle_lock":   d.hex_saddle_lock_mm,
            "hex_height_adj":    d.hex_saddle_height_mm,
        },
        "studs": {
            "thread":            d.stud_thread,
            "stud_head_dia_mm":  d.stud_head_dia_mm,
            "stud_total_mm":     d.stud_total_length_mm,
            "stud_shank_mm":     d.stud_shank_length_mm,
            "insert_od_mm":      d.insert_od_mm,
            "insert_length_mm":  d.insert_length_mm,
            "insert_pilot_mm":   d.stud_insert_pilot_mm,
            "stud_spacing_mm":   routing.stud_spacing_mm,
            "stud_offset_bass":  d.stud_offset_bass_mm,
            "stud_offset_treble":d.stud_offset_treble_mm,
        },
        "routing": {
            "pocket_width_mm":  routing.pocket_width_mm,
            "pocket_depth_mm":  routing.pocket_depth_mm,
            "stud_hole_dia_mm": routing.stud_hole_dia_mm,
            "stud_hole_depth_mm": routing.stud_hole_depth_mm,
            "variant":          body_depth_variant,
            "notes":            routing.notes,
        },
        "saddles": [asdict(s) for s in saddles],
        "source": "Floyd Rose Original Schematics 2021 (official)",
    }


# ─── CNC routing G-code helper ───────────────────────────────────────────────

def floyd_rose_routing_gcode(
    scale_length_mm: float,
    string_center_from_neck_pocket: float,
    body_depth_variant: str = "standard",
    tool_dia_mm: float = 6.35,
    feed_roughing: float = 1800.0,
    feed_finishing: float = 900.0,
    spindle_rpm: int = 18000,
    safe_z: float = 6.0,
) -> str:
    """
    Generate CNC G-code for Floyd Rose body routing.

    Coordinate origin: center of stud span, at body top surface.
    X+: toward treble
    Y+: toward tail (away from neck)
    Z+: up (clear of body)

    Pockets generated:
      1. Main bridge pocket (rectangular, centered on stud span)
      2. Bass stud hole
      3. Treble stud hole
      4. Spring cavity reference comment (requires separate rear-access operation)

    Parameters
    ----------
    scale_length_mm : float
        Scale length — used to confirm bridge position.
    string_center_from_neck_pocket : float
        Distance from neck pocket reference to string span center (mm).
        Used for placement validation only; G-code is in local coords.
    body_depth_variant : str
        'standard' | 'medium' | 'low'
    tool_dia_mm : float
        Routing bit diameter (default 1/4" = 6.35mm).
    """
    d = FR_ORIGINAL
    routing = compute_routing_spec(body_depth_variant)
    r = tool_dia_mm / 2.0

    pocket_w = routing.pocket_width_mm    # 50mm front-back
    pocket_l = routing.pocket_length_mm   # 54mm string-span direction
    pocket_d = routing.pocket_depth_mm

    # Stud hole positions from string span center
    # Bass stud: x = -(half_span + stud_offset_bass - half_span)
    # Treble stud: x = +...
    # Actually: from the plate, string span starts 6mm from bass edge.
    # String span center from bass edge = 6 + 27 = 33mm.
    # Bass stud from bass edge = 14.6mm.
    # Bass stud from string center = 33 - 14.6 = 18.4mm (toward bass).
    # Treble stud from string center = plate_width - 33 - 9.8 = 74.3 - 33 - 9.8 = 31.5mm
    # Wait: treble stud from bass edge = 74.3 - 9.8 = 64.5mm
    # Treble stud from string center = 64.5 - 33 = 31.5mm (toward treble)
    stud_bass_x   = -(33.0 - d.stud_offset_bass_mm)      # -18.4mm (bass = negative X)
    stud_treble_x = +(d.plate_width_mm - 33.0 - d.stud_offset_treble_mm)  # +31.5mm

    stud_hole_r  = routing.stud_hole_dia_mm / 2.0
    stud_hole_d  = routing.stud_hole_depth_mm

    lines = [
        f"( Floyd Rose Original — Body Routing )",
        f"( Scale: {scale_length_mm:.1f}mm  Pocket: {body_depth_variant} "
        f"({pocket_d:.0f}mm) )",
        f"( Tool: {tool_dia_mm}mm end mill  Feed R:{feed_roughing:.0f} F:{feed_finishing:.0f} )",
        f"( Origin: string span center at body top surface )",
        f"( Source: FR_Original_Schematics_2021 )",
        "",
        "G90 G21 G17",
        f"M3 S{spindle_rpm}",
        f"G0 Z{safe_z:.3f}",
        "",
        f"( ── Pocket 1: Main bridge pocket {pocket_l:.1f}×{pocket_w:.1f}mm ── )",
    ]

    # Pocket: centered on string span (X) and pivot line (Y)
    # Y: front edge of pocket at y = -pocket_w/2, rear at y = +pocket_w/2
    x0, x1 = -pocket_l/2 + r, +pocket_l/2 - r
    y0, y1 = -pocket_w/2 + r, +pocket_w/2 - r

    n_passes = max(1, int(math.ceil(pocket_d / 4.0)))   # 4mm max depth per pass
    dz = pocket_d / n_passes

    for step in range(1, n_passes + 1):
        z_cut = -step * dz
        lines += [
            f"( Pass {step}/{n_passes}  Z={z_cut:.2f} )",
            f"G0 X{x0:.3f} Y{y0:.3f}",
            f"G1 Z{z_cut:.3f} F{feed_roughing/3:.0f}",
            f"G1 X{x1:.3f} Y{y0:.3f} F{feed_roughing:.0f}",
            f"G1 X{x1:.3f} Y{y1:.3f}",
            f"G1 X{x0:.3f} Y{y1:.3f}",
            f"G1 X{x0:.3f} Y{y0:.3f}",
        ]
    lines += [f"G0 Z{safe_z:.3f}", ""]

    # Stud holes (helical interpolation approximated as circular pocketing)
    for label, sx in [("bass", stud_bass_x), ("treble", stud_treble_x)]:
        lines += [
            f"( ── Stud hole: {label}  X={sx:.2f}  ⌀{routing.stud_hole_dia_mm}mm"
            f"  depth {stud_hole_d:.0f}mm ── )",
            f"G0 X{sx + stud_hole_r - r:.3f} Y0.000",
            f"G0 Z2.000",
        ]
        n_h = max(1, int(math.ceil(stud_hole_d / 3.0)))
        dz_h = stud_hole_d / n_h
        for step in range(1, n_h + 1):
            z_cut = -step * dz_h
            lines += [
                f"G1 Z{z_cut:.3f} F{feed_roughing/4:.0f}",
                f"G2 I{-(stud_hole_r - r):.3f} J0.000 F{feed_finishing:.0f}",
            ]
        lines += [f"G0 Z{safe_z:.3f}", ""]

    lines += [
        "( ── Spring cavity: machine from rear of body separately ── )",
        f"( Spring hole span: {d.spring_hole_span_mm:.1f}mm,"
        f" spacing: {d.spring_hole_spacing_mm:.0f}mm )",
        "",
        f"G0 Z{safe_z:.3f}",
        "G0 X0.000 Y0.000",
        "M5",
        "M30",
    ]
    return "\n".join(lines)


# ─── Comparison: locked vs unlocked saddle radius ────────────────────────────

def radius_match_note(fingerboard_radius_mm: float) -> str:
    """
    Advisory note on matching fingerboard radius to FR saddle radius.

    The FR Original has a fixed 305mm (12") radius across all saddles.
    Many guitars using FR systems have compound or shallower radii.
    """
    fr_radius = FR_ORIGINAL.saddle_radius_mm   # 305mm
    diff = fingerboard_radius_mm - fr_radius

    if abs(diff) < 5:
        return (f"Fingerboard radius {fingerboard_radius_mm:.0f}mm ≈ "
                f"FR saddle radius {fr_radius:.0f}mm. Good match.")
    elif diff < 0:
        return (f"Fingerboard radius {fingerboard_radius_mm:.0f}mm is FLATTER than "
                f"FR saddle {fr_radius:.0f}mm. Outer strings will sit high — "
                f"reduce action at center strings or use compound-radius saddles.")
    else:
        return (f"Fingerboard radius {fingerboard_radius_mm:.0f}mm is MORE CURVED than "
                f"FR saddle {fr_radius:.0f}mm. Center strings may fret out under "
                f"aggressive bending. Consider a 12\" radius fingerboard or shim saddles.")


# ─── Module summary ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("Floyd Rose Original — Bridge Design Module")
    print("=" * 56)
    print()

    # Standard preset
    preset = floyd_rose_bridge_preset(scale_length_mm=647.7)
    print("Preset (25.5\" scale, standard routing):")
    print(json.dumps(preset, indent=2, default=str))

    print()
    print("Routing spec:")
    rs = compute_routing_spec("standard")
    for note in rs.notes:
        print(f"  {note}")

    print()
    print("Saddle positions (standard 9-42):")
    for s in compute_saddle_positions(647.7):
        print(f"  {s.string_name:<8} y={s.y_from_center:+6.1f}mm  "
              f"comp={s.compensation:.2f}mm  pos={s.saddle_pos:.2f}mm")

    print()
    print("Radius note (Strat 9.5\" fingerboard):")
    print(" ", radius_match_note(241.3))

    print()
    print("G-code preview (first 25 lines):")
    gcode = floyd_rose_routing_gcode(647.7, 548.0, "standard")
    for line in gcode.split("\n")[:25]:
        print(" ", line)
