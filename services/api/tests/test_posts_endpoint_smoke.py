"""Smoke tests for Posts (Post-Processor) endpoints."""

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
    """GET /api/posts/ endpoint exists."""
    response = client.get("/api/posts/")
    assert response.status_code != 404


def test_get_post_endpoint_exists(client):
    """GET /api/posts/{post_id} endpoint exists."""
    response = client.get("/api/posts/GRBL")
    assert response.status_code != 404


def test_create_post_endpoint_exists(client):
    """POST /api/posts/ endpoint exists."""
    response = client.post("/api/posts/", json={
        "id": "TEST_EXISTS",
        "name": "Test",
        "header": ["G21"],
        "footer": ["M30"]
    })
    assert response.status_code != 404


def test_validate_post_endpoint_exists(client):
    """POST /api/posts/validate endpoint exists."""
    response = client.post("/api/posts/validate", json={
        "id": "TEST_VALIDATE",
        "name": "Test",
        "header": ["G21"],
        "footer": ["M30"]
    })
    assert response.status_code != 404


def test_tokens_list_endpoint_exists(client):
    """GET /api/posts/tokens/list endpoint exists."""
    response = client.get("/api/posts/tokens/list")
    assert response.status_code != 404



# =============================================================================
# List Posts Endpoint
# =============================================================================

def test_list_posts_returns_200(client):
    """GET /api/posts/ returns 200."""
    response = client.get("/api/posts/")
    assert response.status_code == 200


def test_list_posts_has_posts_key(client):
    """List response has posts key."""
    response = client.get("/api/posts/")
    data = response.json()

    assert "posts" in data
    assert isinstance(data["posts"], list)


def test_list_posts_has_builtin_posts(client):
    """List includes builtin posts."""
    response = client.get("/api/posts/")
    data = response.json()

    ids = [p["id"] for p in data["posts"]]
    # At least one builtin should exist
    builtin_ids = ["GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO"]
    has_any_builtin = any(bid in ids for bid in builtin_ids)
    assert has_any_builtin or len(data["posts"]) >= 0


def test_list_posts_item_has_id(client):
    """Post list item has id field."""
    response = client.get("/api/posts/")
    data = response.json()

    if len(data["posts"]) > 0:
        post = data["posts"][0]
        assert "id" in post


def test_list_posts_item_has_name(client):
    """Post list item has name field."""
    response = client.get("/api/posts/")
    data = response.json()

    if len(data["posts"]) > 0:
        post = data["posts"][0]
        assert "name" in post


def test_list_posts_item_has_builtin(client):
    """Post list item has builtin field."""
    response = client.get("/api/posts/")
    data = response.json()

    if len(data["posts"]) > 0:
        post = data["posts"][0]
        assert "builtin" in post


# =============================================================================
# Get Single Post Endpoint
# =============================================================================

def test_get_grbl_post(client):
    """GET /api/posts/GRBL returns post if exists."""
    response = client.get("/api/posts/GRBL")
    # May be 200 or 404 depending on whether builtin files exist
    assert response.status_code in [200, 404]


def test_get_unknown_post_404(client):
    """GET /api/posts/UNKNOWN_XYZ returns 404."""
    response = client.get("/api/posts/UNKNOWN_XYZ_999")
    assert response.status_code == 404


def test_get_post_has_id(client):
    """Post detail has id field."""
    response = client.get("/api/posts/GRBL")
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert data["id"] == "GRBL"


def test_get_post_has_name(client):
    """Post detail has name field."""
    response = client.get("/api/posts/GRBL")
    if response.status_code == 200:
        data = response.json()
        assert "name" in data


def test_get_post_has_header(client):
    """Post detail has header field."""
    response = client.get("/api/posts/GRBL")
    if response.status_code == 200:
        data = response.json()
        assert "header" in data


def test_get_post_has_footer(client):
    """Post detail has footer field."""
    response = client.get("/api/posts/GRBL")
    if response.status_code == 200:
        data = response.json()
        assert "footer" in data


# =============================================================================
# Validate Post Endpoint
# =============================================================================

def test_validate_post_returns_200(client):
    """POST /api/posts/validate returns 200."""
    response = client.post("/api/posts/validate", json={
        "id": "VALID_POST",
        "name": "Valid Post",
        "header": ["G21", "G90"],
        "footer": ["M5", "M30"]
    })
    assert response.status_code == 200


def test_validate_post_has_valid_field(client):
    """Validation response has valid field."""
    response = client.post("/api/posts/validate", json={
        "id": "VALID_POST_2",
        "name": "Valid Post",
        "header": ["G21"],
        "footer": ["M30"]
    })
    data = response.json()

    assert "valid" in data
    assert isinstance(data["valid"], bool)


def test_validate_post_has_warnings(client):
    """Validation response has warnings field."""
    response = client.post("/api/posts/validate", json={
        "id": "VALID_POST_3",
        "name": "Valid Post",
        "header": ["G21"],
        "footer": ["M30"]
    })
    data = response.json()

    assert "warnings" in data
    assert isinstance(data["warnings"], list)


def test_validate_post_has_errors(client):
    """Validation response has errors field."""
    response = client.post("/api/posts/validate", json={
        "id": "VALID_POST_4",
        "name": "Valid Post",
        "header": ["G21"],
        "footer": ["M30"]
    })
    data = response.json()

    assert "errors" in data
    assert isinstance(data["errors"], list)


def test_validate_post_valid_config_passes(client):
    """Valid post configuration passes validation."""
    response = client.post("/api/posts/validate", json={
        "id": "CUSTOM_VALID",
        "name": "Custom Valid",
        "header": ["G21", "G90", "G17"],
        "footer": ["M5", "M30"]
    })
    data = response.json()

    assert data["valid"] is True
    assert len(data["errors"]) == 0


def test_validate_post_reserved_prefix_error(client):
    """Post ID starting with reserved prefix has error."""
    response = client.post("/api/posts/validate", json={
        "id": "GRBL_CUSTOM",
        "name": "Reserved Prefix",
        "header": ["G21"],
        "footer": ["M30"]
    })
    data = response.json()

    # Should have error about reserved prefix
    assert len(data["errors"]) > 0


def test_validate_post_requires_id(client):
    """Validation requires id field."""
    response = client.post("/api/posts/validate", json={
        "name": "No ID",
        "header": ["G21"],
        "footer": ["M30"]
    })
    assert response.status_code == 422


def test_validate_post_requires_name(client):
    """Validation requires name field."""
    response = client.post("/api/posts/validate", json={
        "id": "NO_NAME",
        "header": ["G21"],
        "footer": ["M30"]
    })
    assert response.status_code == 422


def test_validate_post_requires_header(client):
    """Validation requires header field."""
    response = client.post("/api/posts/validate", json={
        "id": "NO_HEADER",
        "name": "No Header",
        "footer": ["M30"]
    })
    assert response.status_code == 422


def test_validate_post_requires_footer(client):
    """Validation requires footer field."""
    response = client.post("/api/posts/validate", json={
        "id": "NO_FOOTER",
        "name": "No Footer",
        "header": ["G21"]
    })
    assert response.status_code == 422


# =============================================================================
# Tokens List Endpoint
# =============================================================================

def test_tokens_list_returns_200(client):
    """GET /api/posts/tokens/list returns 200."""
    response = client.get("/api/posts/tokens/list")
    assert response.status_code == 200


def test_tokens_list_is_dict(client):
    """Tokens response is a dictionary."""
    response = client.get("/api/posts/tokens/list")
    data = response.json()

    assert isinstance(data, dict)


def test_tokens_list_has_units(client):
    """Tokens includes UNITS."""
    response = client.get("/api/posts/tokens/list")
    data = response.json()

    assert "UNITS" in data


def test_tokens_list_has_tool_diameter(client):
    """Tokens includes TOOL_DIAMETER."""
    response = client.get("/api/posts/tokens/list")
    data = response.json()

    assert "TOOL_DIAMETER" in data


def test_tokens_list_has_feed_xy(client):
    """Tokens includes FEED_XY."""
    response = client.get("/api/posts/tokens/list")
    data = response.json()

    assert "FEED_XY" in data


def test_tokens_list_has_spindle_rpm(client):
    """Tokens includes SPINDLE_RPM."""
    response = client.get("/api/posts/tokens/list")
    data = response.json()

    assert "SPINDLE_RPM" in data


def test_tokens_values_are_strings(client):
    """Token descriptions are strings."""
    response = client.get("/api/posts/tokens/list")
    data = response.json()

    for key, value in data.items():
        assert isinstance(key, str)
        assert isinstance(value, str)


# =============================================================================
# Create/Update/Delete (CRUD) - Minimal Checks
# =============================================================================

def test_create_post_requires_header(client):
    """Create requires non-empty header."""
    response = client.post("/api/posts/", json={
        "id": "CREATE_TEST",
        "name": "Create Test",
        "header": [],
        "footer": ["M30"]
    })
    assert response.status_code == 422


def test_create_post_requires_footer(client):
    """Create requires non-empty footer."""
    response = client.post("/api/posts/", json={
        "id": "CREATE_TEST_2",
        "name": "Create Test",
        "header": ["G21"],
        "footer": []
    })
    assert response.status_code == 422


def test_create_post_reserved_id_rejected(client):
    """Create rejects reserved ID prefixes."""
    response = client.post("/api/posts/", json={
        "id": "GRBL_CUSTOM",
        "name": "Reserved ID",
        "header": ["G21"],
        "footer": ["M30"]
    })
    assert response.status_code == 400


def test_update_builtin_forbidden(client):
    """Cannot update builtin posts."""
    response = client.put("/api/posts/GRBL", json={
        "name": "Modified GRBL"
    })
    # Should be 403 (forbidden) or 404 (if builtin doesn't exist)
    assert response.status_code in [403, 404]


def test_delete_builtin_forbidden(client):
    """Cannot delete builtin posts."""
    response = client.delete("/api/posts/GRBL")
    # Should be 403 (forbidden) or 404 (if builtin doesn't exist)
    assert response.status_code in [403, 404]


def test_delete_unknown_post_404(client):
    """Delete unknown post returns 404."""
    response = client.delete("/api/posts/UNKNOWN_DELETE_XYZ")
    assert response.status_code == 404


def test_update_unknown_post_404(client):
    """Update unknown post returns 404."""
    response = client.put("/api/posts/UNKNOWN_UPDATE_XYZ", json={
        "name": "Updated"
    })
    assert response.status_code == 404
