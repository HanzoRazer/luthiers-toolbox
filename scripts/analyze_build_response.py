#!/usr/bin/env python3
"""Derive descriptive observations from an integrity-verified witness package."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "api"))

from app.physical_engineering.build_witness.cli import analyze_main


if __name__ == "__main__":
    raise SystemExit(analyze_main())
