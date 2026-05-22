# CAM Dev Order 7X — Federated Manufacturing Semantics Handoff

**Date:** 2026-05-21  
**Status:** Complete  
**Branch:** fix/wood-shrinkage-data-integrity

---

## Summary

7X establishes **federated manufacturing semantics** — a cross-domain semantic coordination layer that allows CAM, Geometry, Morphology, Acoustics, Runtime Governance, and Review Intelligence to reference one another without collapsing domain authority boundaries.

This is the first federation layer in the repository. It coordinates semantic references, not ontologies. It does not centralize authority, merge schemas, or authorize execution.

---

## Core Principles

### Domains May Reference, Not Absorb

```
Domains may reference one another.
Domains may not absorb one another's authority.
```

### Federation Coordinates, Does Not Centralize

```
Federation coordinates semantics.
Federation does not centralize ontology ownership.
```

---

## What 7X Provides

| Capability | Description |
|------------|-------------|
| Federated Semantic References | Cross-domain links with relationship types |
| Cross-Domain Continuity Records | Continuity linkage across domain boundaries |
| Federated Review Packages | Immutable cross-domain cognition bundles |
| Authority Override Detection | Detects boundary violations at registration |
| Fragmented Federation Detection | Detects broken continuity chains |
| CI Summary Endpoint | Aggregated federation health status |
| Registry Layer | In-memory indexes with validation |

---

## What 7X Does NOT Provide

| Anti-pattern | Reason |
|--------------|--------|
| Ontology auto-merging | Domains own their schemas |
| Automatic semantic reconciliation | Federation is manual/explicit |
| Autonomous promotion | No machine authority |
| Runtime execution | Observational only |
| Distributed state mutation | No cross-domain writes |
| Geometry mutation | IBG/BOE owns geometry authority |
| Schema centralization | Each domain keeps its own schema |

---

## Domain Authority Map

| Domain | Owns |
|--------|------|
| IBG/BOE | Canonical geometry authority |
| CAM Governance | Manufacturing cognition |
| Acoustics | Observational acoustic semantics |
| Runtime Governance | Runtime lifecycle semantics |
| Translator Governance | Serialization/export governance |
| Review Governance | Review continuity semantics |
| Topology | Experimental topology variants |
| Morphology | Body morphology semantics |

7X connects these domains. It does not collapse them.

---

## New Files

### Core Models

| File | Purpose |
|------|---------|
| `app/cam/federated_semantic_reference.py` | `FederatedSemanticReference` model, domain types, relationship types |
| `app/cam/cross_domain_continuity.py` | `CrossDomainContinuityRecord` model |
| `app/cam/federated_review_package.py` | `FederatedReviewPackage` model |
| `app/cam/federated_semantic_registry.py` | In-memory indexes, validation, CI summary |
| `app/routers/cam/federated_semantics_router.py` | REST endpoints |

### Tests

| File | Test Count |
|------|------------|
| `tests/cam/test_federated_semantics.py` | 90+ tests |

---

## Modified Files

| File | Change |
|------|--------|
| `app/cam/manufacturing_replay_session.py` | Added `federation_ref_ids: List[str]` field (7X linkage) |
| `app/cam/replay_safe_review_package.py` | Added `cross_domain_continuity_refs: List[str]` field (7X linkage) |
| `app/router_registry/manifests/cam_manifest.py` | Registered federated semantics router |

---

## Taxonomy

### Federated Domain Types

```python
FederatedDomainType = Literal[
    "cam",
    "geometry",
    "morphology",
    "topology",
    "acoustics",
    "runtime_governance",
    "translator_governance",
    "review_governance",
]
```

### Semantic Relationship Types

```python
SemanticRelationshipType = Literal[
    "references",       # A references B
    "derives_from",     # A derives from B
    "observes",         # A observes B
    "validates",        # A validates B
    "annotates",        # A annotates B
    "packages",         # A packages B
    "replays",          # A replays B
    "shares_provenance_with",   # A shares provenance with B
    "shares_continuity_with",   # A shares continuity with B
]
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/cam/federation/references` | POST | Create federation reference |
| `/api/cam/federation/references/{ref_id}` | GET | Get reference by ID |
| `/api/cam/federation/references` | GET | List all references (summaries) |
| `/api/cam/federation/continuity` | POST | Create continuity record |
| `/api/cam/federation/continuity/{record_id}` | GET | Get record by ID |
| `/api/cam/federation/continuity` | GET | List all records (summaries) |
| `/api/cam/federation/package` | POST | Create federated package |
| `/api/cam/federation/package/{package_id}` | GET | Get package by ID |
| `/api/cam/federation/packages` | GET | List all packages (summaries) |
| `/api/cam/federation/ci` | GET | CI summary (pass/warn/fail) |

---

## CI Summary Status Logic

| Status | Conditions |
|--------|------------|
| **fail** | Authority override, ontology mutation, execution/machine output flags, invalid continuity, blocking issues |
| **warn** | Fragmented federation, warnings present |
| **pass** | All registered federation state is clean |

---

## Authority Override Detection

Authority override is detected when:

- `preserves_authority_boundary == False`
- `authority_override_attempted == True`
- `ontology_mutation_attempted == True`
- `execution_authorized == True`
- `machine_output_allowed == True`
- Same domain claiming cross-domain semantics inappropriately

Registration rejects hard invariant violations by default.

---

## Hash Determinism

All federation models use deterministic hashing:

- Hash semantic fields only
- Exclude generated IDs, timestamps, hash field itself
- Same semantic state → same hash
- Lists are sorted before hashing

This supports:
- Change detection
- Continuity verification
- Federation integrity checks

---

## Integration with 7W

7X adds optional federation linkage to 7W artifacts:

```python
# ManufacturingReplaySession (7W)
federation_ref_ids: List[str] = []  # 7X linkage

# ReplaySafeReviewPackage (7W)
cross_domain_continuity_refs: List[str] = []  # 7X linkage
```

Replay remains observational. Federation extends, does not replace.

---

## Recommended Ref Format

7X accepts opaque strings for reference IDs. Recommended format:

```
<domain>:<local_id>
```

Examples:
- `cam:strategy-abc123`
- `geometry:body-ref-456`
- `acoustics:observation-789`

7X does not enforce this format.

---

## Future Evolution Paths

7X establishes the foundation for:

1. **Cross-domain replay** — Replay sessions spanning CAM, geometry, and acoustics
2. **Federated provenance chains** — Provenance tracking across domain boundaries
3. **Semantic drift detection** — CI-level detection of diverging domain semantics
4. **Multi-domain review packages** — Review cognition bundles spanning the platform

---

## Guardrails

```
7X coordinates cross-domain semantic continuity.
It does not centralize ontology authority,
mutate schemas, invoke runtimes,
authorize execution, or generate machine output.
```

All 7X models enforce:
- `execution_authorized: False`
- `machine_output_allowed: False`

Federation packages enforce:
- `immutable: True`

---

## Test Coverage

90+ tests covering:
- Model invariants
- Hash determinism
- Authority override detection
- Fragmented federation detection
- Registry operations
- CI summary logic
- Router endpoints
- Integration with 7W

---

## Verification

```bash
pytest services/api/tests/cam/test_federated_semantics.py -v
```

All tests must pass before merge.

---

## Next Steps

1. Integrate federation refs into existing CAM workflows
2. Add federation linkage to IBG/BOE geometry pipelines
3. Add federation linkage to acoustics observation workflows
4. Build cross-domain replay UI in client
5. Extend CI summary to governance dashboard
