"""Smoke tests for Tooling endpoints (posts + tool library)."""

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

def test_list_posts_endpoint_exists(client):
    """GET /api/tooling/posts endpoint exists."""
    response = client.get("/api/tooling/posts")
    assert response.status_code != 404


def test_get_post_endpoint_exists(client):
    """GET /api/tooling/posts/{post_id} endpoint exists."""
    response = client.get("/api/tooling/posts/grbl")
    assert response.status_code in (200, 404)


def test_list_tools_endpoint_exists(client):
    """GET /api/tooling/library/tools endpoint exists."""
    response = client.get("/api/tooling/library/tools")
    assert response.status_code != 404


def test_get_tool_endpoint_exists(client):
    """GET /api/tooling/library/tools/{tool_id} endpoint exists."""
    response = client.get("/api/tooling/library/tools/test-tool")
    assert response.status_code in (200, 404)


def test_list_materials_endpoint_exists(client):
    """GET /api/tooling/library/materials endpoint exists."""
    response = client.get("/api/tooling/library/materials")
    assert response.status_code != 404


def test_get_material_endpoint_exists(client):
    """GET /api/tooling/library/materials/{material_id} endpoint exists."""
    response = client.get("/api/tooling/library/materials/test-material")
    assert response.status_code in (200, 404)


def test_validate_library_endpoint_exists(client):
    """GET /api/tooling/library/validate endpoint exists."""
    response = client.get("/api/tooling/library/validate")
    assert response.status_code != 404


# =============================================================================
# Posts - Response Structure
# =============================================================================

def test_list_posts_returns_200(client):
    """GET /api/tooling/posts returns 200."""
    response = client.get("/api/tooling/posts")
    assert response.status_code == 200


def test_list_posts_returns_list(client):
    """GET /api/tooling/posts returns a list."""
    response = client.get("/api/tooling/posts")
    data = response.json()
    assert isinstance(data, list)


def test_list_posts_has_known_posts(client):
    """GET /api/tooling/posts includes known post processors."""
    response = client.get("/api/tooling/posts")
    data = response.json()
    post_ids = [p.get("id") for p in data]
    # Should have at least grbl (most common)
    assert "grbl" in post_ids


def test_post_has_required_fields(client):
    """Post objects have required fields."""
    response = client.get("/api/tooling/posts")
    data = response.json()

    assert len(data) > 0
    post = data[0]

    assert "id" in post
    assert "name" in post
    assert "title" in post
    assert "header" in post
    assert "footer" in post


def test_post_header_footer_are_lists(client):
    """Post header and footer are lists of strings."""
    response = client.get("/api/tooling/posts")
    data = response.json()

    assert len(data) > 0
    post = data[0]

    assert isinstance(post["header"], list)
    assert isinstance(post["footer"], list)


# =============================================================================
# Posts - Individual Post
# =============================================================================

def test_get_grbl_post(client):
    """GET /api/tooling/posts/grbl returns GRBL config."""
    response = client.get("/api/tooling/posts/grbl")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "grbl"
    assert "header" in data
    assert "footer" in data


def test_get_post_case_insensitive(client):
    """GET /api/tooling/posts/{id} is case insensitive."""
    response = client.get("/api/tooling/posts/GRBL")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "grbl"


def test_get_unknown_post_returns_error_field(client):
    """GET /api/tooling/posts/{unknown} returns error field (not 404)."""
    response = client.get("/api/tooling/posts/nonexistent-post-xyz")
    assert response.status_code == 200

    data = response.json()
    assert "error" in data
    assert data["error"] == "Post not found"


# =============================================================================
# Tool Library - Tools
# =============================================================================

def test_list_tools_returns_200(client):
    """GET /api/tooling/library/tools returns 200."""
    response = client.get("/api/tooling/library/tools")
    assert response.status_code == 200


def test_list_tools_returns_list(client):
    """GET /api/tooling/library/tools returns a list."""
    response = client.get("/api/tooling/library/tools")
    data = response.json()
    assert isinstance(data, list)


def test_tool_has_required_fields(client):
    """Tool objects have required fields."""
    response = client.get("/api/tooling/library/tools")
    data = response.json()

    if len(data) > 0:
        tool = data[0]
        assert "tool_id" in tool
        assert "name" in tool
        assert "type" in tool
        assert "diameter_mm" in tool
        assert "flutes" in tool


def test_tool_diameter_is_numeric(client):
    """Tool diameter is a number."""
    response = client.get("/api/tooling/library/tools")
    data = response.json()

    if len(data) > 0:
        tool = data[0]
        assert isinstance(tool["diameter_mm"], (int, float))


def test_get_tool_by_id(client):
    """GET /api/tooling/library/tools/{id} returns tool details."""
    # First get list to find a valid tool_id
    list_response = client.get("/api/tooling/library/tools")
    tools = list_response.json()

    if len(tools) > 0:
        tool_id = tools[0]["tool_id"]
        response = client.get(f"/api/tooling/library/tools/{tool_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["tool_id"] == tool_id
        assert "chipload_mm" in data


def test_get_unknown_tool_returns_error_field(client):
    """GET /api/tooling/library/tools/{unknown} returns error field."""
    response = client.get("/api/tooling/library/tools/nonexistent-tool-xyz")
    assert response.status_code == 200

    data = response.json()
    assert "error" in data


# =============================================================================
# Tool Library - Materials
# =============================================================================

def test_list_materials_returns_200(client):
    """GET /api/tooling/library/materials returns 200."""
    response = client.get("/api/tooling/library/materials")
    assert response.status_code == 200


def test_list_materials_returns_list(client):
    """GET /api/tooling/library/materials returns a list."""
    response = client.get("/api/tooling/library/materials")
    data = response.json()
    assert isinstance(data, list)


def test_material_has_required_fields(client):
    """Material objects have required fields."""
    response = client.get("/api/tooling/library/materials")
    data = response.json()

    if len(data) > 0:
        material = data[0]
        assert "material_id" in material
        assert "name" in material
        assert "heat_sensitivity" in material
        assert "hardness" in material


def test_get_material_by_id(client):
    """GET /api/tooling/library/materials/{id} returns material details."""
    # First get list to find a valid material_id
    list_response = client.get("/api/tooling/library/materials")
    materials = list_response.json()

    if len(materials) > 0:
        material_id = materials[0]["material_id"]
        response = client.get(f"/api/tooling/library/materials/{material_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["material_id"] == material_id
        assert "density_kg_m3" in data


def test_get_unknown_material_returns_error_field(client):
    """GET /api/tooling/library/materials/{unknown} returns error field."""
    response = client.get("/api/tooling/library/materials/nonexistent-material-xyz")
    assert response.status_code == 200

    data = response.json()
    assert "error" in data


# =============================================================================
# Tool Library - Validation
# =============================================================================

def test_validate_library_returns_200(client):
    """GET /api/tooling/library/validate returns 200."""
    response = client.get("/api/tooling/library/validate")
    assert response.status_code == 200


def test_validate_library_has_required_fields(client):
    """Validation response has required fields."""
    response = client.get("/api/tooling/library/validate")
    data = response.json()

    assert "valid" in data
    assert "tool_count" in data
    assert "material_count" in data
    assert "errors" in data


def test_validate_library_valid_is_boolean(client):
    """Validation 'valid' field is boolean."""
    response = client.get("/api/tooling/library/validate")
    data = response.json()

    assert isinstance(data["valid"], bool)


def test_validate_library_errors_is_list(client):
    """Validation 'errors' field is a list."""
    response = client.get("/api/tooling/library/validate")
    data = response.json()

    assert isinstance(data["errors"], list)


def test_validate_library_counts_are_numeric(client):
    """Validation count fields are numeric."""
    response = client.get("/api/tooling/library/validate")
    data = response.json()

    assert isinstance(data["tool_count"], int)
    assert isinstance(data["material_count"], int)
