"""March 2026 consolidation recovery census: integrity of the committed dataset.

The census itself (``BUNDLE_CENSUS.json``) cannot be rebuilt in CI: its inputs are
external bundles. Everything derived from it can, and is checked here: the ledger,
inventory and planning CSVs regenerate byte for byte, every manual override is
explained and reviewed exactly once, and the safety candidate is recorded once.

The fixture tests pin the inference rules that decide a row's class: identical
content at two paths, a rename, a deleted blob, a partial or same-name-different
content match, an ambiguous name, a missing bundle, and malformed overrides.
Ambiguity must come out ``UNRESOLVED``, never as a recovery claim.

Pure offline text analysis plus scratch Git repositories; no application import.
Runtime is dominated by the repository's API-test setup, so related cases share
one test.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.allow_missing_request_id

REPO_ROOT = Path(__file__).resolve().parents[3]
CENSUS = REPO_ROOT / "docs" / "investigations" / "march-2026-consolidation-recovery-census"
TOOLS = REPO_ROOT / "scripts" / "investigations"
LEDGER_TOOL = TOOLS / "march_2026_census_ledger.py"
ALLOWED_DISPOSITIONS = {
    "LIVE_INTEGRATED", "LIVE_MODIFIED", "PARTIALLY_INTEGRATED", "ARCHIVED_COMPLETE",
    "ARCHIVED_INCOMPLETE", "EXTERNAL_ONLY", "LOST_REFERENCE_ONLY", "SUPERSEDED",
    "RECOVERED_FEATURE_CANDIDATE", "RECOVERED_SAFETY_FIX_CANDIDATE", "DUPLICATE", "UNRESOLVED",
}
PROOF_CLASSES = {"MECHANICALLY_VERIFIED", "HEURISTIC_CANDIDATE", "MANUALLY_ADJUDICATED",
                 "SOURCE_UNAVAILABLE", "UNRESOLVED"}
_NEGATION = re.compile(r"\b(not|no|nothing|never|none)\b|n't\b", re.IGNORECASE)
_REVIEWER = re.compile(r"PENDING|(OWNER RULED|ACCEPTED|REJECTED) \d{4}-\d{2}-\d{2}")


def _csv(name: str) -> list[dict]:
    with (CENSUS / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _overrides() -> dict:
    return json.loads((CENSUS / "LEDGER_OVERRIDES.json").read_text(encoding="utf-8"))


def _tool(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # @dataclass resolves its module through sys.modules
    spec.loader.exec_module(module)
    return module


def _run_ledger(census: Path, overrides: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", str(LEDGER_TOOL), "--census", str(census), "--overrides", str(overrides),
         "--out", str(out / "ledger.csv"), "--out-inventory", str(out / "inventory.csv"),
         "--reachability", str(CENSUS / "MARCH_CLAIM_REACHABILITY.csv"),
         "--out-planning", str(out / "planning.csv")],
        capture_output=True, text=True,
    )


def _review_rows() -> dict[str, list[list[str]]]:
    """OVERRIDE_REVIEW.md table rows keyed by the ledger's override_id."""
    rows: dict[str, list[list[str]]] = {}
    section = ""
    for line in (CENSUS / "OVERRIDE_REVIEW.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = re.search(r"`(\w+)`", line).group(1) if "`" in line else ""
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.startswith("| `") or section not in ("by_blob", "by_name", "reference_only"):
            continue
        rows.setdefault(f"{section}:{cells[0].strip('`')}", []).append(cells)
    return rows


def _member(**kw) -> dict:
    base = {"source_id": "S1", "member": "x.py", "blob_lf": "0" * 40, "state": "HISTORY_ONLY",
            "name_only_matches_on_ref": [], "sha256": "", "first_commit": "", "first_date": "",
            "first_path": "", "live_paths": [], "archive_paths": []}
    return base | kw


def _ledger(tmp_path: Path, members: list[dict], overrides: dict | str) -> tuple[subprocess.CompletedProcess, dict]:
    sources = sorted({m["source_id"] for m in members})
    census = {"sources": [{"source_id": s, "path": f"{s}.zip", "kind": "zip", "sha256": "", "top_level": [],
                           "nested_archives": [], "skipped_snapshots": []} for s in sources], "members": members}
    (tmp_path / "c.json").write_text(json.dumps(census), encoding="utf-8")
    text = overrides if isinstance(overrides, str) else json.dumps(
        {"exclude": [], "reference_only": [], "by_blob": {}, "by_name": {}} | overrides)
    (tmp_path / "o.json").write_text(text, encoding="utf-8")
    run = _run_ledger(tmp_path / "c.json", tmp_path / "o.json", tmp_path)
    rows = {}
    if run.returncode == 0:
        with (tmp_path / "ledger.csv").open(encoding="utf-8", newline="") as fh:
            rows = {r["original_path"]: r for r in csv.DictReader(fh)}
    return run, rows


# -- the committed dataset ---------------------------------------------------

def test_ledger_values_and_overrides_are_well_formed():
    ledger = _csv("RECOVERY_LEDGER.csv")
    bad = {r["candidate_id"]: r["disposition"] for r in ledger if r["disposition"] not in ALLOWED_DISPOSITIONS}
    assert bad == {}, f"dispositions outside the allowed set: {bad}"
    unclassed = {r["candidate_id"]: r["proof_class"] for r in ledger if r["proof_class"] not in PROOF_CLASSES}
    assert unclassed == {}, f"rows without a proof class: {unclassed}"
    # A row decided by a name or a ruling must never read as mechanically verified.
    promoted = [r["candidate_id"] for r in ledger if r["proof_class"] == "MECHANICALLY_VERIFIED"
                and (r["override_id"] or r["census_state"] == "HISTORY_ONLY")]
    assert promoted == [], f"inferred or ruled rows labelled MECHANICALLY_VERIFIED: {promoted}"
    for name in ("MARCH_CLAIM_REACHABILITY.csv", "PLANNING_RECONCILIATION.csv"):
        rows = _csv(name)
        status = "classification" if "classification" in rows[0] else "current_status"
        wrong = [r[list(r)[0]] for r in rows if r[status] in ("VERIFIED_STRUCTURAL", "PARTIAL_MIGRATION",
                 "STRANDED_IMPLEMENTATION") and r["proof_class"] != "HEURISTIC_CANDIDATE"]
        assert wrong == [], f"{name}: reachability labels not marked heuristic: {wrong}"

    ov = _overrides()
    unexplained = [k for k, o in (ov["by_name"] | ov["by_blob"]).items() if len(o.get("reason", "")) < 20]
    unexplained += [r["candidate_id"] for r in ov["reference_only"] if len(r.get("disposition_reason", "")) < 5]
    assert unexplained == [], f"overrides without a stated reason: {unexplained}"
    assert ov["exclude_reason"], "an exclusion without a reason hides evidence"


def test_every_manual_override_has_exactly_one_matching_review_row():
    """OVERRIDE_REVIEW.md is the human review surface; it must agree with what the tool did."""
    review = _review_rows()
    ledger = {r["override_id"]: r for r in _csv("RECOVERY_LEDGER.csv") if r["override_id"]}
    ov = _overrides()
    applied = {*(f"by_name:{k}" for k in ov["by_name"]), *(f"by_blob:{k[:8]}" for k in ov["by_blob"]),
               *(f"reference_only:{r['candidate_id']}" for r in ov["reference_only"])}
    assert set(ledger) == applied, f"overrides not applied exactly once: {sorted(applied ^ set(ledger))}"
    assert set(review) == applied, (f"review rows without an override: {sorted(set(review) - applied)}; "
                                    f"overrides without a review row: {sorted(applied - set(review))}")
    duplicated = sorted(k for k, rows in review.items() if len(rows) != 1)
    assert duplicated == [], f"overrides reviewed more than once: {duplicated}"
    for oid, [cells] in review.items():
        row = ledger[oid]
        assert _REVIEWER.fullmatch(cells[-1]), f"{oid}: reviewer disposition {cells[-1]!r}"
        if oid.startswith("reference_only:"):
            assert cells[1] == row["disposition"], f"{oid}: review says {cells[1]}, ledger {row['disposition']}"
            continue
        assert row["candidate_id"] in cells[1], f"{oid}: review row names a different candidate"
        auto, final = (c.strip() for c in cells[2].split("→"))
        assert (auto, final) == (row["automatic_disposition"], row["disposition"]), (
            f"{oid}: review says {auto} -> {final}, tool gives "
            f"{row['automatic_disposition']} -> {row['disposition']}")
        assert ("yes" in cells[3]) == (auto != final), f"{oid}: 'changes the answer' is wrong"
    for pattern in ov["exclude"]:
        assert f"`{pattern}`" in (CENSUS / "OVERRIDE_REVIEW.md").read_text(encoding="utf-8")


def test_inventory_agrees_with_the_raw_census():
    census = json.loads((CENSUS / "BUNDLE_CENSUS.json").read_text(encoding="utf-8"))
    inventory = _csv("SOURCE_BUNDLE_INVENTORY.csv")
    assert [r["source_id"] for r in inventory] == [s["source_id"] for s in census["sources"]]
    for row in inventory:
        total = int(row["members"]) + int(row["excluded_third_party"])
        actual = sum(1 for m in census["members"] if m["source_id"] == row["source_id"])
        assert total == actual, f"{row['source_id']}: inventory {total} != census {actual}"


def test_the_derived_csvs_regenerate_byte_for_byte(tmp_path):
    run = _run_ledger(CENSUS / "BUNDLE_CENSUS.json", CENSUS / "LEDGER_OVERRIDES.json", tmp_path)
    assert run.returncode == 0, run.stderr
    for out, committed in (("ledger", "RECOVERY_LEDGER.csv"), ("inventory", "SOURCE_BUNDLE_INVENTORY.csv"),
                           ("planning", "PLANNING_RECONCILIATION.csv")):
        expected = (CENSUS / committed).read_bytes().replace(b"\r\n", b"\n")
        assert (tmp_path / f"{out}.csv").read_bytes() == expected, f"{committed} does not regenerate"


def test_the_safety_candidate_is_recorded_once_and_contained():
    """The live headstock route descends from blob 8e436e7b, not the B17S sibling draft.

    #441 contained the route (409 before generation); the generator defect is not fixed.
    """
    flagged = [r for r in _csv("RECOVERY_LEDGER.csv") if "SAFETY CANDIDATE" in r["safety_relevance"]]
    assert [r["content_blob_lf"][:8] for r in flagged] == ["8e436e7b"]
    assert flagged[0]["filename"] == "headstock_transition_export.py"
    assert flagged[0]["follow_up_order"] == "HEADSTOCK-TRANSITION-GCODE-SAFETY-001"
    assert flagged[0]["safety_relevance"].startswith("CONTAINED SAFETY CANDIDATE")
    assert "UNRESOLVED" in flagged[0]["safety_relevance"]


def test_census_documents_keep_the_owner_rulings():
    """CL-RED was a July typo for CI-RED (owner, 2026-10-14); no collision record exists for the window."""
    misuse, collision = [], []
    for path in sorted(CENSUS.rglob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            where = f"{path.name}:{number}"
            if "CL-RED" in line and not re.search(r"typo|\bnot\b|erratum", line, re.IGNORECASE):
                misuse.append(where)
            if re.search(r"namespace[- ]collision", line, re.IGNORECASE) and not _NEGATION.search(line):
                collision.append(where)
    assert misuse == [], f"CL-RED used as a recovery object: {misuse}"
    assert collision == [], f"loss attributed to a namespace collision: {collision}"


# -- the inference rules, on fixtures ----------------------------------------

def test_ledger_rules_on_fixtures(tmp_path):
    same = "1" * 40
    members = [
        # identical content at two paths in two bundles -> one row listing both
        _member(source_id="S1", member="a/dup.py", blob_lf=same, state="LIVE_IDENTICAL", live_paths=["app/dup.py"]),
        _member(source_id="S2", member="b/dup_copy.py", blob_lf=same, state="LIVE_IDENTICAL", live_paths=["app/dup.py"]),
        # first-commit path still live with other content -> heuristic, by path lineage
        _member(member="lineage.py", blob_lf="2" * 40, first_path="app/lineage.py",
                name_only_matches_on_ref=["app/lineage.py", "other/lineage.py"]),
        # one same-name live file, first path gone -> heuristic, by name
        _member(member="named.py", blob_lf="3" * 40, first_path="old/named.py",
                name_only_matches_on_ref=["app/named.py"]),
        # two same-name live files, first path gone -> ambiguous, never guessed
        _member(member="twin.py", blob_lf="4" * 40, first_path="old/twin.py",
                name_only_matches_on_ref=["app/a/twin.py", "app/b/twin.py"]),
        # same name only in an archive -> not "live in modified form"
        _member(member="relic.py", blob_lf="5" * 40, first_path="old/relic.py",
                name_only_matches_on_ref=["docs/archive/relic.py"]),
        # same name, different content, never in Git -> external, the name is only a hint
        _member(member="hint.py", blob_lf="6" * 40, state="EXTERNAL_ONLY", name_only_matches_on_ref=["app/hint.py"]),
        # an ambiguous row that a human then rules on
        _member(member="ruled.py", blob_lf="7" * 40, first_path="old/ruled.py",
                name_only_matches_on_ref=["app/a/ruled.py", "app/b/ruled.py"]),
    ]
    run, rows = _ledger(tmp_path, members, {"by_blob": {"7" * 40: {
        "disposition": "SUPERSEDED", "reason": "fixture ruling with a long enough reason"}}})
    assert run.returncode == 0, run.stderr
    expected = {
        "a/dup.py": ("LIVE_INTEGRATED", "MECHANICALLY_VERIFIED", "LIVE_INTEGRATED"),
        "lineage.py": ("LIVE_MODIFIED", "HEURISTIC_CANDIDATE", "LIVE_MODIFIED"),
        "named.py": ("LIVE_MODIFIED", "HEURISTIC_CANDIDATE", "LIVE_MODIFIED"),
        "twin.py": ("UNRESOLVED", "UNRESOLVED", "UNRESOLVED"),
        "relic.py": ("UNRESOLVED", "UNRESOLVED", "UNRESOLVED"),
        "hint.py": ("EXTERNAL_ONLY", "MECHANICALLY_VERIFIED", "EXTERNAL_ONLY"),
        "ruled.py": ("SUPERSEDED", "MANUALLY_ADJUDICATED", "UNRESOLVED"),
    }
    got = {k: (r["disposition"], r["proof_class"], r["automatic_disposition"]) for k, r in rows.items()}
    assert got == expected
    assert rows["a/dup.py"]["source_bundles"] == "S1;S2"
    assert "app/lineage.py" in rows["lineage.py"]["proof_method"]
    assert rows["ruled.py"]["override_id"] == "by_blob:77777777"


def test_malformed_overrides_are_refused(tmp_path):
    members = [_member(member="a/x.py", blob_lf="1" * 40), _member(member="b/x.py", blob_lf="2" * 40),
               _member(member="y.py", blob_lf="3" * 40)]
    good = {"disposition": "SUPERSEDED", "reason": "r" * 20}
    blob = "3" * 40
    cases = {
        "ambiguous name": ({"by_name": {"x.py": good}}, "ambiguous"),
        "duplicate key": ('{"exclude": [], "reference_only": [], "by_name": {}, "by_blob": {'
                          f'"{blob}": {json.dumps(good)}, "{blob}": {json.dumps(good)}}}}}', "duplicate key"),
        "unknown disposition": ({"by_blob": {blob: good | {"disposition": "PROBABLY_FINE"}}}, "not allowed"),
        "short reason": ({"by_blob": {blob: good | {"reason": "because"}}}, "under 20"),
        "stale blob": ({"by_blob": {"9" * 40: good}}, "matches nothing"),
        "stale name": ({"by_name": {"gone.py": good}}, "matches nothing"),
        "duplicate reference id": ({"reference_only": [
            {"candidate_id": "MC-R01", "disposition": "UNRESOLVED"},
            {"candidate_id": "MC-R01", "disposition": "UNRESOLVED"}]}, "MC-R01"),
        "not JSON": ("{", "not valid JSON"),
    }
    for label, (overrides, marker) in cases.items():
        out = tmp_path / label.replace(" ", "_")
        out.mkdir()
        run, _ = _ledger(out, members, overrides)
        assert run.returncode == 2, f"{label}: accepted ({run.stderr})"
        assert marker in run.stderr, f"{label}: {run.stderr}"
        assert not (out / "ledger.csv").exists(), f"{label}: a ledger was written anyway"


def test_bundle_census_matches_by_content_not_name(tmp_path, monkeypatch):
    """Run the census tool against a scratch repository with a rename, a deletion and an edit."""
    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text("", encoding="utf-8")
    for key, value in {"GIT_CONFIG_GLOBAL": str(gitconfig), "GIT_CONFIG_NOSYSTEM": "1",
                       "GIT_AUTHOR_NAME": "census", "GIT_AUTHOR_EMAIL": "census@example.invalid",
                       "GIT_COMMITTER_NAME": "census", "GIT_COMMITTER_EMAIL": "census@example.invalid"}.items():
        monkeypatch.setenv(key, value)
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)

    def put(rel: str, data: bytes) -> None:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes(data)

    git("init", "-q")
    for rel, data in {"app/keep.py": b"keep\n", "app/old_name.py": b"moved\n", "app/gone.py": b"deleted\n",
                      "archive/old.py": b"archived\n", "app/edit.py": b"v1\n"}.items():
        put(rel, data)
    git("add", "-A")
    git("commit", "-q", "-m", "one")
    git("mv", "app/old_name.py", "app/new_name.py")
    git("rm", "-q", "app/gone.py")
    put("app/edit.py", b"v1\nv2\n")
    git("add", "-A")
    git("commit", "-q", "-m", "two")

    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w") as zf:
        zf.writestr("edit.py", b"v1\nv2\nv3\n")  # superset of live content: a partial match is not presence
    bundle = tmp_path / "bundle.zip"
    with zipfile.ZipFile(bundle, "w") as zf:
        zf.writestr("keep.py", b"keep\r\n")      # CRLF copy of live content
        zf.writestr("old_name.py", b"moved\n")   # live content under a misleading (pre-rename) name
        zf.writestr("gone.py", b"deleted\n")     # deleted, still reachable in history
        zf.writestr("old.py", b"archived\n")     # only under archive/
        zf.writestr("edit.py", b"v1\n")          # an earlier version of a live file
        zf.writestr("nested.zip", inner.getvalue())

    census_tool = _tool("march_2026_bundle_census")
    outs = [f"--out-json={tmp_path / 'c.json'}", f"--out-bundles={tmp_path / 'b.csv'}",
            f"--out-members={tmp_path / 'm.csv'}"]
    assert census_tool.main(["--repo", str(repo), "--ref", "HEAD", *outs, f"S1={tmp_path / 'absent.zip'}"]) == 2
    assert not (tmp_path / "c.json").exists(), "a missing bundle must not yield a partial census"
    assert census_tool.main(["--repo", str(repo), "--ref", "HEAD", *outs, f"S1={bundle}"]) == 0

    members = {m["member"]: m for m in json.loads((tmp_path / "c.json").read_text(encoding="utf-8"))["members"]}
    got = {k: (m["state"], m["live_paths"] or m["archive_paths"], m["name_only_matches_on_ref"])
           for k, m in members.items()}
    assert got == {
        "keep.py": ("LIVE_IDENTICAL", ["app/keep.py"], []),
        "old_name.py": ("LIVE_IDENTICAL", ["app/new_name.py"], []),
        "gone.py": ("HISTORY_ONLY", [], []),
        "old.py": ("ARCHIVE_ONLY", ["archive/old.py"], []),
        "edit.py": ("HISTORY_ONLY", [], ["app/edit.py"]),
        "nested.zip!/edit.py": ("EXTERNAL_ONLY", [], ["app/edit.py"]),
    }
    assert members["gone.py"]["first_path"] == "app/gone.py"

    empty = {"exclude": [], "reference_only": [], "by_blob": {}, "by_name": {}}
    (tmp_path / "o.json").write_text(json.dumps(empty), encoding="utf-8")
    run = _run_ledger(tmp_path / "c.json", tmp_path / "o.json", tmp_path)
    assert run.returncode == 0, run.stderr
    with (tmp_path / "ledger.csv").open(encoding="utf-8", newline="") as fh:
        ledger = {r["original_path"]: (r["disposition"], r["proof_class"]) for r in csv.DictReader(fh)}
    assert ledger == {
        "keep.py": ("LIVE_INTEGRATED", "MECHANICALLY_VERIFIED"),
        "old_name.py": ("LIVE_INTEGRATED", "MECHANICALLY_VERIFIED"),
        "gone.py": ("UNRESOLVED", "UNRESOLVED"),
        "old.py": ("ARCHIVED_COMPLETE", "MECHANICALLY_VERIFIED"),
        "edit.py": ("LIVE_MODIFIED", "HEURISTIC_CANDIDATE"),
        "nested.zip!/edit.py": ("EXTERNAL_ONLY", "MECHANICALLY_VERIFIED"),
    }


def test_reachability_labels_other_than_absence_are_heuristic():
    proof = _tool("march_2026_claim_reachability").proof
    assert proof("FALSE_MIGRATION_CLAIM")[0] == "MECHANICALLY_VERIFIED"
    assert proof("VERIFIED_PRESENT")[0] == "MECHANICALLY_VERIFIED"
    for label in ("VERIFIED_STRUCTURAL", "PARTIAL_MIGRATION", "STRANDED_IMPLEMENTATION"):
        assert proof(label)[0] == "HEURISTIC_CANDIDATE", label
