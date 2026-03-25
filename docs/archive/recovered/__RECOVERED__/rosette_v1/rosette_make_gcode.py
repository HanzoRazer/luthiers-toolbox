"""
Rosette G-code Generator
Migrated from: server/pipelines/rosette/rosette_make_gcode.py
Status: Medium Priority Pipeline

Generates spiral G-code for rosette channel cutting.
Creates concentric circular toolpaths with stepdown.

Dependencies: None (pure Python)
"""
import math
from typing import List


def generate_spiral_gcode(
    inner_r: float,
    outer_r: float,
    tool_mm: float = 3.0,
    feed: int = 600,
    rpm: int = 18000,
    stepdown: float = 0.5,
    total_depth: float = 1.5,
    safe_z: float = 5.0,
) -> str:
    """
    Generate spiral G-code for rosette channel.
    
    Args:
        inner_r: Inner radius of channel (mm)
        outer_r: Outer radius of channel (mm)
        tool_mm: Tool diameter (mm)
        feed: Feed rate (mm/min)
        rpm: Spindle speed (RPM)
        stepdown: Depth per pass (mm)
        total_depth: Final depth (mm)
        safe_z: Safe retract height (mm)
    
    Returns:
        G-code as string
    """
    lines: List[str] = []
    
    # Header
    lines.append(f"; Rosette Channel G-code")
    lines.append(f"; Inner R: {inner_r}mm, Outer R: {outer_r}mm")
    lines.append(f"; Tool: {tool_mm}mm, Depth: {total_depth}mm")
    lines.append("")
    lines.append("G21 ; mm mode")
    lines.append("G90 ; absolute positioning")
    lines.append("G17 ; XY plane")
    lines.append(f"S{rpm} M3 ; spindle on")
    lines.append(f"G0 Z{safe_z:.2f} ; safe height")
    
    # Calculate stepover (50% tool diameter)
    stepover = tool_mm * 0.5
    
    # Calculate number of passes
    channel_width = outer_r - inner_r
    num_rings = max(1, int(math.ceil(channel_width / stepover)))
    
    # Generate passes at each depth level
    current_depth = 0
    while current_depth < total_depth:
        current_depth = min(current_depth + stepdown, total_depth)
        z = -current_depth
        
        lines.append(f"")
        lines.append(f"; Depth pass: Z={z:.2f}")
        
        # Generate concentric rings from inner to outer
        for ring_idx in range(num_rings):
            radius = inner_r + stepover * ring_idx + tool_mm / 2
            if radius > outer_r - tool_mm / 2:
                radius = outer_r - tool_mm / 2
            
            # Move to start of circle
            lines.append(f"G0 X{radius:.3f} Y0")
            lines.append(f"G1 Z{z:.2f} F{feed // 3} ; plunge")
            
            # Full circle using G2 (CW arc)
            # I, J are relative to current position
            lines.append(f"G2 X{radius:.3f} Y0 I{-radius:.3f} J0 F{feed}")
        
        # Retract between depth passes
        lines.append(f"G0 Z{safe_z:.2f}")
    
    # Footer
    lines.append("")
    lines.append("M5 ; spindle off")
    lines.append(f"G0 Z{safe_z:.2f}")
    lines.append("G0 X0 Y0")
    lines.append("M30 ; program end")
    
    return "\n".join(lines)


# CLI entry point
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate rosette spiral G-code')
    parser.add_argument('--inner-r', type=float, default=40.0, help='Inner radius (mm)')
    parser.add_argument('--outer-r', type=float, default=50.0, help='Outer radius (mm)')
    parser.add_argument('--tool-mm', type=float, default=3.0, help='Tool diameter (mm)')
    parser.add_argument('--feed', type=int, default=600, help='Feed rate (mm/min)')
    parser.add_argument('--rpm', type=int, default=18000, help='Spindle RPM')
    parser.add_argument('--stepdown', type=float, default=0.5, help='Depth per pass (mm)')
    parser.add_argument('--depth', type=float, default=1.5, help='Total depth (mm)')
    parser.add_argument('-o', '--output', type=str, help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    gcode = generate_spiral_gcode(
        inner_r=args.inner_r,
        outer_r=args.outer_r,
        tool_mm=args.tool_mm,
        feed=args.feed,
        rpm=args.rpm,
        stepdown=args.stepdown,
        total_depth=args.depth,
    )
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(gcode)
        print(f"Wrote: {args.output}")
    else:
        print(gcode)
