"""
RMOS Runs v2 Migration Utilities

One-time migration from v1 single-file to v2 date-partitioned.

GOVERNANCE:
- Creates backup before migration
- Verifies migration integrity
- Provides rollback capability
"""
from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import RunArtifact
from .store import RunStoreV2, ImmutabilityViolation
from .compat import convert_v1_to_v2, validate_v1_record

logger = logging.getLogger(__name__)


@dataclass
class MigrationReport:
    """Report of migration results."""
    v1_path: str
    v2_root: str
    backup_path: Optional[str]
    total_v1_runs: int
    migrated_count: int
    skipped_count: int
    error_count: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    dry_run: bool = False

    @property
    def success(self) -> bool:
        return self.error_count == 0 and self.migrated_count + self.skipped_count == self.total_v1_runs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "v1_path": self.v1_path,
            "v2_root": self.v2_root,
            "backup_path": self.backup_path,
            "total_v1_runs": self.total_v1_runs,
            "migrated_count": self.migrated_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "errors": self.errors[:20],  # Limit for display
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success": self.success,
            "dry_run": self.dry_run,
        }


def backup_v1_store(v1_path: str) -> str:
    """
    Create backup of v1 runs.json before migration.

    Returns backup path.
    """
    v1_file = Path(v1_path)
    if not v1_file.exists():
        raise FileNotFoundError(f"V1 store not found: {v1_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = v1_file.with_name(f"{v1_file.stem}_backup_{timestamp}.json")

    shutil.copy2(v1_file, backup_path)
    logger.info(f"Created v1 backup: {backup_path}")

    return str(backup_path)


def load_v1_store(v1_path: str) -> Dict[str, Any]:
    """Load v1 runs.json file."""
    v1_file = Path(v1_path)
    if not v1_file.exists():
        raise FileNotFoundError(f"V1 store not found: {v1_path}")

    with open(v1_file, "r", encoding="utf-8") as f:
        return json.load(f)


def migrate_v1_to_v2(
    v1_path: str = "services/api/app/data/runs.json",
    v2_root: str = "data/runs/rmos",
    dry_run: bool = False,
    skip_backup: bool = False,
) -> MigrationReport:
    """
    One-time migration from v1 single-file to v2 date-partitioned.

    Args:
        v1_path: Path to v1 runs.json
        v2_root: Root directory for v2 date-partitioned storage
        dry_run: If True, validate without writing
        skip_backup: If True, skip backup (use with caution)

    Returns:
        MigrationReport with results
    """
    report = MigrationReport(
        v1_path=v1_path,
        v2_root=v2_root,
        backup_path=None,
        total_v1_runs=0,
        migrated_count=0,
        skipped_count=0,
        error_count=0,
        dry_run=dry_run,
    )

    # Check v1 exists
    v1_file = Path(v1_path)
    if not v1_file.exists():
        report.errors.append({"error": f"V1 store not found: {v1_path}"})
        report.error_count = 1
        report.completed_at = datetime.now()
        return report

    # Backup v1 store
    if not dry_run and not skip_backup:
        try:
            report.backup_path = backup_v1_store(v1_path)
        except Exception as e:
            report.errors.append({"error": f"Backup failed: {e}"})
            report.error_count = 1
            report.completed_at = datetime.now()
            return report

    # Load v1 data
    try:
        v1_data = load_v1_store(v1_path)
    except Exception as e:
        report.errors.append({"error": f"Failed to load v1 data: {e}"})
        report.error_count = 1
        report.completed_at = datetime.now()
        return report

    report.total_v1_runs = len(v1_data)
    logger.info(f"Found {report.total_v1_runs} runs in v1 store")

    # Create v2 store
    store_v2 = RunStoreV2(v2_root)

    # Convert and write each run
    for run_id, raw in v1_data.items():
        try:
            # Ensure run_id is in the data
            if "run_id" not in raw:
                raw["run_id"] = run_id

            # Validate before conversion
            validation = validate_v1_record(raw)
            if not validation["can_convert"]:
                report.errors.append({
                    "run_id": run_id,
                    "error": f"Cannot convert: {validation['issues']}",
                    "type": "validation",
                })
                report.error_count += 1
                continue

            # Convert to v2 format
            artifact_v2 = convert_v1_to_v2(raw)

            # Write to v2 store
            if not dry_run:
                try:
                    store_v2.put(artifact_v2)
                    report.migrated_count += 1
                    logger.debug(f"Migrated {run_id}")
                except ImmutabilityViolation:
                    report.skipped_count += 1
                    logger.debug(f"Skipped {run_id}: already exists")
            else:
                report.migrated_count += 1
                logger.debug(f"[DRY RUN] Would migrate {run_id}")

        except Exception as e:
            report.errors.append({
                "run_id": run_id,
                "error": str(e),
                "type": type(e).__name__,
            })
            report.error_count += 1
            logger.error(f"Error migrating {run_id}: {e}")

    report.completed_at = datetime.now()

    logger.info(
        f"Migration complete: {report.migrated_count}/{report.total_v1_runs} migrated, "
        f"{report.skipped_count} skipped, {report.error_count} errors"
    )

    return report


def verify_migration(
    v1_path: str,
    v2_root: str,
) -> Dict[str, Any]:
    """
    Verify migration by comparing v1 and v2 stores.

    Returns verification report.
    """
    # Load v1 data
    v1_data = load_v1_store(v1_path)

    # Load v2 store
    store_v2 = RunStoreV2(v2_root)

    missing_in_v2 = []
    mismatched = []
    verified = 0

    for run_id, v1_raw in v1_data.items():
        # Ensure run_id matches
        actual_run_id = v1_raw.get("run_id", run_id)

        v2_artifact = store_v2.get(actual_run_id)
        if v2_artifact is None:
            missing_in_v2.append({"run_id": actual_run_id, "reason": "not_found"})
            continue

        # Verify critical fields
        if v1_raw.get("status") != v2_artifact.status:
            mismatched.append({
                "run_id": actual_run_id,
                "field": "status",
                "v1": v1_raw.get("status"),
                "v2": v2_artifact.status,
            })

        verified += 1

    return {
        "v1_count": len(v1_data),
        "v2_count": store_v2.count(),
        "verified_count": verified,
        "missing_in_v2": missing_in_v2,
        "mismatched": mismatched,
        "success": len(missing_in_v2) == 0 and len(mismatched) == 0,
    }


def rollback_migration(
    backup_path: str,
    v1_path: str,
) -> None:
    """
    Rollback migration by restoring v1 backup.

    WARNING: This only restores the v1 file.
    V2 data must be manually cleaned if needed.
    """
    backup_file = Path(backup_path)
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    v1_file = Path(v1_path)
    shutil.copy2(backup_file, v1_file)
    logger.info(f"Restored v1 store from backup: {backup_path}")


def get_migration_status(
    v1_path: str = "services/api/app/data/runs.json",
    v2_root: str = "data/runs/rmos",
) -> Dict[str, Any]:
    """
    Check current migration status.

    Returns status report.
    """
    v1_exists = Path(v1_path).exists()
    v2_exists = Path(v2_root).exists()

    v1_count = 0
    v2_count = 0

    if v1_exists:
        try:
            v1_data = load_v1_store(v1_path)
            v1_count = len(v1_data)
        except Exception:
            pass

    if v2_exists:
        try:
            store_v2 = RunStoreV2(v2_root)
            v2_count = store_v2.count()
        except Exception:
            pass

    if not v1_exists and not v2_exists:
        status = "EMPTY"
    elif v1_exists and not v2_exists:
        status = "V1_ONLY"
    elif not v1_exists and v2_exists:
        status = "V2_ONLY"
    elif v1_count == v2_count:
        status = "MIGRATED"
    elif v2_count > 0:
        status = "PARTIAL"
    else:
        status = "V1_ONLY"

    return {
        "status": status,
        "v1_exists": v1_exists,
        "v2_exists": v2_exists,
        "v1_count": v1_count,
        "v2_count": v2_count,
        "v1_path": v1_path,
        "v2_root": v2_root,
    }
