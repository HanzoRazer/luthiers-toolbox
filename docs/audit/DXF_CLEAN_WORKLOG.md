# DXF CLEAN — Worklog (living)

**Stream:** Phase 2 of 3 — **CLEAN** (acts on the AUDIT matrix). The matrix
(`DXF_FORMAT_FLOW_MATRIX.md`) is the **frozen** snapshot; this is the living record of CLEAN actions.
**Started against:** `origin/main` (post-#150).

> Separate from the AUDIT matrix on purpose: AUDIT stays a frozen, reproducible snapshot at `c33b700a`;
> CLEAN findings accumulate here so the phase boundary stays legible.

---

## Done

### PR #150 — contour_reconstruction off the raw-bypass (CONSOLIDATE-lever applied to one emitter)
Squash `db9a7a1b`. `reconstruct_contours` + `reconstruct_bracing_dxf` converted from raw
`msp.add_lwpolyline` onto canonical `dxf_compat.add_polyline`; default now **R12-safe (AC1009, LINE
chains)**, R2000/LWPOLYLINE explicit opt-in; governed save records the actual emitted version. Bracing's
R12-safety justified by **data-flow trace** (bytes reach only the HTTP Response; the
`/reconstruct-contours`→pocketing path is a *name collision* on the separate `app.cam.contour_reconstructor`),
not grep-by-name. Confirmed green on the real merge commit.

### UNKNOWN seams grounded (matrix's start-order: UNKNOWNs first) — 2026-06-23
Read-only data-flow traces. Resolution: **UNKNOWN → {DEAD, RISK, DEAD}** — live RISK surface *shrank*.

| Matrix UNKNOWN | Resolution | Evidence |
|---|---|---|
| `core/dxf_geometry.load_dxf_geometries` (LINE+CIRCLE reader) | **DEAD** | Function-name grep across `app` returns only the def; module imported nowhere. No live caller. (Function-name grep is authoritative for callers; still confirm before deleting per the grep-absence tier.) |
| `cam/contour_reconstructor.reconstruct_contours_from_dxf` (LINE+SPLINE reader) | **RISK** (live) | Two feeders: `/reconstruct-contours` HTTP route (`blueprint_cam_core_router:65`, arbitrary user upload) + IBG `topology_recovery` (internal fallback). LWPOLYLINE-only upload → **silent empty loops** (inverse-direction D5 silent-break). Stays on CLEAN core list. |
| `cam/archtop/archtop_contour_generator.read_single_outline` (closed-(LW)POLYLINE only) | **DEAD via broken route** | Only caller is `mode_outline`, reached by `/contours/outline` shelling out via subprocess — but `archtop_cam_router:123` script path is **stale** (`cam/archtop_contour_generator.py`; file is at `cam/`**`archtop/`**`archtop_contour_generator.py`). Path doesn't resolve → route 500s "not found" before reaching the consumer. Not live-reachable. (Path is CWD-relative; assumes server runs from repo root.) |

**C2-intersection pre-check (before grounding):** all 3 seam files contain **zero** C2-arbitrated symbols
(`ContinuityLevel`/`continuity_*`/`topology_builder`/geometry-authority/IBG-vocab). DXF CLEAN is
**independent** of the C2 arbitration — parallel tracks, not sequential.

---

## Leads recorded (out-of-scope — NOT chased)

- **Broken route bug:** `/contours/outline` (`routers/cam/guitar/archtop_cam_router.py:123`) shells out to
  a **stale post-reorg script path** (`services/api/app/cam/archtop_contour_generator.py` → should be
  `cam/archtop/archtop_contour_generator.py`). Route returns HTTP 500 before reaching the generator.
  CAM/route bug, not a DXF-format issue — recorded-and-passed (Appendix-C class).

---

## Done — 4 grep-absence DEAD seams data-flow-confirmed (2026-06-24)

Per the grep-absence-vs-positive-trace discipline, each was traced across **all** of `services/api`
(app + tests + manifests/registries), not by call-by-name. Result: **of 4 grep-flagged DEAD, ZERO were
safe-and-right to retire now — 2 are live/tested (refuted), 2 are runtime-dead-but-intended-utility (deferred).**

| Candidate | Verdict | Evidence |
|---|---|---|
| `cam/body_region_selector.py` (`BodyRegionSelector`/`select_*`) | **runtime-DEAD, intended-utility — DEFERRED** | Zero importers anywhere — verified beyond grep: no dynamic import / `__all__` re-export / router-manifest entry (only non-self ref is `complexity_baseline.json`). BUT it is a coherent **Sprint-3 body-isolation feature** (446 lines, auto body-outline detection from blueprint sheets) in an **active area** (IBG / blueprint-reader / morphology); the matrix said "retire **or wire**". By the same intended-utility standard applied to `line_deduplicator`, **deferred pending an explicit wire-or-abandon decision** rather than retired. File **retained**; its `complexity_baseline.json` entry is **intentionally kept** — the file still exists, so it is not an orphan. |
| `cam/line_deduplicator.py:deduplicate_parallel_lines` | **runtime-DEAD, test-coupled — DEFERRED** | Only caller is the lifecycle-guard test `test_dxf_lifecycle_read_modify_save_guards.py`. No production path. Retiring = also remove its guard test; judgment call (intended utility?) — left in place. |
| `generators/bezier_body.py:BezierBodyGenerator` | **NOT DEAD — REFUTED** | Re-exported in `app.generators.__all__` (`__init__.py:70,136`); full suite `test_bezier_body_generator.py` + guard test. Tested public-API library (no HTTP route ≠ dead). Do **not** retire. |
| `art_studio/services/generators/inlay_export.py:geometry_to_dxf_bytes` | **NOT DEAD — REFUTED** | **Live**: called by `art_studio/api/inlay_pattern_routes.py:133`, which is **mounted** via `router_registry/manifests/art_studio_manifest.py:81`. Do **not** retire. |

**Discipline payoff (stronger than first written):** of the 4 grep-absence DEAD candidates, **none were
safe-and-right to retire outright.** 2 are live → **refuted** (a mounted-route dependency `geometry_to_dxf_bytes`;
a tested public-API class `BezierBodyGenerator`); 2 are runtime-dead-but-intended-utility → **deferred**
(`line_deduplicator` test-coupled; `body_region_selector` a Sprint-3 feature in an active area). **This pass:
0 retired, 2 deferred, 2 refuted.** The trace didn't just catch 2 false-deads — it caught that even the one
genuinely import-dead module wasn't *right* to delete yet (intended-utility; git-recoverable but
undiscoverable once deleted). Matrix Appendix-A (frozen — fold in at next matrix revision) should drop the
2 refuted from the DEAD list and move the 2 deferred to a deferred-pending-decision bucket. The 2 newly-DEAD
from UNKNOWN-grounding (`load_dxf_geometries`, `read_single_outline`/broken-route) still pending the same pass.

## Next (CLEAN, per matrix start-order)

1. Data-flow-confirm the 2 newly-DEAD (`load_dxf_geometries`, `read_single_outline`/broken-route) before retiring.
2. Work the **RISK seams** — the R12/LINE-producer-meets-strict-LWPOLYLINE-consumer cases at the
   user-upload boundary, now including `#2 contour_reconstructor` (inverse: LINE/SPLINE-consumer fed
   LWPOLYLINE).
3. Appendix-B contract-label mismatches + the toolpath header/entity inconsistency.

CONSOLIDATE (the ~25 `create_document` emitters + a tier-aware version-negotiation helper) comes after CLEAN.
