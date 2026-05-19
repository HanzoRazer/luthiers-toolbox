"""
Topology Runtime Support Classification.

Sprint: MRP-5H
Status: PROTOTYPE

Classifies body categories and semantic configurations by their
topology runtime support level. This is a critical gate that determines
whether topology can be generated at runtime.

Classifications:
    SUPPORTED_PROTOTYPE: Can generate prototype topology now
    PARTIAL_PROTOTYPE: Some features supported, others skipped with warnings
    UNSUPPORTED_RUNTIME: Cannot generate, clean rejection required
    RESEARCH_REQUIRED: Future capability needed
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .contracts import TopologyTier


class TopologyRuntimeSupport(str, Enum):
    """Runtime support classification for topology generation."""

    SUPPORTED_PROTOTYPE = "SUPPORTED_PROTOTYPE"
    PARTIAL_PROTOTYPE = "PARTIAL_PROTOTYPE"
    UNSUPPORTED_RUNTIME = "UNSUPPORTED_RUNTIME"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"


# Body category to runtime support mapping
# Based on ACOUSTIC_TOPOLOGY_READINESS_MATRIX.md
BODY_CATEGORY_SUPPORT: Dict[str, TopologyRuntimeSupport] = {
    # Electric solid bodies - flat extrusion is sufficient
    "flat_body": TopologyRuntimeSupport.SUPPORTED_PROTOTYPE,
    # Flat-top acoustic with uniform thickness - flat extrusion works
    "acoustic_flat_top": TopologyRuntimeSupport.SUPPORTED_PROTOTYPE,
    # Semi-hollow bodies - basic loft may be needed
    "hollow_electric": TopologyRuntimeSupport.PARTIAL_PROTOTYPE,
    # Archtop instruments - complex surface generation required
    "archtop": TopologyRuntimeSupport.RESEARCH_REQUIRED,
    "acoustic_arched_top": TopologyRuntimeSupport.RESEARCH_REQUIRED,
    # Resonator instruments - specialized topology
    "resonator": TopologyRuntimeSupport.RESEARCH_REQUIRED,
    # Unknown category - cannot proceed
    "unknown": TopologyRuntimeSupport.UNSUPPORTED_RUNTIME,
}

# Features that affect support classification
FEATURE_SUPPORT: Dict[str, TopologyRuntimeSupport] = {
    # Thickness models
    "thickness_uniform": TopologyRuntimeSupport.SUPPORTED_PROTOTYPE,
    "thickness_component": TopologyRuntimeSupport.SUPPORTED_PROTOTYPE,
    "thickness_zonal": TopologyRuntimeSupport.PARTIAL_PROTOTYPE,
    "thickness_continuous": TopologyRuntimeSupport.RESEARCH_REQUIRED,
    # Profile types
    "profile_flat": TopologyRuntimeSupport.SUPPORTED_PROTOTYPE,
    "profile_uniform_arch": TopologyRuntimeSupport.PARTIAL_PROTOTYPE,
    "profile_graduated_arch": TopologyRuntimeSupport.RESEARCH_REQUIRED,
    "profile_recurve": TopologyRuntimeSupport.RESEARCH_REQUIRED,
    # Continuity requirements
    "continuity_g0": TopologyRuntimeSupport.SUPPORTED_PROTOTYPE,
    "continuity_g1": TopologyRuntimeSupport.PARTIAL_PROTOTYPE,
    "continuity_g2": TopologyRuntimeSupport.RESEARCH_REQUIRED,
    # Taper types
    "taper_none": TopologyRuntimeSupport.SUPPORTED_PROTOTYPE,
    "taper_linear": TopologyRuntimeSupport.PARTIAL_PROTOTYPE,
    "taper_graduated": TopologyRuntimeSupport.RESEARCH_REQUIRED,
}


def classify_topology_runtime(
    body_category: str,
    cad_semantics: Optional[Dict[str, Any]] = None,
    tier: TopologyTier = TopologyTier.PROTOTYPE,
) -> Tuple[TopologyRuntimeSupport, List[str], List[str]]:
    """
    Classify the topology runtime support for a given configuration.

    Args:
        body_category: The body category from cad_semantics
        cad_semantics: Full CAD semantics dictionary (optional)
        tier: Runtime tier (PROTOTYPE or PRODUCTION)

    Returns:
        Tuple of (classification, supported_features, unsupported_features)
    """
    supported_features: List[str] = []
    unsupported_features: List[str] = []
    warnings: List[str] = []

    # Start with body category classification
    base_support = BODY_CATEGORY_SUPPORT.get(
        body_category, TopologyRuntimeSupport.UNSUPPORTED_RUNTIME
    )

    if base_support == TopologyRuntimeSupport.UNSUPPORTED_RUNTIME:
        unsupported_features.append(f"body_category:{body_category}")
        return base_support, supported_features, unsupported_features

    supported_features.append(f"body_category:{body_category}")

    # If no semantics provided, return base classification
    if not cad_semantics:
        return base_support, supported_features, unsupported_features

    # Analyze acoustic semantics if present
    acoustic = cad_semantics.get("acoustic")
    if acoustic:
        # Check thickness model
        thickness = acoustic.get("thickness")
        if thickness:
            level = thickness.get("level", 1)
            if level == 1:
                supported_features.append("thickness_uniform")
            elif level == 2:
                supported_features.append("thickness_component")
            elif level == 3:
                if _is_supported(FEATURE_SUPPORT.get("thickness_zonal")):
                    supported_features.append("thickness_zonal")
                else:
                    unsupported_features.append("thickness_zonal")
            elif level >= 4:
                unsupported_features.append("thickness_continuous")

        # Check side profile
        side_profile = acoustic.get("side_profile")
        if side_profile:
            profile_type = side_profile.get("profile_type", "flat")
            feature_key = f"profile_{profile_type}"
            feature_support = FEATURE_SUPPORT.get(
                feature_key, TopologyRuntimeSupport.UNSUPPORTED_RUNTIME
            )
            if _is_supported(feature_support):
                supported_features.append(feature_key)
            else:
                unsupported_features.append(feature_key)

        # Check continuity requirements
        continuity = acoustic.get("continuity_targets", {})
        for junction, target in continuity.items():
            feature_key = f"continuity_{target.lower()}"
            feature_support = FEATURE_SUPPORT.get(
                feature_key, TopologyRuntimeSupport.RESEARCH_REQUIRED
            )
            if _is_supported(feature_support):
                supported_features.append(f"{junction}:{target}")
            else:
                unsupported_features.append(f"{junction}:{target}")

    # Determine final classification
    final_support = _compute_final_support(
        base_support, supported_features, unsupported_features, tier
    )

    return final_support, supported_features, unsupported_features


def _is_supported(support: Optional[TopologyRuntimeSupport]) -> bool:
    """Check if a feature support level allows prototype generation."""
    if support is None:
        return False
    return support in (
        TopologyRuntimeSupport.SUPPORTED_PROTOTYPE,
        TopologyRuntimeSupport.PARTIAL_PROTOTYPE,
    )


def _compute_final_support(
    base_support: TopologyRuntimeSupport,
    supported_features: List[str],
    unsupported_features: List[str],
    tier: TopologyTier,
) -> TopologyRuntimeSupport:
    """Compute the final support classification."""
    # If base is unsupported, stay unsupported
    if base_support == TopologyRuntimeSupport.UNSUPPORTED_RUNTIME:
        return TopologyRuntimeSupport.UNSUPPORTED_RUNTIME

    # If base requires research, stay at research
    if base_support == TopologyRuntimeSupport.RESEARCH_REQUIRED:
        return TopologyRuntimeSupport.RESEARCH_REQUIRED

    # If any unsupported features exist
    if unsupported_features:
        # In PRODUCTION tier, unsupported features block
        if tier == TopologyTier.PRODUCTION:
            return TopologyRuntimeSupport.UNSUPPORTED_RUNTIME
        # In PROTOTYPE tier, we may still proceed with partial support
        return TopologyRuntimeSupport.PARTIAL_PROTOTYPE

    # If base is partial, stay partial
    if base_support == TopologyRuntimeSupport.PARTIAL_PROTOTYPE:
        return TopologyRuntimeSupport.PARTIAL_PROTOTYPE

    # Fully supported
    return TopologyRuntimeSupport.SUPPORTED_PROTOTYPE


def get_unsupported_reason(
    support: TopologyRuntimeSupport, unsupported_features: List[str]
) -> str:
    """Generate a human-readable reason for unsupported classification."""
    if support == TopologyRuntimeSupport.SUPPORTED_PROTOTYPE:
        return "Fully supported for prototype generation"

    if support == TopologyRuntimeSupport.PARTIAL_PROTOTYPE:
        if unsupported_features:
            return (
                f"Partial support. Unsupported features will be skipped: "
                f"{', '.join(unsupported_features)}"
            )
        return "Partial support with some limitations"

    if support == TopologyRuntimeSupport.UNSUPPORTED_RUNTIME:
        if unsupported_features:
            return (
                f"Cannot generate topology. Blocking features: "
                f"{', '.join(unsupported_features)}"
            )
        return "Cannot generate topology for this configuration"

    if support == TopologyRuntimeSupport.RESEARCH_REQUIRED:
        return "Topology generation requires research/implementation not yet available"

    return "Unknown support classification"


def can_generate_topology(support: TopologyRuntimeSupport) -> bool:
    """Check if topology can be generated with this support level."""
    return support in (
        TopologyRuntimeSupport.SUPPORTED_PROTOTYPE,
        TopologyRuntimeSupport.PARTIAL_PROTOTYPE,
    )
