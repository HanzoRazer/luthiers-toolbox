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

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Union

from ..moves import GCodeMove


class Dialect(str, Enum):
    """Supported G-code dialects."""
    GRBL = "grbl"
    FANUC = "fanuc"
    LINUXCNC = "linuxcnc"
    MACH3 = "mach3"
    HAAS = "haas"
    MARLIN = "marlin"


@dataclass(frozen=True)
class DialectConfig:
    """
    Controller-specific G-code configuration.

    This defines how G-code should be formatted for a specific controller.
    """
    name: str
    dialect: Dialect

    # Arc mode: True for R-word arcs, False for I/J center offsets
    use_r_mode: bool = False

    # Dwell format: True for G4 S (seconds), False for G4 P (milliseconds)
    dwell_in_seconds: bool = False

    # Line numbers: True for N-codes (FANUC), False for none (GRBL)
    use_line_numbers: bool = False
    line_number_start: int = 10
    line_number_increment: int = 10

    # Program structure
    use_o_number: bool = False      # O-number program header (FANUC)
    use_percent_signs: bool = False  # % start/end markers (FANUC)

    # Comment style: "semicolon" (GRBL), "parentheses" (FANUC)
    comment_style: str = "semicolon"

    # Path blending (LinuxCNC only)
    supports_g64: bool = False
    default_path_tolerance: Optional[float] = None

    # Coordinate precision (decimal places)
    coord_decimals: int = 3
    feed_decimals: int = 1

    # G-code format (G0 vs G00)
    use_two_digit_gcodes: bool = False  # G00 instead of G0


# Default dialect configs for each controller
DIALECT_CONFIGS: Dict[Dialect, DialectConfig] = {
    Dialect.GRBL: DialectConfig(
        name="GRBL",
        dialect=Dialect.GRBL,
        use_r_mode=False,
        dwell_in_seconds=False,
        use_line_numbers=False,
        comment_style="semicolon",
        coord_decimals=3,
    ),
    Dialect.FANUC: DialectConfig(
        name="FANUC",
        dialect=Dialect.FANUC,
        use_r_mode=False,
        dwell_in_seconds=False,
        use_line_numbers=True,
        use_o_number=True,
        use_percent_signs=True,
        comment_style="parentheses",
        use_two_digit_gcodes=True,
        coord_decimals=4,
    ),
    Dialect.LINUXCNC: DialectConfig(
        name="LinuxCNC",
        dialect=Dialect.LINUXCNC,
        use_r_mode=False,
        dwell_in_seconds=False,
        use_line_numbers=False,
        comment_style="semicolon",
        supports_g64=True,
        default_path_tolerance=0.002,
        coord_decimals=4,
    ),
    Dialect.MACH3: DialectConfig(
        name="Mach3",
        dialect=Dialect.MACH3,
        use_r_mode=False,
        dwell_in_seconds=False,
        use_line_numbers=False,
        comment_style="parentheses",
        coord_decimals=4,
    ),
    Dialect.HAAS: DialectConfig(
        name="Haas",
        dialect=Dialect.HAAS,
        use_r_mode=True,  # Haas prefers R-mode arcs
        dwell_in_seconds=True,  # G4 S (seconds)
        use_line_numbers=True,
        use_o_number=True,
        use_percent_signs=True,
        comment_style="parentheses",
        use_two_digit_gcodes=True,
        coord_decimals=4,
    ),
    Dialect.MARLIN: DialectConfig(
        name="Marlin",
        dialect=Dialect.MARLIN,
        use_r_mode=False,
        dwell_in_seconds=False,
        use_line_numbers=False,
        comment_style="semicolon",
        coord_decimals=3,
    ),
}


def get_dialect_config(dialect: Union[str, Dialect]) -> DialectConfig:
    """
    Get dialect configuration by name or enum.

    Args:
        dialect: Dialect name (case-insensitive) or Dialect enum

    Returns:
        DialectConfig for the specified dialect

    Raises:
        ValueError: If dialect is not recognized

    Example:
        >>> config = get_dialect_config("grbl")
        >>> config.use_r_mode
        False
    """
    if isinstance(dialect, str):
        dialect_lower = dialect.lower()
        try:
            dialect_enum = Dialect(dialect_lower)
        except ValueError:
            available = ", ".join(d.value for d in Dialect)
            raise ValueError(f"Unknown dialect '{dialect}'. Available: {available}")
    else:
        dialect_enum = dialect

    return DIALECT_CONFIGS[dialect_enum]


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
