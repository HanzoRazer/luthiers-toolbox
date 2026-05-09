# CAM Candidate Evaluation — 2026-05-09

**Date:** 2026-05-09  
**Evaluator:** Claude (CAM Dev Order 5A)  
**Scope:** All CANDIDATE CAM module categories

---

## Executive Summary

8 candidate categories evaluated using the CAM Module Readiness Scorecard.

| Category | Score | Promotion Target | Primary Blocker |
|----------|-------|------------------|-----------------|
| Profiling | 67/100 | GOVERNED PREVIEW | Coordinate docs incomplete |
| Drilling | 72/100 | GOVERNED PREVIEW | Preview endpoint missing |
| Binding | 62/100 | GOVERNED PREVIEW | Tests sparse |
| Rosette | 70/100 | GOVERNED PREVIEW | Postprocessor integration partial |
| V-Carve | 68/100 | GOVERNED PREVIEW | Coordinate docs missing |
| Fret Slot CAM | 75/100 | GOVERNED EXPORT | RMOS integration incomplete |
| Fan Fret CAM | 70/100 | GOVERNED PREVIEW | Dependent on fret_slots_cam |
| Saw Lab | N/A | QUARANTINED | Machine output without governance |

---

## Category: Profiling

**Module:** `cam/profiling/`  
**Primary Generator:** `ProfileToolpathGenerator` in `profile_toolpath.py`  
**Category:** Export Generator

### Scored Criteria

| Criteria | Score | Evidence |
|----------|-------|----------|
| Coordinate Documentation | 8/15 | Features documented but no explicit origin/Z-zero |
| Tests | 10/20 | Incidental coverage via integration tests |
| Safety Gates | 15/20 | @safety_critical present, input validation |
| Preview Support | 10/15 | Toolpath points available but no preview endpoint |
| Provenance Clarity | 7/10 | Route exists, generator identifiable |
| Export Separation | 17/20 | G-code in separate method, postprocessor-ready |

**Total: 67/100**

### Informational Metrics

| Metric | Level | Notes |
|--------|-------|-------|
| RMOS Readiness | Low | No RMOS integration |
| Frontend/API Readiness | Medium | Pydantic config exists |
| Route Provenance Maturity | Medium | `/api/cam/profiling/gcode` exists |

### Strengths

- Well-structured ProfileConfig dataclass
- Holding tabs, lead-in/out, climb milling all implemented
- Safe-Z and retract-Z properly handled

### Blocking Issues

- [ ] Coordinate system origin not explicitly documented
- [ ] Z-zero semantics not documented
- [ ] No dedicated test file

### Promotion Target

GOVERNED PREVIEW (score 67 meets 60 threshold)

### Recommended Actions

1. Add coordinate system documentation to module docstring
2. Create dedicated test file with boundary conditions
3. Add preview endpoint for toolpath visualization

---

## Category: Drilling

**Module:** `cam/drilling/`  
**Primary Generator:** `DrillingPeckCycleGenerator` in `peck_cycle.py`  
**Category:** Export Generator

### Scored Criteria

| Criteria | Score | Evidence |
|----------|-------|----------|
| Coordinate Documentation | 10/15 | G83 format documented, Z/R semantics clear |
| Tests | 15/20 | `test_cam_drilling_smoke.py` with 3 tests |
| Safety Gates | 15/20 | @safety_critical present, DrillConfig validation |
| Preview Support | 10/15 | DrillResult includes metadata but no preview endpoint |
| Provenance Clarity | 7/10 | `/api/cam/drilling/pattern/gcode` exists |
| Export Separation | 15/20 | G-code generation in result, postprocessor-ready |

**Total: 72/100**

### Informational Metrics

| Metric | Level | Notes |
|--------|-------|-------|
| RMOS Readiness | Low | No RMOS integration |
| Frontend/API Readiness | Medium | DrillConfig/DrillResult dataclasses |
| Route Provenance Maturity | High | Route in manifest |

### Strengths

- Clear G83 peck drilling documentation
- Configurable peck depth, dwell, canned cycle option
- Estimated time calculation included

### Blocking Issues

- [ ] Preview endpoint missing
- [ ] Coordinate origin not explicitly documented

### Promotion Target

GOVERNED PREVIEW (score 72 meets 60 threshold)

### Recommended Actions

1. Add explicit coordinate origin documentation
2. Create preview endpoint returning hole positions as JSON
3. Add RMOS integration for full export path

---

## Category: Binding

**Module:** `cam/binding/`  
**Primary Generator:** `BindingChannel` in `channel_toolpath.py`  
**Category:** Export Generator

### Scored Criteria

| Criteria | Score | Evidence |
|----------|-------|----------|
| Coordinate Documentation | 8/15 | Safe-Z documented but origin implicit |
| Tests | 10/20 | `test_binding_geometry.py` exists |
| Safety Gates | 15/20 | @safety_critical present, BindingConfig validation |
| Preview Support | 10/15 | BindingResult includes toolpath_points |
| Provenance Clarity | 7/10 | `/api/cam/binding/channel/gcode` exists |
| Export Separation | 12/20 | G-code generation coupled with channel logic |

**Total: 62/100**

### Informational Metrics

| Metric | Level | Notes |
|--------|-------|-------|
| RMOS Readiness | Low | No RMOS integration |
| Frontend/API Readiness | Medium | BindingConfig/BindingResult dataclasses |
| Route Provenance Maturity | Medium | Route in manifest |

### Strengths

- Multi-pass auto-detection for wide channels
- Climb milling option for clean edge
- Resolves multiple GAPs (OM-GAP-03, OM-GAP-04, OM-PURF-01, BEN-GAP-01)

### Blocking Issues

- [ ] Coordinate origin not documented
- [ ] Export separation needs improvement
- [ ] Tests could be more comprehensive

### Promotion Target

GOVERNED PREVIEW (score 62 meets 60 threshold)

### Recommended Actions

1. Document coordinate system (body outline relative)
2. Separate G-code generation into postprocessor-compatible function
3. Add dedicated tests for channel depth validation

---

## Category: Rosette

**Module:** `cam/rosette/`  
**Primary Generator:** `generate_gcode_from_toolpaths()` in `cnc/cnc_gcode_exporter.py`  
**Category:** Export Generator

### Scored Criteria

| Criteria | Score | Evidence |
|----------|-------|----------|
| Coordinate Documentation | 10/15 | Machine coordinates mentioned, safe_z documented |
| Tests | 15/20 | `test_golden_rosette_geometry.py`, `test_rosette_cam_bridge.py` |
| Safety Gates | 15/20 | @safety_critical present, cnc_safety_validator.py exists |
| Preview Support | 10/15 | Pattern geometry available but preview scattered |
| Provenance Clarity | 7/10 | `/api/cam/rosette/post-gcode` exists |
| Export Separation | 13/20 | MachineProfile enum (GRBL/FANUC) but incomplete |

**Total: 70/100**

### Informational Metrics

| Metric | Level | Notes |
|--------|-------|-------|
| RMOS Readiness | Medium | Some RMOS integration via rosette_cam_router |
| Frontend/API Readiness | High | Extensive schemas in pattern_schemas.py |
| Route Provenance Maturity | High | Route in manifest |

### Strengths

- MachineProfile enum for GRBL vs FANUC
- cnc_safety_validator.py for validation
- Large, feature-rich module (40+ files)
- Pattern geometry well-developed

### Blocking Issues

- [ ] Coordinate origin not explicitly documented
- [ ] Postprocessor integration partial (inline profile switching)
- [ ] Preview consolidation needed

### Promotion Target

GOVERNED PREVIEW (score 70 meets 60 threshold)

### Recommended Actions

1. Document coordinate system (soundhole center relative)
2. Complete postprocessor integration via rmos/posts/
3. Add consolidated preview endpoint

---

## Category: V-Carve

**Module:** `cam/vcarve/`  
**Primary Generator:** `VCarveToolpathGenerator` in `toolpath.py`  
**Category:** Export Generator

### Scored Criteria

| Criteria | Score | Evidence |
|----------|-------|----------|
| Coordinate Documentation | 8/15 | Safe-Z documented but origin implicit |
| Tests | 10/20 | `test_relief_vcarve_endpoint_smoke.py` |
| Safety Gates | 15/20 | @safety_critical present, chipload validation |
| Preview Support | 10/15 | Toolpath data available |
| Provenance Clarity | 7/10 | `/api/cam/vcarve/production/gcode` exists |
| Export Separation | 18/20 | Good separation, chipload module |

**Total: 68/100**

### Informational Metrics

| Metric | Level | Notes |
|--------|-------|-------|
| RMOS Readiness | Low | No RMOS integration |
| Frontend/API Readiness | High | VCarveConfig dataclass |
| Route Provenance Maturity | High | Route in manifest |

### Strengths

- Chipload-based feed rate calculation
- Corner slowdown for quality
- Multi-pass stepdown for deep cuts
- V-bit geometry calculations

### Blocking Issues

- [ ] Coordinate origin not documented
- [ ] Dedicated test file needed

### Promotion Target

GOVERNED PREVIEW (score 68 meets 60 threshold)

### Recommended Actions

1. Document coordinate system origin
2. Create dedicated test file
3. Add preview endpoint for toolpath visualization

---

## Category: Fret Slot CAM

**Module:** `calculators/fret_slots_cam.py`  
**Primary Function:** `compute_fret_slot_toolpath()`, `generate_gcode()`  
**Category:** Export Generator

### Scored Criteria

| Criteria | Score | Evidence |
|----------|-------|----------|
| Coordinate Documentation | 12/15 | FretboardEcosphere provides context, partial docs |
| Tests | 17/20 | `test_cam_fret_slots_preview_smoke.py`, `test_cam_fret_slots_export.py`, `test_fret_slots_cam_guard.py` |
| Safety Gates | 15/20 | @safety_critical present, validation via ecosphere |
| Preview Support | 13/15 | Preview endpoint exists |
| Provenance Clarity | 8/10 | Clear route to generator |
| Export Separation | 10/20 | G-code generation inline, needs postprocessor |

**Total: 75/100**

### Informational Metrics

| Metric | Level | Notes |
|--------|-------|-------|
| RMOS Readiness | Medium | RmosContext parameter but incomplete integration |
| Frontend/API Readiness | High | Integrated with FretboardEcosphere |
| Route Provenance Maturity | High | `/api/cam/fret_slots/*` routes exist |

### Strengths

- Integrated with FretboardEcosphere (canonical fret geometry)
- Radius-blended depth calculation
- DXF + G-code output bundle
- Good test coverage

### Blocking Issues

- [ ] G-code generation not via postprocessor
- [ ] RMOS integration incomplete
- [ ] Coordinate docs could be more explicit

### Promotion Target

GOVERNED EXPORT (score 75 meets threshold, export separation at 10 blocks full promotion)

### Recommended Actions

1. Refactor generate_gcode() to use postprocessor interface
2. Complete RMOS integration with run_id pattern
3. Document coordinate system explicitly

---

## Category: Fan Fret CAM

**Module:** `calculators/fret_slots_fan_cam.py`  
**Primary Function:** `generate_fan_fret_cam()`  
**Category:** Export Generator

### Scored Criteria

| Criteria | Score | Evidence |
|----------|-------|----------|
| Coordinate Documentation | 10/15 | Inherits from fret_slots_cam |
| Tests | 15/20 | Tested via fret_slots tests |
| Safety Gates | 15/20 | @safety_critical, validate_fan_fret_geometry() |
| Preview Support | 10/15 | Via fret_slots_cam |
| Provenance Clarity | 7/10 | Route via fret_slots routes |
| Export Separation | 13/20 | Delegates to fret_slots_cam |

**Total: 70/100**

### Informational Metrics

| Metric | Level | Notes |
|--------|-------|-------|
| RMOS Readiness | Medium | Via fret_slots_cam |
| Frontend/API Readiness | High | FretboardSpec integration |
| Route Provenance Maturity | Medium | Dependent on parent module |

### Strengths

- Fan-fret geometry validation
- Perpendicular fret support
- Delegates properly to fret_slots_cam infrastructure

### Blocking Issues

- [ ] Dependent on fret_slots_cam promotion
- [ ] Coordinate docs inherited, not explicit

### Promotion Target

GOVERNED PREVIEW (blocked by fret_slots_cam dependency)

### Recommended Actions

1. Promote fret_slots_cam first
2. Add explicit coordinate documentation
3. Ensure tests cover fan-fret-specific edge cases

---

## Category: Saw Lab

**Module:** `saw_lab/`  
**Status:** QUARANTINED  
**Category:** Export Generator (with machine output)

### Quarantine Status

**PRIMARY BLOCKER:** `batch_gcode_router.py` produces machine-ready G-code without RMOS governance.

This category cannot be scored for normal promotion because:
1. Machine output endpoints exist without governance
2. G-code download available without audit trail
3. No run_id pattern for provenance

### Subsystem Analysis

| Subsystem | Risk | Notes |
|-----------|------|-------|
| `risk_evaluator.py` | LOW | Safety scoring only, no machine output |
| `path_planner.py` | LOW | Path planning only, no machine output |
| `toolpath_builder.py` | MEDIUM | Builds G-code, used by quarantined endpoints |
| `batch_gcode_router.py` | HIGH | Quarantined — machine output without governance |
| `store.py` | LOW | Artifact storage, not machine output |
| `calculators/` | LOW | Physics calculations, no machine output |

### Candidate Subsystems (Safe for Future Promotion)

1. `risk_evaluator.py` — Could become GOVERNED PREVIEW as risk scoring service
2. `path_planner.py` — Could become GOVERNED PREVIEW as planning service
3. `calculators/` — Could become LIBRARY as physics utilities

### Quarantine Release Requirements

Before saw_lab can be promoted:

1. Split machine-output endpoints from preview/analysis services
2. Wire G-code endpoints to RMOS with run_id pattern
3. Add input/output hashing for provenance
4. Add user confirmation before G-code download
5. Document coordinate system for all operations

### Promotion Target

QUARANTINE → SPLIT → CANDIDATE (subsystems) → GOVERNED PREVIEW

### Recommended Actions

1. Keep quarantine status until split complete
2. Identify candidate subsystems for separate promotion
3. Create governance plan for machine-output endpoints

---

## Summary: Promotion Readiness

| Category | Score | Ready for GOVERNED PREVIEW? | Ready for GOVERNED EXPORT? |
|----------|-------|----------------------------|---------------------------|
| Profiling | 67 | ✓ (with docs fix) | ✗ |
| Drilling | 72 | ✓ (with preview) | ✗ |
| Binding | 62 | ✓ (with docs fix) | ✗ |
| Rosette | 70 | ✓ (with docs fix) | ✗ |
| V-Carve | 68 | ✓ (with docs fix) | ✗ |
| Fret Slot CAM | 75 | ✓ | ✓ (with postprocessor) |
| Fan Fret CAM | 70 | ✓ (after fret_slots_cam) | ✗ |
| Saw Lab | N/A | ✗ QUARANTINED | ✗ QUARANTINED |

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_PROMOTION_FRAMEWORK.md` | Promotion stages |
| `CAM_MODULE_READINESS_SCORECARD.md` | Scoring criteria |
| `CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md` | Saw lab quarantine |
| `cam_candidate_registry.json` | Machine-readable registry |

---

*Evaluation completed: 2026-05-09*
