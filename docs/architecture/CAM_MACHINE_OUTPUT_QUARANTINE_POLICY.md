# CAM Machine Output Quarantine Policy

**Date:** 2026-05-08  
**Status:** ACTIVE POLICY  
**Scope:** All G-code-emitting endpoints and services  
**Cross-ref:** CAM_EXPORT_GOVERNANCE_POLICY.md, CAM_MODULE_CLASSIFICATION_2026-05-07.md

---

## Purpose

This policy defines which endpoints produce machine-ready output (G-code, .nc, .tap, .ngc files) and their governance status. It distinguishes between:

1. **GOVERNED MACHINE OUTPUT** — Endpoints with full audit trail, RMOS tracking, and validation
2. **QUARANTINE** — Endpoints that emit machine output without governance, requiring review
3. **CANDIDATE** — Modules that generate G-code but need governance review before production use
4. **LIBRARY** — Code that parses/simulates G-code but does not emit it

---

## Governance Model

### What Makes Output "Governed"

The canonical pattern is `rmos/mvp_router.py`. Governed output must have:

| Requirement | Description |
|-------------|-------------|
| **Run ID** | Unique identifier (e.g., `RUN-DXF-...`) for traceability |
| **Input hashing** | SHA-256 of input geometry for provenance |
| **Attachment persistence** | Input and output stored via `put_*_attachment()` |
| **Toolpath validation** | Calls validated CAM generator (e.g., `compute_plan()`) |
| **Post-processor ready** | Uses or is compatible with `rmos/posts/` framework |

### What Makes Output "Quarantined"

Endpoints that:
- Return `PlainTextResponse` with G-code content directly
- Set `Content-Disposition: attachment` for .nc/.ngc/.tap download
- Call `emit_gcode_*` or `generate_gcode()` without RMOS tracking
- Do not persist artifacts for audit

---

## Classification: TRUE QUARANTINE TARGETS

These endpoints produce machine-ready output without governance gates:

### 1. Saw Lab Batch G-code Router

| Property | Value |
|----------|-------|
| **File** | `app/saw_lab/batch_gcode_router.py` |
| **Endpoints** | `GET /api/saw/batch/op-toolpaths/{id}/gcode`<br>`GET /api/saw/batch/executions/{id}/gcode` |
| **Output** | `PlainTextResponse` with `.ngc` filename |
| **Risk** | HIGH — downloadable G-code without RMOS audit trail |
| **Service** | `services/saw_lab_gcode_emit_service.py` |

**Evidence:**
- Line 36: Returns G-code via `PlainTextResponse`
- Line 60: Sets `Content-Disposition: attachment; filename="{id}.ngc"`
- Calls `emit_gcode_from_moves()` which has `@safety_critical` decorator but no RMOS run tracking

### 2. Saw Lab G-code Emit Service

| Property | Value |
|----------|-------|
| **File** | `app/services/saw_lab_gcode_emit_service.py` |
| **Function** | `emit_gcode_from_moves()` |
| **Output** | G-code string |
| **Risk** | MEDIUM — service layer, not directly exposed |

---

## Classification: GOVERNED MACHINE OUTPUT

These endpoints follow the canonical governance pattern:

### 1. MVP DXF-to-GRBL Router

| Property | Value |
|----------|-------|
| **File** | `app/rmos/mvp_router.py` |
| **Endpoint** | `POST /wrap/mvp/dxf-to-grbl` |
| **Governance** | Full RMOS tracking, SHA hashing, attachment persistence |
| **Status** | **CANONICAL** |

---

## Classification: CANDIDATE G-CODE GENERATORS

These modules generate G-code but are not directly exposed via routes, or need governance review:

| Module | Location | Risk | Notes |
|--------|----------|------|-------|
| ProfileToolpathGenerator | `cam/profiling/profile_toolpath.py` | LOW | Generator class, not direct endpoint |
| DrillingPeckCycleGenerator | `cam/drilling/peck_cycle.py` | LOW | Generator class |
| VCarveToolpathGenerator | `cam/vcarve/toolpath.py` | LOW | Generator class |
| BindingChannelGenerator | `cam/binding/channel_toolpath.py` | LOW | Generator class |
| SurfaceCarvingGenerator | `cam/carving/surface_carving.py` | LOW | Generator class |
| FretSlotGenerator | `cam/neck/fret_slots.py` | LOW | Generator class |
| LesPaulGCodeGenerator | `generators/lespaul_gcode/` | LOW | Full instrument generator |
| AcousticBodyGenerator | `generators/acoustic_body_generator.py` | LOW | Full instrument generator |
| fret_slots_cam.generate_gcode | `calculators/fret_slots_cam.py` | MEDIUM | Has `generate_gcode()` function |
| fret_slots_export.generate_gcode | `calculators/fret_slots_export.py` | MEDIUM | Export function |

### CANDIDATE Routers (G-code endpoints needing review)

| Endpoint | Router | Generator | Notes |
|----------|--------|-----------|-------|
| `/api/cam/drilling/pattern/gcode` | drill_pattern_router.py | DrillingPeckCycleGenerator | Verify RMOS wiring |
| `/api/cam/drilling/modal/gcode` | drill_modal_router.py | generate_drilling_gcode() | Verify RMOS wiring |
| `/api/cam/profiling/gcode` | profile_router.py | ProfileToolpathGenerator | Verify RMOS wiring |
| `/api/cam/binding/channel/gcode` | binding_router.py | BindingChannelGenerator | Verify RMOS wiring |
| `/api/cam/vcarve/production/gcode` | production_router.py | VCarveToolpathGenerator | Verify RMOS wiring |
| `/api/cam/rosette/post-gcode` | rosette_toolpath_router.py | cnc_gcode_exporter | Verify RMOS wiring |
| `/cam/gcode` | dxf_workflow.py | Various | Legacy endpoint, verify status |

---

## Classification: LIBRARY (Not Machine Output)

These modules parse, simulate, or analyze G-code but do not generate machine output:

| Module | Location | Purpose |
|--------|----------|---------|
| simulator.py | `util/gcode/simulator.py` | G-code state machine, travel calc |
| lexer.py | `util/gcode/lexer.py` | G-code parsing |
| types.py | `util/gcode/types.py` | Type definitions |
| geometry.py | `util/gcode/geometry.py` | Arc interpolation |

---

## Promotion Criteria by Category

### Fret Slot CAM
To promote from CANDIDATE to CANONICAL:
- [ ] Coordinate system documented (fretboard nut end origin)
- [ ] Input/output contract documented (PlanIn → G-code string)
- [ ] Unit tests with boundary conditions
- [ ] Safety gates for depth vs stock thickness
- [ ] Preview endpoint before export
- [ ] Postprocessor boundary (uses `rmos/posts/` or documented alternative)
- [ ] Route provenance documented

### Drilling
To promote from CANDIDATE to CANONICAL:
- [ ] Coordinate system documented
- [ ] Peck depth vs stock thickness validation
- [ ] Retract height safety checks
- [ ] Preview visualization
- [ ] RMOS run tracking wired

### Profiling
To promote from CANDIDATE to CANONICAL:
- [ ] Coordinate system documented
- [ ] Holding tab placement validation
- [ ] Entry/exit strategy documented
- [ ] Preview with safe moves highlighted
- [ ] RMOS run tracking wired

### V-Carve
To promote from CANDIDATE to CANONICAL:
- [ ] Coordinate system documented
- [ ] V-bit geometry validation (angle, tip diameter)
- [ ] Depth limit checks
- [ ] Preview visualization
- [ ] RMOS run tracking wired

### Binding
To promote from CANDIDATE to CANONICAL:
- [ ] Coordinate system documented (body outline relative)
- [ ] Channel depth vs wood thickness
- [ ] Ledge offset validation
- [ ] Preview visualization
- [ ] RMOS run tracking wired

### Rosette
To promote from CANDIDATE to CANONICAL:
- [ ] Coordinate system documented (soundhole center relative)
- [ ] Pattern geometry validation
- [ ] Depth vs top thickness
- [ ] Preview visualization
- [ ] RMOS run tracking wired

### Saw Lab
To promote from CANDIDATE to GOVERNED:
- [ ] Coordinate system documented
- [ ] Blade dynamics validation integrated
- [ ] Risk evaluator gates enforced
- [ ] RMOS run tracking (not just artifact storage)
- [ ] Audit trail with run_id pattern
- [ ] Input hashing for provenance

---

## Quarantine Release Process

Before an endpoint can be promoted from QUARANTINE to GOVERNED:

1. **Gate audit** — All safety gates from CAM_EXPORT_GOVERNANCE_POLICY.md must pass
2. **RMOS integration** — Must use `put_*_attachment()` for input/output persistence
3. **Run ID** — Must generate unique run identifier
4. **Postprocessor** — Must use or be compatible with `rmos/posts/` framework
5. **Documentation** — Coordinate system, input/output contract documented
6. **Tests** — Gate evaluation tests, boundary condition tests
7. **Review** — Architecture review before promotion

---

## Policy Enforcement

### Current State (4B)

- Documentation and labeling only
- No runtime blockers
- No endpoint disabling
- No route behavior changes

### Future State (4C+)

When governance gates are implemented:
- Runtime checks for machine output
- Audit logging for all G-code downloads
- User acknowledgment before download
- RMOS run tracking mandatory

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Safety gates definition |
| `CAM_MODULE_CLASSIFICATION_2026-05-07.md` | Module classification |
| `CAM_COORDINATE_SYSTEM_GOVERNANCE.md` | Coordinate validation |
| `CAM_GCODE_GENERATION_HANDOFF_2026-05-08.md` | Generator inventory |
| `CAM_PROMOTION_FRAMEWORK.md` | Promotion stages for candidates |
| `cam_candidate_registry.json` | Machine-readable candidate status |

---

*Policy established: 2026-05-08*  
*Cross-references updated: 2026-05-09*
