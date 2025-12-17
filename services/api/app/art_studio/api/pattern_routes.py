"""
Pattern Library Routes - Bundle 31.0.1

CRUD API for pattern library.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas.pattern_library import (
    PatternRecord,
    PatternListResponse,
    PatternCreateRequest,
    PatternUpdateRequest,
)
from ..services.pattern_store import PatternStore, resolve_art_studio_data_root


router = APIRouter(
    prefix="/api/art/patterns",
    tags=["art_studio_patterns"],
)


def get_pattern_store() -> PatternStore:
    return PatternStore(data_root=resolve_art_studio_data_root())


@router.get("", response_model=PatternListResponse)
async def list_patterns(
    q: str | None = Query(default=None, description="Search name/description/tags"),
    tag: str | None = Query(default=None, description="Filter by tag"),
    generator_key: str | None = Query(default=None, description="Filter by generator key"),
    limit: int = Query(default=100, ge=1, le=500),
    store: PatternStore = Depends(get_pattern_store),
) -> PatternListResponse:
    """List patterns with optional filtering."""
    items = store.list_patterns(q=q, tag=tag, generator_key=generator_key, limit=limit)
    return PatternListResponse(items=items)


@router.post("", response_model=PatternRecord)
async def create_pattern(
    req: PatternCreateRequest,
    store: PatternStore = Depends(get_pattern_store),
) -> PatternRecord:
    """Create a new pattern."""
    return store.create(req)


@router.get("/{pattern_id}", response_model=PatternRecord)
async def get_pattern(
    pattern_id: str,
    store: PatternStore = Depends(get_pattern_store),
) -> PatternRecord:
    """Get a pattern by ID."""
    pattern = store.get(pattern_id)
    if pattern is None:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return pattern


@router.put("/{pattern_id}", response_model=PatternRecord)
async def update_pattern(
    pattern_id: str,
    req: PatternUpdateRequest,
    store: PatternStore = Depends(get_pattern_store),
) -> PatternRecord:
    """Update an existing pattern."""
    pattern = store.update(pattern_id, req)
    if pattern is None:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return pattern


@router.delete("/{pattern_id}")
async def delete_pattern(
    pattern_id: str,
    store: PatternStore = Depends(get_pattern_store),
) -> dict:
    """Delete a pattern."""
    ok = store.delete(pattern_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return {"ok": True, "pattern_id": pattern_id}
