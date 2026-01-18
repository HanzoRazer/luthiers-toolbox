"""
Stable fingerprinting for design intent + feasibility payloads.

This is the ONLY approved way to compute fingerprints for:
- design_fingerprint
- feasibility_fingerprint
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.shared.stablejson import stable_dumps

FINGERPRINT_ALGO = "sha256-stablejson-v1"


def fingerprint_stable(obj: Any) -> str:
    """
    Produce a deterministic fingerprint for an object.

    - Uses stable JSON normalization
    - Uses SHA-256
    - Prefixed with algorithm identifier
    """
    payload = stable_dumps(obj).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"{FINGERPRINT_ALGO}:{digest}"
