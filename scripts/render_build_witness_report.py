#!/usr/bin/env python3
"""Render the factual witness report. It does not add a scientific conclusion."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "api"))

from app.physical_engineering.build_witness.cli import render_main


if __name__ == "__main__":
    raise SystemExit(render_main())
