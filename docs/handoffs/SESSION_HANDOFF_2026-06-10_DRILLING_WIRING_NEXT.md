# Session Handoff — 2026-06-10 — Drilling/Pocketing Frontend Wiring is NEXT

**Author:** prior session (Claude Opus 4.8), stopping on a clean boundary ahead of a system reset.
**For:** the next engineer picking up cold.
**Governing discipline (proven across the last reset):** VERIFY AGAINST REALITY, DON'T TRUST NARRATIVE.
Everything below — including this doc — is a CLAIM until git/execution confirms it. Re-ground before acting.

---

## TL;DR — where we stopped and what's next

- **015-E is verified DONE — it is NOT calc drift.** It is OFF the MVP-blocking list. (Detail below.)
- **The sole remaining clear MVP blocker is the CAM operation FRONTEND WIRING.** The op-view UIs run
  `setTimeout` fakes with no API call; the real backends (8I drilling / 8J pocketing) are merged on main
  but the UIs never call them.
- **Next action = a net-new, user-facing BUILD: wire `DrillingView` → `/api/cam/drilling/intent-gcode`.**
  This was deliberately banked for a fresh head (highest-stakes build on the board). Nothing is in flight;
  tree is clean on `main`.

---

## STEP 0 — shell gate (first; hard stop)
`echo ok` ; `git --version; echo "exit=$?"` — confirm clean output + `exit=0` (bash `$?`, NOT
`$LASTEXITCODE`). If it doesn't return clean, STOP — don't run a mutation through an unverified shell.

## STEP 1 — load durable state (it survives resets; reconstruct nothing)
1. Read the memory pointers: `project_mvp_backlog_inventory`, **`project_015e_verified_not_drift`** (new),
   `project_cam_8i_drilling_dev_order`, `feedback_push_before_session_boundary`.
2. Read on main: `docs/audit/BACKLOG_INVENTORY_2026-06-09.md` (authoritative worklist) and THIS doc.
3. Confirm repo on `main`, synced with `origin/main`, clean tree. Note HEAD SHA.

## STEP 2 — re-verify the load-bearing claims (read-only; 2nd-pass every search — this repo under-reports)
- **015-E** — re-run the targeted suites (see exact command below); confirm the only reds are the two
  stale-test failures classified here, not new numeric drift.
- **Frontend fakes still present?** `DrillingView.vue` / `PocketClearingView.vue` still `setTimeout`,
  no fetch, docstrings still name the OLD `preview/generate` (not `intent-gcode`).
- **Backends still on main?** `POST /api/cam/drilling/intent-gcode` + `…/pocketing/intent-gcode` present
  (verify by route/content presence, NOT `--is-ancestor` — squash merges break ancestry checks).
- **Anything in flight from the reset?** `git reflog`, `git fsck --no-reflogs`, `git stash list`,
  `git branch -a` — preserve any uncommitted/dangling work FIRST if found.

---

## 015-E verification result (2026-06-10) — NOT calc drift

Run, read-only, repo `.venv` (Python 3.13.7 / numpy 2.2.6 = CI parity):
```
cd services/api
PYTHONPATH=".;tests" "<repo>/.venv/Scripts/python.exe" -m pytest -q \
  app/tests/test_board_feet.py \
  tests/test_fretboard_ecosphere.py \
  tests/test_fretboard_router.py \
  app/tests/integration/test_fretboard_ecosphere_roundtrip.py
```
Result: **2 failed, 55 passed, 1 skipped.** Both reds are contract/shape regressions where the TEST is
stale — neither is a wrong number:

- **F1** `test_seasonal_movement_wraps` — `assert 'maple_hard' == 'maple'`. Test checks only the species
  *label* echo (no numeric assertion). `seasonal_movement`→`compute_wood_movement` now canonicalizes
  `"maple"`→`"maple_hard"`. Stale test trailing an intentional species-key canonicalization. **Fix:**
  assert the canonical key / membership. NOT blocking.
- **F2** `test_r2000_fret_slots_produce_grbl_gcode` — `AttributeError: 'dict' object has no attribute
  'count'`. `/api/rmos/wrap/mvp/dxf-to-grbl` **intentionally** returns `gcode: {inline, text}` on success
  (`app/rmos/mvp_router.py:192-213`; `None` on empty/error). Confirmed the **intended contract**, not a
  regression (endpoint returned 200 with real G-code). Test predates the envelope (assumes flat string).
  **Fix:** read `gcode["text"]`. NOT blocking.

**Spot-check (green-but-wrong guard):** `board_feet(1,6,96,1)==4.0` = (1·6·96)/144 exactly — passing tests
expect the *right* numbers, no pinned-drift. Kernels compute correctly.

**Disposition:** F1 + F2 are logged NON-blocking residuals. Park; fold each fix into the next build
touching that surface (F2 → the drilling/G-code wiring; F1 → next board_feet touch). Do NOT touch the kernels.

---

## NEXT BUILD — wire DrillingView to the real 8I lane (the MVP blocker)

**This is net-new, user-facing construction. Give it the full treatment.**

**The fake to replace:** `packages/client/src/views/cam/DrillingView.vue` — `generateToolpath()` (~line 37)
does `await new Promise(r => setTimeout(r, 500))`, no API call. Header docstring names stale
`/api/cam/drilling/{preview,generate}` — IGNORE those; they are not the real lane.

**Ground against the REAL merged 8I contract** — `services/api/app/cam/routers/drilling/intent_router.py`:
- **Endpoint:** `POST /api/cam/drilling/intent-gcode`
- **Request body:** `CamIntentV1` (JSON) — `app/rmos/cam/schemas_intent.py`. Must normalize to
  `mode = router_3axis`; `design` validated against `DrillingDesignV1`; optional `tool_id`.
- **200 → `DrillingIntentResponse`:**
  - `gcode: str` — **a FLAT STRING here** (contrast: the MVP wrapper returns `{inline,text}`. The two
    G-code surfaces have DIFFERENT shapes — do NOT assume F2's envelope. Read `response.gcode` directly.)
  - `issues: [{code, message, path}]` — soft warnings, render them.
  - `run_id: str`, `hashes: {request_sha256, feasibility_sha256, gcode_sha256}`
  - `metadata: {hole_count, total_depth_mm, estimated_time_seconds, risk_level}`
- **Error paths the UI MUST handle (not just the 200):**
  - **409 `FEASIBILITY_BLOCKED`** — the **peck-block** path. `detail: {error, message, run_id,
    feasibility:{...}}`. A wiring that ignores the 409 is a thinner version of the same fake — surface the
    block reason + feasibility to the user.
  - 422 `NORMALIZATION_ERROR` / `INVALID_MODE` / `INVALID_DESIGN` / `ADAPTER_ERROR` — bad input.
  - 400 `TOOLPATH_GENERATION_ERROR` — generation failure (carries `run_id`).

**Witness against the live backend** (don't trust the wiring on assertion alone): run the API, POST a
valid `CamIntentV1`, see a real 200 with G-code; POST an infeasible one, see the 409 render. **Push the
instant it verifies** — a reset is the exact condition that loses unpushed work (this session's #1 lesson).

**Then:** `PocketClearingView` → `/api/cam/pocketing/intent-gcode` (same pattern, ground its own contract).
Decide wire-vs-gate for `ContourCuttingView` / `SurfacingView` / `FretSlottingView` (item 1 of the inventory).

---

## Standing disciplines (carried; apply throughout)
- Verify by CONTENT, not ancestry (squash merges break `--is-ancestor` / `git branch -d`; use `-D` only
  after content-verifying the merge landed).
- PUSH the moment work is built+verified — unpushed work through a session boundary evaporates.
- Search the object store (reflog + log --all + fsck + orphaned `.pyc`) before building OR concluding lost.
- Reconcile every search with a 2nd pass before recording "found N" / "found nothing."
- Stage by EXPLICIT PATH, never `git add -A` (tree carries mixed untracked streams).
- One stream = one branch = one PR. Hold mutations at push for the codeowner; escalate interpretation calls.

## Reset-survival note
Durable surfaces that survive a reset: the memory store (auto-loads) and `main` (+ pushed branches). This
doc and the new memory `project_015e_verified_not_drift` are both written for that reason. If Step 1 comes
back thinner than this doc implies, that itself is a finding (the reset was deeper than a terminal restart)
— the verify-against-main steps still hold, because main is ground truth regardless.
