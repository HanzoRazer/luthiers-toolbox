from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class Endpoint:
    method: str
    path: str

    def key(self) -> str:
        return f"{self.method.upper()} {self.path}"


def endpoint_to_dict(e: Endpoint) -> Dict[str, str]:
    return {"method": e.method.upper(), "path": e.path}


def safe_json(obj: Any) -> Any:
    """
    Convert objects into JSON-safe types (best-effort).
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): safe_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [safe_json(x) for x in obj]
    return str(obj)
