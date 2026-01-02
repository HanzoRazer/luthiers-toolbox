# Technical Debt Handoff - December 2025

**Generated:** December 21, 2025
**Status:** Manual resolution required
**Source:** Analysis of inline TODOs and stray planning files

---

## Executive Summary

10 inline TODOs remain as technical debt across the codebase. The 9 previously broken routers have been fixed. Two stray planning files should be deleted.

---

## Priority 1: Critical Stubs (Production Blockers)

These return fake/stub data and represent **safety risks** if deployed to production.

### 1.1 SAW Feasibility Scorer
- **File:** `services/api/app/rmos/api/rmos_feasibility_router.py`
- **Line:** 97
- **Current:** Returns hardcoded `GREEN` risk level
- **Needed:** Wire to real CNC Saw Labs feasibility calculators
- **Risk:** Could approve unsafe cutting operations

```python
# Line 97
TODO: Wire to real SAW feasibility scorer (CNC Saw Labs calculators).
```

### 1.2 Rosette Feasibility Scorer
- **File:** `services/api/app/rmos/api/rmos_feasibility_router.py`
- **Line:** 146
- **Current:** Returns hardcoded `GREEN` risk level
- **Needed:** Wire to rosette manufacturability scorer
- **Risk:** Could approve impossible-to-manufacture designs

```python
# Line 146
TODO: Wire to rosette manufacturability scorer.
```

### 1.3 Toolpath Generators
- **File:** `services/api/app/rmos/api/rmos_toolpaths_router.py`
- **Line:** 216, 238, 259
- **Current:** Returns empty/dummy toolpaths
- **Needed:** Wire to real CAM engines (SAW + Rosette)
- **Risk:** No actual G-code generation

```python
# Line 216
# Toolpath dispatchers (TODO: replace with real engines)

# Line 238
TODO: Wire to real CNC Saw Labs toolpath generator.

# Line 259
TODO: Wire to real rosette CAM engine.
```

---

## Priority 2: Incomplete Features (Reduced Functionality)

These features exist but don't fully work.

### 2.1 DXF LWPOLYLINE Export
- **File:** `services/api/app/toolpath/dxf_exporter.py`
- **Line:** 133
- **Current:** Uses LINE entities
- **Needed:** True LWPOLYLINE for R14/R18 DXF compatibility
- **Impact:** Older CAD software may not import correctly

```python
# Line 133
# TODO: Implement true LWPOLYLINE for R14/R18
```

### 2.2 String Spacing Calculation
- **File:** `services/api/app/rmos/context.py`
- **Lines:** 282-283
- **Current:** Returns empty arrays `[]`
- **Needed:** Compute from nut_spacing and bridge_spacing
- **Impact:** Fretboard calculations incomplete

```python
# Lines 282-283
"string_spacings_at_nut_mm": [],  # TODO: compute from nut_spacing
"string_spacings_at_bridge_mm": [],  # TODO: compute from bridge_spacing
```

### 2.3 Compare Engine
- **File:** `services/api/app/util/compare_automation_helpers.py`
- **Line:** 89
- **Current:** Stub function
- **Needed:** Wire to actual compare engine
- **Impact:** Compare Lab automation incomplete

```python
# Line 89
TODO: Wire to actual compare engine
```

### 2.4 Storage Lookup
- **File:** `services/api/app/util/compare_automation_helpers.py`
- **Line:** 41
- **Current:** Stub function
- **Needed:** Implement real baseline retrieval
- **Impact:** Cannot retrieve stored baselines

```python
# Line 41
TODO: Implement real storage lookup:
```

### 2.5 DXF Parsing
- **File:** `services/api/app/rmos/context_adapter.py`
- **Line:** 273
- **Current:** Stub parser
- **Needed:** Full DXF import support
- **Impact:** Blueprint import limited

```python
# Line 273
# TODO: Replace with actual DXF parsing
```

---

## Priority 3: Enhancements (Nice-to-Have)

System works without these but would benefit from them.

### 3.1 Blade-Specific RPM Limits
- **File:** `services/api/app/cam_core/saw_lab/saw_blade_validator.py`
- **Line:** 293
- **Current:** Generic safety limits
- **Needed:** Per-blade manufacturer specifications
- **Impact:** Enhanced validation accuracy

```python
# Line 293
# TODO: Add blade-specific RPM limits to SawBladeSpec model
```

### 3.2 Learned Overrides System
- **File:** `services/api/app/_experimental/cnc_production/learn/live_learn_ingestor.py`
- **Line:** 80
- **Current:** Not wired
- **Needed:** Connect to learned overrides store
- **Impact:** ML-based feed/speed optimization unavailable

```python
# Line 80
# TODO: Wire to actual learned overrides system when available
```

### 3.3 Tool ID Extraction
- **File:** `services/api/app/_experimental/cnc_production/learn/saw_live_learn_dashboard.py`
- **Line:** 184
- **Current:** Returns `None`
- **Needed:** Extract tool_id from run.meta
- **Impact:** Dashboard shows incomplete data

```python
# Line 184
tool_id = None  # TODO: extract from run.meta if available
```

---

## Cleanup Tasks

### Stale Comments in main.py

The following "broken router" comments (lines 114-168) are **stale** and should be removed - all 9 routers now import successfully:

```python
# Line 114: # Note: feasibility_router broken - needs rmos.context module
# Line 124: # Note: cam_preview_router broken - needs rmos.context
# Line 125: # Note: adaptive_poly_gcode_router broken - needs routers.util
# Line 138: # Note: pipeline_router broken - needs httpx
# Line 145: # Note: blueprint_router broken - needs analyzer module
# Line 168: # Note: saw_blade/gcode/validate/telemetry routers broken - need cam_core
```

**Verification:** All 9 routers import successfully (tested December 21, 2025).

### Files to Delete

| File | Reason | Status |
|------|--------|--------|
| `Based on my analysis, heres the TODO.txt` | Outdated TODO list (this handoff supersedes it) | ✅ Not found / already deleted |

---

## Quick Reference

| Priority | Count | Action |
|----------|-------|--------|
| P1 Critical | 3 | Wire real implementations before production |
| P2 Incomplete | 5 | Complete when feature is needed |
| P3 Enhancement | 3 | Implement when time permits |
| Cleanup | 7 | Remove stale comments + 1 file |

---

## File Index

| File | TODOs | Priority |
|------|-------|----------|
| `rmos/api/rmos_feasibility_router.py` | 2 | P1 |
| `rmos/api/rmos_toolpaths_router.py` | 3 | P1 |
| `toolpath/dxf_exporter.py` | 1 | P2 |
| `rmos/context.py` | 2 | P2 |
| `util/compare_automation_helpers.py` | 2 | P2 |
| `rmos/context_adapter.py` | 1 | P2 |
| `cam_core/saw_lab/saw_blade_validator.py` | 1 | P3 |
| `_experimental/cnc_production/learn/live_learn_ingestor.py` | 1 | P3 |
| `_experimental/cnc_production/learn/saw_live_learn_dashboard.py` | 1 | P3 |
| `main.py` | 6 stale comments | Cleanup |

---

*Handoff prepared by Claude Code - December 21, 2025*
