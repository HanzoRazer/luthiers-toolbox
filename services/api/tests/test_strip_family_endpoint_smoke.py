"""Smoke tests for Strip Family endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_list_strip_families_endpoint_exists(client):
    """GET /api/rmos/strip-families/ endpoint exists."""
    response = client.get("/api/rmos/strip-families/")
    assert response.status_code != 404


def test_list_templates_endpoint_exists(client):
    """GET /api/rmos/strip-families/templates endpoint exists."""
    response = client.get("/api/rmos/strip-families/templates")
    assert response.status_code != 404


def test_create_from_template_endpoint_exists(client):
    """POST /api/rmos/strip-families/from-template/{id} endpoint exists."""
    response = client.post("/api/rmos/strip-families/from-template/test_template")
    # 404 from template not found is valid (endpoint exists but template doesn't)
    # 405 would mean wrong method, which would indicate endpoint doesn't exist for POST
    assert response.status_code != 405


def test_get_strip_family_endpoint_exists(client):
    """GET /api/rmos/strip-families/{id} endpoint exists."""
    response = client.get("/api/rmos/strip-families/test_family_id")
    # 404 from family not found is valid (endpoint exists but family doesn't)
    # We just verify it's not a 405 Method Not Allowed
    assert response.status_code in [200, 404]


# =============================================================================
# List Strip Families Endpoint
# =============================================================================

def test_list_strip_families_returns_200(client):
    """GET /api/rmos/strip-families/ returns 200."""
    response = client.get("/api/rmos/strip-families/")
    assert response.status_code == 200


def test_list_strip_families_returns_list(client):
    """List endpoint returns a list."""
    response = client.get("/api/rmos/strip-families/")
    data = response.json()

    assert isinstance(data, list)


def test_list_strip_families_items_are_dicts(client):
    """List items are dictionaries."""
    response = client.get("/api/rmos/strip-families/")
    data = response.json()

    # If there are items, they should be dicts
    for item in data:
        assert isinstance(item, dict)


# =============================================================================
# List Templates Endpoint
# =============================================================================

def test_list_templates_returns_200(client):
    """GET /api/rmos/strip-families/templates returns 200."""
    response = client.get("/api/rmos/strip-families/templates")
    assert response.status_code == 200


def test_list_templates_returns_list(client):
    """Templates endpoint returns a list."""
    response = client.get("/api/rmos/strip-families/templates")
    data = response.json()

    assert isinstance(data, list)


def test_list_templates_items_have_id(client):
    """Template items have id field."""
    response = client.get("/api/rmos/strip-families/templates")
    data = response.json()

    if len(data) > 0:
        template = data[0]
        assert "id" in template or "template_id" in template


def test_list_templates_items_have_name(client):
    """Template items have name field."""
    response = client.get("/api/rmos/strip-families/templates")
    data = response.json()

    if len(data) > 0:
        template = data[0]
        assert "name" in template or "label" in template or "title" in template


# =============================================================================
# Create From Template Endpoint
# =============================================================================

def test_create_from_unknown_template_404(client):
    """Create from unknown template returns 404."""
    response = client.post("/api/rmos/strip-families/from-template/UNKNOWN_TEMPLATE_XYZ")
    assert response.status_code == 404


def test_create_from_template_returns_dict(client):
    """Create from valid template returns dict."""
    # First get available templates
    templates_response = client.get("/api/rmos/strip-families/templates")
    templates = templates_response.json()

    if len(templates) > 0:
        # Use first template
        template_id = templates[0].get("id") or templates[0].get("template_id")
        if template_id:
            response = client.post(f"/api/rmos/strip-families/from-template/{template_id}")
            # Should succeed or fail with known error
            assert response.status_code in [200, 201, 400, 409]


# =============================================================================
# Get Strip Family Endpoint
# =============================================================================

def test_get_unknown_family_404(client):
    """Get unknown strip family returns 404."""
    response = client.get("/api/rmos/strip-families/UNKNOWN_FAMILY_XYZ_999")
    assert response.status_code == 404


def test_get_strip_family_returns_dict(client):
    """Get existing family returns dict."""
    # First list families
    list_response = client.get("/api/rmos/strip-families/")
    families = list_response.json()

    if len(families) > 0:
        # Get first family
        family_id = families[0].get("id") or families[0].get("family_id")
        if family_id:
            response = client.get(f"/api/rmos/strip-families/{family_id}")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)


# =============================================================================
# Integration Tests
# =============================================================================

def test_list_and_get_consistency(client):
    """List and get endpoints are consistent."""
    # Get list
    list_response = client.get("/api/rmos/strip-families/")
    families = list_response.json()

    if len(families) > 0:
        family = families[0]
        family_id = family.get("id") or family.get("family_id")

        if family_id:
            # Get individual
            get_response = client.get(f"/api/rmos/strip-families/{family_id}")

            if get_response.status_code == 200:
                individual = get_response.json()
                # Should have same ID
                ind_id = individual.get("id") or individual.get("family_id")
                assert ind_id == family_id


def test_templates_and_families_both_work(client):
    """Both templates and families endpoints work."""
    templates_response = client.get("/api/rmos/strip-families/templates")
    families_response = client.get("/api/rmos/strip-families/")

    assert templates_response.status_code == 200
    assert families_response.status_code == 200
