"""
Unit tests for agentic layer contracts.

Tests schema validation, safe defaults, and cross-repo contract compatibility.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.agentic import (
    # Contracts
    ToolCapabilityV1,
    CapabilityAction,
    SafeDefaults,
    AttentionDirectiveV1,
    AttentionAction,
    FocusTarget,
    AgentEventV1,
    EventType,
    EventSource,
    UWSMv1,
    PreferenceDimension,
    DecayConfig,
    # Capabilities
    get_all_capabilities,
    get_capability_by_id,
    TAP_TONE_ANALYZER,
)


# -----------------------------------------------------------------------------
# ToolCapabilityV1 Tests
# -----------------------------------------------------------------------------


class TestToolCapabilityV1:
    """Tests for ToolCapabilityV1 contract."""

    def test_valid_capability(self):
        """Test creating a valid capability."""
        cap = ToolCapabilityV1(
            tool_id="test_tool",
            version="1.0.0",
            display_name="Test Tool",
            actions=[CapabilityAction.ANALYZE_AUDIO],
        )
        assert cap.tool_id == "test_tool"
        assert cap.version == "1.0.0"
        assert CapabilityAction.ANALYZE_AUDIO in cap.actions

    def test_tool_id_validation(self):
        """Test that tool_id must be snake_case."""
        with pytest.raises(ValidationError):
            ToolCapabilityV1(
                tool_id="InvalidToolId",  # Not snake_case
                version="1.0.0",
                display_name="Test",
                actions=[CapabilityAction.ANALYZE_AUDIO],
            )

    def test_version_format(self):
        """Test that version must be semver."""
        with pytest.raises(ValidationError):
            ToolCapabilityV1(
                tool_id="test_tool",
                version="1.0",  # Missing patch version
                display_name="Test",
                actions=[CapabilityAction.ANALYZE_AUDIO],
            )

    def test_safe_defaults(self):
        """Test that safe defaults are applied."""
        cap = ToolCapabilityV1(
            tool_id="test_tool",
            version="1.0.0",
            display_name="Test Tool",
            actions=[CapabilityAction.ANALYZE_AUDIO],
        )
        assert cap.safe_defaults.dry_run is True
        assert cap.safe_defaults.require_confirmation is True
        assert cap.safe_defaults.pii_scrub_enabled is True

    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected (strict validation)."""
        with pytest.raises(ValidationError):
            ToolCapabilityV1(
                tool_id="test_tool",
                version="1.0.0",
                display_name="Test",
                actions=[CapabilityAction.ANALYZE_AUDIO],
                unknown_field="should fail",  # Extra field
            )


# -----------------------------------------------------------------------------
# AttentionDirectiveV1 Tests
# -----------------------------------------------------------------------------


class TestAttentionDirectiveV1:
    """Tests for AttentionDirectiveV1 contract."""

    def test_valid_directive(self):
        """Test creating a valid attention directive."""
        directive = AttentionDirectiveV1(
            directive_id="attn_001",
            action=AttentionAction.REVIEW,
            summary="Please review this analysis",
            focus=FocusTarget(
                target_type="spectrum_region",
                target_id="peak_3",
            ),
        )
        assert directive.action == AttentionAction.REVIEW
        assert directive.urgency == 0.5  # Default

    def test_urgency_bounds(self):
        """Test that urgency is bounded 0-1."""
        with pytest.raises(ValidationError):
            AttentionDirectiveV1(
                directive_id="attn_001",
                action=AttentionAction.REVIEW,
                summary="Test",
                focus=FocusTarget(target_type="test", target_id="1"),
                urgency=1.5,  # Out of bounds
            )

    def test_auto_dismiss(self):
        """Test auto-dismiss configuration."""
        directive = AttentionDirectiveV1(
            directive_id="attn_001",
            action=AttentionAction.INSPECT,
            summary="FYI",
            focus=FocusTarget(target_type="test", target_id="1"),
            auto_dismiss_after_seconds=60,
        )
        assert directive.auto_dismiss_after_seconds == 60

    def test_supersedes(self):
        """Test that directive can supersede others."""
        directive = AttentionDirectiveV1(
            directive_id="attn_002",
            action=AttentionAction.DECIDE,
            summary="New decision needed",
            focus=FocusTarget(target_type="test", target_id="1"),
            supersedes=["attn_001"],
        )
        assert "attn_001" in directive.supersedes


# -----------------------------------------------------------------------------
# AgentEventV1 Tests
# -----------------------------------------------------------------------------


class TestAgentEventV1:
    """Tests for AgentEventV1 contract."""

    def test_valid_event(self):
        """Test creating a valid event."""
        event = AgentEventV1(
            event_id="evt_001",
            event_type=EventType.ANALYSIS_COMPLETED,
            source=EventSource(
                repo="tap_tone_pi",
                component="wolf_detector",
            ),
        )
        assert event.event_type == EventType.ANALYSIS_COMPLETED
        assert event.source.repo == "tap_tone_pi"

    def test_privacy_layer_default(self):
        """Test that privacy layer defaults to 3."""
        event = AgentEventV1(
            event_id="evt_001",
            event_type=EventType.ANALYSIS_STARTED,
            source=EventSource(repo="test", component="test"),
        )
        assert event.privacy_layer == 3

    def test_privacy_layer_bounds(self):
        """Test that privacy layer is bounded 0-5."""
        with pytest.raises(ValidationError):
            AgentEventV1(
                event_id="evt_001",
                event_type=EventType.ANALYSIS_STARTED,
                source=EventSource(repo="test", component="test"),
                privacy_layer=6,  # Out of bounds
            )

    def test_correlation_chain(self):
        """Test event correlation chain."""
        parent = AgentEventV1(
            event_id="evt_001",
            event_type=EventType.ANALYSIS_STARTED,
            source=EventSource(repo="test", component="test"),
            correlation_id="session_xyz",
        )
        child = AgentEventV1(
            event_id="evt_002",
            event_type=EventType.ANALYSIS_COMPLETED,
            source=EventSource(repo="test", component="test"),
            correlation_id="session_xyz",
            parent_event_id="evt_001",
        )
        assert child.parent_event_id == parent.event_id
        assert child.correlation_id == parent.correlation_id


# -----------------------------------------------------------------------------
# UWSMv1 Tests
# -----------------------------------------------------------------------------


class TestUWSMv1:
    """Tests for UWSMv1 (User Working Style Model) contract."""

    def test_default_uwsm(self):
        """Test default UWSM initialization."""
        uwsm = UWSMv1()
        assert uwsm.user_id == "local"
        assert uwsm.privacy_layer == 0  # Local-only by default
        assert len(uwsm.dimensions) == 6  # All 6 dimensions

    def test_dimension_initial_values(self):
        """Test that dimensions start at neutral 0.5."""
        uwsm = UWSMv1()
        for dim in PreferenceDimension:
            state = uwsm.get_dimension(dim)
            assert state.value == 0.5
            assert state.confidence == 0.0  # No data yet

    def test_record_signal(self):
        """Test recording a preference signal."""
        from app.agentic.contracts.uwsm import PreferenceSignal

        uwsm = UWSMv1()
        signal = PreferenceSignal(
            dimension=PreferenceDimension.GUIDANCE_DENSITY,
            value=0.8,
            confidence=0.6,
        )
        uwsm.record_signal(signal)

        state = uwsm.get_dimension(PreferenceDimension.GUIDANCE_DENSITY)
        assert state.signal_count == 1
        assert state.value == 0.8
        assert state.confidence == 0.6

    def test_multiple_signals_average(self):
        """Test that multiple signals are averaged."""
        from app.agentic.contracts.uwsm import PreferenceSignal

        uwsm = UWSMv1()

        # First signal: high guidance
        uwsm.record_signal(PreferenceSignal(
            dimension=PreferenceDimension.GUIDANCE_DENSITY,
            value=0.9,
            confidence=0.5,
        ))

        # Second signal: low guidance
        uwsm.record_signal(PreferenceSignal(
            dimension=PreferenceDimension.GUIDANCE_DENSITY,
            value=0.3,
            confidence=0.5,
        ))

        state = uwsm.get_dimension(PreferenceDimension.GUIDANCE_DENSITY)
        assert state.signal_count == 2
        # Weighted average should be around 0.6
        assert 0.5 < state.value < 0.7

    def test_sync_disabled_by_default(self):
        """Test that cloud sync is disabled by default."""
        uwsm = UWSMv1()
        assert uwsm.sync_enabled is False


# -----------------------------------------------------------------------------
# Capability Registry Tests
# -----------------------------------------------------------------------------


class TestCapabilityRegistry:
    """Tests for capability registry."""

    def test_get_all_capabilities(self):
        """Test that registry returns all capabilities."""
        caps = get_all_capabilities()
        assert len(caps) >= 1  # At least tap_tone_analyzer
        tool_ids = [c.tool_id for c in caps]
        assert "tap_tone_analyzer" in tool_ids

    def test_get_capability_by_id(self):
        """Test looking up capability by ID."""
        cap = get_capability_by_id("tap_tone_analyzer")
        assert cap is not None
        assert cap.tool_id == "tap_tone_analyzer"
        assert cap.source_repo == "tap_tone_pi"

    def test_tap_tone_analyzer_capabilities(self):
        """Test that TAP_TONE_ANALYZER has expected capabilities."""
        assert CapabilityAction.ANALYZE_AUDIO in TAP_TONE_ANALYZER.actions
        assert CapabilityAction.ANALYZE_SPECTRUM in TAP_TONE_ANALYZER.actions
        assert "wolf_candidates_v1" in TAP_TONE_ANALYZER.output_schemas

    def test_capability_not_found(self):
        """Test that unknown capability returns None."""
        cap = get_capability_by_id("nonexistent_tool")
        assert cap is None


# -----------------------------------------------------------------------------
# Cross-Repo Contract Compatibility Tests
# -----------------------------------------------------------------------------


class TestCrossRepoCompatibility:
    """Tests for cross-repo contract compatibility."""

    def test_event_from_tap_tone(self):
        """Test that tap_tone_pi events are valid."""
        event = AgentEventV1(
            event_id="evt_tap_001",
            event_type=EventType.ANALYSIS_COMPLETED,
            source=EventSource(
                repo="tap_tone_pi",
                component="wolf_detector",
                version="1.0.0",
            ),
            payload={
                "candidates_found": 3,
                "max_confidence": 0.87,
            },
            privacy_layer=2,
        )
        assert event.source.repo == "tap_tone_pi"

    def test_attention_for_wolf_tone(self):
        """Test attention directive for wolf tone detection."""
        directive = AttentionDirectiveV1(
            directive_id="attn_wolf_001",
            action=AttentionAction.REVIEW,
            summary="Potential wolf tone at 247Hz",
            detail=(
                "The analyzer detected a potential wolf tone at 247Hz "
                "with 87% confidence. This frequency may cause tonal "
                "issues in the B3-C4 range."
            ),
            focus=FocusTarget(
                target_type="spectrum_region",
                target_id="peak_3",
                highlight_region={
                    "freq_hz": 247,
                    "bandwidth_hz": 10,
                },
            ),
            urgency=0.7,
            confidence=0.87,
            evidence_refs=["wolf_candidates_v1:abc123:peak_3"],
            source_tool="tap_tone_wolf_detector",
        )
        assert directive.urgency == 0.7
        assert "247Hz" in directive.summary

    def test_capability_schema_references(self):
        """Test that capability schema refs are consistent."""
        cap = TAP_TONE_ANALYZER
        # Input schemas should exist in tap_tone_pi
        assert "tap_tone_bundle_v1" in cap.input_schemas
        # Output schemas should match event payloads
        assert "wolf_candidates_v1" in cap.output_schemas
