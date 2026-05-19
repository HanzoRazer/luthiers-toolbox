"""
Export Object to DXF Translator Adapter

CAM Dev Order 6D/7C: Semantic mapping for translator boundary validation.

This module maps Export Object geometry/toolpath semantics into
translator-neutral classification. It does NOT generate DXF.

Purpose:
  - Detect geometry types from Export Object
  - Classify translator requirements
  - Validate translator compatibility
  - Registry-gated validation (7C)

NOT:
  - DXF generation
  - Coordinate transformation
  - Serialization

Core principle:
  Translation is separate from representation.
  Export Object owns manufacturing intent.
  This adapter prepares for translation without executing it.

7C additions:
  - Registry lookup before compatibility checks
  - Category validation (translator vs postprocessor)
  - Output class validation (must be dxf)
  - Execution state validation
"""

from __future__ import annotations

from typing import List, Optional, Set, Tuple

from app.cam.dxf_translator_boundary import (
    DXFTranslatorCompatibilityReport,
    DXFTranslatorMetadata,
    DXFTranslatorProfile,
)
from app.cam.export_object import ExportObject
from app.cam.translator_capability_registry import (
    TranslatorCapability,
    get_translator_capability,
)


# -----------------------------------------------------------------------------
# Geometry Type Detection
# -----------------------------------------------------------------------------

def detect_geometry_types(export_object: ExportObject) -> List[str]:
    """
    Detect geometry types present in the export object.

    Maps export object structure to DXF-relevant geometry classifications:
      - slot → polyline (linear path)
      - hole → circle (future)
      - profile → polyline (future)
      - arc moves → arc

    Returns list of detected geometry type strings.
    """
    detected = set()

    # Check geometry entities
    if export_object.geometry and export_object.geometry.entities:
        for entity in export_object.geometry.entities:
            entity_type = entity.type.lower()

            # Map entity types to DXF geometry types
            if entity_type in ("slot", "groove", "channel"):
                detected.add("polyline")
                detected.add("line")
            elif entity_type in ("hole", "circle"):
                detected.add("circle")
            elif entity_type in ("arc", "curve"):
                detected.add("arc")
            elif entity_type in ("profile", "contour", "outline"):
                detected.add("polyline")
            elif entity_type in ("spline", "bezier"):
                detected.add("spline")
            else:
                # Default to polyline for unknown entity types
                detected.add("polyline")

    # Check toolpath moves for arc requirements
    if export_object.toolpaths and export_object.toolpaths.operations:
        for op in export_object.toolpaths.operations:
            for move in op.moves:
                if move.type in ("arc_cw", "arc_ccw"):
                    detected.add("arc")
                elif move.type in ("linear", "plunge", "rapid", "retract"):
                    detected.add("line")

    # Ensure at least line/polyline if any geometry exists
    if not detected and export_object.geometry and export_object.geometry.entities:
        detected.add("polyline")

    return sorted(detected)


def detect_required_features(
    export_object: ExportObject,
    geometry_types: List[str],
) -> List[str]:
    """
    Detect translator features required by the export object.

    Returns list of required feature strings.
    """
    features = set()

    # Geometry type requirements
    if "polyline" in geometry_types:
        features.add("polyline_support")
    if "line" in geometry_types:
        features.add("line_support")
    if "arc" in geometry_types:
        features.add("arc_support")
    if "circle" in geometry_types:
        features.add("circle_support")
    if "spline" in geometry_types:
        features.add("spline_support")

    # Layer requirements (always needed for organized output)
    if export_object.geometry and export_object.geometry.entities:
        features.add("layer_support")

    # Multi-operation handling
    if export_object.toolpaths and len(export_object.toolpaths.operations) > 1:
        features.add("multi_entity_support")

    return sorted(features)


# -----------------------------------------------------------------------------
# Registry-Gated Validation (7C)
# -----------------------------------------------------------------------------

def validate_translator_registry(
    translator_id: str,
) -> Tuple[Optional[TranslatorCapability], List[str]]:
    """
    Validate translator against capability registry (7C).

    Checks:
      1. Translator exists in registry
      2. Translator category is 'translator' (not 'postprocessor')
      3. Output class is 'dxf'
      4. Execution state is compatible with validation

    Returns (capability, blocking_issues).
    If blocking_issues is non-empty, validation should fail RED.
    """
    blocking_issues = []

    # 1. Check translator exists
    capability = get_translator_capability(translator_id)
    if capability is None:
        blocking_issues.append(
            f"Unknown translator: '{translator_id}' not found in capability registry"
        )
        return None, blocking_issues

    # 2. Check translator category (translator vs postprocessor)
    if capability.translator_category != "translator":
        blocking_issues.append(
            f"Translator '{translator_id}' is a {capability.translator_category}, "
            f"not a DXF translator"
        )

    # 3. Check output class
    if capability.output_class != "dxf":
        blocking_issues.append(
            f"Translator '{translator_id}' output class '{capability.output_class}' "
            f"is incompatible with DXF validation"
        )

    # 4. Check execution state (execution_disabled means not usable)
    if capability.execution_state == "execution_disabled":
        blocking_issues.append(
            f"Translator '{translator_id}' is disabled and cannot be used for validation"
        )

    return capability, blocking_issues


# -----------------------------------------------------------------------------
# Compatibility Checks
# -----------------------------------------------------------------------------

def check_unit_compatibility(
    export_object: ExportObject,
    translator_profile: DXFTranslatorProfile,
) -> Tuple[bool, str | None]:
    """
    Check unit compatibility between export object and translator.

    Returns (passed, error_message).
    """
    export_units = export_object.geometry.coordinate_system.units
    translator_units = translator_profile.units

    if export_units != translator_units:
        return False, f"Unit mismatch: export uses '{export_units}', translator expects '{translator_units}'"

    return True, None


def check_geometry_support(
    geometry_types: List[str],
    translator_profile: DXFTranslatorProfile,
) -> Tuple[bool, List[str], List[str]]:
    """
    Check if translator supports all detected geometry types.

    Returns (all_supported, unsupported_types, warnings).
    """
    supported = set(translator_profile.supported_geometry_types)
    detected = set(geometry_types)

    unsupported = detected - supported
    warnings = []

    # Check for specific unsupported cases
    if "spline" in unsupported and not translator_profile.supports_splines:
        # This is expected if splines not supported
        pass
    elif "spline" in detected and not translator_profile.supports_splines:
        unsupported.add("spline")

    all_supported = len(unsupported) == 0

    return all_supported, sorted(unsupported), warnings


def check_feature_support(
    required_features: List[str],
    translator_profile: DXFTranslatorProfile,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Check if translator supports required features.

    Returns (blocking_issues, warnings, missing_optional).
    """
    blocking = []
    warnings = []
    missing_optional = []

    for feature in required_features:
        if feature == "polyline_support":
            if "polyline" not in translator_profile.supported_geometry_types:
                blocking.append("Translator does not support polyline geometry")

        elif feature == "line_support":
            if "line" not in translator_profile.supported_geometry_types:
                # Line is fundamental - blocking
                blocking.append("Translator does not support line geometry")

        elif feature == "arc_support":
            if "arc" not in translator_profile.supported_geometry_types:
                blocking.append("Translator does not support arc geometry")

        elif feature == "circle_support":
            if "circle" not in translator_profile.supported_geometry_types:
                blocking.append("Translator does not support circle geometry")

        elif feature == "spline_support":
            if not translator_profile.supports_splines:
                blocking.append("Translator does not support spline geometry")

        elif feature == "layer_support":
            if not translator_profile.supports_layers:
                # Layers are optional but recommended
                warnings.append("Translator does not support layers; geometry will be flat")
                missing_optional.append("layer_support")

        elif feature == "multi_entity_support":
            # All translators should handle multiple entities
            pass

    return blocking, warnings, missing_optional


# -----------------------------------------------------------------------------
# Main Evaluation Function
# -----------------------------------------------------------------------------

def evaluate_dxf_translator_compatibility(
    export_object: ExportObject,
    translator_profile: DXFTranslatorProfile,
) -> DXFTranslatorCompatibilityReport:
    """
    Evaluate export object compatibility with DXF translator profile.

    Returns a compatibility REPORT, not DXF output.
    No serialization occurs. No DXF is generated.

    7C: Registry-gated validation runs FIRST (fail fast).

    Gate logic:
      - GREEN: All checks pass, ready for translation
      - YELLOW: Checks pass with warnings
      - RED: Blocking issues prevent translation
    """
    blocking_issues = []
    warnings = []
    unsupported: List[str] = []

    # --- 7C: Registry validation FIRST (fail fast) ---
    registry_capability, registry_issues = validate_translator_registry(
        translator_profile.translator_id
    )

    if registry_issues:
        # Registry validation failed - return RED immediately
        return DXFTranslatorCompatibilityReport(
            compatible=False,
            gate="red",
            translator_output_generated=False,
            dxf_generated=False,
            translation_ready=False,
            geometry_types_detected=[],
            unsupported_geometry=[],
            warnings=[],
            blocking_issues=registry_issues,
            required_translator_features=[],
            metadata=DXFTranslatorMetadata(
                validation_only=True,
                risk_class="B",
                translator_class="DXF",
                machine_ready=False,
            ),
        )

    # --- Registry validated, proceed with compatibility checks ---

    # Detect geometry types
    geometry_types = detect_geometry_types(export_object)

    # Detect required features
    required_features = detect_required_features(export_object, geometry_types)

    # 1. Unit compatibility check
    unit_passed, unit_error = check_unit_compatibility(export_object, translator_profile)
    if not unit_passed:
        blocking_issues.append(unit_error)

    # 2. Geometry support check
    geom_passed, unsupported, geom_warnings = check_geometry_support(
        geometry_types, translator_profile
    )
    if not geom_passed:
        for unsup in unsupported:
            blocking_issues.append(f"Unsupported geometry type: {unsup}")
    warnings.extend(geom_warnings)

    # 3. Feature support check
    feature_blocking, feature_warnings, _ = check_feature_support(
        required_features, translator_profile
    )
    blocking_issues.extend(feature_blocking)
    warnings.extend(feature_warnings)

    # Determine gate status
    if blocking_issues:
        gate = "red"
        compatible = False
        translation_ready = False
    elif warnings:
        gate = "yellow"
        compatible = True
        translation_ready = True
    else:
        gate = "green"
        compatible = True
        translation_ready = True

    return DXFTranslatorCompatibilityReport(
        compatible=compatible,
        gate=gate,
        translator_output_generated=False,  # Always false
        dxf_generated=False,  # Always false
        translation_ready=translation_ready,
        geometry_types_detected=geometry_types,
        unsupported_geometry=list(unsupported) if not geom_passed else [],
        warnings=warnings,
        blocking_issues=blocking_issues,
        required_translator_features=required_features,
        metadata=DXFTranslatorMetadata(
            validation_only=True,
            risk_class="B",
            translator_class="DXF",
            machine_ready=False,
        ),
    )
