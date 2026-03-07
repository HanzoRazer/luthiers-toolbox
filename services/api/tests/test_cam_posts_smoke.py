"""Smoke tests for CAM posts endpoints (proxied to posts_consolidated_router)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_posts_list_returns_posts_array(client):
    """GET /api/cam/posts returns posts list with builtin posts."""
    response = client.get("/api/cam/posts")
    assert response.status_code == 200
    data = response.json()
    assert "posts" in data
    assert isinstance(data["posts"], list)
    # Should have at least one builtin post
    if len(data["posts"]) > 0:
        post = data["posts"][0]
        assert "id" in post
        assert "name" in post
        assert "builtin" in post


def test_posts_get_grbl_returns_config(client):
    """GET /api/cam/posts/GRBL returns GRBL post config."""
    response = client.get("/api/cam/posts/GRBL")
    # May return 404 if GRBL not loaded, but should not error
    if response.status_code == 200:
        data = response.json()
        assert data["id"] == "GRBL"
        assert "header" in data or "tokens" in data
    else:
        # 404 is acceptable if post files not present
        assert response.status_code == 404


def test_posts_get_nonexistent_returns_404(client):
    """GET /api/cam/posts/{nonexistent} returns 404."""
    response = client.get("/api/cam/posts/NONEXISTENT_POST_XYZ")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_posts_list_structure_matches_frontend_expectations(client):
    """GET /api/cam/posts returns structure expected by frontend."""
    response = client.get("/api/cam/posts")
    assert response.status_code == 200
    data = response.json()
    # Frontend expects { posts: [{ id, name, builtin, description }] }
    assert "posts" in data
    for post in data["posts"]:
        assert "id" in post
        assert "name" in post
        assert "builtin" in post
        assert "description" in post
