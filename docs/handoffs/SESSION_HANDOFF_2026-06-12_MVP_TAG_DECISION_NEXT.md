# Session Handoff — 2026-06-12 — CAM surface CLOSED; live decision = the MVP TAG

**Author:** prior session (Claude Opus 4.8), handing off on a session reset.
**For:** the next engineer picking up cold.
**Governing discipline (proven across resets, the spine of the whole arc):**
VERIFY AGAINST REALITY, DON'T TRUST NARRATIVE. Everything below — including this doc —
is a CLAIM until git/execution confirms it. The board MOVES between sessions (the codeowner
merges PRs manually); **re-verify state at execution time before acting.** Nobody's narrative
gets a pass, including this handoff's and including the user's.

---

## TL;DR — where we are, what's next

- **The CAM surface is CLOSED on main — all five op-views are honest.** This was the session's
  central problem (four CAM lanes narrated-complete-and-mostly-phantom) and it's closed *on
  execution*, not on anyone's word. No view fakes the G-code step anymore.
- **The contract gate is green, the CI-RED closures are verified-real, the governance docs are
  structure-not-blockers.** The "narrated-complete-but-phantom" debt that blocked an honest tag
  has been ground to verified reality across the surfaces that matter.
- **The LIVE DECISION when the reset hit = whether/how to TAG the MVP.** Three questions are on
  the table for the user (below). Two things sit between here and a no-asterisk tag: (1) the
  literal MVP bar includes a *physical cut* software can't self-certify; (2) the acoustics view
  currently 404s on main — the last hidden defect, a likely tag-prerequisite gate.

---

## STEP 0 — shell gate (first; hard stop)
`echo ok` ; `git --version; echo "exit=$?"` — confirm clean output + `exit=0` (bash `$?`, NOT
`$LASTEXITCODE`). If not clean, STOP.

## STEP 1 — load durable state + RE-GROUND (the board moves)
1. Read memory pointers (recalled into context): `project_mvp_backlog_inventory`,
   `project_cam_pocketing_frontend_wired`, `project_governance_grounding_sweep`,
   `project_api_contract_classification`, `feedback_verify_before_acting`,
   `feedback_push_before_session_boundary`, `feedback_narrative_questions`.
2. **Re-verify main HEAD + open PRs** (`git fetch`; `git log --oneline -8 origin/main`;
   `gh pr list --state open`). At handoff time: **origin/main = `d656c9ee`** (#108), **one open
   PR = #110** (held). If these moved, reconcile by CONTENT before trusting any state below.
3. Confirm the CAM surface by CONTENT on origin/main (not ancestry — squash merges break it):
   each `views/cam/*.vue` either calls a real `generate*Gcode` or is honestly gated; **none**
   contain `setTimeout(resolve` as a fake generate path.

---

## VERIFIED STATE ON MAIN (`d656c9ee`) — what's actually done

### CAM op-views — all five honest (the closed surface)
- **DrillingView** — wired to real 8I `/api/cam/drilling/intent-gcode` (#100 `0625dfb4`). Tapping honest-gated.
- **PocketClearingView** — wired to real 8J `/api/cam/pocketing/intent-gcode` (#101 `70b13d89`). The #101
  merge ALSO carried a real fence fix: all 4 CAM intent routers (drilling/pocketing/profiling/vcarve) had
  direct `RunArtifact()` → swapped to `validate_and_persist()` (artifact_authority fence). Behavior-preserving
  (re-witnessed). 4 honest-gates (DXF/strategies/spindle/stepover-clamp).
- **ContourCuttingView** — wired to real 8H **profiling** `/api/cam/profiling/intent-gcode` (contour ≈
  perimeter-profiling; no separate contour lane). History: #107 merged → REVERTED (`18b995a4`) → re-done by
  codeowner as **#108 `d656c9ee` with 20 robustness fixes**. **Re-witnessed post-fix on merged main (PASS):**
  200 flat-gcode (7 passes/4 tabs), 409 FEASIBILITY_BLOCKED (`tab_height_mm must be < cut_depth_mm`). 4
  honest-gates (DXF/on-line-cut/tangent-lead-in/spindle). Client = `packages/client/src/api/profiling.ts`.
- **SurfacingView** — honestly GATED (#105 `22867166`). True void: no facing/surfacing lane exists (only
  machine Z-probing, a different op). Generate/download disabled "coming soon".
- **FretSlottingView** — toolpath button GATED, real DXF export KEPT (#106 `4686307d`). The DXF path
  (`useFretboardEcosphere` → `/api/v1/fretboard/dxf`) is real; only the gcode "Generate Toolpath" was a fake.

**Wire-vs-gate was decided at the LIVE-ROUTE-TABLE bar** (boot uvicorn, enumerate mounted routes): the only
4 mounted CAM intent lanes are drilling/pocketing/profiling/vcarve. No contour/surfacing/fretslotting lane —
so Contour borrows profiling, Surfacing+FretSlotting gate. Don't trust view docstrings (they name
`preview/generate` endpoints that were never built); check the mounted table.

### Contract gate (api_contract_check) — green, honestly
- 13 verified-real routes added to `contracts/api_endpoints.json` (#102 `69e9ec59`) — AI-assistant/vectorizer/
  cam-workspace-neck/ltb. All confirmed mounted at the live-route bar (NOT file-grep — the validator never
  consults the backend, `BACKEND_DIR` defined-but-unused, so it can bless voids).
- Dead `IngestEventsView.vue` deleted (#104 `ecc1f4d7`) — an orphan view (not routed) whose inline calls were
  the last 3 NEW violations. Gate went green by REMOVING a phantom, not certifying one.
- Gate-quality blind-spot recorded in the inventory (#103 `453a8acb`).
- **Validator NEW violations: 0 on main.** Caveat: the baseline grandfathers pre-existing calls (incl.
  `/api/v1/dxf/cam/gcode`) — a deferred audit item.

### Governance grounding sweep (2026-06-12) — done, ground-first
- **CI-RED closures are TRUSTWORTHY.** Spot-checked 5 closed entries vs main, ALL hold: 015-D (artifact
  `services/api/metrics/live_routes.json` exists, ~200KB — the inventory's "never executed" was STALE/FALSE),
  002 (mis-scoping fix), 008/006/014 (fix-artifacts present). The full ~14-entry re-verify is UNNECESSARY.
  **Source of truth = `SPRINTS.md` ledger, NOT the inventory's characterization** (which carried the stale
  015-D claim). Correction is in **PR #110 (HELD)**.
- **The "paused sandboxes / convergence" frame = dormancy, NOT blocked streams.** User clarified: solo
  operator, no active dev in those domains; work happens as PR-level fixes with AI engineers (the engine that
  closed CAM). The C2 namespace-arbitration apparatus is real ongoing structure (C2-A ratified → C2-B draft,
  semantic collision log) but NOT urgent — nothing is paused-at-a-blocker. Record-and-deprioritize; advance
  when chosen. See `project_governance_grounding_sweep`.

---

## OPEN / HELD — what's not done

- **PR #110** (inventory CI-RED correction) — HELD for codeowner merge. Pure docs; corrects the stale 015-D
  line + marks closures VERIFIED. Low-risk; merge whenever.
- **THE MVP TAG — the live decision.** Three questions for the user (posed, unanswered when reset hit):
  1. **Which bar does the tag mean?** The literal MVP bar (SPRINTS.md:53) = *"design → platform → G-code →
     cut on BCAM 2030CA"* — it includes a **physical cut** no code can self-certify. So: (a) a
     **software-readiness** tag (design→platform→G-code honest, physical cut a separate milestone), or (b)
     gated on the **physical cut having happened**? And: has a part been cut on the BCAM 2030CA yet?
  2. **Is the acoustics 404 a tag blocker?** The routed `AcousticsIngestEvents.vue` calls `/ingest/events`
     (slash) against a backend that's unmounted / on a different path (`/ingest-events` hyphen) → 404. It's
     the last hidden user-facing defect (everything else is honestly-gated or working). **Prior session's
     lean: gate it honestly BEFORE tagging** (cheap PR, the proven pattern) so the surface has zero hidden
     defects. See the full acoustics analysis in `project_api_contract_classification` (the double-fake: a
     dead view AND a live view that diverges from the unmounted backend on path + response-shape).
  3. **Tag mechanics (if go):** version/name (e.g. `v0.1.0-mvp`?), annotated tag on which commit, and **just
     a git tag or a GitHub release**? Outward-facing + hard to reverse → confirm exact form + commit BEFORE
     creating anything. Do NOT tag/release without explicit user confirmation of form.

- **Acoustics scope** (the bigger version of #2 above) — build-or-gate the acoustics-ingest feature. It is NOT
  currently working (live view reaches the backend on neither path nor response-shape; backend
  `router_ingest_audit.py` is good code but UNMOUNTED). If MVP-scope: mount the router + reconcile the live
  view↔backend onto one path + one response contract, then contract. If not: gate the view, defer past tag.
  Likely defer-and-gate (it's an audit-log viewer, peripheral to design→G-code→cut).
- **Client-side fixes #3/#13 (Contour)** — response-validation + `blocked.issues` coercion live in the `.vue`;
  the backend re-witness confirmed their INPUTS are intact but not their own logic. Witnessed-by-inputs, not
  by-execution. Low-risk; fold a frontend run / client unit-test into the next touch of that view.

---

## Prior session's RECOMMENDATION on the tag (for context, not a mandate)
Gate acoustics first (closes the last honest gap, cheap), then tag against the **software-readiness bar (a)**
— because that's the bar the software can actually certify; the physical BCAM cut is a real-world milestone the
tag can *enable* rather than *claim*. The physical-cut-or-not and the version/release form are the user's calls.

---

## Standing disciplines (carried; apply throughout)
- **Verify by CONTENT, not ancestry** (squash merges break `--is-ancestor` / `git branch -d`).
- **Re-verify PR/main state at execution time** — the board moves between sessions (codeowner merges manually;
  #101 was thought "held" but had merged; #108 superseded #107 via revert+redo; #103/#110 moved).
- **Live-route-table bar** for "does a backend lane exist" — boot uvicorn, enumerate mounted routes; file-grep
  says "code exists," only the mounted table says "reachable" (caught the acoustics unmounted-router void).
- **Decompose a numeric delta to its cause** — a real regression moves geometry-driven values; an input
  difference moves only what the input changed (the +70mm contour length was `retract_z_mm`, not drift).
- **PUSH before session boundary** (this doc is that discipline applied to context); **PUSH ≠ MERGE** — push
  for durability, hold the merge for the codeowner.
- **Stage by EXPLICIT PATH, never `git add -A`** — the tree always carries 6 long-standing untracked audit
  docs (inventory item #10); leave them alone.
- **One stream = one branch = one PR.**
- **Ask clarifying questions as PROSE, not the picker UI** (`feedback_narrative_questions`).
- **Witness backends live before declaring a wire real** — uvicorn recipe:
  `cd services/api; PYTHONPATH=".;tests" ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8077 --log-level warning`
  (`/openapi.json` 500s on an unrelated `solve_from_dxf` Pydantic bug — that does NOT mean the server is down;
  POST the operation endpoint directly.)

---

## The shape of where this landed
Opened with four CAM lanes narrated-complete-and-mostly-phantom. Closes with the CAM surface honest on main,
the contract gate green by removing a phantom (not blessing one), the CI-RED closures verified-real, the
governance frame corrected from "paused streams" to "dormant domains," and one clean decision left: tag the
MVP — against the bar the software can honestly certify, after gating the one remaining 404. That's the whole
arc's difference: not "done" on someone's word, but verified reality on execution.
