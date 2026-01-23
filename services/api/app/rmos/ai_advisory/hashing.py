"""
Canonical JSON Hashing

Deterministic JSON canonicalization for provenance tracking.
Uses sorted keys and minimal whitespace for reproducibility.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """
    Produce canonical JSON representation.

    - UTF-8 encoded
    - Sorted keys
    - No extra whitespace
    - ensure_ascii=False for Unicode preservation
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_canonical_json(obj: Any) -> str:
    """
    Compute SHA-256 hash of canonical JSON representation.

    Returns lowercase hex string.
    """
    canonical = canonical_json(obj)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
