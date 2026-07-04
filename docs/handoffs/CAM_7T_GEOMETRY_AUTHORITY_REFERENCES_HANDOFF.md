# CAM Dev Order 7T: Geometry Authority Reference Contracts

**Status**: COMPLETE  
**Date**: 2026-05-20  
**Test Coverage**: 100 tests passing

## Overview

7T establishes a five-layer geometry authority taxonomy that prevents derived geometry from acquiring canonical authority. The core invariant:

> **Derived geometry may carry provenance. Derived geometry may not acquire authority.**

## Five-Layer Taxonomy

| Layer | Authority Rank | Owns Design Truth | Requires Source |
|-------|----------------|-------------------|-----------------|
| canonical_geometry | 100 | YES | NO |
| manufacturing_geometry | 80 | NO | YES |
| cognition_geometry | 60 | NO | YES |
| export_geometry | 40 | NO | YES |
| visualization_geometry | 20 | NO | YES |

### Layer Definitions

1. **canonical_geometry** — Authoritative design truth produced by the approved canonical process following a governed approval event. Only this layer may define canonical geometry. Does not require source reference.

2. **manufacturing_geometry** — Derived manufacturing interpretation consumed by CAM. Must reference upstream canonical source.

3. **cognition_geometry** — Reasoning abstraction for 7S strategies/workspaces. Cannot be exported directly.

4. **export_geometry** — Serialized downstream representation for translators. Cannot be used for strategy reasoning.

5. **visualization_geometry** — UI/rendering convenience only. Cannot be exported, translated, or used for strategy.

## 7T Invariants

All references enforce these invariants via Pydantic `@model_validator`:

```python
may_mutate_source_geometry: bool = False      # ALWAYS
may_promote_to_canonical: bool = False        # ALWAYS
machine_output_allowed: bool = False          # ALWAYS
execution_authorized: bool = False            # ALWAYS
may_define_canonical_geometry: bool = False   # For non-canonical layers
```

Attempting to create a reference violating these invariants raises `ValueError`.

## Validation Gates

| Gate | Meaning | Conditions |
|------|---------|------------|
| GREEN | Valid authority chain | Source valid, provenance present, no violations |
| YELLOW | Valid but incomplete | Missing provenance, incomplete allowed_uses |
| RED | Authority violation | Missing source, authority collapse, invariant violation |

### Authority Collapse Detection

Authority collapse occurs when non-canonical layers claim canonical authority:
- Non-canonical layer has `may_define_canonical_geometry=True`
- Export geometry used as canonical source
- Visualization geometry used for export/strategy

## Files Created

### Core Modules

```
app/cam/geometry_authority_taxonomy.py      # Five-layer definitions
app/cam/geometry_authority_reference.py     # Reference model + factories
app/cam/geometry_authority_validation.py    # GREEN/YELLOW/RED validation
app/cam/geometry_authority_registry.py      # In-memory indexes + CI summary
```

### Router

```
app/routers/cam/geometry_authority_router.py  # HTTP endpoints
```

### Tests

```
tests/cam/test_geometry_authority_references.py  # 100 tests
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/cam/geometry-authority/ | API metadata |
| GET | /api/cam/geometry-authority/layers | List all layers |
| GET | /api/cam/geometry-authority/layers/{layer} | Get layer definition |
| POST | /api/cam/geometry-authority/references/canonical | Create legacy/unapproved canonical reference |
| POST | /api/cam/geometry-authority/references/canonical/process-approved | Create process-approved canonical reference |
| POST | /api/cam/geometry-authority/references/derived | Create derived reference |
| GET | /api/cam/geometry-authority/references | List all references |
| GET | /api/cam/geometry-authority/references/{id} | Get reference by ID |
| GET | /api/cam/geometry-authority/references/by-layer/{layer} | Filter by layer |
| GET | /api/cam/geometry-authority/references/by-source/{source_id} | Filter by source |
| POST | /api/cam/geometry-authority/validate/{reference_id} | Validate reference |
| GET | /api/cam/geometry-authority/validations | List all validations |
| GET | /api/cam/geometry-authority/ci | CI health summary |

## CI Summary

The `/api/cam/geometry-authority/ci` endpoint returns:

```json
{
  "total_references": 42,
  "total_validations": 40,
  "unvalidated_reference_count": 2,
  "green_count": 38,
  "yellow_count": 2,
  "red_count": 0,
  "authority_collapse_count": 0,
  "references_by_layer": {
    "canonical_geometry": 10,
    "manufacturing_geometry": 15,
    "cognition_geometry": 8,
    "export_geometry": 6,
    "visualization_geometry": 3
  },
  "status": "warn"
}
```

Status values:
- **pass**: All references have GREEN validation
- **warn**: Unvalidated refs or YELLOW validations exist
- **fail**: RED validations or authority collapse exists

## Integration with 7S

The 7S workspace and strategy models include optional `geometry_authority_ref_id` fields:

```python
# In LuthierOperationWorkspaceV1
geometry_authority_ref_id: Optional[str] = None

# In GeometryReference
geometry_authority_ref_id: Optional[str] = None

# In LuthierManufacturingStrategy
geometry_authority_ref_id: Optional[str] = None
```

These fields allow workspaces and strategies to reference validated geometry authority contracts.

## Usage Example

```python
from app.cam.geometry_authority_reference import (
    create_process_approved_canonical_geometry_reference,
    create_manufacturing_geometry_reference,
)
from app.cam.canonical_geometry_process_approval import (
    PROPOSED_APPROVAL_RULE_ID,
    PROPOSED_CANONICAL_PROCESS_ID,
    PROPOSED_CANONICAL_PROCESS_VERSION,
    create_canonical_process_approval_record,
)
from app.cam.geometry_authority_registry import (
    register_geometry_authority_reference,
    validate_reference,
    get_ci_summary,
)

# Create process-approved canonical reference
approval_record = create_canonical_process_approval_record(
    canonical_process_id=PROPOSED_CANONICAL_PROCESS_ID,
    canonical_process_version=PROPOSED_CANONICAL_PROCESS_VERSION,
    governed_approval_event_id="event-body-outline-approval",
    approval_rule_id=PROPOSED_APPROVAL_RULE_ID,
    source_geometry_id="ibg-body-outline-source",
    provenance_hash="sha256:abc123...",
    process_inputs_hash="sha256:inputs123...",
    approver_id="human:reviewer",
)
canonical = create_process_approved_canonical_geometry_reference(
    approval_record=approval_record,
    owning_domain="boe",
    description="Martin D-28 body outline",
)
registered = register_geometry_authority_reference(canonical)

# Create derived manufacturing reference
mfg_ref = create_manufacturing_geometry_reference(
    source_geometry_id=registered.geometry_reference_id,
    owning_domain="cam",
    source_authority="ibg",
    provenance_hash="sha256:def456...",
)
register_geometry_authority_reference(mfg_ref)

# Validate references
result = validate_reference(mfg_ref.geometry_reference_id)
print(f"Gate: {result.gate}")  # GREEN, YELLOW, or RED

# Get CI summary
summary = get_ci_summary()
print(f"Status: {summary['status']}")  # pass, warn, or fail
```

## Test Categories

| Category | Count | Description |
|----------|-------|-------------|
| Taxonomy Tests | 15 | Layer definitions, authority rules |
| Taxonomy Helpers | 10 | Helper function behavior |
| Use Permissions | 8 | Allowed/prohibited use checking |
| Reference Creation | 12 | Factory functions, uniqueness |
| Invariant Tests | 12 | Model-enforced constraints |
| Validation Tests | 15 | GREEN/YELLOW/RED gates |
| Registry Tests | 10 | Index operations, lookup |
| CI Summary Tests | 8 | CI health reporting |
| Router Tests | 10 | HTTP endpoint behavior |

## Relationship to Other Dev Orders

- **7S (Governed Manufacturing Cognition)**: 7T provides geometry authority tracking for 7S workspaces and strategies
- **Future 7U**: Will add export authorization gates using 7T references
- **ExportObject/TranslationArtifact**: Can be extended with geometry_authority_ref_id via adapters

## Guardrails

7T **must not**:
- Rewrite geometry
- Merge workspace references
- Make export/translation artifacts authoritative
- Allow derived geometry to claim canonical authority

7T **does**:
- Track provenance through the authority chain
- Validate authority relationships
- Detect and report authority collapse
- Provide CI-compatible health summaries
