"""
CAD Semantic Extensions for Export Objects.

Sprint: MRP-5C (flat-body basics)
Updated: MRP-5F (acoustic semantic extensions)

Provides optional CAD semantic descriptors that enrich Export Objects
for downstream CAD translators without modifying BOE-approved geometry.

Authority Model:
- BOE: Geometry authority (immutable)
- IBG: Morphology authority (advisory)
- cad_semantics: CAD construction hints (optional)
- Translator: Topology construction (from approved data only)

Key Rule: CAD semantics may EXTEND approved geometry context.
They may NOT override, reinterpret, or invent approved geometry.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ─── Enums ───────────────────────────────────────────────────────────────────


class BodyCategory(str, Enum):
    """Body type classification for CAD translation routing."""

    FLAT_BODY = "flat_body"  # Supported: solid electric guitars
    ACOUSTIC_FLAT_TOP = "acoustic_flat_top"  # Semantic only: steel-string, classical
    ACOUSTIC_ARCHED_TOP = "acoustic_arched_top"  # Future: arched soundboard
    HOLLOW_ELECTRIC = "hollow_electric"  # Future: semi-hollow
    ARCHTOP = "archtop"  # Future: jazz archtop
    RESONATOR = "resonator"  # Future/unsupported: resonator guitars
    UNKNOWN = "unknown"  # Fallback


class SideProfileType(str, Enum):
    """Side/rim depth profile type."""

    UNIFORM = "uniform"  # Constant depth
    TAPERED = "tapered"  # Depth varies tail-to-neck


class ContinuityTarget(str, Enum):
    """
    Target geometric continuity at junctions.

    ADVISORY ONLY — C2-C Constitutional Classification (2026-05-18)

    ContinuityTarget expresses semantic preference and interoperability guidance.

    It does NOT:
    - define geometry authority (see BOE)
    - require manufacturability guarantees (see TopologyTier)
    - imply topology canonization (see ContinuityLevel in topology_builder)
    - feed into validate_continuity() enforcement

    For enforcement-level continuity, see:
        topology_builder.contracts.ContinuityLevel (G0/G1/G2)

    G2 (curvature continuity) is intentionally omitted here because
    acoustic body junctions rarely require G2-level smoothness.

    Consumption path: Currently advisory for CAD translators.
    No direct connection to topology_builder validation.
    """

    G0 = "G0"  # Positional continuity (advisory)
    G1 = "G1"  # Tangent continuity (advisory)


class ClosureType(str, Enum):
    """Rim closure classification."""

    CLOSED_RIM = "closed_rim"  # Standard closed rim
    CUTAWAY = "cutaway"  # Has cutaway


class PlateType(str, Enum):
    """Top/back plate surface type."""

    FLAT = "flat"  # Planar surface
    RADIUSED = "radiused"  # Spherical cap (single radius)
    ARCHED = "arched"  # Carved arch (RESEARCH_ONLY)


class RuntimeSupport(str, Enum):
    """Translator runtime support classification."""

    SUPPORTED = "supported"  # Full runtime generation
    SEMANTIC_ONLY = "semantic_only"  # Schema valid, no runtime topology
    UNSUPPORTED = "unsupported"  # Not supported


# ─── Thickness Semantics (Level 2) ───────────────────────────────────────────


class ThicknessSemantics(BaseModel):
    """
    Level 2 component thickness semantics.

    Provides distinct thickness values for top, back, and side components.
    Level 1 (uniform) uses only uniform_thickness_mm in parent CadSemantics.
    Level 3 (zonal) and Level 4 (continuous) are RESEARCH_ONLY.
    """

    top_thickness_mm: Optional[float] = Field(
        default=None,
        description="Soundboard thickness (typical 2.5-3.5mm)",
        ge=0.1,
        le=50.0,
    )
    back_thickness_mm: Optional[float] = Field(
        default=None,
        description="Back plate thickness (typical 2.0-3.0mm)",
        ge=0.1,
        le=50.0,
    )
    side_depth_mm: Optional[float] = Field(
        default=None,
        description="Side/rim depth (typical 95-125mm for acoustic)",
        ge=1.0,
        le=500.0,
    )

    @field_validator("top_thickness_mm", "back_thickness_mm", "side_depth_mm")
    @classmethod
    def validate_positive(cls, v: Optional[float]) -> Optional[float]:
        """Ensure thickness values are positive when provided."""
        if v is not None and v <= 0:
            raise ValueError("Thickness must be positive")
        return v


# ─── Side/Rim Semantics ──────────────────────────────────────────────────────


class SideProfileSemantics(BaseModel):
    """
    Side/rim depth profile descriptors.

    These are semantic descriptors, not geometry runtime.
    Describes how depth varies from tail to neck.
    """

    type: SideProfileType = Field(
        default=SideProfileType.UNIFORM,
        description="Profile type: uniform or tapered",
    )
    taper_axis: str = Field(
        default="tail_to_neck",
        description="Axis along which taper occurs",
    )
    max_depth_mm: Optional[float] = Field(
        default=None,
        description="Maximum depth (at butt/tail)",
        ge=1.0,
        le=500.0,
    )
    min_depth_mm: Optional[float] = Field(
        default=None,
        description="Minimum depth (at shoulder/neck)",
        ge=1.0,
        le=500.0,
    )

    @field_validator("min_depth_mm")
    @classmethod
    def validate_taper_consistency(
        cls, v: Optional[float], info
    ) -> Optional[float]:
        """Validate taper min/max consistency."""
        if v is not None:
            max_depth = info.data.get("max_depth_mm")
            if max_depth is not None and v > max_depth:
                raise ValueError("min_depth_mm cannot exceed max_depth_mm")
        return v


class RimSemantics(BaseModel):
    """
    Rim junction and continuity descriptors.

    Describes expected continuity at plate-rim junctions.
    These are semantic targets, not runtime guarantees.

    C2-C Advisory Classification: semantic_continuity layer.
    No enforcement path to topology_builder validation.
    """

    continuity_target: ContinuityTarget = Field(
        default=ContinuityTarget.G1,
        description="Advisory target continuity at plate-rim junctions (not enforced)",
    )
    closure_type: ClosureType = Field(
        default=ClosureType.CLOSED_RIM,
        description="Rim closure classification",
    )


# ─── Plate Relationship Semantics ────────────────────────────────────────────


class PlateRelationshipSemantics(BaseModel):
    """
    Top/back plate surface type descriptors.

    Describes plate surface classifications for acoustic bodies.
    """

    top_type: PlateType = Field(
        default=PlateType.FLAT,
        description="Top plate surface type",
    )
    back_type: PlateType = Field(
        default=PlateType.FLAT,
        description="Back plate surface type",
    )
    back_radius_mm: Optional[float] = Field(
        default=None,
        description="Back arch radius for radiused backs (e.g., 7620mm = 25ft)",
        ge=100.0,
    )


# ─── Acoustic Semantics Container ────────────────────────────────────────────


class AcousticSemantics(BaseModel):
    """
    Acoustic body semantic extension container.

    Aggregates acoustic-specific descriptors. All fields optional.
    These are semantic descriptors for future acoustic topology translators.
    Current runtime status: SEMANTIC_ONLY (no topology generation).
    """

    thickness: Optional[ThicknessSemantics] = Field(
        default=None,
        description="Level 2 component thickness semantics",
    )
    side_profile: Optional[SideProfileSemantics] = Field(
        default=None,
        description="Side/rim depth profile semantics",
    )
    rim: Optional[RimSemantics] = Field(
        default=None,
        description="Rim junction semantics",
    )
    plate_relationship: Optional[PlateRelationshipSemantics] = Field(
        default=None,
        description="Top/back plate relationship semantics",
    )

    # IBG reference flag
    use_ibg_side_heights: bool = Field(
        default=False,
        description="Whether to consume IBG side_heights_mm if available",
    )


# ─── Flat Body Semantics ─────────────────────────────────────────────────────


class FlatBodySemantics(BaseModel):
    """
    Flat body extrusion semantics.

    Level 1 thickness: single uniform extrusion depth.
    Supported by current STEP translator (MRP-5C).
    """

    uniform_thickness_mm: float = Field(
        description="Uniform extrusion depth in mm",
        ge=0.1,
        le=500.0,
    )
    extrusion_direction: str = Field(
        default="positive_z",
        description="Extrusion direction from profile plane",
    )
    extrusion_origin: str = Field(
        default="top_face",
        description="Z-origin reference for extrusion",
    )


# ─── Main CadSemantics Schema ────────────────────────────────────────────────


class CadSemantics(BaseModel):
    """
    CAD Semantic Extension for Export Objects.

    Provides optional CAD construction hints for downstream translators.
    All fields except schema_version are optional for backward compatibility.

    Authority Rule:
        cad_semantics may EXTEND approved geometry context.
        It may NOT override, reinterpret, or invent approved geometry.

    Runtime Support:
        - flat_body: SUPPORTED (STEP translator)
        - acoustic_flat_top: SEMANTIC_ONLY (schema valid, no topology)
        - Others: UNSUPPORTED or RESEARCH_ONLY
    """

    # Schema metadata
    schema_version: str = Field(
        default="1.0.0",
        description="CAD semantics schema version",
    )

    # Body classification
    body_category: BodyCategory = Field(
        default=BodyCategory.FLAT_BODY,
        description="Body type classification for translator routing",
    )

    # Level 1: Uniform thickness (flat body)
    flat_body: Optional[FlatBodySemantics] = Field(
        default=None,
        description="Flat body extrusion semantics (Level 1)",
    )

    # Acoustic extensions (Level 2+)
    acoustic: Optional[AcousticSemantics] = Field(
        default=None,
        description="Acoustic body semantic extensions",
    )

    # Legacy compatibility field (MRP-5B proposal)
    uniform_thickness_mm: Optional[float] = Field(
        default=None,
        description="Legacy: uniform thickness (prefer flat_body.uniform_thickness_mm)",
        ge=0.1,
        le=500.0,
    )

    def get_runtime_support(self) -> RuntimeSupport:
        """
        Classify runtime support for this semantic configuration.

        Returns:
            RuntimeSupport enum indicating translator capability.
        """
        if self.body_category == BodyCategory.FLAT_BODY:
            return RuntimeSupport.SUPPORTED
        elif self.body_category == BodyCategory.ACOUSTIC_FLAT_TOP:
            return RuntimeSupport.SEMANTIC_ONLY
        elif self.body_category in (
            BodyCategory.ACOUSTIC_ARCHED_TOP,
            BodyCategory.HOLLOW_ELECTRIC,
            BodyCategory.ARCHTOP,
        ):
            return RuntimeSupport.SEMANTIC_ONLY
        else:
            return RuntimeSupport.UNSUPPORTED

    def get_effective_thickness(self) -> Optional[float]:
        """
        Get effective uniform thickness for flat-body translation.

        Prioritizes flat_body.uniform_thickness_mm over legacy field.

        Returns:
            Thickness in mm, or None if not specified.
        """
        if self.flat_body and self.flat_body.uniform_thickness_mm:
            return self.flat_body.uniform_thickness_mm
        return self.uniform_thickness_mm

    def requires_acoustic_topology(self) -> bool:
        """
        Check if semantic configuration requires acoustic topology runtime.

        Returns:
            True if acoustic topology generation would be required.
        """
        if self.body_category not in (
            BodyCategory.FLAT_BODY,
            BodyCategory.UNKNOWN,
        ):
            return True

        if self.acoustic:
            # Check for non-trivial acoustic semantics
            if self.acoustic.side_profile:
                if self.acoustic.side_profile.type == SideProfileType.TAPERED:
                    return True
            if self.acoustic.plate_relationship:
                if self.acoustic.plate_relationship.top_type != PlateType.FLAT:
                    return True
                if self.acoustic.plate_relationship.back_type != PlateType.FLAT:
                    return True

        return False


# ─── Validation Utilities ────────────────────────────────────────────────────


class SemanticValidationResult(BaseModel):
    """Result of semantic validation."""

    valid: bool
    blocking_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    runtime_support: RuntimeSupport = RuntimeSupport.UNSUPPORTED


def validate_acoustic_semantics(semantics: CadSemantics) -> SemanticValidationResult:
    """
    Validate acoustic semantic configuration.

    Blocking errors:
        - Negative/zero thickness values
        - Invalid enum values
        - Contradictory required fields
        - Taper min > max

    Warnings:
        - Missing optional acoustic fields
        - Unknown future descriptors
        - Incomplete taper profile when not used for runtime

    Args:
        semantics: CadSemantics instance to validate.

    Returns:
        SemanticValidationResult with errors and warnings.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Check body category
    try:
        _ = BodyCategory(semantics.body_category)
    except ValueError:
        errors.append(f"Invalid body_category: {semantics.body_category}")

    # Validate flat_body if present
    if semantics.flat_body:
        if semantics.flat_body.uniform_thickness_mm <= 0:
            errors.append("flat_body.uniform_thickness_mm must be positive")

    # Validate acoustic semantics if present
    if semantics.acoustic:
        acoustic = semantics.acoustic

        # Validate thickness
        if acoustic.thickness:
            th = acoustic.thickness
            if th.top_thickness_mm is not None and th.top_thickness_mm <= 0:
                errors.append("acoustic.thickness.top_thickness_mm must be positive")
            if th.back_thickness_mm is not None and th.back_thickness_mm <= 0:
                errors.append("acoustic.thickness.back_thickness_mm must be positive")
            if th.side_depth_mm is not None and th.side_depth_mm <= 0:
                errors.append("acoustic.thickness.side_depth_mm must be positive")

        # Validate side profile
        if acoustic.side_profile:
            sp = acoustic.side_profile
            if sp.type == SideProfileType.TAPERED:
                if sp.max_depth_mm is None or sp.min_depth_mm is None:
                    warnings.append(
                        "Tapered side_profile missing max/min depth values"
                    )
                elif sp.min_depth_mm > sp.max_depth_mm:
                    errors.append(
                        "side_profile.min_depth_mm cannot exceed max_depth_mm"
                    )

        # Validate plate relationship
        if acoustic.plate_relationship:
            pr = acoustic.plate_relationship
            if pr.back_type == PlateType.RADIUSED and pr.back_radius_mm is None:
                warnings.append(
                    "Radiused back_type specified but back_radius_mm not provided"
                )

    # Check for category/semantic mismatch
    if semantics.body_category == BodyCategory.FLAT_BODY:
        if semantics.acoustic and semantics.requires_acoustic_topology():
            warnings.append(
                "body_category is flat_body but acoustic semantics suggest "
                "acoustic topology requirements"
            )

    # Determine runtime support
    runtime_support = semantics.get_runtime_support()

    return SemanticValidationResult(
        valid=len(errors) == 0,
        blocking_errors=errors,
        warnings=warnings,
        runtime_support=runtime_support,
    )


def classify_acoustic_runtime_support(
    semantics: CadSemantics,
) -> Dict[str, RuntimeSupport]:
    """
    Classify runtime support for each semantic component.

    Args:
        semantics: CadSemantics instance.

    Returns:
        Dict mapping component names to RuntimeSupport.
    """
    result: Dict[str, RuntimeSupport] = {
        "body_category": RuntimeSupport.SUPPORTED
        if semantics.body_category == BodyCategory.FLAT_BODY
        else RuntimeSupport.SEMANTIC_ONLY,
        "flat_body": RuntimeSupport.SUPPORTED
        if semantics.flat_body
        else RuntimeSupport.UNSUPPORTED,
        "acoustic": RuntimeSupport.SEMANTIC_ONLY
        if semantics.acoustic
        else RuntimeSupport.UNSUPPORTED,
    }

    if semantics.acoustic:
        result["acoustic.thickness"] = RuntimeSupport.SEMANTIC_ONLY
        result["acoustic.side_profile"] = RuntimeSupport.SEMANTIC_ONLY
        result["acoustic.rim"] = RuntimeSupport.SEMANTIC_ONLY
        result["acoustic.plate_relationship"] = RuntimeSupport.SEMANTIC_ONLY

    return result
