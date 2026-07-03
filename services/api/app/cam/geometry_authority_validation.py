"""
Geometry Authority Validation

CAM Dev Order 7T: Validation logic for geometry authority references.

Provides:
  - Authority validation with GREEN/YELLOW/RED gates
  - Authority collapse detection
  - Missing provenance detection
  - Invalid layer use detection

7T invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False

Validation gates:
  - RED: authority collapse, missing source, execution/machine flags
  - YELLOW: missing provenance, incomplete allowed uses
  - GREEN: valid authority chain with provenance
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.cam.geometry_authority_taxonomy import (
    GeometryAuthorityLayer,
    get_layer_definition,
    is_canonical_layer,
    is_use_allowed,
    layer_requires_source,
)
from app.cam.geometry_authority_reference import GeometryAuthorityReference


ValidationGate = Literal["green", "yellow", "red"]


class GeometryAuthorityValidationResult(BaseModel):
    """
    Result of validating a geometry authority reference.

    7T invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    validation_id: str = Field(
        default_factory=lambda: f"geo-val-{uuid4().hex[:12]}",
        description="Unique validation identifier"
    )

    geometry_reference_id: str = Field(
        ..., description="ID of the validated reference"
    )

    gate: ValidationGate = Field(
        ..., description="Validation gate result"
    )

    authority_layer: GeometryAuthorityLayer = Field(
        ..., description="Layer of the validated reference"
    )

    source_reference_valid: bool = Field(
        default=False,
        description="Whether source reference is valid"
    )
    provenance_present: bool = Field(
        default=False,
        description="Whether provenance hash is present"
    )
    allowed_use_valid: bool = Field(
        default=True,
        description="Whether allowed uses are valid for layer"
    )
    canonical_authority_respected: bool = Field(
        default=True,
        description="Whether canonical authority is respected"
    )

    authority_collapse_detected: bool = Field(
        default=False,
        description="Whether authority collapse was detected"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="RED blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="YELLOW warnings"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7T does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7T does not allow machine output"
    )

    validated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Validation timestamp"
    )

    deterministic_validation_hash: str = Field(
        default="",
        description="Deterministic hash of validation result"
    )

    @model_validator(mode="after")
    def enforce_7t_invariants(self) -> "GeometryAuthorityValidationResult":
        """Enforce 7T invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7T invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7T invariant violation: machine_output_allowed must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of validation result."""
        hash_input = {
            "geometry_reference_id": self.geometry_reference_id,
            "gate": self.gate,
            "authority_layer": self.authority_layer,
            "source_reference_valid": self.source_reference_valid,
            "provenance_present": self.provenance_present,
            "authority_collapse_detected": self.authority_collapse_detected,
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def validate_geometry_authority_reference(
    reference: GeometryAuthorityReference,
    source_exists_checker: Optional[callable] = None,
) -> GeometryAuthorityValidationResult:
    """
    Validate a geometry authority reference.

    Checks:
      - Source reference validity for derived layers
      - Provenance presence
      - Allowed use validity
      - Canonical authority respect
      - Authority collapse detection
      - 7T invariant compliance

    Args:
        reference: The reference to validate
        source_exists_checker: Optional callable to verify source exists

    Returns:
        GeometryAuthorityValidationResult with gate and issues
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    layer_def = get_layer_definition(reference.authority_layer)

    source_reference_valid = True
    if layer_requires_source(reference.authority_layer):
        if not reference.source_geometry_id and not reference.derived_from:
            blocking_issues.append(
                f"Layer '{reference.authority_layer}' requires source reference, "
                f"but neither source_geometry_id nor derived_from is set"
            )
            source_reference_valid = False
        elif source_exists_checker and reference.source_geometry_id:
            if not source_exists_checker(reference.source_geometry_id):
                warnings.append(
                    f"Source geometry '{reference.source_geometry_id}' not found in registry"
                )

    provenance_present = reference.provenance_hash is not None
    if not provenance_present and reference.authority_layer != "canonical_geometry":
        warnings.append("Provenance hash not present for derived geometry")

    # C2 process-exclusive canonical authority (PROPOSED, transition mode).
    # A canonical reference not backed by a governed process-approval record is
    # a transition-state WARNING in this PR — never a RED gate. PR 4 may flip
    # this to RED once all canonical creators have migrated.
    if is_canonical_layer(reference.authority_layer):
        canonical_ok, canonical_reason = validate_canonical_process_authority(reference)
        if not canonical_ok and canonical_reason:
            warnings.append(canonical_reason)

    allowed_use_valid = True
    for use in reference.allowed_uses:
        if not is_use_allowed(reference.authority_layer, use):
            blocking_issues.append(
                f"Use '{use}' is not allowed for layer '{reference.authority_layer}'"
            )
            allowed_use_valid = False

    canonical_authority_respected = True
    authority_collapse_detected = False

    if not is_canonical_layer(reference.authority_layer):
        if reference.may_define_canonical_geometry:
            blocking_issues.append(
                f"Non-canonical layer '{reference.authority_layer}' has "
                f"may_define_canonical_geometry=True — authority collapse"
            )
            canonical_authority_respected = False
            authority_collapse_detected = True

    if reference.authority_layer == "export_geometry":
        if "canonical_definition" in reference.allowed_uses:
            blocking_issues.append(
                "Export geometry used as canonical source — authority collapse"
            )
            authority_collapse_detected = True
        if "source_authority" in reference.allowed_uses:
            blocking_issues.append(
                "Export geometry claiming source authority — authority collapse"
            )
            authority_collapse_detected = True

    if reference.authority_layer == "visualization_geometry":
        if "export" in reference.allowed_uses:
            blocking_issues.append(
                "Visualization geometry used for export — layer violation"
            )
        if "translation" in reference.allowed_uses:
            blocking_issues.append(
                "Visualization geometry used for translation — layer violation"
            )
        if "strategy" in reference.allowed_uses:
            blocking_issues.append(
                "Visualization geometry used for strategy — layer violation"
            )

    if reference.machine_output_allowed:
        blocking_issues.append(
            "machine_output_allowed=True — 7T invariant violation"
        )

    if reference.execution_authorized:
        blocking_issues.append(
            "execution_authorized=True — 7T invariant violation"
        )

    if reference.may_mutate_source_geometry:
        blocking_issues.append(
            "may_mutate_source_geometry=True — 7T invariant violation"
        )

    if reference.may_promote_to_canonical:
        blocking_issues.append(
            "may_promote_to_canonical=True — 7T invariant violation"
        )

    if not reference.source_authority and reference.authority_layer != "canonical_geometry":
        warnings.append("source_authority not specified for derived geometry")

    if not reference.allowed_uses:
        warnings.append("No allowed_uses specified — may be incomplete")

    if reference.derived_from and not reference.source_geometry_id:
        warnings.append(
            "derived_from set but source_geometry_id not set — "
            "consider setting primary source"
        )

    if blocking_issues:
        gate: ValidationGate = "red"
    elif warnings:
        gate = "yellow"
    else:
        gate = "green"

    result = GeometryAuthorityValidationResult(
        geometry_reference_id=reference.geometry_reference_id,
        gate=gate,
        authority_layer=reference.authority_layer,
        source_reference_valid=source_reference_valid,
        provenance_present=provenance_present,
        allowed_use_valid=allowed_use_valid,
        canonical_authority_respected=canonical_authority_respected,
        authority_collapse_detected=authority_collapse_detected,
        blocking_issues=blocking_issues,
        warnings=warnings,
    )

    result.deterministic_validation_hash = result.compute_hash()

    return result


def validate_canonical_process_authority(
    reference: GeometryAuthorityReference,
) -> tuple[bool, Optional[str]]:
    """
    Validate that a canonical reference is backed by a governed process-approval
    record (C2 process-exclusive ruling — PROPOSED).

    Returns ``(is_valid, reason)``.

    Rules:
      - Only applies to ``canonical_geometry`` references (derived layers return
        ``(True, None)`` — not applicable).
      - ``canonical_process_id``, ``canonical_process_version``,
        ``governed_approval_event_id``, and ``process_approval_record_hash`` must
        all be present.
      - Authority cannot be inferred from format, route, serializer, registry
        location, IBG/vectorizer/template origin, or individual reviewer
        identity — only from the presence of the process-approval metadata.

    A missing-metadata result is a TRANSITION-STATE signal. Callers in this PR
    surface it as a warning, not a RED gate.
    """
    if not is_canonical_layer(reference.authority_layer):
        return True, None

    required = {
        "canonical_process_id": reference.canonical_process_id,
        "canonical_process_version": reference.canonical_process_version,
        "governed_approval_event_id": reference.governed_approval_event_id,
        "process_approval_record_hash": reference.process_approval_record_hash,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        return False, (
            "Canonical reference lacks process-approval metadata "
            f"({', '.join(missing)}); under the C2 process-exclusive ruling "
            "canonical authority is created only by the approved canonical process "
            "following a governed approval event. Authority cannot be inferred from "
            "format, route, serializer, registry location, IBG/vectorizer/template "
            "origin, or individual reviewer identity. Use "
            "create_process_approved_canonical_geometry_reference(). "
            "(transition-state warning; not a RED gate in this PR)"
        )
    return True, None


def detect_authority_collapse(reference: GeometryAuthorityReference) -> bool:
    """
    Detect if a reference exhibits authority collapse.

    Authority collapse occurs when:
      - Non-canonical layer claims may_define_canonical_geometry
      - Export geometry is used as canonical source
      - Visualization geometry is used for export/strategy
    """
    if not is_canonical_layer(reference.authority_layer):
        if reference.may_define_canonical_geometry:
            return True

    if reference.authority_layer == "export_geometry":
        if "canonical_definition" in reference.allowed_uses:
            return True
        if "source_authority" in reference.allowed_uses:
            return True

    if reference.authority_layer == "visualization_geometry":
        if "export" in reference.allowed_uses:
            return True

    return False


def validate_source_reference_required(
    reference: GeometryAuthorityReference,
) -> tuple[bool, Optional[str]]:
    """
    Validate that source reference is present when required.

    Returns:
        (is_valid, error_message)
    """
    if layer_requires_source(reference.authority_layer):
        if not reference.source_geometry_id and not reference.derived_from:
            return False, (
                f"Layer '{reference.authority_layer}' requires source reference"
            )
    return True, None


def validate_allowed_use(
    reference: GeometryAuthorityReference,
    requested_use: str,
) -> tuple[bool, Optional[str]]:
    """
    Validate that a requested use is allowed for a reference.

    Returns:
        (is_allowed, error_message)
    """
    if not is_use_allowed(reference.authority_layer, requested_use):
        return False, (
            f"Use '{requested_use}' is not allowed for layer '{reference.authority_layer}'"
        )

    if requested_use in reference.prohibited_uses:
        return False, (
            f"Use '{requested_use}' is explicitly prohibited for this reference"
        )

    if reference.allowed_uses and requested_use not in reference.allowed_uses:
        return False, (
            f"Use '{requested_use}' is not in allowed_uses for this reference"
        )

    return True, None
