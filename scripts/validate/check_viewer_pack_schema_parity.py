#!/usr/bin/env python3
"""
Check viewer_pack_v1 schema parity between tap_tone_pi and ToolBox.

This script verifies that the vendored schema in ToolBox matches
the canonical schema in tap_tone_pi.

Usage:
    # From ToolBox repo (checks against pinned hash):
    python scripts/validate/check_viewer_pack_schema_parity.py --mode check

    # Print current hash (for updating pin):
    python scripts/validate/check_viewer_pack_schema_parity.py --mode print

    # Compare two schema files directly:
    python scripts/validate/check_viewer_pack_schema_parity.py --mode compare \
        --source /path/to/tap_tone_pi/contracts/viewer_pack_v1.schema.json \
        --target /path/to/toolbox/contracts/viewer_pack_v1.schema.json

Exit codes:
    0 = parity OK (or print mode)
    1 = parity mismatch
    2 = runtime error
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Set


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Hash of canonical schema from tap_tone_pi
# Update this when the source schema changes intentionally
PINNED_SCHEMA_HASH = "644dfb421ae5e89d563da05b155d6f1bd16c9b55afdb3c0de4bd110492a92518"

# Repo-relative paths
TOOLBOX_SCHEMA_PATH = Path("contracts/viewer_pack_v1.schema.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_normalized_hash(schema_path: Path) -> str:
    """
    Compute a normalized hash of the schema.

    Normalization:
    - Parse as JSON
    - Remove vendoring metadata keys (_vendored_from, _vendored_note)
    - Serialize with sorted keys
    - Hash the result
    """
    content = schema_path.read_text(encoding="utf-8")
    schema = json.loads(content)

    # Remove ToolBox-specific vendoring metadata
    schema.pop("_vendored_from", None)
    schema.pop("_vendored_note", None)

    # Canonical JSON
    normalized = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_key_properties(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key structural properties for comparison."""
    props = schema.get("properties", {})
    defs = schema.get("$defs", {})

    return {
        "required": sorted(schema.get("required", [])),
        "additionalProperties": schema.get("additionalProperties"),
        "property_keys": sorted(props.keys()),
        "schema_version_const": props.get("schema_version", {}).get("const"),
        "schema_id_const": props.get("schema_id", {}).get("const"),
        "kind_enum": sorted(
            defs.get("fileEntry", {}).get("properties", {}).get("kind", {}).get("enum", [])
        ),
        "contents_required": sorted(
            props.get("contents", {}).get("required", [])
        ),
    }


def compare_schemas(source_path: Path, target_path: Path) -> Dict[str, Any]:
    """
    Compare two schema files structurally.

    Returns a dict with:
    - match: bool
    - source_hash: str
    - target_hash: str
    - differences: list of difference descriptions
    """
    source_content = source_path.read_text(encoding="utf-8")
    target_content = target_path.read_text(encoding="utf-8")

    source = json.loads(source_content)
    target = json.loads(target_content)

    # Remove vendoring metadata from target for comparison
    target.pop("_vendored_from", None)
    target.pop("_vendored_note", None)

    source_props = extract_key_properties(source)
    target_props = extract_key_properties(target)

    differences = []

    for key in set(source_props.keys()) | set(target_props.keys()):
        sv = source_props.get(key)
        tv = target_props.get(key)
        if sv != tv:
            differences.append({
                "property": key,
                "source": sv,
                "target": tv,
            })

    source_hash = compute_normalized_hash(source_path)
    target_hash = compute_normalized_hash(target_path)

    return {
        "match": len(differences) == 0 and source_hash == target_hash,
        "source_hash": source_hash,
        "target_hash": target_hash,
        "differences": differences,
    }


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace) -> int:
    """Check vendored schema against pinned hash."""
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = repo_root / TOOLBOX_SCHEMA_PATH

    if not schema_path.is_file():
        print(f"ERROR: Schema not found: {schema_path}", file=sys.stderr)
        return 2

    actual_hash = compute_normalized_hash(schema_path)

    if PINNED_SCHEMA_HASH == "REPLACE_ME_AFTER_FIRST_RUN":
        print(f"Schema hash: {actual_hash}")
        print(
            "\nPinned hash not set. Update PINNED_SCHEMA_HASH in this script to:",
            file=sys.stderr,
        )
        print(f'  PINNED_SCHEMA_HASH = "{actual_hash}"', file=sys.stderr)
        return 1

    if actual_hash != PINNED_SCHEMA_HASH:
        print(f"PARITY FAIL: Schema hash mismatch", file=sys.stderr)
        print(f"  pinned:  {PINNED_SCHEMA_HASH}", file=sys.stderr)
        print(f"  actual:  {actual_hash}", file=sys.stderr)
        print(
            "\nIf this change is intentional, update PINNED_SCHEMA_HASH.",
            file=sys.stderr,
        )
        return 1

    print(f"PARITY OK: Schema hash matches pinned value")
    print(f"  hash: {actual_hash[:16]}...")
    return 0


def cmd_print(args: argparse.Namespace) -> int:
    """Print current schema hash."""
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = repo_root / TOOLBOX_SCHEMA_PATH

    if not schema_path.is_file():
        print(f"ERROR: Schema not found: {schema_path}", file=sys.stderr)
        return 2

    actual_hash = compute_normalized_hash(schema_path)
    print(f"Schema: {schema_path}")
    print(f"Hash:   {actual_hash}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare two schema files."""
    source = Path(args.source)
    target = Path(args.target)

    if not source.is_file():
        print(f"ERROR: Source not found: {source}", file=sys.stderr)
        return 2
    if not target.is_file():
        print(f"ERROR: Target not found: {target}", file=sys.stderr)
        return 2

    result = compare_schemas(source, target)

    print(f"Source: {source}")
    print(f"Target: {target}")
    print(f"Source hash: {result['source_hash']}")
    print(f"Target hash: {result['target_hash']}")
    print()

    if result["match"]:
        print("MATCH: Schemas are equivalent")
        return 0
    else:
        print("MISMATCH: Schemas differ")
        for diff in result["differences"]:
            print(f"  - {diff['property']}:")
            print(f"      source: {diff['source']}")
            print(f"      target: {diff['target']}")
        return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check viewer_pack_v1 schema parity."
    )
    ap.add_argument(
        "--mode",
        choices=["check", "print", "compare"],
        default="check",
        help="Operation mode (default: check)",
    )
    ap.add_argument(
        "--source",
        help="Source schema path (for compare mode)",
    )
    ap.add_argument(
        "--target",
        help="Target schema path (for compare mode)",
    )
    args = ap.parse_args()

    if args.mode == "check":
        return cmd_check(args)
    elif args.mode == "print":
        return cmd_print(args)
    elif args.mode == "compare":
        if not args.source or not args.target:
            print("ERROR: --source and --target required for compare mode", file=sys.stderr)
            return 2
        return cmd_compare(args)
    else:
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
