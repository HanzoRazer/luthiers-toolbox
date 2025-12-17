from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.rmos.run_artifacts.index import get_artifact, query_artifacts


router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunIndexRowOut(BaseModel):
    artifact_id: str
    kind: str
    status: str
    created_utc: str
    session_id: str
    index_meta: Dict[str, Any] = Field(default_factory=dict)


class RunIndexPageOut(BaseModel):
    items: List[RunIndexRowOut]
    next_cursor: Optional[str] = None


@router.get("", response_model=RunIndexPageOut)
def list_runs(
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    kind: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    tool_id: Optional[str] = Query(default=None),
    material_id: Optional[str] = Query(default=None),
    machine_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
) -> RunIndexPageOut:
    rows, next_cursor = query_artifacts(
        cursor=cursor,
        limit=limit,
        filters={
            "kind": kind,
            "status": status,
            "tool_id": tool_id,
            "material_id": material_id,
            "machine_id": machine_id,
            "session_id": session_id,
        },
    )
    return RunIndexPageOut(
        items=[
            RunIndexRowOut(
                artifact_id=r.artifact_id,
                kind=r.kind,
                status=r.status,
                created_utc=r.created_utc,
                session_id=r.session_id,
                index_meta=r.index_meta,
            )
            for r in rows
        ],
        next_cursor=next_cursor,
    )


@router.get("/{artifact_id}")
def read_run(artifact_id: str) -> Dict[str, Any]:
    try:
        return get_artifact(artifact_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------
# Diff Viewer Endpoint
# ---------------------------

def _pick(obj: Dict[str, Any], path: str) -> Any:
    """
    Safe nested getter: path like "payload.feasibility.meta.policy_version"
    """
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


class RunDiffOut(BaseModel):
    a_id: str
    b_id: str
    summary: Dict[str, Any]
    changed_fields: List[Dict[str, Any]]


@router.get("/diff/{a_id}/{b_id}", response_model=RunDiffOut)
def diff_runs(a_id: str, b_id: str) -> RunDiffOut:
    try:
        a = get_artifact(a_id)
        b = get_artifact(b_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Stable “governance diff” fields (no giant payloads)
    fields = [
        ("kind", "kind"),
        ("status", "status"),
        ("session_id", "session_id"),
        ("tool_id", "index_meta.tool_id"),
        ("material_id", "index_meta.material_id"),
        ("machine_id", "index_meta.machine_id"),
        ("risk_bucket", "payload.feasibility.risk_bucket"),
        ("score", "payload.feasibility.score"),
        ("policy_version", "payload.feasibility.meta.policy_version"),
        ("feasibility_hash", "payload.feasibility.meta.feasibility_hash"),
        ("design_hash", "payload.feasibility.meta.design_hash"),
        ("context_hash", "payload.feasibility.meta.context_hash"),
        ("toolpath_hash", "payload.toolpaths.meta.toolpath_hash"),
    ]

    changed: List[Dict[str, Any]] = []
    for label, p in fields:
        av = _pick(a, p)
        bv = _pick(b, p)
        if av != bv:
            changed.append({"field": label, "a": av, "b": bv, "path": p})

    summary = {
        "a_created_utc": a.get("created_utc"),
        "b_created_utc": b.get("created_utc"),
        "a_status": a.get("status"),
        "b_status": b.get("status"),
        "a_kind": a.get("kind"),
        "b_kind": b.get("kind"),