"""Feeds and speeds calculator with chipload, heat, and deflection analysis."""
from __future__ import annotations

from typing import Dict, Any, Mapping

from .chipload_calc import calc_chipload_mm
from .heat_model import estimate_heat_rating
from .deflection_model import estimate_deflection_mm
from .presets_db import PRESETS_DB, get_preset
from .schemas import SpeedFeedPreset

_DEFAULT_TOOL = {
    "flutes": 2,
    "diameter_mm": 6.35,
    "stickout_mm": 25.0,
}

_FALLBACK_TOOLS = {
    "upcut_1_4": {"flutes": 2, "diameter_mm": 6.35, "stickout_mm": 25.0},
    "downcut_1_4": {"flutes": 2, "diameter_mm": 6.35, "stickout_mm": 25.0},
    "ballnose_1_8": {"flutes": 2, "diameter_mm": 3.175, "stickout_mm": 19.0},
    "surfacing_2in": {"flutes": 3, "diameter_mm": 50.8, "stickout_mm": 20.0},
    "slitting_3in": {"flutes": 2, "diameter_mm": 76.2, "stickout_mm": 15.0},
}


def _tool_attr(tool: Any, attr: str) -> Any:
    if tool is None:
        return None
    if isinstance(tool, Mapping):
        return tool.get(attr)
    return getattr(tool, attr, None)


def _tool_geometry(tool_id: str, tool: Any | None = None) -> dict[str, float]:
    base = dict(_DEFAULT_TOOL)
    base.update(_FALLBACK_TOOLS.get(tool_id, {}))

    for field in ("flutes", "diameter_mm", "stickout_mm"):
        value = _tool_attr(tool, field)
        if value is not None:
            base[field] = value

    return base


def resolve_feeds_speeds(
    tool: Any,
    material: str,
    mode: str = "roughing",
    machine_profile: str = "default"
) -> Dict[str, Any]:
    """Return RPM/feed guidance for the supplied tool/material/machine_profile combination."""

    tool_id = _tool_attr(tool, "id") or (tool if isinstance(tool, str) else None)
    if not tool_id:
        raise ValueError("Tool identifier missing for feeds/speeds resolution")

    preset = get_preset(tool_id, material, mode)
    if not preset:
        raise ValueError(f"No preset defined for {tool_id} / {material} / {mode}")

    geom = _tool_geometry(tool_id, tool)
    chipload = calc_chipload_mm(preset.feed_mm_min, preset.rpm, int(geom["flutes"]))
    heat = estimate_heat_rating(preset.rpm, preset.feed_mm_min, preset.stepdown_mm)
    deflection = estimate_deflection_mm(
        geom["diameter_mm"],
        geom["stickout_mm"],
        force_n=12.0,
    )

    return {
        "tool_id": tool_id,
        "material": material,
        "mode": mode,
        "machine_profile": machine_profile,
        "rpm": preset.rpm,
        "feed_mm_min": preset.feed_mm_min,
        "stepdown_mm": preset.stepdown_mm,
        "stepover_mm": preset.stepover_mm,
        "strategy": preset.strategy,
        "finish_quality": preset.finish_quality,
        "chipload_mm": chipload,
        "heat_rating": heat,
        "deflection_mm": deflection,
        "max_chipload_mm": preset.max_chipload_mm,
        "recommended_chipload_mm": preset.recommended_chipload_mm,
    }


def calculate_feed_plan(tool: Dict[str, Any], material: str, strategy: str) -> Dict[str, Any]:
    """
    Calculate feed plan for a tool/material/strategy combination.

    This is the main entry point for CAM operations.
    Falls back gracefully if no preset exists.
    """
    tool_id = tool.get("id")

    # Map strategy to mode
    mode = "finishing" if strategy in ("parallel", "scallop", "contour") else "roughing"

    try:
        result = resolve_feeds_speeds(tool, material, mode=mode)
        return {
            "tool_id": tool_id,
            "material": material,
            "strategy": strategy,
            "feed_xy": result["feed_mm_min"],
            "feed_z": result["feed_mm_min"] * 0.5,  # Z feed is typically 50% of XY
            "rpm": result["rpm"],
            "stepdown_mm": result["stepdown_mm"],
            "stepover_mm": result["stepover_mm"],
            "chipload_mm": result["chipload_mm"],
            "heat_rating": result["heat_rating"],
            "deflection_mm": result["deflection_mm"],
            "notes": f"Preset: {tool_id}/{material}/{mode}",
        }
    except ValueError:
        # No preset found - calculate from tool geometry
        flutes = tool.get("flutes", 2)
        diameter = tool.get("diameter_mm", 6.35)

        # Conservative defaults based on tool size
        rpm = int(min(18000, max(8000, 300000 / diameter)))  # SFM-based estimate
        chipload = 0.03 if diameter >= 6 else 0.015  # mm per tooth
        feed = rpm * flutes * chipload

        return {
            "tool_id": tool_id,
            "material": material,
            "strategy": strategy,
            "feed_xy": feed,
            "feed_z": feed * 0.5,
            "rpm": rpm,
            "stepdown_mm": diameter * 0.5,
            "stepover_mm": diameter * 0.4,
            "chipload_mm": chipload,
            "heat_rating": "WARM",
            "deflection_mm": 0.0,
            "notes": "Calculated from tool geometry (no preset available)",
        }
