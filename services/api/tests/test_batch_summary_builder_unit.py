from __future__ import annotations

from app.rmos.runs_v2.batch_summary import BatchSummaryPorts, build_batch_summary


class _FakePorts:
    def __init__(self, artifacts):
        self._arts = {a["id"]: a for a in artifacts}

    def list_runs_filtered(self, **kwargs):
        sid = kwargs.get("session_id")
        bl = kwargs.get("batch_label")
        tk = kwargs.get("tool_kind")
        out = []
        for a in self._arts.values():
            meta = a.get("index_meta", {})
            if sid and meta.get("session_id") != sid:
                continue
            if bl and meta.get("batch_label") != bl:
                continue
            if tk and meta.get("tool_kind") != tk:
                continue
            out.append(a)
        return {"items": out}

    def get_run(self, artifact_id: str):
        return self._arts.get(artifact_id)


def test_batch_summary_rolls_up_counts_latest_and_status_risk():
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}, "payload": {"created_utc": "2026-01-01T00:00:00+00:00"}},
        {"id": "plan1", "kind": "saw_batch_plan", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_spec_artifact_id": "spec1"}, "payload": {"created_utc": "2026-01-01T00:01:00+00:00", "status": "OK"}},
        {"id": "dec1", "kind": "saw_batch_decision", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_plan_artifact_id": "plan1"}, "payload": {"created_utc": "2026-01-01T00:02:00+00:00", "status": "APPROVED", "risk_bucket": "GREEN"}},
        {"id": "tp1", "kind": "saw_batch_toolpaths", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_decision_artifact_id": "dec1"}, "payload": {"created_utc": "2026-01-01T00:03:00+00:00", "status": "OK", "risk_bucket": "GREEN"}},
        {"id": "jl1", "kind": "saw_batch_job_log", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}, "payload": {"created_utc": "2026-01-01T00:04:00+00:00", "status": "OK"}},
    ]
    ports = _FakePorts(artifacts)
    out = build_batch_summary(
        BatchSummaryPorts(list_runs_filtered=ports.list_runs_filtered, get_run=ports.get_run),
        session_id="s1",
        batch_label="b1",
        tool_kind="saw",
        max_nodes=100,
    )
    assert out["session_id"] == "s1"
    assert out["batch_label"] == "b1"
    assert out["counts_by_type"]["spec"] == 1
    assert out["counts_by_type"]["plan"] == 1
    assert out["counts_by_type"]["decision"] == 1
    assert out["counts_by_type"]["toolpaths"] == 1
    assert out["counts_by_type"]["job_log"] == 1
    assert out["stages"]["toolpaths"]["latest_id"] == "tp1"
    assert out["overall_status"] == "OK"
    assert out["overall_risk"] == "GREEN"
    assert out["first_seen_utc"] == "2026-01-01T00:00:00+00:00"
    assert out["last_seen_utc"] == "2026-01-01T00:04:00+00:00"
