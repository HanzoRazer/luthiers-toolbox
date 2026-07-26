# Performance Audit — Executive Developer Handoff

**Date:** 2026-07-04 · **Scope:** luthiers-toolbox API + client

---

## Bottom line

We profiled the platform's real bottlenecks (measured, not guessed) and shipped the confirmed, cheap fixes. **Biggest wins:** a CAM optimizer endpoint that could hang a request thread for ~10s is now bounded; a simulation endpoint that could return 7–70 MB now returns a bounded preview; a CI step that timed out at ~4 minutes now runs in seconds; and the rosette art-job store no longer re-parses and rewrites a 730 KB file on every save. Several loudly-suspected "hot spots" were **measured and cleared** — don't spend time optimizing them.

---

## Performance picture, by subsystem

Each row: what we measured → what we did → impact. `verified` = measured; `refuted` = measured and *not* a problem.

### CAM / request-thread compute
- **`POST /api/cam/opt/what_if`** (`app/cam/whatif_opt.py`) — feed/stepover optimizer is `O(grid_cells × moves)`, clones the full moves list and re-estimates per cell, runs **synchronously on the request thread**. Measured **0.5s** (default 6×6, ~2k moves) → **10.6s** (20×20). Client-controlled, uncapped. → **Fixed:** grid axis capped at 12 (default unchanged); larger grids get a 400 pointing at bounds refinement. `verified`.
- **`adaptive_core.py`** ("legacy O(n²) geometry") — **dead code**, zero live/test importers; live paths use `adaptive_core_l1`. → No action. `refuted`.
- **Sync CPU inside 3 `async def` handlers** (`photo_vectorizer_router.py:360`, `blueprint/phase3_router.py:156`, `vision/segmentation_router.py:76`) — full vectorization/vision blocks the event loop, stalling *all* concurrent requests. → **Deferred** (needs `run_in_executor`; correct pattern already in `body_solver_router.py`). `verified`.

### API payload sizes
- **`POST /api/cam/sim/upload`** (`app/routers/simulation_consolidated_router.py`) — echoed one JSON object per motion line, **unbounded**; a 3D program (10⁵–10⁶ lines) → **~7–70 MB** response. → **Fixed:** returns a decimated preview (default 5000 moves) with true `move_count`/stats intact; `include_moves=true` opts into full fidelity.
- **Note:** the live endpoint is `app/routers/simulation_consolidated_router.py`, **not** the same-named file under `app/cam/routers/simulation/` — that one is a dead, unmounted duplicate. (Found by exercising the route, not by grep.)

### Data stores
- **Rosette art-job store** — two file-based stores re-parsed + rewrote the entire **~730 KB `data/art_jobs.json` on every create/read** (measured **22 ms/parse**, append-only, unbounded), and had accidentally split into two incompatible record shapes sharing one file. → **Fixed:** each now backs onto its own SQLite table (existing `SQLiteArtJobsStore` + a new `art_studio_jobs` table), with a one-time shape-filtered migration. Public APIs unchanged, so no route behavior changed. `verified`.
- **RMOS SQLite (patterns/joblogs/etc.)** — list/history queries were the loudest prior lead. **Measured refuted:** already index-covered, and the DB is near-empty (single-operator, `n≈0`). → Added *preventive* indexes only (`strip_families` had none; composite `created_at` removes sort overhead) as a cheap hedge against growth. `refuted` (as a current bottleneck).

### CI / developer-loop time
- **Two governance scanners** (`scripts/governance/check_feedback_correction_calls.py`, `check_semantic_sandbox_imports.py`) walked the whole tree **including `.venv`** — 7,423 of 9,624 files scanned were third-party, and both **timed out at 120s** in CI. → **Fixed:** prune dependency dirs (reused the existing pattern in `check_dxf_compat.py`); now **~1.5–2.5s each** (~4 min of CI reclaimed).

### Startup / boot
- **API import ~18s warm / ~105s cold** — 143 routers mounted eagerly + heavy libs (scipy/ezdxf/weasyprint) imported at module load. This is the latency a readiness probe waits on (explains CI-RED-020 flapping). Big data files are correctly lazy. → **Deferred** (lazy-import the heavy libs recovers ~3–4s; no single silver bullet). `verified`.

### Frontend perceived latency
- **3D toolpath playback (F-X1)** — the Three.js scene is **rebuilt in full every playback tick** (N up to 100k). Documented as "the single largest frontend defect" (`ToolpathCanvas3D.vue:752`). → **Deferred** (needs incremental scene diffing; tracked `SPRINTS.md → CAM-TPA-001`). `verified` (from code+doc; not driven live).
- **Toolpath store** holds 2× up-to-100k deep-reactive arrays (`useToolpathPlayerStore.ts:163`). → **Deferred** (`shallowRef` + input cap).
- **LiveMonitor event stream** grew without bound over a session (`useLiveMonitorStore.ts`). → **Fixed:** 500-entry ring buffer.

---

## Shipped this session — impact table

| Improvement | Impact | Risk |
|-------------|--------|------|
| Cap `what_if` grid | request-thread stall 10.6s → bounded | low (default unchanged) |
| Decimate `sim/upload` preview | response 7–70 MB → bounded (opt-in full) | low (small uploads unchanged) |
| Art-job stores → SQLite | drops 22 ms parse + full 730 KB rewrite per op; unbounded-growth removed | medium (storage-backend; public API + data preserved via migration) |
| Prune `.venv` in CI scanners | ~4 min of CI per run reclaimed | low (dev tooling only) |
| Preventive RMOS indexes | hedge against future data growth | low (additive, idempotent) |
| Bound LiveMonitor buffer | removes a long-session memory leak | low |

All changes are test-covered (new + existing suites pass) and backward-compatible except the art-job storage backend, which preserves the public API and migrates existing data.

---

## What we checked and cleared (so you don't re-investigate)

- SQLite list/history queries — index-covered, `n≈0`.
- `adaptive_core.py` O(n²) — dead code.
- DXF contour reconstruction — already O(n) with a 30s timeout + hard limits; measured linear to 10k edges.
- Second-pass materialization loops — all benign single O(n) passes.
- N+1 queries — none on any live request path.

---

## What's left (prioritized)

| Priority | Item | Location | Why deferred |
|----------|------|----------|--------------|
| High (perceived latency) | 3D playback rebuilds whole scene per tick | `ToolpathCanvas3D.vue:752` → `buildToolpath()` | needs incremental scene diffing |
| Medium (concurrency) | Sync CPU in 3 `async def` handlers | `photo_vectorizer_router.py:360`, `blueprint/phase3_router.py:156`, `vision/segmentation_router.py:76` | needs threadpool offload |
| Medium (boot) | ~18s import time | eager scipy/ezdxf/weasyprint + 143-router mount | lazy imports recover ~3–4s |
| Low–med (frontend) | Toolpath store 2× 100k reactive arrays | `useToolpathPlayerStore.ts:163` | `shallowRef` + cap |

**Correctness side-findings (not performance, worth a ticket):**
- 500-vertex depth-fuse silently drops large single contours — `app/cam/graph_algorithms.py:173` (a spline-heavy outline flattened to >500 segments returns `loops=0` / HTTP 422).
- `whatif_opt` docstring perf claims are 50–100× optimistic (`app/cam/whatif_opt.py:234-236`).

**Measure with production data before acting on the deferred items:** live `what_if` grid/move sizes (real p95), art-job growth post-migration, a 100k-segment playback FPS, and cold-container first-ready time.

---

## Appendix — where the code lives

Full measured audit: `PERFORMANCE_AUDIT_2026-07-04.md`. Shipped fixes are in two open PRs (**#188** one-hour fixes; **#189** art-job store migration); verification commands and per-fix commits are in each PR description. Rebase each on latest `main` before merge — the diff-based CI gates are base-sensitive.
