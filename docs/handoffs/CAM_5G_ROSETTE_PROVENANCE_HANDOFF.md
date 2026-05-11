# CAM Dev Order 5G — Rosette Provenance Handoff

**Date:** 2026-05-10  
**Dev Order:** 5G  
**Status:** COMPLETE

---

## Summary

5G established authoritative provenance and governance boundaries for Rosette CAM through:

1. Frontend/backend route tracing
2. Canonical preview candidate identification
3. Export surface classification
4. Preview/export boundary definition
5. Machine-readable governance manifest

**No runtime behavior was changed.**

---

## Key Findings

### Provenance Status

| Metric | Count |
|--------|-------|
| Total rosette routes audited | 29 |
| Frontend routes with valid backend | 18 |
| Frontend routes missing backend | 6 |
| Backend routes without frontend consumer | 8 |
| Candidate preview routes | 5 |
| Governed export routes | 1 |
| Quarantined export routes | 1 |

### Critical Issue: `/api/rmos/rosette/export-cnc`

**Classification:** `QUARANTINED_EXPORT`

**Evidence:**
- Produces G-code without RMOS artifact persistence
- No input/output hashing
- Safety decision returned but not enforced
- No coordinate system in response

**Required Governance (before promotion):**
1. RMOS run artifact creation
2. Input/output hash persistence
3. Safety gate enforcement
4. Coordinate system declaration
5. Tool validation

**Recommended Migration Target:** `/api/cam/rosette/post-gcode` (already governed)

---

## Canonical Preview Decision

### For Design Preview (Visual)

**Recommended:** `/api/art/rosette/preview/svg`

| Criterion | Score |
|-----------|-------|
| Frontend alignment | GOOD |
| Generator ownership | GOOD |
| Export coupling | NONE |
| RMOS integration | NONE (add) |

### For CAM Preview (Geometry Validation)

**Recommended:** `/api/rmos/rosette/preview`

| Criterion | Score |
|-----------|-------|
| Frontend alignment | GOOD |
| Generator ownership | GOOD |
| Export coupling | PARTIAL (separate) |
| RMOS integration | PARTIAL |

---

## Frontend/Backend Drift

### Missing Backend Routes

| Frontend Reference | Status |
|--------------------|--------|
| `/art-studio/rosette/preview` | MISSING |
| `/art-studio/rosette/export-dxf` | MISSING |
| `/art-studio/rosette/presets` | MISSING |
| `/api/art/rosette/feasibility/batch` | MISSING |

**Root Cause:** Art Studio consolidation left orphaned frontend paths.

**Recommendation:** Update frontend to use verified routes or implement missing endpoints.

---

## Preview/Export Boundary

### Preview Layer (Safe)

- Visual geometry (SVG, paths)
- Ring/tile segmentation
- BOM calculation
- Feasibility scoring
- Design comparison

### Export Layer (Governed)

- G-code generation
- CNC-ready DXF
- Toolpath postprocessing
- CNC job creation

---

## Deliverables Created

| Document | Purpose |
|----------|---------|
| `ROSETTE_FRONTEND_BACKEND_TRACE.md` | Provenance trace |
| `ROSETTE_CANONICAL_ROUTE_PROPOSAL.md` | Canonical recommendations |
| `ROSETTE_EXPORT_SURFACE_AUDIT.md` | Export risk analysis |
| `ROSETTE_PREVIEW_EXPORT_BOUNDARY.md` | Architecture proposal |
| `rosette_governance_gate_manifest.json` | Machine-readable map |
| `CAM_5G_ROSETTE_PROVENANCE_HANDOFF.md` | This document |

---

## Unresolved Blockers

| Blocker | Severity | Resolution Phase |
|---------|----------|------------------|
| `/export-cnc` ungoverned | HIGH | 5J |
| Frontend drift (6 routes) | MEDIUM | 5H |
| Coordinate documentation | MEDIUM | 5H |
| Postprocessor fragmentation | LOW | 5K |

---

## Safe Next Steps (5H)

### Immediate (No Code Changes)

1. Validate canonical preview selections with team
2. Decide on frontend drift resolution (fix frontend vs add backend)
3. Prioritize coordinate documentation

### Implementation (5H)

1. Select canonical preview routes
2. Add `coordinate_system` to preview responses
3. Add governance metadata to canonical preview

### Export Governance (5J)

1. Add RMOS artifacts to `/export-cnc`
2. Add deprecation header pointing to `/post-gcode`
3. Enforce safety gate

---

## Acceptance Criteria Status

| Criterion | Status |
|-----------|--------|
| Frontend/backend provenance mapped | COMPLETE |
| Canonical preview candidates identified | COMPLETE |
| Export routes classified | COMPLETE |
| CNC/G-code governance risks documented | COMPLETE |
| Preview/export boundaries proposed | COMPLETE |
| Governance gates documented | COMPLETE |
| Machine-readable manifest exists | COMPLETE |
| Future canonicalization sequence defined | COMPLETE |
| No runtime behavior changed | VERIFIED |

---

## Strategic Outcome

After 5G:

```
Rosette CAM now has authoritative ownership boundaries.
```

This is the prerequisite for safe governed preview normalization.

**Rosette Maturity:**
- Before 5G: `FRAGMENTED CANDIDATE WITH EXPORT RISK`
- After 5G: `PROVENANCE-STABILIZED CANDIDATE`

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_5F_ROSETTE_AUDIT_HANDOFF.md` | Prior audit |
| `ROSETTE_CAM_ROUTE_MAP.md` | Route inventory |
| `ROSETTE_CAM_OWNERSHIP_GRAPH.md` | Generator ownership |
| `ROSETTE_CAM_FRAGMENTATION_AUDIT.md` | Fragmentation analysis |
| `ROSETTE_FRAGMENTATION_RESOLUTION_PLAN.md` | Resolution strategy |

---

*5G completed: 2026-05-10*  
*No runtime changes made*  
*Ready for 5H: Canonical Preview Selection*
