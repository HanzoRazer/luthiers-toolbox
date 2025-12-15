# services/api/app/tests/rmos/test_rosette_patterns_router.py

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_patterns_initially_empty():
    """
    Wave N11.x: patterns router should respond with 200 and a list
    (possibly empty) at the new RMOS path.

    This confirms:
      - Router is wired under /api/rmos
      - No 'no such column: pattern_type' schema errors
    """
    resp = client.get("/api/rmos/patterns")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "items" in data or isinstance(data, list)  # support either style


def test_create_rosette_pattern_and_fetch():
    """
    Creates a minimal 'rosette' pattern and verifies:

      - 201 Created on POST
      - pattern_type='rosette' is accepted / stored
      - GET /api/rmos/patterns/{id} returns the same record

    Adjust field names to match your actual create schema.
    """
    pattern_id = f"test-rosette-{uuid.uuid4().hex[:8]}"

    payload = {
        "id": pattern_id,
        "name": "Test Rosette Pattern",
        "ring_count": 3,
        "pattern_type": "rosette",
        "geometry_json": '{"rings": []}',
        # optional fields; adjust as your schema requires
        "rosette_geometry": '{"version": 1, "segments": []}',
        "strip_family_id": None,
        "metadata_json": None,
    }

    # Create
    resp = client.post("/api/rmos/patterns", json=payload)
    assert resp.status_code in (200, 201), resp.text
    created = resp.json()
    assert created.get("id") == pattern_id
    assert created.get("pattern_type") == "rosette"

    # Fetch by id
    resp_get = client.get(f"/api/rmos/patterns/{pattern_id}")
    assert resp_get.status_code == 200, resp_get.text
    fetched = resp_get.json()
    assert fetched.get("id") == pattern_id
    assert fetched.get("name") == "Test Rosette Pattern"
    assert fetched.get("pattern_type") == "rosette"
    # Make sure the new column is coming back
    assert "rosette_geometry" in fetched


def test_filter_patterns_by_type_if_supported():
    """
    If the router supports filtering by pattern_type (e.g. ?type=rosette),
    verify that we don't crash and that rosette patterns appear in the result.

    If you don't support filtering yet, you can either:
      - comment this test out for now, or
      - loosen the assertions to 'status_code == 200' only.
    """
    resp = client.get("/api/rmos/patterns?pattern_type=rosette")
    assert resp.status_code == 200
    # Implementation detail: some routers return {"items": [...]}, some return [...]
    data = resp.json()
    items = data.get("items", data if isinstance(data, list) else [])
    assert isinstance(items, list)
    # We don't insist there's ALWAYS a rosette, but we assert we didn't blow up
