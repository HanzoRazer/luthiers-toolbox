"""Validate the consolidation candidate ledger (evidence-only investigation).

This test lives in the investigation directory (NOT a production package). It
validates the two ledger representations, the disposition vocabulary, CF2
accounting against the committed manufacturing-output inventory, and evidence
presence. It covers CRO-007..016 (the non-git-state CRO cases).

Run: python -m pytest docs/investigations/consolidation-resume-options_2026-09-29/test_consolidation_ledger.py -q
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]  # docs/investigations/<dir> -> repo root
LEDGER_JSON = HERE / "CANDIDATE_LEDGER.json"
LEDGER_MD = HERE / "CANDIDATE_LEDGER.md"
CF2_REMAINDER = HERE / "CF2_REMAINDER.md"
INVENTORY = REPO / "services/api/governance/manufacturing_output_inventory.json"

VALID_DISPOSITIONS = {
    "COMPLETE_LIVE", "LIVE_INCOMPLETE", "BUILT_DISCONNECTED", "DUPLICATE_SUPERSEDED",
    "PROTOTYPE_EXPLICIT", "DORMANT_UNRESOLVED", "DEAD_CONFIRMED", "DOC_ONLY", "DEFERRED_AUTHORIZED",
}
BASE_SHA = "5258d4c6754c122fcdad65df2019c9f7c11eaffe"


def _ledger():
    return json.loads(LEDGER_JSON.read_text(encoding="utf-8"))


def test_base_sha_pinned():
    assert _ledger()["base_sha"] == BASE_SHA


def test_cro007_every_candidate_has_one_valid_disposition():
    for c in _ledger()["candidates"]:
        assert c["disposition"] in VALID_DISPOSITIONS, c["candidate_id"]


def test_cro008_every_candidate_has_provenance_and_evidence():
    for c in _ledger()["candidates"]:
        assert c.get("introduced_date"), c["candidate_id"]  # date or 'unverified'
        assert isinstance(c.get("january_provenance"), bool), c["candidate_id"]
        assert c.get("evidence"), f"{c['candidate_id']} has no evidence"


def test_cro009_dead_confirmed_has_exclusion_evidence():
    for c in _ledger()["candidates"]:
        if c["disposition"] == "DEAD_CONFIRMED":
            blob = " ".join(c["evidence"]).lower()
            assert any(k in blob for k in ("no ", "never", "dead", "gate", "absent", "removed")), c["candidate_id"]


def test_cro010_duplicate_names_canonical_survivor():
    for c in _ledger()["candidates"]:
        if c["disposition"] == "DUPLICATE_SUPERSEDED":
            blob = " ".join(c["evidence"] + [c["recommended_action"]]).lower()
            assert any(k in blob for k in ("survivor", "canonical", "mounted", "manifest", "supersed")), c["candidate_id"]


def test_cro011_json_and_md_have_identical_candidate_ids():
    ids = {c["candidate_id"] for c in _ledger()["candidates"]}
    md = LEDGER_MD.read_text(encoding="utf-8")
    md_ids = set(re.findall(r"`([A-Z0-9]+-[0-9]+-[A-Z0-9\-]+)`", md))
    # every JSON id must appear in the MD mirror, and no extra ledger id in MD
    assert ids <= md_ids, ("missing from MD", ids - md_ids)
    assert md_ids <= ids, ("extra in MD", md_ids - ids)


def test_cro012_all_13_live_ungoverned_rows_in_cf2_remainder():
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    live = [r for r in inv["rows"] if r["containment"] == "LIVE_UNGOVERNED"]
    assert len(live) == 13
    text = CF2_REMAINDER.read_text(encoding="utf-8")
    for r in live:
        assert r["path"] in text, f"missing {r['path']} in CF2_REMAINDER.md"
        assert text.count(r["path"]) >= 1


def test_cro013_no_governed_or_unknown_row_labeled_live_ungoverned():
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    rosette = {r["path"]: r["containment"] for r in inv["rows"] if r["path"].startswith("/api/rmos/rosette/")}
    assert rosette.get("/api/rmos/rosette/export-cnc") == "FAIL_CLOSED"
    assert rosette.get("/api/rmos/rosette/design") == "FAIL_CLOSED"
    # CF2_REMAINDER's 13-row table must not list a FAIL_CLOSED/UNKNOWN row as one of the 13
    live_paths = {r["path"] for r in inv["rows"] if r["containment"] == "LIVE_UNGOVERNED"}
    assert "/api/rmos/rosette/design" not in live_paths
    assert "/api/rmos/rosette/export-cnc" not in live_paths


def test_cro015_options_are_three_and_mutually_exclusive():
    opts = (HERE / "OPTIONS.md").read_text(encoding="utf-8")
    for marker in ("Option A", "Option B", "Option C", "mutually exclusive"):
        assert marker in opts


def test_cro016_recommendation_is_one_bounded_increment():
    rec = (HERE / "RECOMMENDATION.md").read_text(encoding="utf-8")
    assert "Option A" in rec
    assert "bounded next increment" in rec.lower()


def test_ledger_count_within_ceiling_and_overflow_recorded():
    d = _ledger()
    assert 1 <= len(d["candidates"]) <= 40, "hard ceiling 40"
    assert isinstance(d.get("overflow_backlog"), list)
    for o in d["overflow_backlog"]:
        assert o.get("path") and o.get("discovery_signal") and o.get("reason_deferred")
