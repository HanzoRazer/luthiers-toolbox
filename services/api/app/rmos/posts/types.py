"""
Post-Processor Type Definitions

LANE: OPERATION (infrastructure)

This module defines the core types used by post-processors:
- Dialect: Enum of supported G-code dialects
- DialectConfig: Controller-specific configuration
- DIALECT_CONFIGS: Default configs for each dialect
- get_dialect_config(): Lookup function
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Union


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
