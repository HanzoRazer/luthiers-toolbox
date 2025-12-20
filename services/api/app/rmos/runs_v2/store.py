"""
RMOS Run Artifact Store v2 - Date-Partitioned, Immutable

Governance-compliant storage implementation per RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md.

Key Features:
- Date-partitioned directory structure: {YYYY-MM-DD}/{run_id}.json
- Immutable artifacts (write-once, never modified)
- Atomic writes via .tmp + os.replace()
- Append-only advisory links (preserves immutability)
- Thread-safe with file locking
- Global index for fast list/filter/count operations (_index.json)
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .schemas import RunArtifact, AdvisoryInputRef, Hashes, RunDecision, RunOutputs


# Default storage path per governance contract
STORE_ROOT_DEFAULT = "services/api/data/runs/rmos"

# Thread lock for index operations
_INDEX_LOCK = threading.Lock()


# =============================================================================
# COMPLETENESS GUARD: Required Invariants Check
# =============================================================================

# Required fields per RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md
REQUIRED_INVARIANTS = [
    ("hashes.feasibility_sha256", "feasibility_sha256 is required for audit"),
    ("decision.risk_level", "risk_level is required for safety classification"),
]


class CompletenessViolation:
    """Details of a completeness violation."""
    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason

    def __str__(self) -> str:
        return f"{self.field}: {self.reason}"


def check_completeness(
    *,
    feasibility_sha256: Optional[str] = None,
    risk_level: Optional[str] = None,
    feasibility: Optional[Dict[str, Any]] = None,
) -> List[CompletenessViolation]:
    """
    Check if required invariants are present.

    Returns list of violations (empty if compliant).

    Args:
        feasibility_sha256: Hash of server-computed feasibility
        risk_level: Risk classification (GREEN, YELLOW, RED, etc.)
        feasibility: Feasibility dict (used to extract sha256 if not provided)

    Returns:
        List of CompletenessViolation objects (empty if all required fields present)
    """
    violations = []

    # Check feasibility_sha256
    if not feasibility_sha256:
        # Try to extract from feasibility dict
        if feasibility and isinstance(feasibility, dict):
            feasibility_sha256 = feasibility.get("sha256") or feasibility.get("hash")
        if not feasibility_sha256:
            violations.append(CompletenessViolation(
                "hashes.feasibility_sha256",
                "Required for audit trail - hash of server-computed feasibility"
            ))

    # Check risk_level
    if not risk_level or not risk_level.strip():
        violations.append(CompletenessViolation(
            "decision.risk_level",
            "Required for safety classification - must be GREEN, YELLOW, RED, UNKNOWN, or ERROR"
        ))

    return violations


def create_blocked_artifact_for_violations(
    *,
    run_id: str,
    mode: str,
    tool_id: str,
    violations: List[CompletenessViolation],
    request_summary: Optional[Dict[str, Any]] = None,
    feasibility: Optional[Dict[str, Any]] = None,
) -> RunArtifact:
    """
    Create a BLOCKED artifact when required invariants are missing.

    This ensures every request creates an artifact for audit trail,
    even when the request is incomplete.

    Args:
        run_id: Unique run identifier
        mode: Operation mode
        tool_id: Tool identifier
        violations: List of completeness violations
        request_summary: Original request (sanitized)
        feasibility: Server-computed feasibility (if available)

    Returns:
        RunArtifact with status=BLOCKED and block_reason explaining violations
    """
    violation_details = "; ".join(str(v) for v in violations)
    block_reason = f"Completeness guard: missing required fields - {violation_details}"

    # Use placeholder hash if not provided (indicates incomplete data)
    placeholder_hash = "0" * 64

    return RunArtifact(
        run_id=run_id,
        mode=mode,
        tool_id=tool_id,
        status="BLOCKED",
        request_summary=request_summary or {},
        feasibility=feasibility or {},
        decision=RunDecision(
            risk_level="ERROR",
            block_reason=block_reason,
            warnings=[f"Completeness violation: {v}" for v in violations],
            details={"violations": [{"field": v.field, "reason": v.reason} for v in violations]},
        ),
        hashes=Hashes(
            feasibility_sha256=placeholder_hash,  # Placeholder - incomplete data
        ),
        outputs=RunOutputs(),
        meta={"completeness_guard": True, "violation_count": len(violations)},
    )


def validate_and_persist(
    *,
    run_id: str,
    mode: str,
    tool_id: str,
    status: str,
    request_summary: Dict[str, Any],
    feasibility: Dict[str, Any],
    feasibility_sha256: Optional[str] = None,
    risk_level: Optional[str] = None,
    decision_score: Optional[float] = None,
    decision_warnings: Optional[List[str]] = None,
    decision_details: Optional[Dict[str, Any]] = None,
    outputs: Optional[RunOutputs] = None,
    block_reason: Optional[str] = None,
    toolpaths_sha256: Optional[str] = None,
    gcode_sha256: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> RunArtifact:
    """
    Validate completeness and persist artifact.

    COMPLETENESS GUARD:
    - If required invariants are missing, creates BLOCKED artifact
    - Still persists the artifact (for audit trail)
    - Returns the artifact (caller can check status)

    This is the recommended entry point for creating run artifacts.

    Args:
        run_id: Unique run identifier
        mode: Operation mode (saw, router, etc.)
        tool_id: Tool identifier
        status: Intended status (OK, BLOCKED, ERROR) - may be overridden if incomplete
        request_summary: Sanitized request summary
        feasibility: Server-computed feasibility
        feasibility_sha256: Hash of feasibility (REQUIRED)
        risk_level: Risk classification (REQUIRED)
        decision_score: Numeric score (optional)
        decision_warnings: Warning messages (optional)
        decision_details: Additional decision context (optional)
        outputs: Generated outputs (optional)
        block_reason: Why blocked (if status=BLOCKED)
        toolpaths_sha256: Hash of toolpaths (if generated)
        gcode_sha256: Hash of G-code (if generated)
        meta: Free-form metadata (optional)

    Returns:
        Persisted RunArtifact (check status for BLOCKED due to completeness)
    """
    # Check completeness
    violations = check_completeness(
        feasibility_sha256=feasibility_sha256,
        risk_level=risk_level,
        feasibility=feasibility,
    )

    if violations:
        # Create BLOCKED artifact for audit trail
        artifact = create_blocked_artifact_for_violations(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            violations=violations,
            request_summary=request_summary,
            feasibility=feasibility,
        )
    else:
        # All required fields present - create normal artifact
        artifact = RunArtifact(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            status=status,
            request_summary=request_summary,
            feasibility=feasibility,
            decision=RunDecision(
                risk_level=risk_level,
                score=decision_score,
                block_reason=block_reason,
                warnings=decision_warnings or [],
                details=decision_details or {},
            ),
            hashes=Hashes(
                feasibility_sha256=feasibility_sha256,
                toolpaths_sha256=toolpaths_sha256,
                gcode_sha256=gcode_sha256,
            ),
            outputs=outputs or RunOutputs(),
            meta=meta or {},
        )

    # Persist (always - for audit trail)
    store = _get_default_store()
    store.put(artifact)

    return artifact


def _get_store_root() -> str:
    """Get the store root from environment or default."""
    return os.getenv("RMOS_RUNS_DIR", STORE_ROOT_DEFAULT)


def _extract_index_meta(artifact: RunArtifact) -> Dict[str, Any]:
    """
    Extract lightweight metadata for the index.

    Only includes fields needed for list/filter/count operations.
    """
    return {
        "run_id": artifact.run_id,
        "created_at_utc": artifact.created_at_utc.isoformat() if artifact.created_at_utc else None,
        "event_type": getattr(artifact, 'event_type', None),
        "status": artifact.status,
        "workflow_session_id": getattr(artifact, 'workflow_session_id', None),
        "tool_id": artifact.tool_id,
        "mode": artifact.mode,
        "partition": artifact.created_at_utc.strftime("%Y-%m-%d") if artifact.created_at_utc else None,
    }


def _read_json_file(path: Path) -> Dict[str, Any]:
    """Read a JSON file, returning empty dict if not found."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Atomically write a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


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
        self._index_path = self.root / "_index.json"

    def _read_index(self) -> Dict[str, Dict[str, Any]]:
        """Read the global index file."""
        with _INDEX_LOCK:
            return _read_json_file(self._index_path)

    def _write_index(self, index: Dict[str, Dict[str, Any]]) -> None:
        """Write the global index file atomically."""
        with _INDEX_LOCK:
            _write_json_file(self._index_path, index)

    def _update_index_entry(self, run_id: str, meta: Dict[str, Any]) -> None:
        """Add or update a single entry in the index."""
        with _INDEX_LOCK:
            index = _read_json_file(self._index_path)
            index[run_id] = meta
            _write_json_file(self._index_path, index)

    def rebuild_index(self) -> int:
        """
        Rebuild the index by scanning all date partitions.

        Returns:
            Number of runs indexed
        """
        index: Dict[str, Dict[str, Any]] = {}

        partitions = [
            p for p in self.root.iterdir()
            if p.is_dir() and not p.name.startswith("_")
        ]

        for partition in partitions:
            for path in partition.glob("*.json"):
                # Skip advisory links and temp files
                if "_advisory_" in path.name or path.suffix == ".tmp":
                    continue

                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    artifact = RunArtifact.model_validate(data)
                    index[artifact.run_id] = _extract_index_meta(artifact)
                except Exception:
                    continue

        self._write_index(index)
        return len(index)

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

            # Update the global index with lightweight metadata
            self._update_index_entry(artifact.run_id, _extract_index_meta(artifact))
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
        offset: int = 0,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        tool_id: Optional[str] = None,
        mode: Optional[str] = None,
        workflow_session_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[RunArtifact]:
        """
        List runs with optional filtering using the index.

        Uses the lightweight index for fast filtering, then loads
        only the artifacts needed for the result page.

        Args:
            limit: Maximum results
            offset: Number of results to skip (for pagination)
            event_type: Filter by event_type
            status: Filter by status (OK, BLOCKED, ERROR)
            tool_id: Filter by tool_id
            mode: Filter by mode
            workflow_session_id: Filter by workflow session linkage
            date_from: Filter by date >=
            date_to: Filter by date <=

        Returns:
            Filtered list of RunArtifact objects
        """
        index = self._read_index()

        # If index is empty, rebuild it from partitions
        if not index:
            self.rebuild_index()
            index = self._read_index()

        def matches_meta(m: Dict[str, Any]) -> bool:
            # Date filtering
            if date_from or date_to:
                created = m.get("created_at_utc")
                if created:
                    try:
                        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        if date_from and created_dt < date_from:
                            return False
                        if date_to and created_dt > date_to:
                            return False
                    except Exception:
                        pass

            if event_type and m.get("event_type") != event_type:
                return False
            if status and m.get("status") != status:
                return False
            if tool_id and m.get("tool_id") != tool_id:
                return False
            if mode and m.get("mode") != mode:
                return False
            if workflow_session_id and m.get("workflow_session_id") != workflow_session_id:
                return False
            return True

        # Filter using index metadata
        matching_metas = [m for m in index.values() if matches_meta(m)]

        # Sort by created_at_utc descending
        matching_metas.sort(
            key=lambda m: m.get("created_at_utc") or "",
            reverse=True
        )

        # Apply pagination
        page_metas = matching_metas[offset:offset + limit]

        # Load full artifacts only for the page
        results: List[RunArtifact] = []
        for meta in page_metas:
            run_id = meta.get("run_id")
            partition = meta.get("partition")
            if not run_id:
                continue

            # Try to load from the known partition first
            artifact = None
            if partition:
                path = self.root / partition / f"{run_id.replace('/', '_').replace(chr(92), '_')}.json"
                if path.exists():
                    try:
                        data = json.loads(path.read_text(encoding="utf-8"))
                        artifact = RunArtifact.model_validate(data)
                        artifact = self._load_advisory_links(artifact, path.parent)
                    except Exception:
                        pass

            # Fall back to full search if partition lookup failed
            if artifact is None:
                artifact = self.get(run_id)

            if artifact:
                results.append(artifact)

        return results

    def count_runs_filtered(
        self,
        *,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        tool_id: Optional[str] = None,
        mode: Optional[str] = None,
        workflow_session_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """
        Count runs matching filters using the index (fast).

        Uses the lightweight index for efficient counting without
        loading full artifacts.
        """
        index = self._read_index()

        # If index is empty, fall back to partition scan
        if not index:
            # Rebuild index to populate it
            self.rebuild_index()
            index = self._read_index()

        def matches_meta(m: Dict[str, Any]) -> bool:
            # Date filtering
            if date_from or date_to:
                created = m.get("created_at_utc")
                if created:
                    try:
                        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        if date_from and created_dt < date_from:
                            return False
                        if date_to and created_dt > date_to:
                            return False
                    except Exception:
                        pass

            if event_type and m.get("event_type") != event_type:
                return False
            if status and m.get("status") != status:
                return False
            if tool_id and m.get("tool_id") != tool_id:
                return False
            if mode and m.get("mode") != mode:
                return False
            if workflow_session_id and m.get("workflow_session_id") != workflow_session_id:
                return False
            return True

        return sum(1 for m in index.values() if matches_meta(m))


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
    offset: int = 0,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    tool_id: Optional[str] = None,
    mode: Optional[str] = None,
    workflow_session_id: Optional[str] = None,
) -> List[RunArtifact]:
    """List runs with optional filtering from the default store."""
    store = _get_default_store()
    return store.list_runs_filtered(
        limit=limit,
        offset=offset,
        event_type=event_type,
        status=status,
        tool_id=tool_id,
        mode=mode,
        workflow_session_id=workflow_session_id,
    )


def count_runs_filtered(
    *,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    tool_id: Optional[str] = None,
    mode: Optional[str] = None,
    workflow_session_id: Optional[str] = None,
) -> int:
    """Count runs matching filters from the default store."""
    store = _get_default_store()
    return store.count_runs_filtered(
        event_type=event_type,
        status=status,
        tool_id=tool_id,
        mode=mode,
        workflow_session_id=workflow_session_id,
    )


def rebuild_index() -> int:
    """Rebuild the global index from the default store."""
    store = _get_default_store()
    return store.rebuild_index()


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
