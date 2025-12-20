"""
Workflow Sessions - Pure SQLite Persistence Layer

Minimal SQLite-backed store for workflow sessions that:
- Uses the workflow_sessions table from migrations
- Schema-tolerant: introspects columns, writes only to columns that exist
- Complements (not replaces) the existing SQLAlchemy stores

Exports:
    WorkflowSessionStore - SQLite-backed CRUD
    WorkflowSessionCreateRequest, WorkflowSessionPatchRequest - Pydantic schemas
    WorkflowSessionResponse, WorkflowSessionListResponse - Response models
    workflow_sessions_router - FastAPI router
"""
from .schemas import (
    WorkflowSessionCreateRequest,
    WorkflowSessionPatchRequest,
    WorkflowSessionResponse,
    WorkflowSessionListResponse,
)
from .store import WorkflowSessionStore
from .routes import router as workflow_sessions_router

__all__ = [
    "WorkflowSessionCreateRequest",
    "WorkflowSessionPatchRequest",
    "WorkflowSessionResponse",
    "WorkflowSessionListResponse",
    "WorkflowSessionStore",
    "workflow_sessions_router",
]
