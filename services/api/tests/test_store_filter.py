"""
Tests for Store Filter Module.

Tests index metadata filtering for run artifact queries.
"""
from datetime import datetime, timezone
import pytest

from app.rmos.runs_v2.store_filter import (
    matches_index_meta,
    _matches_date_range,
    _matches_simple_fields,
    _matches_session_labels,
    _matches_lineage,
    _any_field_matches,
)


class TestMatchesDateRange:
    """Tests for _matches_date_range function."""

    def test_no_filters_always_passes(self):
        """Should pass when no date filters provided."""
        m = {"created_at_utc": "2024-01-15T10:00:00Z"}
        assert _matches_date_range(m, None, None) is True

    def test_no_created_at_passes(self):
        """Should pass when no created_at_utc in metadata."""
        m = {}
        date_from = datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert _matches_date_range(m, date_from, None) is True

    def test_date_from_passes(self):
        """Should pass when created_at >= date_from."""
        m = {"created_at_utc": "2024-01-15T10:00:00Z"}
        date_from = datetime(2024, 1, 10, tzinfo=timezone.utc)
        assert _matches_date_range(m, date_from, None) is True

    def test_date_from_fails(self):
        """Should fail when created_at < date_from."""
        m = {"created_at_utc": "2024-01-05T10:00:00Z"}
        date_from = datetime(2024, 1, 10, tzinfo=timezone.utc)
        assert _matches_date_range(m, date_from, None) is False

    def test_date_to_passes(self):
        """Should pass when created_at <= date_to."""
        m = {"created_at_utc": "2024-01-15T10:00:00Z"}
        date_to = datetime(2024, 1, 20, tzinfo=timezone.utc)
        assert _matches_date_range(m, None, date_to) is True

    def test_date_to_fails(self):
        """Should fail when created_at > date_to."""
        m = {"created_at_utc": "2024-01-25T10:00:00Z"}
        date_to = datetime(2024, 1, 20, tzinfo=timezone.utc)
        assert _matches_date_range(m, None, date_to) is False

    def test_date_range_passes(self):
        """Should pass when created_at within range."""
        m = {"created_at_utc": "2024-01-15T10:00:00Z"}
        date_from = datetime(2024, 1, 10, tzinfo=timezone.utc)
        date_to = datetime(2024, 1, 20, tzinfo=timezone.utc)
        assert _matches_date_range(m, date_from, date_to) is True

    def test_date_range_outside_fails(self):
        """Should fail when created_at outside range."""
        m = {"created_at_utc": "2024-01-25T10:00:00Z"}
        date_from = datetime(2024, 1, 10, tzinfo=timezone.utc)
        date_to = datetime(2024, 1, 20, tzinfo=timezone.utc)
        assert _matches_date_range(m, date_from, date_to) is False

    def test_handles_z_suffix(self):
        """Should handle ISO format with Z suffix."""
        m = {"created_at_utc": "2024-01-15T10:00:00Z"}
        date_from = datetime(2024, 1, 14, tzinfo=timezone.utc)
        assert _matches_date_range(m, date_from, None) is True

    def test_handles_invalid_date_gracefully(self):
        """Should pass when date is invalid (not parseable)."""
        m = {"created_at_utc": "not-a-date"}
        date_from = datetime(2024, 1, 10, tzinfo=timezone.utc)
        assert _matches_date_range(m, date_from, None) is True


class TestMatchesSimpleFields:
    """Tests for _matches_simple_fields function."""

    def test_no_filters_passes(self):
        """Should pass when no filters provided."""
        m = {"event_type": "plan", "status": "OK"}
        assert _matches_simple_fields(m, None, None, None, None, None, None) is True

    def test_event_type_matches(self):
        """Should match event_type filter."""
        m = {"event_type": "plan"}
        assert _matches_simple_fields(m, "plan", None, None, None, None, None) is True

    def test_event_type_no_match(self):
        """Should fail when event_type doesn't match."""
        m = {"event_type": "execute"}
        assert _matches_simple_fields(m, "plan", None, None, None, None, None) is False

    def test_kind_alias_for_event_type(self):
        """Should treat kind as alias for event_type."""
        m = {"event_type": "plan"}
        assert _matches_simple_fields(m, None, "plan", None, None, None, None) is True

    def test_event_type_takes_precedence_over_kind(self):
        """event_type should take precedence when both provided."""
        m = {"event_type": "plan"}
        # First argument is event_type, second is kind
        assert _matches_simple_fields(m, "plan", "execute", None, None, None, None) is True

    def test_status_matches(self):
        """Should match status filter."""
        m = {"status": "OK"}
        assert _matches_simple_fields(m, None, None, "OK", None, None, None) is True

    def test_status_no_match(self):
        """Should fail when status doesn't match."""
        m = {"status": "BLOCKED"}
        assert _matches_simple_fields(m, None, None, "OK", None, None, None) is False

    def test_tool_id_matches(self):
        """Should match tool_id filter."""
        m = {"tool_id": "tool_6mm"}
        assert _matches_simple_fields(m, None, None, None, "tool_6mm", None, None) is True

    def test_tool_id_no_match(self):
        """Should fail when tool_id doesn't match."""
        m = {"tool_id": "tool_8mm"}
        assert _matches_simple_fields(m, None, None, None, "tool_6mm", None, None) is False

    def test_mode_matches(self):
        """Should match mode filter."""
        m = {"mode": "plan"}
        assert _matches_simple_fields(m, None, None, None, None, "plan", None) is True

    def test_mode_no_match(self):
        """Should fail when mode doesn't match."""
        m = {"mode": "execute"}
        assert _matches_simple_fields(m, None, None, None, None, "plan", None) is False

    def test_workflow_session_id_matches(self):
        """Should match workflow_session_id filter."""
        m = {"workflow_session_id": "session_123"}
        assert _matches_simple_fields(m, None, None, None, None, None, "session_123") is True

    def test_workflow_session_id_no_match(self):
        """Should fail when workflow_session_id doesn't match."""
        m = {"workflow_session_id": "session_456"}
        assert _matches_simple_fields(m, None, None, None, None, None, "session_123") is False

    def test_multiple_filters_all_match(self):
        """Should pass when all filters match."""
        m = {"event_type": "plan", "status": "OK", "tool_id": "tool_6mm"}
        assert _matches_simple_fields(m, "plan", None, "OK", "tool_6mm", None, None) is True

    def test_multiple_filters_one_fails(self):
        """Should fail when any filter doesn't match."""
        m = {"event_type": "plan", "status": "BLOCKED", "tool_id": "tool_6mm"}
        assert _matches_simple_fields(m, "plan", None, "OK", "tool_6mm", None, None) is False


class TestMatchesSessionLabels:
    """Tests for _matches_session_labels function."""

    def test_no_filters_passes(self):
        """Should pass when no filters provided."""
        m = {"batch_label": "batch_1"}
        assert _matches_session_labels(m, None, None) is True

    def test_batch_label_top_level_matches(self):
        """Should match batch_label at top level."""
        m = {"batch_label": "batch_1"}
        assert _matches_session_labels(m, "batch_1", None) is True

    def test_batch_label_nested_matches(self):
        """Should match batch_label in nested meta."""
        m = {"meta": {"batch_label": "batch_1"}}
        assert _matches_session_labels(m, "batch_1", None) is True

    def test_batch_label_no_match(self):
        """Should fail when batch_label doesn't match."""
        m = {"batch_label": "batch_2"}
        assert _matches_session_labels(m, "batch_1", None) is False

    def test_session_id_top_level_matches(self):
        """Should match session_id at top level."""
        m = {"session_id": "session_123"}
        assert _matches_session_labels(m, None, "session_123") is True

    def test_session_id_nested_matches(self):
        """Should match session_id in nested meta."""
        m = {"meta": {"session_id": "session_123"}}
        assert _matches_session_labels(m, None, "session_123") is True

    def test_session_id_no_match(self):
        """Should fail when session_id doesn't match."""
        m = {"session_id": "session_456"}
        assert _matches_session_labels(m, None, "session_123") is False

    def test_both_filters_match(self):
        """Should pass when both batch_label and session_id match."""
        m = {"batch_label": "batch_1", "session_id": "session_123"}
        assert _matches_session_labels(m, "batch_1", "session_123") is True

    def test_mixed_top_nested_match(self):
        """Should match when labels are split between top-level and nested."""
        m = {"batch_label": "batch_1", "meta": {"session_id": "session_123"}}
        assert _matches_session_labels(m, "batch_1", "session_123") is True

    def test_empty_meta_still_checks_top_level(self):
        """Should check top-level when meta is empty."""
        m = {"batch_label": "batch_1", "meta": {}}
        assert _matches_session_labels(m, "batch_1", None) is True


class TestMatchesLineage:
    """Tests for _matches_lineage function."""

    def test_no_filters_passes(self):
        """Should pass when no filters provided."""
        m = {"lineage": {"parent_plan_run_id": "run_1"}}
        assert _matches_lineage(m, None, None, None, None) is True

    def test_parent_plan_run_id_top_level_matches(self):
        """Should match parent_plan_run_id at top level."""
        m = {"parent_plan_run_id": "run_1"}
        assert _matches_lineage(m, "run_1", None, None, None) is True

    def test_parent_plan_run_id_lineage_matches(self):
        """Should match parent_plan_run_id in lineage dict."""
        m = {"lineage": {"parent_plan_run_id": "run_1"}}
        assert _matches_lineage(m, "run_1", None, None, None) is True

    def test_parent_plan_run_id_meta_matches(self):
        """Should match parent_plan_run_id in meta dict."""
        m = {"meta": {"parent_plan_run_id": "run_1"}}
        assert _matches_lineage(m, "run_1", None, None, None) is True

    def test_parent_plan_run_id_no_match(self):
        """Should fail when parent_plan_run_id doesn't match."""
        m = {"parent_plan_run_id": "run_2"}
        assert _matches_lineage(m, "run_1", None, None, None) is False

    def test_parent_batch_plan_artifact_id_matches(self):
        """Should match parent_batch_plan_artifact_id."""
        m = {"lineage": {"parent_batch_plan_artifact_id": "artifact_1"}}
        assert _matches_lineage(m, None, "artifact_1", None, None) is True

    def test_parent_batch_plan_artifact_id_alias_matches(self):
        """Should match batch_plan_artifact_id alias."""
        m = {"lineage": {"batch_plan_artifact_id": "artifact_1"}}
        assert _matches_lineage(m, None, "artifact_1", None, None) is True

    def test_parent_batch_spec_artifact_id_matches(self):
        """Should match parent_batch_spec_artifact_id."""
        m = {"lineage": {"parent_batch_spec_artifact_id": "spec_1"}}
        assert _matches_lineage(m, None, None, "spec_1", None) is True

    def test_parent_batch_spec_artifact_id_alias_matches(self):
        """Should match batch_spec_artifact_id alias."""
        m = {"lineage": {"batch_spec_artifact_id": "spec_1"}}
        assert _matches_lineage(m, None, None, "spec_1", None) is True

    def test_parent_artifact_id_matches(self):
        """Should match generic parent_artifact_id."""
        m = {"lineage": {"parent_artifact_id": "parent_1"}}
        assert _matches_lineage(m, None, None, None, "parent_1") is True

    def test_parent_artifact_id_execution_alias_matches(self):
        """Should match parent_batch_execution_artifact_id alias."""
        m = {"lineage": {"parent_batch_execution_artifact_id": "exec_1"}}
        assert _matches_lineage(m, None, None, None, "exec_1") is True

    def test_multiple_lineage_filters_all_match(self):
        """Should pass when all lineage filters match."""
        m = {
            "lineage": {
                "parent_plan_run_id": "run_1",
                "parent_batch_plan_artifact_id": "artifact_1",
            }
        }
        assert _matches_lineage(m, "run_1", "artifact_1", None, None) is True

    def test_multiple_lineage_filters_one_fails(self):
        """Should fail when any lineage filter doesn't match."""
        m = {
            "lineage": {
                "parent_plan_run_id": "run_1",
                "parent_batch_plan_artifact_id": "artifact_2",
            }
        }
        assert _matches_lineage(m, "run_1", "artifact_1", None, None) is False


class TestAnyFieldMatches:
    """Tests for _any_field_matches helper function."""

    def test_matches_in_m(self):
        """Should find value in main dict m."""
        m = {"field1": "value1"}
        lineage = {}
        meta = {}
        assert _any_field_matches(m, lineage, meta, "field1", "value1") is True

    def test_matches_in_lineage(self):
        """Should find value in lineage dict."""
        m = {}
        lineage = {"field1": "value1"}
        meta = {}
        assert _any_field_matches(m, lineage, meta, "field1", "value1") is True

    def test_matches_in_meta(self):
        """Should find value in meta dict."""
        m = {}
        lineage = {}
        meta = {"field1": "value1"}
        assert _any_field_matches(m, lineage, meta, "field1", "value1") is True

    def test_no_match_anywhere(self):
        """Should return False when not found in any dict."""
        m = {}
        lineage = {}
        meta = {}
        assert _any_field_matches(m, lineage, meta, "field1", "value1") is False

    def test_matches_alias(self):
        """Should find value under alias key."""
        m = {"alias_key": "value1"}
        lineage = {}
        meta = {}
        assert _any_field_matches(m, lineage, meta, "field1", "value1", aliases=("alias_key",)) is True

    def test_alias_in_lineage(self):
        """Should find alias in lineage dict."""
        m = {}
        lineage = {"alias_key": "value1"}
        meta = {}
        assert _any_field_matches(m, lineage, meta, "field1", "value1", aliases=("alias_key",)) is True

    def test_alias_in_meta(self):
        """Should find alias in meta dict."""
        m = {}
        lineage = {}
        meta = {"alias_key": "value1"}
        assert _any_field_matches(m, lineage, meta, "field1", "value1", aliases=("alias_key",)) is True

    def test_wrong_value_no_match(self):
        """Should return False when field exists but value is wrong."""
        m = {"field1": "other_value"}
        lineage = {}
        meta = {}
        assert _any_field_matches(m, lineage, meta, "field1", "value1") is False

    def test_multiple_aliases(self):
        """Should check all aliases."""
        m = {"alias2": "value1"}
        lineage = {}
        meta = {}
        assert _any_field_matches(m, lineage, meta, "field1", "value1", aliases=("alias1", "alias2")) is True


class TestMatchesIndexMeta:
    """Tests for matches_index_meta main function."""

    def test_no_filters_passes(self):
        """Should pass when no filters provided."""
        m = {
            "event_type": "plan",
            "status": "OK",
            "created_at_utc": "2024-01-15T10:00:00Z",
        }
        assert matches_index_meta(m) is True

    def test_empty_meta_passes(self):
        """Should pass empty metadata with no filters."""
        m = {}
        assert matches_index_meta(m) is True

    def test_event_type_filter(self):
        """Should filter by event_type."""
        m = {"event_type": "plan"}
        assert matches_index_meta(m, event_type="plan") is True
        assert matches_index_meta(m, event_type="execute") is False

    def test_kind_filter(self):
        """Should filter by kind (alias for event_type)."""
        m = {"event_type": "plan"}
        assert matches_index_meta(m, kind="plan") is True
        assert matches_index_meta(m, kind="execute") is False

    def test_status_filter(self):
        """Should filter by status."""
        m = {"status": "OK"}
        assert matches_index_meta(m, status="OK") is True
        assert matches_index_meta(m, status="BLOCKED") is False

    def test_tool_id_filter(self):
        """Should filter by tool_id."""
        m = {"tool_id": "tool_6mm"}
        assert matches_index_meta(m, tool_id="tool_6mm") is True
        assert matches_index_meta(m, tool_id="tool_8mm") is False

    def test_mode_filter(self):
        """Should filter by mode."""
        m = {"mode": "plan"}
        assert matches_index_meta(m, mode="plan") is True
        assert matches_index_meta(m, mode="execute") is False

    def test_workflow_session_id_filter(self):
        """Should filter by workflow_session_id."""
        m = {"workflow_session_id": "session_123"}
        assert matches_index_meta(m, workflow_session_id="session_123") is True
        assert matches_index_meta(m, workflow_session_id="session_456") is False

    def test_batch_label_filter(self):
        """Should filter by batch_label."""
        m = {"batch_label": "batch_1"}
        assert matches_index_meta(m, batch_label="batch_1") is True
        assert matches_index_meta(m, batch_label="batch_2") is False

    def test_session_id_filter(self):
        """Should filter by session_id."""
        m = {"session_id": "session_123"}
        assert matches_index_meta(m, session_id="session_123") is True
        assert matches_index_meta(m, session_id="session_456") is False

    def test_parent_plan_run_id_filter(self):
        """Should filter by parent_plan_run_id."""
        m = {"lineage": {"parent_plan_run_id": "run_1"}}
        assert matches_index_meta(m, parent_plan_run_id="run_1") is True
        assert matches_index_meta(m, parent_plan_run_id="run_2") is False

    def test_parent_batch_plan_artifact_id_filter(self):
        """Should filter by parent_batch_plan_artifact_id."""
        m = {"lineage": {"parent_batch_plan_artifact_id": "artifact_1"}}
        assert matches_index_meta(m, parent_batch_plan_artifact_id="artifact_1") is True
        assert matches_index_meta(m, parent_batch_plan_artifact_id="artifact_2") is False

    def test_parent_batch_spec_artifact_id_filter(self):
        """Should filter by parent_batch_spec_artifact_id."""
        m = {"lineage": {"parent_batch_spec_artifact_id": "spec_1"}}
        assert matches_index_meta(m, parent_batch_spec_artifact_id="spec_1") is True
        assert matches_index_meta(m, parent_batch_spec_artifact_id="spec_2") is False

    def test_parent_artifact_id_filter(self):
        """Should filter by parent_artifact_id."""
        m = {"lineage": {"parent_artifact_id": "parent_1"}}
        assert matches_index_meta(m, parent_artifact_id="parent_1") is True
        assert matches_index_meta(m, parent_artifact_id="parent_2") is False

    def test_date_from_filter(self):
        """Should filter by date_from."""
        m = {"created_at_utc": "2024-01-15T10:00:00Z"}
        date_from = datetime(2024, 1, 10, tzinfo=timezone.utc)
        date_late = datetime(2024, 1, 20, tzinfo=timezone.utc)
        assert matches_index_meta(m, date_from=date_from) is True
        assert matches_index_meta(m, date_from=date_late) is False

    def test_date_to_filter(self):
        """Should filter by date_to."""
        m = {"created_at_utc": "2024-01-15T10:00:00Z"}
        date_to = datetime(2024, 1, 20, tzinfo=timezone.utc)
        date_early = datetime(2024, 1, 10, tzinfo=timezone.utc)
        assert matches_index_meta(m, date_to=date_to) is True
        assert matches_index_meta(m, date_to=date_early) is False

    def test_combined_filters_all_pass(self):
        """Should pass when all combined filters match."""
        m = {
            "event_type": "execute",
            "status": "OK",
            "tool_id": "tool_6mm",
            "batch_label": "batch_1",
            "created_at_utc": "2024-01-15T10:00:00Z",
            "lineage": {"parent_plan_run_id": "run_1"},
        }
        date_from = datetime(2024, 1, 10, tzinfo=timezone.utc)
        assert matches_index_meta(
            m,
            event_type="execute",
            status="OK",
            tool_id="tool_6mm",
            batch_label="batch_1",
            parent_plan_run_id="run_1",
            date_from=date_from,
        ) is True

    def test_combined_filters_one_fails(self):
        """Should fail when any combined filter fails."""
        m = {
            "event_type": "execute",
            "status": "BLOCKED",  # Will fail status check
            "tool_id": "tool_6mm",
        }
        assert matches_index_meta(
            m,
            event_type="execute",
            status="OK",  # Mismatch
            tool_id="tool_6mm",
        ) is False

    def test_date_filter_fails_stops_early(self):
        """Date filter failure should stop further checks."""
        m = {
            "event_type": "execute",
            "created_at_utc": "2024-01-05T10:00:00Z",
        }
        date_from = datetime(2024, 1, 10, tzinfo=timezone.utc)
        # Even though event_type matches, date filter should fail
        assert matches_index_meta(
            m,
            event_type="execute",
            date_from=date_from,
        ) is False
