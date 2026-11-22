#!/usr/bin/env python3
"""Create a blank external build-response witness. Measurements are not invented."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "api"))

from app.physical_engineering.build_witness.cli import create_main


if __name__ == "__main__":
    raise SystemExit(create_main())
