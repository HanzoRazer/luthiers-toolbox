"""
Luthier Operation Workspace

CAM Dev Order 7S: Local-first, serializable workspace artifact.

Provides:
  - LuthierOperationWorkspaceV1 model
  - Workspace lifecycle (draft → validated → export_ready)
  - Geometry and export object references
  - Strategy binding
  - Serialization for local storage

7S invariants:
  - executable_payload_present always False
  - machine_output_allowed always False
  - gcode_content always None

Salvaged pattern:
  .obc (OpenBuilds-CAM project file) concept — local-first workspace
  serialization with geometry + operation references. Implementation
  is repo-native; no OpenBuilds code imported.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


WorkspaceStatus = Literal[
    "draft",
    "geometry_bound",
    "strategy_attached",
    "validated",
    "export_ready",
    "archived",
]

OperationFamily = Literal[
    "rosette",
    "binding_channel",
    "neck_profile",
    "fret_slotting",
    "bridge_location",
    "body_outline",
    "fixture_setup",
    "inspection",
    "soundhole",
    "headstock",
    "bracing",
    "inlay",
    "carving",
    "drilling",
    "custom",
]


class GeometryReference(BaseModel):
    """
    Reference to geometry in the export object or IBG layer.

    Does NOT contain actual geometry data — just references.
    """

    reference_id: str = Field(
        default_factory=lambda: f"geo-ref-{uuid4().hex[:8]}",
        description="Unique reference identifier"
    )
    reference_type: Literal["export_object", "ibg_layer", "contour", "point_set"] = Field(
        ..., description="Type of geometry reference"
    )
    source_id: str = Field(..., description="ID of the source object")
    layer_name: Optional[str] = Field(
        default=None, description="Layer name if applicable"
    )
    description: str = Field(default="", description="Human description")


class WorkspaceValidationResult(BaseModel):
    """
    Result of workspace validation check.

    Validation checks geometry bindings, strategy attachment,
    and modality compatibility. Does NOT validate for execution.
    """

    valid: bool = Field(..., description="Whether validation passed")
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Validation timestamp"
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Validation issues found"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )


class LuthierOperationWorkspaceV1(BaseModel):
    """
    Local-first workspace artifact for luthier CAM operations.

    Workspaces collect geometry references, strategies, and operation
    metadata into a serializable artifact for local storage and
    collaboration.

    7S invariants (model-enforced):
      - executable_payload_present always False
      - machine_output_allowed always False
      - gcode_content always None

    Inspired by OpenBuilds .obc concept but repo-native.
    """

    workspace_id: str = Field(
        default_factory=lambda: f"ws-{uuid4().hex[:12]}",
        description="Unique workspace identifier"
    )
    workspace_version: str = Field(
        default="1.0",
        description="Workspace schema version"
    )

    title: str = Field(..., description="Human-readable workspace title")
    description: str = Field(default="", description="Workspace description")

    operation_family: OperationFamily = Field(
        ..., description="Primary operation family"
    )
    modality_id: Optional[str] = Field(
        default=None,
        description="Bound modality ID from CAM_OPERATION_MODALITY_INDEX"
    )

    geometry_references: List[GeometryReference] = Field(
        default_factory=list,
        description="References to bound geometry"
    )

    export_object_ids: List[str] = Field(
        default_factory=list,
        description="IDs of related export objects"
    )

    strategy_ids: List[str] = Field(
        default_factory=list,
        description="IDs of attached manufacturing strategies"
    )

    status: WorkspaceStatus = Field(
        default="draft",
        description="Workspace lifecycle status"
    )

    review_status: Literal[
        "not_reviewed",
        "pending_review",
        "approved",
        "rejected",
        "deferred",
    ] = Field(
        default="not_reviewed",
        description="Human review status"
    )

    validation_result: Optional[WorkspaceValidationResult] = Field(
        default=None,
        description="Most recent validation result"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="User-defined tags"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible metadata"
    )

    executable_payload_present: bool = Field(
        default=False,
        description="Always False — 7S workspaces contain no executable payloads"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7S does not allow machine output"
    )
    gcode_content: Optional[str] = Field(
        default=None,
        description="Always None — 7S does not store G-code"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
    )

    deterministic_hash: str = Field(
        default="",
        description="Deterministic hash of workspace state"
    )

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "LuthierOperationWorkspaceV1":
        """
        Enforce 7S invariants:
        - executable_payload_present must be False
        - machine_output_allowed must be False
        - gcode_content must be None
        """
        if self.executable_payload_present:
            raise ValueError(
                "7S invariant violation: executable_payload_present must be False — "
                "7S workspaces contain no executable payloads"
            )

        if self.machine_output_allowed:
            raise ValueError(
                "7S invariant violation: machine_output_allowed must be False — "
                "7S does not allow machine output"
            )

        if self.gcode_content is not None:
            raise ValueError(
                "7S invariant violation: gcode_content must be None — "
                "7S does not store G-code"
            )

        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of workspace state."""
        hash_input = {
            "workspace_id": self.workspace_id,
            "title": self.title,
            "operation_family": self.operation_family,
            "modality_id": self.modality_id,
            "geometry_references": [
                {
                    "reference_id": ref.reference_id,
                    "reference_type": ref.reference_type,
                    "source_id": ref.source_id,
                }
                for ref in self.geometry_references
            ],
            "export_object_ids": sorted(self.export_object_ids),
            "strategy_ids": sorted(self.strategy_ids),
            "status": self.status,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


LUTHIER_WORKSPACE_INDEX: Dict[str, LuthierOperationWorkspaceV1] = {}


def create_workspace(
    title: str,
    operation_family: OperationFamily,
    modality_id: Optional[str] = None,
    description: str = "",
    tags: Optional[List[str]] = None,
) -> LuthierOperationWorkspaceV1:
    """
    Create a new workspace artifact.

    Creates in draft status. Compute hash on creation.

    Args:
        title: Human-readable title
        operation_family: Primary operation family
        modality_id: Optional bound modality
        description: Optional description
        tags: Optional tags

    Returns: New workspace in draft status
    """
    workspace = LuthierOperationWorkspaceV1(
        title=title,
        operation_family=operation_family,
        modality_id=modality_id,
        description=description,
        tags=tags or [],
    )

    workspace.deterministic_hash = workspace.compute_hash()

    LUTHIER_WORKSPACE_INDEX[workspace.workspace_id] = workspace

    return workspace


def get_workspace(workspace_id: str) -> Optional[LuthierOperationWorkspaceV1]:
    """Get workspace by ID."""
    return LUTHIER_WORKSPACE_INDEX.get(workspace_id)


def list_workspaces() -> List[LuthierOperationWorkspaceV1]:
    """List all workspaces."""
    return list(LUTHIER_WORKSPACE_INDEX.values())


def list_workspaces_by_family(
    family: OperationFamily,
) -> List[LuthierOperationWorkspaceV1]:
    """List workspaces by operation family."""
    return [
        ws for ws in LUTHIER_WORKSPACE_INDEX.values()
        if ws.operation_family == family
    ]


def list_workspaces_by_status(
    status: WorkspaceStatus,
) -> List[LuthierOperationWorkspaceV1]:
    """List workspaces by status."""
    return [
        ws for ws in LUTHIER_WORKSPACE_INDEX.values()
        if ws.status == status
    ]


def add_geometry_reference(
    workspace_id: str,
    reference: GeometryReference,
) -> Optional[LuthierOperationWorkspaceV1]:
    """
    Add a geometry reference to a workspace.

    Updates workspace status and hash.

    Args:
        workspace_id: Workspace to update
        reference: Geometry reference to add

    Returns: Updated workspace or None if not found
    """
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None

    workspace.geometry_references.append(reference)
    workspace.updated_at = datetime.now(timezone.utc)

    if workspace.status == "draft" and workspace.geometry_references:
        workspace.status = "geometry_bound"

    workspace.deterministic_hash = workspace.compute_hash()

    return workspace


def attach_strategy(
    workspace_id: str,
    strategy_id: str,
) -> Optional[LuthierOperationWorkspaceV1]:
    """
    Attach a manufacturing strategy to a workspace.

    Updates workspace status and hash.

    Args:
        workspace_id: Workspace to update
        strategy_id: Strategy ID to attach

    Returns: Updated workspace or None if not found
    """
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None

    if strategy_id not in workspace.strategy_ids:
        workspace.strategy_ids.append(strategy_id)
        workspace.updated_at = datetime.now(timezone.utc)

        if workspace.status in ("draft", "geometry_bound") and workspace.strategy_ids:
            workspace.status = "strategy_attached"

        workspace.deterministic_hash = workspace.compute_hash()

    return workspace


def bind_export_object(
    workspace_id: str,
    export_object_id: str,
) -> Optional[LuthierOperationWorkspaceV1]:
    """
    Bind an export object to a workspace.

    Args:
        workspace_id: Workspace to update
        export_object_id: Export object ID to bind

    Returns: Updated workspace or None if not found
    """
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None

    if export_object_id not in workspace.export_object_ids:
        workspace.export_object_ids.append(export_object_id)
        workspace.updated_at = datetime.now(timezone.utc)
        workspace.deterministic_hash = workspace.compute_hash()

    return workspace


def validate_workspace(
    workspace_id: str,
) -> Optional[WorkspaceValidationResult]:
    """
    Validate a workspace for completeness.

    Checks:
    - Has geometry references
    - Has at least one strategy (for non-draft workspaces)
    - Modality is bound

    Does NOT validate for execution readiness (7S invariant).

    Args:
        workspace_id: Workspace to validate

    Returns: Validation result or None if workspace not found
    """
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None

    issues: List[str] = []
    warnings: List[str] = []

    if not workspace.geometry_references:
        issues.append("No geometry references bound")

    if workspace.status != "draft" and not workspace.strategy_ids:
        issues.append("No manufacturing strategies attached")

    if not workspace.modality_id:
        warnings.append("No operation modality bound")

    if not workspace.export_object_ids:
        warnings.append("No export objects bound")

    result = WorkspaceValidationResult(
        valid=len(issues) == 0,
        issues=issues,
        warnings=warnings,
    )

    workspace.validation_result = result
    workspace.updated_at = datetime.now(timezone.utc)

    if result.valid and workspace.status == "strategy_attached":
        workspace.status = "validated"
        workspace.deterministic_hash = workspace.compute_hash()

    return result


def promote_to_export_ready(
    workspace_id: str,
) -> Optional[LuthierOperationWorkspaceV1]:
    """
    Promote a validated workspace to export_ready status.

    Requires:
    - Workspace must be in validated status
    - Validation must have passed

    Does NOT generate export — just marks as ready for export review.

    Args:
        workspace_id: Workspace to promote

    Returns: Updated workspace or None if not found or invalid
    """
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None

    if workspace.status != "validated":
        return None

    if not workspace.validation_result or not workspace.validation_result.valid:
        return None

    workspace.status = "export_ready"
    workspace.updated_at = datetime.now(timezone.utc)
    workspace.deterministic_hash = workspace.compute_hash()

    return workspace


def archive_workspace(
    workspace_id: str,
) -> Optional[LuthierOperationWorkspaceV1]:
    """
    Archive a workspace.

    Archived workspaces are retained for lineage but no longer active.

    Args:
        workspace_id: Workspace to archive

    Returns: Updated workspace or None if not found
    """
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None

    workspace.status = "archived"
    workspace.updated_at = datetime.now(timezone.utc)
    workspace.deterministic_hash = workspace.compute_hash()

    return workspace


def serialize_workspace(workspace_id: str) -> Optional[str]:
    """
    Serialize a workspace to JSON for local storage.

    This is the local-first serialization pattern inspired by
    OpenBuilds .obc files.

    Args:
        workspace_id: Workspace to serialize

    Returns: JSON string or None if not found
    """
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None

    return workspace.model_dump_json(indent=2)


def deserialize_workspace(json_str: str) -> LuthierOperationWorkspaceV1:
    """
    Deserialize a workspace from JSON.

    Registers the workspace in the index after deserialization.

    Args:
        json_str: JSON string to deserialize

    Returns: Deserialized workspace

    Raises: ValueError if JSON is invalid or violates 7S invariants
    """
    workspace = LuthierOperationWorkspaceV1.model_validate_json(json_str)

    LUTHIER_WORKSPACE_INDEX[workspace.workspace_id] = workspace

    return workspace


def clear_workspace_index() -> None:
    """Clear workspace index (for testing)."""
    LUTHIER_WORKSPACE_INDEX.clear()
