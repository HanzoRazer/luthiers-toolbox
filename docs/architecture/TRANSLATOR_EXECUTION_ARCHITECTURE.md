# Translator Execution Architecture

**CAM Dev Order 7A — Execution Runtime Topology**

**Status:** Planning Only — No Implementation  
**Date:** 2026-05-13

---

## Purpose

This document defines the future translator execution architecture. It describes how translators and postprocessors will eventually execute, while preserving the governance boundaries established in 6A–6M.

**This is architecture planning, not implementation.**

---

## Core Principle

```
Execution systems must remain subordinate to governance.
Governance systems must not embed execution.
```

The Export Object remains the canonical manufacturing representation. Translation artifacts are downstream serializations, not sources of truth.

---

## Execution Stack Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GOVERNANCE LAYER                              │
│                    (Established in 6A–6M)                            │
│                                                                      │
│  ┌──────────────┐   ┌─────────────┐   ┌─────────────────────────┐   │
│  │ Governed     │ → │ Export      │ → │ Compatibility           │   │
│  │ Preview      │   │ Object      │   │ Validation              │   │
│  └──────────────┘   └─────────────┘   └─────────────────────────┘   │
│                            │                     │                   │
│                            ▼                     ▼                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Lifecycle Orchestration + Policy Engine         │    │
│  │              Audit Ledger + Promotion Evidence               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                            │                                         │
│                            ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              HUMAN APPROVAL BOUNDARY                         │    │
│  │              (6M — registry_mutation_performed = false)      │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       EXECUTION LAYER                                │
│                      (Future — 7A Plans)                             │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              EXECUTION AUTHORIZATION BOUNDARY                │    │
│  │              (Human approval required to cross)              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    TRANSLATOR RUNTIME                         │   │
│  │                                                               │   │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐ │   │
│  │  │ DXF         │   │ SVG         │   │ Neutral Toolpath    │ │   │
│  │  │ Translator  │   │ Translator  │   │ Translator          │ │   │
│  │  └─────────────┘   └─────────────┘   └─────────────────────┘ │   │
│  │                                                               │   │
│  │  Input: Export Object (validated, approved)                   │   │
│  │  Output: Translation Artifact                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  POSTPROCESSOR RUNTIME                        │   │
│  │                                                               │   │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐ │   │
│  │  │ GRBL        │   │ FANUC       │   │ ShopBot             │ │   │
│  │  │ Postproc    │   │ Postproc    │   │ Postproc            │ │   │
│  │  └─────────────┘   └─────────────┘   └─────────────────────┘ │   │
│  │                                                               │   │
│  │  Input: Neutral toolpath (from translator)                    │   │
│  │  Output: Controller-specific machine output                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                MACHINE OUTPUT PACKAGE                         │   │
│  │                                                               │   │
│  │  - Postprocessed artifact                                     │   │
│  │  - Provenance metadata                                        │   │
│  │  - Authorization chain                                        │   │
│  │  - Execution signature                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              MACHINE EXECUTION APPROVAL BOUNDARY              │   │
│  │              (Human approval required before machine run)     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    MACHINE RUNTIME                            │   │
│  │                    (Out of scope for 7A)                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer Ownership

| Layer | Owner | Authority |
|-------|-------|-----------|
| Governed Preview | Governance | Geometry validation |
| Export Object | Governance | Canonical manufacturing representation |
| Compatibility Validation | Governance | Gate before translation |
| Lifecycle Orchestration | Governance | Policy enforcement |
| Human Approval Boundary | Human | Promotion decisions |
| Execution Authorization | Human | Translation approval |
| Translator Runtime | Execution | Serialization |
| Postprocessor Runtime | Execution | Controller specialization |
| Machine Output Package | Execution | Execution bundle |
| Machine Execution Approval | Human | Final execution gate |
| Machine Runtime | Execution | Physical execution |

---

## Authority Boundaries

### Governance Layer Authority

The governance layer may:
- Validate geometry
- Create Export Objects
- Evaluate compatibility
- Enforce policy
- Generate audit trails
- Package promotion evidence
- Recommend actions

The governance layer may NOT:
- Execute translators
- Generate DXF/G-code artifacts
- Modify execution state
- Bypass human approval

### Execution Layer Authority

The execution layer may:
- Serialize Export Objects to format-specific artifacts
- Postprocess toolpaths to controller dialects
- Package machine output
- Record execution audit

The execution layer may NOT:
- Modify governance state
- Bypass approval boundaries
- Mutate Export Objects
- Self-authorize execution
- Skip provenance recording

---

## Artifact Transitions

```
Export Object (canonical)
    │
    ├── [Human Approval] ──→ Translation Artifact (DXF, SVG, etc.)
    │                              │
    │                              └── [Provenance linked to Export Object]
    │
    └── [Human Approval] ──→ Neutral Toolpath Package
                                   │
                                   ├── [Human Approval] ──→ GRBL G-code
                                   ├── [Human Approval] ──→ FANUC G-code
                                   └── [Human Approval] ──→ ShopBot file
```

Each transition requires:
1. Prior stage validated
2. Human approval granted
3. Provenance chain maintained
4. Audit record created

---

## Execution Isolation Requirements

### Runtime Isolation

Future translator runtimes must:
- Execute in isolated contexts
- Have no write access to governance state
- Have no network access (unless explicitly approved)
- Have bounded resource usage
- Have deterministic output for same input

### State Isolation

Execution systems must NOT:
- Modify capability registry
- Modify policy engine state
- Modify audit ledgers
- Create governance artifacts
- Bypass validation boundaries

---

## Integration with Existing Validation Layers

### Current State (Validation Only)

```python
# dxf_translator_boundary.py — Validation gate
DXFTranslatorProfile
evaluate_dxf_translator_compatibility()

# postprocessor_boundary.py — Validation gate  
MachineProfileValidationOnly
evaluate_postprocessor_compatibility()

# export_object_to_dxf_adapter.py — Compatibility adapter
evaluate_dxf_translator_compatibility()
```

### Future State (Validation → Execution)

```
Validation Boundary (EXISTS)
         │
         ▼
    [Approval Gate]
         │
         ▼
Execution Runtime (FUTURE)
```

The existing validation modules are not temporary scaffolding. They are the permanent governance gate that precedes any future execution.

---

## dxf_compat Position

The existing `dxf_compat` module is:
- Low-level DXF serialization infrastructure
- Deterministic R12/R2000 format writer
- NOT a translator
- NOT a governance component

Future DXF Translator will:
- Call `dxf_compat` internally for serialization
- Only execute after approval gates
- Record provenance to RMOS
- Never bypass validation boundary

```
Export Object
    │
    ▼
DXF Translator (future, governed)
    │
    ▼
dxf_compat (existing, serialization infra)
    │
    ▼
DXF Artifact
```

---

## Non-Goals

This architecture explicitly does NOT plan for:
- Real-time machine control
- Streaming execution
- Controller feedback loops
- Machine learning integration
- Automatic approval systems
- Self-modifying translators

---

## Related Documents

- `TRANSLATOR_PLUGIN_STANDARD.md` — Plugin interface contracts
- `EXECUTION_BOUNDARY_POLICY.md` — Governance vs execution isolation
- `MACHINE_OUTPUT_AUTHORIZATION_MODEL.md` — Approval semantics
- `TRANSLATOR_ARTIFACT_LIFECYCLE.md` — Artifact provenance
- `CAM_GOVERNED_EXPORT_ARCHITECTURE.md` — Export Object architecture

---

*Translator Execution Architecture — CAM 7A — 2026-05-13*
