"""
SVG Generation Style Presets

Defines style presets optimized for vectorization and lutherie patterns.
These prompt suffixes produce images that vectorize well to SVG.
"""
from __future__ import annotations

from typing import Dict


# Style presets with prompt suffixes optimized for vectorization
SVG_STYLE_PRESETS: Dict[str, Dict[str, str]] = {
    "line_art": {
        "name": "Line Art",
        "description": "Clean black and white line drawing, ideal for CNC patterns",
        "prompt_suffix": (
            "black and white line art, clean vector style, "
            "high contrast, no gradients, no shading, "
            "simple clean lines, isolated on white background"
        ),
    },
    "woodcut": {
        "name": "Woodcut",
        "description": "Traditional woodcut/linocut style with bold lines",
        "prompt_suffix": (
            "woodcut style, bold black lines, high contrast, "
            "no gradients, traditional engraving aesthetic, "
            "clean edges, white background"
        ),
    },
    "geometric": {
        "name": "Geometric",
        "description": "Geometric pattern with precise shapes",
        "prompt_suffix": (
            "geometric pattern, precise shapes, symmetrical, "
            "black and white, vector art style, "
            "clean lines, mathematical precision"
        ),
    },
    "celtic": {
        "name": "Celtic Knot",
        "description": "Celtic knot and interlace patterns",
        "prompt_suffix": (
            "celtic knot pattern, interlace design, "
            "black and white line art, continuous lines, "
            "traditional celtic style, symmetrical"
        ),
    },
    "rosette": {
        "name": "Rosette Pattern",
        "description": "Guitar soundhole rosette design",
        "prompt_suffix": (
            "circular rosette pattern, concentric rings, "
            "guitar soundhole decoration, black and white, "
            "intricate repeating pattern, vector style"
        ),
    },
    "inlay": {
        "name": "Inlay Design",
        "description": "Guitar inlay pattern (headstock, fretboard)",
        "prompt_suffix": (
            "guitar inlay design, decorative pattern, "
            "black and white silhouette, clean edges, "
            "suitable for CNC routing, no gradients"
        ),
    },
    "marquetry": {
        "name": "Marquetry",
        "description": "Wood marquetry/veneer pattern",
        "prompt_suffix": (
            "marquetry pattern, wood veneer design, "
            "interlocking shapes, geometric, "
            "black and white, clean vector lines"
        ),
    },
    "herringbone": {
        "name": "Herringbone",
        "description": "Classic herringbone binding pattern",
        "prompt_suffix": (
            "herringbone pattern, repeating chevron, "
            "black and white, precise lines, "
            "traditional guitar binding style"
        ),
    },
    "purfling": {
        "name": "Purfling",
        "description": "Decorative border/purfling pattern",
        "prompt_suffix": (
            "decorative border pattern, purfling design, "
            "linear repeating pattern, black and white, "
            "thin precise lines, guitar trim style"
        ),
    },
    "mosaic": {
        "name": "Mosaic",
        "description": "Mosaic tile pattern",
        "prompt_suffix": (
            "mosaic pattern, small repeating tiles, "
            "black and white, geometric shapes, "
            "traditional mosaic style, vector art"
        ),
    },
    "silhouette": {
        "name": "Silhouette",
        "description": "Simple solid silhouette",
        "prompt_suffix": (
            "solid black silhouette, simple shape, "
            "no details inside, clean outline, "
            "white background, high contrast"
        ),
    },
    "technical": {
        "name": "Technical Drawing",
        "description": "Engineering/technical drawing style",
        "prompt_suffix": (
            "technical drawing style, blueprint aesthetic, "
            "precise lines, annotations style, "
            "black on white, engineering diagram"
        ),
    },
}


def get_style_prompt_suffix(style: str) -> str:
    """
    Get the prompt suffix for a style preset.

    Args:
        style: Style name (e.g., "line_art", "rosette")

    Returns:
        Prompt suffix string to append to user prompt
    """
    style_lower = style.lower().replace(" ", "_").replace("-", "_")

    if style_lower in SVG_STYLE_PRESETS:
        return SVG_STYLE_PRESETS[style_lower]["prompt_suffix"]

    # Default to line_art if style not found
    return SVG_STYLE_PRESETS["line_art"]["prompt_suffix"]


def list_styles() -> list[dict]:
    """
    List all available style presets.

    Returns:
        List of style info dicts with name, description
    """
    return [
        {
            "id": key,
            "name": preset["name"],
            "description": preset["description"],
        }
        for key, preset in SVG_STYLE_PRESETS.items()
    ]
