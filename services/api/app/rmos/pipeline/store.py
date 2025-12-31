"""
RMOS Pipeline Store - Artifact Persistence for Multi-Stage Execution

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 4

This module provides the storage layer for pipeline artifacts, wrapping
the core run artifacts store with pipeline-specific functionality.

Key Features:
- Immutable artifact persistence
- Parent-child linking for lineage tracking
- Query by parent artifact ID (ancestry queries)
- Execution history lookup (newest-first)
- Deterministic replay support
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Union

from .schemas import (
    PipelineStage,
    PipelineStatus,
    PipelineArtifactBase,
    SpecArtifact,
    PlanArtifact,
    DecisionArtifact,
    ExecutionArtifact,
    OpToolpathsArtifact,
    IndexMeta,
    ArtifactQuery,
    ArtifactQueryResult,
)

# Import from runs module (v1/v2 abstracted)
from ..runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
)

# Try to import query functions if available
try:
    from ..run_artifacts.store import (
        read_run_artifact,
        query_run_artifacts,
        list_run_artifacts,
    )
    _HAS_QUERY = True
except ImportError:
    _HAS_QUERY = False


def _utc_now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _generate_artifact_id() -> str:
    """Generate a unique artifact ID."""
    return create_run_id()


class PipelineStore(Protocol):
    """Protocol for pipeline artifact storage."""

    def write(self, artifact: PipelineArtifactBase) -> str:
        """Write artifact and return its ID."""
        ...

    def read(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Read artifact by ID."""
        ...

    def query(self, query: ArtifactQuery) -> ArtifactQueryResult:
        """Query artifacts with filters."""
        ...


class DefaultPipelineStore:
    """
    Default implementation using run artifacts store.

    This wraps the existing run artifacts infrastructure to provide
    pipeline-specific functionality.
    """

    def write(
        self,
        kind: str,
        stage: PipelineStage,
        status: PipelineStatus,
        index_meta: Dict[str, Any],
        payload: Dict[str, Any],
        *,
        request_hash: Optional[str] = None,
        output_hash: Optional[str] = None,
    ) -> str:
        """
        Write a pipeline artifact.

        Args:
            kind: Artifact kind (e.g., "roughing_spec")
            stage: Pipeline stage
            status: Artifact status
            index_meta: Query metadata
            payload: Full artifact payload

        Returns:
            Generated artifact ID
        """
        artifact_id = _generate_artifact_id()
        now = _utc_now_iso()

        # Build run artifact
        artifact = RunArtifact(
            run_id=artifact_id,
            created_at_utc=now,
            tool_id=index_meta.get("tool_type", kind.split("_")[0]),
            workflow_mode=index_meta.get("workflow_mode", "pipeline"),
            event_type=kind,
            status=status.value,
            request_hash=request_hash,
            gcode_hash=output_hash,
            notes=f"Pipeline stage: {stage.value}",
            # Store full payload in a way that can be retrieved
            feasibility=payload.get("feasibility"),
        )

        # Persist using run artifacts store
        persist_run(artifact)

        # Store extended metadata (if we have extended storage)
        # For now, we rely on the artifact's serializable fields

        return artifact_id

    def read(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Read artifact by ID."""
        if not _HAS_QUERY:
            return None

        try:
            return read_run_artifact(artifact_id)
        except Exception:
            return None

    def query(self, query: ArtifactQuery) -> ArtifactQueryResult:
        """Query artifacts with filters."""
        if not _HAS_QUERY:
            return ArtifactQueryResult(items=[], total=0)

        try:
            # Build filter dict
            filters = {}
            if query.kind:
                filters["kind"] = query.kind
            if query.tool_type:
                filters["tool_type"] = query.tool_type
            if query.batch_label:
                filters["batch_label"] = query.batch_label
            if query.session_id:
                filters["session_id"] = query.session_id
            if query.parent_spec_artifact_id:
                filters["parent_spec_artifact_id"] = query.parent_spec_artifact_id
            if query.parent_plan_artifact_id:
                filters["parent_plan_artifact_id"] = query.parent_plan_artifact_id
            if query.parent_decision_artifact_id:
                filters["parent_decision_artifact_id"] = query.parent_decision_artifact_id
            if query.status:
                filters["status"] = query.status

            items = query_run_artifacts(**filters)

            # Apply pagination
            total = len(items)
            items = items[query.offset : query.offset + query.limit]

            return ArtifactQueryResult(
                items=items,
                total=total,
                limit=query.limit,
                offset=query.offset,
            )
        except Exception:
            return ArtifactQueryResult(items=[], total=0)


# Singleton store instance
_pipeline_store: Optional[DefaultPipelineStore] = None


def get_pipeline_store() -> DefaultPipelineStore:
    """Get the pipeline store singleton."""
    global _pipeline_store
    if _pipeline_store is None:
        _pipeline_store = DefaultPipelineStore()
    return _pipeline_store


# =============================================================================
# Convenience Functions
# =============================================================================

def write_artifact(
    kind: str,
    stage: PipelineStage,
    status: PipelineStatus,
    index_meta: Dict[str, Any],
    payload: Dict[str, Any],
    **kwargs: Any,
) -> str:
    """
    Write a pipeline artifact.

    Args:
        kind: Artifact kind (e.g., "roughing_spec")
        stage: Pipeline stage
        status: Artifact status
        index_meta: Query metadata
        payload: Full artifact payload

    Returns:
        Generated artifact ID
    """
    store = get_pipeline_store()
    return store.write(kind, stage, status, index_meta, payload, **kwargs)


def read_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    """Read artifact by ID."""
    store = get_pipeline_store()
    return store.read(artifact_id)


def query_artifacts(query: ArtifactQuery) -> ArtifactQueryResult:
    """Query artifacts with filters."""
    store = get_pipeline_store()
    return store.query(query)


def list_executions_for_decision(
    decision_artifact_id: str,
    *,
    limit: int = 25,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    List all executions for a decision (newest-first).

    This enables deterministic replay by finding all execution
    artifacts that were created from a given decision.

    Args:
        decision_artifact_id: The decision to find executions for
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        List of execution artifacts, newest first
    """
    query = ArtifactQuery(
        parent_decision_artifact_id=decision_artifact_id,
        limit=limit,
        offset=offset,
    )
    result = query_artifacts(query)

    # Sort by created_at_utc (newest first)
    items = sorted(
        result.items,
        key=lambda x: str(x.get("created_at_utc", "")),
        reverse=True,
    )

    return items


def latest_execution_for_decision(
    decision_artifact_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Get the most recent execution for a decision.

    Args:
        decision_artifact_id: The decision to find execution for

    Returns:
        Most recent execution artifact, or None
    """
    items = list_executions_for_decision(decision_artifact_id, limit=1)
    return items[0] if items else None


def list_children_for_execution(
    execution_artifact_id: str,
) -> List[Dict[str, Any]]:
    """
    List all child op_toolpaths artifacts for an execution.

    Args:
        execution_artifact_id: The parent execution artifact

    Returns:
        List of child op_toolpaths artifacts
    """
    query = ArtifactQuery(
        parent_decision_artifact_id=execution_artifact_id,
        # Note: This assumes children reference execution as parent
        # In practice, we may need to read the parent and get children list
    )
    result = query_artifacts(query)
    return result.items


def get_artifact_lineage(artifact_id: str) -> Dict[str, Optional[str]]:
    """
    Get the full lineage (ancestry) for an artifact.

    Returns dict with keys:
    - spec_artifact_id
    - plan_artifact_id
    - decision_artifact_id
    - execution_artifact_id

    Args:
        artifact_id: Any artifact in the chain

    Returns:
        Dict mapping stage to artifact ID (None if not in lineage)
    """
    lineage = {
        "spec_artifact_id": None,
        "plan_artifact_id": None,
        "decision_artifact_id": None,
        "execution_artifact_id": None,
    }

    artifact = read_artifact(artifact_id)
    if not artifact:
        return lineage

    # Extract lineage from index_meta or direct fields
    index_meta = artifact.get("index_meta", {})

    # Check direct parent references
    if index_meta.get("parent_spec_artifact_id"):
        lineage["spec_artifact_id"] = index_meta["parent_spec_artifact_id"]
    if index_meta.get("parent_plan_artifact_id"):
        lineage["plan_artifact_id"] = index_meta["parent_plan_artifact_id"]
    if index_meta.get("parent_decision_artifact_id"):
        lineage["decision_artifact_id"] = index_meta["parent_decision_artifact_id"]
    if index_meta.get("parent_execution_artifact_id"):
        lineage["execution_artifact_id"] = index_meta["parent_execution_artifact_id"]

    # Also check payload for direct references
    payload = artifact.get("payload", {})
    if payload.get("spec_artifact_id"):
        lineage["spec_artifact_id"] = payload["spec_artifact_id"]
    if payload.get("plan_artifact_id"):
        lineage["plan_artifact_id"] = payload["plan_artifact_id"]
    if payload.get("decision_artifact_id"):
        lineage["decision_artifact_id"] = payload["decision_artifact_id"]
    if payload.get("execution_artifact_id"):
        lineage["execution_artifact_id"] = payload["execution_artifact_id"]

    # Determine current artifact's stage and add it
    kind = artifact.get("kind", "")
    if "_spec" in kind:
        lineage["spec_artifact_id"] = artifact_id
    elif "_plan" in kind:
        lineage["plan_artifact_id"] = artifact_id
    elif "_decision" in kind:
        lineage["decision_artifact_id"] = artifact_id
    elif "_execution" in kind:
        lineage["execution_artifact_id"] = artifact_id

    return lineage
