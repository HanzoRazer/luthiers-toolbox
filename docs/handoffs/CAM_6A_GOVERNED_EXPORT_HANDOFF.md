# CAM Dev Order 6A — Governed Export Architecture Handoff

**Date:** 2026-05-10  
**Author:** Claude (CAM Dev Order 6A)  
**Status:** COMPLETE

---

## Summary

Defined the canonical architecture for governed CAM export, establishing clear boundaries between Preview, Export, and Machine Output layers. Created comprehensive documentation connecting existing policies with new architectural definitions.

**Key outcome:** The repo now has a complete architectural model for portable manufacturing representation, separating human inspection (Preview) from manufacturing systems (Export) from machine execution (Machine Output).

---

## Scope

### In Scope (Completed)

- Layer architecture definition (7 layers)
- Classification system (PREVIEW, EXPORT, MACHINE OUTPUT)
- Boundary definitions with crossing requirements
- Export Object schema
- Postprocessor interface contract
- Machine profile model
- Tool library model
- Export lifecycle specification
- Governance registry manifest

### Out of Scope (Per 6A Guardrails)

- No implementation code
- No endpoint changes
- No G-code generation changes
- No existing policy modifications

---

## Deliverables

| Deliverable | Location | Purpose |
|-------------|----------|---------|
| CAM_GOVERNED_EXPORT_ARCHITECTURE.md | docs/architecture/ | Umbrella document |
| CAM_EXPORT_OBJECT_MODEL.md | docs/architecture/ | Export schema |
| CAM_POSTPROCESSOR_INTERFACE_STANDARD.md | docs/architecture/ | Translation boundary |
| CAM_MACHINE_PROFILE_STANDARD.md | docs/architecture/ | Machine abstraction |
| CAM_TOOL_LIBRARY_STANDARD.md | docs/architecture/ | Tooling abstraction |
| CAM_EXPORT_LIFECYCLE.md | docs/architecture/ | Flow specification |
| governed_export_manifest.json | docs/architecture/ | Registry |
| CAM_6A_GOVERNED_EXPORT_HANDOFF.md | docs/handoffs/ | This document |

---

## Architecture Summary

### Layer Model

```
Layer 1: Geometry           — NEUTRAL — Pure dimensional data
Layer 2: Toolpath           — NEUTRAL — Machine-agnostic generation
Layer 3: Governed Preview   — PREVIEW — Human inspection, gate evaluation
Layer 4: Export Object      — EXPORT — Portable manufacturing representation
Layer 5: RMOS Persistence   — GOVERNANCE — Artifact storage, lineage
Layer 6: Postprocessor      — MACHINE OUTPUT — Controller translation
Layer 7: Machine Output     — MACHINE OUTPUT — Executable delivery
```

### Classification System

| Classification | Purpose | Governance |
|----------------|---------|------------|
| NEUTRAL | No governance | None |
| PREVIEW | Human inspection | Governed Preview Standard |
| EXPORT | Manufacturing systems | Export Object Model |
| GOVERNANCE | System tracking | RMOS |
| MACHINE OUTPUT | Machine execution | Quarantine + Export Policy |

### Boundary Crossings

**Preview → Export:**
- Gate GREEN or YELLOW
- User confirmation for YELLOW
- Validation record attached
- Preview hash preserved

**Export → Postprocessor:**
- Valid Export Object
- Machine Profile selected
- Tool validated
- Envelope validated
- RMOS tracking active

---

## Export Object Model

Self-contained portable manufacturing representation:

```json
{
  "schema_version": "1.0.0",
  "export_id": "EXP-...",
  "export_type": "toolpath",
  "metadata": { ... },
  "geometry": { ... },
  "toolpaths": { ... },
  "tooling": { ... },
  "material": { ... },
  "stock": { ... },
  "validation": { ... },
  "intent": { ... }
}
```

---

## Postprocessor Model

Interface contract for machine translation:

- Consumes Export Object + Machine Profile
- Validates compatibility before translation
- Produces machine-specific G-code
- Records audit trail with hashes

---

## Machine Profile Model

Declarative machine specification:

- Controller type and dialect
- Work envelope
- Spindle capabilities
- Feed rate limits
- Tool change behavior
- Feature capabilities

---

## Tool Library Model

Declarative tool specification:

- Physical geometry
- Material/coating
- Operation classes
- Recommended parameters
- Machine compatibility rules

---

## Strategic Outcome

After 6A, the repo has:

1. **Clear classification** — Every output type classified
2. **Defined boundaries** — Explicit crossing requirements
3. **Export Object model** — Canonical portable representation
4. **Postprocessor interface** — Standard translation boundary
5. **Machine profile model** — Machine abstraction
6. **Tool library model** — Tooling abstraction
7. **Governance integration** — Existing policies connected

This enables:
- DXF export normalization
- G-code promotion from quarantine
- Postprocessor implementation
- Machine profile creation
- Tool library integration

---

## Relationship to Prior Work

### 5C-5E (Governed Preview)

6A builds on top of the Governed Preview Standard established in 5C-5E. Preview responses with gate evaluation flow into the Export Object creation process.

### 5F (Rosette Audit)

The Rosette audit identified `/rmos/rosette/export-cnc` as a G-code export without RMOS governance. The Export Lifecycle defined in 6A provides the architectural framework for bringing this endpoint into compliance.

### Existing Policies

6A integrates with:
- `CAM_EXPORT_GOVERNANCE_POLICY.md` — Export → Machine Output gates
- `CAM_POSTPROCESSOR_BOUNDARY.md` — Postprocessor requirements
- `CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md` — Endpoint classification
- `CAM_PREVIEW_CONTRACT_STANDARD.md` — Preview response shape

---

## Recommended Next Steps

### 6B: Export Object Implementation

Implement Export Object creation from governed previews:
1. Define `ExportObject` dataclass
2. Add export endpoints to governed preview operations
3. Wire RMOS artifact persistence

### 6C: Postprocessor Implementation

Implement GRBL postprocessor as reference:
1. Implement `GRBLPostprocessor` class
2. Add validation against machine profile
3. Add audit trail integration

### 6D: Machine Profile Editor

Create UI for machine profile management:
1. Profile creation/editing
2. Envelope visualization
3. Capability selection

### 6E: Tool Library Editor

Create UI for tool library management:
1. Tool creation/editing
2. Machine compatibility display
3. Operation class assignment

---

## Test Verification

No implementation code changed. All existing tests remain passing:
- 179 tests passed
- Coverage: 23.04%

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| governed_export_manifest.json | Machine-readable registry |
| CAM_5F_ROSETTE_AUDIT_HANDOFF.md | Prior audit |
| CAM_5E_DRILLING_NORMALIZATION_NOTES.md | Prior normalization |
| FEATURE_PARITY_MIGRATION_POLICY.md | Migration governance |

---

*6A architecture complete: 2026-05-10*
