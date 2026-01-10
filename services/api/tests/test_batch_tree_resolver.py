from __future__ import annotations

from app.rmos.runs_v2.batch_tree import list_batch_tree, resolve_batch_root


class _FakeStore:
    def __init__(self, items):
        self._items = items

    def list_runs_filtered(self, **kwargs):
        # naive filter on session_id + batch_label
        sid = kwargs.get("session_id")
        bl = kwargs.get("batch_label")
        out = []
        for a in self._items:
            meta = a.get("index_meta", {})
            if sid and meta.get("session_id") != sid:
                continue
            if bl and meta.get("batch_label") != bl:
                continue
            out.append(a)
        return {"items": out}


def test_resolve_batch_root_prefers_spec_kind():
    items = [
        {"id": "plan1", "kind": "saw_batch_plan", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_spec_artifact_id": "spec1"}},
        {"id": "spec1", "kind": "saw_batch_spec", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
    ]
    store = _FakeStore(items)
    root = resolve_batch_root(list_runs_filtered=store.list_runs_filtered, session_id="s1", batch_label="b1", tool_kind="saw")
    assert root == "spec1"


def test_list_batch_tree_wires_children():
    items = [
        {"id": "spec1", "kind": "saw_batch_spec", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "plan1", "kind": "saw_batch_plan", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_spec_artifact_id": "spec1"}},
        {"id": "dec1", "kind": "saw_batch_decision", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_plan_artifact_id": "plan1"}},
        {"id": "tp1", "kind": "saw_batch_toolpaths", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_decision_artifact_id": "dec1"}},
    ]
    store = _FakeStore(items)
    tree = list_batch_tree(list_runs_filtered=store.list_runs_filtered, session_id="s1", batch_label="b1", tool_kind="saw")
    assert tree["root_artifact_id"] == "spec1"
    nodes = {n["id"]: n for n in tree["nodes"]}
    assert "plan1" in nodes["spec1"]["children"]
    assert "dec1" in nodes["plan1"]["children"]
    assert "tp1" in nodes["dec1"]["children"]


def test_resolve_batch_root_falls_back_to_no_parent():
    """When no spec kind exists, pick the node with no parent in the batch."""
    items = [
        {"id": "root1", "kind": "saw_batch_parent", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "child1", "kind": "saw_batch_child", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_artifact_id": "root1"}},
    ]
    store = _FakeStore(items)
    root = resolve_batch_root(list_runs_filtered=store.list_runs_filtered, session_id="s1", batch_label="b1", tool_kind="saw")
    assert root == "root1"


def test_list_batch_tree_handles_empty_batch():
    store = _FakeStore([])
    tree = list_batch_tree(list_runs_filtered=store.list_runs_filtered, session_id="s1", batch_label="b1")
    assert tree["root_artifact_id"] is None
    assert tree["node_count"] == 0
    assert tree["nodes"] == []


def test_list_batch_tree_orders_nodes_bfs():
    """Nodes should be ordered BFS from root."""
    items = [
        {"id": "spec1", "kind": "saw_batch_spec", "created_utc": "2025-01-01T00:00:00Z", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
        {"id": "plan1", "kind": "saw_batch_plan", "created_utc": "2025-01-01T00:01:00Z", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_spec_artifact_id": "spec1"}},
        {"id": "plan2", "kind": "saw_batch_plan", "created_utc": "2025-01-01T00:02:00Z", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_spec_artifact_id": "spec1"}},
        {"id": "dec1", "kind": "saw_batch_decision", "created_utc": "2025-01-01T00:03:00Z", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_plan_artifact_id": "plan1"}},
    ]
    store = _FakeStore(items)
    tree = list_batch_tree(list_runs_filtered=store.list_runs_filtered, session_id="s1", batch_label="b1", tool_kind="saw")

    # BFS order: spec1 -> plan1, plan2 -> dec1
    ids = [n["id"] for n in tree["nodes"]]
    assert ids[0] == "spec1"
    assert "plan1" in ids[1:3]
    assert "plan2" in ids[1:3]
    assert ids[-1] == "dec1"
