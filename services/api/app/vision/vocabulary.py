"""app.vision.vocabulary

Canonical vocabulary for guitar image prompting.
Pure data/helpers for guitar image prompting vocabulary (no IO).
"""

from __future__ import annotations

from typing import Dict, List

# Minimal vocabulary surface for UI dropdowns.
# Expand safely over time; keep keys stable.

BODY_SHAPES: List[str] = [
    "dreadnought",
    "grand auditorium",
    "parlor",
    "jumbo",
    "concert",
    "les paul",
    "stratocaster",
    "telecaster",
    "sg",
    "jazzmaster",
    "semi-hollow",
    "archtop",
    "classical",
    "bass",
]

FINISHES: List[str] = [
    "natural",
    "sunburst",
    "black",
    "white",
    "solid color",
    "transparent stain",
    "nitrocellulose lacquer",
    "french polish",
]

WOODS: List[str] = [
    "spruce",
    "cedar",
    "mahogany",
    "rosewood",
    "maple",
    "walnut",
    "koa",
    "ebony",
]

HARDWARE: List[str] = [
    "vintage tuners",
    "locking tuners",
    "hardtail bridge",
    "tremolo bridge",
    "humbuckers",
    "single coils",
    "p90 pickups",
]

INLAYS: List[str] = [
    "dots",
    "blocks",
    "trapezoids",
    "custom inlay",
]

PHOTOGRAPHY_STYLES: List[str] = [
    "product",
    "dramatic",
    "studio",
    "lifestyle",
    "vintage",
    "cinematic",
    "workshop",
]

def as_dict() -> Dict[str, List[str]]:
    return {
        "body_shapes": BODY_SHAPES,
        "finishes": FINISHES,
        "woods": WOODS,
        "hardware": HARDWARE,
        "inlays": INLAYS,
        "photography_styles": PHOTOGRAPHY_STYLES,
    }
