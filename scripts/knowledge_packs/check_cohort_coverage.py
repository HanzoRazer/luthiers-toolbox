#!/usr/bin/env python3
"""Fail if knowledge packs are incomplete, unfiled, or missing from CBSP21 / catalog.

Anti-sandbox-floor gate for physics + shop cohorts.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACOUSTICS = ROOT / "docs" / "calculators" / "acoustics"
CATALOG = ACOUSTICS / "cohort_catalog.json"
CBSP21 = ROOT / ".cbsp21" / "patches" / "gore-lecture-series-packs-1-5.json"
ORIENT = ACOUSTICS / "KNOWLEDGE_PACK_DEVELOPER_ORIENTATION.md"

REQUIRED = [
    "README.md",
    "SOURCE_TRANSCRIPT.md",
    "CROSSWALK_TOOLBOX.md",
    "GAPS_NOT_RECORDED.md",
]


def main() -> int:
    # ensure catalog fresh
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_cohort_catalog import main as rebuild

    rebuild()
    catalog = json.loads(CATALOG.read_text())
    cbsp = json.loads(CBSP21.read_text())
    cbsp_files = set(cbsp["scope"]["files_expected_to_change"])
    ori = ORIENT.read_text()

    errors: list[str] = []
    warnings: list[str] = []

    if catalog["counts"]["unfiled"]:
        for p in catalog["packs"]:
            if "unfiled" in p["lane"]:
                errors.append(f"UNFILED lane: {p['pack_id']} (add to PHYSICS_ or SHOP_ index)")

    for p in catalog["packs"]:
        pid = p["pack_id"]
        if p["missing_template_files"]:
            errors.append(
                f"TEMPLATE incomplete: {pid} missing {p['missing_template_files']}"
            )
        if p["point_count"] == 0:
            errors.append(f"NO POINT IDs: {pid} annotated notes have zero extractable IDs")
        for pref in p["point_prefix"]:
            if pref not in catalog["known_point_prefixes"]:
                errors.append(
                    f"UNKNOWN PREFIX {pref} in {pid} — register in orientation + build_cohort_catalog.KNOWN_PREFIX"
                )
            listed = (
                f"| {pref} |" in ori
                or f"| {pref}-* |" in ori
                or f"`{pref}`" in ori
                or (pref == "G" and "G-*" in ori)
            )
            if not listed:
                warnings.append(
                    f"Prefix {pref} ({pid}) not listed in KNOWLEDGE_PACK_DEVELOPER_ORIENTATION namespaces"
                )
        # CBSP21: every pack file under template must be listed
        pack_dir = ROOT / p["path"]
        for fp in pack_dir.iterdir():
            if not fp.is_file() or fp.name.startswith("."):
                continue
            rel = str(fp.relative_to(ROOT))
            if rel not in cbsp_files:
                errors.append(f"CBSP21 missing file: {rel}")

    # catalog itself + search index + governance must be in CBSP21
    for rel in (
        "docs/calculators/acoustics/cohort_catalog.json",
        "docs/calculators/acoustics/POINT_SEARCH_INDEX.md",
        "docs/calculators/acoustics/COHORT_GOVERNANCE.md",
        "scripts/knowledge_packs/build_cohort_catalog.py",
        "scripts/knowledge_packs/check_cohort_coverage.py",
    ):
        if rel not in cbsp_files and Path(ROOT / rel).exists():
            errors.append(f"CBSP21 missing governance artifact: {rel}")

    # orphan: CBSP21 acoustics pack paths that don't exist
    for rel in sorted(cbsp_files):
        if not rel.startswith("docs/calculators/acoustics/"):
            continue
        if rel.endswith(".md") or rel.endswith(".json"):
            if not (ROOT / rel).exists():
                errors.append(f"CBSP21 lists missing path: {rel}")

    print(
        f"cohort check: {catalog['counts']['packs']} packs, "
        f"{catalog['counts']['points']} points"
    )
    for w in warnings:
        print("WARN:", w)
    if errors:
        print("FAIL:")
        for e in errors:
            print(" -", e)
        return 1
    print("COHORT COVERAGE: PASS — floor held (annotated + searchable + CBSP21)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
