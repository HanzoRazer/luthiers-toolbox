"""Evidence gate for CLIENT-ROSETTE-COMPARE-RECONCILE-023.

useRosetteCompareApi.ts is the only Rosette baseline/diff Axios client.
RosetteComparePanel.vue keeps presentation, selection, drawing, localStorage,
and job-id emission. /api/compare/lab is a different contract. The original
Axios inventory CSV stays unchanged. The panel stays unrouted.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INVESTIGATION = REPO / "docs/investigations/client-rosette-compare-reconcile-023"
RECONCILE_PATH = INVESTIGATION / "RECONCILIATION.json"
README_PATH = INVESTIGATION / "README.md"
INVENTORY = (
    REPO / "docs/investigations/client-axios-reachability-020_2026-11-10/AXIOS_IMPORT_INVENTORY.csv"
)
RETIREMENTS = (
    REPO / "docs/investigations/client-axios-reachability-020_2026-11-10/POST_AUDIT_RETIREMENTS.json"
)
PANEL = "packages/client/src/components/art/RosetteComparePanel.vue"
CANONICAL = "packages/client/src/components/art/rosette-compare/useRosetteCompareApi.ts"
INDEX = "packages/client/src/components/art/rosette-compare/index.ts"
PANEL_SPEC = "packages/client/src/components/art/__tests__/RosetteComparePanel.spec.ts"
API_SPEC = "packages/client/src/components/art/rosette-compare/__tests__/useRosetteCompareApi.spec.ts"
SRC = REPO / "packages/client/src"
ROUTER = SRC / "router"
WORKFLOW = REPO / ".github/workflows/core_ci.yml"
SPRINTS = REPO / "SPRINTS.md"
PACKAGE = REPO / "packages/client/package.json"
SCAN_SCRIPT = REPO / "scripts/investigations/client_axios_reachability.py"
sys.path.insert(0, str(SCAN_SCRIPT.parent))
import client_axios_reachability as scan  # noqa: E402

PANEL_AXIOS_SHA256 = "37d4b02e3bdb25820b7701ad111d9c97289fcdfd276164284d98ac550fb802fc"
INVENTORY_SHA256 = "8fd2500b9d35bf38566dfa62db8ee2785562f449a0417e764492131c645d1092"
ORDER = "CLIENT-ROSETTE-COMPARE-RECONCILE-023"
LAB_CLIENTS = (
    "packages/client/src/composables/useCompareState.ts",
    "packages/client/src/components/compare/CompareBaselinePicker.vue",
    "packages/client/src/components/compare/CompareDiffViewer.vue",
)
UNROUTED_NAMES = (
    "RosetteComparePanel",
    "useRosetteCompareApi",
    "ArtStudioUnified",
    "CamProductionView",
)
AUTHORITY_TOKENS = ("manufacturing", "readiness", "approval", "cam_ready", "machine_approved")
OPERATIONS = [
    {
        "name": "loadBaselines",
        "method": "GET",
        "url": "/api/compare/baselines",
        "params": {"lane": "rosette"},
    },
    {
        "name": "saveBaseline",
        "method": "POST",
        "url": "/api/compare/baselines",
        "body": ["name", "lane", "geometry"],
        "name_trimmed": False,
        "then": "loadBaselines",
        "returns": "id",
    },
    {
        "name": "loadBaselineGeometry",
        "method": "GET",
        "url": "/api/compare/baselines/{id}",
        "url_encoding": "encodeURIComponent",
        "stores": "geometry",
    },
    {
        "name": "runDiff",
        "method": "POST",
        "url": "/api/compare/diff",
        "body": ["baseline_id", "lane", "current_geometry"],
        "trimmed_optional": ["job_id", "preset"],
        "omit_when_blank": ["job_id", "preset"],
    },
]
RESULT_KEYS = (
    "focused_vitest",
    "client_vitest",
    "type_check",
    "lint",
    "production_build",
    "lineage_pytest",
    "cbsp21",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_reconciliation() -> dict:
    return json.loads(RECONCILE_PATH.read_text(encoding="utf-8"))


def hashes_by_path(record: dict) -> dict[str, dict]:
    return {item["path"]: item for item in record["source_hashes"]}


def test_reconciliation_names_the_canonical_unrouted_client() -> None:
    record = load_reconciliation()
    assert record["order_id"] == ORDER
    assert record["authority"] == "NONE"
    assert record["disposition"] == "DORMANT_PRESERVE — CANONICAL_BUT_UNROUTED"
    assert record["routing_status"] == "UNROUTED"
    assert record["canonical_client"] == CANONICAL
    assert record["presentation"] == PANEL
    assert record["axios_status"] == "RETAINED"
    assert record["importers"] == {"before": 18, "after": 17}
    assert record["operations"] == OPERATIONS
    assert record["not_equivalent"] == list(LAB_CLIENTS)
    non_goals = " ".join(record["non_goals"]).lower()
    for phrase in (
        "axios removal",
        "archive",
        "risk dashboard",
        "router",
        "backend",
        "/api/compare/lab",
        "cam",
    ):
        assert phrase in non_goals
    assert record["findings"][0]["id"] == "ROSETTE-C01"
    assert record["findings"][0]["status"] == "resolved"


def test_source_hashes_match_the_tree_and_the_pre_adoption_panel() -> None:
    record = load_reconciliation()
    hashed = hashes_by_path(record)
    panel = hashed[PANEL]
    assert panel["historical_sha256"] == PANEL_AXIOS_SHA256
    assert panel["sha256"] == sha256(REPO / PANEL)
    assert panel["sha256"] != panel["historical_sha256"]
    assert panel["status"] == "edited"
    canonical = hashed[CANONICAL]
    assert canonical["sha256"] == sha256(REPO / CANONICAL)
    assert canonical["historical_sha256"] == "1e12557982dbc655697aaab494fc6d09b0a22dd1a3c20de1be9aca3ba79c8f68"
    assert canonical["status"] == "edited"
    index = hashed[INDEX]
    assert index["sha256"] == sha256(REPO / INDEX)
    assert index["sha256"] == index["historical_sha256"]
    assert index["status"] == "unchanged"
    for rel in (PANEL_SPEC, API_SPEC):
        assert hashed[rel]["sha256"] == sha256(REPO / rel)
    assert sha256(INVENTORY) == INVENTORY_SHA256
    assert record["inventory_sha256"] == INVENTORY_SHA256


def test_panel_has_no_axios_and_the_composable_owns_the_four_calls() -> None:
    panel = (REPO / PANEL).read_text(encoding="utf-8")
    canonical = (REPO / CANONICAL).read_text(encoding="utf-8")
    assert "from 'axios'" not in panel and 'from "axios"' not in panel
    assert not re.search(r"\baxios\.", panel)
    assert "useRosetteCompareApi" in panel
    assert "localStorage" in panel
    assert "ltb:compare:lastJobId" in panel
    assert "update:job-id" in panel
    assert "/api/compare" not in panel
    assert "encodeURIComponent" in canonical
    assert "/api/compare/baselines" in canonical
    assert "/api/compare/diff" in canonical
    assert "/api/compare/lab" not in canonical
    assert "localStorage" not in canonical
    assert "update:job-id" not in canonical
    for token in AUTHORITY_TOKENS:
        assert token not in panel.lower()
        assert token not in canonical.lower()


def test_barrel_exports_the_client_once() -> None:
    index = (REPO / INDEX).read_text(encoding="utf-8")
    assert len(re.findall(r"^\s*useRosetteCompareApi,", index, re.M)) == 1
    for name in (
        "GeometryPayload",
        "BaselineSummary",
        "DiffStats",
        "DiffOut",
        "UseRosetteCompareApiOptions",
    ):
        assert len(re.findall(rf"^\s*type {name},?\s*$", index, re.M)) == 1


def test_lab_clients_remain_a_different_contract() -> None:
    record = load_reconciliation()
    assert record["not_equivalent"] == list(LAB_CLIENTS)
    for rel in LAB_CLIENTS:
        text = (REPO / rel).read_text(encoding="utf-8")
        assert "/api/compare/lab" in text
        assert rel != CANONICAL
    combined = "\n".join((REPO / rel).read_text(encoding="utf-8") for rel in (PANEL, CANONICAL))
    assert "/api/compare/lab" not in combined


def test_only_the_composable_imports_axios_for_these_endpoints() -> None:
    holders: list[str] = []
    for path in SRC.rglob("*"):
        if path.suffix not in {".ts", ".vue", ".js"} or "__tests__" in path.parts:
            continue
        if path.name.endswith(".spec.ts"):
            continue
        text = path.read_text(encoding="utf-8")
        if "from 'axios'" not in text and 'from "axios"' not in text:
            continue
        if "/api/compare/baselines" in text or "/api/compare/diff" in text:
            holders.append(path.relative_to(REPO).as_posix())
    assert holders == [CANONICAL]


def test_feature_stays_unrouted_and_axios_stays_declared() -> None:
    router_text = "\n".join(path.read_text(encoding="utf-8") for path in ROUTER.rglob("*") if path.is_file())
    for name in UNROUTED_NAMES:
        assert name not in router_text
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    declared = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    assert declared["axios"] == "^1.21.0"
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "scripts/ci/test_client_rosette_compare_lineage.py" in workflow
    sprints = SPRINTS.read_text(encoding="utf-8")
    assert ORDER in sprints
    assert "dormant-preserve" in sprints
    assert "Axios consolidation remains incomplete" in sprints
    readme = README_PATH.read_text(encoding="utf-8")
    assert "unrouted" in readme
    assert "18" in readme and "17" in readme
    assert "/api/compare/lab" in readme


def test_overlay_retires_the_panel_import_and_keeps_the_csv() -> None:
    overlay = json.loads(RETIREMENTS.read_text(encoding="utf-8"))
    retired = {item["path"]: item for item in overlay["retired_importers"]}
    panel = retired[PANEL]
    assert panel["sha256"] == PANEL_AXIOS_SHA256
    assert panel["canonical_replacement"] == CANONICAL
    assert panel["reconciliation_order"] == ORDER
    assert panel["file_retained"] is True
    reclassified = {item["path"]: item for item in overlay["reclassified_importers"]}
    assert reclassified[CANONICAL]["disposition"] == "DORMANT_PRESERVE — CANONICAL_BUT_UNROUTED"
    assert sha256(INVENTORY) == INVENTORY_SHA256
    with INVENTORY.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 20
    assert overlay.get("post_audit_importers") == []


def test_scanned_production_importers_are_17() -> None:
    scanned = {f"packages/client/src/{rel}" for rel in scan.axios_importers(SRC)}
    with INVENTORY.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    overlay = json.loads(RETIREMENTS.read_text(encoding="utf-8"))
    retired = {item["path"] for item in overlay["retired_importers"]}
    extra = set(overlay.get("post_audit_importers") or [])
    expected = sorted(({row["path"] for row in rows} - retired) | extra)
    assert len(expected) == 17
    assert PANEL not in scanned
    assert PANEL not in expected
    assert CANONICAL in scanned
    assert CANONICAL in expected
    unexpected = [
        path
        for path in scanned - set(expected)
        if "/__tests__/" not in path and not path.endswith(".spec.ts")
    ]
    assert unexpected == []


def test_record_includes_the_verification_commands() -> None:
    record = load_reconciliation()
    commands = "\n".join(record["verification"]["commands"])
    for fragment in (
        "useRosetteCompareApi.spec.ts",
        "RosetteComparePanel.spec.ts",
        "npm test",
        "npm run build",
        "type-check",
        "lint:report",
        "test_client_rosette_compare_lineage.py",
        "test_client_axios_reachability.py",
        "check_cbsp21_gate.py",
        "check_cbsp21_patch_input.py",
    ):
        assert fragment in commands
    results = record["verification"]["results"]
    for key in RESULT_KEYS:
        assert str(results[key]).strip()
