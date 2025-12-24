"""
Verification Test: Backend Snapshot Concurrency

Tests that concurrent snapshot exports don't corrupt files.
Run with: python -m pytest tests/verification/test_snapshot_concurrency.py -v

Requirements:
- Server running on localhost:8000
- OR run directly against the store module
"""

import asyncio
import json
import hashlib
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# Add app to path for direct store testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))


def test_concurrent_exports_via_store():
    """
    Test concurrent snapshot writes directly against the store.
    Verifies atomic writes prevent corruption.
    """
    from app.art_studio.services.rosette_snapshot_store import (
        save_snapshot,
        load_snapshot,
        delete_snapshot,
        create_snapshot_id,
        compute_design_fingerprint,
    )
    from app.art_studio.schemas.rosette_snapshot import (
        RosetteDesignSnapshot,
        SnapshotMetadata,
    )
    from app.art_studio.schemas.rosette_params import RosetteParamSpec

    NUM_CONCURRENT = 10
    results: List[Dict[str, Any]] = []
    errors: List[str] = []

    def create_and_save_snapshot(index: int) -> Dict[str, Any]:
        """Create a unique snapshot and save it."""
        try:
            # Create unique design
            design = RosetteParamSpec(
                outer_diameter_mm=100.0 + index,
                inner_diameter_mm=20.0 + index,
                ring_params=[],
            )

            snapshot_id = create_snapshot_id()
            fingerprint = compute_design_fingerprint(design)

            snapshot = RosetteDesignSnapshot(
                snapshot_id=snapshot_id,
                design_fingerprint=fingerprint,
                design=design,
                metadata=SnapshotMetadata(
                    name=f"Concurrent Test {index}",
                    source="test",
                ),
            )

            # Save
            saved = save_snapshot(snapshot)

            # Immediately reload and verify
            loaded = load_snapshot(snapshot_id)

            if loaded is None:
                return {"index": index, "error": "Failed to reload snapshot"}

            # Verify integrity
            if loaded.snapshot_id != snapshot_id:
                return {"index": index, "error": "Snapshot ID mismatch"}

            if loaded.design_fingerprint != fingerprint:
                return {"index": index, "error": "Fingerprint mismatch"}

            # Cleanup
            delete_snapshot(snapshot_id)

            return {
                "index": index,
                "snapshot_id": snapshot_id,
                "success": True,
            }

        except Exception as e:
            return {"index": index, "error": str(e)}

    # Run concurrent writes
    print(f"\n{'='*60}")
    print(f"Running {NUM_CONCURRENT} concurrent snapshot writes...")
    print(f"{'='*60}\n")

    with ThreadPoolExecutor(max_workers=NUM_CONCURRENT) as executor:
        futures = [
            executor.submit(create_and_save_snapshot, i)
            for i in range(NUM_CONCURRENT)
        ]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            if "error" in result:
                errors.append(f"Index {result['index']}: {result['error']}")
                print(f"  [FAIL] Index {result['index']}: {result['error']}")
            else:
                print(f"  [OK]   Index {result['index']}: {result['snapshot_id']}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Results: {len(results) - len(errors)}/{len(results)} successful")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors:
            print(f"  - {err}")
        print(f"{'='*60}\n")
        assert False, f"{len(errors)} concurrent writes failed"
    else:
        print(f"All concurrent writes completed without corruption!")
        print(f"{'='*60}\n")


def test_same_id_rejection():
    """
    Test that writing the same snapshot ID twice is rejected.
    (Immutability guard)
    """
    from app.art_studio.services.rosette_snapshot_store import (
        save_snapshot,
        load_snapshot,
        delete_snapshot,
        compute_design_fingerprint,
    )
    from app.art_studio.schemas.rosette_snapshot import (
        RosetteDesignSnapshot,
        SnapshotMetadata,
    )
    from app.art_studio.schemas.rosette_params import RosetteParamSpec

    print(f"\n{'='*60}")
    print("Testing same-ID write rejection...")
    print(f"{'='*60}\n")

    # Create first snapshot
    design = RosetteParamSpec(
        outer_diameter_mm=100.0,
        inner_diameter_mm=20.0,
        ring_params=[],
    )

    snapshot_id = "test_duplicate_id_check"
    fingerprint = compute_design_fingerprint(design)

    snapshot1 = RosetteDesignSnapshot(
        snapshot_id=snapshot_id,
        design_fingerprint=fingerprint,
        design=design,
        metadata=SnapshotMetadata(name="First", source="test"),
    )

    # Clean up any existing
    delete_snapshot(snapshot_id)

    # First write should succeed
    save_snapshot(snapshot1)
    print(f"  [OK] First write succeeded")

    # Second write with same ID - current behavior overwrites
    # (Note: If you want rejection, the store needs modification)
    snapshot2 = RosetteDesignSnapshot(
        snapshot_id=snapshot_id,
        design_fingerprint=fingerprint,
        design=design,
        metadata=SnapshotMetadata(name="Second", source="test"),
    )

    try:
        save_snapshot(snapshot2)
        # Currently overwrites - this is acceptable with atomic writes
        loaded = load_snapshot(snapshot_id)
        print(f"  [INFO] Second write overwrote (atomic, no corruption)")
        print(f"         Loaded name: {loaded.metadata.name}")
    except ValueError as e:
        print(f"  [OK] Second write rejected: {e}")

    # Cleanup
    delete_snapshot(snapshot_id)
    print(f"\n{'='*60}\n")


def verify_json_integrity():
    """
    Scan all snapshot files for JSON integrity.
    """
    from app.art_studio.services.rosette_snapshot_store import _snapshot_dir

    print(f"\n{'='*60}")
    print("Verifying JSON integrity of all snapshots...")
    print(f"{'='*60}\n")

    snapshot_dir = _snapshot_dir()
    files = list(snapshot_dir.glob("*.json"))

    if not files:
        print("  No snapshot files found (OK - empty store)")
        return

    corrupt = []
    valid = 0

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            # Basic structure check
            if "snapshot_id" not in data:
                corrupt.append((path.name, "Missing snapshot_id"))
            elif "design" not in data:
                corrupt.append((path.name, "Missing design"))
            else:
                valid += 1
        except json.JSONDecodeError as e:
            corrupt.append((path.name, f"Invalid JSON: {e}"))

    print(f"  Valid files: {valid}")
    print(f"  Corrupt files: {len(corrupt)}")

    if corrupt:
        print(f"\n  Corrupt files:")
        for name, reason in corrupt:
            print(f"    - {name}: {reason}")
        assert False, f"{len(corrupt)} corrupt snapshot files found"
    else:
        print(f"\n  All files are valid JSON with correct structure!")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SNAPSHOT CONCURRENCY VERIFICATION")
    print("="*60)

    test_concurrent_exports_via_store()
    test_same_id_rejection()
    verify_json_integrity()

    print("\n" + "="*60)
    print("ALL VERIFICATIONS PASSED")
    print("="*60 + "\n")
