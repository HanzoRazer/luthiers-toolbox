# CAM Dev Order 7L — Governance Continuity Graph

**Date**: 2026-05-15  
**Status**: IMPLEMENTED  
**Dev Order**: 7L  

---

## Summary

7L establishes the final immutable governance continuity layer that connects governance review ledger entries (7K) into deterministic replayable continuity graphs.

This enables:
- Deterministic governance replay
- Escalation continuity tracking
- Immutable governance ancestry traversal
- Review evolution analysis
- Replay integrity verification

---

## Architecture

### Core Principle

A Governance Continuity Graph is an **immutable governance replay structure**, NOT an execution workflow engine.

### Scope

- **Per-translator only**: One continuity graph per `translator_id`
- Cross-translator governance graphs are out of scope for 7L

### Data Flow

```
translator_id
  → review ledger entries (7K)
  → ordered review trace chain
  → continuity graph (7L)
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Graph scope | Per-translator | 7K lineage is already translator-scoped |
| Builder input | Objects directly | Pure function, index lookups at router layer |
| Build mode | Rebuild from scratch | Stateless, deterministic, no mutation |
| Graph ID | Deterministic derivation | Enables idempotent rebuilds |
| Hash chains | Preserve exact order | Positional correlation for replay |
| Integrity | Comprehensive | Structure + invariant violations |
| Replay output | Structured object | GovernanceReplayResult with integrity |

---

## Models

### TranslatorGovernanceContinuityGraph

```python
class TranslatorGovernanceContinuityGraph(BaseModel):
    continuity_graph_id: str          # Deterministic from translator + hashes
    translator_id: str
    
    # Trace hashes
    root_review_trace_hash: str       # Genesis entry
    current_review_trace_hash: str    # Most recent entry
    
    # Positionally correlated hash chains
    review_trace_chain: List[str]
    dossier_hash_chain: List[str]
    provenance_hash_chain: List[str]
    readiness_hash_chain: List[str]
    quarantine_hash_chain: List[str]
    
    # Integrity
    continuity_integrity_valid: bool
    integrity_violations: List[str]
    
    # Deterministic hash
    deterministic_continuity_hash: str
    
    # 7L invariants (always enforced)
    replayable: bool = True
    immutable: bool = True
    execution_authorized: bool = False
    machine_output_allowed: bool = False
```

### GovernanceReplayResult

```python
class GovernanceReplayResult(BaseModel):
    translator_id: str
    replay_chain: List[TranslatorGovernanceReviewLedgerEntry]
    replay_trace_hash: str
    continuity_hash: str
    replay_integrity_valid: bool
    replay_length: int
    root_review_trace_hash: str
    current_review_trace_hash: str
    replay_state: Literal["review_only", "non_executable", "future_escalation_required"]
    
    # 7L invariants
    execution_authorized: bool = False
    machine_output_allowed: bool = False
```

---

## Integrity Validation

Comprehensive integrity checking. `continuity_integrity_valid = False` for:

- Broken parent linkage
- Orphaned review traces
- Missing parent hashes
- Non-deterministic ordering
- Replay chain discontinuity
- Duplicate review traces in chain
- `execution_authorized == true` anywhere
- `machine_output_allowed == true` anywhere
- `immutable == false` anywhere
- Replay hash mismatch
- Continuity hash mismatch

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/cam/translators/governance-continuity/policy` | Get 7L policy |
| POST | `/api/cam/translators/governance-continuity/build` | Build graph for translator |
| GET | `/api/cam/translators/governance-continuity` | List all graphs |
| GET | `/api/cam/translators/governance-continuity/{id}` | Get graph by ID |
| GET | `/api/cam/translators/governance-continuity/by-translator/{id}` | List graphs for translator |
| GET | `/api/cam/translators/governance-continuity/{id}/replay` | Replay governance trace |

---

## Files

| File | Purpose |
|------|---------|
| `app/cam/translator_governance_continuity_graph.py` | Models, builder, helpers, index |
| `app/routers/cam/translator_governance_continuity_router.py` | REST endpoints |
| `tests/cam/test_translator_governance_continuity_graph.py` | Test suite |

---

## 7L Invariants

Always enforced at model level:

```python
replayable = True
immutable = True
execution_authorized = False
machine_output_allowed = False
```

---

## Guardrail

> 7L continuity graph remains immutable replay infrastructure only.
> No mutation, approval, execution, serializer invocation, or machine-output semantics.

---

## What Replay Means

Replay is **deterministic ancestry traversal only**.

Replay is NOT:
- Runtime replay
- Execution replay
- Serializer replay

---

## Integration with 7K

7L builds on 7K ledger entries:

```
7K: TranslatorGovernanceReviewLedgerEntry
  → individual immutable review traces
  → parent_ledger_hashes for lineage

7L: TranslatorGovernanceContinuityGraph
  → aggregates ledger entries into continuity structure
  → provides replay traversal
  → validates comprehensive integrity
```

---

## Testing

Run tests:

```bash
cd services/api
python -m pytest tests/cam/test_translator_governance_continuity_graph.py -v
```

---

## Future Work (Out of Scope)

The following are explicitly out of scope for 7L:

- Cross-translator governance graphs
- Execution workflows
- Runtime translators
- Serializer invocation
- DXF/G-code generation
- Machine control
- Automated escalation
- Mutable governance graphs
- Orchestration runtimes

These require explicit governance escalation approval beyond 7L.
