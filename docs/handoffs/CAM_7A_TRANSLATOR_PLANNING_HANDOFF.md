# CAM Dev Order 7A: Translator Planning Handoff

**Date:** 2026-05-13  
**Status:** Complete (Planning Only)  
**Predecessor:** 6M (Promotion Evidence)

---

## Summary

Defined the future translator execution architecture without implementing any translator execution. Established execution boundaries, authorization models, artifact lifecycles, and security requirements that preserve the governance guarantees from 6A–6M.

---

## Core Outcome

```
Execution systems will remain subordinate to governance.
Governance will not embed execution.
```

This boundary is now architecturally documented across 7 planning documents.

---

## Documents Created

| Document | Purpose |
|----------|---------|
| `TRANSLATOR_EXECUTION_ARCHITECTURE.md` | Runtime topology: Export Object → Translator → Postprocessor → Machine |
| `TRANSLATOR_PLUGIN_STANDARD.md` | Interface contracts for translator/postprocessor plugins |
| `EXECUTION_BOUNDARY_POLICY.md` | Formal separation between governance and execution |
| `MACHINE_OUTPUT_AUTHORIZATION_MODEL.md` | Human approval semantics for execution stages |
| `TRANSLATOR_ARTIFACT_LIFECYCLE.md` | Artifact chain provenance and immutability |
| `EXECUTION_CAPABILITY_REGISTRY_MODEL.md` | Translator capability declarations (separate from operation registry) |
| `TRANSLATOR_SECURITY_MODEL.md` | Sandboxing, isolation, determinism, verification |

---

## Key Architectural Decisions

### 1. Two Registries, Two Authorities

```
CAM_OPERATION_REGISTRY (Governance)
- Defines operations and their governance state
- Controls lifecycle, policy, promotion
- Exists (6H)

TRANSLATOR_CAPABILITY_REGISTRY (Execution)
- Defines translator/postprocessor capabilities
- Controls execution enablement
- Future (not implemented)
```

These are separate registries with separate authority chains.

### 2. Validation → Approval → Execution Flow

```
Existing Validation Boundary
         │
         ├── DXFTranslatorProfile
         ├── evaluate_dxf_translator_compatibility()
         ├── MachineProfileValidationOnly
         └── evaluate_postprocessor_compatibility()
         │
         ▼
    [Human Approval]
         │
         ▼
Future Execution Runtime
         │
         ├── TranslatorPlugin.generate_translation_artifact()
         └── PostprocessorPlugin.generate_machine_output()
```

The existing validation modules are permanent gates, not temporary scaffolding.

### 3. Translator vs Postprocessor Distinction

| Component | Input | Output | Examples |
|-----------|-------|--------|----------|
| Translator | Export Object | Format-specific artifact | DXF, SVG, neutral toolpath |
| Postprocessor | Neutral toolpath | Controller-specific output | GRBL, FANUC, ShopBot |

### 4. dxf_compat Position

```
dxf_compat = Low-level serialization infrastructure
DXF Translator = Future governed wrapper that calls dxf_compat

dxf_compat does NOT become canonical.
Export Object remains canonical.
```

### 5. Authorization Chain

```
Lifecycle Approval (6M) — operation maturity
         │
         ▼
Translation Approval (future) — Export Object → artifact
         │
         ▼
Postprocessing Approval (future) — artifact → machine output
         │
         ▼
Execution Approval (future) — output → physical machine
```

Each stage requires explicit human approval.

---

## Governance Preservation

### Invariants Preserved

| Invariant | Status |
|-----------|--------|
| Export Object is canonical | Preserved |
| Execution cannot mutate governance state | Enforced |
| Human approval required | Required |
| Provenance chain required | Specified |
| Deterministic execution | Required |
| Sandboxed execution | Required |

### What Execution May NOT Do

- Modify CAM_OPERATION_REGISTRY
- Modify policy engine state
- Modify audit ledgers
- Create approvals
- Bypass validation boundaries
- Access filesystem (outside sandbox)
- Access network
- Generate non-deterministic output

---

## Integration with Existing Code

### Existing Validation Modules

| Module | Role in Architecture |
|--------|---------------------|
| `dxf_translator_boundary.py` | Validation gate before DXF translation |
| `postprocessor_boundary.py` | Validation gate before postprocessing |
| `export_object_to_dxf_adapter.py` | Compatibility adapter |
| `dxf_compat.py` | Serialization infrastructure (to be called by translator) |

### Existing Governance Modules

| Module | Role |
|--------|------|
| `cam_operation_registry.py` | Operation capabilities (governance) |
| `cam_lifecycle_policy_engine.py` | Policy enforcement |
| `cam_lifecycle_audit_ledger.py` | Audit traceability |
| `cam_promotion_evidence.py` | Promotion evidence packaging |

No changes to existing code required for 7A (planning only).

---

## Security Model Summary

### Sandboxing

- Execution runs in isolated context
- No filesystem access
- No network access
- Bounded resources (256MB memory, 60s CPU)
- No access to governance state

### Determinism

- Same input → same output
- No random values
- No timestamps in output
- Stable iteration order
- Verifiable by re-execution

### Verification

- Artifact format validation
- Hash verification
- Provenance chain verification
- Authorization token verification
- Prohibited content scanning

---

## Unresolved Questions

### 1. Sandbox Implementation

Which sandboxing technology?
- Process isolation
- Container isolation
- WASM sandbox
- Python subprocess with restrictions

Decision deferred to implementation phase.

### 2. Plugin Loading

How are plugins loaded?
- Built-in only (no dynamic loading)
- Dynamic loading with code signing
- Plugin marketplace

Decision deferred.

### 3. Authorization Token Storage

Where are tokens stored?
- In-memory only
- Persisted to RMOS
- Separate token store

Decision deferred.

### 4. Multi-Machine Workflow

How does authorization flow across machines?
- Not addressed in 7A
- Requires network security model

Future consideration.

---

## Implementation Constraints

When execution is eventually implemented:

1. **No bypass of validation boundary** — Translator must call validation layer
2. **No direct RMOS writes** — Go through governance layer
3. **No registry modification** — Read-only access
4. **No approval self-grant** — Tokens come from governance
5. **No network access** — Sandboxed execution
6. **No filesystem access** — Sandboxed execution
7. **Deterministic output** — Same input = same output
8. **Full provenance** — Every artifact links to source

---

## Test Impact

### No Code Changes

7A is planning only. No code was modified.

### CAM Tests Unchanged

All 478 CAM tests remain passing. No regression.

---

## Future Implementation Order

When execution implementation begins:

```
1. Sandbox infrastructure
2. Translator capability registry (separate from operation registry)
3. DXF translator wrapper (around dxf_compat)
4. Authorization token model
5. Artifact persistence with provenance
6. Postprocessor framework
7. Controller-specific postprocessors
8. Machine output packaging
9. Execution approval UI
```

Each step requires architecture review before implementation.

---

## What 7A Does NOT Do

- No translator implementation
- No postprocessor implementation
- No DXF generation
- No G-code generation
- No execution runtimes
- No sandbox implementation
- No approval automation
- No token persistence
- No machine control

**Planning only. No execution.**

---

*Translator Planning Handoff — CAM 7A — 2026-05-13*
