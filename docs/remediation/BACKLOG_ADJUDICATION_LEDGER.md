# BR-001 — Backlog Adjudication Ledger

> The canonical item-level ledger. **No item may appear in the execution queue without a corresponding
> adjudication record here.** Populated from the discovery sweep; each record carries its
> evidence tier and current verification state so coverage is never overstated.

## Record schema

Every adjudicated item carries:

```text
Backlog ID                 BR-NNN (stable)
Title
Subsystem
Source reference           (branch / doc path / issue# / file:line)
Original date              (where available)
Evidence tier              A | B | C   (charter §3)
Current evidence           (what was inspected/reproduced now)
Reproduction method        (failing test / command / code-path / contract / runtime obs / absent-impl)
Primary disposition        (one of the 13 — charter §4)
Secondary labels           (subsystem / severity / safety / user-impact / release)
Severity
User impact
Safety or manufacturing impact
Architectural impact
Dependencies               (BR-NNN it needs)
Blocking items             (BR-NNN it blocks)
Estimated size
Readiness                  (ready / blocked / needs-owner-decision)
Recommended action
Owner ruling required      (yes/no + question)
Notes
```

## Disposition vocabulary (exactly one primary per item)

`COMPLETE` · `SUPERSEDED` · `DUPLICATE` · `STALE_OR_NOT_REPRODUCIBLE` · `UNFINISHED_SPRINT_WORK` ·
`CONFIRMED_DEFECT` · `MIGRATION_GAP` · `PERFORMANCE_DEBT` · `MAINTAINABILITY_DEBT` · `ENHANCEMENT` ·
`DEFERRED_RESEARCH` · `EXTERNAL_OR_ENVIRONMENTAL` · `OWNER_DECISION_REQUIRED`

## Ledger

Adjudicated set from the 2026-07-20 sweep against `origin/main` `d716d16`. **Verification method** is
recorded per item: `code-inspection` (deterministic grep/read — a valid current reproduction basis per
charter §4 · Disposition discipline), `test-encoded` (a committed xfail/skip test asserts the behavior now), `doc-validated`
(Tier B — checked against current tree, not run), `wave0-local-run` (surfaced by the Wave 0 pytest on a
local non-CI toolchain — directional, CI-stack confirmation pending), `pending-CI-run` (needs the
authoritative CI-stack run). Tier A/B items only are queue-eligible; Tier C is inventoried in aggregate
(see below).

| BR ID | Title | Subsystem | Source ref | Tier | Disposition | Verify | Sev | Readiness | Recommended action |
| ----- | ----- | --------- | ---------- | ---- | ----------- | ------ | --- | --------- | ------------------ |
| BR-001 | `store_artifact()` rejects `batch_label` (TypeError) | saw_lab | `app/saw_lab/store.py:16`; `tests/test_saw_lab_endpoint_smoke.py:30` xfail | A | CONFIRMED_DEFECT | code-inspection + test-encoded | high | ready | thread `batch_label` into store layer; flip xfail |
| BR-002 | `list_runs_filtered()` rejects `tool_kind` (TypeError) | rmos/runs_v2 | 3-layer chain (per [BR-002A_PROOF](BR-002A_PROOF.md) Q1): `store_api.py:200` raise-site (re-exported as `store.list_runs_filtered` via `store.py:396`), then `store.py:294` class method, then `store_filter.matches_index_meta` (only 2 internal callers); `tests/test_saw_lab_endpoint_smoke.py:24` xfail | A | CONFIRMED_DEFECT | code-inspection + test-encoded | high | **BR-002B-ready** (owner auth pending) | proof green — apply the [BR-002A_PROOF](BR-002A_PROOF.md) patch plan as **BR-002B** |
| BR-003 | Simulation metrics router/schema mismatch (8 xfails) | simulation | `tests/test_simulation_endpoint_smoke.py:28` | A | CONFIRMED_DEFECT | test-encoded | med | ready | reconcile metrics router vs schema |
| BR-004 | `list_runs_filtered()` kwarg bug (was mislabeled "store_artifact") | rmos | `tests/test_rmos_endpoint_smoke.py:21` xfail (`strict=False`) | A | CONFIRMED_DEFECT | test-encoded | med | dedup → BR-002 | **same `list_runs_filtered` root as BR-002** (per [BR-002A_PROOF](BR-002A_PROOF.md) Q7); fixed by BR-002B |
| BR-005 | CAM 7D/7E/7F translation-artifact: "impl complete, pending tests+commit" | cam/translation | `docs/handoffs/CAM_7{D,E,F}_*.md` | A | UNFINISHED_SPRINT_WORK | doc-validated | med | ready | complete tests + commit the authorized work |
| BR-006 | CAM 8J pocketing-intent reconstruction (source `.py` lost, `.pyc` only) | cam/pocketing | `docs/handoffs/DEV_ORDER_2026-06-08_CAM_8J_POCKETING_INTENT.md`, `RECOVERY_8J_*` | A | UNFINISHED_SPRINT_WORK | doc-validated | high | ready | reconstruct lane (data-loss risk) |
| BR-007 | CI-RED-020B API health+smoke nightly witness recovery | ci | `docs/handoffs/CI_RED_020B_dev_order.md` (+addendum) | A | UNFINISHED_SPRINT_WORK | doc-validated | med | ready | execute dev-ready handoff |
| BR-008 | CI-RED-016B endpoint consumer map | ci/api | `docs/handoffs/CI_RED_016B_*.md` | B | UNFINISHED_SPRINT_WORK | doc-validated | low | blocked(016) | consumer-map prerequisite for 016 consolidation |
| BR-009 | CI-RED-019-003 ledger reconciliation | ci | `docs/handoffs/CI_RED_019_003_*.md` | B | UNFINISHED_SPRINT_WORK | doc-validated | low | ready | reconcile CI-RED ledger vs SPRINTS |
| BR-010 | NECK-A frontend migration completion | client/neck | `docs/handoffs/NECK_A_MIGRATION_COMPLETION_PLAN.md` | A | UNFINISHED_SPRINT_WORK | doc-validated | med | ready | finish migration (no behavior change) |
| BR-011 | Three-loop/AGE conflation removal (unsourced mandate) | governance/docs | `docs/handoffs/DEV_HANDOFF_2026-05-30_THREE_LOOP_*` | B | UNFINISHED_SPRINT_WORK | doc-validated | low | ready | remove unsourced architecture doc mandate |
| BR-012 | Aperture workspace refactor (Track A mid-flight) | cam/aperture | `docs/handoffs/APERTURE_WORKSPACE_REFACTOR_*.md` | A | UNFINISHED_SPRINT_WORK | doc-validated | med | needs-scope | finish or bound Track A |
| BR-013 | RMOS workflow `approve` endpoint not wired (`state_machine.approve()` exists, no route) | rmos/workflow | `tests/test_rmos_workflow_e2e.py:63` skip | A | UNFINISHED_SPRINT_WORK | test-encoded | med | ready | wire approve route |
| BR-014 | SPINE-002/003/004 adoption sprints held-draft, unmerged | project-spine | branches `spine-002/003/004-*` (unmerged); audits SPINE_002/3/4 | A | UNFINISHED_SPRINT_WORK | doc-validated | med | needs-owner | owner merge decision (as SPINE-005 pattern) |
| BR-015 | rmos runs_v2 `strict=False` pending post-migration enable | rmos/runs_v2 | `app/rmos/runs_v2/store.py:169` TODO | A | MIGRATION_GAP | code-inspection | med | ready | enable `strict=True` after migration |
| BR-016 | instrument_geometry deprecated monolith endpoints still sole home | instrument_geometry | `tests/test_instrument_geometry_router_smoke.py:60,699` skip | A | MIGRATION_GAP | test-encoded | med | ready | migrate endpoints off deprecated monolith |
| BR-017 | IBG PR #224 readiness-report content stranded off `main` (squash-order race) | ibg_repository | PR #224 `e7e84b4`; branch `feature/ibg-repository-proposal-evaluation` | A | MIGRATION_GAP | code-inspection | med | ready | re-land #224 content to main |
| BR-018 | DXF consolidator R2000 fallback: sanction vs make R12-safe (unmade fork) | dxf | `docs/handoffs/DEV_ORDER_2026-06-08_DXF_CONSOLIDATOR_R2000_*` (DRAFT) | A | OWNER_DECISION_REQUIRED | doc-validated | med | needs-owner | resolve Option A/B fork before execution |
| BR-019 | Auth + DB-session are stubs in API deps | api/deps | `app/api/deps/__init__.py:84,100` TODO | A | OWNER_DECISION_REQUIRED | code-inspection | high? | needs-owner | is a user/auth system in scope? safety-adjacent |
| BR-020 | Standing residual reds #7 (REJECT→authority lock), #12 (zone x-gating) | rmos/geometry | triage doc 2026-06-29 | A | OWNER_DECISION_REQUIRED | pending-CI-run | med | needs-owner | product decisions block auto-fix |
| BR-021 | CI gates suppressed: `client_lint_build` continue-on-error (400+ TS errors); vue_decomposition non-blocking | ci/client | `.github/workflows/client_lint_build.yml:42`, `vue_decomposition_gate.yml:79` | A | MAINTAINABILITY_DEBT | code-inspection | med | ready | burn down TS errors → re-block gate |
| BR-022 | SG_SPEC_TOKEN private-repo failures across ~21 workflows (partially guarded) | ci | `docs/ci/CI_HYGIENE_DEBT_PATCH_PLAN.md` (issue #20) | B | MAINTAINABILITY_DEBT | doc-validated | low | ready | complete env-guard rollout |
| BR-023 | Art-studio UI surfaces wired to non-existent API (Soundhole/Binding "coming soon") | client/art-studio | `SoundholeRosetteShell.vue:94-114`, `BindingDesignerView.vue:53-66` | B | ENHANCEMENT | code-inspection | low | needs-owner | backend never approved — enhancement, not defect |
| BR-024 | "Still `ezdxf.new(R2000)`" regression (spiral/archtop) | dxf | audit `sprints_audit_2026-04-23.md` | B | SUPERSEDED | code-inspection | — | n/a | **superseded by BR-018.** The literal `ezdxf.new("R2000")` call form is gone (DXF version now flows through `app/util/dxf_compat.py`, version-parameterized), but R2000 is **not** removed — it remains a supported output referenced across ~29 `app/` files incl. the audited `archtop_floating_bridge.py`. Grep-absence of the literal string ≠ R2000 output removed; the R2000 default/sanction decision is the open **BR-018** fork. |
| BR-025 | Baseline test failures handoff (40 failed) | ci | `docs/handoffs/BASELINE_TEST_FAILURES_HANDOFF.md` | B | SUPERSEDED | doc-validated | — | n/a | ratchets rebaselined (945→1225); superseded |
| BR-026 | CI-RED-015D wire-URL collision open decisions | ci | `docs/handoffs/CI_RED_015D_OPEN_DECISIONS.md` | B | COMPLETE | doc-validated | — | n/a | doc self-declares CLOSED 2026-05-30 |
| BR-027 | CAM_7x governance + MRP_5x runtime-spine clusters | cam/rmos | handoffs marked COMPLETE/IMPLEMENTED/RELEASE READY | B | COMPLETE | doc-validated (sampled) | — | n/a | historical-complete; excluded from queue |
| BR-028 | Endpoint sprawl (1,132 mounted operations) | api | audit `CI_RED_016_ENDPOINT_CONSUMER_MAP.md`; ratchet `TARGET_MAX_ENDPOINTS=1225` | B | MAINTAINABILITY_DEBT | doc-validated | med | blocked(BR-008) | consolidation, gated by consumer map |
| BR-029 | 52 high-risk formulas awaiting manual verification | calculators | audit `math_formula_catalog_2026-04-30.md` | B | OWNER_DECISION_REQUIRED | doc-validated | med | needs-owner | evidence-integrity; owner verification plan |
| BR-030 | Instrument model coverage: 24 models, only 2 complete end-to-end | instrument models | audit `instrument_model_coverage_2026-04-26.md` | B | ENHANCEMENT | doc-validated | low | n/a | capability expansion, not defect |
| BR-031 | Salvage/backup branches (7 `salvage/*` stashes, `backup/*`) | git hygiene | branch inventory | C | STALE_OR_NOT_REPRODUCIBLE | code-inspection | — | n/a | archive; not queue work |
| BR-032 | Body-solver failure cluster (17 reds: body_solver_integration/morphology_spine/ibg_export + 3 cam feeds/speeds) | body_solver / cam | Wave 0 run; unmerged `fix/ci-red-015{i,k}-*` | A | CONFIRMED_DEFECT | wave0-local-run (CI-stack unconfirmed) | high | needs-CI-confirm | reproduce on CI 3.11; check if 015i/015k resolve; then bound |
| BR-033 | `app.openapi()` fails to build; field `validate` shadows `BaseModel.validate` | api/schema | Wave 0 `test_openapi.py`; pydantic UserWarnings | A | CONFIRMED_DEFECT | wave0-local-run (toolchain-amplified) | med | needs-CI-confirm | rename shadowing field; confirm openapi builds on CI stack |
| BR-034 | Stale xfail marker now XPASSes (1) | tests | Wave 0 (1 xpassed) | B | MAINTAINABILITY_DEBT | test-encoded | low | ready | identify + remove the obsolete xfail marker |

## Verification coverage

34 items total: **Tier A 20 · Tier B 13 · Tier C 1**.

- **Tier A items:** 20 (BR-001..007, 010, 012..021, 032, 033). Verified — **code-inspection**: BR-001,
  002, 015, 017, 019, 021 (also BR-024 Tier B, 031 Tier C by inspection); **test-encoded**: BR-003, 004,
  013, 016; **doc-validated**: BR-005, 006, 007, 010, 012, 014, 018; **wave0-local-run**: BR-032, 033;
  **pending-CI-run**: BR-020.
- **Tier B items:** 13 (BR-008, 009, 011, 022, 023, 024, 025..030, 034). Validated against current tree;
  not run.
- **Tier C:** 1 (BR-031), plus the aggregate inventory — ~7 `salvage/*` stash branches, `backup/*`,
  declared-complete handoff clusters (CAM_7x, MRP_5x), and superseded docs. Not individually revalidated;
  not queue-eligible.
- **Owner-decision items:** BR-014, 018, 019, 020, 029 (5).
- **Not exhaustive:** this is the adjudicated *material* set. The ~166 handoffs / 157 branches / 40
  audits are catalogued in [BACKLOG_SOURCE_INVENTORY.md](BACKLOG_SOURCE_INVENTORY.md); items not
  surfacing a current signal remain Tier C (inventoried, not revalidated) per charter §3.
- **Wave 0 live run — DONE (2026-07-20):** full `services/api` pytest vs `d716d16` — **21 failed / 8155
  passed / 19 xfailed / 1 xpassed** on a local Python 3.14 toolchain (**directional, not the authoritative
  CI count**; triage reported ~12 on the older `0daeab14`). Surfaced BR-032/033/034. Full record +
  caveat: [WAVE_0_VERIFICATION.md](WAVE_0_VERIFICATION.md). The authoritative **CI-stack (3.11)** run
  remains the recommended confirmation.
