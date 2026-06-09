# Surface Grounding — Executable Ground Truth Across Four Code Surfaces

**Date:** 2026-06-04
**Repo:** `luthiers-toolbox-clean` (sibling checkout), branch `main`, HEAD `d11dc81d`, clean tree.
**Method:** READ-ONLY executable grounding. Imports run, tests collected and run, routes
enumerated from the live app object, git refs queried. No edits, staging, commits, or fixtures.
This document is the only file written.
**Principle:** Narrative checkpoints are informational; execution defines truth (Directional
Manifesto §3). A checkpoint's "COMPLETE" is at best OBSERVED until execution upgrades it.

## Confidence vocabulary
- **VERIFIED** — confirmed by execution (import/test/route). Command + result stated.
- **OBSERVED** — directly visible in code/structure, not executed.
- **INFERRED** — architectural interpretation; needs validation.
- **SPECULATIVE** — projection; flagged as such.

---

## STEP 0 — Shell Health Gate: **PASS**

All four probes returned output **and** exit codes, witnessed live (PowerShell, the session shell
all subsequent commands routed through):

| Probe | Result (verbatim) |
|---|---|
| `echo grounding-probe-alive` | `grounding-probe-alive` |
| `python --version` | `Python 3.14.0` |
| `git -C ...\luthiers-toolbox-clean rev-parse --abbrev-ref HEAD` | `main` |
| `git --version; "exit=$LASTEXITCODE"` | `git version 2.53.0.windows.2` / `exit=0` |

Clean-tree precondition re-verified at execution time: `git status --porcelain` → empty,
`porcelain-exit=0`; HEAD `d11dc81d` (#88 squash of 8G). **Floor confirmed — the shell did not lie
by omission.** The shell remained healthy for the entire pass (every command below returned output
and an exit code; no dead-probe symptom observed).

**Dependency floor (one-time):** `fastapi, pydantic, pytest, pytest_cov, pytest_asyncio, ezdxf,
numpy` all import in the system interpreter (`deps-exit=0`). Therefore a Python import failure in
any surface would be **genuine in-repo breakage**, not an env-blocked artifact. No installs were
performed (locked env policy: diagnose, don't install). **No venv exists** in the repo; system
Python 3.14.0 was used.

**JS toolchain:** Node v24.11.0 / npm 11.6.1 present, but **no `node_modules` anywhere** and **no
vitest binary**. Running the TS/Vue suites would require `npm install` (a large tree mutation, out
of read-only scope). Per the locked fallback, all TS/Vue **run-status is INFERRED**, compensated by
reading what the tests assert (real behavior vs stub).

---

## SURFACE A — Aperture / Neck Studio

**Question:** did the A3–A6 chain land, or is it stranded at A2 (spiral math only)?

| Claim | Tag | Evidence (command + result) |
|---|---|---|
| `aperture_geometry.py` exists; `ApertureGeometry` dataclass defined | OBSERVED | `services/api/app/instrument_geometry/soundhole/aperture_geometry.py`; `@dataclass class ApertureGeometry` at line 30; bridge `aperture_from_spiral_geometry()` at line 74 |
| A2 spiral math present | OBSERVED | `soundhole/spiral_geometry.py` exists alongside |
| Module + `app.main` import (A2+A3) | **VERIFIED** | `python -c "from app...aperture_geometry import ApertureGeometry, aperture_from_spiral_geometry; from app...spiral_geometry import SpiralGeometry; from app.main import app"` → `IMPORT-OK`, `import-exit=0` (full registry: 141 routers loaded) |
| Soundhole/aperture tests pass (A2–A4) | **VERIFIED** | `pytest tests/test_soundhole_spiral.py tests/test_aperture_geometry.py tests/test_aperture_geometry_endpoint.py tests/test_soundhole_spiral_endpoint.py` → **47 passed**, `pytest-exit=0` |
| API routes registered (A4) | **VERIFIED** | route enum from live `app`: `/api/instrument/soundhole`, `/types`, `/spiral/geometry`, `/spiral/dxf`, `/spiral/default`, `/spiral/validate` (route-exit=0) |
| Aperture geometry delivered via live endpoint | **VERIFIED** | `/soundhole/spiral/geometry` injects `aperture_geometry` into response (`soundhole_router.py:365–369`); endpoint tests POST to live app and assert real response structure — behavioral, not stubbed |
| A5/A6 Vue workspace exists | OBSERVED | `packages/client/src/views/art-studio/ApertureWorkspace.vue` exists; **stays OBSERVED** — checked 2026-06-07 with vitest now installed: there is **no aperture frontend test suite** to run. The four aperture files (`ApertureWorkspace.vue`, `StandardAperturePanel.vue`, `ApertureResultCard.vue`, `ApertureComparisonPanel.vue`) have no co-located `.test.ts`/`.spec.ts`; the only test that mentions "aperture" (`topologyVariant.test.ts`) uses it as a `category` enum value, not a workspace test. Cannot be execution-upgraded until such a test exists |

**Verdict: COMPLETE-VERIFIED (backend A2–A4); A5–A6 frontend OBSERVED (no runnable test).**
The handoff's "A2 done, A3–A6 pending" is **REFUTED for A3 and A4** — both are shipped and
execution-verified on main. The feature is **not** stranded at A2. A5/A6 stays OBSERVED: the
2026-06-07 toolchain install made vitest available, but no aperture frontend suite exists to convert
OBSERVED→VERIFIED — that conversion is blocked on a frontend test that has not yet been written, not
on the toolchain.

---

## SURFACE B — Measurement Lab / DO-83

**Question:** is DO-83 actually shipped on main, or a last-response that never landed?

| Claim | Tag | Evidence |
|---|---|---|
| `experimentalSession.ts` (types + utils) exists | OBSERVED | `packages/client/src/types/acoustics/experimentalSession.ts`; `src/utils/acoustics/experimentalSession.ts` |
| Utils export the four claimed fns (+1) | OBSERVED | `createExperimentalSession:38`, `appendArchiveToSession:70`, `sortSessionArchives:93`, `buildSessionSummary:138`, `linkVariantToSession:184` |
| `ExperimentalSessionPanel.vue` exists | OBSERVED | `packages/client/src/components/acoustics/ExperimentalSessionPanel.vue` |
| Test count = 23 | OBSERVED | `__tests__/experimentalSession.test.ts` — 23 `it()` cases (4+4+3+4+3+2+1+2) |
| Tests are real behavioral, not stub-pinning | OBSERVED | Import the **real** `../experimentalSession` (no `vi.mock`/stub); assert timestamp-derived ID gen, reference-equality immutability, dedup, timestamp sort order, `durationDays=4`, null-handling, forbidden-recommendation-field absence |
| Panel wired into `ApertureWorkspace.vue` | OBSERVED | import at `:41`; rendered with live prop at `:274` `<ExperimentalSessionPanel :archives="evidenceArchivesById" />` — real binding, not a dangling import |
| Tests collect/run | **VERIFIED** | was INFERRED (vitest uninstalled); upgraded 2026-06-07 via `cd packages/client && npx vitest run src/utils/acoustics/__tests__/experimentalSession.test.ts` → **23/23 passed** (vitest 2.1.9, 1 file, 0 red, 0 skipped) — **exact match to the 23-`it()` source-read count**, so no overcount was hiding incompleteness. Assertion-content read (above) remains corroborating evidence |

**Verdict: SHIPPED → CLOSEOUT (run-status VERIFIED).**
All OBSERVED evidence is mutually consistent with a landed feature: files present, exports complete,
panel rendered with a real prop binding, 23 genuinely behavioral tests against the real module. The
last gap — executable test-run confirmation — was closed on 2026-06-07: `npm install` in
`packages/client` provided the toolchain, and `npx vitest run experimentalSession.test.ts` returned
**23/23 passed**, the exact count the source-read predicted. The INFERRED→VERIFIED upgrade is done;
the asterisk is removed.

---

## SURFACE C — CAM-Intent lanes 8G–8J + convergence

**Question:** did the two CAM sprints converge — are all four lanes real (not faked) on main?

**Structural census (VERIFIED):** `find services -name '*.py'` for profiling/drilling/pocketing
intent files → **NONE**. Only `cam/routers/vcarve/intent_router.py` + `cam/vcarve/intent_adapter.py`
+ `intent_schema.py` exist. `git log --all --grep='Dev Order 8'` across **all refs** → only **8G**
and **8H** commits exist; **no 8I or 8J commit anywhere**.

| Lane | Tag | Evidence | Status |
|---|---|---|---|
| **8G vcarve** | **VERIFIED** | imports (in `app.main` load); `pytest tests/cam/test_vcarve_design_schema.py tests/cam/test_vcarve_intent_migration.py` → **33 passed**, `vcarve-pytest-exit=0` (incl. `TestVCarveIntentRouterIntegration::test_intent_endpoint_accepts_valid_request`); `/api/cam/vcarve/intent-gcode` registered in live app; adapter does real work (`vcarve_params_from_intent` → `VCarveConfig`/`MLPath`); FAKE-CHECK on adapter+router → **no stub patterns** | **COMPLETE-VERIFIED on main** |
| **8H profiling (Profile)** | **VERIFIED** (absence on main; presence on salvage) | No intent file on main. Commit `a9634ab1 feat(cam): add Profile CamIntentV1 endpoint migration (Dev Order 8H)` is reachable **only** from `remotes/origin/salvage/confenv-stash2-devorder-namespace`. Main copy is **absent** (not a thinner stub — it does not exist); the salvage copy is the only and more-complete one | **NOT-LANDED on main → RECOVERY from salvage** |
| **8I drilling** | **VERIFIED** (absence) | No intent lane in any ref. Frontend `views/cam/DrillingView.vue::generateToolpath()` = `loading=true; await new Promise(r=>setTimeout(r,500)); loading=false` — no toolpath work | **NOT-LANDED → FAKE frontend scaffold** |
| **8J pocketing** | **VERIFIED** (absence) | No intent lane in any ref. Frontend `views/cam/PocketClearingView.vue`: `await setTimeout(...,1000); estimatedTime.value = 12.5 // mock` | **NOT-LANDED → FAKE frontend scaffold** |

**8J contradiction resolved by execution:** the "REMAINING" checkpoint is **correct**; the "COMPLETE"
checkpoint is **REFUTED** — no pocketing intent lane exists in any reachable ref.

**Neck-audit setTimeout cross-check:** 6 CAM-ish Vue views carry `setTimeout`, including
`DrillingView`, `PocketClearingView`, `ContourCuttingView`, `SurfacingView`, `CamWorkspaceView`,
`FretSlottingView`. The two relevant to 8I/8J (Drilling, PocketClearing) are confirmed demo
scaffolds (fake delay / explicit `// mock`), not real operations.

**Verdict: NOT CONVERGED. 8G COMPLETE-VERIFIED · 8H RECOVERY (salvage-only) · 8I + 8J NOT-LANDED
(FAKE frontend).** Only one of four lanes is real on main.

---

## SURFACE D — DXF header collision (the C2 seam)

**Question:** which two DXF-writing surfaces carry mismatched header namespace counts; is it live on main?
*(Scoped strictly to the namespace mismatch — not the broader ezdxf.new() violation inventory.)*

The two surfaces are the **two `dxf_compat.py` modules**, both tracked on main
(`git ls-files --error-unmatch` confirms both):

| Surface | Tag | Header namespace set emitted (source-level) |
|---|---|---|
| `services/api/app/util/dxf_compat.py` `create_document()` | OBSERVED | **{ } — none.** R12: `ezdxf.new(validated)`; R13+: `ezdxf.new(validated, setup=setup)`. `grep 'header['` → **NONE**. Sets no `$INSUNITS`, `$MEASUREMENT`, `$EXTMIN/$EXTMAX` (relies on ezdxf defaults) |
| `services/blueprint-import/dxf_compat.py` `create_document()` (+ `set_document_bounds()`) | OBSERVED | **{ `$INSUNITS`=4, `$MEASUREMENT`=1 }** for R13+ (lines 93–94); **plus { `$EXTMIN`, `$EXTMAX` }** from geometry via `set_document_bounds()` (lines 199–200) |

- **Divergence live on main: YES.** Both files present and define divergent `create_document`. The
  api copy emits **0** explicit header vars; the blueprint-import copy emits **2–4**.
- **`set_document_bounds` is live-called (VERIFIED):** imported at `vectorizer_phase3.py:66`,
  invoked at `vectorizer_phase3.py:2630` (`set_document_bounds(doc, body_pts)`) — so `$EXTMIN/$EXTMAX`
  population is active, not dormant.
- **Governance conflict (OBSERVED):** CLAUDE.md BLOCKING INFRASTRUCTURE states *"No EXTMIN/EXTMAX
  population (use sentinel values 1e+20)."* The blueprint-import surface **populates EXTMIN/EXTMAX
  from real geometry**, directly contradicting the stated standard; the api surface complies.
- **Run-status caveat (INFERRED):** the *runtime-emitted* header was not dumped (writing a test DXF
  is outside the read-only scope). The divergence is OBSERVED definitively at source; the precise
  on-disk header contents are INFERRED from the source assignments.

**Verdict: DIVERGENCE PRESENT / LIVE ON MAIN — UNRECONCILED.** Two DXF writers disagree on header
namespace count (0 vs 2–4), and the blueprint-import path additionally violates the repo's own
EXTMIN/EXTMAX sentinel standard.

---

## What this changes

Based only on VERIFIED/OBSERVED findings (INFERRED items flagged):

**Closeouts (document as done; do not re-open as work):**
- **Surface A backend (A2–A4)** — COMPLETE-VERIFIED on main (47 tests, routes registered, live
  endpoint emits aperture geometry). The "stranded at A2" narrative is refuted.
- **Surface B / DO-83 Measurement Lab** — SHIPPED & **run-VERIFIED (2026-06-07)**. Files, exports,
  rendered panel with a real prop binding all present, and the experimentalSession suite now runs
  green: `npx vitest run experimentalSession.test.ts` → **23/23 passed**, the exact source-read
  count. The last asterisk is removed — INFERRED→VERIFIED is done, not pending.

**Recovery jobs (real, but the work already exists elsewhere):**
- **Surface C / 8H profiling (Profile CamIntentV1)** — implemented at `a9634ab1` on
  `origin/salvage/confenv-stash2-devorder-namespace`, never merged to main. Recover/cherry-pick;
  do not rebuild from scratch.
- **Surface A / A5–A6 frontend workspace** — exists (`ApertureWorkspace.vue`), **stays OBSERVED**.
  Checked 2026-06-07 with vitest installed: no aperture frontend test suite exists to run, so this
  cannot be execution-upgraded yet. The genuine follow-up is **writing** a frontend test for the
  aperture workspace, not running an existing one.

**Real remaining work (does not exist anywhere; must be built):**
- **Surface C / 8I drilling + 8J pocketing intent lanes** — no backend lane in any ref. The
  frontend `DrillingView`/`PocketClearingView` are `setTimeout` demo scaffolds (one with an explicit
  `// mock`) and must be replaced with real intent endpoints. This is the genuine CAM sprint to
  restart — and it is **two lanes, not "convergence of four."**
- **Surface D / dxf_compat reconciliation** — unify the two header policies (0 vs 2–4 namespace
  vars) and resolve the EXTMIN/EXTMAX-vs-sentinel governance conflict (blueprint-import currently
  violates the stated standard, live, via `vectorizer_phase3.py:2630`).

---

*Read-only pass complete (2026-06-04). No repository state modified. No action taken on findings.*

---

## Upgrade log

**2026-06-07 — Surface B INFERRED→VERIFIED.** Toolchain installed (`npm install` in
`packages/client`; `node_modules` is gitignored, tracked tree unchanged) and the one blocking suite
run: `npx vitest run src/utils/acoustics/__tests__/experimentalSession.test.ts` → **23/23 passed**
(vitest 2.1.9), the exact 23-`it()` count from the source-read. Surface B run-status upgraded
INFERRED→VERIFIED; closeout asterisk removed. **Surface A / A5–A6 checked the same session and left
OBSERVED** — no aperture frontend test suite exists to run (the only "aperture" reference in tests is
a `category` enum value in `topologyVariant.test.ts`); upgrading it needs a frontend test to be
*written*, not run. Repo `luthiers-toolbox-clean`, branch off `main` @ `d11dc81d`.
