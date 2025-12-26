#!/usr/bin/env python3
"""
CLI tool for importing an acoustics bundle package into RMOS runs_v2 store.

Usage:
    python -m app.rmos.acoustics.cli_import_package /path/to/package

The package directory is expected to contain:
    - manifest.json
    - attachments/  (directory with files referenced in manifest)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .schemas_manifest_v1 import TapToneBundleManifestV1
from .importer import import_acoustics_bundle
from .persist_glue import persist_import_plan, _json_load


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import an acoustics bundle package into RMOS runs_v2 store."
    )
    parser.add_argument(
        "package_path",
        type=Path,
        help="Path to the package directory containing manifest.json and attachments/",
    )
    parser.add_argument(
        "--status",
        default="completed",
        help="Run status (default: completed)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate only; do not persist.",
    )
    args = parser.parse_args(argv)

    package_root: Path = args.package_path.expanduser().resolve()
    manifest_path = package_root / "manifest.json"

    if not manifest_path.exists():
        print(f"ERROR: manifest.json not found at {manifest_path}", file=sys.stderr)
        return 1

    # Load and validate manifest
    try:
        manifest = TapToneBundleManifestV1.model_validate(_json_load(manifest_path))
    except Exception as e:
        print(f"ERROR: Failed to parse manifest: {e}", file=sys.stderr)
        return 1

    print(f"Loaded manifest: bundle_id={manifest.bundle_id}")
    print(f"  Files: {len(manifest.files)}")
    print(f"  Instrument: {manifest.instrument.instrument_id if manifest.instrument else 'N/A'}")

    # Build import plan
    plan = import_acoustics_bundle(manifest)
    print(f"Import plan: {len(plan.attachments)} attachments")

    if args.dry_run:
        print("Dry run complete. No files persisted.")
        return 0

    # Persist
    try:
        result = persist_import_plan(
            plan=plan,
            package_root=package_root,
            manifest=manifest,
            status=args.status,
        )
    except Exception as e:
        print(f"ERROR: Persist failed: {e}", file=sys.stderr)
        return 1

    print(f"Persisted run: {result.run_id}")
    print(f"  Run JSON: {result.run_json_path}")
    print(f"  Attachments written: {result.attachments_written}")
    print(f"  Attachments deduped: {result.attachments_deduped}")
    print(f"  Index updated: {result.index_updated}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
