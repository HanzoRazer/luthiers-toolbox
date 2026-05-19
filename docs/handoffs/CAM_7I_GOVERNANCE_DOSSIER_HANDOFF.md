# CAM Dev Order 7I: Governance Escalation Dossier

**Status**: COMPLETE  
**Date**: 2026-05-14  
**Depends on**: 7E (Authorization), 7F (Provenance), 7G (Readiness), 7H (Quarantine)

## Purpose

7I packages complete governance evidence into a single immutable dossier for human review. It does NOT create approval authority, execution authority, or mutation authority.

## Files Created

| File | Purpose |
|------|---------|
| `app/cam/translator_governance_dossier.py` | Core dossier model, builder, in-memory index |
| `app/routers/cam/translator_governance_dossier_router.py` | REST endpoints |
| `tests/cam/test_translator_governance_dossier.py` | 34 tests |

## Files Modified

| File | Change |
|------|--------|
| `app/cam/translator_execution_quarantine.py` | Added `governance_dossier_summary` field |
| `app/router_registry/manifests/cam_manifest.py` | Router registration |

## Architecture

### Dossier Model

```python
class TranslatorGovernanceDossier(BaseModel):
    dossier_id: str
    translator_id: str
    
    # Evidence snapshots (from 7E, 7F, 7G, 7H)
    readiness_snapshot: Dict[str, Any]
    provenance_snapshot: Dict[str, Any]
    authorization_snapshot: Dict[str, Any]
    freeze_manifest_snapshot: Dict[str, Any]
    
    # Hash chains for tamper evidence
    evidence_hash: str  # SHA256 of all snapshots
    lifecycle_hashes: List[str]
    audit_hashes: List[str]
    promotion_evidence_hashes: List[str]
    
    # Governance metadata
    governance_constraints: List[str]
    required_escalation_layers: List[str]
    review_state: str  # "future_escalation_required"
    
    # 7I invariants (model-enforced)
    execution_authorized: bool = False      # Always false
    machine_output_allowed: bool = False    # Always false
    immutable: bool = True                  # Always true
```

### In-Memory Index

```python
DOSSIER_INDEX: Dict[str, TranslatorGovernanceDossier] = {}
```

### Deterministic Hashing

Evidence hash is computed from:
- translator_id
- readiness_snapshot (sorted JSON)
- provenance_snapshot (sorted JSON)
- authorization_snapshot (sorted JSON)
- freeze_manifest_snapshot (sorted JSON)

Excludes timestamps and UUIDs to ensure determinism.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/cam/translators/governance-dossier/build` | Build dossier |
| GET | `/api/cam/translators/governance-dossiers` | List all dossiers |
| GET | `/api/cam/translators/governance-dossiers/policy` | Get policy info |
| GET | `/api/cam/translators/governance-dossiers/{id}` | Get by ID |
| GET | `/api/cam/translators/governance-dossiers/by-translator/{id}` | Get by translator |

## 7I Invariants

All model-enforced via Pydantic validators:

1. **execution_authorized = false** — dossier never authorizes execution
2. **machine_output_allowed = false** — dossier never permits machine output
3. **immutable = true** — dossier is read-only after creation

## Required Escalation Layers

All dossiers declare these 5 canonical escalation layers:

1. `governance_review`
2. `translator_execution_architecture_review`
3. `human_approval`
4. `security_review`
5. `artifact_generation_policy_review`

## Governance Constraints

Dossiers include these 8 canonical constraints:

1. No DXF generation
2. No SVG generation
3. No G-code generation
4. No serializer invocation
5. No runtime execution
6. No plugin loading
7. No machine output
8. No subprocess execution

## Builder Requirements

`build_governance_escalation_dossier()` requires all four inputs:
- `readiness_evaluation` (from 7G)
- `provenance` (from 7F)
- `authorization_evaluation` (from 7E)
- `freeze_manifest` (from 7H)

Raises `DossierBuildError` if any input is missing.

## Integration with 7H

The quarantine model includes an optional `governance_dossier_summary` field for forward reference when a dossier exists. This is populated by the router/endpoint layer, not the core module.

## Test Coverage

34 tests covering:
- 7I invariants (6 tests)
- Deterministic hashing (5 tests)
- Builder requirements (7 tests)
- Index operations (3 tests)
- Summary model (2 tests)
- Endpoints (6 tests)
- Safety assertions (3 tests)
- Canonical constraints (2 tests)

## Guardrail

> 7I packages complete governance evidence for review.
> It does NOT create approval authority, execution authority, or mutation authority.

## Chain Summary

```
7E (Authorization) ──┐
7F (Provenance) ─────┼──► 7I (Dossier)
7G (Readiness) ──────┤
7H (Quarantine) ─────┘
```

Each upstream component provides evidence that 7I aggregates into an immutable review package.
