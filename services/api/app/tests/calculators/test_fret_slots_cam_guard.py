# services/api/app/tests/calculators/test_fret_slots_cam_guard.py

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_fret_slots_preview_route_defined():
    """
    Guard 1: Ensure the preview route exists under the agreed path.
    We use GET here just to confirm that the route is wired.
    If the endpoint is POST-only, FastAPI will return 405 (Method Not Allowed),
    which still proves the route exists. A 404 would mean it's missing.
    """
    resp = client.get("/api/cam/fret_slots/preview")
    assert resp.status_code in (200, 405), f"Expected 200/405, got {resp.status_code}"


def test_fret_slots_export_multi_route_defined():
    """
    Guard 2: Ensure the multi-post export route exists.
    Path is intentionally /export_multi to match the current RMOS/CAM spec.
    Again, 200 or 405 = route exists; 404 = missing.
    """
    resp = client.get("/api/cam/fret_slots/export_multi")
    assert resp.status_code in (200, 405), f"Expected 200/405, got {resp.status_code}"


def test_fret_slots_preview_does_not_500_on_basic_payload():
    """
    Guard 3: Hitting the preview endpoint with a plausible payload should NOT 404/500.
    - 200: fully implemented and happy.
    - 400: model loading error (acceptable during development)
    - 422: request validation error (schema mismatch, missing fields) is acceptable
      while we align the Pydantic model.
    - 404 / 500: NOT acceptable; indicates broken routing or unhandled exception.
    """
    payload = {
        # Adjust these field names to match your FretSlotsPreviewRequest model.
        "model_id": "benedetto_17",
        "fret_count": 20,
        "slot_depth_mm": 2.0,
        "slot_width_mm": 0.6,
        # Optional: "mode": "straight",
    }
    resp = client.post("/api/cam/fret_slots/preview", json=payload)
    assert resp.status_code not in (404, 500), (
        f"Preview route should not 404/500, got {resp.status_code}: {resp.text}"
    )
    assert resp.status_code in (200, 400, 422), (
        f"Expected 200/400/422 for preview, got {resp.status_code}"
    )


def test_fret_slots_export_multi_does_not_500_on_basic_payload():
    """
    Guard 4: Hitting the multi-post export endpoint with a plausible payload
    should NOT 404/500.
    This validates:
    - Endpoint is wired correctly.
    - Basic serialization / response generation does not explode.
    """
    payload = {
        # Adjust names to match your actual request model.
        "model_id": "benedetto_17",
        "fret_count": 20,
        "slot_depth_mm": 2.0,
        "slot_width_mm": 0.6,
        "post_ids": ["grbl"],  # e.g. GRBL, mach4, linuxcnc
    }
    resp = client.post("/api/cam/fret_slots/export_multi", json=payload)
    assert resp.status_code not in (404, 500), (
        f"Export route should not 404/500, got {resp.status_code}: {resp.text}"
    )
    assert resp.status_code in (200, 422), (
        f"Expected 200 or 422 for export_multi, got {resp.status_code}"
    )
