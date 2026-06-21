"""
Manufacturing Replay Intelligence Tests

CAM Dev Order 7W: Comprehensive test suite for observational manufacturing replay.

Test categories:
  - Observation Tests: review observation model and functions
  - Replay Session Tests: replay session model and continuity
  - Timeline Tests: review timeline model and progression
  - Package Tests: replay-safe review package model
  - Invariant Tests: 7W model-enforced constraints
  - Registry Tests: index operations and lookup
  - Continuity Tests: fragmentation detection and validation
  - CI Summary Tests: CI health reporting
  - Router Tests: HTTP endpoints

Target: 80+ tests
"""

import pytest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.cam.manufacturing_review_observation import (
    ManufacturingReviewObservation,
    ReviewObservationCategory,
    ObservationSeverity,
    create_review_observation,
    create_topology_warning,
    create_fixture_warning,
    create_export_review_note,
    create_review_rationale,
    create_provenance_warning,
    add_provenance_ref_to_observation,
    add_geometry_authority_ref_to_observation,
    validate_observation,
    build_observation_hash,
    is_critical_observation,
    is_warning_observation,
    requires_immediate_review,
)
from app.cam.manufacturing_replay_session import (
    ManufacturingReplaySession,
    ReplayContinuityState,
    create_replay_session,
    add_observation_to_session,
    add_topology_evaluation_to_session,
    add_fixture_package_to_session,
    add_export_package_to_session,
    add_blocking_issue_to_session,
    add_warning_to_session,
    mark_missing_refs_detected,
    mark_fragmented_replay_detected,
    update_continuity_state,
    validate_replay_session,
    is_replay_complete,
    is_replay_fragmented,
    build_replay_session_hash,
    get_session_ref_counts,
)
from app.cam.review_intelligence_timeline import (
    ReviewIntelligenceTimeline,
    create_review_timeline,
    append_observation_to_timeline,
    append_review_state_to_timeline,
    append_topology_risk_to_timeline,
    append_fixture_warning_to_timeline,
    update_timeline_continuity_state,
    validate_timeline,
    is_timeline_complete,
    get_timeline_length,
    get_latest_review_state,
    get_latest_topology_risk,
    get_latest_fixture_warning,
    has_topology_risks,
    has_fixture_warnings,
    build_timeline_hash,
    get_timeline_summary,
)
from app.cam.replay_safe_review_package import (
    ReplaySafeReviewPackage,
    create_replay_safe_review_package,
    add_observation_to_package,
    add_provenance_ref_to_package,
    add_warning_to_package,
    add_blocking_issue_to_package,
    set_timeline_for_package,
    update_review_summary,
    update_continuity_state as update_package_continuity_state,
    validate_replay_safe_review_package,
    is_package_complete,
    is_package_valid_for_review,
    build_replay_package_hash,
    get_package_summary,
)
from app.cam.manufacturing_replay_registry import (
    MANUFACTURING_REVIEW_OBSERVATION_INDEX,
    MANUFACTURING_REPLAY_SESSION_INDEX,
    REVIEW_INTELLIGENCE_TIMELINE_INDEX,
    REPLAY_SAFE_REVIEW_PACKAGE_INDEX,
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
    detect_missing_replay_refs,
    validate_observation_provenance,
    validate_replay_package_integrity,
    build_review_timeline,
    build_replay_summary,
    build_observational_replay,
    get_ci_summary,
    clear_manufacturing_replay_indexes_for_tests,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear all indexes before each test."""
    clear_manufacturing_replay_indexes_for_tests()
    yield
    clear_manufacturing_replay_indexes_for_tests()


# ============================================================================
# OBSERVATION TESTS (15 tests)
# ============================================================================


class TestManufacturingReviewObservation:
    """Tests for review observation model."""

    def test_create_observation_with_category(self):
        """Observation created with category."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test warning",
            workspace_id="ws-123",
        )
        assert obs.observation_category == "topology_warning"
        assert obs.observation_text == "Test warning"
        assert obs.workspace_id == "ws-123"

    def test_create_topology_warning(self):
        """Topology warning helper creates correct observation."""
        obs = create_topology_warning(
            observation_text="Topology risk detected",
            workspace_id="ws-123",
        )
        assert obs.observation_category == "topology_warning"
        assert obs.severity == "warning"

    def test_create_fixture_warning(self):
        """Fixture warning helper creates correct observation."""
        obs = create_fixture_warning(
            observation_text="Fixture conflict detected",
            workspace_id="ws-123",
        )
        assert obs.observation_category == "fixture_warning"
        assert obs.severity == "warning"

    def test_create_export_review_note(self):
        """Export review note helper creates correct observation."""
        obs = create_export_review_note(
            observation_text="Export ready for review",
            workspace_id="ws-123",
        )
        assert obs.observation_category == "export_review_note"
        assert obs.severity == "info"

    def test_create_review_rationale(self):
        """Review rationale helper creates correct observation."""
        obs = create_review_rationale(
            observation_text="Approved because of spec compliance",
            workspace_id="ws-123",
        )
        assert obs.observation_category == "review_rationale"

    def test_create_provenance_warning(self):
        """Provenance warning helper creates correct observation."""
        obs = create_provenance_warning(
            observation_text="Provenance chain incomplete",
            workspace_id="ws-123",
        )
        assert obs.observation_category == "provenance_warning"
        assert obs.severity == "warning"

    def test_observation_has_unique_id(self):
        """Each observation has unique ID."""
        obs1 = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test 1",
            workspace_id="ws-1",
        )
        obs2 = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test 2",
            workspace_id="ws-2",
        )
        assert obs1.observation_id != obs2.observation_id
        assert obs1.observation_id.startswith("mro-")

    def test_observation_has_timestamp(self):
        """Observation has timestamp."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        assert obs.created_at is not None
        assert isinstance(obs.created_at, datetime)

    def test_observation_has_hash(self):
        """Observation has deterministic hash."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        assert obs.deterministic_observation_hash != ""
        assert len(obs.deterministic_observation_hash) == 64

    def test_add_provenance_ref(self):
        """Can add provenance ref to observation."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        original_hash = obs.deterministic_observation_hash
        add_provenance_ref_to_observation(obs, "prov-ref-1")
        assert "prov-ref-1" in obs.provenance_refs
        assert obs.deterministic_observation_hash != original_hash

    def test_add_geometry_authority_ref(self):
        """Can add geometry authority ref to observation."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        add_geometry_authority_ref_to_observation(obs, "geo-auth-1")
        assert "geo-auth-1" in obs.geometry_authority_ref_ids

    def test_validate_observation_valid(self):
        """Valid observation passes validation."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test warning",
            workspace_id="ws-123",
        )
        is_valid, issues = validate_observation(obs)
        assert is_valid is True
        assert len(issues) == 0

    def test_is_critical_observation(self):
        """Critical observation detected correctly."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Critical issue",
            workspace_id="ws-123",
            severity="critical",
        )
        assert is_critical_observation(obs) is True
        assert is_warning_observation(obs) is False

    def test_requires_immediate_review(self):
        """Critical observation requires immediate review."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Critical issue",
            workspace_id="ws-123",
            severity="critical",
            review_required=True,
        )
        assert requires_immediate_review(obs) is True

    def test_observation_hash_stable(self):
        """Hash is stable for same input."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        hash1 = build_observation_hash(obs)
        hash2 = build_observation_hash(obs)
        assert hash1 == hash2


# ============================================================================
# OBSERVATION INVARIANT TESTS (5 tests)
# ============================================================================


class TestObservationInvariants:
    """Tests for 7W observation invariants."""

    def test_execution_authorized_must_be_false(self):
        """execution_authorized must be False."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            ManufacturingReviewObservation(
                observation_category="topology_warning",
                observation_text="Test",
                execution_authorized=True,
            )

    def test_machine_output_allowed_must_be_false(self):
        """machine_output_allowed must be False."""
        with pytest.raises(ValueError, match="machine_output_allowed must be False"):
            ManufacturingReviewObservation(
                observation_category="topology_warning",
                observation_text="Test",
                machine_output_allowed=True,
            )

    def test_modifies_geometry_authority_must_be_false(self):
        """modifies_geometry_authority must be False."""
        with pytest.raises(ValueError, match="modifies_geometry_authority must be False"):
            ManufacturingReviewObservation(
                observation_category="topology_warning",
                observation_text="Test",
                modifies_geometry_authority=True,
            )

    def test_default_invariants_are_false(self):
        """Default invariants are False."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        assert obs.execution_authorized is False
        assert obs.machine_output_allowed is False
        assert obs.modifies_geometry_authority is False

    def test_validation_rejects_invalid_invariants(self):
        """Validation catches invariant violations."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        obs.execution_authorized = True
        obs.__dict__["execution_authorized"] = True
        is_valid, issues = validate_observation(obs)
        assert is_valid is False
        assert "execution_authorized must be False" in issues


# ============================================================================
# REPLAY SESSION TESTS (15 tests)
# ============================================================================


class TestManufacturingReplaySession:
    """Tests for replay session model."""

    def test_create_session_with_workspace(self):
        """Session created with workspace."""
        session = create_replay_session(
            workspace_id="ws-123",
        )
        assert session.workspace_id == "ws-123"
        assert session.replay_session_id.startswith("mrs-")

    def test_create_session_with_observation_ids(self):
        """Session created with observation IDs."""
        session = create_replay_session(
            workspace_id="ws-123",
            observation_ids=["obs-1", "obs-2"],
        )
        assert "obs-1" in session.observation_ids
        assert "obs-2" in session.observation_ids

    def test_add_observation_to_session(self):
        """Can add observation to session."""
        session = create_replay_session(workspace_id="ws-123")
        add_observation_to_session(session, "obs-1")
        assert "obs-1" in session.observation_ids

    def test_add_observation_deduplicates(self):
        """Adding same observation twice doesn't duplicate."""
        session = create_replay_session(workspace_id="ws-123")
        add_observation_to_session(session, "obs-1")
        add_observation_to_session(session, "obs-1")
        assert session.observation_ids.count("obs-1") == 1

    def test_add_fixture_package_to_session(self):
        """Can add fixture package to session."""
        session = create_replay_session(workspace_id="ws-123")
        add_fixture_package_to_session(session, "fix-pkg-1")
        assert "fix-pkg-1" in session.fixture_package_ids

    def test_add_export_package_to_session(self):
        """Can add export package to session."""
        session = create_replay_session(workspace_id="ws-123")
        add_export_package_to_session(session, "export-pkg-1")
        assert "export-pkg-1" in session.export_package_ids

    def test_add_blocking_issue(self):
        """Can add blocking issue to session."""
        session = create_replay_session(workspace_id="ws-123")
        add_blocking_issue_to_session(session, "Missing provenance")
        assert "Missing provenance" in session.blocking_issues

    def test_mark_missing_refs_detected(self):
        """Can mark missing refs detected."""
        session = create_replay_session(workspace_id="ws-123")
        mark_missing_refs_detected(session)
        assert session.missing_refs_detected is True
        assert session.continuity_integrity_valid is False

    def test_mark_fragmented_replay_detected(self):
        """Can mark fragmented replay detected."""
        session = create_replay_session(workspace_id="ws-123")
        mark_fragmented_replay_detected(session)
        assert session.fragmented_replay_detected is True
        assert session.replay_continuity_state == "fragmented"

    def test_update_continuity_state(self):
        """Can update continuity state."""
        session = create_replay_session(workspace_id="ws-123")
        update_continuity_state(session, "complete")
        assert session.replay_continuity_state == "complete"

    def test_session_has_unique_id(self):
        """Each session has unique ID."""
        session1 = create_replay_session(workspace_id="ws-1")
        session2 = create_replay_session(workspace_id="ws-2")
        assert session1.replay_session_id != session2.replay_session_id

    def test_session_has_hash(self):
        """Session has deterministic hash."""
        session = create_replay_session(workspace_id="ws-123")
        assert session.deterministic_replay_hash != ""
        assert len(session.deterministic_replay_hash) == 64

    def test_is_replay_complete(self):
        """Replay completeness check works."""
        session = create_replay_session(workspace_id="ws-123")
        session.replay_continuity_state = "complete"
        session.continuity_integrity_valid = True
        assert is_replay_complete(session) is True

    def test_is_replay_fragmented(self):
        """Replay fragmentation check works."""
        session = create_replay_session(workspace_id="ws-123")
        mark_fragmented_replay_detected(session)
        assert is_replay_fragmented(session) is True

    def test_get_session_ref_counts(self):
        """Can get reference counts for session."""
        session = create_replay_session(
            workspace_id="ws-123",
            observation_ids=["obs-1", "obs-2"],
            fixture_package_ids=["fix-1"],
        )
        counts = get_session_ref_counts(session)
        assert counts["observation_count"] == 2
        assert counts["fixture_package_count"] == 1


# ============================================================================
# SESSION INVARIANT TESTS (5 tests)
# ============================================================================


class TestSessionInvariants:
    """Tests for 7W session invariants."""

    def test_replay_execution_present_must_be_false(self):
        """replay_execution_present must be False."""
        with pytest.raises(ValueError, match="replay_execution_present must be False"):
            ManufacturingReplaySession(
                replay_execution_present=True,
            )

    def test_machine_output_allowed_must_be_false(self):
        """machine_output_allowed must be False."""
        with pytest.raises(ValueError, match="machine_output_allowed must be False"):
            ManufacturingReplaySession(
                machine_output_allowed=True,
            )

    def test_execution_authorized_must_be_false(self):
        """execution_authorized must be False."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            ManufacturingReplaySession(
                execution_authorized=True,
            )

    def test_default_invariants_are_false(self):
        """Default invariants are False."""
        session = create_replay_session(workspace_id="ws-123")
        assert session.replay_execution_present is False
        assert session.machine_output_allowed is False
        assert session.execution_authorized is False

    def test_validate_session_valid(self):
        """Valid session passes validation."""
        session = create_replay_session(workspace_id="ws-123")
        add_observation_to_session(session, "obs-1")
        is_valid, issues = validate_replay_session(session)
        assert is_valid is True


# ============================================================================
# TIMELINE TESTS (12 tests)
# ============================================================================


class TestReviewIntelligenceTimeline:
    """Tests for review timeline model."""

    def test_create_timeline(self):
        """Timeline created with session ID."""
        timeline = create_review_timeline(
            replay_session_id="mrs-123",
        )
        assert timeline.replay_session_id == "mrs-123"
        assert timeline.timeline_id.startswith("rit-")

    def test_create_timeline_with_observations(self):
        """Timeline created with observation IDs."""
        timeline = create_review_timeline(
            replay_session_id="mrs-123",
            ordered_observation_ids=["obs-1", "obs-2"],
        )
        assert timeline.ordered_observation_ids == ["obs-1", "obs-2"]

    def test_append_observation(self):
        """Can append observation to timeline."""
        timeline = create_review_timeline(replay_session_id="mrs-123")
        append_observation_to_timeline(timeline, "obs-1")
        assert "obs-1" in timeline.ordered_observation_ids

    def test_append_review_state(self):
        """Can append review state to timeline."""
        timeline = create_review_timeline(replay_session_id="mrs-123")
        append_review_state_to_timeline(timeline, "approved")
        assert "approved" in timeline.review_state_progression

    def test_append_topology_risk(self):
        """Can append topology risk to timeline."""
        timeline = create_review_timeline(replay_session_id="mrs-123")
        append_topology_risk_to_timeline(timeline, "undercut detected")
        assert "undercut detected" in timeline.topology_risk_progression

    def test_append_fixture_warning(self):
        """Can append fixture warning to timeline."""
        timeline = create_review_timeline(replay_session_id="mrs-123")
        append_fixture_warning_to_timeline(timeline, "clamp conflict")
        assert "clamp conflict" in timeline.fixture_warning_progression

    def test_get_latest_review_state(self):
        """Can get latest review state."""
        timeline = create_review_timeline(replay_session_id="mrs-123")
        append_review_state_to_timeline(timeline, "pending")
        append_review_state_to_timeline(timeline, "approved")
        assert get_latest_review_state(timeline) == "approved"

    def test_has_topology_risks(self):
        """Can check for topology risks."""
        timeline = create_review_timeline(replay_session_id="mrs-123")
        assert has_topology_risks(timeline) is False
        append_topology_risk_to_timeline(timeline, "risk")
        assert has_topology_risks(timeline) is True

    def test_has_fixture_warnings(self):
        """Can check for fixture warnings."""
        timeline = create_review_timeline(replay_session_id="mrs-123")
        assert has_fixture_warnings(timeline) is False
        append_fixture_warning_to_timeline(timeline, "warning")
        assert has_fixture_warnings(timeline) is True

    def test_timeline_has_hash(self):
        """Timeline has deterministic hash."""
        timeline = create_review_timeline(replay_session_id="mrs-123")
        assert timeline.deterministic_timeline_hash != ""
        assert len(timeline.deterministic_timeline_hash) == 64

    def test_get_timeline_summary(self):
        """Can get timeline summary."""
        timeline = create_review_timeline(
            replay_session_id="mrs-123",
            ordered_observation_ids=["obs-1", "obs-2"],
        )
        append_topology_risk_to_timeline(timeline, "risk")
        summary = get_timeline_summary(timeline)
        assert summary["observation_count"] == 2
        assert summary["topology_risk_count"] == 1

    def test_is_timeline_complete(self):
        """Timeline completeness check works."""
        timeline = create_review_timeline(
            replay_session_id="mrs-123",
            ordered_observation_ids=["obs-1"],
        )
        update_timeline_continuity_state(timeline, "complete")
        assert is_timeline_complete(timeline) is True


# ============================================================================
# PACKAGE TESTS (10 tests)
# ============================================================================


class TestReplaySafeReviewPackage:
    """Tests for replay-safe review package model."""

    def test_create_package(self):
        """Package created with session ID."""
        package = create_replay_safe_review_package(
            replay_session_id="mrs-123",
        )
        assert package.replay_session_id == "mrs-123"
        assert package.package_id.startswith("rsrp-")

    def test_package_is_immutable(self):
        """Package is marked immutable by default."""
        package = create_replay_safe_review_package(replay_session_id="mrs-123")
        assert package.immutable is True

    def test_add_observation_to_package(self):
        """Can add observation to package."""
        package = create_replay_safe_review_package(replay_session_id="mrs-123")
        add_observation_to_package(package, "obs-1")
        assert "obs-1" in package.observation_ids

    def test_add_provenance_ref(self):
        """Can add provenance ref to package."""
        package = create_replay_safe_review_package(replay_session_id="mrs-123")
        add_provenance_ref_to_package(package, "prov-ref-1")
        assert "prov-ref-1" in package.provenance_refs

    def test_set_timeline(self):
        """Can set timeline for package."""
        package = create_replay_safe_review_package(replay_session_id="mrs-123")
        set_timeline_for_package(package, "rit-123")
        assert package.timeline_id == "rit-123"

    def test_update_review_summary(self):
        """Can update review summary."""
        package = create_replay_safe_review_package(replay_session_id="mrs-123")
        update_review_summary(package, "All checks passed")
        assert package.review_summary == "All checks passed"

    def test_package_has_hash(self):
        """Package has deterministic hash."""
        package = create_replay_safe_review_package(replay_session_id="mrs-123")
        assert package.deterministic_package_hash != ""
        assert len(package.deterministic_package_hash) == 64

    def test_is_package_complete(self):
        """Package completeness check works."""
        package = create_replay_safe_review_package(replay_session_id="mrs-123")
        add_observation_to_package(package, "obs-1")
        update_package_continuity_state(package, "complete")
        assert is_package_complete(package) is True

    def test_get_package_summary(self):
        """Can get package summary."""
        package = create_replay_safe_review_package(
            replay_session_id="mrs-123",
            observation_ids=["obs-1", "obs-2"],
        )
        summary = get_package_summary(package)
        assert summary["observation_count"] == 2
        assert summary["immutable"] is True

    def test_validate_package_valid(self):
        """Valid package passes validation."""
        package = create_replay_safe_review_package(
            replay_session_id="mrs-123",
            observation_ids=["obs-1"],
        )
        is_valid, issues = validate_replay_safe_review_package(package)
        assert is_valid is True


# ============================================================================
# PACKAGE INVARIANT TESTS (5 tests)
# ============================================================================


class TestPackageInvariants:
    """Tests for 7W package invariants."""

    def test_immutable_must_be_true(self):
        """immutable must be True."""
        with pytest.raises(ValueError, match="immutable must be True"):
            ReplaySafeReviewPackage(
                replay_session_id="mrs-123",
                immutable=False,
            )

    def test_execution_authorized_must_be_false(self):
        """execution_authorized must be False."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            ReplaySafeReviewPackage(
                replay_session_id="mrs-123",
                execution_authorized=True,
            )

    def test_machine_output_allowed_must_be_false(self):
        """machine_output_allowed must be False."""
        with pytest.raises(ValueError, match="machine_output_allowed must be False"):
            ReplaySafeReviewPackage(
                replay_session_id="mrs-123",
                machine_output_allowed=True,
            )

    def test_replay_execution_present_must_be_false(self):
        """replay_execution_present must be False."""
        with pytest.raises(ValueError, match="replay_execution_present must be False"):
            ReplaySafeReviewPackage(
                replay_session_id="mrs-123",
                replay_execution_present=True,
            )

    def test_default_invariants_correct(self):
        """Default invariants are correct."""
        package = create_replay_safe_review_package(replay_session_id="mrs-123")
        assert package.immutable is True
        assert package.execution_authorized is False
        assert package.machine_output_allowed is False
        assert package.replay_execution_present is False


# ============================================================================
# REGISTRY TESTS (10 tests)
# ============================================================================


class TestManufacturingReplayRegistry:
    """Tests for manufacturing replay registry."""

    def test_register_observation(self):
        """Can register observation."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        registered = register_review_observation(obs)
        assert registered.observation_id in MANUFACTURING_REVIEW_OBSERVATION_INDEX

    def test_get_observation(self):
        """Can get observation by ID."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        register_review_observation(obs)
        retrieved = get_review_observation(obs.observation_id)
        assert retrieved is not None
        assert retrieved.observation_id == obs.observation_id

    def test_list_observations_by_workspace(self):
        """Can list observations by workspace."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        register_review_observation(obs)
        observations = list_observations_by_workspace("ws-123")
        assert len(observations) == 1

    def test_register_session(self):
        """Can register session."""
        session = create_replay_session(workspace_id="ws-123")
        registered = register_replay_session(session)
        assert registered.replay_session_id in MANUFACTURING_REPLAY_SESSION_INDEX

    def test_get_session(self):
        """Can get session by ID."""
        session = create_replay_session(workspace_id="ws-123")
        register_replay_session(session)
        retrieved = get_replay_session(session.replay_session_id)
        assert retrieved is not None

    def test_register_timeline(self):
        """Can register timeline."""
        timeline = create_review_timeline(replay_session_id="mrs-123")
        registered = register_review_timeline(timeline)
        assert registered.timeline_id in REVIEW_INTELLIGENCE_TIMELINE_INDEX

    def test_list_timelines_by_session(self):
        """Can list timelines by session."""
        timeline = create_review_timeline(replay_session_id="mrs-123")
        register_review_timeline(timeline)
        timelines = list_timelines_by_session("mrs-123")
        assert len(timelines) == 1

    def test_register_package(self):
        """Can register package."""
        package = create_replay_safe_review_package(replay_session_id="mrs-123")
        registered = register_replay_safe_review_package(package)
        assert registered.package_id in REPLAY_SAFE_REVIEW_PACKAGE_INDEX

    def test_list_packages_by_session(self):
        """Can list packages by session."""
        package = create_replay_safe_review_package(replay_session_id="mrs-123")
        register_replay_safe_review_package(package)
        packages = list_packages_by_session("mrs-123")
        assert len(packages) == 1

    def test_clear_indexes(self):
        """Can clear indexes."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        register_review_observation(obs)
        assert len(MANUFACTURING_REVIEW_OBSERVATION_INDEX) == 1
        clear_manufacturing_replay_indexes_for_tests()
        assert len(MANUFACTURING_REVIEW_OBSERVATION_INDEX) == 0


# ============================================================================
# CONTINUITY TESTS (8 tests)
# ============================================================================


class TestContinuityValidation:
    """Tests for continuity validation."""

    def test_validate_replay_continuity_valid(self):
        """Valid continuity passes validation."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        register_review_observation(obs)
        session = create_replay_session(
            workspace_id="ws-123",
            observation_ids=[obs.observation_id],
        )
        is_valid, issues = validate_replay_continuity(session)
        assert is_valid is True
        assert len(issues) == 0

    def test_validate_replay_continuity_missing_observation(self):
        """Missing observation detected in continuity validation."""
        session = create_replay_session(
            workspace_id="ws-123",
            observation_ids=["obs-missing"],
        )
        is_valid, issues = validate_replay_continuity(session)
        assert is_valid is False
        assert any("Missing observation" in issue for issue in issues)

    def test_detect_fragmented_replay_no_fragments(self):
        """No fragmentation when all refs resolve."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        register_review_observation(obs)
        session = create_replay_session(
            workspace_id="ws-123",
            observation_ids=[obs.observation_id],
        )
        is_fragmented, missing = detect_fragmented_replay(session)
        assert is_fragmented is False
        assert len(missing) == 0

    def test_detect_fragmented_replay_with_missing(self):
        """Fragmentation detected when refs missing."""
        session = create_replay_session(
            workspace_id="ws-123",
            observation_ids=["obs-missing"],
        )
        is_fragmented, missing = detect_fragmented_replay(session)
        assert is_fragmented is True
        assert len(missing) > 0

    def test_detect_missing_replay_refs(self):
        """Can detect missing replay refs."""
        session = create_replay_session(
            workspace_id="ws-123",
            observation_ids=["obs-1", "obs-2"],
        )
        missing = detect_missing_replay_refs(session)
        assert len(missing) == 2

    def test_validate_replay_package_integrity_valid(self):
        """Valid package integrity passes validation."""
        session = create_replay_session(workspace_id="ws-123")
        register_replay_session(session)
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        register_review_observation(obs)
        package = create_replay_safe_review_package(
            replay_session_id=session.replay_session_id,
            observation_ids=[obs.observation_id],
        )
        is_valid, issues = validate_replay_package_integrity(package)
        assert is_valid is True

    def test_validate_replay_package_integrity_missing_session(self):
        """Missing session detected in package integrity validation."""
        package = create_replay_safe_review_package(
            replay_session_id="mrs-missing",
        )
        is_valid, issues = validate_replay_package_integrity(package)
        assert is_valid is False
        assert any("Missing replay session" in issue for issue in issues)

    def test_build_review_timeline_from_session(self):
        """Can build timeline from session."""
        obs = create_topology_warning(
            observation_text="Topology risk",
            workspace_id="ws-123",
        )
        register_review_observation(obs)
        session = create_replay_session(
            workspace_id="ws-123",
            observation_ids=[obs.observation_id],
        )
        timeline = build_review_timeline(session)
        assert timeline.replay_session_id == session.replay_session_id
        assert len(timeline.ordered_observation_ids) == 1
        assert len(timeline.topology_risk_progression) == 1


# ============================================================================
# CI SUMMARY TESTS (5 tests)
# ============================================================================


class TestCISummary:
    """Tests for CI summary."""

    def test_ci_summary_empty(self):
        """CI summary works with empty indexes."""
        summary = get_ci_summary()
        assert summary["total_observations"] == 0
        assert summary["total_sessions"] == 0
        assert summary["status"] == "pass"

    def test_ci_summary_with_observations(self):
        """CI summary counts observations."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Test",
            workspace_id="ws-123",
        )
        register_review_observation(obs)
        summary = get_ci_summary()
        assert summary["total_observations"] == 1

    def test_ci_summary_critical_fails(self):
        """Critical observation causes CI fail."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Critical issue",
            workspace_id="ws-123",
            severity="critical",
        )
        register_review_observation(obs)
        summary = get_ci_summary()
        assert summary["status"] == "fail"
        assert summary["critical_observation_count"] == 1

    def test_ci_summary_warning_warns(self):
        """Warning observation causes CI warn."""
        obs = create_review_observation(
            observation_category="topology_warning",
            observation_text="Warning",
            workspace_id="ws-123",
            severity="warning",
        )
        register_review_observation(obs)
        summary = get_ci_summary()
        assert summary["status"] == "warn"
        assert summary["warning_observation_count"] == 1

    def test_ci_summary_counts_by_category(self):
        """CI summary groups by category."""
        obs1 = create_topology_warning("Test 1", workspace_id="ws-123")
        obs2 = create_fixture_warning("Test 2", workspace_id="ws-123")
        register_review_observation(obs1)
        register_review_observation(obs2)
        summary = get_ci_summary()
        assert summary["observations_by_category"]["topology_warning"] == 1
        assert summary["observations_by_category"]["fixture_warning"] == 1

# ============================================================================
# ROUTER TESTS (10 tests)
# ============================================================================


class TestManufacturingReplayRouter:
    """Tests for manufacturing replay router endpoints."""

    def test_get_meta(self):
        """Meta endpoint returns version info."""
        response = client.get("/api/cam/manufacturing-replay/")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "7W"
        assert data["replay_execution_present"] is False
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False

    def test_create_observation(self):
        """Can create observation via API."""
        response = client.post(
            "/api/cam/manufacturing-replay/observations",
            json={
                "observation_category": "topology_warning",
                "observation_text": "Test warning",
                "workspace_id": "ws-123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["observation_category"] == "topology_warning"
        assert data["observation_id"].startswith("mro-")

    def test_list_observations(self):
        """Can list observations via API."""
        client.post(
            "/api/cam/manufacturing-replay/observations",
            json={
                "observation_category": "topology_warning",
                "observation_text": "Test",
                "workspace_id": "ws-123",
            },
        )
        response = client.get("/api/cam/manufacturing-replay/observations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_create_session(self):
        """Can create session via API."""
        response = client.post(
            "/api/cam/manufacturing-replay/session",
            json={
                "workspace_id": "ws-123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["replay_session_id"].startswith("mrs-")

    def test_get_session_summary(self):
        """Can get session summary via API."""
        session_response = client.post(
            "/api/cam/manufacturing-replay/session",
            json={"workspace_id": "ws-123"},
        )
        session_id = session_response.json()["replay_session_id"]
        response = client.get(f"/api/cam/manufacturing-replay/session/{session_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert "observation_count" in data

    def test_create_timeline(self):
        """Can create timeline via API."""
        response = client.post(
            "/api/cam/manufacturing-replay/timeline",
            json={
                "replay_session_id": "mrs-123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["timeline_id"].startswith("rit-")

    def test_create_package(self):
        """Can create package via API."""
        response = client.post(
            "/api/cam/manufacturing-replay/package",
            json={
                "replay_session_id": "mrs-123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["package_id"].startswith("rsrp-")
        assert data["immutable"] is True

    def test_get_ci_status(self):
        """Can get CI status via API."""
        response = client.get("/api/cam/manufacturing-replay/ci")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "total_observations" in data
        assert "total_sessions" in data

    def test_validate_observation_endpoint(self):
        """Can validate observation via API."""
        create_response = client.post(
            "/api/cam/manufacturing-replay/observations",
            json={
                "observation_category": "topology_warning",
                "observation_text": "Test",
                "workspace_id": "ws-123",
            },
        )
        obs_id = create_response.json()["observation_id"]
        response = client.post(f"/api/cam/manufacturing-replay/observations/{obs_id}/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    def test_observational_replay_endpoint(self):
        """Can get observational replay via API."""
        session_response = client.post(
            "/api/cam/manufacturing-replay/session",
            json={"workspace_id": "ws-123"},
        )
        session_id = session_response.json()["replay_session_id"]
        response = client.get(f"/api/cam/manufacturing-replay/session/{session_id}/replay")
        assert response.status_code == 200
        data = response.json()
        assert data["replay_execution_present"] is False
        assert data["machine_output_allowed"] is False
        assert data["execution_authorized"] is False
