"""
RMOS-CONVERGE-001A - the governed production decision chain.

Acceptance witnesses TC-14 .. TC-21.

Proves the chain the cutover is meant to make trustworthy end to end:

    server-authoritative feasibility
        -> SafetyPolicy
        -> RunDecision
        -> immutable RunArtifact
        -> RunStoreV2
        -> governed export
        -> SHA256 + retrieval

Nothing here rewrites ``RunStoreV2`` or ``RunArtifact`` semantics; these are
regression witnesses that the persistence/override/export architecture the
audit found sound still holds once the authority boundary above it is real.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from app.rmos.policies import SafetyPolicy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def runs_env(tmp_path, monkeypatch):
    """Redirect RunStoreV2, attachments and the override index to temp storage."""
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")

    attachments_dir = tmp_path / "run_attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(attachments_dir))
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ENV", "test")

    try:
        from app.rmos.runs_v2 import store as runs_v2_store

        runs_v2_store._default_store = None
    except ImportError:
        pass

    yield runs_dir

    try:
        from app.rmos.runs_v2 import store as runs_v2_store

        runs_v2_store._default_store = None
    except ImportError:
        pass


@pytest.fixture()
def client(runs_env):
    try:
        from fastapi.testclient import TestClient
        from app.main import app
    except Exception as e:  # pragma: no cover - environment guard
        pytest.skip(f"Could not import FastAPI app: {e}")
    return TestClient(app)


def _adaptive_plan_path(client) -> str:
    """Resolve the mounted adaptive plan route rather than hard-coding a prefix."""
    for route in client.app.routes:
        path = getattr(route, "path", "")
        if path.endswith("/pocket/adaptive/plan"):
            return path
    pytest.skip("adaptive plan route is not mounted in this build")


SANE_PLAN = {
    "loops": [{"pts": [[0, 0], [100, 0], [100, 60], [0, 60]]}],
    "units": "mm",
    "tool_d": 6.0,
    "stepover": 0.45,
    "stepdown": 2.0,
    "margin": 0.5,
    "strategy": "Spiral",
    "smoothing": 0.5,
    "climb": True,
    "feed_xy": 1200.0,
    "safe_z": 5.0,
    "z_rough": -1.5,
}


def _red_plan() -> dict:
    """
    A plan the router's own input validation accepts but the feasibility
    rule engine rejects.

    ``_validate_plan_inputs`` guards loops/tool_d/stepover/strategy, so a bad
    stepover never reaches feasibility. ``z_rough`` is unguarded there and a
    non-negative cutting depth is rule F004 (RED) - which is exactly the
    shape this witness needs: valid request, unsafe operation.
    """
    plan = dict(SANE_PLAN)
    plan["z_rough"] = 1.5  # rule F004: z_rough must be negative
    return plan


def _latest_adaptive_run(event_type: str):
    """
    Find the run the adaptive lane just persisted.

    ``PlanOut`` is the endpoint's ``response_model``, and it declares no
    ``_run_id`` field, so FastAPI strips the run id the router sets on the
    response dict. The governed run is therefore only reachable through the
    store. (That the client cannot see its own run id is recorded in the
    audit addendum, not fixed here.)
    """
    from app.rmos.runs_v2.store_api import list_runs_filtered

    runs = list_runs_filtered(limit=10, event_type=event_type)
    assert runs, f"no {event_type} run was persisted"
    return runs[0]


# ---------------------------------------------------------------------------
# TC-14 / TC-18 / TC-19 - the persisted run carries the server's decision
# ---------------------------------------------------------------------------

def test_tc14_persisted_run_risk_matches_the_server_decision(client):
    """
    TC-14: the persisted governed run records exactly the risk the server
    computed - not a client assertion, and not a helper's own vocabulary.
    """
    path = _adaptive_plan_path(client)
    resp = client.post(path, json=SANE_PLAN)
    assert resp.status_code == 200, resp.text

    run = _latest_adaptive_run("adaptive_plan_execution")

    # The server's own verdict for this plan.
    from app.rmos.api.rmos_feasibility_router import compute_feasibility_internal

    server = compute_feasibility_internal(
        tool_id="adaptive:plan",
        req={**SANE_PLAN, "tool_id": "adaptive:plan"},
        context="test",
    )
    expected = SafetyPolicy.extract_safety_decision(server).risk_level_str()

    assert run.decision.risk_level == expected == "GREEN"


def test_tc14b_client_asserted_green_does_not_reach_the_persisted_run(client):
    """
    The F1 witness at the persistence layer: a RED-producing plan carrying a
    client ``safety: GREEN`` must still persist a BLOCKED/RED run.
    """
    from app.rmos.runs_v2.store_api import get_run

    path = _adaptive_plan_path(client)
    payload = {**_red_plan(), "safety": {"risk_level": "GREEN"}, "risk_level": "GREEN"}

    resp = client.post(path, json=payload)
    assert resp.status_code == 409, resp.text

    detail = resp.json()["detail"]
    assert detail["error"] == "SAFETY_BLOCKED"
    assert detail["decision"]["risk_level"] == "RED"
    assert "F004" in detail["authoritative_feasibility"]["safety"]["details"]["rules_triggered"]

    run = get_run(detail["run_id"])
    assert run is not None
    assert run.status == "BLOCKED"
    assert run.decision.risk_level == "RED"


def test_tc18_and_tc19_run_hashes_stay_linked_and_retrievable(client):
    """
    TC-18/TC-19: the persisted run keeps its feasibility and toolpath hashes,
    and retrieving it returns the same authoritative risk and hashes.
    """
    from app.rmos.runs_v2.store_api import get_run
    from app.rmos.runs_v2.hashing import sha256_of_obj

    path = _adaptive_plan_path(client)
    resp = client.post(path, json=SANE_PLAN)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    run = _latest_adaptive_run("adaptive_plan_execution")

    # Feasibility hash is present and is the hash of the stored feasibility.
    assert run.hashes.feasibility_sha256 == sha256_of_obj(run.feasibility)
    # Toolpath hash links the run to the emitted moves.
    assert run.hashes.toolpaths_sha256 == sha256_of_obj(body["moves"])

    # Retrieval is stable.
    again = get_run(run.run_id)
    assert again.decision.risk_level == run.decision.risk_level
    assert again.hashes.feasibility_sha256 == run.hashes.feasibility_sha256
    assert again.hashes.toolpaths_sha256 == run.hashes.toolpaths_sha256


# ---------------------------------------------------------------------------
# TC-15 / TC-16 / TC-17 - export is gated, override is audited, RED is history
# ---------------------------------------------------------------------------

def _persist_blocked_red_run(run_id: str) -> None:
    from app.rmos.runs_v2.schemas import Hashes, RunArtifact, RunDecision, RunOutputs
    from app.rmos.runs_v2.store_api import persist_run

    persist_run(
        RunArtifact(
            run_id=run_id,
            mode="adaptive",
            tool_id="adaptive:plan",
            event_type="adaptive_plan_blocked",
            status="BLOCKED",
            request_summary={"test": True},
            feasibility={"safety": {"risk_level": "RED"}},
            decision=RunDecision(
                risk_level="RED",
                block_reason="Blocked by safety policy: RED",
            ),
            hashes=Hashes(feasibility_sha256="a" * 64),
            outputs=RunOutputs(),
            meta={},
        )
    )


def test_tc15_export_from_red_unoverridden_run_is_denied(runs_env):
    """TC-15: a RED run with no override cannot be exported."""
    from fastapi import HTTPException

    from app.rmos.runs_v2.exports import export_operator_pack

    run_id = uuid4().hex
    _persist_blocked_red_run(run_id)

    with pytest.raises(HTTPException) as exc:
        export_operator_pack(run_id)

    assert exc.value.status_code == 403
    assert "RED" in str(exc.value.detail)


def test_tc16_red_override_is_denied_when_the_flag_is_disabled(runs_env, monkeypatch):
    """TC-16: RED override requires the explicit administrative flag."""
    from app.rmos.runs_v2 import override_service
    from app.rmos.runs_v2.schemas_override import OverrideRequest

    monkeypatch.delenv("RMOS_ALLOW_RED_OVERRIDE", raising=False)

    run_id = uuid4().hex
    _persist_blocked_red_run(run_id)

    with pytest.raises(override_service.RedOverrideNotAllowedError):
        override_service.apply_override(
            run_id=run_id,
            request=OverrideRequest(
                reason="operator judgement on a test fixture",
                scope="RED",
                acknowledge_risk=True,
            ),
            operator_id="tester",
        )


def test_tc16b_red_override_is_denied_without_acknowledgement(runs_env, monkeypatch):
    """RED override also requires an explicit risk acknowledgement."""
    from app.rmos.runs_v2 import override_service
    from app.rmos.runs_v2.schemas_override import OverrideRequest

    monkeypatch.setenv("RMOS_ALLOW_RED_OVERRIDE", "1")

    run_id = uuid4().hex
    _persist_blocked_red_run(run_id)

    with pytest.raises(override_service.AcknowledgmentRequiredError):
        override_service.apply_override(
            run_id=run_id,
            request=OverrideRequest(
                reason="operator judgement on a test fixture",
                scope="RED",
                acknowledge_risk=False,
            ),
            operator_id="tester",
        )


def test_tc17_enabled_and_acknowledged_red_override_is_permitted_by_policy(runs_env, monkeypatch):
    """
    TC-17 (policy half): with ``RMOS_ALLOW_RED_OVERRIDE=1`` and an explicit
    acknowledgement, the override policy permits the RED run - the same
    request that TC-16/TC-16b prove is refused without either.

    The end-to-end half of TC-17 (apply, then read the run back) cannot be
    witnessed on this tree: ``override_service.apply_override`` calls
    ``put_json_attachment(data=..., run_id=...)`` while the function's
    signature is ``(obj, kind, filename, ext)`` returning a 3-tuple, so every
    application raises ``TypeError`` before it writes anything. That is an
    override-service defect, not a feasibility-authority one; it is recorded
    in the audit addendum and left to the run-writer convergence tranche
    rather than repaired here.
    """
    from app.rmos.runs_v2 import override_service
    from app.rmos.runs_v2.schemas_override import OverrideRequest
    from app.rmos.runs_v2.store_api import get_run

    monkeypatch.setenv("RMOS_ALLOW_RED_OVERRIDE", "1")

    run_id = uuid4().hex
    _persist_blocked_red_run(run_id)
    run = get_run(run_id)

    request = OverrideRequest(
        reason="operator judgement on a test fixture",
        scope="RED",
        acknowledge_risk=True,
    )

    # Permitted: no precondition error is raised.
    override_service.validate_override_preconditions(run, request)

    # And the run it authorizes is still, on its face, RED.
    assert run.decision.risk_level == "RED"
    assert run.status == "BLOCKED"


def test_override_never_rewrites_the_original_risk_determination(runs_env, monkeypatch):
    """
    D6 / TC-17 (invariant half): override is a separate audited authority; it
    may change status and meta, and must never rewrite the historical risk.

    Asserted against the record the service builds, so the invariant is
    pinned even while the application path above is broken.
    """
    from app.rmos.runs_v2 import override_service
    from app.rmos.runs_v2.schemas_override import OverrideRequest
    from app.rmos.runs_v2.store_api import get_run

    monkeypatch.setenv("RMOS_ALLOW_RED_OVERRIDE", "1")

    run_id = uuid4().hex
    _persist_blocked_red_run(run_id)
    run = get_run(run_id)

    record = override_service.create_override_record(
        run=run,
        request=OverrideRequest(
            reason="operator judgement on a test fixture",
            scope="RED",
            acknowledge_risk=True,
        ),
        operator_id="tester",
        operator_name="Test Operator",
    )

    # The override records the risk it overrode rather than replacing it.
    assert record.original_risk_level == "RED"
    assert record.original_status == "BLOCKED"
    assert record.acknowledged_risk is True

    # The stored run is untouched by building the record.
    assert get_run(run_id).decision.risk_level == "RED"

    # Structural: the service's update set never includes `decision`.
    import inspect

    src = inspect.getsource(override_service.apply_override)
    assert '"status": new_status' in src
    assert '"decision"' not in src


# ---------------------------------------------------------------------------
# TC-20 / TC-21 - existing evaluators keep working
# ---------------------------------------------------------------------------

def test_tc20_saw_and_rosette_real_feasibility_still_evaluate():
    """
    TC-20: the saw and rosette engines produce substantive, differentiated
    verdicts from the request.

    Before the cutover both engines raised on every call - the scorer was
    bound to ``art_studio``'s ``extra="forbid"`` rosette schema, which
    rejects the fields the router passes and carries no ``ring_count`` - and
    the failure was swallowed into a fixed ``YELLOW`` / ``score=50.0``. So
    this witness requires real calculator output and a verdict that differs
    between the two lanes, not merely a non-crashing call.
    """
    from app.rmos.api.rmos_feasibility_router import (
        compute_rosette_feasibility,
        compute_saw_feasibility,
    )

    saw = compute_saw_feasibility(
        req={"tool_id": "saw:thin_140", "material_id": "hardwood"}, context="test"
    )
    rosette = compute_rosette_feasibility(
        req={"tool_id": "rosette:default", "material_id": "spruce"}, context="test"
    )

    for result, mode in ((saw, "saw"), (rosette, "rosette")):
        assert result["mode"] == mode
        assert result["safety"]["risk_level"] in ("GREEN", "YELLOW", "RED")
        assert result["safety"]["details"]["engine"] == "feasibility_scorer"
        assert result["safety"]["warnings"], f"{mode} produced no findings"
        # Not the old fail-open constant.
        assert result["safety"]["score"] != 50.0

    # The saw lane reaches the saw calculators, the rosette lane the router
    # calculators, and they reach different verdicts.
    assert saw["safety"]["risk_level"] != rosette["safety"]["risk_level"]
    assert rosette["safety"]["details"]["calculator_results"]


def test_tc21_operation_specific_cam_evaluators_still_evaluate():
    """
    TC-21: the drilling / pocketing / profiling intent lanes carry their own
    real evaluators. They do not route through the feasibility dispatcher and
    must be unaffected by the cutover.
    """
    from app.cam.drilling.feasibility import compute_drilling_feasibility
    from app.cam.profiling.feasibility import compute_profile_feasibility

    ok = compute_drilling_feasibility(
        hole_depth_mm=10.0,
        hole_diameter_mm=3.0,
        peck_drilling=True,
        peck_depth_mm=2.0,
        hole_count=6,
        feed_rate_mm_min=300.0,
        spindle_rpm=12000.0,
        safe_z_mm=5.0,
        retract_z_mm=2.0,
    )
    assert ok.feasible is True

    # The mandatory peck rule still blocks.
    bad = compute_drilling_feasibility(
        hole_depth_mm=10.0,
        hole_diameter_mm=3.0,
        peck_drilling=True,
        peck_depth_mm=12.0,
        hole_count=6,
        feed_rate_mm_min=300.0,
        spindle_rpm=12000.0,
        safe_z_mm=5.0,
        retract_z_mm=2.0,
    )
    assert bad.feasible is False
    assert bad.issues

    profile = compute_profile_feasibility(
        tool_diameter_mm=6.0,
        cut_depth_mm=12.0,
        stepdown_mm=2.0,
        feed_rate_mm_min=1000.0,
        plunge_rate_mm_min=300.0,
        safe_z_mm=5.0,
        retract_z_mm=2.0,
        contour_point_count=64,
        tab_count=4,
        tab_height_mm=1.5,
        use_tabs=True,
        finishing_pass=True,
        finishing_allowance_mm=0.3,
    )
    assert profile.feasible is True
