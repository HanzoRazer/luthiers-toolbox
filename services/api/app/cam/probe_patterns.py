"""
CNC probing patterns for work offset establishment.

Generates G31 probing routines for automatic part location and work coordinate setup.
Supports 10+ patterns including corner finding, boss/hole location, and surface Z-zero.
"""

from typing import Dict, List, Tuple, Optional, Any
from math import cos, sin, radians


def generate_corner_probe(
    pattern: str = "corner_outside",
    approach_distance: float = 20.0,
    retract_distance: float = 2.0,
    feed_probe: float = 100.0,
    safe_z: float = 10.0,
    work_offset: int = 1
) -> str:
    """Generate corner finding probe pattern."""
    outside = (pattern == "corner_outside")
    wcs_cmd = f"G{53 + work_offset}"  # G54-G59
    
    # Probe direction signs
    x_sign = "+" if outside else "-"
    y_sign = "+" if outside else "-"
    x_dir = 1 if outside else -1
    y_dir = 1 if outside else -1
    
    gcode_lines = [
        f"(Corner Find - {pattern})",
        f"({wcs_cmd} Work Offset)",
        "",
        "G90 (Absolute mode)",
        "M5 (Spindle off - safety)",
        f"G0 Z{safe_z:.4f} (Safe Z)",
        "",
        "(Initialize variables)",
        "#100 = 0 (X1)",
        "#101 = 0 (X2)",
        "#102 = 0 (Y1)",
        "#103 = 0 (Y2)",
        "#104 = 0 (Corner X)",
        "#105 = 0 (Corner Y)",
        "",
        f"(Probe {x_sign}X face - Lower point)",
        f"G0 X{-approach_distance * x_dir:.4f} Y10.0",
        f"G31 X{approach_distance * x_dir:.4f} F{feed_probe:.1f}",
        "#100 = #5061 (Store X position)",
        f"G0 X[#100{'-' if outside else '+'}{retract_distance:.1f}] (Retract)",
        "",
        f"(Probe {x_sign}X face - Upper point)",
        "G0 Y40.0",
        f"G31 X{approach_distance * x_dir:.4f} F{feed_probe:.1f}",
        "#101 = #5061",
        f"G0 X[#101{'-' if outside else '+'}{retract_distance:.1f}]",
        "",
        f"(Probe {y_sign}Y face - Left point)",
        f"G0 X10.0 Y{-approach_distance * y_dir:.4f}",
        f"G31 Y{approach_distance * y_dir:.4f} F{feed_probe:.1f}",
        "#102 = #5062 (Store Y position)",
        f"G0 Y[#102{'-' if outside else '+'}{retract_distance:.1f}] (Retract)",
        "",
        f"(Probe {y_sign}Y face - Right point)",
        "G0 X40.0",
        f"G31 Y{approach_distance * y_dir:.4f} F{feed_probe:.1f}",
        "#103 = #5062",
        f"G0 Y[#103{'-' if outside else '+'}{retract_distance:.1f}]",
        "",
        "(Calculate corner position)",
        "#104 = [#100 + #101] / 2 (Average X)",
        "#105 = [#102 + #103] / 2 (Average Y)",
        "",
        f"(Set {wcs_cmd} origin at corner)",
        f"G10 L20 P{work_offset} X#104 Y#105",
        "",
        f"G0 Z{safe_z:.4f}",
        "G0 X0 Y0 (Move to new origin)",
        "",
        "M0 (Check position and continue)",
        f"(Corner set: X=#104, Y=#105)"
    ]
    
    return "\n".join(gcode_lines)


def generate_boss_probe(
    pattern: str = "boss_circular",
    estimated_diameter: float = 50.0,
    estimated_center: Tuple[float, float] = (0.0, 0.0),
    probe_count: int = 4,
    approach_distance: float = 5.0,
    retract_distance: float = 5.0,
    feed_probe: float = 100.0,
    safe_z: float = 10.0,
    work_offset: int = 1
) -> str:
    """Generate circular boss/hole finding pattern."""
    boss = (pattern == "boss_circular")
    wcs_cmd = f"G{53 + work_offset}"
    ex, ey = estimated_center
    radius = estimated_diameter / 2.0
    
    # Probe direction (outward for boss, inward for hole)
    dir_sign = 1 if boss else -1
    
    gcode_lines = [
        f"(Boss/Hole Find - {pattern})",
        f"({wcs_cmd} Work Offset)",
        f"(Estimated center: X{ex:.2f} Y{ey:.2f})",
        f"(Estimated diameter: {estimated_diameter:.2f}mm)",
        "",
        "G90 (Absolute mode)",
        "M5 (Spindle off - safety)",
        f"G0 Z{safe_z:.4f}",
        "",
        "(Initialize probe storage)",
    ]
    
    # Add variable initialization
    for i in range(probe_count):
        gcode_lines.append(f"#1{10+i} = 0 (Probe {i+1} X)")
        gcode_lines.append(f"#1{20+i} = 0 (Probe {i+1} Y)")
    
    gcode_lines.extend([
        "#200 = 0 (Center X)",
        "#201 = 0 (Center Y)",
        "#202 = 0 (Measured diameter)",
        ""
    ])
    
    # Generate probe moves at evenly spaced angles
    angle_step = 360.0 / probe_count
    
    for i in range(probe_count):
        angle = i * angle_step
        angle_rad = radians(angle)
        
        # Start position (beyond estimated edge)
        start_dist = radius + approach_distance
        start_x = ex + start_dist * cos(angle_rad) * dir_sign
        start_y = ey + start_dist * sin(angle_rad) * dir_sign
        
        # Target position (beyond opposite edge)
        target_dist = radius + approach_distance
        target_x = ex - target_dist * cos(angle_rad) * dir_sign
        target_y = ey - target_dist * sin(angle_rad) * dir_sign
        
        gcode_lines.extend([
            f"(Probe {i+1}: {angle:.0f}°)",
            f"G0 X{start_x:.4f} Y{start_y:.4f}",
            f"G31 X{target_x:.4f} Y{target_y:.4f} F{feed_probe:.1f}",
            f"#1{10+i} = #5061 (Store X)",
            f"#1{20+i} = #5062 (Store Y)",
            ""
        ])
        
        # Retract
        retract_x = ex + (radius + retract_distance) * cos(angle_rad) * dir_sign
        retract_y = ey + (radius + retract_distance) * sin(angle_rad) * dir_sign
        gcode_lines.append(f"G0 X{retract_x:.4f} Y{retract_y:.4f} (Retract)")
        gcode_lines.append("")
    
    # Calculate center (average of all probe points)
    gcode_lines.extend([
        "(Calculate center position)",
        "#200 = 0 (Reset sum X)",
        "#201 = 0 (Reset sum Y)",
    ])
    
    for i in range(probe_count):
        gcode_lines.append(f"#200 = #200 + #1{10+i}")
        gcode_lines.append(f"#201 = #201 + #1{20+i}")
    
    gcode_lines.extend([
        f"#200 = #200 / {probe_count} (Average X)",
        f"#201 = #201 / {probe_count} (Average Y)",
        "",
        "(Calculate diameter - use opposing points)",
        "#202 = SQRT[[#110 - #112] * [#110 - #112] + [#120 - #122] * [#120 - #122]]",
        "",
        f"(Set {wcs_cmd} origin at center)",
        f"G10 L20 P{work_offset} X#200 Y#201",
        "",
        f"G0 Z{safe_z:.4f}",
        "G0 X0 Y0 (Move to center)",
        "",
        "M0 (Check position)",
        f"(Center: X=#200, Y=#201, Ø=#202)"
    ])
    
    return "\n".join(gcode_lines)


def generate_surface_z_probe(
    approach_z: float = 10.0,
    probe_depth: float = -20.0,
    feed_probe: float = 50.0,
    retract_distance: float = 5.0,
    work_offset: int = 1
) -> str:
    """Generate surface Z-zero touch-off pattern."""
    wcs_cmd = f"G{53 + work_offset}"
    
    gcode_lines = [
        "(Surface Z Touch-Off)",
        f"({wcs_cmd} Work Offset)",
        "",
        "G90 (Absolute mode)",
        "M5 (Spindle off - safety)",
        "",
        "(Move to probe position)",
        "G0 X0 Y0 (Assume X/Y already set)",
        f"G0 Z{approach_z:.4f}",
        "",
        "(Probe surface)",
        f"G31 Z{probe_depth:.4f} F{feed_probe:.1f}",
        "#150 = #5063 (Store Z position)",
        "",
        "(Retract)",
        f"G0 Z[#150 + {retract_distance:.1f}]",
        "",
        f"(Set {wcs_cmd} Z-zero at surface)",
        f"G10 L20 P{work_offset} Z#150",
        "",
        f"G0 Z{approach_z:.4f}",
        "M0 (Z-zero set at surface)",
        "(Surface Z: #150)"
    ]
    
    return "\n".join(gcode_lines)


def generate_pocket_probe(
    pocket_width: float = 100.0,
    pocket_height: float = 60.0,
    approach_distance: float = 10.0,
    retract_distance: float = 2.0,
    feed_probe: float = 100.0,
    safe_z: float = 10.0,
    work_offset: int = 1,
    origin_corner: str = "lower_left"
) -> str:
    """Generate inside pocket corner finding pattern."""
    wcs_cmd = f"G{53 + work_offset}"
    hw = pocket_width / 2.0
    hh = pocket_height / 2.0
    
    gcode_lines = [
        "(Pocket Find - Inside)",
        f"({wcs_cmd} Work Offset)",
        f"(Pocket: {pocket_width:.1f} × {pocket_height:.1f} mm)",
        f"(Origin: {origin_corner})",
        "",
        "G90 (Absolute mode)",
        "M5 (Spindle off - safety)",
        f"G0 Z{safe_z:.4f}",
        "",
        "(Initialize variables)",
        "#110 = 0 (X1 -X wall)",
        "#111 = 0 (X2 +X wall)",
        "#112 = 0 (Y1 -Y wall)",
        "#113 = 0 (Y2 +Y wall)",
        "#114 = 0 (Pocket X)",
        "#115 = 0 (Pocket Y)",
        "",
        "(Probe -X wall)",
        f"G0 X0 Y{hh * 0.5:.4f}",
        f"G31 X{-hw + approach_distance:.4f} F{feed_probe:.1f}",
        "#110 = #5061",
        f"G0 X[#110 + {retract_distance:.1f}]",
        "",
        "(Probe +X wall)",
        "G0 X0",
        f"G31 X{hw - approach_distance:.4f} F{feed_probe:.1f}",
        "#111 = #5061",
        f"G0 X[#111 - {retract_distance:.1f}]",
        "",
        "(Probe -Y wall)",
        f"G0 X{hw * 0.5:.4f} Y0",
        f"G31 Y{-hh + approach_distance:.4f} F{feed_probe:.1f}",
        "#112 = #5062",
        f"G0 Y[#112 + {retract_distance:.1f}]",
        "",
        "(Probe +Y wall)",
        "G0 Y0",
        f"G31 Y{hh - approach_distance:.4f} F{feed_probe:.1f}",
        "#113 = #5062",
        f"G0 Y[#113 - {retract_distance:.1f}]",
        "",
        "(Calculate pocket center)",
        "#114 = [#110 + #111] / 2",
        "#115 = [#112 + #113] / 2",
        ""
    ]
    
    # Set origin based on corner selection
    if origin_corner == "center":
        gcode_lines.extend([
            f"(Set {wcs_cmd} origin at pocket center)",
            f"G10 L20 P{work_offset} X#114 Y#115"
        ])
    elif origin_corner == "lower_left":
        gcode_lines.extend([
            f"(Set {wcs_cmd} origin at lower-left corner)",
            f"G10 L20 P{work_offset} X#110 Y#112"
        ])
    elif origin_corner == "lower_right":
        gcode_lines.extend([
            f"(Set {wcs_cmd} origin at lower-right corner)",
            f"G10 L20 P{work_offset} X#111 Y#112"
        ])
    elif origin_corner == "upper_left":
        gcode_lines.extend([
            f"(Set {wcs_cmd} origin at upper-left corner)",
            f"G10 L20 P{work_offset} X#110 Y#113"
        ])
    elif origin_corner == "upper_right":
        gcode_lines.extend([
            f"(Set {wcs_cmd} origin at upper-right corner)",
            f"G10 L20 P{work_offset} X#111 Y#113"
        ])
    
    gcode_lines.extend([
        "",
        f"G0 Z{safe_z:.4f}",
        "G0 X0 Y0 (Move to origin)",
        "",
        "M0 (Check position)",
        "(Pocket center: X=#114, Y=#115)"
    ])
    
    return "\n".join(gcode_lines)


def generate_vise_square_probe(
    vise_jaw_height: float = 50.0,
    probe_spacing: float = 100.0,
    approach_distance: float = 20.0,
    retract_distance: float = 5.0,
    feed_probe: float = 100.0,
    safe_z: float = 10.0
) -> str:
    """Generate vise squareness check pattern."""
    gcode_lines = [
        "(Vise Squareness Check)",
        "(Probes vise jaw at 2 points to measure angle)",
        "",
        "G90 (Absolute mode)",
        "M5 (Spindle off - safety)",
        f"G0 Z{safe_z:.4f}",
        "",
        "(Initialize variables)",
        "#120 = 0 (X1 first point)",
        "#121 = 0 (X2 second point)",
        "#122 = 0 (Delta X)",
        "#123 = 0 (Angle degrees)",
        "",
        f"(Probe point 1 at Y0)",
        "G0 X-10.0 Y0",
        f"G0 Z{vise_jaw_height:.4f}",
        f"G31 X{approach_distance:.4f} F{feed_probe:.1f}",
        "#120 = #5061",
        f"G0 X[#120 - {retract_distance:.1f}]",
        f"G0 Z{safe_z:.4f}",
        "",
        f"(Probe point 2 at Y{probe_spacing:.1f})",
        f"G0 Y{probe_spacing:.4f}",
        f"G0 Z{vise_jaw_height:.4f}",
        f"G31 X{approach_distance:.4f} F{feed_probe:.1f}",
        "#121 = #5061",
        f"G0 X[#121 - {retract_distance:.1f}]",
        f"G0 Z{safe_z:.4f}",
        "",
        "(Calculate angle)",
        "#122 = #121 - #120 (X difference)",
        f"#123 = ATAN[#122 / {probe_spacing:.1f}] (Angle radians)",
        "#123 = #123 * 57.2958 (Convert to degrees)",
        "",
        "(Check tolerance)",
        "#124 = ABS[#123]",
        "IF [#124 GT 0.1] THEN #3000=1 (Vise not square! Angle: #123°)",
        "",
        "G0 Y0",
        "M0 (Vise angle: #123°)",
        "(X1=#120, X2=#121, ΔX=#122, Angle=#123°)"
    ]
    
    return "\n".join(gcode_lines)


def get_probe_patterns() -> List[Dict[str, Any]]:
    """
    Get list of available probe patterns with metadata.
    
    Returns:
        List of pattern info dictionaries
    """
    return [
        {
            "id": "corner_outside",
            "name": "Corner Find (Outside)",
            "description": "4-point probe on external corner",
            "probes": 4,
            "sets": "X/Y origin at corner",
            "typical_time_s": 30
        },
        {
            "id": "corner_inside",
            "name": "Corner Find (Inside)",
            "description": "4-point probe on internal corner (pocket)",
            "probes": 4,
            "sets": "X/Y origin at pocket corner",
            "typical_time_s": 30
        },
        {
            "id": "boss_circular",
            "name": "Boss Find (Circular)",
            "description": "4-12 point probe on cylindrical boss",
            "probes": "4-12",
            "sets": "X/Y origin at boss center",
            "typical_time_s": 45
        },
        {
            "id": "hole_circular",
            "name": "Hole Find (Circular)",
            "description": "4-12 point probe inside hole",
            "probes": "4-12",
            "sets": "X/Y origin at hole center",
            "typical_time_s": 45
        },
        {
            "id": "pocket_inside",
            "name": "Pocket Find",
            "description": "4-point probe inside rectangular pocket",
            "probes": 4,
            "sets": "X/Y origin at pocket center or corner",
            "typical_time_s": 35
        },
        {
            "id": "surface_z",
            "name": "Surface Z Touch-Off",
            "description": "Single Z-axis probe on top surface",
            "probes": 1,
            "sets": "Z-zero at surface",
            "typical_time_s": 10
        },
        {
            "id": "vise_square",
            "name": "Vise Squareness Check",
            "description": "2-point angle measurement on vise jaw",
            "probes": 2,
            "sets": "Reports angle deviation",
            "typical_time_s": 20
        }
    ]


def get_statistics(gcode: str) -> Dict[str, Any]:
    """
    Calculate statistics from generated probe G-code.
    
    Args:
        gcode: Generated G-code string
    
    Returns:
        Statistics dictionary
    """
    lines = gcode.split('\n')
    
    probe_count = sum(1 for line in lines if 'G31' in line)
    variable_count = sum(1 for line in lines if line.strip().startswith('#'))
    has_wcs_set = any('G10 L20' in line for line in lines)
    
    # Estimate time (rough: 3s per probe + 10s overhead)
    estimated_time = probe_count * 3 + 10
    
    return {
        "probe_moves": probe_count,
        "variables_used": variable_count,
        "sets_wcs": has_wcs_set,
        "estimated_time_s": estimated_time,
        "lines": len([l for l in lines if l.strip() and not l.strip().startswith('(')])
    }
