"""
Translation Artifact Registry

CAM Dev Order 7D: Registry of supported translation artifact classes.

This module declares what artifact types the system can produce,
NOT the artifacts themselves. Artifacts are created per-export;
this registry describes the categories they can belong to.

7D invariants:
  - All registered artifact classes are non-executable
  - All registered artifact classes are validation-only
  - No executable payloads, no machine output
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# -----------------------------------------------------------------------------
# Type Definitions
# -----------------------------------------------------------------------------

ArtifactClassState = Literal[
    "validation_only",
    "non_executable",
]

ArtifactOutputClass = Literal[
    "dxf",
    "svg",
    "neutral_toolpath",
    "gcode",
    "machine_output",
]


# -----------------------------------------------------------------------------
# Artifact Class Registration Model
# -----------------------------------------------------------------------------

class ArtifactClassRegistration(BaseModel):
    """
    Registration entry for a translation artifact class.

    Describes a category of artifacts the system can produce,
    not individual artifacts. Each export creates an artifact
    instance; this registry describes the class it belongs to.

    7D invariants (model-enforced):
      - executable_output_supported: always false
      - machine_output_supported: always false
    """

    artifact_class_id: str = Field(
        ..., description="Unique artifact class identifier"
    )
    output_class: ArtifactOutputClass = Field(
        ..., description="Output format classification"
    )
    artifact_class_state: ArtifactClassState = Field(
        default="validation_only",
        description="Artifact class lifecycle state"
    )
    description: str = Field(
        ..., description="Human-readable description"
    )

    # 7D Safety Invariants — always false
    executable_output_supported: bool = Field(
        default=False,
        description="Always false in 7D — no executable output"
    )
    machine_output_supported: bool = Field(
        default=False,
        description="Always false in 7D — no machine output"
    )

    # Classification
    translator_category: Literal["translator", "postprocessor"] = Field(
        default="translator",
        description="Whether artifacts come from translator or postprocessor"
    )

    # Metadata
    notes: Optional[str] = Field(
        default=None,
        description="Implementation notes"
    )

    @model_validator(mode="after")
    def enforce_7d_invariants(self) -> "ArtifactClassRegistration":
        """Enforce 7D invariants: no executable or machine output."""
        if self.executable_output_supported:
            raise ValueError(
                f"Artifact class '{self.artifact_class_id}': "
                f"executable_output_supported must be False in 7D"
            )
        if self.machine_output_supported:
            raise ValueError(
                f"Artifact class '{self.artifact_class_id}': "
                f"machine_output_supported must be False in 7D"
            )
        return self


# -----------------------------------------------------------------------------
# Translation Artifact Class Registry
# -----------------------------------------------------------------------------

TRANSLATION_ARTIFACT_CLASS_REGISTRY: Dict[str, ArtifactClassRegistration] = {
    # DXF validation artifact
    "dxf_validation_artifact": ArtifactClassRegistration(
        artifact_class_id="dxf_validation_artifact",
        output_class="dxf",
        artifact_class_state="validation_only",
        description="DXF translation validation artifact — compatibility metadata only",
        translator_category="translator",
        executable_output_supported=False,
        machine_output_supported=False,
        notes="Records DXF translator compatibility without generating DXF content",
    ),

    # SVG validation artifact
    "svg_validation_artifact": ArtifactClassRegistration(
        artifact_class_id="svg_validation_artifact",
        output_class="svg",
        artifact_class_state="validation_only",
        description="SVG translation validation artifact — compatibility metadata only",
        translator_category="translator",
        executable_output_supported=False,
        machine_output_supported=False,
        notes="Records SVG translator compatibility without generating SVG content",
    ),

    # Neutral toolpath validation artifact
    "neutral_toolpath_validation_artifact": ArtifactClassRegistration(
        artifact_class_id="neutral_toolpath_validation_artifact",
        output_class="neutral_toolpath",
        artifact_class_state="validation_only",
        description="Neutral toolpath validation artifact — operation metadata only",
        translator_category="translator",
        executable_output_supported=False,
        machine_output_supported=False,
        notes="Records toolpath structure without generating machine-specific output",
    ),

    # G-code validation artifact
    "gcode_validation_artifact": ArtifactClassRegistration(
        artifact_class_id="gcode_validation_artifact",
        output_class="gcode",
        artifact_class_state="non_executable",
        description="G-code validation artifact — postprocessor compatibility metadata",
        translator_category="postprocessor",
        executable_output_supported=False,
        machine_output_supported=False,
        notes="Records postprocessor compatibility without generating G-code",
    ),
}


# -----------------------------------------------------------------------------
# Registry Access Functions
# -----------------------------------------------------------------------------

def get_artifact_class(artifact_class_id: str) -> Optional[ArtifactClassRegistration]:
    """
    Get artifact class registration by ID.

    Args:
        artifact_class_id: Artifact class identifier

    Returns:
        ArtifactClassRegistration if found, None otherwise
    """
    return TRANSLATION_ARTIFACT_CLASS_REGISTRY.get(artifact_class_id)


def list_artifact_classes() -> List[ArtifactClassRegistration]:
    """
    List all registered artifact classes.

    Returns:
        List of all ArtifactClassRegistration entries
    """
    return list(TRANSLATION_ARTIFACT_CLASS_REGISTRY.values())


def list_artifact_class_ids() -> List[str]:
    """
    List all registered artifact class IDs.

    Returns:
        List of artifact class identifiers
    """
    return list(TRANSLATION_ARTIFACT_CLASS_REGISTRY.keys())


def get_artifact_classes_by_output(
    output_class: ArtifactOutputClass,
) -> List[ArtifactClassRegistration]:
    """
    Get all artifact classes for a specific output class.

    Args:
        output_class: Output format classification

    Returns:
        List of matching ArtifactClassRegistration entries
    """
    return [
        reg for reg in TRANSLATION_ARTIFACT_CLASS_REGISTRY.values()
        if reg.output_class == output_class
    ]


def get_artifact_classes_by_category(
    translator_category: Literal["translator", "postprocessor"],
) -> List[ArtifactClassRegistration]:
    """
    Get all artifact classes for a specific translator category.

    Args:
        translator_category: "translator" or "postprocessor"

    Returns:
        List of matching ArtifactClassRegistration entries
    """
    return [
        reg for reg in TRANSLATION_ARTIFACT_CLASS_REGISTRY.values()
        if reg.translator_category == translator_category
    ]


def artifact_class_exists(artifact_class_id: str) -> bool:
    """
    Check if an artifact class is registered.

    Args:
        artifact_class_id: Artifact class identifier

    Returns:
        True if artifact class exists
    """
    return artifact_class_id in TRANSLATION_ARTIFACT_CLASS_REGISTRY


def get_artifact_class_for_translator(translator_id: str) -> Optional[str]:
    """
    Map translator ID to appropriate artifact class ID.

    Args:
        translator_id: Translator identifier from translator registry

    Returns:
        Artifact class ID if mapping exists, None otherwise
    """
    # Map translator output types to artifact classes
    translator_to_artifact_map = {
        "dxf_r12": "dxf_validation_artifact",
        "dxf_r2000": "dxf_validation_artifact",
        "body_outline_dxf_r12": "dxf_validation_artifact",
        "body_outline_dxf_r2000": "dxf_validation_artifact",
        "gcode_grbl_placeholder": "gcode_validation_artifact",
    }
    return translator_to_artifact_map.get(translator_id)
