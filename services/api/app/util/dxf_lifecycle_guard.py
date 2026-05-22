"""
DXF Lifecycle Guard — Runtime Boundary Phase 2A

Non-mutating validation guard for DXF export lifecycle context.

This module validates export context only. It does not:
- Mutate DXF documents
- Attach provenance metadata
- Log or emit audit records (deferred to later phase)
- Block or authorize execution

Usage:
    from app.util.dxf_lifecycle_guard import (
        DxfLifecycleContext,
        assert_dxf_lifecycle_context,
    )

    context = DxfLifecycleContext(
        source_module=__name__,
        export_type="dxf-create-save",
        dxf_version="R2010",
        lifecycle_status="COMPAT_ONLY",
        runtime_callable="router_endpoint",
        authority_context="user_request",
        provenance_status="NO",
    )
    assert_dxf_lifecycle_context(context)
    doc.saveas(path)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class DxfLifecycleGuardError(Exception):
    """Raised when DXF lifecycle context validation fails."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        message = f"DXF lifecycle guard validation failed: {'; '.join(errors)}"
        super().__init__(message)


VALID_EXPORT_TYPES = frozenset({
    "dxf-create-save",
    "dxf-read-modify-save",
    "dxf-create-only",
    "dxf-preview",
    "dxf-write-only",
})

VALID_LIFECYCLE_STATUSES = frozenset({
    "LIFECYCLE_GOVERNED",
    "COMPAT_ONLY",
    "DIRECT_SAVE_GAP",
    "BLOCKED_PROVENANCE",
    "TEST_ONLY",
    "R_AND_D_EXCLUDED",
})

VALID_RUNTIME_CALLABLES = frozenset({
    "router_endpoint",
    "runtime_service",
    "script_only",
    "test_only",
    "excluded",
})

VALID_PROVENANCE_STATUSES = frozenset({
    "YES",
    "NO",
    "BLOCKED",
    "N/A",
})

VALID_AUTHORITY_CONTEXTS = frozenset({
    "user_request",
    "pipeline_stage",
    "batch_operation",
    "preview_only",
    "unknown",
})


@dataclass(frozen=True)
class DxfLifecycleContext:
    """
    Lightweight lifecycle context for DXF export operations.

    All fields are required. Use "unknown" for authority_context if not known.
    """

    source_module: str
    export_type: str
    dxf_version: str
    lifecycle_status: str
    runtime_callable: str
    authority_context: str
    provenance_status: str


def validate_dxf_lifecycle_context(context: DxfLifecycleContext) -> List[str]:
    """
    Validate a DXF lifecycle context.

    Returns:
        Empty list if valid, list of error strings if invalid.
    """
    errors: List[str] = []

    if not context.source_module:
        errors.append("source_module is required")

    if not context.export_type:
        errors.append("export_type is required")
    elif context.export_type not in VALID_EXPORT_TYPES:
        errors.append(
            f"export_type '{context.export_type}' is not valid; "
            f"must be one of: {', '.join(sorted(VALID_EXPORT_TYPES))}"
        )

    if not context.dxf_version:
        errors.append("dxf_version is required")

    if not context.lifecycle_status:
        errors.append("lifecycle_status is required")
    elif context.lifecycle_status not in VALID_LIFECYCLE_STATUSES:
        errors.append(
            f"lifecycle_status '{context.lifecycle_status}' is not valid; "
            f"must be one of: {', '.join(sorted(VALID_LIFECYCLE_STATUSES))}"
        )

    if not context.runtime_callable:
        errors.append("runtime_callable is required")
    elif context.runtime_callable not in VALID_RUNTIME_CALLABLES:
        errors.append(
            f"runtime_callable '{context.runtime_callable}' is not valid; "
            f"must be one of: {', '.join(sorted(VALID_RUNTIME_CALLABLES))}"
        )

    if not context.authority_context:
        errors.append("authority_context is required")
    elif context.authority_context not in VALID_AUTHORITY_CONTEXTS:
        errors.append(
            f"authority_context '{context.authority_context}' is not valid; "
            f"must be one of: {', '.join(sorted(VALID_AUTHORITY_CONTEXTS))}"
        )

    if not context.provenance_status:
        errors.append("provenance_status is required")
    elif context.provenance_status not in VALID_PROVENANCE_STATUSES:
        errors.append(
            f"provenance_status '{context.provenance_status}' is not valid; "
            f"must be one of: {', '.join(sorted(VALID_PROVENANCE_STATUSES))}"
        )

    return errors


def assert_dxf_lifecycle_context(context: DxfLifecycleContext) -> None:
    """
    Assert that a DXF lifecycle context is valid.

    Raises:
        DxfLifecycleGuardError: If validation fails.
    """
    errors = validate_dxf_lifecycle_context(context)
    if errors:
        raise DxfLifecycleGuardError(errors)
