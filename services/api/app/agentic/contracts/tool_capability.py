"""
Tool Capability Contract v1

Defines what each tool/analyzer can do in a cross-repo discoverable way.
This is the "thin waist" contract that allows agent orchestration without
tight coupling to tool implementations.

Design principles:
1. Capabilities are declarative, not imperative
2. Safe defaults are explicit and auditable
3. Actions describe what CAN be done, not how
4. Version field enables forward compatibility
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CapabilityAction(str, Enum):
    """
    Actions a tool can perform.

    Categories:
    - ANALYZE_*: Read-only analysis operations
    - GENERATE_*: Creates new artifacts
    - VALIDATE_*: Checks conformance to spec
    - TRANSFORM_*: Modifies existing data
    """
    # Analysis (read-only)
    ANALYZE_AUDIO = "analyze_audio"
    ANALYZE_GEOMETRY = "analyze_geometry"
    ANALYZE_TOOLPATH = "analyze_toolpath"
    ANALYZE_SPECTRUM = "analyze_spectrum"

    # Generation (creates artifacts)
    GENERATE_REPORT = "generate_report"
    GENERATE_GCODE = "generate_gcode"
    GENERATE_DXF = "generate_dxf"
    GENERATE_PREVIEW = "generate_preview"

    # Validation (conformance checks)
    VALIDATE_SCHEMA = "validate_schema"
    VALIDATE_FEASIBILITY = "validate_feasibility"
    VALIDATE_SAFETY = "validate_safety"

    # Transformation (modifies data)
    TRANSFORM_NORMALIZE = "transform_normalize"
    TRANSFORM_REDACT = "transform_redact"
    TRANSFORM_AGGREGATE = "transform_aggregate"


class SafeDefaults(BaseModel):
    """
    Explicit safe defaults for tool operation.

    These defaults are chosen for safety over performance.
    Agents can override, but must do so explicitly.
    """
    model_config = ConfigDict(extra="forbid")

    # Privacy defaults
    redaction_layer: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Default privacy layer (0=ephemeral, 5=cohort-only)"
    )
    pii_scrub_enabled: bool = Field(
        default=True,
        description="Whether to scrub PII by default"
    )

    # Safety defaults
    dry_run: bool = Field(
        default=True,
        description="Preview-only mode by default"
    )
    require_confirmation: bool = Field(
        default=True,
        description="Require user confirmation for destructive actions"
    )

    # Resource defaults
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Default operation timeout"
    )
    max_output_size_bytes: int = Field(
        default=10_000_000,
        ge=1,
        description="Maximum output size (10MB default)"
    )


class ToolCapabilityV1(BaseModel):
    """
    Declares what a tool can do.

    This contract is published by each tool repo and consumed by
    the agent orchestration layer. It enables:
    - Discovery: Agent knows what tools exist
    - Planning: Agent can match user intent to capabilities
    - Safety: Safe defaults are explicit and auditable
    - Versioning: Schema evolution without breaking changes

    Example (tap_tone_pi analyzer):
        ToolCapabilityV1(
            tool_id="tap_tone_analyzer",
            version="1.0.0",
            display_name="Tap Tone Analyzer",
            actions=[CapabilityAction.ANALYZE_AUDIO, CapabilityAction.ANALYZE_SPECTRUM],
            input_schemas=["tap_tone_bundle_v1", "audio_wav"],
            output_schemas=["wolf_candidates_v1", "mode_analysis_v1"],
        )
    """
    model_config = ConfigDict(extra="forbid")

    # Identity
    tool_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique tool identifier (snake_case)"
    )
    version: str = Field(
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version (MAJOR.MINOR.PATCH)"
    )
    display_name: str = Field(
        min_length=1,
        max_length=128,
        description="Human-readable tool name"
    )

    # Capabilities
    actions: list[CapabilityAction] = Field(
        min_length=1,
        description="Actions this tool can perform"
    )
    input_schemas: list[str] = Field(
        default_factory=list,
        description="Schema IDs this tool can consume"
    )
    output_schemas: list[str] = Field(
        default_factory=list,
        description="Schema IDs this tool can produce"
    )

    # Safety
    safe_defaults: SafeDefaults = Field(
        default_factory=SafeDefaults,
        description="Explicit safe defaults for this tool"
    )

    # Metadata
    description: str = Field(
        default="",
        max_length=1024,
        description="Tool description for agent planning"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for capability discovery"
    )

    # Cross-repo coordination
    source_repo: str = Field(
        default="",
        description="Source repository (e.g., 'tap_tone_pi', 'luthiers-toolbox')"
    )
    requires_repos: list[str] = Field(
        default_factory=list,
        description="Other repos this tool depends on"
    )
