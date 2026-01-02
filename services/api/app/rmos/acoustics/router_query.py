from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .persist_glue import RUNS_ROOT_DEFAULT, INDEX_FILENAME


router = APIRouter(tags=["rmos", "acoustics"])  # prefix set once in main.py (Issue B fix)


def _get_runs_root() -> Path:
    return Path(os.getenv("RMOS_RUNS_ROOT", RUNS_ROOT_DEFAULT)).expanduser().resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_iso_utc(s: str) -> datetime:
    # accepts "YYYY-MM-DDTHH:MM:SSZ" or ISO with +00:00
    if s.endswith("Z"):
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    return datetime.fromisoformat(s)


class IndexResponse(BaseModel):
    version: int = 1
    updated_at: Optional[str] = None
    total: int
    returned: int
    offset: int
    limit: int
    runs: list[dict[str, Any]]


@router.get("/index", response_model=IndexResponse)
def get_index(
    instrument_id: Optional[str] = Query(default=None),
    build_stage: Optional[str] = Query(default=None),
    bundle_id: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    tool_id: Optional[str] = Query(default=None),
    mode: Optional[str] = Query(default="acoustics"),
    since: Optional[str] = Query(default=None, description="ISO UTC, e.g. 2025-12-25T00:00:00Z"),
    until: Optional[str] = Query(default=None, description="ISO UTC, e.g. 2025-12-26T00:00:00Z"),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> IndexResponse:
    """
    Query the runs_v2 _index.json cache.
    Filters are best-effort and operate on cached fields in each index entry.
    """
    runs_root = _get_runs_root()
    idx_path = runs_root / INDEX_FILENAME
    if not idx_path.exists():
        # No index is not an error; just empty.
        return IndexResponse(total=0, returned=0, offset=offset, limit=limit, runs=[], updated_at=None)

    idx = _load_json(idx_path)
    runs = idx.get("runs", [])
    if not isinstance(runs, list):
        runs = []

    since_dt = _parse_iso_utc(since) if since else None
    until_dt = _parse_iso_utc(until) if until else None

    def match(r: dict[str, Any]) -> bool:
        if mode and r.get("mode") != mode:
            return False
        if instrument_id and r.get("instrument_id") != instrument_id:
            return False
        if build_stage and r.get("build_stage") != build_stage:
            return False
        if bundle_id and r.get("bundle_id") != bundle_id:
            return False
        if event_type and r.get("event_type") != event_type:
            return False
        if status and r.get("status") != status:
            return False
        if tool_id and r.get("tool_id") != tool_id:
            return False

        if since_dt or until_dt:
            ca = r.get("created_at")
            if not ca:
                return False
            try:
                ca_dt = _parse_iso_utc(ca)
            except Exception:
                return False
            if since_dt and ca_dt < since_dt:
                return False
            if until_dt and ca_dt >= until_dt:
                return False

        return True

    # Filter then sort by created_at desc (best-effort)
    filtered = [r for r in runs if isinstance(r, dict) and match(r)]

    def sort_key(r: dict[str, Any]) -> str:
        return r.get("created_at") or ""

    filtered.sort(key=sort_key, reverse=True)

    total = len(filtered)
    page = filtered[offset: offset + limit]

    return IndexResponse(
        version=int(idx.get("version", 1)),
        updated_at=idx.get("updated_at"),
        total=total,
        returned=len(page),
        offset=offset,
        limit=limit,
        runs=page,
    )


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    """
    Fetch the canonical run_{run_id}.json pointer.

    Strategy:
      1) If _index.json exists, use its path entry.
      2) Fallback: search date partitions under runs_root for the file.
    """
    runs_root = _get_runs_root()
    idx_path = runs_root / INDEX_FILENAME

    # 1) Try index path
    if idx_path.exists():
        try:
            idx = _load_json(idx_path)
            runs = idx.get("runs", [])
            if isinstance(runs, list):
                for r in runs:
                    if isinstance(r, dict) and r.get("run_id") == run_id:
                        rel = r.get("path")
                        if rel:
                            p = (runs_root / rel).resolve()
                            if p.exists() and p.is_file():
                                return _load_json(p)
        except Exception:
            # ignore and fall back
            pass

    # 2) Fallback: scan date partitions
    target = f"run_{run_id}.json"
    if not runs_root.exists():
        raise HTTPException(status_code=404, detail="runs store not found")

    # Date partitions are directories like YYYY-MM-DD
    for child in sorted(runs_root.iterdir(), reverse=True):
        if not child.is_dir():
            continue
        # skip non-date dirs
        name = child.name
        if len(name) != 10 or name[4] != "-" or name[7] != "-":
            continue
        p = child / target
        if p.exists() and p.is_file():
            return _load_json(p)

    raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")
