"""
Simple in-memory PipelinePresetStore used for testing and development.

Provides a minimal interface expected by the pipeline preset run router:
- get(preset_id) -> dict | None
- save(preset_id, payload) -> dict
- list() -> list[dict]

This is intentionally lightweight. Production should replace with DB-backed store.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4


class PipelinePresetStore:
    """In-memory preset store.

    Note: Not thread-safe or persistent. Intended for local dev and smoke tests.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def get(self, preset_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(preset_id)

    def save(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure an id exists
        preset_id = payload.get("id") or payload.get("name") or f"preset_{uuid4().hex[:8]}"
        record = {"id": preset_id, **payload}
        self._store[preset_id] = record
        return record

    def list(self) -> list[Dict[str, Any]]:
        return list(self._store.values())


_default_store = PipelinePresetStore()

def get_default_store() -> PipelinePresetStore:
    return _default_store
