"""app.vision.prompt_engine

Canonical prompt engineering for guitar image generation.
Moved from app._experimental.ai_graphics.prompt_engine (trimmed for Release A.1).

Governance note:
- This module may *expand user input into descriptive photography language*.
- It must not score, rank, or recommend design choices.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .vocabulary import PHOTOGRAPHY_STYLES

@dataclass(frozen=True)
class PromptPreview:
    raw_prompt: str
    engineered_prompt: str
    photography_style: Optional[str] = None

def _normalize_style(style: Optional[str]) -> Optional[str]:
    if not style:
        return None
    s = style.strip().lower()
    return s if s in PHOTOGRAPHY_STYLES else None

def engineer_guitar_prompt(prompt: str, style: Optional[str] = None) -> PromptPreview:
    """Expand a casual prompt into a more explicit photography prompt.

    This is intentionally conservative: it adds *rendering context* (lighting, background),
    not design recommendations.
    """
    raw = (prompt or "").strip()
    raw = re.sub(r"\s+", " ", raw)

    st = _normalize_style(style)

    photo_clause = ""
    if st == "product":
        photo_clause = "product photography, clean studio lighting, neutral background"
    elif st == "dramatic":
        photo_clause = "dramatic lighting, high contrast, dark backdrop"
    elif st == "studio":
        photo_clause = "studio lighting, soft shadows, high detail"
    elif st == "lifestyle":
        photo_clause = "lifestyle scene, natural light, shallow depth of field"
    elif st == "vintage":
        photo_clause = "vintage aesthetic, warm tones, subtle film grain"
    elif st == "cinematic":
        photo_clause = "cinematic lighting, shallow depth of field, moody atmosphere"
    elif st == "workshop":
        photo_clause = "workshop environment, practical lighting, realistic textures"

    engineered = raw
    if photo_clause:
        engineered = f"{raw}. {photo_clause}."

    # Universal quality clause (still non-interpretive)
    engineered = f"{engineered} ultra high detail, accurate guitar geometry, no text, no watermark"

    return PromptPreview(raw_prompt=raw, engineered_prompt=engineered, photography_style=st)
