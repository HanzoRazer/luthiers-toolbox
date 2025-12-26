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


def _get_runs_root() -> Path:
    return Path(os.getenv("RMOS_RUNS_ROOT", RUNS_ROOT_DEFAULT)).expanduser().resolve()


def _get_attachments_root() -> Path:
    return Path(os.getenv("RMOS_RUN_ATTACHMENTS_DIR", ATTACHMENTS_ROOT_DEFAULT)).expanduser().resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _guess_mime(ext: str) -> Optional[str]:
    e = ext.lower()
    if e == ".wav":
        return "audio/wav"
    if e == ".json":
        return "application/json"
    if e == ".csv":
        return "text/csv"
    if e == ".png":
        return "image/png"
    if e in (".jpg", ".jpeg"):
        return "image/jpeg"
    if e == ".txt":
        return "text/plain"
    if e == ".dxf":
        return "image/vnd.dxf"  # not perfect, but fine
    if e in (".nc", ".gcode"):
        return "text/plain"
    return None


def _safe_ext_from_relpath(relpath: str) -> str:
    name = relpath.replace("\\", "/").split("/")[-1]
    return Path(name).suffix if name else ""


def _sharded_path(root: Path, sha256_hex: str, ext: str) -> Path:
    return root / sha256_hex[:2] / sha256_hex[2:4] / f"{sha256_hex}{ext}"


def _resolve_blob_path(root: Path, sha256_hex: str, ext_hint: str) -> Optional[Path]:
    """
    Resolve actual stored blob file for sha256.
    Prefer ext_hint; otherwise probe common extensions in the shard directory.
    """
    shard_dir = root / sha256_hex[:2] / sha256_hex[2:4]
    if not shard_dir.exists():
        return None

    if ext_hint:
        p = shard_dir / f"{sha256_hex}{ext_hint}"
        if p.exists():
            return p

    # probe common
    common = [".json", ".wav", ".csv", ".png", ".jpg", ".jpeg", ".txt", ".nc", ".gcode", ".dxf"]
    for e in common:
        p = shard_dir / f"{sha256_hex}{e}"
        if p.exists():
            return p

    # try no extension
    p0 = shard_dir / sha256_hex
    return p0 if p0.exists() else None


def _find_run_json_path(run_id: str) -> Path:
    runs_root = _get_runs_root()
    idx_path = runs_root / INDEX_FILENAME

    # 1) Use index path if present
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
                                return p
        except Exception:
            pass

    # 2) Scan date partitions
    target = f"run_{run_id}.json"
    if not runs_root.exists():
        raise HTTPException(status_code=404, detail="runs store not found")

    for child in sorted(runs_root.iterdir(), reverse=True):
        if not child.is_dir():
            continue
        name = child.name
        if len(name) != 10 or name[4] != "-" or name[7] != "-":
            continue
        p = child / target
        if p.exists() and p.is_file():
            return p

    raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")


class RunAttachmentResolved(BaseModel):
    sha256: str
    relpath: Optional[str] = None
    kind: Optional[str] = None
    point_id: Optional[str] = None

    exists: bool
    resolved_path: Optional[str] = None
    bytes: Optional[int] = None
    mime: Optional[str] = None
    ext: Optional[str] = None


class RunAttachmentsResponse(BaseModel):
    run_id: str
    run_json_path: str
    attachments: list[RunAttachmentResolved]


@router.get("/runs/{run_id}/attachments", response_model=RunAttachmentsResponse)
def list_run_attachments(
    run_id: str,
    download: int = Query(default=0, description="Set 1 to stream a single attachment selected by sha256 param"),
    sha256: Optional[str] = Query(default=None, description="Required if download=1; which attachment to stream"),
) -> RunAttachmentsResponse:
    """
    List attachments for a run with resolved path/bytes/mime.

    If download=1 and sha256=<...> is provided, streams that attachment instead of returning JSON.
    """
    run_path = _find_run_json_path(run_id)
    run_obj = _load_json(run_path)

    attachments = run_obj.get("attachments", [])
    if not isinstance(attachments, list):
        attachments = []

    # Optional streaming mode
    if download == 1:
        if not sha256:
            raise HTTPException(status_code=400, detail="sha256 query param required when download=1")
        s = sha256.lower().strip()
        if not _SHA_RE.match(s):
            raise HTTPException(status_code=400, detail="Invalid sha256")
        # find the attachment record (to get relpath for ext)
        rec = None
        for a in attachments:
            if isinstance(a, dict) and (a.get("sha256") or "").lower() == s:
                rec = a
                break
        if rec is None:
            raise HTTPException(status_code=404, detail="sha256 not found in this run attachments list")

        ext_hint = _safe_ext_from_relpath(str(rec.get("relpath") or ""))
        blob_root = _get_attachments_root()
        p = _resolve_blob_path(blob_root, s, ext_hint)
        if p is None:
            raise HTTPException(status_code=404, detail="attachment blob not found in store")

        mime = _guess_mime(p.suffix) or "application/octet-stream"
        return FileResponse(path=str(p), media_type=mime, filename=p.name)

    # JSON listing mode
    blob_root = _get_attachments_root()
    out: list[RunAttachmentResolved] = []

    for a in attachments:
        if not isinstance(a, dict):
            continue
        sha = (a.get("sha256") or "").lower().strip()
        if not _SHA_RE.match(sha):
            # skip malformed records
            continue

        relpath = a.get("relpath")
        kind = a.get("kind")
        point_id = a.get("point_id")

        ext_hint = _safe_ext_from_relpath(str(relpath or ""))
        p = _resolve_blob_path(blob_root, sha, ext_hint)

        if p is None:
            out.append(RunAttachmentResolved(
                sha256=sha,
                relpath=relpath,
                kind=kind,
                point_id=point_id,
                exists=False,
            ))
            continue

        st = p.stat()
        out.append(RunAttachmentResolved(
            sha256=sha,
            relpath=relpath,
            kind=kind,
            point_id=point_id,
            exists=True,
            resolved_path=str(p),
            bytes=int(st.st_size),
            mime=_guess_mime(p.suffix),
            ext=p.suffix or None,
        ))

    return RunAttachmentsResponse(
        run_id=run_id,
        run_json_path=str(run_path),
        attachments=out,
    )
