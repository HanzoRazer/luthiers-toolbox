"""
RMOS Runs v2 Diff Endpoint Tests

Tests the GET /api/rmos/runs_v2/diff/{a}/{b} endpoint for comparing runs.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    runs_dir = tmp_path / "runs" / "rmos"
    atts_dir = tmp_path / "run_attachments"
    runs_dir.mkdir(parents=True, exist_ok=True)
    atts_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(atts_dir))

    try:
        import app.rmos.runs_v2.store as store_mod
        store_mod._default_store = None
    except Exception:
        pass

    from app.main import app
    return TestClient(app)


def _create_run(client: TestClient, *, feed_xy: int, feed_z: int) -> str:
    dxf_path = Path("tests/testdata/mvp_rect_with_island.dxf")
    assert dxf_path.exists(), "Missing MVP DXF fixture"

    with dxf_path.open("rb") as f:
        resp = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("mvp_rect_with_island.dxf", f, "application/dxf")},
            data={
                "tool_d": "6.0",
                "stepover": "0.45",
                "stepdown": "1.5",
                "z_rough": "-3.0",
                "feed_xy": str(feed_xy),
                "feed_z": str(feed_z),
                "safe_z": "5.0",
                "strategy": "Spiral",
                "layer_name": "GEOMETRY",
                "post_id": "GRBL",
            },
        )
    assert resp.status_code == 200, resp.text
    j = resp.json()
    return j["run_id"]


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_diff_endpoint_returns_structured_diff(client: TestClient):
    """Diff endpoint returns structured comparison of two runs."""
    run_a = _create_run(client, feed_xy=1200, feed_z=300)
    run_b = _create_run(client, feed_xy=600, feed_z=1200)

    r = client.get(f"/api/rmos/runs_v2/diff/{run_a}/{run_b}")
    assert r.status_code == 200, r.text
    j = r.json()

    assert j["run_a"] == run_a
    assert j["run_b"] == run_b

    for k in [
        "request_diff",
        "feasibility_diff",
        "decision_diff",
        "hashes_diff",
        "attachments_diff",
    ]:
        assert k in j


@pytest.mark.integration
@pytest.mark.allow_missing_request_id
def test_diff_endpoint_404_on_missing_run(client: TestClient):
    """Diff endpoint returns 404 when a run doesn't exist."""
    run_a = _create_run(client, feed_xy=1200, feed_z=300)
    r = client.get(f"/api/rmos/runs_v2/diff/{run_a}/run_DOES_NOT_EXIST")
    assert r.status_code == 404
