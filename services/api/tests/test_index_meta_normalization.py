"""
Unit tests for index_meta normalization and validation (System 2 hardening).

Tests the centralized index_meta governance layer.
"""
from __future__ import annotations

import pytest

from app.rmos.runs_v2.index_meta import (
    IndexMetaError,
    normalize_index_meta,
    validate_index_meta,
    set_parent_links,
)


class TestNormalizeIndexMeta:
    """Tests for normalize_index_meta()."""

    def test_normalize_promotes_and_stringifies(self):
        """Test that normalize promotes params and stringifies identifiers."""
        meta = normalize_index_meta(
            event_type="saw_batch_plan",
            index_meta={"tool_kind": "saw"},
            session_id=123,  # non-str should become str
            batch_label="b1",
            parent_artifact_id="spec_1",
        )
        assert meta["kind"] == "saw_batch_plan"
        assert meta["event_type"] == "saw_batch_plan"
        assert meta["session_id"] == "123"
        assert meta["batch_label"] == "b1"
        assert meta["tool_kind"] == "saw"
        assert meta["parent_artifact_id"] == "spec_1"

    def test_normalize_preserves_existing_keys(self):
        """Test that normalize doesn't overwrite existing values."""
        meta = normalize_index_meta(
            event_type="saw_batch_plan",
            index_meta={
                "session_id": "existing_session",
                "batch_label": "existing_batch",
                "custom_field": "preserved",
            },
            session_id="new_session",  # should NOT overwrite
            batch_label="new_batch",  # should NOT overwrite
        )
        assert meta["session_id"] == "existing_session"
        assert meta["batch_label"] == "existing_batch"
        assert meta["custom_field"] == "preserved"

    def test_normalize_returns_dict_for_none_input(self):
        """Test that normalize returns dict even when index_meta is None."""
        meta = normalize_index_meta(
            event_type="test_event",
            index_meta=None,
        )
        assert isinstance(meta, dict)
        assert meta["kind"] == "test_event"

    def test_normalize_stringifies_numeric_ids(self):
        """Test that numeric IDs are converted to strings."""
        meta = normalize_index_meta(
            event_type="test",
            index_meta={
                "session_id": 12345,
                "tool_id": 999,
            },
        )
        assert meta["session_id"] == "12345"
        assert meta["tool_id"] == "999"


class TestValidateIndexMeta:
    """Tests for validate_index_meta()."""

    def test_validate_requires_dict(self):
        """Test that validate rejects non-dict input."""
        with pytest.raises(IndexMetaError, match="must be a dict"):
            validate_index_meta("not a dict", event_type="test")

    def test_validate_strict_requires_core_keys(self):
        """Test that strict mode requires session_id, batch_label, tool_kind."""
        meta = {
            "kind": "saw_batch_plan",
            "event_type": "saw_batch_plan",
            # missing session_id, batch_label, tool_kind
        }
        with pytest.raises(IndexMetaError, match="missing index_meta.session_id"):
            validate_index_meta(meta, event_type="saw_batch_plan", strict=True)

    def test_validate_strict_requires_parent_for_plan(self):
        """Test that plan artifacts require parent spec link in strict mode."""
        meta = {
            "kind": "saw_batch_plan",
            "session_id": "s1",
            "batch_label": "b1",
            "tool_kind": "saw",
            # missing parent link
        }
        with pytest.raises(IndexMetaError, match="plan missing parent spec link"):
            validate_index_meta(meta, event_type="saw_batch_plan", strict=True)

    def test_validate_strict_requires_parent_for_decision(self):
        """Test that decision artifacts require parent plan link in strict mode."""
        meta = {
            "kind": "saw_batch_decision",
            "session_id": "s1",
            "batch_label": "b1",
            "tool_kind": "saw",
            # missing parent link
        }
        with pytest.raises(IndexMetaError, match="decision missing parent plan link"):
            validate_index_meta(meta, event_type="saw_batch_decision", strict=True)

    def test_validate_non_strict_does_not_raise(self):
        """Test that non-strict mode logs warnings but doesn't raise."""
        meta = {
            "kind": "saw_batch_plan",
            # missing everything
        }
        # Should not raise in non-strict mode
        validate_index_meta(meta, event_type="saw_batch_plan", strict=False)

    def test_validate_passes_with_complete_meta(self):
        """Test that validation passes with complete metadata."""
        meta = {
            "kind": "saw_batch_plan",
            "session_id": "s1",
            "batch_label": "b1",
            "tool_kind": "saw",
            "parent_batch_spec_artifact_id": "spec_123",
        }
        # Should not raise
        validate_index_meta(meta, event_type="saw_batch_plan", strict=True)


class TestSetParentLinks:
    """Tests for set_parent_links()."""

    def test_set_parent_links_adds_typed_pointers(self):
        """Test that set_parent_links adds typed parent pointers."""
        meta = {"session_id": "s1"}
        result = set_parent_links(
            meta,
            spec_id="spec_123",
            plan_id="plan_456",
            decision_id="dec_789",
        )
        assert result["parent_batch_spec_artifact_id"] == "spec_123"
        assert result["parent_batch_plan_artifact_id"] == "plan_456"
        assert result["parent_batch_decision_artifact_id"] == "dec_789"
        assert result["session_id"] == "s1"  # preserved

    def test_set_parent_links_skips_none_values(self):
        """Test that None values are not added to meta."""
        meta = {}
        result = set_parent_links(
            meta,
            spec_id="spec_123",
            plan_id=None,  # should not be added
        )
        assert result["parent_batch_spec_artifact_id"] == "spec_123"
        assert "parent_batch_plan_artifact_id" not in result

    def test_set_parent_links_adds_generic_parent(self):
        """Test that generic parent_artifact_id can be set."""
        meta = {}
        result = set_parent_links(meta, parent_artifact_id="parent_123")
        assert result["parent_artifact_id"] == "parent_123"


class TestIntegration:
    """Integration tests for the full normalize + validate flow."""

    def test_normalize_then_validate_passes(self):
        """Test that normalized meta passes validation."""
        meta = normalize_index_meta(
            event_type="saw_batch_plan",
            index_meta={},
            session_id="session_1",
            batch_label="batch_1",
            tool_kind="saw",
        )
        meta = set_parent_links(meta, spec_id="spec_123")

        # Should pass strict validation
        validate_index_meta(meta, event_type="saw_batch_plan", strict=True)

    def test_batch_tree_linkage(self):
        """Test that a full batch tree can be linked correctly."""
        # Spec (root)
        spec_meta = normalize_index_meta(
            event_type="saw_batch_spec",
            index_meta={},
            session_id="session_1",
            batch_label="batch_1",
            tool_kind="saw",
        )

        # Plan -> Spec
        plan_meta = normalize_index_meta(
            event_type="saw_batch_plan",
            index_meta={},
            session_id="session_1",
            batch_label="batch_1",
            tool_kind="saw",
        )
        plan_meta = set_parent_links(plan_meta, spec_id="spec_123")
        validate_index_meta(plan_meta, event_type="saw_batch_plan", strict=True)

        # Decision -> Plan
        decision_meta = normalize_index_meta(
            event_type="saw_batch_decision",
            index_meta={},
            session_id="session_1",
            batch_label="batch_1",
            tool_kind="saw",
        )
        decision_meta = set_parent_links(decision_meta, plan_id="plan_456")
        validate_index_meta(decision_meta, event_type="saw_batch_decision", strict=True)

        # Toolpaths -> Decision
        toolpaths_meta = normalize_index_meta(
            event_type="saw_batch_toolpaths",
            index_meta={},
            session_id="session_1",
            batch_label="batch_1",
            tool_kind="saw",
        )
        toolpaths_meta = set_parent_links(toolpaths_meta, decision_id="decision_789")
        validate_index_meta(toolpaths_meta, event_type="saw_batch_toolpaths", strict=True)
