"""RMOS Run Artifact Store v2 - Date-Partitioned, Immutable"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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

# Rate limiting (H3.6.2) — extracted WP-3
from .store_ratelimit import (
    DeleteRateLimitError,
    check_delete_rate_limit as _check_delete_rate_limit,
)

# Completeness guard — extracted WP-3
from .store_completeness import (
    REQUIRED_INVARIANTS,
    CompletenessViolation,
    check_completeness,
    create_blocked_artifact_for_violations,
    validate_and_persist,
)

_log = logging.getLogger(__name__)

# Default storage path per governance contract
STORE_ROOT_DEFAULT = "services/api/data/runs/rmos"

# Thread lock for index operations
_INDEX_LOCK = threading.Lock()

def _get_store_root() -> str:
    """Get the store root from environment or default."""
    return os.getenv("RMOS_RUNS_DIR", STORE_ROOT_DEFAULT)

def _extract_index_meta(artifact: RunArtifact) -> Dict[str, Any]:
    """Extract lightweight metadata for the index."""
    lineage_dict = {"parent_plan_run_id": artifact.lineage.parent_plan_run_id} if artifact.lineage else (
        {"parent_plan_run_id": artifact.meta.get("parent_plan_run_id")} if artifact.meta and artifact.meta.get("parent_plan_run_id") else None)
    return {"run_id": artifact.run_id, "created_at_utc": artifact.created_at_utc.isoformat() if artifact.created_at_utc else None,
        "event_type": getattr(artifact, 'event_type', None), "status": artifact.status,
        "workflow_session_id": getattr(artifact, 'workflow_session_id', None), "tool_id": artifact.tool_id, "mode": artifact.mode,
        "partition": artifact.created_at_utc.strftime("%Y-%m-%d") if artifact.created_at_utc else None, "meta": artifact.meta, "lineage": lineage_dict}

def _read_json_file(path: Path) -> Dict[str, Any]:
    """Read a JSON file, returning empty dict if not found."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):  # WP-1: narrowed from except Exception
        return {}

def _write_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Atomically write a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:  # WP-1: narrowed from except Exception
        if tmp.exists():
            tmp.unlink()
        raise

class RunStoreV2:
    """Date-partitioned, immutable run artifact store."""

    def __init__(self, root_dir: Optional[str] = None):
        """Initialize the store."""
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
        """Rebuild the index by scanning all date partitions."""
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
                except (json.JSONDecodeError, ValueError, OSError, KeyError):  # WP-1: narrowed from except Exception
                    continue

        self._write_index(index)
        return len(index)

    # =========================================================================
    # Shared index helpers
    # =========================================================================

    def _update_index_from_artifact(self, artifact: RunArtifact) -> None:
        """Build merged index meta and update the index entry for *artifact*.

        Shared by ``put()`` and ``update_mutable_fields()`` to avoid duplication.
        """
        base_meta = _extract_index_meta(artifact)
        normalized_meta = extract_and_normalize_from_artifact(artifact)
        index_meta = {**base_meta, **normalized_meta}

        try:
            validate_index_meta(
                index_meta,
                event_type=getattr(artifact, "event_type", None),
                strict=False,  # TODO: Enable strict=True after migration
            )
        except IndexMetaError as e:
            _log.warning("index_meta validation warning for %s: %s", artifact.run_id, e)

        self._update_index_entry(artifact.run_id, index_meta)

    # =========================================================================
    # Advisory Link + Index Glue Methods
    # =========================================================================

    def _read_advisory_lookup(self) -> Dict[str, Dict[str, Any]]:
        """Read global advisory lookup mapping advisory_id -> entry dict."""
        if not self._advisory_lookup_path.exists(): return {}
        try:
            txt = self._advisory_lookup_path.read_text(encoding="utf-8")
            obj = json.loads(txt) if txt.strip() else {}
            return obj if isinstance(obj, dict) else {}
        except (json.JSONDecodeError, OSError): return {}

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
        """Store run-local advisory summaries in _index.json for fast listing."""
        index = self._read_index()
        meta = index.get(run_id) or {}
        advs = meta.get("advisories") or []
        existing_ids = {a.get("advisory_id") for a in advs if isinstance(a, dict)}
        if summary.advisory_id not in existing_ids:
            advs.append(summary.dict()); meta["advisories"] = advs; index[run_id] = meta; self._write_index(index)

    def put_advisory_link(self, link: RunAdvisoryLinkV1) -> None:
        """Append-only: write a run_<run_id>_advisory_<advisory_id>.json link file,"""
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
        except (AttributeError, TypeError):  # WP-1: narrowed from except Exception
            # fallback: assume ISO string with date prefix
            date_part = str(created)[:10]

        part_dir = self.root / date_part
        part_dir.mkdir(parents=True, exist_ok=True)

        link_path = part_dir / f"run_{link.run_id}_advisory_{link.advisory_id}.json"
        tmp = link_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(link.dict(), indent=2, sort_keys=True), encoding="utf-8")
        os.replace(str(tmp), str(link_path))

        # Update run-local rollup in _index.json
        summary = IndexRunAdvisorySummaryV1(advisory_id=link.advisory_id, sha256=link.advisory_sha256, kind=link.kind,
            mime=link.mime, size_bytes=link.size_bytes, created_at_utc=link.created_at_utc, status=link.status,
            tags=link.tags, confidence_max=link.confidence_max)
        self._append_run_advisory_rollup(link.run_id, summary)

        # Update global advisory lookup
        lookup_entry = IndexAdvisoryLookupV1(advisory_id=link.advisory_id, run_id=link.run_id, sha256=link.advisory_sha256,
            kind=link.kind, mime=link.mime, size_bytes=link.size_bytes, created_at_utc=link.created_at_utc, status=link.status,
            tags=link.tags, confidence_max=link.confidence_max, bundle_sha256=link.bundle_sha256, manifest_sha256=link.manifest_sha256)
        self._upsert_advisory_lookup(lookup_entry)

    def list_run_advisories(self, run_id: str) -> List[Dict[str, Any]]:
        """Fast path: read from _index.json rollup."""
        meta = self._read_index().get(run_id) or {}
        advs = meta.get("advisories") or []
        return [a for a in advs if isinstance(a, dict)] if isinstance(advs, list) else []

    def resolve_advisory(self, advisory_id: str) -> Optional[Dict[str, Any]]:
        """Resolve advisory_id -> lookup entry dict."""
        entry = self._read_advisory_lookup().get(advisory_id)
        return entry if isinstance(entry, dict) else None

    def _date_partition(self, dt: datetime) -> str:
        """Get date partition string from datetime."""
        return dt.strftime("%Y-%m-%d")

    def _path_for(self, run_id: str, created_at: datetime) -> Path:
        """Get the file path for a run artifact."""
        return self.root / self._date_partition(created_at) / f"{run_id.replace('/', '_').replace(chr(92), '_')}.json"

    def _advisory_link_path(self, run_id: str, advisory_id: str, created_at: datetime) -> Path:
        """Get the file path for an advisory link."""
        partition = self._date_partition(created_at)
        safe = lambda s: s.replace("/", "_").replace(chr(92), "_")
        return self.root / partition / f"{safe(run_id)}_advisory_{safe(advisory_id)}.json"

    def put(self, artifact: RunArtifact) -> None:
        """Write a run artifact to storage."""
        path = self._path_for(artifact.run_id, artifact.created_at_utc)

        if path.exists():
            raise ValueError(f"Artifact {artifact.run_id} already exists. Run artifacts are immutable per governance contract.")

        # Ensure partition directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        tmp = path.with_suffix(".json.tmp")
        try:
            tmp.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
            os.replace(tmp, path)
            self._update_index_from_artifact(artifact)
            try: self._attachment_meta.update_from_artifact(artifact)
            except (OSError, ValueError, TypeError, KeyError): pass
            try:
                from .attachment_meta import AttachmentRecentIndex
                AttachmentRecentIndex(self.root).rebuild_from_meta_index(self._attachment_meta)
            except (ImportError, OSError, ValueError, TypeError): pass
        except OSError:
            if tmp.exists(): tmp.unlink()
            raise

    def update_mutable_fields(self, artifact: RunArtifact) -> None:
        """Update mutable fields of an existing run artifact."""
        path = self._path_for(artifact.run_id, artifact.created_at_utc)
        if not path.exists(): raise ValueError(f"Artifact {artifact.run_id} not found for update")
        tmp = path.with_suffix(".json.tmp")
        try:
            tmp.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
            os.replace(tmp, path)
            self._update_index_from_artifact(artifact)
        except OSError:
            if tmp.exists(): tmp.unlink()
            raise

    def get(self, run_id: str) -> Optional[RunArtifact]:
        """Retrieve a run artifact by ID."""
        safe_id = run_id.replace("/", "_").replace(chr(92), "_")
        partitions = sorted([p for p in self.root.iterdir() if p.is_dir() and not p.name.startswith("_")], reverse=True)
        for partition in partitions:
            path = partition / f"{safe_id}.json"
            if path.exists():
                try:
                    artifact = RunArtifact.model_validate(json.loads(path.read_text(encoding="utf-8")))
                    return self._load_advisory_links(artifact, partition)
                except (json.JSONDecodeError, ValueError, OSError, KeyError): continue
        return None

    def _load_advisory_links(self, artifact: RunArtifact, partition: Path) -> RunArtifact:
        """Load append-only advisory links for an artifact."""
        safe_id = artifact.run_id.replace("/", "_").replace(chr(92), "_")
        advisory_inputs = list(artifact.advisory_inputs) if artifact.advisory_inputs else []
        for link_path in partition.glob(f"{safe_id}_advisory_*.json"):
            try:
                ref = AdvisoryInputRef.model_validate(json.loads(link_path.read_text(encoding="utf-8")))
                if not any(a.advisory_id == ref.advisory_id for a in advisory_inputs): advisory_inputs.append(ref)
            except (json.JSONDecodeError, ValueError, OSError, KeyError): continue
        return artifact.model_copy(update={"advisory_inputs": advisory_inputs})

    def attach_advisory(self, run_id: str, advisory_id: str, kind: str = "unknown",
                        engine_id: Optional[str] = None, engine_version: Optional[str] = None,
                        request_id: Optional[str] = None) -> Optional[AdvisoryInputRef]:
        """Attach an advisory reference to a run (append-only)."""
        artifact = self.get(run_id)
        if artifact is None: return None
        existing = artifact.advisory_inputs or []
        if any(a.advisory_id == advisory_id for a in existing):
            return next(a for a in existing if a.advisory_id == advisory_id)
        ref = AdvisoryInputRef(advisory_id=advisory_id, kind=kind, engine_id=engine_id,
            engine_version=engine_version, request_id=request_id)
        link_path = self._advisory_link_path(run_id, advisory_id, artifact.created_at_utc)
        link_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = link_path.with_suffix(".json.tmp")
        try:
            tmp.write_text(ref.model_dump_json(indent=2), encoding="utf-8")
            os.replace(tmp, link_path)
        except OSError:
            if tmp.exists(): tmp.unlink()
            raise
        return ref

    def delete_run(self, run_id: str, *, mode: str = "soft", reason: str, actor: Optional[str] = None,
                   request_id: Optional[str] = None, rate_limit_key: Optional[str] = None, cascade: bool = True) -> Dict[str, Any]:
        """Delete a run artifact with audit logging."""
        from .store_delete import execute_delete
        return execute_delete(root=self.root, index_path=self._index_path, index_lock=_INDEX_LOCK,
            read_json=_read_json_file, write_json=_write_json_file, run_id=run_id, mode=mode, reason=reason,
            actor=actor, request_id=request_id, rate_limit_key=rate_limit_key, cascade=cascade,
            check_rate_limit=_check_delete_rate_limit, DeleteRateLimitError_cls=DeleteRateLimitError)

    def list_runs(self, limit: int = 50, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> List[RunArtifact]:
        """List run artifacts, newest first."""
        runs = []
        partitions = sorted([p for p in self.root.iterdir() if p.is_dir() and not p.name.startswith("_")], reverse=True)
        for partition in partitions:
            try:
                pd = datetime.strptime(partition.name, "%Y-%m-%d")
                if date_from and pd.date() < date_from.date(): continue
                if date_to and pd.date() > date_to.date(): continue
            except ValueError: continue
            for path in partition.glob("*.json"):
                if "_advisory_" in path.name or path.suffix == ".tmp": continue
                try:
                    artifact = self._load_advisory_links(RunArtifact.model_validate(json.loads(path.read_text(encoding="utf-8"))), partition)
                    runs.append(artifact)
                except (json.JSONDecodeError, ValueError, OSError, KeyError): continue
                if len(runs) >= limit: break
            if len(runs) >= limit: break
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
        """List runs with optional filtering using the index."""
        from .store_filter import matches_index_meta

        index = self._read_index()
        if not index:
            self.rebuild_index()
            index = self._read_index()

        fkw = dict(
            event_type=event_type, kind=kind, status=status, tool_id=tool_id,
            mode=mode, workflow_session_id=workflow_session_id,
            batch_label=batch_label, session_id=session_id,
            parent_plan_run_id=parent_plan_run_id,
            parent_batch_plan_artifact_id=parent_batch_plan_artifact_id,
            parent_batch_spec_artifact_id=parent_batch_spec_artifact_id,
            date_from=date_from, date_to=date_to,
        )
        matching_metas = [m for m in index.values() if matches_index_meta(m, **fkw)]

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
                    except (json.JSONDecodeError, ValueError, OSError, KeyError):  # WP-1: narrowed from except Exception
                        pass

            # Fall back to full search if partition lookup failed
            if artifact is None:
                artifact = self.get(run_id)

            if artifact:
                results.append(artifact)

        return results

    def count_runs_filtered(self, *, event_type: Optional[str] = None, status: Optional[str] = None,
                            tool_id: Optional[str] = None, mode: Optional[str] = None,
                            workflow_session_id: Optional[str] = None, date_from: Optional[datetime] = None,
                            date_to: Optional[datetime] = None) -> int:
        """Count runs matching filters using the index (fast)."""
        from .store_filter import matches_index_meta

        index = self._read_index()
        if not index:
            self.rebuild_index()
            index = self._read_index()

        fkw = dict(
            event_type=event_type, status=status, tool_id=tool_id,
            mode=mode, workflow_session_id=workflow_session_id,
            date_from=date_from, date_to=date_to,
        )
        return sum(1 for m in index.values() if matches_index_meta(m, **fkw))

# =============================================================================
# Module-level convenience API (re-exported for backward compatibility)
# =============================================================================
# Moved to store_api.py — re-export all public names so existing imports work.

from .store_api import (create_run_id, persist_run, store_artifact, update_run, get_run,  # noqa: E402
    list_runs_filtered, count_runs_filtered, rebuild_index, attach_advisory, delete_run, query_runs,
    query_recent, _get_default_store, _default_store, _norm, _get_nested, _extract_sort_key)
