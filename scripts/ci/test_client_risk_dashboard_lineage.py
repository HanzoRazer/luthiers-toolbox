"""Evidence gate for CLIENT-RISK-DASHBOARD-LINEAGE-021.

Fails when an exported symbol from the five risk modules is missing from the
behavior matrix, a matrix row has no classification, a canonical ruling is
recorded while EARLIER_ONLY, CONTRACT_DRIFT, or UNKNOWN_INTENT remains, a
superseded disposition has no named replacement, or a recorded source hash
no longer matches the file.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INVESTIGATION = REPO / "docs/investigations/client-risk-dashboard-lineage-021_2026-11-10"
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


def missing_exports(rows: list[dict[str, str]], repo: Path) -> list[str]:
    present = {(row["source_file"], row["symbol"]) for row in rows}
    missing: list[str] = []
    for rel in CLUSTER_FILES:
        for name in exported_symbols(repo / rel):
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


def canonical_conflicts(decision: str, rows: list[dict[str, str]]) -> list[str]:
    if not declares_canonical(decision):
        return []
    return [
        f"{row['source_file']}::{row['symbol']} {row['classification']}"
        for row in rows
        if (row.get("classification") or "").strip() in BLOCKING_WHEN_CANONICAL
    ]


def superseded_without_replacement(decision: str) -> bool:
    return "SUPERSEDED_REMOVE" in decision and CANONICAL_REPLACEMENT not in decision


def hash_mismatches(sources: list[dict[str, str]], repo: Path) -> list[str]:
    problems: list[str] = []
    recorded = {item["path"]: item["sha256"] for item in sources}
    for rel in REQUIRED_HASH_PATHS:
        if rel not in recorded:
            problems.append(f"missing hash entry {rel}")
    for rel, expected in recorded.items():
        actual = hashlib.sha256((repo / rel).read_bytes()).hexdigest()
        if actual != expected:
            problems.append(f"{rel} recorded {expected} actual {actual}")
    return problems


def test_risk_dashboard_lineage_evidence() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    rows = load_matrix(MATRIX_PATH)
    decision = DECISION_PATH.read_text(encoding="utf-8")
    assert list(evidence["cluster_files"]) == list(CLUSTER_FILES)
    assert missing_exports(rows, REPO) == []
    assert unclassified(rows) == []
    assert canonical_conflicts(decision, rows) == []
    assert superseded_without_replacement(decision) is False
    recorded_paths = {item["path"] for item in evidence["sources"]}
    matrix_paths = {row["source_file"] for row in rows}
    assert matrix_paths <= recorded_paths
    assert hash_mismatches(evidence["sources"], REPO) == []


def test_checker_rejects_a_missing_export(tmp_path: Path) -> None:
    source = tmp_path / "useRiskBuckets.ts"
    source.write_text("export function useRiskBuckets() {}\n", encoding="utf-8")
    rows = [{"source_file": CLUSTER_FILES[0], "symbol": "other"}]
    # The real cluster files are read from the repo. A renamed expectation is
    # covered by comparing the live export list with a matrix that drops one.
    live = load_matrix(MATRIX_PATH)
    dropped = [row for row in live if not (
        row["source_file"] == CLUSTER_FILES[0] and row["symbol"] == "useRiskBuckets"
    )]
    assert any(item.endswith("::useRiskBuckets") for item in missing_exports(dropped, REPO))
    assert source.exists()


def test_checker_rejects_a_blank_classification() -> None:
    rows = load_matrix(MATRIX_PATH)
    broken = [dict(row) for row in rows]
    broken[0]["classification"] = ""
    assert unclassified(broken)


def test_checker_rejects_canonical_with_unresolved_difference() -> None:
    rows = [{"source_file": "a.ts", "symbol": "refresh", "classification": "CONTRACT_DRIFT"}]
    assert canonical_conflicts("CANONICAL_BASELINE:\npackages/client/src/views/art/risk-dashboard/\n", rows)
    earlier = [{"source_file": "a.ts", "symbol": "sync", "classification": "EARLIER_ONLY"}]
    assert canonical_conflicts("CANONICAL_BASELINE:\n", earlier)
    assert canonical_conflicts("canonical status is withheld\n", earlier) == []


def test_checker_rejects_superseded_without_a_named_replacement() -> None:
    assert superseded_without_replacement("DISPOSITION:\nFebruary 19 cluster = SUPERSEDED_REMOVE\n")
    assert superseded_without_replacement(
        "SUPERSEDED_REMOVE\n" + CANONICAL_REPLACEMENT
    ) is False


def test_checker_rejects_a_stale_hash(tmp_path: Path) -> None:
    target = tmp_path / "sample.ts"
    target.write_text("export const value = 1\n", encoding="utf-8")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    # Point the checker at a one-file tree by calling the hash helper's
    # comparison shape directly.
    wrong = hashlib.sha256(b"changed\n").hexdigest()
    assert digest != wrong
    sources = [{"path": rel, "sha256": digest} for rel in REQUIRED_HASH_PATHS]
    sources[0]["sha256"] = wrong
    assert hash_mismatches(sources, REPO)


def test_decision_does_not_declare_canonical_while_earlier_behavior_remains() -> None:
    rows = load_matrix(MATRIX_PATH)
    decision = DECISION_PATH.read_text(encoding="utf-8")
    assert any(row["classification"] == "EARLIER_ONLY" for row in rows)
    assert declares_canonical(decision) is False
