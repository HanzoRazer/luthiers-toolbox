from __future__ import annotations

from app.rmos.runs_v2.batch_timeline import (
    BatchTimelinePorts,
    build_batch_timeline,
    get_batch_progress,
)


class _FakePorts:
    def __init__(self, artifacts):
        self._arts = {a["id"]: a for a in artifacts}

    def list_runs_filtered(self, **kwargs):
        sid = kwargs.get("session_id")
        bl = kwargs.get("batch_label")
        tool_kind = kwargs.get("tool_kind")
        out = []
        for a in self._arts.values():
            meta = a.get("index_meta", {})
            if sid and meta.get("session_id") != sid:
                continue
            if bl and meta.get("batch_label") != bl:
                continue
            if tool_kind and meta.get("tool_kind") != tool_kind:
                continue
            out.append(a)
        return {"items": out}

    def get_run(self, artifact_id: str):
        return self._arts.get(artifact_id)


def test_build_batch_timeline_returns_chronological_events():
    """Test that timeline returns events sorted chronologically."""
    artifacts = [
        {"id": "plan1", "kind": "saw_batch_plan", "created_utc": "2025-01-01T00:01:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "spec1", "kind": "saw_batch_spec", "created_utc": "2025-01-01T00:00:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "dec1", "kind": "saw_batch_decision", "created_utc": "2025-01-01T00:02:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
    ]
    ports = _FakePorts(artifacts)
    timeline = build_batch_timeline(
        BatchTimelinePorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
        ),
        session_id="s1",
        batch_label="b1",
        tool_kind="saw",
    )

    assert timeline["event_count"] == 3
    events = timeline["events"]
    # Should be chronological: spec1, plan1, dec1
    assert events[0]["artifact_id"] == "spec1"
    assert events[1]["artifact_id"] == "plan1"
    assert events[2]["artifact_id"] == "dec1"


def test_build_batch_timeline_assigns_phases():
    """Test that artifact kinds are mapped to correct phases."""
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "created_utc": "2025-01-01T00:00:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "plan1", "kind": "saw_batch_plan", "created_utc": "2025-01-01T00:01:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "dec1", "kind": "saw_batch_decision", "created_utc": "2025-01-01T00:02:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "tp1", "kind": "saw_batch_toolpaths", "created_utc": "2025-01-01T00:03:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
    ]
    ports = _FakePorts(artifacts)
    timeline = build_batch_timeline(
        BatchTimelinePorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
        ),
        session_id="s1",
        batch_label="b1",
    )

    events = timeline["events"]
    phases = {e["artifact_id"]: e["phase"] for e in events}
    assert phases["spec1"] == "SPEC"
    assert phases["plan1"] == "PLAN"
    assert phases["dec1"] == "DECISION"
    assert phases["tp1"] == "TOOLPATHS"


def test_build_batch_timeline_phase_summary():
    """Test that phase_summary contains correct counts and time ranges."""
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "created_utc": "2025-01-01T00:00:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "plan1", "kind": "saw_batch_plan", "created_utc": "2025-01-01T00:01:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "plan2", "kind": "saw_batch_plan", "created_utc": "2025-01-01T00:02:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
    ]
    ports = _FakePorts(artifacts)
    timeline = build_batch_timeline(
        BatchTimelinePorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
        ),
        session_id="s1",
        batch_label="b1",
    )

    ps = timeline["phase_summary"]
    assert ps["SPEC"]["count"] == 1
    assert ps["PLAN"]["count"] == 2
    assert ps["PLAN"]["first_utc"] == "2025-01-01T00:01:00Z"
    assert ps["PLAN"]["last_utc"] == "2025-01-01T00:02:00Z"


def test_build_batch_timeline_empty_batch():
    """Test that empty batch returns valid structure."""
    ports = _FakePorts([])
    timeline = build_batch_timeline(
        BatchTimelinePorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
        ),
        session_id="s1",
        batch_label="b1",
    )

    assert timeline["event_count"] == 0
    assert timeline["events"] == []
    assert timeline["phase_summary"] == {}


def test_get_batch_progress_in_progress():
    """Test progress detection for in-progress batch."""
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "created_utc": "2025-01-01T00:00:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "plan1", "kind": "saw_batch_plan", "created_utc": "2025-01-01T00:01:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
    ]
    ports = _FakePorts(artifacts)
    progress = get_batch_progress(
        BatchTimelinePorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
        ),
        session_id="s1",
        batch_label="b1",
    )

    assert progress["status"] == "IN_PROGRESS"
    assert "SPEC" in progress["phases_completed"]
    assert "PLAN" in progress["phases_completed"]
    assert progress["current_phase"] == "PLAN"
    assert progress["total_artifacts"] == 2


def test_get_batch_progress_completed():
    """Test progress detection for completed batch."""
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "created_utc": "2025-01-01T00:00:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "exec1", "kind": "saw_batch_execution", "created_utc": "2025-01-01T00:05:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
    ]
    ports = _FakePorts(artifacts)
    progress = get_batch_progress(
        BatchTimelinePorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
        ),
        session_id="s1",
        batch_label="b1",
    )

    assert progress["status"] == "COMPLETED"


def test_get_batch_progress_blocked():
    """Test progress detection for blocked batch."""
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "created_utc": "2025-01-01T00:00:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "plan1", "kind": "saw_batch_plan", "created_utc": "2025-01-01T00:01:00Z", "status": "BLOCKED", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
    ]
    ports = _FakePorts(artifacts)
    progress = get_batch_progress(
        BatchTimelinePorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
        ),
        session_id="s1",
        batch_label="b1",
    )

    assert progress["status"] == "BLOCKED"


def test_get_batch_progress_error():
    """Test progress detection for errored batch."""
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "created_utc": "2025-01-01T00:00:00Z", "status": "OK", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "plan1", "kind": "saw_batch_plan", "created_utc": "2025-01-01T00:01:00Z", "status": "ERROR", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
    ]
    ports = _FakePorts(artifacts)
    progress = get_batch_progress(
        BatchTimelinePorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
        ),
        session_id="s1",
        batch_label="b1",
    )

    assert progress["status"] == "ERROR"


def test_get_batch_progress_not_started():
    """Test progress detection for empty batch."""
    ports = _FakePorts([])
    progress = get_batch_progress(
        BatchTimelinePorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
        ),
        session_id="s1",
        batch_label="b1",
    )

    assert progress["status"] == "NOT_STARTED"
    assert progress["phases_completed"] == []
    assert progress["current_phase"] is None
    assert progress["total_artifacts"] == 0
