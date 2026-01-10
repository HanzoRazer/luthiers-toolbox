from __future__ import annotations

import os

from fastapi.testclient import TestClient


def test_diff_endpoint_persists_full_diff_as_attachment_when_large(monkeypatch, tmp_path):
    """
    Proves end-to-end contract:
      - response preview is bounded
      - full diff is retrievable via existing attachment route:
          GET /api/rmos/runs/{run_id}/attachments/{sha256}
    """
    from app.main import app

    # Isolate attachments for the test
    attachments_dir = tmp_path / "attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)
    os.environ["RMOS_RUN_ATTACHMENTS_DIR"] = str(attachments_dir)

    # Fake runs
    left = {"id": "A", "payload": {"x": "1"}}
    right = {"id": "B", "payload": {"x": "2"}}

    def _fake_get_run(rid: str):
        return {"A": left, "B": right}.get(rid)

    # Fake diff builder -> huge string
    def _fake_build_diff(_l, _r):
        return "HEADER\n" + ("line\n" * 100000) + "TAIL\n"

    # Patch where imported, not where defined (api_runs does `from .store import get_run`)
    monkeypatch.setattr("app.rmos.runs_v2.api_runs.get_run", _fake_get_run)
    monkeypatch.setattr("app.rmos.runs_v2.api_runs.build_diff", _fake_build_diff)

    c = TestClient(app)
    r = c.get(
        "/api/rmos/runs/diff",
        params={"left_id": "A", "right_id": "B", "preview_max_chars": 2000},
    )
    assert r.status_code == 200
    data = r.json()

    assert data["left_id"] == "A"
    assert data["right_id"] == "B"
    assert data["diff_kind"] == "unified"
    assert data["truncated"] is True
    assert len(data["preview"]) == 2000
    assert data["diff_attachment"] is not None
    assert data["diff_attachment"]["run_id"] == "B"
    assert data["diff_attachment"]["sha256"]
    assert data["diff_attachment"]["filename"].endswith(".diff")

    sha = data["diff_attachment"]["sha256"]
    run_id = data["diff_attachment"]["run_id"]

    # Download full diff via existing attachment API
    rr = c.get(f"/api/rmos/runs/{run_id}/attachments/{sha}")
    assert rr.status_code == 200
    body = rr.content.decode("utf-8", errors="replace")
    assert "TAIL" in body
    assert len(body) > len(data["preview"])
