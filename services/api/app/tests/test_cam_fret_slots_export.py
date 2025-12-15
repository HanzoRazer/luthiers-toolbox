# services/api/app/tests/test_cam_fret_slots_export.py

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_export_single_grbl_smoke():
    """
    Test single-post export endpoint with GRBL post-processor.
    
    Validates:
    - Endpoint responds with 200
    - Response includes model_id, post_id, gcode
    - G-code contains G21 (mm units) marker
    """
    resp = client.post(
        "/api/cam/fret_slots/export",
        json={
            "model_id": "benedetto_17",
            "post_id": "grbl",
            "slot_depth_mm": 2.0,
            "slot_width_mm": 0.6,
            "compensation_mm": 0.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_id"] == "benedetto_17"
    assert data["post_id"] == "grbl"
    assert "gcode" in data
    assert "G21" in data["gcode"]  # mm units marker


def test_export_multi_posts_smoke():
    """
    Test multi-post export endpoint with 3 post-processors.
    
    Validates:
    - Endpoint responds with 200
    - Response includes exports array with 3 items
    - All requested post_ids are present in response
    """
    resp = client.post(
        "/api/cam/fret_slots/export_multi",
        json={
            "model_id": "benedetto_17",
            "post_ids": ["grbl", "mach4", "linuxcnc"],
            "slot_depth_mm": 2.0,
            "slot_width_mm": 0.6,
            "compensation_mm": 0.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_id"] == "benedetto_17"
    exports = data["exports"]
    assert len(exports) == 3
    posts = {e["post_id"] for e in exports}
    assert posts == {"grbl", "mach4", "linuxcnc"}


def test_export_mach4_header():
    """
    Test that Mach4 export has correct header comment.
    """
    resp = client.post(
        "/api/cam/fret_slots/export",
        json={
            "model_id": "benedetto_17",
            "post_id": "mach4",
            "slot_depth_mm": 2.0,
            "slot_width_mm": 0.6,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Mach4" in data["gcode"]


def test_export_linuxcnc_header():
    """
    Test that LinuxCNC export has correct header comment.
    """
    resp = client.post(
        "/api/cam/fret_slots/export",
        json={
            "model_id": "benedetto_17",
            "post_id": "linuxcnc",
            "slot_depth_mm": 2.0,
            "slot_width_mm": 0.6,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "LinuxCNC" in data["gcode"]


def test_export_includes_filename_hint():
    """
    Test that response includes filename_hint for download.
    """
    resp = client.post(
        "/api/cam/fret_slots/export",
        json={
            "model_id": "lp_24_75",
            "post_id": "grbl",
            "slot_depth_mm": 3.0,
            "slot_width_mm": 0.6,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "filename_hint" in data
    assert "lp_24_75" in data["filename_hint"]
    assert ".nc" in data["filename_hint"]


def test_export_multi_different_models():
    """
    Test that multi-export works with different instrument models.
    """
    resp = client.post(
        "/api/cam/fret_slots/export_multi",
        json={
            "model_id": "lp_24_75",
            "post_ids": ["grbl", "mach4"],
            "slot_depth_mm": 3.0,
            "slot_width_mm": 0.6,
            "compensation_mm": 0.5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_id"] == "lp_24_75"
    assert len(data["exports"]) == 2
