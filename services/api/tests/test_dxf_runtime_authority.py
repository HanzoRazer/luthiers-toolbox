"""
DXF-RUNTIME-AUTHORITY-001: manufacturing authority for governed catalog assets.

Owner ruling 2026-09-16: quarantine records describe known failure and never
grant manufacturing authority; authority is a separate positive assertion over
one asset and its exact bytes. These tests hold that line from both sides:

- nothing in the catalog may reach manufacturing without a positive
  authorization whose digest matches the file (fail-closed);
- an asset that is authorized, and unchanged, is allowed (so the contract is
  not vacuously satisfied by blocking everything);
- CI and runtime agree: every quarantine record resolves BLOCKED at runtime;
- a DXF outside the governed catalog keeps its own contract and is not judged
  here - uploads do not become blocked merely by having no record.
"""
import copy
import json
from pathlib import Path

import pytest

from app.ci import dxf_catalog_policy as policy
from app.ci import dxf_catalog_schema as schema
from app.instrument_geometry import dxf_authority as authority

pytestmark = pytest.mark.allow_missing_request_id

CATALOG_ROOT = authority.CATALOG_ROOT
LES_PAUL = CATALOG_ROOT / "body" / "dxf" / "electric" / "LesPaul_CAM_Closed.dxf"
BODY = "manufacturing_body"


@pytest.fixture(scope="module")
def registry():
    return policy.load_registry()


@pytest.fixture
def catalog(tmp_path, registry):
    """A governed catalog of one asset, with its own registry. Returns (root, registry_path, dxf)."""
    root = tmp_path / "catalog"
    folder = root / "body" / "dxf" / "electric"
    folder.mkdir(parents=True)
    dxf = folder / "x.dxf"
    dxf.write_bytes(b"0\nSECTION\n0\nENDSEC\n0\nEOF\n")
    reg = copy.deepcopy(registry)
    reg["quarantine"] = []
    reg["manufacturing_authority"] = {"basis": "test fixture", "authorized": []}
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(reg), encoding="utf-8")
    return root, path, dxf


def _authorize(registry_path, asset, digest, authority_value="ALLOWED"):
    reg = json.loads(registry_path.read_text(encoding="utf-8"))
    reg["manufacturing_authority"]["authorized"] = [
        {"asset": asset, "asset_sha256": digest, "authority": authority_value,
         "basis": "test fixture: adjudicated and authorized"}]
    registry_path.write_text(json.dumps(reg), encoding="utf-8")
    return reg


def _resolve(catalog, dxf=None):
    root, registry_path, asset = catalog
    return authority.resolve_manufacturing_authority(dxf or asset, registry_path, root)


# -----------------------------------------------------------------------------
# The positive case: authorization of exact bytes
# -----------------------------------------------------------------------------

def test_authorized_asset_with_matching_digest_is_allowed(catalog):
    root, registry_path, dxf = catalog
    _authorize(registry_path, "body/dxf/electric/x.dxf", authority.file_sha256(dxf))
    result = _resolve(catalog)
    assert (result.state, result.blocked, result.sha256_matches) == (authority.ALLOWED, False, True)
    assert result.asset_class == BODY
    authority.require_manufacturing_authority(dxf, registry_path, root)  # does not raise


def test_the_authorized_fixture_is_a_registry_the_real_schema_accepts(catalog):
    """T3 must not rely on a shape production could never hold."""
    root, registry_path, dxf = catalog
    reg = _authorize(registry_path, "body/dxf/electric/x.dxf", authority.file_sha256(dxf))
    schema.validate_registry(reg, policy.classify)  # raises RegistryError if the shape is invalid


# -----------------------------------------------------------------------------
# Fail-closed cases
# -----------------------------------------------------------------------------

def test_changed_bytes_are_not_the_authorized_bytes(catalog):
    root, registry_path, dxf = catalog
    _authorize(registry_path, "body/dxf/electric/x.dxf", authority.file_sha256(dxf))
    dxf.write_bytes(dxf.read_bytes() + b"; edited\n")
    result = _resolve(catalog)
    assert (result.state, result.sha256_matches) == (authority.BLOCKED, False)
    assert "authorized bytes" in result.reason


def test_no_authorization_blocks_even_with_no_quarantine_record(catalog):
    """Absence of a quarantine record is not authorization."""
    result = _resolve(catalog)
    assert result.state == authority.BLOCKED
    assert "no positive manufacturing authorization" in result.reason


def test_an_unclassified_catalog_file_is_blocked(catalog):
    root, registry_path, _ = catalog
    stray = root / "stray.dxf"
    stray.write_bytes(b"0\nEOF\n")
    result = authority.resolve_manufacturing_authority(stray, registry_path, root)
    assert result.state == authority.BLOCKED
    assert "not classified" in result.reason


def test_a_missing_asset_is_blocked(catalog):
    root, registry_path, dxf = catalog
    _authorize(registry_path, "body/dxf/electric/x.dxf", authority.file_sha256(dxf))
    dxf.unlink()
    result = _resolve(catalog)
    assert result.state == authority.BLOCKED


@pytest.mark.parametrize("content", ["{ not json", json.dumps({"schema": "x"})])
def test_a_malformed_registry_blocks_governed_manufacturing(catalog, content):
    root, registry_path, dxf = catalog
    registry_path.write_text(content, encoding="utf-8")
    result = authority.resolve_manufacturing_authority(dxf, registry_path, root)
    assert result.state == authority.BLOCKED
    assert "registry" in result.reason


def test_authority_other_than_allowed_does_not_grant_use(catalog):
    root, registry_path, dxf = catalog
    _authorize(registry_path, "body/dxf/electric/x.dxf", authority.file_sha256(dxf), "BLOCKED")
    assert _resolve(catalog).state == authority.BLOCKED


def test_require_raises_a_structured_domain_error(catalog):
    root, registry_path, dxf = catalog
    with pytest.raises(authority.ManufacturingAuthorityBlocked) as caught:
        authority.require_manufacturing_authority(dxf, registry_path, root)
    error = caught.value
    assert isinstance(error, ValueError)  # the CAM routers' 422 mapping covers it
    detail = error.as_detail()
    assert detail["code"] == "DXF_MANUFACTURING_AUTHORITY_BLOCKED"
    assert detail["asset"] == "body/dxf/electric/x.dxf"
    assert detail["manufacturing_authority"] == "BLOCKED"
    assert str(root) not in json.dumps(detail)  # no filesystem paths in the client payload


# -----------------------------------------------------------------------------
# Outside the governed catalog: someone else's contract
# -----------------------------------------------------------------------------

def test_a_dxf_outside_the_catalog_is_not_judged_here(tmp_path):
    upload = tmp_path / "user_upload.dxf"
    upload.write_bytes(b"0\nEOF\n")
    result = authority.resolve_manufacturing_authority(upload)
    assert (result.state, result.blocked, result.governed) == (authority.NOT_CATALOG, False, False)
    authority.require_manufacturing_authority(upload)  # does not raise


def test_traversal_out_of_the_catalog_is_not_a_catalog_asset(tmp_path, catalog):
    root, registry_path, _ = catalog
    outside = tmp_path / "outside.dxf"
    outside.write_bytes(b"0\nEOF\n")
    sneaky = root / "body" / ".." / ".." / "outside.dxf"
    assert authority.catalog_relative_path(sneaky, root) is None
    assert authority.resolve_manufacturing_authority(sneaky, registry_path, root).state == authority.NOT_CATALOG


# -----------------------------------------------------------------------------
# CI and runtime agree on the real catalog
# -----------------------------------------------------------------------------

def test_every_quarantine_record_blocks_at_runtime(registry):
    """CI says manufacturing_authority BLOCKED; runtime must say BLOCKED."""
    blocked = []
    for record in registry["quarantine"]:
        result = authority.resolve_manufacturing_authority(CATALOG_ROOT / record["asset"])
        if result.state != authority.BLOCKED:
            blocked.append((record["asset"], result.state))
    assert blocked == []


def test_no_catalog_asset_is_manufacturing_authorized_today(registry):
    """Nothing is authorized yet, so no governed asset may be manufactured from."""
    assert registry["manufacturing_authority"]["authorized"] == []
    allowed = [p.name for p in CATALOG_ROOT.rglob("*.dxf")
               if authority.resolve_manufacturing_authority(p).state == authority.ALLOWED]
    assert allowed == []


def test_a_passing_reference_trace_is_still_not_authorized_to_manufacture(registry):
    """export_ready is not manufacturing authority (T10)."""
    trace = next(p for p in (CATALOG_ROOT / "reference_dxf").rglob("*.dxf"))
    asset = authority.catalog_relative_path(trace)
    assert policy.classify(asset, registry) == "reference"
    assert policy.quarantine_record(asset, registry) is None  # it passes its catalog contract
    assert authority.resolve_manufacturing_authority(trace).state == authority.BLOCKED


def test_the_les_paul_template_is_blocked_while_unadjudicated(registry):
    """The principal regression witness of this order."""
    record = policy.quarantine_record("body/dxf/electric/LesPaul_CAM_Closed.dxf", registry)
    assert record["disposition"] == "UNADJUDICATED"
    result = authority.resolve_manufacturing_authority(LES_PAUL)
    assert result.state == authority.BLOCKED
    assert result.disposition == "UNADJUDICATED"
    assert result.exit_condition  # the record says what would clear it


# -----------------------------------------------------------------------------
# Schema: the authorization section cannot be abused
# -----------------------------------------------------------------------------

AUTHORIZED = {"asset": "body/dxf/electric/LesPaul_body.dxf", "asset_sha256": "a" * 64,
              "authority": "ALLOWED", "basis": "test"}
BREAKS = [
    ("quarantined asset authorized", lambda e: e, "cannot be authorized"),
    ("unknown asset", lambda e: {**e, "asset": "nowhere/x.dxf"}, "not classified"),
    ("bad digest", lambda e: {**e, "asset_sha256": "abc"}, "64 lowercase hex"),
    ("authority is a block", lambda e: {**e, "authority": "BLOCKED"}, "only grants authority"),
    ("missing basis", lambda e: {k: v for k, v in e.items() if k != "basis"}, "missing or empty"),
]


@pytest.mark.parametrize("name,mutate,expected", BREAKS, ids=[b[0] for b in BREAKS])
def test_malformed_authorization_is_rejected_at_load(registry, name, mutate, expected):
    reg = copy.deepcopy(registry)
    reg["manufacturing_authority"]["authorized"] = [mutate(AUTHORIZED)]
    with pytest.raises(schema.RegistryError, match=expected):
        schema.validate_registry(reg, policy.classify)


def test_the_section_is_required(registry):
    reg = copy.deepcopy(registry)
    reg.pop("manufacturing_authority")
    with pytest.raises(schema.RegistryError, match="manufacturing_authority"):
        schema.validate_registry(reg, policy.classify)


def test_duplicate_authorizations_are_rejected(registry):
    reg = copy.deepcopy(registry)
    entry = {**AUTHORIZED, "asset": "body/dxf/electric/Smart-Guitar-v1_front.dxf"}
    reg["quarantine"] = [r for r in reg["quarantine"] if r["asset"] != entry["asset"]]
    reg["manufacturing_authority"]["authorized"] = [entry, copy.deepcopy(entry)]
    with pytest.raises(schema.RegistryError, match="duplicate"):
        schema.validate_registry(reg, policy.classify)
