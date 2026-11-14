#!/usr/bin/env python3
"""Preservation tests for CLIENT-AXIOS-DORMANT-PRESERVATION-024.

The archive is provenance. These tests do not require a production file to
be deleted, and they do not treat a missing backend route as deletion authority.
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
SCRIPT = REPO / "scripts" / "investigations" / "client_axios_preservation.py"
INVENTORY = (
    REPO
    / "docs/investigations/client-axios-reachability-020_2026-11-10/AXIOS_IMPORT_INVENTORY.csv"
)
OVERLAY = INVENTORY.with_name("POST_AUDIT_RETIREMENTS.json")
ARCHIVE = REPO / "archive/experimental/2026-11/client-axios-dormant-capabilities"
LEDGER = REPO / "docs/investigations/client-axios-dormant-preservation-024/PRESERVATION_LEDGER.csv"
INDEX = ARCHIVE / "CAPABILITY_INDEX.md"
MATRIX = ARCHIVE / "ENDPOINT_MATRIX.csv"
PACKAGE = REPO / "packages" / "client" / "package.json"
LOCK = REPO / "packages" / "client" / "package-lock.json"
SRC = REPO / "packages" / "client" / "src"
sys.path.insert(0, str(SCRIPT.parent))
import client_axios_preservation as tool  # noqa: E402

SOURCE_COMMIT = "cfaf07751110d99b3539647e877c2ffd80f4f29c"
CANONICAL = "packages/client/src/components/art/rosette-compare/useRosetteCompareApi.ts"
ALLOWED_PREFIXES = (
    "archive/experimental/2026-11/client-axios-dormant-capabilities/",
    "docs/investigations/client-axios-dormant-preservation-024/",
    "docs/investigations/client-axios-reachability-020_2026-11-10/POST_AUDIT_RETIREMENTS.json",
    "scripts/investigations/client_axios_preservation.py",
    "scripts/ci/test_client_axios_preservation.py",
    "scripts/ci/test_client_axios_reachability.py",
    ".github/workflows/core_ci.yml",
    "SPRINTS.md",
    ".cbsp21/patches/client-axios-dormant-preservation-024.json",
)


def _plan() -> dict:
    if not hasattr(_plan, "cached"):
        _plan.cached = tool.build_plan(REPO, INVENTORY, None)  # type: ignore[attr-defined]
    return _plan.cached  # type: ignore[attr-defined]


def _git_bytes(rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"origin/main:{rel}"], cwd=REPO)


class EntryCensus(unittest.TestCase):
    def test_seventeen_importers_and_no_unresolved(self) -> None:
        plan = _plan()
        self.assertEqual(plan["importer_count"], 17)
        self.assertEqual(plan["effective_unresolved"], [])
        self.assertEqual(plan["axios_declared"], "^1.21.0")
        self.assertEqual(plan["source_commit"], SOURCE_COMMIT)
        self.assertIn(CANONICAL, plan["importers"])
        self.assertFalse(plan["production_files_retired"])
        self.assertFalse(plan["axios_removal_authorized"])
        self.assertFalse(plan["dormant_preserve_means_safe_to_delete"])
        client_text = "\n".join(
            path.read_text(encoding="utf-8", errors="surrogateescape")
            for path in SRC.rglob("*")
            if path.is_file() and path.suffix in {".ts", ".vue", ".js", ".mjs", ".cjs"}
        )
        self.assertNotIn("archive/experimental", client_text)

    def test_each_importer_is_in_exactly_one_cluster(self) -> None:
        owners: dict[str, str] = {}
        for item in _plan()["files"]:
            if item["role"] != "importer":
                continue
            self.assertNotIn(item["original_path"], owners)
            owners[item["original_path"]] = item["capability_cluster"]
        self.assertEqual(set(owners), set(_plan()["importers"]))
        self.assertEqual(len(owners), 17)

    def test_overlay_records_preservation_and_does_not_retire_production(self) -> None:
        before = json.loads(_git_bytes(OVERLAY.relative_to(REPO).as_posix()))
        after = json.loads(OVERLAY.read_text(encoding="utf-8"))
        self.assertEqual(before["retired_importers"], after["retired_importers"])
        self.assertEqual(before["reclassified_importers"], after["reclassified_importers"])
        self.assertEqual(before["post_audit_importers"], after["post_audit_importers"])
        preserved = after["preservation"]
        self.assertEqual(preserved["rosette_compare_merge_commit"], SOURCE_COMMIT)
        self.assertFalse(preserved["production_files_retired"])
        self.assertFalse(preserved["axios_removal_authorized"])
        retired = {item["path"] for item in after["retired_importers"]}
        for path in _plan()["importers"]:
            self.assertNotIn(path, retired)
            self.assertTrue((REPO / path).is_file())
        self.assertEqual(
            [item["path"] for item in after["reclassified_importers"]],
            [
                "packages/client/src/views/art/risk-dashboard/useRiskBuckets.ts",
                "packages/client/src/views/art/risk-dashboard/useRiskExports.ts",
                "packages/client/src/views/art/risk-dashboard/useRiskBucketDetails.ts",
                CANONICAL,
            ],
        )


class Integrity(unittest.TestCase):
    def test_archive_matches_source_manifest_and_git_blob(self) -> None:
        tool.verify_archive(REPO, ARCHIVE, _plan())
        manifest = json.loads((ARCHIVE / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest, json.loads(tool.render_manifest(_plan())))
        for item in manifest["files"]:
            original = (REPO / item["original_path"]).read_bytes()
            archived = (ARCHIVE / item["archive_path"]).read_bytes()
            self.assertEqual(archived, original)
            self.assertEqual(tool.sha256_bytes(archived), item["sha256"])
            self.assertEqual(tool.git_blob_sha1(archived), item["git_blob"])
            self.assertEqual(item["source_commit"], SOURCE_COMMIT)
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{SOURCE_COMMIT}:{item['original_path']}"],
                cwd=REPO,
                text=True,
            ).strip()
            self.assertEqual(blob, item["git_blob"])

    def test_manifest_is_byte_stable(self) -> None:
        plan = _plan()
        self.assertEqual(tool.render_manifest(plan), tool.render_manifest(plan))
        self.assertEqual(tool.render_endpoint_matrix(), tool.render_endpoint_matrix())
        self.assertEqual(tool.render_ledger(plan), tool.render_ledger(plan))
        self.assertEqual(tool.render_capability_index(plan), tool.render_capability_index(plan))
        self.assertEqual((ARCHIVE / "CAPABILITY_INDEX.md").read_text(encoding="utf-8"), tool.render_capability_index(plan))
        self.assertEqual(MATRIX.read_text(encoding="utf-8"), tool.render_endpoint_matrix())
        self.assertEqual(LEDGER.read_text(encoding="utf-8"), tool.render_ledger(plan))

    def test_crlf_and_non_ascii_keep_original_bytes(self) -> None:
        raw = "café line\r\nsecond\r\n".encode("utf-8")
        self.assertIn(b"\r\n", raw)
        self.assertIn("é".encode("utf-8"), raw)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "source.txt"
            dest = root / "nested" / "copy.txt"
            src.write_bytes(raw)
            tool.copy_bytes(src, dest)
            self.assertEqual(dest.read_bytes(), raw)
            self.assertEqual(tool.sha256_bytes(dest.read_bytes()), tool.sha256_bytes(raw))

    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "archive"
            before = list(Path(tmp).rglob("*"))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(REPO),
                    "--inventory",
                    str(INVENTORY),
                    "--archive-root",
                    str(dest),
                    "--dry-run",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("dry-run: no files written", completed.stdout)
            self.assertFalse(dest.exists())
            self.assertEqual(list(Path(tmp).rglob("*")), before)

    def test_missing_path_and_ambiguous_path_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(tool.PreservationError) as missing:
                tool._validate_closure(Path(tmp), tool.clusters())
            self.assertIn("missing path", str(missing.exception))
        with self.assertRaises(tool.PreservationError) as ambiguous:
            tool.assert_no_ambiguous_paths(["packages/client/src/api/n15.ts", "packages/client/src/api/n15.ts"])
        self.assertIn("ambiguous", str(ambiguous.exception))

    def test_archive_inside_client_source_is_rejected_and_not_created(self) -> None:
        dest = SRC / "__preservation_reject_destination"
        self.assertFalse(dest.exists())
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(REPO),
                "--inventory",
                str(INVENTORY),
                "--archive-root",
                str(dest),
                "--dry-run",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2, completed.stdout)
        self.assertIn("inside production client source", completed.stderr)
        self.assertFalse(dest.exists())

    def test_write_without_destination_is_rejected(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(REPO),
                "--inventory",
                str(INVENTORY),
                "--write-manifest",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2, completed.stdout)
        self.assertIn("without --archive-root", completed.stderr)


class Closure(unittest.TestCase):
    def test_direct_callers_are_archived_or_excluded(self) -> None:
        plan = _plan()
        archived = {item["original_path"] for item in plan["files"]}
        excluded = {
            (item["capability_cluster"], item["path"])
            for item in plan["exclusions"]
            if item["kind"] == "caller"
        }
        for item in plan["files"]:
            for caller in item["known_callers"]:
                path = caller["path"]
                if path in archived and any(
                    other["original_path"] == path and other["capability_cluster"] == item["capability_cluster"]
                    for other in plan["files"]
                ):
                    self.assertEqual(caller["included"], "archived")
                    continue
                self.assertEqual(caller["included"], "excluded")
                self.assertTrue(caller["reason"].strip())
                self.assertIn((item["capability_cluster"], path), excluded)

    def test_endpoint_matrix_covers_axios_operations_and_distinct_contracts(self) -> None:
        with MATRIX.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        with INVENTORY.open(encoding="utf-8", newline="") as handle:
            inventory = list(csv.DictReader(handle))
        by_path: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            by_path.setdefault(row["production_path"], []).append(row)
            self.assertEqual(row["deletion_authority"], "false")
            if row["canonical_production_path"]:
                self.assertTrue((REPO / row["canonical_production_path"]).is_file(), row["canonical_production_path"])
        current = set(_plan()["importers"])
        for item in inventory:
            if item["path"] not in current:
                continue
            endpoints = {row["endpoint"] for row in by_path[item["path"]]}
            for literal in (part.strip() for part in item["endpoint_literals"].split(";")):
                self.assertTrue(
                    any(literal == endpoint or endpoint.startswith(literal) for endpoint in endpoints),
                    f"{item['path']} missing {literal}",
                )
        contracts = {row["contract"] for row in rows}
        self.assertIn("compare-lab", contracts)
        self.assertIn("rosette-baseline-diff", contracts)
        self.assertIn("rosette-compare-history", contracts)
        self.assertIn("art-rosette-history", contracts)
        lab_paths = {row["production_path"] for row in rows if row["contract"] == "compare-lab"}
        self.assertIn("packages/client/src/composables/useCompareState.ts", lab_paths)
        self.assertNotIn(CANONICAL, lab_paths)
        history_paths = {row["production_path"] for row in rows if row["contract"] == "rosette-compare-history"}
        baseline_paths = {row["production_path"] for row in rows if row["contract"] == "rosette-baseline-diff"}
        self.assertTrue(history_paths.isdisjoint(baseline_paths))
        self.assertEqual(
            tool.preservation_status_for_route(False),
            "PRESERVED_COPY_PRODUCTION_RETAINED",
        )
        self.assertEqual(
            tool.preservation_status_for_route(None),
            tool.preservation_status_for_route(True),
        )

    def test_ledger_has_one_row_per_importer(self) -> None:
        with LEDGER.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([row["path"] for row in rows], _plan()["importers"])
        for row in rows:
            self.assertEqual(row["preservation_status"], "PRESERVED_COPY_PRODUCTION_RETAINED")
            self.assertIn(row["path"], row["archive_closure"].split(";"))
            self.assertTrue(row["next_adjudication"].strip())
            if "CANONICAL_BUT_UNROUTED" in row["disposition"]:
                self.assertTrue((REPO / row["path"]).is_file())


class Boundary(unittest.TestCase):
    def test_production_client_router_and_inventory_are_unchanged(self) -> None:
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", "origin/main"],
            cwd=REPO,
            text=True,
        ).splitlines()
        untracked = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=REPO,
            text=True,
        ).splitlines()
        touched = changed + untracked
        for path in touched:
            self.assertTrue(
                any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PREFIXES),
                path,
            )
        self.assertEqual(PACKAGE.read_bytes(), _git_bytes("packages/client/package.json"))
        self.assertEqual(LOCK.read_bytes(), _git_bytes("packages/client/package-lock.json"))
        self.assertEqual(
            (SRC / "router/index.ts").read_bytes(),
            _git_bytes("packages/client/src/router/index.ts"),
        )
        self.assertEqual(INVENTORY.read_bytes(), _git_bytes(INVENTORY.relative_to(REPO).as_posix()))
        self.assertFalse(any(path.startswith("packages/client/") for path in touched))
        self.assertTrue(INDEX.is_file())
        self.assertIn(SOURCE_COMMIT, INDEX.read_text(encoding="utf-8"))
        self.assertIn("does not mean safe to delete", (ARCHIVE / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
