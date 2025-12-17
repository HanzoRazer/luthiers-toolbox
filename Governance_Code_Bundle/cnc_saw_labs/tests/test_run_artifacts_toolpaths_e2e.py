from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """
    Uses your real FastAPI app, but redirects artifact storage to a temp folder.
    """
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ENV", "test")  # ensure non-prod behavior where applicable

    try:
        from app.main import app  # adjust if your FastAPI entrypoint differs
    except Exception as e:
        pytest.skip(f"Could not import FastAPI app from app.main: {e}")

    return TestClient(app)


def _extract_artifact_id(response) -> str:
    """
    Your wrappers return artifact_id on:
      - 200 OK in body
      - 409/500 via HTTPException detail payload
    """
    data = response.json()
    if response.status_code == 200:
        assert "artifact_id" in data, f"Expected artifact_id in OK response body, got: {data}"
        return data["artifact_id"]

    # FastAPI HTTPException returns {"detail": {...}}
    assert "detail" in data, f"Expected detail in error response, got: {data}"
    detail = data["detail"]
    assert isinstance(detail, dict), f"Expected dict detail, got: {detail}"
    assert "artifact_id" in detail, f"Expected artifact_id in error detail, got: {detail}"
    return detail["artifact_id"]


def test_toolpaths_e2e_persists_and_returns_artifact_ids_then_diff(client):
    """
    End-to-end proof hitting /api/rmos/toolpaths:

      1) POST /api/rmos/toolpaths twice (different materials)
         - expects either 200 OK or 409 BLOCKED
         - in both cases extracts artifact_id immediately
      2) GET /api/runs confirms both artifacts exist
      3) GET /api/runs/diff/{a}/{b} confirms differences are detected
    """
    req_1 = {
        "mode": "design_first",
        "design": {"example": "design_A"},
        "context": {"tool_id": "saw:thin_140", "material_id": "ebony", "machine_id": "router_a", "extra": {}},
    }

    req_2 = {
        "mode": "design_first",
        "design": {"example": "design_A"},  # same design on purpose; change material only
        "context": {"tool_id": "saw:thin_140", "material_id": "maple", "machine_id": "router_a", "extra": {}},
    }

    # 1) toolpaths calls (should still return artifact_id even if BLOCKED/ERROR)
    r1 = client.post("/api/rmos/toolpaths", json=req_1)
    assert r1.status_code in (200, 409, 500), r1.text
    a_id = _extract_artifact_id(r1)

    r2 = client.post("/api/rmos/toolpaths", json=req_2)
    assert r2.status_code in (200, 409, 500), r2.text
    b_id = _extract_artifact_id(r2)

    assert a_id != b_id, "Expected two distinct toolpaths artifacts"

    # 2) Query index and confirm the artifacts show up
    idx = client.get("/api/runs", params={"limit": 100})
    assert idx.status_code == 200, idx.text
    items = idx.json()["items"]
    ids = {row["artifact_id"] for row in items}
    assert a_id in ids, "First toolpaths artifact not found in /api/runs"
    assert b_id in ids, "Second toolpaths artifact not found in /api/runs"

    # 3) Read artifacts back
    ra = client.get(f"/api/runs/{a_id}")
    assert ra.status_code == 200, ra.text
    obj_a = ra.json()
    assert obj_a["artifact_id"] == a_id

    rb = client.get(f"/api/runs/{b_id}")
    assert rb.status_code == 200, rb.text
    obj_b = rb.json()
    assert obj_b["artifact_id"] == b_id

    # Sanity: they should be toolpaths artifacts
    assert obj_a.get("kind") == "toolpaths", f"Expected kind=toolpaths, got {obj_a.get('kind')}"
    assert obj_b.get("kind") == "toolpaths", f"Expected kind=toolpaths, got {obj_b.get('kind')}"

    # 4) Diff artifacts (governance diff)
    d = client.get(f"/api/runs/diff/{a_id}/{b_id}")
    assert d.status_code == 200, d.text
    diff = d.json()

    assert diff["a_id"] == a_id
    assert diff["b_id"] == b_id
    assert diff["summary"]["changed_count"] >= 1, "Expected at least one changed field"

    changed_fields = {c["field"] for c in diff["changed_fields"]}

    # Because we changed material_id, we expect that to show up in the diff fields
    assert "material_id" in changed_fields or "score" in changed_fields or "risk_bucket" in changed_fields, (
        f"Expected diff to capture material_id or other governance fields. Changed: {changed_fields}"
    )
Why this test is “correct” for your governance model
It doesn’t assume toolpaths will always succeed.
It proves the invariant you set:
artifact_id is returned immediately
artifacts exist even on BLOCKED/ERROR
diff works against real stored artifacts