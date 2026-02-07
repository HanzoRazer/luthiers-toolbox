"""
Snapshot Routes - Bundle 31.0.4

Design snapshot save/load/export/import API.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..schemas.design_snapshot import (
    DesignSnapshot,
    SnapshotCreateRequest,
    SnapshotExportResponse,
    SnapshotImportRequest,
    SnapshotListResponse,
    SnapshotUpdateRequest,
)
from ..services.design_snapshot_store import (
    DesignSnapshotStore,
    resolve_art_studio_data_root,
)


router = APIRouter(
    prefix="/api/art/snapshots",
    tags=["art_studio_snapshots"],
)


def get_snapshot_store() -> DesignSnapshotStore:
    return DesignSnapshotStore(data_root=resolve_art_studio_data_root())


@router.post("", response_model=DesignSnapshot)
async def create_snapshot(
    req: SnapshotCreateRequest,
    store: DesignSnapshotStore = Depends(get_snapshot_store),
) -> DesignSnapshot:
    """Create a new design snapshot."""
    return store.create(req)


@router.get("/recent", response_model=SnapshotListResponse)
async def list_recent_snapshots(
    q: str | None = Query(default=None, description="Search name/notes/tags"),
    tag: str | None = Query(default=None, description="Filter by tag"),
    pattern_id: str | None = Query(default=None, description="Filter by pattern_id"),
    limit: int = Query(default=50, ge=1, le=200),
    store: DesignSnapshotStore = Depends(get_snapshot_store),
) -> SnapshotListResponse:
    """List recent snapshots with optional filtering."""
    items = store.list_recent(q=q, tag=tag, pattern_id=pattern_id, limit=limit)
    return SnapshotListResponse(items=items)


@router.get("/{snapshot_id}", response_model=DesignSnapshot)
async def get_snapshot(
    snapshot_id: str,
    store: DesignSnapshotStore = Depends(get_snapshot_store),
) -> DesignSnapshot:
    """Get a snapshot by ID."""
    snap = store.get(snapshot_id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snap


@router.put("/{snapshot_id}", response_model=DesignSnapshot)
async def update_snapshot(
    snapshot_id: str,
    req: SnapshotUpdateRequest,
    store: DesignSnapshotStore = Depends(get_snapshot_store),
) -> DesignSnapshot:
    """Update an existing snapshot."""
    snap = store.update(snapshot_id, req)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snap


@router.delete("/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: str,
    store: DesignSnapshotStore = Depends(get_snapshot_store),
) -> dict:
    """Delete a snapshot."""
    ok = store.delete(snapshot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"ok": True, "snapshot_id": snapshot_id}


@router.get("/{snapshot_id}/export", response_model=SnapshotExportResponse)
async def export_snapshot(
    snapshot_id: str,
    store: DesignSnapshotStore = Depends(get_snapshot_store),
) -> SnapshotExportResponse:
    """Export a snapshot as JSON."""
    raw = store.export_raw(snapshot_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return SnapshotExportResponse(snapshot=raw)


@router.get("/{snapshot_id}/export/download")
async def export_snapshot_download(
    snapshot_id: str,
    store: DesignSnapshotStore = Depends(get_snapshot_store),
):
    """Export a snapshot as a downloadable JSON file."""
    raw = store.export_raw(snapshot_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    filename = f"{snapshot_id}.json"
    return JSONResponse(
        content=raw,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=DesignSnapshot)
async def import_snapshot(
    req: SnapshotImportRequest,
    store: DesignSnapshotStore = Depends(get_snapshot_store),
) -> DesignSnapshot:
    """
    Import a previously exported snapshot.

    If the snapshot_id already exists, a new ID is assigned.
    """
    try:
        return store.import_raw(req.snapshot)
    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")
