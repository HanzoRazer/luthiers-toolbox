#!/usr/bin/env python3
"""Recompute witness sizes and digests and report the contract result."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "api"))

from app.physical_engineering.build_witness.cli import verify_main


if __name__ == "__main__":
    raise SystemExit(verify_main())
