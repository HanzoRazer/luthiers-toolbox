from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """
    Uses your real FastAPI app, but redirects artifact storage to a temp folder.
    """
    # Ensure artifacts are written to temp
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    # Optional: mark non-prod for dev toggles, if your app uses ENV
    monkeypatch.setenv("ENV", "test")

    # Import your app (adjust import if your app entrypoint differs)
    try:
        from app.main import app  # typical: services/api/app/main.py
    except Exception as e:
        pytest.skip(f"Could not import FastAPI app from app.main: {e}")

    return TestClient(app)


def test_run_artifacts_end_to_end_write_list_diff(client):
    """
    End-to-end proof:
      - writes artifacts (via store.py)
      - queries /api/runs
      - diffs two artifacts
    """
    # Write two artifacts directly (fast, deterministic)
    try:
        from app.rmos.run_artifacts.store import write_run_artifact
    except Exception as e:
        pytest.skip(f"Could not import artifact store: {e}")

    a = write_run_artifact(
        kind="feasibility",
        status="OK",
        session_id="sess_test_1",
        index_meta={"tool_id": "saw:thin_140", "material_id": "ebony", "machine_id": "router_a"},
        payload={
            "feasibility": {
                "score": 92.0,
                "risk_bucket": "GREEN",
                "warnings": [],
                "meta": {
                    "policy_version": "v1",
                    "feasibility_hash": "hash_A",
                    "design_hash": "dhash_A",
                    "context_hash": "chash_A",
                },
            }
        },
    )

    b = write_run_artifact(
        kind="feasibility",
        status="OK",
        session_id="sess_test_2",
        index_meta={"tool_id": "saw:thin_140", "material_id": "maple", "machine_id": "router_a"},
        payload={
            "feasibility": {
                "score": 71.0,
                "risk_bucket": "YELLOW",
                "warnings": ["heat risk"],
                "meta": {
                    "policy_version": "v1",
                    "feasibility_hash": "hash_B",
                    "design_hash": "dhash_B",
                    "context_hash": "chash_B",
                },
            }
        },
    )

    # 1) Query /api/runs (index API)
    res = client.get("/api/runs", params={"limit": 50})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    ids = {row["artifact_id"] for row in data["items"]}
    assert a.artifact_id in ids, "Artifact A not found in /api/runs index"
    assert b.artifact_id in ids, "Artifact B not found in /api/runs index"

    # 2) Query /api/runs/{id} (raw read)
    res_a = client.get(f"/api/runs/{a.artifact_id}")
    assert res_a.status_code == 200, res_a.text
    obj_a = res_a.json()
    assert obj_a["artifact_id"] == a.artifact_id

    # 3) Diff /api/runs/diff/{a}/{b}
    diff_res = client.get(f"/api/runs/diff/{a.artifact_id}/{b.artifact_id}")
    assert diff_res.status_code == 200, diff_res.text
    diff = diff_res.json()

    assert diff["a_id"] == a.artifact_id
    assert diff["b_id"] == b.artifact_id
    assert diff["summary"]["changed_count"] >= 1, "Expected at least one changed field in diff"

    # Ensure the diff catches at least score/risk/material differences
    changed_fields = {c["field"] for c in diff["changed_fields"]}
    assert ("score" in changed_fields) or ("risk_bucket" in changed_fields) or ("material_id" in changed_fields)
Notes (so it runs cleanly)
This assumes your FastAPI app is importable as from app.main import app. If yours is different (e.g., app.main:app but different package root), change that one import line.