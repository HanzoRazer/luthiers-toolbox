#!/usr/bin/env python3
"""
G-code Reader & Summarizer (Backward Compatibility)

This module re-exports from the split gcode/ package for backward compatibility.
New code should import directly from app.util.gcode instead.

Original module split into:
- gcode/types.py: Move, Summary dataclasses
- gcode/lexer.py: strip_comments(), parse_words()
- gcode/reader.py: parse_gcode(), validate_gcode()
- gcode/report.py: print_report(), write_csv(), write_json()
- gcode/cli.py: main()

Usage (unchanged):
  python gcode_reader.py path/to/file.nc
  python gcode_reader.py file.nc --csv path.csv --json summary.json
  python gcode_reader.py file.nc --validate
"""
from __future__ import annotations

# Re-export all public API for backward compatibility
from .gcode import (
    Move,
    Summary,
    parse_gcode,
    parse_words,
    print_report,
    strip_comments,
    validate_gcode,
    write_csv,
)
from .gcode.cli import main

__all__ = [
    "Move",
    "Summary",
    "strip_comments",
    "parse_words",
    "parse_gcode",
    "validate_gcode",
    "print_report",
    "write_csv",
    "main",
]

if __name__ == "__main__":
    raise SystemExit(main())
