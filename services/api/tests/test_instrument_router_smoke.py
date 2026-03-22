"""
Smoke tests for instrument_router.py (23 endpoints).

Each endpoint returns 200 or 422, not 404.
Coverage target: wiring verification, not business logic.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

PREFIX = "/api/instrument"


# ---------------------------------------------------------------------------
# GET endpoints (7)
# ---------------------------------------------------------------------------

def test_geometry_presets_returns_200():
    """GET /geometry/presets"""
    r = client.get(f"{PREFIX}/geometry/presets")
    assert r.status_code == 200


def test_string_tension_presets_returns_200():
    """GET /string-tension/presets"""
    r = client.get(f"{PREFIX}/string-tension/presets")
    assert r.status_code == 200


def test_soundhole_body_styles_returns_200():
    """GET /soundhole/body-styles"""
    r = client.get(f"{PREFIX}/soundhole/body-styles")
    assert r.status_code == 200


def test_kerfing_types_returns_200():
    """GET /kerfing/types"""
    r = client.get(f"{PREFIX}/kerfing/types")
    assert r.status_code == 200


def test_tuning_machine_post_heights_returns_200():
    """GET /tuning-machine/post-heights"""
    r = client.get(f"{PREFIX}/tuning-machine/post-heights")
    assert r.status_code == 200


def test_tuning_machine_string_trees_returns_200():
    """GET /tuning-machine/string-trees"""
    r = client.get(f"{PREFIX}/tuning-machine/string-trees")
    assert r.status_code == 200


def test_nut_compensation_types_returns_200():
    """GET /nut-compensation/types"""
    r = client.get(f"{PREFIX}/nut-compensation/types")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# POST endpoints (16)
# ---------------------------------------------------------------------------

def test_geometry_bridge_returns_200():
    """POST /geometry/bridge"""
    r = client.post(f"{PREFIX}/geometry/bridge", json={
        "scale_length_mm": 648.0
    })
    assert r.status_code == 200


def test_geometry_radius_profile_returns_200():
    """POST /geometry/radius-profile"""
    r = client.post(f"{PREFIX}/geometry/radius-profile", json={
        "fret_count": 22,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    assert r.status_code == 200


def test_geometry_radius_at_position_returns_200():
    """POST /geometry/radius-at-position"""
    r = client.post(f"{PREFIX}/geometry/radius-at-position", json={
        "position_mm": 300.0,
        "fretboard_length_mm": 480.0,
        "base_radius_mm": 184.0,
        "end_radius_mm": 305.0
    })
    assert r.status_code == 200


def test_geometry_standard_guitar_returns_200():
    """POST /geometry/standard-guitar"""
    r = client.post(f"{PREFIX}/geometry/standard-guitar", json={
        "preset_name": "dreadnought"
    })
    # Could be 200 or 422 if preset not found
    assert r.status_code in (200, 422, 400)


def test_string_tension_returns_200():
    """POST /string-tension"""
    r = client.post(f"{PREFIX}/string-tension", json={
        "scale_length_mm": 648.0
    })
    assert r.status_code == 200


def test_soundhole_returns_200():
    """POST /soundhole"""
    r = client.post(f"{PREFIX}/soundhole", json={
        "body_style": "dreadnought",
        "body_length_mm": 510.0
    })
    assert r.status_code == 200


def test_soundhole_check_position_returns_200():
    """POST /soundhole/check-position"""
    r = client.post(f"{PREFIX}/soundhole/check-position", json={
        "diameter_mm": 100.0,
        "position_mm": 255.0,
        "body_length_mm": 510.0
    })
    assert r.status_code == 200


def test_kerfing_returns_200():
    """POST /kerfing"""
    r = client.post(f"{PREFIX}/kerfing", json={
        "side_depth_mm": 100.0,
        "body_style": "dreadnought"
    })
    assert r.status_code == 200


def test_tuning_machine_returns_200():
    """POST /tuning-machine"""
    r = client.post(f"{PREFIX}/tuning-machine", json={
        "headstock_angle_deg": 14.0,
        "nut_to_post_mm": 50.0,
        "post_height_mm": 10.0,
        "string_name": "E"
    })
    assert r.status_code == 200


def test_tuning_machine_required_height_returns_200():
    """POST /tuning-machine/required-height"""
    r = client.post(f"{PREFIX}/tuning-machine/required-height", json={
        "headstock_angle_deg": 14.0,
        "nut_to_post_mm": 50.0
    })
    assert r.status_code == 200


def test_nut_compensation_returns_200():
    """POST /nut-compensation"""
    r = client.post(f"{PREFIX}/nut-compensation", json={
        "action_at_nut_mm": 0.5,
        "fret_height_mm": 1.0,
        "scale_length_mm": 648.0
    })
    assert r.status_code == 200


def test_nut_compensation_compare_returns_200():
    """POST /nut-compensation/compare"""
    r = client.post(f"{PREFIX}/nut-compensation/compare", json={
        "action_at_nut_mm": 0.5,
        "fret_height_mm": 1.0,
        "scale_length_mm": 648.0
    })
    assert r.status_code == 200


def test_nut_compensation_zero_fret_positions_returns_200():
    """POST /nut-compensation/zero-fret-positions"""
    r = client.post(f"{PREFIX}/nut-compensation/zero-fret-positions", json={
        "scale_length_mm": 648.0,
        "fret_count": 22
    })
    assert r.status_code == 200


def test_saddle_force_returns_200():
    """POST /saddle-force"""
    r = client.post(f"{PREFIX}/saddle-force", json={
        "string_tensions_n": [80.0, 90.0, 100.0, 90.0, 80.0, 70.0],
        "break_angles_deg": [15.0, 15.0, 15.0, 15.0, 15.0, 15.0]
    })
    assert r.status_code == 200


def test_top_deflection_returns_200():
    """POST /top-deflection"""
    r = client.post(f"{PREFIX}/top-deflection", json={
        "load_n": 500.0,
        "plate": {
            "E_L_GPa": 12.0,
            "thickness_mm": 2.8,
            "length_mm": 500.0,
            "width_mm": 400.0
        }
    })
    assert r.status_code == 200


def test_brace_sizing_returns_200():
    """POST /brace-sizing"""
    r = client.post(f"{PREFIX}/brace-sizing", json={
        "max_deflection_mm": 1.5,
        "applied_load_n": 500.0,
        "plate_length_mm": 500.0
    })
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Validation tests (422 expected)
# ---------------------------------------------------------------------------

def test_geometry_bridge_missing_field_returns_422():
    """POST /geometry/bridge with missing required field"""
    r = client.post(f"{PREFIX}/geometry/bridge", json={})
    assert r.status_code == 422


def test_string_tension_invalid_scale_returns_422():
    """POST /string-tension with invalid scale length"""
    r = client.post(f"{PREFIX}/string-tension", json={
        "scale_length_mm": -100.0
    })
    assert r.status_code == 422


def test_soundhole_missing_body_style_returns_422():
    """POST /soundhole with missing body_style"""
    r = client.post(f"{PREFIX}/soundhole", json={
        "body_length_mm": 510.0
    })
    assert r.status_code == 422


def test_saddle_force_mismatched_arrays_returns_422_or_400():
    """POST /saddle-force with mismatched array lengths"""
    r = client.post(f"{PREFIX}/saddle-force", json={
        "string_tensions_n": [80.0, 90.0],
        "break_angles_deg": [15.0]
    })
    # Could be 422 (validation) or 400 (business logic error)
    assert r.status_code in (400, 422)
