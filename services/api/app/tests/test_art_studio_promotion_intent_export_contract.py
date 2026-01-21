# services/api/app/tests/test_art_studio_promotion_intent_export_contract.py
"""
Phase 32.0 — Promotion Intent Export Contract

Contract tests:
1) Canonical export endpoint (raw PromotionIntentV1 JSON)
   GET /api/art/design-first-workflow/sessions/{session_id}/promotion_intent.json
   - 403 if not approved
   - 200 and strict keys present if approved

2) Lightweight wrapper endpoint (UI ergonomic)
   POST /api/art/design-first-workflow/sessions/{session_id}/promotion_intent_v1
   - 200 always
   - ok=false + blocked_reason if not approved
   - ok=true + intent if approved
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _start_session() -> str:
    """
    Start a DRAFT design-first workflow session with a minimal RosetteParamSpec.
    We include a feasibility dict shaped like RosetteFeasibilitySummary so the v1 export
    can be strict without relying on external RMOS execution during tests.
    """
    r = client.post(
        "/api/art/design-first-workflow/sessions/start",
        json={
            "mode": "design_first",
            "design": {
                "outer_diameter_mm": 110.0,
                "inner_diameter_mm": 90.0,
                "ring_params": [
                    {"ring_index": 0, "width_mm": 2.0, "pattern_type": "SOLID"}
                ],
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
    data = r.json()
    assert "session" in data
    return data["session"]["session_id"]


def _transition(session_id: str, to_state: str) -> None:
    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/transition",
        json={"to_state": to_state, "actor": "pytest"},
    )
    assert r.status_code == 200, r.text


def _approve_session(session_id: str) -> None:
    # Contract: must go DRAFT -> IN_REVIEW -> APPROVED
    _transition(session_id, "in_review")
    _transition(session_id, "approved")


def test_wrapper_returns_blocked_when_not_approved() -> None:
    session_id = _start_session()

    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent_v1"
    )
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["ok"] is False
    assert data.get("intent") is None
    # Block reason must be present and non-empty
    assert isinstance(data.get("blocked_reason"), str)
    assert len(data["blocked_reason"]) > 0


def test_canonical_export_403_when_not_approved() -> None:
    session_id = _start_session()

    r = client.get(
        f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent.json"
    )
    assert r.status_code == 403, r.text


def test_wrapper_returns_intent_when_approved() -> None:
    session_id = _start_session()
    _approve_session(session_id)

    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent_v1"
    )
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["ok"] is True
    assert data.get("blocked_reason") in (None, "")
    assert isinstance(data.get("intent"), dict)


def test_canonical_export_returns_strict_v1_shape_when_approved() -> None:
    session_id = _start_session()
    _approve_session(session_id)

    r = client.get(
        f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent.json"
    )
    assert r.status_code == 200, r.text
    d = r.json()

    # ---- STRICT TOP-LEVEL CONTRACT (PromotionIntentV1) ----
    required_top = [
        "intent_version",
        "session_id",
        "mode",
        "created_at",
        "design",
        "feasibility",
        "design_fingerprint",
        "feasibility_fingerprint",
        "fingerprint_algo",
    ]
    missing_top = [k for k in required_top if k not in d]
    assert not missing_top, f"Missing top-level keys: {missing_top}"

    assert d["intent_version"] == "v1"
    assert d["session_id"] == session_id
    assert isinstance(d["mode"], str) and len(d["mode"]) > 0
    assert isinstance(d["created_at"], str) and len(d["created_at"]) > 0
    assert isinstance(d["design_fingerprint"], str) and len(d["design_fingerprint"]) > 0
    assert isinstance(d["feasibility_fingerprint"], str) and len(d["feasibility_fingerprint"]) > 0
    assert isinstance(d["fingerprint_algo"], str) and len(d["fingerprint_algo"]) > 0

    # ---- STRICT NESTED CONTRACT: design (RosetteParamSpec) ----
    design = d["design"]
    assert isinstance(design, dict)
    for k in ["outer_diameter_mm", "inner_diameter_mm", "ring_params"]:
        assert k in design, f"Missing design.{k}"
    assert isinstance(design["outer_diameter_mm"], (int, float))
    assert isinstance(design["inner_diameter_mm"], (int, float))
    assert isinstance(design["ring_params"], list)

    # ---- STRICT NESTED CONTRACT: feasibility (RosetteFeasibilitySummary) ----
    feas = d["feasibility"]
    assert isinstance(feas, dict)
    for k in [
        "overall_score",
        "risk_bucket",
        "material_efficiency",
        "estimated_cut_time_min",
        "warnings",
    ]:
        assert k in feas, f"Missing feasibility.{k}"
    assert isinstance(feas["overall_score"], (int, float))
    assert isinstance(feas["material_efficiency"], (int, float))
    assert isinstance(feas["estimated_cut_time_min"], (int, float))
    assert isinstance(feas["risk_bucket"], str) and len(feas["risk_bucket"]) > 0
    assert isinstance(feas["warnings"], list)
