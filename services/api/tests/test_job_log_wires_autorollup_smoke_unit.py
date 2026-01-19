from __future__ import annotations

import os


def test_write_job_log_calls_autorollup_when_enabled(monkeypatch):
    """
    Ensures the job-log endpoint wiring invokes autorollup behind the feature flag.
    This is a pure unit test (no DB).
    """
    os.environ["SAW_LAB_EXECUTION_METRICS_AUTOROLLUP_ENABLED"] = "true"

    # Patch store_artifact so job log can be created
    def _fake_store_artifact(**kwargs):
        assert kwargs["kind"] == "saw_batch_job_log"
        return "jl1"

    # Patch autorollup helper
    called = {"n": 0}

    def _fake_maybe_autorollup_execution_metrics(**kwargs):
        called["n"] += 1
        assert kwargs["batch_execution_artifact_id"] == "exec1"
        return "mx1"

    monkeypatch.setattr("app.saw_lab.batch_router.store_artifact", _fake_store_artifact)
    monkeypatch.setattr("app.saw_lab.batch_router.maybe_autorollup_execution_metrics", _fake_maybe_autorollup_execution_metrics, raising=False)

    # Import after monkeypatch where possible
    from app.saw_lab.batch_router import JobLogRequest, write_job_log

    req = JobLogRequest(
        batch_plan_artifact_id="plan1",
        batch_execution_artifact_id="exec1",
        session_id="s1",
        batch_label="b1",
        statistics={"total_length_mm": 10.0},
        notes="ok",
    )

    resp = write_job_log(req)
    assert resp.batch_job_log_artifact_id == "jl1"
    assert called["n"] == 1
