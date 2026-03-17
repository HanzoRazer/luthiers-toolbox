# Sprint Board

**Last Updated:** 2026-03-17
**Gap Count:** 101/120 resolved (19 remaining)

---

## Current Sprint: Binding & Purfling Completion

### Completed This Session

| Gap | Description | Status |
|-----|-------------|--------|
| OM-PURF-03 | Purfling ledge second-pass + neck purfling | DONE |
| OM-PURF-05 | Binding corner miter G-code | DONE |
| OM-PURF-08 | Channel depth probe cycle (G38.2) | DONE |

### MEDIUM Priority Gaps - Status

| Gap | Description | Status |
|-----|-------------|--------|
| BIND-GAP-04 | Binding strip length calculator | Ready |
| CCEX-GAP-05 | Archtop graduation thickness map | Deferred (need reference measurements) |
| CCEX-GAP-06 | Tap tone frequency targets | Deferred (need reference measurements) |
| CCEX-GAP-07 | Bracing pattern library | Deferred (need reference measurements) |
| CCEX-GAP-08 | Sound port placement calculator | Deferred (need reference measurements) |
| INLAY-03 | Inlay depth calculator | Done |
| VEC-GAP-06 | Vectorizer contour election | Done |

### Next Up

- **GEN-5**: Generator factory pattern completion

---

## Session Log

| Date | Gaps Closed | Notes | Next |
|------|-------------|-------|------|
| 2026-03-17 | — | useWoodGrain.ts: import moved to top (composables). InlayWorkspaceShell: Stage 0 Headstock Design (template + species + DXF import + preview + Next). useDxfImport composable; grain provided for children. npm run build pass. | GEN-5 next |
| 2026-03-17 | OM-PURF-03/05/08 | Purfling second-pass, corner miter G-code, G38.2 channel depth probe. 27 tests passing. | GEN-5 next |
| 2026-03-16 | BIND-GAP-01/02/03/05 | Binding design orchestration endpoint, body outline resolver, material bend radius validation | OM-PURF gaps |
| 2026-03-15 | 93 gaps | Major sprint day - platform architecture integrated | Binding module |

---

## Gap Categories Summary

| Category | Resolved | Remaining |
|----------|----------|-----------|
| CAM Core | 28 | 4 |
| Binding/Purfling | 12 | 2 |
| Generators | 8 | 3 |
| Instrument Geometry | 15 | 2 |
| Art Studio | 14 | 3 |
| Vision/Vectorizer | 9 | 1 |
| RMOS | 8 | 2 |
| Other | 7 | 2 |
| **Total** | **101** | **19** |

---

## Deferred Items

### CCEX (Carved/Carved Expert) Gaps
These gaps require physical reference measurements from actual instruments:
- CCEX-GAP-05: Archtop graduation thickness maps
- CCEX-GAP-06: Tap tone frequency targets for various body sizes
- CCEX-GAP-07: Bracing pattern dimensional data
- CCEX-GAP-08: Sound port acoustic modeling data

**Action Required:** Capture measurements from reference instruments before implementation.
