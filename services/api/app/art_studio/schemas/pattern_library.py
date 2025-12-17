"""
Pattern Library Schemas - Bundle 31.0.1

Defines the data models for storing and managing rosette patterns
in the Art Studio pattern library.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PatternRecord(BaseModel):
    """
    A saved pattern in the library.

    Patterns store generator_key + params, which can be used to
    regenerate a RosetteParamSpec at any time.
    """
    model_config = ConfigDict(extra="forbid")

    pattern_id: str = Field(..., min_length=6, max_length=80)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    tags: List[str] = Field(default_factory=list)
    generator_key: str = Field(
        ...,
        description="Generator key, e.g., 'basic_rings@1', 'mosaic_band@1'"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Generator-specific parameters"
    )
    created_at: datetime
    updated_at: datetime


class PatternSummary(BaseModel):
    """Lightweight pattern summary for list views."""
    model_config = ConfigDict(extra="forbid")

    pattern_id: str
    name: str
    tags: List[str]
    generator_key: str
    updated_at: datetime


class PatternListResponse(BaseModel):
    """Response for pattern list endpoint."""
    model_config = ConfigDict(extra="forbid")

    items: List[PatternSummary]


class PatternCreateRequest(BaseModel):
    """Request to create a new pattern."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    tags: List[str] = Field(default_factory=list)
    generator_key: str = Field(
        ...,
        description="Generator key, e.g., 'basic_rings@1'"
    )
    params: Dict[str, Any] = Field(default_factory=dict)


class PatternUpdateRequest(BaseModel):
    """
    Request to update an existing pattern.
    All fields are optional - only provided fields are updated.
    """
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    tags: Optional[List[str]] = None
    generator_key: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
