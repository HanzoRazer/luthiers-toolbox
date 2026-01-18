from __future__ import annotations

import hashlib
import json
from typing import Any


def _stable(obj: Any) -> str:
    """
    Deterministic JSON serialization:
      - sorted keys
      - no whitespace
      - safe for hashing
    """
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    elif hasattr(obj, "dict"):
        obj = obj.dict()
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def fingerprint_stable(obj: Any) -> str:
    """
    Stable SHA256 fingerprint for design / feasibility objects.
    """
    payload = _stable(obj)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
