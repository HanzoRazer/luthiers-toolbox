# CAM Dev Order 7K: Governance Review Ledger

**Status**: COMPLETE  
**Date**: 2026-05-15  
**Depends on**: 7J (Review Matrix)

## Purpose

7K creates the immutable governance review trace chain that records deterministic review-readiness evaluations and preserves governance trace ancestry.

**Key distinction**: A governance review ledger entry is an immutable governance trace record, NOT an approval decision.

## Files Created

| File | Purpose |
|------|---------|
| `app/cam/translator_governance_review_ledger.py` | Core ledger model, builder, lineage helpers, in-memory index |
| `app/routers/cam/translator_governance_review_ledger_router.py` | REST endpoints |
| `tests/cam/test_translator_governance_review_ledger.py` | 44 tests |

## Files Modified

| File | Change |
|------|--------|
| `app/router_registry/manifests/cam_manifest.py` | Router registration |

## Architecture

### Ledger Entry Model

```python
class TranslatorGovernanceReviewLedgerEntry(BaseModel):
    ledger_entry_id: str
    review_matrix_id: str
    dossier_id: str
    translator_id: str
    
    # Review state
    review_gate: str
    review_readiness_score: int
    review_state: Literal["review_only", "non_executable", "future_escalation_required"]
    
    # Source evidence hashes
    provenance_hash: str
    readiness_hash: str
    quarantine_hash: str
    authorization_hash: str
    dossier_hash: str
    review_matrix_hash: str
    
    # Lineage
    parent_ledger_hashes: List[str]  # Ancestry chain
    
    # Governance constraints
    governance_constraints: List[str]
    
    # Deterministic trace hash
    review_trace_hash: str
    
    # 7K invariants (model-enforced)
    immutable: bool = True              # Always true
    execution_authorized: bool = False  # Always false
    machine_output_allowed: bool = False  # Always false
    
    # Tracking
    unresolved_hashes: List[str]  # Hashes that couldn't be resolved
```

### Deterministic Review Trace Hash

Computed from:
- review_matrix_hash
- dossier_hash
- provenance_hash
- readiness_hash
- quarantine_hash
- authorization_hash
- governance_constraints (sorted)
- parent_ledger_hashes (sorted)

Excludes: timestamps, UUIDs, transient metadata, RMOS attachment IDs

**Goal**: Same governance review ancestry → same review trace hash

### Lineage Chains

Rules:
- `parent_ledger_hashes` references earlier review traces
- Genesis entry (first for translator) has empty `parent_ledger_hashes = []`
- Auto-detect: finds most recent entry's `review_trace_hash` for same translator
- Override: explicit `parent_ledger_hashes` parameter takes precedence
- Lineage is append-only — no mutation of previous entries

### Builder Pattern

```python
build_governance_review_ledger_entry(
    review_matrix,           # Required
    dossier=None,            # Optional, fallback to index lookup
    provenance=None,         # Optional
    readiness=None,          # Optional
    quarantine=None,         # Optional
    authorization=None,      # Optional
    parent_ledger_hashes=None,  # Optional, auto-detect if None
    persist_to_rmos=False,
)
```

Hash resolution:
- Uses input objects' existing hash fields when provided
- Falls back to index lookup when objects not provided
- Uses `"unresolved"` placeholder for missing hashes (tracked in `unresolved_hashes`)
- Never silently fabricates evidence

### Duplicate Protection

Registering a duplicate `ledger_entry_id` raises `DuplicateLedgerEntryError`. Ledger entries are append-only and immutable.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/cam/translators/governance-review-ledger/build` | Build ledger entry (201 Created) |
| GET | `/api/cam/translators/governance-review-ledger` | List all entries |
| GET | `/api/cam/translators/governance-review-ledger/policy` | Get policy config |
| GET | `/api/cam/translators/governance-review-ledger/{id}` | Get by ID |
| GET | `/api/cam/translators/governance-review-ledger/by-translator/{id}` | Get by translator |
| GET | `/api/cam/translators/governance-review-ledger/{id}/lineage` | Get ancestry chain |

Duplicate ID returns 409 Conflict.

## 7K Invariants

All model-enforced via Pydantic validators:

1. **immutable = true** — ledger entries are immutable
2. **execution_authorized = false** — never authorizes execution
3. **machine_output_allowed = false** — never permits machine output

## In-Memory Index

```python
REVIEW_LEDGER_INDEX: Dict[str, TranslatorGovernanceReviewLedgerEntry] = {}
```

Functions:
- `register_review_ledger_entry(entry)` — raises on duplicate
- `get_review_ledger_entry(ledger_entry_id)`
- `list_review_ledger_entries()`
- `list_review_ledger_entries_for_translator(translator_id)`
- `get_latest_ledger_entry_for_translator(translator_id)`
- `clear_review_ledger_index()`

### Lineage Helper

```python
get_lineage_chain(ledger_entry_id, max_depth=10) -> List[Entry]
```

Walks `parent_ledger_hashes` to build ancestry chain from newest to oldest.

## Optional RMOS Persistence

Enabled via `persist_to_rmos=True` parameter.

Artifact kind: `translator_governance_review_ledger_json`

Persists metadata only — no executable payloads.

## Test Coverage

44 tests covering:
- 7K invariants (6 tests)
- Deterministic hashing (5 tests)
- Builder (5 tests)
- Parent detection & lineage (4 tests)
- Duplicate protection (1 test)
- Index operations (5 tests)
- Summary model (2 tests)
- Endpoints (8 tests)
- Safety assertions (3 tests)
- RMOS persistence (2 tests)
- Hash extraction (3 tests)

## Guardrail

> 7K records governance review trace ancestry. It must not mutate prior entries, approval state, or execution authority.

## Chain Summary

```
7E (Authorization) ──┐
7F (Provenance) ─────┼──► 7I (Dossier) ──► 7J (Review Matrix) ──► 7K (Ledger)
7G (Readiness) ──────┤
7H (Quarantine) ─────┘
```

7K is the final immutable governance trace layer. It records review evaluations in an append-only lineage chain, enabling:
- Governance audit replay
- Review ancestry tracking
- Escalation evidence preservation

Without enabling:
- Approval authority
- Execution authorization
- Runtime capability
- Serializer invocation
