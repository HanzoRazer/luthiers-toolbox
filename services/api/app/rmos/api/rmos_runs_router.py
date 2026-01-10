"""
RMOS Runs Router - Artifact Query and Diff API

Implements RUN_ARTIFACT_INDEX_QUERY_API_CONTRACT_v1.md and
RUN_DIFF_VIEWER_CONTRACT_v1.md governance specifications.

Provides:
- GET /api/rmos/runs - List artifacts with filters + pagination
- GET /api/rmos/runs/{run_id} - Fetch single artifact
- GET /api/rmos/runs/{run_id}/download - Download artifact as JSON file
- GET /api/rmos/runs/diff/{a_id}/{b_id} - Compare two artifacts
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.rmos.run_artifacts.index import (
    get_artifact,
    query_artifacts,
    RunIndexRow,
)

router = APIRouter(prefix="/api/rmos/runs", tags=["RMOS", "Runs"])


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class RunIndexRowOut(BaseModel):
    """Index row for artifact listing."""
    artifact_id: str
    kind: str
    status: str
    created_utc: str
    session_id: str
    index_meta: Dict[str, Any] = Field(default_factory=dict)


class RunIndexPageOut(BaseModel):
    """Paginated artifact list response."""
    items: List[RunIndexRowOut]
    next_cursor: Optional[str] = None


class RunDiffOut(BaseModel):
    """Diff comparison response."""
    a_id: str
    b_id: str
    summary: Dict[str, Any]
    changed_fields: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# List Endpoint
# ---------------------------------------------------------------------------

@router.get("", response_model=Union[RunIndexPageOut, List[Dict[str, Any]]])
def list_runs(
    cursor: Optional[str] = Query(default=None, description="Pagination cursor"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results per page"),
    kind: Optional[str] = Query(default=None, description="Filter by artifact kind"),
    status: Optional[str] = Query(default=None, description="Filter by status (OK, BLOCKED, ERROR)"),
    tool_id: Optional[str] = Query(default=None, description="Filter by tool_id"),
    material_id: Optional[str] = Query(default=None, description="Filter by material_id"),
    machine_id: Optional[str] = Query(default=None, description="Filter by machine_id"),
    session_id: Optional[str] = Query(default=None, description="Filter by session_id"),
    parent_batch_decision_artifact_id: Optional[str] = Query(default=None, description="Filter by parent batch decision artifact"),
    parent_batch_plan_artifact_id: Optional[str] = Query(default=None, description="Filter by parent batch plan artifact"),
    parent_batch_spec_artifact_id: Optional[str] = Query(default=None, description="Filter by parent batch spec artifact"),
) -> Union[RunIndexPageOut, List[Dict[str, Any]]]:
    """
    List run artifacts with filtering and pagination.

    Per RUN_ARTIFACT_INDEX_QUERY_API_CONTRACT_v1.md.
    """
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
            "parent_batch_decision_artifact_id": parent_batch_decision_artifact_id,
            "parent_batch_plan_artifact_id": parent_batch_plan_artifact_id,
            "parent_batch_spec_artifact_id": parent_batch_spec_artifact_id,
        },
    )
    items_models = [
        RunIndexRowOut(
            artifact_id=r.artifact_id,
            kind=r.kind,
            status=r.status,
            created_utc=r.created_utc,
            session_id=r.session_id,
            index_meta=r.index_meta,
        )
        for r in rows
    ]

    # Compatibility mode:
    # Some legacy tests/clients expect a raw list (not a paginated envelope)
    # when filtering by parent batch plan/spec IDs.
    if parent_batch_plan_artifact_id or parent_batch_spec_artifact_id:
        def _dump(m: Any) -> Dict[str, Any]:
            return m.model_dump() if hasattr(m, "model_dump") else m.dict()
        return [_dump(m) for m in items_models]

    return RunIndexPageOut(items=items_models, next_cursor=next_cursor)


# ---------------------------------------------------------------------------
# Single Artifact Endpoint
# ---------------------------------------------------------------------------

@router.get("/{run_id}")
def read_run(run_id: str) -> Dict[str, Any]:
    """
    Fetch a single run artifact by ID.

    Returns full artifact JSON.
    """
    try:
        return get_artifact(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": run_id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "INVALID_RUN_ID", "message": str(e)})


# ---------------------------------------------------------------------------
# Download Endpoint
# ---------------------------------------------------------------------------

@router.get("/{run_id}/download")
def download_run(run_id: str) -> JSONResponse:
    """
    Download a run artifact as a JSON file.

    Returns with Content-Disposition: attachment.
    """
    try:
        artifact = get_artifact(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": run_id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "INVALID_RUN_ID", "message": str(e)})

    return JSONResponse(
        content=artifact,
        headers={
            "Content-Disposition": f'attachment; filename="{run_id}.json"'
        }
    )


# ---------------------------------------------------------------------------
# Diff Endpoint
# ---------------------------------------------------------------------------

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


@router.get("/diff/{a_id}/{b_id}", response_model=RunDiffOut)
def diff_runs(a_id: str, b_id: str) -> RunDiffOut:
    """
    Compare two run artifacts.

    Per RUN_DIFF_VIEWER_CONTRACT_v1.md, compares governance-relevant fields:
    - kind, status, session_id
    - tool_id, material_id, machine_id
    - risk_bucket, score, policy_version
    - feasibility_hash, design_hash, context_hash, toolpath_hash

    Does NOT compare large payloads like gcode_text.
    """
    try:
        a = get_artifact(a_id)
        b = get_artifact(b_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "message": str(e)})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "INVALID_RUN_ID", "message": str(e)})

    # Stable "governance diff" fields (no giant payloads)
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
        "total_changes": len(changed),
    }

    return RunDiffOut(
        a_id=a_id,
        b_id=b_id,
        summary=summary,
        changed_fields=changed,
    )
