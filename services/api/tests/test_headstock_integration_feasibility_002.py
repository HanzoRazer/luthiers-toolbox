"""HEADSTOCK-INTEGRATION-FEASIBILITY-002: lock the evidence, not a port.

The investigation records what was recovered and names one later design-only
cluster. These tests fail if that record drifts from the archive bytes, if the
missing canvas module reappears as a file, or if a manufacturing composable
gains a runtime caller while this order is still evidence-only.

Pure offline file reads; no application import.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.allow_missing_request_id

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = (
    REPO_ROOT
    / "docs"
    / "investigations"
    / "headstock-integration-feasibility-002_2026-10-19"
)
SUITE = REPO_ROOT / "archive" / "experimental" / "2026-03" / "headstock-suite-refined"
CLIENT = REPO_ROOT / "packages" / "client" / "src"
_COMMENT = re.compile(r"/\*.*?\*/|//.*?$", re.DOTALL | re.MULTILINE)
_CALL = re.compile(r"\b(useExportDxf|useCamSpec)\s*\(")

# LF-normalized SHA-256 measured against main at 4837c500. The four view
# digests are not the short git blob prefixes in the archive README.
EXPECTED_LF_HASHES = {
    "ConfiguratorView.vue": "29670eb1148222bbc608a4d6d6797478b47f39bbcddbd483dda04b651fd8db1b",
    "ImportView.vue": "c76a02a1198b078819e78bb3b4cbc3dbfff09a4777205f02ff2973f85661c9cc",
    "ParametricView.vue": "141dc0cc7a5fb0173c3b06ed1128410ed72043626e14268660d1db666ff14f88",
    "WorkspaceView.vue": "329e1bd6525962bf57fda89f57f519796b12d6cf0fad10fd48c20a8f8aa879a0",
    "ps-vue-src/types/headstock.ts": "e1f41b9622ad77297c33f5fc75ac528db52b84f7e1bf06dbf5b8883a035253ee",
    "ps-vue-src/stores/headstock.ts": "d62da3602a738434df4e9fce8dd486c0f81ca7c1c4a4b2b3a8f75f7f88f22b62",
    "ps-vue-src/composables/useHeadstockPath.ts": "5a0be21190fc07b0dc989353ea97fa7693594d276c780c75d1ac14a87a9d43b6",
    "ps-vue-src/composables/useScoring.ts": "eb0011c0454134b9aaf08866214a9275ecf7113412b8d0ba9f2cc03b6fa3c440",
    "ps-vue-src/composables/useKonvaCanvas.ts": "1e981dc54266d2ffbfa8469c067b12a206da45077e67fb56e3931c9e2c05b867",
    "ps-vue-src/components/headstock/constants.ts": "176f80d84e845df6d0e1a9e6a347d55ac9011cf0287ad874bee0809a42f264bf",
}

EXPECTED_TYPE_ERRORS = [
    ("packages/client/src/composables/useDxfImport.ts", 124, "TS2339"),
    ("packages/client/src/composables/useDxfImport.ts", 168, "TS2769"),
    ("packages/client/src/composables/useDxfImport.ts", 180, "TS2353"),
    ("packages/client/src/composables/useDxfImport.ts", 198, "TS2353"),
    ("packages/client/src/composables/useDxfImport.ts", 207, "TS2353"),
    ("packages/client/src/composables/useExportDxf.ts", 34, "TS2339"),
    ("packages/client/src/composables/useExportDxf.ts", 37, "TS2339"),
    ("packages/client/src/composables/useExportDxf.ts", 38, "TS2339"),
    ("packages/client/src/composables/useExportDxf.ts", 39, "TS2339"),
    ("packages/client/src/composables/useExportDxf.ts", 40, "TS2339"),
    ("packages/client/src/composables/useExportDxf.ts", 74, "TS2339"),
]

DEFINITION_FILES = {
    "useExportDxf": "packages/client/src/composables/useExportDxf.ts",
    "useCamSpec": "packages/client/src/design-utilities/lutherie/neck/useCamSpec.ts",
}


def _inventory() -> dict:
    return json.loads((EVIDENCE / "inventory.json").read_text(encoding="utf-8"))


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _code(text: str) -> str:
    return _COMMENT.sub("", text)


def test_inventory_names_one_design_only_cluster():
    data = _inventory()
    rec = data["recommendation"]
    assert data["order"] == "HEADSTOCK-INTEGRATION-FEASIBILITY-002"
    assert data["measured_against"] == "4837c500d7f1fa4756c0ea365396478796887582"
    assert data["provisional_destination"].endswith("HeadstockDesignerView.vue")
    assert data["provisional_route"] == "/art-studio/headstock"
    assert rec == {
        "outcome": "port",
        "cluster_id": "parametric-outline-preview",
        "manufacturing": False,
        "destination": data["provisional_destination"],
        "restores_archived_application": False,
    }
    assert data["use_headstock"]["classification"] == "NOT_RECOVERED_GENERATION_UNKNOWN"
    assert [item["name"] for item in data["use_headstock"]["exports"]] == [
        "drawBackground",
        "drawHeadstock",
        "createInlayGroup",
        "exportWorkspaceSVG",
    ]
    assert data["konva"]["implements_four_exports"] is False
    assert data["konva"]["classification"] == "PARTIAL_RECONSTRUCTION_INPUT"


def test_scoring_selects_only_the_cluster_that_clears():
    scores = _inventory()["scores"]
    for row in scores:
        assert row["total"] == (
            row["complete"] + row["fit"] + row["independent"]
            + row["no_manufacturing"] + row["testable"] + row["value"]
        )

    def clears(row: dict) -> bool:
        return (
            row["complete"] >= 4
            and row["independent"] == 5
            and row["no_manufacturing"] == 5
        )

    clearing = [row for row in scores if clears(row)]
    selected = [row for row in scores if row["selected"]]
    assert [row["cluster_id"] for row in selected] == ["parametric-outline-preview"]
    assert selected[0]["total"] == max(row["total"] for row in clearing)
    assert "interactive-inlay" in {row["cluster_id"] for row in scores}
    assert all(not row["selected"] for row in scores if row["cluster_id"] != "parametric-outline-preview")


def test_archive_hashes_match_the_inventory_and_the_bytes():
    recorded = _inventory()["archive_hashes_lf"]
    assert recorded == EXPECTED_LF_HASHES
    mismatched = [
        rel for rel, digest in EXPECTED_LF_HASHES.items()
        if _sha256_lf(SUITE / rel) != digest
    ]
    assert mismatched == []


def test_recovered_type_errors_stay_the_measured_eleven():
    rows = _inventory()["type_errors_exposed_by_recovered_types"]
    assert [
        (row["file"], row["line"], row["code"]) for row in rows
    ] == EXPECTED_TYPE_ERRORS
    assert _inventory()["vue_tsc"]["error_count"] == 94


def test_use_headstock_module_is_not_on_disk():
    hits = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in REPO_ROOT.rglob("useHeadstock.ts")
        if "node_modules" not in path.parts and ".git" not in path.parts
    ]
    assert hits == []
    assert not (CLIENT / "types" / "headstock.ts").exists()


def test_client_does_not_import_the_archived_suite():
    needle = "headstock-suite-refined"
    importers = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in CLIENT.rglob("*")
        if path.suffix in {".ts", ".vue", ".js"}
        and path.is_file()
        and needle in path.read_text(encoding="utf-8", errors="replace")
    ]
    assert importers == []


def test_routed_headstock_is_the_designer_and_dxf_composables_have_no_caller():
    router = (CLIENT / "router" / "index.ts").read_text(encoding="utf-8")
    assert 'path: "/art-studio/headstock"' in router
    assert 'path: "/art-studio/inlay-workspace"' in router
    headstock_route = router.split('path: "/art-studio/headstock"', 1)[1][:400]
    assert "HeadstockDesignerView.vue" in headstock_route
    assert "ArtStudioHeadstock.vue" not in router

    shell = (CLIENT / "views" / "art-studio" / "InlayWorkspaceShell.vue").read_text(encoding="utf-8")
    assert "useDxfImport()" in _code(shell)

    calls: list[str] = []
    for path in CLIENT.rglob("*"):
        if path.suffix not in {".ts", ".vue"} or not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        for match in _CALL.finditer(_code(path.read_text(encoding="utf-8", errors="replace"))):
            name = match.group(1)
            if rel != DEFINITION_FILES[name]:
                calls.append(f"{rel}: {name}")
    assert calls == []

    designer = (CLIENT / "views" / "art-studio" / "HeadstockDesignerView.vue").read_text(encoding="utf-8")
    assert "/api/export/headstock-dxf" not in designer
    assert "buildHeadstockPath" not in designer


def test_next_order_stays_unscheduled_and_manufacturing_free():
    order = (EVIDENCE / "NEXT_ORDER.md").read_text(encoding="utf-8")
    assert order.startswith("# Next order: HEADSTOCK-PARAMETRIC-OUTLINE-PREVIEW-003")
    assert "It is not the implementation." in order
    for forbidden in (
        "useHeadstock",
        "POST /api/export/headstock-dxf",
        "POST /api/dxf/spline/evaluate",
        "ArtStudioHeadstock.vue",
    ):
        assert forbidden in order
    manufacturing = [
        row["path"] for row in _inventory()["endpoints"] if row["kind"] == "manufacturing"
    ]
    assert "/api/export/headstock-dxf" in manufacturing
    assert "/api/dxf/spline/evaluate" in manufacturing
