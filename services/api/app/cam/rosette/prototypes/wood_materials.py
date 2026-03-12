"""
Shared wood material library for rosette prototypes.

Superset of all species across JSX prototypes. Each entry carries visual
properties used by the grain renderer and the interactive viewers.

Usage:
    from wood_materials import WOODS, wood_by_id, hex_to_rgb
"""

from __future__ import annotations

WOODS: list[dict] = [
    {"id": "ebony",    "name": "Ebony",           "base": "#1a1008", "grain": "#0d0804", "accent": "#221408",  "hi": "#2a1c10", "tight": True,  "figure": False, "iridescent": False},
    {"id": "maple",    "name": "Maple",           "base": "#f2e8c8", "grain": "#d8c898", "accent": "#f8f0d8",  "hi": "#fff8e8", "tight": True,  "figure": False, "iridescent": False},
    {"id": "maple_q",  "name": "Quilted Maple",   "base": "#f0d890", "grain": "#c8a840", "accent": "#f8e8a0",  "hi": "#f8e8a0", "tight": False, "figure": True,  "iridescent": False},
    {"id": "rosewood", "name": "Rosewood",        "base": "#4a1e10", "grain": "#3a1408", "accent": "#5a2818",  "hi": "#6a3020", "tight": False, "figure": False, "iridescent": False},
    {"id": "spruce",   "name": "Spruce",          "base": "#e8d8a0", "grain": "#c0a850", "accent": "#f0e0b0",  "hi": "#f8f0c0", "tight": True,  "figure": False, "iridescent": False},
    {"id": "cedar",    "name": "Cedar",           "base": "#c07040", "grain": "#a05028", "accent": "#d08050",  "hi": "#d89060", "tight": False, "figure": False, "iridescent": False},
    {"id": "mahogany", "name": "Mahogany",        "base": "#7a3018", "grain": "#5a1e08", "accent": "#8a4020",  "hi": "#9a5030", "tight": False, "figure": False, "iridescent": False},
    {"id": "koa",      "name": "Koa",             "base": "#b86820", "grain": "#8a4810", "accent": "#d08030",  "hi": "#e8a848", "tight": False, "figure": True,  "iridescent": False},
    {"id": "ovangkol", "name": "Ovangkol",        "base": "#a07830", "grain": "#706020", "accent": "#b88840",  "hi": "#c89838", "tight": True,  "figure": True,  "iridescent": False},
    {"id": "walnut",   "name": "Walnut",          "base": "#5c3818", "grain": "#3c2008", "accent": "#6c4828",  "hi": "#7c5838", "tight": False, "figure": False, "iridescent": False},
    {"id": "mop",      "name": "Mother-of-Pearl", "base": "#e8f0f8", "grain": "#c0d8f0", "accent": "#f0f8ff",  "hi": "#f0f8ff", "tight": False, "figure": True,  "iridescent": True},
    {"id": "abalone",  "name": "Abalone",         "base": "#609070", "grain": "#408060", "accent": "#80b090",  "hi": "#80b898", "tight": False, "figure": True,  "iridescent": True},
    {"id": "bone",     "name": "Bone",            "base": "#f0ead0", "grain": "#d0c898", "accent": "#f8f4e0",  "hi": "#fff8f0", "tight": True,  "figure": False, "iridescent": False},
    {"id": "air",      "name": "Air / Open",      "base": "#080604", "grain": "#060402", "accent": "#0a0806",  "hi": "#0a0806", "tight": False, "figure": False, "iridescent": False},
]

_WOOD_INDEX: dict[str, dict] = {w["id"]: w for w in WOODS}


def wood_by_id(wood_id: str) -> dict:
    """Look up a wood by its ID. Falls back to ebony."""
    return _WOOD_INDEX.get(wood_id, _WOOD_INDEX["ebony"])


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    """Convert '#rrggbb' to (r, g, b) ints."""
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def hex_to_rgb_float(h: str) -> tuple[float, float, float]:
    """Convert '#rrggbb' to (r, g, b) floats in [0, 1]."""
    r, g, b = hex_to_rgb(h)
    return r / 255.0, g / 255.0, b / 255.0


def prng(seed: int):
    """Deterministic PRNG matching the JSX s=(s*9301+49297)%233280 pattern."""
    s = seed * 9301 + 49297

    def _next():
        nonlocal s
        s = (s * 9301 + 49297) % 233280
        return s / 233280.0

    return _next
