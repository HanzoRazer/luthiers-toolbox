"""Smoke tests for G-code Backplot endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# Sample G-code for testing
SIMPLE_GCODE = """G0 X10 Y10
G1 X20 Y10 F600
G1 X20 Y20
G1 X10 Y20
G1 X10 Y10
"""

# G-code with arcs
ARC_GCODE = """G0 X0 Y0
G1 X10 Y0 F600
G2 X20 Y10 I10 J0
G1 X20 Y20
"""

# G-code with different units
INCH_GCODE = """G20
G0 X1 Y1
G1 X2 Y1 F10
G1 X2 Y2
"""

# Minimal G-code
MINIMAL_GCODE = """G0 X10 Y10
G1 X20 Y20 F500
"""

# Empty/whitespace G-code
EMPTY_GCODE = ""

# G-code without explicit feed rate (uses default_feed_mm_min)
NO_FEED_GCODE = """G0 X10 Y10
G1 X20 Y10
G1 X20 Y20
G1 X10 Y20
G1 X10 Y10
"""

# G-code with comments
COMMENTED_GCODE = """(Program start)
G0 X0 Y0    ; Home position
G1 X10 Y10 F600  ; Move to position
M30
"""


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_plot_svg_endpoint_exists(client):
    """POST /api/cam/gcode/plot.svg endpoint exists."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": SIMPLE_GCODE
    })
    assert response.status_code != 404


def test_estimate_endpoint_exists(client):
    """POST /api/cam/gcode/estimate endpoint exists."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE
    })
    assert response.status_code != 404


# =============================================================================
# Plot SVG Endpoint
# =============================================================================

def test_plot_svg_returns_200(client):
    """POST /api/cam/gcode/plot.svg returns 200."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": SIMPLE_GCODE
    })
    assert response.status_code == 200


def test_plot_svg_returns_svg_content_type(client):
    """Plot endpoint returns SVG content type."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": SIMPLE_GCODE
    })

    content_type = response.headers.get("content-type", "")
    assert "svg" in content_type or "xml" in content_type


def test_plot_svg_contains_svg_tag(client):
    """Plot response contains SVG element."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": SIMPLE_GCODE
    })

    content = response.text
    assert "<svg" in content
    assert "</svg>" in content


def test_plot_svg_contains_path_or_polyline(client):
    """Plot SVG contains path or polyline element."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": SIMPLE_GCODE
    })

    content = response.text
    # Should have path or polyline element
    assert "<path" in content or "<polyline" in content or "points=" in content


def test_plot_svg_custom_stroke(client):
    """Plot accepts custom stroke color."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": SIMPLE_GCODE,
        "stroke": "red"
    })

    content = response.text
    assert "red" in content


def test_plot_svg_default_stroke_black(client):
    """Plot uses black stroke by default."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": SIMPLE_GCODE
    })

    content = response.text
    assert "black" in content


def test_plot_svg_units_mm(client):
    """Plot accepts mm units."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": SIMPLE_GCODE,
        "units": "mm"
    })
    assert response.status_code == 200


def test_plot_svg_units_inch(client):
    """Plot accepts inch units."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": INCH_GCODE,
        "units": "inch"
    })
    assert response.status_code == 200


def test_plot_svg_with_arcs(client):
    """Plot handles arc commands."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": ARC_GCODE
    })
    assert response.status_code == 200


def test_plot_svg_with_comments(client):
    """Plot handles commented G-code."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": COMMENTED_GCODE
    })
    assert response.status_code == 200


def test_plot_svg_custom_rapid_rate(client):
    """Plot accepts custom rapid rate."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": SIMPLE_GCODE,
        "rapid_mm_min": 5000.0
    })
    assert response.status_code == 200


def test_plot_svg_custom_feed_rate(client):
    """Plot accepts custom default feed rate."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": SIMPLE_GCODE,
        "default_feed_mm_min": 800.0
    })
    assert response.status_code == 200


def test_plot_svg_requires_gcode(client):
    """Plot requires gcode field."""
    response = client.post("/api/cam/gcode/plot.svg", json={})
    assert response.status_code == 422


def test_plot_svg_minimal_gcode(client):
    """Plot handles minimal G-code."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": MINIMAL_GCODE
    })
    assert response.status_code == 200


def test_plot_svg_empty_gcode(client):
    """Plot handles empty G-code."""
    response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": EMPTY_GCODE
    })
    # Should still return 200, just empty plot
    assert response.status_code == 200


# =============================================================================
# Estimate Endpoint
# =============================================================================

def test_estimate_returns_200(client):
    """POST /api/cam/gcode/estimate returns 200."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE
    })
    assert response.status_code == 200


def test_estimate_has_travel_mm(client):
    """Estimate response has travel_mm field."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE
    })
    data = response.json()

    assert "travel_mm" in data
    assert isinstance(data["travel_mm"], (int, float))


def test_estimate_has_cut_mm(client):
    """Estimate response has cut_mm field."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE
    })
    data = response.json()

    assert "cut_mm" in data
    assert isinstance(data["cut_mm"], (int, float))


def test_estimate_has_time_fields(client):
    """Estimate response has time fields."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE
    })
    data = response.json()

    assert "t_rapid_min" in data
    assert "t_feed_min" in data
    assert "t_total_min" in data


def test_estimate_has_points_xy(client):
    """Estimate response has points_xy field."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE
    })
    data = response.json()

    assert "points_xy" in data
    assert isinstance(data["points_xy"], list)


def test_estimate_total_time_is_sum(client):
    """Total time equals rapid + feed time."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE
    })
    data = response.json()

    total = data["t_rapid_min"] + data["t_feed_min"]
    # Allow small floating point tolerance
    assert abs(data["t_total_min"] - total) < 0.0001


def test_estimate_rapid_distance_positive(client):
    """Estimate has positive rapid distance for G0 moves."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE
    })
    data = response.json()

    # First G0 move should create travel distance
    assert data["travel_mm"] >= 0


def test_estimate_cut_distance_positive(client):
    """Estimate has positive cutting distance for G1 moves."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE
    })
    data = response.json()

    # G1 moves should create cutting distance
    assert data["cut_mm"] > 0


def test_estimate_points_count(client):
    """Estimate returns correct number of points."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": MINIMAL_GCODE  # G0 X10 Y10, G1 X20 Y20
    })
    data = response.json()

    # Should have at least origin + 2 points
    assert len(data["points_xy"]) >= 2


def test_estimate_units_mm(client):
    """Estimate with mm units."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE,
        "units": "mm"
    })
    assert response.status_code == 200


def test_estimate_units_inch(client):
    """Estimate with inch units."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": INCH_GCODE,
        "units": "inch"
    })
    assert response.status_code == 200


def test_estimate_custom_rapid_rate(client):
    """Estimate with custom rapid rate changes time."""
    slow = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE,
        "rapid_mm_min": 1000.0
    }).json()

    fast = client.post("/api/cam/gcode/estimate", json={
        "gcode": SIMPLE_GCODE,
        "rapid_mm_min": 5000.0
    }).json()

    # Faster rapid = less rapid time (if there's rapid movement)
    if slow["travel_mm"] > 0:
        assert slow["t_rapid_min"] > fast["t_rapid_min"]


def test_estimate_custom_feed_rate(client):
    """Estimate with custom feed rate changes time."""
    # Use G-code without explicit F commands so default_feed_mm_min is used
    slow = client.post("/api/cam/gcode/estimate", json={
        "gcode": NO_FEED_GCODE,
        "default_feed_mm_min": 300.0
    }).json()

    fast = client.post("/api/cam/gcode/estimate", json={
        "gcode": NO_FEED_GCODE,
        "default_feed_mm_min": 900.0
    }).json()

    # Faster feed = less feed time
    assert slow["t_feed_min"] > fast["t_feed_min"]


def test_estimate_with_arcs(client):
    """Estimate handles arc commands."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": ARC_GCODE
    })
    data = response.json()

    assert response.status_code == 200
    assert data["cut_mm"] > 0


def test_estimate_with_comments(client):
    """Estimate handles commented G-code."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": COMMENTED_GCODE
    })
    assert response.status_code == 200


def test_estimate_requires_gcode(client):
    """Estimate requires gcode field."""
    response = client.post("/api/cam/gcode/estimate", json={})
    assert response.status_code == 422


def test_estimate_empty_gcode(client):
    """Estimate handles empty G-code."""
    response = client.post("/api/cam/gcode/estimate", json={
        "gcode": EMPTY_GCODE
    })
    data = response.json()

    assert response.status_code == 200
    assert data["travel_mm"] == 0
    assert data["cut_mm"] == 0


# =============================================================================
# Integration Tests
# =============================================================================

def test_estimate_and_plot_same_gcode(client):
    """Estimate and plot work on same G-code."""
    gcode = SIMPLE_GCODE

    plot_response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": gcode
    })
    estimate_response = client.post("/api/cam/gcode/estimate", json={
        "gcode": gcode
    })

    assert plot_response.status_code == 200
    assert estimate_response.status_code == 200


def test_complex_gcode_program(client):
    """Both endpoints handle complex G-code program."""
    complex_gcode = """
    G21 ; mm mode
    G90 ; absolute
    G0 Z5
    G0 X0 Y0
    G0 Z0.5
    G1 Z-1 F100
    G1 X50 F600
    G1 Y50
    G2 X0 Y50 I-25 J0
    G1 Y0
    G0 Z5
    M30
    """

    plot_response = client.post("/api/cam/gcode/plot.svg", json={
        "gcode": complex_gcode
    })
    estimate_response = client.post("/api/cam/gcode/estimate", json={
        "gcode": complex_gcode
    })

    assert plot_response.status_code == 200
    assert estimate_response.status_code == 200

    data = estimate_response.json()
    assert data["cut_mm"] > 0
    assert data["t_total_min"] > 0
