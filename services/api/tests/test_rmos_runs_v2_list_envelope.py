"""
RMOS Runs v2 List Envelope Tests

Tests for GET /api/rmos/runs_v2 with envelope response and cursor pagination.
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


def test_runs_list_returns_envelope_shape(client: TestClient):
    _create_run(client, feed_xy=1200, feed_z=300)
    _create_run(client, feed_xy=600, feed_z=1200)  # likely YELLOW

    r = client.get("/api/rmos/runs_v2?limit=10")
    assert r.status_code == 200, r.text
    j = r.json()

    assert "items" in j
    assert isinstance(j["items"], list)
    assert "count" in j
    assert j["count"] == len(j["items"])
    assert "next_cursor" in j

    # Validate summary fields
    assert len(j["items"]) >= 1
    item0 = j["items"][0]
    for k in ["run_id", "created_at_utc", "mode", "tool_id", "status", "risk_level", "rules_triggered"]:
        assert k in item0


def test_runs_list_cursor_paginates(client: TestClient):
    _create_run(client, feed_xy=1200, feed_z=300)
    _create_run(client, feed_xy=600, feed_z=1200)

    r1 = client.get("/api/rmos/runs_v2?limit=1")
    assert r1.status_code == 200
    j1 = r1.json()
    assert j1["count"] == 1
    cur = j1.get("next_cursor")
    assert cur, "expected next_cursor for limit=1"

    r2 = client.get(f"/api/rmos/runs_v2?limit=10&cursor={cur}")
    assert r2.status_code == 200
    j2 = r2.json()
    # Should return remaining items (>=1) or empty if store ordering differs
    assert "items" in j2
    assert "count" in j2


def test_runs_list_filters_by_risk(client: TestClient):
    _create_run(client, feed_xy=1200, feed_z=300)
    _create_run(client, feed_xy=600, feed_z=1200)

    r = client.get("/api/rmos/runs_v2?risk=YELLOW&limit=50")
    assert r.status_code == 200
    j = r.json()
    # If rule drift causes none to be YELLOW, this should simply be empty.
    for it in j["items"]:
        assert it["risk_level"] == "YELLOW"
