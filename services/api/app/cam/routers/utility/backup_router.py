"""Backup Router — CAM backup/snapshot endpoints.

Provides:
- POST /backup/snapshot - Force immediate backup
- GET /backup/list - List available backups
- GET /backup/download/{name} - Download specific backup
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Response

from ....services.cam_backup_service import BACKUP_DIR, ensure_dir, write_snapshot

router = APIRouter(prefix="/backup")


@router.post("/snapshot")
async def snapshot_now() -> Dict[str, Any]:
    """Force an immediate backup snapshot."""
    p = write_snapshot()
    return {"status": "ok", "path": str(p)}


@router.get("/list")
async def list_backups() -> List[Dict[str, Any]]:
    """List all available backup files."""
    ensure_dir()
    items: List[Dict[str, Any]] = []
    for p in sorted(BACKUP_DIR.glob("*.json")):
        items.append({"name": p.name, "bytes": p.stat().st_size})
    return items


@router.get("/download/{name}")
async def download_backup(name: str) -> Response:
    """Download a specific backup file."""
    ensure_dir()
    safe = Path(name).name
    path = BACKUP_DIR / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="not found")
    data = path.read_bytes()
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{safe}"'},
    )


__all__ = ["router"]
