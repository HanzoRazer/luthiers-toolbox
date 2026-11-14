#!/usr/bin/env python3
"""Reachability evidence tests for CLIENT-AXIOS-REACHABILITY-020.

The scanner reports import facts. These tests pin that behavior and check
the investigation inventory. They do not decide that a file may be deleted.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "investigations" / "client_axios_reachability.py"
INVENTORY_DIR = REPO / "docs" / "investigations" / "client-axios-reachability-020_2026-11-10"
INVENTORY = INVENTORY_DIR / "AXIOS_IMPORT_INVENTORY.csv"
RETIREMENTS = INVENTORY_DIR / "POST_AUDIT_RETIREMENTS.json"
PRESERVATION = INVENTORY_DIR / "PRESERVATION_MAP.md"
LINEAGE_EVIDENCE = (
    REPO / "docs/investigations/client-risk-dashboard-lineage-021_2026-11-10/evidence.json"
)
PANEL_IMPORTER = "packages/client/src/components/art/RosetteComparePanel.vue"
CANONICAL_ROSETTE = "packages/client/src/components/art/rosette-compare/useRosetteCompareApi.ts"
# SHA-256 of the panel while it still imported Axios. The file remains; the import does not.
PANEL_AXIOS_SHA256 = "37d4b02e3bdb25820b7701ad111d9c97289fcdfd276164284d98ac550fb802fc"
# Specs that import Axios only to mock it. They are not rows in the 20-row audit.
CHARACTERIZATION_MOCKS = {
    "packages/client/src/components/art/__tests__/RosetteComparePanel.spec.ts",
    "packages/client/src/components/art/rosette-compare/__tests__/useRosetteCompareApi.spec.ts",
    "packages/client/src/views/art/__tests__/RiskDashboardCrossLab.spec.ts",
    "packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardDecomposed.spec.ts",
    "packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardRequestOrder.spec.ts",
}
PACKAGE = REPO / "packages" / "client" / "package.json"
SRC = REPO / "packages" / "client" / "src"
sys.path.insert(0, str(SCRIPT.parent))
import client_axios_reachability as scan  # noqa: E402

ALLOWED = {
    "LIVE_REPLACE",
    "DORMANT_PRESERVE",
    "SUPERSEDED_REMOVE",
    "ORPHAN_REMOVE",
    "UNRESOLVED",
}
COLUMNS = [
    "path",
    "exported_symbols",
    "axios_operations",
    "endpoint_literals",
    "direct_callers",
    "router_or_entrypoint_path",
    "dynamic_import_path",
    "test_coverage",
    "history_origin",
    "archive_match",
    "canonical_equivalent",
    "unique_capability",
    "disposition",
    "evidence",
    "reviewer",
]


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ReachabilityFixtures(unittest.TestCase):
    def test_static_importer_reachable_from_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "main.ts", "import { ping } from './api/ping'\n")
            _write(src, "api/ping.ts", "import axios from 'axios'\nexport function ping() { return axios.get('/ping') }\n")
            payload = scan.analyze(src, ["main.ts"])
            self.assertEqual(payload["axios_importers"], ["api/ping.ts"])
            self.assertTrue(payload["importers"][0]["binding_reachable"])

    def test_lazy_router_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "router/index.ts", "export const routes = [{ component: () => import('./views/Page.vue') }]\n")
            _write(src, "router/views/Page.vue", "<script setup lang=\"ts\">\nimport { ping } from '../api/ping'\n</script>\n")
            _write(src, "router/api/ping.ts", "import axios from 'axios'\nexport function ping() { return axios.get('/ping') }\n")
            payload = scan.analyze(src, ["router/index.ts"])
            self.assertTrue(payload["importers"][0]["binding_reachable"])

    def test_vue_component_imported_by_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "App.vue", "<script setup lang=\"ts\">\nimport Child from './Child.vue'\n</script>\n")
            _write(src, "Child.vue", "<script setup lang=\"ts\">\nimport axios from 'axios'\n</script>\n")
            payload = scan.analyze(src, ["App.vue"])
            self.assertEqual(payload["axios_importers"], ["Child.vue"])
            self.assertTrue(payload["importers"][0]["binding_reachable"])

    def test_alias_import_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "main.ts", "import { ping } from '@/api/ping'\n")
            _write(src, "api/ping.ts", "import axios from 'axios'\nexport function ping() { return axios.get('/ping') }\n")
            payload = scan.analyze(src, ["main.ts"])
            self.assertTrue(payload["importers"][0]["binding_reachable"])
            self.assertEqual(payload["unresolved_imports"], [])

    def test_type_only_import_is_not_runtime_reachability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "main.ts", "import type { Shape } from './api/types'\n")
            _write(src, "api/types.ts", "import axios from 'axios'\nexport interface Shape { id: string }\n")
            payload = scan.analyze(src, ["main.ts"])
            self.assertFalse(payload["importers"][0]["binding_reachable"])
            self.assertFalse(payload["importers"][0]["evaluated_reachable"])

    def test_comment_and_string_are_not_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(
                src,
                "main.ts",
                "\n".join([
                    "// import axios from 'axios'",
                    "const sample = \"import axios from 'axios'\"",
                    "const ghost = \"import('./missing-file')\"",
                    "export const ready = true",
                    "",
                ]),
            )
            payload = scan.analyze(src, ["main.ts"])
            self.assertEqual(payload["axios_importers"], [])
            self.assertEqual(payload["unresolved_imports"], [])

    def test_missing_target_is_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "main.ts", "import { missing } from './missing'\n")
            payload = scan.analyze(src, ["main.ts"])
            self.assertEqual(payload["unresolved_imports"], [{"from": "main.ts", "specifier": "./missing"}])

    def test_import_cycle_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "main.ts", "import { fromA } from './a'\n")
            _write(src, "a.ts", "import axios from 'axios'\nimport { fromB } from './b'\nexport function fromA() { return fromB() }\n")
            _write(src, "b.ts", "import axios from 'axios'\nimport { fromA } from './a'\nexport function fromB() { return fromA() }\n")
            first = scan.analyze(src, ["main.ts"])
            second = scan.analyze(src, ["main.ts"])
            self.assertEqual(first, second)
            self.assertEqual(
                [row["path"] for row in first["importers"]],
                ["a.ts", "b.ts"],
            )
            self.assertTrue(all(row["binding_reachable"] for row in first["importers"]))

    def test_output_is_stable_under_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "main.ts", "import { zed } from './zed'\nimport { alpha } from './alpha'\n")
            _write(src, "zed.ts", "import axios from 'axios'\nexport function zed() { return axios.post('/z') }\n")
            _write(src, "alpha.ts", "import axios from 'axios'\nexport function alpha() { return axios.get('/a') }\n")
            payload = scan.analyze(src, ["main.ts"])
            again = scan.analyze(src, ["main.ts"])
            text = json.dumps(payload, indent=2, sort_keys=True)
            self.assertEqual(payload, again)
            self.assertEqual(text, json.dumps(json.loads(text), indent=2, sort_keys=True))
            self.assertEqual([row["path"] for row in payload["importers"]], ["alpha.ts", "zed.ts"])

    def test_known_live_barrel_is_not_classified_unreachable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "main.ts", "import { liveCall } from './barrel'\n")
            _write(src, "barrel.ts", "export * from './live'\nexport * from './dormant'\n")
            _write(src, "live.ts", "import axios from 'axios'\nexport function liveCall() { return axios.get('/live') }\n")
            _write(src, "dormant.ts", "import axios from 'axios'\nexport function dormantCall() { return axios.get('/dormant') }\n")
            payload = scan.analyze(src, ["main.ts"])
            by_path = {row["path"]: row for row in payload["importers"]}
            self.assertTrue(by_path["live.ts"]["binding_reachable"])
            self.assertFalse(by_path["dormant.ts"]["binding_reachable"])
            self.assertTrue(by_path["dormant.ts"]["evaluated_reachable"])

    def test_every_resolvable_extension_is_discovered(self) -> None:
        # Resolution accepts .jsx/.mjs/.cjs; discovery must too, or a module the
        # resolver finds silently drops out of the walk and out of the importers.
        for ext in (".jsx", ".mjs", ".cjs"):
            with self.subTest(ext=ext), tempfile.TemporaryDirectory() as tmp:
                src = Path(tmp)
                _write(src, "main.ts", "import { ping } from './api/ping'\n")
                _write(src, f"api/ping{ext}", "import axios from 'axios'\nexport function ping() { return axios.get('/ping') }\n")
                payload = scan.analyze(src, ["main.ts"])
                self.assertEqual(payload["axios_importers"], [f"api/ping{ext}"])
                self.assertTrue(payload["importers"][0]["binding_reachable"])

    def test_barrel_side_effect_import_runs_with_binding_import(self) -> None:
        # main.ts only demands `ping`, which the barrel re-exports from elsewhere.
        # The barrel is still evaluated, so its bare side-effect import runs.
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "main.ts", "import { ping } from './api'\n")
            _write(src, "api/index.ts", "import './interceptors'\nexport { ping } from './ping'\n")
            _write(src, "api/ping.ts", "export function ping() { return 1 }\n")
            _write(src, "api/interceptors.ts", "import axios from 'axios'\naxios.interceptors.request.use((c) => c)\n")
            payload = scan.analyze(src, ["main.ts"])
            self.assertEqual(payload["axios_importers"], ["api/interceptors.ts"])
            self.assertTrue(payload["importers"][0]["binding_reachable"])

    def test_axios_reexport_and_subpath_count_as_importers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            _write(src, "http.ts", "export { default as http } from 'axios'\n")
            _write(src, "star.ts", "export * from 'axios'\n")
            _write(src, "sub.ts", "import { AxiosHeaders } from 'axios/index.js'\nexport const h = AxiosHeaders\n")
            _write(src, "req.js", "const a = require('axios/dist/node/axios.cjs')\n")
            _write(src, "unrelated.ts", "import x from 'axios-retry'\nexport const y = x\n")
            self.assertEqual(
                scan.axios_importers(src),
                ["http.ts", "req.js", "star.ts", "sub.ts"],
            )


def _inventory_rows() -> list[dict[str, str]]:
    with INVENTORY.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _retirements() -> dict:
    return json.loads(RETIREMENTS.read_text(encoding="utf-8"))


def expected_importers(rows: list[dict[str, str]], retirements: dict) -> list[str]:
    retired = {item["path"] for item in retirements["retired_importers"]}
    extra = set(retirements.get("post_audit_importers") or [])
    return sorted(({row["path"] for row in rows} - retired) | extra)


def effective_unresolved(rows: list[dict[str, str]], retirements: dict) -> list[str]:
    retired = {item["path"] for item in retirements["retired_importers"]}
    reclassified = {item["path"] for item in retirements["reclassified_importers"]}
    return sorted(
        row["path"]
        for row in rows
        if row["disposition"] == "UNRESOLVED"
        and row["path"] not in retired
        and row["path"] not in reclassified
    )


class InventoryIntegrity(unittest.TestCase):
    def test_inventory_matches_scanned_importers_exactly_once(self) -> None:
        scanned = [f"packages/client/src/{rel}" for rel in scan.axios_importers(SRC)]
        rows = _inventory_rows()
        retirements = _retirements()
        paths = [row["path"] for row in rows]
        expected = expected_importers(rows, retirements)
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(rows), 20)
        self.assertEqual(set(scanned) - set(expected), CHARACTERIZATION_MOCKS)
        self.assertEqual(set(expected) - set(scanned), set())
        self.assertEqual(len(expected), 17)
        self.assertGreater(len(expected), 0)

    def test_every_row_has_one_allowed_disposition_and_no_blanks(self) -> None:
        with INVENTORY.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(list(rows[0].keys()), COLUMNS)
        for row in rows:
            for column in COLUMNS:
                self.assertTrue(row[column].strip(), f"{row['path']} blank {column}")
            self.assertIn(row["disposition"], ALLOWED)
            if row["disposition"] == "LIVE_REPLACE":
                self.assertNotIn(row["canonical_equivalent"], {"", "none"})
            if row["disposition"] == "SUPERSEDED_REMOVE":
                self.assertNotIn(row["canonical_equivalent"], {"", "none"})
            if row["disposition"] == "DORMANT_PRESERVE":
                self.assertIn("preservation_target=", row["evidence"])
                self.assertNotEqual(row["history_origin"], "none")
                self.assertIn(row["path"], PRESERVATION.read_text(encoding="utf-8"))

    def test_post_audit_retirements_name_replacements_and_drop_the_paths(self) -> None:
        rows = _inventory_rows()
        retirements = _retirements()
        evidence = {
            item["path"]: item["sha256"]
            for item in json.loads(LINEAGE_EVIDENCE.read_text(encoding="utf-8"))["sources"]
        }
        retired_paths = []
        for item in retirements["retired_importers"]:
            retired_paths.append(item["path"])
            self.assertTrue(item["canonical_replacement"].strip())
            self.assertNotEqual(item["canonical_replacement"], item["path"])
            self.assertTrue(item["reason"].strip())
            self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue((REPO / item["canonical_replacement"]).is_file())
            if item["path"] == PANEL_IMPORTER:
                self.assertEqual(item["reconciliation_order"], "CLIENT-ROSETTE-COMPARE-RECONCILE-023")
                self.assertEqual(item["sha256"], PANEL_AXIOS_SHA256)
                self.assertEqual(item["canonical_replacement"], CANONICAL_ROSETTE)
                panel = (REPO / item["path"]).read_text(encoding="utf-8")
                self.assertNotIn("from 'axios'", panel)
                self.assertNotIn('from "axios"', panel)
                self.assertNotRegex(panel, r"\baxios\.")
                self.assertIn("useRosetteCompareApi", panel)
                continue
            self.assertEqual(item["reconciliation_order"], "CLIENT-RISK-DASHBOARD-RECONCILE-022")
            self.assertEqual(item["sha256"], evidence[item["path"]])
            self.assertFalse((REPO / item["path"]).exists(), item["path"])
        self.assertEqual(len(retired_paths), len(set(retired_paths)))
        reclassified = retirements["reclassified_importers"]
        self.assertEqual(
            [item["path"] for item in reclassified],
            [
                "packages/client/src/views/art/risk-dashboard/useRiskBuckets.ts",
                "packages/client/src/views/art/risk-dashboard/useRiskExports.ts",
                "packages/client/src/views/art/risk-dashboard/useRiskBucketDetails.ts",
                CANONICAL_ROSETTE,
            ],
        )
        for item in reclassified:
            self.assertEqual(item["disposition"], "DORMANT_PRESERVE — CANONICAL_BUT_UNROUTED")
            self.assertTrue((REPO / item["path"]).is_file())
        scanned = {f"packages/client/src/{rel}" for rel in scan.axios_importers(SRC)}
        self.assertTrue(set(item["path"] for item in reclassified) <= scanned)
        self.assertTrue(set(retirements.get("post_audit_importers") or []).issubset(scanned))

    def test_unresolved_blocks_dependency_removal(self) -> None:
        # One-directional: removing Axios requires zero effective UNRESOLVED
        # rows. The original inventory stays intact. Rosette Compare is no
        # longer unresolved in the overlay. The raw CSV still marks that pair
        # UNRESOLVED, so the removal branch below still fails a deletion.
        # Dormant-preserve importers also remain. Axios stays declared.
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        declared = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
        rows = _inventory_rows()
        unresolved = [row["path"] for row in rows if row["disposition"] == "UNRESOLVED"]
        current = effective_unresolved(rows, _retirements())
        self.assertEqual(current, [])
        self.assertIn("axios", declared)
        self.assertEqual(declared["axios"], "^1.21.0")
        if "axios" not in declared:
            self.assertEqual(unresolved, [], "a removal PR cannot contain UNRESOLVED")
            self.assertEqual(current, [], "a removal PR cannot leave Rosette Compare unresolved")

    def test_cli_writes_only_the_requested_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            out = Path(tmp) / "out" / "reach.json"
            _write(src, "main.ts", "export const ready = true\n")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--src", str(src), "--output", str(out)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(out.is_file())
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["axios_importers"], [])
            written = sorted(path.relative_to(tmp).as_posix() for path in Path(tmp).rglob("*") if path.is_file())
            self.assertEqual(written, ["out/reach.json", "src/main.ts"])


if __name__ == "__main__":
    unittest.main()
