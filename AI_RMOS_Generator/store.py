"""
RMOS Runs v2 Store

Date-partitioned, immutable storage with separate advisory link files.
Per: docs/governance/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md

GOVERNANCE:
- Write-once (immutable) - put() raises if artifact exists
- Date-partitioned: {root}/{YYYY-MM-DD}/{run_id}.json
- Advisory links: separate files to preserve immutability
- Atomic writes: .tmp + os.replace()
- NO patch_meta() - artifacts cannot be modified
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from filelock import FileLock

from .schemas import RunArtifact, AdvisoryInputRef

logger = logging.getLogger(__name__)

_RUN_ID_PATTERN = re.compile(r'^run_[a-f0-9]{12}$')


class ImmutabilityViolation(Exception):
    """Raised when attempting to modify an immutable artifact."""
    pass


class RunStoreV2:
    """
    Date-partitioned, immutable run artifact store.

    Storage structure:
        {root}/
        ├── 2025-12-17/
        │   ├── run_abc123def456.json
        │   ├── run_abc123def456_advisory_adv_001.json
        │   └── run_abc123def456_explanation.json
        └── 2025-12-18/
            └── run_ghi789jkl012.json

    GOVERNANCE:
    - Artifacts are write-once (immutable)
    - Advisory links stored as separate files
    - Explanation status stored as separate file
    - Atomic writes via .tmp + os.replace()
    """

    def __init__(self, root_dir: str):
        self.root = Path(root_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _validate_run_id(self, run_id: str) -> None:
        """Validate run_id format to prevent path traversal."""
        if not _RUN_ID_PATTERN.match(run_id):
            raise ValueError(f"Invalid run_id format: {run_id}")

    def _date_partition(self, dt: datetime) -> str:
        """Generate date-based partition: YYYY-MM-DD"""
        return dt.strftime("%Y-%m-%d")

    def _path_for(self, run_id: str, created_at: datetime) -> Path:
        """Get path for a run artifact."""
        self._validate_run_id(run_id)
        partition = self._date_partition(created_at)
        return self.root / partition / f"{run_id}.json"

    def _advisory_link_path(self, run_id: str, advisory_id: str, partition: str) -> Path:
        """Get path for an advisory link file."""
        safe_advisory_id = re.sub(r'[^a-zA-Z0-9_-]', '_', advisory_id)
        return self.root / partition / f"{run_id}_advisory_{safe_advisory_id}.json"

    def _explanation_path(self, run_id: str, partition: str) -> Path:
        """Get path for explanation status file."""
        return self.root / partition / f"{run_id}_explanation.json"

    def _lock_path(self, path: Path) -> Path:
        """Get lock file path for atomic operations."""
        return path.with_suffix(".lock")

    def _atomic_write(self, path: Path, data: str) -> None:
        """Write data atomically via temp file + rename."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(data, encoding="utf-8")
        os.replace(tmp, path)

    # -------------------------------------------------------------------------
    # Core Operations
    # -------------------------------------------------------------------------

    def put(self, artifact: RunArtifact) -> None:
        """
        Write artifact to storage. Write-once (immutable).

        GOVERNANCE: Raises ImmutabilityViolation if artifact already exists.
        """
        path = self._path_for(artifact.run_id, artifact.created_at_utc)

        with FileLock(self._lock_path(path)):
            if path.exists():
                raise ImmutabilityViolation(
                    f"Artifact {artifact.run_id} already exists. "
                    "Run artifacts are immutable per governance contract."
                )

            # Don't persist advisory_inputs or explanation - stored separately
            data = artifact.model_dump(mode="json")
            data["advisory_inputs"] = []
            data["explanation_status"] = "NONE"
            data["explanation_summary"] = None

            self._atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False))
            logger.info(f"Created immutable artifact: {artifact.run_id}")

    def get(self, run_id: str) -> Optional[RunArtifact]:
        """
        Retrieve artifact by run_id.

        Searches all date partitions (newest first).
        Loads advisory links and explanation from separate files.
        """
        self._validate_run_id(run_id)

        for partition_dir in sorted(self.root.iterdir(), reverse=True):
            if not partition_dir.is_dir():
                continue

            path = partition_dir / f"{run_id}.json"
            if path.exists():
                with FileLock(self._lock_path(path)):
                    try:
                        raw = json.loads(path.read_text(encoding="utf-8"))
                        artifact = RunArtifact.model_validate(raw)

                        # Load advisory links from separate files
                        artifact.advisory_inputs = self._load_advisory_links(
                            run_id, partition_dir.name
                        )

                        # Load explanation status from separate file
                        exp_status, exp_summary = self._load_explanation(
                            run_id, partition_dir.name
                        )
                        artifact.explanation_status = exp_status
                        artifact.explanation_summary = exp_summary

                        return artifact
                    except Exception as e:
                        logger.error(f"Error reading run {run_id}: {e}")
                        return None

        return None

    def exists(self, run_id: str) -> bool:
        """Check if a run exists."""
        self._validate_run_id(run_id)
        for partition_dir in self.root.iterdir():
            if partition_dir.is_dir():
                if (partition_dir / f"{run_id}.json").exists():
                    return True
        return False

    def _find_partition(self, run_id: str) -> Optional[str]:
        """Find which partition contains a run."""
        self._validate_run_id(run_id)
        for partition_dir in sorted(self.root.iterdir(), reverse=True):
            if partition_dir.is_dir():
                if (partition_dir / f"{run_id}.json").exists():
                    return partition_dir.name
        return None

    # -------------------------------------------------------------------------
    # Advisory Links (append-only, preserves immutability)
    # -------------------------------------------------------------------------

    def _load_advisory_links(self, run_id: str, partition: str) -> List[AdvisoryInputRef]:
        """Load all advisory link files for a run."""
        links = []
        partition_dir = self.root / partition

        pattern = f"{run_id}_advisory_*.json"
        for link_path in partition_dir.glob(pattern):
            if link_path.suffix == ".json" and not link_path.name.endswith(".tmp"):
                try:
                    raw = json.loads(link_path.read_text(encoding="utf-8"))
                    links.append(AdvisoryInputRef.model_validate(raw))
                except Exception as e:
                    logger.warning(f"Error reading advisory link {link_path}: {e}")
                    continue

        links.sort(key=lambda x: x.created_at_utc)
        return links

    def attach_advisory(
        self,
        run_id: str,
        advisory_id: str,
        kind: str = "unknown",
        engine_id: Optional[str] = None,
        engine_version: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Optional[RunArtifact]:
        """
        Attach advisory reference to a run (append-only).

        Creates separate link file to preserve artifact immutability.
        Returns None if run not found.
        Idempotent - skips if link already exists.
        """
        partition = self._find_partition(run_id)
        if partition is None:
            return None

        link_path = self._advisory_link_path(run_id, advisory_id, partition)

        with FileLock(self._lock_path(link_path)):
            if link_path.exists():
                logger.debug(f"Advisory {advisory_id} already attached to {run_id}")
                return self.get(run_id)

            ref = AdvisoryInputRef(
                advisory_id=advisory_id,
                kind=kind,
                engine_id=engine_id,
                engine_version=engine_version,
                request_id=request_id,
            )

            self._atomic_write(link_path, ref.model_dump_json(indent=2))
            logger.info(f"Attached advisory {advisory_id} to {run_id}")

        return self.get(run_id)

    # -------------------------------------------------------------------------
    # Explanation Status (separate file, preserves immutability)
    # -------------------------------------------------------------------------

    def _load_explanation(self, run_id: str, partition: str) -> tuple[str, Optional[str]]:
        """Load explanation status from separate file."""
        exp_path = self._explanation_path(run_id, partition)
        if not exp_path.exists():
            return "NONE", None

        try:
            raw = json.loads(exp_path.read_text(encoding="utf-8"))
            return raw.get("status", "NONE"), raw.get("summary")
        except Exception as e:
            logger.warning(f"Error reading explanation for {run_id}: {e}")
            return "NONE", None

    def set_explanation(
        self,
        run_id: str,
        status: str,
        summary: Optional[str] = None,
    ) -> Optional[RunArtifact]:
        """
        Update explanation status via separate file.

        Preserves artifact immutability by storing explanation state separately.
        """
        partition = self._find_partition(run_id)
        if partition is None:
            return None

        exp_path = self._explanation_path(run_id, partition)

        with FileLock(self._lock_path(exp_path)):
            exp_data = {
                "status": status,
                "summary": summary,
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            self._atomic_write(exp_path, json.dumps(exp_data, indent=2))
            logger.info(f"Set explanation for {run_id}: {status}")

        return self.get(run_id)

    # -------------------------------------------------------------------------
    # Listing and Filtering
    # -------------------------------------------------------------------------

    def list_all(self, limit: int = 100) -> List[RunArtifact]:
        """List all runs, newest first."""
        runs = []

        for partition_dir in sorted(self.root.iterdir(), reverse=True):
            if not partition_dir.is_dir():
                continue

            for path in sorted(partition_dir.glob("run_????????????.json"), reverse=True):
                if len(runs) >= limit:
                    return runs

                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                    artifact = RunArtifact.model_validate(raw)

                    # Load advisory links
                    artifact.advisory_inputs = self._load_advisory_links(
                        artifact.run_id, partition_dir.name
                    )

                    # Load explanation
                    exp_status, exp_summary = self._load_explanation(
                        artifact.run_id, partition_dir.name
                    )
                    artifact.explanation_status = exp_status
                    artifact.explanation_summary = exp_summary

                    runs.append(artifact)
                except Exception as e:
                    logger.warning(f"Skipping corrupt run file {path}: {e}")
                    continue

        return runs

    def list_filtered(
        self,
        *,
        limit: int = 100,
        status: Optional[str] = None,
        mode: Optional[str] = None,
        tool_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[RunArtifact]:
        """List runs with filtering."""
        runs = []

        for partition_dir in sorted(self.root.iterdir(), reverse=True):
            if not partition_dir.is_dir():
                continue

            # Date range filter on partition
            if date_from or date_to:
                try:
                    partition_date = datetime.strptime(partition_dir.name, "%Y-%m-%d")
                    if date_from and partition_date.date() < date_from.date():
                        continue
                    if date_to and partition_date.date() > date_to.date():
                        continue
                except ValueError:
                    continue

            for path in sorted(partition_dir.glob("run_????????????.json"), reverse=True):
                if len(runs) >= limit:
                    return runs

                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))

                    # Filter before full validation for performance
                    if status and raw.get("status") != status:
                        continue
                    if mode and raw.get("mode") != mode:
                        continue
                    if tool_id and raw.get("tool_id") != tool_id:
                        continue
                    if risk_level:
                        decision = raw.get("decision", {})
                        if decision.get("risk_level") != risk_level:
                            continue

                    artifact = RunArtifact.model_validate(raw)
                    artifact.advisory_inputs = self._load_advisory_links(
                        artifact.run_id, partition_dir.name
                    )
                    exp_status, exp_summary = self._load_explanation(
                        artifact.run_id, partition_dir.name
                    )
                    artifact.explanation_status = exp_status
                    artifact.explanation_summary = exp_summary

                    runs.append(artifact)
                except Exception as e:
                    logger.warning(f"Skipping file {path}: {e}")
                    continue

        return runs

    def count(self) -> int:
        """Count total runs."""
        total = 0
        for partition_dir in self.root.iterdir():
            if partition_dir.is_dir():
                total += len(list(partition_dir.glob("run_????????????.json")))
        return total


# Module-level store instance
_store: Optional[RunStoreV2] = None


def get_store() -> RunStoreV2:
    """Get or create the store singleton."""
    global _store
    if _store is None:
        root = os.environ.get("RMOS_RUNS_GOV_DIR", "data/runs/rmos")
        _store = RunStoreV2(root)
    return _store


def reset_store() -> None:
    """Reset the store singleton (for testing)."""
    global _store
    _store = None
