"""
Verify RMOS runs_v2 store integrity.

Checks:
- Index file (_index.json) exists and is readable
- Every run_id in index has a corresponding partition/{run_id}.json
- Optional: artifacts deserialize as RunArtifact (schema validation)

Run:
  cd services/api
  python -m app.rmos.runs_v2.verify_store
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .store import RunStoreV2, _get_store_root
from .schemas import RunArtifact


def _is_tombstone(meta: dict) -> bool:
    """Check if an index entry is a soft-deleted tombstone."""
    return bool(meta.get("deleted") or meta.get("_deleted"))


def verify(
    *,
    store_root: Optional[str] = None,
    strict_deserialize: bool = True,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify the split store integrity.

    Args:
        store_root: Optional custom store root path
        strict_deserialize: If True, validates each artifact deserializes correctly

    Returns:
        (ok, report) tuple where ok is False if any issues found
    """
    store = RunStoreV2(root_dir=store_root)

    # Check if index exists
    index_exists = store._index_path.exists()
    if not index_exists:
        # Try to rebuild from partitions
        count = store.rebuild_index()
        index_exists = store._index_path.exists()

    index = store._read_index()
    run_ids: List[str] = list(index.keys())

    missing_artifacts: List[str] = []
    deserialize_failures: List[Dict[str, str]] = []
    partition_mismatches: List[Dict[str, str]] = []
    tombstone_count: int = 0

    for run_id, meta in index.items():
        # H3.6.2: Skip tombstones - soft-deleted runs don't require artifact files
        if _is_tombstone(meta):
            tombstone_count += 1
            continue

        partition = meta.get("partition")
        if not partition:
            partition_mismatches.append({
                "run_id": run_id,
                "error": "No partition in index metadata"
            })
            continue

        # Check artifact file exists
        safe_id = run_id.replace("/", "_").replace("\\", "_")
        artifact_path = store.root / partition / f"{safe_id}.json"

        if not artifact_path.exists():
            missing_artifacts.append(run_id)
            continue

        if strict_deserialize:
            try:
                data = json.loads(artifact_path.read_text(encoding="utf-8"))
                RunArtifact.model_validate(data)
            except (OSError, json.JSONDecodeError, ValueError) as e:  # WP-1: narrowed from except Exception
                deserialize_failures.append({
                    "run_id": run_id,
                    "error": repr(e)
                })

    ok = (
        len(missing_artifacts) == 0 and
        len(deserialize_failures) == 0 and
        len(partition_mismatches) == 0
    )

    report: Dict[str, Any] = {
        "store_root": str(store.root),
        "index_exists": index_exists,
        "indexed_runs": len(run_ids),
        "tombstones": tombstone_count,
        "active_runs": len(run_ids) - tombstone_count,
        "missing_artifacts": missing_artifacts,
        "deserialize_failures": deserialize_failures,
        "partition_mismatches": partition_mismatches,
        "strict_deserialize": strict_deserialize,
    }
    return ok, report


def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point."""
    argv = argv or sys.argv[1:]
    strict = True
    if "--no-strict" in argv:
        strict = False

    print("RMOS runs_v2 Store Verification")
    print("================================")
    print(f"Store root: {_get_store_root()}")
    print()

    ok, report = verify(strict_deserialize=strict)

    print(f"Index exists: {'Yes' if report['index_exists'] else 'No'}")
    print(f"Runs indexed: {report['indexed_runs']}")
    print(f"  - Active runs: {report['active_runs']}")
    print(f"  - Tombstones (soft-deleted): {report['tombstones']}")
    print()

    if report["missing_artifacts"]:
        print(f"[ERROR] Missing artifacts: {len(report['missing_artifacts'])}")
        for rid in report["missing_artifacts"][:25]:
            print(f"   - {rid}")
        if len(report["missing_artifacts"]) > 25:
            print("   ...")
    else:
        print("[OK] All artifacts present")

    if report["partition_mismatches"]:
        print(f"[ERROR] Partition mismatches: {len(report['partition_mismatches'])}")
        for item in report["partition_mismatches"][:10]:
            print(f"   - {item['run_id']}: {item['error']}")
    else:
        print("[OK] All index entries have valid partitions")

    if strict:
        if report["deserialize_failures"]:
            print(f"[ERROR] Deserialize failures: {len(report['deserialize_failures'])}")
            for item in report["deserialize_failures"][:10]:
                print(f"   - {item['run_id']}: {item['error']}")
            if len(report["deserialize_failures"]) > 10:
                print("   ...")
        else:
            print("[OK] All artifacts deserialize as RunArtifact")

    print()
    if ok:
        print("Verification PASSED")
        sys.exit(0)
    else:
        print("Verification FAILED")
        sys.exit(2)


if __name__ == "__main__":
    main()
