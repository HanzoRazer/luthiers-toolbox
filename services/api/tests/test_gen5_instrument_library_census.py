"""GEN-5-A — focused tests for the instrument-library source census utility.

These test the census tool itself (data inspection), not any runtime module. The
utility must parse all five legacy sources WITHOUT importing ``app.*``.
"""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "services/api/scripts/build_instrument_library_census.py"
FROZEN_NOW = "2026-07-06T00:00:00+00:00"

REPRESENTATIVE_IDS = ["stratocaster", "les_paul", "flying_v", "dreadnought", "om_000"]
EXPECTED_SOURCES = [
    "model_specs",
    "instrument_model_registry",
    "body_dimension_reference",
    "body_templates",
    "body_catalog",
]


def _load_module():
    spec = importlib.util.spec_from_file_location("gen5_census", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def census():
    return _load_module().build_census(REPO_ROOT, FROZEN_NOW)


def test_script_exists():
    assert SCRIPT.exists(), f"census utility missing: {SCRIPT}"


def test_loads_all_five_sources(census):
    # every named source resolved with a positive entry count
    assert set(census["source_counts"]) == set(EXPECTED_SOURCES)
    for source in EXPECTED_SOURCES:
        assert census["source_counts"][source] > 0, f"{source} produced no entries"


def test_source_counts_present_in_snapshot(census):
    for source in EXPECTED_SOURCES:
        snap = census["source_snapshot"][source]
        assert snap["count"] == census["source_counts"][source]
        assert snap["path"], f"{source} snapshot missing path"


def test_representative_ids_present(census):
    for mid in REPRESENTATIVE_IDS:
        assert mid in census["model_index"], f"representative id {mid} absent from census"
        assert census["model_index"][mid]["present_in_count"] >= 1


def test_model_specs_resolved_from_enum(census):
    # MODEL_SPECS keys are InstrumentModelId.<MEMBER> — must resolve to string ids
    strat = census["model_index"]["stratocaster"]
    assert strat["presence"]["model_specs"] is True
    assert strat["source_ids"]["model_specs"] == "stratocaster"


def test_original_ids_distinct_from_normalized(census):
    # at least one model must carry an original source id that differs from its
    # normalized id (proves original ids are preserved, not overwritten)
    found = False
    for norm, mi in census["model_index"].items():
        for source, original in mi["source_ids"].items():
            if original != norm:
                found = True
    assert found, "no original id differed from normalized id — aliasing not exercised"


def test_known_alias_folding(census):
    # es335 (body_dimension_reference) folds with es_335 (registry) under one model
    assert "es_335" in census["model_index"]
    src_ids = census["model_index"]["es_335"]["source_ids"]
    originals = set(src_ids.values())
    assert "es335" in originals or "es_335" in originals


def test_source_specific_entry_reported_not_dropped(census):
    # 'js1000' exists only in body_catalog and must survive into the census
    assert "js1000" in census["model_index"], "catalog-only entry js1000 was dropped"
    presence = census["model_index"]["js1000"]["presence"]
    assert presence["body_catalog"] is True
    assert sum(presence.values()) == 1, "js1000 should be single-source"


def test_conflicts_are_structured_records(census):
    conflicts = census["conflicts"]
    assert isinstance(conflicts, list) and conflicts, "expected >=1 structured conflict"
    for rec in conflicts:
        assert set(["model", "field", "values", "delta", "note"]).issubset(rec)
        assert isinstance(rec["values"], dict) and len(rec["values"]) >= 2
    # the known stratocaster scale_length disagreement (648.0 vs 647.7)
    strat = [c for c in conflicts
             if c["model"] == "stratocaster" and c["field"] == "scale_length_mm"]
    assert strat, "expected stratocaster scale_length_mm conflict"


def test_missing_by_source_shape(census):
    assert set(census["missing_by_source"]) == set(EXPECTED_SOURCES)
    for source, missing in census["missing_by_source"].items():
        assert isinstance(missing, list)
        assert missing == sorted(missing)


def test_deterministic_for_unchanged_input():
    mod = _load_module()
    a = mod.build_census(REPO_ROOT, FROZEN_NOW)
    b = mod.build_census(REPO_ROOT, FROZEN_NOW)
    assert mod._stable_json(a) == mod._stable_json(b)
    # only generated_at is non-deterministic across timestamps
    c = mod.build_census(REPO_ROOT, "2099-01-01T00:00:00+00:00")
    assert mod._strip_generated_at(a) == mod._strip_generated_at(c)


def test_check_mode_passes_on_committed_artifacts():
    mod = _load_module()
    rc = mod.main(["--check", "--now", FROZEN_NOW, "--repo-root", str(REPO_ROOT)])
    assert rc == 0, "committed artifacts are stale vs sources — run --write"


def test_utility_does_not_import_app_modules():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            offenders += [a.name for a in node.names if a.name.split(".")[0] == "app"]
        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root == "app":
                offenders.append(node.module)
    assert not offenders, f"census utility must not import app.*: {offenders}"


def test_schema_proposal_is_field_role_based(census):
    proposal = census["schema_proposal"]
    assert proposal["version"]
    model = proposal["families"]["<family>"]["models"]["<model_id>"]
    for role in ["metadata", "physical_dimensions", "body_template", "body_catalog",
                 "runtime_spec", "assets", "cam_capability", "source_provenance"]:
        assert role in model, f"schema proposal missing field-role group: {role}"
