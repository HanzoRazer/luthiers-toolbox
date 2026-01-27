from __future__ import annotations

from unittest.mock import patch


def _make_artifact(kind, artifact_id, created_utc, payload=None, state=None):
    """Helper to build a minimal artifact dict."""
    p = dict(payload or {})
    if state:
        p["state"] = state
    return {
        "kind": kind,
        "id": artifact_id,
        "artifact_id": artifact_id,
        "created_utc": created_utc,
        "payload": p,
    }


def test_resolve_latest_metrics_for_batch_picks_latest_execution_then_metrics():
    """
    resolve_latest_metrics_for_batch should chain:
      batch -> latest approved decision -> latest execution -> latest metrics
    """
    decision = _make_artifact(
        kind="saw_batch_decision",
        artifact_id="dec-001",
        created_utc="2026-01-01T00:00:00Z",
        state="APPROVED",
    )
    execution = _make_artifact(
        kind="saw_batch_execution",
        artifact_id="ex-001",
        created_utc="2026-01-01T01:00:00Z",
    )
    metrics = _make_artifact(
        kind="saw_batch_execution_metrics",
        artifact_id="met-001",
        created_utc="2026-01-01T02:00:00Z",
        payload={"kpis": {"total_cut_time_s": 120.0}},
    )

    # Mock at the service function level to test the chaining logic
    with patch(
        "app.saw_lab.latest_batch_chain_service.resolve_latest_approved_decision_for_batch",
        return_value=decision,
    ), patch(
        "app.saw_lab.latest_batch_chain_service.resolve_latest_execution_for_batch",
        return_value=execution,
    ), patch(
        "app.saw_lab.metrics_lookup_service.resolve_latest_metrics_for_execution",
        return_value=metrics,
    ):
        from app.saw_lab.latest_batch_chain_service import (
            resolve_latest_metrics_for_batch,
        )

        result = resolve_latest_metrics_for_batch(
            session_id="sess-001",
            batch_label="batch-A",
            tool_kind="saw",
        )

    assert result["latest_approved_decision_artifact_id"] == "dec-001"
    assert result["latest_execution_artifact_id"] == "ex-001"
    assert result["latest_metrics_artifact_id"] == "met-001"
    assert result["kpis"]["total_cut_time_s"] == 120.0


def test_resolve_latest_metrics_for_batch_no_execution():
    """When no execution artifact exists, metrics are None."""
    decision = _make_artifact(
        kind="saw_batch_decision",
        artifact_id="dec-001",
        created_utc="2026-01-01T00:00:00Z",
        state="APPROVED",
    )

    with patch(
        "app.saw_lab.latest_batch_chain_service.resolve_latest_approved_decision_for_batch",
        return_value=decision,
    ), patch(
        "app.saw_lab.latest_batch_chain_service.resolve_latest_execution_for_batch",
        return_value=None,
    ):
        from app.saw_lab.latest_batch_chain_service import (
            resolve_latest_metrics_for_batch,
        )

        result = resolve_latest_metrics_for_batch(
            session_id="sess-001",
            batch_label="batch-A",
        )

    assert result["latest_approved_decision_artifact_id"] == "dec-001"
    assert result["latest_execution_artifact_id"] is None
    assert result["latest_metrics_artifact_id"] is None
    assert result["kpis"] is None
