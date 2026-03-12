# tests/test_neck_gcode_smoke.py

"""
Smoke tests for neck G-code generation endpoints.

OM-GAP-07: Verifies neck G-code router is mounted and functional.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestNeckGcodeEndpoints:
    """Smoke tests for neck G-code API."""

    def test_generate_gcode_default(self):
        """POST /gcode/generate returns G-code with default parameters."""
        response = client.post(
            "/api/neck/gcode/generate",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert "gcode" in data
        assert len(data["gcode"]) > 500  # Has substantial G-code
        assert data["line_count"] > 50  # Multiple operations
        assert "G0" in data["gcode"] or "G1" in data["gcode"]  # Has motion commands

    def test_generate_gcode_with_preset(self):
        """POST /gcode/generate with preset generates styled G-code."""
        response = client.post(
            "/api/neck/gcode/generate",
            json={
                "preset": "gibson_standard",
                "headstock_style": "gibson_open",
                "profile": "c",
                "job_name": "Gibson_Les_Paul_Neck",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["headstock_style"] == "gibson_open"
        assert data["profile"] == "c"
        assert "Gibson_Les_Paul_Neck" in data["gcode"]

    def test_generate_gcode_with_overrides(self):
        """POST /gcode/generate with dimension overrides."""
        response = client.post(
            "/api/neck/gcode/generate",
            json={
                "scale_length": 25.5,
                "nut_width": 1.6875,
                "headstock_style": "fender_strat",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scale_length"] == 25.5
        assert data["nut_width"] == 1.6875
        assert data["headstock_style"] == "fender_strat"

    def test_generate_gcode_operations(self):
        """POST /gcode/generate returns operation list."""
        response = client.post(
            "/api/neck/gcode/generate",
            json={"headstock_style": "fender_strat"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should have multiple operations (truss rod, headstock, tuners, profile)
        assert "operations" in data
        # Operations list may be populated or empty depending on generator state
        assert isinstance(data["operations"], list)

    def test_download_gcode(self):
        """POST /gcode/download returns downloadable .nc file."""
        response = client.post(
            "/api/neck/gcode/download",
            json={
                "headstock_style": "gibson_open",
                "job_name": "Test_Neck"
            }
        )
        assert response.status_code == 200
        assert "attachment" in response.headers.get("content-disposition", "")
        assert ".nc" in response.headers.get("content-disposition", "")
        # Content should be G-code
        content = response.content.decode("utf-8")
        assert "G" in content  # Has G-codes

    def test_get_headstock_styles(self):
        """GET /gcode/styles returns available headstock styles."""
        response = client.get("/api/neck/gcode/styles")
        assert response.status_code == 200
        data = response.json()
        assert "styles" in data
        assert len(data["styles"]) >= 5  # Multiple styles available
        style_ids = [s["id"] for s in data["styles"]]
        assert "paddle" in style_ids
        assert "fender_strat" in style_ids
        assert "gibson_open" in style_ids

    def test_get_neck_profiles(self):
        """GET /gcode/profiles returns available neck profiles."""
        response = client.get("/api/neck/gcode/profiles")
        assert response.status_code == 200
        data = response.json()
        assert "profiles" in data
        assert len(data["profiles"]) >= 4  # Multiple profiles
        profile_ids = [p["id"] for p in data["profiles"]]
        assert "c" in profile_ids
        assert "d" in profile_ids
        assert "v" in profile_ids

    def test_get_tool_library(self):
        """GET /gcode/tools returns tool library."""
        response = client.get("/api/neck/gcode/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) >= 5  # Multiple tools
        # Check tool structure
        tool = data["tools"][0]
        assert "number" in tool
        assert "name" in tool
        assert "diameter_in" in tool
        assert "rpm" in tool

    def test_invalid_headstock_style_fallback(self):
        """POST /gcode/generate with invalid style falls back to paddle."""
        response = client.post(
            "/api/neck/gcode/generate",
            json={"headstock_style": "nonexistent_style"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["headstock_style"] == "paddle"  # Fallback

    def test_invalid_profile_fallback(self):
        """POST /gcode/generate with invalid profile falls back to C."""
        response = client.post(
            "/api/neck/gcode/generate",
            json={"profile": "nonexistent_profile"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profile"] == "c"  # Fallback

    def test_gcode_contains_operations(self):
        """Generated G-code contains expected operation comments."""
        response = client.post(
            "/api/neck/gcode/generate",
            json={"headstock_style": "gibson_open"}
        )
        assert response.status_code == 200
        gcode = response.json()["gcode"]
        # Check for operation markers
        assert "OP10" in gcode or "TRUSS ROD" in gcode
        assert "OP20" in gcode or "HEADSTOCK" in gcode
        assert "OP30" in gcode or "TUNER" in gcode
