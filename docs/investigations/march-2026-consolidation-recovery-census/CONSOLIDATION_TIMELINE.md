# Consolidation timeline, 2026-03-15 → 2026-03-21 (with the later events that settled it)

**Labels:**
- **D** = direct evidence: a commit, a hashed file, or a timestamped bundle name.
- **I** = inferred sequence.
- **G** = gap: history not preserved.

All times are local (−05:00). Bundle times come from the claude.ai download file names. "Repo" means a
commit reachable from `main` or from tag `v2.4.0-alpha.1`.

## Before the window

| When | Kind | Event |
|---|---|---|
| 03-14 23:55 / 03-15 00:02 | D | `calculator-unification-remediation.md`: remediation tasks **R-1…R-7** (R-8 appears in later docs). Downloads only |
| 03-15 22:35 | D repo | `680e3258` LP-GAP-03: modular neck CNC pipeline, the **live orchestrator's origin** |

## March 15–16: calculator UI and Phase 7 staging

| When | Kind | Event |
|---|---|---|
| 03-15 00:35 / 01:07 / 06:50 | D bundle | Calculator UI bundles (StringTension, LutherieGeometry, StiffnessIndex panels) |
| 03-15 18:23 → 19:55 | D bundle | **Seven** project-graph / blueprint-save / hub / bridge-lab / materials / string-tension / router-wiring bundles |
| 03-16 13:57 | D repo | `114c5d32` shared G-code verification utility wired into the three `*_full_build.py` scripts |
| 03-16 14:39 | D bundle | Three vectorizer result sets (concept SG, jumbo archtop, Benedetto rembg/potrace). Images, DXF and SVG only |
| 03-16 17:59 | D repo | `ee31d921` "integrate Phase 7 staging bundles": the **seven 03-15 subjects enter Git here**, mostly renamed into the app tree |
| 03-16 23:48 | D repo | `498bc17f` binding design endpoint (BIND-GAP-01…05) |

## March 17: three streams at once

| When | Kind | Event |
|---|---|---|
| 03:53 → 18:22 | D bundle | **ps-vue suite**: headstock generator, then neck + CAM modules (17 bundles). Final headstock views 17:27–18:22 |
| 14:04 | D repo | `0a3d53b9` OM-PURF-03/05/08: binding corner miter, neck purfling, G38.2 depth probe |
| 15:39 | D repo | `3466da7f` **GEN-6** acoustic body generator + `/api/cam/guitar/acoustic/*` |
| 15:39 / 15:59 | D bundle | Neck profile export, CamSpec, NeckTaper; **headstock transition export** (DXF + G-code) |
| 18:30 | D repo | `ebfc8b8a` Smart Guitar shell + nav modules (Cursor) |
| 22:32 | D repo | `fe1e2f51` `cam/machines.py` + sagitta fix + **PostProcessor wired into truss rod** |
| 22:38 → 22:42 | D bundle | ps-vue CAM workspace bundles; 22:42 also carries the **seven 03-15 ZIPs nested inside** |
| 23:10 | D repo | `1d7dbd9e` PostProcessor wired into profile carving and fret slots |
| 23:13 | D repo | `34e22a77` **CAM Workspace wizard Phase 1** (Cursor), 31 min after the bundle |

## March 18: integration, archiving and backlog closure

| When | Kind | Event |
|---|---|---|
| 00:18 | D repo | `95ef35d5` `cam_workspace_router` (incl. `/neck/generate-full`) + NeckOpPanel |
| 01:13 | D bundle | Archtop graduation JSONs |
| 02:14 | D repo | `8c553069` titled "E_C_gpa cross-grain modulus"; **also adds the 4 headstock views and both March bundle folders** (Cursor) |
| 03:19 | D bundle | **CAM-backend bundle**: `BACKLOG.md`, orchestrator, machines, router, evaluator, plate physics |
| 03:41 | D repo | `3855579c` PORT-001 plate physics, from the 03:19 bundle |
| 04:11 | D repo | `52ebb632` `cam_cutting_evaluator`, "from uploaded files" (03:19 bundle) |
| 13:03 | D repo | `a1ff8417` machine selector wired to the backend |
| 13:44 | D repo | `8ef349c9` first committed `docs/BACKLOG.md`: the 03:19 bundle's `BACKLOG.md` minus ARCH-002 |
| 19:37 | D repo | `21fe1b1f` PORT-001, HEADSTOCK-001 and VECTORIZER-001 marked complete, **26 minutes before** `98c0b58d` implements HEADSTOCK-001 / VECTORIZER-001 |
| 19:43 | D repo | `1fdd5d53` session summary writes **"HEADSTOCK-001: dxf_export.py (needs locating)"** into SPRINT_BOARD "Next Up". Still on `main` (`docs/SPRINT_BOARD.md:126`) |
| 20:03 | D repo | `98c0b58d` HEADSTOCK-001 headstock DXF export + VECTORIZER-001 router |
| 20:07 | D repo | `c2c332b8` registers the **headstock transition router (DXF + G-code)** |
| 20:38 | D repo | `4741f084` removes ARCH-001, **NECK-001 ("neck suite integrated 2026-03-18")**, CAM-SURVEY-001, ROOT-CLEANUP-001. The message says GEOMETRY-009 was "not present", but the diff deletes it |
| 20:50 → 22:50 | D repo | CONSTRUCTION-001…010 and GEOMETRY-001…010 calculators, one commit each |

## March 19–21: calculators, path packs, archive sweep

| When | Kind | Event |
|---|---|---|
| 03-19 00:43 → 03-20 02:31 | D bundle | Soundhole, neck block, fret wire, nut and saddle compensation, headstock break angle **path packs**; bracing + radius dish |
| 03-19 12:46 | D repo | `a24cc63d` graduates `cnc_production` → `app/cam_core/` |
| 03-19 18:34 | D repo | `9b235f50` splits `instrument_geometry_router.py` into 9 domain routers |
| 03-21 02:02 | D repo | `3215ef9b` radius dish router (G-code) |
| 03-21 02:14 | D repo | **`73a2703d` "chore: archive photo-vectorizer patch history"**: archives the 03-18 03:19 bundle **nested inside** the 03-18 01:13 bundle's folder, plus 03-19/03-20 bundles. **The orchestrator and `machines.py` are archived here, not integrated** |
| 03-21 02:15 → 23:58 | D repo | Session A calculators, AI assistant D-1…D-4, ACOUSTIC-001…005 |
| 03-21 02:15 / 11:54 / 12:39 | D bundle | photo_vectorizer_v2 + contour stage; two `side_bending_calc.py` iterations |

## After the window: settlement and loss

| When | Kind | Event |
|---|---|---|
| 03-24 23:22 | D repo | `bc196138` flattens `photo_vectorizer_patches` |
| 03-24 | D repo | `8e28ba4b` live orchestrator gains `@safety_critical` |
| 03-30 | D repo | tag `v2.4.0-alpha.1`: **last preserved pre-rewrite state** |
| 03-30 → 04-05 | **G** | Not preserved. The `ImportView` photo-source selector edit and the BCAM → BCAMCNC archive prose edit happened here |
| 04-05 17:31 | D repo | `8d91c4c7` **parentless root** (4,553 files); `SPRINTS.md` first appears |
| 04-23 | D repo | Sprint 3 records 12 DXF-writer migrations as done (`SPRINTS.md:424-434`) |
| 04-25 / 04-26 | D repo | `414d41dc` verification audit: **10 of 12 false**; `8a86ae89` reopens Sprint 3 |
| 05-11 / 05-20 | D repo | `9b7630b9`, `d5033799` fix the 10 via the `create_document` wrapper, **keeping R2010** |
| 09-22 | D repo | `b9b0b929` (#398) LTB-REMEDIATE-P1: neck rapids at depth fixed; route fail-closed |
| 2026-10-13 | D repo | #437 / #438: headstock suite preserved (open) |

## Inferred sequence (I)

On the evening of 03-18, backlog closure ran ahead of implementation:

- items were removed as complete before, or without, the commit that implemented them;
- evidence was cited from files that were deleted the next day (`neck_profile_export`).

The 03-21 archive sweep then preserved, under one unrelated commit subject, everything from 03-18…03-20
not yet integrated. No record shows a per-file decision. This matches "preserve what we did not get to",
not "rejected".

## Unresolved gaps (G)

- **03-30 → 04-05 history.**
- Whether anyone evaluated the archived orchestrator or `machines.py` before archiving.
- The origin of the cited Sprint 1 commits `4c4f1a52`, `04735bd4` and `3db07c62`, which do not resolve
  in the object store (`R12_R15_CHAIN.md`).

No namespace-collision record exists for any item in this window. Losses are labelled
**CONSOLIDATION/MIGRATION ARTIFACT**.
