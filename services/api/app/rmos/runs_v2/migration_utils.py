"""
RMOS Runs Migration Utilities

Tools for migrating from v1 (single-file) to v2 (date-partitioned) storage.

Usage:
    from runs_v2.migration_utils import migrate_v1_to_v2

    report = migrate_v1_to_v2(
        v1_path="services/api/app/data/runs.json",
        v2_root="services/api/data/runs/rmos"
    )
    print(report)
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .compat import convert_v1_to_v2, validate_v2_artifact
from .store import RunStoreV2


@dataclass
class MigrationReport:
    """Report from a v1 -> v2 migration."""
    started_at: datetime
    completed_at: Optional[datetime] = None
    v1_path: str = ""
    v2_root: str = ""
    backup_path: Optional[str] = None
    total_v1: int = 0
    migrated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    partitions_created: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed == 0 and self.migrated == self.total_v1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "v1_path": self.v1_path,
            "v2_root": self.v2_root,
            "backup_path": self.backup_path,
            "total_v1": self.total_v1,
            "migrated": self.migrated,
            "skipped": self.skipped,
            "failed": self.failed,
            "success": self.success,
            "errors": self.errors,
            "partitions_created": self.partitions_created,
        }


def backup_v1_store(v1_path: str) -> str:
    """
    Create a backup of the v1 store before migration.

    Args:
        v1_path: Path to runs.json

    Returns:
        Path to backup file
    """
    src = Path(v1_path)
    if not src.exists():
        raise FileNotFoundError(f"v1 store not found: {v1_path}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = src.with_suffix(f".backup_{timestamp}.json")

    shutil.copy2(src, backup_path)
    return str(backup_path)


def load_v1_store(v1_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load the v1 store from disk.

    Args:
        v1_path: Path to runs.json

    Returns:
        Dict mapping run_id -> artifact data
    """
    with open(v1_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict in {v1_path}, got {type(data)}")

    return data


def migrate_v1_to_v2(
    v1_path: str = "services/api/app/data/runs.json",
    v2_root: str = "services/api/data/runs/rmos",
    *,
    dry_run: bool = False,
    skip_backup: bool = False,
    stop_on_error: bool = False,
) -> MigrationReport:
    """
    Migrate from v1 single-file store to v2 date-partitioned store.

    Args:
        v1_path: Path to v1 runs.json
        v2_root: Root directory for v2 store
        dry_run: If True, validate but don't write
        skip_backup: If True, skip backup creation
        stop_on_error: If True, stop on first error

    Returns:
        MigrationReport with migration results
    """
    report = MigrationReport(
        started_at=datetime.now(timezone.utc),
        v1_path=v1_path,
        v2_root=v2_root,
    )

    # Check v1 exists
    if not Path(v1_path).exists():
        report.errors.append({"error": "v1_not_found", "path": v1_path})
        report.completed_at = datetime.now(timezone.utc)
        return report

    # Backup v1
    if not skip_backup and not dry_run:
        try:
            report.backup_path = backup_v1_store(v1_path)
        except OSError as e:  # WP-1: narrowed from except Exception
            report.errors.append({"error": "backup_failed", "detail": str(e)})
            if stop_on_error:
                report.completed_at = datetime.now(timezone.utc)
                return report

    # Load v1 data
    try:
        v1_data = load_v1_store(v1_path)
    except (OSError, json.JSONDecodeError, ValueError) as e:  # WP-1: narrowed from except Exception
        report.errors.append({"error": "load_failed", "detail": str(e)})
        report.completed_at = datetime.now(timezone.utc)
        return report

    report.total_v1 = len(v1_data)

    # Create v2 store
    store_v2 = RunStoreV2(v2_root)
    partitions = set()

    # Migrate each artifact
    for run_id, raw in v1_data.items():
        try:
            # Ensure run_id is in the data
            if "run_id" not in raw:
                raw["run_id"] = run_id

            # Convert to v2
            artifact = convert_v1_to_v2(raw)

            # Validate
            validation_errors = validate_v2_artifact(artifact)
            if validation_errors:
                report.errors.append({
                    "run_id": run_id,
                    "error": "validation_failed",
                    "detail": validation_errors,
                })
                report.failed += 1
                if stop_on_error:
                    break
                continue

            # Write (unless dry run)
            if not dry_run:
                try:
                    store_v2.put(artifact)
                    partition = artifact.created_at_utc.strftime("%Y-%m-%d")
                    partitions.add(partition)
                except ValueError as e:
                    # Already exists (immutability violation)
                    if "already exists" in str(e):
                        report.skipped += 1
                        continue
                    raise

            report.migrated += 1

        except (ValueError, TypeError, KeyError, OSError) as e:  # WP-1: narrowed from except Exception
            report.errors.append({
                "run_id": run_id,
                "error": "conversion_failed",
                "detail": str(e),
            })
            report.failed += 1
            if stop_on_error:
                break

    report.partitions_created = sorted(partitions)
    report.completed_at = datetime.now(timezone.utc)
    return report


def verify_migration(
    v1_path: str,
    v2_root: str,
) -> Dict[str, Any]:
    """
    Verify that all v1 artifacts were migrated to v2.

    Args:
        v1_path: Path to v1 runs.json
        v2_root: Root directory of v2 store

    Returns:
        Verification report
    """
    # Load v1
    try:
        v1_data = load_v1_store(v1_path)
    except FileNotFoundError:
        return {"error": "v1_not_found", "path": v1_path}

    # Load v2 store
    store_v2 = RunStoreV2(v2_root)

    missing = []
    found = []
    mismatched = []

    for run_id, v1_raw in v1_data.items():
        v2_artifact = store_v2.get(run_id)
        if v2_artifact is None:
            missing.append(run_id)
        else:
            found.append(run_id)
            # Verify hash matches
            if v1_raw.get("request_hash") and v1_raw["request_hash"] != v2_artifact.hashes.feasibility_sha256:
                mismatched.append({
                    "run_id": run_id,
                    "v1_hash": v1_raw.get("request_hash"),
                    "v2_hash": v2_artifact.hashes.feasibility_sha256,
                })

    return {
        "v1_count": len(v1_data),
        "v2_found": len(found),
        "missing": missing,
        "mismatched": mismatched,
        "complete": len(missing) == 0,
    }


def rollback_migration(
    v1_path: str,
    backup_path: str,
    v2_root: str,
    *,
    delete_v2: bool = False,
) -> Dict[str, Any]:
    """
    Rollback a migration by restoring the v1 backup.

    Args:
        v1_path: Path to restore v1 runs.json
        backup_path: Path to backup file
        v2_root: Root directory of v2 store
        delete_v2: If True, also delete v2 data

    Returns:
        Rollback status
    """
    result: Dict[str, Any] = {
        "restored_v1": False,
        "deleted_v2": False,
        "errors": [],
    }

    # Restore v1 from backup
    if Path(backup_path).exists():
        try:
            shutil.copy2(backup_path, v1_path)
            result["restored_v1"] = True
        except OSError as e:  # WP-1: narrowed from except Exception
            result["errors"].append(f"Failed to restore v1: {e}")
    else:
        result["errors"].append(f"Backup not found: {backup_path}")

    # Optionally delete v2 data
    if delete_v2:
        v2_path = Path(v2_root)
        if v2_path.exists():
            try:
                shutil.rmtree(v2_path)
                result["deleted_v2"] = True
            except OSError as e:  # WP-1: narrowed from except Exception
                result["errors"].append(f"Failed to delete v2: {e}")

    return result


def migration_status(v2_root: str) -> Dict[str, Any]:
    """
    Get current migration status and statistics.

    Args:
        v2_root: Root directory of v2 store

    Returns:
        Status report with partition counts
    """
    root = Path(v2_root)
    if not root.exists():
        return {"exists": False, "partitions": [], "total_artifacts": 0}

    partitions = []
    total = 0

    for partition_dir in sorted(root.iterdir()):
        if partition_dir.is_dir() and not partition_dir.name.startswith("_"):
            count = len([f for f in partition_dir.glob("*.json") if "_advisory_" not in f.name])
            partitions.append({
                "date": partition_dir.name,
                "artifact_count": count,
            })
            total += count

    return {
        "exists": True,
        "root": str(root),
        "partitions": partitions,
        "partition_count": len(partitions),
        "total_artifacts": total,
    }
