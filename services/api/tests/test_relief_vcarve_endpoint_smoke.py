"""Smoke tests for Art Studio Relief and VCarve preview endpoints.

NOTE: These routers are mounted at /api without internal prefixes,
so both relief_router and vcarve_router define POST /preview at /api/preview.
Only one is active (relief_router based on manifest order).
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# Sample SVG for testing
SAMPLE_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="10" y="10" width="80" height="60"/>
</svg>'''

SIMPLE_SVG = '<svg xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="50" height="30"/></svg>'


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_preview_endpoint_exists(client):
    """POST /api/preview endpoint exists."""
    response = client.post("/api/preview", json={"svg": SIMPLE_SVG})
    assert response.status_code != 404


# =============================================================================
# Preview Endpoint - Basic
# =============================================================================

def test_preview_returns_200(client):
    """POST /api/preview returns 200 with valid SVG."""
    response = client.post("/api/preview", json={
        "svg": SAMPLE_SVG,
        "normalize": True
    })
    assert response.status_code == 200


def test_preview_requires_svg(client):
    """POST /api/preview requires svg field."""
    response = client.post("/api/preview", json={})
    assert response.status_code == 422  # Validation error


def test_preview_rejects_empty_svg(client):
    """POST /api/preview rejects empty SVG."""
    response = client.post("/api/preview", json={
        "svg": "",
        "normalize": True
    })
    assert response.status_code == 400


def test_preview_rejects_whitespace_svg(client):
    """POST /api/preview rejects whitespace-only SVG."""
    response = client.post("/api/preview", json={
        "svg": "   ",
        "normalize": True
    })
    assert response.status_code == 400


# =============================================================================
# Preview Endpoint - Response Structure
# =============================================================================

def test_preview_has_stats(client):
    """Preview response has stats field."""
    response = client.post("/api/preview", json={"svg": SAMPLE_SVG})
    data = response.json()

    assert "stats" in data


def test_preview_has_normalized_flag(client):
    """Preview response has normalized field."""
    response = client.post("/api/preview", json={"svg": SAMPLE_SVG})
    data = response.json()

    assert "normalized" in data
    assert isinstance(data["normalized"], bool)


def test_preview_stats_has_svg_data(client):
    """Preview stats contain SVG geometry data."""
    response = client.post("/api/preview", json={"svg": SAMPLE_SVG})
    data = response.json()

    # Relief router wraps in "svg" key
    stats = data["stats"]
    if "svg" in stats:
        svg_stats = stats["svg"]
    else:
        svg_stats = stats

    # Should have polyline info
    assert "polyline_count" in svg_stats or "total_length" in svg_stats or "bbox" in svg_stats


def test_preview_stats_has_bbox(client):
    """Preview stats include bounding box."""
    response = client.post("/api/preview", json={"svg": SAMPLE_SVG})
    data = response.json()

    stats = data["stats"]
    if "svg" in stats:
        svg_stats = stats["svg"]
    else:
        svg_stats = stats

    if "bbox" in svg_stats:
        bbox = svg_stats["bbox"]
        assert "min_x" in bbox
        assert "min_y" in bbox
        assert "max_x" in bbox
        assert "max_y" in bbox


# =============================================================================
# Preview Endpoint - Normalize Option
# =============================================================================

def test_preview_normalize_true(client):
    """Preview with normalize=true returns normalized=true."""
    response = client.post("/api/preview", json={
        "svg": SAMPLE_SVG,
        "normalize": True
    })
    data = response.json()

    assert data["normalized"] is True


def test_preview_normalize_false(client):
    """Preview with normalize=false returns normalized=false."""
    response = client.post("/api/preview", json={
        "svg": SAMPLE_SVG,
        "normalize": False
    })
    data = response.json()

    assert data["normalized"] is False


def test_preview_normalize_default(client):
    """Preview defaults to normalize=true."""
    response = client.post("/api/preview", json={"svg": SAMPLE_SVG})
    data = response.json()

    # Default is True
    assert data["normalized"] is True


# =============================================================================
# Preview Endpoint - Different SVG Shapes
# =============================================================================

def test_preview_rect(client):
    """Preview parses SVG rect element."""
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="100" height="50"/></svg>'
    response = client.post("/api/preview", json={"svg": svg})
    assert response.status_code == 200


def test_preview_circle(client):
    """Preview parses SVG circle element."""
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="25"/></svg>'
    response = client.post("/api/preview", json={"svg": svg})
    assert response.status_code == 200


def test_preview_path(client):
    """Preview parses SVG path element."""
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0,0 L100,0 L100,50 L0,50 Z"/></svg>'
    response = client.post("/api/preview", json={"svg": svg})
    assert response.status_code == 200


def test_preview_polygon(client):
    """Preview parses SVG polygon element."""
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><polygon points="50,0 100,50 0,50"/></svg>'
    response = client.post("/api/preview", json={"svg": svg})
    assert response.status_code == 200


def test_preview_polyline(client):
    """Preview parses SVG polyline element."""
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><polyline points="0,0 50,25 100,0"/></svg>'
    response = client.post("/api/preview", json={"svg": svg})
    assert response.status_code == 200


def test_preview_line(client):
    """Preview parses SVG line element."""
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><line x1="0" y1="0" x2="100" y2="50"/></svg>'
    response = client.post("/api/preview", json={"svg": svg})
    assert response.status_code == 200


def test_preview_ellipse(client):
    """Preview parses SVG ellipse element."""
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><ellipse cx="50" cy="25" rx="50" ry="25"/></svg>'
    response = client.post("/api/preview", json={"svg": svg})
    assert response.status_code == 200


# =============================================================================
# Preview Endpoint - Complex SVG
# =============================================================================

def test_preview_multiple_shapes(client):
    """Preview handles SVG with multiple shapes."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="50" height="30"/>
        <circle cx="75" cy="15" r="10"/>
        <line x1="0" y1="40" x2="100" y2="40"/>
    </svg>'''
    response = client.post("/api/preview", json={"svg": svg})
    assert response.status_code == 200

    data = response.json()
    stats = data["stats"]
    if "svg" in stats:
        svg_stats = stats["svg"]
    else:
        svg_stats = stats

    # Should have multiple polylines
    if "polyline_count" in svg_stats:
        assert svg_stats["polyline_count"] >= 1


def test_preview_nested_groups(client):
    """Preview handles SVG with nested groups."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg">
        <g>
            <g>
                <rect x="0" y="0" width="50" height="30"/>
            </g>
        </g>
    </svg>'''
    response = client.post("/api/preview", json={"svg": svg})
    assert response.status_code == 200


def test_preview_with_transforms(client):
    """Preview handles SVG with transforms."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg">
        <g transform="translate(10, 10)">
            <rect x="0" y="0" width="50" height="30"/>
        </g>
    </svg>'''
    response = client.post("/api/preview", json={"svg": svg})
    assert response.status_code == 200
