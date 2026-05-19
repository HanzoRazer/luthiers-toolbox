"""
Translator Capability Registry

CAM Dev Order 7B: Declarative translator capability declarations.

This module provides a governed capability registry where translators
and postprocessors declare their capabilities explicitly.

Core principle:
  Capability declaration is separate from execution.
  This registry is declarative only — no execution occurs.

The registry becomes the canonical source of truth for:
  - Translator/postprocessor identity
  - Output format classification
  - Supported operations (semantic)
  - Execution state
  - Authorization requirements

Safety assertions (7B invariants):
  - execution_supported: always false in 7B
  - artifact_generation_supported: always false in 7B
  - machine_output_supported: always false in 7B
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# -----------------------------------------------------------------------------
# Type Definitions
# -----------------------------------------------------------------------------

TranslatorOutputClass = Literal["dxf", "gcode", "svg", "toolpath"]

TranslatorMaturity = Literal[
    "placeholder",
    "candidate",
    "governed",
    "canonical",
]

ExecutionState = Literal[
    "validation_only",
    "execution_planned",
    "execution_disabled",
    "execution_authorized_future",
    "governed_execution",  # MRP-3A: Translator authorized for Export Object consumption
]

TranslatorCategory = Literal[
    "translator",
    "postprocessor",
]


# -----------------------------------------------------------------------------
# Capability Model
# -----------------------------------------------------------------------------

class TranslatorCapability(BaseModel):
    """
    Capability declaration for a translator or postprocessor.

    Declares what a translator CAN do, not what it DOES.
    All execution flags are false in 7B — declarative only.

    Two complementary field sets:
      - execution_state: semantic architecture language from 7A
      - boolean flags: operational guards for tests/filtering/invariants
    """

    # --- Identity ---
    translator_id: str = Field(
        ..., description="Unique identifier (e.g., 'dxf_r12', 'gcode_grbl_placeholder')"
    )
    translator_name: str = Field(
        ..., description="Human-readable name"
    )
    translator_version: str = Field(
        default="0.0.0", description="Semantic version"
    )

    # --- Classification ---
    translator_category: TranslatorCategory = Field(
        ..., description="Whether this is a translator or postprocessor"
    )
    output_class: TranslatorOutputClass = Field(
        ..., description="Output format classification"
    )
    output_format_version: Optional[str] = Field(
        default=None, description="Format-specific version (e.g., 'R12', 'R2000', '1.1')"
    )

    # --- Lifecycle Semantics (7A architecture language) ---
    execution_state: ExecutionState = Field(
        default="validation_only",
        description="Execution lifecycle state"
    )
    maturity: TranslatorMaturity = Field(
        default="placeholder",
        description="Governance maturity level (aligned with CAM promotion semantics)"
    )

    # --- Operational Boolean Flags (guards/tests/filtering) ---
    execution_supported: bool = Field(
        default=False,
        description="Always false in 7B — no execution capability"
    )
    artifact_generation_supported: bool = Field(
        default=False,
        description="Always false in 7B — no artifact generation"
    )
    machine_output_supported: bool = Field(
        default=False,
        description="Always false in 7B — no machine output"
    )

    # --- Authorization ---
    authorization_required: bool = Field(
        default=True,
        description="Whether human authorization is required for execution (future)"
    )

    # --- Capability Declarations (semantic, not enforced in 7B) ---
    supported_operations: List[str] = Field(
        default_factory=list,
        description="CAM operations this translator supports"
    )
    supported_geometry_types: List[str] = Field(
        default_factory=list,
        description="Geometry types this translator can handle"
    )
    supported_units: List[str] = Field(
        default_factory=lambda: ["mm"],
        description="Unit systems supported"
    )

    # --- Documentation ---
    description: Optional[str] = Field(
        default=None, description="Translator description"
    )
    notes: Optional[str] = Field(
        default=None, description="Additional notes"
    )

    # --- Invariant Enforcement ---
    @model_validator(mode="after")
    def enforce_execution_invariants(self) -> "TranslatorCapability":
        """
        Enforce execution state invariants.

        7B invariants (declarative-only translators):
        - validation_only: all execution flags must be False
        - execution_disabled: all execution flags must be False
        - machine_output_supported: always False in 7B

        MRP-3A invariants (governed translators):
        - governed_execution: execution_supported=True, artifact_generation_supported=True
        - governed_execution: machine_output_supported=False (no G-code, only geometry)
        """
        # Invariant 1: validation_only state requires all flags false
        if self.execution_state == "validation_only":
            if self.execution_supported:
                raise ValueError(
                    f"Translator '{self.translator_id}': execution_supported must be "
                    f"False when execution_state is 'validation_only'"
                )
            if self.artifact_generation_supported:
                raise ValueError(
                    f"Translator '{self.translator_id}': artifact_generation_supported "
                    f"must be False when execution_state is 'validation_only'"
                )
            if self.machine_output_supported:
                raise ValueError(
                    f"Translator '{self.translator_id}': machine_output_supported must "
                    f"be False when execution_state is 'validation_only'"
                )

        # Invariant 2: machine_output_supported must always be False (no G-code translators yet)
        if self.machine_output_supported:
            raise ValueError(
                f"Translator '{self.translator_id}': machine_output_supported must be "
                f"False — no machine output capability authorized"
            )

        # Invariant 3: execution_disabled also requires all flags false
        if self.execution_state == "execution_disabled":
            if self.execution_supported:
                raise ValueError(
                    f"Translator '{self.translator_id}': execution_supported must be "
                    f"False when execution_state is 'execution_disabled'"
                )

        # Invariant 4: governed_execution requires execution_supported=True
        if self.execution_state == "governed_execution":
            if not self.execution_supported:
                raise ValueError(
                    f"Translator '{self.translator_id}': execution_supported must be "
                    f"True when execution_state is 'governed_execution'"
                )

        return self


# -----------------------------------------------------------------------------
# Canonical Registry
# -----------------------------------------------------------------------------

TRANSLATOR_CAPABILITY_REGISTRY: Dict[str, TranslatorCapability] = {
    # --- Legacy CAM translators (7B: validation_only) ---
    "dxf_r12": TranslatorCapability(
        translator_id="dxf_r12",
        translator_name="DXF R12 Translator",
        translator_version="1.0.0",
        translator_category="translator",
        output_class="dxf",
        output_format_version="R12",
        execution_state="validation_only",
        maturity="candidate",
        execution_supported=False,
        artifact_generation_supported=False,
        machine_output_supported=False,
        authorization_required=True,
        supported_operations=["nut_slot", "drilling"],
        supported_geometry_types=["line", "arc", "circle"],
        supported_units=["mm", "inch"],
        description="DXF R12 geometry translator for legacy CAM systems",
        notes="Free tier output format. Emits line entities via dxf_compat.",
    ),
    "dxf_r2000": TranslatorCapability(
        translator_id="dxf_r2000",
        translator_name="DXF R2000 Translator",
        translator_version="1.0.0",
        translator_category="translator",
        output_class="dxf",
        output_format_version="R2000",
        execution_state="validation_only",
        maturity="candidate",
        execution_supported=False,
        artifact_generation_supported=False,
        machine_output_supported=False,
        authorization_required=True,
        supported_operations=["nut_slot", "drilling"],
        supported_geometry_types=["line", "arc", "circle", "lwpolyline"],
        supported_units=["mm", "inch"],
        description="DXF R2000 geometry translator for modern CAM systems",
        notes="Paid tier output format. Emits lwpolyline entities via dxf_compat.",
    ),
    # --- MRP-3A: Governed body outline translators ---
    "body_outline_dxf_r12": TranslatorCapability(
        translator_id="body_outline_dxf_r12",
        translator_name="Body Outline DXF R12 Translator",
        translator_version="1.0.0",
        translator_category="translator",
        output_class="dxf",
        output_format_version="R12",
        execution_state="governed_execution",
        maturity="governed",
        execution_supported=True,
        artifact_generation_supported=True,
        machine_output_supported=False,
        authorization_required=False,
        supported_operations=["body_profiling"],
        supported_geometry_types=["closed_contour"],
        supported_units=["mm"],
        description="MRP-3A governed body outline translator (free tier)",
        notes="Consumes BodyExportObject, emits R12 DXF via dxf_writer. "
              "Downstream of MRP morphology spine.",
    ),
    "body_outline_dxf_r2000": TranslatorCapability(
        translator_id="body_outline_dxf_r2000",
        translator_name="Body Outline DXF R2000 Translator",
        translator_version="1.0.0",
        translator_category="translator",
        output_class="dxf",
        output_format_version="R2000",
        execution_state="governed_execution",
        maturity="governed",
        execution_supported=True,
        artifact_generation_supported=True,
        machine_output_supported=False,
        authorization_required=False,
        supported_operations=["body_profiling"],
        supported_geometry_types=["closed_contour"],
        supported_units=["mm"],
        description="MRP-3A governed body outline translator (paid tier)",
        notes="Consumes BodyExportObject, emits R2000 DXF via dxf_writer. "
              "Downstream of MRP morphology spine.",
    ),
    "gcode_grbl_placeholder": TranslatorCapability(
        translator_id="gcode_grbl_placeholder",
        translator_name="GRBL G-code Postprocessor (Placeholder)",
        translator_version="0.0.0",
        translator_category="postprocessor",
        output_class="gcode",
        output_format_version="1.1",
        execution_state="execution_disabled",
        maturity="placeholder",
        execution_supported=False,
        artifact_generation_supported=False,
        machine_output_supported=False,
        authorization_required=True,
        supported_operations=[],
        supported_geometry_types=[],
        supported_units=["mm"],
        description="Placeholder for future GRBL postprocessor",
        notes="7B: Registered for introspection only. No execution capability. "
              "Empty supported_operations communicates no approved operation bindings.",
    ),
}


# -----------------------------------------------------------------------------
# Registry Helper Functions
# -----------------------------------------------------------------------------

def get_translator_capability(translator_id: str) -> Optional[TranslatorCapability]:
    """
    Get capability declaration for a translator.

    Args:
        translator_id: Translator identifier

    Returns:
        TranslatorCapability if registered, None otherwise
    """
    return TRANSLATOR_CAPABILITY_REGISTRY.get(translator_id)


def list_translator_capabilities() -> List[TranslatorCapability]:
    """
    List all registered translator capabilities.

    Returns:
        List of all TranslatorCapability entries
    """
    return list(TRANSLATOR_CAPABILITY_REGISTRY.values())


def list_translator_ids() -> List[str]:
    """
    List all registered translator identifiers.

    Returns:
        List of translator IDs in the registry
    """
    return list(TRANSLATOR_CAPABILITY_REGISTRY.keys())


def list_translators_by_category(
    category: TranslatorCategory,
) -> List[TranslatorCapability]:
    """
    List translators by category (translator vs postprocessor).

    Args:
        category: The category to filter by

    Returns:
        List of TranslatorCapability entries matching the category
    """
    return [
        cap
        for cap in TRANSLATOR_CAPABILITY_REGISTRY.values()
        if cap.translator_category == category
    ]


def list_translators_by_output_class(
    output_class: TranslatorOutputClass,
) -> List[TranslatorCapability]:
    """
    List translators by output format class.

    Args:
        output_class: The output class to filter by (dxf, gcode, svg, toolpath)

    Returns:
        List of TranslatorCapability entries producing that output class
    """
    return [
        cap
        for cap in TRANSLATOR_CAPABILITY_REGISTRY.values()
        if cap.output_class == output_class
    ]


def list_translators_for_operation(operation: str) -> List[TranslatorCapability]:
    """
    List translators that declare support for an operation.

    Args:
        operation: Operation identifier (e.g., 'nut_slot', 'drilling')

    Returns:
        List of TranslatorCapability entries supporting that operation
    """
    return [
        cap
        for cap in TRANSLATOR_CAPABILITY_REGISTRY.values()
        if operation in cap.supported_operations
    ]


def list_governed_translators() -> List[TranslatorCapability]:
    """
    List translators with governed_execution state.

    MRP-3A: These translators are authorized to consume Export Objects
    and generate output artifacts.

    Returns:
        List of TranslatorCapability entries with governed_execution
    """
    return [
        cap
        for cap in TRANSLATOR_CAPABILITY_REGISTRY.values()
        if cap.execution_state == "governed_execution"
    ]


def list_execution_capable_translators() -> List[TranslatorCapability]:
    """
    List translators that can execute (execution_supported=True).

    Returns:
        List of TranslatorCapability entries that can execute
    """
    return [
        cap
        for cap in TRANSLATOR_CAPABILITY_REGISTRY.values()
        if cap.execution_supported
    ]
