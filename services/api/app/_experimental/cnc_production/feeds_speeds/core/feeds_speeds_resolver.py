from __future__ import annotations

from typing import Any, Mapping

from app.cnc_production.feeds_speeds.core.chipload_calc import calc_chipload_mm
from app.cnc_production.feeds_speeds.core.deflection_model import estimate_deflection_mm
from app.cnc_production.feeds_speeds.core.heat_model import estimate_heat_rating
from app.cnc_production.feeds_speeds.core.presets_db import PRESETS_DB

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


def resolve_feeds_speeds(tool: Any, material: str, mode: str = "roughing", machine_profile: str = "default") -> dict[str, Any]:
    """Return RPM/feed guidance for the supplied tool/material/machine_profile combination."""

    tool_id = _tool_attr(tool, "id") or (tool if isinstance(tool, str) else None)
    if not tool_id:
        raise ValueError("Tool identifier missing for feeds/speeds resolution")

    key = f"{tool_id}:{material}:{mode}:{machine_profile}"
    preset = PRESETS_DB.get(key)
    if not preset:
        raise ValueError(f"No preset defined for {tool_id} / {material} / {mode} / {machine_profile}")

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
