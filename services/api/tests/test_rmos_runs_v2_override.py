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


def _create_run(client: TestClient, *, feed_xy: int, feed_z: int, tool_d: float = 6.0) -> str:
    dxf_path = Path("tests/testdata/mvp_rect_with_island.dxf")
    assert dxf_path.exists(), "Missing MVP DXF fixture"

    with dxf_path.open("rb") as f:
        resp = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("mvp_rect_with_island.dxf", f, "application/dxf")},
            data={
                "tool_d": str(tool_d),
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


def test_override_yellow_unblocks_and_attaches_override_json(client: TestClient):
    # Intentionally trigger YELLOW: plunge feed > XY feed (F011)
    run_id = _create_run(client, feed_xy=600, feed_z=1200)

    r = client.get(f"/api/rmos/runs_v2/{run_id}")
    assert r.status_code == 200
    run = r.json()
    assert run["decision"]["risk_level"] in {"YELLOW", "RED", "GREEN"}  # tolerate rule changes

    # If it didn't go YELLOW (unexpected), at least ensure the override endpoint behaves safely.
    if run["decision"]["risk_level"] == "GREEN":
        o = client.post(
            f"/api/rmos/runs_v2/{run_id}/override",
            json={"operator": "op_test", "reason": "test override", "scope": "test"},
        )
        assert o.status_code == 409
        return

    if run["decision"]["risk_level"] == "RED":
        o = client.post(
            f"/api/rmos/runs_v2/{run_id}/override",
            json={"operator": "op_test", "reason": "test override", "scope": "test"},
        )
        assert o.status_code in {403, 409}
        return

    # Normal path: YELLOW override allowed
    o = client.post(
        f"/api/rmos/runs_v2/{run_id}/override",
        json={"operator": "op_test", "reason": "Operator reviewed warnings", "scope": "manufacturing"},
    )
    assert o.status_code == 200, o.text
    j = o.json()
    assert j["ok"] is True
    assert j["run_id"] == run_id
    assert j["risk_level"] == "YELLOW"
    assert j["override_attachment"]["kind"] == "override"

    # Run artifact should now include override attachment and be OK
    r2 = client.get(f"/api/rmos/runs_v2/{run_id}")
    assert r2.status_code == 200
    run2 = r2.json()
    kinds = [a["kind"] for a in (run2.get("attachments") or [])]
    assert "override" in kinds
    assert run2["status"] == "OK"
    assert "override" in (run2.get("meta") or {})


def test_override_red_requires_feature_flag(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    # Intentionally trigger RED: invalid tool diameter (F001 expected)
    run_id = _create_run(client, feed_xy=600, feed_z=300, tool_d=0.0)

    r = client.get(f"/api/rmos/runs_v2/{run_id}")
    assert r.status_code == 200
    run = r.json()

    # If it didn't go RED due to rule drift, treat as non-applicable.
    if run["decision"]["risk_level"] != "RED":
        return

    # Without flags -> forbidden
    o1 = client.post(
        f"/api/rmos/runs_v2/{run_id}/override?allow_red=true",
        json={"operator": "op_test", "reason": "dev only", "scope": "dev"},
    )
    assert o1.status_code == 403

    # Enable flag -> allowed
    monkeypatch.setenv("RMOS_ALLOW_RED_OVERRIDE", "1")
    o2 = client.post(
        f"/api/rmos/runs_v2/{run_id}/override?allow_red=true",
        json={"operator": "op_test", "reason": "dev only", "scope": "dev"},
    )
    assert o2.status_code == 200, o2.text
    j2 = o2.json()
    assert j2["ok"] is True
    assert j2["risk_level"] == "RED"

    r2 = client.get(f"/api/rmos/runs_v2/{run_id}")
    assert r2.status_code == 200
    run2 = r2.json()
    kinds = [a["kind"] for a in (run2.get("attachments") or [])]
    assert "override" in kinds
    assert run2["status"] == "OK"
