"""SHOP-OPERATING-LOOP-RECOVERY-001: integrity of the committed audit package.

The committed ledger, maps and recommendation must pass every rule in
``scripts/investigations/shop_operating_loop_ledger.py``, and the JSON ledger
must regenerate byte for byte from the CSV. Where the Git objects are present,
every luthiers-toolbox content digest is recomputed.

The fixture package pins the rules on the eight cases the order names: a live
routed feature, disconnected complete code, an archive-only source, a
concept-only item, two same-named nonidentical artifacts, an unresolved
cross-repository ID link, a missing capability, and an authority-boundary
conflict. Each mutation must produce its rule's message; none may pass silently.

Pure offline text analysis; no application import. Runtime is dominated by the
repository's API-test setup, so related cases share one test.
"""
from __future__ import annotations

import copy
import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.allow_missing_request_id

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / "docs" / "investigations" / "shop-operating-loop-recovery_2026-10-26"
TOOL = REPO_ROOT / "scripts" / "investigations" / "shop_operating_loop_ledger.py"
D1, D2 = "1" * 40, "2" * 40


def _tool():
    spec = importlib.util.spec_from_file_location("shop_operating_loop_ledger", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules["shop_operating_loop_ledger"] = module
    spec.loader.exec_module(module)
    return module


def _row(cid: str, track: str, **kw) -> dict:
    base = dict(
        candidate_id=cid, capability_track=track, repo="luthiers-toolbox", path_or_ref=f"src/{cid}.py",
        artifact_type="code:api", source_revision="0" * 40, content_digest=D1, provenance="fixture tree",
        reachability="LIVE_ROUTED", reachability_evidence="app/manifest.py:12 registers it",
        completeness="PARTIAL", authority="NONE", current_owner="fixture", overlap_or_successor="none",
        disposition="REFERENCE_ONLY", disposition_basis="fixture evidence basis, long enough",
        mvs_step="S1", open_question="none",
    )
    base.update(kw)
    return base


def _fixture_rows() -> list[dict]:
    return [
        # live routed feature, canonical CAM owner of S6
        _row("SOL-A01", "A_JOB_IDENTITY", completeness="COMPLETE", authority="CAM",
             disposition="RETAIN_CANONICAL", mvs_step="S6"),
        # disconnected but complete code
        _row("SOL-B01", "B_ESTIMATE_ACTUAL", reachability="BUILT_DISCONNECTED",
             reachability_evidence="no importer (grep x = 0)", completeness="COMPLETE", disposition="RECONNECT"),
        # archive-only source
        _row("SOL-C01", "C_KITS", reachability="ARCHIVED_RECOVERABLE", content_digest=D2,
             reachability_evidence="deleted in abc123", provenance="pre-rewrite tag v0"),
        # concept-only backlog item
        _row("SOL-D01", "D_TIME_CAPTURE", artifact_type="doc:plan", reachability="CONCEPT_ONLY",
             reachability_evidence="concept document", completeness="NOT_APPLICABLE"),
        # two same-named, nonidentical artifacts
        _row("SOL-D02", "D_TIME_CAPTURE", path_or_ref="a/models.py", content_digest=D1),
        _row("SOL-D03", "D_TIME_CAPTURE", path_or_ref="b/models.py", content_digest=D2,
             overlap_or_successor=f"same-name-different-content:a/models.py@{D1}"),
        # missing capability
        _row("SOL-E01", "E_GUIDED_WORKFLOW", artifact_type="missing", reachability="MISSING",
             reachability_evidence="grep traveler = 0", content_digest="none:missing",
             completeness="NOT_APPLICABLE", disposition="MISSING_BUILD"),
        # authority-boundary conflict held open by an owner ruling
        _row("SOL-B02", "B_ESTIMATE_ACTUAL", authority="COMMERCIAL", disposition="RETAIN_CANONICAL",
             mvs_step="S3", repo="CNC-Production-Shop"),
        _row("SOL-B03", "B_ESTIMATE_ACTUAL", authority="COMMERCIAL", disposition="OWNER_RULING_REQUIRED",
             mvs_step="S3"),
    ]


ID_MAP = (
    "| From | To | Status | Evidence |\n|---|---|---|---|\n"
    "| project | run | PROVEN | stored: run_id at app/schemas.py:613 |\n"
    "| project | external job | UNKNOWN | no field either side |\n"
)


def _mvs(statuses: dict | None = None) -> str:
    statuses = statuses or {}
    lines = ["| Step | Name | Status | Artifact | Basis |", "|---|---|---|---|---|"]
    for i in range(1, 10):
        step = f"S{i}"
        status, artifact = statuses.get(step, ("BUILD", "SOL-E01"))
        lines.append(f"| {step} | step {i} | {status} | {artifact} | fixture |")
    return "\n".join(lines) + "\n"


def _write(pkg: Path, tool, rows, id_map=ID_MAP, mvs=None, rec="RECOMMENDED_INCREMENT: one thing\n",
           changed=None, json_override=None) -> Path:
    pkg.mkdir(parents=True, exist_ok=True)
    with (pkg / "CAPABILITY_LEDGER.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=tool.FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (pkg / "CAPABILITY_LEDGER.json").write_text(
        json_override if json_override is not None else tool.build_json(rows), encoding="utf-8", newline="\n")
    (pkg / "JOB_IDENTITY_MAP.md").write_text(id_map, encoding="utf-8")
    (pkg / "MVS_GAP_MATRIX.md").write_text(mvs if mvs is not None else _mvs(), encoding="utf-8")
    (pkg / "RECOMMENDATION.md").write_text(rec, encoding="utf-8")
    paths = changed if changed is not None else [tool.PACKAGE_PREFIX + "README.md"]
    (pkg / "evidence.json").write_text(json.dumps({"changed_paths": paths}), encoding="utf-8")
    return pkg


def test_committed_package_passes_and_digests_reproduce():
    tool = _tool()
    assert tool.validate_package(PKG) == []
    rows = tool.read_csv(PKG / "CAPABILITY_LEDGER.csv")
    digest_errors, _checked = tool.verify_digests(rows, REPO_ROOT)
    assert digest_errors == []

    evidence = json.loads((PKG / "evidence.json").read_text(encoding="utf-8"))
    counts = evidence["counts"]
    assert counts["rows"] == len(rows)
    for track in tool.TRACKS:
        assert counts["by_track"][track] == sum(r["capability_track"] == track for r in rows)
    for value in tool.DISPOSITION:
        assert counts["by_disposition"].get(value, 0) == sum(r["disposition"] == value for r in rows)
    assert set(evidence["changed_paths"]) >= {
        "scripts/investigations/shop_operating_loop_ledger.py",
        "services/api/tests/test_shop_operating_loop_recovery_evidence.py",
    }


def test_committed_package_is_internally_final():
    """Every owner ruling is recorded and no ledger row still awaits one."""
    tool = _tool()
    rows = tool.read_csv(PKG / "CAPABILITY_LEDGER.csv")
    evidence = json.loads((PKG / "evidence.json").read_text(encoding="utf-8"))
    assert [r["candidate_id"] for r in rows if r["disposition"] == "OWNER_RULING_REQUIRED"] == []
    rulings = (PKG / "OWNER_RULINGS.md").read_text(encoding="utf-8")
    ruled = {m for m in (f"R{i}" for i in range(1, 8)) if f"## {m} " in rulings and "(RULED" in
             rulings.split(f"## {m} ", 1)[1].splitlines()[0]}
    assert ruled == {f"R{i}" for i in range(1, 8)}
    assert set(evidence["counts"]["owner_rulings"]["ruled"]) == ruled
    assert evidence["counts"]["owner_rulings"]["open"] == []


def test_fixture_package_covers_the_eight_named_cases(tmp_path):
    tool = _tool()
    pkg = _write(tmp_path / "ok", tool, _fixture_rows())
    assert tool.validate_package(pkg) == []
    rows = {r["candidate_id"]: r for r in _fixture_rows()}
    assert rows["SOL-A01"]["reachability"] == "LIVE_ROUTED"
    assert rows["SOL-B01"]["reachability"] == "BUILT_DISCONNECTED" and rows["SOL-B01"]["completeness"] == "COMPLETE"
    assert rows["SOL-C01"]["reachability"] == "ARCHIVED_RECOVERABLE"
    assert rows["SOL-D01"]["reachability"] == "CONCEPT_ONLY"
    assert rows["SOL-D02"]["content_digest"] != rows["SOL-D03"]["content_digest"]
    assert "| UNKNOWN |" in ID_MAP
    assert rows["SOL-E01"]["reachability"] == "MISSING"
    assert {rows["SOL-B02"]["disposition"], rows["SOL-B03"]["disposition"]} == {
        "RETAIN_CANONICAL", "OWNER_RULING_REQUIRED"}


def _mutate(rows, cid, **kw):
    out = copy.deepcopy(rows)
    for r in out:
        if r["candidate_id"] == cid:
            r.update(kw)
    return out


def test_every_rule_fires_on_its_violation(tmp_path):
    tool = _tool()
    base = _fixture_rows()
    cases = {
        "duplicate candidate_id": dict(rows=base + [copy.deepcopy(base[0])]),
        "blank field": dict(rows=_mutate(base, "SOL-A01", provenance="")),
        "no file:line reachability": dict(rows=_mutate(base, "SOL-A01", reachability_evidence="it is routed")),
        "needs provenance and a 40-hex": dict(rows=_mutate(base, "SOL-C01", content_digest="none:missing")),
        "COMPLETE cites only a concept": dict(rows=_mutate(base, "SOL-D01", completeness="COMPLETE")),
        "not an evidence basis": dict(rows=_mutate(base, "SOL-B01", disposition_basis="trust me")),
        "row claims CAM authority": dict(rows=_mutate(base, "SOL-D01", authority="CAM")),
        "without equal content digest": dict(rows=_mutate(base, "SOL-D03", overlap_or_successor="duplicate:SOL-D02")),
        "digests are equal": dict(rows=_mutate(base, "SOL-D03", content_digest=D1)),
        "both canonical COMMERCIAL owners": dict(rows=_mutate(base, "SOL-B03", disposition="RETAIN_CANONICAL")),
        "neither a candidate nor a MISSING row": dict(
            rows=[r for r in base if r["capability_track"] != "E_GUIDED_WORKFLOW"]),
        "PROVEN without a stored field": dict(
            rows=base, id_map=ID_MAP.replace("| UNKNOWN | no field", "| PROVEN | same name")),
        "missing from MVS_GAP_MATRIX": dict(rows=base, mvs=_mvs().replace("| S9 |", "| S10 |")),
        "not AVAILABLE/ADAPT/BUILD/BLOCKED": dict(rows=base, mvs=_mvs({"S2": ("MAYBE", "SOL-E01")})),
        "AVAILABLE without a RETAIN_CANONICAL": dict(rows=base, mvs=_mvs({"S2": ("AVAILABLE", "SOL-B01")})),
        "disagrees with CAPABILITY_LEDGER.csv": dict(rows=base, json_override="{}\n"),
        "names 2 increments": dict(rows=base, rec="RECOMMENDED_INCREMENT: a\nRECOMMENDED_INCREMENT: b\n"),
        "outside the evidence-only scope": dict(rows=base, changed=["services/api/app/main.py"]),
    }
    misses = []
    for i, (expected, kw) in enumerate(cases.items()):
        pkg = _write(tmp_path / f"case{i}", tool, **kw)
        errors = tool.validate_package(pkg)
        if not any(expected in e for e in errors):
            misses.append((expected, errors))
    assert misses == []

    # the AVAILABLE rule accepts a real canonical owner
    ok = _write(tmp_path / "available", tool, base, mvs=_mvs({"S6": ("AVAILABLE", "SOL-A01")}))
    assert tool.validate_package(ok) == []
