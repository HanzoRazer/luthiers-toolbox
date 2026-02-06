"""
tap_tone_pi.cli — Unified command-line interface.

Migrated from: tap_tone/main.py

Entry point:
    ttp <command> [options]

Commands:
    devices     List audio devices
    record      Record single tap
    live        Continuous recording mode
    gold-run    Gold standard run workflow
    gui         Launch Tkinter GUI
    phase2      Phase 2 ODS workflow
    chladni     Chladni pattern analysis
    bending     Bending MOE calculation

Example:
    ttp devices
    ttp record --out ./out --label A0
    ttp gui
"""
from .main import main, build_parser

__all__ = ["main", "build_parser"]
