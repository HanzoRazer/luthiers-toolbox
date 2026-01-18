# services/api/tests/test_toolpaths_download_gcode_redirect.py
from __future__ import annotations

from fastapi.testclient import TestClient


def test_toolpaths_download_gcode_redirects(monkeypatch):
    # Import module for patching BEFORE importing app
    from app.rmos.runs_v2 import store as runs_store

    def _fake_get_run(run_id: str):
        assert run_id == "tp1"
        return {
            "id": "tp1",
            "kind": "saw_batch_toolpaths",
            "payload": {"attachments": {"gcode_sha256": "abc123"}},
        }

    monkeypatch.setattr(runs_store, "get_run", _fake_get_run)

    from app.main import app

    c = TestClient(app)
    r = c.get("/api/saw/batch/toolpaths/tp1/download/gcode", follow_redirects=False)
    assert r.status_code in (301, 302, 307, 308)
    assert r.headers["location"] == "/api/rmos/attachments/abc123"
