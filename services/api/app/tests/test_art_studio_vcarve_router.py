# services/api/app/tests/test_art_studio_vcarve_router.py

"""
Smoke tests for Art Studio VCarve Router (Wave 1).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


SAMPLE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">
  <rect x="0" y="0" width="10" height="10" />
</svg>
""".strip()


def test_vcarve_preview_smoke():
    """Test /vcarve/preview returns valid stats."""
    r = client.post(
        "/api/art-studio/vcarve/preview",
        json={"svg": SAMPLE_SVG, "normalize": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["normalized"] is True
    assert data["stats"]["polyline_count"] >= 1


def test_vcarve_gcode_smoke():
    """Test /vcarve/gcode returns valid G-code."""
    r = client.post(
        "/api/art-studio/vcarve/gcode",
        json={
            "svg": SAMPLE_SVG,
            "bit_angle_deg": 60.0,
            "depth_mm": 1.5,
            "safe_z_mm": 5.0,
            "feed_rate_mm_min": 800.0,
            "plunge_rate_mm_min": 300.0,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "gcode" in data
    assert "G21" in data["gcode"]  # mm units
    assert "M30" in data["gcode"]  # program end


def test_vcarve_preview_empty_svg():
    """Test that empty SVG returns 400 error."""
    r = client.post(
        "/api/art-studio/vcarve/preview",
        json={"svg": "", "normalize": True},
    )
    assert r.status_code == 400
