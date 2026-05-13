# Execution Boundary Policy

**CAM Dev Order 7A — Governance vs Execution Isolation**

**Status:** Planning Only — No Implementation  
**Date:** 2026-05-13

---

## Purpose

This document defines the formal separation between governance systems and execution systems. It establishes policies that prevent execution from contaminating governance truth.

**This is architecture planning, not implementation.**

---

## Fundamental Separation

```
┌─────────────────────────────────────────────────────────────────────┐
│                       GOVERNANCE DOMAIN                              │
│                                                                      │
│  Authority: Lifecycle state, policy, validation, audit, promotion   │
│  Truth: Export Object is canonical                                   │
│  Mutation: Only through governed processes                          │
│  Approval: Human decision required                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    [BOUNDARY WALL]
                              │
┌─────────────────────────────────────────────────────────────────────┐
│                       EXECUTION DOMAIN                               │
│                                                                      │
│  Authority: Serialization, translation, postprocessing              │
│  Truth: Derives from Export Object (never vice versa)               │
│  Mutation: Artifacts only, never governance state                   │
│  Approval: Inherited from governance, cannot self-grant             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Boundary Invariants

### Invariant 1: Export Object Supremacy

```
The Export Object is the canonical manufacturing representation.
Translation artifacts derive from it.
Translation artifacts cannot modify it.
```

If a DXF artifact conflicts with its source Export Object, the Export Object is correct.

### Invariant 2: Governance State Immutability from Execution

```
Execution systems cannot modify:
- Capability registry
- Policy engine state
- Audit ledger content
- Promotion evaluation state
- Lifecycle orchestration state
```

Execution is read-only with respect to governance.

### Invariant 3: Approval Authority Isolation

```
Execution systems cannot:
- Grant approvals
- Bypass approval gates
- Create approval tokens
- Extend approval scope
```

Approval authority remains exclusively human.

### Invariant 4: Provenance Chain Integrity

```
Every execution artifact must link to:
- Source Export Object
- Approval authorization
- Execution timestamp
- Translator/postprocessor identity
```

Artifacts without provenance are invalid.

---

## Layer Comparison

| Aspect | Governance Layer | Execution Layer |
|--------|------------------|-----------------|
| Primary purpose | Ensure correctness | Produce artifacts |
| State ownership | Owns lifecycle state | No state ownership |
| Truth source | Export Object | Derives from Export Object |
| Mutation scope | Governance artifacts | Translation artifacts only |
| Approval authority | Grants approvals | Consumes approvals |
| Audit role | Produces audit records | Contributes execution audit |
| Registry access | Read/write (governed) | Read-only |
| Policy enforcement | Enforces | Subject to |
| Failure mode | Block execution | Produce error artifact |

---

## Interaction Protocols

### Governance → Execution (Permitted)

```
1. Governance validates Export Object
2. Governance evaluates translator compatibility
3. Human approves execution
4. Governance passes Export Object + approval token to execution
5. Execution produces artifact
6. Execution returns artifact with provenance
7. Governance records execution audit
```

### Execution → Governance (Prohibited Patterns)

```
❌ Execution modifies capability registry
❌ Execution creates policy exceptions
❌ Execution writes audit ledger directly
❌ Execution grants additional approvals
❌ Execution modifies Export Object
❌ Execution bypasses validation boundary
```

### Execution → Governance (Permitted Patterns)

```
✓ Execution returns artifact reference
✓ Execution returns execution status
✓ Execution returns error information
✓ Execution returns provenance metadata
```

---

## Validation vs Execution Boundary

### Current State (Validation Only)

```python
# These exist and are operational

# dxf_translator_boundary.py
class DXFTranslatorProfile:
    # Declares translator capabilities
    pass

def evaluate_dxf_translator_compatibility():
    # Pure validation, no execution
    pass

# postprocessor_boundary.py  
class MachineProfileValidationOnly:
    # Declares machine capabilities
    pass

def evaluate_postprocessor_compatibility():
    # Pure validation, no execution
    pass
```

### Future State (Validation → Execution)

```
┌─────────────────────────────────────────┐
│         VALIDATION BOUNDARY             │
│         (Current - Operational)         │
│                                         │
│  DXFTranslatorProfile                   │
│  evaluate_dxf_translator_compatibility  │
│  MachineProfileValidationOnly           │
│  evaluate_postprocessor_compatibility   │
│                                         │
│  Purpose: Gate before execution         │
│  Output: Compatibility report           │
│  Side effects: None                     │
└─────────────────────────────────────────┘
                    │
                    ▼
           [Human Approval]
                    │
                    ▼
┌─────────────────────────────────────────┐
│         EXECUTION RUNTIME               │
│         (Future - Not Implemented)      │
│                                         │
│  TranslatorPlugin.generate_artifact()   │
│  PostprocessorPlugin.generate_output()  │
│                                         │
│  Purpose: Produce artifacts             │
│  Output: Translation/machine artifacts  │
│  Side effects: Artifact creation        │
└─────────────────────────────────────────┘
```

The validation boundary is permanent infrastructure, not temporary scaffolding.

---

## Approval Gate Semantics

### Pre-Execution Requirements

Before any execution may occur:

1. **Export Object Validated** — Green gate from governed preview
2. **Translator Compatible** — Green/yellow gate from validation boundary
3. **Policy Approved** — Policy engine allows operation
4. **Human Approved** — Explicit human decision recorded
5. **Authorization Token Present** — Execution context includes approval reference

### Approval Scope Limits

An approval grants:
- Execution of specific Export Object
- By specific translator/postprocessor
- At specific time
- With specific output format

An approval does NOT grant:
- Future executions
- Different Export Objects
- Different translators
- Registry modifications
- Policy exceptions

---

## Failure Handling

### Governance Failure

If governance validation fails:
- Execution is blocked
- No artifacts produced
- Error recorded in lifecycle report
- Human intervention required

### Execution Failure

If execution fails:
- Error artifact produced (with provenance)
- Governance state unchanged
- Execution audit records failure
- May be retried with new approval

### Boundary Violation Attempt

If execution attempts governance modification:
- Operation rejected
- Security alert generated
- Execution context terminated
- Incident recorded

---

## Audit Separation

### Governance Audit (6K)

```
LifecycleAuditLedger:
- Lifecycle decisions
- Policy outcomes
- Capability state
- Validation summaries
- RMOS references
```

### Execution Audit (Future)

```
ExecutionAuditRecord:
- Execution request
- Authorization reference
- Translator/postprocessor identity
- Artifact produced
- Execution duration
- Resource usage
- Error information (if any)
```

These are separate audit systems with separate concerns.

---

## Registry Separation

### CAM_OPERATION_REGISTRY (Governance)

```python
# Governance owns this
CAM_OPERATION_REGISTRY = {
    "nut_slot": {
        "maturity": "canonical",
        "lifecycle_supported": True,
        "machine_output_supported": False,  # Governance flag
        ...
    }
}
```

### TRANSLATOR_PLUGIN_REGISTRY (Execution)

```python
# Execution owns this (future)
TRANSLATOR_PLUGIN_REGISTRY = {
    "dxf_r2000": {
        "execution_allowed": False,
        "validation_only": True,
        ...
    }
}
```

Separate registries. Separate authority. Separate mutation rules.

---

## Enforcement Mechanisms

### Compile-Time Enforcement (Future)

- Execution modules cannot import governance mutation functions
- Type system prevents governance objects in execution context
- Linting rules flag boundary violations

### Runtime Enforcement (Future)

- Execution runs in sandboxed process
- No write access to governance state files
- API calls filtered at boundary
- Authorization tokens validated

### Audit Enforcement

- All execution attempts logged
- Unauthorized attempts trigger alerts
- Periodic audit review of boundary integrity

---

## Policy Violations

### Severity Levels

| Violation | Severity | Response |
|-----------|----------|----------|
| Execution without approval | Critical | Block, alert, audit |
| Governance state mutation from execution | Critical | Reject, rollback, alert |
| Bypassing validation boundary | High | Block, audit |
| Missing provenance | Medium | Reject artifact |
| Expired approval | Low | Request re-approval |

---

## Related Documents

- `TRANSLATOR_EXECUTION_ARCHITECTURE.md` — Runtime topology
- `MACHINE_OUTPUT_AUTHORIZATION_MODEL.md` — Approval semantics
- `TRANSLATOR_SECURITY_MODEL.md` — Isolation requirements

---

*Execution Boundary Policy — CAM 7A — 2026-05-13*
