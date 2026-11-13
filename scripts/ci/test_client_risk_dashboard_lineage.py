"""Evidence gate for CLIENT-RISK-DASHBOARD-LINEAGE-021.

The 63-row matrix stays the pre-reconciliation record. A closed reconciliation
may declare the February 22 directory canonical when every EARLIER_ONLY row
maps to a resolved finding, no CONTRACT_DRIFT or UNKNOWN_INTENT remains, and
the replacement path is named. Historical hashes stay in the 021 evidence
file. Superseded paths must be absent, and their recorded hashes must still
match that evidence when the path was hashed there.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INVESTIGATION = REPO / "docs/investigations/client-risk-dashboard-lineage-021_2026-11-10"
RECONCILE_PATH = (
    REPO / "docs/investigations/client-risk-dashboard-reconcile-022_2026-11-13/RECONCILIATION.json"
)
MATRIX_PATH = INVESTIGATION / "BEHAVIOR_MATRIX.csv"
DECISION_PATH = INVESTIGATION / "DECISION.md"
EVIDENCE_PATH = INVESTIGATION / "evidence.json"

CLUSTER_FILES = (
    "packages/client/src/views/art/composables/useRiskBuckets.ts",
    "packages/client/src/views/art/composables/useRiskExport.ts",
    "packages/client/src/views/art/risk-dashboard/useRiskBuckets.ts",
    "packages/client/src/views/art/risk-dashboard/useRiskExports.ts",
    "packages/client/src/views/art/risk-dashboard/useRiskBucketDetails.ts",
)

REQUIRED_HASH_PATHS = CLUSTER_FILES + (
    "packages/client/src/views/art/composables/index.ts",
    "packages/client/src/views/art/composables/useRiskFilters.ts",
    "packages/client/src/views/art/risk-dashboard/index.ts",
    "packages/client/src/views/art/risk-dashboard/riskFormatters.ts",
    "packages/client/src/views/art/risk-dashboard/useRiskFilters.ts",
    "packages/client/src/views/art/risk-dashboard/useRiskNavigation.ts",
    "packages/client/src/views/art/RiskDashboardCrossLab.vue",
    "packages/client/src/views/art/RiskDashboardCrossLabV2.vue",
)

CANONICAL_REPLACEMENT = "packages/client/src/views/art/risk-dashboard/"
ALLOWED_FINDINGS = {"RISK-L01", "RISK-L02", "RISK-L03"}
CLASSIFICATIONS = {
    "EQUIVALENT",
    "INTENTIONAL_IMPROVEMENT",
    "EARLIER_ONLY",
    "LATER_ONLY",
    "CONTRACT_DRIFT",
    "UNKNOWN_INTENT",
}
BLOCKING_WHEN_CANONICAL = {"EARLIER_ONLY", "CONTRACT_DRIFT", "UNKNOWN_INTENT"}
STATUSES = {"Equivalent", "changed", "unique", "missing", "uncertain"}
EXPORT_RE = re.compile(
    r"^export\s+(?:async\s+)?(?:function|interface|type|const|class|enum)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)


def exported_symbols(path: Path) -> list[str]:
    return EXPORT_RE.findall(path.read_text(encoding="utf-8"))


def load_matrix(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_reconciliation(path: Path | None = None) -> dict:
    return json.loads((path or RECONCILE_PATH).read_text(encoding="utf-8"))


def superseded_paths(reconciliation: dict) -> set[str]:
    return set(reconciliation.get("superseded_paths") or [])


def missing_exports(
    rows: list[dict[str, str]],
    repo: Path,
    superseded: set[str] | None = None,
) -> list[str]:
    present = {(row["source_file"], row["symbol"]) for row in rows}
    skipped = superseded or set()
    missing: list[str] = []
    for rel in CLUSTER_FILES:
        if rel in skipped:
            continue
        path = repo / rel
        if not path.is_file():
            missing.append(f"absent {rel}")
            continue
        for name in exported_symbols(path):
            if (rel, name) not in present:
                missing.append(f"{rel}::{name}")
    return missing


def unclassified(rows: list[dict[str, str]]) -> list[str]:
    problems: list[str] = []
    for index, row in enumerate(rows, start=2):
        status = (row.get("status") or "").strip()
        classification = (row.get("classification") or "").strip()
        label = f"line {index} {row.get('source_file')}::{row.get('symbol')}"
        if status not in STATUSES:
            problems.append(f"{label} status {status!r}")
        if classification not in CLASSIFICATIONS:
            problems.append(f"{label} classification {classification!r}")
    return problems


def declares_canonical(decision: str) -> bool:
    return any(line.strip().startswith("CANONICAL_BASELINE:") for line in decision.splitlines())


def _finding_complete(finding: object) -> bool:
    if not isinstance(finding, dict):
        return False
    return bool(finding.get("implementation")) and bool(finding.get("tests"))


def canonical_conflicts(
    decision: str,
    rows: list[dict[str, str]],
    reconciliation: dict | None = None,
) -> list[str]:
    status = ""
    if reconciliation is not None:
        status = str(reconciliation.get("canonical_status") or "")
    if not declares_canonical(decision) and status != "CANONICAL":
        return []
    if reconciliation is None:
        return [
            f"{row['source_file']}::{row['symbol']} {row['classification']}"
            for row in rows
            if (row.get("classification") or "").strip() in BLOCKING_WHEN_CANONICAL
        ]
    problems: list[str] = []
    if str(reconciliation.get("target_baseline") or "") != CANONICAL_REPLACEMENT:
        problems.append("canonical status without a named replacement")
    resolved = reconciliation.get("resolved_findings") or {}
    if not isinstance(resolved, dict):
        resolved = {}
        problems.append("resolved_findings is not an object")
    for finding_id in ALLOWED_FINDINGS:
        if not _finding_complete(resolved.get(finding_id)):
            problems.append(f"incomplete resolution {finding_id}")
    mapped: set[tuple[str, str]] = set()
    for item in reconciliation.get("earlier_only_resolutions") or []:
        finding = str(item.get("finding") or "")
        key = (str(item.get("source_file") or ""), str(item.get("symbol") or ""))
        if finding not in ALLOWED_FINDINGS or finding not in resolved:
            problems.append(f"unrecognized resolution {finding}")
            continue
        mapped.add(key)
    for row in rows:
        classification = (row.get("classification") or "").strip()
        key = (str(row.get("source_file") or ""), str(row.get("symbol") or ""))
        label = f"{key[0]}::{key[1]}"
        if classification in {"CONTRACT_DRIFT", "UNKNOWN_INTENT"}:
            problems.append(f"{label} {classification}")
        elif classification == "EARLIER_ONLY" and key not in mapped:
            problems.append(f"unclosed {label}")
    return problems


def superseded_without_replacement(decision: str) -> bool:
    return "SUPERSEDED_REMOVE" in decision and CANONICAL_REPLACEMENT not in decision


def historical_hash_gaps(sources: list[dict[str, str]]) -> list[str]:
    recorded = {item["path"] for item in sources if item.get("sha256")}
    return [f"missing hash entry {rel}" for rel in REQUIRED_HASH_PATHS if rel not in recorded]


def closed_reconciliation_problems(
    reconciliation: dict,
    sources: list[dict[str, str]],
    repo: Path,
) -> list[str]:
    problems = historical_hash_gaps(sources)
    recorded = {item["path"]: item["sha256"] for item in sources}
    hashes = {item["path"]: item for item in reconciliation.get("source_hashes") or []}
    superseded = superseded_paths(reconciliation)
    for rel in sorted(superseded):
        if (repo / rel).exists():
            problems.append(f"surviving superseded production file {rel}")
        digest = str((hashes.get(rel) or {}).get("sha256") or "")
        if not digest:
            problems.append(f"missing historical hash {rel}")
            continue
        if rel in recorded and digest != recorded[rel]:
            problems.append(f"historical hash mismatch {rel}")
    for rel, entry in hashes.items():
        if rel in superseded or entry.get("status") == "superseded":
            continue
        path = repo / rel
        if not path.is_file():
            problems.append(f"missing canonical target {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != entry.get("sha256"):
            problems.append(f"{rel} recorded {entry.get('sha256')} actual {actual}")
        historical = str(entry.get("historical_sha256") or "")
        if entry.get("status") == "edited":
            if not historical:
                problems.append(f"missing historical hash {rel}")
            elif rel in recorded and historical != recorded[rel]:
                problems.append(f"historical hash mismatch {rel}")
        elif entry.get("status") == "unchanged" and rel in recorded and actual != recorded[rel]:
            problems.append(f"historical drift {rel}")
    for rel in REQUIRED_HASH_PATHS:
        if rel in superseded:
            continue
        if rel not in hashes:
            problems.append(f"missing canonical target record {rel}")
    return problems


def test_risk_dashboard_lineage_evidence() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    rows = load_matrix(MATRIX_PATH)
    decision = DECISION_PATH.read_text(encoding="utf-8")
    reconciliation = load_reconciliation()
    assert list(evidence["cluster_files"]) == list(CLUSTER_FILES)
    assert missing_exports(rows, REPO, superseded_paths(reconciliation)) == []
    assert unclassified(rows) == []
    assert canonical_conflicts(decision, rows, reconciliation) == []
    assert superseded_without_replacement(decision) is False
    recorded_paths = {item["path"] for item in evidence["sources"]}
    matrix_paths = {row["source_file"] for row in rows}
    assert matrix_paths <= recorded_paths
    assert closed_reconciliation_problems(reconciliation, evidence["sources"], REPO) == []
    assert reconciliation["canonical_status"] == "CANONICAL"
    assert reconciliation["routing_status"] == "UNROUTED"
    assert reconciliation["authority"] == "NONE"
    assert reconciliation["axios_status"] == "RETAINED"


def test_checker_rejects_a_missing_export() -> None:
    live = load_matrix(MATRIX_PATH)
    surviving = CLUSTER_FILES[2]
    dropped = [
        row for row in live
        if not (row["source_file"] == surviving and row["symbol"] == "useRiskBuckets")
    ]
    missing = missing_exports(dropped, REPO, superseded_paths(load_reconciliation()))
    assert f"{surviving}::useRiskBuckets" in missing


def test_checker_rejects_a_blank_classification() -> None:
    rows = load_matrix(MATRIX_PATH)
    broken = [dict(row) for row in rows]
    broken[0]["classification"] = ""
    assert unclassified(broken)


def test_checker_rejects_canonical_with_unresolved_difference() -> None:
    rows = [{"source_file": "a.ts", "symbol": "refresh", "classification": "CONTRACT_DRIFT"}]
    assert canonical_conflicts(
        "CANONICAL_BASELINE:\npackages/client/src/views/art/risk-dashboard/\n",
        rows,
    )
    earlier = [{"source_file": "a.ts", "symbol": "sync", "classification": "EARLIER_ONLY"}]
    assert canonical_conflicts("CANONICAL_BASELINE:\n", earlier)
    assert canonical_conflicts("canonical status is withheld\n", earlier) == []


def test_checker_rejects_superseded_without_a_named_replacement() -> None:
    assert superseded_without_replacement("DISPOSITION:\nFebruary 19 cluster = SUPERSEDED_REMOVE\n")
    assert superseded_without_replacement("SUPERSEDED_REMOVE\n" + CANONICAL_REPLACEMENT) is False


def test_checker_rejects_an_unclosed_earlier_only_behavior() -> None:
    rows = load_matrix(MATRIX_PATH)
    broken = json.loads(json.dumps(load_reconciliation()))
    broken["earlier_only_resolutions"] = [
        item for item in broken["earlier_only_resolutions"] if item["finding"] != "RISK-L03"
    ]
    problems = canonical_conflicts(DECISION_PATH.read_text(encoding="utf-8"), rows, broken)
    assert any("unclosed" in item and "watch since until" in item for item in problems)


def test_checker_rejects_canonical_without_a_named_replacement() -> None:
    rows = load_matrix(MATRIX_PATH)
    broken = json.loads(json.dumps(load_reconciliation()))
    broken["target_baseline"] = ""
    problems = canonical_conflicts(DECISION_PATH.read_text(encoding="utf-8"), rows, broken)
    assert any("named replacement" in item for item in problems)


def test_checker_rejects_a_missing_historical_hash() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    sources = [item for item in evidence["sources"] if not item["path"].endswith("V2.vue")]
    assert any("RiskDashboardCrossLabV2.vue" in item for item in historical_hash_gaps(sources))
    broken = json.loads(json.dumps(load_reconciliation()))
    for item in broken["source_hashes"]:
        if item["path"].endswith("RiskDashboardCrossLabV2.vue"):
            item["sha256"] = ""
    problems = closed_reconciliation_problems(broken, evidence["sources"], REPO)
    assert any("missing historical hash" in item and "V2.vue" in item for item in problems)


def test_checker_rejects_a_stale_hash() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    broken = json.loads(json.dumps(load_reconciliation()))
    for item in broken["source_hashes"]:
        if item["path"].endswith("useRiskNavigation.ts"):
            item["sha256"] = "0" * 64
    problems = closed_reconciliation_problems(broken, evidence["sources"], REPO)
    assert any("useRiskNavigation.ts" in item for item in problems)


def test_checker_rejects_a_surviving_superseded_file(tmp_path: Path) -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    rel = "packages/client/src/views/art/RiskDashboardCrossLabV2.vue"
    target = tmp_path / rel
    target.parent.mkdir(parents=True)
    target.write_text("still here\n", encoding="utf-8")
    problems = closed_reconciliation_problems(load_reconciliation(), evidence["sources"], tmp_path)
    assert any(item.startswith("surviving superseded") and rel in item for item in problems)


def test_checker_rejects_a_missing_canonical_target(tmp_path: Path) -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    problems = closed_reconciliation_problems(load_reconciliation(), evidence["sources"], tmp_path)
    assert any(
        item.startswith("missing canonical target ") and item.endswith("useRiskFilters.ts")
        for item in problems
    )


def test_checker_rejects_an_unrecognized_resolution_id() -> None:
    rows = [{
        "source_file": "packages/client/src/views/art/risk-dashboard/useRiskFilters.ts",
        "symbol": "syncFiltersToQuery",
        "classification": "EARLIER_ONLY",
    }]
    reconciliation = {
        "canonical_status": "CANONICAL",
        "target_baseline": CANONICAL_REPLACEMENT,
        "resolved_findings": {
            "RISK-L01": {"implementation": "useRiskFilters.ts", "tests": ["trim spec"]},
            "RISK-L02": {"implementation": "RiskDashboardCrossLab.vue", "tests": ["view spec"]},
            "RISK-L03": {"implementation": "RiskDashboardCrossLab.vue", "tests": ["view spec"]},
        },
        "earlier_only_resolutions": [{
            "source_file": rows[0]["source_file"],
            "symbol": "syncFiltersToQuery",
            "finding": "RISK-L99",
        }],
    }
    problems = canonical_conflicts("CANONICAL_BASELINE:\n", rows, reconciliation)
    assert any("unrecognized resolution RISK-L99" in item for item in problems)


def test_closure_declares_canonical_only_after_findings_resolve() -> None:
    rows = load_matrix(MATRIX_PATH)
    decision = DECISION_PATH.read_text(encoding="utf-8")
    assert any(row["classification"] == "EARLIER_ONLY" for row in rows)
    assert "IMPLEMENTATION_CLOSURE:" in decision
    assert declares_canonical(decision) is True
    assert canonical_conflicts(decision, rows, load_reconciliation()) == []
    assert canonical_conflicts(decision, rows) != []
