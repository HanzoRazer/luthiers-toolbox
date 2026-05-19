# CAM Dev Order 7M — Canonical Ontology Reconciliation Layer

**Date**: 2026-05-16  
**Status**: IMPLEMENTED  
**Dev Order**: 7M  
**Governance Tier**: Tier 1 — Structural / Ontology Governance

---

## Summary

7M establishes the first operational Canonical Ontology Reconciliation Layer for the repository. This creates deterministic ontology synchronization infrastructure across CAM, MRP, governance, morphology, runtime contracts, and future domains.

---

## Strategic Significance

7M is the first implementation of **singular ontology authority** inside the repository.

This dev order operationalizes:
- Canonical Ontology Authority
- Governance-owned vocabulary
- Semantic reconciliation governance

After 7M, **ontology coherence itself becomes observable infrastructure**.

---

## Architecture

### Core Principle

7M makes ontology drift **visible**. It does not automatically **repair** ontology drift.

### What 7M Creates

1. Canonical ontology vocabulary registry
2. Ontology ownership registry
3. Semantic conflict detection
4. Lifecycle terminology normalization
5. Cross-domain vocabulary reconciliation
6. Ontology drift reporting
7. CI-visible semantic integrity reporting

### What 7M Does NOT Do

- Mutate existing domain behavior
- Alter runtime logic
- Change translator execution state
- Authorize machine output
- Introduce adaptive semantics
- Automatically repair conflicts

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Vocabulary seeding | Hard-coded at module load | Governance authority, not runtime config |
| Conflict detection | Closed-world (registered only) | Codebase scanning deferred to future order |
| Lifecycle drift | Via lifecycle_semantics field | Simple, extensible |
| Reconcile endpoint | Passive, read-only | No automatic mutation |
| Alignment score | Severity-weighted penalties | Makes critical conflicts visible |
| Domain indexes | Both directions | Efficient lookups |

---

## Models

### CanonicalOntologyTerm

```python
class CanonicalOntologyTerm(BaseModel):
    term: str
    canonical_definition: str
    owning_domain: str
    owning_governance_tier: int  # 1=Structural, 2=Domain, 3=Operational
    canonical_contracts: list[str]
    prohibited_reinterpretations: list[str]
    lifecycle_semantics: Optional[list[str]]
    aliases: list[str]
    
    # 7M invariants (always enforced)
    immutable: bool = True
    ontology_authoritative: bool = True
```

### OntologyConflict

```python
class OntologyConflict(BaseModel):
    conflict_id: str
    term: str
    conflicting_sources: list[str]
    canonical_source: str
    conflict_type: Literal[
        "duplicate_definition",
        "lifecycle_drift",
        "authority_collision",
        "runtime_reinterpretation",
        "semantic_alias_collision",
    ]
    severity: Literal["low", "medium", "high", "critical"]
    reconciliation_required: bool = True
```

### OntologyReconciliationReport

```python
class OntologyReconciliationReport(BaseModel):
    report_id: str
    terms_evaluated: int
    conflicts_detected: int
    canonical_alignment_score: float  # 0.0 to 1.0
    ontology_integrity_valid: bool
    deterministic_report_hash: str
    
    # 7M invariants
    execution_authorized: bool = False
    machine_output_allowed: bool = False
```

---

## Alignment Score

Severity-weighted penalty model:

| Severity | Penalty |
|----------|---------|
| low | 2 |
| medium | 5 |
| high | 15 |
| critical | 30 |

Score calculation:
```
alignment_score = max(0, 100 - total_penalty) / 100
```

---

## Initial Canonical Vocabulary

14 terms seeded at module load:

| Term | Domain | Tier |
|------|--------|------|
| translator | CAM | 2 |
| runtime | Runtime Governance | 1 |
| intent | CAM | 2 |
| provenance | Governance | 1 |
| morphology | MRP | 2 |
| validation | Governance | 1 |
| execution | Runtime Governance | 1 |
| readiness | CAM Governance | 2 |
| quarantine | CAM Governance | 2 |
| topology | MRP | 2 |
| serialization | Translator Governance | 2 |
| artifact | CAM Governance | 2 |
| geometry_authority | Geometry | 2 |
| runtime_authority | Runtime Governance | 1 |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/cam/ontology/policy` | Get 7M policy |
| GET | `/api/cam/ontology/terms` | List canonical terms |
| GET | `/api/cam/ontology/terms/{term}` | Get canonical term |
| GET | `/api/cam/ontology/domains` | List domain ownership |
| GET | `/api/cam/ontology/lifecycles` | Get lifecycle vocabularies |
| GET | `/api/cam/ontology/conflicts` | List detected conflicts |
| POST | `/api/cam/ontology/reconcile` | Generate reconciliation report |
| GET | `/api/cam/ontology/report/latest` | Get latest report |
| GET | `/api/cam/ontology/ci` | Get CI summary |

---

## CI Integration

The `/api/cam/ontology/ci` endpoint returns:

```json
{
  "status": "pass|warn|fail",
  "alignment_score": 0.95,
  "conflicts_detected": 2,
  "critical_conflicts": 0,
  "ontology_integrity_valid": true,
  "summary_message": "..."
}
```

Status determination:
- **pass**: No conflicts detected
- **warn**: Non-critical conflicts only
- **fail**: Critical conflicts present

---

## Files

| File | Purpose |
|------|---------|
| `canonical_ontology_registry.py` | Term registration, aliases, indexes |
| `ontology_authority_map.py` | Domain ownership, authority queries |
| `ontology_reconciliation_engine.py` | Conflict detection, report generation |
| `ontology_drift_report.py` | Drift classification, CI formatting |
| `ontology_reconciliation_router.py` | REST endpoints |
| `test_ontology_reconciliation.py` | Test suite |

---

## 7M Invariants

Always enforced at model level:

```python
immutable = True
ontology_authoritative = True
execution_authorized = False
machine_output_allowed = False
```

---

## Guardrail

> 7M makes ontology drift visible. It does not automatically repair ontology drift.

---

## Conflict Types Detected

1. **duplicate_definition**: Same term defined differently
2. **lifecycle_drift**: Incompatible lifecycle vocabularies
3. **authority_collision**: Multiple domains claiming ownership
4. **runtime_reinterpretation**: Prohibited reinterpretations registered
5. **semantic_alias_collision**: Aliases creating ambiguity

---

## Testing

Run tests:

```bash
cd services/api
python -m pytest tests/cam/test_ontology_reconciliation.py -v
```

---

## Future Work (Out of Scope for 7M)

- Codebase scanning (open-world detection)
- Automatic conflict resolution
- AI-powered semantic analysis
- Runtime ontology mutation
- Unified governance registry

These require separate dev orders.
