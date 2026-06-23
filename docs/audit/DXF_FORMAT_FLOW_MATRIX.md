# DXF Format-Flow Matrix

**Audit branch:** `audit/dxf-format-flow` off `origin/main` `c33b700a`
**Date:** 2026-06-23
**Stream:** Phase 1 of 3 — **AUDIT** (read-only). Next: CLEAN → CONSOLIDATE.
**Scope:** Every DXF producer / consumer in `services/api/app`, and the seams between them.
**Constraint:** Read-only. This document + `scripts/audit/dxf_inspect_file.py` are the only
artifacts; no production code was edited.

> This matrix exists to convert "R2000 keeps popping up" from an unknown-sized problem into a
> mapped one, so the CLEAN and CONSOLIDATE streams can be scoped against the whole field instead
> of getting swept up in CAM work the way the last DXF sprint did.

---

## Summary header — "what we're dealing with"

| Metric | Count |
|---|---|
| DXF **producer** functions (emit a DXF artifact) | **≈46** across ≈34 files |
| DXF **consumer** sites (readfile / entity-requirement) | **≈29** across ≈26 files |
| **Seams** classified (producer→consumer edges + dead ends) | **31 rows** below |
| Seam status — **OK** | 13 |
| Seam status — **RISK** | 9 |
| Seam status — **UNKNOWN** | 3 |
| Seam status — **DEAD** | 6 |

### Three emission stacks coexist
1. **`dxf_compat`** (`util/dxf_compat.py`, PROTECTED) — the version-aware layer. `create_document(version)`
   + `add_polyline(...,version)` which emits **LINE-chains for R12, LWPOLYLINE for R13+**.
2. **`cam.dxf_writer.DxfWriter`** (PROTECTED) — wraps `dxf_compat`; default `version="R12"`. The *only*
   path that actually exercises the version-aware entity branching.
3. **Hand-rolled / raw** — `toolpath/dxf_exporter.py` + `dxf_io_legacy.py` (raw group-code strings),
   `util/exporters.py:export_dxf` (ASCII R12), `app/exports/dxf_helpers` (legacy router). These
   **bypass `dxf_compat` entirely** (not even via `ezdxf.new()` — via string writes).

### The decentralization finding (input to CONSOLIDATE)
- **No canonical version-negotiation helper exists.** Version is set ~30 times as a **hardcoded
  literal** or a **caller-supplied request param**. There is **exactly one** tier-aware pick in the
  whole app: `api_v1/fretboard.py:221` — `version = "R2000" if _is_pro(principal) else "R12"`.
  Everywhere else the CLAUDE.md "free=R12 / paid=R2000" rule is **prose, not enforced** — and
  `cam/layer_consolidator.py` actively inverts it (R12→R2000) on an internal tempfile.
- The real lever is **not `create_document`** (almost everything routes through it correctly) — it's
  the **entity-emission bypass**: most producers call `create_document(version=...)` and then write
  **raw `msp.add_lwpolyline(...)`** instead of `dxf_compat.add_polyline(...)`. So the version-aware
  LINE-vs-LWPOLYLINE branch is dead code in every path except `DxfWriter`/`BodyOutlineDxfTranslator`.

### Concentration
RISK is **not in one subsystem** — it's distributed along the **entity-type contract** wherever a
strict consumer meets a producer of the wrong entity class. It clusters at **two boundaries**:
1. **User re-upload → strict LWPOLYLINE consumers** (`extract_loops_from_dxf`, `rmos dxf_to_grbl`,
   `adaptive /plan_from_dxf`): these silently return empty on R12/LINE input, and several of our own
   producers ship R12/LINE.
2. **LINE-only consumers fed LWPOLYLINE** (`geometry import_router`, blueprint `unified_dxf_cleaner`,
   `core/dxf_geometry`): silently drop entities.
The root cause of both is the same decentralized version selection — fix the producer side
(CONSOLIDATE) and the consumer-side RISK collapses.

### The motivating seam is RESOLVED (see T6)
`reconstruct_bracing_dxf` produces **R2000/LWPOLYLINE** and ships **only to an end-user HTTP download**.
Repo-wide grep finds **no internal CAM consumer** of its output. The feared "bracing → CAM consumer
that requires LWPOLYLINE" seam **does not exist** as an internal pipeline — and even if a user
re-uploads it, R2000/LWPOLYLINE is exactly what the strict consumers want. **Status: OK.** The audit's
motivating fear was misplaced; the real risk is the *inverse* (R12 producers → strict consumers).

### Size estimate for the next streams
- **CLEAN:** ≈12–15 backlog items — the 9 RISK seams + 4 contract-label mismatches (Appendix B) +
  the toolpath header/entity inconsistency + the 6 DEAD retirements (Appendix A).
- **CONSOLIDATE:** one central, tier-aware version-negotiation helper to replace the ~30 decentralized
  picks, **plus** converting raw `add_lwpolyline` call-sites onto `dxf_compat.add_polyline` so the
  version actually drives entity class. The DEAD retirements should land first to shrink the surface.

---

## Seam matrix

Legend — **Via:** `compat`=dxf_compat/DxfWriter · `raw`=hand-rolled strings · `bypass`=create_document
then raw `add_lwpolyline`. **Ent:** entities actually emitted. **Ship:** `user`=HTTP download to end
user (tolerant CAD) · `internal`=feeds another step · `disk`=server file.

| # | Producer (file:func) | Ver | Via | Ent | Artifact → Consumer | Consumer requirement | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | `blueprint_cam/contour_reconstruction.py:reconstruct_bracing_dxf` | R2000 | bypass | LWPOLYLINE | tempfile→bytes→**HTTP download** | end-user CAD (tolerant) | **OK** | **Motivating seam — no internal consumer (T6).** R2000/LWPOLYLINE. |
| 2 | `blueprint_cam/contour_reconstruction.py:reconstruct_contours` | R2000 | bypass | LWPOLYLINE | →HTTP download | end-user CAD | **OK** | `create_document("R2000")`==`AC1015` recorded — consistent. |
| 3 | `blueprint_cam/dxf_preprocessor.py:normalize_dxf_format` | R2000 | bypass | LWPOLYLINE+LINE+CIRCLE+ARC | →HTTP download / →densify | end-user / internal | **OK** | Forces R2000; guards the `/preprocess/full` pipeline. |
| 4 | `blueprint_cam/dxf_preprocessor.py:densify_dxf` | inherits | bypass | LWPOLYLINE | →HTTP download | end-user CAD | **RISK** | Standalone `/preprocess/densify` has **no normalize guard**; raw `add_lwpolyline` onto an inherited-version doc — breaks if input is R12. |
| 5 | `services/blueprint_orchestrator.py` CAM_READY_R2000 path | R2000 | external vectorizer | LWPOLYLINE | base64→**HTTP**→(user may re-upload to CAM) | `extract_loops_from_dxf` wants LWPOLYLINE | **OK** | Paid/cam_ready path satisfies strict CAM consumers. |
| 6 | `services/blueprint_orchestrator.py` V2_RAW path | R12 | external vectorizer | LINE | base64→**HTTP**→(user may re-upload to CAM) | `extract_loops_from_dxf` wants LWPOLYLINE | **RISK** | Free/raw path emits R12 LINE; if re-fed to CAM extraction → **silent empty loops**. The genuine in-product version seam. |
| 7 | `instrument_geometry/soundhole/spiral_geometry.py:generate_dxf` | R12 | compat | LINE | →HTTP download | end-user CAD | **OK** | Emission OK; but route/docstring **label says "R2000"** → Appendix B. |
| 8 | `instrument_geometry/neck/fretboard_ecosphere.py:write_ecosphere_dxf` | R12/R2000 | compat | LINE / LWPOLYLINE | →HTTP download | end-user CAD | **OK** | **The one tier-aware producer** (`_is_pro`→R2000 else R12). Reference pattern for CONSOLIDATE. |
| 9 | `instrument_geometry/bridge/archtop_floating_bridge.py:generate_dxf` | R12 | compat | LINE+ARC+CIRCLE | →HTTP download | end-user CAD | **OK** | Route label "R2000" ≠ emitted R12 → Appendix B. |
| 10 | `routers/instruments/guitar/smart_guitar_dxf_router.py` (inline) | R2010 | bypass | LWPOLYLINE+CIRCLE | →HTTP download | end-user CAD | **OK** | Live smart-guitar route. Body-module twin is DEAD (A). |
| 11 | `routers/headstock/dxf_export.py:build_dxf` | R2010 | bypass | LWPOLYLINE+CIRCLE+LINE+ARC+TEXT | →StreamingResponse | end-user CAD | **OK** | R2010-legal LWPOLYLINE; hardcoded bypass. |
| 12 | `routers/neck/export.py:export_neck_dxf` | R12 | bypass | POLYLINE2D+LINE+CIRCLE+TEXT | →HTTP download | end-user CAD | **OK** | POLYLINE2D is R12-legal. |
| 13 | `routers/neck/headstock_transition_export.py:build_transition_dxf` | R2010 | bypass | POLYLINE3D+LINE+TEXT | →StreamingResponse | end-user CAD | **OK** | Mounted at `/api/headstock/transition/dxf`. |
| 14 | `cam/translators/dxf/body_outline_translator.py` (+registry) | R12/R2000 param | compat | LINE / LWPOLYLINE | →`/api/export/translate/dxf` | end-user CAD | **OK** | Canonical governed translator; version = **query param**, principal injected but unused. |
| 15 | `routers/export/curve_export_router.py:export_curve_dxf` | R2010 | compat+raw spline | SPLINE/LWPOLYLINE | →StreamingResponse | end-user CAD | **OK** | |
| 16 | `cam/archtop_bridge_generator.py` / `archtop_saddle_generator.py` | R2010 | compat | LWPOLYLINE+LINE+CIRCLE+TEXT | →disk + JSON metadata | end-user (downloads file) | **OK** | `/archtop/bridge`,`/saddle`. |
| 17 | `cam/archtop/archtop_contour_generator.py:mode_csv/mode_outline` | R2010 | compat | LWPOLYLINE | →disk (subprocess) | end-user / re-read by `read_single_outline` | **OK** | |
| 18 | `routers/archtop_router.py:generate_contours` (DxfWriter default) | R12 | compat | LINE | base64→HTTP | end-user CAD | **OK** | Same domain as #16/#17 but **R12/LINE** — two version regimes in one subsystem. |
| 19 | `calculators/inlay_calc.py:generate_inlay_dxf_string` (+`art_studio/inlay_router`) | param (def R12) | compat | LINE/LWPOLYLINE+CIRCLE | →HTTP download | end-user CAD | **OK** | Version = **request field**, no tier gate. |
| 20 | `art_studio/bracing_router.py:export_bracing_dxf` | param (def R12) | compat | LINE/LWPOLYLINE+CIRCLE+TEXT | →StreamingResponse (`X-DXF-Version`) | end-user CAD | **OK** | Version = request field, R12–R18, no tier gate. |
| 21 | `routers/geometry/{export,import,bundle}_router.py` → `util/exporters.export_dxf` | ASCII R12 | raw | LINE+ARC | →HTTP / ZIP | end-user CAD | **OK** | Hand-rolled ASCII R12, dxf_compat bypassed; single layer `0`. |
| 22 | `routers/legacy_dxf_exports_router.py:export_polyline_dxf/export_biarc_dxf` | R12 | raw/helpers | POLYLINE/ARC/LINE | →HTTP download | end-user CAD | **OK** | ezdxf-or-ASCII-R12 fallback; bypasses dxf_compat. |
| 23 | `toolpath/dxf_exporter.py:export_mlpaths_to_dxf` | param `$ACADVER` | raw | POLYLINE(R12-style) / LWPOLYLINE | →`/api/cam/toolpath/relief/export-dxf` | end-user CAD | **RISK** | **Header advertises R14/R2000/R18 while default path emits R12-style POLYLINE** (own comment admits it) → Appendix B. User-parameterized version+`prefer_lwpolyline`. |
| 24 | `services/layered_dxf_writer.py:write_layered_dxf` | R12 | compat | LINE | disk→`blueprint_orchestrator`/`body_geometry_repair` | `DXFCleaner` chains LINE | **OK** | Internal; R12 LINE matches LINE consumer. |
| 25 | `ibg/instrument_body_generator.py:save_dxf` (`outline_to_dxf`) | R12 | compat | LINE | base64→`body_solver_router` return_dxf | end-user CAD | **OK** | Provenance-gated (`IbgDxfExportBlockedError`→422 unless RATIFIED). |
| 26 | IBG **consume** chain: upload → `_consolidate_if_needed`→`LayerConsolidator`(R2000 LWPOLYLINE tempfile)→`ConstraintExtractor` | R2000 (internal) | bypass | LWPOLYLINE | internal tempfile, `os.unlink`'d | `ConstraintExtractor` generic (LINE/LWPOLYLINE/POLYLINE) | **OK** | Internal R12→R2000 hop is load-bearing; works because the extractor is generic. |
| 27 | (upload) → `blueprint_cam/extraction.py:extract_loops_from_dxf` | n/a (consumer) | — | — | user upload (Phase-2 vectorizer) | **requires closed LWPOLYLINE on `GEOMETRY`** | **RISK** | Filters `dxftype=='LWPOLYLINE'`, skips non-closed → **R12/LINE input = silent empty + warning**. Fed by #5/#6 via user. |
| 28 | (upload) → `rmos/mvp_router.py:dxf_to_grbl` | n/a (consumer) | — | — | user upload | **requires closed LWPOLYLINE/POLYLINE** | **RISK** | LINE-only DXF → `{"ok":false,"No closed polylines found"}`. Several of our producers ship R12/LINE. |
| 29 | (upload) → `routers/adaptive/dxf_router.py:_dxf_to_loops_from_bytes` | n/a (consumer) | — | — | user upload | **closed LWPOLYLINE on layer `GEOMETRY`** | **RISK** | Hardest requirement (type **and** layer **and** closed); R12/LINE → HTTP 400. |
| 30 | (upload) → `routers/geometry/import_router.py:_dxf_to_segments` | n/a (consumer) | — | — | user upload | **LINE+ARC only** | **RISK** | Silently **drops LWPOLYLINE/POLYLINE/CIRCLE** → cannot round-trip the LWPOLYLINE/CIRCLE that #19/#20 emit. Inverse failure mode. |
| 31 | (upload/path) → `core/dxf_geometry.py:load_dxf_geometries` | n/a (consumer) | — | — | `dxf_path` arg | **LINE+CIRCLE only** | **UNKNOWN** | Drops polylines/arcs silently; **feeder not statically traceable** (path arg). Needs runtime trace. |

**Additional UNKNOWN consumers (not separate rows; feeder undetermined):**
- `cam/contour_reconstructor.py:reconstruct_contours_from_dxf` (LINE+SPLINE) — fed by `/reconstruct-contours`
  user upload; **UNKNOWN** whether LWPOLYLINE-only uploads occur (would yield no chains).
- `cam/archtop/archtop_contour_generator.py:read_single_outline` (closed LW/POLYLINE only, drops LINE)
  — fed by user-supplied `req.dxf_path`; **UNKNOWN** input class.

---

## Appendix A — Producers with no live consumer (DEAD / retirement candidates)

Route each to its own disposition in the CLEAN stream; **none has a live runtime consumer.**

| Producer | Evidence | Disposition lead |
|---|---|---|
| `cam/dxf_consolidator.py` | Retired #149; only caller is `test_dxf_consolidator_retirement.py` (a guard asserting it stays dead). | Already sanctioned — confirm removal. |
| `cam/body_region_selector.py:BodyRegionSelector` (LINE consumer) | No live `app/` caller; only `complexity_baseline.json` ref. | Retire or wire. |
| `cam/line_deduplicator.py:deduplicate_parallel_lines` | Only test callers (`test_dxf_lifecycle_*`). | Retire or wire. |
| `instrument_geometry/body/smart_guitar_dxf.py:generate_smart_guitar_dxf` | No router imports it; live route uses router-inline twin (#10). Two parallel generators, different geometry origins. | Retire body module **or** reconcile with #10. |
| `generators/bezier_body.py:BezierBodyGenerator.to_dxf` | No router; docstring refs only. | Library/CLI — mark as such. |
| `routers/neck/neck_profile_export.py` (`build_neck_dxf` + its routes) | **Not in any `router_registry` manifest**; manual `include_router` never wired. | Mount or delete (distinct from live `routers/neck/export.py`). |
| `ibg/arc_reconstructor.py` (`chains_to_dxf`, `ArcReconstructor`, `run_on_dxf`) | CLI/test only; IBG `complete_from_dxf` uses `ConstraintExtractor`, **not** `ArcReconstructor`. | Dev tool — segregate from runtime. |
| `cam/archtop/archtop_surface_tools.py:export_contours` | No HTTP route; CLI `main()` only — **and uses removed `cs.collections` (mpl≥3.8)**, would crash. | Retire (its live twin `archtop_contour_generator` was migrated to `cs.allsegs`). |
| `art_studio/services/generators/inlay_export.py:geometry_to_dxf` | No cluster route; live inlay export uses `generate_inlay_dxf_string` (#19). | Retire or wire. |
| `instrument_geometry/dxf_loader.py:load_dxf_geometry_stub` + `get_body_dxf_asset_for_model` + `dxf_registry` chain | No callers outside docstrings; the one live consumer (`context_adapter`) uses `load_dxf_geometry_by_path`, which **bypasses the registry**. | Registry is advisory-metadata only; reconcile. |
| `calculators/inlay_calc.py:_generate_basic_r12_dxf` | Import-fallback only (fires if `dxf_compat` import fails — practically unreachable). | Dead fallback — remove. |
| `cam/dxf_advanced_validation.py:create_test_*_dxf` | Test fixtures, not a route. | Keep as test util (label). |

---

## Appendix B — Internally inconsistent / contract-mismatched files (D6)

| File | Inconsistency | Class |
|---|---|---|
| `toolpath/dxf_exporter.py` | `_write_header` declares `$ACADVER` R14/R2000/R18 while the **default entity path emits R12-style POLYLINE+VERTEX+SEQEND** (acknowledged in its own docstring L90-92). Declared version **newer** than entity style. (The R12+LWPOLYLINE inverse is correctly *blocked* by the `use_lwpolyline` guard.) | declared-version ≠ emitted-entities |
| `instrument_geometry/body/smart_guitar_dxf.py` | `create_document("R2000")` (L303) but lifecycle guard records `dxf_version="R2010"` (L605) — two version literals disagree in one function. (DEAD — Appendix A.) | declared-version internal disagreement |
| `instrument_geometry/soundhole/spiral_geometry.py` + `soundhole_router.py` + `woodworking_router.py` | Route `summary`/docstring say **"DXF R2000"** but producer emits **R12 LINE** (DxfWriter default; lifecycle `dxf_version="R12"`). | contract-label ≠ emitted-format |
| `instrument_geometry/bridge/archtop_floating_bridge.py` + `woodworking_router.py:post_archtop_dxf` | Route `summary` "DXF R2000" but producer is documented **"R12 LINE-only"** and emits R12. | contract-label ≠ emitted-format |
| `routers/geometry/import_router.py:_dxf_to_segments` | Reads **LINE+ARC only**; silently drops LWPOLYLINE/POLYLINE/CIRCLE — so it **cannot round-trip** the LWPOLYLINE/CIRCLE that the inlay/bracing exporters (#19/#20) produce. | consumer requirement narrower than sibling producers emit |

**Static D6 method note:** the producer-side declared-vs-emitted checks above were determined from
code (version literal + which `add_*` calls). For *file* artifacts, `scripts/audit/dxf_inspect_file.py`
performs the same check on a real DXF (`$ACADVER` vs entity histogram); validated on archive samples,
including the malformed `smart_guitar_front_v3.dxf` (group-code fallback: R2000 + 12 LWPOLYLINE) and
the Explorer R12 file (caught its `1e+20` sentinel extents — the documented zoom-to-fit bug, in an
archive sample, not a live producer).

---

## Appendix C — Out-of-scope noticed (recorded-and-passed, NOT followed)

One-line leads for the CLEAN stream and others; the audit did **not** act on these.

- **The motivating emitter is mid-clean.** At audit time the *local working tree* (not `origin/main`)
  has **uncommitted edits to `routers/blueprint_cam/contour_reconstruction.py` + its router + test**.
  This matrix audits the **baseline-main** state (`c33b700a`); the in-progress edits are a separate
  cleaning-stream work item, **not reflected here**. Cleaning stream: coordinate — that emitter is
  already being worked.
- **Name collisions** that will bite refactors: two distinct `reconstruct_contours`
  (`cam/contour_reconstructor.py` LINE+SPLINE→Loops vs `blueprint_cam/contour_reconstruction.py`
  LINE+ARC→DXF); two distinct `TopologyValidator` classes (`cam/dxf_advanced_validation.py` vs
  `cam/topology_validation/validators.py`); two `generate_smart_guitar_dxf` (dead body module vs live
  router inline).
- **No tier enforcement of the free=R12/paid=R2000 rule** anywhere except `api_v1/fretboard.py`
  (`_is_pro`). `dxf_translate_router` injects `principal` but never reads it for version. (CONSOLIDATE
  input, but worth a product decision: is the rule real, or aspirational prose?)
- **`spiral_geometry.generate_dxf` spec-type divergence:** typed for `DualSpiralSpec` (reads
  `.upper`/`.lower`) but `woodworking_router` calls it with a single `SpiralSoundholeSpec`. Possible
  latent bug — not a version issue.
- **`relief_export_router` constructs `RunArtifact()` directly** (already in `fence_baseline.json` as a
  known `artifact_authority` exception) — noted, not a DXF concern.
- **Archive DXF carries `1e+20` sentinel extents** (`gibson_explorer_..._body_cavities.dxf`) — the exact
  zoom-to-fit bug CLAUDE.md documents. It's an archived reference sample, not a producer output; no action.

---

## Verification — T1–T7 (the audit's own "tests")

| Test | Result |
|---|---|
| **T1 — Producer completeness.** Every `create_document(` and `ezdxf.new(` from Pass A is represented. | **PASS.** All `create_document` sites (≈30) are in the matrix or Appendix A; the only `ezdxf.new(` calls are inside `dxf_compat.create_document` itself (PROTECTED, the one sanctioned creation point). No raw `ezdxf.new()` bypass exists in `app/`. |
| **T2 — Consumer completeness.** Every `readfile(` and `query("…POLYLINE")` from Pass B is represented. | **PASS.** The single `query('LWPOLYLINE')` (`extraction.py:67`) is seam #27. All `ezdxf.readfile` sites are in the seam matrix, the UNKNOWN list, or Appendix A (dead readers). |
| **T3 — No orphan producers unexplained.** | **PASS.** Every producer has a seam row or an Appendix-A DEAD entry. |
| **T4 — Every seam has a status.** | **PASS.** 31 rows, each OK/RISK/UNKNOWN/DEAD; 3 additional UNKNOWN consumers noted with reason. |
| **T5 — Declared-vs-emitted check run.** | **PASS.** Producer rows carry version + entity class; mismatches in Appendix B. `dxf_inspect_file.py` performs the file-level check and was validated on real artifacts. |
| **T6 — Motivating seam resolved.** | **PASS.** `reconstruct_bracing_dxf` → **no internal consumer**; ships to end-user CAD (tolerant). Status **OK**. The feared internal LWPOLYLINE-CAM seam does not exist; the real risk is the inverse (R12 producers → strict consumers, seams #6/#27/#28/#29). |
| **T7 — Summary header populated.** | **PASS.** Counts, three-stack finding, decentralization finding, concentration analysis, and CLEAN/CONSOLIDATE size estimate are above. |

---

## §3 carried-facts re-verification (against `c33b700a`)

| Carried fact | Verdict on fresh main |
|---|---|
| No canonical version-negotiation helper; tier policy is docstring prose | **CONFIRMED** (+ refined: one real exception, `fretboard.py` `_is_pro`). |
| ~25+ direct version picks | **CONFIRMED** — ≈30 literal/param picks. |
| `dxf_compat` is PROTECTED, version-aware entity layer | **CONFIRMED** (header present; read-only here). |
| `dxf_consolidator` retired/dead (#149); `layer_consolidator` internal, feeds body solver via tempfile | **CONFIRMED** — consolidator test-guard-only; layer_consolidator's sole live caller is IBG `instrument_body_generator`, output `os.unlink`'d. |
| `contour_reconstruction` = direct `create_document("R2000")`, ships `application/dxf`, no tier gate; bracing may feed a CAM LWPOLYLINE consumer | **PARTLY CORRECTED** — R2000/no-gate/ships-`application/dxf` all confirmed; **but the bracing output has NO internal CAM consumer** (T6). The "open seam that motivated this audit" is, on the evidence, **not an open internal seam**. |

---

*End of matrix. Phase 1 (AUDIT) complete. Inputs handed to CLEAN: the 9 RISK seams + Appendix B
mismatches + the toolpath header inconsistency; to CONSOLIDATE: the decentralized version-selection
landscape + the raw-`add_lwpolyline` bypass. DEAD retirements (Appendix A) should land first to shrink
the field.*
