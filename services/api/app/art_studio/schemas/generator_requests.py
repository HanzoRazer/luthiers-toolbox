"""
Generator Request/Response Schemas - Bundle 31.0.2

Defines the data models for the parametric generator system.
"""
from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict

from .rosette_params import RosetteParamSpec


class GeneratorDescriptor(BaseModel):
    """
    Describes an available generator.
    """
    model_config = ConfigDict(extra="forbid")

    generator_key: str = Field(
        ...,
        description="Unique key, e.g., 'basic_rings@1', 'mosaic_band@1'"
    )
    name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Generator description")
    param_hints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Hints about expected parameters and their types/defaults"
    )


class GeneratorListResponse(BaseModel):
    """Response listing all available generators."""
    model_config = ConfigDict(extra="forbid")

    generators: List[GeneratorDescriptor]


class GeneratorGenerateRequest(BaseModel):
    """Request to generate a RosetteParamSpec from a generator."""
    model_config = ConfigDict(extra="forbid")

    outer_diameter_mm: float = Field(..., gt=0)
    inner_diameter_mm: float = Field(..., gt=0)
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Generator-specific parameters"
    )


class GeneratorGenerateResponse(BaseModel):
    """Response containing the generated RosetteParamSpec."""
    model_config = ConfigDict(extra="forbid")

    spec: RosetteParamSpec
    generator_key: str
    warnings: List[str] = Field(default_factory=list)
