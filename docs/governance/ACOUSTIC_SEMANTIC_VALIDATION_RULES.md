# Acoustic Semantic Validation Rules

**Sprint:** MRP-5F  
**Status:** ACTIVE  
**Authority:** CAD Semantic Governance

---

## Purpose

Define validation rules for acoustic semantic configurations. These rules ensure schema integrity while distinguishing between blocking errors and non-blocking warnings.

---

## Validation Classification

### Blocking Errors

Blocking errors prevent further processing. The Export Object is rejected.

| Rule | Field | Condition | Error Message |
|------|-------|-----------|---------------|
| V001 | `top_thickness_mm` | ≤ 0 or < 0.1 | "top_thickness_mm must be positive" |
| V002 | `back_thickness_mm` | ≤ 0 or < 0.1 | "back_thickness_mm must be positive" |
| V003 | `side_depth_mm` | ≤ 0 or < 1.0 | "side_depth_mm must be positive" |
| V004 | `body_category` | Invalid enum | "Invalid body_category: {value}" |
| V005 | `min_depth_mm` | > `max_depth_mm` | "min_depth_mm cannot exceed max_depth_mm" |
| V006 | `uniform_thickness_mm` | ≤ 0 | "uniform_thickness_mm must be positive" |

### Warnings

Warnings are logged but do not block processing.

| Rule | Field | Condition | Warning Message |
|------|-------|-----------|-----------------|
| W001 | `side_profile` | TAPERED without depths | "Tapered side_profile missing max/min depth values" |
| W002 | `plate_relationship` | RADIUSED without radius | "Radiused back_type specified but back_radius_mm not provided" |
| W003 | `body_category` | FLAT_BODY with acoustic topology | "body_category is flat_body but acoustic semantics suggest acoustic topology requirements" |
| W004 | Unknown field | Future semantic | "Unknown semantic field: {field}" |

---

## Field Constraints

### Thickness Fields

| Field | Type | Min | Max | Units |
|-------|------|-----|-----|-------|
| `top_thickness_mm` | float | 0.1 | 50.0 | mm |
| `back_thickness_mm` | float | 0.1 | 50.0 | mm |
| `side_depth_mm` | float | 1.0 | 500.0 | mm |
| `uniform_thickness_mm` | float | 0.1 | 500.0 | mm |
| `back_radius_mm` | float | 100.0 | — | mm |

### Depth Fields

| Field | Type | Min | Max | Units |
|-------|------|-----|-----|-------|
| `max_depth_mm` | float | 1.0 | 500.0 | mm |
| `min_depth_mm` | float | 1.0 | 500.0 | mm |

### Consistency Rules

```
IF side_profile.type == TAPERED:
    min_depth_mm <= max_depth_mm  # REQUIRED

IF plate_relationship.back_type == RADIUSED:
    back_radius_mm IS RECOMMENDED
```

---

## Validation Flow

```
Input: CadSemantics
    │
    ├── Check body_category enum
    │   └── Invalid? → BLOCKING ERROR
    │
    ├── Check flat_body (if present)
    │   └── uniform_thickness_mm > 0? → BLOCKING if not
    │
    ├── Check acoustic.thickness (if present)
    │   ├── top_thickness_mm > 0? → BLOCKING if not
    │   ├── back_thickness_mm > 0? → BLOCKING if not
    │   └── side_depth_mm > 0? → BLOCKING if not
    │
    ├── Check acoustic.side_profile (if present)
    │   ├── TAPERED with min > max? → BLOCKING
    │   └── TAPERED without depths? → WARNING
    │
    ├── Check acoustic.plate_relationship (if present)
    │   └── RADIUSED without radius? → WARNING
    │
    └── Check category/semantic mismatch
        └── FLAT_BODY with acoustic topology? → WARNING

Output: SemanticValidationResult
    ├── valid: bool
    ├── blocking_errors: List[str]
    ├── warnings: List[str]
    └── runtime_support: RuntimeSupport
```

---

## Runtime Support Determination

```python
def get_runtime_support(semantics: CadSemantics) -> RuntimeSupport:
    if semantics.body_category == BodyCategory.FLAT_BODY:
        return RuntimeSupport.SUPPORTED
    elif semantics.body_category in (
        BodyCategory.ACOUSTIC_FLAT_TOP,
        BodyCategory.ACOUSTIC_ARCHED_TOP,
        BodyCategory.HOLLOW_ELECTRIC,
        BodyCategory.ARCHTOP,
    ):
        return RuntimeSupport.SEMANTIC_ONLY
    else:
        return RuntimeSupport.UNSUPPORTED
```

---

## Acoustic Topology Detection

```python
def requires_acoustic_topology(semantics: CadSemantics) -> bool:
    # Non-flat body categories require topology
    if semantics.body_category not in (
        BodyCategory.FLAT_BODY,
        BodyCategory.UNKNOWN,
    ):
        return True

    # Check for non-trivial acoustic semantics
    if semantics.acoustic:
        # Tapered sides require topology
        if (semantics.acoustic.side_profile and
            semantics.acoustic.side_profile.type == SideProfileType.TAPERED):
            return True

        # Non-flat plates require topology
        if semantics.acoustic.plate_relationship:
            if semantics.acoustic.plate_relationship.top_type != PlateType.FLAT:
                return True
            if semantics.acoustic.plate_relationship.back_type != PlateType.FLAT:
                return True

    return False
```

---

## Translator Validation Integration

### Pre-Translation Check

```python
def validate_for_translation(export_object: BodyExportObject) -> ValidationResult:
    # Standard geometry validation
    geo_result = validate_body_geometry(export_object)
    if not geo_result.valid:
        return geo_result

    # Semantic validation (if present)
    if export_object.extensions and export_object.extensions.cad_semantics:
        sem_result = validate_acoustic_semantics(
            export_object.extensions.cad_semantics
        )
        if not sem_result.valid:
            return ValidationResult(
                valid=False,
                errors=sem_result.blocking_errors,
            )

    return ValidationResult(valid=True)
```

### Safe Rejection

```python
def translate(export_object: BodyExportObject) -> TranslatorResult:
    semantics = export_object.extensions.cad_semantics

    if semantics and semantics.requires_acoustic_topology():
        return TranslatorResult(
            success=False,
            error_classification="UNSUPPORTED_TOPOLOGY_RUNTIME",
            message=(
                f"Acoustic topology generation not supported for "
                f"body_category={semantics.body_category.value}. "
                f"Runtime support: {semantics.get_runtime_support().value}"
            ),
        )

    # Proceed with supported translation...
```

---

## Test Coverage

| Rule | Test File | Test Class |
|------|-----------|------------|
| V001-V003 | `test_acoustic_semantic_validation.py` | `TestInvalidThicknessRejection` |
| V004 | `test_acoustic_semantic_validation.py` | `TestEnumValidation` |
| V005 | `test_acoustic_semantic_validation.py` | `TestTaperConsistency` |
| W001 | `test_acoustic_semantic_validation.py` | `TestTaperConsistency` |
| W002 | `test_acoustic_semantic_validation.py` | `TestPlateRelationship` |
| W003 | `test_acoustic_semantic_validation.py` | `TestCategorySemanticMismatch` |

---

## Related Documents

- `ACOUSTIC_CAD_SEMANTIC_EXTENSION_MODEL.md` — Schema structure
- `ACOUSTIC_RUNTIME_LIMITATIONS.md` — Runtime constraints
- `CAD_REGRESSION_CLASSIFICATION_MODEL.md` — Error classification
