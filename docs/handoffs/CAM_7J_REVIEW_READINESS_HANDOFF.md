# CAM Dev Order 7J: Governance Review Readiness Matrix

**Status**: COMPLETE  
**Date**: 2026-05-14  
**Depends on**: 7I (Governance Dossier)

## Purpose

7J transforms governance dossier evidence into a deterministic human-review readiness matrix. It evaluates governance completeness, scores review readiness, and classifies deficiencies into blockers and warnings.

**Key distinction**: A review readiness matrix determines whether evidence is complete enough for human review. It does NOT create approval authority, execution authority, or mutation authority.

## Files Created

| File | Purpose |
|------|---------|
| `app/cam/translator_governance_review_matrix.py` | Core matrix model, scoring engine, evaluator, in-memory index |
| `app/routers/cam/translator_governance_review_router.py` | REST endpoints |
| `tests/cam/test_translator_governance_review_matrix.py` | 53 tests |

## Files Modified

| File | Change |
|------|--------|
| `app/router_registry/manifests/cam_manifest.py` | Router registration |

## Architecture

### Review Matrix Model

```python
class TranslatorGovernanceReviewMatrix(BaseModel):
    review_matrix_id: str
    dossier_id: str
    translator_id: str
    
    # Gate and scoring
    review_gate: Literal["green", "yellow", "red"]
    review_readiness_score: int  # 0-100
    
    # Integrity checks
    dossier_integrity_valid: bool
    provenance_integrity_valid: bool
    quarantine_integrity_valid: bool
    authorization_integrity_valid: bool
    readiness_integrity_valid: bool
    
    # Governance completeness
    governance_constraints_satisfied: bool
    escalation_layers_complete: bool
    
    # Deficiency counts
    blocker_count: int
    warning_count: int
    blockers: List[str]
    warnings: List[str]
    
    # Human review requirements
    required_human_reviews: List[str]
    
    # Review state
    review_state: Literal["review_only", "non_executable", "future_escalation_required"]
    
    # Eligibility
    eligible_for_human_governance_review: bool
    
    # 7J invariants (model-enforced)
    execution_authorized: bool = False      # Always false
    machine_output_allowed: bool = False    # Always false
```

### Deterministic Scoring

| Category | Weight |
|----------|--------|
| Dossier integrity | 20 |
| Provenance integrity | 20 |
| Quarantine integrity | 20 |
| Authorization integrity | 15 |
| Readiness integrity | 15 |
| Governance completeness | 10 |
| **Total** | **100** |

### Gate Thresholds

| Score | Gate |
|-------|------|
| >= 80 | GREEN |
| 50-79 | YELLOW |
| < 50 | RED |

**Hard RED conditions** (override score):
- Dossier integrity failure
- Provenance integrity failure
- Quarantine invariant failure
- Authorization invariant failure
- Readiness invariant failure
- Missing required escalation layers
- `execution_authorized = true`
- `machine_output_allowed = true`
- `immutable = false`

### Eligibility Rules

```
eligible_for_human_governance_review = true ONLY when:
  - review_gate != "red"
  - blocker_count == 0
  - execution_authorized == false
  - machine_output_allowed == false
```

Warnings do not affect eligibility.

### Blocker vs Warning Classification

**Blockers** (prevent eligibility):
- Integrity failures
- Invariant violations
- Missing required escalation layers
- Execution/machine output flags true

**Warnings** (informational):
- Score below ideal but no invariant broken
- Readiness gate not green
- Authorization not eligible
- Non-critical missing metadata

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/cam/translators/governance-review/evaluate` | Evaluate review readiness |
| GET | `/api/cam/translators/governance-review` | List all matrices |
| GET | `/api/cam/translators/governance-review/policy` | Get policy config |
| GET | `/api/cam/translators/governance-review/{id}` | Get by ID |
| GET | `/api/cam/translators/governance-review/by-translator/{id}` | Get by translator |

## 7J Invariants

All model-enforced via Pydantic validators:

1. **execution_authorized = false** — matrix never authorizes execution
2. **machine_output_allowed = false** — matrix never permits machine output

## In-Memory Index

```python
REVIEW_MATRIX_INDEX: Dict[str, TranslatorGovernanceReviewMatrix] = {}
```

Functions:
- `register_review_matrix(matrix)`
- `get_review_matrix(review_matrix_id)`
- `list_review_matrices()`
- `list_review_matrices_for_translator(translator_id)`
- `get_latest_review_matrix_for_translator(translator_id)`
- `clear_review_matrix_index()`

## Optional RMOS Persistence

Enabled via `persist_to_rmos=True` parameter.

Artifact kind: `translator_governance_review_matrix_json`

Persists metadata only — no executable payloads.

## Canonical Escalation Layers

Required human reviews derived from dossier's required_escalation_layers:

1. `governance_review`
2. `translator_execution_architecture_review`
3. `human_approval`
4. `security_review`
5. `artifact_generation_policy_review`

Missing any layer causes a blocker.

## Test Coverage

53 tests covering:
- 7J invariants (4 tests)
- Deterministic scoring (7 tests)
- Gate thresholds (7 tests)
- Deficiency classification (4 tests)
- Eligibility logic (5 tests)
- Evidence hashing (3 tests)
- Index operations (4 tests)
- Summary model (2 tests)
- Endpoints (6 tests)
- Safety assertions (3 tests)
- Canonical constants (4 tests)
- RMOS persistence (2 tests)

## Guardrail

> 7J determines review readiness only. It does not create approval authority, execution authority, or mutation authority.

## Chain Summary

```
7E (Authorization) ──┐
7F (Provenance) ─────┼──► 7I (Dossier) ──► 7J (Review Matrix)
7G (Readiness) ──────┤
7H (Quarantine) ─────┘
```

7J consumes dossiers from 7I and produces review readiness evaluations. It is the final governance aggregation layer before any future governance escalation process could theoretically begin.
