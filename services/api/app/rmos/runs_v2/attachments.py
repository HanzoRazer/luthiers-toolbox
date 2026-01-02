"""
RMOS Run Attachments v2 - Content-Addressed Storage

Content-addressed attachment storage using SHA256 hashes.
Files are stored by their content hash, providing natural deduplication.

Preserved from v1 implementation with Pydantic schema updates.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .schemas import RunAttachment
from .hashing import sha256_of_obj, sha256_of_text, sha256_of_bytes, sha256_file


# Default storage path
ATTACHMENTS_DIR_DEFAULT = "services/api/data/run_attachments"


def _get_attachments_dir() -> str:
    """Get attachments directory from environment or default."""
    return os.getenv("RMOS_RUN_ATTACHMENTS_DIR", ATTACHMENTS_DIR_DEFAULT)


def _ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def _path_for_sha(sha256: str, ext: str = "") -> Path:
    """
    Get the storage path for a content hash.

    Uses two-level directory structure for better filesystem performance:
    {root}/{sha[0:2]}/{sha[2:4]}/{sha}{ext}
    """
    root = Path(_get_attachments_dir())
    # Two-level sharding by hash prefix
    return root / sha256[:2] / sha256[2:4] / f"{sha256}{ext}"


def put_bytes_attachment(
    data: bytes,
    kind: str,
    mime: str,
    filename: str,
    ext: str = "",
) -> Tuple[RunAttachment, str]:
    """
    Store binary data as a content-addressed attachment.

    Args:
        data: Binary content to store
        kind: Attachment type (geometry, toolpaths, gcode, debug)
        mime: MIME type
        filename: Display filename
        ext: File extension (e.g., ".json", ".gcode")

    Returns:
        Tuple of (RunAttachment metadata, storage path)
    """
    sha = sha256_of_bytes(data)
    path = _path_for_sha(sha, ext)

    # Only write if not already present (deduplication)
    if not path.exists():
        _ensure_dir(path.parent)
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            tmp.write_bytes(data)
            os.replace(tmp, path)
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise

    from datetime import datetime, timezone
    attachment = RunAttachment(
        sha256=sha,
        kind=kind,
        mime=mime,
        filename=filename,
        size_bytes=len(data),
        created_at_utc=datetime.now(timezone.utc).isoformat(),
    )

    return attachment, str(path)


def put_text_attachment(
    text: str,
    kind: str,
    mime: str = "text/plain",
    filename: str = "attachment.txt",
    ext: str = ".txt",
) -> Tuple[RunAttachment, str]:
    """
    Store text content as a content-addressed attachment.

    Args:
        text: Text content to store
        kind: Attachment type
        mime: MIME type (default: text/plain)
        filename: Display filename
        ext: File extension

    Returns:
        Tuple of (RunAttachment metadata, storage path)
    """
    data = text.encode("utf-8")
    return put_bytes_attachment(data, kind, mime, filename, ext)


def put_json_attachment(
    obj: Any,
    kind: str,
    filename: str = "data.json",
    ext: str = ".json",
) -> Tuple[RunAttachment, str, str]:
    """
    Store JSON-serializable object as a content-addressed attachment.

    Uses stable_json_dumps for deterministic serialization.

    Args:
        obj: JSON-serializable object
        kind: Attachment type
        filename: Display filename
        ext: File extension

    Returns:
        Tuple of (RunAttachment metadata, storage path, sha256 hash)
    """
    # Use deterministic JSON serialization
    from .hashing import stable_json_dumps
    text = stable_json_dumps(obj)
    data = text.encode("utf-8")

    sha = sha256_of_bytes(data)
    path = _path_for_sha(sha, ext)

    # Only write if not already present
    if not path.exists():
        _ensure_dir(path.parent)
        # Pretty print for readability while preserving hash
        pretty = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            tmp.write_text(pretty, encoding="utf-8")
            os.replace(tmp, path)
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise

    from datetime import datetime, timezone
    attachment = RunAttachment(
        sha256=sha,
        kind=kind,
        mime="application/json",
        filename=filename,
        size_bytes=len(data),
        created_at_utc=datetime.now(timezone.utc).isoformat(),
    )

    return attachment, str(path), sha


def get_attachment_path(sha256: str) -> Optional[str]:
    """
    Get the filesystem path for an attachment by its SHA256 hash.

    Tries common extensions if exact match not found.

    Args:
        sha256: The content hash

    Returns:
        Path string if found, None otherwise
    """
    # Try with no extension first
    path = _path_for_sha(sha256)
    if path.exists():
        return str(path)

    # Try common extensions
    for ext in [".json", ".gcode", ".txt", ".svg", ".dxf"]:
        path = _path_for_sha(sha256, ext)
        if path.exists():
            return str(path)

    return None


def get_bytes_attachment(sha256: str) -> Optional[bytes]:
    """
    Get the raw bytes of an attachment by its SHA256 hash.

    Args:
        sha256: The content hash

    Returns:
        Bytes content if found, None otherwise
    """
    path = get_attachment_path(sha256)
    if path is None:
        return None
    try:
        return Path(path).read_bytes()
    except Exception:
        return None


def load_json_attachment(sha256: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON attachment by its SHA256 hash.

    Args:
        sha256: The content hash

    Returns:
        Parsed JSON object if found, None otherwise
    """
    path = get_attachment_path(sha256)
    if path is None:
        return None

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def verify_attachment(sha256: str) -> Dict[str, Any]:
    """
    Verify an attachment's integrity by recomputing its hash.

    Args:
        sha256: Expected content hash

    Returns:
        Verification result dict with 'ok', 'actual_sha256', etc.
    """
    path = get_attachment_path(sha256)

    if path is None:
        return {
            "sha256": sha256,
            "ok": False,
            "error": "blob_not_found",
        }

    try:
        actual = sha256_file(path)
        match = actual == sha256
        return {
            "sha256": sha256,
            "ok": match,
            "path": path,
            "size_bytes": os.path.getsize(path),
            "actual_sha256": actual,
            "error": None if match else "hash_mismatch",
        }
    except Exception as e:
        return {
            "sha256": sha256,
            "ok": False,
            "error": str(e),
        }


# =============================================================================
# INTERNAL RESOLVER HELPERS (no path disclosure in responses)
# =============================================================================


def resolve_attachment_path(sha256: str) -> Path:
    """
    Resolve the on-disk shard path for a given sha256 in the attachments store.

    INTERNAL USE ONLY.
    Do not return this path directly to untrusted clients.
    """
    root = Path(_get_attachments_dir()).expanduser().resolve()
    s = sha256.lower()
    shard = root / s[0:2] / s[2:4]

    # Try common extensions (fast-path).
    # NOTE: sha256 is authoritative; ext is only a convenience.
    for ext in [
        "",
        ".json",
        ".txt",
        ".csv",
        ".npz",
        ".wav",
        ".png",
        ".jpg",
        ".jpeg",
        ".svg",
        ".dxf",
        ".gcode",
        ".nc",
    ]:
        candidate = shard / f"{s}{ext}"
        if candidate.exists():
            return candidate

    # Fallback: accept any extension (no extension knowledge required).
    # This supports files like {sha256}.bin or uncommon artifacts while still
    # keeping sha256 as the primary key.
    matches = sorted(shard.glob(f"{s}.*"))
    if matches:
        return matches[0]

    # Not found: return the no-extension canonical path (callers can .exists()).
    return shard / s


def attachment_exists(sha256: str) -> bool:
    """Internal check for attachment existence by sha256."""
    return resolve_attachment_path(sha256).exists()


def attachment_stat(sha256: str) -> Optional[Dict[str, Any]]:
    """Internal stat metadata for an attachment blob (no path disclosure)."""
    p = resolve_attachment_path(sha256)
    if not p.exists():
        return None
    st = p.stat()
    return {
        "sha256": sha256.lower(),
        "size_bytes": int(st.st_size),
        "modified_at_utc": None,  # keep None unless you have an utc formatter util here
    }
