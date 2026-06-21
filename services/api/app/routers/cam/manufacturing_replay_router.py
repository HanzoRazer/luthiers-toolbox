"""
Manufacturing Replay Router

CAM Dev Order 7W: HTTP endpoints for observational manufacturing replay.

Provides endpoints for:
  - Review observations
  - Replay sessions
  - Review timelines
  - Replay packages
  - CI summary

7W invariants:
  - No endpoint authorizes execution
  - No endpoint allows machine output
  - No endpoint replays execution
  - No endpoint generates G-code
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.cam.manufacturing_review_observation import (
    ManufacturingReviewObservation,
    ReviewObservationCategory,
    ObservationSeverity,
    create_review_observation,
    create_topology_warning,
    create_fixture_warning,
    create_export_review_note,
    create_review_rationale,
    validate_observation,
)
from app.cam.manufacturing_replay_session import (
    ManufacturingReplaySession,
    ReplayContinuityState,
    create_replay_session,
    add_observation_to_session,
    add_fixture_package_to_session,
    add_export_package_to_session,
    validate_replay_session,
    is_replay_complete,
    is_replay_fragmented,
)
from app.cam.review_intelligence_timeline import (
    ReviewIntelligenceTimeline,
    create_review_timeline,
    append_observation_to_timeline,
    validate_timeline,
    get_timeline_summary,
)
from app.cam.replay_safe_review_package import (
    ReplaySafeReviewPackage,
    create_replay_safe_review_package,
    validate_replay_safe_review_package,
    get_package_summary,
)
from app.cam.manufacturing_replay_registry import (
    register_review_observation,
    get_review_observation,
    list_review_observations,
    list_observations_by_workspace,
    list_observations_by_strategy,
    list_observations_by_category,
    list_observations_by_severity,
    register_replay_session,
    get_replay_session,
    list_replay_sessions,
    list_sessions_by_workspace,
    list_sessions_by_strategy,
    list_sessions_by_continuity_state,
    register_review_timeline,
    get_review_timeline,
    list_review_timelines,
    list_timelines_by_session,
    register_replay_safe_review_package,
    get_replay_safe_review_package,
    list_replay_safe_review_packages,
    list_packages_by_session,
    validate_replay_continuity,
    detect_fragmented_replay,
    build_review_timeline,
    build_replay_summary,
    build_observational_replay,
    get_ci_summary,
)


router = APIRouter(
    prefix="/api/cam/manufacturing-replay",
    tags=["CAM", "Manufacturing", "Replay", "Review"],
)


class ManufacturingReplayMeta(BaseModel):
    """Metadata for Manufacturing Replay API."""

    version: str = "7W"
    replay_execution_present: bool = False
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    generates_gcode: bool = False
    description: str = "Observational manufacturing replay intelligence — no execution"


@router.get("/", response_model=ManufacturingReplayMeta)
async def get_meta() -> ManufacturingReplayMeta:
    """Get Manufacturing Replay API metadata."""
    return ManufacturingReplayMeta()


# ============================================================================
# OBSERVATION ENDPOINTS
# ============================================================================


class CreateObservationRequest(BaseModel):
    """Request to create a review observation."""

    observation_category: ReviewObservationCategory
    observation_text: str
    workspace_id: Optional[str] = None
    strategy_id: Optional[str] = None
    fixture_package_id: Optional[str] = None
    export_package_id: Optional[str] = None
    geometry_authority_ref_ids: Optional[List[str]] = None
    severity: ObservationSeverity = "info"
    provenance_refs: Optional[List[str]] = None
    review_required: bool = True


@router.post("/observations", response_model=ManufacturingReviewObservation)
async def create_observation(
    request: CreateObservationRequest,
) -> ManufacturingReviewObservation:
    """
    Create and register a review observation.

    Observations are observational only — they do not authorize execution.
    """
    observation = create_review_observation(
        observation_category=request.observation_category,
        observation_text=request.observation_text,
        workspace_id=request.workspace_id,
        strategy_id=request.strategy_id,
        fixture_package_id=request.fixture_package_id,
        export_package_id=request.export_package_id,
        geometry_authority_ref_ids=request.geometry_authority_ref_ids,
        severity=request.severity,
        provenance_refs=request.provenance_refs,
        review_required=request.review_required,
    )
    return register_review_observation(observation)


@router.get("/observations", response_model=List[ManufacturingReviewObservation])
async def list_observations() -> List[ManufacturingReviewObservation]:
    """List all review observations."""
    return list_review_observations()


@router.get("/observations/{observation_id}", response_model=ManufacturingReviewObservation)
async def get_observation(observation_id: str) -> ManufacturingReviewObservation:
    """Get a specific observation by ID."""
    observation = get_review_observation(observation_id)
    if not observation:
        raise HTTPException(404, f"Observation '{observation_id}' not found")
    return observation


@router.get(
    "/observations/by-workspace/{workspace_id}",
    response_model=List[ManufacturingReviewObservation],
)
async def get_observations_by_workspace(
    workspace_id: str,
) -> List[ManufacturingReviewObservation]:
    """List all observations for a workspace."""
    return list_observations_by_workspace(workspace_id)


@router.get(
    "/observations/by-strategy/{strategy_id}",
    response_model=List[ManufacturingReviewObservation],
)
async def get_observations_by_strategy(
    strategy_id: str,
) -> List[ManufacturingReviewObservation]:
    """List all observations for a strategy."""
    return list_observations_by_strategy(strategy_id)


@router.get(
    "/observations/by-category/{category}",
    response_model=List[ManufacturingReviewObservation],
)
async def get_observations_by_category(
    category: ReviewObservationCategory,
) -> List[ManufacturingReviewObservation]:
    """List all observations with a specific category."""
    return list_observations_by_category(category)


@router.get(
    "/observations/by-severity/{severity}",
    response_model=List[ManufacturingReviewObservation],
)
async def get_observations_by_severity(
    severity: ObservationSeverity,
) -> List[ManufacturingReviewObservation]:
    """List all observations with a specific severity."""
    return list_observations_by_severity(severity)


@router.post("/observations/{observation_id}/validate")
async def validate_observation_endpoint(observation_id: str) -> Dict[str, Any]:
    """Validate that an observation is well-formed."""
    observation = get_review_observation(observation_id)
    if not observation:
        raise HTTPException(404, f"Observation '{observation_id}' not found")

    is_valid, issues = validate_observation(observation)

    return {
        "observation_id": observation_id,
        "is_valid": is_valid,
        "issues": issues,
        "category": observation.observation_category,
        "severity": observation.severity,
    }


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================


class CreateSessionRequest(BaseModel):
    """Request to create a replay session."""

    workspace_id: Optional[str] = None
    strategy_id: Optional[str] = None
    observation_ids: Optional[List[str]] = None
    topology_evaluation_ids: Optional[List[str]] = None
    fixture_package_ids: Optional[List[str]] = None
    export_package_ids: Optional[List[str]] = None


@router.post("/session", response_model=ManufacturingReplaySession)
async def create_session(
    request: CreateSessionRequest,
) -> ManufacturingReplaySession:
    """
    Create and register a replay session.

    Sessions collect observation references for replay — they do not replay execution.
    """
    session = create_replay_session(
        workspace_id=request.workspace_id,
        strategy_id=request.strategy_id,
        observation_ids=request.observation_ids,
        topology_evaluation_ids=request.topology_evaluation_ids,
        fixture_package_ids=request.fixture_package_ids,
        export_package_ids=request.export_package_ids,
    )
    return register_replay_session(session)


@router.get("/sessions", response_model=List[ManufacturingReplaySession])
async def list_sessions() -> List[ManufacturingReplaySession]:
    """List all replay sessions."""
    return list_replay_sessions()


@router.get("/session/{session_id}", response_model=ManufacturingReplaySession)
async def get_session(session_id: str) -> ManufacturingReplaySession:
    """Get a specific session by ID."""
    session = get_replay_session(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return session


@router.get(
    "/sessions/by-workspace/{workspace_id}",
    response_model=List[ManufacturingReplaySession],
)
async def get_sessions_by_workspace(
    workspace_id: str,
) -> List[ManufacturingReplaySession]:
    """List all sessions for a workspace."""
    return list_sessions_by_workspace(workspace_id)


@router.get(
    "/sessions/by-strategy/{strategy_id}",
    response_model=List[ManufacturingReplaySession],
)
async def get_sessions_by_strategy(
    strategy_id: str,
) -> List[ManufacturingReplaySession]:
    """List all sessions for a strategy."""
    return list_sessions_by_strategy(strategy_id)


@router.get(
    "/sessions/by-continuity-state/{continuity_state}",
    response_model=List[ManufacturingReplaySession],
)
async def get_sessions_by_continuity_state(
    continuity_state: ReplayContinuityState,
) -> List[ManufacturingReplaySession]:
    """List all sessions with a specific continuity state."""
    return list_sessions_by_continuity_state(continuity_state)


class AddObservationToSessionRequest(BaseModel):
    """Request to add an observation to a session."""

    observation_id: str


@router.post(
    "/session/{session_id}/observations",
    response_model=ManufacturingReplaySession,
)
async def add_observation_to_session_endpoint(
    session_id: str,
    request: AddObservationToSessionRequest,
) -> ManufacturingReplaySession:
    """Add an observation to a session."""
    session = get_replay_session(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")

    observation = get_review_observation(request.observation_id)
    if not observation:
        raise HTTPException(404, f"Observation '{request.observation_id}' not found")

    updated = add_observation_to_session(session, request.observation_id)
    return updated


@router.post("/session/{session_id}/validate")
async def validate_session_endpoint(session_id: str) -> Dict[str, Any]:
    """Validate that a session is well-formed."""
    session = get_replay_session(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")

    is_valid, issues = validate_replay_session(session)
    continuity_valid, continuity_issues = validate_replay_continuity(session)
    is_fragmented, missing_refs = detect_fragmented_replay(session)

    return {
        "session_id": session_id,
        "is_valid": is_valid,
        "issues": issues,
        "continuity_valid": continuity_valid,
        "continuity_issues": continuity_issues,
        "is_fragmented": is_fragmented,
        "missing_refs": missing_refs,
        "continuity_state": session.replay_continuity_state,
    }


@router.get("/session/{session_id}/summary")
async def get_session_summary(session_id: str) -> Dict[str, Any]:
    """Get a summary for a replay session."""
    session = get_replay_session(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")

    return build_replay_summary(session)


@router.get("/session/{session_id}/replay")
async def get_observational_replay(session_id: str) -> Dict[str, Any]:
    """
    Get observational replay for a session.

    Returns ordered observations and context.
    Does NOT replay execution or generate machine output.
    """
    session = get_replay_session(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")

    return build_observational_replay(session)


# ============================================================================
# TIMELINE ENDPOINTS
# ============================================================================


class CreateTimelineRequest(BaseModel):
    """Request to create a review timeline."""

    replay_session_id: str
    ordered_observation_ids: Optional[List[str]] = None
    review_state_progression: Optional[List[str]] = None
    topology_risk_progression: Optional[List[str]] = None
    fixture_warning_progression: Optional[List[str]] = None


@router.post("/timeline", response_model=ReviewIntelligenceTimeline)
async def create_timeline(
    request: CreateTimelineRequest,
) -> ReviewIntelligenceTimeline:
    """
    Create and register a review timeline.

    Timelines track observation progression — they do not replay execution.
    """
    timeline = create_review_timeline(
        replay_session_id=request.replay_session_id,
        ordered_observation_ids=request.ordered_observation_ids,
        review_state_progression=request.review_state_progression,
        topology_risk_progression=request.topology_risk_progression,
        fixture_warning_progression=request.fixture_warning_progression,
    )
    return register_review_timeline(timeline)


@router.post("/session/{session_id}/build-timeline", response_model=ReviewIntelligenceTimeline)
async def build_timeline_for_session(session_id: str) -> ReviewIntelligenceTimeline:
    """
    Build and register a timeline from a replay session.

    Automatically populates progressions from session observations.
    """
    session = get_replay_session(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")

    timeline = build_review_timeline(session)
    return register_review_timeline(timeline)


@router.get("/timelines", response_model=List[ReviewIntelligenceTimeline])
async def list_timelines() -> List[ReviewIntelligenceTimeline]:
    """List all review timelines."""
    return list_review_timelines()


@router.get("/timeline/{timeline_id}", response_model=ReviewIntelligenceTimeline)
async def get_timeline(timeline_id: str) -> ReviewIntelligenceTimeline:
    """Get a specific timeline by ID."""
    timeline = get_review_timeline(timeline_id)
    if not timeline:
        raise HTTPException(404, f"Timeline '{timeline_id}' not found")
    return timeline


@router.get(
    "/timelines/by-session/{session_id}",
    response_model=List[ReviewIntelligenceTimeline],
)
async def get_timelines_by_session(
    session_id: str,
) -> List[ReviewIntelligenceTimeline]:
    """List all timelines for a replay session."""
    return list_timelines_by_session(session_id)


@router.post("/timeline/{timeline_id}/validate")
async def validate_timeline_endpoint(timeline_id: str) -> Dict[str, Any]:
    """Validate that a timeline is well-formed."""
    timeline = get_review_timeline(timeline_id)
    if not timeline:
        raise HTTPException(404, f"Timeline '{timeline_id}' not found")

    is_valid, issues = validate_timeline(timeline)

    return {
        "timeline_id": timeline_id,
        "is_valid": is_valid,
        "issues": issues,
        "continuity_state": timeline.continuity_state,
        "observation_count": len(timeline.ordered_observation_ids),
    }


@router.get("/timeline/{timeline_id}/summary")
async def get_timeline_summary_endpoint(timeline_id: str) -> Dict[str, Any]:
    """Get a summary for a timeline."""
    timeline = get_review_timeline(timeline_id)
    if not timeline:
        raise HTTPException(404, f"Timeline '{timeline_id}' not found")

    return get_timeline_summary(timeline)


# ============================================================================
# PACKAGE ENDPOINTS
# ============================================================================


class CreatePackageRequest(BaseModel):
    """Request to create a replay package."""

    replay_session_id: str
    observation_ids: Optional[List[str]] = None
    timeline_id: Optional[str] = None
    provenance_refs: Optional[List[str]] = None
    review_summary: str = ""


@router.post("/package", response_model=ReplaySafeReviewPackage)
async def create_package(
    request: CreatePackageRequest,
) -> ReplaySafeReviewPackage:
    """
    Create and register a replay-safe review package.

    Packages are immutable bundles — they do not replay execution.
    """
    package = create_replay_safe_review_package(
        replay_session_id=request.replay_session_id,
        observation_ids=request.observation_ids,
        timeline_id=request.timeline_id,
        provenance_refs=request.provenance_refs,
        review_summary=request.review_summary,
    )
    return register_replay_safe_review_package(package)


@router.get("/packages", response_model=List[ReplaySafeReviewPackage])
async def list_packages() -> List[ReplaySafeReviewPackage]:
    """List all replay-safe review packages."""
    return list_replay_safe_review_packages()


@router.get("/package/{package_id}", response_model=ReplaySafeReviewPackage)
async def get_package(package_id: str) -> ReplaySafeReviewPackage:
    """Get a specific package by ID."""
    package = get_replay_safe_review_package(package_id)
    if not package:
        raise HTTPException(404, f"Package '{package_id}' not found")
    return package


@router.get(
    "/packages/by-session/{session_id}",
    response_model=List[ReplaySafeReviewPackage],
)
async def get_packages_by_session(
    session_id: str,
) -> List[ReplaySafeReviewPackage]:
    """List all packages for a replay session."""
    return list_packages_by_session(session_id)


@router.post("/package/{package_id}/validate")
async def validate_package_endpoint(package_id: str) -> Dict[str, Any]:
    """Validate that a package is well-formed."""
    package = get_replay_safe_review_package(package_id)
    if not package:
        raise HTTPException(404, f"Package '{package_id}' not found")

    is_valid, issues = validate_replay_safe_review_package(package)

    return {
        "package_id": package_id,
        "is_valid": is_valid,
        "issues": issues,
        "continuity_state": package.continuity_state,
        "immutable": package.immutable,
    }


@router.get("/package/{package_id}/summary")
async def get_package_summary_endpoint(package_id: str) -> Dict[str, Any]:
    """Get a summary for a package."""
    package = get_replay_safe_review_package(package_id)
    if not package:
        raise HTTPException(404, f"Package '{package_id}' not found")

    return get_package_summary(package)


# ============================================================================
# CI ENDPOINT
# ============================================================================


@router.get("/ci")
async def get_ci_status() -> Dict[str, Any]:
    """
    Get CI summary for manufacturing replay intelligence health.

    Returns:
      - total_observations
      - total_sessions
      - total_timelines
      - total_packages
      - critical_observation_count
      - warning_observation_count
      - fragmented_session_count
      - invalid_session_count
      - missing_ref_count
      - status: pass|warn|fail

    Status:
      - fail: any critical observation or invalid session
      - warn: warning observations or fragmented sessions
      - pass: all observations are info and all sessions complete
    """
    return get_ci_summary()
