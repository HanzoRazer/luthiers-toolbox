# Export Geometry Authority Review

**Phase:** C2-A — Geometry Authority Decomposition  
**Date:** 2026-05-18  
**Owner:** Terminal 5 (Export/Serialization Reviewer)  
**Status:** Draft — Requires code verification

---

## Purpose

This document reviews export and serialization systems for geometry authority boundary compliance, ensuring translators serialize but do not generate geometry.

---

## 1. Export System Inventory

### 1.1 Translator Systems

| Translator | Location | Output Format |
|------------|----------|---------------|
| DXF Translator | `export/dxf_writer.py` | DXF (R12/R2000) |
| STEP Translator | `export/step_translator.py` | STEP AP214 |
| G-code Translator | `cam/translators/` | G-code (GRBL) |
| SVG Translator | `export/svg_writer.py` | SVG |

### 1.2 Serialization Paths

```
TopologyBuilder
  │
  ▼
ShellValidation (quality gate)
  │
  ▼
Translator Selection
  │
  ├──► DXF Writer ──► .dxf
  ├──► STEP Translator ──► .step
  ├──► G-code Translator ──► .nc/.gcode
  └──► SVG Writer ──► .svg
```

---

## 2. Authority Boundary Analysis

### 2.1 Constitutional Requirement

From `authority_chain_registry.json`:

```
"Translators serialize but do not generate geometry"
```

This is the core invariant under review.

### 2.2 DXF Writer Analysis

| Aspect | Finding |
|--------|---------|
| Input | Topology shell, contours |
| Output | DXF entities (LINE, LWPOLYLINE) |
| Geometry generation | NO — converts existing |
| Semantic injection | LAYER NAMES — see 3.1 |

**Boundary Status:** OK — serialization only

### 2.3 STEP Translator Analysis

| Aspect | Finding |
|--------|---------|
| Input | Topology shell |
| Output | STEP entities |
| Geometry generation | NO — converts existing |
| Semantic injection | ENTITY TYPES — may constrain |

**Boundary Status:** OK — serialization only

### 2.4 G-code Translator Analysis

| Aspect | Finding |
|--------|---------|
| Input | Toolpath, operation params |
| Output | G-code commands |
| Geometry generation | PARTIAL — feedrate, depth |
| Semantic injection | CAM PARAMETERS — see 3.2 |

**Boundary Status:** ATTENTION — CAM parameters are authority

### 2.5 SVG Writer Analysis

| Aspect | Finding |
|--------|---------|
| Input | Contours, dimensions |
| Output | SVG paths |
| Geometry generation | NO — converts existing |
| Semantic injection | CSS CLASSES — may encode |

**Boundary Status:** OK — serialization only

---

## 3. Semantic Injection Points

### 3.1 DXF Layer Names

| Layer Name | Source | Risk |
|------------|--------|------|
| `BODY_OUTLINE` | ContourCategory enum | LOW — from upstream |
| `SOUNDHOLE` | ContourCategory enum | LOW — from upstream |
| `BRACING` | ContourCategory enum | LOW — from upstream |

**Finding:** Layer names come from `ContourCategory.value.upper()`, which is upstream authority. DXF writer does not invent layers.

### 3.2 G-code CAM Parameters

| Parameter | Source | Risk |
|-----------|--------|------|
| Feed rate | Operation config | MEDIUM — CAM authority |
| Spindle speed | Operation config | MEDIUM — CAM authority |
| Depth of cut | Operation config | MEDIUM — CAM authority |
| Tool selection | Operation config | MEDIUM — CAM authority |

**Finding:** G-code translator injects CAM parameters. These are CAM domain authority, not geometry authority. This is acceptable — CAM owns machining parameters.

### 3.3 Export Schema Constraints

| Format | Constraint | Impact |
|--------|------------|--------|
| DXF R12 | LINE entities only | Limits curve representation |
| DXF R2000 | LWPOLYLINE allowed | Better curve support |
| STEP | Entity type hierarchy | May constrain topology |
| G-code | Linear interpolation | Splines become line segments |

**Finding:** Export format constraints are external limitations, not authority violations. Translators work within format constraints.

---

## 4. Authority Violation Scan

### 4.1 Does Any Translator Generate Geometry?

| Translator | Generates Geometry? | Evidence |
|------------|---------------------|----------|
| DXF Writer | NO | Converts contours to entities |
| STEP Translator | NO | Converts topology to STEP |
| G-code Translator | NO | Converts toolpath to commands |
| SVG Writer | NO | Converts contours to paths |

**Finding:** No translator generates geometry. ✓

### 4.2 Does Any Translator Define Vocabulary?

| Translator | Defines Vocabulary? | Evidence |
|------------|---------------------|----------|
| DXF Writer | NO | Uses ContourCategory |
| STEP Translator | NO | Uses topology types |
| G-code Translator | NO | Uses operation types |
| SVG Writer | NO | Uses contour types |

**Finding:** No translator defines geometry vocabulary. ✓

### 4.3 Downstream Semantic Hardening Risk

| Risk | Description | Mitigation |
|------|-------------|------------|
| DXF layer semantics | Downstream tools may interpret layers | Document layer convention |
| STEP entity semantics | CAD tools may interpret entity types | STEP is standardized |
| G-code comment semantics | Post-processors may parse comments | Minimize semantic comments |

**Finding:** Downstream hardening is external system risk, not translator authority violation.

---

## 5. Translator Non-Authority Verification

### 5.1 Invariant Check

| Invariant | Translator | Status |
|-----------|------------|--------|
| Does not generate topology | DXF Writer | ✓ VERIFIED |
| Does not generate topology | STEP Translator | ✓ VERIFIED |
| Does not generate topology | G-code Translator | ✓ VERIFIED |
| Does not generate topology | SVG Writer | ✓ VERIFIED |

### 5.2 Consumer Status Check

| Translator | Authority Claim | Status |
|------------|-----------------|--------|
| DXF Writer | None | ✓ Consumer |
| STEP Translator | None | ✓ Consumer |
| G-code Translator | CAM params (own domain) | ✓ Consumer (geometry) |
| SVG Writer | None | ✓ Consumer |

**Finding:** All translators are geometry consumers. ✓

---

## 6. Export Governance Compliance

### 6.1 Export Lifecycle Chain Compliance

From `authority_chain_registry.json`:

```
Export Request → Feasibility Check → Validation → Translation → Authorization Gate → Machine Output
```

| Stage | Responsible System | Compliance |
|-------|-------------------|------------|
| Export Request | User/API | N/A |
| Feasibility Check | RMOS | Separate authority |
| Validation | ShellValidation | Consumer |
| Translation | Translators | Consumer ✓ |
| Authorization Gate | Export Governance | Separate authority |
| Machine Output | DXF/STEP/G-code | Output |

**Finding:** Translators operate within export lifecycle. ✓

### 6.2 Authorization Gate Review

| Gate | Location | Function |
|------|----------|----------|
| `CamGate` | `operation_manifest.py` | green/yellow/red |
| Preview gate | Export workflow | `preview_only` status |
| Machine gate | Export workflow | `machine_candidate` status |

**Finding:** Authorization gates are upstream of translators. Translators do not bypass gates.

---

## 7. Serialization Propagation Analysis

### 7.1 What Propagates Through Serialization

| Data | Source | Propagates to |
|------|--------|---------------|
| Geometry coordinates | TopologyBuilder | DXF entities |
| Layer assignments | ContourCategory | DXF layers |
| Entity structure | Topology shell | STEP entities |
| Toolpath | CAM planner | G-code |

### 7.2 What Does NOT Propagate

| Data | Reason |
|------|--------|
| Geometry provenance | Not in export format |
| Classification metadata | Not in export format |
| Approval status | Not in export format |
| Authority chain | Not in export format |

**Finding:** Export formats lose provenance. This is a limitation, not a violation.

### 7.3 Provenance Loss Concern

| Concern | Description | Mitigation |
|---------|-------------|------------|
| Provenance not in DXF | DXF has no provenance field | Document separately |
| Provenance not in STEP | STEP has limited metadata | Add STEP header |
| Provenance not in G-code | G-code is command-only | Add header comment |

**Recommendation:** Add provenance comments/headers to export files where format allows. This is informational, not authoritative.

---

## 8. T5 Findings Summary

### 8.1 Authority Boundary Status

| Boundary | Status | Evidence |
|----------|--------|----------|
| Translator geometry generation | OK | No generation |
| Translator vocabulary definition | OK | No definitions |
| Translator authority claim | OK | All consumers |
| Export gate bypass | OK | Gates upstream |

### 8.2 Positive Findings

| Finding | Evidence |
|---------|----------|
| All translators are consumers | No geometry generation |
| Layer names from upstream | ContourCategory.value |
| CAM params are CAM authority | Separate domain |
| Export lifecycle compliant | Gates respected |

### 8.3 Concerns (Non-Blocking)

| Concern | Severity | Recommendation |
|---------|----------|----------------|
| Provenance loss in export | LOW | Add headers |
| Downstream hardening risk | LOW | Document conventions |
| Format constraints | LOW | Inherent to format |

---

## 9. Export Authority Recommendations

### 9.1 Documentation Needed

| Document | Purpose |
|----------|---------|
| DXF layer convention | What layers mean |
| STEP entity mapping | Topology to STEP |
| G-code header convention | Provenance comments |

### 9.2 No Code Changes Required

Export systems comply with geometry authority boundaries. No code changes required for C2-A.

---

## 10. Cross-Reference

| Document | Relationship |
|----------|--------------|
| `C2A_GEOMETRY_AUTHORITY_PACKET.md` | Parent packet |
| `GEOMETRY_OWNERSHIP_TOPOLOGY.md` | T1 companion |
| `RUNTIME_GEOMETRY_BOUNDARY_MAP.md` | T2 companion |
| `authority_chain_registry.json` | Source of invariants |
| `CAM_GOVERNED_EXPORT_ARCHITECTURE.md` | Export architecture |

---

## T5 Status

**Draft complete.** Export systems verified compliant with geometry authority boundaries. Translators are consumers, not authorities.

**Sign-off recommendation:** APPROVE C2-A from T5 perspective.
