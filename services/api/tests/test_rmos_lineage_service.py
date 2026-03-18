"""
Tests for RMOS Lineage Service.

Tests for Plan → Execute tracking lineage functions.
"""
import pytest

from app.rmos.services.lineage import (
    build_lineage,
    extract_parent_plan_run_id,
    merge_lineage_into_artifact,
    has_lineage,
    validate_lineage_consistency,
)


class TestBuildLineage:
    """Tests for build_lineage function."""

    def test_build_lineage_with_parent_id(self):
        """Should create lineage envelope with parent_plan_run_id."""
        result = build_lineage("run_abc123")
        assert result == {"lineage": {"parent_plan_run_id": "run_abc123"}}

    def test_build_lineage_with_none(self):
        """Should create lineage envelope with None parent."""
        result = build_lineage(None)
        assert result == {"lineage": {"parent_plan_run_id": None}}

    def test_build_lineage_default(self):
        """Should default to None when called without args."""
        result = build_lineage()
        assert result == {"lineage": {"parent_plan_run_id": None}}


class TestExtractParentPlanRunId:
    """Tests for extract_parent_plan_run_id function."""

    def test_extract_from_lineage(self):
        """Should extract from lineage envelope."""
        artifact = {"lineage": {"parent_plan_run_id": "run_123"}}
        assert extract_parent_plan_run_id(artifact) == "run_123"

    def test_extract_from_meta_fallback(self):
        """Should extract from meta field as fallback."""
        artifact = {"meta": {"parent_plan_run_id": "run_456"}}
        assert extract_parent_plan_run_id(artifact) == "run_456"

    def test_extract_from_toplevel_fallback(self):
        """Should extract from top-level field as fallback."""
        artifact = {"parent_plan_run_id": "run_789"}
        assert extract_parent_plan_run_id(artifact) == "run_789"

    def test_extract_lineage_takes_precedence(self):
        """Lineage field should take precedence over meta."""
        artifact = {
            "lineage": {"parent_plan_run_id": "run_lineage"},
            "meta": {"parent_plan_run_id": "run_meta"},
            "parent_plan_run_id": "run_toplevel",
        }
        assert extract_parent_plan_run_id(artifact) == "run_lineage"

    def test_extract_meta_takes_precedence_over_toplevel(self):
        """Meta field should take precedence over top-level."""
        artifact = {
            "meta": {"parent_plan_run_id": "run_meta"},
            "parent_plan_run_id": "run_toplevel",
        }
        assert extract_parent_plan_run_id(artifact) == "run_meta"

    def test_extract_returns_none_for_empty_artifact(self):
        """Should return None for empty artifact."""
        assert extract_parent_plan_run_id({}) is None

    def test_extract_returns_none_for_null_lineage(self):
        """Should return None when lineage is null."""
        artifact = {"lineage": None}
        assert extract_parent_plan_run_id(artifact) is None

    def test_extract_returns_none_for_empty_lineage(self):
        """Should return None when lineage has no parent_plan_run_id."""
        artifact = {"lineage": {}}
        assert extract_parent_plan_run_id(artifact) is None

    def test_extract_converts_to_string(self):
        """Should convert numeric values to string."""
        artifact = {"lineage": {"parent_plan_run_id": 12345}}
        assert extract_parent_plan_run_id(artifact) == "12345"


class TestMergeLineageIntoArtifact:
    """Tests for merge_lineage_into_artifact function."""

    def test_merge_into_empty_artifact(self):
        """Should merge lineage into empty artifact."""
        result = merge_lineage_into_artifact({}, "run_abc")
        assert result == {"lineage": {"parent_plan_run_id": "run_abc"}}

    def test_merge_preserves_existing_fields(self):
        """Should preserve existing artifact fields."""
        artifact = {"run_id": "exec_123", "status": "completed"}
        result = merge_lineage_into_artifact(artifact, "run_plan")
        assert result["run_id"] == "exec_123"
        assert result["status"] == "completed"
        assert result["lineage"]["parent_plan_run_id"] == "run_plan"

    def test_merge_does_not_mutate_original(self):
        """Should not mutate the original artifact."""
        original = {"run_id": "test"}
        result = merge_lineage_into_artifact(original, "parent")
        assert "lineage" not in original
        assert "lineage" in result

    def test_merge_overwrites_existing_lineage(self):
        """Should overwrite existing lineage field."""
        artifact = {"lineage": {"parent_plan_run_id": "old_parent"}}
        result = merge_lineage_into_artifact(artifact, "new_parent")
        assert result["lineage"]["parent_plan_run_id"] == "new_parent"


class TestHasLineage:
    """Tests for has_lineage function."""

    def test_has_lineage_true(self):
        """Should return True when lineage exists."""
        artifact = {"lineage": {"parent_plan_run_id": "run_123"}}
        assert has_lineage(artifact) is True

    def test_has_lineage_false_empty(self):
        """Should return False for empty artifact."""
        assert has_lineage({}) is False

    def test_has_lineage_false_none_parent(self):
        """Should return False when parent is None."""
        artifact = {"lineage": {"parent_plan_run_id": None}}
        assert has_lineage(artifact) is False

    def test_has_lineage_false_empty_string(self):
        """Should return False when parent is empty string."""
        artifact = {"lineage": {"parent_plan_run_id": ""}}
        assert has_lineage(artifact) is False

    def test_has_lineage_false_whitespace_string(self):
        """Should return False when parent is whitespace only."""
        artifact = {"lineage": {"parent_plan_run_id": "   "}}
        assert has_lineage(artifact) is False

    def test_has_lineage_true_from_meta(self):
        """Should return True when lineage in meta field."""
        artifact = {"meta": {"parent_plan_run_id": "run_456"}}
        assert has_lineage(artifact) is True


class TestValidateLineageConsistency:
    """Tests for validate_lineage_consistency function."""

    def test_consistent_lineage(self):
        """Should return True when execute references plan's run_id."""
        plan = {"run_id": "plan_123"}
        execute = {"lineage": {"parent_plan_run_id": "plan_123"}}
        assert validate_lineage_consistency(plan, execute) is True

    def test_consistent_lineage_with_id_field(self):
        """Should work with 'id' field instead of 'run_id'."""
        plan = {"id": "plan_456"}
        execute = {"lineage": {"parent_plan_run_id": "plan_456"}}
        assert validate_lineage_consistency(plan, execute) is True

    def test_inconsistent_lineage(self):
        """Should return False when execute references wrong plan."""
        plan = {"run_id": "plan_123"}
        execute = {"lineage": {"parent_plan_run_id": "plan_999"}}
        assert validate_lineage_consistency(plan, execute) is False

    def test_missing_plan_run_id(self):
        """Should return False when plan has no run_id."""
        plan = {}
        execute = {"lineage": {"parent_plan_run_id": "plan_123"}}
        assert validate_lineage_consistency(plan, execute) is False

    def test_missing_execute_lineage(self):
        """Should return False when execute has no lineage."""
        plan = {"run_id": "plan_123"}
        execute = {}
        assert validate_lineage_consistency(plan, execute) is False

    def test_prefers_run_id_over_id(self):
        """Should prefer run_id field over id field."""
        plan = {"run_id": "run_id_value", "id": "id_value"}
        execute = {"lineage": {"parent_plan_run_id": "run_id_value"}}
        assert validate_lineage_consistency(plan, execute) is True
