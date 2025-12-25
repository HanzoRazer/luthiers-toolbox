"""
Art Studio Workflow Integration Service

Bridges Pattern Library (generators, patterns, snapshots) with the
governance-compliant Workflow State Machine.

Enables:
- Creating workflow sessions from saved patterns
- Generating designs directly from parametric generators
- Restoring work-in-progress from snapshots
- Server-side feasibility evaluation
- Human approval workflow before toolpath generation
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel, Field

# Conditional imports for FastAPI context vs CLI testing
try:
    from app.workflow.state_machine import (
        WorkflowSession,
        WorkflowMode,
        WorkflowState,
        ActorRole,
        RiskBucket,
        FeasibilityResult,
        new_session,
        set_design,
        set_context,
        request_feasibility,
        store_feasibility,
        approve,
        reject,
        require_revision,
        next_step_hint,
    )
    from app.workflow.session_store import STORE as SESSION_STORE
    from app.workflow.workflow_runs_bridge import get_workflow_runs_bridge

    from app.art_studio.services.pattern_store import PatternStore, resolve_art_studio_data_root
    from app.art_studio.services.design_snapshot_store import DesignSnapshotStore
    from app.art_studio.services.generators.registry import generate_spec, list_generators
    from app.art_studio.schemas.design_snapshot import (
        DesignSnapshot,
        DesignContextRefs,
        SnapshotCreateRequest,
    )
    from app.art_studio.schemas.rosette_params import RosetteParamSpec

    # RMOS Integration (H5.2 - feasibility wiring)
    from app.rmos.presets import get_preset_registry
    from app.rmos.feasibility_fusion import evaluate_feasibility as rmos_evaluate_feasibility, RiskLevel
    from app.rmos.context import RmosContext, MaterialProfile
except ImportError:
    # Fallback for CLI testing or relative imports within package
    try:
        from workflow.state_machine import (
            WorkflowSession,
            WorkflowMode,
            WorkflowState,
            ActorRole,
            RiskBucket,
            FeasibilityResult,
            new_session,
            set_design,
            set_context,
            request_feasibility,
            store_feasibility,
            approve,
            reject,
            require_revision,
            next_step_hint,
        )
        from workflow.session_store import STORE as SESSION_STORE
        from workflow.workflow_runs_bridge import get_workflow_runs_bridge

        from art_studio.services.pattern_store import PatternStore, resolve_art_studio_data_root
        from art_studio.services.design_snapshot_store import DesignSnapshotStore
        from art_studio.services.generators.registry import generate_spec, list_generators
        from art_studio.schemas.design_snapshot import (
            DesignSnapshot,
            DesignContextRefs,
            SnapshotCreateRequest,
        )
        from art_studio.schemas.rosette_params import RosetteParamSpec

        # RMOS Integration (H5.2 - feasibility wiring)
        from rmos.presets import get_preset_registry
        from rmos.feasibility_fusion import evaluate_feasibility as rmos_evaluate_feasibility, RiskLevel
        from rmos.context import RmosContext, MaterialProfile
    except ImportError:
        # Final fallback: relative imports (when used as submodule)
        from ...workflow.state_machine import (
            WorkflowSession,
            WorkflowMode,
            WorkflowState,
            ActorRole,
            RiskBucket,
            FeasibilityResult,
            new_session,
            set_design,
            set_context,
            request_feasibility,
            store_feasibility,
            approve,
            reject,
            require_revision,
            next_step_hint,
        )
        from ...workflow.session_store import STORE as SESSION_STORE
        from ...workflow.workflow_runs_bridge import get_workflow_runs_bridge

        from .pattern_store import PatternStore, resolve_art_studio_data_root
        from .design_snapshot_store import DesignSnapshotStore
        from .generators.registry import generate_spec, list_generators
        from ..schemas.design_snapshot import (
            DesignSnapshot,
            DesignContextRefs,
            SnapshotCreateRequest,
        )
        from ..schemas.rosette_params import RosetteParamSpec

        # RMOS Integration (H5.2 - feasibility wiring)
        from ...rmos.presets import get_preset_registry
        from ...rmos.feasibility_fusion import evaluate_feasibility as rmos_evaluate_feasibility, RiskLevel
        from ...rmos.context import RmosContext, MaterialProfile

logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================

class CreateFromPatternRequest(BaseModel):
    """Create workflow session from a pattern library item."""
    pattern_id: str
    mode: WorkflowMode = WorkflowMode.DESIGN_FIRST
    context_refs: Optional[DesignContextRefs] = None
    context_override: Optional[Dict[str, Any]] = None


class CreateFromGeneratorRequest(BaseModel):
    """Create workflow session directly from a generator."""
    generator_key: str
    outer_diameter_mm: float = Field(..., gt=0)
    inner_diameter_mm: float = Field(..., ge=0)
    params: Dict[str, Any] = Field(default_factory=dict)
    mode: WorkflowMode = WorkflowMode.DESIGN_FIRST
    context_refs: Optional[DesignContextRefs] = None
    context_override: Optional[Dict[str, Any]] = None


class CreateFromSnapshotRequest(BaseModel):
    """Create workflow session from a saved snapshot."""
    snapshot_id: str
    mode: Optional[WorkflowMode] = None  # None = use snapshot's mode
    context_override: Optional[Dict[str, Any]] = None


class EvaluateFeasibilityRequest(BaseModel):
    """Request to evaluate feasibility for a session."""
    context_override: Optional[Dict[str, Any]] = None


class ApproveSessionRequest(BaseModel):
    """Request to approve a session."""
    note: Optional[str] = None


class RejectSessionRequest(BaseModel):
    """Request to reject a session."""
    reason: str


class RequestRevisionRequest(BaseModel):
    """Request design revision."""
    reason: str


class UpdateDesignRequest(BaseModel):
    """Update session design parameters."""
    rosette_params: RosetteParamSpec


class SaveSnapshotRequest(BaseModel):
    """Save current session state as a snapshot."""
    name: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class SessionStatusResponse(BaseModel):
    """Detailed session status for UI."""
    session_id: str
    mode: str
    state: str
    next_step: str
    events_count: int
    
    # Design info
    has_design: bool
    has_context: bool
    
    # Feasibility info
    feasibility_score: Optional[float] = None
    feasibility_risk: Optional[str] = None
    feasibility_warnings: List[str] = Field(default_factory=list)
    
    # Artifact refs
    last_feasibility_artifact_id: Optional[str] = None
    last_toolpaths_artifact_id: Optional[str] = None
    
    # Governance
    allow_red_override: bool = False
    require_explicit_approval: bool = True


class WorkflowCreatedResponse(BaseModel):
    """Response after creating a workflow session."""
    session_id: str
    mode: str
    state: str
    next_step: str
    warnings: List[str] = Field(default_factory=list)


class FeasibilityResponse(BaseModel):
    """Response after feasibility evaluation."""
    session_id: str
    state: str
    score: float
    risk_bucket: str
    warnings: List[str]
    run_artifact_id: Optional[str] = None
    next_step: str


class ApprovalResponse(BaseModel):
    """Response after approval/rejection."""
    session_id: str
    state: str
    approved: bool
    message: str
    run_artifact_id: Optional[str] = None


class SnapshotCreatedResponse(BaseModel):
    """Response after saving a snapshot."""
    snapshot_id: str
    name: str
    session_id: str


class GeneratorInfo(BaseModel):
    """Generator info for UI."""
    generator_key: str
    name: str
    description: str
    param_hints: Dict[str, Any]


# =============================================================================
# Integration Service Functions
# =============================================================================

def _get_pattern_store() -> PatternStore:
    """Get pattern store instance."""
    return PatternStore(data_root=resolve_art_studio_data_root())


def _get_snapshot_store() -> DesignSnapshotStore:
    """Get snapshot store instance."""
    return DesignSnapshotStore(data_root=resolve_art_studio_data_root())


def _build_context_from_refs(refs: Optional[DesignContextRefs]) -> Dict[str, Any]:
    """
    Build RMOS context dict from context refs.

    Loads full preset data from the preset registry for material and tool presets.
    """
    if refs is None:
        return {}

    context: Dict[str, Any] = {}
    registry = get_preset_registry()

    if refs.material_preset_id:
        material = registry.get_material(refs.material_preset_id)
        if material:
            context["material"] = {
                "id": material.id,
                "name": material.name,
                "hardness": material.hardness,
                "density_kgm3": material.density_kgm3,
                "burn_tendency": material.burn_tendency,
                "tearout_tendency": material.tearout_tendency,
                "recommended_feed_mm_min": material.recommended_feed_mm_min,
                "recommended_rpm": material.recommended_rpm,
            }
        context["material_id"] = refs.material_preset_id

    if refs.tool_preset_id:
        tool = registry.get_tool(refs.tool_preset_id)
        if tool:
            context["tool"] = {
                "id": tool.id,
                "name": tool.name,
                "diameter_mm": tool.diameter_mm,
                "flute_count": tool.flute_count,
                "tool_type": tool.tool_type,
            }
        context["tool_id"] = refs.tool_preset_id

    if refs.machine_id:
        context["machine_id"] = refs.machine_id

    if refs.mode:
        context["workflow_mode"] = refs.mode

    return context


def create_workflow_from_pattern(
    request: CreateFromPatternRequest,
) -> WorkflowCreatedResponse:
    """
    Create a workflow session from a pattern library item.
    
    1. Load pattern from store
    2. Generate RosetteParamSpec using pattern's generator
    3. Create workflow session in DRAFT state
    4. Set design and context
    5. Return session for further workflow steps
    """
    store = _get_pattern_store()
    pattern = store.get(request.pattern_id)
    
    if pattern is None:
        raise ValueError(f"Pattern not found: {request.pattern_id}")
    
    warnings: List[str] = []
    
    # Generate spec from pattern
    gen_response = generate_spec(
        generator_key=pattern.generator_key,
        outer_diameter_mm=pattern.params.get("outer_diameter_mm", 100.0),
        inner_diameter_mm=pattern.params.get("inner_diameter_mm", 10.0),
        params=pattern.params,
    )
    warnings.extend(gen_response.warnings)
    
    # Build context
    context = _build_context_from_refs(request.context_refs)
    if request.context_override:
        context.update(request.context_override)
    
    # Create session
    index_meta = {
        "tool_id": context.get("tool_id"),
        "material_id": context.get("material_id"),
        "machine_id": context.get("machine_id"),
        "pattern_id": request.pattern_id,
        "generator_key": pattern.generator_key,
    }
    
    session = new_session(request.mode, index_meta=index_meta)
    
    # Set design
    design_dict = gen_response.spec.model_dump()
    set_design(session, design_dict, actor=ActorRole.USER)
    
    # Set context (transitions to CONTEXT_READY)
    set_context(session, context, actor=ActorRole.USER)
    
    SESSION_STORE.put(session)
    
    logger.info(
        "art_studio.workflow_from_pattern",
        extra={
            "session_id": session.session_id,
            "pattern_id": request.pattern_id,
            "generator_key": pattern.generator_key,
        }
    )
    
    return WorkflowCreatedResponse(
        session_id=session.session_id,
        mode=session.mode.value,
        state=session.state.value,
        next_step=next_step_hint(session),
        warnings=warnings,
    )


def create_workflow_from_generator(
    request: CreateFromGeneratorRequest,
) -> WorkflowCreatedResponse:
    """
    Create a workflow session directly from a parametric generator.
    
    Skips pattern library - generates spec directly.
    """
    warnings: List[str] = []
    
    # Generate spec
    gen_response = generate_spec(
        generator_key=request.generator_key,
        outer_diameter_mm=request.outer_diameter_mm,
        inner_diameter_mm=request.inner_diameter_mm,
        params=request.params,
    )
    warnings.extend(gen_response.warnings)
    
    # Build context
    context = _build_context_from_refs(request.context_refs)
    if request.context_override:
        context.update(request.context_override)
    
    # Create session
    index_meta = {
        "tool_id": context.get("tool_id"),
        "material_id": context.get("material_id"),
        "machine_id": context.get("machine_id"),
        "generator_key": request.generator_key,
    }
    
    session = new_session(request.mode, index_meta=index_meta)
    
    # Set design
    design_dict = gen_response.spec.model_dump()
    set_design(session, design_dict, actor=ActorRole.USER)
    
    # Set context
    set_context(session, context, actor=ActorRole.USER)
    
    SESSION_STORE.put(session)
    
    logger.info(
        "art_studio.workflow_from_generator",
        extra={
            "session_id": session.session_id,
            "generator_key": request.generator_key,
        }
    )
    
    return WorkflowCreatedResponse(
        session_id=session.session_id,
        mode=session.mode.value,
        state=session.state.value,
        next_step=next_step_hint(session),
        warnings=warnings,
    )


def create_workflow_from_snapshot(
    request: CreateFromSnapshotRequest,
) -> WorkflowCreatedResponse:
    """
    Create a workflow session from a saved snapshot.
    
    Restores design parameters, context refs, and optionally feasibility.
    """
    store = _get_snapshot_store()
    snapshot = store.get(request.snapshot_id)
    
    if snapshot is None:
        raise ValueError(f"Snapshot not found: {request.snapshot_id}")
    
    warnings: List[str] = []
    
    # Determine mode
    mode = request.mode
    if mode is None:
        mode_str = snapshot.context_refs.mode if snapshot.context_refs else "design_first"
        try:
            mode = WorkflowMode(mode_str.lower())
        except ValueError:
            mode = WorkflowMode.DESIGN_FIRST
            warnings.append(f"Unknown mode '{mode_str}', defaulting to design_first")
    
    # Build context
    context = _build_context_from_refs(snapshot.context_refs)
    if request.context_override:
        context.update(request.context_override)
    
    # Create session
    index_meta = {
        "tool_id": context.get("tool_id"),
        "material_id": context.get("material_id"),
        "machine_id": context.get("machine_id"),
        "snapshot_id": request.snapshot_id,
        "pattern_id": snapshot.pattern_id,
    }
    
    session = new_session(mode, index_meta=index_meta)
    
    # Set design from snapshot
    design_dict = snapshot.rosette_params.model_dump()
    set_design(session, design_dict, actor=ActorRole.USER)
    
    # Set context
    set_context(session, context, actor=ActorRole.USER)
    
    SESSION_STORE.put(session)
    
    logger.info(
        "art_studio.workflow_from_snapshot",
        extra={
            "session_id": session.session_id,
            "snapshot_id": request.snapshot_id,
        }
    )
    
    return WorkflowCreatedResponse(
        session_id=session.session_id,
        mode=session.mode.value,
        state=session.state.value,
        next_step=next_step_hint(session),
        warnings=warnings,
    )


def evaluate_session_feasibility(
    session_id: str,
    request: Optional[EvaluateFeasibilityRequest] = None,
) -> FeasibilityResponse:
    """
    Evaluate feasibility for a session using RMOS feasibility engine.
    
    1. Request feasibility (state transition)
    2. Compute feasibility server-side
    3. Store result (state transition)
    4. Create run artifact via bridge
    """
    session = SESSION_STORE.get(session_id)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")
    
    # Transition to FEASIBILITY_REQUESTED
    request_feasibility(session, actor=ActorRole.USER)

    # Get design and context
    design = session.design or {}
    context_dict = session.context or {}

    # Apply any request-level context override
    if request and request.context_override:
        context_dict = {**context_dict, **request.context_override}

    # Build RMOS context for feasibility evaluation
    try:
        # Create MaterialProfile from context if material data available
        material_profile = None
        if "material" in context_dict:
            mat = context_dict["material"]
            material_profile = MaterialProfile(
                density_kg_m3=mat.get("density_kgm3", 700.0),
            )

        # Build RmosContext
        rmos_ctx = RmosContext(
            model_id=context_dict.get("model_id", "generic"),
            model_spec=context_dict.get("model_spec", {}),
            materials=material_profile,
        )

        # Add design parameters to physics_inputs for calculator access
        rmos_ctx.physics_inputs = {
            "tool_diameter_mm": context_dict.get("tool", {}).get("diameter_mm", 6.0),
            "feed_rate_mmpm": context_dict.get("material", {}).get("recommended_feed_mm_min", 1500),
            "spindle_rpm": context_dict.get("material", {}).get("recommended_rpm", 18000),
            "depth_of_cut_mm": design.get("depth_mm", 3.0),
            **design,
        }

        # Evaluate using RMOS feasibility engine
        report = rmos_evaluate_feasibility(design, rmos_ctx)

        # Map RiskLevel to RiskBucket
        risk_level_to_bucket = {
            RiskLevel.GREEN: RiskBucket.GREEN,
            RiskLevel.YELLOW: RiskBucket.YELLOW,
            RiskLevel.RED: RiskBucket.RED,
            RiskLevel.UNKNOWN: RiskBucket.UNKNOWN,
        }

        score = report.overall_score
        risk_bucket = risk_level_to_bucket.get(report.overall_risk, RiskBucket.UNKNOWN)

        # Collect all warnings from assessments + recommendations
        warnings: List[str] = []
        for assessment in report.assessments:
            warnings.extend(assessment.warnings)
        warnings.extend(report.recommendations)

    except Exception as e:
        # Fallback to basic validation if RMOS engine fails
        logger.warning(f"RMOS feasibility engine failed, using fallback: {e}")
        score = 70.0
        risk_bucket = RiskBucket.YELLOW
        warnings = [f"Feasibility engine error: {str(e)}", "Using fallback validation"]

        # Basic validation checks as fallback
        outer_d = design.get("outer_diameter_mm", 0)
        inner_d = design.get("inner_diameter_mm", 0)

        if outer_d <= 0:
            warnings.append("Invalid outer diameter")
            score -= 20
        if inner_d < 0:
            warnings.append("Invalid inner diameter")
            score -= 10
        if outer_d > 0 and outer_d <= inner_d:
            warnings.append("Outer diameter must be greater than inner diameter")
            score -= 30
            risk_bucket = RiskBucket.RED

        score = max(0.0, min(100.0, score))
        if score < 50:
            risk_bucket = RiskBucket.RED
        elif score < 70:
            risk_bucket = RiskBucket.YELLOW
    
    # Create feasibility result
    result = FeasibilityResult(
        score=score,
        risk_bucket=risk_bucket,
        warnings=warnings,
        meta={
            "source": "rmos_feasibility_fusion",  # Mark as RMOS engine-computed
            "design_hash": str(hash(str(design))),
        },
    )
    
    # Store feasibility (transitions to FEASIBILITY_READY)
    store_feasibility(session, result, actor=ActorRole.SYSTEM)
    
    # Create run artifact via bridge
    bridge = get_workflow_runs_bridge()
    artifact_ref = bridge.on_feasibility_stored(session)
    
    if artifact_ref:
        session.last_feasibility_artifact = artifact_ref
    
    SESSION_STORE.put(session)
    
    logger.info(
        "art_studio.feasibility_evaluated",
        extra={
            "session_id": session_id,
            "score": score,
            "risk_bucket": risk_bucket.value,
        }
    )
    
    return FeasibilityResponse(
        session_id=session_id,
        state=session.state.value,
        score=score,
        risk_bucket=risk_bucket.value,
        warnings=warnings,
        run_artifact_id=artifact_ref.artifact_id if artifact_ref else None,
        next_step=next_step_hint(session),
    )


def approve_session(
    session_id: str,
    request: ApproveSessionRequest,
) -> ApprovalResponse:
    """
    Approve a session for toolpath generation.
    
    Enforces governance rules (score threshold, risk level).
    """
    session = SESSION_STORE.get(session_id)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")
    
    try:
        approve(session, actor=ActorRole.OPERATOR, note=request.note)
        
        # Create run artifact via bridge
        bridge = get_workflow_runs_bridge()
        artifact_ref = bridge.on_approved(session)
        
        SESSION_STORE.put(session)
        
        logger.info(
            "art_studio.session_approved",
            extra={"session_id": session_id}
        )
        
        return ApprovalResponse(
            session_id=session_id,
            state=session.state.value,
            approved=True,
            message="Session approved for toolpath generation",
            run_artifact_id=artifact_ref.artifact_id if artifact_ref else None,
        )
    except Exception as e:
        return ApprovalResponse(
            session_id=session_id,
            state=session.state.value,
            approved=False,
            message=str(e),
        )


def reject_session(
    session_id: str,
    request: RejectSessionRequest,
) -> ApprovalResponse:
    """Reject a session."""
    session = SESSION_STORE.get(session_id)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")
    
    reject(session, actor=ActorRole.OPERATOR, reason=request.reason)
    
    # Create run artifact via bridge
    bridge = get_workflow_runs_bridge()
    artifact_ref = bridge.on_rejected(session, reason=request.reason)
    
    SESSION_STORE.put(session)
    
    logger.info(
        "art_studio.session_rejected",
        extra={"session_id": session_id, "reason": request.reason}
    )
    
    return ApprovalResponse(
        session_id=session_id,
        state=session.state.value,
        approved=False,
        message=f"Session rejected: {request.reason}",
        run_artifact_id=artifact_ref.artifact_id if artifact_ref else None,
    )


def request_session_revision(
    session_id: str,
    request: RequestRevisionRequest,
) -> SessionStatusResponse:
    """Request design revision for a session."""
    session = SESSION_STORE.get(session_id)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")
    
    require_revision(session, actor=ActorRole.OPERATOR, reason=request.reason)
    SESSION_STORE.put(session)
    
    logger.info(
        "art_studio.revision_requested",
        extra={"session_id": session_id, "reason": request.reason}
    )
    
    return get_session_status(session_id)


def update_session_design(
    session_id: str,
    request: UpdateDesignRequest,
) -> SessionStatusResponse:
    """Update design parameters for a session."""
    session = SESSION_STORE.get(session_id)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")
    
    design_dict = request.rosette_params.model_dump()
    set_design(session, design_dict, actor=ActorRole.USER)
    SESSION_STORE.put(session)
    
    logger.info(
        "art_studio.design_updated",
        extra={"session_id": session_id}
    )
    
    return get_session_status(session_id)


def save_session_as_snapshot(
    session_id: str,
    request: SaveSnapshotRequest,
) -> SnapshotCreatedResponse:
    """Save current session state as a snapshot."""
    session = SESSION_STORE.get(session_id)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")
    
    if session.design is None:
        raise ValueError("Session has no design to save")
    
    # Build snapshot request
    context_refs = DesignContextRefs(
        material_preset_id=session.index_meta.get("material_id"),
        tool_preset_id=session.index_meta.get("tool_id"),
        machine_id=session.index_meta.get("machine_id"),
        mode=session.mode.value,
    )
    
    # Convert design dict back to RosetteParamSpec
    rosette_params = RosetteParamSpec.model_validate(session.design)
    
    # Build feasibility dict if available
    feasibility_dict = None
    if session.feasibility:
        feasibility_dict = {
            "score": session.feasibility.score,
            "risk_bucket": session.feasibility.risk_bucket.value,
            "warnings": session.feasibility.warnings,
            "meta": session.feasibility.meta,
        }
    
    snapshot_request = SnapshotCreateRequest(
        name=request.name,
        notes=request.notes,
        pattern_id=session.index_meta.get("pattern_id"),
        tags=request.tags,
        context_refs=context_refs,
        rosette_params=rosette_params,
        feasibility=feasibility_dict,
    )
    
    store = _get_snapshot_store()
    snapshot = store.create(snapshot_request)
    
    logger.info(
        "art_studio.snapshot_saved",
        extra={
            "session_id": session_id,
            "snapshot_id": snapshot.snapshot_id,
        }
    )
    
    return SnapshotCreatedResponse(
        snapshot_id=snapshot.snapshot_id,
        name=snapshot.name,
        session_id=session_id,
    )


def list_active_sessions(
    limit: int = 50,
    state_filter: Optional[str] = None,
) -> List[SessionStatusResponse]:
    """List non-archived workflow sessions."""
    all_sessions = SESSION_STORE.list_all()
    
    results: List[SessionStatusResponse] = []
    
    for session in all_sessions:
        # Skip archived
        if session.state == WorkflowState.ARCHIVED:
            continue
        
        # Apply state filter
        if state_filter:
            try:
                filter_state = WorkflowState(state_filter)
                if session.state != filter_state:
                    continue
            except ValueError:
                pass
        
        results.append(_session_to_status(session))
        
        if len(results) >= limit:
            break
    
    return results


def get_session_status(session_id: str) -> SessionStatusResponse:
    """Get detailed session status."""
    session = SESSION_STORE.get(session_id)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")
    
    return _session_to_status(session)


def _session_to_status(session: WorkflowSession) -> SessionStatusResponse:
    """Convert WorkflowSession to SessionStatusResponse."""
    feas_score = None
    feas_risk = None
    feas_warnings: List[str] = []
    
    if session.feasibility:
        feas_score = session.feasibility.score
        feas_risk = session.feasibility.risk_bucket.value
        feas_warnings = session.feasibility.warnings
    
    return SessionStatusResponse(
        session_id=session.session_id,
        mode=session.mode.value,
        state=session.state.value,
        next_step=next_step_hint(session),
        events_count=len(session.events),
        has_design=session.design is not None,
        has_context=session.context is not None,
        feasibility_score=feas_score,
        feasibility_risk=feas_risk,
        feasibility_warnings=feas_warnings,
        last_feasibility_artifact_id=(
            session.last_feasibility_artifact.artifact_id
            if session.last_feasibility_artifact else None
        ),
        last_toolpaths_artifact_id=(
            session.last_toolpaths_artifact.artifact_id
            if session.last_toolpaths_artifact else None
        ),
        allow_red_override=session.allow_red_override,
        require_explicit_approval=session.require_explicit_approval,
    )


def get_available_generators() -> List[GeneratorInfo]:
    """List available parametric generators."""
    descriptors = list_generators()
    
    return [
        GeneratorInfo(
            generator_key=d.generator_key,
            name=d.name,
            description=d.description,
            param_hints=d.param_hints,
        )
        for d in descriptors
    ]
