"""
FANUC Post-Processor

G-code post-processor for FANUC CNC controllers.
Targets: FANUC 0i, 16i, 18i, 21i, 30i series and compatibles.

Registry Declaration:
    impl="app.rmos.posts.fanuc:render"

Features:
- O-number program identification
- Line numbers (N-codes)
- Metric units (G21)
- Absolute coordinates (G90)
- Standard FANUC spindle control (M03/M05)
- Tool change with M6
- Proper FANUC-style comments in parentheses
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime


# Line number increment
LINE_INCREMENT = 10


def render(
    toolpaths: Dict[str, Any],
    context: Dict[str, Any],
    *,
    program_number: Optional[int] = None,
    program_comment: Optional[str] = None,
) -> str:
    """
    Render toolpaths to FANUC-compatible G-code.
    
    Args:
        toolpaths: Toolpath data with segments
        context: Machine context (spindle_rpm, feed_rate, etc.)
        program_number: Optional O-number (defaults to 1)
        program_comment: Optional program description
    
    Returns:
        G-code string
    """
    lines: List[str] = []
    line_num = 0
    
    def next_line(code: str) -> str:
        nonlocal line_num
        line_num += LINE_INCREMENT
        return f"N{line_num:04d} {code}"
    
    # Program header
    o_num = program_number or context.get("program_number", 1)
    lines.append(f"O{o_num:04d}")
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    lines.append(f"(RMOS STUDIO - {timestamp})")
    if program_comment:
        lines.append(f"({program_comment})")
    
    # Setup block
    lines.append(next_line("G21 (METRIC)"))
    lines.append(next_line("G90 (ABSOLUTE)"))
    lines.append(next_line("G17 (XY PLANE)"))
    lines.append(next_line("G40 (CANCEL CUTTER COMP)"))
    lines.append(next_line("G49 (CANCEL TOOL LENGTH COMP)"))
    lines.append(next_line("G80 (CANCEL CANNED CYCLES)"))
    
    # Extract parameters
    spindle_rpm = context.get("spindle_rpm", 12000)
    safe_z = context.get("safe_z_mm", 5.0)
    tool_id = context.get("tool_number", 1)
    
    # Tool change
    lines.append(next_line(f"T{tool_id:02d} M06"))
    
    # Move to safe Z before spindle start
    lines.append(next_line(f"G00 Z{safe_z:.3f}"))
    
    # Spindle on
    lines.append(next_line(f"S{spindle_rpm} M03"))
    lines.append(next_line("G04 P2.0 (SPINDLE WARMUP)"))
    
    # Process toolpath segments
    segments = toolpaths.get("segments", [])
    moves = toolpaths.get("moves", [])
    
    if segments:
        for segment_line in _render_segments(segments, safe_z, context):
            lines.append(next_line(segment_line))
    elif moves:
        for move_line in _render_moves(moves):
            lines.append(next_line(move_line))
    else:
        lines.append(next_line("(NO TOOLPATH DATA)"))
    
    # Footer
    lines.append(next_line(f"G00 Z{safe_z:.3f}"))
    lines.append(next_line("M05 (SPINDLE STOP)"))
    lines.append(next_line("G91 G28 Z0 (RETURN Z HOME)"))
    lines.append(next_line("G28 X0 Y0 (RETURN XY HOME)"))
    lines.append(next_line("M30 (PROGRAM END)"))
    lines.append("%")  # End of file marker
    
    return "\n".join(lines)


def _render_segments(
    segments: List[Dict[str, Any]],
    safe_z: float,
    context: Dict[str, Any],
) -> List[str]:
    """Render segment-based toolpaths for FANUC."""
    lines = []
    current_z = safe_z
    
    for i, seg in enumerate(segments):
        # Retract if needed
        if current_z < safe_z:
            lines.append(f"G00 Z{safe_z:.3f}")
            current_z = safe_z
        
        # Extract coordinates
        x_start = seg.get("x_start_mm", 0)
        y_start = seg.get("y_start_mm", 0)
        z_start = seg.get("z_start_mm", 0)
        x_end = seg.get("x_end_mm", x_start)
        y_end = seg.get("y_end_mm", y_start)
        z_end = seg.get("z_end_mm", z_start)
        feed = seg.get("feed_mm_per_min", context.get("feed_rate", 1000))
        
        lines.append(f"(SEGMENT {i+1})")
        lines.append(f"G00 X{x_start:.3f} Y{y_start:.3f}")
        
        # Plunge to start Z
        if z_start < current_z:
            lines.append(f"G01 Z{z_start:.3f} F{feed:.0f}")
            current_z = z_start
        
        # Cut to end position
        lines.append(f"G01 X{x_end:.3f} Y{y_end:.3f} Z{z_end:.3f} F{feed:.0f}")
        current_z = z_end
    
    return lines


def _render_moves(moves: List[Dict[str, Any]]) -> List[str]:
    """Render move-based toolpaths for FANUC."""
    lines = []
    
    # Map common codes to FANUC style
    code_map = {
        "G0": "G00",
        "G1": "G01",
        "G2": "G02",
        "G3": "G03",
    }
    
    for move in moves:
        code = move.get("code", "")
        
        # Normalize code
        code = code_map.get(code, code)
        
        # Skip non-motion codes that might conflict
        if code in ["M2", "M30"]:
            continue  # Will be added in footer
        
        # Build G-code line
        parts = [code]
        
        if move.get("x") is not None:
            parts.append(f"X{move['x']:.4f}")
        if move.get("y") is not None:
            parts.append(f"Y{move['y']:.4f}")
        if move.get("z") is not None:
            parts.append(f"Z{move['z']:.4f}")
        if move.get("f") is not None:
            parts.append(f"F{move['f']:.1f}")
        
        line = " ".join(parts)
        
        # Add comment in FANUC style
        if move.get("comment"):
            line += f" ({move['comment'].upper()})"
        
        lines.append(line)
    
    return lines


# =============================================================================
# FANUC-specific utilities
# =============================================================================

def get_fanuc_parameter_recommendations() -> Dict[str, Any]:
    """
    Return recommended FANUC parameters for lutherie work.
    
    Note: These are typical values - actual parameters depend on machine setup.
    """
    return {
        "description": "Recommended FANUC parameters for precision lutherie work",
        "parameters": {
            # Servo parameters
            "1820": 1,      # Servo loop gain (higher = faster response)
            "1825": 100,    # Position gain
            
            # Feedrate parameters  
            "1420": 10000,  # Max feedrate (mm/min)
            "1422": 500,    # Max cutting feedrate (mm/min) - conservative for wood
            
            # Accuracy parameters
            "1770": 1,      # In-position check enabled
            "1771": 0.01,   # In-position tolerance (mm)
            
            # Interpolation
            "1602": 1,      # Nano smoothing enabled
            "1603": 0.001,  # Nano tolerance (mm)
        },
        "notes": [
            "Consult machine manual before changing parameters",
            "Backup parameters before modification",
            "Test with conservative feedrates first",
        ],
    }


def generate_tool_table_entry(
    tool_number: int,
    tool_type: str,
    diameter_mm: float,
    length_mm: float,
    description: str = "",
) -> Dict[str, Any]:
    """
    Generate a FANUC tool table entry.
    
    This is for documentation/reference - actual tool tables
    must be entered at the machine.
    """
    return {
        "tool_number": tool_number,
        "tool_type": tool_type,
        "geometry": {
            "diameter_mm": diameter_mm,
            "length_mm": length_mm,
            "radius_mm": diameter_mm / 2,
        },
        "offsets": {
            "H": tool_number,  # Height offset register
            "D": tool_number,  # Diameter offset register
        },
        "description": description,
        "fanuc_entry": f"T{tool_number:02d} D{diameter_mm:.3f} L{length_mm:.3f}",
    }


def validate_for_fanuc(gcode: str) -> List[str]:
    """
    Validate G-code for FANUC compatibility.
    
    Returns list of warnings/errors.
    """
    warnings = []
    lines = gcode.split("\n")
    
    has_o_number = False
    has_m30 = False
    has_percent = False
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip().upper()
        
        # Check for O-number
        if stripped.startswith("O"):
            has_o_number = True
        
        # Check for program end
        if "M30" in stripped:
            has_m30 = True
        
        # Check for percent sign
        if stripped == "%":
            has_percent = True
        
        # Check for GRBL-style comments (should be parentheses for FANUC)
        if ";" in stripped:
            warnings.append(f"Line {i}: Semicolon comment - FANUC uses parentheses")
        
        # Check for lowercase (FANUC traditionally uppercase)
        if any(c.islower() for c in stripped if c.isalpha()):
            if not stripped.startswith("("):  # Comments can be mixed case
                warnings.append(f"Line {i}: Lowercase characters - FANUC prefers uppercase")
    
    if not has_o_number:
        warnings.append("Missing O-number at start of program")
    
    if not has_m30:
        warnings.append("Missing M30 program end")
    
    return warnings
