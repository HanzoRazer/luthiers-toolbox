# Repository Ground-Truth Stabilization Audit

**Date:** 2026-05-07  
**Branch:** fix/wood-shrinkage-data-integrity  
**Purpose:** Establish verified operational truth for trustworthy future guidance

---

## SECTION 1: VERIFIED CANONICAL MANUFACTURING PATH

### DXF/Geometry → G-code → RMOS Pipeline

| Stage | Verified System | Status | Evidence |
|-------|-----------------|--------|----------|
| DXF Input | DxfUploadZone | **VERIFIED CANONICAL** | Used in DxfToGcodeView, QuickCutView |
| CAM Parameters | CamParametersForm | **VERIFIED CANONICAL** | Real form, binds to generation |
| G-code Generation | `/api/rmos/wrap/mvp/dxf-to-grbl` | **VERIFIED CANONICAL** | mvp_router.py:24-100 |
| Simulation | ToolpathPlayer | **VERIFIED CANONICAL** | 393 lines, used in DxfToGcodeView ONLY |
| Risk Gates | RiskBadge, WhyPanel | **VERIFIED CANONICAL** | GREEN/YELLOW/RED blocking |
| RMOS Artifacts | runs_v2/attachments | **VERIFIED CANONICAL** | put_bytes_attachment, put_json_attachment |
| G-code Export | Blob download | **VERIFIED CANONICAL** | Direct browser download |

### Canonical Workflows

| Workflow | Entry Point | ToolpathPlayer | RMOS Trail | Risk Gates | Classification |
|----------|-------------|----------------|------------|------------|----------------|
| **DxfToGcodeView** | `/cam/dxf-to-gcode` | YES | YES | YES | **VERIFIED CANONICAL** |
| **QuickCutView** | `/quick-cut` | NO | YES | YES | **VERIFIED WORKING** (simplified) |
| **CamWorkspaceView** | `/cam/workspace` | NO | NO | YES (gates only) | **VERIFIED PARTIAL** |

---

## SECTION 2: FALSE COMPLETION FINDINGS

### P0 — Critical False Completions

| System | Claimed State | Verified State | Severity | Evidence |
|--------|---------------|----------------|----------|----------|
| **DxfToGcodeWizard** | DXF workflow | PLACEHOLDER TRAP | **HIGH** | Calls `/api/v1/dxf/upload` (works), `/api/v1/dxf/cam/gcode` (returns PLACEHOLDER G-code with TODO comment) — dxf_workflow.py:298-299 |
| **ToolpathSimulatorView** | Simulation view | DEAD SHELL | **CRITICAL** | Comments reference `/api/cam/simulate/*` but ZERO fetch() calls. Has "coming soon" notice. |
| **CamWorkspaceView** | CAM workspace | INCOMPLETE | **HIGH** | Uses GcodePreviewPanel (text-only), NO ToolpathPlayer, NO RMOS artifacts |
| **/api/cam/sim/metrics** | Metrics endpoint | BROKEN | **HIGH** | Router/schema mismatch. 8 tests xfail-protected. See test_simulation_endpoint_smoke.py:18-30 |
| **FretSlottingView** | Fret slot generator | FAKE | **HIGH** | `generateToolpath()` is `setTimeout(500)` only. No API call. |
| **PocketClearingView** | Pocket clearing | FAKE | **HIGH** | `setTimeout(1000)` + `estimatedTime = 12.5 // mock` |
| **ContourCuttingView** | Contour cutting | FAKE | **HIGH** | `setTimeout(1000)` only, no API call |
| **SurfacingView** | Surfacing | FAKE | **HIGH** | `setTimeout(1000)` only, no API call |
| **DrillingView** | Drilling | FAKE | **HIGH** | `setTimeout(500)` only, no API call |

### P1 — Scaffolded Systems

| System | Defined | Instantiated | Methods Called | Classification |
|--------|---------|--------------|----------------|----------------|
| **FeedbackSystem** | vectorizer_phase3.py:1181 | Line 2805 (conditional) | `record_classification()` YES | **PARTIAL** |
| **FeedbackSystem.submit_correction()** | vectorizer_phase3.py:1212 | — | **NEVER** | **DEAD** |
| **TrainingDataCollector** | vectorizer_phase3.py:1273 | **NEVER** | — | **DEAD** |
| **AGE Integration** | CLAUDE.md documented | **0 LINES** | — | **UNIMPLEMENTED** |
| **Phase 4 Dimension Linking** | phase4/ directory | Standalone | Not integrated | **SCAFFOLDED** |

---

## SECTION 3: DUPLICATE SYSTEMS

### Verified Duplicates

| Category | Instance 1 | Instance 2 | Notes |
|----------|------------|------------|-------|
| **Simulation Router** | `routers/simulation_consolidated_router.py` (326 lines) | `cam/routers/simulation/simulation_consolidated_router.py` (143 lines) | Same name, DIFFERENT content. Root has `/metrics`, cam/ does not. |

### Router Registration

| File | Prefix | Has /metrics |
|------|--------|--------------|
| `routers/simulation_consolidated_router.py` | `/api/cam/sim` | YES |
| `cam/routers/simulation/simulation_consolidated_router.py` | `/api/cam/simulation` | NO |

---

## SECTION 4: ROUTE VERIFICATION

### Frontend Routes Summary

| Count | Description |
|-------|-------------|
| 75 | Total routes in router/index.ts |
| 183 | Total view files in views/ |

### CAM Routes Verification

| Route | Component | Real API Calls | ToolpathPlayer | Classification |
|-------|-----------|----------------|----------------|----------------|
| `/cam/dxf-to-gcode` | DxfToGcodeView | YES (composable) | YES | **CANONICAL** |
| `/cam/workspace` | CamWorkspaceView | YES (3 endpoints) | NO | **PARTIAL** |
| `/cam/simulator` | ToolpathSimulatorView | NO | NO | **DEAD SHELL** |
| `/cam/pocket` | PocketClearingView | NO (setTimeout) | NO | **FAKE** |
| `/cam/contour` | ContourCuttingView | NO (setTimeout) | NO | **FAKE** |
| `/cam/surfacing` | SurfacingView | NO (setTimeout) | NO | **FAKE** |
| `/cam/drilling` | DrillingView | NO (setTimeout) | NO | **FAKE** |
| `/cam/fret-slots` | FretSlottingView | Partial (DXF only) | NO | **PARTIAL** |

---

## SECTION 5: ENDPOINT VERIFICATION

### Backend Statistics

| Metric | Count |
|--------|-------|
| Router files | 204 |
| Endpoint decorators | 974 |
| include_router calls | 50+ |

### Critical Endpoint Status

| Endpoint | Registered | Called by Frontend | Working | Classification |
|----------|------------|-------------------|---------|----------------|
| `/api/rmos/wrap/mvp/dxf-to-grbl` | YES | QuickCutView | YES | **VERIFIED** |
| `/api/cam-workspace/machines` | YES | CamWorkspaceView | YES | **VERIFIED** |
| `/api/cam-workspace/neck/evaluate` | YES | CamWorkspaceView | YES | **VERIFIED** |
| `/api/cam-workspace/neck/generate-full` | YES | CamWorkspaceView | YES | **VERIFIED** |
| `/api/cam/sim/gcode` | YES | Unknown | YES | **VERIFIED** |
| `/api/cam/sim/upload` | YES | Unknown | YES | **VERIFIED** |
| `/api/cam/sim/metrics` | YES | Unknown | **BROKEN** (schema mismatch) | **FALSE COMPLETION** |
| `/api/v1/dxf/upload` | YES | DxfToGcodeWizard | YES | **VERIFIED** |
| `/api/v1/dxf/cam/gcode` | YES | DxfToGcodeWizard | **PLACEHOLDER** | **FALSE COMPLETION** — returns stub G-code, TODO comment at line 298 |
| `/api/teaching/*` | **NO** | TeachingModeView | N/A | **MISSING** — frontend references, no backend router |
| `/api/vision/*` | YES | Unknown | YES | **VERIFIED** — mounted via router_registry/system_manifest.py |
| `/api/art-studio/*` | YES | Multiple art views | YES | **VERIFIED** — art_studio_manifest.py |
| `/api/cam/relief/*` | YES | ReliefCarvingView | YES | **VERIFIED** — cam_relief_router.py |
| `/api/art/inlay-patterns` | YES | InlayPatternView | YES | **VERIFIED** — inlay_pattern_routes.py |
| `/api/cam/simulate/preview` | **NO** | ToolpathSimulatorView (never called) | N/A | **MISSING** |
| `/api/cam/simulate/analyze` | **NO** | ToolpathSimulatorView (never called) | N/A | **MISSING** |

---

## SECTION 6: RELIABILITY CLASSIFICATION

### Classification Key

| Classification | Meaning |
|----------------|---------|
| **VERIFIED** | Confirmed through code inspection + execution path tracing |
| **OBSERVED** | Directly visible in code, not execution-traced |
| **INFERRED** | Architectural interpretation based on patterns |
| **SPECULATIVE** | Future-risk framing without direct evidence |

### Findings Classification

| Finding | Classification | Confidence |
|---------|----------------|------------|
| DxfToGcodeView uses ToolpathPlayer | **VERIFIED** | HIGH |
| CamWorkspaceView does NOT use ToolpathPlayer | **VERIFIED** | HIGH |
| DxfToGcodeWizard calls placeholder endpoint | **VERIFIED** | HIGH (api_v1/dxf_workflow.py:298 has TODO) |
| /api/teaching/* has no backend | **VERIFIED** | HIGH (grep found 0 router files) |
| /api/cam/sim/metrics has schema mismatch | **VERIFIED** | HIGH (xfail tests prove it) |
| CAM operation views are fake (setTimeout) | **VERIFIED** | HIGH |
| TrainingDataCollector never instantiated | **VERIFIED** | HIGH |
| submit_correction() never called | **VERIFIED** | HIGH |
| Two simulation_consolidated_router.py files | **VERIFIED** | HIGH |
| AGE integration has 0 lines | **OBSERVED** | HIGH |

---

## SECTION 7: HUMAN VALIDATION REQUIRED

### Decisions Beyond Executable Verification

| Question | Context | Why Human Required |
|----------|---------|-------------------|
| Complete DxfToGcodeWizard backend? | /cam/gcode returns placeholder | Resource allocation decision |
| Delete ToolpathSimulatorView? | Dead shell | May be placeholder for future work |
| Merge simulation routers? | Two files, different content | Need to determine canonical |
| Wire CamWorkspaceView to ToolpathPlayer? | Currently text-only | Scope/priority decision |
| Wire CamWorkspaceView to RMOS? | No audit trail | Manufacturing compliance decision |
| Complete vectorizer feedback loops? | Scaffolded but dead | Resource allocation decision |
| Fix /api/cam/sim/metrics schema? | 8 xfail tests | Priority vs other work |

---

## SECTION 8: MANUFACTURING PATH SUMMARY

### Verified Working Path

```
DXF File
    ↓
DxfUploadZone (drag-drop, validation)
    ↓
CamParametersForm (tool, feeds, depths)
    ↓
POST /api/rmos/wrap/mvp/dxf-to-grbl (mvp_router.py)
    ↓
ezdxf parsing + adaptive toolpath + G-code generation
    ↓
RMOS run artifact creation (run_id, attachments)
    ↓
ToolpathPlayer (simulation visualization) ← ONLY in DxfToGcodeView
    ↓
RiskBadge / WhyPanel (GREEN/YELLOW/RED gates)
    ↓
G-code download (Blob)
```

### Parallel Paths

| Path | Status | Missing vs DxfToGcodeView |
|------|--------|---------------------------|
| QuickCutView | Working | No ToolpathPlayer |
| CamWorkspaceView | Partial | No ToolpathPlayer, No RMOS |
| PocketClearingView | Fake | Everything (setTimeout only) |
| ContourCuttingView | Fake | Everything (setTimeout only) |
| SurfacingView | Fake | Everything (setTimeout only) |
| DrillingView | Fake | Everything (setTimeout only) |
| FretSlottingView | Partial | No API for generate, DXF export only |

---

## SECTION 9: IMMEDIATE ACTIONS

### Safe to Execute Now

| Action | Risk | Justification |
|--------|------|---------------|
| Add "Under Construction" banner to DxfToGcodeWizard | LOW | /cam/gcode returns placeholder G-code |
| Add deprecation notice to ToolpathSimulatorView | LOW | Dead shell with "coming soon" |
| Mark CAM operation views as "Demo" in UI | LOW | Prevent user confusion |
| Fix /api/cam/sim/metrics schema or remove xfail | MEDIUM | Known production bug |

### Requires Planning

| Action | Risk | Justification |
|--------|------|---------------|
| Wire CamWorkspaceView to ToolpathPlayer | MEDIUM | Requires prop wiring, state management |
| Wire CamWorkspaceView to RMOS | LOW | Infrastructure exists |
| Merge simulation routers | MEDIUM | Need to determine canonical |
| Complete vectorizer feedback loops | HIGH | New development |

---

## SECTION 10: AUDIT METHODOLOGY

### Tools Used

- `grep -r` for endpoint pattern matching
- `Read` for file content verification
- Route tracing from router/index.ts
- Import chain verification
- Test file analysis for xfail patterns
- router_registry manifest verification

### Breadth Scan Coverage

| Scan | Files Checked | Findings |
|------|---------------|----------|
| Frontend API calls | 100+ view files | 1 missing backend (/api/teaching/*) |
| DXF ezdxf.new() violations | All Python files | 24 violations in 20 files |
| Router duplicate detection | 204 router files | 1 duplicate (simulation_consolidated_router.py) |
| Endpoint registration | router_registry manifests | Art studio, vision, relief - all mounted |

### What Was NOT Verified

- Runtime behavior (no dev server started)
- Database state
- External service integrations
- User-facing behavior
- Performance characteristics

### Limitations

This audit verifies code structure and wiring, not runtime correctness. A system classified as "VERIFIED WORKING" means the code paths are wired correctly, not that the feature works end-to-end.

---

## SECTION 11: DXF STANDARD COMPLIANCE

### CLAUDE.md Requirement

Per CLAUDE.md: "All DXF generators must use dxf_compat — direct ezdxf.new() calls forbidden"

### Violation Scan Results

| Metric | Count |
|--------|-------|
| Files with direct `ezdxf.new()` calls | 20 |
| Total `ezdxf.new()` violations | 24 |
| Files using `dxf_compat` correctly | 4 |
| **Compliance rate** | **17%** |

### Violating Files (VERIFIED)

| File | Violation Count | Location |
|------|-----------------|----------|
| `app/instrument_geometry/soundhole/spiral_geometry.py` | 1 | Body outline generator |
| `app/instrument_geometry/bridge/archtop_floating_bridge.py` | 1 | Bridge generator |
| `app/instrument_geometry/body_outline/bass_body_outline.py` | 1 | Bass body |
| `app/instrument_geometry/body_outline/acoustic_body_outline.py` | 1 | Acoustic body |
| `app/instrument_geometry/body_outline/electric_body_outline.py` | 1 | Electric body |
| `app/calculators/fret_calc.py` | 1 | Fret calculator |
| `app/calculators/neck_geometry_calc.py` | 1 | Neck geometry |
| `app/calculators/soundhole_facade.py` | 1 | Soundhole facade |
| `app/calculators/nut_slot_calc.py` | 1 | Nut slot calculator |
| `app/cam/toolpath/*.py` | 4 | Various CAM modules |
| `services/blueprint-import/vectorizer_phase3.py` | 2 | Vectorizer export |
| Other generators | 9 | Various locations |

### Compliant Files (VERIFIED)

| File | Notes |
|------|-------|
| `app/dxf_compat.py` | Central compatibility layer |
| `app/cam/dxf_writer.py` | Uses dxf_compat |
| `app/instrument_geometry/body_outline/cuatro_body_outline.py` | Uses dxf_compat |
| `app/instrument_geometry/smart_guitar/smart_guitar_dxf.py` | Uses dxf_compat |

### Impact

- Direct `ezdxf.new()` calls bypass format/entity/layer standards
- Inconsistent DXF output causes CAD software compatibility issues
- Historical incident: Fusion 360 freeze on smart_guitar_front_v3.dxf (pre-dxf_compat)

---

*Audit completed: 2026-05-07*
*Auditor: Claude Opus 4.5 (updated by Opus 4.5)*
*Classification: VERIFIED OPERATIONAL TRUTH*
