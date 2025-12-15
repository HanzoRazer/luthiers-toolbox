# services/api/app/data/__init__.py
"""
Data layer for ToolBox API.

This package holds structured data assets such as:

- tool_library.json   : tool & material parameters
- machines.json       : CNC machine profiles
- posts/              : Post-processor configurations
- presets.json        : Pipeline presets

Provides loader and lookup helpers for tools and materials.
"""

from .tool_library import (
    load_tool_library,
    get_tool_profile,
    get_material_profile,
    ToolProfile,
    MaterialProfile,
)

__all__ = [
    "load_tool_library",
    "get_tool_profile",
    "get_material_profile",
    "ToolProfile",
    "MaterialProfile",
]
