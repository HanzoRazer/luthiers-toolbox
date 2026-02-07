"""
Phase 27.0: Rosette Compare Mode MVP
Baseline storage service using JSON files
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from ..models.compare_baseline import CompareBaselineOut, CompareBaselineSummary

BASELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "baselines"


def _ensure_dir() -> None:
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)


def _baseline_path(baseline_id: str) -> Path:
    return BASELINES_DIR / f"{baseline_id}.json"


def save_baseline(baseline: CompareBaselineOut) -> None:
    """Save a baseline to disk as JSON."""
    _ensure_dir()
    path = _baseline_path(baseline.id)
    payload = {
        "id": baseline.id,
        "name": baseline.name,
        "lane": baseline.lane,
        "created_at": baseline.created_at.isoformat(),
        "geometry": baseline.geometry,
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def list_baselines(lane: str | None = None) -> List[CompareBaselineSummary]:
    """List all baselines, optionally filtered by lane."""
    _ensure_dir()
    out: List[CompareBaselineSummary] = []
    for file in BASELINES_DIR.glob("*.json"):
        try:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if lane and data.get("lane") != lane:
                continue
            created_at = datetime.fromisoformat(data["created_at"])
            out.append(
                CompareBaselineSummary(
                    id=data["id"],
                    name=data["name"],
                    lane=data["lane"],
                    created_at=created_at,
                )
            )
        except (OSError, json.JSONDecodeError, KeyError, ValueError):  # WP-1: narrowed from except Exception
            # ignore malformed baselines in MVP
            continue
    # newest first
    out.sort(key=lambda b: b.created_at, reverse=True)
    return out


def load_baseline(baseline_id: str) -> CompareBaselineOut | None:
    """Load a single baseline by ID with full geometry."""
    path = _baseline_path(baseline_id)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    created_at = datetime.fromisoformat(data["created_at"])
    return CompareBaselineOut(
        id=data["id"],
        name=data["name"],
        lane=data["lane"],
        created_at=created_at,
        geometry=data["geometry"],
    )
