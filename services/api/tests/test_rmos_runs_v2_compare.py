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

    # Reset store singleton if present
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
    assert j.get("ok") is True
    return j["run_id"]


def test_compare_runs_returns_summary_and_diffs(client: TestClient):
    # A: likely GREEN; B: likely YELLOW (feed_z > feed_xy triggers warning/rule)
    run_a = _create_run(client, feed_xy=1200, feed_z=300)
    run_b = _create_run(client, feed_xy=600, feed_z=1200)

    r = client.get(f"/api/rmos/runs_v2/compare/{run_a}/{run_b}")
    assert r.status_code == 200, r.text
    j = r.json()

    assert "summary" in j
    for k in [
        "risk_changed",
        "blocking_changed",
        "feasibility_changed",
        "cam_changed",
        "gcode_changed",
        "attachments_changed",
        "override_changed",
    ]:
        assert k in j["summary"]

    assert "decision_diff" in j
    assert "before" in j["decision_diff"]
    assert "after" in j["decision_diff"]
    assert "risk_level" in j["decision_diff"]["before"]
    assert "risk_level" in j["decision_diff"]["after"]

    assert "feasibility_diff" in j
    assert "rules_added" in j["feasibility_diff"]
    assert "rules_removed" in j["feasibility_diff"]

    assert "param_diff" in j
    assert isinstance(j["param_diff"], dict)

    assert "artifact_diff" in j
    assert "gcode_sha256" in j["artifact_diff"]


def test_compare_runs_404_on_missing_run(client: TestClient):
    run_a = _create_run(client, feed_xy=1200, feed_z=300)
    r = client.get(f"/api/rmos/runs_v2/compare/{run_a}/run_DOES_NOT_EXIST")
    assert r.status_code == 404
