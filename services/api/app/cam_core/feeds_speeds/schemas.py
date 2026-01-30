"""Feeds & speeds schema definitions."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class SpeedFeedPreset(BaseModel):
    """Authoritative spindle/feed guidance for a tool/material/mode tuple."""

    id: str
    tool_id: str
    material: str

    rpm: int = Field(..., gt=500, lt=30000)
    feed_mm_min: float = Field(..., gt=10)
    stepdown_mm: float = Field(..., gt=0)
    stepover_mm: float = Field(..., gt=0)

    strategy: Literal["adaptive", "contour", "pocket", "parallel", "scallop"] = "adaptive"
    finish_quality: Literal["rough", "semi", "finish"] = "semi"
    mode: Literal["roughing", "finishing"] = "roughing"

    max_chipload_mm: float = Field(..., gt=0)
    recommended_chipload_mm: float = Field(..., gt=0)
