"""
DXF-CATALOG-GATE-001: the DXF catalog registry (split from test_dxf_catalog_gate.py).

Registry integrity on the committed file, schema v2 rejection of malformed
registries with a clear message, clause drift between registry and gates,
and per-segment class globs with no rule-order dependence.
"""
import copy
import importlib.util
import sys
from pathlib import Path

import pytest

from app.ci import check_dxf_files
from app.ci import dxf_catalog_policy as policy

pytestmark = pytest.mark.allow_missing_request_id

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_ROOT = REPO_ROOT / "services" / "api" / "app" / "instrument_geometry"
BODY = "manufacturing_body"


@pytest.fixture(scope="module")
def registry():
    return policy.load_registry()


@pytest.fixture(scope="module")
def asset_gate():
    path = REPO_ROOT / "scripts" / "validate_dxf_assets.py"
    spec = importlib.util.spec_from_file_location("validate_dxf_assets_registry_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

# -----------------------------------------------------------------------------
# Registry integrity
# -----------------------------------------------------------------------------

def test_version_policy_is_r12_only(registry):
    assert registry["version_policy"]["approved"] == ["AC1009"]


def test_every_catalog_dxf_is_classified(registry):
    unclassified = [p for p in CATALOG_ROOT.rglob("*.dxf")
                    if policy.classify(policy.relative_asset(p, CATALOG_ROOT), registry) is None]
    assert unclassified == []


def test_quarantine_records_are_complete_and_blocked(registry):
    clauses = set(registry["clauses"])
    dispositions = {"QUARANTINED", "QUARANTINE_CANDIDATE", "UNADJUDICATED", "NONCONFORMING_VERSION"}
    assets = [r["asset"] for r in registry["quarantine"]]
    assert len(assets) == len(set(assets)), "one record per asset"
    for record in registry["quarantine"]:
        assert all(record.get(f) for f in policy.RECORD_FIELDS), record["asset"]
        assert record["manufacturing_authority"] == "BLOCKED"
        assert record["owner_stream"] == "DXF Catalog Integrity"
        assert record["disposition"] in dispositions
        assert set(record["failed_contract"]) <= clauses
        assert set(record["failed_contract"]) <= set(policy.contract_for(record["asset_class"], registry))
        assert policy.classify(record["asset"], registry) == record["asset_class"]


def test_no_orphan_quarantine_records(registry):
    assert policy.orphan_records(registry, CATALOG_ROOT) == []


# -----------------------------------------------------------------------------
# Registry schema (v2): malformed registries fail at load with a clear message
# -----------------------------------------------------------------------------

def _mutate(registry, fn):
    reg = copy.deepcopy(registry)
    fn(reg)
    return reg


SCHEMA_BREAKS = [
    ("schema name", lambda r: r.update(schema="dxf_catalog_registry_v1"), "schema is"),
    ("clause drift", lambda r: r["clauses"].pop("topology_valid"), "clauses must be exactly"),
    ("unknown clause in record", lambda r: r["quarantine"][0]["failed_contract"].append("no_such_clause"),
     "not within"),
    ("missing coverage", lambda r: r["asset_classes"][BODY].pop("outline_coverage_min"), "outline_coverage_min"),
    ("bad disposition", lambda r: r["quarantine"][0].update(disposition="LOOKS_FINE"), "disposition"),
    ("evidence cites wrong clause",
     lambda r: r["quarantine"][0]["observed_evidence"]["gate"].append("[closed_outline] x"), "gate evidence cites"),
    ("bad sha", lambda r: r["quarantine"][0].update(asset_sha256="abc"), "asset_sha256"),
    ("owner is a person", lambda r: r["quarantine"][0].update(owner_stream="Ross"), "owner_stream"),
    ("authority not blocked", lambda r: r["quarantine"][0].update(manufacturing_authority="ALLOWED"), "BLOCKED"),
    ("rule to unknown class", lambda r: r["class_rules"].append({"glob": "x/*.dxf", "class": "ghost"}),
     "unknown class"),
    ("record class disagrees with rules", lambda r: r["quarantine"][0].update(asset_class="reference"),
     "classify the asset"),
    ("duplicate record", lambda r: r["quarantine"].append(copy.deepcopy(r["quarantine"][0])), "duplicate"),
    ("missing field", lambda r: r["quarantine"][0].pop("exit_condition"), "missing or empty"),
]


@pytest.mark.parametrize("name,mutate,expected", SCHEMA_BREAKS, ids=[b[0] for b in SCHEMA_BREAKS])
def test_malformed_registry_is_rejected_with_a_clear_message(registry, name, mutate, expected):
    from app.ci import dxf_catalog_schema as schema

    with pytest.raises(schema.RegistryError, match=expected):
        schema.validate_registry(_mutate(registry, mutate), policy.classify)


def test_every_registry_clause_is_implemented_and_vice_versa():
    from app.ci import dxf_catalog_schema as schema

    implemented = set(check_dxf_files.CLAUSE_CHECKS) | {"readable"}
    assert implemented == set(schema.KNOWN_CLAUSES)
    assert check_dxf_files.GATE_CLAUSES == set(schema.KNOWN_CLAUSES)


def test_asset_gate_evaluates_only_known_clauses(asset_gate):
    assert asset_gate.GATE_CLAUSES <= set(policy.KNOWN_CLAUSES)


# -----------------------------------------------------------------------------
# Classification: per-segment globs, no rule-order dependence
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("path,expected", [
    ("body/dxf/electric/x.dxf", BODY),
    ("body/dxf/electric/nested/x.dxf", None),  # a single star does not span folders
    ("body/dxf/x.dxf", None),
    ("reference_dxf/x.dxf", "reference"),
    ("reference_dxf/cuatro/regenerated_v3/x.dxf", "reference"),
    ("reference_dxf/cuatro/notes.txt", None),
])
def test_class_globs_match_per_segment(registry, path, expected):
    assert policy.classify(path, registry) == expected


def test_overlapping_rules_for_two_classes_are_an_error(registry):
    reg = _mutate(registry, lambda r: r["class_rules"].append({"glob": "body/**/*.dxf", "class": "reference"}))
    with pytest.raises(policy.RegistryError, match="Ambiguous"):
        policy.classify("body/dxf/electric/x.dxf", reg)


def test_registry_catalog_root_must_match_the_scanned_root(registry, tmp_path):
    problems = policy.registry_problems(registry, REPO_ROOT, tmp_path)
    assert any("catalog_root" in p for p in problems)
    assert policy.registry_problems(registry, REPO_ROOT, CATALOG_ROOT) == []
