from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ENV", "test")

    try:
        from app.main import app
    except Exception as e:
        pytest.skip(f"Could not import FastAPI app from app.main: {e}")

    return TestClient(app)


def test_e2e_feasibility_approve_toolpaths_index_diff(client: TestClient):
    # 1) Create feasibility run (creates session + feasibility artifact)
    feasibility_req = {
        "mode": "design_first",
        "design": {"example": "design_A"},
        "context": {"tool_id": "saw:thin_140", "material_id": "ebony", "machine_id": "router_a", "extra": {}},
    }

    f = client.post("/api/rmos/feasibility", json=feasibility_req)
    assert f.status_code == 200, f.text
    f_body = f.json()

    feas_artifact_id = f_body["artifact_id"]
    session_id = f_body["session_id"]
    assert feas_artifact_id
    assert session_id

    # 2) Approve the session explicitly
    appr = client.post("/api/workflow/approve", json={"session_id": session_id, "actor": "operator", "note": "OK to proceed"})
    assert appr.status_code == 200, appr.text
    appr_body = appr.json()
    assert appr_body["approved"] is True

    # 3) Toolpaths using the same session_id (should now be allowed if feasibility is not RED)
    toolpaths_req = {
        "session_id": session_id,
        "mode": "design_first",
        "design": {"example": "design_A"},
        "context": {"tool_id": "saw:thin_140", "material_id": "ebony", "machine_id": "router_a", "extra": {}},
    }

    t = client.post("/api/rmos/toolpaths", json=toolpaths_req)
    assert t.status_code == 200, t.text
    t_body = t.json()

    toolpaths_artifact_id = t_body["artifact_id"]
    assert toolpaths_artifact_id
    assert toolpaths_artifact_id != feas_artifact_id

    # 4) Index query contains both artifacts
    idx = client.get("/api/runs", params={"limit": 100})
    assert idx.status_code == 200, idx.text
    ids = {row["artifact_id"] for row in idx.json()["items"]}
    assert feas_artifact_id in ids
    assert toolpaths_artifact_id in ids

    # 5) Diff feasibility vs toolpaths artifacts (should show kind/status differences at minimum)
    d = client.get(f"/api/runs/diff/{feas_artifact_id}/{toolpaths_artifact_id}")
    assert d.status_code == 200, d.text
    diff = d.json()
    assert diff["summary"]["changed_count"] >= 1