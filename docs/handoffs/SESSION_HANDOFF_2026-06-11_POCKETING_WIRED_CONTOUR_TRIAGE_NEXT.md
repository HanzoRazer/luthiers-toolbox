# Session Handoff — 2026-06-11 — Pocketing WIRED (held in #101); next = Contour/Surfacing/FretSlotting wire-vs-gate

**Author:** prior session (Claude Opus 4.8), stopping on a clean boundary.
**For:** the next engineer picking up cold.
**Governing discipline (proven across resets):** VERIFY AGAINST REALITY, DON'T TRUST NARRATIVE.
Everything below — including this doc — is a CLAIM until git/execution confirms it. Re-ground before acting.
Predecessor that set up *this* session: `SESSION_HANDOFF_2026-06-11_POCKETING_WIRING_NEXT.md`
(branch `docs/session-handoff-2026-06-11-pocketing-next`).

---

## TL;DR — where we stopped and what's next

- **Drilling (8I) is MERGED on main.** PR #100 squash-merged as `0625dfb4` (content-verified on main:
  `src/api/drilling.ts` present, `DrillingView` calls `generateDrillingGcode`, no `setTimeout`). Merged
  branch deleted (local + remote). The held-fake state is RESOLVED for drilling.
- **Pocketing (8J) is WIRED and witnessed — HELD AT MERGE in PR #101.** Branch
  `feat/cam-8j-pocketing-frontend-wiring`, commit `4a6e73f2`. On `main`, `PocketClearingView` is **still
  the `setTimeout(1000)` fake** until #101 lands. Do not treat pocketing-on-main as real until #101 merges.
- **NEXT = wire-vs-gate triage for the remaining three op views:** `ContourCuttingView`, `SurfacingView`,
  `FretSlottingView` (inventory item 1, `docs/audit/BACKLOG_INVENTORY_2026-06-09.md`). For each: does a real
  CamIntent backend lane exist to wire to (copy the drilling/pocketing pattern), or should it be honestly
  gated "coming soon" until a lane exists? This is the last frontend slice before the MVP tag is close.

---

## STEP 0 — shell gate (first; hard stop)
`echo ok` ; `git --version; echo "exit=$?"` — confirm clean output + `exit=0` (bash `$?`, NOT
`$LASTEXITCODE`). If not clean, STOP.

## STEP 1 — load durable state + reconcile PR #101 (it gates pocketing-on-main)
1. Read memory pointers: `project_mvp_backlog_inventory`, `project_cam_pocketing_frontend_wired` (new,
   points here), `project_cam_drilling_frontend_wired` (now says MERGED), `project_015e_verified_not_drift`,
   `feedback_push_before_session_boundary`.
2. **Reconcile PR #101:** `gh pr view 101`.
   - If **MERGED** → pocketing UI is real on main; verify by CONTENT (`PocketClearingView` imports
     `generatePocketingGcode` vs `setTimeout`), sync main, delete the merged branch (`-D`, licensed by the
     content verify), and flip `project_cam_pocketing_frontend_wired` + this doc's pointer to "merged."
   - If **OPEN/held** → pocketing on main is **still the fake**. Either land #101 first (codeowner's call),
     or proceed knowing pocketing-on-main is not yet wired. Do NOT assume it's live.
3. Confirm repo on `main`, synced with `origin/main`, clean tree. Note HEAD SHA.

## STEP 2 — the wire-vs-gate triage (the actual next work; read-only first)
For EACH of `ContourCuttingView`, `SurfacingView`, `FretSlottingView`
(`packages/client/src/views/cam/`):
1. **Is it still a fake?** Grep for `setTimeout` / absence of a real `fetch` (this repo under-reports —
   second-pass every search).
2. **Does a real CamIntent lane exist?** Look for `services/api/app/cam/routers/<op>/intent_router.py`
   exposing `POST /api/cam/<op>/intent-gcode` that takes `CamIntentV1`. Verify by route/content, NOT
   `--is-ancestor` (squash merges break ancestry). Note: the CamIntent bridge (8G+8H+8I+8J) is CLOSED —
   profile/drilling/pocketing/v-carve — so a *given* op view may or may not have a matching lane. Contour
   ≈ profile (a lane likely exists); surfacing / fret-slotting may NOT have an intent lane yet.
3. **Decide per view:**
   - **Lane exists → WIRE it** as a copy-job. The pattern is now doubly-proven (drilling + pocketing).
     Create `src/api/<op>.ts` mirroring `drilling.ts`/`pocketing.ts` (raw fetch, preserve 409 `detail`),
     map the view's form to the lane's *own* grounded `<Op>DesignV1` (do NOT assume drilling/pocketing
     fields), handle 200/409/422/400, honest-gate any unservable UI option, live-witness both paths, push.
   - **No lane → GATE it** honestly: disable the generate action with a "coming soon" affordance that names
     why (no backend lane yet). Do not leave a `setTimeout` fake that implies a working backend. This is a
     small, honest docs-grade change — still its own branch/PR.

---

## How pocketing was wired (the worked example to copy — pattern is proven twice now)

- Branch `feat/cam-8j-pocketing-frontend-wiring`, PR #101 (HELD at merge).
- **`packages/client/src/api/pocketing.ts`** (new) — typed CamIntentV1 client for the pocketing lane;
  raw `fetch` (NOT `fetchJson`) to preserve the structured 409 `detail`. Mirrors `drilling.ts`.
- **`PocketClearingView.vue`** — fake replaced. KEY DECISION (matches drilling's): the intent endpoint
  takes an **explicit boundary polygon + islands**, NOT a DXF/SVG file, so the UI enters geometry directly
  (boundary point editor + optional islands), exactly as `DrillingView` enters `holes[]`. The DXF-upload
  premise the old fake implied does not map to this lane.
- **Honest gates (pocketing analogs of drilling's tapping):** DXF/SVG import (lane takes explicit boundary);
  Adaptive/Offset strategies (adapter serves only `strategy ∈ {Spiral, Lanes}`); Spindle speed (pocketing
  `context` has no spindle field — engine emits a fixed `S18000`); Stepover clamped to the engine's 30–70%.
- **Grounded contract** (read these before any contour/surfacing mapping, as the shape to ground against):
  `services/api/app/cam/pocketing/intent_schema.py` (`PocketDesignV1`), `intent_adapter.py`
  (`pocket_params_from_intent` — design→engine; stepover% → fraction; strategy allow-list),
  `feasibility.py` (what trips a 409: invalid/island-outside-boundary/out-of-bounds params),
  `routers/pocketing/intent_router.py` (200/409/422/400/503 shapes).
- **Live witness (uvicorn :8077):** valid 100×60 pocket → **200** flat-string G-code (4 passes,
  `pocket_area_mm2=6000`); island outside boundary → **409 FEASIBILITY_BLOCKED**,
  `issues=['island 0 extends outside boundary']` rendered; tool-too-large → **400
  TOOLPATH_GENERATION_ERROR**. `vue-tsc --noEmit` clean for both files (repo has pre-existing unrelated TS).

### Witness recipe (reused, works)
```
cd services/api
PYTHONPATH=".;tests" ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8077 --log-level warning
```
`/openapi.json` 500s on an unrelated `solve_from_dxf` Pydantic bug — that does NOT mean the server is down;
POST the operation endpoint directly. A clean **409** trigger for a pocketing-style lane: a geometrically
valid input that fails a feasibility *rule* (island outside boundary), NOT a degenerate one that dies in
generation (tool-too-large gives a 400, a different path). Pick the input that exercises the gate you want
to witness.

---

## Two parked, NON-blocking 015-E residuals (fold each into the next build touching its surface)
- **F1** `test_seasonal_movement_wraps` — assert canonical key (`maple`→`maple_hard`), not the bare label.
- **F2** `test_r2000_fret_slots_produce_grbl_gcode` — read `gcode["text"]`; that's the **MVP-wrapper**
  endpoint `/api/rmos/wrap/mvp/dxf-to-grbl` returning `{inline,text}`. NOTE (re-confirmed this session): the
  **op intent endpoints return a FLAT `gcode: str`** — drilling AND pocketing both do. F2's dict-shape is a
  DIFFERENT surface (the wrapper). Do not assume the envelope on the op endpoints. (Relevant when you reach
  `FretSlottingView` — check whether it should target an intent lane or the MVP wrapper.)

## Standing disciplines (carried; apply throughout)
- Verify by CONTENT, not ancestry (squash merges break `--is-ancestor` / `git branch -d`).
- PUSH the moment work is built+verified — unpushed work through a session boundary evaporates.
- PUSH ≠ MERGE. Push for durability; hold the merge for the codeowner. PRs #100/#101 are this posture.
- A pointer must describe what's ACTUALLY on main — don't claim pocketing is live while it's held in #101.
- Stage by EXPLICIT PATH, never `git add -A` (tree carries mixed untracked streams: several stale audit
  docs sit untracked at all times — leave them alone).
- One stream = one branch = one PR. This doc is its own docs stream/branch, separate from #101's code.
- Ground the contract (schema + adapter + feasibility) BEFORE mapping — the real decisions hide there.
- The geometry-source question recurs: intent lanes take EXPLICIT geometry, the old fakes implied file
  upload. Resolve it the way drilling/pocketing did (explicit entry; gate the file path) unless the lane
  actually accepts a file.
