"""
CAM Runtime Result Contracts

Dev Order 58: Normalized runtime result vocabulary.

All runtime plugins must speak the same runtime result language.
Results are observational and non-authoritative — they report stage outcomes
without authorizing machine execution.

Hard invariants:
- observational_only is always True
- execution_ready is always False (validation)
- machine_operation_authorized is always False (validation)
- machine_output_generated is always False (export)
"""

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def _generate_result_id() -> str:
    """Generate a unique result ID."""
    return f"rr_{uuid4().hex[:12]}"


class RuntimeResultBase(BaseModel):
    """
    Base class for all runtime result contracts.

    All runtime results share:
    - Unique result_id for traceability
    - Schema version for contract governance
    - Status indicating outcome
    - Provenance chain for audit
    - Diagnostics for debugging
    - observational_only flag (always True)
    """

    result_id: str = Field(default_factory=_generate_result_id)
    schema_version: Literal["runtime-result.v1"] = "runtime-result.v1"

    status: Literal["available", "placeholder", "unsupported", "error"]

    provenance: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)

    observational_only: Literal[True] = Field(
        default=True,
        description="Always True. Runtime results are observational, not authoritative.",
    )

    @field_validator("observational_only", mode="before")
    @classmethod
    def enforce_observational_only(cls, v: bool) -> Literal[True]:
        """Enforce that observational_only is always True."""
        if v is False:
            raise ValueError("observational_only must always be True")
        return True


class RuntimeValidationResult(RuntimeResultBase):
    """
    Result of intent validation by a runtime plugin.

    Reports validation outcome without authorizing execution.

    Hard invariants:
    - execution_ready is always False
    - machine_operation_authorized is always False
    """

    validation_gate: Literal["green", "yellow", "red"]

    execution_ready: Literal[False] = Field(
        default=False,
        description="Always False. Validation does not authorize execution.",
    )
    machine_operation_authorized: Literal[False] = Field(
        default=False,
        description="Always False. Validation does not authorize machine operation.",
    )

    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

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

    @property
    def valid(self) -> bool:
        """Convenience property: validation passed if gate is not red."""
        return self.validation_gate != "red"


class RuntimeGeometryResolution(RuntimeResultBase):
    """
    Result of geometry resolution by a runtime plugin.

    Reports geometry queries and resolution status without mutating geometry.
    """

    geometry_resolution_status: Literal[
        "resolved",
        "partial",
        "placeholder",
        "unsupported",
    ]

    geometry_queries: list[str] = Field(default_factory=list)
    geometry_id: str | None = None
    summary: str = ""


class RuntimePlanResult(RuntimeResultBase):
    """
    Result of operation planning by a runtime plugin.

    Reports planning stage without generating toolpaths or machine coordinates.
    """

    planning_stage: Literal[
        "placeholder",
        "deterministic_stub",
        "unsupported",
    ]

    operation_count: int = 0
    plan_id: str | None = None
    summary: str = ""


class RuntimePreviewResult(RuntimeResultBase):
    """
    Result of preview generation by a runtime plugin.

    Reports preview availability without rendering engine integration.
    """

    preview_stage: Literal[
        "placeholder",
        "preview_stub",
        "unsupported",
    ]

    preview_artifacts: list[str] = Field(default_factory=list)
    preview_data: dict | None = None
    summary: str = ""


class RuntimeExportResult(RuntimeResultBase):
    """
    Result of export by a runtime plugin.

    Reports export availability without generating machine output.

    Hard invariant:
    - machine_output_generated is always False
    """

    export_stage: Literal[
        "placeholder",
        "export_stub",
        "unsupported",
    ]

    export_formats: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    summary: str = ""

    machine_output_generated: Literal[False] = Field(
        default=False,
        description="Always False. Export does not generate machine output in skeleton.",
    )

    @field_validator("machine_output_generated", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: bool) -> Literal[False]:
        """Enforce that machine_output_generated is always False."""
        if v is True:
            raise ValueError("machine_output_generated must always be False")
        return False


def create_unsupported_validation_result(
    reason: str,
    provenance: list[str] | None = None,
) -> RuntimeValidationResult:
    """Create a validation result for unsupported operations."""
    return RuntimeValidationResult(
        status="unsupported",
        validation_gate="red",
        provenance=provenance or ["runtime:unsupported"],
        diagnostics=[reason],
        errors=[reason],
    )


def create_unsupported_geometry_result(
    reason: str,
    provenance: list[str] | None = None,
) -> RuntimeGeometryResolution:
    """Create a geometry resolution result for unsupported operations."""
    return RuntimeGeometryResolution(
        status="unsupported",
        geometry_resolution_status="unsupported",
        provenance=provenance or ["runtime:unsupported"],
        diagnostics=[reason],
        summary=reason,
    )


def create_unsupported_plan_result(
    reason: str,
    provenance: list[str] | None = None,
) -> RuntimePlanResult:
    """Create a plan result for unsupported operations."""
    return RuntimePlanResult(
        status="unsupported",
        planning_stage="unsupported",
        provenance=provenance or ["runtime:unsupported"],
        diagnostics=[reason],
        summary=reason,
    )


def create_unsupported_preview_result(
    reason: str,
    provenance: list[str] | None = None,
) -> RuntimePreviewResult:
    """Create a preview result for unsupported operations."""
    return RuntimePreviewResult(
        status="unsupported",
        preview_stage="unsupported",
        provenance=provenance or ["runtime:unsupported"],
        diagnostics=[reason],
        summary=reason,
    )


def create_unsupported_export_result(
    reason: str,
    provenance: list[str] | None = None,
) -> RuntimeExportResult:
    """Create an export result for unsupported operations."""
    return RuntimeExportResult(
        status="unsupported",
        export_stage="unsupported",
        provenance=provenance or ["runtime:unsupported"],
        diagnostics=[reason],
        summary=reason,
    )
