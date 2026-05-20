# CAM Dev Order 7N — Runtime Semantic Consumption Discipline

**Date**: 2026-05-16  
**Status**: IMPLEMENTED  
**Dev Order**: 7N  
**Governance Tier**: Tier 1 — Structural / Runtime Governance

---

## Summary

7N establishes the Runtime Semantic Consumption Discipline for the repository. This enforces that runtime systems may consume canonical ontology (from 7M) but may NOT create, mutate, reinterpret, or fork it.

---

## Strategic Significance

7N is the first implementation of **runtime consumption boundary enforcement** inside the repository.

This dev order operationalizes:
- Runtime consumption declaration
- Ontology consumer registration
- Consumption validation against 7M registry
- Prohibited authority claim detection
- Reinterpretation risk detection

After 7N, **runtime semantic consumption itself becomes observable infrastructure**.

---

## Architecture

### Core Principle

7N verifies that runtimes consume ontology without owning ontology. It does not permit runtime execution, ontology mutation, lifecycle definition, or semantic reinterpretation.

### What 7N Creates

1. Runtime semantic consumer registry
2. Consumer registration with invariants
3. Consumption validation against 7M
4. Prohibited authority claim detection
5. Reinterpretation risk detection
6. Consumption alignment scoring
7. CI-visible discipline reporting

### What 7N Does NOT Do

- Execute runtime systems
- Mutate canonical ontology
- Define lifecycle states
- Reinterpret term semantics
- Fork vocabulary
- Generate machine output
- Auto-repair violations

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Consumer seeding | Hard-coded at module load | Governance authority, not runtime config |
| Ontology integration | Import 7M registry directly | Single source of truth |
| Validation behavior | Report-based, not silent failure | Makes violations visible |
| Event logging | Inside report only | No separate ledger yet |
| Hash exclusions | Timestamps, UUIDs, report_id | Consumer_id is semantic |
| Prohibited operations | Literal type (7 operations) | Type safety |

---

## Models

### RuntimeSemanticConsumer

```python
class RuntimeSemanticConsumer(BaseModel):
    consumer_id: str
    consumer_name: str
    consumer_domain: str
    consumed_terms: list[str]
    consumption_purpose: str
    registered_at: datetime
    
    # 7N invariants (always false)
    declared_semantic_authority: bool = False
    may_register_terms: bool = False
    may_mutate_ontology: bool = False
    may_define_lifecycle: bool = False
    may_execute_runtime: bool = False
    may_generate_machine_output: bool = False
```

### ConsumptionDisciplineReport

```python
class ConsumptionDisciplineReport(BaseModel):
    report_id: str
    generated_at: datetime
    consumer_id: str
    
    consumed_terms: list[str]
    missing_terms: list[str]
    term_mismatches: list[TermConsumptionMismatch]
    prohibited_authority_claims: list[ProhibitedAuthorityClaim]
    runtime_reinterpretation_risks: list[RuntimeReinterpretationRisk]
    
    consumption_alignment_score: float  # 0.0 to 1.0
    discipline_valid: bool
    deterministic_report_hash: str
    
    # 7N invariants
    execution_authorized: bool = False
    machine_output_allowed: bool = False
```

### ProhibitedRuntimeSemanticOperation

```python
ProhibitedRuntimeSemanticOperation = Literal[
    "register_term",
    "mutate_ontology",
    "define_lifecycle",
    "reinterpret_term",
    "fork_vocabulary",
    "execute_runtime",
    "generate_machine_output",
]
```

---

## Alignment Score

Severity-weighted penalty model (aligned with 7M):

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

## Initial Seeded Consumers

5 consumers seeded at module load:

| Consumer ID | Domain | Consumed Terms |
|-------------|--------|----------------|
| cam_runtime | CAM | translator, intent, artifact, readiness, quarantine |
| translator_runtime | Translator Governance | translator, serialization, provenance, validation |
| morphology_runtime | MRP | morphology, topology, geometry_authority |
| execution_scheduler | Runtime Governance | runtime, execution, runtime_authority |
| validation_runtime | Governance | validation, provenance |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/cam/consumption/policy` | Get 7N policy |
| GET | `/api/cam/consumption/consumers` | List consumers |
| GET | `/api/cam/consumption/consumers/{id}` | Get consumer |
| GET | `/api/cam/consumption/consumers/domains` | List domains |
| GET | `/api/cam/consumption/consumers/domain/{d}` | List by domain |
| POST | `/api/cam/consumption/validate` | Validate consumer |
| POST | `/api/cam/consumption/validate/all` | Validate all |
| GET | `/api/cam/consumption/reports` | List reports |
| GET | `/api/cam/consumption/reports/latest` | Latest report |
| GET | `/api/cam/consumption/ci` | CI summary |

---

## CI Integration

The `/api/cam/consumption/ci` endpoint returns:

```json
{
  "status": "pass|warn|fail",
  "consumers_evaluated": 5,
  "consumers_valid": 5,
  "consumers_invalid": 0,
  "total_missing_terms": 0,
  "total_prohibited_claims": 0,
  "total_reinterpretation_risks": 0,
  "average_alignment_score": 1.0,
  "summary_message": "..."
}
```

Status determination:
- **pass**: All consumers valid
- **warn**: No violations but risks present
- **fail**: Any violations (invalid consumers)

---

## Files

| File | Purpose |
|------|---------|
| `runtime_semantic_consumption.py` | Consumer models, registry, validation |
| `runtime_consumption_policy.py` | Policy, scoring, report generation |
| `runtime_semantic_consumption_router.py` | REST endpoints |
| `test_runtime_semantic_consumption.py` | Test suite |

---

## 7N Invariants

### Global Invariants

```python
immutable = True
ontology_authoritative = True
execution_authorized = False
machine_output_allowed = False
```

### Consumer Invariants

```python
declared_semantic_authority = False
may_register_terms = False
may_mutate_ontology = False
may_define_lifecycle = False
may_execute_runtime = False
may_generate_machine_output = False
```

---

## Guardrail

> 7N verifies that runtimes consume ontology without owning ontology. It does not permit runtime execution, ontology mutation, lifecycle definition, or semantic reinterpretation.

---

## Key Boundary

> 7N is semantic consumption validation, not runtime activation.

---

## Validation Behavior

| Condition | Result |
|-----------|--------|
| Term missing from 7M registry | Report invalid, add to missing_terms |
| Consumer not registered | Endpoint returns 404 |
| Prohibited operation claim | Report invalid, add to prohibited_authority_claims |
| Mutation/fork/reinterpretation | Report invalid, add to runtime_reinterpretation_risks |

7N does NOT:
- Auto-repair violations
- Register missing terms from runtime
- Silently ignore failures

---

## Testing

Run tests:

```bash
cd services/api
python -m pytest tests/cam/test_runtime_semantic_consumption.py -v
```

---

## Governance Chain

7N integrates with the preceding governance dev orders:

```
7A → 7B → 7C → 7D → 7E → 7F → 7G → 7H → 7I → 7J → 7K → 7L → 7M → 7N
```

Key relationships:
- **7M** provides canonical ontology that 7N consumers validate against
- **7L** provides continuity graph patterns used for report tracking
- **7K** provides governance dossier patterns

---

## Future Work (Out of Scope for 7N)

- Runtime consumption ledger (persistent)
- Cross-consumer consumption correlation
- Automatic consumer discovery
- Runtime execution authorization (requires separate order)
- Machine output generation (requires separate order)

These require separate dev orders.
