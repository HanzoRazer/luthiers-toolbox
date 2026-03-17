# Sprint Board

**Last Updated:** 2026-03-17
**Gap Count:** 111/120 resolved (9 remaining)

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
| INLAY-07 | Inlay pocket depth control | Done |
| VEC-GAP-06 | Vectorizer contour election | Done |

### Next Up

- **GEN-5**: Generator factory pattern completion

---

## Session Log

| Date | Gaps Closed | Notes | Next |
|------|-------------|-------|------|
| 2026-03-17 | — | **SmartGuitarShell.vue:** Module 5 shell at views/smart-guitar/SmartGuitarShell.vue with 5 tabs (Body Design → Instrument Hub, Electronics Layout, RPi5 Cavity, WiFi & Antenna, Export & BOM). Route /smart-guitar (SmartGuitar) in place. Nav: Smart Guitar → /smart-guitar. Added alias /instrument-hub → InstrumentGeometry for shell link. npm run build pass. | GEN-5 next |
| 2026-03-17 | — | **INLAY-03/INLAY-07 labeling fix:** GAP_ANALYSIS_MASTER: Added INLAY-07 (Inlay pocket depth control, Resolved). INLAY-03 marked Resolved (FretMarkersView superseded by InlayWorkspaceShell Stage 2). FretMarkersView.vue deprecated (comment only); route /art-studio/fret-markers removed from router. No Fret Markers nav link in AppDashboardView. SPRINT_BOARD: INLAY-03→INLAY-07 for pocket depth. npm run build pass. | GEN-5 next |
| 2026-03-17 | — | **router_registry/manifest.py decomposed** into domain manifests: cam_manifest.py (35), art_studio_manifest.py (14), rmos_manifest.py (15), business_manifest.py (15), system_manifest.py (16). manifest.py assembles ROUTER_REGISTRY/ROUTER_MANIFEST in &lt;80 lines. 95 RouterSpec entries unchanged; load_all_routers verified. | GEN-5 next |
| 2026-03-17 | — | **Audit Log nav:** No shop-floor audit route in router (only /tools/audio-analyzer/ingest). Removed Audit Log link from Shop Floor; kept Manufacturing Runs, Job Queue. **presets.py split:** preset_definitions.py (580 lines), preset_registry.py (41 lines), presets.py shim (18 lines). Imports unchanged. | GEN-5 next |
| 2026-03-17 | — | **FILE 2:** job_queue split into queue_storage.py (persistence, CRUD), queue_execution.py (workers, handlers, retries), queue.py orchestrator (~190 lines). All queue tests passing. **Nav:** AppDashboardView.vue reorganized into 5 modules: Design, Art Studio, CAM, Shop Floor, Smart Guitar. Routes unchanged; npm run build pass. | GEN-5 next |
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
