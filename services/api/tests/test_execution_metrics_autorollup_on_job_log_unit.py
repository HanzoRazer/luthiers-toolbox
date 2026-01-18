from __future__ import annotations

import os


def test_autorollup_runs_when_flag_enabled(monkeypatch):
    # Enable flag
    os.environ["SAW_LAB_EXECUTION_METRICS_AUTOROLLUP_ENABLED"] = "true"

    from app.saw_lab.execution_metrics_autorollup import maybe_autorollup_execution_metrics

    called = {"n": 0}

    def _fake_write_execution_metrics_rollup_artifact(**kwargs):
        called["n"] += 1
        assert kwargs["batch_execution_artifact_id"] == "exec1"
        assert kwargs["session_id"] == "s1"
        assert kwargs["batch_label"] == "b1"
        return "mx1"

    monkeypatch.setattr(
        "app.saw_lab.execution_metrics_rollup_service.write_execution_metrics_rollup_artifact",
        _fake_write_execution_metrics_rollup_artifact,
    )

    out = maybe_autorollup_execution_metrics(
        batch_execution_artifact_id="exec1",
        session_id="s1",
        batch_label="b1",
        tool_kind="saw",
    )
    assert out == "mx1"
    assert called["n"] == 1


def test_autorollup_does_not_run_when_flag_disabled(monkeypatch):
    os.environ["SAW_LAB_EXECUTION_METRICS_AUTOROLLUP_ENABLED"] = "false"

    from app.saw_lab.execution_metrics_autorollup import maybe_autorollup_execution_metrics

    called = {"n": 0}

    def _fake_write_execution_metrics_rollup_artifact(**kwargs):
        called["n"] += 1
        return "mx1"

    monkeypatch.setattr(
        "app.saw_lab.execution_metrics_rollup_service.write_execution_metrics_rollup_artifact",
        _fake_write_execution_metrics_rollup_artifact,
    )

    out = maybe_autorollup_execution_metrics(
        batch_execution_artifact_id="exec1",
        session_id="s1",
        batch_label="b1",
        tool_kind="saw",
    )
    assert out is None
    assert called["n"] == 0
