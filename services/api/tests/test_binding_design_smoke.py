"""
Smoke tests for binding_design_router.py.

Mounted at /api/binding. Each route must not return **404** (unmounted).
Happy paths: **200**; validation: **422**; optional **503** if added later.
This router also returns **400** for domain rules (e.g. strip-length inputs).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PREFIX = "/api/binding"


def _not_route_missing(status: int) -> None:
    assert status != 404, "Endpoint not mounted (404)"


def _acceptable(status: int) -> None:
    """Route exists; allow success, validation, or service-unavailable."""
    _not_route_missing(status)
    assert status in (200, 400, 422, 503), f"Unexpected status: {status}"


class TestBindingDesignRouterMount:
    def test_get_styles_not_404(self):
        resp = client.get(f"{PREFIX}/styles")
        _acceptable(resp.status_code)
        assert resp.status_code == 200
        data = resp.json()
        assert "styles" in data
        assert "count" in data

    def test_get_materials_not_404(self):
        resp = client.get(f"{PREFIX}/materials")
        _acceptable(resp.status_code)
        assert resp.status_code == 200
        data = resp.json()
        assert "materials" in data

    def test_get_purfling_patterns_not_404(self):
        resp = client.get(f"{PREFIX}/purfling-patterns")
        _acceptable(resp.status_code)
        assert resp.status_code == 200
        data = resp.json()
        assert "patterns" in data


class TestPostDesign:
    def test_design_valid_body_style_returns_200(self):
        resp = client.post(
            f"{PREFIX}/design",
            json={
                "body_style": "om",
                "binding_material": "abs_plastic",
                "binding_width_mm": 2.5,
            },
        )
        _acceptable(resp.status_code)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert "binding_path_analysis" in data

    def test_design_missing_required_returns_422(self):
        resp = client.post(f"{PREFIX}/design", json={})
        _not_route_missing(resp.status_code)
        assert resp.status_code == 422


class TestPostStripLength:
    def test_strip_length_perimeter_only_returns_200(self):
        resp = client.post(
            f"{PREFIX}/strip-length",
            json={"perimeter_mm": 1000.0},
        )
        _acceptable(resp.status_code)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert "order_length_mm" in data

    def test_strip_length_body_style_returns_200(self):
        resp = client.post(
            f"{PREFIX}/strip-length",
            json={"body_style": "om"},
        )
        _acceptable(resp.status_code)
        assert resp.status_code == 200

    def test_strip_length_invalid_perimeter_returns_422(self):
        resp = client.post(
            f"{PREFIX}/strip-length",
            json={"perimeter_mm": -1.0},
        )
        _not_route_missing(resp.status_code)
        assert resp.status_code == 422

    def test_strip_length_neither_style_nor_perimeter_returns_400(self):
        resp = client.post(f"{PREFIX}/strip-length", json={})
        _not_route_missing(resp.status_code)
        assert resp.status_code == 400
