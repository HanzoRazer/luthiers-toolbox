"""RunStoreV2 delete operation — extracted from store.py for size reduction."""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .delete_audit import append_delete_audit, build_delete_audit_event

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers extracted from execute_delete (CC-31 → ≤15)
# ---------------------------------------------------------------------------

def _safe_audit(
    root: Path,
    *,
    run_id: str,
    mode: str,
    reason: str,
    actor: Optional[str],
    request_id: Optional[str],
    index_updated: bool,
    artifact_deleted: bool,
    attachments_deleted: int,
    errors: Optional[str],
    meta: Optional[dict],
    label: str = "final",
) -> None:
    """Write a delete-audit event, swallowing OS/type errors."""
    try:
        event = build_delete_audit_event(
            run_id=run_id, mode=mode, reason=reason,
            actor=actor, request_id=request_id,
            index_updated=index_updated, artifact_deleted=artifact_deleted,
            attachments_deleted=attachments_deleted,
            errors=errors, meta=meta,
        )
        append_delete_audit(store_root=root, event=event)
    except (OSError, TypeError) as audit_err:
        log.warning("Delete audit failed (%s): %s", label, audit_err)


def _find_artifact(root: Path, safe_id: str) -> tuple:
    """Scan date-partitions (newest-first) for a run artifact.

    Returns ``(artifact_path, partition_name)`` or ``(None, None)``.
    """
    partitions = sorted(
        [p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")],
        reverse=True,
    )
    for p in partitions:
        candidate = p / f"{safe_id}.json"
        if candidate.exists():
            return candidate, p.name
    return None, None


def _build_tombstone(
    run_id: str,
    reason: str,
    actor: Optional[str],
    request_id: Optional[str],
    original_meta: Optional[dict],
    partition: Optional[str],
) -> dict:
    """Construct a soft-delete tombstone entry for the index."""
    return {
        "run_id": run_id,
        "deleted": True,
        "deleted_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "deleted_reason": reason,
        "deleted_by": actor,
        "request_id": request_id,
        "created_at_utc": original_meta.get("created_at_utc") if original_meta else None,
        "status": original_meta.get("status") if original_meta else None,
        "mode": original_meta.get("mode") if original_meta else None,
        "partition": partition,
    }


def _hard_delete_files(
    root: Path,
    partition: Optional[str],
    safe_id: str,
    artifact_path: Path,
    cascade: bool,
) -> tuple:
    """Delete advisory links (if *cascade*) and the artifact file.

    Returns ``(advisory_links_deleted, artifact_deleted, error_msg)``.
    """
    advisory_links_deleted = 0
    artifact_deleted = False
    error_msg: Optional[str] = None

    if cascade and partition:
        partition_dir = root / partition
        for link_path in partition_dir.glob(f"{safe_id}_advisory_*.json"):
            try:
                link_path.unlink()
                advisory_links_deleted += 1
            except OSError:
                pass

    try:
        artifact_path.unlink()
        artifact_deleted = True
    except OSError as e:
        error_msg = f"Failed to delete artifact: {e}"

    return advisory_links_deleted, artifact_deleted, error_msg


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def execute_delete(
    *,
    root: Path,
    index_path: Path,
    index_lock: threading.Lock,
    read_json: Any,  # callable(Path) -> dict
    write_json: Any,  # callable(Path, dict) -> None
    run_id: str,
    mode: str = "soft",
    reason: str,
    actor: Optional[str] = None,
    request_id: Optional[str] = None,
    rate_limit_key: Optional[str] = None,
    cascade: bool = True,
    check_rate_limit: Any = None,  # callable(key) -> None, raises DeleteRateLimitError
    DeleteRateLimitError_cls: type = Exception,
) -> Dict[str, Any]:
    """Execute a run deletion with audit logging.

    This is the extracted body of RunStoreV2.delete_run, accepting
    primitives/callables so the caller (RunStoreV2) wires in its own state.
    """
    if not reason or not reason.strip():
        raise ValueError("Delete reason is required for audit trail")

    limit_key = rate_limit_key or actor or "anonymous"
    _akw = dict(root=root, run_id=run_id, mode=mode, reason=reason,
                actor=actor, request_id=request_id)

    # --- rate-limit pre-check ---
    if check_rate_limit is not None:
        try:
            check_rate_limit(limit_key)
        except Exception as e:  # WP-3: broad catch intentional — callback may raise arbitrary errors, always re-raises  # AUDITED 2026-03
            log.error("Rate-limit check failed for run %s: %s", run_id, e, exc_info=True)
            if isinstance(e, DeleteRateLimitError_cls):
                _safe_audit(**_akw, index_updated=False, artifact_deleted=False,
                            attachments_deleted=0, errors=f"Rate limited: {e}",
                            meta={"rate_limit_key": limit_key}, label="rate-limit")
                raise
            raise

    result: Dict[str, Any] = {
        "run_id": run_id, "deleted": False, "mode": mode,
        "index_updated": False, "artifact_deleted": False,
        "advisory_links_deleted": 0, "partition": None,
    }
    error_msg: Optional[str] = None
    safe_id = run_id.replace("/", "_").replace("\\", "_")

    try:
        artifact_path, partition = _find_artifact(root, safe_id)
        result["partition"] = partition

        if artifact_path is None:
            _safe_audit(**_akw, index_updated=False, artifact_deleted=False,
                        attachments_deleted=0, errors="Run not found",
                        meta=None, label="not-found")
            raise KeyError(f"Run not found: {run_id}")

        with index_lock:
            index = read_json(index_path)
            original_meta = index.get(run_id)

            if mode == "soft":
                index[run_id] = _build_tombstone(
                    run_id, reason, actor, request_id, original_meta, partition)
                write_json(index_path, index)
                result["index_updated"] = True
                result["deleted"] = True
            else:
                if run_id in index:
                    del index[run_id]
                    write_json(index_path, index)
                    result["index_updated"] = True

        if mode == "hard":
            adv_del, art_del, err = _hard_delete_files(
                root, partition, safe_id, artifact_path, cascade)
            result["advisory_links_deleted"] = adv_del
            result["artifact_deleted"] = art_del
            if art_del:
                result["deleted"] = True
            if err:
                error_msg = err

    except KeyError:
        raise
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:  # WP-3: narrowed — audit then fail-closed
        log.error("Delete operation failed for run %s: %s", run_id, e, exc_info=True)
        error_msg = str(e)
        _safe_audit(**_akw, index_updated=result["index_updated"],
                    artifact_deleted=result["artifact_deleted"],
                    attachments_deleted=result["advisory_links_deleted"],
                    errors=error_msg,
                    meta={"cascade": cascade, "partition": result["partition"],
                          "rate_limit_key": limit_key},
                    label="error")
        raise

    _safe_audit(**_akw, index_updated=result["index_updated"],
                artifact_deleted=result["artifact_deleted"],
                attachments_deleted=result["advisory_links_deleted"],
                errors=error_msg,
                meta={"cascade": cascade, "partition": result["partition"],
                      "rate_limit_key": limit_key},
                label="final")
    return result
