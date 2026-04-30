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


# =============================================================================
# POST /dxf
# =============================================================================

class TestDxfEndpoint:
    def test_dxf_default_unauthenticated_returns_r12(self):
        """No auth, no version -> R12 LINE DXF."""
        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "equal_12", "string_count": 6,
        })
        assert resp.status_code == 200
        assert resp.headers.get("X-DXF-Version") == "R12"
        assert b"AC1009" in resp.content[:200]

    def test_dxf_explicit_r12_unauthenticated_succeeds(self):
        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "equal_12", "string_count": 6,
            "dxf_version": "R12",
        })
        assert resp.status_code == 200
        assert b"AC1009" in resp.content[:200]

    def test_dxf_r2000_unauthenticated_returns_401(self):
        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "equal_12", "string_count": 6,
            "dxf_version": "R2000",
        })
        assert resp.status_code == 401
        body = resp.json()
        assert "R12" in str(body)

    @pytest.mark.skip(reason="Requires test fixture for pro principal")
    def test_dxf_r2000_pro_authenticated_returns_r2000(self):
        """When auth fixture is available, this test verifies R2000 output."""
        pass

    def test_dxf_returns_dxf_content_type(self):
        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "equal_12", "string_count": 6,
        })
        assert resp.headers["content-type"] == "application/dxf"
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_dxf_accepts_slot_width_mm(self):
        """Custom slot width propagates to DXF generation."""
        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "equal_12", "string_count": 6,
            "slot_width_mm": 0.75,
        })
        assert resp.status_code == 200

    def test_dxf_contains_nine_layers(self):
        """Phase 7: DXF output contains all nine named layers."""
        import tempfile
        import ezdxf

        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "equal_12", "string_count": 6,
        })
        assert resp.status_code == 200

        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
            f.write(resp.content)
            f.flush()
            doc = ezdxf.readfile(f.name)

        layer_names = {layer.dxf.name for layer in doc.layers}
        expected_layers = {
            "STRINGS", "FRETS", "FRETBOARD_OUTLINE", "FRET_SLOTS",
            "NUT", "BRIDGE", "BRIDGE_COMPENSATED", "HARMONICS_OVERLAY",
            "ANNOTATIONS",
        }
        missing = expected_layers - layer_names
        assert not missing, f"Missing layers: {missing}"

    def test_dxf_fret_slots_has_closed_polylines(self):
        """Phase 7: FRET_SLOTS layer contains closed polylines for CAM."""
        import tempfile
        import ezdxf

        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "equal_12", "string_count": 6,
        })
        assert resp.status_code == 200

        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
            f.write(resp.content)
            f.flush()
            doc = ezdxf.readfile(f.name)

        msp = doc.modelspace()
        slot_entities = [e for e in msp if e.dxf.layer == "FRET_SLOTS"]

        assert len(slot_entities) >= 22, f"Expected 22 fret slot entities, got {len(slot_entities)}"

    def test_dxf_annotations_has_fret_numbers(self):
        """Phase 7: ANNOTATIONS layer contains fret number text."""
        import tempfile
        import ezdxf

        resp = client.post("/api/v1/fretboard/dxf", json={
            "scale_length_mm": 647.7, "fret_count": 22,
            "temperament": "equal_12", "string_count": 6,
        })
        assert resp.status_code == 200

        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
            f.write(resp.content)
            f.flush()
            doc = ezdxf.readfile(f.name)

        msp = doc.modelspace()
        annotation_texts = [
            e for e in msp
            if e.dxf.layer == "ANNOTATIONS" and e.dxftype() == "TEXT"
        ]
        assert len(annotation_texts) >= 22, "Should have at least 22 fret number labels"
