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
| BR-001 | `store_artifact()` rejects `batch_label` (TypeError) | saw_lab | `app/saw_lab/store.py:16` | A | COMPLETE | test-verified | high | **FIXED (BR-002B)** | `store_artifact` now accepts `batch_label`/`tool_kind` (batch_label→payload); xfail removed, test passes |
| BR-002 | `list_runs_filtered()` rejects `tool_kind` (TypeError) | rmos/runs_v2 | 3-layer chain: `store_api.py` + `store.py` + `store_filter.matches_index_meta` | A | COMPLETE | test-verified | high | **FIXED (BR-002B)** | `tool_kind` threaded through all 3 layers; `matches_index_meta` reads nested `meta.tool_kind` via canonical `tool_kind_matches()` (lenient+synonym); list/count parity; xfail removed |
| BR-003 | Simulation metrics router/schema mismatch (8 xfails) | simulation | `tests/test_simulation_endpoint_smoke.py:28` | A | CONFIRMED_DEFECT | test-encoded | med | ready | reconcile metrics router vs schema |
| BR-004 | `list_runs_filtered()` kwarg bug (was mislabeled "store_artifact") | rmos | `tests/test_rmos_endpoint_smoke.py:21` | A | COMPLETE | test-verified | med | **FIXED (BR-002B)** | same root as BR-002; fixed together; xfail removed, test passes |
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
| BR-035 | `batch_tree` `tool_kind` exact-match silently under-returns mixed/old batches | rmos/runs_v2 | `app/rmos/runs_v2/batch_tree.py:51,122` | A | COMPLETE | test-verified | med | **FIXED (BR-002B)** | both filters now use the canonical `tool_kind_matches()` helper (lenient+synonym); regression `test_batch_tree_tool_kind_lenient` |
| BR-036 | `batch_tree` `isinstance(a, dict)` guard excludes `RunArtifact` results from `list_runs_filtered` (via `as_items`) → **empty trees** for the real store output | rmos/runs_v2 | `app/rmos/runs_v2/batch_tree.py:51,122` + `artifact_helpers.as_items`; found empirically during BR-002B | A | CONFIRMED_DEFECT | **code-traced + reproduced** | **high** | ready | **out of BR-002B scope** (per owner boundary — shape/persistence, not the `tool_kind` repair); own bounded Dev Order — needs a shape adapter, not a cast (see severity note below) |

> **BR-036 severity raised med → high (2026-07-22, BR-002B review).** Three findings, each
> code-traced on the PR head and reproduced:
>
> 1. **It is live, not potential.** `RunStoreV2.list_runs_filtered` is annotated
>    `-> List[RunArtifact]` and appends `RunArtifact.model_validate(...)`; the
>    `store_api.list_runs_filtered` wrapper returns that list **without dict conversion**.
>    So `as_items()` — whose docstring promises "list of artifact **dicts**" — returns
>    pydantic models, and `list_batch_tree` drops every one at `isinstance(a, dict)`.
>    Production trees are **empty (`node_count: 0`)**, not merely incomplete.
> 2. **Second failure mode: a crash, not just an empty result.** `resolve_batch_root`
>    applied its `isinstance` filter only inside the `if tool_kind:` branch, so the
>    *unfiltered* call reached `_get_id(a)` → `a.get(...)` → **`AttributeError` (HTTP 500)`**,
>    while the same input with `tool_kind` set returned `None`. Reproduced directly.
>    BR-002B makes this path *graceful* (filter hoisted, pinned by
>    `test_resolve_batch_root_non_dict_items_does_not_crash_without_tool_kind`) but does
>    **not** fix the shape defect — trees stay empty until BR-036 lands.
> 3. **Consequence for BR-035.** Because every item is dropped upstream, the BR-035
>    `tool_kind` filter inside `batch_tree` **never executes against real store output**.
>    BR-035 is correct and regression-pinned, but is exercised only by dict-shaped test
>    doubles; its production benefit is gated on BR-036.
>
> **Fix is a shape adapter, not a cast.** A plain `model_dump()` is insufficient — the
> helpers and `RunArtifact` use different vocabularies:
> `id`/`artifact_id`→`run_id`, `created_utc`→`created_at_utc` (and `str`→`datetime`),
> `index_meta`→`meta`, `kind`→`event_type`. Only `index_tool_kind()` already reads `meta`.
> `batch_timeline.py:111` consumes `as_items` identically and carries the same defect, so
> the adapter belongs in `artifact_helpers.as_items` (restoring its documented contract),
> which fixes both call sites at once. This sizing confirms the BR-002B scope boundary was
> correct: it is a bounded Dev Order, not a line-edit.

## Materials-index intake (2026-08-03)

Adjudicated outside the 2026-07-20 sweep, against `origin/main` `ada33581`. Recorded here because the
execution queue requires a corresponding adjudication record; kept in its own dated section so the
sweep table above continues to mean "the 2026-07-20 set".

| BR ID | Title | Subsystem | Source ref | Tier | Disposition | Verify | Sev | Readiness | Recommended action |
| ----- | ----- | --------- | ---------- | ---- | ----------- | ------ | --- | --------- | ------------------ |
| BR-043 | Tonewood radiation-ratio `*1e6` collapses `_score_acoustic` to 0.0 for every species | materials | `app/materials/schemas.py:148-156` vs `recommendation/scorer.py:33-73` | A | CONFIRMED_DEFECT | test-verified | high | **RESOLVED** | producer corrected to unscaled `c/rho`; direct scorer coverage added (19 tests). Merged PR #245 → `a34b6f5d`, CI 44 pass / 0 fail. Post-merge witness on `a34b6f5d`: Basswood `radiation_ratio` 11.87, `_score_acoustic(soundboard)` **0.9924** (was 0.0) |

**Evidence.** The producer returns `(c/rho)*1e6`; its own docstring, `_ROLE_TARGETS`, and `router.py:88`
all declare the unscaled `c/rho` scale. `_score_acoustic` compares directly with `sigma = 3.0` and no
inverse scaling, so the Gaussian underflows to 0.0 for every real wood. Reproduced by
`tests/materials/test_tonewood_acoustic_indices.py` (3 × `xfail(strict=True)`).

| BR-044 | Frontend radiation-ratio producer and rating thresholds use incompatible scales | client/wood-intelligence | `useStiffnessIndex.ts:69-71` vs `:149-152` + `StiffnessIndexPanel.vue:312-317` | A | CONFIRMED_DEFECT | code-inspection | high | **QUEUED — NOT AUTHORIZED** | reproduce the rendered symptom, inventory consumers, then rule on frontend-corrected vs consume-backend |

| BR-045 | `specific_moe` carries two incompatible scales across backend and frontend (1000×) | materials + client | `schemas.py` `specific_moe` vs `useStiffnessIndex.ts:78-80,159` | A | ~~OWNER_DECISION_REQUIRED~~ **RESOLVED** | test-verified + runtime witness | med | **RESOLVED** | Owner ruled `c²/10⁶` 2026-08-04; PR #247 → `f12f88c2` (`1e6`→`1e3`). Post-merge witness on `969bdbdc`: Basswood/WRC/Bubinga `specific_moe` = **24.2651 / 21.0270 / 20.6854** (= `c²/10⁶` = frontend); BR-043 `radiation_ratio` 11.87 / score **0.9924** unchanged |

| BR-046 | CBSP21 gate names an unrelated stale manifest when nothing covers the diff | ci/governance tooling | `scripts/ci/check_cbsp21_gate.py` + `cbsp21_manifest_discovery.py`; CI run `31466755438` | B | CONFIRMED_DEFECT | ci-reproduced | low | **QUEUED — NOT AUTHORIZED** | at 0 covered files, suppress the manifest name and emit the existing "create one under `.cbsp21/patches/`" guidance instead. **Diagnostic quality only — enforcement is sound** |

**BR-046 — evidence and boundary.** Reproduced by the DEP-SEC-001B negative-gate witness: a throwaway
branch off `main` @ `25fc189d` carrying one undeclared file made the gate print
`Manifest: .cbsp21/patches/audit-n1-refuted.json` — an unrelated merged-PR manifest — at 0.0% coverage.
The same witness proved enforcement is **correct** in both directions on the real patch (declared 5-file
set → 100.0%, exit 0; +1 undeclared file → 80.0%, exit 1, file named). Observed in practice on PRs #251
and #252, which both reported `wp-002-a-shim-reconfirmation.json` at 0.0% when the true cause was that
no per-PR manifest existed yet. Contradicts `.cbsp21/patches/README.md`, which states stale manifests
"are ignored automatically". Filed separately from PR #259 rather than repaired inline, since folding a
tooling fix into a docs/governance patch is the scope contamination Rule 8 exists to prevent.

**BR-045 — historical disposition note.** Intake used `OWNER_DECISION_REQUIRED` (not `CONFIRMED_DEFECT`)
because the docstring contradiction was confirmed but *which side moves* was not repository-derivable
without a published-unit ruling. That ruling was granted 2026-08-04 (`c²/10⁶`), implemented in PR #247
(`f12f88c2`), and closed by BR-045A after post-merge witness on `969bdbdc`. Lifecycle:

```text
queued pending owner unit ruling
→ owner ruling granted
→ implementation authorized
→ PR #247 merged
→ post-merge runtime witness passed
→ resolved
```

**BR-044 evidence label — `STATIC-FACT CONFIRMED`.** The frontend producer computes `(c/ρ)*1000`
(~9,000–14,000 for normal tonewoods) while `rrColor` and `soundboardRating` threshold at 12.0 / 10.5 /
9.0 on the unscaled scale, so every wood with MOE data takes the top branch. Separate implementation
and data path from BR-043 — it reads hardcoded `tonewoodData.ts`, not the API. Requires
rendered-behavior reproduction and an authority decision before remediation.

> **Vocabulary note.** `STATIC-FACT CONFIRMED` is the register's *evidence label* for intake leads
> (see the scan-intake exception in [REPOSITORY_DEFECT_REGISTER.md](REPOSITORY_DEFECT_REGISTER.md)),
> not one of the 13 primary dispositions. The nearest primary term is `CONFIRMED_DEFECT` with
> `code-inspection` verification, which the register explicitly admits as a valid current reproduction
> basis. Readiness carries the real constraint: the runtime symptom is **unreproduced** and the item
> is **not authorized**.

**Owner ruling required:** BR-043 no — this is an internal-consistency repair against contracts the
repository already states; it does not adjudicate physics, role targets, or recommendation philosophy.
**BR-044 yes** — proof-packet item 5 is an authority decision between correcting the frontend
calculation and deleting it in favour of the backend canonical value.

**Dependencies:** none. Independent of PR #244 — MB Sound corroborates the scale but is not runtime
authority and is not imported by this repair.

> **Ledger/register divergence, noted not fixed.** BR-037…BR-042 appear in
> [REPOSITORY_DEFECT_REGISTER.md](REPOSITORY_DEFECT_REGISTER.md) but have no row in this ledger; both
> were admitted through dated register sections that did not write back here. BR-043 does write back.
> Reconciling BR-037…042 is pre-existing and outside this Dev Order.

## Verification coverage

36 items total in the 2026-07-20 sweep table: **Tier A 22 · Tier B 13 · Tier C 1**. Plus **BR-043**
(Tier A, `CONFIRMED_DEFECT`, 2026-08-03 materials-index intake, recorded in its own section above). **BR-001/002/004/035 FIXED by BR-002B** (first
executed code remediation); BR-036 added (deeper batch_tree shape defect, out of BR-002B scope).

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
