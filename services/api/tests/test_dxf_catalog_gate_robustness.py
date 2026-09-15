"""
DXF-CATALOG-GATE-001: robustness of the catalog gates (second review round).

Each test pins a defect a probe confirmed:
- building the manufacturing view used to destroy entities in the parsed
  document, so a registry that ordered closed_outline after preflight made it
  crash on them;
- a contract clause with no implementation used to be skipped as a pass;
- hashing an unreadable file used to crash the gate instead of failing it;
- (third round) a crash in a clause a quarantine record declares was reported
  QUARANTINED, so a broken check hid behind the record;
plus the CLI entry points end to end (exit code and the JSON report CI uploads).
"""
import copy
import json
import subprocess
import sys

import pytest

from app.ci import check_dxf_files
from app.ci import dxf_catalog_policy as policy
from tests.test_dxf_catalog_gate import (  # noqa: F401  (fixtures are used by name)
    BODY, ELLIPSE, REPO_ROOT, _lines, _record, _save, asset_gate, bare_registry, mini_catalog, registry,
)

pytestmark = pytest.mark.allow_missing_request_id

SELF_CROSSING_POINTS = [(0, 0), (50, 50), (50, 0), (0, 50), (0, 0)]


def _body_with_points_layer(folder):
    def build(m):
        m.add_lwpolyline(ELLIPSE, close=True, dxfattribs={"layer": "BODY_OUTLINE"})
        m.add_lwpolyline(SELF_CROSSING_POINTS, dxfattribs={"layer": "BODY_POINTS"})
    return _save(folder, "points", "R2000", build)


def test_clause_order_does_not_change_the_verdict(tmp_path, bare_registry):  # noqa: F811
    path = _body_with_points_layer(tmp_path)
    reordered = copy.deepcopy(bare_registry)
    contract = reordered["asset_classes"][BODY]["contract"]
    contract.remove("closed_outline")
    contract.append("closed_outline")  # after preflight/topology, which build the manufacturing view
    normal = check_dxf_files.validate_dxf_file(path, bare_registry, asset_class=BODY)
    late = check_dxf_files.validate_dxf_file(path, reordered, asset_class=BODY)
    assert normal["info"]["failed_clauses"] == late["info"]["failed_clauses"] == ["version_allowed"]
    assert not any("crashed" in line for line in late["errors"] + late["warnings"])


@pytest.mark.parametrize("gate", ["files", "assets"])
def test_unimplemented_contract_clause_fails_instead_of_passing(tmp_path, bare_registry, asset_gate, gate):  # noqa: F811
    bare_registry["asset_classes"][BODY]["contract"].append("typo_clause")
    path = _save(tmp_path, "body", "R12", lambda m: _lines(m, ELLIPSE))
    if gate == "files":
        result = check_dxf_files.validate_dxf_file(path, bare_registry, asset_class=BODY)
        status, text = result["status"], " ".join(result["errors"])
    else:
        result = asset_gate.validate_dxf_file(path, bare_registry, asset_class=BODY)
        status, text = result.status, " ".join(i.message for i in result.issues)
    assert status == "FAIL"
    assert "No implementation for contract clause 'typo_clause'" in text


def test_asset_gate_still_skips_clauses_owned_by_the_files_gate(tmp_path, bare_registry, asset_gate):  # noqa: F811
    path = _save(tmp_path, "body", "R12", lambda m: _lines(m, ELLIPSE))
    assert asset_gate.validate_dxf_file(path, bare_registry, asset_class=BODY).status == "PASS"


def test_unreadable_recorded_file_fails_without_crashing(mini_catalog, bare_registry, asset_gate):  # noqa: F811
    missing = mini_catalog / "body" / "dxf" / "electric" / "gone.dxf"
    bare_registry["quarantine"] = [_record("body/dxf/electric/gone.dxf", ["readable"], "a" * 64)]
    files = check_dxf_files.validate_dxf_file(missing, bare_registry)
    assets = asset_gate.validate_dxf_file(missing, bare_registry)
    assert (files["status"], assets.status) == ("FAIL", "FAIL")
    assert any("unreadable (FileNotFoundError)" in e for e in files["errors"])


def test_unrecorded_files_are_not_hashed(mini_catalog, bare_registry, monkeypatch):  # noqa: F811
    path = _save(mini_catalog / "body" / "dxf" / "electric", "x", "R12", lambda m: _lines(m, ELLIPSE))

    def refuse(_path):
        raise AssertionError("hashed a file that has no quarantine record")
    monkeypatch.setattr(policy, "file_sha256", refuse)
    assert check_dxf_files.validate_dxf_file(path, bare_registry)["status"] == "PASS"


def _crash(*args, **kwargs):
    raise RuntimeError("synthetic check bug")


def test_files_gate_does_not_quarantine_a_crash_in_a_recorded_clause(mini_catalog, bare_registry,  # noqa: F811
                                                                     monkeypatch):
    path = _save(mini_catalog / "body" / "dxf" / "electric", "x", "R12",
                 lambda m: m.add_polyline2d(ELLIPSE, close=True, dxfattribs={"layer": "GEOMETRY"}))
    bare_registry["quarantine"] = [
        _record("body/dxf/electric/x.dxf", ["preflight_valid"], policy.file_sha256(path))]
    assert check_dxf_files.validate_dxf_file(path, bare_registry)["status"] == "QUARANTINED"  # control
    monkeypatch.setattr(check_dxf_files, "DXFPreflight", _crash)
    result = check_dxf_files.validate_dxf_file(path, bare_registry)
    assert result["status"] == "FAIL"
    assert any("Checks for recorded clauses crashed: preflight_valid" in e for e in result["errors"])


def test_asset_gate_does_not_quarantine_a_crash_in_a_recorded_clause(mini_catalog, bare_registry,  # noqa: F811
                                                                     asset_gate, monkeypatch):  # noqa: F811
    path = _save(mini_catalog / "body" / "dxf" / "electric", "x", "R12", lambda m: _lines(m, ELLIPSE, closed=False))
    bare_registry["quarantine"] = [_record("body/dxf/electric/x.dxf", ["closed_outline"], policy.file_sha256(path))]
    assert asset_gate.validate_dxf_file(path, bare_registry).status == "QUARANTINED"  # control
    monkeypatch.setattr(asset_gate.policy, "check_closed_outline", _crash)
    result = asset_gate.validate_dxf_file(path, bare_registry)
    assert result.status == "FAIL"
    assert any("Checks for recorded clauses crashed: closed_outline" in i.message for i in result.issues)


def test_result_has_no_ambiguous_passed_field(tmp_path, bare_registry):  # noqa: F811
    path = _body_with_points_layer(tmp_path)
    result = check_dxf_files.validate_dxf_file(path, bare_registry, asset_class=BODY)
    assert "passed" not in result
    assert (result["blocks_gate"], result["export_ready"]) == (True, False)


# -----------------------------------------------------------------------------
# CLI entry points, end to end
# -----------------------------------------------------------------------------

def _run(args, cwd):
    return subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})


def test_files_gate_cli_exits_1_and_writes_the_report(tmp_path):
    folder = tmp_path / "scan"
    folder.mkdir()
    _save(folder, "stray", "R12", lambda m: _lines(m, ELLIPSE))
    report = tmp_path / "report.json"
    proc = _run(["-m", "app.ci.check_dxf_files", "--path", str(folder), "--report", str(report)],
                cwd=REPO_ROOT / "services" / "api")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    data = json.loads(report.read_text(encoding="utf-8"))
    assert (data["total"], data["failed"], data["registry_problems"]) == (1, 1, [])
    assert "RESULT: FAILED" in proc.stdout


def test_asset_gate_cli_exits_1_on_a_failing_file(tmp_path):
    folder = tmp_path / "scan"
    folder.mkdir()
    _save(folder, "stray", "R12", lambda m: _lines(m, ELLIPSE))
    proc = _run([str(REPO_ROOT / "scripts" / "validate_dxf_assets.py"), "--root", str(folder)], cwd=REPO_ROOT)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "FAILED" in proc.stdout
