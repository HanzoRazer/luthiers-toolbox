from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

PRESETS_PATH = Path("data/art_presets.json")


@dataclass
class ArtPreset:
    id: str
    lane: str  # rosette / adaptive / relief / "all"
    name: str
    params: Dict[str, Any]
    created_at: float


def _load() -> List[Dict[str, Any]]:
    if not PRESETS_PATH.exists():
        return []
    try:
        raw = PRESETS_PATH.read_text(encoding="utf-8")
        if not raw.strip():
            return []
        return json.loads(raw)
    except Exception:
        return []


def _save(rows: List[Dict[str, Any]]) -> None:
    PRESETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRESETS_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def list_presets(lane: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = _load()
    rows.sort(key=lambda r: r.get("created_at", 0.0), reverse=True)
    if lane:
        rows = [r for r in rows if r.get("lane") in (lane, "all")]
    return rows


def create_preset(lane: str, name: str, params: Dict[str, Any]) -> ArtPreset:
    rows = _load()
    pid = f"{lane}_preset_{int(time.time()*1000)}"
    preset = ArtPreset(
        id=pid,
        lane=lane,
        name=name,
        params=params,
        created_at=time.time(),
    )
    rows.append(asdict(preset))
    _save(rows)
    return preset


def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    rows = _load()
    for row in rows:
        if row.get("id") == preset_id:
            return row
    return None


def delete_preset(preset_id: str) -> bool:
    rows = _load()
    before = len(rows)
    rows = [r for r in rows if r.get("id") != preset_id]
    if len(rows) == before:
        return False
    _save(rows)
    return True
