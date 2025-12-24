"""
RMOS Delete Audit Log - Append-only audit trail for run deletions.

H3.6.2: Separate from index tombstones (survives index compaction).

Storage:
    ${RMOS_RUNS_DIR}/_audit/deletes.jsonl

Each line is a JSON object with:
    ts_utc, run_id, mode, reason, actor, request_id,
    index_updated, artifact_deleted, attachments_deleted, errors, meta
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


AUDIT_DIRNAME = "_audit"
AUDIT_FILENAME = "deletes.jsonl"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _get_audit_path(store_root: Path) -> Path:
    audit_dir = store_root / AUDIT_DIRNAME
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir / AUDIT_FILENAME


@dataclass(frozen=True)
class DeleteAuditEvent:
    ts_utc: str
    run_id: str
    mode: str  # "soft" | "hard"
    reason: str
    actor: Optional[str] = None
    request_id: Optional[str] = None

    # H3.6.2: Policy and rate limit tracking
    allowed_by_policy: bool = True
    allowed_by_rate_limit: bool = True
    client_ip: Optional[str] = None
    outcome: str = "ok"  # ok|not_found|error|forbidden|rate_limited|invalid

    # effects
    index_updated: bool = False
    artifact_deleted: bool = False
    attachments_deleted: int = 0
    errors: Optional[str] = None

    # freeform
    meta: Optional[Dict[str, Any]] = None


def append_delete_audit(
    *,
    store_root: Path,
    event: DeleteAuditEvent,
) -> Path:
    """
    Append a single JSON line to the delete audit log.

    Design goals:
    - separate from index tombstones (survives index compaction)
    - append-only (no rewrites)
    - best-effort atomic line append (POSIX append semantics; Windows is still fine for single-process CI/dev)
    """
    path = _get_audit_path(store_root)

    payload = asdict(event)
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"

    # append + fsync to reduce "lost last line" risk on crashes
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            # fsync may fail on some filesystems; audit is best-effort
            pass

    return path


def build_delete_audit_event(
    *,
    run_id: str,
    mode: str,
    reason: str,
    actor: Optional[str],
    request_id: Optional[str],
    index_updated: bool,
    artifact_deleted: bool,
    attachments_deleted: int,
    errors: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    # H3.6.2: New fields
    allowed_by_policy: bool = True,
    allowed_by_rate_limit: bool = True,
    client_ip: Optional[str] = None,
    outcome: str = "ok",
) -> DeleteAuditEvent:
    return DeleteAuditEvent(
        ts_utc=_utc_now_iso(),
        run_id=run_id,
        mode=mode,
        reason=reason,
        actor=actor,
        request_id=request_id,
        allowed_by_policy=allowed_by_policy,
        allowed_by_rate_limit=allowed_by_rate_limit,
        client_ip=client_ip,
        outcome=outcome,
        index_updated=index_updated,
        artifact_deleted=artifact_deleted,
        attachments_deleted=attachments_deleted,
        errors=errors,
        meta=meta,
    )
