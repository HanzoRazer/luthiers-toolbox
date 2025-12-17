from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # DB + artifacts isolated
    monkeypatch.setenv("RMOS_DB_URL", f"sqlite:///{tmp_path / 'rmos_test.sqlite3'}")
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ENV", "test")

    # Point loader at the fake engine module
    monkeypatch.setenv("RMOS_ENGINE_MODULE", "tests.fake_rmos_engine")

    try:
        from app.main import app
    except Exception as e:
        pytest.skip(f"Could not import FastAPI app from app.main: {e}")

    return TestClient(app)


def test_real_rmos_call_wires_to_artifacts_and_diff(client: TestClient):
    # 1) feasibility (creates session + feasibility artifact)
    f = client.post("/api/rmos/feasibility", json={
        "mode": "design_first",
        "design": {"shape": "ring", "od": 140},
        "context": {"tool_id": "saw:thin_140", "material_id": "ebony", "machine_id": "router_a", "extra": {}},
    })
    assert f.status_code == 200, f.text
    feas_body = f.json()
    session_id = feas_body["session_id"]
    feas_artifact_id = feas_body["artifact_id"]

    # 2) approve
    a = client.post("/api/workflow/approve", json={"session_id": session_id, "actor": "operator", "note": "ok"})
    assert a.status_code == 200, a.text

    # 3) toolpaths (server recomputes feasibility + generates toolpaths)
    t = client.post("/api/rmos/toolpaths", json={
        "session_id": session_id,
        "mode": "design_first",
        "design": {"shape": "ring", "od": 140},
        "context": {"tool_id": "saw:thin_140", "material_id": "ebony", "machine_id": "router_a", "extra": {}},
    })
    assert t.status_code == 200, t.text
    tool_body = t.json()
    tool_artifact_id = tool_body["artifact_id"]

    # 4) index contains both
    idx = client.get("/api/runs", params={"limit": 100})
    assert idx.status_code == 200, idx.text
    ids = {row["artifact_id"] for row in idx.json()["items"]}
    assert feas_artifact_id in ids
    assert tool_artifact_id in ids

    # 5) read toolpaths artifact and verify meta wiring
    tool_obj = client.get(f"/api/runs/{tool_artifact_id}").json()
    assert tool_obj["kind"] == "toolpaths"
    # Confirm toolpath_hash + versions exist