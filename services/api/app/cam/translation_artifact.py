"""
Translation Artifact Models

CAM Dev Order 7D: Governed translation artifact contracts.

This module defines Translation Artifacts — the governed representation
of future translator results. Artifacts capture lineage, policy state,
and classification metadata WITHOUT containing executable payloads.

Core principle:
  A Translation Artifact is a governed representation of a future
  translator result, NOT the execution itself.

7D invariants:
  - execution_supported: always false
  - executable_payload_present: always false
  - machine_output_present: always false

No DXF. No G-code. No serialization. Metadata contracts only.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.cam.export_object import ExportObject
from app.cam.translator_capability_registry import (
    TranslatorCapability,
    get_translator_capability,
)


# -----------------------------------------------------------------------------
# Type Definitions
# -----------------------------------------------------------------------------

ArtifactOutputClass = Literal[
    "dxf",
    "svg",
    "neutral_toolpath",
    "gcode",
    "machine_output",
]

ArtifactState = Literal[
    "validation_only",
    "non_executable",
    "execution_planned",
]

ArtifactCategory = Literal[
    "translator",
    "postprocessor",
]


# -----------------------------------------------------------------------------
# Translation Artifact Summary (for lifecycle reports)
# -----------------------------------------------------------------------------

class TranslationArtifactSummary(BaseModel):
    """
    Lightweight summary of translation artifact for lifecycle reports.

    Contains classification and state only — no payloads.
    """

    artifact_id: str = Field(..., description="Unique artifact identifier")
    translator_id: str = Field(..., description="Source translator identifier")
    output_class: ArtifactOutputClass = Field(..., description="Output classification")
    artifact_state: ArtifactState = Field(..., description="Artifact lifecycle state")

    # 7D invariants — always false
    execution_supported: bool = Field(
        default=False,
        description="Always false in 7D — no execution capability"
    )
    executable_payload_present: bool = Field(
        default=False,
        description="Always false in 7D — no payload generation"
    )
    machine_output_present: bool = Field(
        default=False,
        description="Always false in 7D — no machine output"
    )

    # Lineage
    source_export_object_hash: Optional[str] = Field(
        default=None,
        description="SHA256 hash of source export object"
    )
    deterministic_hash: Optional[str] = Field(
        default=None,
        description="Deterministic hash of artifact governance state"
    )


# -----------------------------------------------------------------------------
# Translation Artifact (Full Model)
# -----------------------------------------------------------------------------

class TranslationArtifact(BaseModel):
    """
    Governed translation artifact model.

    Represents what a translator WOULD produce without containing
    the actual executable content. Captures lineage, policy state,
    and classification metadata.

    7D invariants (model-enforced):
      - validation_only → executable_payload_present = false
      - non_executable → machine_output_present = false
      - 7D globally → execution_supported = false, machine_output_present = false
    """

    # --- Identity ---
    artifact_id: str = Field(
        default_factory=lambda: f"artifact-{uuid4().hex[:12]}",
        description="Unique artifact identifier"
    )

    # --- Classification ---
    translator_id: str = Field(..., description="Source translator identifier")
    translator_category: ArtifactCategory = Field(
        ..., description="Whether source is translator or postprocessor"
    )
    output_class: ArtifactOutputClass = Field(
        ..., description="Output format classification"
    )

    # --- Lifecycle State ---
    artifact_state: ArtifactState = Field(
        default="validation_only",
        description="Artifact lifecycle state"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Artifact creation timestamp"
    )

    # --- Lineage ---
    source_export_object_id: str = Field(
        ..., description="Source export object identifier"
    )
    source_export_object_hash: str = Field(
        ..., description="SHA256 hash of source export object"
    )

    # --- Snapshots (governance state at creation time) ---
    capability_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Translator capability state at artifact creation"
    )
    policy_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Policy evaluation state at artifact creation"
    )

    # --- 7D Safety Invariants ---
    execution_supported: bool = Field(
        default=False,
        description="Always false in 7D — no execution capability"
    )
    executable_payload_present: bool = Field(
        default=False,
        description="Always false in 7D — no payload generation"
    )
    machine_output_present: bool = Field(
        default=False,
        description="Always false in 7D — no machine output"
    )

    # --- Metadata ---
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional artifact metadata"
    )

    # --- Invariant Enforcement ---
    @model_validator(mode="after")
    def enforce_7d_invariants(self) -> "TranslationArtifact":
        """
        Enforce 7D invariants:
        - validation_only → executable_payload_present = false
        - non_executable → machine_output_present = false
        - 7D globally → execution_supported = false, machine_output_present = false
        """
        # Invariant 1: validation_only requires no executable payload
        if self.artifact_state == "validation_only":
            if self.executable_payload_present:
                raise ValueError(
                    f"Artifact '{self.artifact_id}': executable_payload_present must be "
                    f"False when artifact_state is 'validation_only'"
                )

        # Invariant 2: non_executable requires no machine output
        if self.artifact_state == "non_executable":
            if self.machine_output_present:
                raise ValueError(
                    f"Artifact '{self.artifact_id}': machine_output_present must be "
                    f"False when artifact_state is 'non_executable'"
                )

        # Invariant 3: execution_supported must always be False in 7D
        if self.execution_supported:
            raise ValueError(
                f"Artifact '{self.artifact_id}': execution_supported must be "
                f"False in 7D — no execution capability"
            )

        # Invariant 4: machine_output_present must always be False in 7D
        if self.machine_output_present:
            raise ValueError(
                f"Artifact '{self.artifact_id}': machine_output_present must be "
                f"False in 7D — no machine output"
            )

        return self

    def to_summary(self) -> TranslationArtifactSummary:
        """Create lightweight summary for lifecycle reports."""
        return TranslationArtifactSummary(
            artifact_id=self.artifact_id,
            translator_id=self.translator_id,
            output_class=self.output_class,
            artifact_state=self.artifact_state,
            execution_supported=self.execution_supported,
            executable_payload_present=self.executable_payload_present,
            machine_output_present=self.machine_output_present,
            source_export_object_hash=self.source_export_object_hash,
            deterministic_hash=self.compute_deterministic_hash(),
        )

    def compute_deterministic_hash(self) -> str:
        """Compute deterministic hash of artifact governance state."""
        hash_input = {
            "translator_id": self.translator_id,
            "translator_category": self.translator_category,
            "output_class": self.output_class,
            "artifact_state": self.artifact_state,
            "source_export_object_hash": self.source_export_object_hash,
            "capability_snapshot": _normalize_for_hash(self.capability_snapshot),
            "policy_snapshot": _normalize_for_hash(self.policy_snapshot),
        }
        canonical_json = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# Hash Utilities
# -----------------------------------------------------------------------------

def _normalize_for_hash(obj: Any) -> Any:
    """Normalize object for deterministic hashing (remove timestamps, sort)."""
    if isinstance(obj, dict):
        return {
            k: _normalize_for_hash(v)
            for k, v in sorted(obj.items())
            if k not in ("created_at", "timestamp", "updated_at")
        }
    elif isinstance(obj, list):
        return [_normalize_for_hash(item) for item in obj]
    elif isinstance(obj, datetime):
        return None  # Exclude timestamps from hash
    else:
        return obj


def compute_export_object_hash(export_object: ExportObject) -> str:
    """
    Compute SHA256 hash of export object.

    Excludes timestamps for deterministic hashing.
    """
    export_dict = export_object.model_dump(mode="json")
    normalized = _normalize_for_hash(export_dict)
    canonical_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# Validation-Only Artifact Builder
# -----------------------------------------------------------------------------

def build_validation_translation_artifact(
    export_object: ExportObject,
    translator_capability: TranslatorCapability,
    policy_snapshot: Optional[Dict[str, Any]] = None,
) -> TranslationArtifact:
    """
    Build a validation-only translation artifact.

    Creates metadata-only artifact with:
    - Lineage (export object hash)
    - Governance snapshots (capability, policy)
    - Classification metadata

    No payload generation. No serialization. No executable content.

    Args:
        export_object: Source export object
        translator_capability: Translator capability from registry
        policy_snapshot: Optional policy evaluation snapshot

    Returns:
        TranslationArtifact with validation_only state
    """
    return TranslationArtifact(
        translator_id=translator_capability.translator_id,
        translator_category=translator_capability.translator_category,
        output_class=translator_capability.output_class,
        artifact_state="validation_only",
        source_export_object_id=export_object.export_id,
        source_export_object_hash=compute_export_object_hash(export_object),
        capability_snapshot=translator_capability.model_dump(mode="json"),
        policy_snapshot=policy_snapshot or {},
        execution_supported=False,
        executable_payload_present=False,
        machine_output_present=False,
        metadata={
            "builder": "build_validation_translation_artifact",
            "dev_order": "7D",
            "validation_only": True,
        },
    )


def build_artifact_summary_from_translator(
    export_object: ExportObject,
    translator_id: str,
) -> Optional[TranslationArtifactSummary]:
    """
    Build artifact summary directly from translator ID.

    Convenience function for lifecycle integration.

    Args:
        export_object: Source export object
        translator_id: Translator identifier from registry

    Returns:
        TranslationArtifactSummary if translator found, None otherwise
    """
    capability = get_translator_capability(translator_id)
    if capability is None:
        return None

    artifact = build_validation_translation_artifact(
        export_object=export_object,
        translator_capability=capability,
    )
    return artifact.to_summary()
