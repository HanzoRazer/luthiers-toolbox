# tests/test_headstock_inlay_smoke.py

"""
Smoke tests for headstock inlay router endpoints.

INLAY-01: Verifies headstock inlay API is mounted and functional.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestHeadstockInlayEndpoints:
    """Smoke tests for headstock inlay API."""

    def test_list_styles(self):
        """GET /styles returns available headstock styles."""
        response = client.get("/api/instruments/guitar/headstock-inlay/styles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 10  # At least 10 styles defined in HeadstockStyle
        style_ids = [s["id"] for s in data]
        assert "les_paul" in style_ids
        assert "stratocaster" in style_ids
        assert "prs" in style_ids

    def test_get_style_info(self):
        """GET /styles/{id} returns specific style details."""
        response = client.get("/api/instruments/guitar/headstock-inlay/styles/les_paul")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "les_paul"
        assert "description" in data
        assert "open book" in data["description"].lower() or "gibson" in data["description"].lower()

    def test_get_invalid_style(self):
        """GET /styles/{id} returns 404 for unknown style."""
        response = client.get("/api/instruments/guitar/headstock-inlay/styles/nonexistent")
        assert response.status_code == 404

    def test_list_designs(self):
        """GET /designs returns available inlay designs."""
        response = client.get("/api/instruments/guitar/headstock-inlay/designs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 20  # Many designs defined
        design_ids = [d["id"] for d in data]
        assert "hummingbird" in design_ids
        assert "dove" in design_ids
        assert "tree_of_life" in design_ids

    def test_get_design_info(self):
        """GET /designs/{id} returns specific design details."""
        response = client.get("/api/instruments/guitar/headstock-inlay/designs/hummingbird")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "hummingbird"
        assert "description" in data
        assert len(data["description"]) > 50  # Has substantial description

    def test_list_materials(self):
        """GET /materials returns wood species and materials."""
        response = client.get("/api/instruments/guitar/headstock-inlay/materials")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 15  # Many materials defined
        material_ids = [m["id"] for m in data]
        assert "mahogany" in material_ids
        assert "mother_of_pearl" in material_ids
        assert "abalone" in material_ids
        # Check categories
        categories = {m["category"] for m in data}
        assert "dark_wood" in categories
        assert "accent" in categories

    def test_list_templates(self):
        """GET /templates returns pre-built templates."""
        response = client.get("/api/instruments/guitar/headstock-inlay/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 10  # Many templates defined
        template_ids = [t["id"] for t in data]
        assert "gibson_hummingbird" in template_ids
        assert "tree_of_life" in template_ids

    def test_get_template(self):
        """GET /templates/{id} returns template with generated prompt."""
        response = client.get("/api/instruments/guitar/headstock-inlay/templates/gibson_hummingbird")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "gibson_hummingbird"
        assert "prompt" in data
        assert len(data["prompt"]) > 200  # Has substantial prompt
        assert "hummingbird" in data["prompt"].lower()

    def test_get_invalid_template(self):
        """GET /templates/{id} returns 404 for unknown template."""
        response = client.get("/api/instruments/guitar/headstock-inlay/templates/nonexistent")
        assert response.status_code == 404

    def test_generate_prompt(self):
        """POST /generate-prompt returns AI prompt."""
        response = client.post(
            "/api/instruments/guitar/headstock-inlay/generate-prompt",
            json={
                "style": "les_paul",
                "headstock_wood": "mahogany",
                "inlay_design": "dove",
                "inlay_material": "mother_of_pearl",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "prompt" in data
        assert data["style"] == "les_paul"
        assert data["inlay_design"] == "dove"
        assert len(data["prompt"]) > 200
        assert "dove" in data["prompt"].lower()
        assert "mahogany" in data["prompt"].lower()

    def test_generate_prompt_invalid_style(self):
        """POST /generate-prompt returns 422 for invalid style."""
        response = client.post(
            "/api/instruments/guitar/headstock-inlay/generate-prompt",
            json={
                "style": "invalid_style",
                "headstock_wood": "mahogany",
                "inlay_design": "dove",
                "inlay_material": "mother_of_pearl",
            }
        )
        assert response.status_code == 422

    def test_generate_inlay_prompt(self):
        """POST /generate-inlay-prompt returns isolated inlay prompt."""
        response = client.post(
            "/api/instruments/guitar/headstock-inlay/generate-inlay-prompt",
            json={
                "design": "eagle",
                "material": "abalone",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "prompt" in data
        assert data["design"] == "eagle"
        assert "eagle" in data["prompt"].lower()

    def test_get_all_options(self):
        """GET /options returns all available options."""
        response = client.get("/api/instruments/guitar/headstock-inlay/options")
        assert response.status_code == 200
        data = response.json()
        assert "headstock_styles" in data
        assert "inlay_designs" in data
        assert "wood_species" in data
        assert "templates" in data
        assert len(data["headstock_styles"]) >= 10
        assert len(data["inlay_designs"]) >= 20

    def test_list_inlay_templates(self):
        """GET /inlay-templates returns isolated inlay templates."""
        response = client.get("/api/instruments/guitar/headstock-inlay/inlay-templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5
        assert any(t["design"] == "eagle" for t in data)
