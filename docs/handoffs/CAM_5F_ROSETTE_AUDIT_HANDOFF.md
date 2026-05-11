# CAM Dev Order 5F — Rosette Route Consolidation Audit

**Date:** 2026-05-10  
**Author:** Claude (CAM Dev Order 5F)  
**Status:** COMPLETE

---

## Summary

Completed comprehensive audit of Rosette CAM route ecosystem. Mapped 29 endpoints across 11 route files, identified 7 generators, and documented fragmentation across preview, export, and governance dimensions.

**Key finding:** Rosette CAM is highly fragmented but governable with staged migration.

---

## Audit Scope

### In Scope (Completed)

- Route surface inventory
- Generator ownership mapping
- Preview/export separation analysis
- Frontend consumer identification
- Coordinate system documentation status
- Fragmentation classification
- Consolidation boundary identification
- Machine-readable manifest generation

### Out of Scope (Per 5F Guardrails)

- No generator rewrites
- No response shape changes
- No route removals
- No frontend changes
- No G-code changes

---

## Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| ROSETTE_CAM_ROUTE_MAP.md | docs/architecture/ | Complete |
| ROSETTE_CAM_OWNERSHIP_GRAPH.md | docs/architecture/ | Complete |
| ROSETTE_CAM_FRAGMENTATION_AUDIT.md | docs/architecture/ | Complete |
| ROSETTE_CAM_NORMALIZATION_BLOCKERS.md | docs/architecture/ | Complete |
| rosette_cam_route_manifest.json | docs/architecture/ | Complete |
| CAM_5F_ROSETTE_AUDIT_HANDOFF.md | docs/handoffs/ | This document |

---

## Key Findings

### 1. Route Surface (HIGH fragmentation)

- 11 route files with rosette endpoints
- 3+ preview routes producing different formats
- 2+ G-code export paths
- Mixed Art Studio / RMOS / CAM prefixes

### 2. Generator Ownership (MEDIUM fragmentation)

- 7 distinct generators
- Clear primary owners for each function
- Some experimental code in production paths
- Prototype imports from `herringbone_parametric.py`

### 3. Preview/Export Separation (MIXED)

- `rosette_toolpath_router.py` — Good (RMOS integrated)
- `rosette_cam_router.py` — **Problem** (G-code without RMOS)
- `rosette_designer_routes.py` — OK (export is SVG only)

### 4. Coordinate Systems (PARTIAL documentation)

- `cnc_gcode_exporter.py` — Documented
- `rosette_cam_bridge.py` — Partial
- Others — Not documented

### 5. Frontend/Backend Alignment (NEEDS TRACE)

- Frontend references routes not found in audit
- Possible prefix mounting differences
- Needs deeper investigation

---

## Fragmentation Classification

| Subsystem | Status | Notes |
|-----------|--------|-------|
| rosette_designer | ACTIVE | Well-contained, no governed preview |
| rosette_jobs | ACTIVE | Overlaps with snapshots |
| rosette_snapshots | ACTIVE | Good RMOS integration |
| rosette_compare | ACTIVE | Standalone |
| rosette_pattern | ACTIVE | Imports experimental code |
| rosette_manufacturing | ACTIVE | Complex dependencies |
| rosette_toolpath | ACTIVE | Good RMOS |
| rosette_cam (RMOS) | ACTIVE | **G-code governance gap** |

---

## Normalization Blockers

### Blocking (Must Resolve Before 5G)

1. **Route surface ambiguity** — Which preview route is canonical?
2. **Missing frontend route trace** — Unknown consumer breakage risk
3. **Ungoverned G-code** — `/rmos/rosette/export-cnc` needs RMOS
4. **Coordinate documentation** — Required for governed preview

### Non-Blocking (Defer)

- Preview output format variance
- Prototype code in production
- Multiple job stores

---

## Recommended Next Steps

### Phase 1: Trace (No Code Changes)

1. Complete frontend route prefix trace
2. Verify actual mounted paths
3. Document coordinate systems

### Phase 2: Governance Gates

1. Add RMOS to `rosette_cam_router.py` G-code endpoints
2. Decide canonical preview route
3. Add `coordinate_system` to preview responses

### Phase 3: Normalization (5G)

1. Wire governed preview to canonical route
2. Add gate semantics for rosette-specific conditions
3. Deprecate non-canonical preview routes

---

## Test Verification

All CAM tests passed at time of audit. No runtime changes made.

---

## Strategic Outcome

After 5F:

```
Rosette CAM is now:
- Fully inventoried (29 endpoints, 7 generators)
- Fragmentation documented
- Blockers identified
- Consolidation path defined
```

Rosette is now promotable to governed preview once blockers are resolved.

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| ROSETTE_CAM_ROUTE_MAP.md | Full route inventory |
| ROSETTE_CAM_OWNERSHIP_GRAPH.md | Generator ownership |
| ROSETTE_CAM_FRAGMENTATION_AUDIT.md | Overlap analysis |
| ROSETTE_CAM_NORMALIZATION_BLOCKERS.md | Prerequisites |
| rosette_cam_route_manifest.json | Machine-readable |
| CAM_CANDIDATE_EVALUATION_2026-05-09.md | Prior evaluation |

---

*5F audit complete: 2026-05-10*
