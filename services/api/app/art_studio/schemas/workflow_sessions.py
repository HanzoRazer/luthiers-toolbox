# services/api/app/art_studio/schemas/workflow_sessions.py
"""
Workflow Sessions API Schemas (Bundle 32.7.6)

List/Delete endpoints for workflow session management.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class WorkflowSessionSummary(BaseModel):
    session_id: str
    mode: str
    state: str
    updated_at: datetime
    created_at: datetime

    # best-effort "risk" surfaced for quick scanning (optional)
    risk_bucket: Optional[str] = None


class ListWorkflowSessionsResponse(BaseModel):
    items: List[WorkflowSessionSummary] = Field(default_factory=list)
    next_cursor: Optional[str] = None


class DeleteWorkflowSessionResponse(BaseModel):
    ok: bool
    session_id: str
