"""
Saw Lab 2.0 - CNC Saw Blade Integration for RMOS

This module integrates saw blade operations as a first-class mode within
the RMOS orchestration system. Activated when tool_id starts with "saw:".

Key Components:
    - models.py: Pydantic models for saw operations
    - geometry.py: Geometry computation for saw paths
    - path_planner.py: Toolpath planning for saw cuts
    - toolpath_builder.py: G-code generation for saw operations
    - risk_evaluator.py: Safety risk assessment for saw operations
    - calculators/: Material-specific feasibility calculations
        - saw_heat.py: Heat buildup calculations
        - saw_deflection.py: Blade deflection analysis
        - saw_rimspeed.py: Rim speed safety checks
        - saw_bite_load.py: Tooth bite load analysis
        - saw_kickback.py: Kickback risk evaluation

Usage:
    from saw_lab import SawLabService, SawContext

    ctx = SawContext(
        blade_diameter_mm=254.0,
        blade_kerf_mm=3.0,
        tooth_count=24,
        max_rpm=5000
    )

    service = SawLabService()
    feasibility = service.check_feasibility(design, ctx)
    toolpaths = service.generate_toolpaths(design, ctx)
"""

from .models import (
    SawContext,
    SawDesign,
    SawFeasibilityResult,
    SawToolpathPlan,
    SawRiskLevel,
)
from .path_planner import (
    SawPathPlanner,
    # NEW: Saw Path Planner 2.1 exports
    SawPlannerConfig,
    SawCutOperation,
    SawCutPlan,
    SawCutContext,
    SawBladeSpec,
    SawMaterialSpec,
    SawLabConfig,
    plan_saw_cuts_for_board,
)
from .toolpath_builder import SawToolpathBuilder
from .risk_evaluator import SawRiskEvaluator
from .geometry import SawGeometryEngine

# Convenience imports for calculator bundle
from .calculators import FeasibilityCalculatorBundle


class SawLabService:
    """
    Main entry point for Saw Lab operations within RMOS.

    Provides:
        - Feasibility analysis for saw cuts
        - Toolpath generation for saw operations
        - Risk evaluation for safety
    """

    def __init__(self):
        self._path_planner = SawPathPlanner()
        self._toolpath_builder = SawToolpathBuilder()
        self._risk_evaluator = SawRiskEvaluator()
        self._geometry_engine = SawGeometryEngine()
        self._calculator_bundle = FeasibilityCalculatorBundle()

    def check_feasibility(
        self, design: SawDesign, ctx: SawContext
    ) -> SawFeasibilityResult:
        """
        Check if saw cut is feasible and safe.

        Args:
            design: Saw cut design parameters
            ctx: Saw blade and machine context

        Returns:
            SawFeasibilityResult with score, risk level, warnings
        """
        return self._calculator_bundle.evaluate(design, ctx)

    def generate_toolpaths(self, design: SawDesign, ctx: SawContext) -> SawToolpathPlan:
        """
        Generate toolpaths for saw cut operation.

        Args:
            design: Saw cut design parameters
            ctx: Saw blade and machine context

        Returns:
            SawToolpathPlan with moves, length, time estimate
        """
        # Generate geometry
        paths = self._path_planner.plan_cuts(design, ctx)

        # Convert to toolpath moves
        toolpaths = self._toolpath_builder.build(paths, ctx)

        return toolpaths

    def evaluate_risk(self, design: SawDesign, ctx: SawContext) -> SawRiskLevel:
        """
        Evaluate safety risk for saw operation.

        Args:
            design: Saw cut design parameters
            ctx: Saw blade and machine context

        Returns:
            SawRiskLevel enum (GREEN, YELLOW, RED)
        """
        return self._risk_evaluator.evaluate(design, ctx)


__all__ = [
    "SawLabService",
    "SawContext",
    "SawDesign",
    "SawFeasibilityResult",
    "SawToolpathPlan",
    "SawRiskLevel",
    "SawPathPlanner",
    "SawToolpathBuilder",
    "SawRiskEvaluator",
    "SawGeometryEngine",
    "FeasibilityCalculatorBundle",
    # NEW: Saw Path Planner 2.1 exports
    "SawPlannerConfig",
    "SawCutOperation",
    "SawCutPlan",
    "SawCutContext",
    "SawBladeSpec",
    "SawMaterialSpec",
    "SawLabConfig",
    "plan_saw_cuts_for_board",
    # Decision Intelligence
    "apply_decision_to_context",
    "get_multipliers_from_decision",
    # Toolpaths lookup
    "get_latest_toolpaths_for_decision",
    # Execution Metrics Rollup
    "rollup_execution_metrics_from_job_logs",
    "write_execution_metrics_rollup_artifact",
    # Execution Metrics Autorollup (Bundle 32.7.3)
    "is_execution_metrics_autorollup_enabled",
    "maybe_autorollup_execution_metrics",
    # Latest Batch Chain (Bundle 32.7.5)
    "resolve_latest_approved_decision_for_batch",
    "resolve_latest_execution_for_batch",
    "resolve_latest_metrics_for_batch",
]


# Lazy imports for decision apply service
def apply_decision_to_context(base_context, decision_payload):
    """Apply a tuning decision's multipliers to a base context."""
    from .decision_apply_service import apply_decision_to_context as _apply

    return _apply(base_context, decision_payload)


def get_multipliers_from_decision(decision_payload):
    """Extract multipliers from a tuning decision payload."""
    from .decision_apply_service import get_multipliers_from_decision as _get

    return _get(decision_payload)


def get_latest_toolpaths_for_decision(
    *, batch_decision_artifact_id, tool_kind="saw", limit=500
):
    """Lookup alias: decision -> latest toolpaths artifact."""
    from .toolpaths_lookup_service import get_latest_toolpaths_for_decision as _get

    return _get(
        batch_decision_artifact_id=batch_decision_artifact_id,
        tool_kind=tool_kind,
        limit=limit,
    )


def get_latest_execution_for_decision(
    *, batch_decision_artifact_id, tool_kind="saw", limit=1000
):
    """Lookup alias: decision -> latest execution artifact."""
    from .executions_lookup_service import get_latest_execution_for_decision as _get

    return _get(
        batch_decision_artifact_id=batch_decision_artifact_id,
        tool_kind=tool_kind,
        limit=limit,
    )


def list_executions_for_decision(
    *,
    batch_decision_artifact_id,
    tool_kind="saw",
    limit=200,
    offset=0,
    newest_first=True,
    max_scan=5000
):
    """List alias: decision -> all execution artifacts (summaries), paginated."""
    from .executions_list_service import list_executions_for_decision as _list

    return _list(
        batch_decision_artifact_id=batch_decision_artifact_id,
        tool_kind=tool_kind,
        limit=limit,
        offset=offset,
        newest_first=newest_first,
        max_scan=max_scan,
    )


def include_decision_intel_router(app) -> None:
    """
    Call from app.main after Saw routers are mounted.
    Kept here so Saw Lab owns its own router wiring.
    """
    from .decision_intelligence_router import router as decision_intel_router
    from .decision_intel_apply_router import router as decision_intel_apply_router

    app.include_router(decision_intel_router)
    app.include_router(decision_intel_apply_router)


# Execution Metrics Rollup
def rollup_execution_metrics_from_job_logs(job_log_artifacts):
    """Roll up KPIs from a list of job log artifacts (best-effort)."""
    from .execution_metrics_rollup_service import (
        rollup_execution_metrics_from_job_logs as _rollup,
    )

    return _rollup(job_log_artifacts)


def write_execution_metrics_rollup_artifact(
    *, batch_execution_artifact_id, session_id=None, batch_label=None, tool_kind="saw"
):
    """
    Reads all saw_batch_job_log artifacts for the batch execution, rolls up KPIs,
    and persists a governed metrics artifact.
    """
    from .execution_metrics_rollup_service import (
        write_execution_metrics_rollup_artifact as _write,
    )

    return _write(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )


# Lazy imports for execution metrics autorollup (Bundle 32.7.3)
def is_execution_metrics_autorollup_enabled():
    """Check if autorollup on job log write is enabled."""
    from .execution_metrics_autorollup import is_execution_metrics_autorollup_enabled as _is_enabled

    return _is_enabled()


def maybe_autorollup_execution_metrics(
    *, batch_execution_artifact_id, session_id=None, batch_label=None, tool_kind="saw"
):
    """Best-effort writer for execution metrics rollup triggered by job log write."""
    from .execution_metrics_autorollup import maybe_autorollup_execution_metrics as _maybe

    return _maybe(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )


# Lazy imports for latest batch chain (Bundle 32.7.5)
def resolve_latest_approved_decision_for_batch(
    *, session_id, batch_label, tool_kind="saw", limit=20000
):
    """Returns latest APPROVED decision artifact for a batch (best-effort)."""
    from .latest_batch_chain_service import resolve_latest_approved_decision_for_batch as _resolve

    return _resolve(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        limit=limit,
    )


def resolve_latest_execution_for_batch(
    *, session_id, batch_label, tool_kind="saw", limit=20000
):
    """Latest execution for the batch (does not require decision id)."""
    from .latest_batch_chain_service import resolve_latest_execution_for_batch as _resolve

    return _resolve(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        limit=limit,
    )


def resolve_latest_metrics_for_batch(*, session_id, batch_label, tool_kind="saw"):
    """No decision id required: batch -> latest execution -> latest metrics."""
    from .latest_batch_chain_service import resolve_latest_metrics_for_batch as _resolve

    return _resolve(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
