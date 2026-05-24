#!/usr/bin/env python
"""
Generate Runtime Spine Manifest.

Sprint: MRP-5T
Usage: python generate_runtime_manifest.py [--output FILE] [--verbose]

Generates the complete runtime spine manifest with all contracts.
"""

import argparse
import json
import sys
from pathlib import Path

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))

from app.cam.runtime_manifest import (
    build_runtime_spine_manifest,
    manifest_to_json,
    compute_manifest_hash,
    get_version_info,
    ContractClassification,
)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Runtime Spine Manifest"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary instead of full manifest",
    )
    args = parser.parse_args()

    # Build manifest
    manifest = build_runtime_spine_manifest()

    if args.summary:
        print_summary(manifest, args.verbose)
        return 0

    # Generate JSON
    json_output = manifest_to_json(manifest, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json_output, encoding="utf-8")
        if args.verbose:
            print(f"[OK] Manifest written to: {output_path}")
            print(f"     Hash: {compute_manifest_hash(manifest)}")
            print(f"     Contracts: {manifest.total_contracts}")
    else:
        print(json_output)

    return 0


def print_summary(manifest, verbose: bool = False):
    """Print manifest summary."""
    version_info = get_version_info()

    print("=" * 60)
    print("RUNTIME SPINE MANIFEST SUMMARY")
    print("Sprint: MRP-5T")
    print("=" * 60)

    print("\n[Version Info]")
    print(f"    Runtime Spine Version: {version_info['runtime_spine_version']}")
    print(f"    Replay Bundle Schema:  {version_info['replay_bundle_schema_version']}")
    print(f"    Manifest Schema:       {version_info['manifest_schema_version']}")
    print(f"    Contract Freeze Date:  {version_info['contract_freeze_date']}")
    print(f"    Manifest Hash:         {compute_manifest_hash(manifest)}")

    print("\n[Contract Counts]")
    print(f"    Total Contracts:       {manifest.total_contracts}")
    print(f"    Governed (PUBLIC):     {len(manifest.governed_contracts)}")
    print(f"    Developer APIs:        {len(manifest.developer_apis)}")
    print(f"    Internal:              {len(manifest.internal_contracts)}")

    print("\n[Compatibility Status]")
    print(f"    Status: {manifest.compatibility_status}")

    if verbose:
        print("\n[Governed Contracts]")
        for c in manifest.governed_contracts:
            status = "[DEPRECATED]" if c.deprecated else "[STABLE]"
            print(f"    {status} {c.contract_name}")
            print(f"           -> {c.module_path}")
            if c.description:
                print(f"              {c.description}")

        print("\n[Developer APIs]")
        for c in manifest.developer_apis:
            print(f"    {c.contract_name}")
            print(f"           -> {c.module_path}")

        print("\n[Internal Contracts]")
        for c in manifest.internal_contracts:
            print(f"    {c.contract_name}")
            print(f"           -> {c.module_path}")

    # Check for deprecations
    deprecated = [c for c in manifest.governed_contracts if c.deprecated]
    if deprecated:
        print("\n[WARNING] Deprecated Contracts:")
        for c in deprecated:
            print(f"    {c.contract_name}: {c.deprecation_note}")

    # Check stability
    non_deterministic = [
        c for c in manifest.governed_contracts if not c.deterministic
    ]
    if non_deterministic:
        print("\n[WARNING] Non-Deterministic Governed Contracts:")
        for c in non_deterministic:
            print(f"    {c.contract_name}")

    non_replayable = [
        c for c in manifest.governed_contracts if not c.replay_safe
    ]
    if non_replayable:
        print("\n[WARNING] Non-Replayable Governed Contracts:")
        for c in non_replayable:
            print(f"    {c.contract_name}")

    print("\n" + "=" * 60)
    print("MANIFEST GENERATION: COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
