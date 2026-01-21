from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _start_session() -> str:
    r = client.post(
        "/api/art/design-first-workflow/sessions/start",
        json={
            "mode": "design_first",
            "design": {
                "outer_diameter_mm": 110.0,
                "inner_diameter_mm": 90.0,
                "ring_params": [{"ring_index": 0, "width_mm": 2.0, "pattern_type": "SOLID"}],
            },
            "feasibility": {
                "overall_score": 0.92,
                "risk_bucket": "GREEN",
                "material_efficiency": 0.88,
                "estimated_cut_time_min": 12.5,
                "warnings": [],
            },
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["session"]["session_id"]


def _transition(session_id: str, to_state: str) -> None:
    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/transition",
        json={"to_state": to_state, "actor": "pytest"},
    )
    assert r.status_code == 200, r.text


def _approve(session_id: str) -> None:
    _transition(session_id, "in_review")
    _transition(session_id, "approved")


def test_promote_blocked_when_not_approved() -> None:
    sid = _start_session()
    r = client.post(f"/api/art/design-first-workflow/sessions/{sid}/promote_to_cam")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ok"] is False
    assert data["request"] is None
    assert isinstance(data.get("blocked_reason"), str) and data["blocked_reason"]


def test_promote_ok_when_approved_and_is_idempotent() -> None:
    sid = _start_session()
    _approve(sid)

    r1 = client.post(f"/api/art/design-first-workflow/sessions/{sid}/promote_to_cam")
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    assert d1["ok"] is True
    req1 = d1["request"]
    assert req1["promotion_request_version"] == "v1"
    assert req1["session_id"] == sid
    assert req1["status"] == "QUEUED"
    assert req1["design_fingerprint"] and req1["feasibility_fingerprint"]

    r2 = client.post(f"/api/art/design-first-workflow/sessions/{sid}/promote_to_cam")
    assert r2.status_code == 200, r2.text
    d2 = r2.json()
    assert d2["ok"] is True
    req2 = d2["request"]

    # Idempotency guarantee: same request id for same fingerprints
    assert req2["promotion_request_id"] == req1["promotion_request_id"]
