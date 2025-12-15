"""
Modal drilling cycle generation (G81-G89).
Supports both canned cycles and expanded G0/G1 moves.

Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Phase 5 Part 3: N.06 Modal Cycles
"""

from typing import List, Dict, Any, Tuple, Optional


def generate_g81_drill(
    holes: List[Dict[str, float]],
    depth: float,
    retract: float,
    feed: float,
    safe_z: float,
    use_modal: bool = True
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Generate G81 drilling cycle (simple drill, rapid retract).
    
    Args:
        holes: List of hole dicts with 'x' and 'y' keys
        depth: Final Z depth (negative)
        retract: R-plane for retract (positive, above surface)
        feed: Feed rate in mm/min
        safe_z: Safe Z height for rapid moves
        use_modal: True for canned cycle, False for expanded moves
    
    Returns:
        (gcode_lines, stats)
    
    Example modal output:
        G0 Z10.0
        G81 Z-20.0 R2.0 F300
        X10.0 Y10.0
        X20.0 Y10.0
        G80
    
    Example expanded output:
        G0 Z10.0
        G0 X10.0 Y10.0
        G0 Z2.0
        G1 Z-20.0 F300
        G0 Z10.0
        G0 X20.0 Y10.0
        G0 Z2.0
        G1 Z-20.0 F300
        G0 Z10.0
    """
    lines = []
    
    if use_modal:
        # Canned cycle (modal)
        lines.append(f"G0 Z{safe_z:.4f}")
        lines.append(f"G81 Z{depth:.4f} R{retract:.4f} F{feed:.1f}")
        
        for hole in holes:
            lines.append(f"X{hole['x']:.4f} Y{hole['y']:.4f}")
        
        lines.append("G80")  # Cancel cycle
    else:
        # Expanded (hobby controllers)
        lines.append(f"G0 Z{safe_z:.4f}")
        
        for hole in holes:
            lines.append(f"G0 X{hole['x']:.4f} Y{hole['y']:.4f}")
            lines.append(f"G0 Z{retract:.4f}")
            lines.append(f"G1 Z{depth:.4f} F{feed:.1f}")
            lines.append(f"G0 Z{safe_z:.4f}")
    
    stats = {
        "holes": len(holes),
        "depth": abs(depth),
        "cycle": "G81",
        "mode": "modal" if use_modal else "expanded"
    }
    
    return lines, stats


def generate_g83_peck_drill(
    holes: List[Dict[str, float]],
    depth: float,
    retract: float,
    feed: float,
    safe_z: float,
    peck_depth: float = 5.0,
    use_modal: bool = True
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Generate G83 peck drilling cycle (drill with full retract).
    
    Args:
        holes: List of hole dicts
        depth: Final Z depth (negative)
        retract: R-plane for retract
        feed: Feed rate
        safe_z: Safe Z height
        peck_depth: Depth per peck (positive)
        use_modal: True for canned cycle, False for expanded
    
    Returns:
        (gcode_lines, stats)
    """
    lines = []
    
    if use_modal:
        # Canned cycle
        lines.append(f"G0 Z{safe_z:.4f}")
        lines.append(f"G83 Z{depth:.4f} R{retract:.4f} Q{peck_depth:.4f} F{feed:.1f}")
        
        for hole in holes:
            lines.append(f"X{hole['x']:.4f} Y{hole['y']:.4f}")
        
        lines.append("G80")
    else:
        # Expanded with pecking logic
        lines.append(f"G0 Z{safe_z:.4f}")
        
        for hole in holes:
            lines.append(f"G0 X{hole['x']:.4f} Y{hole['y']:.4f}")
            lines.append(f"G0 Z{retract:.4f}")
            
            # Calculate peck increments
            current_depth = retract
            target_depth = depth
            
            while current_depth > target_depth:
                next_depth = max(current_depth - peck_depth, target_depth)
                lines.append(f"G1 Z{next_depth:.4f} F{feed:.1f}")
                lines.append(f"G0 Z{retract:.4f}")  # Full retract
                current_depth = next_depth
            
            lines.append(f"G0 Z{safe_z:.4f}")
    
    pecks = int(abs(depth - retract) / peck_depth) + 1
    
    stats = {
        "holes": len(holes),
        "depth": abs(depth),
        "peck_depth": peck_depth,
        "pecks_per_hole": pecks,
        "cycle": "G83",
        "mode": "modal" if use_modal else "expanded"
    }
    
    return lines, stats


def generate_g73_chip_break(
    holes: List[Dict[str, float]],
    depth: float,
    retract: float,
    feed: float,
    safe_z: float,
    peck_depth: float = 5.0,
    chip_break_retract: float = 0.5,
    use_modal: bool = True
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Generate G73 chip breaking cycle (drill with partial retract).
    
    Similar to G83 but retracts only slightly to break chips,
    not all the way to R-plane. Faster than G83.
    
    Args:
        chip_break_retract: Distance to retract for chip break (mm)
    """
    lines = []
    
    if use_modal:
        # Canned cycle
        lines.append(f"G0 Z{safe_z:.4f}")
        lines.append(f"G73 Z{depth:.4f} R{retract:.4f} Q{peck_depth:.4f} F{feed:.1f}")
        
        for hole in holes:
            lines.append(f"X{hole['x']:.4f} Y{hole['y']:.4f}")
        
        lines.append("G80")
    else:
        # Expanded with chip break logic
        lines.append(f"G0 Z{safe_z:.4f}")
        
        for hole in holes:
            lines.append(f"G0 X{hole['x']:.4f} Y{hole['y']:.4f}")
            lines.append(f"G0 Z{retract:.4f}")
            
            current_depth = retract
            target_depth = depth
            
            while current_depth > target_depth:
                next_depth = max(current_depth - peck_depth, target_depth)
                lines.append(f"G1 Z{next_depth:.4f} F{feed:.1f}")
                lines.append(f"G0 Z{next_depth + chip_break_retract:.4f}")  # Partial retract
                current_depth = next_depth
            
            lines.append(f"G0 Z{safe_z:.4f}")
    
    stats = {
        "holes": len(holes),
        "depth": abs(depth),
        "peck_depth": peck_depth,
        "cycle": "G73",
        "mode": "modal" if use_modal else "expanded"
    }
    
    return lines, stats


def generate_g84_tap(
    holes: List[Dict[str, float]],
    depth: float,
    retract: float,
    thread_pitch: float,
    spindle_rpm: float,
    safe_z: float,
    use_modal: bool = True
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Generate G84 rigid tapping cycle.
    
    Feed rate auto-calculated from: F = RPM × pitch
    
    Args:
        thread_pitch: Thread pitch in mm (e.g., 0.5 for M3, 0.75 for M4)
        spindle_rpm: Spindle speed
    """
    # Calculate tap feed rate
    tap_feed = spindle_rpm * thread_pitch
    
    lines = []
    
    if use_modal:
        lines.append(f"G0 Z{safe_z:.4f}")
        lines.append(f"S{spindle_rpm:.0f} M3")
        lines.append(f"G84 Z{depth:.4f} R{retract:.4f} F{tap_feed:.1f}")
        
        for hole in holes:
            lines.append(f"X{hole['x']:.4f} Y{hole['y']:.4f}")
        
        lines.append("G80")
        lines.append("M5")
    else:
        lines.append(f"G0 Z{safe_z:.4f}")
        lines.append(f"S{spindle_rpm:.0f} M3")
        
        for hole in holes:
            lines.append(f"G0 X{hole['x']:.4f} Y{hole['y']:.4f}")
            lines.append(f"G0 Z{retract:.4f}")
            lines.append(f"G1 Z{depth:.4f} F{tap_feed:.1f}")  # Down
            lines.append(f"M4")  # Reverse
            lines.append(f"G1 Z{retract:.4f} F{tap_feed:.1f}")  # Up
            lines.append(f"M3")  # Forward
            lines.append(f"G0 Z{safe_z:.4f}")
        
        lines.append("M5")
    
    stats = {
        "holes": len(holes),
        "depth": abs(depth),
        "thread_pitch": thread_pitch,
        "spindle_rpm": spindle_rpm,
        "tap_feed": tap_feed,
        "cycle": "G84",
        "mode": "modal" if use_modal else "expanded"
    }
    
    return lines, stats


def generate_g85_bore(
    holes: List[Dict[str, float]],
    depth: float,
    retract: float,
    feed: float,
    safe_z: float,
    use_modal: bool = True
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Generate G85 boring cycle (bore, feed out).
    
    Similar to G81 but feeds out instead of rapid retract.
    Better surface finish than rapid retract.
    """
    lines = []
    
    if use_modal:
        lines.append(f"G0 Z{safe_z:.4f}")
        lines.append(f"G85 Z{depth:.4f} R{retract:.4f} F{feed:.1f}")
        
        for hole in holes:
            lines.append(f"X{hole['x']:.4f} Y{hole['y']:.4f}")
        
        lines.append("G80")
    else:
        lines.append(f"G0 Z{safe_z:.4f}")
        
        for hole in holes:
            lines.append(f"G0 X{hole['x']:.4f} Y{hole['y']:.4f}")
            lines.append(f"G0 Z{retract:.4f}")
            lines.append(f"G1 Z{depth:.4f} F{feed:.1f}")  # Feed in
            lines.append(f"G1 Z{retract:.4f} F{feed:.1f}")  # Feed out
            lines.append(f"G0 Z{safe_z:.4f}")
    
    stats = {
        "holes": len(holes),
        "depth": abs(depth),
        "cycle": "G85",
        "mode": "modal" if use_modal else "expanded"
    }
    
    return lines, stats


def should_expand_cycles(post_id: Optional[str]) -> bool:
    """
    Determine if canned cycles should be expanded to G0/G1 for given post.
    
    Args:
        post_id: Post-processor ID
    
    Returns:
        True if cycles should be expanded, False if modal cycles OK
    
    Logic:
        - GRBL: Expand (no canned cycle support)
        - Hobby controllers: Expand
        - Industrial (Fanuc, Haas, Mazak, LinuxCNC): Use modal cycles
    """
    if not post_id:
        return False  # Default: use modal cycles
    
    post_lower = post_id.lower()
    
    # Expand for hobby/basic controllers
    if post_lower in ["grbl", "grbl_1.1", "tinyg", "smoothie", "marlin"]:
        return True
    
    # Use modal cycles for industrial controllers
    if post_lower in ["fanuc", "fanuc_generic", "haas", "haas_vf", "haas_mini",
                       "mazak", "mazak_iso", "okuma", "okuma_osp",
                       "linuxcnc", "pathpilot", "mach4"]:
        return False
    
    # Default: use modal cycles
    return False


def generate_drilling_gcode(
    cycle: str,
    holes: List[Dict[str, float]],
    depth: float,
    retract: float,
    feed: float,
    safe_z: float,
    post_id: Optional[str] = None,
    peck_depth: Optional[float] = None,
    thread_pitch: Optional[float] = None,
    spindle_rpm: Optional[float] = None,
    expand_cycles: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """
    Main entry point for drilling G-code generation.
    
    Args:
        cycle: Cycle type (G81, G83, G73, G84, G85)
        holes: List of hole coordinates
        depth: Final Z depth (negative)
        retract: R-plane (positive, above surface)
        feed: Feed rate (mm/min)
        safe_z: Safe Z height
        post_id: Post-processor ID (for auto-expand logic)
        peck_depth: For G83/G73 (default 5mm)
        thread_pitch: For G84 tapping (mm)
        spindle_rpm: For G84 tapping
        expand_cycles: Force expansion to G0/G1
    
    Returns:
        (gcode_string, stats_dict)
    """
    # Determine if cycles should be expanded
    use_modal = not expand_cycles and not should_expand_cycles(post_id)
    
    # Route to appropriate cycle generator
    if cycle == "G81":
        lines, stats = generate_g81_drill(holes, depth, retract, feed, safe_z, use_modal)
    elif cycle == "G83":
        pd = peck_depth or 5.0
        lines, stats = generate_g83_peck_drill(holes, depth, retract, feed, safe_z, pd, use_modal)
    elif cycle == "G73":
        pd = peck_depth or 5.0
        lines, stats = generate_g73_chip_break(holes, depth, retract, feed, safe_z, pd, 0.5, use_modal)
    elif cycle == "G84":
        if not thread_pitch or not spindle_rpm:
            raise ValueError("G84 requires thread_pitch and spindle_rpm")
        lines, stats = generate_g84_tap(holes, depth, retract, thread_pitch, spindle_rpm, safe_z, use_modal)
    elif cycle == "G85":
        lines, stats = generate_g85_bore(holes, depth, retract, feed, safe_z, use_modal)
    else:
        raise ValueError(f"Unsupported cycle: {cycle}")
    
    # Add metadata comment
    gcode = f"(Drilling Cycle: {cycle})\n"
    gcode += f"(Holes: {len(holes)})\n"
    gcode += f"(Depth: {abs(depth):.2f}mm)\n"
    gcode += f"(Mode: {stats['mode']})\n"
    gcode += "\n".join(lines)
    
    return gcode, stats
