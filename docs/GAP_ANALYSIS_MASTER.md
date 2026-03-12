# Gap Analysis Master — All Instrument Build Handoffs

> **Generated:** 2026-03-09 | **Updated:** 2026-03-10 | **Sources:** 11 build handoff documents | **Total Gaps:** 113

---

## Remediation Log

| Date | Commit | Fix | Gaps Resolved |
|------|--------|-----|---------------|
| 2026-03-10 | `eafaead0` | Wire auth guards (`initAuthGuard`, `requireAuth`, `requireTier`) + add `@safety_critical` to 8 CNC endpoints | P0 blockers (not gap IDs) |
| 2026-03-10 | `eafaead0` | TypeScript fix: add `PARTIAL` to instrument status union type in `instrumentApi.ts:55` | Build blocker — enables `npm run build` |
| 2026-03-10 | `14260731` | Commit 7 documentation files including this gap analysis | Documentation |
| 2026-03-10 | `d80b0799` | Refactor auth store to use SDK instead of raw fetch() | SDK convention compliance |
| 2026-03-10 | `7826e6ef` | Add CNC pre-flight validation gate (`preflight_gate.py`) — blocking safety check before G-code execution | CAM safety |
| 2026-03-10 | `8f74f599` | Add perimeter profiling toolpath generator (`app/cam/profiling/`) | OM-GAP-02, BEN-GAP-03, VINE-07, FV-GAP-03 |
| 2026-03-10 | `e60e2df0` | Add binding/purfling channel CAM module (`app/cam/binding/`) | OM-GAP-03, OM-GAP-04, OM-PURF-01, OM-PURF-02, BEN-GAP-01 |
| 2026-03-10 | `bc81f7c5` | Add DXF validation gate (CI check for format, geometry, bounds) | LP-GAP-01, EX-GAP-01, EX-GAP-02, SG-GAP-01 |
| 2026-03-10 | `ba9574fd` | Add drilling CAM module (G83 peck cycle, patterns) | FV-GAP-06 |
| 2026-03-10 | `64f1a87f` | Add production V-carve module (chipload, stepdown, corner slowdown) | VINE-03 |
| 2026-03-10 | `49aac7d0` | Mount CAM modules via routers (profiling, binding, vcarve production) | Category 5 API coverage |
| 2026-03-10 | `611addfa` | Add headstock inlay prompt router (11 templates, AI prompt generation) | INLAY-01 |
| 2026-03-10 | — | **False positive:** Bracing router already mounted in manifest.py line 266 | VINE-08 (already resolved) |
| 2026-03-10 | — | **False positive:** Neck router already mounted in manifest.py line 372 | VINE-04, OM-GAP-07 (already resolved) |
| 2026-03-10 | `fe2b4e62` | Add SVG-to-DXF `/convert` endpoint in geometry router | VINE-02 |
| 2026-03-10 | `6cfe4d12` | Add inlay pocket G-code `/export-gcode` endpoint | VINE-01 |
| 2026-03-10 | `08a7db0d` | Add Phase 3 vectorizer API endpoint `/blueprint/phase3/vectorize` | VEC-GAP-01 |
| 2026-03-10 | `b8ba05b3` | Add Phase 4 dimension linking API endpoint `/blueprint/phase4/link` | VEC-GAP-02 |
| 2026-03-10 | `03acbb4f` | Add PipelineResult to CAM adapter `/cam/blueprint/pipeline-adapter/from-pipeline` | VEC-GAP-03 |
| 2026-03-10 | `4a0af084` | Add Blueprint → CAM integration tests (20 tests) | VEC-GAP-04 |
| 2026-03-10 | `f8e4dded` | Add Phase 1 → Phase 3 scale handoff `scale_hint_mm_per_pixel` | VEC-GAP-05 |
| 2026-03-10 | ec003681 | Add Flying V CAM-ready DXF with closed LWPOLYLINE | FV-GAP-04 |
| 2026-03-10 | 461caebc | Add Les Paul 8-layer CAM DXF (26 entities) | LP-GAP-01 |
| 2026-03-10 | a7a9ee24 | Add DXF preprocessor pipeline (format normalize, curve densify, dimension validate) | EX-GAP-01, EX-GAP-02, EX-GAP-03 |
| 2026-03-10 | 638b7578 | Add DXF geometry correction pipeline (dimension scaling, centerline alignment) | SG-GAP-01, SG-GAP-02 |
| 2026-03-11 | c9ac19ec | Restore POST /api/saw/batch/toolpaths/from-decision endpoint + 8 schemas (P1-SAW fix) | P1-SAW (pipeline break) |
| 2026-03-11 | 5cd6c2ba | Add Martin + Benedetto headstock outlines + neck presets | OM-GAP-06, BEN-GAP-06 |
| 2026-03-11 | (pending) | Add corner_radius to 7 Smart Guitar cavities | SG-GAP-12 |
| 2026-03-11 | (pending) | Add cover plate screw positions + clarify antenna depth | SG-GAP-08, SG-GAP-10 |
| 2026-03-11 | 289b4ac4 | GIBSON_SOLID headstock already added | VINE-06 |
| 2026-03-11 | (pending) | Smart Guitar spec coordinate system fixes | SG-GAP-03, SG-GAP-04, SG-GAP-05, SG-GAP-06, SG-GAP-07 |
| 2026-03-12 | 289b4ac4 | FENDER_STRAT headstock was already implemented | NECK-01, GAP-01 |
| 2026-03-12 | (pending) | Document inch mode in Les Paul generator, add dual-unit comments | LP-GAP-10 |
---

## Summary by Category

| # | Category | Critical | High | Medium | Low | Total | Core Fix |
|---|----------|----------|------|--------|-----|-------|----------|
| 1 | DXF & Asset Quality | 4 | 2 | 2 | 1 | **9** | Regenerate all DXFs to R12, match spec dims |
| 2 | CAM Toolpath Generation | 3 | 8 | 5 | 1 | **17** | Build perimeter profiler + binding/purfling CAM modules |
| 3 | Spec & Data Completeness | — | 5 | 3 | 2 | **10** | Audit all spec JSONs, add missing fields |
| 4 | Geometry & Shape Generators | 3 | 5 | 3 | — | **11** | Headstock outlines + body outline generators |
| 5 | API & Endpoint Coverage | 3 | 5 | 1 | 1 | **10** | Mount existing modules via routers in main.py |
| 6 | Integration & Pipeline Bridges | 3 | 3 | 3 | 1 | **10** | SVG→DXF converter + DXF→CAM orchestrator |
| 7 | Verification & Simulation | — | — | 5 | 1 | **6** | Backplot simulator (now partially addressed by VIS) |
| 8 | Post-Processor & G-code Quality | — | — | 2 | 5 | **7** | G43 tool length comp + cutter comp + unit standardization |
| 9 | Frontend & UI | — | 4 | 2 | — | **6** | Wire headstock designer, inlay canvas, vectorizer phases |
| 10 | Vectorizer Pipeline | 1 | 2 | 4 | 1 | **8** | Phase 3/4 API endpoints + frontend integration |
| 11 | Config, Presets & Registry | — | — | 3 | 2 | **5** | Add missing presets and registry entries |
| 12 | Accuracy & Position Validation | — | 2 | 4 | 2 | **8** | Validate cavity positions against factory references |
| 13 | Physical Component Geometry ⏸️ | 2 | 2 | 2 | — | **6** | Pickup calculator + body centerline — **TABLED** (physical dependencies) |
| | **TOTALS** | **19** | **38** | **39** | **17** | **113** | |

---

## Category 1 — DXF & Asset Quality

**Problem:** DXF files are missing, wrong format (AC1024 instead of R12/AC1009), dimensionally inaccurate, or too coarse for production CNC. Every CNC build hit this.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| LP-GAP-01 | Les Paul 1959 | Multi-layer CAM DXF (`LesPaul_CAM_Closed.dxf`) never delivered — 8 named layers referenced in spec | **Resolved** (461caebc) |
| EX-GAP-01 | Explorer 1958 | DXF is coarse 24-point approximation — production needs 200+ points with arc interpolation | **Resolved** (a7a9ee24) |
| EX-GAP-02 | Explorer 1958 | DXF is AC1024 (AutoCAD 2010), not R12 (AC1009) — repo convention violated | **Resolved** (a7a9ee24) |
| SG-GAP-01 | Smart Guitar | DXF 12.1% narrow, 4.3% short vs spec — build script scales to compensate, distorting shape | **Resolved** (638b7578) |
| EX-GAP-03 | Explorer 1958 | DXF extents don't match spec dimensions (556×434mm vs 475×460mm) | **Resolved** (a7a9ee24) |
| SG-GAP-02 | Smart Guitar | DXF X-axis asymmetric — centerline 22.2mm off-center, all cavities shifted | **Resolved** (638b7578) |
| OM-PURF-05 | OM Purfling | Scan data has 5,451 scattered points, not a contour — parametric regen required | MEDIUM |
| VINE-12 | J45 Vine | Extracted DXFs are R2000 not R12 — LWPolyline necessity but violates convention | LOW |
| VINE-09 | J45 Vine | Bracing DXF has raw lines/arcs, not closed contours — 460 entities, 0 closed polylines | **Resolved** (30e50bb3) |
| SAW-LAB-GAP-01 | Duplicate artifact helpers across 7 files | refactor(saw-lab): SAW-LAB-GAP-01 | 6dd8280a | Centralized 8 helpers into artifact_helpers.py |
| RMOS-GAP-01 | Duplicate artifact helpers in runs_v2/ (3 files) | refactor(rmos): RMOS-GAP-01 | 528f577d | Moved helpers to rmos/, centralized across saw_lab + runs_v2 |
| CORRUPT-GAP-01 | 8 Python files in app/services/ with corrupted formatting | fix(services): CORRUPT-GAP-01 | 8f530691 | Reconstructed all 8 files with proper Python formatting |

### Fixes

1. **DXF Regeneration Pipeline** — Create `scripts/regenerate_all_dxfs.py` that reads spec JSONs and produces R12 (AC1009) DXFs with closed LWPolylines matching spec dimensions exactly. Run for every instrument in registry.
2. **DXF Validation Gate** — Add CI check: every `*.dxf` in `instrument_geometry/` must be AC1009, have ≥1 closed LWPOLYLINE, and bounding box within ±1mm of spec dimensions.
3. **High-Resolution Outlines** — Replace coarse polygons (24-point Explorer, 21-point Smart Guitar) with 200+ point arc-interpolated contours from factory references or parametric generators.
4. **Bracing DXF Cleanup** — Convert scattered entities to closed contours via `scripts/cleanup_bracing_dxf.py` using proximity-based joining.

---

## Category 2 — CAM Toolpath Generation

**Problem:** The CAM engine has interior pocket clearing but is missing several critical toolpath types. Perimeter profiling, binding/purfling channels, and neck operations are the biggest gaps.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| OM-GAP-03 | OM-28 | No binding geometry backend at all — no offset curve generator, no channel calculator | CRITICAL |
| OM-GAP-04 | OM-28 | No purfling channel CAM module — even with binding geometry, no toolpath generation | CRITICAL |
| BEN-GAP-01 | Benedetto | No binding channel routing CAM — archtop curved surface adds complexity | CRITICAL |
| OM-GAP-02 | OM-28 | Body perimeter profiling toolpath missing — only interior pocket clearing exists | HIGH |
| BEN-GAP-03 | Benedetto | Body perimeter profiling missing (duplicate of OM-GAP-02) | HIGH |
| VINE-07 | J45 Vine | Body perimeter profiling missing — no outside-contour routing with tabs | HIGH |
| FV-GAP-03 | Flying V | No `ProfileToolpath` class — body perimeter is hand-generated | HIGH |
| BEN-GAP-08 | Benedetto | Archtop top/back carving CAM missing — graduation map exists, no toolpath gen | HIGH |
| BEN-GAP-09 | Benedetto | F-hole routing CAM missing — DXFs exist but no CAM module | MEDIUM |
| LP-GAP-03 | Les Paul 1959 | No neck CNC pipeline — only 2D geometry exists, no G-code for neck profile/truss rod/fret slots | HIGH |
| OM-PURF-01 | OM Purfling | No binding channel CAM module — standalone script only | HIGH |
| OM-PURF-02 | OM Purfling | No purfling ledge operation — needs dedicated CAM step | HIGH |
| FV-GAP-05 | Flying V | No pocket toolpath generator that consumes outline data for parametric cavity placement | MEDIUM |
| FV-GAP-06 | Flying V | String-through drilling has no backend API — G83 peck cycle hand-generated | MEDIUM |
| VINE-03 | J45 Vine | V-carve G-code is demo quality — ignores cutter comp, chipload, stepdown | HIGH |
| OM-PURF-03 | OM Purfling | No neck purfling routing — requires neck-specific fixture | MEDIUM |
| LP-GAP-05 | Les Paul 1959 | Carved top uses elliptical paraboloid approximation vs real asymmetric carve | MEDIUM |
| OM-PURF-06 | OM Purfling | No material-aware feed rates — generic 600mm/min for all materials | LOW |

### Fixes

1. **`app/cam/profiling/` module** — Create `ProfileToolpath` class that takes a closed LWPOLYLINE, generates outside-contour toolpath with configurable tab count/size, lead-in arcs, and climb/conventional direction. This single module resolves OM-GAP-02, BEN-GAP-03, VINE-07, FV-GAP-03 (4 instruments blocked).
2. **`app/cam/binding/` module** — Create binding channel routing: takes body outline + offset distance + channel depth/width, generates parallel offset toolpath. Separate `purfling_ledge()` for second-pass ledge cut. Resolves OM-GAP-03, OM-GAP-04, OM-PURF-01, OM-PURF-02, BEN-GAP-01 (2 instruments blocked).
3. **`app/cam/neck/` module** — Neck CNC pipeline: truss rod channel, profile carving (with station awareness beyond 12"), fret slot integration, headstock routing. Resolves LP-GAP-03.
4. **`app/cam/drilling/` module** — Parametric drilling operations: string-through G83 peck, bolt pattern, pilot holes. Resolves FV-GAP-06.
5. **`app/cam/carving/` module** — 3D surface carving: archtop graduation, Les Paul carved top (with proper asymmetric 1959 profile). Resolves BEN-GAP-08, LP-GAP-05.
6. **Upgrade `svg_to_naive_gcode()` → production V-carve** — Add cutter compensation, chipload calc, proper stepdown. Resolves VINE-03.

---

## Category 3 — Spec & Data Completeness

**Problem:** Spec JSON files have missing fields, inconsistent coordinate systems, and undefined geometry that forces build scripts to guess.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| SG-GAP-04 | Smart Guitar | Pickups use `y_from_bridge` while 9 other cavities use `y_from_top` — mixed system | **Resolved** (pending) |
| SG-GAP-05 | Smart Guitar | Control plate has NO `body_position_mm` — only grid_position (0–1 normalized) | **Resolved** (pending) |
| SG-GAP-06 | Smart Guitar | Wiring channels have from/to labels but zero XYZ coordinate pairs | **Resolved** (pending) |
| SG-GAP-07 | Smart Guitar | Neck pocket bolt pattern undefined — no positions, diameters, count, spacing | **Resolved** (pending) |
| SG-GAP-03 | Smart Guitar | Output jack bore angle undefined — spec says "angled" but no angle_degrees field | **Resolved** (pending) |
| SG-GAP-08 | Smart Guitar | Cover plate screw positions undefined for both rear cavities | **Resolved** (pending) |
| SG-GAP-10 | Smart Guitar | Antenna recess depth geometry ambiguous (2mm wood cover vs 20.45mm remaining) | **Resolved** (pending) |
| SG-GAP-12 | Smart Guitar | No `corner_radius` on any pocket — hardware has sharp corners, CNC has fillets | **Resolved** (pending) |
| LP-GAP-10 | Les Paul 1959 | Mixed unit systems: Phase 1-2 use G20 (inches), Phase 3 uses G21 (mm) | **Resolved** (documented) |
| SG-GAP-11 | Smart Guitar | Generator has stale scale length comment ("25.5 Fender" instead of 24.75 Gibson) | LOW |

### Fixes

1. **Spec JSON Schema Validator** — Create `scripts/validate_spec_json.py` that enforces: all cavities use same coordinate system (`y_from_top`), all cavities have `body_position_mm`, all channels have XYZ pairs, all pockets have `corner_radius`, bolt patterns have positions.
2. **Smart Guitar Spec v1.2** — Audit and fix all SG-GAP fields: standardize to `y_from_top`, add `body_position_mm` to control plate, add wiring channel coordinates, add bolt pattern, add jack angle, add screw positions, add corner radii.
3. **Unit Standardization** — Enforce G21 (mm) across all phases for all instruments per repo convention. Convert any G20 files.

---

## Category 4 — Geometry & Shape Generators

**Problem:** Critical instrument shapes (headstock outlines, body outline generators, binding geometry) are missing or incomplete stubs.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| GAP-07 | 24-Fret Strat | Strat body outline generator does not exist — only Les Paul generator exists | CRITICAL |
| GAP-04 | 24-Fret Strat | Pickup position calculator does not exist anywhere in the codebase | CRITICAL |
| NECK-01 | Strat Neck | Strat headstock outline generator — `FENDER_STRAT` enum falls through to paddle headstock | **Resolved** (289b4ac4) |
| GAP-01 | 24-Fret Strat | Stratocaster headstock outline is incomplete stub (same as NECK-01) | **Resolved** (289b4ac4) |
| GAP-05 | 24-Fret Strat | Fretboard overhang channel — no geometry or preset for 24-fret bolt-on | HIGH |
| BEN-GAP-04 | Benedetto | Neck binding geometry missing — must account for fretboard taper and radius | HIGH |
| BEN-GAP-05 | Benedetto | Headstock binding geometry missing — tightest bend at ~20mm tip radius | HIGH |
| OM-GAP-06 | OM-28 | Martin headstock outline missing — neither slotted nor solid | **Resolved** (5cd6c2ba) |
| BEN-GAP-06 | Benedetto | Archtop/Benedetto headstock outline missing in `neck_headstock_config.py` | **Resolved** (5cd6c2ba) |
| VINE-06 | J45 Vine | Gibson acoustic solid headstock outline missing — current is electric open-book | **Resolved** (289b4ac4) |
| BEN-GAP-07 | Benedetto | Miter joint geometry computation missing — no module for angle/cut/joint geometry | MEDIUM |

### Fixes

1. **`neck_headstock_config.py` expansion** — Add headstock outlines: `FENDER_STRAT`, `MARTIN_SLOTTED`, `MARTIN_SOLID`, `BENEDETTO_ARCHTOP`, `GIBSON_ACOUSTIC_SOLID`. 5 additions resolve 5 gaps (NECK-01, GAP-01, OM-GAP-06, BEN-GAP-06, VINE-06).
2. **`generators/body_outline/stratocaster.py`** — Strat body outline generator with parametric contour cuts, horn geometry, belly cut. Resolves GAP-07.
3. **`calculators/pickup_position.py`** — Pickup position calculator: takes scale length, pickup count, pickup type → returns XY positions. Resolves GAP-04.
4. **`calculators/binding_geometry.py`** — Offset curve generation for body/neck/headstock binding paths, with bend-radius constraints and miter joint angle computation. Resolves BEN-GAP-04, BEN-GAP-05, BEN-GAP-07.
5. **24-fret extensions** — Fretboard overhang channel geometry preset, neck profile stations extended to 19.14". Resolves GAP-05.

---

## Category 5 — API & Endpoint Coverage

**Problem:** Backend modules exist with full logic but have no HTTP routes mounted in `main.py`, or routes are mounted but return stubs.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| VEC-GAP-01 | OM Purfling | Phase 3.6 Vectorizer has no API endpoint — only accessible via Python import | CRITICAL |
| VINE-01 | J45 Vine | Inlay DXF → pocket milling G-code bridge missing — pipeline dead-ends at DXF | CRITICAL |
| INLAY-01 | Custom Inlay | No headstock inlay router — `inlay_prompts.py` has 11 styles but no API | CRITICAL |
| VEC-GAP-02 | OM Purfling | Phase 4 Dimension Linking is CLI-only — no `/api/blueprint/phase4` route | HIGH |
| VINE-04 | J45 Vine | Neck G-code generator class exists but no HTTP endpoint | HIGH |
| OM-GAP-07 | OM-28 | Neck G-code generator has no HTTP endpoint (same as VINE-04) | HIGH |
| NECK-04 | Strat Neck | Strat-specific API endpoint missing — neck router defaults to Les Paul | HIGH |
| VINE-08 | J45 Vine | Bracing router has 4 endpoints but is not mounted in `main.py` — dead code | HIGH |
| LP-GAP-04 | Les Paul 1959 | Fret slot CAM exists (934 lines) but not wired into build pipeline | MEDIUM |
| INLAY-05 | Custom Inlay | `inlay_prompts.py` is orphaned — zero imports, unreachable from any endpoint | LOW |

### Fixes

1. **Mount existing routers** — In `main.py`, mount: bracing router (VINE-08), neck G-code router (VINE-04/OM-GAP-07), headstock inlay router (INLAY-01). These are code-complete modules that just need `app.include_router()`.
2. **Vectorizer Phase 3/4 routers** — Create `app/routers/blueprint_phase3_router.py` and `blueprint_phase4_router.py` wrapping existing CLI logic. Resolves VEC-GAP-01, VEC-GAP-02.
3. **Inlay→CAM orchestrator** — Create endpoint that takes inlay DXF output and feeds it to adaptive milling with correct depth/tool parameters. Resolves VINE-01.
4. **Fret slot integration** — Wire `fret_slots_cam.py` into neck build pipeline as a step. Resolves LP-GAP-04.
5. **Strat neck preset** — Add Strat preset to neck router with Fender scale/profile defaults. Resolves NECK-04.

---

## Category 6 — Integration & Pipeline Bridges

**Problem:** Different subsystems produce outputs that the next subsystem can't consume. Format converters, coordinate bridges, and orchestrators are missing.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| VINE-02 | J45 Vine | SVG → DXF format converter missing — Art Studio outputs SVG, CAM consumes DXF | CRITICAL |
| VINE-01 | J45 Vine | Inlay DXF → pocket milling G-code bridge missing (also in Cat 5) | CRITICAL |
| VINE-05 | J45 Vine | Unified fretboard↔headstock coordinate canvas missing — separate coord systems | HIGH |
| VEC-GAP-03 | OM Purfling | Phase 4 `PipelineResult` has no consumer — nothing in CAM or frontend reads it | HIGH |
| VEC-GAP-05 | OM Purfling | Phase 1 AI scale detection not passed to Phase 3 as calibration hint | MEDIUM |
| VEC-GAP-04 | OM Purfling | Phase 3 → CAM bridge — same layer but no integration test | MEDIUM |
| INLAY-04 | Custom Inlay | No unified coordinate space — fretboard and headstock use disconnected systems | MEDIUM |
| VINE-11 | J45 Vine | Bracing presets disconnected from instrument specs — generic, not instrument-aware | MEDIUM |
| FV-GAP-04 | Flying V | Vectorizer Phase 2 never processed Flying V DWGs — DWG→DXF conversion not run | **Resolved** (ec003681) |
| VEC-GAP-08 | OM Purfling | OCR dimensions from Phase 3.6 unused downstream | LOW |

### Fixes

1. **`app/util/svg_to_dxf.py`** — SVG→DXF converter: parses SVG paths, converts to R12 LWPOLYLINE. This is the single biggest pipeline gap — blocks all art→CAM workflows. Resolves VINE-02.
2. **Inlay orchestrator endpoint** — `/api/cam/inlay/mill` takes DXF + material + depth → returns pocket milling G-code. Resolves VINE-01.
3. **Unified coordinate canvas** — Add `origin_offset_mm` field to headstock spec relative to fretboard nut, enabling single coordinate space. Resolves VINE-05, INLAY-04.
4. **Vectorizer pipeline wiring** — Pass Phase 1 scale → Phase 3 calibration. Wire Phase 4 PipelineResult to CAM bridge. Resolves VEC-GAP-03, VEC-GAP-05.
5. **Run vectorizer Phase 2 on Flying V DWGs** — One-time execution + store results. Resolves FV-GAP-04.

---

## Category 7 — Verification & Simulation

**Problem:** Every build produced thousands of lines of G-code with zero automated backplot verification. No collision checks, no air-cutting detection, no depth validation.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| LP-GAP-08 | Les Paul 1959 | 452K lines unverified for collisions, air-cutting, over-depth, tab miscalcation | MEDIUM |
| EX-GAP-12 | Explorer 1958 | 9,401 lines unverified | MEDIUM |
| SG-GAP-13 | Smart Guitar | 11,967 lines across 2 phases unverified | MEDIUM |
| OM-PURF-08 | OM Purfling | No channel depth verification — no probe cycle for ±0.1mm tolerance | MEDIUM |
| FV-GAP-10 | Flying V | G-code uses parametric approximation, not DXF-extracted coordinates — unverified | MEDIUM |
| FV-GAP-09 | Flying V | `detailed_outlines.py` has no Flying V entry — partial data | LOW |

### Fixes

1. **Toolpath Visualizer (PARTIALLY DEPLOYED)** — The VIS P1-P3 implementation (just committed) provides animated playback, progress tracking, and time estimates. This enables visual backplot verification for all builds.
2. **Automated G-code Validator** — Extend `gcodeValidator.ts` (deployed) to check: max Z depth vs stock thickness, rapid moves below stock surface, total time reasonableness.
3. **Backend simulation depth check** — Add `validate_depths(segments, stock_thickness)` to `gcode_parser.py` that flags any cut deeper than stock. Resolves depth-related concerns across all builds.
4. **Probe cycle template** — Add G38.2 probe routine template to post-processor for critical-tolerance operations. Resolves OM-PURF-08.

---

## Category 8 — Post-Processor & G-code Quality

**Problem:** Generated G-code lacks standard CNC safety features: no tool length compensation, no cutter compensation, inconsistent units.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| LP-GAP-06 | Les Paul 1959 | No G43 tool length compensation — all tool changes need manual Z-touch-off | MEDIUM |
| EX-GAP-13 | Explorer 1958 | No G43 — same issue | LOW |
| SG-GAP-14 | Smart Guitar | No G43 — same issue | LOW |
| OM-PURF-07 | OM Purfling | No G41/G42 cutter compensation — pre-calculated offset only | LOW |
| FV-GAP-07 | Flying V | No tool-change sequencing — multi-tool programs require manual M0 pauses | MEDIUM |
| LP-GAP-10 | Les Paul 1959 | Mixed G20/G21 across phases — operator risk | LOW |
| SG-GAP-09 | Smart Guitar | USB-C slot requires 3+1 axis edge routing — 3-axis approximation used | LOW |

### Fixes

1. **Post-processor upgrade: G43 emission** — Add `emit_tool_length_comp=True` option to all G-code emitters. After each `M6 Tn`, emit `G43 Hn`. Single change resolves LP-GAP-06, EX-GAP-13, SG-GAP-14.
2. **Post-processor upgrade: G41/G42 support** — Add `use_cutter_comp=True` option. Emit `G41 D{tool}` for climb, `G42 D{tool}` for conventional. Resolves OM-PURF-07.
3. **Tool-change sequencing** — Add automatic `M6 Tn` + `G43 Hn` + optional `M0` (operator pause) or `M1` (optional stop) between tool sections. Resolves FV-GAP-07.
4. **Unit enforcement** — All G-code starts with `G21` (mm). No G20 generation. Resolves LP-GAP-10.

---

## Category 9 — Frontend & UI

**Problem:** Backend capabilities lack frontend surfaces. Headstock designer is a dead stub, inlay canvas can't span fretboard+headstock, vectorizer UI covers Phase 1 only.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| INLAY-02 | Custom Inlay | `HeadstockDesignerView.vue` is non-functional stub — no API calls, no reactivity | HIGH |
| INLAY-06 | Custom Inlay | No unified inlay canvas — can't show artwork flowing fretboard→headstock | HIGH |
| NECK-05 | Strat Neck | No `StratocasterNeckGenerator.vue` or composables | HIGH |
| INLAY-03 | Custom Inlay | `FretMarkersView.vue` overlaps `InlayDesignerView.vue` — duplication | MEDIUM |
| VEC-GAP-06 | OM Purfling | `BlueprintImporter.vue` calls only Phase 1 — no UI for Phase 2/3/calibration | MEDIUM |
| VINE-08 | J45 Vine | Bracing endpoints unreachable — no frontend consumes them (also in Cat 5) | HIGH |

### Fixes

1. **Wire `HeadstockDesignerView.vue`** — Connect to headstock inlay router (once mounted), add design selection, preview canvas, export. Resolves INLAY-02.
2. **Unified inlay canvas component** — Single canvas component that renders fretboard + headstock with shared coordinate space. Resolves INLAY-06.
3. **Strat neck UI** — `StratocasterNeckGenerator.vue` with preset selector, profile preview, G-code generation. Resolves NECK-05.
4. **Merge fret marker views** — Consolidate `FretMarkersView.vue` into `InlayDesignerView.vue`. Resolves INLAY-03.
5. **Vectorizer multi-phase UI** — Add Phase 2/3/4 step panels to `BlueprintImporter.vue`. Resolves VEC-GAP-06.

---

## Category 10 — Vectorizer Pipeline

**Problem:** The blueprint vectorizer pipeline (Phases 1–4) has implementation but poor API coverage, no frontend beyond Phase 1, and broken inter-phase handoffs.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| VEC-GAP-01 | OM Purfling | Phase 3.6 Vectorizer has no API endpoint | CRITICAL |
| VEC-GAP-02 | OM Purfling | Phase 4 Dimension Linking is CLI-only | HIGH |
| VEC-GAP-03 | OM Purfling | Phase 4 `PipelineResult` has no consumer | HIGH |
| VEC-GAP-04 | OM Purfling | Phase 3 → CAM bridge has no integration test | MEDIUM |
| VEC-GAP-05 | OM Purfling | Phase 1 scale detection not passed to Phase 3 | MEDIUM |
| VEC-GAP-06 | OM Purfling | Frontend covers Phase 1 only | MEDIUM |
| VEC-GAP-07 | OM Purfling | Phase 3 `constants.py` missing `PHASE3_AVAILABLE` flag | MEDIUM |
| VEC-GAP-08 | OM Purfling | OCR dimensions from Phase 3.6 unused downstream | LOW |

### Fixes

1. **Phase 3 API router** — `app/routers/blueprint_phase3_router.py`: POST accepts image + config, returns vectorized DXF. Resolves VEC-GAP-01.
2. **Phase 4 API router** — `app/routers/blueprint_phase4_router.py`: POST accepts Phase 3 output, returns dimension-linked PipelineResult. Resolves VEC-GAP-02.
3. **PipelineResult → CAM adapter** — Service that reads PipelineResult, extracts geometry + dimensions, outputs CAM-ready spec. Resolves VEC-GAP-03.
4. **Integration tests** — Phase 3 → DXF → CAM bridge round-trip test. Resolves VEC-GAP-04.
5. **Phase handoff wiring** — Pass Phase 1 `detected_scale` as Phase 3 `calibration_hint`. Add `PHASE3_AVAILABLE` flag. Resolves VEC-GAP-05, VEC-GAP-07.

---

## Category 11 — Config, Presets & Registry

**Problem:** Missing presets, registry stubs, and model defaults prevent parametric generation for some instruments.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| GAP-02 | 24-Fret Strat | No 24-fret Stratocaster preset in `NECK_PRESETS` | MEDIUM |
| GAP-08 | 24-Fret Strat | Strat model hardcodes `fret_count=22` — no parameterization | MEDIUM |
| NECK-02 | Strat Neck | No canonical `stratocaster.json` spec file | MEDIUM |
| NECK-03 | Strat Neck | Strat registry status is STUB — enum only, no linked spec | LOW |
| EX-GAP-11 | Explorer 1958 | No `body_outlines.json` entry for Explorer | LOW |

### Fixes

1. **Strat preset + spec** — Create `stratocaster.json` spec, add 22-fret and 24-fret presets to `NECK_PRESETS`, parameterize `fret_count`. Resolves GAP-02, GAP-08, NECK-02, NECK-03.
2. **Explorer outline entry** — Extract 200+ point contour from DXF, add to `body_outlines.json`. Resolves EX-GAP-11.

---

## Category 12 — Accuracy & Position Validation

**Problem:** Cavity positions, hardware mounting holes, and bridge/tailpiece positions are heuristic estimates — no verification against factory drawings or measured instruments.

| Gap ID | Instrument | Description | Severity |
|--------|-----------|-------------|----------|
| LP-GAP-02 | Les Paul 1959 | Cavity positions are heuristic center-offset approximations, unvalidated | HIGH |
| EX-GAP-04 | Explorer 1958 | Pickup positions from general Gibson specs, not verified for Explorer | HIGH |
| EX-GAP-05 | Explorer 1958 | Control cavity estimated — 1958 vs reissue routing differences | MEDIUM |
| EX-GAP-06 | Explorer 1958 | Toggle switch position varies by production year — no factory template | MEDIUM |
| EX-GAP-07 | Explorer 1958 | Bridge/tailpiece stud positions use generic Gibson spacing | MEDIUM |
| EX-GAP-08 | Explorer 1958 | Neck tenon dimensions estimated from Les Paul pattern | MEDIUM |
| EX-GAP-09 | Explorer 1958 | Pot layout simplified, wiring channels may intersect structural wood | LOW |
| EX-GAP-10 | Explorer 1958 | Output jack position estimated, no angle applied | LOW |

### Fixes

1. **Reference measurement database** — Create `data/reference_measurements/` with verified dimensions from factory drawings, measured instruments, or published luthier references. Each instrument gets a `{model}_reference.json`.
2. **Position validator** — `scripts/validate_cavity_positions.py` compares spec JSON positions against reference measurements, flags deviations > threshold.
3. **Per-instrument position audit** — Systematic measurement verification using published Gibson factory specs, StewMac templates, or direct instrument measurement. Priority: Les Paul (LP-GAP-02), Explorer (EX-GAP-04 through EX-GAP-10).

---

## Category 13 — Physical Component Geometry ⏸️ TABLED

**Problem:** Pickup positions, body centerline computation, and cavity-to-coordinate mapping all depend on physical hardware details (pickup dimensions, mounting ring specs, string spacing, bridge saddle geometry) that must be measured or sourced from manufacturer data before the software can be finalized. The math foundations exist (`fret_math.py`, `bridge/placement.py`, `body_outlines.json`) but the calculator that ties them together requires physical-world inputs that aren't settled yet.

**Status:** ⏸️ **TABLED** — These gaps are real and block production-accurate builds, but require physical measurements and hardware decisions to be worked out first. Will be unblocked once reference pickup dimensions and mounting specs are confirmed.

| Gap ID | Scope | Description | Severity | Physical Dependency |
|--------|-------|-------------|----------|--------------------|
| PHYS-01 | All electrics | **Pickup position calculator** — No `calculators/pickup_layout.py` exists. Positions are hardcoded per build script. Needs: scale length + fret count + pickup config (SSS/HSS/HH) + clearance rules → cavity center positions (mm from bridge) | CRITICAL | Pickup body dimensions, pole spacing, mounting ring footprint per manufacturer |
| PHYS-02 | All instruments | **Body centerline calculator** — No function computes the geometric centerline/midline from body outline data. Convention assumes `width/2` but asymmetric bodies (Explorer, Flying V) need true symmetry-axis computation | HIGH | Body outline point data must be verified against physical templates |
| PHYS-03 | All electrics | **Pickup cavity-to-coordinate mapper** — Build scripts compute `spec_to_gcode()` inline with hardcoded offsets. Need a reusable function: given pickup position (mm from bridge) + body outline + centerline → CNC cavity coordinates | HIGH | Bridge saddle line position varies by hardware (TOM, trem, hardtail) |
| PHYS-04 | 24-fret instruments | **Neck pickup collision detection** — Fret 24 at 161.73mm from bridge collides with standard neck pickup at ~162mm. The 12mm clearance shift is documented but not codified. Needs fret position data + pickup body width | CRITICAL | Physical pickup cover width per model (single-coil vs humbucker footprint) |
| PHYS-05 | Les Paul, Explorer, SG | **Humbucker mounting ring geometry** — HH and HSH configs need ring dimensions (flat vs slanted, pickup tilt angle, screw hole spacing) to generate accurate cavity outlines | MEDIUM | Ring dimensions vary by manufacturer (Gibson, Seymour Duncan, DiMarzio, etc.) |
| PHYS-06 | All electrics | **String spread at pickup position** — Pickup pole pieces must align with strings. String spacing changes along the scale length (wider at bridge, narrower at nut). Need: nut width + bridge spacing + position → string spread at any point | MEDIUM | Nut slot spacing, bridge saddle string spread — hardware-specific |

### What exists today

| Building block | Location | Status |
|---|---|---|
| Fret position math (equal temperament) | `instrument_geometry/neck/fret_math.py` | ✅ Complete |
| Bridge placement from scale length | `instrument_geometry/bridge/placement.py` | ✅ Complete |
| Body outline point data | `instrument_geometry/body/body_outlines.json` | ✅ Data exists (no centerline calc) |
| Pickup cavity G-code (hardcoded) | `scripts/generate_smart_guitar_full_build.py` | ⚠️ Works but not reusable |
| Pickup cavity G-code (hardcoded) | `scripts/generate_les_paul_full_build.py` | ⚠️ Works but not reusable |
| Grid-based centerline (normalized) | `blueprint-import/classifiers/grid_zone/zones.py` | ⚠️ Normalized only, not mm |

### What needs to happen (when unblocked)

1. **Gather physical reference data** — Pickup body dimensions, mounting ring specs, and bridge saddle positions for target hardware (Gibson, Fender, generic). Store in `data/reference_measurements/pickup_hardware.json`.
2. **`calculators/pickup_layout.py`** — Pure math module: `compute_pickup_positions(scale_length_mm, fret_count, pickup_config, body_style) → List[PickupPosition]`. Uses `fret_math.py` for collision detection on extended fretboards.
3. **`instrument_geometry/body/centerline.py`** — `compute_body_centerline(outline_points) → float` for symmetric bodies, `compute_symmetry_axis(outline_points) → (x, angle)` for asymmetric.
4. **`instrument_geometry/pickup/cavity_placement.py`** — Combines pickup positions + centerline + bridge placement → CNC-ready cavity center coordinates. Replaces inline `spec_to_gcode()` in build scripts.
5. **Integrate into build scripts** — Replace hardcoded offsets in `generate_smart_guitar_full_build.py` and `generate_les_paul_full_build.py` with calculator calls.

---

## Priority Roadmap

### Phase 1 — Unblock CNC Production (Critical gaps)

| Fix | Resolves | Impact |
|-----|----------|--------|
| DXF regeneration pipeline | LP-GAP-01, EX-GAP-01/02/03, SG-GAP-01/02, ~~VINE-09~~ | **6 critical** (VINE-09 resolved) — remaining builds blocked |
| Body perimeter profiling module | OM-GAP-02, BEN-GAP-03, VINE-07, FV-GAP-03 | **4 high** — 4 instruments can't cut outlines |
| Binding/purfling CAM module | OM-GAP-03/04, BEN-GAP-01/02, OM-PURF-01/02 | **4 critical + 2 high** — acoustics blocked |
| SVG→DXF converter | VINE-02 | **1 critical** — all art→CAM blocked |
| Pickup position calculator | GAP-04, PHYS-01 | **1 critical** — all Strat work blocked ⏸️ (physical deps) |

### Phase 2 — Complete Core Generators

| Fix | Resolves | Impact |
|-----|----------|--------|
| Headstock outlines (5 shapes) | NECK-01, GAP-01, OM-GAP-06, BEN-GAP-06, VINE-06 | 5 instruments unblocked |
| Strat body outline generator | GAP-07 | Strat production enabled |
| Neck CNC pipeline | LP-GAP-03 | Full-instrument builds enabled |
| Mount existing routers | VINE-08, VINE-04, INLAY-01 | 3 modules go live with zero new code |
| Post-processor G43/G41 | LP-GAP-06, EX-GAP-13, SG-GAP-14, OM-PURF-07, FV-GAP-07 | Safety + automation for all builds |

### Phase 3 — Polish & Validation

| Fix | Resolves | Impact |
|-----|----------|--------|
| Spec JSON validator | SG-GAP-03 through SG-GAP-12 | Data quality |
| Reference measurement DB | LP-GAP-02, EX-GAP-04 through EX-GAP-10 | Position accuracy |
| Vectorizer Phase 3/4 API | VEC-GAP-01 through VEC-GAP-08 | Blueprint→CAM pipeline |
| Frontend wiring | INLAY-02/06, NECK-05, VEC-GAP-06 | UI completeness |
| G-code depth validator | LP-GAP-08, EX-GAP-12, SG-GAP-13 | Build safety |
