"""
Preview Schemas - Bundle 31.0.3

Defines the data models for SVG preview rendering.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from .rosette_params import RosetteParamSpec


class RosettePreviewSvgRequest(BaseModel):
    """
    Request for SVG preview of a RosetteParamSpec.
    """
    model_config = ConfigDict(extra="forbid")

    spec: RosetteParamSpec
    size_px: int = Field(default=520, ge=200, le=2000)
    padding_px: int = Field(default=20, ge=0, le=200)


class RosettePreviewSvgResponse(BaseModel):
    """
    Response containing the rendered SVG preview.
    """
    model_config = ConfigDict(extra="forbid")

    svg: str = Field(..., description="Rendered SVG string")
    size_px: int
    view_box: str = Field(..., description="SVG viewBox string")
    warnings: List[str] = Field(default_factory=list)
    debug: Optional[Dict[str, Any]] = None
