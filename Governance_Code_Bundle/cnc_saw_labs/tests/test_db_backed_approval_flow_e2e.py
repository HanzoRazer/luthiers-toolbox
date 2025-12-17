from __future__ import annotations
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Use temp DB + temp artifacts
    monkeypatch.setenv("RMOS_DB_URL", f"sqlite:///{tmp_path / 'rmos_test.sqlite3'}")
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ENV", "test")

    try:
        from app.main import app
    except Exception as e:
        pytest.skip(f"Could not import FastAPI app from app.main: {e}")

    return TestClient(app)


def test_db_backed_feasibility_approve_toolpaths(client: TestClient):
    f = client.post("/api/rmos/feasibility", json={
        "mode": "design_first",
        "design": {"example": "design_A"},
        "context": {"tool_id": "saw:thin_140", "material_id": "ebony", "machine_id": "router_a", "extra": {}},
    })
    assert f.status_code == 200, f.text
    feas = f.json()
    session_id = feas["session_id"]
    feas_artifact_id = feas["artifact_id"]

    a = client.post("/api/workflow/approve", json={"session_id": session_id, "actor": "operator", "note": "ok"})
    assert a.status_code == 200, a.text

    t = client.post("/api/rmos/toolpaths", json={
        "session_id": session_id,
        "mode": "design_first",
        "design": {"example": "design_A"},
        "context": {"tool_id": "saw:thin_140", "material_id": "ebony", "machine_id": "router_a", "extra": {}},
    })
    assert t.status_code == 200, t.text
    tool = t.json()
    tool_artifact_id = tool["artifact_id"]

    # Check both artifacts are indexed
    idx = client.get("/api/runs", params={"limit": 100})
    assert idx.status_code == 200, idx.text
    ids = {row["artifact_id"] for row in idx.json()["items"]}
    assert feas_artifact_id in ids
    assert tool_artifact_id in ids

Configuration summary
SQLite DB path
RMOS_DB_URL=sqlite:///data/rmos.sqlite3 (default)
Artifacts path
RMOS_ARTIFACT_ROOT=data/run_artifacts (default)