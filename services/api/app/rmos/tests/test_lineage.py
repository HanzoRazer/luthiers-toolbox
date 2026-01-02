"""
Tests for RMOS Lineage Service

Bundle 09: Backend lineage support tests.
"""

import pytest

from app.rmos.services.lineage import (
    build_lineage,
    extract_parent_plan_run_id,
    merge_lineage_into_artifact,
    has_lineage,
    validate_lineage_consistency,
)


def test_build_lineage():
    """Test building lineage envelope."""
    result = build_lineage("plan-123")
    assert result == {"lineage": {"parent_plan_run_id": "plan-123"}}


def test_build_lineage_none():
    """Test building lineage envelope with None."""
    result = build_lineage(None)
    assert result == {"lineage": {"parent_plan_run_id": None}}


def test_build_and_extract_lineage():
    """Test round-trip: build and extract."""
    d = build_lineage("plan-123")
    assert d == {"lineage": {"parent_plan_run_id": "plan-123"}}
    assert extract_parent_plan_run_id(d) == "plan-123"


def test_extract_parent_plan_run_id_from_lineage():
    """Test extracting from lineage envelope."""
    artifact = {"lineage": {"parent_plan_run_id": "plan-abc"}}
    assert extract_parent_plan_run_id(artifact) == "plan-abc"


def test_extract_parent_plan_run_id_from_meta():
    """Test extracting from meta (fallback)."""
    artifact = {"meta": {"parent_plan_run_id": "plan-xyz"}}
    assert extract_parent_plan_run_id(artifact) == "plan-xyz"


def test_extract_parent_plan_run_id_from_top_level():
    """Test extracting from top-level (fallback)."""
    artifact = {"parent_plan_run_id": "plan-top"}
    assert extract_parent_plan_run_id(artifact) == "plan-top"


def test_extract_parent_plan_run_id_priority():
    """Test that lineage envelope takes priority."""
    artifact = {
        "lineage": {"parent_plan_run_id": "from-lineage"},
        "meta": {"parent_plan_run_id": "from-meta"},
        "parent_plan_run_id": "from-top",
    }
    assert extract_parent_plan_run_id(artifact) == "from-lineage"


def test_extract_parent_plan_run_id_none():
    """Test extracting when not present."""
    artifact = {"run_id": "some-run"}
    assert extract_parent_plan_run_id(artifact) is None


def test_merge_lineage_into_artifact():
    """Test merging lineage into artifact."""
    artifact = {"run_id": "exec-123", "status": "EXECUTED"}
    result = merge_lineage_into_artifact(artifact, "plan-abc")

    assert result["run_id"] == "exec-123"
    assert result["status"] == "EXECUTED"
    assert result["lineage"]["parent_plan_run_id"] == "plan-abc"

    # Original should not be mutated
    assert "lineage" not in artifact


def test_has_lineage():
    """Test has_lineage check."""
    assert has_lineage({"lineage": {"parent_plan_run_id": "plan-123"}})
    assert not has_lineage({"lineage": {"parent_plan_run_id": None}})
    assert not has_lineage({"lineage": {"parent_plan_run_id": ""}})
    assert not has_lineage({})


def test_validate_lineage_consistency():
    """Test lineage consistency validation."""
    plan = {"run_id": "plan-123"}
    execute_good = {"lineage": {"parent_plan_run_id": "plan-123"}}
    execute_bad = {"lineage": {"parent_plan_run_id": "plan-456"}}
    execute_none = {}

    assert validate_lineage_consistency(plan, execute_good)
    assert not validate_lineage_consistency(plan, execute_bad)
    assert not validate_lineage_consistency(plan, execute_none)
