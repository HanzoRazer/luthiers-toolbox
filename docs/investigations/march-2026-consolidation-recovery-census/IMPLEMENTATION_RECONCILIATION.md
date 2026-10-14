# Implementation reconciliation by subsystem

Each subsystem answers nine questions:

1. generated
2. copied in
3. became live
4. archived
5. external only
6. later superseded by
7. capability missing from `main`
8. safety correction or invariant
9. needed next

Row-level evidence is in `RECOVERY_LEDGER.csv`, `MARCH_CLAIM_REACHABILITY.csv` and
`CLAIM_VERIFICATION.csv`.

## Adjudications of the mechanical reachability labels

| Claim | Mechanical | Adjudicated | Why |
|---|---|---|---|
| CAM-SURVEY-001 | FALSE_MIGRATION_CLAIM | **PARTIAL_MIGRATION** | The claim was "documented in ARCHITECTURE.md". `docs/ARCHITECTURE.md:7` has one table row; the 352-line survey exists only in two archive copies |
| R-2 BridgeBreakAnglePanel | FALSE_MIGRATION_CLAIM | **NOT_IMPLEMENTED; built externally** | A plan, never claimed done. Built in nested bundle 03-15T193643 and never entered Git → `RECOVERED_FEATURE_CANDIDATE` |
| R-3 NutBreakAnglePanel | FALSE_MIGRATION_CLAIM | **NOT_IMPLEMENTED** | A plan; no artefact exists anywhere searched |
| HEADSTOCK-001 | PARTIAL_MIGRATION | PARTIAL_MIGRATION (confirmed) | `/api/export/headstock-dxf*` is live and tested; the only client caller (`useExportDxf.ts`) is reachable only from the stranded headstock `WorkspaceView` |

## Headstock Suite

1. **Generated:** the claude.ai `ps-vue` session on 03-17 (03:53–18:22): headstock designer, configurator,
   parametric, import and workspace views, plus a store, types, composables and data.
2. **Copied in:** the four views (`8c553069`, 03-18, under an unrelated commit title); HEADSTOCK-001 DXF
   export (`98c0b58d`); transition export (`c2c332b8`).
3. **Live:**
   - `/api/export/headstock-dxf` (+ cost, preview), with tests;
   - `/api/headstock/transition/{dxf,gcode,analysis}`, without tests;
   - views: **none routed**.
4. **Archived:** both bundle folders under `archive/experimental/2026-03/`; #438 (open) moves the views to
   `headstock-suite-refined/`.
5. **External only:** two scaffold files (`index.html`, `dxf-requirements.txt`). The **five supporting
   modules** exist only in the claude.ai conversation (`LOST_REFERENCE_ONLY`).
6. **Superseded by:** nothing. The routed `/art-studio/headstock` is a different lineage.
7. **Missing capability:** yes. These views are the only UI for veneer, binding and cost DXF.
8. **Safety:** **yes, active.** The transition `/gcode` route; see `RECOVERY_RECOMMENDATIONS.md`.
9. **Needed:** preservation (owner-side module recovery), then feature adjudication, plus a **separate
   safety validation**.

## Neck tooling

1. **Generated:** ps-vue neck modules (NeckTaper, CamSpec, CamSpecPanel, neck profile export,
   VariantLibrary, WoodGrain).
2. **Copied in:** `36e8e8df` (03-19) and `8c553069`.
3. **Live:**
   - `useNeckTaper.ts` is reachable from the client router;
   - `useCamSpec.ts` is imported, but **not router-reachable**;
   - `CamSpecPanel.vue` exists in **two byte-identical copies, neither imported**;
   - `neck_profile_export.py` is present, **not registered**.
4. **Archived:** 11 bundle files.
5. **External only:** none.
6. **Superseded by:** the CAM workspace NeckOpPanel for operation parameters.
7. **Missing capability:** CamSpec overlay UI (stranded); neck profile DXF export (unregistered).
8. **Safety:** none found.
9. **Needed:** feature adjudication. NECK-001 "integrated 2026-03-18" is **partially false**.

## CAM Workspace / backend

1. **Generated:** the ps-vue CAM workspace (22:38–22:42) and the CAM-backend bundle (03-18 03:19).
2. **Copied in:** `34e22a77`, `95ef35d5`, `a1ff8417`, `52ebb632`.
3. **Live:** `CamWorkspaceView`, `NeckOpPanel` and `cam_workspace_router` are all reachable and tested.
   `/neck/generate-full` is fail-closed since #398.
4. **Archived:** the 03:19 bundle (`73a2703d`).
5. **External only:** none.
6. **Superseded by:** live `machines.py` (`fe1e2f51` lineage).
7. **Missing capability:** no.
8. **Safety:** the archived orchestrator and machine contract were **closed**; see the companion
   investigation.
9. **Needed:** none from this census. The clearance-authority decision is a separate order.

## Neck orchestrator

Fully covered in [`../cam-orchestrator-recovery_2026-10-14/`](../cam-orchestrator-recovery_2026-10-14/).
`SUPERSEDED` / `INCOMPATIBLE_WITH_CURRENT_RUNTIME` / `DO_NOT_FORWARD_PORT`.

## Binding / purfling

1. **Generated / copied in:** in-repo commits `0a3d53b9` and `498bc17f`; no bundle.
2. **Live:** `/api/binding/*`; corner miter and the G38.2 probe are reachable, with a UI
   (`BindingDesignerView.vue`) and tests.
3. **Missing capability:** none found.
4. **Safety:** the G38.2 probe macro uses `#3000` alarms. Controller-dialect validity is unassessed
   (belongs with `GCODE-COMMENT-DIALECT-COMPATIBILITY-001`).
5. **Needed:** none from this census.

## Acoustic-body generator (GEN-6)

- **Copied in:** `3466da7f` (in-repo).
- **Live:** reachable, with UI and tests (`VERIFIED_STRUCTURAL`).
- **Missing capability:** none.
- **Safety:** none assessed here. It emits G-code; no motion replay was done in this census.
- **Needed:** none, unless the owner wants it in the next motion-audit sweep.

## PostProcessor work

- **Copied in:** `fe1e2f51` and `1d7dbd9e`, which wired the PostProcessor into the three neck generators.
- **Live:** **proven by replay.** Every live tool change is `M5 / T M6 / G43 / S M3 / G4 / G0 Z`.
- **Safety:** spindle-off and G43 before motion are proven. No operator pause is emitted.
- **Needed:** `NECK-TOOLCHANGE-PAUSE-001`, after the owner rules.

## G-code verification work

- **Copied in:** `114c5d32` (03-16): `scripts/utils/gcode_verify.py`, wired into the three
  `*_full_build.py` scripts.
- **Live:** present on `main` in a **standalone script lane** that shares no code with the API
  generators.
- **Missing capability:** the API lane has no equivalent shared verifier. Its preflight gate is separate.
- **Needed:** reference only. Any reuse belongs to a CAM verification order.

## Radius dish

1. **Generated:** bundle 03-20T023112: `radius_dish_router.py`, four Vue components, `radius-dish.ts`.
2. **Copied in:** the router (`3215ef9b`, 03-21).
3. **Live:** the router at `/api/acoustics/radius-dish/*` is registered and tested, but **no client file
   calls it**. Live client radius-dish components exist with different content.
4. **Archived:** the bundle's UI files.
5. **External only:** none.
6. **Superseded by:** the live client components (by role; contents differ).
7. **Missing capability:** possibly. The backend G-code path has no UI.
8. **Safety:** it emits G-code; not replayed here.
9. **Needed:** feature adjudication (`PARTIAL_MIGRATION`).

## Plate physics (PORT-001)

- **Copied in:** `3855579c`.
- **Live:** the `plate_design` package and `plate_router` are reachable with UI. `plate_router` itself
  has no test hit (`test_exercises=FAIL`).
- **Archived:** five bundle copies.
- **External only:** none.
- **Needed:** none, beyond an optional router test.

## Vectorizer

- **Generated:** the 03-16 result sets (images, DXF, SVG; external only) and the 03-21 photo_vectorizer_v2
  + contour stage.
- **Copied in:**
  - VECTORIZER-001 router (`98c0b58d`): reachable, UI and tests;
  - 03-21: six files live byte-identical, three archived.
- **External only:** the nine 03-16 result-set files.
- **Missing capability:** no.
- **Safety:** none.
- **Needed:** `REFERENCE_ONLY` preservation decision for the result sets.

## The seven nested 03-15 ZIP subjects

The repository's archived copy of the 22:42 bundle omits these seven ZIPs. **Their content entered Git
anyway** through `ee31d921` (03-16 17:59, "integrate Phase 7 staging bundles").

| Nested ZIP | Subject | Live identical | Live modified | Superseded | External only | Missing on main? |
|---|---|---|---|---|---|---|
| 03-15T182348 | **Project graph** (ADR-002, instrument project schema, service, router) | PLATFORM_ARCHITECTURE.md | schema, service, ADR | unwired `project_router.py` | — | no |
| 03-15T183010 | **Blueprint save** | composable, panel | project writer | unwired `blueprint_save_router.py` | — | no |
| 03-15T184511 | **Instrument hub** | `project-types.ts`, `projects.ts` | `InstrumentHubShell.vue`, `useInstrumentProject.ts` (now with specs) | — | — | no |
| 03-15T185317 | **Bridge lab** | `useBridgeWorkspace.ts`, `BridgeLabPanel.vue` | — | — | — | no |
| 03-15T190701 | **Materials** | scorer, `useTonewoods.ts` | schemas, tonewoods, selector | draft `materials_router.py` (live `app/materials/router.py` by role) | — | no |
| 03-15T193643 | **String tension / break-angle panels** | — | — | — | `StringTensionPanel`, `StiffnessIndexPanel`, `useTension_fixed` drafts; **`BridgeBreakAnglePanel.vue`** | **yes: BridgeBreakAnglePanel (R-2)** |
| 03-15T195528 | **Router wiring** (7th subject: `_wired` routers) | `blueprint_save_router_wired.py` | `project_router_wired.py` → `app/projects/router.py` | — | — | no |

## Summary

| Subsystem | Missing capability on main | Safety | Next |
|---|---|---|---|
| Headstock Suite | yes (views + 5 lost modules) | **active candidate** | preserve → adjudicate; separate safety order |
| Neck tooling | CamSpec UI, profile export | — | adjudicate |
| CAM Workspace/backend | — | closed | — |
| Neck orchestrator | — | closed | — |
| Binding/purfling | — | dialect unassessed | dialect order |
| GEN-6 | — | not replayed | optional motion audit |
| PostProcessor | operator pause | proven partial | pause ruling |
| G-code verification | API lane lacks a shared verifier | — | reference |
| Radius dish | backend has no UI | not replayed | adjudicate |
| Plate physics | — | — | — |
| Vectorizer | — | — | reference-only preservation |
| Nested 03-15 subjects | BridgeBreakAnglePanel | — | R-2 parity check |
