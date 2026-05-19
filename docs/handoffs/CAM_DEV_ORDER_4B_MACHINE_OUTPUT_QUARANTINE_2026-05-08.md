# CAM Dev Order 4B — Machine Output Quarantine

**Date:** 2026-05-08  
**Scope:** Identify and label all machine-output surfaces  
**Status:** COMPLETE  
**Depends on:** CAM Dev Order 4A (audit + governance docs)

---

## Executive Summary

Dev Order 4B identifies all surfaces in the codebase that produce machine-ready output (G-code, .nc, .tap, .ngc files) and classifies them by governance status.

**Key findings:**
- 1 TRUE QUARANTINE TARGET (saw_lab G-code endpoints)
- 1 GOVERNED endpoint (mvp_router.py)
- 10+ CANDIDATE generators (need governance review)
- 4 LIBRARY modules (parse/simulate only)

---

## TRUE QUARANTINE TARGETS

### 1. Saw Lab Batch G-code Router

**Location:** `services/api/app/saw_lab/batch_gcode_router.py`

**Risk:** HIGH — Returns downloadable G-code without RMOS audit trail

**Endpoints:**
```
GET /api/saw/batch/op-toolpaths/{op_toolpaths_artifact_id}/gcode
GET /api/saw/batch/executions/{batch_execution_artifact_id}/gcode
```

**Evidence:**
- Returns `PlainTextResponse` with G-code content
- Sets `Content-Disposition: attachment` for .ngc download
- Calls `saw_lab_gcode_emit_service.export_*_gcode()`
- Does NOT create RMOS run with run_id pattern
- Does NOT hash input for provenance
- Does NOT persist output via `put_bytes_attachment()`

**Service layer:**
- `services/saw_lab_gcode_emit_service.py`
- `emit_gcode_from_moves()` has `@safety_critical` decorator but no RMOS tracking

**Why quarantined:**
The saw lab system stores artifacts in its own store (`saw_lab/store.py`) but does not follow the canonical RMOS pattern established by `mvp_router.py`. G-code is emitted directly without the audit trail that machine output requires.

---

## GOVERNED MACHINE OUTPUT

### 1. MVP DXF-to-GRBL Router (CANONICAL)

**Location:** `services/api/app/rmos/mvp_router.py`

**Endpoint:** `POST /wrap/mvp/dxf-to-grbl`

**Why governed:**
```python
# Line 59: Creates run_id
run_id = f"RUN-DXF-{uuid.uuid4().hex[:12].upper()}"

# Line 64: Hashes input
dxf_sha = hashlib.sha256(dxf_bytes).hexdigest()

# Line 66-73: Persists input
dxf_att, _ = put_bytes_attachment(dxf_bytes, kind="dxf_input", ...)
attachments.append(dxf_att)

# Line 131-136: Persists CAM plan
plan_att, _, plan_sha = put_json_attachment(plan_result, kind="cam_plan", ...)
attachments.append(plan_att)
```

This is the canonical pattern. All machine output should follow this model.

---

## CANDIDATE Generators (Not Quarantined)

These modules have `generate_gcode()` methods but are not direct API surfaces. They require governance review but are not quarantine targets because:
1. They are generator classes, not routes
2. They may be called by governed routes
3. Their risk is downstream, not direct

| Module | Path | Risk |
|--------|------|------|
| ProfileToolpathGenerator | `cam/profiling/profile_toolpath.py` | LOW |
| DrillingPeckCycleGenerator | `cam/drilling/peck_cycle.py` | LOW |
| VCarveToolpathGenerator | `cam/vcarve/toolpath.py` | LOW |
| BindingChannelGenerator | `cam/binding/channel_toolpath.py` | LOW |
| SurfaceCarvingGenerator | `cam/carving/surface_carving.py` | LOW |
| FretSlotGenerator | `cam/neck/fret_slots.py` | LOW |
| TrussRodChannelGenerator | `cam/neck/truss_rod_channel.py` | LOW |
| ProfileCarvingGenerator | `cam/neck/profile_carving.py` | LOW |
| FHoleToolpathGenerator | `cam/fhole/toolpath.py` | LOW |
| LesPaulGCodeGenerator | `generators/lespaul_gcode/generator.py` | LOW |
| AcousticBodyGenerator | `generators/acoustic_body_generator.py` | LOW |
| StratocasterBodyGenerator | `generators/stratocaster_body_generator.py` | LOW |
| NeckGCodeGenerator | `generators/neck_headstock_generator.py` | LOW |

---

## CANDIDATE Routers (Need Governance Audit)

These routes expose G-code generation. They need review to verify RMOS wiring:

| Endpoint | File | Status |
|----------|------|--------|
| `/api/cam/drilling/pattern/gcode` | `cam/routers/drilling/drill_pattern_router.py` | Needs audit |
| `/api/cam/drilling/modal/gcode` | `cam/routers/drilling/drill_modal_router.py` | Needs audit |
| `/api/cam/profiling/gcode` | `cam/routers/profiling/profile_router.py` | Needs audit |
| `/api/cam/binding/channel/gcode` | `cam/routers/binding/binding_router.py` | Needs audit |
| `/api/cam/binding/purfling/gcode` | `cam/routers/binding/binding_router.py` | Needs audit |
| `/api/cam/vcarve/production/gcode` | `cam/routers/vcarve/production_router.py` | Needs audit |
| `/api/cam/toolpath/vcarve/gcode` | `cam/routers/toolpath/vcarve_router.py` | Needs audit |
| `/api/cam/toolpath/roughing/gcode` | `cam/routers/toolpath/roughing_router.py` | Needs audit |
| `/api/cam/toolpath/biarc/gcode` | `cam/routers/toolpath/biarc_router.py` | Needs audit |
| `/api/cam/rosette/post-gcode` | `cam/routers/rosette/rosette_toolpath_router.py` | Needs audit |
| `/cam/gcode` | `api_v1/dxf_workflow.py:260` | Needs audit |

---

## LIBRARY (Not Machine Output)

These modules parse or simulate G-code but do not generate machine output:

| Module | Path | Purpose |
|--------|------|---------|
| simulator.py | `util/gcode/simulator.py` | State machine, travel calc |
| lexer.py | `util/gcode/lexer.py` | Parsing |
| types.py | `util/gcode/types.py` | Type definitions |
| geometry.py | `util/gcode/geometry.py` | Arc interpolation |

---

## Known Bugs (Not Quarantine-Scoped)

### Simulation Metrics Endpoint

**Location:** `routers/simulation_consolidated_router.py`  
**Endpoint:** `/sim/metrics`  
**Tests:** 8 xfail in test suite  
**Issue:** Schema mismatch  
**Risk:** LOW — visualization/metrics only, not machine output

This is a known bug for future cleanup, not a quarantine target.

---

## Search Methodology

Quarantine targets identified by searching for:

```
G0, G1, G2, G3, M3, M5, spindle, feedrate
postprocessor, GRBL, serial, stream, sender
.nc, .tap, .gcode
generate_gcode, to_gcode, emit_gcode
PlainTextResponse.*gcode
Content-Disposition.*attachment
```

94 files matched G-code patterns. Filtered to:
- Routes that return G-code directly
- Services that emit G-code strings
- Generators with `generate_gcode()` methods

---

## Deliverables

| Deliverable | Path | Status |
|-------------|------|--------|
| Quarantine Policy | `docs/architecture/CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md` | Created |
| This Handoff | `docs/handoffs/CAM_DEV_ORDER_4B_MACHINE_OUTPUT_QUARANTINE_2026-05-08.md` | Created |
| Manifest | `docs/architecture/cam_machine_output_manifest.json` | Created |

---

## Code Markers Added

Minimal docstring markers added to TRUE QUARANTINE TARGETS only:

- `saw_lab/batch_gcode_router.py` — Module docstring updated
- `services/saw_lab_gcode_emit_service.py` — Function docstring updated

No markers added to CANDIDATE modules (per guidance: avoid noise).

---

## What 4B Does NOT Do

- No runtime blockers
- No endpoint disabling
- No route behavior changes
- No G-code generation changes
- No postprocessor changes
- No auth or feature flags

4B is documentation and labeling only.

---

## Next Steps (4C+)

When governance gates are ready:

1. Wire saw_lab endpoints to RMOS tracking
2. Add run_id generation pattern
3. Persist G-code output via `put_bytes_attachment()`
4. Audit CANDIDATE routers for RMOS compliance
5. Promote compliant routes to GOVERNED
6. Add user confirmation before G-code download

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md` | Policy definition |
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Safety gates |
| `CAM_MODULE_CLASSIFICATION_2026-05-07.md` | Module classification |
| `CAM_GCODE_GENERATION_HANDOFF_2026-05-08.md` | Generator inventory |

---

*Completed: 2026-05-08*
