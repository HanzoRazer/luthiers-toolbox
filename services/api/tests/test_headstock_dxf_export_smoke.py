"""
Smoke tests for headstock DXF export router.

Endpoints:
    POST /headstock-dxf          — export DXF file
    POST /headstock-dxf/preview  — JSON preview of processed points
    POST /headstock-dxf/cost     — material cost estimate

Pattern: each endpoint returns 200, 422, or 503 — not 404.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.headstock.dxf_export import router

# Mark all tests in this module to allow missing x-request-id header
# (we're testing the router directly without middleware)
pytestmark = pytest.mark.allow_missing_request_id

# Create test app with router mounted
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Simple rectangular SVG path (200x100 rectangle) for valid requests
VALID_OUTLINE_PATH = "M 50 100 L 150 100 L 150 200 L 50 200 Z"


def _valid_export_request() -> dict:
    """Minimal valid ExportRequest payload."""
    return {
        "outline_path": VALID_OUTLINE_PATH,
    }


def _valid_cost_request() -> dict:
    """Minimal valid CostRequest payload."""
    return {
        "outline_path": VALID_OUTLINE_PATH,
    }


# ---------------------------------------------------------------------------
# POST /headstock-dxf
# ---------------------------------------------------------------------------

class TestExportDxf:
    """Tests for POST /headstock-dxf endpoint."""

    def test_export_dxf_200_valid_request(self):
        """Valid request returns DXF file."""
        response = client.post("/headstock-dxf", json=_valid_export_request())
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/dxf"
        assert "content-disposition" in response.headers
        # Verify response has content (DXF file)
        assert len(response.content) > 0

    def test_export_dxf_200_with_tuner_holes(self):
        """Request with tuner holes returns DXF."""
        payload = _valid_export_request()
        payload["tuner_holes"] = [
            {"x": 70, "y": 150, "radius": 4.0},
            {"x": 130, "y": 150, "radius": 4.0},
        ]
        response = client.post("/headstock-dxf", json=payload)
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/dxf"

    def test_export_dxf_200_with_inlay_pockets(self):
        """Request with inlay pockets returns DXF."""
        payload = _valid_export_request()
        payload["inlay_pockets"] = [
            {"path_d": "M 80 130 L 120 130 L 120 140 L 80 140 Z", "depth": 1.5, "label": "Logo"},
        ]
        response = client.post("/headstock-dxf", json=payload)
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/dxf"

    def test_export_dxf_200_with_veneer(self):
        """Request with veneer spec returns DXF."""
        payload = _valid_export_request()
        payload["veneer"] = {
            "thickness_mm": 2.0,
            "overlap_mm": 0.5,
            "species": "Ebony",
        }
        response = client.post("/headstock-dxf", json=payload)
        assert response.status_code == 200

    def test_export_dxf_200_with_binding(self):
        """Request with binding spec returns DXF."""
        payload = _valid_export_request()
        payload["binding"] = {
            "width_mm": 2.5,
            "thickness_mm": 1.5,
            "material": "abs_plastic",
            "purfling_mm": 0.5,
        }
        response = client.post("/headstock-dxf", json=payload)
        assert response.status_code == 200

    def test_export_dxf_200_with_truss_rod(self):
        """Request with truss rod spec returns DXF."""
        payload = _valid_export_request()
        payload["truss_rod"] = {
            "access": "head",
            "type": "single",
            "width_mm": 6.35,
            "depth_mm": 9.5,
            "length_mm": 400.0,
            "end_mill_mm": 3.175,
            "cx_u": 100.0,
            "start_y_u": 298.0,
            "end_y_u": 190.0,
        }
        response = client.post("/headstock-dxf", json=payload)
        assert response.status_code == 200

    def test_export_dxf_200_with_pitch_angle(self):
        """Request with pitch angle returns DXF."""
        payload = _valid_export_request()
        payload["pitch"] = {
            "style": "angled",
            "angle_deg": 14.0,
            "fixture_note": "Headstock pitch: 14 degrees",
        }
        response = client.post("/headstock-dxf", json=payload)
        assert response.status_code == 200

    def test_export_dxf_200_with_custom_kerf(self):
        """Request with custom kerf and tool diameter returns DXF."""
        payload = _valid_export_request()
        payload["kerf_mm"] = 6.35
        payload["tool_dia_mm"] = 6.35
        payload["dogbone"] = True
        response = client.post("/headstock-dxf", json=payload)
        assert response.status_code == 200

    def test_export_dxf_422_missing_outline_path(self):
        """Missing outline_path returns 422."""
        response = client.post("/headstock-dxf", json={})
        assert response.status_code == 422

    def test_export_dxf_422_invalid_outline_path_type(self):
        """Invalid outline_path type returns 422."""
        response = client.post("/headstock-dxf", json={"outline_path": 12345})
        assert response.status_code == 422

    def test_export_dxf_422_invalid_tuner_hole_schema(self):
        """Invalid tuner_hole schema returns 422."""
        payload = _valid_export_request()
        payload["tuner_holes"] = [{"invalid": "schema"}]
        response = client.post("/headstock-dxf", json=payload)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /headstock-dxf/preview
# ---------------------------------------------------------------------------

class TestPreviewDxfPoints:
    """Tests for POST /headstock-dxf/preview endpoint."""

    def test_preview_200_valid_request(self):
        """Valid request returns JSON preview."""
        response = client.post("/headstock-dxf/preview", json=_valid_export_request())
        assert response.status_code == 200
        data = response.json()
        assert "outline" in data
        assert "tuners" in data
        assert "scale_mm_per_unit" in data
        assert "bounding_box" in data

    def test_preview_200_outline_has_points(self):
        """Preview outline contains processed points."""
        response = client.post("/headstock-dxf/preview", json=_valid_export_request())
        assert response.status_code == 200
        data = response.json()
        assert len(data["outline"]) > 0
        # Each point has x, y
        point = data["outline"][0]
        assert "x" in point
        assert "y" in point

    def test_preview_200_with_tuner_holes(self):
        """Preview includes tuner hole positions."""
        payload = _valid_export_request()
        payload["tuner_holes"] = [
            {"x": 70, "y": 150, "radius": 4.0},
        ]
        response = client.post("/headstock-dxf/preview", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["tuners"]) == 1
        assert "x" in data["tuners"][0]
        assert "y" in data["tuners"][0]
        assert "r" in data["tuners"][0]

    def test_preview_200_bounding_box(self):
        """Preview includes bounding box dimensions."""
        response = client.post("/headstock-dxf/preview", json=_valid_export_request())
        assert response.status_code == 200
        data = response.json()
        bbox = data["bounding_box"]
        assert "w_mm" in bbox
        assert "h_mm" in bbox
        assert bbox["w_mm"] > 0
        assert bbox["h_mm"] > 0

    def test_preview_200_scale_override(self):
        """Preview respects scale_override."""
        payload = _valid_export_request()
        payload["scale_override"] = 0.5
        response = client.post("/headstock-dxf/preview", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["scale_mm_per_unit"] == 0.5

    def test_preview_422_missing_outline_path(self):
        """Missing outline_path returns 422."""
        response = client.post("/headstock-dxf/preview", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /headstock-dxf/cost
# ---------------------------------------------------------------------------

class TestEstimateMaterialCost:
    """Tests for POST /headstock-dxf/cost endpoint."""

    def test_cost_200_valid_request(self):
        """Valid cost request returns estimate."""
        response = client.post("/headstock-dxf/cost", json=_valid_cost_request())
        assert response.status_code == 200
        data = response.json()
        # Verify expected fields
        assert "species" in data
        assert "headstock_area_cm2" in data
        assert "blank_area_cm2" in data
        assert "utilisation_pct" in data
        assert "blank_board_feet" in data
        assert "price_per_bf_usd" in data
        assert "material_cost_usd" in data
        assert "total_cost_usd" in data
        assert "waste_adjusted_usd" in data

    def test_cost_200_default_species(self):
        """Default species is mahogany."""
        response = client.post("/headstock-dxf/cost", json=_valid_cost_request())
        assert response.status_code == 200
        data = response.json()
        assert data["species"] == "mahogany"

    def test_cost_200_custom_species(self):
        """Custom species affects pricing."""
        payload = _valid_cost_request()
        payload["species"] = "ebony"
        response = client.post("/headstock-dxf/cost", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["species"] == "ebony"
        # Ebony is more expensive than mahogany
        assert data["price_per_bf_usd"] > 10  # Ebony default is 45

    def test_cost_200_custom_price_per_bf(self):
        """Custom price_per_bf_usd overrides default."""
        payload = _valid_cost_request()
        payload["price_per_bf_usd"] = 100.0
        response = client.post("/headstock-dxf/cost", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["price_per_bf_usd"] == 100.0

    def test_cost_200_with_veneer(self):
        """Cost estimate includes veneer when specified."""
        payload = _valid_cost_request()
        payload["veneer_species"] = "ebony"
        payload["veneer_thickness_mm"] = 2.0
        response = client.post("/headstock-dxf/cost", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["veneer_cost_usd"] > 0

    def test_cost_200_quantity_multiplier(self):
        """Quantity affects total cost."""
        payload = _valid_cost_request()
        payload["quantity"] = 5
        response = client.post("/headstock-dxf/cost", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 5
        # Total qty cost should be ~5x material cost
        assert data["total_qty_cost_usd"] > data["total_cost_usd"]

    def test_cost_200_kerf_waste(self):
        """Kerf waste percentage affects final cost."""
        payload = _valid_cost_request()
        payload["kerf_waste_pct"] = 25.0
        response = client.post("/headstock-dxf/cost", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["kerf_waste_pct"] == 25.0
        # Waste adjusted should be > total qty cost
        assert data["waste_adjusted_usd"] > data["total_qty_cost_usd"]

    def test_cost_200_utilisation_calculation(self):
        """Utilisation percentage is calculated correctly."""
        response = client.post("/headstock-dxf/cost", json=_valid_cost_request())
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["utilisation_pct"] <= 100

    def test_cost_422_missing_outline_path(self):
        """Missing outline_path returns 422."""
        response = client.post("/headstock-dxf/cost", json={})
        assert response.status_code == 422

    def test_cost_422_invalid_quantity(self):
        """Invalid quantity type returns 422."""
        payload = _valid_cost_request()
        payload["quantity"] = "five"  # should be int
        response = client.post("/headstock-dxf/cost", json=payload)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge case tests across endpoints."""

    def test_empty_outline_path_still_processes(self):
        """Empty string outline_path processes (returns empty points)."""
        # Empty path is technically valid (no geometry)
        response = client.post("/headstock-dxf/preview", json={"outline_path": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["outline"] == []

    def test_complex_svg_path_with_curves(self):
        """Complex SVG path with cubic bezier curves."""
        # Path with C (cubic bezier) commands
        complex_path = "M 50 100 C 60 80 90 80 100 100 L 100 200 L 50 200 Z"
        payload = {"outline_path": complex_path}
        response = client.post("/headstock-dxf/preview", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Should have more points due to bezier subdivision
        assert len(data["outline"]) >= 4
