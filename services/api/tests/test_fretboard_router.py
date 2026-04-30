"""Tests for /api/v1/fretboard/* routes.

Sprint FRET-A Phase 2 Commit 1: free-tier routes only.
"""
from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


# =============================================================================
# POST /compute
# =============================================================================

class TestComputeEndpoint:
    def test_compute_minimal_12tet(self):
        """Minimal valid request returns a complete ecosphere."""
        resp = client.post("/api/v1/fretboard/compute", json={
            "scale_length_mm": 647.7,
            "fret_count": 22,
            "temperament": "equal_12",
            "string_count": 6,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "fret_lines" in body
        assert "string_paths" in body
        assert "input_params" in body
        assert body["input_params"]["temperament"] == "equal_12"

    def test_compute_19tet_produces_different_geometry(self):
        """19-TET request returns positions that differ materially from 12-TET."""
        common = {
            "scale_length_mm": 647.7,
            "fret_count": 22,
            "string_count": 6,
        }
        r12 = client.post("/api/v1/fretboard/compute",
                          json={**common, "temperament": "equal_12"})
        r19 = client.post("/api/v1/fretboard/compute",
                          json={**common, "temperament": "equal_19"})
        assert r12.status_code == 200
        assert r19.status_code == 200

        pos_12 = r12.json()["fret_lines"][12]["points"][0]["x_mm"]
        pos_19 = r19.json()["fret_lines"][12]["points"][0]["x_mm"]
        assert abs(pos_12 - pos_19) > 5.0

    def test_compute_invalid_scale_length_returns_422(self):
        resp = client.post("/api/v1/fretboard/compute", json={
            "scale_length_mm": -100.0,
            "fret_count": 22,
            "temperament": "equal_12",
            "string_count": 6,
        })
        assert resp.status_code == 422

    def test_compute_unknown_temperament_returns_422(self):
        resp = client.post("/api/v1/fretboard/compute", json={
            "scale_length_mm": 647.7,
            "fret_count": 22,
            "temperament": "purple",
            "string_count": 6,
        })
        assert resp.status_code == 422


# =============================================================================
# POST /scala
# =============================================================================

class TestScalaEndpoint:
    def test_scala_default_returns_json(self):
        resp = client.post("/api/v1/fretboard/scala", json={
            "scale_length_mm": 647.7, "fret_count": 12,
            "temperament": "equal_12", "string_count": 6,
        })
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        body = resp.json()
        assert body["pitch_count"] == 12
        assert len(body["pitches"]) == 12

    def test_scala_octet_stream_returns_scl_text(self):
        resp = client.post(
            "/api/v1/fretboard/scala",
            json={"scale_length_mm": 647.7, "fret_count": 12,
                  "temperament": "equal_12", "string_count": 6},
            headers={"Accept": "application/octet-stream"},
        )
        assert resp.status_code == 200
        text = resp.content.decode("utf-8")
        assert text.startswith("!")
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_scala_text_plain_returns_scl_text(self):
        resp = client.post(
            "/api/v1/fretboard/scala",
            json={"scale_length_mm": 647.7, "fret_count": 12,
                  "temperament": "equal_12", "string_count": 6},
            headers={"Accept": "text/plain"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")


# =============================================================================
# GET /presets
# =============================================================================

class TestPresetsEndpoint:
    def test_presets_list_returns_items_array(self):
        resp = client.get("/api/v1/fretboard/presets")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert isinstance(body["items"], list)
        assert len(body["items"]) >= 5

    def test_preset_by_name_returns_full_input(self):
        resp = client.get("/api/v1/fretboard/presets/fender_strat_25.5")
        assert resp.status_code == 200
        body = resp.json()
        assert body["scale_length_mm"] == 647.7
        assert body["fret_count"] == 22

    def test_preset_unknown_returns_404(self):
        resp = client.get("/api/v1/fretboard/presets/nonexistent")
        assert resp.status_code == 404

    def test_preset_to_compute_pipeline(self):
        """A preset retrieved via GET should POST to /compute successfully."""
        preset_resp = client.get("/api/v1/fretboard/presets/prs_25.0")
        assert preset_resp.status_code == 200
        compute_resp = client.post("/api/v1/fretboard/compute",
                                   json=preset_resp.json())
        assert compute_resp.status_code == 200


# =============================================================================
# GET /schema
# =============================================================================

class TestSchemaEndpoint:
    def test_schema_returns_pydantic_json_schema(self):
        resp = client.get("/api/v1/fretboard/schema")
        assert resp.status_code == 200
        schema = resp.json()
        assert "$defs" in schema or "properties" in schema
        assert "title" in schema
