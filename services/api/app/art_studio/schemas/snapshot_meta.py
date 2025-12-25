"""
Pydantic models for snapshot metadata operations.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SnapshotMetaPatch(BaseModel):
    """Partial update for snapshot metadata (name, notes, tags)."""

    name: Optional[str] = Field(None, min_length=1, max_length=128)
    notes: Optional[str] = Field(None, max_length=4096)
    tags: Optional[List[str]] = Field(None, max_items=32)


class BaselineToggleRequest(BaseModel):
    """Request body for POST /snapshots/{id}/baseline."""

    baseline: bool = Field(..., description="True to mark as baseline, False to clear.")
