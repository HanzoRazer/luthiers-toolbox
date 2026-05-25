# CAM Dev Order 7U: Strategy/Export Interoperability Contracts

**Status**: COMPLETE  
**Date**: 2026-05-21  
**Test Coverage**: 70 tests passing

## Overview

7U is a bridge layer between 7S cognition artifacts (workspaces/strategies) and governed translation artifacts (existing translator governance). It answers the question:

> **Can this strategy/workspace be safely packaged for this export/translator pathway without violating geometry authority, review state, or execution quarantine?**

## Core Principle

7U packages review-safe export intent by reference. It does not:
- Resolve objects into authority
- Create export payloads
- Invoke translators
- Serialize geometry
- Authorize machine output

## 7U Invariants

All models enforce these invariants via Pydantic `@model_validator`:

```python
execution_authorized: bool = False           # ALWAYS
machine_output_allowed: bool = False         # ALWAYS
serializer_invocation_allowed: bool = False  # ALWAYS
generates_gcode: bool = False                # ALWAYS
```

## Core Models

### StrategyExportCompatibilityEvaluation

Validates whether a cognition artifact can be safely packaged for export.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| workspace_id | Optional[str] | Workspace being evaluated |
| strategy_id | Optional[str] | Strategy being evaluated |
| target_translator_id | Optional[str] | Translator for targeted evaluation |
| modality_compatible | bool | Modality compatibility |
| geometry_authority_exportable | bool | Geometry authority permits export |
| translator_capability_compatible | bool | Translator capabilities match |
| review_state_valid | bool | Review state permits packaging |
| quarantine_respected | bool | Quarantine status respected |
| provenance_complete | bool | Provenance chain complete |
| gate | ValidationGate | GREEN/YELLOW/RED |
| blocking_issues | List[str] | RED blocking issues |
| warnings | List[str] | YELLOW warnings |

**Evaluation Modes:**

1. **General** (no target_translator_id):
   - Checks geometry authority refs
   - Review status
   - Provenance refs
   - Modality compatibility
   - Non-executable invariants

2. **Targeted** (with target_translator_id):
   - All general checks plus:
   - Translator capability registry
   - Translation artifact compatibility
   - Quarantine/governance status

### ReviewSafeExportPackage

Human-review bundle collecting ID-only references.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| workspace_id | Optional[str] | Source workspace |
| strategy_id | Optional[str] | Source strategy |
| strategy_ids | List[str] | Additional strategies |
| geometry_authority_ref_ids | List[str] | Geometry authority refs |
| export_object_id | Optional[str] | Target export object |
| translation_artifact_id | Optional[str] | Target translation artifact |
| translator_id | Optional[str] | Target translator |
| compatibility_evaluation_ids | List[str] | Linked evaluations |
| review_status | PackageReviewStatus | draft/pending/approved/rejected |
| blocking_issues | List[str] | Issues blocking approval |
| warnings | List[str] | Non-blocking warnings |
| provenance_refs | List[str] | Provenance chain |

## Files Created

### Core Modules

```
app/cam/strategy_export_compatibility.py   # Evaluation model + logic
app/cam/review_safe_export_package.py      # Package model + helpers
app/cam/strategy_export_registry.py        # Indexes + CI + adapters
```

### Router

```
app/routers/cam/strategy_export_router.py  # HTTP endpoints
```

### Tests

```
tests/cam/test_strategy_export_compatibility.py  # 70 tests
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/cam/strategy-export/ | API metadata |
| POST | /api/cam/strategy-export/evaluate | Evaluate compatibility |
| GET | /api/cam/strategy-export/evaluations | List evaluations |
| GET | /api/cam/strategy-export/evaluations/{id} | Get evaluation |
| GET | /api/cam/strategy-export/evaluations/by-workspace/{id} | Filter by workspace |
| GET | /api/cam/strategy-export/evaluations/by-strategy/{id} | Filter by strategy |
| POST | /api/cam/strategy-export/packages | Create package |
| GET | /api/cam/strategy-export/packages | List packages |
| GET | /api/cam/strategy-export/packages/{id} | Get package |
| GET | /api/cam/strategy-export/packages/by-workspace/{id} | Filter by workspace |
| GET | /api/cam/strategy-export/packages/by-review-status/{status} | Filter by status |
| POST | /api/cam/strategy-export/packages/{id}/evaluations | Add evaluation |
| POST | /api/cam/strategy-export/packages/{id}/review-status | Update status |
| POST | /api/cam/strategy-export/packages/{id}/validate | Validate package |
| GET | /api/cam/strategy-export/ci | CI health summary |

## CI Summary

The `/api/cam/strategy-export/ci` endpoint returns:

```json
{
  "total_evaluations": 15,
  "total_packages": 8,
  "green_count": 10,
  "yellow_count": 4,
  "red_count": 1,
  "package_without_review_count": 3,
  "packages_with_blocking_issues": 1,
  "packages_approved": 4,
  "evaluations_by_gate": {
    "green": 10,
    "yellow": 4,
    "red": 1
  },
  "packages_by_review_status": {
    "draft": 2,
    "pending_review": 1,
    "approved": 4,
    "rejected": 1
  },
  "status": "fail"
}
```

**Status values:**
- **fail**: Any RED evaluation or package with blocking issues
- **warn**: YELLOW evaluations or packages lacking review
- **pass**: All GREEN evaluations and packages are review-safe

## Adapter Functions

7U includes adapter functions to query existing translator infrastructure:

```python
get_translator_capability_for_export(translator_id)
evaluate_translator_capability_compatibility(translator_id, modality_id)
check_translator_quarantine_status(translator_id)
```

These query existing registries without creating new dependencies.

## Usage Example

```python
from app.cam.strategy_export_compatibility import (
    evaluate_general_export_readiness,
    evaluate_targeted_translator_compatibility,
)
from app.cam.review_safe_export_package import (
    create_review_safe_export_package,
    add_compatibility_evaluation,
    update_review_status,
)
from app.cam.strategy_export_registry import (
    register_strategy_export_compatibility,
    register_review_safe_export_package,
    get_ci_summary,
)

# Evaluate general export readiness
general_eval = evaluate_general_export_readiness(
    workspace_id="ws-123",
    geometry_authority_ref_ids=["geo-auth-1", "geo-auth-2"],
    review_status="validated",
)
registered_eval = register_strategy_export_compatibility(general_eval)
print(f"General evaluation gate: {general_eval.gate}")

# Evaluate targeted translator compatibility
targeted_eval = evaluate_targeted_translator_compatibility(
    workspace_id="ws-123",
    target_translator_id="translator-dxf-r2000",
    geometry_authority_ref_ids=["geo-auth-1"],
    modality_id="body_outline_routing",
)
register_strategy_export_compatibility(targeted_eval)
print(f"Targeted evaluation gate: {targeted_eval.gate}")

# Create review-safe package
package = create_review_safe_export_package(
    workspace_id="ws-123",
    geometry_authority_ref_ids=["geo-auth-1"],
    translator_id="translator-dxf-r2000",
    title="Body Outline Export Package",
)
add_compatibility_evaluation(package, general_eval.evaluation_id)
add_compatibility_evaluation(package, targeted_eval.evaluation_id)
register_review_safe_export_package(package)

# Submit for review
update_review_status(package, "pending_review", "Ready for human review")

# Check CI health
summary = get_ci_summary()
print(f"CI Status: {summary['status']}")
```

## Relationship to Other Dev Orders

| Dev Order | Relationship |
|-----------|--------------|
| 7S | 7U bridges 7S workspaces/strategies to export governance |
| 7T | 7U validates geometry authority references from 7T |
| Existing Translator Governance | 7U queries but does not replace translator registries |
| ExportObject | 7U references but does not extend ExportObject |
| TranslationArtifact | 7U references but does not modify TranslationArtifact |

## Validation Gates

| Gate | Meaning |
|------|---------|
| GREEN | All checks pass, ready for packaging |
| YELLOW | Warnings present (missing provenance, incomplete modality) |
| RED | Blocking issues (archived workspace, quarantined translator) |

## Test Categories

| Category | Count | Description |
|----------|-------|-------------|
| Evaluation Tests | 15 | Compatibility evaluation logic |
| Invariant Tests | 8 | Model-enforced constraints |
| Package Tests | 15 | Review-safe package model |
| Registry Tests | 12 | Index operations, lookup |
| CI Summary Tests | 8 | CI health reporting |
| Router Tests | 12 | HTTP endpoint behavior |

## Guardrails

7U **must not**:
- Create export payloads
- Invoke translators
- Serialize geometry
- Generate G-code
- Authorize machine output
- Resolve objects into authority

7U **does**:
- Evaluate strategy/export compatibility
- Package review-safe export intent by ID reference
- Track review status
- Provide CI-compatible health summaries
- Bridge cognition artifacts to governed translation
