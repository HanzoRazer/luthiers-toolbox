# Toolpath Animated Display — G-code → Video Pipeline Audit

**Date:** 2026-05-30
**Scope:** Read-only audit of the system that converts G-code into animated visual playback — backend simulation engine + frontend player/renderer. Status assessment and defect surface. No remediation performed *during* the audit pass itself.
**Method:** Static read of every component in the pipeline; backend engine exercised via its unit suite (53 tests) and direct invocation; frontend read statically (dev server not stood up).

> **Disclosure (read this first).** Earlier in this same session, before this audit was written, the **backend simulation engine was remediated** at the codeowner's explicit instruction (findings previously raised as X1–Z5). Those backend fixes are committed in the working tree and covered by tests. This audit therefore reports the **current** state honestly: the backend engine is now sound and verified; the **frontend half of the pipeline was not touched and carries the open findings.** Where a finding was fixed this session it is marked **[RESOLVED 2026-05-30]** with the evidence; everything unmarked is live.

---

## Summary

The pipeline is **real and coherent end-to-end, and the backend is now trustworthy; the frontend is feature-rich but unverified and silently drops the backend's new fidelity signals.** Roughly: backend engine ~95% (verified by tests), frontend consumer ~70% (works, but with a real playback-performance risk, a family of off-by-one step/seek bugs, no tests, and three places where it discards data the backend now provides).

G-code enters the player, is POSTed to `POST /api/cam/gcode/simulate`, the backend `simulate_segments()` parses it into pre-interpolated motion segments (arcs linearised, canned cycles expanded), the segments return as JSON, a Pinia store caches/downsamples them and builds a cumulative-time index, and a Three.js (3D) or Canvas-2D renderer animates a tool along the path driven by a requestAnimationFrame clock. Every stage exists and connects; the player is mounted in multiple production views.

The honest gaps now live on the frontend: (1) the store rebuilds the **entire** Three.js scene on every playback tick, which will not scale to the segment counts the backend can emit; (2) the step/seek/jump controls share an off-by-one against the half-open cumulative-time search; (3) downsampling silently shortens reported cycle time; (4) the new `warnings`/`tools` payloads are not consumed, so the player can't tell the user the simulation was "limited"; (5) `units` is never passed from the views; and (6) there are **zero** frontend tests over the store, scrub math, or canvases.

---

## System inventory

### Backend (Python — `services/api/app/`)

| File | What it actually does |
|---|---|
| `util/gcode/simulator.py` | Core engine. `simulate_segments()` → per-segment list for animation; `simulate()` → aggregate totals (now a thin wrapper over `simulate_segments`). Modal state machine: motion (G0–G3), units (G20/21), plane (G17/18/19), absolute/incremental (G90/91), canned cycles (G81/82/83/73/85/84 expanded), dwell (G4), tool/spindle (T/S/M). |
| `util/gcode/geometry.py` | Arc math: `arc_center_from_r`, `arc_center_from_ijk`, `arc_len`, plane-aware `interpolate_arc`, `interpolate_arc_points`. |
| `util/gcode/lexer.py` | `parse_lines` tokenizer; strips `()`/`;` comments; emits `(letter, value)` word lists. |
| `util/gcode/reader.py` | Separate file-oriented parser (`parse_gcode`) producing a `Summary` + `Move` list with validation warnings. **Not** on the animation path — used by report/lint flows. |
| `util/gcode/types.py` | `Modal`, `Move`, `Summary`, `MoveSegment` dataclasses. |
| `util/gcode_parser.py` | Back-compat re-export shim → `util/gcode/*`. Tests and the router import through here, so they share the production code. |
| `routers/gcode_consolidated_router.py` | `POST /cam/gcode/simulate` (animation), `POST /cam/gcode/plot.svg`, `POST /cam/gcode/estimate`. Pydantic request/response models. |
| `generators/lespaul_gcode/drilling.py` | Emits `G83`/`G80` peck-drill cycles + helical bores (`G2 … Z…`) — a real producer of canned-cycle G-code the player consumes. |
| `cam/modal_cycles.py` | Canned-cycle generators (`generate_g83_peck_drill`, …) and `should_expand_cycles(post_id)` — the platform conditionally expands cycles depending on the post. |
| `tests/test_gcode_simulate.py` | 28 unit tests of `simulate_segments` (segment types, arcs, units, bounds, parity). |
| `tests/test_gcode_simulate_fidelity.py` | 25 regression tests added 2026-05-30 covering the X/Y/Z findings. |

### Frontend (Vue 3 + TS — `packages/client/src/`)

| File | What it actually does | Verdict |
|---|---|---|
| `sdk/endpoints/cam/simulate.ts` | Typed client for `/cam/gcode/simulate`. Request supports `units`, `rapid_mm_min`, `default_feed_mm_min`, `arc_resolution_deg`. Response types `MoveSegment`, `SimulateBounds`, `SimulateTotals`, `ToolsInfo`. | Real, **types lag backend** |
| `stores/useToolpathPlayerStore.ts` | Pinia store: owns segments, bounds, playback clock, RAF tick, scrub, sessionStorage cache, downsampling, 100k cap, measurement, selection. | Real, central |
| `components/cam/ToolpathCanvas3D.vue` (997 ln) | Three.js renderer: per-segment lines, tool cylinder, stock box, grid, orbit controls, raycast selection, heatmap, measurement overlays. | Real, heavy |
| `components/cam/ToolpathCanvas.vue` | Canvas-2D renderer with zoom-based LOD and viewport culling. | Real |
| `components/cam/ToolpathPlayer.vue` | Top-level player; composes canvas + control layers via the composables below. | Real |
| `components/cam/toolpath-player/` (~35 files) | Layered UI + composables: `PlaybackControlsBar`, `PlayerHudBar`, `ResolutionSlider`, `CollisionPanel`, `OptimizationPanel`, `ExportAnimationPanel`, `MeasurementsPanel`, `KeyboardShortcutsOverlay`, `OverlaysLayer`, `useToolpathLifecycle/Loader/Analysis/CanvasExport/EventHandlers/Navigation/…`. | Mostly real; see findings |
| `composables/useToolpathShortcuts.ts`, `useToolpathStats.ts` | Keyboard map; stats/efficiency derivations. | Real |
| Consuming views | `views/DxfToGcodeView.vue` (primary), plus `views/cam/PocketClearingView.vue`, `art-studio/VCarveView.vue`, `QuickCutView.vue`, `OffsetLabView.vue`, `bridge_lab/SimulatePanel.vue` reference the store/canvas. | Player is reused across several views |

**Frontend tests:** none for this system. `sdk/endpoints/cam/__tests__/` tests the `roughing` endpoint only; no spec covers the store, scrub math, canvases, or player.

---

## Data flow (end-to-end, as observed)

1. **Input.** G-code is generated in-platform (DXF→G-code workflow) and handed to `<ToolpathPlayer :gcode="…">` (e.g. `views/DxfToGcodeView.vue:231`). Raw text; no file streaming.
2. **Kickoff.** `useToolpathLifecycle.ts:44` calls `store.loadGcode(gcode, { arc_resolution_deg: 5 })` on mount — **no `units`** passed.
3. **Cache check.** `useToolpathPlayerStore.ts:301-312` hashes `gcode + opts` (FNV-1a) and checks `sessionStorage`; on miss it calls `simulate({ gcode, ...options })`.
4. **Transport.** `sdk/endpoints/cam/simulate.ts:128` → `POST /cam/gcode/simulate`.
5. **Parse + generate.** Backend `simulate_segments()` (`util/gcode/simulator.py:257`) runs the modal state machine and returns `{ segments, bounds, totals, tools, warnings }`. Arcs are pre-interpolated; canned cycles expanded.
6. **Ingest.** Store keeps `result.segments` and `result.bounds` (`:317-318`); if `> 100_000` segments it downsamples (`:320-321`); `_rebuildCumulative()` builds the cumulative-time array. **`result.tools` and `result.warnings` are not read.**
7. **Render.** `ToolpathCanvas3D.vue` watches `store.currentSegmentIndex` and rebuilds the scene (`:752-757` → `buildToolpath` `:248`), drawing one `THREE.Line` per segment split into completed/upcoming groups, plus a tool cylinder at `store.toolPosition`.
8. **Playback.** `store.play()` (`:339`) starts a RAF loop (`_tick` `:228`) advancing `currentTimeMs` by `wallDelta * speed`. `currentSegmentIndex` is a binary search over cumulative time (`:172`); `toolPosition` lerps within the active segment (`:177`).
9. **Controls.** Play/pause/stop/seek/step/speed/resolution + measurement + selection, all store actions. Scrub bar emits a normalized `seek(0..1)`.

---

## Findings

> Backend findings X1–Z5 are recorded here for the map's completeness and marked **[RESOLVED 2026-05-30]** with evidence. The live, unaddressed findings are the **F-series (frontend)**.

### Class X — real bugs producing wrong output on inputs the system sees

- **F-X1 — The 3D renderer rebuilds the entire scene on every playback tick.**
  `ToolpathCanvas3D.vue:752-757` watches `store.currentSegmentIndex`; on each change it calls `buildToolpath()` (`:248-287`), which clears **all** line groups and recreates one `THREE.Line` (separate geometry+material) per segment for both completed (`:263-266`) and upcoming (`:269-272`) sets. During playback `currentSegmentIndex` changes many times per second, so this is an O(N) teardown+rebuild per tick with N up to the 100k cap. Result: playback of any non-trivial program will stutter or freeze, and per-segment line objects are a draw-call explosion regardless. This is the single largest frontend defect.

- **F-X2 — Step controls are off-by-one against the cumulative-time search and get stuck.**
  `binarySearchCumulative` (`:58-68`) returns the first index where `cumulative[i] >= t`, so segment `i` is active for `t ∈ (cumulative[i-1], cumulative[i]]`. `stepForward()` (`:434-439`) sets `currentTimeMs = _cumulativeMs[next-1]` = `cumulative[currentIdx]` — the **right boundary of the current segment**, which the search maps back to `currentIdx`. So step-forward does not advance the active segment, and repeated presses stay put. `stepBackward()` (`:441-443`) sets `cumulative[currentIdx-2]`, skipping a segment. `jumpToSelected()` (`:386-390`) lands one segment short of the selection for the same reason. The tool *position* is the boundary point (visually plausible) but the active-segment index / HUD is wrong.

- **F-X3 — Downsampling silently shortens reported cycle time.**
  When `result.segments.length > 100_000`, `downsampleSegments()` (`:71-91`) drops segments, then `_rebuildCumulative()` (`:151-158`) and `totalDurationMs` (`:162-164`) sum durations of the **kept** segments only. So a large program reports a *shorter* total time than reality, and the scrub bar maps to the thinned timeline. Fires only on >100k-segment programs, but on those it is wrong, not approximate.

### Class Y — latent bugs that fire on inputs not currently common

- **F-Y1 — `units` cannot reach the backend.**
  `loadGcode` (`:281-288`) accepts only `rapid_mm_min` / `default_feed_mm_min` / `arc_resolution_deg` — there is no `units` parameter at all, and `useToolpathLifecycle.ts:44` doesn't pass one. The SDK *supports* `units` (`simulate.ts:26`), but the store can't forward it. Inch programs therefore depend entirely on an in-band `G20`; an inch program lacking `G20` animates at 1/25.4 scale. (The Les Paul generator emits `G20`, so this is latent today.)

- **F-Y2 — sessionStorage cache key omits a backend version, so this session's backend fix won't reflect for cached programs.**
  `_cacheKey` (`:251-253`) hashes only `gcode + opts`. After the 2026-05-30 backend change, any program already simulated earlier in the same browser session returns the **stale pre-fix** segments from `sessionStorage` until the tab is closed. Low blast radius (session-scoped), but a real correctness-after-deploy trap.

- **F-Y3 — GIF export silently produces WebM.**
  `useToolpathCanvasExport.ts` exposes `format: "webm" | "gif"` (`:11`) but the recorder hardcodes `mimeType: "video/webm"` (`:33`) and never branches on `opts.format`. Selecting GIF yields a WebM blob.

### Class Z — defensive / incomplete / untested

- **F-Z1 — Backend `warnings` are discarded; the player cannot signal "limited simulation."**
  The backend now returns a `warnings` object (unsupported G/M codes, ignored work offsets, degenerate arcs, truncation). The SDK response type (`simulate.ts:108-114`) has **no `warnings` field**, and the store reads only `segments`/`bounds` (`:317-318`). The fidelity signal added on the backend dies at the network boundary — the exact "fail loud" intent is defeated on the UI side.

- **F-Z2 — Backend `tools` (multi-tool tracking) is typed but never consumed.**
  `ToolsInfo` exists (`simulate.ts:98-105`, `tools?` on the response `:113`) but the store never reads `result.tools`, so tool counts / change events never reach the HUD or a tool legend.

- **F-Z3 — Tool visualization is a fixed-size cylinder, not driven by tool changes.**
  `createTool()` (`ToolpathCanvas3D.vue:185-203`) builds one cylinder from `props.toolDiameter`/`toolLength` (defaults 6/50). It is never rebuilt on a `tool_number` change, so the displayed cutter dimensions are static regardless of T-codes. Fine for path preview, wrong for any gouge/clearance read.

- **F-Z4 — Camera only fits the scene at `currentSegmentIndex === 0`.**
  `buildToolpath()` calls `fitCameraToScene()` only when `currentIdx === 0` (`:284-286`). If autoplay advances the index before the first watch fires, or the path is reloaded mid-playback, the view may never frame the work.

- **F-Z5 — Generic error surface on simulate failure.**
  `loadGcode`'s catch (`:328-333`) collapses any failure to `e.message` or `"Simulation failed"`. A 400 (malformed G-code) and a 500 (server fault) are indistinguishable to the user.

- **F-Z6 — Cache eviction is not LRU.**
  `_writeCache` (`:265-277`) evicts `keys[0]` from `Object.keys(sessionStorage)` — insertion/arbitrary order, not least-recently-used — so a hot entry can be evicted while cold ones survive.

- **F-Z7 — 2D canvas DPR handling unverified.**
  `ToolpathCanvas3D` correctly caps `setPixelRatio(min(dpr, 2))` (`:143`). The 2D `ToolpathCanvas.vue` was not confirmed to apply `ctx.scale(dpr, dpr)`; if absent it renders blurry on high-DPI displays. **Unverified — see Unknowns.**

### Backend findings — [RESOLVED 2026-05-30]

Recorded for completeness; all fixed in `util/gcode/simulator.py` + `geometry.py` and covered by `tests/test_gcode_simulate_fidelity.py` (25 tests; full suite 53 green).

- **X1** Z/3D timing — segment `duration_ms` now uses `math.dist` (3D) (`simulator.py:331-333`). Was XY-only → every plunge/retract had zero duration.
- **X2** Canned cycles G81/82/83/73/85/84 expanded into rapid/plunge/peck/retract (`simulator.py:170-231`, `_expand_canned_cycle`). Was ignored → drilling didn't animate.
- **X3** All G-words per line parsed (`simulator.py:43-71` `gs` list); a trailing non-motion G no longer clobbers the motion code.
- **Y1** G90/G91 absolute/incremental tracked (`simulator.py:103-105`, `:340-348`).
- **Y2** G18/G19 arcs simulated via plane-aware `interpolate_arc` (`geometry.py:171+`); position always advances (no desync).
- **Y3** `arc_center_from_r` returns `None` on zero chord (`geometry.py:85-90`) instead of fabricating a circle.
- **Z1** Unsupported G/M, work offsets, degenerate arcs, truncation collected into `warnings` (`simulator.py:73-135`, `:512-521`). *(Surfacing to UI is open — F-Z1.)*
- **Z2** Dwell (G4) consumes time via a `dwell` segment (`simulator.py:357-362`).
- **Z3** Bounds computed from destinations, excluding the synthetic home origin (`simulator.py:304-307`).
- **Z4** `tools` payload wired through the router (`gcode_consolidated_router.py:138-164`). *(Consuming it is open — F-Z2.)*
- **Z5** Backend segment cap with loud truncation (`simulator.py:264`, `:330-333`).

### Cosmetic

- `ToolpathCanvas3D.vue:352` `linewidth: 1` with a comment noting `>1` is unsupported on most platforms (known).
- `useToolpathLifecycle.ts` paste showed a couple of display-glitch typos in this session's tooling; verify the on-disk file is clean.
- `memoryInfo` estimates 200 bytes/segment (`:122`) — a rough heuristic that may trip the warning early/late.

---

## Test coverage gaps

- **Class X gap:** No frontend test exercises the RAF loop, `binarySearchCumulative`, `seek`, `stepForward/Backward`, or `jumpToSelected` — so F-X2 (step off-by-one) and F-X3 (downsample time loss) are invisible to CI. No render/perf test, so F-X1 is uncaught.
- **Class Y gap:** No test passes `units`, exercises the cache across a backend change, or hits the export format branch.
- **Class Z gap:** Nothing asserts the store reads `warnings`/`tools`; no test mounts either canvas beyond (non-existent) smoke tests.
- **Backend:** now covered — `test_gcode_simulate_fidelity.py` adds Z-duration, multi-G, G90/91, G18/19, R-full-circle, unsupported-code, dwell, bbox, tools, cap, and canned-cycle assertions; the previously false-confidence parity test now shares one engine (delta ~1e-17).

---

## Known limitations (absent, not broken)

- No acceleration/deceleration model — constant-velocity timing; durations are first-order even with the Z fix.
- No material-removal / stock simulation in this path (`StockSimulationPanel.vue` is separate).
- No collision detection feeding the animation geometry (`CollisionPanel` consumes a separate analysis composable).
- Tool is a position cylinder, not a dimensioned cutter with spindle/edge offset (F-Z3).
- No work-offset (G54–G59) application — animation is in program coordinates; offsets are only flagged.

---

## Unknowns (not determinable from a static read)

- **Renderer behavior under load.** The dev server was not run. F-X1 is inferred from the rebuild-per-tick structure; the actual frame rate at 10k/100k segments, scrub frame-accuracy in the live UI, and whether the WebM export panel produces a valid file are unverified.
- **2D canvas DPR (F-Z7).** Whether `ToolpathCanvas.vue` applies a devicePixelRatio transform was not confirmed.
- **Export panel wiring — CONFIRMED wired** (resolved during audit). `ToolpathPlayer.vue:133-141` instantiates `useToolpathCanvasExport`, and `:353 @start-export="canvasExport.startCanvasExport()"` reaches a real MediaRecorder implementation (`useToolpathCanvasExport.ts:37-51` → `useToolpathExport`). So the export feature is genuinely connected; the only open export defect is **F-Y3** (GIF selection produces WebM). What remains unverified is whether the produced blob plays back correctly (needs the dev server).
- **Which views pass non-default options.** Several views mount the player; only `DxfToGcodeView` + `useToolpathLifecycle` were traced. Others may pass (or omit) `units`/feeds differently.

---

## Recommended next steps (for codeowner planning — not a sprint plan)

1. **Stop rebuilding the scene every tick (F-X1).** This is the difference between "demo on a tiny file" and "usable." Build the line set once on load; per tick, only move the tool and recolor the completed/upcoming boundary (or use a single merged geometry with a draw-range). Until then, treat the player as small-file-only.
2. **Fix the cumulative-time off-by-one family (F-X2).** One root cause across `stepForward/stepBackward/jumpToSelected`: they write a segment's *boundary* time, which the half-open search attributes to the neighbor. Decide the convention (land at `cumulative[index-1] + ε`, or change the search to lower-bound) and apply it once.
3. **Carry `warnings`/`tools` to the UI (F-Z1/F-Z2).** The backend's fail-loud work is wasted until the SDK type gains `warnings`, the store reads both, and the player shows a "limited simulation" banner + tool legend. Small, high-value, and it closes the loop the backend remediation opened.
4. **Thread `units` through (F-Y1).** Add `units` to `loadGcode` and pass it from the views, so inch jobs don't depend on an in-band `G20`.
5. **Add the first frontend tests (coverage).** Unit-test `binarySearchCumulative` + the step/seek/jump actions (would have caught F-X2) and the downsample time-conservation (F-X3) before fixing them, so the fixes are pinned.

---

*Audit complete. No frontend code was changed during this pass. The backend remediation referenced above was performed earlier in the session at the codeowner's instruction and is documented as resolved with test evidence. Decisions on what is MVP-blocking versus deferrable are the codeowner's; the deferred items are tracked in `SPRINTS.md` → CAM-TPA-001.*
