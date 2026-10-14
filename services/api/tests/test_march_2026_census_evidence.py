"""March 2026 consolidation recovery census: integrity of the committed dataset.

The census itself (``BUNDLE_CENSUS.json``) cannot be rebuilt in CI: its inputs are
external bundles. Everything derived from it can, and is checked here: the ledger,
inventory and planning CSVs regenerate byte for byte, every manual override is
explained and reviewed, and the safety candidate is recorded once and not fixed.

Pure offline text analysis; no application import. Runtime is dominated by the
repository's API-test setup, so related checks share one test.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.allow_missing_request_id

REPO_ROOT = Path(__file__).resolve().parents[3]
CENSUS = REPO_ROOT / "docs" / "investigations" / "march-2026-consolidation-recovery-census"
LEDGER_TOOL = REPO_ROOT / "scripts" / "investigations" / "march_2026_census_ledger.py"
ALLOWED_DISPOSITIONS = {
    "LIVE_INTEGRATED", "LIVE_MODIFIED", "PARTIALLY_INTEGRATED", "ARCHIVED_COMPLETE",
    "ARCHIVED_INCOMPLETE", "EXTERNAL_ONLY", "LOST_REFERENCE_ONLY", "SUPERSEDED",
    "RECOVERED_FEATURE_CANDIDATE", "RECOVERED_SAFETY_FIX_CANDIDATE", "DUPLICATE", "UNRESOLVED",
}
_NEGATION = re.compile(r"\b(not|no|nothing|never|none)\b|n't\b", re.IGNORECASE)


def _csv(name: str) -> list[dict]:
    with (CENSUS / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _overrides() -> dict:
    return json.loads((CENSUS / "LEDGER_OVERRIDES.json").read_text(encoding="utf-8"))


def _run_ledger(census: Path, overrides: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", str(LEDGER_TOOL), "--census", str(census), "--overrides", str(overrides),
         "--out", str(out / "ledger.csv"), "--out-inventory", str(out / "inventory.csv"),
         "--reachability", str(CENSUS / "MARCH_CLAIM_REACHABILITY.csv"),
         "--out-planning", str(out / "planning.csv")],
        capture_output=True, text=True,
    )


def test_ledger_values_and_overrides_are_well_formed():
    bad = {r["candidate_id"]: r["disposition"] for r in _csv("RECOVERY_LEDGER.csv")
           if r["disposition"] not in ALLOWED_DISPOSITIONS}
    assert bad == {}, f"dispositions outside the allowed set: {bad}"

    ov = _overrides()
    unexplained = [k for k, o in (ov["by_name"] | ov["by_blob"]).items() if len(o.get("reason", "")) < 20]
    unexplained += [r["candidate_id"] for r in ov["reference_only"] if len(r.get("disposition_reason", "")) < 5]
    assert unexplained == [], f"overrides without a stated reason: {unexplained}"
    assert ov["exclude_reason"], "an exclusion without a reason hides evidence"


def test_every_manual_override_has_a_review_row():
    """A reason is not a correctness proof; each override must also be in OVERRIDE_REVIEW.md."""
    review = (CENSUS / "OVERRIDE_REVIEW.md").read_text(encoding="utf-8")
    ov = _overrides()
    keys = [*ov["by_name"], *(b[:8] for b in ov["by_blob"]),
            *(r["candidate_id"] for r in ov["reference_only"])]
    missing = [k for k in keys if f"`{k}`" not in review]
    assert missing == [], f"overrides with no row in OVERRIDE_REVIEW.md: {missing}"
    for pattern in ov["exclude"]:
        assert f"`{pattern}`" in review, f"exclusion {pattern!r} has no row in OVERRIDE_REVIEW.md"


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


def test_a_name_override_matching_two_blobs_is_refused(tmp_path):
    """A by_name override must not silently stamp two different files."""
    member = {"source_id": "S1", "state": "HISTORY_ONLY", "name_only_matches_on_ref": [],
              "sha256": "", "first_commit": "", "first_date": "", "first_path": "",
              "live_paths": [], "archive_paths": []}
    census = {"sources": [{"source_id": "S1", "path": "s1.zip"}], "members": [
        member | {"member": "a/x.py", "blob_lf": "1" * 40},
        member | {"member": "b/x.py", "blob_lf": "2" * 40},
    ]}
    overrides = {"exclude": [], "reference_only": [], "by_blob": {},
                 "by_name": {"x.py": {"disposition": "SUPERSEDED", "reason": "r" * 20}}}
    (tmp_path / "c.json").write_text(json.dumps(census), encoding="utf-8")
    (tmp_path / "o.json").write_text(json.dumps(overrides), encoding="utf-8")
    run = _run_ledger(tmp_path / "c.json", tmp_path / "o.json", tmp_path)
    assert run.returncode == 2
    assert "x.py" in run.stderr
    assert not (tmp_path / "ledger.csv").exists()


def test_the_active_safety_candidate_is_recorded_once_and_not_fixed():
    """The live headstock route descends from blob 8e436e7b, not the B17S sibling draft."""
    flagged = [r for r in _csv("RECOVERY_LEDGER.csv") if "ACTIVE SAFETY CANDIDATE" in r["safety_relevance"]]
    assert [r["content_blob_lf"][:8] for r in flagged] == ["8e436e7b"]
    assert flagged[0]["filename"] == "headstock_transition_export.py"
    assert flagged[0]["follow_up_order"] == "HEADSTOCK-TRANSITION-GCODE-SAFETY-001"


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
