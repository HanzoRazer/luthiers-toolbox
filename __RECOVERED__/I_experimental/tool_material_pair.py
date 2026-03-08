from __future__ import annotations

from pydantic import BaseModel


class ToolMaterialPair(BaseModel):
    """Simple lookup tying a tool to a preferred preset."""

    tool_id: str
    material: str
    preset_id: str
    notes: str | None = None
