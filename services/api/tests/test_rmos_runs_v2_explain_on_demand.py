"""
Phase 5 — Tests for on-demand AI-assisted explanation endpoint.

Tests:
- Endpoint attaches assistant_explanation to run
- Idempotent without force
- Force regenerates explanation
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create test client with isolated storage directories."""
    # Point RMOS storage at tmp dirs
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


def _create_min_run(client: TestClient) -> str:
    """Create a minimal run using the MVP wrapper for testing."""
    dxf_path = Path(__file__).parent / "testdata" / "mvp_rect_with_island.dxf"
    if not dxf_path.exists():
        pytest.skip(f"Missing MVP DXF fixture: {dxf_path}")

    with dxf_path.open("rb") as f:
        resp = client.post(
            "/api/rmos/wrap/mvp/dxf-to-grbl",
            files={"file": ("mvp_rect_with_island.dxf", f, "application/dxf")},
            data={
                "tool_d": "6.0",
                "stepover": "0.45",
                "stepdown": "1.5",
                "z_rough": "-3.0",
                "feed_xy": "1200",
                "feed_z": "300",
                "safe_z": "5.0",
                "strategy": "Spiral",
                "layer_name": "GEOMETRY",
                "post_id": "GRBL",
            },
        )
    assert resp.status_code == 200, resp.text
    j = resp.json()
    assert j.get("ok") is True, j
    return j["run_id"]


def test_explain_endpoint_attaches_assistant_explanation(client: TestClient):
    """Test that explain endpoint creates and attaches assistant_explanation."""
    run_id = _create_min_run(client)

    resp = client.post(f"/api/rmos/runs_v2/runs/{run_id}/explain")
    assert resp.status_code == 200, resp.text
    j = resp.json()
    assert j["ok"] is True
    assert j["run_id"] == run_id
    assert j["explanation_status"] == "READY"
    assert j["attachment"]["kind"] == "assistant_explanation"
    assert "explanation" in j
    assert j["explanation"]["disclaimer"].lower().startswith("this text is advisory")

    # Run artifact should now include attachment
    r2 = client.get(f"/api/rmos/runs_v2/runs/{run_id}")
    assert r2.status_code == 200
    run = r2.json()
    kinds = [a["kind"] for a in (run.get("attachments") or [])]
    assert "assistant_explanation" in kinds


def test_explain_endpoint_idempotent_without_force(client: TestClient):
    """Test that calling explain twice without force returns existing."""
    run_id = _create_min_run(client)

    r1 = client.post(f"/api/rmos/runs_v2/runs/{run_id}/explain")
    assert r1.status_code == 200

    r2 = client.post(f"/api/rmos/runs_v2/runs/{run_id}/explain")
    assert r2.status_code == 200
    j2 = r2.json()
    assert "already present" in (j2.get("note") or "")


def test_explain_endpoint_force_regenerates(client: TestClient):
    """Test that force=true regenerates the explanation."""
    run_id = _create_min_run(client)

    r1 = client.post(f"/api/rmos/runs_v2/runs/{run_id}/explain")
    assert r1.status_code == 200
    a1_sha = r1.json()["attachment"]["sha256"]

    # Force regenerate - should produce same hash since deterministic
    # but the endpoint should still go through regeneration path
    r2 = client.post(f"/api/rmos/runs_v2/runs/{run_id}/explain?force=true")
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2["ok"] is True
    # Note: with deterministic generator, sha256 should be same
    # but the "note" field should NOT say "already present"
    assert "already present" not in (j2.get("note") or "")


def test_explain_endpoint_404_for_missing_run(client: TestClient):
    """Test that explain returns 404 for non-existent run."""
    resp = client.post("/api/rmos/runs_v2/runs/nonexistent_run_id/explain")
    assert resp.status_code == 404


def test_explanation_contains_based_on_context(client: TestClient):
    """Test that explanation includes based_on context."""
    run_id = _create_min_run(client)

    resp = client.post(f"/api/rmos/runs_v2/runs/{run_id}/explain")
    assert resp.status_code == 200
    j = resp.json()

    explanation = j["explanation"]
    assert "based_on" in explanation
    assert explanation["based_on"]["run_id"] == run_id
    assert "risk_level" in explanation["based_on"]
    assert "rules_triggered" in explanation["based_on"]


def test_explanation_meta_contains_generator_info(client: TestClient):
    """Test that explanation meta includes generator info."""
    run_id = _create_min_run(client)

    resp = client.post(f"/api/rmos/runs_v2/runs/{run_id}/explain")
    assert resp.status_code == 200
    j = resp.json()

    explanation = j["explanation"]
    assert "meta" in explanation
    assert explanation["meta"].get("generator") == "deterministic.v1"
    assert "grounded_facts" in explanation["meta"]
