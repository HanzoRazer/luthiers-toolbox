"""
RMOS AI Search Schemas
Pydantic models for AI constraint-first search API requests and responses.

Note: This module complements schemas_logs_ai.py which provides read-only
log view schemas. This module provides the request/response contracts.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


# ======================
# Enums
# ======================

class SearchStatus(str, Enum):
    """Status of an AI search run."""
    SUCCESS = "success"           # Found GREEN result
    BEST_EFFORT = "best_effort"   # No GREEN, returning best YELLOW
    EXHAUSTED = "exhausted"       # Budget exhausted, no acceptable result
    TIMEOUT = "timeout"           # Time limit reached
    ERROR = "error"               # Unrecoverable error


class WorkflowMode(str, Enum):
    """Workflow mode for AI search."""
    CONSTRAINT_FIRST = "constraint_first"
    AI_ASSISTED = "ai_assisted"
    DESIGN_FIRST = "design_first"


# ======================
# Nested Request Models (matches test validation structure)
# ======================

class SearchContext(BaseModel):
    """Manufacturing context for the search."""
    tool_id: Optional[str] = Field(None, description="Tool database ID")
    material_id: Optional[str] = Field(None, description="Material database ID")
    machine_profile_id: Optional[str] = Field(None, description="Machine profile ID")


class SearchBudget(BaseModel):
    """Budget constraints for the search loop."""
    max_attempts: int = Field(50, ge=1, le=200, description="Max candidate attempts (capped at 200)")
    time_limit_seconds: float = Field(30.0, ge=1.0, le=60.0, description="Search time limit (capped at 60s)")
    min_feasibility_score: float = Field(80.0, ge=0, le=100, description="Minimum acceptable score")
    stop_on_first_green: bool = Field(True, description="Stop immediately on GREEN result")
    deterministic: bool = Field(True, description="Use deterministic generation")


# ======================
# Request Model
# ======================

class AiSearchRequest(BaseModel):
    """
    Request payload for POST /api/rmos/ai/constraint-search
    
    Supports both nested structure (recommended) and flat structure (legacy).
    """
    # Workflow mode
    workflow_mode: WorkflowMode = Field(
        WorkflowMode.CONSTRAINT_FIRST,
        description="Search workflow mode"
    )
    
    # Nested structure (recommended)
    context: Optional[SearchContext] = Field(
        None,
        description="Manufacturing context (nested)"
    )
    search_budget: Optional[SearchBudget] = Field(
        None,
        description="Search budget constraints (nested)"
    )
    
    # Optional seed design
    seed_design: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional seed design to start from (RosetteParamSpec dict)"
    )
    
    # Flat structure (legacy fallback)
    tool_id: Optional[str] = Field(None, description="[Legacy] Tool database ID")
    material_id: Optional[str] = Field(None, description="[Legacy] Material database ID")
    machine_profile_id: Optional[str] = Field(None, description="[Legacy] Machine profile ID")
    max_attempts: Optional[int] = Field(None, description="[Legacy] Max attempts")
    time_limit_seconds: Optional[float] = Field(None, description="[Legacy] Time limit")
    
    # Response options
    include_attempt_history: bool = Field(False, description="Include attempt details in response")
    profile_id: Optional[str] = Field(None, description="Constraint profile ID to apply")
    
    def get_effective_context(self) -> SearchContext:
        """Resolve context from nested or flat fields."""
        if self.context:
            return self.context
        return SearchContext(
            tool_id=self.tool_id,
            material_id=self.material_id,
            machine_profile_id=self.machine_profile_id,
        )
    
    def get_effective_budget(self) -> SearchBudget:
        """Resolve budget from nested or flat fields."""
        if self.search_budget:
            return self.search_budget
        return SearchBudget(
            max_attempts=self.max_attempts or 50,
            time_limit_seconds=self.time_limit_seconds or 30.0,
        )


# ======================
# Response Models
# ======================

class SearchAttemptSummary(BaseModel):
    """Lightweight attempt record for response (not for logging)."""
    attempt_index: int = Field(..., description="1-based attempt number")
    score: float = Field(..., description="Feasibility score 0-100")
    risk_bucket: str = Field(..., description="GREEN/YELLOW/RED")
    is_acceptable: bool = Field(..., description="Met minimum score threshold")
    elapsed_ms: float = Field(..., description="Time for this attempt in ms")


class AiSearchResponse(BaseModel):
    """
    Response payload from POST /api/rmos/ai/constraint-search
    """
    # Result status
    status: SearchStatus = Field(..., description="Search outcome status")
    message: str = Field(..., description="Human-readable result summary")
    
    # Best result found (if any)
    best_design: Optional[Dict[str, Any]] = Field(
        None,
        description="Best candidate design found (RosetteParamSpec dict)"
    )
    best_score: Optional[float] = Field(None, description="Score of best design")
    best_risk_bucket: Optional[str] = Field(None, description="Risk bucket of best design")
    best_warnings: List[str] = Field(default_factory=list, description="Warnings for best design")
    
    # Search statistics
    total_attempts: int = Field(..., description="Total attempts made")
    unique_candidates: int = Field(..., description="Unique candidates evaluated")
    green_count: int = Field(0, description="Number of GREEN results found")
    yellow_count: int = Field(0, description="Number of YELLOW results found")
    red_count: int = Field(0, description="Number of RED results found")
    
    # Timing
    elapsed_seconds: float = Field(..., description="Total search time")
    started_at: datetime = Field(..., description="Search start timestamp")
    completed_at: datetime = Field(..., description="Search completion timestamp")
    
    # Attempt history (optional, based on request flag)
    attempts: List[SearchAttemptSummary] = Field(
        default_factory=list,
        description="Attempt summaries (if requested)"
    )
    
    # Run metadata
    run_id: str = Field(..., description="Unique run identifier for logging")
    workflow_mode: str = Field(..., description="Workflow mode used")
    constraint_profile_applied: Optional[str] = Field(
        None,
        description="ID of constraint profile used (if any)"
    )


class AiSearchSummary(BaseModel):
    """
    Lightweight summary for quick-check endpoint.
    """
    run_id: str
    status: SearchStatus
    best_score: Optional[float]
    best_risk_bucket: Optional[str]
    total_attempts: int
    elapsed_seconds: float
    started_at: datetime
    workflow_mode: str
    profile_id: Optional[str] = None
