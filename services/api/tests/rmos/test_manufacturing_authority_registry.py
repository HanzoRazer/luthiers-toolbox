"""RMOS-AUTHORITY-MAP-001 Stage 1 — registry integrity (MAR-001–005).

These tests inspect the committed inert census JSON. They do not import
production routers and they do not assign authority conclusions.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_PATH = (
    REPO_ROOT / "services/api/app/rmos/manufacturing_authority_registry.json"
)
SCHEMA_PATH = (
    REPO_ROOT
    / "services/api/app/rmos/schemas/manufacturing_authority_registry.schema.json"
)
SCRIPT = REPO_ROOT / "scripts/audit/rmos_authority_map.py"

AUTHORITATIVE = {
    "GOVERNED",
    "GOVERNED_PROVENANCE_DEFECT",
    "LIVE_UNGOVERNED_OUTPUT",
    "BLOCKED_BY_DESIGN",
    "AUTHORITY_CONTRACT_MISMATCH",
    "POST_MERGE_AUTHORITY_EXPOSURE",
    "RUNTIME_BROKEN",
    "EXPLICITLY_NON_PRODUCTION",
    "ADVISORY_ONLY",
}

REQUIRED_SEEDS = (
    "retract",
    "adaptive",
    "drilling",
    "profiling",
    "vcarve",
    "roughing",
    "helical",
    "rosette",
    "probing",
    "binding",
    "inlay",
    "radius-dish",
    "feeds-speeds",
    "biarc-contour",
)


def _load_script():
    spec = importlib.util.spec_from_file_location("rmos_authority_map", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_registry_and_schema_exist():
    assert REGISTRY_PATH.is_file()
    assert SCHEMA_PATH.is_file()
    assert SCRIPT.is_file()


def test_schema_warns_no_execution_authority(schema):
    text = (schema.get("description") or "") + json.dumps(schema)
    assert "GRANTS NO EXECUTION AUTHORITY" in text.upper() or "no execution authority" in text.lower()
    assert "CANONICAL_AUTHORITY_MAP" in text
    assert "geometry_authority_registry" in text
    assert "ontology_authority_map" in text


def test_registry_warns_no_execution_authority(registry):
    assert "GRANTS NO EXECUTION AUTHORITY" in registry["warning"].upper()
    paths = {m["path"] for m in registry["adjacent_authority_maps"]}
    assert "docs/governance/CANONICAL_AUTHORITY_MAP.md" in paths
    assert "services/api/app/cam/geometry_authority_registry.py" in paths
    assert "services/api/app/cam/ontology_authority_map.py" in paths


def test_mar_001_capability_ids_unique(registry):
    ids = [c["capability_id"] for c in registry["capabilities"]]
    assert ids, "registry has no capabilities"
    assert len(ids) == len(set(ids))


def test_mar_002_dispositions_in_controlled_vocabulary(registry):
    vocab = set(registry["disposition_vocabulary"])
    for cap in registry["capabilities"]:
        assert cap["authority_disposition"] in vocab, cap["capability_id"]
        assert cap["reachability"] in set(registry["reachability_vocabulary"])


def test_mar_003_authoritative_conclusions_have_evidence(registry):
    for cap in registry["capabilities"]:
        disp = cap["authority_disposition"]
        if disp in AUTHORITATIVE:
            assert cap.get("evidence"), f"{cap['capability_id']} {disp} lacks evidence"


def test_emit_skeleton_stays_unknown():
    """--emit-skeleton remains the UNKNOWN taxonomy checkpoint."""
    mod = _load_script()
    skeleton = mod.build_skeleton(
        {
            "routes": [],
            "top_level_route_objects": 0,
            "walked_operations": 0,
            "unique_mounted_operations": 0,
            "unique_mounted_paths": 0,
            "openapi_paths": 0,
            "duplicate_mounts": [],
        },
        {"candidates": [], "exclusions": []},
    )
    assert skeleton["stage"] == "stage_1_checkpoint"
    for cap in skeleton["capabilities"]:
        assert cap["authority_disposition"] in {"UNKNOWN", "INSUFFICIENT_EVIDENCE"}
        assert cap["runtime_evidence"] == "NOT_OBTAINED_STAGE_1"
        assert cap["surface_kind"] in set(mod.SURFACE_KIND_VOCABULARY)


def test_committed_registry_is_stage2(registry):
    assert registry["stage"] == "stage_2_authority"
    kinds = {c["surface_kind"] for c in registry["capabilities"]}
    assert "manufacturing_capability" in kinds
    assert "advisory" in kinds
    assert "artifact_retrieval" in kinds
    assert "artifact_transformation" in kinds
    feeds = next(c for c in registry["capabilities"] if c["capability_id"] == "feeds-speeds")
    assert feeds["surface_kind"] == "advisory"
    assert feeds["authority_disposition"] == "ADVISORY_ONLY"
    op = next(c for c in registry["capabilities"] if c["capability_id"] == "operator-pack")
    assert op["surface_kind"] == "artifact_retrieval"
    assert op["authority_disposition"] != "GOVERNED"
    geom = next(c for c in registry["capabilities"] if c["capability_id"] == "geometry")
    assert geom["surface_kind"] == "artifact_transformation"
    for cap in registry["capabilities"]:
        assert cap["runtime_evidence"] != "NOT_OBTAINED_STAGE_1"
        assert cap["generation_ordering"] != "UNKNOWN" or cap["authority_disposition"] in {
            "UNKNOWN",
            "INSUFFICIENT_EVIDENCE",
        }


def test_required_seed_capabilities_present(registry):
    ids = {c["capability_id"] for c in registry["capabilities"]}
    missing = [s for s in REQUIRED_SEEDS if s not in ids]
    assert not missing, missing
    by_id = {c["capability_id"]: c for c in registry["capabilities"]}
    for seed in REQUIRED_SEEDS:
        assert by_id[seed]["routes"], f"seeded capability {seed} has no mounted routes"


def test_mar_005_stale_routes_need_historical_flag(registry):
    for cap in registry["capabilities"]:
        for route in cap["routes"]:
            if route["mount_state"] in {"HISTORICAL", "DEAD", "UNMOUNTED"}:
                assert route["historical_or_dead"] is True
            if route["historical_or_dead"] is False:
                assert route["mount_state"] == "MOUNTED"


def test_retract_aliases_are_one_capability(registry):
    retract = next(c for c in registry["capabilities"] if c["capability_id"] == "retract")
    paths = {r["path"] for r in retract["routes"]}
    assert "/api/cam/retract/gcode" in paths
    assert "/api/cam/retract/gcode/download" in paths
    assert "/api/cam/retract/gcode_governed" in paths
    assert "/api/cam/retract/gcode/download_governed" in paths
    # Aliases must not appear as their own capabilities.
    ids = [c["capability_id"] for c in registry["capabilities"]]
    assert "retract-gcode" not in ids
    assert "gcode_governed" not in ids


def test_acoustic_binding_is_not_guitar(registry):
    binding = next(c for c in registry["capabilities"] if c["capability_id"] == "binding")
    guitar = next(c for c in registry["capabilities"] if c["capability_id"] == "cam-guitar")
    bind_paths = {r["path"] for r in binding["routes"]}
    guitar_paths = {r["path"] for r in guitar["routes"]}
    acoustic_binding = [p for p in bind_paths if "/acoustic/" in p and "/binding/" in p]
    assert acoustic_binding, "owner ruling: acoustic binding belongs to binding"
    assert not any("/binding/" in p for p in guitar_paths)


def test_schema_validates_committed_registry(registry, schema):
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator(schema).validate(registry)


def test_script_validate_registry_helper_agrees(registry, schema):
    mod = _load_script()
    errors = mod.validate_registry(registry, schema=schema)
    assert errors == []
