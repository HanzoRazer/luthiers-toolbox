# File: services/cam_backup_service.py
# CAM settings backup service - creates timestamped snapshots

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Backup directory (relative to services/api)
BACKUP_DIR = Path(__file__).parent.parent.parent / "data" / "backups" / "cam"


def ensure_dir() -> None:
    """Ensure the backup directory exists."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def write_snapshot() -> Path:
    """
    Write a timestamped backup snapshot of CAM settings.
    Returns the path to the created file.
    """
    ensure_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cam_settings_{timestamp}.json"
    path = BACKUP_DIR / filename
    
    # Gather current CAM settings from various sources
    snapshot: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "version": "1.0",
        "settings": _gather_cam_settings(),
    }
    
    path.write_text(json.dumps(snapshot, indent=2))
    return path


def _gather_cam_settings() -> Dict[str, Any]:
    """
    Gather CAM settings from data files.
    Returns a dictionary of all current settings.
    """
    settings: Dict[str, Any] = {}
    data_dir = Path(__file__).parent.parent / "data"
    
    # Collect posts
    posts_dir = data_dir / "posts"
    if posts_dir.exists():
        settings["posts"] = [p.stem for p in posts_dir.glob("*.json")]
    
    # Collect machines
    machines_file = data_dir / "machines.json"
    if machines_file.exists():
        try:
            settings["machines"] = json.loads(machines_file.read_text())
        except json.JSONDecodeError:
            settings["machines"] = {"error": "parse_failed"}
    
    # Collect tools
    tools_file = data_dir / "tools.json"
    if tools_file.exists():
        try:
            settings["tools"] = json.loads(tools_file.read_text())
        except json.JSONDecodeError:
            settings["tools"] = {"error": "parse_failed"}
    
    return settings


def load_snapshot(path: Path) -> Dict[str, Any]:
    """Load a backup snapshot from disk."""
    if not path.exists():
        raise FileNotFoundError(f"Backup not found: {path}")
    return json.loads(path.read_text())
