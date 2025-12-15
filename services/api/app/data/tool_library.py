# services/api/app/data/tool_library.py

"""
Tool Library Loader & Lookup Helpers

Provides access to tool and material profiles from tool_library.json.

This module adapts the existing tool_library.json format (which uses arrays
for tools) to the Wave 6 profile interface used by the Saw Bridge.

Features:
- Lazy-loaded singleton library
- Tool profile lookup by ID
- Material profile lookup by name
- Fallback defaults for missing entries
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Relative to this file
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_TOOL_LIBRARY_PATH = os.path.join(_THIS_DIR, "tool_library.json")


@dataclass
class ToolProfile:
    """
    Tool profile with parameters needed by Saw Bridge.

    Attributes:
        tool_id: Unique identifier
        name: Display name
        flutes: Number of cutting flutes
        chipload_min_mm: Minimum recommended chipload
        chipload_max_mm: Maximum recommended chipload
        diameter_mm: Tool diameter in mm
        tool_type: Tool type (flat, ball, v, drill, etc.)
    """

    tool_id: str
    name: str
    flutes: int
    chipload_min_mm: float
    chipload_max_mm: float
    diameter_mm: float = 0.0
    tool_type: str = "unknown"


@dataclass
class MaterialProfile:
    """
    Material profile with heat sensitivity info.

    Attributes:
        material_id: Unique identifier
        name: Display name
        heat_sensitivity: "low", "medium", or "high"
        hardness: Material hardness category
        density_kg_m3: Density in kg/m³
    """

    material_id: str
    name: str
    heat_sensitivity: str
    hardness: str = "medium"
    density_kg_m3: float = 0.0


class ToolLibrary:
    """
    In-memory tool library loaded from JSON.

    Provides lookup methods for tools and materials.
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._materials: Dict[str, Dict[str, Any]] = data.get("materials", {})

        # Convert tools array to dict keyed by id
        tools_list: List[Dict[str, Any]] = data.get("tools", [])
        for tool in tools_list:
            tool_id = tool.get("id", "")
            if tool_id:
                self._tools[tool_id] = tool

    def get_tool_profile(self, tool_id: str) -> Optional[ToolProfile]:
        """
        Get tool profile by ID.

        Args:
            tool_id: Tool identifier (e.g., "flat_6.0", "vbit_60")

        Returns:
            ToolProfile or None if not found
        """
        raw = self._tools.get(tool_id)
        if not raw:
            return None

        flutes = int(raw.get("flutes", 2))
        diameter = float(raw.get("diameter_mm", 6.0))
        tool_type = raw.get("type", "unknown")

        # Derive chipload band from defaults (feed / (rpm * flutes))
        # This is a heuristic based on the tool's default settings
        default_rpm = float(raw.get("default_rpm", 16000))
        default_fxy = float(raw.get("default_fxy", 1200))

        if default_rpm > 0 and flutes > 0:
            ideal_chipload = default_fxy / (default_rpm * flutes)
            # Band is ±50% of ideal
            chip_min = ideal_chipload * 0.5
            chip_max = ideal_chipload * 1.5
        else:
            chip_min = 0.01
            chip_max = 0.04

        # Build notes as name
        name = raw.get("notes", tool_id)

        return ToolProfile(
            tool_id=tool_id,
            name=name,
            flutes=flutes,
            chipload_min_mm=chip_min,
            chipload_max_mm=chip_max,
            diameter_mm=diameter,
            tool_type=tool_type,
        )

    def get_material_profile(self, material_id: str) -> Optional[MaterialProfile]:
        """
        Get material profile by ID.

        Args:
            material_id: Material identifier (e.g., "Ebony", "Hard Maple")

        Returns:
            MaterialProfile or None if not found
        """
        raw = self._materials.get(material_id)
        if not raw:
            # Try case-insensitive lookup
            for key, val in self._materials.items():
                if key.lower() == material_id.lower():
                    raw = val
                    material_id = key
                    break

        if not raw:
            return None

        hardness = raw.get("hardness", "medium")
        density = float(raw.get("density_kg_m3", 0))

        # Derive heat sensitivity from hardness
        # Very hard/dense materials are more heat-sensitive
        hardness_lower = hardness.lower()
        if "very" in hardness_lower or "hard" in hardness_lower:
            heat_sensitivity = "high"
        elif "soft" in hardness_lower:
            heat_sensitivity = "low"
        else:
            heat_sensitivity = "medium"

        return MaterialProfile(
            material_id=material_id,
            name=raw.get("description", material_id),
            heat_sensitivity=heat_sensitivity,
            hardness=hardness,
            density_kg_m3=density,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 1 Migration: List Methods for Validator & Router
    # ─────────────────────────────────────────────────────────────────────────

    def list_tool_ids(self) -> List[str]:
        """Return list of all tool IDs in library."""
        return list(self._tools.keys())

    def list_material_ids(self) -> List[str]:
        """Return list of all material IDs in library."""
        return list(self._materials.keys())

    def get_tool(self, tool_id: str) -> Optional[ToolProfile]:
        """Alias for get_tool_profile for consistency."""
        return self.get_tool_profile(tool_id)

    def get_material(self, material_id: str) -> Optional[MaterialProfile]:
        """Alias for get_material_profile for consistency."""
        return self.get_material_profile(material_id)


# Singleton-ish lazy loaded library
_cached_library: Optional[ToolLibrary] = None


def load_tool_library(path: str = _DEFAULT_TOOL_LIBRARY_PATH) -> ToolLibrary:
    """
    Load and cache the tool library from JSON.

    Args:
        path: Path to tool_library.json

    Returns:
        ToolLibrary instance
    """
    global _cached_library

    if _cached_library is not None:
        return _cached_library

    if not os.path.exists(path):
        # Fallback: empty library
        _cached_library = ToolLibrary({"tools": [], "materials": {}})
        return _cached_library

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _cached_library = ToolLibrary(data)
    return _cached_library


def get_tool_profile(tool_id: str) -> Optional[ToolProfile]:
    """
    Convenience function to get a tool profile.

    Args:
        tool_id: Tool identifier

    Returns:
        ToolProfile or None
    """
    lib = load_tool_library()
    return lib.get_tool_profile(tool_id)


def get_material_profile(material_id: str) -> Optional[MaterialProfile]:
    """
    Convenience function to get a material profile.

    Args:
        material_id: Material identifier

    Returns:
        MaterialProfile or None
    """
    lib = load_tool_library()
    return lib.get_material_profile(material_id)


def reset_cache() -> None:
    """Reset the cached library (useful for testing)."""
    global _cached_library
    _cached_library = None
