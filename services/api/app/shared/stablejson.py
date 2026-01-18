"""
Stable JSON normalization utilities.

Goal:
- Deterministic output across Python versions
- Deterministic key ordering
- Stable float formatting
- No dependence on Pydantic's internal ordering
"""

from __future__ import annotations

import json
from typing import Any


def _normalize(value: Any) -> Any:
    """Recursively normalize a value for stable JSON serialization."""
    if value is None:
        return None

    if isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        # Normalize floats to fixed precision to avoid drift across repr changes
        return round(value, 6)

    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]

    if isinstance(value, dict):
        # Sort keys for stability
        return {k: _normalize(value[k]) for k in sorted(value.keys())}

    # Pydantic v2
    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump(exclude_none=True))

    # Pydantic v1 or other models
    if hasattr(value, "dict"):
        try:
            return _normalize(value.dict(exclude_none=True))
        except TypeError:
            return _normalize(value.dict())

    # Fallback: stable string
    return str(value)


def stable_dumps(obj: Any) -> str:
    """
    Convert an object to canonical JSON string:
    - normalized structure
    - sorted keys
    - no whitespace
    - stable float precision
    """
    normalized = _normalize(obj)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
