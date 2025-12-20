"""
Workflow Sessions Schemas

Pydantic models for workflow session CRUD operations.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowSessionCreateRequest(BaseModel):
    """
    Minimal create contract.
    We keep payload flexible; store will place fields where columns exist.
    """
    user_id: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    workflow_type: Optional[str] = None
    current_step: Optional[str] = "draft"
    machine_id: Optional[str] = None
    material_id: Optional[str] = None
    tool_id: Optional[str] = None
    context_json: Optional[Dict[str, Any]] = None
    state_data_json: Optional[Dict[str, Any]] = None


class WorkflowSessionPatchRequest(BaseModel):
    """
    Minimal patch contract.
    """
    status: Optional[str] = None
    current_step: Optional[str] = None
    workflow_type: Optional[str] = None
    machine_id: Optional[str] = None
    material_id: Optional[str] = None
    tool_id: Optional[str] = None
    context_json: Optional[Dict[str, Any]] = None
    state_data_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class WorkflowSessionResponse(BaseModel):
    """
    Normalized response. Also returns raw row for forward-compat.
    """
    session_id: str
    created_at_utc: Optional[str] = None
    updated_at_utc: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[str] = None
    workflow_type: Optional[str] = None
    current_step: Optional[str] = None
    machine_id: Optional[str] = None
    material_id: Optional[str] = None
    tool_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    state_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

    # forward-compatible escape hatch (includes any extra DB columns)
    raw: Dict[str, Any] = Field(default_factory=dict)


class WorkflowSessionListResponse(BaseModel):
    items: List[WorkflowSessionResponse]
    limit: int
    offset: int
    total: Optional[int] = None  # optional because COUNT(*) can be expensive
