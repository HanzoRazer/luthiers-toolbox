# Performance Audit — luthiers-toolbox

**Date:** 2026-07-04
**Audited commit:** `e6857009063eee9c373751a09c2a8110a736a1c3` (branch `c2-process-exclusive-canonical-authority-pr1`)
**Method:** Read-only. Every claim re-grounded against current `HEAD` code (not the prior assessment's stale-commit quotes). Leads classified **verified / refuted / unmeasured**; hot-path claims gated on **reachability proof**; measured where cheap (`cProfile`/`timeit`, `EXPLAIN QUERY PLAN`, `-X importtime`, wall-clock). Synthetic data is labelled as such.
**Scope covered:** the nine prior leads (Part A), a wider sweep the capped search missed (Part B), and structural/algorithmic issues a lead-list can't see (Part C).

> **Discipline note.** A lead is a hypothesis until measured. Where a number is synthetic, it says so. Where I could not measure, the lead stays **unmeasured** — it is *not* upgraded to "confirmed" on plausibility. Reachability was proven before severity: two of the loudest prior leads (`adaptive_core.py`, the DXF contour reconstructor) collapse on contact with the call graph and the current code respectively.

---

## 0. Executive summary — ranked confirmed bottlenecks

Ranked by **likelihood × impact × how-cheap-to-fix**. "Domain" = runtime (affects end users), dev/CI (affects build time), or frontend (perceived latency).

| # | Bottleneck | Domain | Evidence | Fix cost |
|---|---|---|---|---|
| 1 | **CI governance scan: 2 scripts `rglob` the whole tree incl. `.venv`** — 4m39s CI tier, two 120s timeouts | dev/CI | **Measured** 279s; 7,423 of 9,624 `.py` scanned are venv | **Trivial** (~10 lines; fix pattern already in repo) |
| 2 | **`POST /api/cam/opt/what_if` grid search** — uncapped, synchronous | runtime | **Measured** 0.5s (default) → 10.6s (large grid) | **Cheap** (server-side grid/workload clamp) |
| 3 | **`POST /api/cam/.../simulate/upload` echoes unbounded `moves[]`** | runtime | **Verified** unbounded; ~7–70 MB JSON on real programs | **Cheap** (`move_count` already returned; decimate/opt-in) |
| 4 | **Frontend 3D playback rebuilds whole scene per tick (F-X1)** | frontend | Doc-audit "single largest frontend defect"; code confirmed | Medium (incremental update) |
| 5 | **API startup ~18s warm / ~105s cold import** | runtime/boot | **Measured** 17.7–18.9s warm; explains CI-RED-020 flapping | Medium (lazy heavy imports recover ~3–4s) |
| 6 | **Toolpath Pinia store holds 2× up-to-100k deep-reactive arrays** | frontend | **Verified** ~20 MB × 2, plain `ref` not `shallowRef` | Cheap–medium (`shallowRef` + input cap) |
| 7 | **Sync CPU compute in 3 `async def` handlers blocks the event loop** | runtime | **Verified** (vectorizer/vision); correct offload pattern exists in repo | Medium (`run_in_executor`) |
| 8 | **LiveMonitor event lists grow unbounded** (no retained-event cap) | frontend | **Verified** `push` per WS event, only manual clear | Trivial (cap arrays) |
| 9 | **JSON art-jobs store: full 730 KB parse + full rewrite per op** | runtime | **Measured** 22 ms/parse; live; append-only unbounded | Cheap (finish the already-built SQLite migration) |

**One-hour fix list** (confirmed *and* cheap) is in §5. Items 1, 3, 8, 9 and the two preventive index additions are all ≲1 hour each; item 2 is a small clamp.

---

## 1. Part A — adjudication of the nine prior leads

### Lead #1 — SQLite list queries → **REFUTED (as a current bottleneck)**
Every RMOS/art store list query was traced and its plan checked with `EXPLAIN QUERY PLAN` against `services/api/data/rmos.db`.

- Schema at `services/api/app/core/rmos_db.py:95-145` creates single-column indexes on the columns that matter: `patterns(name, strip_family_id, pattern_type)`, `joblogs(pattern_id, status, created_at)`, `art_jobs(job_type, created_at)`, `art_presets(lane, name)`.
- Plans confirm the WHERE filters use those indexes (e.g. `SEARCH patterns USING INDEX idx_patterns_pattern_type`, `SEARCH art_jobs USING INDEX idx_art_jobs_type`).
- **The decisive fact is `n`:** `rmos.db` is 98 KB with `patterns=0`, `joblogs=2`, everything else empty. This is a single-operator shop. Even an unindexed full scan of a few hundred rows is sub-millisecond. There is no volume here for a list query to be slow on.

**Residual (only bites at large `n`, preventive — see §5):** `strip_families` has **zero** secondary indexes → `WHERE material_type`, `WHERE strip_width_mm BETWEEN`, and `get_all` all `SCAN strip_families` + `USE TEMP B-TREE FOR ORDER BY`. And no store has a composite `(filter_col, created_at DESC)` index, so *every* list query does a `TEMP B-TREE` sort. Harmless at today's row counts; a cheap hedge if data ever grows.

### Lead #2 — filtered history scans → **REFUTED (same reasoning)**
`joblogs`, `art_jobs`, `cam_logs` history filters are index-covered (`idx_joblogs_pattern`, `idx_art_jobs_type`; `cam_logs.segments` is covered by its `UNIQUE(run_id, idx)` implicit index at `telemetry/cam_logs.py:276`). Same `n` argument. `runs.machine_id` (`cam_logs.py`) is unindexed but the runs table is one row per CAM operation — tiny.

### Lead #3 — exhaustive CAM optimization → **VERIFIED BOTTLENECK (measured)**  → ranked **#2**
`optimize_feed_stepover()` at `services/api/app/cam/whatif_opt.py:338`. It is **not** the O(n²) the prior list implied — it is **O(grid_cells × moves)**: a 2-level grid over feed × stepover (`:386`, `:389`, default `(6,6)`=36 cells at `:347`), and *inside each cell* it deep-copies the entire `moves` list (`:397-402`) and re-runs `estimate_cycle_time_v2` (`:405`).

**Reachability — LIVE:** `router_registry/manifests/cam_manifest.py` mounts `app.cam.routers.utility` at `/api/cam` → `utility_consolidated_router.py:50` includes `optimization_router` (`/opt`) → `optimization_router.py:41` `@router.post("/what_if")` calls it. **Endpoint: `POST /api/cam/opt/what_if`.** No server-side clamp on `body.grid`.

**Measured** (venv py3.11, synthetic pocket toolpaths):

| moves | grid | cells | time |
|------|------|------|------|
| 200 | (6,6) | 36 | 64 ms |
| 2000 | (6,6) | 36 | **468 ms** |
| 2000 | (10,10) | 100 | 1.16 s |
| 5000 | (20,20) | 400 | **10.6 s** |

The module's own docstring claims (`whatif_opt.py:234-236`, "~0.2 ms/combination, <100 ms for 400 combinations") are optimistic by ~50–100× because they ignore the per-cell clone + full re-estimate. Runs synchronously on the request path (see Lead-Part-B sync compute). **Bites when `cells × moves` ≳ 40k.**

### Lead #4 — legacy adaptive geometry → **REFUTED / DEAD CODE**
`services/api/app/cam/adaptive_core.py`. The O(n²) offsetting (`spiralize` nearest-neighbour `:325`, `build_offset_stacks` `:282`) is real, **but reaches nothing**:
- `grep -w adaptive_core` across `services/api` → only self-references (a docstring example at `:118`). Zero live importers.
- Every live import of the public names resolves to a *different* module: `plan_router.py:30-33`, `blueprint_cam_core_router.py:31`, `pocketing/intent_router.py:43` all import `to_toolpath`/etc. from **`adaptive_core_l1`**, not L.0. `plan_adaptive` used live is `app.services.adaptive_kernel.plan_adaptive`.
- Not in any router manifest; not referenced by any test.

The file's own header self-classifies it "LEGACY L.0 … SUPERSEDED by L.1/L.2/L.3, kept for historical reference." **A documentation note, not a bottleneck.** Deliberately not measured — measuring dead code would be inflation.

### Lead #5 — high-complexity DXF/tessellation functions → **REFUTED (already hardened)**
`radon_complexity_report.txt` has **no E/F grades — max is D**, and D is branch-count, not algorithmic cost.

- **`reconstruct_contours_from_dxf` (`cam/contour_reconstructor.py:305`, D/24) — LIVE** (`POST /reconstruct-contours` → `blueprint_cam/blueprint_cam_core_router.py:48`), but delegates to `graph_algorithms.py`: O(n) spatial-hash adjacency (`:43`) + O(V+E) iterative DFS (`:100`), guarded by `MAX_DXF_EDGES=100_000`, `MAX_CYCLE_SEARCH_ITERATIONS=1_000_000`, and a **30 s thread-pool timeout**. **Measured linear:** full pipeline 1k→204 ms, 5k→553 ms, 10k→1126 ms (dominated by `ezdxf.readfile`); internals sub-15 ms. No blowup before the limits fire (~100k edges).
- The **O(n²) twins** `build_adjacency_map` (`:137`) + `find_cycles_dfs` (`:192`) are **dead** — referenced only by their own defs and docstrings; superseded by the safe versions.
- `dxf_compat.add_polyline` (`util/dxf_compat.py:92`) is trivially O(n). `helical_gcode` (`helical_router.py:158`, D/21) is O(moves) linear with decimated preview.
- `vectorizer_phase3.py` reconstruction is OpenCV-native (`findContours`, `morphologyEx`, `approxPolyDP`) — no Python-level O(n²).

**Side-finding (correctness, not perf):** `MAX_RECURSION_DEPTH=500` in `find_cycles_iterative` (`graph_algorithms.py:173`) **silently abandons any single closed loop with >500 vertices** — a spline-heavy body outline flattened to >500 segments returns `loops=0` / HTTP 422. Flag for a separate correctness fix.

### Lead #6 — CI file scanning → **VERIFIED + MEASURED**  → ranked **#1**
`scripts/governance/check_all.py` runs each check as a subprocess (120 s timeout each, `:286`). **Measured CI tier: 4m39s** (`check_all.py --tier ci`). **Two scripts each hit the 120 s timeout** (240 s of the 279 s total), both doing an **unpruned** `rglob("*.py")` over `services/`:
- `scripts/governance/check_semantic_sandbox_imports.py:72`
- `scripts/governance/check_feedback_correction_calls.py:18`

They see **9,624 `.py` files, of which 7,423 (77%) live in `services/api/.venv/site-packages`** — third-party source that is read + regex-scanned line by line for nothing. Neither prunes `.venv`/`node_modules`/`__pycache__`. Only ~2,201 files are real repo source. **This is dev/CI-time cost, not request runtime** — but it is paid on every CI run (GitHub CI builds the venv at the same path). The **correct pattern already exists in-repo**: `scripts/check_dxf_compat.py:55` defines `PRUNE_DIRS` and prunes in-place during `os.walk`. Fix = copy that. Expected: 120 s timeout → ~2 s each.

### Lead #7 — large geometry payloads → **VERIFIED (one unbounded endpoint)**  → ranked **#3**
`simulate_gcode_upload` at `services/api/app/cam/routers/simulation/simulation_consolidated_router.py:137` (`POST .../simulate/upload`, mounted via `cam_manifest.py`) returns `"moves": moves` — one `{code,x,y,z,f}` dict **per motion line** of the uploaded G-code, **no pagination/decimation**, while `move_count` is *already* computed alongside. A body program is thousands of lines (CLAUDE.md cites 2,260); a 3D relief/pocket program is 10⁵–10⁶ lines → **~7 MB to 70+ MB** JSON. Trivially fixable.
Secondary full-but-bounded returns (worth a glance, not urgent): `adaptive/plan_router.py:391,417` (note `:460` correctly decimates), `utility/compare_router.py:48,55` (returns *two* full toolpaths), `rmos/rosette_cam_router.py:76,188`.

### Lead #8 — second-pass materialization loops → **REFUTED**
All 19 candidate sites are benign single extra O(n) passes: tonewood filters (`materials/router.py:101-110`), materialize-then-validate in DXF validators (`cam/dxf_advanced_validation.py:361,530`, `cam/dxf_preflight.py:241,360`), min/max after `all_points` (`cam/unified_dxf_cleaner.py:539`). No large-n double-materialization.

### Lead #9 — doc-reported user-visible slowness → **VERIFIED (one open, one historical)**
- **OPEN, high value — F-X1 3D playback stutter/freeze.** `docs/audit/TOOLPATH_ANIMATION_AUDIT_2026-05-30.md:76-77` calls it *"the single largest frontend defect"*: the Three.js renderer rebuilds the **entire** scene every playback tick (O(N) teardown+rebuild, N up to 100k). Code at `packages/client/src/components/cam/ToolpathCanvas3D.vue:752-757` (watch) → `buildToolpath()` `:248-287`. Tracked as `SPRINTS.md → CAM-TPA-001`. Structurally clear; **not verified live** (dev server not run) — see §4.
- **HISTORICAL / fixed — Fusion 360 freeze** on `smart_guitar_front_v3.dxf`: pre-`dxf_compat` malformed-LWPOLYLINE incident, resolved by the R12 gate (`CLAUDE.md:218`). Not an open bottleneck.
- The `TRANSLATOR_SECURITY_MODEL.md:105` 60 s translator timeout is a *guard*, implying complex geometry can approach it — corroborates Lead #3/#5 rather than a separate finding.

---

## 2. Refuted leads (what measurement/reachability killed — stops wasted optimization)

| Lead | Why refuted |
|---|---|
| #1 SQLite list queries | Index-covered; `n≈0` (rmos.db near-empty, single-operator). Query plans confirm index use. |
| #2 filtered history scans | Same; history filters indexed, `cam_logs.segments` covered by `UNIQUE(run_id,idx)`. |
| #4 `adaptive_core.py` O(n²) | **Dead code** — zero live/test importers; live paths use `adaptive_core_l1`. |
| #5 DXF contour reconstructor | Current code is O(n) + 30s timeout + hard limits; **measured linear** to 10k edges. O(n²) twins are dead. |
| #8 second-pass materialization | All sites are benign single O(n) passes. |
| N+1 queries (Part B) | **None on any live request path** — the only store-call-in-loop sites are offline migration/audit tools (`tools/rmos_migration_audit.py:290+`, `tools/rmos_migrate_json_to_sqlite.py:99+`). Bulk import (`utility/settings_router.py:190`) fetches ids once, uses O(1) in-memory dict stores. |

---

## 3. Part B / C — new findings the capped search missed

### N1. JSON art-jobs store: full-file parse + full rewrite per operation → **VERIFIED (measured), ranked #9**
`services/api/app/services/art_jobs_store.py` (and near-twin `art_job_store.py`) back rosette CAM jobs with `data/art_jobs.json` (**730 KB, 43 records**):
- `get_art_job()` calls `_load_jobs()` (full parse) then linear-scans (`:82-88`).
- `create_art_job()` does `_load_jobs()` → append → `_save_jobs()` **rewrites the entire file** (`json.dump(indent=2)`, `:45-49,75-77`).
- **Measured:** `json.load` = **22 ms per call** (20-run avg, 730 KB).
- **Reachability — LIVE:** `cam/routers/rosette/rosette_jobs_router.py:79` (create), `:112` (get); `rmos/rosette_cam_router.py:415`; `pipeline_ops_rosette.py:77`; `art_studio/api/rosette_jobs_routes.py:239`.
- **Migration is half-done:** `core/store_registry.py:152-154` canonically wires `ART_JOBS → SQLiteArtJobsStore` ("migrated from JSON file stores"), and the SQLite `art_jobs` table + indexes exist — but the live rosette routers still call the JSON functions directly, bypassing the registry. Append-only, **never pruned → grows unbounded**; the 22 ms parse and the full rewrite both scale with file size. Fix = point those routers at the existing SQLite store.

### N2. Synchronous CPU compute inside request handlers → **VERIFIED, ranked #7**
Offload primitives (`run_in_executor`/`BackgroundTasks`/`to_thread`) exist in only 10 files, and **none of the heavy vision/geometry routers use them** (the correct-pattern contrast: `body_solver_router.py`, `blueprint_async_router.py` *do* offload).

**Worst — `async def` doing CPU work blocks the whole event loop** (every concurrent request stalls):
- `routers/photo_vectorizer_router.py:308` `async def extract_from_photo` → `:360` full cv2/rembg/potrace vectorization inline.
- `routers/blueprint/phase3_router.py:103` `async def vectorize_blueprint` → `:156` dual-pass ML + rasterize-to-1200-DPI inline; also `:225 quick_vectorize`.
- `vision/segmentation_router.py:37` `async def segment_guitar` → `:76` AI vision + inline DXF/SVG export; `:142 photo_to_gcode` chains segmentation→DXF→G-code inline.

**Less bad — `def` handlers block one threadpool worker:** `gcode_consolidated_router.py:194 simulate_gcode` (up to 100k segments inline); `simulation_consolidated_router.py:143 simulate_gcode_json`, `:219 calculate_metrics`.

### N3. API startup ~18s warm / ~105s cold import → **VERIFIED (measured), ranked #5**
143 routers mount via a **static manifest registry** (not a filesystem walk): `main.py:229-233` loops `load_all_routers()` (`router_registry/loader.py:54`, `importlib.import_module` per spec) over 144 specs from 6 domain manifests. Loader log: `143 loaded, 0 skipped/failed`.
- **Measured `import app.main`:** warm **17.7 / 18.9 / ~18 s**; cold (first `.pyc` compile) **~105 s**.
- Dominant self-time: **`app.main` body = 5.07 s** (eager `include_router` × 143 → FastAPI route-table + Pydantic model building), then a flat long tail — largest non-app leaf is 0.25 s.
- Heavy eager libs: scipy 1.04 s (via `acoustics/plate_router.py` → `plate_design.inverse_solver`), numpy 0.94 s, ezdxf 0.77 s (via `util/dxf_compat`), sqlalchemy 0.75 s, weasyprint 0.32 s (via `reports/pdf_renderer`).
- **Big-data files are correctly lazy** (`wood_species.json` 885 KB, `art_jobs.json` — all function-scoped, not import-time). Good; not a startup cost.
- **CI-RED-020 connection:** the three `@app.on_event("startup")` handlers are cheap (migrations gated off by default `db/startup.py:36`; safety re-imports are cache hits). The readiness latency the boot-witness waits on **is the ~18 s import** — a short-timeout probe flaps during that window (far worse cold on a fresh Railway container without a warm `__pycache__`). No single quick win; deferring scipy/ezdxf/weasyprint behind function scope recovers ~3–4 s.

### N4. Frontend reactive state size → **VERIFIED, ranked #6 and #8**
- **#6 — `packages/client/src/stores/useToolpathPlayerStore.ts:163-164`** holds **two** deep-reactive arrays of up to 100k `MoveSegment` objects each (`segments`, `fullSegments`; cap `MAX_SEGMENTS=100_000` `:37`, ~200 B/segment `:192` → ~20 MB × 2), plus the full G-code string `:208`. Plain `ref` (deep Vue proxy) not `shallowRef`, app-wide in Pinia. This is the same array set F-X1 rebuilds per tick — the dominant reactivity/memory cost.
- **#8 — LiveMonitor event buffers** (`stores/useLiveMonitorStore.ts`, `components/rmos/LiveMonitor.vue`) keep appending WebSocket events with no retained-event cap — an unbounded growth (effective leak) over a long monitoring session; only manual `clearEvents()` frees it.
- Lower: `toolpath-player/useToolpathLoader.ts:39` `machineStates` (1:1 per segment), `ToolpathComparePanel.vue:180` (2nd full toolpath). `stores/geometry.ts` is explicitly capped — fine.

### C. Algorithmic / concurrency notes (Part C)
- **Algorithmic that bites at scale:** the only *reachable* super-linear cost is Lead #3's `cells × moves` product (§Lead #3) — everything else on live paths is O(n) or guarded. The `preview_infill` contour-parallel loop (`vcarve_router.py:141`, `:205`) is bounded by `region_size / stepover` (min 0.1 mm) → up to thousands of native clipper/shapely ops; **unmeasured** (see §4).
- **SQLite concurrency:** stores open a fresh `sqlite3.connect` per operation (`rmos_db.py:57`) with **no WAL** on the RMOS DB and no pool. Under concurrent writes SQLite serializes on a file lock — fine for a single operator, a latent contention point only under real multi-user load. (`cam_logs.py:247` *does* set `PRAGMA journal_mode=WAL`.) Not a problem at current usage; noted for honesty.

---

## 4. Unmeasured / needs production data (the honest frontier)

These are plausible but I could **not** confirm without real volumes or a running environment. Each lists exactly what would settle it.

| Item | Why unmeasured | What would settle it |
|---|---|---|
| Lead #3 real-world severity | Measured on synthetic toolpaths; real call frequency + typical user grid sizes unknown | Log `grid` size + `moves` count on live `/what_if` calls; sample p95 latency |
| `preview_infill` (vcarve) worst case | Needs pyclipper+shapely fixture with a large region + 0.1 mm stepover | Profile with a real V-carve infill request at min stepover |
| JSON art-jobs growth trajectory | 43 records today; parse/rewrite cost scales with file size | Measure `art_jobs.json` size + `/what_if`… `create_art_job` latency after N months of production jobs |
| F-X1 3D playback freeze | Structurally clear from code + doc; dev server not run | Load a 50k–100k-segment program in the client, record FPS during playback |
| SQLite at scale | rmos.db near-empty; the missing `strip_families`/composite indexes only bite at large `n` | Seed `strip_families`/`patterns` to 10k rows, re-run `EXPLAIN QUERY PLAN` + `timeit` |
| Startup on fresh Railway container | Measured locally; cold `.pyc` behaviour on the real deploy image unknown | Time first-request-ready on a clean container deploy (no warm `__pycache__`) |
| Sync-compute concurrency impact | Verified the pattern; not load-tested | Fire 2 concurrent `/extract_from_photo` requests, measure the 2nd's added latency |

---

## 5. The one-hour fix list (confirmed AND cheap, in order)

Each is a *separate, scoped PR after this audit* — this document changes no code. Ordered by value-per-minute.

1. **Prune `.venv`/`node_modules`/`__pycache__` in the two governance scanners** (`check_semantic_sandbox_imports.py:72`, `check_feedback_correction_calls.py:18`). Copy the existing `PRUNE_DIRS` + in-place `os.walk` prune from `scripts/check_dxf_compat.py:55`. **~240 s → ~4 s of CI time, every run.** (Lead #6)
2. **Clamp the `/what_if` grid workload server-side** (`whatif_opt.py` / `optimization_router.py`) — reject or cap excessive total cells and `cells × moves`; optionally stop deep-copying `moves` per cell. Kills the 10 s tail while allowing cheap rectangular grids. (Lead #3)
3. **Decimate / make opt-in the `moves[]` in `simulate_gcode_upload`** (`simulation_consolidated_router.py:137`) — `move_count` is already returned; gate the full array behind a query param or downsample. Kills the 7–70 MB payload. (Lead #7)
4. **Cap LiveMonitor retained events** in both the store and visible component. Stops the long-session growth. (Finding N4/#8)
5. **Point the live rosette routers at the existing `SQLiteArtJobsStore`** instead of the JSON functions (`rosette_jobs_router.py:79,112`, `rmos/rosette_cam_router.py:415`, `pipeline_ops_rosette.py:77`). The SQLite store + indexes already exist — this finishes a half-done migration and removes the 22 ms parse + full rewrite. (Finding N1/#9)
6. **Preventive DB indexes** (`rmos_db.py`): add `strip_families(material_type)`, `strip_families(strip_width_mm)`, and composite `(<filter>, created_at DESC)` indexes on the list tables. Near-free; hedges Leads #1/#2 against future growth.

**Deliberately *not* in the one-hour list** (real but not cheap): F-X1 3D playback rebuild (#4 — needs incremental scene diffing), startup import time (#5 — structural, ~3–4 s recoverable via lazy imports but no single win), sync-compute offload (#7 — needs `run_in_executor` plumbing per handler). And two **correctness** side-findings for separate tickets: the 500-vertex depth-fuse silently dropping large contours (`graph_algorithms.py:173`), and the `whatif_opt` docstring perf claims being 50–100× optimistic.

---

## 6. What I'd measure next with production data

The audit's honest open frontier (mirrors §4): instrument live `/what_if` grid/move sizes; track `art_jobs.json` size + rosette-create latency over time; FPS-profile a 100k-segment playback in the real client; time first-ready on a cold Railway deploy; and seed the RMOS stores to 10k rows to confirm the index hedges before committing them. None of these block the §5 fixes — they tell you whether items #3/#5/#9's *severity* is climbing, so you fix in the right order rather than on inference.
