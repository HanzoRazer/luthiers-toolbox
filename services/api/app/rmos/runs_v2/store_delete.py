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
    if check_rate_limit is not None:
        try:
            check_rate_limit(limit_key)
        except Exception as e:  # WP-1: broad catch intentional — callback may raise arbitrary errors, always re-raises
            if isinstance(e, DeleteRateLimitError_cls):
                try:
                    event = build_delete_audit_event(
                        run_id=run_id, mode=mode, reason=reason,
                        actor=actor, request_id=request_id,
                        index_updated=False, artifact_deleted=False,
                        attachments_deleted=0,
                        errors=f"Rate limited: {e}",
                        meta={"rate_limit_key": limit_key},
                    )
                    append_delete_audit(store_root=root, event=event)
                except (OSError, TypeError) as audit_err:
                    log.warning('Delete audit failed (rate-limit): %s', audit_err)
                raise
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

    try:
        artifact_path: Optional[Path] = None
        partition: Optional[str] = None

        partitions = sorted(
            [p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")],
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
            error_msg = "Run not found"
            try:
                event = build_delete_audit_event(
                    run_id=run_id, mode=mode, reason=reason,
                    actor=actor, request_id=request_id,
                    index_updated=False, artifact_deleted=False,
                    attachments_deleted=0, errors=error_msg, meta=None,
                )
                append_delete_audit(store_root=root, event=event)
            except (OSError, TypeError) as audit_err:
                log.warning('Delete audit failed (not-found): %s', audit_err)
            raise KeyError(f"Run not found: {run_id}")

        with index_lock:
            index = read_json(index_path)
            original_meta = index.get(run_id)

            if mode == "soft":
                tombstone = {
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
                index[run_id] = tombstone
                write_json(index_path, index)
                result["index_updated"] = True
                result["deleted"] = True
            else:
                if run_id in index:
                    del index[run_id]
                    write_json(index_path, index)
                    result["index_updated"] = True

        if mode == "hard":
            if cascade and partition:
                pattern = f"{safe_id}_advisory_*.json"
                partition_dir = root / partition
                for link_path in partition_dir.glob(pattern):
                    try:
                        link_path.unlink()
                        result["advisory_links_deleted"] += 1
                    except OSError:
                        pass

            try:
                artifact_path.unlink()
                result["artifact_deleted"] = True
                result["deleted"] = True
            except OSError as e:
                error_msg = f"Failed to delete artifact: {e}"

    except KeyError:
        raise
    except Exception as e:  # WP-1: broad catch intentional — ensures audit event is written, always re-raises specific errors
        if isinstance(e, DeleteRateLimitError_cls):
            raise
        error_msg = str(e)

    try:
        event = build_delete_audit_event(
            run_id=run_id, mode=mode, reason=reason,
            actor=actor, request_id=request_id,
            index_updated=result["index_updated"],
            artifact_deleted=result["artifact_deleted"],
            attachments_deleted=result["advisory_links_deleted"],
            errors=error_msg,
            meta={"cascade": cascade, "partition": result["partition"], "rate_limit_key": limit_key},
        )
        append_delete_audit(store_root=root, event=event)
    except (OSError, TypeError) as audit_err:
        log.warning('Delete audit failed (final): %s', audit_err)

    return result
