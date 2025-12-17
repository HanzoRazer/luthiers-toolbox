"""
Workflow package for Luthier's Tool Box.

This package implements directional workflow modes for Art Studio integration:
- design_first: Full artistic freedom, then machine constraints
- constraint_first: Start with machine limits, then design
- ai_assisted: AI-driven parameter suggestions based on goals

Also provides canonical workflow state machine per governance contracts.

Part of RMOS 2.0 / Art Studio Directional Workflow 2.0.
"""

from .directional_workflow import (
    DirectionalMode,
    ModePreviewRequest,
    ModePreviewResult,
    compute_feasibility_for_mode,
    get_mode_constraints,
)

# Canonical workflow state machine (governance)
from .state_machine import (
    WorkflowMode,
    WorkflowState,
    RiskBucket,
    ActorRole,
    RunStatus,
    WorkflowSession,
    WorkflowEvent,
    FeasibilityResult,
    ToolpathPlanRef,
    WorkflowApproval,
    WorkflowTransitionError,
    GovernanceError,
    new_session,
    set_design,
    set_context,
    request_feasibility,
    store_feasibility,
    approve,
    reject,
    request_toolpaths,
    store_toolpaths,
    require_revision,
    archive,
    next_step_hint,
)

from .session_store import InMemoryWorkflowSessionStore, STORE

__all__ = [
    # Directional workflow (existing)
    "DirectionalMode",
    "ModePreviewRequest",
    "ModePreviewResult",
    "compute_feasibility_for_mode",
    "get_mode_constraints",
    # Canonical state machine (governance)
    "WorkflowMode",
    "WorkflowState",
    "RiskBucket",
    "ActorRole",
    "RunStatus",
    "WorkflowSession",
    "WorkflowEvent",
    "FeasibilityResult",
    "ToolpathPlanRef",
    "WorkflowApproval",
    "WorkflowTransitionError",
    "GovernanceError",
    "new_session",
    "set_design",
    "set_context",
    "request_feasibility",
    "store_feasibility",
    "approve",
    "reject",
    "request_toolpaths",
    "store_toolpaths",
    "require_revision",
    "archive",
    "next_step_hint",
    "InMemoryWorkflowSessionStore",
    "STORE",
]
