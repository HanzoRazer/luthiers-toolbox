"""
RMOS Run Attachments Store

Content-addressed storage for run artifact attachments.
Files are stored by SHA256 hash, ensuring deduplication.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from .hashing import sha256_of_obj, sha256_of_text
from .schemas import RunAttachment


ATTACH_DIR_DEFAULT = "services/api/app/data/run_attachments"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _attach_dir() -> str:
    return os.getenv("RMOS_RUN_ATTACHMENTS_DIR", ATTACH_DIR_DEFAULT)


def _ensure_dir() -> str:
    d = _attach_dir()
    os.makedirs(d, exist_ok=True)
    return d


def _path_for_sha(sha256: str, ext: Optional[str] = None) -> str:
    """Get path for a content-addressed file."""
    fn = sha256 if not ext else f"{sha256}{ext}"
    return os.path.join(_ensure_dir(), fn)


def put_text_attachment(
    *,
    text: str,
    kind: str,
    mime: str,
    filename: str,
    ext: str = ""
) -> Tuple[RunAttachment, str]:
    """
    Store text content as an attachment.
    
    Returns: (RunAttachment metadata, file path)
    """
    sha = sha256_of_text(text)
    path = _path_for_sha(sha, ext=ext or None)
    
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    size = os.path.getsize(path)
    meta = RunAttachment(
        sha256=sha,
        kind=kind,
        mime=mime,
        filename=filename,
        size_bytes=size,
        created_at_utc=_now_utc_iso(),
    )
    return meta, path


def put_json_attachment(
    *,
    obj: Any,
    kind: str,
    filename: str,
    ext: str = ".json"
) -> Tuple[RunAttachment, str, str]:
    """
    Store JSON object as an attachment.
    
    Returns: (RunAttachment metadata, file path, sha256)
    """
    sha = sha256_of_obj(obj)
    path = _path_for_sha(sha, ext=ext)
    
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, sort_keys=True)

    size = os.path.getsize(path)
    meta = RunAttachment(
        sha256=sha,
        kind=kind,
        mime="application/json",
        filename=filename,
        size_bytes=size,
        created_at_utc=_now_utc_iso(),
    )
    return meta, path, sha


def get_attachment_path(sha256: str) -> Optional[str]:
    """
    Get path to attachment blob by SHA256.
    
    Returns None if not found.
    """
    d = _ensure_dir()
    
    # Try exact match first
    exact = os.path.join(d, sha256)
    if os.path.exists(exact):
        return exact
    
    # Try common extensions
    for ext in (".json", ".gcode", ".txt"):
        p = os.path.join(d, f"{sha256}{ext}")
        if os.path.exists(p):
            return p
    
    return None


def load_json_attachment(sha256: str) -> Any:
    """Load JSON content from attachment."""
    path = get_attachment_path(sha256)
    if not path:
        raise FileNotFoundError(f"Attachment blob not found for sha256={sha256}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
