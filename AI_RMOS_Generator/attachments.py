"""
RMOS Runs v2 Attachments

Content-addressed attachment storage with integrity verification.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .hashing import sha256_bytes, sha256_file, verify_hash


def _attachments_root() -> Path:
    """Get attachments root directory."""
    root = os.environ.get("RMOS_ATTACHMENTS_DIR", "data/runs/attachments")
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path_for_sha(sha256: str) -> Path:
    """
    Get filesystem path for attachment by SHA256.
    
    Uses two-level directory structure: ab/cd/abcdef...
    """
    root = _attachments_root()
    prefix = sha256[:2]
    subdir = sha256[2:4]
    return root / prefix / subdir / sha256


def get_attachment_path(sha256: str) -> Optional[str]:
    """
    Get filesystem path for attachment if it exists.
    
    Returns None if attachment not found.
    """
    path = _path_for_sha(sha256)
    if path.exists():
        return str(path)
    return None


def store_attachment(content: bytes, filename: str) -> str:
    """
    Store attachment content, return SHA256.

    Content-addressed: same content = same hash = deduplicated.
    """
    sha = sha256_bytes(content)
    target_path = _path_for_sha(sha)

    if not target_path.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = target_path.with_suffix(".tmp")
        tmp.write_bytes(content)
        os.replace(tmp, target_path)

    return sha


def verify_attachment(sha256: str) -> bool:
    """
    Verify attachment integrity by recomputing hash.
    
    Returns True if file exists and hash matches.
    """
    path = get_attachment_path(sha256)
    if path is None:
        return False
    actual = sha256_file(path)
    return verify_hash(sha256, actual)


def delete_attachment(sha256: str) -> bool:
    """
    Delete attachment by SHA256.
    
    WARNING: Only use for cleanup of orphaned attachments.
    Returns True if deleted, False if not found.
    """
    path = _path_for_sha(sha256)
    if path.exists():
        path.unlink()
        return True
    return False


def list_attachments() -> list[str]:
    """List all attachment SHA256 hashes."""
    root = _attachments_root()
    hashes = []
    
    for prefix_dir in root.iterdir():
        if not prefix_dir.is_dir():
            continue
        for subdir in prefix_dir.iterdir():
            if not subdir.is_dir():
                continue
            for file_path in subdir.iterdir():
                if file_path.is_file() and len(file_path.name) == 64:
                    hashes.append(file_path.name)
    
    return hashes


def get_attachment_size(sha256: str) -> Optional[int]:
    """Get attachment file size in bytes."""
    path = get_attachment_path(sha256)
    if path is None:
        return None
    return Path(path).stat().st_size
