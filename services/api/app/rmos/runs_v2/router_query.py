"""
RMOS Runs v2 Query Router - Envelope-based List Endpoint

Provides stable list endpoint with cursor pagination and envelope response.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple, Set

import os
import json
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.rmos.explain_ai import generate_assistant_explanation
from .store import get_run, persist_run, _get_store_root
from .attachments import put_json_attachment
from .hashing import sha256_of_obj
from .compare import compare_run_artifacts


router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================


class RunArtifactSummary(BaseModel):
    run_id: str
    created_at_utc: str
    mode: str
    tool_id: str
    status: str
    risk_level: str
    rules_triggered: List[str] = Field(default_factory=list)


class RunsListResponse(BaseModel):
    items: List[RunArtifactSummary]
    next_cursor: Optional[str] = None
    count: int


# =============================================================================
# Helpers
# =============================================================================


def _safe_read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _iter_run_json_paths(store_root: str) -> List[Path]:
    """
    Store layout:
      {RMOS_RUNS_DIR}/{YYYY-MM-DD}/{run_id}.json
    We scan date partitions (newest first), then files.
    """
    root = Path(store_root)
    if not root.exists():
        return []
    parts = [p for p in root.iterdir() if p.is_dir()]
    parts.sort(key=lambda p: p.name, reverse=True)
    out: List[Path] = []
    for d in parts:
        files = [f for f in d.glob("run_*.json") if f.is_file()]
        files.sort(key=lambda p: p.name, reverse=True)
        out.extend(files)
    return out


def _cursor_key(created_at_utc: str, run_id: str) -> str:
    # Stable, opaque cursor token
    return f"{created_at_utc}|{run_id}"


def _parse_cursor(cursor: str) -> Optional[Tuple[str, str]]:
    if not cursor:
        return None
    if "|" not in cursor:
        return None
    a, b = cursor.split("|", 1)
    a = a.strip()
    b = b.strip()
    if not a or not b:
        return None
    return a, b


# =============================================================================
# Override Gate Helper (imported from existing pattern)
# =============================================================================


def _allow_red_override() -> bool:
    # Feature flag: allow RED override only when explicitly enabled.
    return os.getenv("RMOS_ALLOW_RED_OVERRIDE", "").strip().lower() in {"1", "true", "yes", "on"}


# =============================================================================
# List Endpoint
# =============================================================================


@router.get("/runs_v2", response_model=RunsListResponse)
def list_runs_v2(
    mode: Optional[str] = Query(None, description="Filter by run.mode"),
    risk: Optional[str] = Query(None, description="Filter by decision.risk_level"),
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = Query(None, description="Opaque pagination cursor from prior response."),
) -> RunsListResponse:
    """
    Stable list endpoint with envelope response:
      { items: [...], next_cursor: "...", count: N }

    Cursor is an opaque token "created_at_utc|run_id" representing the last item returned.
    """
    store_root = _get_store_root()
    mode_f = mode.strip() if mode else None
    risk_f = risk.strip().upper() if risk else None
    after = _parse_cursor(cursor) if cursor else None

    paths = _iter_run_json_paths(store_root)
    items: List[RunArtifactSummary] = []

    for p in paths:
        raw = _safe_read_json(p)
        if not raw:
            continue

        run_id = str(raw.get("run_id", "")).strip()
        created_at = str(raw.get("created_at_utc") or raw.get("created_at") or "").strip()
        if not run_id or not created_at:
            continue

        # Apply cursor: skip until strictly "older" than cursor key
        if after is not None:
            after_created, after_run = after
            # Sort is newest-first; we include items only once we pass the cursor position.
            if (created_at, run_id) >= (after_created, after_run):
                continue

        m = str(raw.get("mode", "")).strip()
        if mode_f and m != mode_f:
            continue

        decision = raw.get("decision") or {}
        rlevel = str(decision.get("risk_level", "UNKNOWN")).upper()
        if risk_f and rlevel != risk_f:
            continue

        feasibility = raw.get("feasibility") or {}
        rt = feasibility.get("rules_triggered") or []
        rules_triggered = [str(x).strip().upper() for x in rt] if isinstance(rt, list) else []

        items.append(
            RunArtifactSummary(
                run_id=run_id,
                created_at_utc=created_at,
                mode=m,
                tool_id=str(raw.get("tool_id", "")).strip(),
                status=str(raw.get("status", "")).strip(),
                risk_level=rlevel,
                rules_triggered=rules_triggered,
            )
        )

        if len(items) >= limit:
            break

    next_cursor = None
    if len(items) == limit:
        last = items[-1]
        next_cursor = _cursor_key(last.created_at_utc, last.run_id)

    return RunsListResponse(items=items, next_cursor=next_cursor, count=len(items))

# ─────────────────────────────────────────────────────────────────────────────
# Run Diff Endpoint
# ─────────────────────────────────────────────────────────────────────────────


class RunDiffResponse(BaseModel):
    run_a: str
    run_b: str
    request_diff: Dict[str, Any]
    feasibility_diff: Dict[str, Any]
    decision_diff: Dict[str, Any]
    hashes_diff: Dict[str, Any]
    attachments_diff: Dict[str, Any]


def _dict_diff(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    keys: Set[str] = set(a.keys()) | set(b.keys())
    out: Dict[str, Dict[str, Any]] = {}
    for k in sorted(keys):
        va = a.get(k)
        vb = b.get(k)
        if va != vb:
            out[k] = {"a": va, "b": vb}
    return out


def _list_diff(a: List[Any], b: List[Any]) -> Dict[str, List[Any]]:
    sa = set(map(json.dumps, a))
    sb = set(map(json.dumps, b))
    return {
        "only_in_a": [json.loads(x) for x in sa - sb],
        "only_in_b": [json.loads(x) for x in sb - sa],
    }


@router.get("/runs_v2/diff/{run_id_a}/{run_id_b}", response_model=RunDiffResponse)
def diff_runs(run_id_a: str, run_id_b: str) -> RunDiffResponse:
    """
    Compare two RunArtifacts and return a structured diff.

    Intended for operator / engineer trust-building:
      - What changed between two runs?
      - Why does the outcome differ?
    """
    ra = get_run(run_id_a)
    rb = get_run(run_id_b)

    if ra is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id_a}")
    if rb is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id_b}")

    # Normalize to dicts where needed
    ra_req = ra.request_summary or {}
    rb_req = rb.request_summary or {}

    ra_feat = ra.feasibility or {}
    rb_feat = rb.feasibility or {}

    ra_dec = ra.decision.model_dump() if hasattr(ra.decision, "model_dump") else (ra.decision or {})
    rb_dec = rb.decision.model_dump() if hasattr(rb.decision, "model_dump") else (rb.decision or {})

    ra_hash = ra.hashes.model_dump() if hasattr(ra.hashes, "model_dump") else (ra.hashes or {})
    rb_hash = rb.hashes.model_dump() if hasattr(rb.hashes, "model_dump") else (rb.hashes or {})

    ra_atts = [a.model_dump() if hasattr(a, "model_dump") else a for a in (ra.attachments or [])]
    rb_atts = [a.model_dump() if hasattr(a, "model_dump") else a for a in (rb.attachments or [])]

    return RunDiffResponse(
        run_a=run_id_a,
        run_b=run_id_b,
        request_diff=_dict_diff(ra_req, rb_req),
        feasibility_diff=_dict_diff(ra_feat, rb_feat),
        decision_diff=_dict_diff(ra_dec, rb_dec),
        hashes_diff=_dict_diff(ra_hash, rb_hash),
        attachments_diff=_list_diff(ra_atts, rb_atts),
    )


@router.get("/runs_v2/compare/{run_id_a}/{run_id_b}")
def compare_runs_v2(run_id_a: str, run_id_b: str) -> Dict[str, Any]:
    """
    Operator-facing structured compare endpoint.
    Returns a compact summary + focused diffs (and also includes optional deep diffs).
    """
    ra = get_run(run_id_a)
    rb = get_run(run_id_b)
    if ra is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id_a}")
    if rb is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id_b}")
    return compare_run_artifacts(ra, rb)
