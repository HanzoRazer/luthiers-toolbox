from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.cnc_production.feeds_speeds.core.feeds_speeds_resolver import resolve_feeds_speeds
from app.cnc_production.feeds_speeds.core.presets_db import load_presets

router = APIRouter(prefix="/feeds-speeds", tags=["feeds-speeds"])


@router.get("/resolve")
def resolve(tool_id: str, material: str, mode: str = "roughing"):
    """Resolve RPM/feed guidance for the requested tool/material."""
    try:
        return resolve_feeds_speeds(tool_id, material, mode)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reload")
def reload_presets():
    """Reload preset JSON files from disk for hot-reload friendly tuning."""
    load_presets()
    return {"status": "ok", "message": "Feeds & speeds presets reloaded."}
