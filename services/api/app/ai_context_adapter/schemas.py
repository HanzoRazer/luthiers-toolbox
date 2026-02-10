# services/api/app/ai_context_adapter/schemas.py
"""Pydantic schemas for AI Context Adapter routes."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AiContextBuildRequest(BaseModel):
    """Request to build a bounded AI context bundle."""
    run_id: Optional[str] = Field(None, description="RMOS run ID")
    snapshot_id: Optional[str] = Field(None, description="Art Studio snapshot ID")
    pattern_id: Optional[str] = Field(None, description="[DEPRECATED] Alias for snapshot_id")
    compare_run_id: Optional[str] = Field(None, description="Run ID for diff_summary")
    mode: str = Field(default="run_first", description="run_first or art_studio_first")
    include: List[str] = Field(
        default_factory=list,
        description="What to include: rosette_param_spec, diff_summary, artifact_manifest, run_summary, design_intent, governance_notes",
    )
    user_notes: Optional[str] = Field(None, description="User-provided notes")


class AiContextBuildResponse(BaseModel):
    """Response with bounded AI context bundle."""
    schema_id: str = Field(default="toolbox_ai_context", description="Schema identifier")
    schema_version: str = Field(default="v1", description="Schema version")
    context_id: str = Field(..., description="Unique context bundle ID")
    summary: str = Field(..., description="Human-readable summary")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context payload")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
