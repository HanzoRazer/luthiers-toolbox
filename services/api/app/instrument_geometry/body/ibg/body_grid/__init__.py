"""
Body Grid — Semantic Morphology System for IBG
===============================================

Provides a deterministic Body Grid semantic model for reasoning
about musical instrument body variants.

The Body Grid teaches the system how to handle variants by separating
invariants from variant expressions.

Usage:
    from app.instrument_geometry.body.ibg.body_grid import (
        MorphologyAnalyzer,
        MorphologyDescriptor,
        BodyEvidence,
        export_overlay,
    )

    # Analyze body evidence
    analyzer = MorphologyAnalyzer()
    evidence = BodyEvidence(outline_points=[(x, y), ...])
    descriptor = analyzer.analyze(evidence)

    # Export human review overlay
    export_overlay(descriptor, "body_grid_overlay.png")

    # Get classification
    print(descriptor.variant_match.morphology_class)

Author: Production Shop
Date: 2026-05-15
Sprint: IBG Body Grid Semantic Encoding
"""

# Core schema
from .body_grid_schema import (
    BodyEvidence,
    CenterlineDescriptor,
    AsymmetryDescriptor,
    ContourSegment,
    CoordinateSpace,
    EvidenceSource,
    HardwareRegion,
    Landmark,
    NormalizedPoint,
    RawCoordinate,
    ZoneAssignment,
)

# Zones
from .zones import (
    ZoneId,
    ZoneDefinition,
    ZoneClassifier,
    ZONE_DEFINITIONS,
)

# Primitives
from .primitives import (
    CurvatureClass,
    GeometryType,
    MorphologyPrimitive,
    PrimitiveDetector,
    PrimitiveType,
    SlopeClass,
)

# Variant grammar
from .variant_grammar import (
    BodyMorphologyClass,
    BoutBehavior,
    HornBehavior,
    VariantGrammar,
    VariantMatch,
    VariantRule,
    WaistBehavior,
    VARIANT_RULES,
)

# Normalizer
from .grid_normalizer import (
    GridNormalizer,
    NormalizationTransform,
    normalize_from_landmarks,
)

# Main output
from .morphology_descriptor import (
    FlankProfile,
    MorphologyAnalyzer,
    MorphologyDescriptor,
    analyze_from_dxf_landmarks,
)

# Overlay export
from .overlay_exporter import (
    OverlayConfig,
    OverlayExporter,
    export_overlay,
)

__all__ = [
    # Schema
    "BodyEvidence",
    "CenterlineDescriptor",
    "AsymmetryDescriptor",
    "ContourSegment",
    "CoordinateSpace",
    "EvidenceSource",
    "HardwareRegion",
    "Landmark",
    "NormalizedPoint",
    "RawCoordinate",
    "ZoneAssignment",
    # Zones
    "ZoneId",
    "ZoneDefinition",
    "ZoneClassifier",
    "ZONE_DEFINITIONS",
    # Primitives
    "CurvatureClass",
    "GeometryType",
    "MorphologyPrimitive",
    "PrimitiveDetector",
    "PrimitiveType",
    "SlopeClass",
    # Variant grammar
    "BodyMorphologyClass",
    "BoutBehavior",
    "HornBehavior",
    "VariantGrammar",
    "VariantMatch",
    "VariantRule",
    "WaistBehavior",
    "VARIANT_RULES",
    # Normalizer
    "GridNormalizer",
    "NormalizationTransform",
    "normalize_from_landmarks",
    # Main output
    "FlankProfile",
    "MorphologyAnalyzer",
    "MorphologyDescriptor",
    "analyze_from_dxf_landmarks",
    # Overlay
    "OverlayConfig",
    "OverlayExporter",
    "export_overlay",
]
