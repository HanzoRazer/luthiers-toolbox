"""Persistent storage helpers for Compare Lab baselines."""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.compare_baseline import Baseline, BaselineGeometry, BaselineToolpath

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "compare" / "baselines"


def _ensure_data_dir() -> None:
    """Create data directory on first write (not at import time for Docker compatibility)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _baseline_path(baseline_id: str) -> Path:
    return DATA_DIR / f"{baseline_id}.json"


def list_baselines() -> List[Baseline]:
    baselines: List[Baseline] = []
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            baselines.append(Baseline.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return baselines


def load_baseline(baseline_id: str) -> Optional[Baseline]:
    path = _baseline_path(baseline_id)
    if not path.exists():
        return None
    return Baseline.model_validate_json(path.read_text(encoding="utf-8"))


def delete_baseline(baseline_id: str) -> bool:
    path = _baseline_path(baseline_id)
    if not path.exists():
        return False
    path.unlink()
    return True


def save_baseline(payload: Dict[str, Any]) -> Baseline:
    baseline_id = payload.get("id") or str(uuid.uuid4())
    now_iso = datetime.utcnow().isoformat()

    geometry = payload.get("geometry") or {}
    toolpath = payload.get("toolpath") or None

    baseline = Baseline(
        id=baseline_id,
        name=payload.get("name", "Untitled Baseline"),
        type=payload.get("type", "geometry"),
        created_at=payload.get("created_at", now_iso),
        description=payload.get("description"),
        tags=payload.get("tags", []),
        preset_id=payload.get("preset_id"),
        preset_name=payload.get("preset_name"),
        machine_id=payload.get("machine_id"),
        post_id=payload.get("post_id"),
        geometry=BaselineGeometry(**geometry) if geometry else None,
        toolpath=BaselineToolpath(**toolpath) if toolpath else None,
    )

    _ensure_data_dir()  # Create directory on first write
    _baseline_path(baseline_id).write_text(baseline.model_dump_json(indent=2), encoding="utf-8")
    return baseline
