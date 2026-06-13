# Session Handoff — 2026-06-13 — MVP tag blocked on B-scoped CI clearing (grounded)

**Author:** prior session (Claude Opus 4.8).
**For:** the next engineer (likely fresh head — the construction below is real work).
**Governing discipline:** VERIFY AGAINST REALITY, DON'T TRUST NARRATIVE. Everything here is a
CLAIM until git/CI/execution confirms it. The board moves between sessions; **re-verify main HEAD,
open PRs, and CI at execution time before acting.**

---

## TL;DR

- **The MVP tag is decided in shape, blocked on CI.** Version `toolbox-v0.40.0` (meaning in the
  release title, NOT the number — repo convention is `toolbox-v{M}.{m}.{p}`; the repo is already at
  `toolbox-v0.39.1`, so `v0.1.0-mvp` was rejected as a regression/convention-break). Form: **GitHub
  release** (repo convention, 10+ releases). Bar: **software-readiness** (design→platform→G-code),
  with the **physical BCAM 2030CA cut named as NOT-certified** (cut is still ahead — confirmed by user).
- **The release notes are drafted** (see "Release notes draft" below). Ready to use once CI is honestly-green.
- **The blocker:** the tag commit's CI rollup is `failure`. The user chose **Option B-scoped**: fix the
  genuinely-real bounded reds, *declare baselines* for known-debt ratchets, fix/skip obviously-stale
  tests — then tag when the commit is **honestly-green** (reds declared, not failing-silently).
- **All five reds are PRE-EXISTING on parent `d656c9ee`** — the two milestone PRs (#110 docs, #111
  acoustics gate) added ZERO to any of them. The whole CAM convergence arc was built/merged on this red.

---

## STATE ON MAIN (`32bce392`)

- `32bce392` = `chore(acoustics): honestly gate AcousticsIngestEvents (#111)` — MERGED.
- `29a9f34c` = `docs(audit): correct stale 015-D claim (#110)` — MERGED.
- Acoustics view is **double-gated**: disabled UI controls (my gate) + a codeowner-added hard guard
  `const AUDIT_LOG_ENABLED = false` guarding all three fetch functions (loadEvents/loadMore/showDetail).
  No `onMounted`/`watch` auto-fire. Verified on main.
- CAM op-views all honest (re-witnessed on `32bce392`: no `setTimeout(resolve` fake-generate).
- `#110` inventory correction present (row 7: 015-D marked VERIFIED, "never executed" labeled stale).

**Held PRs / branches:** none blocking. This handoff is on `docs/session-handoff-2026-06-13-bscoped-ci-clearing`.

---

## THE FIVE REDS — GROUNDED CLASSIFICATION (read-only, done this session)

Authoritative per-commit check-runs on `32bce392`; identical failure set on parent `d656c9ee` minus
api-verify (which went fail→pending→fail). Investigated each via `gh run view <id> --log-failed`.

### 1. `build` — Jekyll / GitHub-Pages docs-site publish (ORTHOGONAL)
- **NOT app compilation.** `build-and-test` and `lint-build` both PASS. `build` is the GitHub Pages
  Jekyll publish job (run `27453114727`, job "Build with Jekyll").
- **Fatal cause:** `invalid byte sequence in UTF-8` in `docs/governance/MORPHOLOGY_FAILURE_TAXONOMY.md`
  (kramdown `RuntimeError: source text contains invalid characters for UTF-8`). Also a 2nd file flagged:
  `docs/soundhole_calculator_user_guide.md`.
- Non-fatal noise: Liquid warnings from `{{ }}` in markdown code samples (CLAUDE.md AGE-prompt JSON,
  BRIDGE_COMPENSATION_LAB, etc.) — warnings, not the failure.
- **B-scoped action (REAL, trivial, tonight-able):** re-encode/repair the invalid byte(s) in
  `MORPHOLOGY_FAILURE_TAXONOMY.md` (and check `soundhole_calculator_user_guide.md`). Find with e.g.
  `python -c "open('docs/governance/MORPHOLOGY_FAILURE_TAXONOMY.md',encoding='utf-8').read()"` → it
  raises at the bad offset; or `iconv -f utf-8 -t utf-8 //IGNORE`-style repair. One PR: `fix(docs):`.

### 2. `check-sunsets` — 2 routes overdue (REAL, bounded)
- `python -m app.ci.check_deprecation_sunset --upcoming 30` (run `27453118016`).
- **[FAIL] OVERDUE (2 routes past sunset 2026-06-01, 12 days overdue):**
  - `compat-geometry` → module `app.routers.geometry.export_router` — Action: REMOVE THIS MODULE
  - `compat-material` → module `app.routers.material_router` — Action: REMOVE THIS MODULE
- (8 other routes already successfully sunset/removed — gate works; these 2 are genuinely overdue.)
- **B-scoped action (REAL, bounded, likely fresh-head):** remove the 2 compat modules + their registry
  registration; grep for importers/route refs first; run the suite. One PR: `chore(sunset):`. CAUTION:
  these are legacy *redirect/compat* routers — confirm nothing live depends on them before deletion
  (verify-before-acting). The sunset registry entry for each must also be removed.

### 3. `file-size-check` — ratchet, pre-existing KNOWN-DEBT
- `python ci/file_size_gate.py` (run `27453118020`), baseline 500 LOC. FAIL on ~8+ pre-existing files:
  `translator_governance_continuity_graph.py` (902), `instrument_project.py` (740), `simulator.py` (705),
  `translator_execution_quarantine.py` (704), `nut_slot_cam.py` (669), `canonical_ontology_registry.py`
  (659), `export_lifecycle_orchestrator.py` (635), `bracing_router.py` (546)… **None touched by #110/#111.**
- **B-scoped action (DECLARE baseline, NOT code fix):** update the file-size baseline to the current set
  so these are *acknowledged known-debt*, not silently failing. Locate the baseline (in/near
  `ci/file_size_gate.py`). Honest-green = declared. (Refactoring these files is POST-MVP, out of scope.)

### 4. `debt-gates` — complexity ratchet, pre-existing KNOWN-DEBT
- `python -m app.ci.check_complexity --baseline app/ci/complexity_baseline.json` (run `27453118002`),
  threshold 15. VIOLATIONS (all pre-existing, none from #110/#111):
  - `app/services/blueprint_orchestrator.py:234 process_file` (82)
  - `app/util/gcode/simulator.py:368 simulate_segments` (57)
  - `app/routers/headstock/dxf_export.py:274 build_dxf` (46)
  - `app/instrument_geometry/body/ibg/workflow/topology_recovery.py:271 _fallback_topology_recovery` (41)
  - `app/instrument_geometry/body/ibg/constraint_extractor.py:154 _detect_landmarks` (38)
  - `app/cam/export_lifecycle_orchestrator.py:320 run_governed_export_lifecycle` (37)
  - `scripts/audit_wire_urls.py:208 audit` (36)
- **B-scoped action (DECLARE baseline):** update `app/ci/complexity_baseline.json` to acknowledge these.
  Honest-green = declared known-debt. (Decomposition is POST-MVP.)

### 5. `api-verify` — 60 failed / 7492 passed — the DEEP one (run `27453118047`)
Mixed bag. The fence/RunArtifact-authority checks #101 fixed are **still PASSING** ("101 current, 101
baselined, PASS") — the red is the pytest suite. Buckets:

**(a) Obviously STALE — fix or skip (tonight-able):**
  - `tests/test_saddle_compensation.py::TestCsvRoundTrip::test_cli_write_example_csv` —
    `FileNotFoundError: 'C:/Users/thepr/Downloads/luthiers-toolbox/services/api'` — **hardcoded Windows
    path running on Linux CI.** Broken test, not a code defect. Fix the path or skip-with-reason.
  - `app/tests/test_board_feet.py::test_seasonal_movement_wraps` — `assert 'maple_hard' == 'maple'` —
    this is the **known 015-E F1 species-label canonicalization** stale test (see memory
    `project_015e_verified_not_drift`). Kernel computes right; test trails an intentional label change.

**(b) DEBT-as-tests → DECLARE baseline (same known-debt family as gates 3/4):**
  - `test_technical_debt_gates.py::test_duplicate_routes_under_baseline` — dup routes 123 > baseline 108
  - `...::test_large_files_count` — large files 96 > target 63
  - `...::test_god_object_count` — god objects 15 > target 14
  - `...::test_no_unreviewed_god_objects`
  - Action: bump these baselines/targets to current (declared known-debt), consistent with gates 3/4.

**(c) TRIAGE-needed — classify real-vs-stale per test (fresh-head, the bulk):**
  - **Auth/rate-limit cluster (~9, likely ONE root cause):** `test_body_solver_integration.py` many
    `assert 401 == 200/400/404`; `test_body_export_bridge.py assert 429 == 200`. Smells like a test-env
    auth/rate-limit config regression — **investigate as a batch; one root fix may clear ~9.**
  - **IBG / body-geometry morphology (~12, IBG is experimental/BLOCKED per memory):**
    `test_body_geometry_repair.py` (straight_line_single_run 9==1, arc fitting, detect_arc 0>=1,
    repair `'6A_analysis'=='6A_validation'` label), `test_ibg_morphology_primitives.py`
    (classify_lower_bout 0.25>0.5), `test_outline_reconstructor.py` (concave_arc 41.59<0),
    `test_solve_dreadnought_returns_valid_dimensions` (0.455>0.5 — tolerance just off).
  - **Real-looking defects (verify):** `test_morphology_harvest_json_serialization.py` —
    `ImportError: cannot import name 'get_blueprint_adapter' from ...morphology_harvest.adapters`;
    `test_fretboard_ecosphere_roundtrip.py::...r2000_fret_slots_produce_grbl_gcode` —
    `AttributeError: 'dict' object has no attribute 'count'`.
  - **IBG constitutional/intake (~2):** `test_ibg_constitutional_integration.py`,
    `test_ibg_intake_gate.py` — rejection-reason enum mismatches (likely intentional-state trailing).
  - **Misc:** `test_rmos_runs_e2e.py::test_runs_index_with_filters` (3==1).
- **NOTE on orthogonality:** most of bucket (c) is IBG/body-solver/morphology — **orthogonal to the
  CAM design→G-code software-readiness claim.** Do NOT let api-verify balloon into fixing all of IBG.
  B-scoped target: fix/skip (a), baseline (b), and for (c) classify each as real-defect / stale / known-
  experimental and either fix the small real ones (the 2 import/attr errors are bounded) or skip-with-
  reason the experimental/orthogonal ones so the suite is **honestly-green (declared, not silently red).**

---

## B-SCOPED EXECUTION ORDER (suggested, one-stream-one-branch-one-PR each)

1. **`fix(docs):` UTF-8 byte** in `MORPHOLOGY_FAILURE_TAXONOMY.md` (+ check soundhole guide). Clears `build`. Trivial.
2. **`chore(baselines):` declare known-debt** — file-size baseline + `complexity_baseline.json` + the 4
   debt-as-tests baselines. Clears gates 3, 4, and api-verify bucket (b). Bounded, careful.
3. **`fix(tests):` stale api-verify** — Windows-path test + 015-E maple label (bucket a). Bounded.
4. **`chore(sunset):` remove 2 overdue compat routers** — geometry/export_router, material_router
   (+ registry entries). Clears `check-sunsets`. Verify-before-delete (grep importers/live refs).
5. **`fix:` api-verify bucket (c) triage** — the DEEP one. Batch the auth/429-401 root cause first
   (one fix may clear ~9), fix the 2 bounded real errors (import/attr), skip-with-reason the
   experimental/orthogonal IBG/morphology tests. This is the multi-session part if it goes deep.
6. **Re-run CI on the resulting HEAD; confirm honestly-green; then tag** (see below).

After each PR merges to main, **content-verify on main** (squash breaks ancestry) and **re-check the CI
rollup** — the goal state is: rollup green OR every remaining red is a *declared* baseline (not a silent fail).

---

## THE TAG (once honestly-green) — do NOT create without explicit user confirm of commit + form

- **Version:** `toolbox-v0.40.0`. **Form:** GitHub release. **Title:** "v0.40.0 — MVP Software-Readiness".
- **Re-verify at execution:** main HEAD, open PRs, CI rollup, and re-witness CAM surface + acoustics gate
  on the exact commit being tagged. Reconcile the notes to the actual commit (the acoustics gate is now
  double-guarded — notes already cover "browsing disabled, no live call").
- **Hold-the-irreversible-step:** report the exact final commit, get explicit user GO on commit + form
  BEFORE `gh release create`. A release is outward-facing / hard to fully un-publish.

### Release notes draft (cut-is-ahead variant; add a Known-Limitations line if any red is left declared)

```
# v0.40.0 — MVP Software-Readiness

This release certifies the software-readiness portion of the MVP bar: design → platform → G-code
is verified honest on main. It does NOT certify the physical cut — see "Not certified" below.

## What this release certifies
CAM operation surface — all five op-views honest:
- Drilling → live /api/cam/drilling/intent-gcode
- Pocketing → live /api/cam/pocketing/intent-gcode
- Contour → live /api/cam/profiling/intent-gcode (contour ≈ perimeter profiling)
- Surfacing → honestly gated (no surfacing toolpath lane exists)
- Fret slotting → toolpath gated; real DXF export retained
No op-view fakes the G-code step. Wire-vs-gate decided at the live mounted-route bar.

Acoustics ingest audit log — honestly gated (events backend lane unmounted); browsing disabled
(UI + hard guard), no live 404, no faked data.

API contract gate — green. CI-RED closures — verified real against main; inventory 015-D corrected.

## Not certified by this release
The physical cut on the BCAM 2030CA has not been performed. The literal MVP bar (design→platform→
G-code→cut) includes a physical cut software cannot self-certify. This release certifies the path up
to honest G-code generation and ENABLES the physical-cut milestone — it does not claim it.

## Known limitations  [ADD ONLY IF any red remains as a declared baseline]
<name the declared-baseline governance debt: file-size / complexity ratchets, etc. — pre-existing,
orthogonal to the design→G-code path, accepted as known-debt baselines.>
```

---

## Standing disciplines (carried)
- Verify by CONTENT not ancestry (squash merges). Re-verify main/PR/CI at execution time.
- Decompose a red to its cause before classifying it (build=docs-site, not compile, was the key catch).
- A ratchet gate failing on pre-existing debt is DECLARED via baseline, not "fixed" — but say so out loud.
- Stage by EXPLICIT PATH, never `git add -A` (tree carries unrelated untracked audit docs).
- One stream = one branch = one PR. PUSH before boundary; PUSH ≠ MERGE (hold for codeowner).
- Ask clarifying questions as PROSE, not the picker UI.
- Don't let api-verify balloon into fixing all of IBG — it's orthogonal; skip-with-reason is honest-green.
