"""
CAM Operation Manifest Schema

Dev Order 57: Governed dispatch result contract.
Dev Order 58: Added result ID references for traceability.

Hard invariants:
- execution_ready is always False
- machine_operation_authorized is always False

The dispatcher does not authorize machine execution.
"""

import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RuntimeArtifactV1(BaseModel):
    """Artifact produced during dispatch."""

    artifact_id: str = Field(default_factory=lambda: f"artifact-{uuid.uuid4().hex[:12]}")
    artifact_type: Literal[
        "validation_report",
        "geometry_resolution",
        "plan_placeholder",
        "preview_placeholder",
        "export_placeholder",
    ]
    status: Literal["available", "placeholder", "unsupported", "error"]
    summary: str


class OperationManifestV1(BaseModel):
    """
    Governed dispatch result for CAM runtime operations.

    This manifest records what happened during dispatch without
    authorizing any machine execution.

    Hard invariants (enforced by validators):
    - execution_ready is always False
    - machine_operation_authorized is always False
    """

    manifest_id: str = Field(default_factory=lambda: f"manifest-{uuid.uuid4().hex[:12]}")
    schema_version: Literal["operation-manifest.v1"] = "operation-manifest.v1"

    intent_id: str | None = None
    operation_type: str
    runtime_id: str | None = None

    dispatch_status: Literal[
        "unsupported_operation",
        "validated_only",
        "planned_placeholder",
        "runtime_error",
    ]

    validation_gate: Literal["green", "yellow", "red"]

    # Result ID references for traceability (Dev Order 58)
    validation_result_id: str | None = None
    geometry_result_id: str | None = None
    plan_result_id: str | None = None
    preview_result_id: str | None = None
    export_result_id: str | None = None

    execution_ready: Literal[False] = Field(
        default=False,
        description="Always False. Dispatcher does not authorize execution.",
    )
    machine_operation_authorized: Literal[False] = Field(
        default=False,
        description="Always False. Dispatcher does not authorize machine operation.",
    )

    provenance: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    artifacts: list[RuntimeArtifactV1] = Field(default_factory=list)

    @field_validator("execution_ready", mode="before")
    @classmethod
    def enforce_execution_not_ready(cls, v: bool) -> Literal[False]:
        """Enforce that execution_ready is always False."""
        if v is True:
            raise ValueError("execution_ready must always be False")
        return False

    @field_validator("machine_operation_authorized", mode="before")
    @classmethod
    def enforce_machine_not_authorized(cls, v: bool) -> Literal[False]:
        """Enforce that machine_operation_authorized is always False."""
        if v is True:
            raise ValueError("machine_operation_authorized must always be False")
        return False


def create_unsupported_manifest(
    operation_type: str,
    intent_id: str | None = None,
    reason: str | None = None,
) -> OperationManifestV1:
    """
    Create a manifest for an unsupported operation.

    Returns RED validation gate with unsupported_operation status.
    """
    diagnostic = reason or f"No runtime plugin registered for operation_type '{operation_type}'"
    return OperationManifestV1(
        intent_id=intent_id,
        operation_type=operation_type,
        runtime_id=None,
        dispatch_status="unsupported_operation",
        validation_gate="red",
        provenance=["dispatcher:unsupported_operation"],
        diagnostics=[diagnostic],
        artifacts=[],
    )


def create_runtime_error_manifest(
    operation_type: str,
    runtime_id: str,
    intent_id: str | None = None,
    error: str | None = None,
) -> OperationManifestV1:
    """
    Create a manifest for a runtime error.

    Returns RED validation gate with runtime_error status.
    No execution authorization even on error path.
    """
    return OperationManifestV1(
        intent_id=intent_id,
        operation_type=operation_type,
        runtime_id=runtime_id,
        dispatch_status="runtime_error",
        validation_gate="red",
        provenance=[f"dispatcher:runtime_error:{runtime_id}"],
        diagnostics=[error or "Runtime error occurred during dispatch"],
        artifacts=[],
    )
