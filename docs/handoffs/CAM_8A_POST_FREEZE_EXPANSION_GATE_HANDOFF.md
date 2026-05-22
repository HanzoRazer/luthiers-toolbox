# CAM 8A: Post-Freeze Expansion Gate Handoff

## Status

```text
IMPLEMENTED
```

## Summary

8A implements the post-freeze expansion gate system, enabling controlled capability proposals after the 7Z governance baseline freeze. Proposals declare intent for human review but do not authorize implementation, execution, or machine output.

## Core Principle

```text
Post-freeze work must extend capability through declared gates,
not bypass the frozen governance baseline.
```

## 8A Invariants (Model-Enforced)

All models enforce these invariants via Pydantic validators:

| Field | Value | Rationale |
|-------|-------|-----------|
| `implementation_authorized` | `False` | 8A does not authorize implementation |
| `execution_authorized` | `False` | 8A does not authorize execution |
| `machine_output_allowed` | `False` | 8A does not allow machine output |

Attempting to set any of these to `True` raises `ValueError`.

## Files Created

### Models

| File | Purpose |
|------|---------|
| `services/api/app/cam/post_freeze_expansion_gate.py` | `PostFreezeExpansionProposal` model with 8A invariants |
| `services/api/app/cam/post_freeze_readiness.py` | `PostFreezeExpansionReadiness` model and gate classification |
| `services/api/app/cam/post_freeze_registry.py` | Registry, CI summary, and query helpers |

### Router

| File | Prefix |
|------|--------|
| `services/api/app/routers/cam/post_freeze_expansion_router.py` | `/api/cam/post-freeze` |

### Tests

| File | Coverage |
|------|----------|
| `services/api/tests/cam/test_post_freeze_expansion_gate.py` | ~70 tests covering models, gates, registry, CI, router |

## Key Models

### PostFreezeExpansionProposal

```python
class PostFreezeExpansionProposal(BaseModel):
    proposal_id: str
    title: str
    target_layer: TargetLayer  # manufacturing_cognition, geometry_authority, etc.
    depends_on_freeze_id: Optional[str]  # Reference to 7Z freeze
    proposed_capability: str
    expected_artifacts: List[str]
    governance_risks: List[str]
    required_reviews: List[str]

    # Explicit mutation flags (RED gate detection)
    ontology_mutation_requested: bool = False
    baseline_rewrite_requested: bool = False

    # 8A invariants (always False)
    implementation_authorized: bool = False
    execution_authorized: bool = False
    machine_output_allowed: bool = False

    proposal_state: Literal["draft", "submitted_for_review"] = "draft"
    deterministic_proposal_hash: str
```

### PostFreezeExpansionReadiness

```python
class PostFreezeExpansionReadiness(BaseModel):
    readiness_id: str
    proposal_id: str
    freeze_compatible: bool
    freeze_exists: bool
    freeze_status: Optional[str]
    required_reviews_declared: bool
    gate: Literal["green", "yellow", "red"]
    blocking_issues: List[str]
    warnings: List[str]

    # 8A invariants (always False)
    implementation_authorized: bool = False
    execution_authorized: bool = False
    machine_output_allowed: bool = False

    deterministic_readiness_hash: str
```

## Gate Rules

### RED (Blocked)

| Condition | Meaning |
|-----------|---------|
| `baseline_rewrite_requested = True` | Requires explicit governance approval |
| `execution_authorized = True` | 8A does not authorize execution |
| `machine_output_allowed = True` | 8A does not allow machine output |
| `implementation_authorized = True` | 8A does not authorize implementation |
| `ontology_mutation_requested = True` | Requires explicit future governance order |

### YELLOW (Needs Attention)

| Condition | Meaning |
|-----------|---------|
| `depends_on_freeze_id = None` | Missing freeze reference — incomplete governance linkage |
| Freeze ID provided but not found | Stronger warning — verify freeze ID |
| `required_reviews` empty | Reviews not declared |
| `target_layer` unclear | Layer validation issue |
| `governance_risks` empty | Risk list may be incomplete |

### GREEN (Ready for Review)

All conditions met:
- Freeze compatible
- Required reviews declared
- No execution authority
- No machine output authority
- No baseline rewrite
- No ontology mutation

## API Endpoints

### Proposals

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/cam/post-freeze/proposals` | Create proposal |
| GET | `/api/cam/post-freeze/proposals` | List proposals (filter by `target_layer`) |
| GET | `/api/cam/post-freeze/proposals/latest` | Get latest proposal |
| GET | `/api/cam/post-freeze/proposals/{id}` | Get proposal by ID |

### Readiness

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/cam/post-freeze/readiness/{proposal_id}` | Evaluate readiness |
| GET | `/api/cam/post-freeze/readiness/latest` | Get latest evaluation |
| GET | `/api/cam/post-freeze/readiness` | List all evaluations |
| GET | `/api/cam/post-freeze/readiness/proposal/{id}` | List evaluations for proposal |

### CI & Status

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/cam/post-freeze/ci` | CI summary (gate distribution, status) |
| GET | `/api/cam/post-freeze/status` | Aggregated status summary |

## CI Summary Shape

```python
{
    "total_proposals": int,
    "total_readiness_evaluations": int,
    "green_count": int,
    "yellow_count": int,
    "red_count": int,
    "missing_freeze_ref_count": int,
    "baseline_rewrite_request_count": int,
    "ontology_mutation_request_count": int,
    "execution_request_count": int,
    "machine_output_request_count": int,
    "status": "pass" | "warn" | "fail",
    "blocking_issues": List[str],
    "warnings": List[str],
}
```

## 7Z Integration

8A consumes 7Z shallowly:

- When `depends_on_freeze_id` is provided, attempts to resolve in 7Z registry
- If found: reads freeze status and blocking issues
- If not found: YELLOW (not RED) — incomplete governance linkage
- Does not re-evaluate or mutate 7Z state

## Design Decisions

1. **Explicit mutation flags**: `ontology_mutation_requested` and `baseline_rewrite_requested` are explicit boolean fields, not inferred from free-text `governance_risks`. Free-text can produce warnings but not RED gates.

2. **No approval workflow**: Proposals remain static. Optional `proposal_state` field supports `draft` and `submitted_for_review`, but no `approved` or `implemented` states. `implementation_authorized` remains `False`.

3. **Standalone design**: 8A depends only on stable/registered prior layers (7Z). No cross-references to untracked runtime provenance modules.

4. **Soft freeze validation**: Missing or not-found freeze references produce YELLOW warnings, not RED blocks. Missing freeze is incomplete governance linkage, not an execution violation.

## Test Coverage

- Model invariants (implementation/execution/machine_output always False)
- Gate classification (all RED, YELLOW, GREEN conditions)
- Freeze linkage (None, not found, found)
- Registry operations (CRUD, ordering, filtering)
- CI summary (pass/warn/fail conditions)
- Router endpoints (all CRUD operations)
- Integration workflows (clean and blocked proposals)

## Guardrail

```text
8A governs post-freeze expansion proposals.
It does not authorize implementation, mutate the frozen baseline,
invoke serializers, execute runtimes, or generate machine output.
```

## Next Steps

Future dev orders may:
- Add approval workflows (requires new governance order)
- Implement cross-layer dependency tracking
- Add proposal versioning
- Enable controlled ontology expansion paths

All future work must extend through declared gates, not bypass the frozen governance baseline.
