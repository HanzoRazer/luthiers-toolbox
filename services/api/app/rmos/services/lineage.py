"""
RMOS Lineage Service

Bundle 09: Backend lineage support for Plan → Execute tracking.

Provides stable lineage envelope:
- lineage.parent_plan_run_id

References:
- docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
- services/api/app/rmos/operations/adapter.py
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def build_lineage(parent_plan_run_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Build a lineage envelope for a run artifact.

    Args:
        parent_plan_run_id: The run_id of the parent plan artifact

    Returns:
        Lineage envelope dict: {"lineage": {"parent_plan_run_id": ...}}

    Example:
        >>> build_lineage("run_abc123")
        {"lineage": {"parent_plan_run_id": "run_abc123"}}

        >>> build_lineage(None)
        {"lineage": {"parent_plan_run_id": None}}
    """
    return {"lineage": {"parent_plan_run_id": parent_plan_run_id}}


def extract_parent_plan_run_id(artifact: Dict[str, Any]) -> Optional[str]:
    """
    Extract parent_plan_run_id from a run artifact.

    Checks multiple locations for backwards compatibility:
    1. artifact["lineage"]["parent_plan_run_id"]
    2. artifact["meta"]["parent_plan_run_id"]
    3. artifact["parent_plan_run_id"]

    Args:
        artifact: Run artifact dict

    Returns:
        parent_plan_run_id if found, None otherwise
    """
    # Primary location: lineage envelope
    lineage = artifact.get("lineage")
    if isinstance(lineage, dict):
        parent = lineage.get("parent_plan_run_id")
        if parent:
            return str(parent)

    # Fallback: meta field (some older code may put it here)
    meta = artifact.get("meta")
    if isinstance(meta, dict):
        parent = meta.get("parent_plan_run_id")
        if parent:
            return str(parent)

    # Fallback: top-level field
    parent = artifact.get("parent_plan_run_id")
    if parent:
        return str(parent)

    return None


def merge_lineage_into_artifact(
    artifact: Dict[str, Any],
    parent_plan_run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Merge lineage envelope into an artifact dict.

    Does not mutate the original; returns a new dict.

    Args:
        artifact: Run artifact dict
        parent_plan_run_id: Parent plan run_id to set

    Returns:
        New artifact dict with lineage merged
    """
    lineage = build_lineage(parent_plan_run_id)
    return {**artifact, **lineage}


def has_lineage(artifact: Dict[str, Any]) -> bool:
    """
    Check if an artifact has lineage information.

    Returns True if parent_plan_run_id is set and non-empty.
    """
    parent = extract_parent_plan_run_id(artifact)
    return parent is not None and parent.strip() != ""


def validate_lineage_consistency(
    plan_artifact: Dict[str, Any],
    execute_artifact: Dict[str, Any],
) -> bool:
    """
    Validate that an execute artifact correctly references a plan artifact.

    Args:
        plan_artifact: The plan artifact
        execute_artifact: The execute artifact that should reference the plan

    Returns:
        True if lineage is consistent (execute references plan's run_id)
    """
    plan_run_id = plan_artifact.get("run_id") or plan_artifact.get("id")
    execute_parent = extract_parent_plan_run_id(execute_artifact)

    if not plan_run_id:
        return False

    return execute_parent == plan_run_id
