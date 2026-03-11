"""
Saw Lab Artifact Helpers
========================

Centralized utilities for artifact dict access and timestamp extraction.

Resolves: SAW-LAB-GAP-01 (DRY violation - duplicate helpers across 7 files)

These helpers are used throughout the Saw Lab sector for safe access to
artifact dictionaries, timestamp extraction, and artifact metadata operations.
"""

from typing import Any, Dict, List, Optional


def as_dict(x: Any) -> Dict[str, Any]:
    """
    Safe dict coercion.

    Returns x if it's already a dict, otherwise returns empty dict.
    Prevents TypeError when accessing .get() on None or other types.
    """
    return x if isinstance(x, dict) else {}


def as_list(x: Any) -> List[Any]:
    """
    Safe list coercion.

    Returns x if it's already a list, otherwise returns empty list.
    Prevents TypeError when iterating over None or other types.
    """
    return x if isinstance(x, list) else []


def extract_created_utc(art: Dict[str, Any]) -> str:
    """
    Extract created_utc timestamp from artifact.

    Checks payload/data first, then root level.
    Returns empty string if not found.

    Args:
        art: Artifact dictionary (may have payload or data sub-dict)

    Returns:
        ISO timestamp string or empty string
    """
    p = as_dict(art.get("payload") or art.get("data"))
    if isinstance(p.get("created_utc"), str):
        return p["created_utc"]
    if isinstance(art.get("created_utc"), str):
        return art["created_utc"]
    return ""


def get_kind(a: Dict[str, Any]) -> str:
    """
    Get artifact kind from root or index_meta.

    Args:
        a: Artifact dictionary

    Returns:
        Kind string (e.g., "decision", "execution", "toolpaths")
    """
    return str(a.get("kind") or as_dict(a.get("index_meta")).get("kind") or "")


def get_artifact_id(a: Dict[str, Any]) -> Optional[str]:
    """
    Extract artifact ID from various locations.

    Checks id, artifact_id, and index_meta.id in order.

    Args:
        a: Artifact dictionary

    Returns:
        Artifact ID string or None
    """
    return a.get("id") or a.get("artifact_id") or as_dict(a.get("index_meta")).get("id")


def pick_latest(artifacts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Select most recent artifact by created_utc.

    Args:
        artifacts: List of artifact dictionaries

    Returns:
        Most recent artifact or None if list is empty
    """
    if not artifacts:
        return None
    return max(artifacts, key=lambda a: extract_created_utc(a))


def matches_parent_decision(art: Dict[str, Any], decision_id: str) -> bool:
    """
    Check if artifact references a parent decision.

    Args:
        art: Artifact dictionary
        decision_id: Decision ID to match

    Returns:
        True if artifact's parent_decision_id or decision_id matches
    """
    p = as_dict(art.get("payload") or art.get("data"))
    return p.get("parent_decision_id") == decision_id or p.get("decision_id") == decision_id


# Backwards-compatible aliases (will be removed in future version)
_as_dict = as_dict
_as_list = as_list
_created_utc = extract_created_utc
_extract_created_utc = extract_created_utc
_kind = get_kind
_artifact_id = get_artifact_id
_pick_latest = pick_latest
_matches_parent_decision = matches_parent_decision
