"""
Guitar Body Outlines for ToolBox

Coordinate data for 11 guitar body models (2,041 points total).
Data loaded from body_outlines.json; original source was DXF extraction.
Source DXFs archived 2026-02-07 (code owner decision: Python data is truth source).

Usage:
    from app.instrument_geometry.body.detailed_outlines import BODY_OUTLINES
    outline = BODY_OUTLINES["stratocaster"]
"""

from __future__ import annotations

import json
from pathlib import Path

_JSON_PATH = Path(__file__).parent / "body_outlines.json"

# Load once on import; convert JSON arrays back to tuples for
# compatibility with downstream geometry code.
BODY_OUTLINES = {
    key: [tuple(pt) for pt in pts]
    for key, pts in json.loads(_JSON_PATH.read_text()).items()
}
