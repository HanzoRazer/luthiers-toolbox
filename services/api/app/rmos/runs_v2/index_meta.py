"""
Index Meta Normalization + Validation (System 2 Hardening)

Centralizes index_meta governance for Option B reporting/export features.

Key Functions:
- normalize_index_meta(): Canonicalizes metadata to prevent drift
- validate_index_meta(): Enforces repo-wide invariants
- set_parent_links(): Typed parent pointers for batch tree navigation

Per: Platform Invariants System 2 spec
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class IndexMetaError(ValueError):
    """Raised when index_meta fails validation."""
    pass


def set_parent_links(
    index_meta: Dict[str, Any],
    *,
    spec_id: Optional[str] = None,
    plan_id: Optional[str] = None,
    decision_id: Optional[str] = None,
    toolpaths_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    parent_artifact_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Typed parent pointers used by Option B reporting/export.
    Keep both typed pointers and a generic parent_artifact_id when available.
    """
    if spec_id:
        index_meta["parent_batch_spec_artifact_id"] = spec_id
    if plan_id:
        index_meta["parent_batch_plan_artifact_id"] = plan_id
    if decision_id:
        index_meta["parent_batch_decision_artifact_id"] = decision_id
    if toolpaths_id:
        index_meta["parent_batch_toolpaths_artifact_id"] = toolpaths_id
    if execution_id:
        index_meta["parent_batch_execution_artifact_id"] = execution_id
    if parent_artifact_id:
        index_meta["parent_artifact_id"] = parent_artifact_id
    return index_meta


def normalize_index_meta(
    *,
    event_type: Optional[str] = None,
    index_meta: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: Optional[str] = None,
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    parent_artifact_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Canonicalizes index_meta to prevent drift. This is the *single source of truth*
    for index_meta composition.

    Rules:
      - Always return a dict
      - Promote known top-level params into index_meta if missing
      - Normalize known keys to strings
      - Preserve existing keys (do not delete)

    Args:
        event_type: The artifact kind/event_type (e.g., "saw_batch_plan")
        index_meta: Existing metadata dict to normalize
        session_id: Workflow session identifier
        batch_label: Batch label for grouping
        tool_kind: Tool category (e.g., "saw", "router")
        tool_id: Specific tool identifier
        material_id: Material identifier
        parent_artifact_id: Generic parent link
    """
    meta: Dict[str, Any] = dict(index_meta or {})

    # Canonical kind/event_type presence
    if event_type:
        meta["kind"] = meta.get("kind") or event_type
        meta["event_type"] = meta.get("event_type") or event_type

    # Promote common filters used by reporting
    if session_id and not meta.get("session_id"):
        meta["session_id"] = session_id
    if batch_label and not meta.get("batch_label"):
        meta["batch_label"] = batch_label
    if tool_kind and not meta.get("tool_kind"):
        meta["tool_kind"] = tool_kind
    if tool_id and not meta.get("tool_id"):
        meta["tool_id"] = tool_id
    if material_id and not meta.get("material_id"):
        meta["material_id"] = material_id
    if parent_artifact_id and not meta.get("parent_artifact_id"):
        meta["parent_artifact_id"] = parent_artifact_id

    # Stringify key identifiers (stable querying)
    for k in (
        "kind",
        "event_type",
        "session_id",
        "batch_label",
        "tool_kind",
        "tool_id",
        "material_id",
        "parent_artifact_id",
        "parent_batch_spec_artifact_id",
        "parent_batch_plan_artifact_id",
        "parent_batch_decision_artifact_id",
        "parent_batch_toolpaths_artifact_id",
        "parent_batch_execution_artifact_id",
    ):
        if k in meta and meta[k] is not None and not isinstance(meta[k], str):
            meta[k] = str(meta[k])

    return meta


def validate_index_meta(
    meta: Dict[str, Any],
    *,
    event_type: Optional[str] = None,
    strict: bool = False,
) -> None:
    """
    Enforces repo-wide invariants. Keep it strict on the keys Option B depends on.

    Required keys (when strict=True):
      - meta.session_id
      - meta.batch_label
      - meta.tool_kind

    Parent linkage invariants (by event_type name):
      - *plan*      -> should link to spec
      - *decision*  -> should link to plan
      - *toolpaths* -> should link to decision
      - *execution* -> should link to decision (or toolpaths)

    Args:
        meta: The index_meta dict to validate
        event_type: The artifact kind/event_type for context-specific rules
        strict: If True, enforce all required keys; if False, warn-only mode

    Raises:
        IndexMetaError: If validation fails in strict mode
    """
    if not isinstance(meta, dict):
        raise IndexMetaError("index_meta must be a dict")

    # Determine the kind from event_type or meta
    k = (event_type or meta.get("event_type") or meta.get("kind") or "").lower()

    # In strict mode, enforce required keys
    if strict:
        for req in ("session_id", "batch_label", "tool_kind"):
            if not meta.get(req):
                raise IndexMetaError(f"missing index_meta.{req}")

    def _need(key: str, msg: str) -> None:
        if strict and not meta.get(key):
            raise IndexMetaError(msg)

    # Parent linkage rules (lightweight but high-signal)
    # Only enforce in strict mode
    if "plan" in k and "spec" not in k:
        _need(
            "parent_batch_spec_artifact_id",
            "plan missing parent spec link (parent_batch_spec_artifact_id)"
        )
    if "decision" in k or "approve" in k:
        if not (meta.get("parent_batch_plan_artifact_id") or meta.get("parent_artifact_id")):
            if strict:
                raise IndexMetaError(
                    "decision missing parent plan link (parent_batch_plan_artifact_id|parent_artifact_id)"
                )
    if "toolpaths" in k:
        if not (meta.get("parent_batch_decision_artifact_id") or meta.get("parent_artifact_id")):
            if strict:
                raise IndexMetaError(
                    "toolpaths missing parent decision link (parent_batch_decision_artifact_id|parent_artifact_id)"
                )
    if "execution" in k:
        if not (meta.get("parent_batch_decision_artifact_id") or meta.get("parent_artifact_id")):
            if strict:
                raise IndexMetaError(
                    "execution missing parent decision link (parent_batch_decision_artifact_id|parent_artifact_id)"
                )


def extract_and_normalize_from_artifact(artifact: "RunArtifact") -> Dict[str, Any]:
    """
    Extract index_meta from a RunArtifact and normalize it.

    This is a convenience function that bridges the artifact model
    to the normalization layer.

    Args:
        artifact: The RunArtifact to extract metadata from

    Returns:
        Normalized index_meta dict
    """
    # Import here to avoid circular dependency
    from .schemas import RunArtifact

    # Extract base metadata from artifact.meta
    base_meta = dict(artifact.meta) if artifact.meta else {}

    # Extract event_type if available
    event_type = getattr(artifact, 'event_type', None)

    # Normalize with artifact fields
    return normalize_index_meta(
        event_type=event_type,
        index_meta=base_meta,
        session_id=base_meta.get("session_id"),
        batch_label=base_meta.get("batch_label"),
        tool_kind=artifact.mode,  # mode maps to tool_kind
        tool_id=artifact.tool_id,
        material_id=getattr(artifact, 'material_id', None),
        parent_artifact_id=base_meta.get("parent_artifact_id"),
    )
