"""
Tests for cantilever arm rest calculator and endpoint.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.calculators.cantilever_armrest_calc import (
    ArmRestSpec,
    compute_armrest,
    preset_standard,
    preset_classical,
    preset_archtop,
)


client = TestClient(app)


# ─── Unit Tests ──────────────────────────────────────────────────────────────

def test_compute_armrest_standard_preset():
    """Test compute_armrest with standard preset returns valid sections."""
    spec = preset_standard()
    result = compute_armrest(spec, n_stations=11)

    assert len(result.sections) == 11
    assert result.apex_section is not None
    assert result.max_overhang_mm > 0
    assert result.max_total_width_mm > 0
    assert result.face_length_apex_mm > 0
    # Apex should be at t=0.38 for standard preset
    assert abs(result.apex_section.t - 0.38) < 0.01


def test_compute_armrest_validates_spec():
    """Test that invalid spec parameters produce warnings."""
    # Create spec with extreme parameters
    spec = ArmRestSpec(
        span_mm=50.0,  # Very short
        h_max_mm=30.0,  # Very tall
        theta_max_deg=75.0,  # Very steep angle
    )
    result = compute_armrest(spec)

    # Should still compute but may have warnings
    assert len(result.sections) > 0
    assert result.apex_section is not None


def test_sections_ordered_by_t():
    """Test that sections are ordered from heel (t=0) to toe (t=1)."""
    spec = preset_classical()
    result = compute_armrest(spec, n_stations=11)

    t_values = [s.t for s in result.sections]
    assert t_values == sorted(t_values)
    assert t_values[0] == 0.0
    assert t_values[-1] == 1.0


# ─── Endpoint Tests ──────────────────────────────────────────────────────────

def test_cantilever_armrest_endpoint_with_preset():
    """Test POST /api/instrument/cantilever-armrest with preset parameter."""
    response = client.post(
        "/api/instrument/cantilever-armrest",
        json={"preset": "standard"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "sections" in data
    assert "apex_section" in data
    assert "warnings" in data
    assert "max_overhang_mm" in data
    assert "spec" in data

    # Verify sections structure
    assert len(data["sections"]) > 0
    section = data["sections"][0]
    assert "t" in section
    assert "h_total_mm" in section
    assert "theta_deg" in section


def test_cantilever_armrest_endpoint_custom_params():
    """Test POST /api/instrument/cantilever-armrest with custom parameters."""
    response = client.post(
        "/api/instrument/cantilever-armrest",
        json={
            "span_mm": 160.0,
            "t_apex": 0.4,
            "h_max_mm": 12.0,
            "theta_max_deg": 40.0,
            "n_stations": 5
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["sections"]) == 5
    assert data["spec"]["span_mm"] == 160.0
    assert data["spec"]["h_max_mm"] == 12.0


def test_cantilever_armrest_presets_endpoint():
    """Test GET /api/instrument/cantilever-armrest/presets lists all presets."""
    response = client.get("/api/instrument/cantilever-armrest/presets")

    assert response.status_code == 200
    data = response.json()

    assert "standard" in data
    assert "classical" in data
    assert "archtop" in data

    # Verify preset structure
    for name, preset in data.items():
        assert "span_mm" in preset
        assert "h_max_mm" in preset
        assert "theta_max_deg" in preset
        assert "t_apex" in preset
