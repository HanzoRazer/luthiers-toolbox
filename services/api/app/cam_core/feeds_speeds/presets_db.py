"""Feeds & speeds preset database loaded from JSON configs."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

from .schemas import SpeedFeedPreset

logger = logging.getLogger(__name__)

CONFIG_ROOT = Path(__file__).resolve().parent / "configs"
PRESETS_DB: Dict[str, SpeedFeedPreset] = {}


def _iter_config_files() -> list[Path]:
    if not CONFIG_ROOT.exists():
        logger.warning("Feeds/Speeds config directory missing: %s", CONFIG_ROOT)
        return []
    return sorted(CONFIG_ROOT.rglob("*.json"))


def _load_file(path: Path) -> None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to parse preset file %s: %s", path, exc)
        return

    material = raw.get("material")
    presets = raw.get("presets", {})
    if not material or not isinstance(presets, dict):
        logger.warning("Preset file %s missing material/presets", path)
        return

    for key, payload in presets.items():
        if ":" not in key:
            logger.warning("Preset key '%s' missing mode delimiter in %s", key, path)
            continue
        tool_id, mode = key.split(":", 1)
        preset_id = f"{material}:{key}"
        try:
            preset = SpeedFeedPreset(
                id=preset_id,
                tool_id=tool_id,
                material=material,
                mode=mode,
                **payload,
            )
        except Exception as exc:
            logger.warning("Invalid preset '%s' in %s: %s", key, path, exc)
            continue

        PRESETS_DB[f"{tool_id}:{material}:{mode}"] = preset


def load_presets() -> None:
    """Reload presets from disk (hot reload friendly)."""
    PRESETS_DB.clear()
    for cfg in _iter_config_files():
        _load_file(cfg)


def get_preset(tool_id: str, material: str, mode: str = "roughing") -> SpeedFeedPreset | None:
    """Get a preset by tool/material/mode, returns None if not found."""
    return PRESETS_DB.get(f"{tool_id}:{material}:{mode}")


def list_materials() -> list[str]:
    """Return list of available materials."""
    return sorted(set(p.material for p in PRESETS_DB.values()))


def list_presets_for_material(material: str) -> list[SpeedFeedPreset]:
    """Return all presets for a given material."""
    return [p for p in PRESETS_DB.values() if p.material == material]


# Load at import so routers can resolve immediately.
load_presets()
