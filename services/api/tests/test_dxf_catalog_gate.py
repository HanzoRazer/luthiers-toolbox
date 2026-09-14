"""
DXF-CATALOG-GATE-001: the declarative DXF catalog gates.

Owner rulings (2026-09-13/14) under test:
- the Files gate is an export-readiness gate: malformed witnesses still fail;
- asset class comes from folder + layer, declared in dxf_catalog_registry.json;
- BODY_POINTS is reference data; no other layer role is assumed;
- stored catalog DXFs are R12 only (R2000 is paid-tier vectorizer output);
- a quarantine record never passes a file and never hides an extra failure,
  and a record whose failure has healed is stale (the gate fails);
- every record carries the required fields, owner stream DXF Catalog
  Integrity, and manufacturing authority BLOCKED.
"""
import copy
import importlib.util
import io
import sys
from pathlib import Path

import pytest

from app.ci import check_dxf_files
from app.ci import dxf_catalog_policy as policy
from app.util.dxf_compat import create_document

pytestmark = pytest.mark.allow_missing_request_id

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_ROOT = REPO_ROOT / "services" / "api" / "app" / "instrument_geometry"
BODY = "manufacturing_body"
ELLIPSE = [(175.0 * __import__("math").cos(i * 0.0981748), 225.0 * __import__("math").sin(i * 0.0981748))
           for i in range(64)]  # 64-point body-sized ellipse, 350 x 450 mm


@pytest.fixture(scope="module")
def registry():
    return policy.load_registry()


@pytest.fixture
def bare_registry(registry):
    """The real classes and version policy, with no quarantine records."""
    reg = copy.deepcopy(registry)
    reg["quarantine"] = []
    return reg


@pytest.fixture(scope="module")
def asset_gate():
    path = REPO_ROOT / "scripts" / "validate_dxf_assets.py"
    spec = importlib.util.spec_from_file_location("validate_dxf_assets_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _save(tmp_path, name, version, build, crlf=False):
    doc = create_document(version=version)
    build(doc.modelspace())
    stream = io.StringIO()
    doc.write(stream)
    data = doc.encode(stream.getvalue()).replace(b"\r\n", b"\n")
    if crlf:
        data = data.replace(b"\n", b"\r\n")
    path = tmp_path / f"{name}.dxf"
    path.write_bytes(data)
    return path


def _lines(msp, pts, closed=True, layer="BODY_OUTLINE"):
    ends = pts[1:] + (pts[:1] if closed else [])
    for start, end in zip(pts, ends):
        msp.add_line(start, end, dxfattribs={"layer": layer})


def _files(path, registry, klass=BODY):
    return check_dxf_files.validate_dxf_file(path, registry, asset_class=klass)


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
# closed_outline
# -----------------------------------------------------------------------------

def _outline(path, registry):
    import ezdxf

    doc = ezdxf.readfile(str(path))
    return policy.check_closed_outline(list(doc.modelspace()), registry["asset_classes"][BODY]).failure


def test_closed_r12_line_chain_is_a_closed_outline(tmp_path, registry):
    path = _save(tmp_path, "loop", "R12", lambda m: _lines(m, ELLIPSE))
    assert _outline(path, registry) is None


def test_dangling_mark_does_not_break_a_closed_chain(tmp_path, registry):
    path = _save(tmp_path, "dangle", "R12",
                 lambda m: (_lines(m, ELLIPSE), m.add_line((0, 225), (0, 240), dxfattribs={"layer": "BODY_OUTLINE"})))
    assert _outline(path, registry) is None


@pytest.mark.parametrize("name,build", [
    ("open_chain", lambda m: _lines(m, ELLIPSE, closed=False)),
    ("gap_0p5mm", lambda m: (_lines(m, ELLIPSE, closed=False),
                             m.add_line(ELLIPSE[-1], (ELLIPSE[0][0], ELLIPSE[0][1] + 0.5),
                                        dxfattribs={"layer": "BODY_OUTLINE"}))),
    ("circle_only", lambda m: m.add_circle((0, 0), 3.0, dxfattribs={"layer": "BODY_OUTLINE"})),
    ("line_drawn_twice", lambda m: [m.add_line((-175, -225), (175, 225), dxfattribs={"layer": "BODY_OUTLINE"})
                                    for _ in range(2)]),
    ("no_outline_layer", lambda m: _lines(m, ELLIPSE, layer="0")),
    ("strip_not_body", lambda m: (_lines(m, [(-175, 0), (175, 0), (175, 20), (-175, 20)]),
                                  _lines(m, ELLIPSE, closed=False))),
])
def test_malformed_outlines_fail_closed_outline(tmp_path, registry, name, build):
    path = _save(tmp_path, name, "R12", build)
    assert _outline(path, registry), name


# -----------------------------------------------------------------------------
# Files gate: export readiness
# -----------------------------------------------------------------------------

def test_clean_r12_line_body_passes_the_files_gate(tmp_path, bare_registry):
    result = _files(_save(tmp_path, "body", "R12", lambda m: _lines(m, ELLIPSE)), bare_registry)
    assert result["status"] == "PASS", result["errors"]


@pytest.mark.parametrize("version", ["R2000", "R2010"])
def test_non_r12_catalog_file_fails_version(tmp_path, bare_registry, version):
    path = _save(tmp_path, f"v{version}", version,
                 lambda m: m.add_lwpolyline(ELLIPSE, close=True, dxfattribs={"layer": "BODY_OUTLINE"}))
    result = _files(path, bare_registry)
    assert result["status"] == "FAIL"
    assert result["info"]["failed_clauses"] == ["version_allowed"]


@pytest.mark.parametrize("crlf", [False, True])
def test_self_intersecting_outline_fails_topology(tmp_path, bare_registry, crlf):
    fig8 = [(0, 0), (200, 300), (200, 0), (0, 100)]
    path = _save(tmp_path, "fig8", "R2000",
                 lambda m: m.add_lwpolyline(fig8, close=True, dxfattribs={"layer": "BODY_OUTLINE"}), crlf=crlf)
    assert "topology_valid" in _files(path, bare_registry)["info"]["failed_clauses"]


def test_crossing_line_chain_outline_fails_topology(tmp_path, bare_registry):
    bowtie = [(-175, -225), (175, 225), (175, -225), (-175, 225)]
    result = _files(_save(tmp_path, "bowtie", "R12", lambda m: _lines(m, bowtie)), bare_registry)
    assert result["info"]["failed_clauses"] == ["topology_valid"]


def test_open_lwpolyline_outline_fails_outline_and_preflight(tmp_path, bare_registry):
    path = _save(tmp_path, "open", "R2000",
                 lambda m: m.add_lwpolyline(ELLIPSE, close=False, dxfattribs={"layer": "BODY_OUTLINE"}))
    failed = _files(path, bare_registry)["info"]["failed_clauses"]
    assert {"closed_outline", "preflight_valid"} <= set(failed)


def test_body_points_reference_layer_is_exempt(tmp_path, bare_registry):
    def build(m):
        m.add_lwpolyline(ELLIPSE, close=True, dxfattribs={"layer": "BODY_OUTLINE"})
        m.add_lwpolyline([(0, 0), (50, 50), (50, 0), (0, 50), (0, 0)], dxfattribs={"layer": "BODY_POINTS"})
    result = _files(_save(tmp_path, "points", "R2000", build), bare_registry)
    assert result["info"]["failed_clauses"] == ["version_allowed"]  # only the R2000 storage


def test_same_open_self_crossing_polyline_on_an_undeclared_layer_fails(tmp_path, bare_registry):
    def build(m):
        m.add_lwpolyline(ELLIPSE, close=True, dxfattribs={"layer": "BODY_OUTLINE"})
        m.add_lwpolyline([(0, 0), (50, 50), (50, 0), (0, 50), (0, 0)], dxfattribs={"layer": "WIRING_CHANNEL"})
    failed = _files(_save(tmp_path, "wiring", "R2000", build), bare_registry)["info"]["failed_clauses"]
    assert {"preflight_valid", "topology_valid"} <= set(failed)


def test_r12_polyline_body_fails_runtime_preflight(tmp_path, bare_registry):
    path = _save(tmp_path, "poly", "R12",
                 lambda m: m.add_polyline2d(ELLIPSE, close=True, dxfattribs={"layer": "GEOMETRY"}))
    assert _files(path, bare_registry)["info"]["failed_clauses"] == ["preflight_valid"]


@pytest.mark.parametrize("name,build,clause", [
    ("empty", lambda m: None, "nonempty"),
    ("text_only", lambda m: m.add_text("BODY"), "geometry_present"),
])
def test_empty_and_text_only_files_fail(tmp_path, bare_registry, name, build, clause):
    result = _files(_save(tmp_path, name, "R12", build), bare_registry)
    assert result["status"] == "FAIL"
    assert result["info"]["failed_clauses"] == [clause]


def test_reference_class_makes_no_outline_assertion(tmp_path, bare_registry):
    path = _save(tmp_path, "trace", "R12", lambda m: _lines(m, ELLIPSE, closed=False, layer="0"))
    assert _files(path, bare_registry, klass="reference")["status"] == "PASS"


def test_file_outside_the_catalog_is_unclassified(tmp_path, bare_registry):
    path = _save(tmp_path, "stray", "R12", lambda m: _lines(m, ELLIPSE))
    result = check_dxf_files.validate_dxf_file(path, bare_registry)
    assert result["status"] == "FAIL"
    assert any("Unclassified" in line for line in result["errors"])


# -----------------------------------------------------------------------------
# Quarantine semantics
# -----------------------------------------------------------------------------

def _record(asset, failed):
    return {"asset": asset, "asset_class": BODY, "failed_contract": failed, "observed_evidence": ["test"],
            "disposition": "QUARANTINE_CANDIDATE", "reason": "test", "owner_stream": "DXF Catalog Integrity",
            "manufacturing_authority": "BLOCKED", "exit_condition": "test"}


def test_failures_within_the_record_are_quarantined_not_passed(bare_registry):
    bare_registry["quarantine"] = [_record("a.dxf", ["version_allowed", "topology_valid"])]
    verdict = policy.judge("a.dxf", BODY, {"version_allowed": ["x"], "topology_valid": ["y"]},
                           {"version_allowed", "topology_valid"}, bare_registry)
    assert verdict.status == "QUARANTINED"
    assert not verdict.blocks_gate
    assert any("BLOCKED" in m for m in verdict.messages)


def test_a_failure_outside_the_record_fails_the_gate(bare_registry):
    bare_registry["quarantine"] = [_record("a.dxf", ["version_allowed"])]
    verdict = policy.judge("a.dxf", BODY, {"version_allowed": ["x"], "topology_valid": ["new"]},
                           {"version_allowed", "topology_valid"}, bare_registry)
    assert verdict.status == "FAIL"


def test_a_healed_clause_makes_the_record_stale(bare_registry):
    bare_registry["quarantine"] = [_record("a.dxf", ["version_allowed", "topology_valid"])]
    verdict = policy.judge("a.dxf", BODY, {"version_allowed": ["x"]},
                           {"version_allowed", "topology_valid"}, bare_registry)
    assert verdict.status == "FAIL"
    assert any("now pass" in m for m in verdict.messages)


def test_clauses_a_gate_does_not_evaluate_are_not_stale(bare_registry):
    bare_registry["quarantine"] = [_record("a.dxf", ["preflight_valid"])]
    verdict = policy.judge("a.dxf", BODY, {}, {"version_allowed", "closed_outline"}, bare_registry)
    assert verdict.status == "QUARANTINED"


# -----------------------------------------------------------------------------
# Asset gate uses the same policy
# -----------------------------------------------------------------------------

def test_asset_gate_accepts_r12_line_body(tmp_path, bare_registry, asset_gate):
    path = _save(tmp_path, "body", "R12", lambda m: _lines(m, ELLIPSE))
    assert asset_gate.validate_dxf_file(path, bare_registry, asset_class=BODY).status == "PASS"


@pytest.mark.parametrize("name,version,build,clause", [
    ("circle_only", "R12", lambda m: m.add_circle((0, 0), 3.0, dxfattribs={"layer": "BODY_OUTLINE"}),
     "closed_outline"),
    ("open_chain", "R12", lambda m: _lines(m, ELLIPSE, closed=False), "closed_outline"),
    ("r2000", "R2000", lambda m: m.add_lwpolyline(ELLIPSE, close=True, dxfattribs={"layer": "BODY_OUTLINE"}),
     "version_allowed"),
])
def test_asset_gate_rejects_malformed_witnesses(tmp_path, bare_registry, asset_gate, name, version, build, clause):
    result = asset_gate.validate_dxf_file(_save(tmp_path, name, version, build), bare_registry, asset_class=BODY)
    assert result.status == "FAIL"
    assert clause in {i.category for i in result.issues}
