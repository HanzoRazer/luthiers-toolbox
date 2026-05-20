"""
JSON Serialization Utilities for Morphology Harvest
====================================================

Provides json_safe() utility for converting complex objects
(enums, dataclasses, paths) to JSON-serializable primitives.

Used at export/report boundaries only. Internal model fields
retain their native types.

Author: Production Shop
Date: 2026-05-19
Sprint: IBG Morphology Harvest 1B Unblock
"""

from __future__ import annotations

import json
from dataclasses import is_dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


def json_safe(value: Any) -> Any:
    """
    Recursively convert value to JSON-serializable form.

    Handles:
    - Enum → value (string/int)
    - dataclass → dict (recursively)
    - Path → str
    - datetime → isoformat string
    - set → list
    - dict → dict with json_safe values
    - list/tuple → list with json_safe values
    - other → passthrough

    Use at export boundary:
        return json_safe(payload)
        json.dump(json_safe(data), f)
    """
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return json_safe(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, set):
        return [json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


class SafeJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that handles enums, dataclasses, paths, datetimes.

    Use as:
        json.dumps(data, cls=SafeJSONEncoder)
        json.dump(data, f, cls=SafeJSONEncoder)
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Enum):
            return obj.value
        if is_dataclass(obj) and not isinstance(obj, type):
            return json_safe(asdict(obj))
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)
