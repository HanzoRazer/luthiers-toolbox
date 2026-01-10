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
from .schemas_advisories import (
    RunAdvisoryLinkV1,
    IndexRunAdvisorySummaryV1,
    IndexAdvisoryLookupV1,
)
from .delete_audit import append_delete_audit, build_delete_audit_event
from .attachment_meta import AttachmentMetaIndex

# Index meta governance (System 2 hardening)
from .index_meta import (
    IndexMetaError,
    normalize_index_meta,
    validate_index_meta,
    extract_and_normalize_from_artifact,
)

# =============================================================================
# H3.6.2: Delete Rate Limiting
# =============================================================================

import time
from collections import defaultdict

# In-process rate limiter: {rate_limit_key: [timestamps]}
_DELETE_RATE_LIMIT: Dict[str, List[float]] = defaultdict(list)
_DELETE_RATE_LIMIT_LOCK = threading.Lock()

# Default: 10 deletes per minute per actor
DELETE_RATE_LIMIT_MAX = int(os.getenv("RMOS_DELETE_RATE_LIMIT_MAX", "10"))
DELETE_RATE_LIMIT_WINDOW_SEC = int(os.getenv("RMOS_DELETE_RATE_LIMIT_WINDOW", "60"))


class DeleteRateLimitError(Exception):
    """Raised when delete rate limit is exceeded."""
    def __init__(self, key: str, limit: int, window: int):
        self.key = key
        self.limit = limit
        self.window = window
        super().__init__(f"Rate limit exceeded for '{key}': max {limit} deletes per {window}s")


def _check_delete_rate_limit(key: str) -> None:
    """
    Check if a delete operation is allowed under rate limiting.

    Raises DeleteRateLimitError if limit exceeded.
    """
    if DELETE_RATE_LIMIT_MAX <= 0:
        return  # Rate limiting disabled

    now = time.time()
    cutoff = now - DELETE_RATE_LIMIT_WINDOW_SEC

    with _DELETE_RATE_LIMIT_LOCK:
        # Prune old entries
        _DELETE_RATE_LIMIT[key] = [t for t in _DELETE_RATE_LIMIT[key] if t > cutoff]

        if len(_DELETE_RATE_LIMIT[key]) >= DELETE_RATE_LIMIT_MAX:
            raise DeleteRateLimitError(key, DELETE_RATE_LIMIT_MAX, DELETE_RATE_LIMIT_WINDOW_SEC)

        # Record this attempt
        _DELETE_RATE_LIMIT[key].append(now)


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

    Bundle 09/10: Now includes lineage for parent_plan_run_id filtering.
    """
    # Extract lineage if present
    lineage_dict = None
    if artifact.lineage:
        lineage_dict = {
            "parent_plan_run_id": artifact.lineage.parent_plan_run_id,
        }
    elif artifact.meta and artifact.meta.get("parent_plan_run_id"):
        # Fallback: check meta for backwards compatibility
        lineage_dict = {
            "parent_plan_run_id": artifact.meta.get("parent_plan_run_id"),
        }

    return {
        "run_id": artifact.run_id,
        "created_at_utc": artifact.created_at_utc.isoformat() if artifact.created_at_utc else None,
        "event_type": getattr(artifact, 'event_type', None),
        "status": artifact.status,
        "workflow_session_id": getattr(artifact, 'workflow_session_id', None),
        "tool_id": artifact.tool_id,
        "mode": artifact.mode,
        "partition": artifact.created_at_utc.strftime("%Y-%m-%d") if artifact.created_at_utc else None,
        "meta": artifact.meta,  # Include meta for batch_label and session_id filtering
        "lineage": lineage_dict,  # Bundle 09: Include lineage for parent_plan_run_id filtering
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
        self._advisory_lookup_path = self.root / "_advisory_lookup.json"
        self._attachment_meta = AttachmentMetaIndex(self.root)

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

    # =========================================================================
    # Advisory Link + Index Glue Methods
    # =========================================================================

    def _read_advisory_lookup(self) -> Dict[str, Dict[str, Any]]:
        """
        Read global advisory lookup mapping advisory_id -> entry dict.

        Stored separately because _index.json is Dict[run_id -> meta].
        """
        if not self._advisory_lookup_path.exists():
            return {}
        try:
            txt = self._advisory_lookup_path.read_text(encoding="utf-8")
            obj = json.loads(txt) if txt.strip() else {}
            if isinstance(obj, dict):
                return obj
            return {}
        except Exception:
            return {}

    def _write_advisory_lookup(self, lookup: Dict[str, Dict[str, Any]]) -> None:
        """Write advisory lookup atomically."""
        tmp = self._advisory_lookup_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(lookup, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(str(tmp), str(self._advisory_lookup_path))

    def _upsert_advisory_lookup(self, entry: IndexAdvisoryLookupV1) -> None:
        lookup = self._read_advisory_lookup()
        lookup[entry.advisory_id] = entry.dict()
        self._write_advisory_lookup(lookup)

    def _append_run_advisory_rollup(self, run_id: str, summary: IndexRunAdvisorySummaryV1) -> None:
        """
        Store run-local advisory summaries inside _index.json meta for fast listing:
          index[run_id]["advisories"] = [ ... ]
        """
        index = self._read_index()
        meta = index.get(run_id) or {}
        advs = meta.get("advisories") or []
        # De-dupe by advisory_id
        existing_ids = {a.get("advisory_id") for a in advs if isinstance(a, dict)}
        if summary.advisory_id not in existing_ids:
            advs.append(summary.dict())
            meta["advisories"] = advs
            index[run_id] = meta
            self._write_index(index)

    def put_advisory_link(self, link: RunAdvisoryLinkV1) -> None:
        """
        Append-only: write a run_<run_id>_advisory_<advisory_id>.json link file,
        then update indices (_index.json rollup + _advisory_lookup.json).

        This DOES NOT modify the advisory blob (stored as attachment by sha256),
        and DOES NOT require modifying the run artifact JSON.
        """
        # Determine partition directory from the run artifact location
        artifact = self.get(link.run_id)
        if artifact is None:
            raise FileNotFoundError(f"run_id not found: {link.run_id}")

        # Compute the date partition dir
        created = getattr(artifact, "created_at_utc", None)
        if created is None:
            raise ValueError("run artifact missing created_at_utc")

        # created may be datetime; normalize:
        try:
            date_part = created.date().isoformat()
        except Exception:
            # fallback: assume ISO string with date prefix
            date_part = str(created)[:10]

        part_dir = self.root / date_part
        part_dir.mkdir(parents=True, exist_ok=True)

        link_path = part_dir / f"run_{link.run_id}_advisory_{link.advisory_id}.json"
        tmp = link_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(link.dict(), indent=2, sort_keys=True), encoding="utf-8")
        os.replace(str(tmp), str(link_path))

        # Update run-local rollup in _index.json
        summary = IndexRunAdvisorySummaryV1(
            advisory_id=link.advisory_id,
            sha256=link.advisory_sha256,
            kind=link.kind,
            mime=link.mime,
            size_bytes=link.size_bytes,
            created_at_utc=link.created_at_utc,
            status=link.status,
            tags=link.tags,
            confidence_max=link.confidence_max,
        )
        self._append_run_advisory_rollup(link.run_id, summary)

        # Update global advisory lookup
        lookup_entry = IndexAdvisoryLookupV1(
            advisory_id=link.advisory_id,
            run_id=link.run_id,
            sha256=link.advisory_sha256,
            kind=link.kind,
            mime=link.mime,
            size_bytes=link.size_bytes,
            created_at_utc=link.created_at_utc,
            status=link.status,
            tags=link.tags,
            confidence_max=link.confidence_max,
            bundle_sha256=link.bundle_sha256,
            manifest_sha256=link.manifest_sha256,
        )
        self._upsert_advisory_lookup(lookup_entry)

    def list_run_advisories(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Fast path: read from _index.json rollup. Returns list of summary dicts.
        """
        index = self._read_index()
        meta = index.get(run_id) or {}
        advs = meta.get("advisories") or []
        if isinstance(advs, list):
            return [a for a in advs if isinstance(a, dict)]
        return []

    def resolve_advisory(self, advisory_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve advisory_id -> lookup entry dict (contains sha256, run_id, etc).
        Blob retrieval should be done via attachments store using sha256.
        """
        lookup = self._read_advisory_lookup()
        entry = lookup.get(advisory_id)
        return entry if isinstance(entry, dict) else None

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
            # Start with base index fields (run_id, partition, created_at_utc, etc)
            base_meta = _extract_index_meta(artifact)

            # System 2 hardening: extract, normalize, and validate additional index_meta
            normalized_meta = extract_and_normalize_from_artifact(artifact)

            # Merge: base fields + normalized fields (normalized takes precedence for filter fields)
            index_meta = {**base_meta, **normalized_meta}

            # Validate index_meta (non-strict mode for backward compatibility)
            # Set strict=True once all artifact creation paths populate required fields
            try:
                validate_index_meta(
                    index_meta,
                    event_type=getattr(artifact, 'event_type', None),
                    strict=False,  # TODO: Enable strict=True after migration
                )
            except IndexMetaError as e:
                # Log but don't fail - we want to track drift without breaking existing flows
                import logging
                logging.getLogger(__name__).warning(
                    f"index_meta validation warning for {artifact.run_id}: {e}"
                )

            self._update_index_entry(artifact.run_id, index_meta)

            # Update global attachment meta index (best-effort)
            try:
                self._attachment_meta.update_from_artifact(artifact)
            except Exception:
                # Best-effort: do not fail run persistence if meta index update fails
                pass

            # Update recency index to keep /recent endpoint fresh (best-effort)
            try:
                from .attachment_meta import AttachmentRecentIndex
                recent_idx = AttachmentRecentIndex(self.root)
                recent_idx.rebuild_from_meta_index(self._attachment_meta)
            except Exception:
                # Best-effort: do not fail run persistence if recency index update fails
                pass
        except Exception:
            # Clean up temp file on failure
            if tmp.exists():
                tmp.unlink()
            raise

    def update_mutable_fields(self, artifact: RunArtifact) -> None:
        """
        Update mutable fields of an existing run artifact.

        CONTROLLED MUTABILITY: Only advisory_reviews field is allowed to be updated.
        This supports the variant review workflow where reviews are explicitly mutable.

        Args:
            artifact: The RunArtifact with updated mutable fields

        Raises:
            ValueError: If artifact doesn't exist
        """
        path = self._path_for(artifact.run_id, artifact.created_at_utc)

        if not path.exists():
            raise ValueError(f"Artifact {artifact.run_id} not found for update")

        # Atomic write: write to .tmp then rename
        tmp = path.with_suffix(".json.tmp")
        try:
            tmp.write_text(
                artifact.model_dump_json(indent=2),
                encoding="utf-8",
            )
            os.replace(tmp, path)

            # Update the global index with lightweight metadata
            # Start with base index fields (run_id, partition, created_at_utc, etc)
            base_meta = _extract_index_meta(artifact)

            # System 2 hardening: extract, normalize, and validate additional index_meta
            normalized_meta = extract_and_normalize_from_artifact(artifact)

            # Merge: base fields + normalized fields (normalized takes precedence for filter fields)
            index_meta = {**base_meta, **normalized_meta}

            # Validate index_meta (non-strict mode for backward compatibility)
            # Set strict=True once all artifact creation paths populate required fields
            try:
                validate_index_meta(
                    index_meta,
                    event_type=getattr(artifact, 'event_type', None),
                    strict=False,  # TODO: Enable strict=True after migration
                )
            except IndexMetaError as e:
                # Log but don't fail - we want to track drift without breaking existing flows
                import logging
                logging.getLogger(__name__).warning(
                    f"index_meta validation warning for {artifact.run_id}: {e}"
                )

            self._update_index_entry(artifact.run_id, index_meta)
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

    def delete_run(
        self,
        run_id: str,
        *,
        mode: str = "soft",
        reason: str,
        actor: Optional[str] = None,
        request_id: Optional[str] = None,
        rate_limit_key: Optional[str] = None,
        cascade: bool = True,
    ) -> Dict[str, Any]:
        """
        Delete a run artifact with audit logging.

        H3.6.2: Append-only audit log survives index compaction.

        Args:
            run_id: The run ID to delete
            mode: "soft" (index tombstone) or "hard" (remove files)
            reason: Required - why this deletion is happening
            actor: Optional actor/user performing the delete
            request_id: Optional correlation ID
            rate_limit_key: Key for rate limiting (defaults to actor or "anonymous")
            cascade: If True, also delete advisory links (attachments are shared blobs)

        Returns:
            Dict with deletion outcome:
            {
                "run_id": str,
                "deleted": bool,
                "mode": str,
                "index_updated": bool,
                "artifact_deleted": bool,
                "advisory_links_deleted": int,
                "partition": str | None,
            }

        Raises:
            ValueError: If reason is empty
            KeyError: If run_id not found
            DeleteRateLimitError: If rate limit exceeded
        """
        if not reason or not reason.strip():
            raise ValueError("Delete reason is required for audit trail")

        # Rate limiting
        limit_key = rate_limit_key or actor or "anonymous"
        try:
            _check_delete_rate_limit(limit_key)
        except DeleteRateLimitError as e:
            # Audit the rate limit rejection
            try:
                event = build_delete_audit_event(
                    run_id=run_id,
                    mode=mode,
                    reason=reason,
                    actor=actor,
                    request_id=request_id,
                    index_updated=False,
                    artifact_deleted=False,
                    attachments_deleted=0,
                    errors=f"Rate limited: {e}",
                    meta={"rate_limit_key": limit_key},
                )
                append_delete_audit(store_root=self.root, event=event)
            except Exception:
                pass
            raise

        result: Dict[str, Any] = {
            "run_id": run_id,
            "deleted": False,
            "mode": mode,
            "index_updated": False,
            "artifact_deleted": False,
            "advisory_links_deleted": 0,
            "partition": None,
        }

        error_msg: Optional[str] = None
        safe_id = run_id.replace("/", "_").replace("\\", "_")
        original_meta: Optional[Dict[str, Any]] = None

        try:
            # Find the artifact file
            artifact_path: Optional[Path] = None
            partition: Optional[str] = None

            partitions = sorted(
                [p for p in self.root.iterdir() if p.is_dir() and not p.name.startswith("_")],
                reverse=True,
            )

            for p in partitions:
                candidate = p / f"{safe_id}.json"
                if candidate.exists():
                    artifact_path = candidate
                    partition = p.name
                    break

            result["partition"] = partition

            if artifact_path is None:
                # Run not found - audit and raise
                error_msg = "Run not found"
                try:
                    event = build_delete_audit_event(
                        run_id=run_id,
                        mode=mode,
                        reason=reason,
                        actor=actor,
                        request_id=request_id,
                        index_updated=False,
                        artifact_deleted=False,
                        attachments_deleted=0,
                        errors=error_msg,
                        meta=None,
                    )
                    append_delete_audit(store_root=self.root, event=event)
                except Exception:
                    pass
                raise KeyError(f"Run not found: {run_id}")

            # Read original index entry for tombstone
            with _INDEX_LOCK:
                index = _read_json_file(self._index_path)
                original_meta = index.get(run_id)

                if mode == "soft":
                    # Soft delete: replace with tombstone
                    from datetime import datetime, timezone
                    tombstone = {
                        "run_id": run_id,
                        "deleted": True,
                        "deleted_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "deleted_reason": reason,
                        "deleted_by": actor,
                        "request_id": request_id,
                        # Preserve minimal original fields
                        "created_at_utc": original_meta.get("created_at_utc") if original_meta else None,
                        "status": original_meta.get("status") if original_meta else None,
                        "mode": original_meta.get("mode") if original_meta else None,
                        "partition": partition,
                    }
                    index[run_id] = tombstone
                    _write_json_file(self._index_path, index)
                    result["index_updated"] = True
                    result["deleted"] = True
                else:
                    # Hard delete: remove from index
                    if run_id in index:
                        del index[run_id]
                        _write_json_file(self._index_path, index)
                        result["index_updated"] = True

            if mode == "hard":
                # Delete advisory links if cascade
                if cascade and partition:
                    pattern = f"{safe_id}_advisory_*.json"
                    partition_dir = self.root / partition
                    for link_path in partition_dir.glob(pattern):
                        try:
                            link_path.unlink()
                            result["advisory_links_deleted"] += 1
                        except Exception:
                            pass

                # Delete the artifact file
                try:
                    artifact_path.unlink()
                    result["artifact_deleted"] = True
                    result["deleted"] = True
                except Exception as e:
                    error_msg = f"Failed to delete artifact: {e}"

        except KeyError:
            raise  # Re-raise KeyError for not found
        except DeleteRateLimitError:
            raise  # Re-raise rate limit error
        except Exception as e:
            error_msg = str(e)

        # H3.6.2: Append to audit log (best-effort, never blocks deletion)
        try:
            event = build_delete_audit_event(
                run_id=run_id,
                mode=mode,
                reason=reason,
                actor=actor,
                request_id=request_id,
                index_updated=result["index_updated"],
                artifact_deleted=result["artifact_deleted"],
                attachments_deleted=result["advisory_links_deleted"],
                errors=error_msg,
                meta={
                    "cascade": cascade,
                    "partition": result["partition"],
                    "rate_limit_key": limit_key,
                },
            )
            append_delete_audit(store_root=self.root, event=event)
        except Exception:
            # Audit must never break delete
            pass

        return result

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
        kind: Optional[str] = None,  # Alias for event_type
        status: Optional[str] = None,
        tool_id: Optional[str] = None,
        mode: Optional[str] = None,
        workflow_session_id: Optional[str] = None,
        batch_label: Optional[str] = None,
        session_id: Optional[str] = None,
        parent_plan_run_id: Optional[str] = None,  # Bundle 10: lineage filtering
        parent_batch_plan_artifact_id: Optional[str] = None,
        parent_batch_spec_artifact_id: Optional[str] = None,
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

            # Merge kind into event_type (kind is an alias)
            effective_event_type = event_type or kind
            if effective_event_type and m.get("event_type") != effective_event_type:
                return False
            if status and m.get("status") != status:
                return False
            if tool_id and m.get("tool_id") != tool_id:
                return False
            if mode and m.get("mode") != mode:
                return False
            if workflow_session_id and m.get("workflow_session_id") != workflow_session_id:
                return False

            # Filter by batch_label and session_id
            # These can be at top level (normalized) or nested in meta (legacy)
            nested_meta = m.get("meta") or {}
            m_batch_label = m.get("batch_label") or nested_meta.get("batch_label")
            m_session_id = m.get("session_id") or nested_meta.get("session_id")
            if batch_label and m_batch_label != batch_label:
                return False
            if session_id and m_session_id != session_id:
                return False

            # Bundle 10: Filter by parent_plan_run_id from lineage
            if parent_plan_run_id:
                lineage = m.get("lineage") or {}
                if lineage.get("parent_plan_run_id") != parent_plan_run_id:
                    # Fallback: check meta and top level for backwards compat
                    if m.get("parent_plan_run_id") != parent_plan_run_id:
                        if nested_meta.get("parent_plan_run_id") != parent_plan_run_id:
                            return False

            # Filter by parent_batch_plan_artifact_id from top-level/lineage/meta
            if parent_batch_plan_artifact_id:
                lineage = m.get("lineage") or {}
                # Check all possible locations
                found = (
                    m.get("parent_batch_plan_artifact_id") == parent_batch_plan_artifact_id or
                    lineage.get("parent_batch_plan_artifact_id") == parent_batch_plan_artifact_id or
                    nested_meta.get("parent_batch_plan_artifact_id") == parent_batch_plan_artifact_id or
                    m.get("batch_plan_artifact_id") == parent_batch_plan_artifact_id or
                    nested_meta.get("batch_plan_artifact_id") == parent_batch_plan_artifact_id
                )
                if not found:
                    return False

            # Filter by parent_batch_spec_artifact_id from top-level/lineage/meta
            if parent_batch_spec_artifact_id:
                lineage = m.get("lineage") or {}
                # Check all possible locations
                found = (
                    m.get("parent_batch_spec_artifact_id") == parent_batch_spec_artifact_id or
                    lineage.get("parent_batch_spec_artifact_id") == parent_batch_spec_artifact_id or
                    nested_meta.get("parent_batch_spec_artifact_id") == parent_batch_spec_artifact_id or
                    m.get("batch_spec_artifact_id") == parent_batch_spec_artifact_id or
                    nested_meta.get("batch_spec_artifact_id") == parent_batch_spec_artifact_id
                )
                if not found:
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


def store_artifact(
    *,
    kind: str,
    payload: Dict[str, Any],
    parent_id: str,
    session_id: str,
) -> str:
    """
    Helper to create and persist a run artifact with minimal boilerplate.
    Returns the generated run_id.
    """
    from .schemas import RunArtifact, utc_now

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        event_type=kind,
        status="OK",
        created_at_utc=utc_now(),
        payload=payload,
        meta={
            "parent_id": parent_id,
            "session_id": session_id,
        },
    )
    persist_run(artifact)
    return run_id


def update_run(artifact: RunArtifact) -> RunArtifact:
    """Update mutable fields of an existing run artifact."""
    store = _get_default_store()
    store.update_mutable_fields(artifact)
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
    kind: Optional[str] = None,  # Alias for event_type
    status: Optional[str] = None,
    tool_id: Optional[str] = None,
    mode: Optional[str] = None,
    workflow_session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    session_id: Optional[str] = None,
    parent_plan_run_id: Optional[str] = None,  # Bundle 10: lineage filtering
    parent_batch_plan_artifact_id: Optional[str] = None,
    parent_batch_spec_artifact_id: Optional[str] = None,
) -> List[RunArtifact]:
    """List runs with optional filtering from the default store."""
    store = _get_default_store()
    return store.list_runs_filtered(
        limit=limit,
        offset=offset,
        event_type=event_type,
        kind=kind,
        status=status,
        tool_id=tool_id,
        mode=mode,
        workflow_session_id=workflow_session_id,
        batch_label=batch_label,
        session_id=session_id,
        parent_plan_run_id=parent_plan_run_id,
        parent_batch_plan_artifact_id=parent_batch_plan_artifact_id,
        parent_batch_spec_artifact_id=parent_batch_spec_artifact_id,
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


def delete_run(
    run_id: str,
    *,
    mode: str = "soft",
    reason: str,
    actor: Optional[str] = None,
    request_id: Optional[str] = None,
    rate_limit_key: Optional[str] = None,
    cascade: bool = True,
) -> Dict[str, Any]:
    """
    Delete a run artifact from the default store with audit logging.

    H3.6.2: Append-only audit log survives index compaction.

    Args:
        run_id: The run ID to delete
        mode: "soft" (index tombstone) or "hard" (remove files)
        reason: Required - why this deletion is happening
        actor: Optional actor/user performing the delete
        request_id: Optional correlation ID
        rate_limit_key: Key for rate limiting (defaults to actor or "anonymous")
        cascade: If True, also delete advisory links

    Returns:
        Dict with deletion outcome

    Raises:
        ValueError: If reason is empty
        KeyError: If run_id not found
        DeleteRateLimitError: If rate limit exceeded
    """
    store = _get_default_store()
    return store.delete_run(
        run_id,
        mode=mode,
        reason=reason,
        actor=actor,
        request_id=request_id,
        rate_limit_key=rate_limit_key,
        cascade=cascade,
    )


# =============================================================================
# H2 Hardening: Cursor-based pagination + server-side filtering
# =============================================================================

def _norm(s: Any) -> str:
    """Normalize a value to lowercase string for comparison."""
    return str(s or "").strip().lower()


def _get_nested(d: Dict[str, Any], path: str) -> Any:
    """Get a nested value from a dict using dot notation."""
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _extract_sort_key(run: Dict[str, Any]) -> tuple:
    """
    Returns (created_at_utc, run_id) for stable sort.
    """
    ts = (
        _get_nested(run, "created_at_utc")
        or _get_nested(run, "meta.created_at_utc")
        or _get_nested(run, "request_summary.created_at_utc")
        or ""
    )
    # Handle datetime objects
    if hasattr(ts, 'isoformat'):
        ts = ts.isoformat()
    rid = str(run.get("run_id") or "")
    return (str(ts), rid)


def query_runs(
    *,
    kind: Optional[str] = None,
    mode: Optional[str] = None,
    tool_id: Optional[str] = None,
    status: Optional[str] = None,
    batch_label: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Query runs with filtering, returning dicts for convenience.

    Args:
        kind: Filter by event_type (e.g., "saw_compare_toolpaths")
        mode: Filter by mode
        tool_id: Filter by tool_id
        status: Filter by status
        batch_label: Filter by batch_label in meta
        session_id: Filter by session_id in meta
        limit: Maximum results
        offset: Skip this many results

    Returns:
        List of run artifact dicts (not RunArtifact objects)
    """
    runs = list_runs_filtered(
        event_type=kind,
        mode=mode,
        tool_id=tool_id,
        status=status,
        batch_label=batch_label,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    return [r.model_dump() for r in runs]


def query_recent(
    *,
    limit: int = 50,
    cursor: Optional[str] = None,
    mode: Optional[str] = None,
    tool_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Query recent runs with cursor-based pagination and server-side filtering.

    H2 Hardening Bundle - scales better than offset pagination.

    Args:
        limit: Maximum results (1-500)
        cursor: Pagination cursor in format "<created_at_utc>|<run_id>"
        mode: Filter by mode (art_studio, saw, router, etc.)
        tool_id: Filter by tool_id
        risk_level: Filter by risk level (GREEN, YELLOW, RED, ERROR, UNKNOWN)
        status: Filter by status (OK, BLOCKED, ERROR)
        source: Filter by source in meta or request_summary

    Returns:
        {
            "items": [run_dict, ...],
            "next_cursor": "..." | None
        }

    Cursor semantics:
        - newest first
        - if cursor provided, returns items strictly *older* than cursor
    """
    store = _get_default_store()
    limit = max(1, min(int(limit or 50), 500))

    # Over-fetch to allow for filtering
    fetch_n = limit * 8

    # Get runs as dicts
    runs = store.list_runs(limit=fetch_n)
    items = [r.model_dump() for r in runs]

    # Sort newest first using (ts, run_id)
    items.sort(key=_extract_sort_key, reverse=True)

    # Parse cursor
    cursor_ts = cursor_id = None
    if cursor:
        try:
            cursor_ts, cursor_id = cursor.split("|", 1)
        except Exception:
            cursor_ts, cursor_id = None, None

    def is_older_than_cursor(r: Dict[str, Any]) -> bool:
        if not cursor_ts:
            return True
        ts, rid = _extract_sort_key(r)
        # strictly older than cursor
        if ts < cursor_ts:
            return True
        if ts == cursor_ts and rid < (cursor_id or ""):
            return True
        return False

    def match(r: Dict[str, Any]) -> bool:
        if mode and _norm(r.get("mode")) != _norm(mode):
            return False

        if status and _norm(r.get("status")) != _norm(status):
            return False

        if tool_id:
            v = _get_nested(r, "request_summary.tool_id") or r.get("tool_id")
            if _norm(v) != _norm(tool_id):
                return False

        if source:
            v = _get_nested(r, "request_summary.source") or _get_nested(r, "meta.source") or r.get("source")
            if _norm(v) != _norm(source):
                return False

        if risk_level:
            v = (
                _get_nested(r, "decision.risk_level")
                or _get_nested(r, "decision.risk_bucket")
                or _get_nested(r, "feasibility.risk_level")
                or _get_nested(r, "feasibility.risk_bucket")
            )
            if _norm(v) != _norm(risk_level):
                return False

        return True

    out: List[Dict[str, Any]] = []
    for r in items:
        if not is_older_than_cursor(r):
            continue
        if not match(r):
            continue
        out.append(r)
        if len(out) >= limit:
            break

    next_cursor = None
    if out:
        ts, rid = _extract_sort_key(out[-1])
        if ts and rid:
            next_cursor = f"{ts}|{rid}"

    return {"items": out, "next_cursor": next_cursor}
