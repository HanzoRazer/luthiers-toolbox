"""JSON-backed CNC Production preset store (B20).

Provides simple helpers to load and persist preset definitions that back the
CNC Production Preset Manager. The store intentionally keeps a transparent
JSON structure (`data/presets/presets.json`) for easy backup and manual edits.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parents[2]
PRESETS_PATH = BASE_DIR / "data" / "presets" / "presets.json"


def _ensure_dir() -> None:
    PRESETS_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_all_presets() -> List[Dict[str, Any]]:
    """Return every stored preset. Malformed files fall back to []."""
    if not PRESETS_PATH.exists():
        return []
    try:
        data = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (OSError, json.JSONDecodeError, ValueError):  # WP-1: narrowed from except Exception
        pass
    return []


def save_all_presets(presets: List[Dict[str, Any]]) -> None:
    _ensure_dir()
    PRESETS_PATH.write_text(
        json.dumps(presets, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
