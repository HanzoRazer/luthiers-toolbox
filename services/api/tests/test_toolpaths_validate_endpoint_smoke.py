# services/api/tests/test_toolpaths_validate_endpoint_smoke.py
from __future__ import annotations

from fastapi.testclient import TestClient


def test_toolpaths_validate_endpoint_smoke(monkeypatch):
    """
    Endpoint smoke test:
      - mounts the router
      - stubs runs_v2.store.get_run
      - POSTs to /api/saw/batch/toolpaths/validate
      - verifies response structure + success
    """
    # Import module for patching BEFORE importing app
    from app.rmos.runs_v2 import store as runs_store

    fake_toolpaths_artifact = {
        "id": "tp1",
        "kind": "saw_batch_toolpaths",
        "payload": {
            "gcode_text": "\n".join(
                [
                    "G21",
                    "G90",
                    "M3",
                    "G0 Z5.0",
                    "G1 X10.0 Y0.0 Z0.0 F250.0",
                    "G1 X20.0 Y0.0 Z0.0 F250.0",
                    "G0 Z5.0",
                    "M5",
                    "M30",
                ]
            )
        },
    }

    def _fake_get_run(run_id: str):
        assert run_id == "tp1"
        return fake_toolpaths_artifact

    # Use import-based patching
    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)

    from app.main import app

    client = TestClient(app)

    resp = client.post(
        "/api/saw/batch/toolpaths/validate",
        json={
            "toolpaths_artifact_id": "tp1",
            "safe_z_mm": 5.0,
            "bounds_mm": None,
            "require_units_mm": True,
            "require_absolute": True,
            "require_xy_plane": False,
            "require_spindle_on": True,
            "require_feed_on_cut": True,
        },
    )

    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["ok"] is True
    assert data["errors"] == []
    assert "warnings" in data
    assert "summary" in data

    summary = data["summary"]
    assert summary["units"] == "mm"
    assert summary["distance_mode"] == "absolute"
    assert summary["spindle_on"] is True
    assert "bounds" in summary
