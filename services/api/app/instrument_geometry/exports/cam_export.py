"""
CAM artifact export utilities.

Target: instrument_geometry/exports/cam_export.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def export_json(data: Dict[str, Any], path: Path) -> Path:
    """Export dictionary as formatted JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def export_text(text: str, path: Path) -> Path:
    """Export text content to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
