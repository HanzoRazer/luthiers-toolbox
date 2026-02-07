from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response


router = APIRouter(prefix="/attachments", tags=["runs"])


def _attachments_root() -> Path:
    # mirror attachments.py default + env var
    default_root = "services/api/data/run_attachments"
    root = os.getenv("RMOS_RUN_ATTACHMENTS_DIR", default_root)
    return Path(root)


def _read_meta(sha256: str) -> dict:
    root = _attachments_root()
    meta_path = root / f"{sha256}.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):  # WP-1: narrowed from except Exception
            return {}
    return {}


@router.get("/{sha256}")
def get_attachment_global(sha256: str):
    """
    Global content-addressed attachment fetch.
    Fixes truncated diff UX and allows direct toolpath downloads without run_id.
    """
    if not sha256 or len(sha256) < 16:
        raise HTTPException(status_code=400, detail="invalid sha256")

    root = _attachments_root()
    data_path = root / sha256
    if not data_path.exists():
        # some older writers may store with extension; try common
        for ext in (".txt", ".diff", ".gcode", ".json"):
            p = root / f"{sha256}{ext}"
            if p.exists():
                data_path = p
                break
    if not data_path.exists():
        raise HTTPException(status_code=404, detail="attachment not found")

    meta = _read_meta(sha256)
    mime = meta.get("mime") if isinstance(meta.get("mime"), str) else "application/octet-stream"
    filename = meta.get("filename") if isinstance(meta.get("filename"), str) else sha256

    try:
        data = data_path.read_bytes()
    except OSError:  # WP-1: narrowed from except Exception
        raise HTTPException(status_code=500, detail="failed to read attachment")

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=data, media_type=mime, headers=headers)
