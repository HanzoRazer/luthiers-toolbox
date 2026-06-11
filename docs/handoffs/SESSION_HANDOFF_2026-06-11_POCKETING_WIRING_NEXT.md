# Session Handoff — 2026-06-11 — Pocketing Frontend Wiring is NEXT (a copy-job)

**Author:** prior session (Claude Opus 4.8), stopping on a clean boundary.
**For:** the next engineer picking up cold.
**Governing discipline (proven across resets):** VERIFY AGAINST REALITY, DON'T TRUST NARRATIVE.
Everything below — including this doc — is a CLAIM until git/execution confirms it. Re-ground before acting.
Predecessor that set up *this* session: `SESSION_HANDOFF_2026-06-10_DRILLING_WIRING_NEXT.md`
(branch `docs/session-handoff-2026-06-10-drilling-wiring`, commit `a1e2b1e4`).

---

## TL;DR — where we stopped and what's next

- **Drilling frontend wiring is DONE and witnessed — but HELD AT MERGE in PR #100.**
  On `main`, `DrillingView` is **still the `setTimeout` fake** until #100 lands. Do not treat
  drilling-on-main as real until you confirm #100 is merged (see STEP 1).
- **The drilling wire established the convention.** `packages/client/src/api/drilling.ts` is the
  per-lane CamIntent client pattern. The hard part — inventing the client convention, proving the
  CamIntentV1 field mapping, confirming the live 200/409 contract — is **done**.
- **NEXT = wire `PocketClearingView` → `/api/cam/pocketing/intent-gcode`. This is now a COPY-JOB,**
  not a from-scratch build. Replicate the proven drilling pattern against the pocketing contract.
  Lower-stakes than drilling was, because the precedent now exists.

---

## STEP 0 — shell gate (first; hard stop)
`echo ok` ; `git --version; echo "exit=$?"` — confirm clean output + `exit=0` (bash `$?`, NOT
`$LASTEXITCODE`). If not clean, STOP — don't run a mutation through an unverified shell.

## STEP 1 — load durable state + reconcile PR #100 (it gates everything)
1. Read memory pointers: `project_mvp_backlog_inventory`, `project_cam_drilling_frontend_wired`
   (new, points here), `project_015e_verified_not_drift`, `feedback_push_before_session_boundary`.
2. **Reconcile PR #100 state — this is load-bearing:** `gh pr view 100`.
   - If **MERGED** → drilling UI is real on main; proceed to pocketing on a main that has drilling wired.
   - If **OPEN/held** → drilling on main is **still the fake**. Either land #100 first (codeowner's call),
     or build pocketing knowing drilling-on-main is not yet wired. Do NOT assume drilling is live on main.
   - Verify by CONTENT: `DrillingView.vue` on main calls `generateDrillingGcode` (real) vs `setTimeout` (fake).
3. Confirm repo on `main`, synced with `origin/main`, clean tree. Note HEAD SHA.

## STEP 2 — re-verify the load-bearing claims (read-only; 2nd-pass every search — this repo under-reports)
- **Pocketing fake still present?** `packages/client/src/views/cam/PocketClearingView.vue` still
  `setTimeout(1000)` (~line 51), no fetch.
- **Pocketing backend on main?** `POST /api/cam/pocketing/intent-gcode` present
  (`services/api/app/cam/routers/pocketing/intent_router.py`). Verify by route/content, NOT `--is-ancestor`
  (squash merges break ancestry checks).
- **Ground the pocketing contract before mapping** — read its request schema + adapter the way the
  drilling wire grounded `DrillingDesignV1`/`intent_adapter.py` first. The two genuine gaps that bit
  drilling (no wired precedent; an unrepresented UI option) are now *partly* retired — the precedent
  exists — but pocketing may have its own design↔context split and its own UI options the backend
  doesn't model. Find that gap BEFORE writing code, not mid-build.

---

## NEXT BUILD — wire PocketClearingView (the copy-job)

**Replicate the drilling pattern. The reference implementation is on `main` (once #100 lands) or on
branch `feat/cam-8i-drilling-frontend-wiring`:**

- **Client:** create `packages/client/src/api/pocketing.ts` mirroring `src/api/drilling.ts` —
  typed `CamIntentV1` request envelope, typed response, a `*IntentError` that **preserves the structured
  FastAPI `detail`** (use raw `fetch`, NOT the shared `fetchJson` — `fetchJson` collapses the error body
  to a generic string and would discard the 409 feasibility detail the UI needs).
- **View:** map `PocketClearingView`'s form to the pocketing contract (its own design = the "what",
  context = feeds/speeds "how", `mode` per its schema). Handle **every** branch: 200 (render result +
  soft `issues`, enable download), **409 FEASIBILITY_BLOCKED** (surface the real block reason — do NOT
  fake through it; this is the whole point of the MVP fix), 422/400 (validation/generation errors).
- **Honest gating:** if PocketClearingView exposes any option the backend can't serve, disable it with
  a "coming soon" affordance — never fake a path the engine can't serve (drilling did this for `tapping`).

**Drilling field mapping, as the worked example to copy the SHAPE of (pocketing's fields differ — ground
its own schema):**
- envelope: `{ mode: "router_3axis", units: "mm", tool_id, design, context }`
- design (the "what"): holes / hole_depth_mm / hole_diameter_mm / peck_drilling / peck_depth_mm
- context (the "how"): feed_rate_mm_min / spindle_rpm / retract_height_mm
- 200 → flat `gcode: str` + `issues[]` + `run_id` + `hashes` + `metadata{hole_count,total_depth_mm,...}`
- 409 → `detail.error="FEASIBILITY_BLOCKED"`, `detail.feasibility{issues[],risk_level,...}`, `detail.run_id`

**Witness against the live backend** (don't trust the wire on assertion alone — the bug class is "UI
doesn't actually call the backend," which only a real request disproves). Spin up uvicorn:
```
cd services/api
PYTHONPATH=".;tests" ../../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8077 --log-level warning
```
NOTE: `/openapi.json` 500s on an unrelated `solve_from_dxf` Pydantic schema bug — that does NOT mean the
server is down. POST the operation endpoint directly. POST a valid pocketing intent → real 200; POST an
infeasible one → real 409 rendered in the UI. **Push the instant it verifies.**

---

## After pocketing — the remaining MVP-frontend work (then the tag is close)
1. **Wire-vs-gate triage** for the other three op views: `ContourCuttingView`, `SurfacingView`,
   `FretSlottingView` (inventory item 1, `docs/audit/BACKLOG_INVENTORY_2026-06-09.md`). For each: is there
   a real CamIntent backend lane to wire to, or should it be honestly gated "coming soon" until one exists?
2. **Two parked, NON-blocking 015-E residuals** (fold each into the next build touching its surface):
   - **F1** `test_seasonal_movement_wraps` — assert canonical key (`maple`→`maple_hard`), not the bare label.
   - **F2** `test_r2000_fret_slots_produce_grbl_gcode` — read `gcode["text"]`; this is the **MVP-wrapper**
     endpoint `/api/rmos/wrap/mvp/dxf-to-grbl` which returns `{inline,text}`. NOTE confirmed live this
     session: the **drilling/op intent endpoints return a FLAT `gcode: str`** — F2's dict-shape is a
     DIFFERENT surface. Do not assume the envelope on the op endpoints.

---

## What shipped this session (drilling wiring) — for reference when copying
- Branch `feat/cam-8i-drilling-frontend-wiring`, PR #100 (HELD at merge for codeowner).
- `packages/client/src/api/drilling.ts` (new) — the convention to copy.
- `packages/client/src/views/cam/DrillingView.vue` — fake replaced; tapping disabled-honest.
- Live witness: valid → 200 flat-string G83 cycle; infeasible peck (`peck_depth ≥ hole_depth`) → 409
  with feasibility issues rendered. `vue-tsc` clean for both files (repo has pre-existing unrelated TS errors).

## Standing disciplines (carried; apply throughout)
- Verify by CONTENT, not ancestry (squash merges break `--is-ancestor` / `git branch -d`).
- PUSH the moment work is built+verified — unpushed work through a session boundary evaporates.
  (This bookmark is itself that discipline applied to CONTEXT — pushed so the next cold start finds it.)
- PUSH ≠ MERGE. Push for durability; hold the merge for the codeowner. PR #100 is exactly this posture.
- A pointer must describe what's ACTUALLY on main — don't claim drilling is live when it's held in a PR.
- Stage by EXPLICIT PATH, never `git add -A` (tree carries mixed untracked streams).
- One stream = one branch = one PR. This doc is its own docs stream/branch, separate from #100's code.
- Ground the contract (schema + adapter) BEFORE mapping — the real decisions hide in the field mapping.
