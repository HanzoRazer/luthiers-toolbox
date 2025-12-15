# File: services/api/app/services/job_int_favorites.py
# NEW – JSON-backed favorites store for Job Intelligence runs

from __future__ import annotations

import json
import os
from typing import Any, Dict

DEFAULT_FAVORITES_PATH = os.path.join("data", "cam_job_favorites.json")


def _ensure_dir(path: str) -> None:
    """Ensure parent directory exists for the given file path."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def load_job_favorites(path: str = DEFAULT_FAVORITES_PATH) -> Dict[str, Dict[str, Any]]:
    """
    Load favorites map from disk.
    
    Structure:
    {
      "run-123": { "favorite": true },
      "run-456": { "favorite": false }
    }
    
    Returns:
        Dictionary mapping run_id to favorite metadata.
    """
    if not os.path.exists(path):
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    
    if not isinstance(data, dict):
        return {}
    
    return data  # type: ignore[return-value]


def save_job_favorites(
    favorites: Dict[str, Dict[str, Any]],
    path: str = DEFAULT_FAVORITES_PATH,
) -> None:
    """Save favorites map to disk."""
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


def get_job_favorite(
    run_id: str,
    *,
    path: str = DEFAULT_FAVORITES_PATH,
) -> bool:
    """
    Get favorite flag for a specific run_id.
    
    Returns:
        True if marked as favorite, False otherwise.
    """
    favs = load_job_favorites(path=path)
    rec = favs.get(run_id)
    if not isinstance(rec, dict):
        return False
    return bool(rec.get("favorite", False))


def update_job_favorite(
    run_id: str,
    favorite: bool,
    *,
    path: str = DEFAULT_FAVORITES_PATH,
) -> bool:
    """
    Set favorite flag for a run_id. Returns the new favorite value.
    
    Args:
        run_id: Pipeline run ID to update.
        favorite: New favorite status.
        path: Path to favorites JSON file.
    
    Returns:
        The new favorite status (should match `favorite` parameter).
    """
    favs = load_job_favorites(path=path)
    rec = favs.get(run_id) or {}
    rec["favorite"] = bool(favorite)
    favs[run_id] = rec
    save_job_favorites(favs, path=path)
    return rec["favorite"]
