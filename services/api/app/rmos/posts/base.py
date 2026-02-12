"""
Post-Processor Base Protocol

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 3

This module defines the PostProcessor protocol that all post-processors must implement.
It provides a unified interface for converting canonical GCodeMoves to dialect-specific
G-code strings.

PROTOCOL INTERFACE:
-------------------
Every post-processor module must provide:

1. `render(toolpaths, context, **kwargs) -> str`
   - Convert complete toolpath structure to G-code program
   - Handle headers, footers, spindle control, coolant, etc.

2. `render_moves(moves, context) -> List[str]`
   - Convert list of GCodeMoves to G-code lines
   - Core move conversion without program structure

3. `validate(toolpaths, context) -> List[str]`
   - Validate toolpaths for controller compatibility
   - Return list of warnings (empty if OK)

4. `get_dialect_config() -> DialectConfig`
   - Return controller-specific settings

SUPPORTED DIALECTS:
-------------------
- grbl: GRBL 1.1+ (Arduino hobbyist CNC)
- fanuc: FANUC Series 0i/0i Mate (Industrial)
- linuxcnc: LinuxCNC/EMC2 (Open-source CNC)
- mach3: Mach3/Mach4 (Windows CNC)
- haas: Haas VF/UMC (Industrial VMC)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Union

from ..moves import GCodeMove

# Import and re-export types for backward compatibility
from .types import (
    Dialect,
    DialectConfig,
    DIALECT_CONFIGS,
    get_dialect_config,
)

__all__ = [
    "Dialect",
    "DialectConfig",
    "DIALECT_CONFIGS",
    "get_dialect_config",
    "PostProcessor",
    "register_post_processor",
    "get_post_processor",
    "format_coord",
    "format_feed",
    "format_speed",
    "render_comment",
    "render_spindle_start",
    "render_footer",
    "render_moves_base",
    "render_segments_base",
    "render_gcode",
]


class PostProcessor(Protocol):
    """
    Protocol defining the post-processor interface.

    All post-processor modules should implement these functions.
    """

    def render(
        self,
        toolpaths: Dict[str, Any],
        context: Dict[str, Any],
        *,
        program_comment: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Render complete toolpath structure to G-code program.

        Args:
            toolpaths: Toolpath data with 'segments' list, each containing 'moves'
            context: Machining context (feeds, speeds, tool info)
            program_comment: Optional header comment

        Returns:
            Complete G-code program as string
        """
        ...

    def render_moves(
        self,
        moves: List[GCodeMove],
        context: Dict[str, Any],
    ) -> List[str]:
        """
        Convert list of GCodeMoves to G-code lines.

        Args:
            moves: List of canonical GCodeMove dicts
            context: Machining context

        Returns:
            List of G-code lines
        """
        ...

    def validate(
        self,
        toolpaths: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[str]:
        """
        Validate toolpaths for controller compatibility.

        Args:
            toolpaths: Toolpath data
            context: Machining context

        Returns:
            List of warning messages (empty if OK)
        """
        ...

    def get_dialect_config(self) -> DialectConfig:
        """Return dialect configuration."""
        ...


# Registry of post-processors by dialect
_POST_PROCESSORS: Dict[Dialect, Any] = {}


def register_post_processor(dialect: Dialect, module: Any) -> None:
    """Register a post-processor module for a dialect."""
    _POST_PROCESSORS[dialect] = module


def get_post_processor(dialect: Union[str, Dialect]) -> Any:
    """
    Get post-processor module for a dialect.

    Args:
        dialect: Dialect name or enum

    Returns:
        Post-processor module with render() function

    Raises:
        ValueError: If dialect not registered
    """
    if isinstance(dialect, str):
        try:
            dialect_enum = Dialect(dialect.lower())
        except ValueError:
            available = ", ".join(d.value for d in Dialect)
            raise ValueError(f"Unknown dialect '{dialect}'. Available: {available}")
    else:
        dialect_enum = dialect

    if dialect_enum not in _POST_PROCESSORS:
        raise ValueError(f"No post-processor registered for dialect '{dialect_enum.value}'")

    return _POST_PROCESSORS[dialect_enum]


# =============================================================================
# SHARED FORMATTING FUNCTIONS
# =============================================================================
# These functions are used by multiple post-processors to reduce duplication.


def format_coord(axis: str, value: float, decimals: int = 3) -> str:
    """Format axis coordinate with specified decimal places."""
    return f"{axis}{value:.{decimals}f}"


def format_feed(feed: float) -> str:
    """Format feedrate value."""
    if feed == int(feed):
        return f"F{int(feed)}"
    return f"F{feed:.1f}"


def format_speed(speed: int) -> str:
    """Format spindle speed value."""
    return f"S{speed}"


def render_comment(text: str, style: str = "semicolon") -> str:
    """
    Render comment in dialect-specific style.

    Args:
        text: Comment text
        style: "semicolon" for GRBL/LinuxCNC, "parentheses" for FANUC
    """
    if style == "parentheses":
        return f"({text})"
    return f"; {text}"


def render_spindle_start(speed: int, direction: str) -> str:
    """Render spindle start command."""
    spindle_code = "M3" if direction.upper() == "CW" else "M4"
    return f"{format_speed(speed)} {spindle_code}"


def render_footer() -> List[str]:
    """Render standard program footer."""
    return [
        "",
        "; END OF PROGRAM",
        "M5",   # Spindle stop
        "M9",   # Coolant off
        "M2",   # Program end
    ]


def render_moves_base(
    moves: List[Dict[str, Any]],
    feed_xy: float,
    feed_z: float,
    *,
    coord_decimals: int = 3,
    dwell_in_seconds: bool = True,
) -> List[str]:
    """
    Render a series of moves to G-code lines.

    This is the shared move rendering logic used by GRBL, LinuxCNC, etc.

    Args:
        moves: List of move dicts with type, x, y, z, i, j, r keys
        feed_xy: XY plane feedrate
        feed_z: Z axis feedrate
        coord_decimals: Decimal places for coordinates
        dwell_in_seconds: True for G4 P in seconds, False for milliseconds
    """
    lines = []

    for move in moves:
        move_type = move.get("type", "linear")

        if move_type == "rapid":
            parts = ["G0"]
            if "x" in move:
                parts.append(format_coord("X", move["x"], coord_decimals))
            if "y" in move:
                parts.append(format_coord("Y", move["y"], coord_decimals))
            if "z" in move:
                parts.append(format_coord("Z", move["z"], coord_decimals))
            lines.append(" ".join(parts))

        elif move_type == "linear":
            parts = ["G1"]
            if "x" in move:
                parts.append(format_coord("X", move["x"], coord_decimals))
            if "y" in move:
                parts.append(format_coord("Y", move["y"], coord_decimals))
            if "z" in move:
                parts.append(format_coord("Z", move["z"], coord_decimals))
                parts.append(format_feed(feed_z))
            else:
                parts.append(format_feed(feed_xy))
            lines.append(" ".join(parts))

        elif move_type in ("cw_arc", "ccw_arc"):
            arc_code = "G2" if move_type == "cw_arc" else "G3"
            parts = [arc_code]
            parts.append(format_coord("X", move["x"], coord_decimals))
            parts.append(format_coord("Y", move["y"], coord_decimals))
            if "z" in move:
                parts.append(format_coord("Z", move["z"], coord_decimals))
            if "i" in move:
                parts.append(format_coord("I", move["i"], coord_decimals))
            if "j" in move:
                parts.append(format_coord("J", move["j"], coord_decimals))
            if "r" in move:
                parts.append(format_coord("R", move["r"], coord_decimals))
            parts.append(format_feed(feed_xy))
            lines.append(" ".join(parts))

        elif move_type == "dwell":
            if dwell_in_seconds:
                dwell_sec = move.get("seconds", move.get("p", 0) / 1000.0)
                lines.append(f"G4 P{dwell_sec:.3f}")
            else:
                dwell_ms = move.get("p", move.get("seconds", 0) * 1000)
                lines.append(f"G4 P{dwell_ms:.0f}")

    return lines


def render_segments_base(
    segments: List[Dict[str, Any]],
    context: Dict[str, Any],
    *,
    coord_decimals: int = 3,
    dwell_in_seconds: bool = True,
    comment_style: str = "semicolon",
) -> List[str]:
    """
    Render all segments (operations) to G-code.

    Shared segment rendering logic for GRBL, LinuxCNC, etc.
    """
    lines = []

    feed_xy = context.get("feed_xy", 1000)
    feed_z = context.get("feed_z", 200)
    safe_z = context.get("safe_z", 10.0)

    for idx, seg in enumerate(segments):
        # Segment comment
        seg_name = seg.get("name", f"Segment {idx + 1}")
        lines.append("")
        lines.append(render_comment(f"--- {seg_name} ---", comment_style))

        # Optional coolant on
        if seg.get("coolant", False):
            coolant_type = seg.get("coolant_type", "flood")
            coolant_code = "M7" if coolant_type == "mist" else "M8"
            lines.append(coolant_code)

        # Retract to safe Z
        lines.append(f"G0 {format_coord('Z', safe_z, coord_decimals)}")

        # Render moves
        moves = seg.get("moves", [])
        move_lines = render_moves_base(
            moves, feed_xy, feed_z,
            coord_decimals=coord_decimals,
            dwell_in_seconds=dwell_in_seconds,
        )
        lines.extend(move_lines)

        # Retract after segment
        lines.append(f"G0 {format_coord('Z', safe_z, coord_decimals)}")

        # Optional coolant off
        if seg.get("coolant", False):
            lines.append("M9")

    return lines


def render_gcode(
    moves: List[GCodeMove],
    dialect: Union[str, Dialect] = Dialect.GRBL,
    context: Optional[Dict[str, Any]] = None,
    *,
    program_comment: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    High-level function to render GCodeMoves to G-code string.

    This is the main entry point for converting canonical moves to G-code.
    It wraps the dialect-specific post-processors with a unified interface.

    Args:
        moves: List of canonical GCodeMove dicts
        dialect: Target dialect (grbl, fanuc, linuxcnc, etc.)
        context: Machining context (feeds, speeds, tool info)
        program_comment: Optional header comment

    Returns:
        G-code program as string

    Example:
        >>> from app.rmos.moves import rapid, linear
        >>> moves = [
        ...     rapid(z=5),
        ...     rapid(x=0, y=0),
        ...     linear(z=-5, f=200),
        ...     linear(x=100, y=0, f=1000),
        ... ]
        >>> gcode = render_gcode(moves, dialect="grbl")
    """
    config = get_dialect_config(dialect)
    ctx = context or {}

    # Build toolpaths structure expected by post-processors
    toolpaths = {
        "segments": [
            {
                "name": "Main",
                "moves": moves,
            }
        ]
    }

    # Try to get registered post-processor
    if isinstance(dialect, str):
        dialect_enum = Dialect(dialect.lower())
    else:
        dialect_enum = dialect

    if dialect_enum in _POST_PROCESSORS:
        processor = _POST_PROCESSORS[dialect_enum]
        return processor.render(toolpaths, ctx, program_comment=program_comment, **kwargs)

    # Fallback: simple rendering using moves module
    from ..moves import moves_to_gcode

    lines = []

    # Header
    if program_comment:
        if config.comment_style == "parentheses":
            lines.append(f"({program_comment})")
        else:
            lines.append(f"; {program_comment}")

    # Program structure
    if config.use_percent_signs:
        lines.insert(0, "%")

    if config.use_o_number:
        prog_num = kwargs.get("program_number", 1)
        lines.append(f"O{prog_num:04d}")

    # Setup block
    lines.append("G21" if ctx.get("units", "mm") == "mm" else "G20")
    lines.append("G90")  # Absolute mode
    lines.append("G17")  # XY plane

    # Path blending for LinuxCNC
    if config.supports_g64 and config.default_path_tolerance:
        lines.append(f"G64 P{config.default_path_tolerance}")

    # Moves
    move_lines = moves_to_gcode(
        moves,
        use_r_mode=config.use_r_mode,
        dwell_in_seconds=config.dwell_in_seconds,
        include_line_numbers=config.use_line_numbers,
        line_number_start=config.line_number_start,
        line_number_increment=config.line_number_increment,
    )
    lines.extend(move_lines)

    # Footer
    lines.append("M5")  # Spindle stop
    lines.append("M30" if config.use_two_digit_gcodes else "M2")  # Program end

    if config.use_percent_signs:
        lines.append("%")

    return "\n".join(lines)
