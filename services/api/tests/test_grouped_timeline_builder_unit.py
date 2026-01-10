from __future__ import annotations

from app.rmos.runs_v2.batch_grouped_timeline import GroupedTimelinePorts, build_grouped_timeline


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


def test_grouped_timeline_builds_nested_tree_and_by_type():
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}, "payload": {"created_utc": "2026-01-01T00:00:00+00:00", "tool_id": "saw:thin_140", "items": [{"material_id": "maple"}]}},
        {"id": "plan1", "kind": "saw_batch_plan", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_spec_artifact_id": "spec1"}, "payload": {"created_utc": "2026-01-01T00:01:00+00:00", "setups": []}},
        {"id": "dec1", "kind": "saw_batch_decision", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_plan_artifact_id": "plan1"}, "payload": {"created_utc": "2026-01-01T00:02:00+00:00", "risk_bucket": "GREEN", "selected_setup_key": "setup_1"}},
        {"id": "tp1", "kind": "saw_batch_toolpaths", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_decision_artifact_id": "dec1"}, "payload": {"created_utc": "2026-01-01T00:03:00+00:00", "statistics": {"move_count": 5}}},
    ]
    ports = _FakePorts(artifacts)
    out = build_grouped_timeline(
        GroupedTimelinePorts(list_runs_filtered=ports.list_runs_filtered, get_run=ports.get_run),
        session_id="s1",
        batch_label="b1",
        tool_kind="saw",
        max_nodes=50,
    )
    assert out["root_artifact_id"] == "spec1"
    root = out["grouped_root"]
    assert root["id"] == "spec1"
    assert root["children"][0]["id"] == "plan1"
    assert root["children"][0]["children"][0]["id"] == "dec1"
    assert root["children"][0]["children"][0]["children"][0]["id"] == "tp1"

    assert "spec" in out["by_type"]
    assert "plan" in out["by_type"]
    assert "decision" in out["by_type"]
    assert "toolpaths" in out["by_type"]


def test_grouped_timeline_filters_hide_types_and_lifts_descendants():
    # spec -> plan -> decision -> toolpaths, plus an "other" leaf under decision
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}, "payload": {"created_utc": "2026-01-01T00:00:00+00:00"}},
        {"id": "plan1", "kind": "saw_batch_plan", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_spec_artifact_id": "spec1"}, "payload": {"created_utc": "2026-01-01T00:01:00+00:00"}},
        {"id": "dec1", "kind": "saw_batch_decision", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_plan_artifact_id": "plan1"}, "payload": {"created_utc": "2026-01-01T00:02:00+00:00"}},
        {"id": "oth1", "kind": "saw_note_misc", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_decision_artifact_id": "dec1"}, "payload": {"created_utc": "2026-01-01T00:02:30+00:00"}},
        {"id": "tp1", "kind": "saw_batch_toolpaths", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_decision_artifact_id": "dec1"}, "payload": {"created_utc": "2026-01-01T00:03:00+00:00", "statistics": {"move_count": 5}}},
    ]
    ports = _FakePorts(artifacts)
    out = build_grouped_timeline(
        GroupedTimelinePorts(list_runs_filtered=ports.list_runs_filtered, get_run=ports.get_run),
        session_id="s1",
        batch_label="b1",
        tool_kind="saw",
        max_nodes=50,
        include_types={"spec", "plan", "decision", "toolpaths"},  # hide "other"
        collapse_other=False,
    )
    root = out["grouped_root"]
    assert root["id"] == "spec1"
    # Ensure "oth1" is not present, but toolpaths remain reachable
    def _collect_ids(n):
        ids = [n.get("id")]
        for c in n.get("children", []):
            ids.extend(_collect_ids(c))
        return ids
    ids = set(_collect_ids(root))
    assert "oth1" not in ids
    assert "tp1" in ids


def test_grouped_timeline_collapse_other_under_nearest_anchor():
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}, "payload": {"created_utc": "2026-01-01T00:00:00+00:00"}},
        {"id": "plan1", "kind": "saw_batch_plan", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_spec_artifact_id": "spec1"}, "payload": {"created_utc": "2026-01-01T00:01:00+00:00"}},
        {"id": "dec1", "kind": "saw_batch_decision", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_plan_artifact_id": "plan1"}, "payload": {"created_utc": "2026-01-01T00:02:00+00:00"}},
        {"id": "oth1", "kind": "saw_note_misc", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_decision_artifact_id": "dec1"}, "payload": {"created_utc": "2026-01-01T00:02:30+00:00"}},
        {"id": "tp1", "kind": "saw_batch_toolpaths", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_decision_artifact_id": "dec1"}, "payload": {"created_utc": "2026-01-01T00:03:00+00:00", "statistics": {"move_count": 5}}},
    ]
    ports = _FakePorts(artifacts)
    out = build_grouped_timeline(
        GroupedTimelinePorts(list_runs_filtered=ports.list_runs_filtered, get_run=ports.get_run),
        session_id="s1",
        batch_label="b1",
        tool_kind="saw",
        max_nodes=50,
        include_types={"spec", "plan", "decision", "toolpaths"},  # hide "other"
        collapse_other=True,
        collapse_other_under="decision",
    )
    root = out["grouped_root"]
    # Expect oth1 attached under decision as a child (but only if we *didn't* explicitly include "other")
    def _find(n, target):
        if n.get("id") == target:
            return n
        for c in n.get("children", []):
            r = _find(c, target)
            if r:
                return r
        return None
    dec = _find(root, "dec1")
    assert dec is not None
    child_ids = [c.get("id") for c in dec.get("children", [])]
    assert "oth1" in child_ids
