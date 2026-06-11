# Backlog Inventory — Path to MVP Tag/Release

**Date:** 2026-06-09
**Scope:** Read-only discovery + triage of the outstanding-issue stockpile, grounded in
executable/observed reality (markers are claims until verified). **One output doc; no fixes.**
**Coverage:** MVP-BLOCKING + DECISION-READY buckets inventoried completely. Deeper independent
re-verification of *closed* CI-RED entries and the 015-E kernel drift is **partial — not re-run this
pass** (heavy suites; flagged below).

---

## STEP 0 — shell gate + reliability

| Probe | Result |
|---|---|
| `echo ok` | `ok` |
| `git --version; echo "exit=$?"` | `git version 2.53.0.windows.2` / `exit=0` |
| repo / branch | `luthiers-toolbox` / `main` |
| HEAD / sync | `49577046`; `main...origin/main` = **0 0** (synced) |
| tracked tree | clean (`porcelain-exit=0`) |

**PASS.** Search-reliability honored: every count below was reconciled with a 2nd pass (Grep tool vs
bash grep, or different query). Two single-pass false-negatives were caught and corrected during this
audit — the debt-marker count (3→13) and a malformed `grep -rI--include` (0→real). Recorded as
evidence that single passes under-report here.

---

## Master table

| # | Item | Source | Confidence | Disposition | MVP | Evidence | Unblocks/resolves |
|---|---|---|---|---|---|---|---|
| 1 | **CAM op frontends are setTimeout fakes** (DrillingView:39, PocketClearingView:51, ContourCuttingView:35, SurfacingView:25, FretSlottingView:56) | code | **VERIFIED** | BUILD | **MVP-BLOCKING** | grep: pure `setTimeout`, no fetch/api; `/api/...` only in header docstrings | Wire each to its real endpoint, or remove/gate the view |
| 2 | **8I/8J backend real but frontend still fake** (Drilling/Pocket UIs reference old `preview/generate`, not the merged `intent-gcode`) | code+git | **VERIFIED** | BUILD | **MVP-BLOCKING** | 8I `a9409305` / 8J `60528f02` merged; views unwired (item 1) | Wire DrillingView/PocketClearingView → `/api/cam/{drilling,pocketing}/intent-gcode` |
| 3 | CI-RED-003 — debt-gate complexity ratchet (113 violations) | SPRINTS.md:875 | OBSERVED (not re-run) | GRIND | POST-MVP | marker OPEN 2026-05-27; triage "not MVP-gating" | Complexity refactor pass (risk: alters kernels) |
| 4 | CI-RED-004 — legacy `/api/rmos/runs` frontend refs | SPRINTS.md:876 | **VERIFIED still open** | STALE-FIX/GRIND | MVP-ADJACENT | Grep: **22 refs / 9 files** in `packages/client/src` | Mechanical reference cleanup; fence-test gated |
| 5 | CI-RED-015-E — `board_feet` + `fretboard` calc drift | TRIAGE:114 | OBSERVED (not re-run) | DECISION→maybe BUILD | **MVP-BLOCKING?** | triage: calc-kernel drift; api-verify not run this pass | **VERIFY FIRST** (run the two suites); if real, fix — calc errors are user-facing |
| 6 | CI-RED-016 — endpoint consolidation (1181 routes) | TRIAGE:115 | OBSERVED | GRIND | POST-MVP | "documentation only until post-MVP cut" | Deferred by design |
| 7 | CI-RED 001/002/005–014/015-A–D — CLOSED | SPRINTS.md:873-886 | OBSERVED (markers; **not independently re-run**) | ALREADY-DONE (claimed) | n/a | markers CLOSED w/ PR refs | Spot-check highest-risk before trusting (015-D, 002) |
| 8 | Consolidator A-task — `contour_reconstruction` R12-safe fallback | [[project_cam_8i...]]/audit | **VERIFIED decided** | BUILD | MVP-ADJACENT | free-tier ungated endpoint ships R2000 (Surface-D audit) | Version-adaptive R12-legal output; POLYLINE-vs-LINE call |
| 9 | Consolidator B-sanctions (`dxf_consolidator` dead code; `layer_consolidator` internal-temp) | audit 2026-06-09 | **VERIFIED decided** | STALE-FIX (doc) | POST-MVP | dxf=no callers (2nd-pass empty); layer=internal IBG temp | Sanction docs + dxf deprecation flag |
| 10 | 6 untracked audit/handoff docs never committed | `git status` | **VERIFIED** | STALE-FIX | POST-MVP | `??` PRE_GOVERNANCE_FORENSIC, PROVENANCE_LEDGER, SANDBOX_DRIFT, SCALE_VALIDATION_VERIFY, **TRIAGE_INVENTORY_2026-06-02** (prior triage!), CAM_INTENT_RUN_PERSISTENCE_HARDENING | Commit-or-delete decision per doc |
| 11 | GOV-CONVERGE-002 (R1 schedule) / 003 (codeowner D1–D4) | SPRINTS.md:778 | OBSERVED | DECISION (codeowner) | POST-MVP | "neither blocks MVP cut" | Codeowner answers / schedules |
| 12 | Dependabot 2 high (main) + npm-audit 23 (client) | [[project_deferred...]] | OBSERVED (re-confirmed outstanding) | GRIND | POST-MVP | recorded 2026-06-08 | `npm audit` triage; dep bumps |
| 13 | ~85 stale local branches | [[project_deferred...]] | OBSERVED | GRIND | POST-MVP | recorded 2026-06-08 | Prune, verify-content-not-ancestry per branch |
| 14 | In-code debt markers (non-test py) | code | **VERIFIED count** | GRIND | POST-MVP | reconciled: **13** TODO/FIXME/HACK/XXX; 198 "mock/stub" mostly legit | Enumerate + clean opportunistically |
| 15 | Repo-wide `setTimeout` (vue/ts non-test) = **180** — NOT 180 fakes | code | **VERIFIED count** | GRIND | POST-MVP | reconciled count; only the **5 cam-op views (item 1)** confirmed pure-fake; ~174 others mostly legit timers (e.g. `CamWorkspaceView` debounce) | Residual gap: other op-views *outside* `views/cam/` not individually checked — see partial note |

---

## MVP-BLOCKING shortlist (the critical path to an honest tag)

The MVP bar (SPRINTS.md:12): **design → platform → G-code → cut on BCAM 2030CA.** "Blocking" = shipping
the tag without it ships a *known-false claim* or *user-facing defect*.

1. **CAM operation frontends are fakes (items 1+2) — BUILD.** The single biggest blocker. The G-code
   step of the MVP bar is *faked in the UI*: 5 cam views run `setTimeout` with no API call. Worst:
   DrillingView + PocketClearingView have **real, merged backends (8I/8J) the UI never calls** — it
   still names the old `preview/generate` endpoints. Shipping a tag where "generate drilling/pocketing
   toolpath" is a 500ms fake is shipping a false claim. **Fix = wire each view to its real endpoint, or
   remove/gate the view from the MVP surface.** (Fresh-head frontend build.)
2. **CI-RED-015-E calc-kernel drift (item 5) — VERIFY, then maybe BUILD.** `board_feet`/`fretboard`
   drift is a *calculation* defect — if real on main, the numbers a user sees are wrong, which is
   MVP-blocking. **Not re-run this pass** → first action is to run the two api-verify suites; classify
   blocking vs not from the result. (Decision-ready to *verify*; fix is a build.)

Conservatively, **only these two** meet the "false claim / user-facing defect" bar. Everything else is
hygiene, post-MVP, or deferrable (below).

---

## DECISION-READY bucket (priority — read-only / trivially-reversible, unblocks a decision, no net-new build)

Ordered by MVP relevance:

1. **CI-RED-015-E verification (item 5)** — run `board_feet` + `fretboard` api-verify suites; the result
   decides whether it's MVP-blocking. Read-only run → decision. *Do this first.*
2. **CLOSED CI-RED spot-check (item 7)** — given the repo's false-completion history, independently
   re-verify the 2 highest-risk CLOSED entries (**015-D** "pending one live app.routes dump — never
   executed"; **002** legacy-usage gate) before trusting the closed-count. Read-only.
3. **Untracked-doc disposition (item 10)** — decide commit-or-delete for the 6 orphans; note the **prior
   triage (TRIAGE_INVENTORY_2026-06-02) is itself untracked**, so its CI-RED status claims aren't on
   main. Trivially reversible.
4. **Consolidator B-sanctions (item 9)** — near-zero-code doc sanctions (dxf=dead-code/deprecate;
   layer=internal-temp). Decision recorded; just needs the doc edit.
5. **CI-RED-004 (item 4)** — confirmed-open (22 refs); mechanical cleanup, fence-gated. Low-judgment.

---

## BUILD bucket (net-new construction — fresh head, NOT decision-ready)

- **CAM op-view wiring (items 1+2)** — the MVP-blocking frontend build: wire DrillingView/
  PocketClearingView (and decide Contour/Surfacing/FretSlotting: wire vs gate) to real endpoints.
  Highest-stakes net-new, user-facing.
- **Consolidator A-task (item 8)** — `contour_reconstruction` R12-safe version-adaptive fallback
  (POLYLINE-vs-LINE-chains decision). Already designated next-session opener.
- **CI-RED-015-E fix (item 5)** — *if* verification confirms the drift.

---

## GRIND / deferred bucket (batchable, low-judgment, or already-deferred)

- CI-RED-003 complexity ratchet (item 3) · CI-RED-016 consolidation (item 6) · CI-RED-004 cleanup
  (item 4) · in-code debt markers (item 14) · dependency advisories (item 12) · ~85-branch prune
  (item 13) · untracked-doc cleanup once dispositioned (item 10).

---

## Stale markers reconciled (so the "real open" count isn't inflated by ghosts)

**ALREADY-DONE on main (verified this/prior session — do NOT count as open):**
- 8G/8H/8I/8J **backend** intent lanes — merged (`b0f88a73`→#88, `5f0dfd91`#92, `a9409305`#93,
  `60528f02`#97). *Caveat: their frontends are NOT done (items 1–2).*
- R2000 bucket-② Scope #1 — merged (#91 `de1d150c`).
- Surface-D EXTMIN sentinel rule — corrected + merged (#98 `49577046`); blueprint-import affirmed correct.
- Consolidator fork — RESOLVED as a *decision* (A/B/B); only the A-task is unbuilt.
- CAM-TPA-001 toolpath animation — RESOLVED 2026-05-30 (SPRINTS.md:25).

**STALE pointers/markers found:**
- DrillingView/PocketClearingView header docstrings name `/api/cam/drilling/{preview,generate}` and
  `/api/cam/pocket/...` — **stale**: those aren't the real lanes (the real ones are `/intent-gcode`),
  and the code calls neither.
- TRIAGE_INVENTORY_2026-06-02 + 5 other audit docs — **untracked, not on main** (item 10); their status
  claims describe a pre-this-session state.

---

## Partial-coverage honesty note

Fully inventoried: CAM-fake cluster (verified), CI-RED open items (003/004/015-E/016), the session's
own merged/decided items, untracked docs, deferred pile, governance tail. **Not re-run this pass
(partial):** independent re-execution of the ~14 CLOSED CI-RED entries (item 7) and the 015-E api-verify
suites (item 5) — both flagged DECISION-READY-to-verify above; and full enumeration of the 13 debt
markers / 198 mock-stub hits (item 14, counted not itemized). **`setTimeout` reconciliation (item 15):**
repo-wide count is **180** in vue/ts non-test — this is NOT 180 fakes; only the 5 cam-operation views
(`views/cam/`) were individually verified as pure fakes. The remaining ~174 were **not individually
checked** (mostly legitimate timers); **residual gap = whether any operation/generation view OUTSIDE
`views/cam/` also fakes its output** — worth a targeted pass before the MVP tag, but the verified
MVP-blocking fakes are the five named in item 1. No other source categories outstanding.

---

## Gate-quality / tooling debt — `api_contract_check` blind spot (addendum 2026-06-11)

**Finding (from the contract-gate classification pass, 2026-06-11):** the
`api_contract_check` CI gate (`scripts/validate_api_contracts.py`) **cannot distinguish a
stale-contract from a fake-frontend on its own.** It only matches frontend `/api/...` string
literals against entries in `contracts/api_endpoints.json`; it **never consults the backend**
(`BACKEND_DIR` is defined but unused). So a violation means *"a frontend call has no contract
entry,"* never *"the route is missing."* Consequences:

1. **The gate can be satisfied by blessing a void.** Adding a non-existent route to the contract
   greens the gate while certifying a 404. This is not hypothetical — of the 16 NEW violations
   classified this pass, **3** (`/api/rmos/acoustics/ingest-events`, `/counts`, `/{event_id}`) are
   routes *declared* in `router_ingest_audit.py` but **never `include_router`'d** (unreachable). A
   prior auto-patch proposed adding them to the contract; that would have institutionalized three
   404s. Telling real from void required a **human-run live-route-table pass** (booting
   `app.main:app`, enumerating mounted routes) — the gate does not do this.
2. **Blind to variable-url calls.** The regex only sees inline `/api/...` literals, so
   `fetch(url, …)` clients (`src/api/drilling.ts`, `pocketing.ts`) are invisible to the gate.
3. **The baseline grandfathers fakes.** `--write-baseline` snapshots *all* current frontend calls
   as accepted, so any fake predating the baseline (e.g. the already-baselined `/api/v1/dxf/cam/gcode`)
   is **permanently green**.

**Recorded improvements (not done — toward an honest MVP tag):**
- **Make the validator mount-aware** — have it consult the live mounted route table (the
  defined-but-unused `BACKEND_DIR`) so mount-gap voids are caught automatically instead of by a
  human pass each time.
- **Audit the baseline set** (`contracts/api_calls_baseline.json`) for grandfathered fake-frontend
  calls; verify baselined calls at the live-route bar, not just NEW ones.

**Resolved this pass (for context):** 13 of the 16 NEW were verified real/mounted and added to the
contract (#102, `69e9ec59`); the gate now shows exactly the 3 acoustics-void violations above, which
are a **mount-or-gate product decision** (mount `router_ingest_audit.py` then contract, OR honest-gate
the frontend calls — NOT a contract add). The frontend also calls `/{eventId}` (camelCase) vs the
declared `/{event_id}` — reconcile if mounting.

---

*Read-only pass complete (original 2026-06-09 section). No repository state modified except this inventory doc. No action taken on any item.*
