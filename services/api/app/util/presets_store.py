"""
Unified Preset Store - Backend Foundation for CAM + Export + Neck Presets

Implements the unified preset architecture per UNIFIED_PRESETS_DESIGN.md
Storage: server/data/presets.json

Schema supports:
- kind: "cam" | "export" | "neck" | "combo"
- cam_params: CAM operation parameters (stepover, strategy, etc.)
- export_params: Export configuration (filename_template, include_flags)
- neck_params: Neck profile defaults (profile_id, scale_length, sections)

Migrates legacy 'lane' field to 'kind' for backward compatibility.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parents[2]
PRESETS_PATH = BASE_DIR / "data" / "presets.json"

PresetKind = Literal["cam", "export", "neck", "combo"]


class PresetFilter(BaseModel):
    """Filter criteria for listing presets."""
    kind: Optional[PresetKind] = Field(None, description="Filter by preset kind")
    tag: Optional[str] = Field(None, description="Filter by tag")
    name_contains: Optional[str] = Field(None, description="Filter by name substring")


def _ensure_dir() -> None:
    """Ensure presets directory exists."""
    PRESETS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _migrate_legacy_preset(preset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate legacy preset format to unified schema.
    
    Converts:
    - 'lane' field → 'kind' field
    - flat params → cam_params (if kind=cam)
    """
    # If already has 'kind', no migration needed
    if "kind" in preset:
        return preset
    
    # Migrate 'lane' → 'kind'
    if "lane" in preset:
        lane = preset.get("lane", "")
        # Map lanes to kinds
        if lane in ("adaptive", "roughing", "finishing", "drilling"):
            preset["kind"] = "cam"
        elif lane in ("rosette", "relief"):
            preset["kind"] = "cam"  # Art Studio lanes are CAM operations
        else:
            preset["kind"] = "cam"  # Default to CAM for unknown lanes
        
        # Move flat params to cam_params if they exist
        if "params" in preset and preset["params"]:
            preset["cam_params"] = preset.pop("params")
    
    # Ensure kind field exists
    if "kind" not in preset:
        preset["kind"] = "cam"
    
    return preset


def load_all_presets() -> List[Dict[str, Any]]:
    """
    Load all presets from unified storage.
    
    Returns:
        List of preset dictionaries with unified schema.
        Empty list if file doesn't exist or is malformed.
    """
    if not PRESETS_PATH.exists():
        return []
    
    try:
        data = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        
        # Migrate legacy presets on load
        migrated = [_migrate_legacy_preset(p) for p in data]
        return migrated
    except (OSError, json.JSONDecodeError, ValueError):  # WP-1: narrowed from except Exception
        return []


def save_all_presets(presets: List[Dict[str, Any]]) -> None:
    """
    Save all presets to unified storage.
    
    Args:
        presets: List of preset dictionaries
    """
    _ensure_dir()
    PRESETS_PATH.write_text(
        json.dumps(presets, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def list_presets(kind: Optional[PresetKind] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List presets with optional filtering.
    
    Args:
        kind: Filter by preset kind (cam, export, neck, combo)
        tag: Filter by tag (matches if tag in preset.tags)
    
    Returns:
        Filtered list of presets
    """
    presets = load_all_presets()
    
    if kind:
        presets = [p for p in presets if p.get("kind") == kind]
    
    if tag:
        presets = [p for p in presets if tag in p.get("tags", [])]
    
    return presets


def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single preset by ID.
    
    Args:
        preset_id: Preset UUID
    
    Returns:
        Preset dictionary or None if not found
    """
    presets = load_all_presets()
    for preset in presets:
        if str(preset.get("id")) == str(preset_id):
            return preset
    return None


def insert_preset(preset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert a new preset.
    
    Args:
        preset: Preset dictionary (must have 'id' field)
    
    Returns:
        The inserted preset
    """
    presets = load_all_presets()
    presets.append(preset)
    save_all_presets(presets)
    return preset


def update_preset(preset_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update an existing preset.
    
    Args:
        preset_id: Preset UUID
        patch: Fields to update (merges with existing)
    
    Returns:
        Updated preset or None if not found
    """
    presets = load_all_presets()
    for idx, preset in enumerate(presets):
        if str(preset.get("id")) == str(preset_id):
            # Merge patch into preset
            updated = {**preset, **patch}
            presets[idx] = updated
            save_all_presets(presets)
            return updated
    return None


def delete_preset(preset_id: str) -> bool:
    """
    Delete a preset by ID.
    
    Args:
        preset_id: Preset UUID
    
    Returns:
        True if deleted, False if not found
    """
    presets = load_all_presets()
    initial_count = len(presets)
    presets = [p for p in presets if str(p.get("id")) != str(preset_id)]
    
    if len(presets) < initial_count:
        save_all_presets(presets)
        return True
    return False
