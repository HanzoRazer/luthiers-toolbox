"""Saw Lab queue placeholders."""
from __future__ import annotations

from typing import List, Dict, Any


class SawLabQueue:
    """In-memory placeholder queue; persist later."""

    def __init__(self) -> None:
        self._items: List[Dict[str, Any]] = []

    def enqueue(self, item: Dict[str, Any]) -> None:
        self._items.append(item)

    def dequeue(self) -> Dict[str, Any] | None:
        if self._items:
            return self._items.pop(0)
        return None

    def snapshot(self) -> List[Dict[str, Any]]:
        return list(self._items)
