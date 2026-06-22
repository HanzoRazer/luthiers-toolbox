# System Conflation Audit — 2026-06-21

> Canonical path: `docs/governance/audits/SYSTEM_CONFLATION_AUDIT_2026-06-21.md`. This is a **point-in-time snapshot**; for current state, look for a newer dated audit in the same directory.

**Repository:** luthiers-toolbox (this git repo only)
**Branch audited:** `ci-red-022-merge` (HEAD `20b734ff`)
**Date:** 2026-06-21
**Audit type:** Classification-only governance audit. **No** migration, refactor, rewrite, or remediation recommendations are made. The question answered is *what exists, what overlaps, what is authoritative, what is active, what is duplicate, what is legacy, what should be retired, and what is unknown* — **not** "how do we fix it."

> **Branch caveat.** This audit reflects the working tree as checked out on `ci-red-022-merge`, a CI-RED merge branch ahead of `main`. Classifications keyed to "recently merged" PRs and to mounted-vs-unmounted router state were verified against this branch. Findings *may differ from `main`*: CI-RED work (manufacturing-replay recovery #142/#143, saw-batch complexity #144, file-size baselines) is present here and may be partially or differently represented on `main`. Anything used for an irreversible decision should be re-confirmed against `main`.

---

## Scope & Boundary Systems

**In scope:** everything committed to *this* repository — backend (`services/api/app`, `services/blueprint-import`, `services/photo-vectorizer`), frontend (`packages/client`), and the loose root / prototype / archive material.

**Out of scope (boundary systems — internals NOT classified here).** These are separate external repos symlinked under `docs/audit-sources/`. They are noted only where they create cross-repo conflation or future reintegration pressure:

- **vectorizer-sandbox** — *Boundary note (recorded per owner):* vectorizer-sandbox is an experimental repo created to develop the Image Body Generator / IBG. Its purpose is to learn what a musical instrument looks like and eventually serve as the agentic guidance layer for the Blueprint Reader and photo vectorizer. When mature, selected capability may be incorporated back into luthiers-toolbox. → **Reintegration pressure point.** In-repo references to its experimental "three-loop / AGE" design (CLAUDE.md, `THREE_LOOP_ARCHITECTURE_REFRAMED.md`, several handoffs) are stale design sketches, not owed runtime work (corrected 2026-05-30, PR #78).
- **tap_tone_pi** — external acoustic tap-tone analysis repo. Couples to this repo only as a *data producer*: this repo's `app.rmos.acoustics.importer` ingests its `TapToneBundleManifestV1`. No code/import coupling. The "vectorizer AGE mirrors tap_tone_pi" claim is conflation (separate repo, opposite-kind engine).
- **CNC-Production-Shop**, **ltb-woodworking-studio** — separate workspace repos; woodworking-studio is intentionally independent (own wood data, own schema, no HTTP dependency on this repo).

**Methodology.** Evidence was gathered by parallel exploration of: the FastAPI router-mount graph, the Vue router table, API clients, test suites, governance manifests/registries, git history of recent PRs, and `git ls-files` / `du` for bloat quantification. Where two evidence passes disagreed, the conflict is recorded explicitly (see ⚠️ markers) rather than resolved by assertion. Where evidence was insufficient, the item is `UNKNOWN`.

---

## Executive Summary

Approximately **80 subsystems** were examined across backend, frontend, and loose artifacts. The repository is **not chaotic** — it has a real, actively-maintained governance spine (router registry, CAM capability/ontology registries, CI fence/ratchet apparatus) and clear canonical implementations for every major *design surface*. The conflation that exists is concentrated in three places: (1) **consolidation shells that were started and not finished** (Aperture/Inlay/Soundhole-Rosette workspaces, CAM aggregator phases), (2) a **large mass of unmounted/never-routed code** (dead routers, ~21 orphaned Vue views), and (3) **multi-gigabyte untracked working-tree clutter** (all correctly gitignored, so not in history).

| Classification | Count (approx.) | Where it concentrates |
|---|---:|---|
| **AUTHORITATIVE** | ~22 | Router registry, design-surface engines (rosette, soundhole, inlay, fretboard, relief, headstock), vectorizer_phase3, dxf_compat, RMOS runs_v2, lutherie system prompt, CI governance apparatus |
| **ACTIVE** | ~28 | CAM intent lanes 8G–8J, prompt modules, agentic spine, GeometryCoachV2, AI image gen, saw lab, guitar-model CAM routers, support calculators, consolidation shells (beta, additive), photo_vectorizer_v2 |
| **DUPLICATE** | ~8 | ApertureWorkspace shell, api_v1 surface, dxf_consolidator vs layer_consolidator, old acoustics routers, DesignFirstWorkflowPanel v1/v2, soundhole router pair |
| **LEGACY** | ~12 | edge_to_dxf, blueprint-reader.html, BlueprintAnalyzer, spiral acoustic models (root), roughing intent, inlay_calc, archived prototypes, Girih/INLAY root dumps, three-loop in-repo refs |
| **RETIRE** | ~6 | production_shop_agent, ~21 orphaned Vue views, removed ai/prompts/templates, disposable root test_*.txt dumps |
| **UNKNOWN** | ~9 | phase4 dimension linker, pickguard (absent), Curvelab cluster, probe/retract subsystems (⚠️ contested), acoustics-ingest path mismatch (⚠️ contested), Guitar Plans/ library, scattered pattern registry, large unmounted-router cohort |

Counts are approximate because several "subsystems" are clusters (e.g. "~21 orphaned views" counts as one RETIRE entry). Two evidence conflicts surfaced during the sweep and were **resolved by direct verification** (✅): the CAM aggregator is confirmed **ACTIVE** (the "55% dead routers" figure was inflated by indirect mounts), and the acoustics-ingest UI is confirmed **divergent and unwired** (backend audit router unmounted; FE/BE paths disagree). Details in the conflation table.

---

## Canonical Authority Map

| Authority domain | Canonical / authoritative system | Status |
|---|---|---|
| **Generator system (CAM operations)** | CAM intent lanes via `cam/routers/aggregator.py` → `/api/cam/<op>/intent-gcode` (CamIntentV1) | Authoritative for 4 lanes (vcarve/profile/drilling/pocketing); others partial |
| **Prompt system** | `app/ai/lutherie_system_prompt.py` (read-only reference values) + **domain-delegated** prompt modules (vision, headstock, rosette) | Authoritative reference + coherent delegation. **No single prompt registry** — by design, not by accident |
| **Geometry system (image→geometry)** | `services/blueprint-import/vectorizer_phase3.py` (`_raw_extract` = V2) for blueprints; `photo_vectorizer_v2.py` for photos | Two canonical engines, **different input domains** (not duplicates) |
| **Validation system (governance/CI)** | `scripts/governance/check_all.py` (tiered) + fence/ratchet baselines + `/api/_meta/routing-truth` witness | Authoritative, actively maintained (baselines updated 2026-06-20/21) |
| **Validation system (geometry/scale)** | `validate_scale_before_export` / `_safe_dxf_save` (vectorizer_phase3 + `app/services/scale_validation.py`) | Authoritative, shipped, independent of the (sandboxed) loop architecture |
| **Export system (DXF)** | `dxf_compat` (enforced gateway; R12 free / R2000 paid). Direct `ezdxf.new()` forbidden | Authoritative |
| **Surface-designer (soundhole)** | `SpiralSoundholeDesigner.vue` + `calculators/soundhole_facade.py` | Authoritative (canonical per CLAUDE.md); `ApertureWorkspace.vue` is a beta shell that *mounts* it |
| **Manufacturing run lifecycle** | `app/rmos/runs_v2/` | Authoritative |
| **Router mounting / dispatch** | `app/router_registry/` (manifest + loader) | Authoritative — but **not the only** mount path (see Dispatch Layer Analysis) |

**Where authority is unclear (stated explicitly):**
- **Probe** and **Retract** CAM subsystems: contested between "dead/unmounted" and "functional legacy." → `UNKNOWN`.
- **Acoustics**: three+ routers touch acoustics (`routers/acoustics/plate`, `rmos/runs_v2/acoustics`, `rmos/acoustics/*`). Wave-22 consolidation designates `rmos/runs_v2/acoustics_router` canonical and disables the old query/attachments routers, but `plate`/`radius_dish` remain mounted. Authority is *declared* but not *singular*.
- **CAM aggregator** as canonical generator dispatch: real, but its phase set is partly disabled and its dead-code footprint is contested (⚠️).

---

## System Conflation Table

| System | Purpose | Overlaps With | Evidence of Use | Classification | Notes |
|---|---|---|---|---|---|
| `router_registry/` (manifest+loader) | Canonical router mounting | api_v1, websocket, analytics mounts | Mounts ~143 routers; startup logging; load-order guards | **AUTHORITATIVE** | Not the sole mount path |
| `api_v1/` curated surface | "Golden path" stable API (10 sub-routers) | router_registry | Mounted via direct `include_router` in `main.py` | **DUPLICATE** | Second stable-API surface outside registry |
| `cam/routers/aggregator.py` | Consolidate CAM op routers under `/api/cam` | legacy CAM paths | **Verified:** 1 manifest entry (`app.cam.routers`) mounts ~16 sub-routers via `cam_router.include_router` (drilling, fret_slots, relief, risk, rosette, simulation, toolpath, export, monitoring, pipeline, utility, profiling, pocketing, binding, vcarve) | **ACTIVE** ✅ | Conflict **resolved**: backend pass called it LEGACY/abandoned, but direct read of `aggregator.py` confirms it is the live CAM dispatch and mounts its sub-routers indirectly. The backend pass's "131/240 unmounted (55% dead)" is **inflated** — these CAM op routers are reachable, just not as top-level manifest entries |
| Unmounted router cohort (genuinely-dead subset) | Various | — | After excluding aggregator/api_v1 indirect mounts, a smaller real cohort remains (e.g. probe/retract, instrument-geometry split, business analytics) | **UNKNOWN** | The headline "55% dead" is wrong (indirect mounts). The *residual* genuinely-unmounted set (dead vs library-only) was not exhaustively separated this pass |
| CAM capability/ontology/governance registries (translator, canonical_ontology, governance_freeze, manufacturing_replay, federated_semantic, geometry_authority, review_ux…) | CAM governance tiers | each other (by tier, not duplicate) | Used by mounted CAM routers; replay recovered in CI-RED-023 (#142/#143) | **ACTIVE** | Domain-driven, not conflation |
| `data_registry/` | Config/product authority | — | Mounted `/api/registry` | **ACTIVE** | |
| `governance/endpoint_registry.py` | Classify endpoints canonical/legacy/shadow | routing-truth | ~12 entries only | **ACTIVE** | Sparse coverage |
| Scattered prompt modules (lutherie/vision/headstock/rosette) | Domain prompts | — | All imported by their domains | **ACTIVE** | No central registry — coherent delegation |
| `art_studio/services/pattern_store.py` + scattered `*patterns.py` | Pattern storage | — | art_studio has store; others are library modules | **UNKNOWN** | Inconsistent registration |
| CI governance apparatus (`scripts/governance/*`, fences, ratchets) | Gate enforcement | — | Tiered runner; baselines updated 06-20/21 | **AUTHORITATIVE** | |
| `art_studio/services/rosette_engine.py` (+ design/geometry/svg/recipes) | Rosette generation | cam/rosette prototypes | Routed; 30+ FE components; recent commits | **AUTHORITATIVE** | |
| `components/rosette/*` (RosetteEditorView…) | Rosette FE | RosettePipelineView | 22 components, routed | **ACTIVE** | |
| `cam/rosette/prototypes/` (17 generators) | Specific rosette CAM generators (Spanish/wave/rope/celtic/herringbone) | rosette_engine | In-production CAM generators (not archive) | **ACTIVE** | Unique IP; authority boundary vs pattern library unclear |
| `docs/archive/rosette_designer_history/` (v2–v5 HTML) | Prior rosette UIs | rosette_engine | Archive location | **LEGACY** | |
| `calculators/soundhole_facade.py` (+ soundhole_*.py) | Soundhole types (round/oval/spiral/fhole) | aperture_geometry | 161 tests; routed; recent commits | **AUTHORITATIVE** | |
| `SpiralSoundholeDesigner.vue` | Canonical spiral designer | ApertureWorkspace | Routed `/calculators/acoustics/spiral-soundhole` | **AUTHORITATIVE** | Canonical per CLAUDE.md |
| `views/art-studio/ApertureWorkspace.vue` | Beta consolidation shell | SpiralSoundholeDesigner | Mounts the canonical; Dev Orders 5–72 incomplete | **DUPLICATE** | Beta shell (State 3); additive, parity not verified |
| `routers/instrument/soundhole_router.py` **and** `routers/instrument_geometry/soundhole_router.py` | Soundhole endpoints | each other | Both present | **DUPLICATE** | Competing pair |
| `instrument_geometry/soundhole/aperture_geometry.py` | Normalized cross-type geometry | facade | Used by comparison panels | **ACTIVE** | |
| `art_studio/services/generators/inlay_*` (10 modules) | Inlay/marquetry engine | inlay_calc, root txt | Routed; tested; decomposed 2026-03 | **AUTHORITATIVE** | |
| `components/art/art_studio_inlay/ArtStudioInlay.vue` | Inlay designer FE | — | Composables; recent commits | **AUTHORITATIVE** | |
| `calculators/inlay_calc.py` | Older inlay calculator | inlay engine | Possibly fallback | **LEGACY** | |
| `generators/neck_headstock_generator.py` (+ config/enums/geometry/presets) | Headstock generator | headstock html | Structured suite; routed | **AUTHORITATIVE** | |
| `HeadstockTransitionPanel.vue` + `headstock_break_angle.py` | Neck/headstock junction | — | Recent commits; calc active | **ACTIVE** | |
| `archive/experimental/2026-03/Interactive_Headstock_Generator/headstock-designer.html` | Standalone HTML designer | generator suite | Archive | **LEGACY** | |
| Fretboard/fret suite (`fret_*_calc.py`, ecosphere, FE panels) | Fret math/slots/CAM | — | Tests; ecosphere roundtrip; routed | **AUTHORITATIVE** | |
| Binding/purfling (`binding_*.py`, `cam/binding/*`) | Binding/purfling geometry+CAM | — | Routed; no dedicated FE | **AUTHORITATIVE** | FE access via generic CAM |
| Relief/engraving (`services/relief_*`, `ArtStudioRelief.vue`) | Relief carving | surface_carving | Routed; FE composables | **AUTHORITATIVE** | |
| `Girih-5 ... .txt`, `INLAY_PATTERN_GENERATORS.txt` (root) | Design generators (text) | inlay engine | Not imported; "Production Shop" IP | **LEGACY** | Unique IP reference, not wired |
| Pickguard | Design surface | — | **No implementation** (reference PDFs only) | **UNKNOWN** | Absent surface |
| `vectorizer_phase3.py` (`_raw_extract`=V2) | Blueprint→DXF | photo_vectorizer | Routed `/api/blueprint/vectorize`; scale gate; tests | **AUTHORITATIVE** | |
| `photo_vectorizer_v2.py` | Photo/AI→DXF | vectorizer_phase3 | Routed `/api/vectorizer/extract`; PhotoOrchestrator | **ACTIVE** | Different input domain — not duplicate |
| `edge_to_dxf.py` | Edge archival (100k–600k LINEs) | vectorizer_phase3 | Endpoint exists; not in auto pipeline; no tests | **LEGACY** | Rejected for production (text garbled) |
| `dxf_compat.py` | Version-aware DXF gateway | — | Required by all consolidators; CI verified | **AUTHORITATIVE** | |
| `dxf_consolidator.py` | RAW LINE→LWPOLYLINE + body classify | layer_consolidator | CAM-integrated | **DUPLICATE** | Overlaps layer_consolidator (different approach) |
| `layer_consolidator.py` | LINE→LWPOLYLINE preserving layers | dxf_consolidator | Lifecycle-guard tests | **ACTIVE** | Preferred for blueprints |
| `contour_reconstruction.py` | Chain LINE/ARC→closed loops (VINE-09) | — | Routed | **ACTIVE** | Distinct problem |
| `toolpath/dxf_exporter.py` | Legacy toolpath DXF | dxf_compat path | No active pipeline integration | **LEGACY** | |
| `blueprint-reader/index.html` (root) | Browser measurement tool | vectorizer | Standalone; canonical IBG intake per memory | **LEGACY** | Frontend-only; not in auto pipeline |
| `services/blueprint-import/phase4/` | OCR→dimension linker (R&D) | phase3 OCR | `PHASE4_AVAILABLE` flag; not called | **UNKNOWN** | Incomplete R&D |
| Scale-validation gate | Pre-export dimension sanity | — | Shipped; tests; centralized copy | **ACTIVE** | Independent of loop architecture |
| Three-loop / AGE (in-repo references) | Experimental feedback architecture | vectorizer-sandbox | Never built in runtime; demoted 2026-05-30 (#78) | **LEGACY** | Sandbox-owned; refs are stale sketches |
| `GeometryCoachV2` | Vectorizer retry/inspection coach | — | Wired into photo orchestrator; 15 tests | **ACTIVE** | Live; protected |
| Agentic Spine (`app/agentic/router.py` + CoachBubble/IdleDetector/store) | Moment→policy→advisory UI | — | Mounted `/api/agentic`; FE wired end-to-end | **ACTIVE** | Minimal advisory; not three-loop |
| `services/blueprint-import/analyzer.py` (BlueprintAnalyzer) | Claude-vision blueprint analysis | vision prompt engine | Present; not wired to live extraction | **LEGACY** | |
| AI image gen (`features/ai_images`, `vision/generation_router`) | Guitar image generation + review | — | Routed `/ai/images`; full pipeline | **ACTIVE** | |
| `app/ai/prompts/templates.py` | Old prompt templates | lutherie prompt | Removed in Phase 4 remediation | **RETIRE** | |
| `production_shop_agent/` (root) | Marketing-site generator service | — | Not wired into main app; no FE refs | **RETIRE** | Orphaned standalone service |
| `app/rmos/runs_v2/` | Manufacturing run lifecycle | — | Authoritative RMOS surface; 50+ modules | **AUTHORITATIVE** | |
| RMOS engines/feasibility/advisory/analytics | RMOS support | — | All imported/routed | **ACTIVE** | |
| `rmos/runs_v2/acoustics_router.py` (Wave 22) | Canonical acoustics API | old acoustics routers | Routed `/api/rmos/acoustics` | **AUTHORITATIVE** | |
| `routers/acoustics/*` (plate/radius active; query/attachments disabled) | Older acoustics API | Wave-22 router | plate/radius mounted; query/attach superseded | **DUPLICATE** | Partial supersession |
| `rmos/acoustics/importer` (tap-tone ingest) | Ingest TapToneBundleManifestV1 | — | Bridges external tap_tone_pi | **ACTIVE** | |
| `views/tools/AcousticsIngestEvents.vue` (+ `rmos/acoustics/router_ingest_audit.py`) | Ingest event viewer + its backend | each other | **Verified divergent & unwired** | **RETIRE / broken pair** ✅ | Conflict **resolved against** the "no mismatch" read. FE fetches `/acoustics_ingest/` (`AcousticsIngestEvents.vue:209`); backend defines `ingest_events`/`/ingest` (`router_ingest_audit.py`) — paths diverge **and** `router_ingest_audit` is **absent from all manifests** (unmounted). Feature is not functional end-to-end |
| `spiral_acoustic_model.py`, `spiral_q_fh_solver.py` (root) | Spiral port acoustics (research) | soundhole physics | Tests exist; not wired to API/FE | **LEGACY** | Research-grade, self-contained |
| CAM intent lanes 8G–8J (vcarve/profile/drilling/pocketing) | Op→gcode | roughing intent | Backend+route+FE wired (#88/#92/#93/#97/#100/#101/#108) | **ACTIVE** | Canonical CAM op pattern |
| `cam_roughing_intent_router.py` | Roughing intent (legacy pattern) | 8G–8J | Mounted; reuses legacy handler | **LEGACY** | Pre-8G pattern |
| `views/cam/SurfacingView.vue` | Surfacing op UI | — | Routed; **no backend intent lane / no API client** | **UNKNOWN** | Orphaned UI |
| `views/cam/FretSlottingView.vue` | Fret-slot op UI | fret_slots preview | Preview-only; generate button gated (#106) | **ACTIVE** | Partial (gated) |
| Guitar-model CAM routers (acoustic/archtop/strat/om/flying_v + registry fallback) | Per-model CAM | each other | Consolidated w/ explicit mount order | **ACTIVE** | Organized, not conflating |
| `app/saw_lab/` (batch + 7 calculators) | Saw batch manufacturing | — | Mounted (required); 17 files; CI-RED-003 #144 | **AUTHORITATIVE** | |
| Probe subsystem (`routers/probe/*`, 7) | Probe/measure | — | Backend pass: all unmounted; CAM pass: functional legacy | **UNKNOWN** ⚠️ | Contested |
| Retract subsystem (`routers/retract/*`, 4) | Retract patterns | — | Backend pass: unmounted | **UNKNOWN** ⚠️ | Contested |
| CAM governed export (7-layer) | Geometry→machine output | — | Layers 1–3 complete; 4–6 defined; 7 quarantined | **ACTIVE** | Machine output intentionally gated off |
| Toolpath player (`components/cam/toolpath-player`, 21–35 files) | G-code visualization | — | Routed via ToolpathSimulatorView | **ACTIVE** | Mature |
| `views/cam/CamWorkspaceView.vue` | Unified CAM workspace (neck wizard) | op views | Routed; neck-specific Phase-1 | **ACTIVE** | Incomplete consolidation (scope-limited) |
| ~21 orphaned Vue views (ArtJobDetail, ArtStudioUnified, CamProductionView[corrupt], RMOSCnc*, Post*, SawLabDashboard…) | Various | their routed successors | Zero routes, zero imports | **RETIRE** | See Surface/Frontend section |
| Consolidation shells (InlayWorkspaceShell, SoundholeRosetteShell, CamWorkspaceView) | Multi-surface consolidation | canonical surfaces | Routed; additive; mount legacy | **ACTIVE** | Beta (State 3); policy-compliant |
| `DesignFirstWorkflowPanel.vue` vs `…V2.vue` | Rosette workflow panel | each other | Both present | **DUPLICATE** | No deprecation path |
| `components/curvelab/*` (4) | Curve lab utility | — | No routed view found | **UNKNOWN** | Orphaned or internal-only |

---

## Domain Conflation Analysis

For each major concept: does it have **one canonical home**, **multiple competing homes**, or **no clear authority**?

| Concept | Verdict | Detail |
|---|---|---|
| **Marquetry** | One canonical home | `art_studio/services/generators/inlay_*` (marquetry is part of the inlay engine). HTML "marquetry_engine" prototypes are archived LEGACY. Root `INLAY_PATTERN_GENERATORS.txt` is unwired IP. |
| **Inlay** | One canonical home (+ legacy calc) | `inlay_*` engine + `ArtStudioInlay.vue`. `calculators/inlay_calc.py` is LEGACY shadow. |
| **Rosette** | One canonical home, **but a real authority boundary** | `rosette_engine.py` (pattern library) **vs** `cam/rosette/prototypes/` (17 in-production type-specific generators). Both active; which path owns which rosette type is not crisply defined. |
| **Prompt generation** | One reference + delegated homes | `lutherie_system_prompt.py` is the read-only authority; domain prompt modules (vision/headstock/rosette) are intentionally separate. **No** central prompt registry. Coherent. |
| **Geometry generation (image→geometry)** | Two canonical homes by domain | `vectorizer_phase3` (blueprints) + `photo_vectorizer_v2` (photos). Complementary, not competing. `edge_to_dxf` is LEGACY archival. |
| **SVG generation** | Distributed, no single authority | rosette_svg, inlay_geometry_svg, wave_rosette_preview.svg, frontend canvases. Each surface emits its own SVG. Not consolidated; not obviously conflated. |
| **Manufacturing validation** | One canonical home | RMOS `runs_v2` + feasibility engines + CAM governed-export gates. |
| **Surface design** | One canonical per surface; consolidation in progress | Each surface (soundhole/rosette/inlay/relief/headstock/fretboard) has a canonical implementation; the *workspaces* that try to unify them are beta shells. |
| **Acoustics** | **No single authority (declared, not singular)** | Wave-22 declares `rmos/runs_v2/acoustics_router` canonical, but `routers/acoustics/plate`+`radius_dish` stay mounted and `rmos/acoustics/*` provides ingest. Plus unwired root spiral-acoustics research models. |
| **DXF export** | One enforced gateway, multiple consolidators | `dxf_compat` is the authority. Beneath it, `dxf_consolidator` vs `layer_consolidator` overlap; `contour_reconstruction` is distinct. |

---

## Dispatch Layer Analysis

| Dispatch / registry | Type | State |
|---|---|---|
| `router_registry/` (manifest + loader) | Router mounting | **Authoritative** — primary mount path (~143 routers) |
| `api_v1/` aggregator | Router mounting | **Duplicate** — second curated surface, mounted directly in `main.py`, outside the registry |
| WebSocket + Analytics + Saw-Lab-batch fallback mounts in `main.py` | Router mounting | **Active** special cases — bypass the registry; analytics is env-gated; saw-lab has a fallback `add_api_route` guard |
| `cam/routers/aggregator.py` | Generator/op dispatch | **Active** ✅ — verified mounts ~16 CAM op sub-routers under one `/api/cam` manifest entry. Confirms the "55% dead" router figure was inflated by indirect mounts. (Whether the *residual* genuinely-unmounted set is dead vs library support is still `UNKNOWN`.) |
| CAM governance registries (translator_capability, canonical_ontology, governance_freeze, manufacturing_replay, federated_semantic, geometry_authority, review_ux/queue) | Capability/ontology registries | **Active** — declarative governance, tiered; replay recovered CI-RED-023 |
| `data_registry/` | Service/config locator | **Active** |
| `rmos/engines/registry.py` | Engine plugin registry | **Active** |
| `governance/endpoint_registry.py` | Endpoint classification | **Active, sparse** (~12 entries) |
| Prompt "registry" | — | **Does not exist as a registry** — prompts are domain-delegated modules. Not an abandoned consolidation; a deliberate non-centralization |
| Pattern "registry" | Pattern storage | **Partial** — art_studio has a store; drilling/probe/retract patterns are plain library modules. `UNKNOWN` whether consolidation was ever intended |

**Abandoned consolidation signal:** the **CAM aggregator's disabled phases** and the **api_v1 second-surface** are the clearest "started, not finished / two ways to do the same thing" dispatch artifacts.

---

## Surface Pattern Analysis

Inventory of design surfaces and completeness:

| Surface | Most complete / reference impl | Completeness | Notes |
|---|---|---|---|
| **Soundhole** | `SpiralSoundholeDesigner.vue` + `soundhole_facade.py` | **Full** (canonical) | Reference implementation for the "canonical + beta shell" pattern |
| **Rosette** | `rosette_engine.py` + `RosetteEditorView` + `RosettePipelineView` | **Full** | Richest surface (30+ FE components, 17 CAM prototypes) |
| **Inlay / Marquetry** | `inlay_*` engine + `ArtStudioInlay.vue` | **Full** | 10-module backend |
| **Fretboard / Fret slotting** | fret calc suite + ecosphere + FE panels | **Full** | Strong test coverage (ecosphere roundtrip) |
| **Relief / Body engraving** | relief subsystem + `ArtStudioRelief.vue` | **Full** | |
| **Headstock** | `neck_headstock_generator` + transition panel | **Full** | + headstock inlay subsurface |
| **Binding / Purfling** | `binding_*` + `cam/binding/*` | **Backend-complete, FE-partial** | No dedicated FE designer; generic CAM access |
| **Pickguard** | — | **Absent** | Reference PDFs only; no code (`UNKNOWN`) |
| **Soundhole comparison / aperture unification** | `ApertureWorkspace.vue` | **Partial (beta shell)** | Mounts canonical; parity not verified |

**Most complete surface:** Rosette and Soundhole are tied for richest. **Reference implementation** for how a surface *should* be structured (canonical impl + governed beta consolidation shell): **Soundhole**. **Partial implementations:** Binding (no FE), Pickguard (absent), the unification *workspaces* (beta).

---

## Repository Bloat Analysis (quantified, classification-only)

**Total on-disk ≈ 11 GB; git-tracked = 5,764 files.** The defining finding: **virtually all multi-GB bloat is UNTRACKED and correctly gitignored** — it clutters the working tree but is **not** in git history. Tracked footprint is dominated by code + a large documentation corpus.

### Untracked working-tree clutter (gitignored — not in history)

| Category | Size (on-disk) | Count | Classification |
|---|---:|---:|---|
| Root `test_*.dxf` (incl. `test_Benedetto_Front_REFINED.dxf` = **1.2 GB**) | ~2.5 GB | 10 | **LEGACY** (test output) |
| `Guitar Plans/` (PDFs, CAD, PSDs, vendor ZIPs) | 2.8 GB | 632 | **UNKNOWN** (reference library; licensing/active-use unclear) |
| `artifacts/` (benedetto/march/pv2 vectorizer outputs) | 1.5 GB | 41 | **LEGACY** (vectorizer test output) |
| `phase4_output/` untracked variants | ~1.5 GB | 87 | **LEGACY** (8 geometry-only files ARE tracked → ACTIVE reference) |
| `.venv/` | 584 MB | — | gitignored dev env (correct) |
| `services/photo-vectorizer/test_*` output dirs (sprint5_benedetto = 312 MB) | ~330 MB | 13 | **LEGACY/ACTIVE mix** (test code tracked; outputs not) |
| `exports/` (vectorizer/regression baselines) | 64 MB | 132 | **UNKNOWN** (regression suite active?) |
| Root images (Benedetto jpgs, ChatGPT pngs, flamed-maple) | 23 MB | 11 | **UNKNOWN** (reference vs export) |
| Root `.txt` dumps | ~5 MB | 54 | **mixed** — see below |
| `wood-density-Cirad-master.zip`, `recovery_triage.docx` | ~2 MB | 2 | reference/notes |

### Root `.txt` dumps (54 files — 53 untracked, 1 tracked)

- **Disposable test output** (`test_*.txt`, `pytest_failures.txt` = 1.2 MB, `failing_output.txt`): ~19 files → **RETIRE**
- **Static-analysis one-timers** (`bandit_report.txt` 361 KB, `radon_complexity_report.txt` 275 KB, `vulture*.txt`): ~5 files → **RETIRE**
- **Design generators / IP shadow** (`INLAY_PATTERN_GENERATORS.txt`, `Girih-5…txt`, `Animate Toolpath Visualizer Code.txt`, `Bridge Compenstation Calculator.txt`, vectorizer design dumps): ~15 files → **LEGACY / UNKNOWN** (unique IP not in code, or shadow copies of code — not resolved)
- **Migration/session planning** (`Comprehensive_Migration_Plan*.txt`, `MD_INVENTORY.txt`): ~6 files → **UNKNOWN**

### Tracked documentation corpus

| Category | Size | Files | Classification |
|---|---:|---:|---|
| `docs/` total (.md) | ~114 MB | 459 | **ACTIVE corpus** (monitor unbounded growth) |
| `docs/archive/` | 109 MB | 85+ | **LEGACY, policy-governed** (60-day rule + INDEX.md; enforcement mechanism unclear) |
| `docs/handoff*` | 2.1 MB | 140 (52K lines) | **ACTIVE governance memory** |
| `SPRINTS.md` | 130 KB | 1 | **ACTIVE** (CI-RED ledger / source of truth) |
| `archive/` (root experimental) | 1.8 MB | ~20 | **LEGACY** (March-2026 interactive-generator snapshots) |

**Primary bloat sources, ranked:** (1) root `test_*.dxf` 2.5 GB, (2) `Guitar Plans/` 2.8 GB, (3) `artifacts/` + untracked `phase4_output/` ≈ 3 GB. All untracked. The **tracked** "growth to monitor" is the documentation corpus (459 .md, handoffs, archive).

---

## Unfinished Consolidation Attempts

Instances where a canonical/unifying architecture was introduced and migration started but did not complete (evidence cited):

1. **Aperture consolidation** — `ApertureWorkspace.vue` is an explicit "Beta consolidation shell (State 3)" that *mounts* the canonical `SpiralSoundholeDesigner.vue` but has not reached parity (Dev Orders 5–72 incomplete). Canonical still routed standalone. *Policy-compliant per FEATURE_PARITY_MIGRATION_POLICY.*
2. **Inlay / Soundhole-Rosette workspace shells** — `InlayWorkspaceShell.vue`, `SoundholeRosetteShell.vue`: multi-stage shells mounting existing views; additive, incomplete.
3. **CAM workspace** — `CamWorkspaceView.vue` is a "unified CAM workspace" but scoped only to a neck Phase-1 wizard; not a general op consolidation.
4. **CAM aggregator phases** — `cam/routers/aggregator.py` documents phases 3.1–3.10 / 4.x; several (utility, monitoring, simulation, export) are disabled with notes ("duplicate legacy paths / zero frontend usage"). Consolidation partially landed.
5. **api_v1 vs router_registry** — two parallel mounting strategies; the curated `api_v1` "stable surface" was introduced alongside (not folded into) the dynamic registry.
6. **Acoustics Wave-22** — old `routers/acoustics` query/attachments routers disabled in favor of `rmos/runs_v2/acoustics_router`, but `plate`/`radius_dish` were left mounted — supersession is partial.
7. **Instrument-geometry split** — a monolithic `instrument_geometry_router.py` was split into ~13 sub-routers (`instrument_geometry/*`); the split set is present but its mount state vs the monolith is part of the contested unmounted-router cohort.
8. **DesignFirstWorkflowPanel v1 → v2** — both versions co-exist with no deprecation path.

---

## Intellectual Property Preservation Analysis

Unique capabilities worth preserving **regardless of architecture decisions** (flagged so classification work does not endanger them):

- **Geometric / pattern generators (highest-value IP):**
  - `cam/rosette/prototypes/` — 17 traditional rosette generators (Spanish, wave, rope-twist, Celtic parametric knots, herringbone variants). In-production, unique.
  - `art_studio/services/generators/inlay_*` — full inlay/marquetry engine (bezier/rope geometry, BOM, SVG, 6+ pattern families).
  - Root `INLAY_PATTERN_GENERATORS.txt` + `Girih-5…txt` — authentic Islamic-geometric / marquetry generator IP **not yet in code**. Unwired but unique; do not discard without integration check.
- **Domain-knowledge systems:**
  - `app/ai/lutherie_system_prompt.py` — canonical lutherie reference constants (plate modes, Helmholtz, fret math, neck angles).
  - `wood_species.json` + CIRAD/FPL-sourced wood data and per-field attribution policy.
  - Spiral soundhole physics (`soundhole_physics.py`) + root research models (`spiral_acoustic_model.py`, `spiral_q_fh_solver.py`) — Williams-2019-based acoustic IP.
- **Manufacturing validation systems:**
  - RMOS `runs_v2` lifecycle + feasibility engines + CAM governed-export gates (machine-output quarantine).
  - The CI governance apparatus itself (fences, ratchets, routing-truth witness) — encodes hard-won invariants.
- **Geometry recovery / fidelity:**
  - `vectorizer_phase3._raw_extract` (V2) + scale-validation gate — the recovered "March 2026 fidelity" extraction path.
  - `dxf_compat` dual-format gateway — encodes verified CAD-compatibility knowledge (R12/R2000, EXTMIN/EXTMAX correctness).

---

## Critical Constraints (restated)

This document is **classification-only**. It does **not** propose new architecture, migrations, refactors, or rewrites. Every classification above is backed by repository evidence (mount graph, route table, imports, tests, git history, or file-system quantification). Two evidence conflicts that arose during the sweep were **resolved by direct verification** (✅ CAM aggregator confirmed active; ✅ acoustics-ingest confirmed divergent/unwired). Items that remain `UNKNOWN` (e.g. probe/retract mount state, pickguard absence, Guitar Plans/ provenance, the residual unmounted-router split) are flagged honestly rather than forced to a verdict. The purpose is to establish reality before any decision about what action, if any, should follow.
