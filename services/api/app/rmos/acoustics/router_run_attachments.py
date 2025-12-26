from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .persist_glue import RUNS_ROOT_DEFAULT, ATTACHMENTS_ROOT_DEFAULT, INDEX_FILENAME

router = APIRouter(prefix="/api/rmos/acoustics", tags=["rmos", "acoustics"])

_SHA_RE = re.compile(r"^[a-f0-9]{64}$")


def _runs_root() -> Path:
    return Path(os.getenv("RMOS_RUNS_ROOT", RUNS_ROOT_DEFAULT)).expanduser().resolve()


def _attachments_root() -> Path:
    return Path(os.getenv("RMOS_RUN_ATTACHMENTS_DIR", ATTACHMENTS_ROOT_DEFAULT)).expanduser().resolve()


def _load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def _guess_mime(ext: str) -> Optional[str]:
    return {
        ".wav": "audio/wav",
        ".json": "application/json",
        ".csv": "text/csv",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".txt": "text/plain",
        ".dxf": "image/vnd.dxf",
        ".nc": "text/plain",
        ".gcode": "text/plain",
    }.get(ext.lower())


def _safe_ext(relpath: str) -> str:
    return Path(relpath.replace("\\", "/")).suffix if relpath else ""


def _resolve_blob(root: Path, sha: str, ext_hint: str) -> Optional[Path]:
    shard = root / sha[:2] / sha[2:4]
    if not shard.exists():
        return None

    if ext_hint:
        p = shard / f"{sha}{ext_hint}"
        if p.exists():
            return p

    for e in [".json", ".wav", ".csv", ".png", ".jpg", ".jpeg", ".txt", ".nc", ".gcode", ".dxf"]:
        p = shard / f"{sha}{e}"
        if p.exists():
            return p

    p0 = shard / sha
    return p0 if p0.exists() else None


def _find_run_json(run_id: str) -> Path:
    runs_root = _runs_root()
    idx = runs_root / INDEX_FILENAME

    if idx.exists():
        try:
            data = _load_json(idx)
            for r in data.get("runs", []):
                if r.get("run_id") == run_id and r.get("path"):
                    p = (runs_root / r["path"]).resolve()
                    if p.exists():
                        return p
        except Exception:
            pass

    target = f"run_{run_id}.json"
    for d in runs_root.iterdir():
        if d.is_dir():
            p = d / target
            if p.exists():
                return p

    raise HTTPException(status_code=404, detail="run not found")


class RunAttachmentResolved(BaseModel):
    sha256: str
    relpath: Optional[str]
    kind: Optional[str]
    point_id: Optional[str]

    exists: bool
    bytes: Optional[int]
    ext: Optional[str]
    mime: Optional[str]


class RunAttachmentsResponse(BaseModel):
    run_id: str
    attachments: list[RunAttachmentResolved]


@router.get("/runs/{run_id}/attachments", response_model=RunAttachmentsResponse)
def list_run_attachments(
    run_id: str,
    download: int = Query(default=0),
    sha256: Optional[str] = Query(default=None),
):
    """
    List attachments for a run with resolved metadata (no path disclosure).

    If download=1 and sha256=<...> is provided, streams that attachment.
    """
    run_path = _find_run_json(run_id)
    run = _load_json(run_path)
    records = run.get("attachments", [])

    blob_root = _attachments_root()

    if download == 1:
        if not sha256 or not _SHA_RE.match(sha256):
            raise HTTPException(status_code=400, detail="Valid sha256 required")
        for r in records:
            if r.get("sha256") == sha256:
                ext = _safe_ext(r.get("relpath", ""))
                blob = _resolve_blob(blob_root, sha256, ext)
                if not blob:
                    raise HTTPException(status_code=404, detail="blob not found")
                return FileResponse(
                    path=str(blob),
                    media_type=_guess_mime(blob.suffix) or "application/octet-stream",
                    filename=blob.name,
                )
        raise HTTPException(status_code=404, detail="attachment not in run")

    out: list[RunAttachmentResolved] = []
    for r in records:
        sha = r.get("sha256")
        if not sha or not _SHA_RE.match(sha):
            continue

        ext = _safe_ext(r.get("relpath", ""))
        blob = _resolve_blob(blob_root, sha, ext)

        if not blob:
            out.append(RunAttachmentResolved(
                sha256=sha,
                relpath=r.get("relpath"),
                kind=r.get("kind"),
                point_id=r.get("point_id"),
                exists=False,
                bytes=None,
                ext=None,
                mime=None,
            ))
            continue

        st = blob.stat()
        out.append(RunAttachmentResolved(
            sha256=sha,
            relpath=r.get("relpath"),
            kind=r.get("kind"),
            point_id=r.get("point_id"),
            exists=True,
            bytes=int(st.st_size),
            ext=blob.suffix or None,
            mime=_guess_mime(blob.suffix),
        ))

    return RunAttachmentsResponse(run_id=run_id, attachments=out)
