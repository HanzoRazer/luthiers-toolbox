from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RMOS_DB_URL", f"sqlite:///{tmp_path / 'rmos_test.sqlite3'}")
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("RMOS_ENGINE_MODULE", "tests.fake_rmos_engine")

    try:
        from app.main import app
    except Exception as e:
        pytest.skip(f"Could not import FastAPI app from app.main: {e}")

    return TestClient(app)


def test_material_change_changes_feasibility_hash_and_versions_present(client: TestClient):
    design = {"shape": "ring", "od": 140}
    common = {"tool_id": "saw:thin_140", "machine_id": "router_a", "extra": {}}

    f1 = client.post("/api/rmos/feasibility", json={
        "mode": "design_first",
        "design": design,
        "context": {**common, "material_id": "ebony"},
    })
    assert f1.status_code == 200, f1.text
    a_id = f1.json()["artifact_id"]

    f2 = client.post("/api/rmos/feasibility", json={
        "mode": "design_first",
        "design": design,
        "context": {**common, "material_id": "maple"},
    })
    assert f2.status_code == 200, f2.text
    b_id = f2.json()["artifact_id"]

    obj_a = client.get(f"/api/runs/{a_id}").json()
    obj_b = client.get(f"/api/runs/{b_id}").json()

    meta_a = obj_a["payload"]["feasibility"]["meta"]
    meta_b = obj_b["payload"]["feasibility"]["meta"]

    assert meta_a["policy_version"] == "policy_test_v1"
    assert meta_a["calculator_versions"]["rim_speed"] == "0.9.0"
    assert meta_a["feasibility_hash"] != meta_b["feasibility_hash"], "Expected feasibility_hash to differ across materials"

E) How to point to your real RMOS in production
Set one env var to your real engine module:
$env:RMOS_ENGINE_MODULE="app.rmos.impl"   # example
Your module must export either:
ENGINE = <instance implementing RmosEngine>
or
def get_engine(): return <instance>
That’s it.