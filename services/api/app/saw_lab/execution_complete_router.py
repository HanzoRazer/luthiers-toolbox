from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class ExecutionOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    SCRAP = "SCRAP"


class ExecutionCompleteChecklist(BaseModel):
    all_cuts_complete: bool = Field(True, description="All planned cuts finished")
    material_removed: bool = Field(True, description="Workpiece removed from fixture")
    workpiece_inspected: bool = Field(True, description="Visual QC performed")
    area_cleared: bool = Field(True, description="Work area cleared for next batch")


class ExecutionCompleteRequest(BaseModel):
    batch_execution_artifact_id: str = Field(..., description="Execution artifact id to complete")
    session_id: str
    batch_label: str
    outcome: ExecutionOutcome
    notes: Optional[str] = None
    operator_id: Optional[str] = None
    tool_kind: str = "saw"
    checklist: Optional[ExecutionCompleteChecklist] = None
    statistics: Optional[Dict[str, Any]] = None


class ExecutionCompleteResponse(BaseModel):
    batch_execution_artifact_id: str
    complete_artifact_id: str
    state: str = "COMPLETED"


@router.post("/execution/complete", response_model=ExecutionCompleteResponse)
def complete_execution(req: ExecutionCompleteRequest) -> ExecutionCompleteResponse:
    if not req.batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")
    if not req.session_id or not req.batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")

    from app.rmos.runs_v2 import store as runs_store

    # Ensure execution exists (avoid completing phantom IDs)
    ex = runs_store.get_run(req.batch_execution_artifact_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="execution artifact not found")

    # Guardrails:
    # - do not allow completion if already aborted
    # - do not allow double completion
    # - require at least one job log to exist for this execution
    def _items(res: Any) -> list:
        if isinstance(res, dict):
            v = res.get("items")
            return v if isinstance(v, list) else []
        return res if isinstance(res, list) else []

    def _parent_id(art: Any) -> Optional[str]:
        if isinstance(art, dict):
            return str(art.get("parent_id") or art.get("parent_artifact_id") or "") or None
        meta = getattr(art, "meta", None)
        if isinstance(meta, dict):
            pid = meta.get("parent_id")
            return str(pid) if pid else None
        return None

    def _payload(art: Any) -> Dict[str, Any]:
        if isinstance(art, dict):
            p = art.get("payload") or art.get("data") or {}
            return p if isinstance(p, dict) else {}
        return {}

    def _created_ts(art: Any) -> Optional[float]:
        """
        Best-effort extraction of a creation timestamp.

        Supports:
        - RunArtifact Pydantic models with `created_at_utc: datetime`
        - Dict-based artifacts (tests / serialized forms)
        - datetime objects
        - numeric epoch seconds
        - ISO-8601 strings (with or without 'Z')

        Returns:
            Unix timestamp in seconds, or None if unavailable.
        """
        # 1) Pydantic RunArtifact (authoritative runtime path)
        created = getattr(art, "created_at_utc", None)
        if isinstance(created, datetime):
            return created.timestamp()

        # 2) Dict-based fallbacks (tests / serialized artifacts)
        if isinstance(art, dict):
            for key in (
                "created_at_utc",
                "created_utc",
                "created_at",
                "created",
                "timestamp",
                "ts",
            ):
                v = art.get(key)
                if v is None:
                    continue

                # datetime
                if isinstance(v, datetime):
                    return v.timestamp()

                # numeric epoch
                if isinstance(v, (int, float)):
                    return float(v)

                # ISO-8601 string
                if isinstance(v, str) and v.strip():
                    s = v.strip()
                    if s.endswith("Z"):
                        s = s[:-1] + "+00:00"
                    try:
                        return datetime.fromisoformat(s).timestamp()
                    except Exception:
                        continue

        return None

    def _latest_by_ts_then_order(items: list[Any]) -> Any:
        """
        Select the latest item by created timestamp.
        Micro-hardening: if timestamps collide (same second), pick the later item
        by insertion order (higher index). If timestamps are missing, fall back to
        the last item.
        """
        if not items:
            raise ValueError("items must be non-empty")

        scored: list[tuple[float, int, Any]] = []
        for idx, it in enumerate(items):
            ts = _created_ts(it)
            if ts is None:
                continue
            # Use integer seconds for collision-aware monotonicity.
            # Tie-breaker: idx (insertion order).
            scored.append((float(int(ts)), idx, it))

        if scored:
            # Max by (second-resolution timestamp, insertion index)
            return max(scored, key=lambda t: (t[0], t[1]))[2]

        # No parseable timestamps → deterministic fallback to last item
        return items[-1]

    # Prefer filtered lists; tolerate older store signatures
    try:
        aborts = _items(
            runs_store.list_runs_filtered(
                session_id=req.session_id,
                batch_label=req.batch_label,
                kind="saw_batch_execution_abort",
                limit=5000,
            )
        )
        completes = _items(
            runs_store.list_runs_filtered(
                session_id=req.session_id,
                batch_label=req.batch_label,
                kind="saw_batch_execution_complete",
                limit=5000,
            )
        )
        job_logs = _items(
            runs_store.list_runs_filtered(
                session_id=req.session_id,
                batch_label=req.batch_label,
                kind="saw_batch_job_log",
                limit=5000,
            )
        )
    except TypeError:
        aborts = _items(runs_store.list_runs_filtered(session_id=req.session_id, batch_label=req.batch_label))
        completes = _items(runs_store.list_runs_filtered(session_id=req.session_id, batch_label=req.batch_label))
        job_logs = _items(runs_store.list_runs_filtered(session_id=req.session_id, batch_label=req.batch_label))

    for a in aborts:
        if _parent_id(a) == str(req.batch_execution_artifact_id):
            raise HTTPException(status_code=409, detail="execution already aborted")

    for c in completes:
        if _parent_id(c) == str(req.batch_execution_artifact_id):
            raise HTTPException(status_code=409, detail="execution already completed")

    # Prerequisite (tight): the LATEST job log for this execution must be QUALIFYING.
    # Qualifying means:
    #   - parented to this execution
    #   - payload.status != "ABORTED"
    #   - payload.metrics indicates work (yield or time > 0)
    def _metrics_indicate_work(m: Any) -> bool:
        if not isinstance(m, dict):
            return False
        try:
            parts_ok = int(m.get("parts_ok") or 0)
            parts_scrap = int(m.get("parts_scrap") or 0)
        except Exception:
            parts_ok, parts_scrap = 0, 0

        def _f(key: str) -> float:
            try:
                return float(m.get(key) or 0.0)
            except Exception:
                return 0.0

        cut_time_s = _f("cut_time_s")
        total_time_s = _f("total_time_s")

        return (parts_ok + parts_scrap) > 0 or cut_time_s > 0.0 or total_time_s > 0.0

    # Select job logs that belong to THIS execution
    exec_logs = [jl for jl in job_logs if _parent_id(jl) == str(req.batch_execution_artifact_id)]
    if not exec_logs:
        raise HTTPException(
            status_code=409,
            detail="execution has no job logs; cannot complete",
        )

    # Determine the latest log deterministically.
    # Uses second-resolution timestamps with insertion order as tie-breaker.
    latest_log = _latest_by_ts_then_order(exec_logs)

    # Validate that the latest log is qualifying
    p = _payload(latest_log)
    status = p.get("status")
    if isinstance(status, str) and status.upper() == "ABORTED":
        raise HTTPException(
            status_code=409,
            detail="latest job log indicates ABORTED; cannot complete",
        )
    metrics = p.get("metrics")
    if not _metrics_indicate_work(metrics):
        raise HTTPException(
            status_code=409,
            detail="latest job log lacks work metrics; cannot complete",
        )

    # Convert checklist pydantic model to dict if provided
    checklist_dict = req.checklist.model_dump() if req.checklist else None

    from .execution_complete_service import write_execution_complete_artifact

    complete_id = write_execution_complete_artifact(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        session_id=req.session_id,
        batch_label=req.batch_label,
        outcome=str(req.outcome.value),
        notes=req.notes,
        operator_id=req.operator_id,
        tool_kind=req.tool_kind,
        checklist=checklist_dict,
        statistics=req.statistics,
    )

    return ExecutionCompleteResponse(
        batch_execution_artifact_id=req.batch_execution_artifact_id,
        complete_artifact_id=complete_id,
        state="COMPLETED",
    )
