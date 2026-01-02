"""
RMOS Operations Module

LANE: OPERATION (governance-compliant)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

This module provides the execution spine for OPERATION lane endpoints.
All artifacts use canonical patterns from runs_v2.

Bundles implemented:
- Bundle 01: Operation Execution Spine (adapter.py, router.py)
- Bundle 02: Saw Execution Adapter (saw_adapter.py)
- Bundle 03: CAM Promotion Bridge (cam_adapter.py)
- Bundle 07: Backend Plan Endpoints (via adapter.plan())
"""

from .adapter import (
    OperationAdapter,
    execute_operation,
    plan_operation,
    OperationRequest,
    OperationResult,
    PlanRequest,
    PlanResult,
    ToolAdapter,
    extract_risk_level,
    should_block,
    make_event_type,
)

from .saw_adapter import (
    SawToolAdapter,
    execute_saw_v1,
    plan_saw_v1,
    compute_saw_feasibility,
)

from .cam_adapter import (
    CamRoughingAdapter,
    execute_cam_roughing_v1,
    plan_cam_roughing_v1,
    compute_cam_roughing_feasibility,
    promote_to_operation_lane,
)

from .router import router as operations_router

from .export import (
    export_run_to_zip,
    get_export_filename,
    ExportError,
)

__all__ = [
    # Core adapter
    "OperationAdapter",
    "execute_operation",
    "plan_operation",
    "OperationRequest",
    "OperationResult",
    "PlanRequest",
    "PlanResult",
    "ToolAdapter",
    # Utilities
    "extract_risk_level",
    "should_block",
    "make_event_type",
    # Saw adapter (Bundle 02)
    "SawToolAdapter",
    "execute_saw_v1",
    "plan_saw_v1",
    "compute_saw_feasibility",
    # CAM adapter (Bundle 03)
    "CamRoughingAdapter",
    "execute_cam_roughing_v1",
    "plan_cam_roughing_v1",
    "compute_cam_roughing_feasibility",
    "promote_to_operation_lane",
    # Router
    "operations_router",
    # Export (Bundle 04)
    "export_run_to_zip",
    "get_export_filename",
    "ExportError",
]
