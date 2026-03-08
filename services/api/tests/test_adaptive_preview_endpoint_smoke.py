"""Smoke tests for Adaptive Toolpath Preview endpoints."""

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

def test_spiral_svg_endpoint_exists(client):
    """POST /api/cam/adaptive/spiral.svg endpoint exists."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0,
        "height": 50.0
    })
    assert response.status_code != 404


def test_trochoid_svg_endpoint_exists(client):
    """POST /api/cam/adaptive/trochoid.svg endpoint exists."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0
    })
    assert response.status_code != 404


# =============================================================================
# Spiral SVG Endpoint
# =============================================================================

def test_spiral_svg_returns_200(client):
    """POST /api/cam/adaptive/spiral.svg returns 200."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0,
        "height": 50.0
    })
    assert response.status_code == 200


def test_spiral_svg_returns_svg_content_type(client):
    """Spiral endpoint returns SVG content type."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0,
        "height": 50.0
    })

    content_type = response.headers.get("content-type", "")
    assert "svg" in content_type or "xml" in content_type


def test_spiral_svg_contains_svg_tag(client):
    """Spiral response contains SVG element."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0,
        "height": 50.0
    })

    content = response.text
    assert "<svg" in content
    assert "</svg>" in content


def test_spiral_svg_contains_polyline(client):
    """Spiral SVG contains polyline element."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0,
        "height": 50.0
    })

    content = response.text
    assert "<polyline" in content or "points=" in content


def test_spiral_svg_purple_stroke(client):
    """Spiral uses purple stroke color."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0,
        "height": 50.0
    })

    content = response.text
    assert "purple" in content


def test_spiral_svg_custom_step(client):
    """Spiral accepts custom step parameter."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0,
        "height": 50.0,
        "step": 5.0
    })
    assert response.status_code == 200


def test_spiral_svg_custom_center(client):
    """Spiral accepts custom center position."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0,
        "height": 50.0,
        "center_x": 10.0,
        "center_y": 15.0
    })
    assert response.status_code == 200


def test_spiral_svg_rectangular_shape(client):
    """Spiral handles rectangular (non-square) dimensions."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 100.0,
        "height": 30.0,
        "step": 3.0
    })
    assert response.status_code == 200


def test_spiral_svg_small_dimensions(client):
    """Spiral handles small dimensions."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 5.0,
        "height": 5.0,
        "step": 1.0
    })
    assert response.status_code == 200


def test_spiral_svg_large_dimensions(client):
    """Spiral handles large dimensions."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 500.0,
        "height": 500.0,
        "step": 10.0
    })
    assert response.status_code == 200


def test_spiral_svg_requires_width(client):
    """Spiral requires width field."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "height": 50.0
    })
    assert response.status_code == 422


def test_spiral_svg_requires_height(client):
    """Spiral requires height field."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0
    })
    assert response.status_code == 422


def test_spiral_svg_viewbox_present(client):
    """Spiral SVG has viewBox attribute."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0,
        "height": 50.0
    })

    content = response.text
    assert "viewBox" in content


def test_spiral_svg_has_width_height_attrs(client):
    """Spiral SVG has width/height attributes."""
    response = client.post("/api/cam/adaptive/spiral.svg", json={
        "width": 50.0,
        "height": 50.0
    })

    content = response.text
    assert 'width="' in content
    assert 'height="' in content


# =============================================================================
# Trochoid SVG Endpoint
# =============================================================================

def test_trochoid_svg_returns_200(client):
    """POST /api/cam/adaptive/trochoid.svg returns 200."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0
    })
    assert response.status_code == 200


def test_trochoid_svg_returns_svg_content_type(client):
    """Trochoid endpoint returns SVG content type."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0
    })

    content_type = response.headers.get("content-type", "")
    assert "svg" in content_type or "xml" in content_type


def test_trochoid_svg_contains_svg_tag(client):
    """Trochoid response contains SVG element."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0
    })

    content = response.text
    assert "<svg" in content
    assert "</svg>" in content


def test_trochoid_svg_contains_polyline(client):
    """Trochoid SVG contains polyline element."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0
    })

    content = response.text
    assert "<polyline" in content or "points=" in content


def test_trochoid_svg_teal_stroke(client):
    """Trochoid uses teal stroke color."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0
    })

    content = response.text
    assert "teal" in content


def test_trochoid_svg_custom_pitch(client):
    """Trochoid accepts custom pitch parameter."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0,
        "pitch": 5.0
    })
    assert response.status_code == 200


def test_trochoid_svg_custom_amplitude(client):
    """Trochoid accepts custom amplitude parameter."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0,
        "amp": 1.5
    })
    assert response.status_code == 200


def test_trochoid_svg_feed_dir_x(client):
    """Trochoid accepts feed_dir='x'."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0,
        "feed_dir": "x"
    })
    assert response.status_code == 200


def test_trochoid_svg_feed_dir_y(client):
    """Trochoid accepts feed_dir='y'."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0,
        "feed_dir": "y"
    })
    assert response.status_code == 200


def test_trochoid_svg_invalid_feed_dir(client):
    """Trochoid rejects invalid feed_dir."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0,
        "feed_dir": "z"
    })
    assert response.status_code == 422


def test_trochoid_svg_rectangular_shape(client):
    """Trochoid handles rectangular dimensions."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 100.0,
        "height": 20.0,
        "pitch": 4.0
    })
    assert response.status_code == 200


def test_trochoid_svg_small_dimensions(client):
    """Trochoid handles small dimensions."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 10.0,
        "height": 5.0,
        "pitch": 2.0
    })
    assert response.status_code == 200


def test_trochoid_svg_requires_width(client):
    """Trochoid requires width field."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "height": 30.0
    })
    assert response.status_code == 422


def test_trochoid_svg_requires_height(client):
    """Trochoid requires height field."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0
    })
    assert response.status_code == 422


def test_trochoid_svg_viewbox_present(client):
    """Trochoid SVG has viewBox attribute."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0
    })

    content = response.text
    assert "viewBox" in content


def test_trochoid_svg_no_fill(client):
    """Trochoid SVG polyline has no fill."""
    response = client.post("/api/cam/adaptive/trochoid.svg", json={
        "width": 50.0,
        "height": 30.0
    })

    content = response.text
    assert 'fill="none"' in content


# =============================================================================
# Integration Tests
# =============================================================================

def test_spiral_and_trochoid_same_dimensions(client):
    """Both endpoints work with same dimensions."""
    params = {
        "width": 60.0,
        "height": 40.0
    }

    spiral = client.post("/api/cam/adaptive/spiral.svg", json=params)
    trochoid = client.post("/api/cam/adaptive/trochoid.svg", json=params)

    assert spiral.status_code == 200
    assert trochoid.status_code == 200


def test_spiral_different_step_sizes(client):
    """Spiral with different step sizes produces valid SVG."""
    for step in [1.0, 2.5, 5.0, 10.0]:
        response = client.post("/api/cam/adaptive/spiral.svg", json={
            "width": 50.0,
            "height": 50.0,
            "step": step
        })
        assert response.status_code == 200
        assert "<svg" in response.text


def test_trochoid_different_pitches(client):
    """Trochoid with different pitches produces valid SVG."""
    for pitch in [1.0, 3.0, 5.0, 10.0]:
        response = client.post("/api/cam/adaptive/trochoid.svg", json={
            "width": 50.0,
            "height": 30.0,
            "pitch": pitch
        })
        assert response.status_code == 200
        assert "<svg" in response.text
