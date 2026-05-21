"""
Luthier Operation Workspace

CAM Dev Order 7S: Local-first, serializable workspace artifact.

7S invariants:
  - executable_payload_present always False
  - machine_output_allowed always False
  - gcode_content always None
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


WorkspaceStatus = Literal["draft", "geometry_bound", "strategy_attached", "validated", "export_ready", "archived"]
OperationFamily = Literal[
    "rosette", "binding_channel", "neck_profile", "fret_slotting", "bridge_location",
    "body_outline", "fixture_setup", "inspection", "soundhole", "headstock", "bracing", "custom",
]


class GeometryReference(BaseModel):
    """Reference to geometry in the export object or IBG layer."""

    reference_id: str = Field(default_factory=lambda: f"geo-ref-{uuid4().hex[:8]}")
    reference_type: Literal["export_object", "ibg_layer", "contour", "point_set"]
    source_id: str
    layer_name: Optional[str] = None
    description: str = ""
    geometry_authority_ref_id: Optional[str] = None


class WorkspaceValidationResult(BaseModel):
    """Result of workspace validation check."""

    valid: bool
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class LuthierOperationWorkspaceV1(BaseModel):
    """Local-first workspace artifact for luthier CAM operations."""

    workspace_id: str = Field(default_factory=lambda: f"ws-{uuid4().hex[:12]}")
    title: str
    description: str = ""
    operation_family: OperationFamily
    modality_id: Optional[str] = None

    geometry_references: List[GeometryReference] = Field(default_factory=list)
    geometry_authority_ref_id: Optional[str] = None
    export_object_ids: List[str] = Field(default_factory=list)
    strategy_ids: List[str] = Field(default_factory=list)

    # 7V: Fixture topology cognition package refs (workspace may reference, not mutate)
    fixture_package_refs: List[str] = Field(default_factory=list)

    status: WorkspaceStatus = "draft"
    review_status: Literal["not_reviewed", "pending_review", "approved", "rejected", "deferred"] = "not_reviewed"
    validation_result: Optional[WorkspaceValidationResult] = None

    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    executable_payload_present: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)
    gcode_content: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "LuthierOperationWorkspaceV1":
        if self.executable_payload_present:
            raise ValueError("7S invariant violation: executable_payload_present must be False")
        if self.machine_output_allowed:
            raise ValueError("7S invariant violation: machine_output_allowed must be False")
        if self.gcode_content is not None:
            raise ValueError("7S invariant violation: gcode_content must be None")
        return self


LUTHIER_WORKSPACE_INDEX: Dict[str, LuthierOperationWorkspaceV1] = {}


def create_workspace(
    title: str,
    operation_family: OperationFamily,
    modality_id: Optional[str] = None,
    description: str = "",
    tags: Optional[List[str]] = None,
) -> LuthierOperationWorkspaceV1:
    workspace = LuthierOperationWorkspaceV1(
        title=title,
        operation_family=operation_family,
        modality_id=modality_id,
        description=description,
        tags=tags or [],
    )
    LUTHIER_WORKSPACE_INDEX[workspace.workspace_id] = workspace
    return workspace


def get_workspace(workspace_id: str) -> Optional[LuthierOperationWorkspaceV1]:
    return LUTHIER_WORKSPACE_INDEX.get(workspace_id)


def list_workspaces() -> List[LuthierOperationWorkspaceV1]:
    return list(LUTHIER_WORKSPACE_INDEX.values())


def list_workspaces_by_family(family: OperationFamily) -> List[LuthierOperationWorkspaceV1]:
    return [ws for ws in LUTHIER_WORKSPACE_INDEX.values() if ws.operation_family == family]


def list_workspaces_by_status(status: WorkspaceStatus) -> List[LuthierOperationWorkspaceV1]:
    return [ws for ws in LUTHIER_WORKSPACE_INDEX.values() if ws.status == status]


def add_geometry_reference(workspace_id: str, reference: GeometryReference) -> Optional[LuthierOperationWorkspaceV1]:
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None
    workspace.geometry_references.append(reference)
    workspace.updated_at = datetime.now(timezone.utc)
    if workspace.status == "draft" and workspace.geometry_references:
        workspace.status = "geometry_bound"
    return workspace


def attach_strategy(workspace_id: str, strategy_id: str) -> Optional[LuthierOperationWorkspaceV1]:
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None
    if strategy_id not in workspace.strategy_ids:
        workspace.strategy_ids.append(strategy_id)
        workspace.updated_at = datetime.now(timezone.utc)
        if workspace.status in ("draft", "geometry_bound"):
            workspace.status = "strategy_attached"
    return workspace


def bind_export_object(workspace_id: str, export_object_id: str) -> Optional[LuthierOperationWorkspaceV1]:
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None
    if export_object_id not in workspace.export_object_ids:
        workspace.export_object_ids.append(export_object_id)
        workspace.updated_at = datetime.now(timezone.utc)
    return workspace


def validate_workspace(workspace_id: str) -> Optional[WorkspaceValidationResult]:
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
    result = WorkspaceValidationResult(valid=len(issues) == 0, issues=issues, warnings=warnings)
    workspace.validation_result = result
    workspace.updated_at = datetime.now(timezone.utc)
    if result.valid and workspace.status == "strategy_attached":
        workspace.status = "validated"
    return result


def promote_to_export_ready(workspace_id: str) -> Optional[LuthierOperationWorkspaceV1]:
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace or workspace.status != "validated":
        return None
    if not workspace.validation_result or not workspace.validation_result.valid:
        return None
    workspace.status = "export_ready"
    workspace.updated_at = datetime.now(timezone.utc)
    return workspace


def archive_workspace(workspace_id: str) -> Optional[LuthierOperationWorkspaceV1]:
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None
    workspace.status = "archived"
    workspace.updated_at = datetime.now(timezone.utc)
    return workspace


def serialize_workspace(workspace_id: str) -> Optional[str]:
    workspace = LUTHIER_WORKSPACE_INDEX.get(workspace_id)
    if not workspace:
        return None
    return workspace.model_dump_json(indent=2)


def deserialize_workspace(json_str: str) -> LuthierOperationWorkspaceV1:
    workspace = LuthierOperationWorkspaceV1.model_validate_json(json_str)
    LUTHIER_WORKSPACE_INDEX[workspace.workspace_id] = workspace
    return workspace


def clear_workspace_index() -> None:
    LUTHIER_WORKSPACE_INDEX.clear()
