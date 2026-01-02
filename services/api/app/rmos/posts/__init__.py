"""
CNC Post-Processors Package

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 3

This package contains post-processor modules for various CNC controllers.
Each module provides a `render()` function that converts toolpaths to G-code.

Available post-processors:
- grbl: GRBL 1.1+ hobby CNC controller (no line numbers, semicolon comments)
- fanuc: FANUC-style industrial CNC (O-numbers, N-codes, parentheses comments)
- linuxcnc: LinuxCNC/EMC2 open-source CNC (G64 path blending, RS274NGC)

Base protocol and utilities:
- Dialect: Enum of supported G-code dialects
- DialectConfig: Controller-specific configuration
- get_dialect_config(): Get config for a dialect
- render_gcode(): High-level function to render moves to G-code
"""
from .base import (
    Dialect,
    DialectConfig,
    DIALECT_CONFIGS,
    get_dialect_config,
    PostProcessor,
    render_gcode,
    register_post_processor,
    get_post_processor,
)
from .fanuc import render as render_fanuc, validate_for_fanuc
from .grbl import render as render_grbl, validate_for_grbl
from .linuxcnc import render as render_linuxcnc, validate_for_linuxcnc

# Register post-processors
register_post_processor(Dialect.GRBL, __import__(__name__ + ".grbl", fromlist=["grbl"]))
register_post_processor(Dialect.FANUC, __import__(__name__ + ".fanuc", fromlist=["fanuc"]))
register_post_processor(Dialect.LINUXCNC, __import__(__name__ + ".linuxcnc", fromlist=["linuxcnc"]))

__all__ = [
    # Base protocol
    "Dialect",
    "DialectConfig",
    "DIALECT_CONFIGS",
    "get_dialect_config",
    "PostProcessor",
    "render_gcode",
    "register_post_processor",
    "get_post_processor",
    # Post-processors
    "render_fanuc",
    "render_grbl",
    "render_linuxcnc",
    # Validators
    "validate_for_fanuc",
    "validate_for_grbl",
    "validate_for_linuxcnc",
]
