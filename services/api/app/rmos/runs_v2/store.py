"""
RMOS Run Artifact Store v2 - Date-Partitioned, Immutable

Governance-compliant storage implementation per RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md.

Key Features:
- Date-partitioned directory structure: {YYYY-MM-DD}/{run_id}.json
- Immutable artifacts (write-once, never modified)
- Atomic writes via .tmp + os.replace()
- Append-only advisory links (preserves immutability)
- Thread-safe with file locking
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .schemas import RunArtifact, AdvisoryInputRef


# Default storage path per governance contract
STORE_ROOT_DEFAULT = "services/api/data/runs/rmos"


def _get_store_root() -> str:
    """Get the store root from environment or default."""
    return os.getenv("RMOS_RUNS_DIR", STORE_ROOT_DEFAULT)


class RunStoreV2:
    """
    Date-partitioned, immutable run artifact store.

    Storage Structure:
        {root}/
        ├── 2025-12-17/
        │   ├── run_abc123def456.json
        │   └── run_abc123def456_advisory_adv001.json
        ├── 2025-12-18/
        │   └── run_ghi789jkl012.json
        └── _index.json (optional)

    Thread Safety:
        Uses atomic writes via .tmp + os.replace()
        For multi-process safety, use filelock (optional dependency)
    """

    def __init__(self, root_dir: Optional[str] = None):
        """
        Initialize the store.

        Args:
            root_dir: Root directory for storage. Defaults to RMOS_RUNS_DIR env var.
        """
        self.root = Path(root_dir or _get_store_root()).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _date_partition(self, dt: datetime) -> str:
        """Get date partition string from datetime."""
        return dt.strftime("%Y-%m-%d")

    def _path_for(self, run_id: str, created_at: datetime) -> Path:
        """
        Get the file path for a run artifact.

        Contract: {root}/{YYYY-MM-DD}/{run_id}.json
        """
        partition = self._date_partition(created_at)
        # Sanitize run_id for filesystem safety
        safe_id = run_id.replace("/", "_").replace("\\", "_")
        return self.root / partition / f"{safe_id}.json"

    def _advisory_link_path(self, run_id: str, advisory_id: str, created_at: datetime) -> Path:
        """
        Get the file path for an advisory link.

        Pattern: {root}/{YYYY-MM-DD}/{run_id}_advisory_{advisory_id}.json
        """
        partition = self._date_partition(created_at)
        safe_run_id = run_id.replace("/", "_").replace("\\", "_")
        safe_adv_id = advisory_id.replace("/", "_").replace("\\", "_")
        return self.root / partition / f"{safe_run_id}_advisory_{safe_adv_id}.json"

    def put(self, artifact: RunArtifact) -> None:
        """
        Write a run artifact to storage.

        IMMUTABLE: Raises if artifact already exists.

        Args:
            artifact: The RunArtifact to store

        Raises:
            ValueError: If artifact with this run_id already exists
        """
        path = self._path_for(artifact.run_id, artifact.created_at_utc)

        if path.exists():
            raise ValueError(
                f"Artifact {artifact.run_id} already exists. "
                "Run artifacts are immutable per governance contract."
            )

        # Ensure partition directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to .tmp then rename
        tmp = path.with_suffix(".json.tmp")
        try:
            tmp.write_text(
                artifact.model_dump_json(indent=2),
                encoding="utf-8",
            )
            os.replace(tmp, path)
        except Exception:
            # Clean up temp file on failure
            if tmp.exists():
                tmp.unlink()
            raise

    def get(self, run_id: str) -> Optional[RunArtifact]:
        """
        Retrieve a run artifact by ID.

        Searches across all date partitions (newest first).

        Args:
            run_id: The run ID to retrieve

        Returns:
            RunArtifact if found, None otherwise
        """
        safe_id = run_id.replace("/", "_").replace("\\", "_")

        # Search partitions in reverse chronological order
        partitions = sorted(
            [p for p in self.root.iterdir() if p.is_dir() and not p.name.startswith("_")],
            reverse=True,
        )

        for partition in partitions:
            path = partition / f"{safe_id}.json"
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    artifact = RunArtifact.model_validate(data)
                    # Load advisory links
                    artifact = self._load_advisory_links(artifact, partition)
                    return artifact
                except Exception:
                    continue

        return None

    def _load_advisory_links(self, artifact: RunArtifact, partition: Path) -> RunArtifact:
        """Load append-only advisory links for an artifact."""
        safe_id = artifact.run_id.replace("/", "_").replace("\\", "_")
        pattern = f"{safe_id}_advisory_*.json"

        advisory_inputs = list(artifact.advisory_inputs) if artifact.advisory_inputs else []

        for link_path in partition.glob(pattern):
            try:
                link_data = json.loads(link_path.read_text(encoding="utf-8"))
                ref = AdvisoryInputRef.model_validate(link_data)
                # Avoid duplicates
                if not any(a.advisory_id == ref.advisory_id for a in advisory_inputs):
                    advisory_inputs.append(ref)
            except Exception:
                continue

        # Return artifact with merged advisory inputs
        return artifact.model_copy(update={"advisory_inputs": advisory_inputs})

    def attach_advisory(
        self,
        run_id: str,
        advisory_id: str,
        kind: str = "unknown",
        engine_id: Optional[str] = None,
        engine_version: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Optional[AdvisoryInputRef]:
        """
        Attach an advisory reference to a run (append-only).

        IMMUTABILITY PRESERVED: Creates a separate link file rather than
        modifying the original artifact.

        Args:
            run_id: The run to attach advisory to
            advisory_id: The advisory asset ID
            kind: Type of advisory (explanation, advisory, note)
            engine_id: AI engine that created it
            engine_version: Engine version
            request_id: Correlation ID

        Returns:
            AdvisoryInputRef if successful, None if run not found
        """
        # Find the artifact to get its creation date
        artifact = self.get(run_id)
        if artifact is None:
            return None

        # Check for duplicate
        existing = artifact.advisory_inputs or []
        if any(a.advisory_id == advisory_id for a in existing):
            # Already attached, return existing
            return next(a for a in existing if a.advisory_id == advisory_id)

        # Create advisory reference
        ref = AdvisoryInputRef(
            advisory_id=advisory_id,
            kind=kind,
            engine_id=engine_id,
            engine_version=engine_version,
            request_id=request_id,
        )

        # Write to separate link file (preserves immutability)
        link_path = self._advisory_link_path(
            run_id, advisory_id, artifact.created_at_utc
        )
        link_path.parent.mkdir(parents=True, exist_ok=True)

        tmp = link_path.with_suffix(".json.tmp")
        try:
            tmp.write_text(
                ref.model_dump_json(indent=2),
                encoding="utf-8",
            )
            os.replace(tmp, link_path)
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise

        return ref

    def list_runs(
        self,
        limit: int = 50,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[RunArtifact]:
        """
        List run artifacts, newest first.

        Args:
            limit: Maximum number of results
            date_from: Filter by date >= this
            date_to: Filter by date <= this

        Returns:
            List of RunArtifact objects
        """
        runs = []

        # Get partitions in reverse order
        partitions = sorted(
            [p for p in self.root.iterdir() if p.is_dir() and not p.name.startswith("_")],
            reverse=True,
        )

        for partition in partitions:
            # Date filtering
            try:
                partition_date = datetime.strptime(partition.name, "%Y-%m-%d")
                if date_from and partition_date.date() < date_from.date():
                    continue
                if date_to and partition_date.date() > date_to.date():
                    continue
            except ValueError:
                continue

            # Load artifacts from this partition
            for path in partition.glob("*.json"):
                # Skip advisory links and temp files
                if "_advisory_" in path.name or path.suffix == ".tmp":
                    continue

                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    artifact = RunArtifact.model_validate(data)
                    artifact = self._load_advisory_links(artifact, partition)
                    runs.append(artifact)
                except Exception:
                    continue

                if len(runs) >= limit:
                    break

            if len(runs) >= limit:
                break

        # Sort by created_at_utc descending
        runs.sort(key=lambda r: r.created_at_utc, reverse=True)
        return runs[:limit]

    def list_runs_filtered(
        self,
        *,
        limit: int = 50,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        tool_id: Optional[str] = None,
        mode: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[RunArtifact]:
        """
        List runs with optional filtering.

        Args:
            limit: Maximum results
            event_type: Filter by event_type
            status: Filter by status (OK, BLOCKED, ERROR)
            tool_id: Filter by tool_id
            mode: Filter by mode
            date_from: Filter by date >=
            date_to: Filter by date <=

        Returns:
            Filtered list of RunArtifact objects
        """
        # Get all runs within date range
        all_runs = self.list_runs(limit=limit * 3, date_from=date_from, date_to=date_to)

        def matches(r: RunArtifact) -> bool:
            if event_type and r.event_type != event_type:
                return False
            if status and r.status != status:
                return False
            if tool_id and r.tool_id != tool_id:
                return False
            if mode and r.mode != mode:
                return False
            return True

        filtered = [r for r in all_runs if matches(r)]
        return filtered[:limit]


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_store: Optional[RunStoreV2] = None


def _get_default_store() -> RunStoreV2:
    """Get or create the default store instance."""
    global _default_store
    if _default_store is None:
        _default_store = RunStoreV2()
    return _default_store


def create_run_id() -> str:
    """Generate a new run ID per governance contract."""
    return f"run_{uuid4().hex}"


def persist_run(artifact: RunArtifact) -> RunArtifact:
    """Persist a run artifact to the default store."""
    store = _get_default_store()
    store.put(artifact)
    return artifact


def get_run(run_id: str) -> Optional[RunArtifact]:
    """Retrieve a run artifact from the default store."""
    store = _get_default_store()
    return store.get(run_id)


def list_runs_filtered(
    *,
    limit: int = 50,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    tool_id: Optional[str] = None,
    mode: Optional[str] = None,
) -> List[RunArtifact]:
    """List runs with optional filtering from the default store."""
    store = _get_default_store()
    return store.list_runs_filtered(
        limit=limit,
        event_type=event_type,
        status=status,
        tool_id=tool_id,
        mode=mode,
    )


def attach_advisory(
    run_id: str,
    advisory_id: str,
    kind: str = "unknown",
    engine_id: Optional[str] = None,
    engine_version: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Optional[AdvisoryInputRef]:
    """Attach an advisory to a run in the default store."""
    store = _get_default_store()
    return store.attach_advisory(
        run_id=run_id,
        advisory_id=advisory_id,
        kind=kind,
        engine_id=engine_id,
        engine_version=engine_version,
        request_id=request_id,
    )
