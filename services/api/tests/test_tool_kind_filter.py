"""BR-002B regression: tool_kind filtering (canonical helper, list/count parity, batch_tree/BR-035).

Verifies the behavioral contract established by the BR-002A empirical gate:
  requested "saw"     matches persisted "saw", "saw_lab", and missing; NOT "cnc"
  requested "saw_lab" matches persisted "saw", "saw_lab", and missing; NOT "cnc"
  no requested filter -> everything matches
"""
from __future__ import annotations

import os
import tempfile

import pytest

from app.rmos.runs_v2.store_filter import tool_kind_matches, index_tool_kind, matches_index_meta


# --------------------------------------------------------------------------- #
# 1. Canonical matcher contract
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("stored,requested,expected", [
    ("saw", "saw", True),
    ("saw_lab", "saw", True),        # synonym
    ("saw", "saw_lab", True),        # synonym (symmetric)
    ("saw_lab", "saw_lab", True),
    (None, "saw", True),             # missing -> lenient
    ("", "saw", True),               # empty -> lenient
    ("cnc", "saw", False),           # unrelated -> no match
    ("cnc", "saw_lab", False),
    ("saw", None, True),             # no filter -> match everything
    ("cnc", None, True),
])
def test_tool_kind_matches_contract(stored, requested, expected):
    assert tool_kind_matches(stored, requested) is expected


def test_index_tool_kind_reads_nested_meta():
    # empirical gate: tool_kind lives in m["meta"]["tool_kind"], not top-level
    assert index_tool_kind({"meta": {"tool_kind": "saw_lab"}}) == "saw_lab"
    assert index_tool_kind({"index_meta": {"tool_kind": "saw"}}) == "saw"
    assert index_tool_kind({"tool_kind": "saw"}) == "saw"          # top-level fallback
    assert index_tool_kind({"meta": {}}) is None                   # missing


def test_matches_index_meta_tool_kind_reads_meta_not_toplevel():
    saw = {"meta": {"tool_kind": "saw"}}
    saw_lab = {"meta": {"tool_kind": "saw_lab"}}
    missing = {"meta": {}}
    cnc = {"meta": {"tool_kind": "cnc"}}
    assert matches_index_meta(saw, tool_kind="saw")
    assert matches_index_meta(saw_lab, tool_kind="saw")      # synonym, not dropped
    assert matches_index_meta(missing, tool_kind="saw")      # lenient, not dropped
    assert not matches_index_meta(cnc, tool_kind="saw")      # unrelated, excluded


# --------------------------------------------------------------------------- #
# 2. End-to-end store: mixed-tag batch, list/count parity
# --------------------------------------------------------------------------- #
@pytest.fixture()
def temp_store(monkeypatch):
    d = tempfile.mkdtemp(prefix="tk_test_")
    monkeypatch.setenv("RMOS_RUNS_DIR", d)
    from app.rmos.runs_v2 import store_api as sa, store as st
    # fresh default store bound to the temp dir
    st._default_store = st.RunStoreV2(root_dir=d)
    return sa, st


def _seed_mixed(sa):
    sa.store_artifact(kind="saw_batch_execution", payload={"s": 1}, session_id="S1", batch_label="B1")                 # saw (default)
    sa.store_artifact(kind="saw_feasibility",     payload={"s": 1}, session_id="S1", batch_label="B1", tool_kind="saw_lab")
    sa.store_artifact(kind="legacy",              payload={"s": 1}, session_id="S1", batch_label="B1", tool_kind="")   # missing
    sa.store_artifact(kind="cnc_job",             payload={"s": 1}, session_id="S1", batch_label="B1", tool_kind="cnc")


def test_mixed_tag_batch_not_dropped(temp_store):
    sa, st = temp_store
    _seed_mixed(sa)
    store = st._get_default_store(); store.rebuild_index()
    rows = st.list_runs_filtered(session_id="S1", batch_label="B1", tool_kind="saw")
    assert len(rows) == 3          # saw + saw_lab + missing, NOT cnc
    assert len(st.list_runs_filtered(session_id="S1", batch_label="B1")) == 4   # unfiltered


def test_list_count_parity(temp_store):
    sa, st = temp_store
    _seed_mixed(sa)
    st._get_default_store().rebuild_index()
    listed = st.list_runs_filtered(tool_kind="saw", limit=1000)
    counted = st.count_runs_filtered(tool_kind="saw")
    assert counted == len(listed)   # count must agree with list under the same filter


# --------------------------------------------------------------------------- #
# 3. BR-001: saw_lab store_artifact accepts batch_label + tool_kind
# --------------------------------------------------------------------------- #
def test_saw_lab_store_artifact_batch_label_roundtrip():
    from app.saw_lab import store as sl
    aid = sl.store_artifact(kind="saw_batch_execution", payload={"session_id": "X"},
                            session_id="X", batch_label="BL9", tool_kind="saw")
    rec = sl._batch_artifacts[aid]
    assert rec["payload"].get("batch_label") == "BL9"     # readers use payload.get("batch_label")
    assert rec["index_meta"].get("tool_kind") == "saw"


# --------------------------------------------------------------------------- #
# 4. BR-035: batch_tree tool_kind filtering uses the lenient/synonym helper
# --------------------------------------------------------------------------- #
def test_batch_tree_tool_kind_lenient(monkeypatch):
    from app.rmos.runs_v2 import batch_tree as bt

    # inject a list_runs_filtered that returns dict items (batch_tree's expected shape)
    items = [
        {"id": "a1", "kind": "saw_batch_spec", "index_meta": {"tool_kind": "saw"}},
        {"id": "a2", "kind": "saw_batch_execution", "parent_id": "a1", "index_meta": {"tool_kind": "saw_lab"}},
        {"id": "a3", "kind": "saw_batch_execution", "parent_id": "a1", "index_meta": {}},          # missing
        {"id": "a4", "kind": "cnc_job", "index_meta": {"tool_kind": "cnc"}},                       # unrelated
    ]

    def fake_lrf(**kw):
        return items

    tree = bt.list_batch_tree(list_runs_filtered=fake_lrf, session_id="S1", batch_label="B1", tool_kind="saw")
    ids = {n["id"] for n in tree["nodes"]}
    assert ids == {"a1", "a2", "a3"}          # saw + saw_lab + missing kept; cnc dropped
    root = bt.resolve_batch_root(list_runs_filtered=fake_lrf, session_id="S1", batch_label="B1", tool_kind="saw")
    assert root == "a1"                        # root resolvable in a mixed-tag batch


# --------------------------------------------------------------------------- #
# 5. BR-002B review fixes
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("stored,requested", [
    ("Saw", "saw"),
    ("SAW_LAB", "saw"),
    ("saw", "SAW"),
    ("Saw_Lab", "saw_lab"),
])
def test_tool_kind_matches_is_case_insensitive(stored, requested):
    """A tagged artifact must not vanish from a filtered result over letter case.

    Written from intent: the policy is lenient, so a *tagged* artifact disappearing is
    a missing-category defect. Case-folding is the term that carries the variation.
    """
    assert tool_kind_matches(stored, requested) is True


def test_tool_kind_case_variation_still_excludes_unrelated():
    """Case-folding must not widen the filter to unrelated tools."""
    assert tool_kind_matches("CNC", "saw") is False
    assert tool_kind_matches("Cnc", "saw_lab") is False


def test_saw_lab_batch_label_payload_and_meta_cannot_disagree():
    """A conflicting payload label and kwarg must not persist two different values.

    Before the fix the payload kept "B_PAYLOAD" (what query_latest_by_label_and_session
    reads) while index_meta kept "B_KWARG" (what a meta-based filter reads), so the same
    artifact resolved differently depending on which reader asked.
    """
    from app.saw_lab import store as sl
    aid = sl.store_artifact(
        kind="saw_batch_execution",
        payload={"batch_label": "B_PAYLOAD"},
        batch_label="B_KWARG",
    )
    rec = sl._batch_artifacts[aid]
    assert rec["payload"]["batch_label"] == rec["index_meta"]["batch_label"]
    assert rec["payload"]["batch_label"] == "B_PAYLOAD"   # precedence unchanged


def test_saw_lab_tool_kind_meta_and_kwarg_cannot_disagree():
    from app.saw_lab import store as sl
    aid = sl.store_artifact(
        kind="saw_batch_execution",
        payload={},
        index_meta={"tool_kind": "saw_lab"},
        tool_kind="saw",
    )
    rec = sl._batch_artifacts[aid]
    assert rec["index_meta"]["tool_kind"] == "saw_lab"    # explicit index_meta wins


def test_resolve_batch_root_non_dict_items_does_not_crash_without_tool_kind():
    """resolve_batch_root must behave the same for non-dict artifacts either way.

    The real store returns List[RunArtifact] (pydantic), not dicts. Previously the
    isinstance filter applied only under `if tool_kind`, so the unfiltered call raised
    AttributeError (HTTP 500) while the filtered call returned None. Pins the symmetry.
    Underlying shape defect is BR-036 and is deliberately still unfixed.
    """
    from app.rmos.runs_v2 import batch_tree as bt

    class _Obj:  # stands in for RunArtifact: no .get()
        run_id = "r1"
        event_type = "saw_batch_spec"

    def fake_lrf(**kw):
        return [_Obj()]

    without = bt.resolve_batch_root(list_runs_filtered=fake_lrf, session_id="S", batch_label="B")
    with_tk = bt.resolve_batch_root(list_runs_filtered=fake_lrf, session_id="S", batch_label="B", tool_kind="saw")
    assert without == with_tk is None
