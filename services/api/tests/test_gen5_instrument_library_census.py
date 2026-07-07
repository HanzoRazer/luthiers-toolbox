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


# --------------------------------------------------------------------------- #
# Regression guards for AST-parse brittleness (silent undercount) and the two
# edge-case fixes: numeric conflict-key and relative output-path resolution.
# --------------------------------------------------------------------------- #
def test_model_specs_count_floor(census):
    # AST extraction of MODEL_SPECS/enum is structurally narrow. If a harmless
    # refactor of guitars/__init__.py or models.py breaks parsing, the count
    # collapses silently and --check still passes (stale artifact == stale
    # recompute). A floor makes that break fail loudly here instead.
    assert census["source_counts"]["model_specs"] >= 15, (
        "model_specs undercount — AST parse of MODEL_SPECS/InstrumentModelId "
        "likely broke after a source refactor; expand the parser or this floor"
    )
    assert census["total_distinct_models"] >= 30, "distinct-model count collapsed"


def test_enum_derived_model_specs_ids_resolved(census):
    # Proves enum members are resolved to their string values (not left as
    # ENUM_MEMBER names). These are stable, known InstrumentModelId values that
    # live in MODEL_SPECS; if the enum value-map parse regresses they vanish.
    for mid in ("stratocaster", "telecaster", "les_paul", "dreadnought"):
        assert mid in census["model_index"], f"{mid} missing from census"
        assert census["model_index"][mid]["presence"]["model_specs"] is True, (
            f"{mid} lost its model_specs presence — enum value resolution regressed"
        )


def test_conflict_key_treats_int_and_float_as_equal():
    mod = _load_module()
    # 648 and 648.0 are the same measurement — must not manufacture a conflict.
    assert mod._conflict_key(648) == mod._conflict_key(648.0)
    # genuine numeric difference stays distinct
    assert mod._conflict_key(648.0) != mod._conflict_key(647.7)
    # bool must never collapse into its int value
    assert mod._conflict_key(True) != mod._conflict_key(1)


def test_relative_output_override_resolves_against_repo_root():
    mod = _load_module()
    root = Path("/some/repo/root").resolve()
    rel = mod._resolve_out("metrics/out.json", "default/rel.json", root)
    # a relative override joins repo_root, NOT the process CWD
    assert rel == root / "metrics/out.json"
    # default (no override) also joins repo_root
    assert mod._resolve_out(None, "default/rel.json", root) == root / "default/rel.json"
    # an absolute override is honored as-is
    abs_path = (root / "elsewhere/out.json").resolve()
    assert mod._resolve_out(str(abs_path), "default/rel.json", root) == abs_path
