"""
Manufacturing Replay Registry

CAM Dev Order 7W: In-memory registry for manufacturing replay intelligence.

Provides:
  - Observation registration and lookup
  - Replay session registration and lookup
  - Timeline registration and lookup
  - Replay package registration and lookup
  - CI summary generation
  - Continuity validation

7W invariants:
  - No registered artifact may authorize execution
  - No registered artifact may allow machine output
  - No registered artifact may replay execution
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from app.cam.manufacturing_review_observation import (
    ManufacturingReviewObservation,
    validate_observation,
)
from app.cam.manufacturing_replay_session import (
    ManufacturingReplaySession,
    validate_replay_session,
    mark_missing_refs_detected,
    mark_fragmented_replay_detected,
    update_continuity_state,
)
from app.cam.review_intelligence_timeline import (
    ReviewIntelligenceTimeline,
    validate_timeline,
)
from app.cam.replay_safe_review_package import (
    ReplaySafeReviewPackage,
    validate_replay_safe_review_package,
)


# Primary indexes
MANUFACTURING_REVIEW_OBSERVATION_INDEX: Dict[str, ManufacturingReviewObservation] = {}
MANUFACTURING_REPLAY_SESSION_INDEX: Dict[str, ManufacturingReplaySession] = {}
REVIEW_INTELLIGENCE_TIMELINE_INDEX: Dict[str, ReviewIntelligenceTimeline] = {}
REPLAY_SAFE_REVIEW_PACKAGE_INDEX: Dict[str, ReplaySafeReviewPackage] = {}

# Secondary indexes by workspace
OBSERVATIONS_BY_WORKSPACE_INDEX: Dict[str, List[str]] = {}
SESSIONS_BY_WORKSPACE_INDEX: Dict[str, List[str]] = {}
PACKAGES_BY_WORKSPACE_INDEX: Dict[str, List[str]] = {}

# Secondary indexes by strategy
OBSERVATIONS_BY_STRATEGY_INDEX: Dict[str, List[str]] = {}
SESSIONS_BY_STRATEGY_INDEX: Dict[str, List[str]] = {}
PACKAGES_BY_STRATEGY_INDEX: Dict[str, List[str]] = {}

# Secondary indexes by session
TIMELINES_BY_SESSION_INDEX: Dict[str, List[str]] = {}
PACKAGES_BY_SESSION_INDEX: Dict[str, List[str]] = {}


# ============================================================================
# OBSERVATION REGISTRATION
# ============================================================================


def register_review_observation(
    observation: ManufacturingReviewObservation,
) -> ManufacturingReviewObservation:
    """
    Register a manufacturing review observation.

    Args:
        observation: Observation to register

    Returns:
        The registered observation
    """
    observation.deterministic_observation_hash = observation.compute_hash()

    MANUFACTURING_REVIEW_OBSERVATION_INDEX[observation.observation_id] = observation

    if observation.workspace_id:
        if observation.workspace_id not in OBSERVATIONS_BY_WORKSPACE_INDEX:
            OBSERVATIONS_BY_WORKSPACE_INDEX[observation.workspace_id] = []
        if observation.observation_id not in OBSERVATIONS_BY_WORKSPACE_INDEX[observation.workspace_id]:
            OBSERVATIONS_BY_WORKSPACE_INDEX[observation.workspace_id].append(observation.observation_id)

    if observation.strategy_id:
        if observation.strategy_id not in OBSERVATIONS_BY_STRATEGY_INDEX:
            OBSERVATIONS_BY_STRATEGY_INDEX[observation.strategy_id] = []
        if observation.observation_id not in OBSERVATIONS_BY_STRATEGY_INDEX[observation.strategy_id]:
            OBSERVATIONS_BY_STRATEGY_INDEX[observation.strategy_id].append(observation.observation_id)

    return observation


def get_review_observation(
    observation_id: str,
) -> Optional[ManufacturingReviewObservation]:
    """Get a review observation by ID."""
    return MANUFACTURING_REVIEW_OBSERVATION_INDEX.get(observation_id)


def list_review_observations() -> List[ManufacturingReviewObservation]:
    """List all registered review observations."""
    return list(MANUFACTURING_REVIEW_OBSERVATION_INDEX.values())


def list_observations_by_workspace(
    workspace_id: str,
) -> List[ManufacturingReviewObservation]:
    """List all observations for a workspace."""
    obs_ids = OBSERVATIONS_BY_WORKSPACE_INDEX.get(workspace_id, [])
    return [
        MANUFACTURING_REVIEW_OBSERVATION_INDEX[oid]
        for oid in obs_ids
        if oid in MANUFACTURING_REVIEW_OBSERVATION_INDEX
    ]


def list_observations_by_strategy(
    strategy_id: str,
) -> List[ManufacturingReviewObservation]:
    """List all observations for a strategy."""
    obs_ids = OBSERVATIONS_BY_STRATEGY_INDEX.get(strategy_id, [])
    return [
        MANUFACTURING_REVIEW_OBSERVATION_INDEX[oid]
        for oid in obs_ids
        if oid in MANUFACTURING_REVIEW_OBSERVATION_INDEX
    ]


def list_observations_by_category(
    category: str,
) -> List[ManufacturingReviewObservation]:
    """List all observations with a specific category."""
    return [
        obs for obs in MANUFACTURING_REVIEW_OBSERVATION_INDEX.values()
        if obs.observation_category == category
    ]


def list_observations_by_severity(
    severity: str,
) -> List[ManufacturingReviewObservation]:
    """List all observations with a specific severity."""
    return [
        obs for obs in MANUFACTURING_REVIEW_OBSERVATION_INDEX.values()
        if obs.severity == severity
    ]


# ============================================================================
# REPLAY SESSION REGISTRATION
# ============================================================================


def register_replay_session(
    session: ManufacturingReplaySession,
) -> ManufacturingReplaySession:
    """
    Register a manufacturing replay session.

    Args:
        session: Session to register

    Returns:
        The registered session
    """
    session.deterministic_replay_hash = session.compute_hash()

    MANUFACTURING_REPLAY_SESSION_INDEX[session.replay_session_id] = session

    if session.workspace_id:
        if session.workspace_id not in SESSIONS_BY_WORKSPACE_INDEX:
            SESSIONS_BY_WORKSPACE_INDEX[session.workspace_id] = []
        if session.replay_session_id not in SESSIONS_BY_WORKSPACE_INDEX[session.workspace_id]:
            SESSIONS_BY_WORKSPACE_INDEX[session.workspace_id].append(session.replay_session_id)

    if session.strategy_id:
        if session.strategy_id not in SESSIONS_BY_STRATEGY_INDEX:
            SESSIONS_BY_STRATEGY_INDEX[session.strategy_id] = []
        if session.replay_session_id not in SESSIONS_BY_STRATEGY_INDEX[session.strategy_id]:
            SESSIONS_BY_STRATEGY_INDEX[session.strategy_id].append(session.replay_session_id)

    return session


def get_replay_session(
    session_id: str,
) -> Optional[ManufacturingReplaySession]:
    """Get a replay session by ID."""
    return MANUFACTURING_REPLAY_SESSION_INDEX.get(session_id)


def list_replay_sessions() -> List[ManufacturingReplaySession]:
    """List all registered replay sessions."""
    return list(MANUFACTURING_REPLAY_SESSION_INDEX.values())


def list_sessions_by_workspace(
    workspace_id: str,
) -> List[ManufacturingReplaySession]:
    """List all sessions for a workspace."""
    session_ids = SESSIONS_BY_WORKSPACE_INDEX.get(workspace_id, [])
    return [
        MANUFACTURING_REPLAY_SESSION_INDEX[sid]
        for sid in session_ids
        if sid in MANUFACTURING_REPLAY_SESSION_INDEX
    ]


def list_sessions_by_strategy(
    strategy_id: str,
) -> List[ManufacturingReplaySession]:
    """List all sessions for a strategy."""
    session_ids = SESSIONS_BY_STRATEGY_INDEX.get(strategy_id, [])
    return [
        MANUFACTURING_REPLAY_SESSION_INDEX[sid]
        for sid in session_ids
        if sid in MANUFACTURING_REPLAY_SESSION_INDEX
    ]


def list_sessions_by_continuity_state(
    continuity_state: str,
) -> List[ManufacturingReplaySession]:
    """List all sessions with a specific continuity state."""
    return [
        session for session in MANUFACTURING_REPLAY_SESSION_INDEX.values()
        if session.replay_continuity_state == continuity_state
    ]


# ============================================================================
# TIMELINE REGISTRATION
# ============================================================================


def register_review_timeline(
    timeline: ReviewIntelligenceTimeline,
) -> ReviewIntelligenceTimeline:
    """
    Register a review intelligence timeline.

    Args:
        timeline: Timeline to register

    Returns:
        The registered timeline
    """
    timeline.deterministic_timeline_hash = timeline.compute_hash()

    REVIEW_INTELLIGENCE_TIMELINE_INDEX[timeline.timeline_id] = timeline

    if timeline.replay_session_id:
        if timeline.replay_session_id not in TIMELINES_BY_SESSION_INDEX:
            TIMELINES_BY_SESSION_INDEX[timeline.replay_session_id] = []
        if timeline.timeline_id not in TIMELINES_BY_SESSION_INDEX[timeline.replay_session_id]:
            TIMELINES_BY_SESSION_INDEX[timeline.replay_session_id].append(timeline.timeline_id)

    return timeline


def get_review_timeline(
    timeline_id: str,
) -> Optional[ReviewIntelligenceTimeline]:
    """Get a review timeline by ID."""
    return REVIEW_INTELLIGENCE_TIMELINE_INDEX.get(timeline_id)


def list_review_timelines() -> List[ReviewIntelligenceTimeline]:
    """List all registered review timelines."""
    return list(REVIEW_INTELLIGENCE_TIMELINE_INDEX.values())


def list_timelines_by_session(
    session_id: str,
) -> List[ReviewIntelligenceTimeline]:
    """List all timelines for a replay session."""
    timeline_ids = TIMELINES_BY_SESSION_INDEX.get(session_id, [])
    return [
        REVIEW_INTELLIGENCE_TIMELINE_INDEX[tid]
        for tid in timeline_ids
        if tid in REVIEW_INTELLIGENCE_TIMELINE_INDEX
    ]


# ============================================================================
# REPLAY PACKAGE REGISTRATION
# ============================================================================


def register_replay_safe_review_package(
    package: ReplaySafeReviewPackage,
) -> ReplaySafeReviewPackage:
    """
    Register a replay-safe review package.

    Args:
        package: Package to register

    Returns:
        The registered package
    """
    package.deterministic_package_hash = package.compute_hash()

    REPLAY_SAFE_REVIEW_PACKAGE_INDEX[package.package_id] = package

    if package.replay_session_id:
        if package.replay_session_id not in PACKAGES_BY_SESSION_INDEX:
            PACKAGES_BY_SESSION_INDEX[package.replay_session_id] = []
        if package.package_id not in PACKAGES_BY_SESSION_INDEX[package.replay_session_id]:
            PACKAGES_BY_SESSION_INDEX[package.replay_session_id].append(package.package_id)

    return package


def get_replay_safe_review_package(
    package_id: str,
) -> Optional[ReplaySafeReviewPackage]:
    """Get a replay-safe review package by ID."""
    return REPLAY_SAFE_REVIEW_PACKAGE_INDEX.get(package_id)


def list_replay_safe_review_packages() -> List[ReplaySafeReviewPackage]:
    """List all registered replay-safe review packages."""
    return list(REPLAY_SAFE_REVIEW_PACKAGE_INDEX.values())


def list_packages_by_session(
    session_id: str,
) -> List[ReplaySafeReviewPackage]:
    """List all packages for a replay session."""
    pkg_ids = PACKAGES_BY_SESSION_INDEX.get(session_id, [])
    return [
        REPLAY_SAFE_REVIEW_PACKAGE_INDEX[pid]
        for pid in pkg_ids
        if pid in REPLAY_SAFE_REVIEW_PACKAGE_INDEX
    ]


def list_packages_by_continuity_state(
    continuity_state: str,
) -> List[ReplaySafeReviewPackage]:
    """List all packages with a specific continuity state."""
    return [
        pkg for pkg in REPLAY_SAFE_REVIEW_PACKAGE_INDEX.values()
        if pkg.continuity_state == continuity_state
    ]


# ============================================================================
# CONTINUITY VALIDATION
# ============================================================================


def validate_replay_continuity(
    session: ManufacturingReplaySession,
) -> tuple[bool, List[str]]:
    """
    Validate replay continuity for a session.

    Checks that all referenced IDs can be resolved.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    # Check observation refs
    for obs_id in session.observation_ids:
        if obs_id not in MANUFACTURING_REVIEW_OBSERVATION_INDEX:
            issues.append(f"Missing observation reference: {obs_id}")

    # Check fixture package refs
    for pkg_id in session.fixture_package_ids:
        try:
            from app.cam.fixture_topology_registry import get_review_safe_fixture_package
            if not get_review_safe_fixture_package(pkg_id):
                issues.append(f"Missing fixture package reference: {pkg_id}")
        except ImportError:
            pass

    # Check export package refs
    for pkg_id in session.export_package_ids:
        try:
            from app.cam.strategy_export_registry import get_review_safe_export_package
            if not get_review_safe_export_package(pkg_id):
                issues.append(f"Missing export package reference: {pkg_id}")
        except ImportError:
            pass

    return len(issues) == 0, issues


def detect_fragmented_replay(
    session: ManufacturingReplaySession,
) -> tuple[bool, List[str]]:
    """
    Detect fragmented replay in a session.

    A replay is fragmented if:
      - Referenced observation IDs are missing
      - Referenced fixture/export packages are missing
      - Expected linkage is incomplete

    Returns:
        (is_fragmented, missing_refs)
    """
    missing_refs: List[str] = []

    # Check observation refs
    for obs_id in session.observation_ids:
        if obs_id not in MANUFACTURING_REVIEW_OBSERVATION_INDEX:
            missing_refs.append(f"observation:{obs_id}")

    # Check fixture package refs
    for pkg_id in session.fixture_package_ids:
        try:
            from app.cam.fixture_topology_registry import get_review_safe_fixture_package
            if not get_review_safe_fixture_package(pkg_id):
                missing_refs.append(f"fixture_package:{pkg_id}")
        except ImportError:
            pass

    # Check export package refs
    for pkg_id in session.export_package_ids:
        try:
            from app.cam.strategy_export_registry import get_review_safe_export_package
            if not get_review_safe_export_package(pkg_id):
                missing_refs.append(f"export_package:{pkg_id}")
        except ImportError:
            pass

    return len(missing_refs) > 0, missing_refs


def detect_missing_replay_refs(
    session: ManufacturingReplaySession,
) -> List[str]:
    """
    Detect missing references in a replay session.

    Returns list of missing reference IDs.
    """
    _, missing = detect_fragmented_replay(session)
    return missing


def validate_observation_provenance(
    observation: ManufacturingReviewObservation,
) -> tuple[bool, List[str]]:
    """
    Validate observation provenance.

    Checks that provenance refs can be resolved where applicable.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    # Check fixture package ref
    if observation.fixture_package_id:
        try:
            from app.cam.fixture_topology_registry import get_review_safe_fixture_package
            if not get_review_safe_fixture_package(observation.fixture_package_id):
                issues.append(f"Missing fixture package: {observation.fixture_package_id}")
        except ImportError:
            pass

    # Check export package ref
    if observation.export_package_id:
        try:
            from app.cam.strategy_export_registry import get_review_safe_export_package
            if not get_review_safe_export_package(observation.export_package_id):
                issues.append(f"Missing export package: {observation.export_package_id}")
        except ImportError:
            pass

    return len(issues) == 0, issues


def validate_replay_package_integrity(
    package: ReplaySafeReviewPackage,
) -> tuple[bool, List[str]]:
    """
    Validate replay package integrity.

    Checks that all package references can be resolved.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    # Check session ref
    if package.replay_session_id not in MANUFACTURING_REPLAY_SESSION_INDEX:
        issues.append(f"Missing replay session: {package.replay_session_id}")

    # Check observation refs
    for obs_id in package.observation_ids:
        if obs_id not in MANUFACTURING_REVIEW_OBSERVATION_INDEX:
            issues.append(f"Missing observation: {obs_id}")

    # Check timeline ref
    if package.timeline_id and package.timeline_id not in REVIEW_INTELLIGENCE_TIMELINE_INDEX:
        issues.append(f"Missing timeline: {package.timeline_id}")

    return len(issues) == 0, issues


# ============================================================================
# REPLAY BUILDING
# ============================================================================


def build_review_timeline(
    session: ManufacturingReplaySession,
) -> ReviewIntelligenceTimeline:
    """
    Build a review timeline from a replay session.

    Collects observations and constructs ordered timeline.
    """
    from app.cam.review_intelligence_timeline import create_review_timeline

    timeline = create_review_timeline(
        replay_session_id=session.replay_session_id,
        ordered_observation_ids=list(session.observation_ids),
    )

    # Populate progression from observations
    for obs_id in session.observation_ids:
        obs = get_review_observation(obs_id)
        if obs:
            if obs.observation_category == "topology_warning":
                timeline.topology_risk_progression.append(obs.observation_text)
            elif obs.observation_category == "fixture_warning":
                timeline.fixture_warning_progression.append(obs.observation_text)

    timeline.deterministic_timeline_hash = timeline.compute_hash()
    return timeline


def build_replay_summary(
    session: ManufacturingReplaySession,
) -> Dict[str, Any]:
    """
    Build a summary for a replay session.

    Returns:
        Summary dictionary with counts and states
    """
    is_fragmented, missing_refs = detect_fragmented_replay(session)

    observations = [
        get_review_observation(oid)
        for oid in session.observation_ids
    ]
    observations = [o for o in observations if o is not None]

    critical_count = sum(1 for o in observations if o.severity == "critical")
    warning_count = sum(1 for o in observations if o.severity == "warning")
    info_count = sum(1 for o in observations if o.severity == "info")

    topology_warnings = sum(1 for o in observations if o.observation_category == "topology_warning")
    fixture_warnings = sum(1 for o in observations if o.observation_category == "fixture_warning")

    return {
        "replay_session_id": session.replay_session_id,
        "workspace_id": session.workspace_id,
        "strategy_id": session.strategy_id,
        "observation_count": len(session.observation_ids),
        "resolved_observation_count": len(observations),
        "topology_evaluation_count": len(session.topology_evaluation_ids),
        "fixture_package_count": len(session.fixture_package_ids),
        "export_package_count": len(session.export_package_ids),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "topology_warning_count": topology_warnings,
        "fixture_warning_count": fixture_warnings,
        "continuity_state": session.replay_continuity_state,
        "is_fragmented": is_fragmented,
        "missing_ref_count": len(missing_refs),
        "blocking_issue_count": len(session.blocking_issues),
        "warning_notification_count": len(session.warnings),
    }


def build_observational_replay(
    session: ManufacturingReplaySession,
) -> Dict[str, Any]:
    """
    Build an observational replay from a session.

    Returns a dictionary with ordered observations and context.
    Does NOT replay execution or generate machine output.
    """
    observations = []
    for obs_id in session.observation_ids:
        obs = get_review_observation(obs_id)
        if obs:
            observations.append({
                "observation_id": obs.observation_id,
                "category": obs.observation_category,
                "severity": obs.severity,
                "text": obs.observation_text,
                "workspace_id": obs.workspace_id,
                "strategy_id": obs.strategy_id,
                "fixture_package_id": obs.fixture_package_id,
                "export_package_id": obs.export_package_id,
            })

    return {
        "replay_session_id": session.replay_session_id,
        "workspace_id": session.workspace_id,
        "strategy_id": session.strategy_id,
        "observations": observations,
        "topology_evaluation_ids": session.topology_evaluation_ids,
        "fixture_package_ids": session.fixture_package_ids,
        "export_package_ids": session.export_package_ids,
        "continuity_state": session.replay_continuity_state,
        "replay_execution_present": False,
        "machine_output_allowed": False,
        "execution_authorized": False,
    }


# ============================================================================
# CI SUMMARY
# ============================================================================


CIStatus = Literal["pass", "warn", "fail"]


class ManufacturingReplayCISummary(Dict[str, Any]):
    """CI summary for manufacturing replay intelligence health."""
    pass


def get_ci_summary() -> ManufacturingReplayCISummary:
    """
    Generate CI summary for manufacturing replay intelligence health.

    Returns summary with:
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
    total_observations = len(MANUFACTURING_REVIEW_OBSERVATION_INDEX)
    total_sessions = len(MANUFACTURING_REPLAY_SESSION_INDEX)
    total_timelines = len(REVIEW_INTELLIGENCE_TIMELINE_INDEX)
    total_packages = len(REPLAY_SAFE_REVIEW_PACKAGE_INDEX)

    critical_count = 0
    warning_count = 0
    info_count = 0

    for obs in MANUFACTURING_REVIEW_OBSERVATION_INDEX.values():
        if obs.severity == "critical":
            critical_count += 1
        elif obs.severity == "warning":
            warning_count += 1
        else:
            info_count += 1

    complete_count = 0
    partial_count = 0
    fragmented_count = 0
    invalid_count = 0
    total_missing_refs = 0

    for session in MANUFACTURING_REPLAY_SESSION_INDEX.values():
        if session.replay_continuity_state == "complete":
            complete_count += 1
        elif session.replay_continuity_state == "partial":
            partial_count += 1
        elif session.replay_continuity_state == "fragmented":
            fragmented_count += 1
        elif session.replay_continuity_state == "invalid":
            invalid_count += 1

        _, missing = detect_fragmented_replay(session)
        total_missing_refs += len(missing)

    status: CIStatus
    if critical_count > 0 or invalid_count > 0:
        status = "fail"
    elif warning_count > 0 or fragmented_count > 0:
        status = "warn"
    else:
        status = "pass"

    observations_by_category: Dict[str, int] = {}
    for obs in MANUFACTURING_REVIEW_OBSERVATION_INDEX.values():
        cat = obs.observation_category
        observations_by_category[cat] = observations_by_category.get(cat, 0) + 1

    observations_by_severity = {
        "critical": critical_count,
        "warning": warning_count,
        "info": info_count,
    }

    sessions_by_continuity_state = {
        "complete": complete_count,
        "partial": partial_count,
        "fragmented": fragmented_count,
        "invalid": invalid_count,
    }

    return ManufacturingReplayCISummary(
        total_observations=total_observations,
        total_sessions=total_sessions,
        total_timelines=total_timelines,
        total_packages=total_packages,
        critical_observation_count=critical_count,
        warning_observation_count=warning_count,
        info_observation_count=info_count,
        complete_session_count=complete_count,
        partial_session_count=partial_count,
        fragmented_session_count=fragmented_count,
        invalid_session_count=invalid_count,
        missing_ref_count=total_missing_refs,
        observations_by_category=observations_by_category,
        observations_by_severity=observations_by_severity,
        sessions_by_continuity_state=sessions_by_continuity_state,
        status=status,
    )


# ============================================================================
# INDEX CLEARING (FOR TESTING)
# ============================================================================


def clear_manufacturing_replay_indexes_for_tests() -> None:
    """Clear all indexes (for testing)."""
    MANUFACTURING_REVIEW_OBSERVATION_INDEX.clear()
    MANUFACTURING_REPLAY_SESSION_INDEX.clear()
    REVIEW_INTELLIGENCE_TIMELINE_INDEX.clear()
    REPLAY_SAFE_REVIEW_PACKAGE_INDEX.clear()
    OBSERVATIONS_BY_WORKSPACE_INDEX.clear()
    SESSIONS_BY_WORKSPACE_INDEX.clear()
    PACKAGES_BY_WORKSPACE_INDEX.clear()
    OBSERVATIONS_BY_STRATEGY_INDEX.clear()
    SESSIONS_BY_STRATEGY_INDEX.clear()
    PACKAGES_BY_STRATEGY_INDEX.clear()
    TIMELINES_BY_SESSION_INDEX.clear()
    PACKAGES_BY_SESSION_INDEX.clear()
