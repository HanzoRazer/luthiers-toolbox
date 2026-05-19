# Canonical Provenance Model

**Status:** DRAFT FOR GOVERNANCE RATIFICATION  
**Authority:** NOT CANONICAL UNTIL RATIFIED — NOT CI BLOCKING POLICY UNTIL WIRED  
**Date:** 2026-05-18  
**Purpose:** Provenance type decomposition for semantic clarity  
**Constitutional Dependency:** REPOSITORY_CONSTITUTION.md §3

---

## 1. Authority Statement

This document defines canonical provenance types.

```
DRAFT FOR GOVERNANCE RATIFICATION
NOT CANONICAL UNTIL RATIFIED
NOT CI BLOCKING POLICY UNTIL WIRED
```

---

## 2. Provenance Principle

```
Provenance records what happened.
Provenance does not grant authority.
```

### What Provenance Is

Provenance is a record of origin, transformation, and handling.

### What Provenance Is Not

| Not Provenance | Reason |
|----------------|--------|
| Authority | Knowing who did something does not grant authority to do it |
| Validation | Recording something happened does not make it correct |
| Ratification | Recording a decision does not ratify the decision |
| Ownership | Recording who touched data does not assign ownership |

---

## 3. Canonical Provenance Types

| Type | Code | Description |
|------|------|-------------|
| Observational | `PROV_OBSERVATIONAL` | What was observed, by whom, when |
| Derivation | `PROV_DERIVATION` | What was computed from what |
| Runtime | `PROV_RUNTIME` | What execution path was taken |
| Authority | `PROV_AUTHORITY` | Who ratified what decision |
| Transformation | `PROV_TRANSFORMATION` | What changed and how |
| Validation | `PROV_VALIDATION` | What checks passed or failed |
| Replay | `PROV_REPLAY` | What sequence can be replayed |

---

## 4. Type Definitions

### Observational Provenance (`PROV_OBSERVATIONAL`)

Records direct observation of external reality.

| Field | Description |
|-------|-------------|
| observer_id | Who or what made the observation |
| observation_timestamp | When observation occurred |
| observation_method | How observation was made |
| observation_conditions | Environmental context |
| observation_raw | Unprocessed observation data |

**Example:** Acoustic measurement captured by device D at time T under conditions C.

**Existing usage mapped:**
- `MeasurementArchive.observer_id` → `PROV_OBSERVATIONAL`
- `HarvestRecord.extracted_by` → `PROV_OBSERVATIONAL`
- Morphology extraction provenance → `PROV_OBSERVATIONAL`

### Derivation Provenance (`PROV_DERIVATION`)

Records computation from inputs to outputs.

| Field | Description |
|-------|-------------|
| derivation_inputs | What data was used |
| derivation_algorithm | What computation was applied |
| derivation_version | Algorithm version |
| derivation_timestamp | When derivation occurred |
| derivation_reproducible | Whether derivation can be repeated |

**Example:** Body grid classification derived from contour extraction using algorithm V2.

**Existing usage mapped:**
- `RuntimeResultBase.provenance` list entries showing computation chain → `PROV_DERIVATION`
- `morphology_category` classification source → `PROV_DERIVATION`

### Runtime Provenance (`PROV_RUNTIME`)

Records execution path through system.

| Field | Description |
|-------|-------------|
| runtime_entry | Where execution started |
| runtime_path | Stages executed |
| runtime_exits | Where execution ended |
| runtime_duration | How long execution took |
| runtime_resources | What resources were consumed |

**Example:** CAM dispatch through validate → resolve_geometry → plan → preview stages.

**Existing usage mapped:**
- `OperationManifestV1.dispatch_status` → `PROV_RUNTIME`
- `RuntimeResultBase.provenance` list showing stage sequence → `PROV_RUNTIME`
- `result_id` references through dispatch chain → `PROV_RUNTIME`

### Authority Provenance (`PROV_AUTHORITY`)

Records governance decisions and ratifications.

| Field | Description |
|-------|-------------|
| authority_decision | What was decided |
| authority_decider | Who made the decision |
| authority_basis | Constitutional or governance basis |
| authority_timestamp | When decision was made |
| authority_scope | What the decision covers |

**Example:** Vocabulary term "observational_only" ratified by governance layer on date D.

**Existing usage mapped:**
- `CANONICAL_AUTHORITY_MAP.md` operational owner assignments → `PROV_AUTHORITY`
- Ratification records → `PROV_AUTHORITY`
- Freeze declarations → `PROV_AUTHORITY`

### Transformation Provenance (`PROV_TRANSFORMATION`)

Records data modification history.

| Field | Description |
|-------|-------------|
| transform_input | Data before transformation |
| transform_output | Data after transformation |
| transform_operation | What transformation was applied |
| transform_reversible | Whether transformation can be undone |
| transform_timestamp | When transformation occurred |

**Example:** DXF coordinates scaled from pixels to millimeters.

**Existing usage mapped:**
- Blueprint vectorizer scale application → `PROV_TRANSFORMATION`
- Coordinate system conversions → `PROV_TRANSFORMATION`
- Schema migrations → `PROV_TRANSFORMATION`

### Validation Provenance (`PROV_VALIDATION`)

Records verification checks and results.

| Field | Description |
|-------|-------------|
| validation_checks | What was checked |
| validation_results | Pass/fail for each check |
| validation_timestamp | When validation occurred |
| validation_version | Validation rules version |
| validation_scope | What was validated |

**Example:** Scale validation check confirming body dimensions within spec tolerance.

**Existing usage mapped:**
- `RuntimeValidationResult.validation_gate` → `PROV_VALIDATION`
- `validation_passed` flags → `PROV_VALIDATION`
- Governance compliance checks → `PROV_VALIDATION`

### Replay Provenance (`PROV_REPLAY`)

Records sequence sufficient for reproduction.

| Field | Description |
|-------|-------------|
| replay_inputs | Starting state |
| replay_operations | Ordered operation sequence |
| replay_checkpoints | Intermediate states for verification |
| replay_deterministic | Whether replay produces identical output |
| replay_version | Replay format version |

**Example:** Full extraction-to-classification sequence for morphology harvest.

**Existing usage mapped:**
- Morphology harvest `upstream_sources` → `PROV_REPLAY`
- CAM operation manifest with full result chain → `PROV_REPLAY`

---

## 5. Provenance Relationships

### Provenance Does Not Imply

| Provenance Type | Does NOT Imply |
|-----------------|----------------|
| `PROV_OBSERVATIONAL` | Observation is correct |
| `PROV_DERIVATION` | Derivation is valid |
| `PROV_RUNTIME` | Execution was successful |
| `PROV_AUTHORITY` | Decision is still current |
| `PROV_TRANSFORMATION` | Transformation preserved semantics |
| `PROV_VALIDATION` | Validation rules are complete |
| `PROV_REPLAY` | Replay will succeed |

### Provenance Composition

Provenance records may be composed:

| Composition | Description |
|-------------|-------------|
| Sequential | One provenance follows another |
| Parallel | Multiple provenances for same data |
| Hierarchical | Provenance contains sub-provenance |
| Cross-reference | Provenance references other provenance |

---

## 6. Existing Usage Mapping

### CAM Runtime Dispatcher

| Existing Field | Provenance Type | Notes |
|----------------|-----------------|-------|
| `provenance: list[str]` | `PROV_RUNTIME` + `PROV_DERIVATION` | Mixed usage, consider splitting |
| `result_id` | `PROV_RUNTIME` | Execution traceability |
| `dispatch_status` | `PROV_RUNTIME` | Execution outcome |
| `validation_gate` | `PROV_VALIDATION` | Validation outcome |

### Morphology Harvest

| Existing Field | Provenance Type | Notes |
|----------------|-----------------|-------|
| `extracted_by` | `PROV_OBSERVATIONAL` | Extraction agent |
| `upstream_sources` | `PROV_DERIVATION` + `PROV_REPLAY` | Mixed usage |
| `harvest_timestamp` | `PROV_OBSERVATIONAL` | Observation time |
| `classification_source` | `PROV_DERIVATION` | Classification algorithm |

### Measurement Archive

| Existing Field | Provenance Type | Notes |
|----------------|-----------------|-------|
| `observer_id` | `PROV_OBSERVATIONAL` | Direct mapping |
| `device_id` | `PROV_OBSERVATIONAL` | Observation instrument |
| `capture_timestamp` | `PROV_OBSERVATIONAL` | Observation time |
| `environmental_conditions` | `PROV_OBSERVATIONAL` | Observation context |

---

## 7. Provenance vs Authority

### Critical Distinction

```
Provenance records who did what.
Authority grants permission to do it.
These are orthogonal.
```

| Example | Provenance | Authority |
|---------|------------|-----------|
| Alice modified vocabulary | `PROV_TRANSFORMATION` records Alice's action | Authority Map determines if Alice may modify vocabulary |
| System derived classification | `PROV_DERIVATION` records derivation | Constitutional Invariant 2 prohibits runtime from defining ontology |
| Bob ratified term | `PROV_AUTHORITY` records Bob's ratification | Ratification Model determines if Bob may ratify |

---

## 8. Provenance Schema

### Base Provenance Record

```python
class ProvenanceRecord(BaseModel):
    provenance_id: str  # Auto-generated with prov_ prefix
    provenance_type: Literal[
        "PROV_OBSERVATIONAL",
        "PROV_DERIVATION",
        "PROV_RUNTIME",
        "PROV_AUTHORITY",
        "PROV_TRANSFORMATION",
        "PROV_VALIDATION",
        "PROV_REPLAY"
    ]
    provenance_timestamp: datetime
    provenance_agent: str  # Who or what created this record
    provenance_payload: dict  # Type-specific fields
```

### Schema Version

```
schema_version: "provenance.v1"
```

---

## 9. Open Provenance Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should provenance types be constitutionally fixed? | Stability vs. evolution |
| 2 | Should provenance records be immutable? | Auditability vs. correction |
| 3 | Should all data carry provenance? | Completeness vs. overhead |
| 4 | Should provenance have retention limits? | Storage vs. history |
| 5 | Should mixed-type provenance be normalized? | Semantic clarity vs. migration cost |

---

## Related Documents

- `REPOSITORY_CONSTITUTION.md` — Constitutional authority
- `CANONICAL_ONTOLOGY_VOCABULARY.md` — Vocabulary including "provenance"
- `ONTOLOGY_DRIFT_CLASSIFICATIONS.md` — Provenance semantic split documented
- `docs/architecture/CAM_RUNTIME_DISPATCHER_ARCHITECTURE.md` — Runtime provenance usage
- `docs/handoffs/CAM_RUNTIME_DISPATCHER_DEVELOPER_HANDOFF.md` — Provenance design decisions

---

*Canonical Provenance Model — DRAFT FOR GOVERNANCE RATIFICATION*
