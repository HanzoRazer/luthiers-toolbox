# CAM Governed Export Architecture

**Date:** 2026-05-10  
**Status:** ARCHITECTURAL DEFINITION  
**Dev Order:** 6A  
**Scope:** Canonical export model connecting preview, export, and machine output

---

## Purpose

This document defines the canonical architecture for governed CAM export, establishing clear boundaries between:

- **Preview** — human-inspection-oriented representation
- **Export** — portable manufacturing-oriented representation  
- **Machine Output** — machine-executable representation

This architecture integrates and supersedes the governance policies defined in:
- `CAM_POSTPROCESSOR_BOUNDARY.md`
- `CAM_EXPORT_GOVERNANCE_POLICY.md`
- `CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md`

---

## Core Architectural Principle

```
Preview validates geometry.
Export preserves manufacturing intent.
Postprocessors produce machine-specific execution.
```

These are distinct concerns with distinct governance requirements.

---

## Layer Architecture (Extended)

Building on the layer model from `CAM_POSTPROCESSOR_BOUNDARY.md`:

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Geometry                                              │
│  ─────────────────                                              │
│  Pure dimensional data — no machining semantics                 │
│  FretboardEcosphere, NeckGeometry, body outlines                │
│  Classification: NEUTRAL                                        │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Toolpath                                              │
│  ─────────────────                                              │
│  Machine-agnostic toolpath generation                           │
│  nut_slot_cam.py, fret_slots_cam.py, rosette_cam_bridge.py      │
│  Output: ToolpathMove[] — neutral intermediate representation   │
│  Classification: NEUTRAL                                        │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Governed Preview                                      │
│  ────────────────────────                                       │
│  Human-inspection representation                                │
│  Gate evaluation, integrity checks, statistics                  │
│  Output: Preview JSON — visualization + validation              │
│  Classification: PREVIEW                                        │
│  Status: ✓ COMPLETE (5C-5E)                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
           ════════════════════════════════════════
           ║       EXPORT BOUNDARY (6A)           ║
           ════════════════════════════════════════
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: Export Object                                         │
│  ───────────────────────                                        │
│  Portable manufacturing representation                          │
│  Includes: geometry, toolpaths, tooling, material, intent       │
│  Output: ExportObject JSON/bundle                               │
│  Classification: EXPORT                                         │
│  Status: ✗ ARCHITECTURE DEFINED (6A)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5: RMOS Persistence (Optional)                           │
│  ─────────────────────────────────────                          │
│  Artifact storage, lineage, provenance                          │
│  Run ID, hashing, attachment persistence                        │
│  Classification: GOVERNANCE                                     │
│  Status: ✓ PARTIAL (existing RMOS)                              │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
           ════════════════════════════════════════
           ║    POSTPROCESSOR BOUNDARY            ║
           ════════════════════════════════════════
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 6: Postprocessor                                         │
│  ──────────────────────                                         │
│  Machine/controller-specific translation                        │
│  Input: ExportObject + MachineProfile                           │
│  Output: Machine-specific instructions                          │
│  Classification: MACHINE OUTPUT                                 │
│  Status: ✗ INTERFACE DEFINED (6A)                               │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 7: Machine Output                                        │
│  ─────────────────────                                          │
│  Executable delivery                                            │
│  G-code files, .nc/.ngc/.tap, serial stream                     │
│  Classification: MACHINE OUTPUT                                 │
│  Status: ✗ NOT IMPLEMENTED                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Classification System

### Classification: PREVIEW

**Definition:** Human-inspection-oriented representation intended for visualization and validation.

**Characteristics:**
- JSON response format
- Includes gate evaluation (GREEN/YELLOW/RED)
- Contains statistics and warnings
- May include SVG visualization
- NOT executable by machines
- NOT intended for downstream CAM import

**Examples:**
- Nut slot preview JSON
- Fret slot preview response
- Drilling preview with hole positions
- SVG backplot visualization

**Governance:** Governed Preview Standard (5C-5E)

---

### Classification: EXPORT

**Definition:** Portable manufacturing-oriented representation that preserves manufacturing intent for downstream systems.

**Characteristics:**
- Self-contained bundle (geometry + tooling + material + intent)
- Machine-agnostic (no controller-specific syntax)
- Importable by downstream CAM systems
- May include DXF geometry
- May include neutral toolpath JSON
- Preserves complete manufacturing specification

**Examples:**
- DXF body outline for CAM import
- Export Object bundle with toolpaths + tooling
- Neutral toolpath JSON with complete context

**Governance:** Export Object Model (defined in `CAM_EXPORT_OBJECT_MODEL.md`)

---

### Classification: MACHINE OUTPUT

**Definition:** Machine-executable representation specific to a particular controller or machine.

**Characteristics:**
- Controller-specific syntax (GRBL, FANUC, LinuxCNC, etc.)
- Executable by target machine
- Requires postprocessor translation
- Requires complete machine profile
- Subject to strict governance gates

**Examples:**
- GRBL G-code file (.nc)
- FANUC program
- LinuxCNC output

**Governance:** Machine Output Quarantine Policy + Export Governance Policy

---

## Export Object Concept

The **Export Object** is the canonical portable manufacturing representation. It sits between governed preview and machine-specific postprocessing.

### Purpose

The Export Object:
1. **Preserves manufacturing intent** — All information needed to manufacture the part
2. **Remains machine-agnostic** — No controller-specific syntax
3. **Enables portability** — Can be imported by various downstream systems
4. **Supports traceability** — Links to source geometry and validation results

### Structure (Summary)

See `CAM_EXPORT_OBJECT_MODEL.md` for complete schema.

```
ExportObject {
  metadata {
    id, version, created_at, source_preview_id
  }
  geometry {
    coordinate_system, bounds, entities[]
  }
  toolpaths {
    operations[], moves[], statistics
  }
  tooling {
    tool_id, geometry, material
  }
  material {
    material_id, properties
  }
  validation {
    gate_status, issues[], preview_hash
  }
  intent {
    operation_type, depth_strategy, finish_requirements
  }
}
```

---

## Boundary Definitions

### Preview → Export Boundary

**Location:** Between Layer 3 (Governed Preview) and Layer 4 (Export Object)

**Crossing requires:**
1. Preview gate status GREEN or YELLOW (not RED)
2. User confirmation for YELLOW gates
3. Complete validation record attached
4. Source preview hash preserved

**Key distinction:** Preview is for human inspection. Export is for manufacturing systems.

### Export → Postprocessor Boundary

**Location:** Between Layer 5 (RMOS Persistence) and Layer 6 (Postprocessor)

**Crossing requires:**
1. Valid Export Object
2. Selected Machine Profile
3. Tool validation against machine
4. Envelope validation against machine
5. RMOS run tracking (mandatory)

**Key distinction:** Export is machine-agnostic. Postprocessor is machine-specific.

---

## Governance Integration

### Relationship to Existing Policies

| Policy Document | Role in Architecture |
|-----------------|---------------------|
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Defines gates for Export → Machine Output |
| `CAM_POSTPROCESSOR_BOUNDARY.md` | Defines postprocessor interface requirements |
| `CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md` | Classifies endpoints by governance status |
| `CAM_PREVIEW_CONTRACT_STANDARD.md` | Defines governed preview response shape |

### Governance Flow

```
1. Preview Generation
   └── Governed Preview Standard applies
   └── Gate evaluation performed
   └── Issues/warnings captured

2. Export Object Creation
   └── Preview validation required (not RED)
   └── Export Object Model applies
   └── Manufacturing intent captured

3. RMOS Persistence (Optional)
   └── Run ID generated
   └── Artifacts hashed and stored
   └── Lineage established

4. Postprocessor Execution
   └── Machine Profile required
   └── Postprocessor Interface Standard applies
   └── All Export Governance gates must pass

5. Machine Output Delivery
   └── Quarantine Policy applies
   └── Audit trail required
   └── User confirmation required
```

---

## Current State vs Target State

### Current State (Post-5E)

| Layer | Status |
|-------|--------|
| Geometry | Complete |
| Toolpath | Complete |
| Governed Preview | **Complete** (5C-5E) |
| Export Object | Not defined |
| RMOS Persistence | Partial |
| Postprocessor | Fragmented |
| Machine Output | Quarantined |

### Target State (Post-6A)

| Layer | Status |
|-------|--------|
| Geometry | Complete |
| Toolpath | Complete |
| Governed Preview | Complete |
| Export Object | **Architecture defined** |
| RMOS Persistence | Architecture aligned |
| Postprocessor | **Interface defined** |
| Machine Output | Quarantined (unchanged) |

---

## Strategic Outcome

After 6A, the repo has:

1. **Clear classification** — Every output type classified as PREVIEW, EXPORT, or MACHINE OUTPUT
2. **Defined boundaries** — Explicit crossing requirements between layers
3. **Export Object model** — Canonical portable manufacturing representation
4. **Postprocessor interface** — Standard translation boundary
5. **Machine profile model** — Machine abstraction for postprocessors
6. **Tool library model** — Tooling abstraction for export objects
7. **Governance integration** — Existing policies connected to architecture

This provides the foundation for all future:
- DXF export normalization
- G-code promotion
- Postprocessor implementation
- Machine profile creation
- Tool library integration

---

## Capability → Layer Mapping

The CAM Capability Registry (6H) defines operation exportability classes. This table maps each class to the layer architecture:

| Exportability Class | Applicable Layers | Description |
|---------------------|-------------------|-------------|
| `preview_only` | Layers 1-3 only | Preview generation only; no export object |
| `governed_export` | Layers 1-5 | Full export pipeline through RMOS persistence |
| `translator_ready` | Layers 1-6 (validation only) | Export + translator validation (no execution) |
| `machine_candidate` | Layers 1-7 (future) | Full pipeline including machine output (not yet implemented) |

**Cross-Reference:** `services/api/app/cam/cam_operation_registry.py`

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| `CAM_EXPORT_OBJECT_MODEL.md` | Export object schema |
| `CAM_POSTPROCESSOR_INTERFACE_STANDARD.md` | Postprocessor contract |
| `CAM_MACHINE_PROFILE_STANDARD.md` | Machine abstraction |
| `CAM_TOOL_LIBRARY_STANDARD.md` | Tooling abstraction |
| `CAM_EXPORT_LIFECYCLE.md` | Preview→Export→Machine flow |
| `governed_export_manifest.json` | Registry |

---

*Architecture defined: 2026-05-10*
