#!/usr/bin/env python3
"""
Phase 2 runner — avoids PYTHONPATH issues until packaging is fixed.

Usage:
    python tools/run_phase2.py run --grid examples/phase2_grid_mm.json --out ./runs_phase2 --synthetic
    python tools/run_phase2.py devices
    python tools/run_phase2.py run --grid ... --out ... --device 1

This script sets up the import paths correctly and forwards all arguments
to scripts/phase2_slice.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Set up import paths
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

# Import and run
from scripts.phase2_slice import main

if __name__ == "__main__":
    # Forward all CLI args (sys.argv[1:] goes to argparse)
    main()
