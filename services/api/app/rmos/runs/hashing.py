"""
RMOS Hashing Utilities

Provides deterministic hashing for run artifacts and payloads.
Critical for replay and drift detection.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_json_dumps(obj: Any) -> str:
    """
    Produce deterministic JSON string.
    
    - Sorted keys
    - Compact separators
    - UTF-8 encoding
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_of_obj(obj: Any) -> str:
    """Compute SHA256 hash of a JSON-serializable object."""
    s = stable_json_dumps(obj)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_of_text(text: str) -> str:
    """Compute SHA256 hash of text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_of_bytes(data: bytes) -> str:
    """Compute SHA256 hash of binary data."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
