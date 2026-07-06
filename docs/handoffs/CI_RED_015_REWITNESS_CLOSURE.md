# CI-RED-015 Re-Witness Closure

**Date:** 2026-07-05
**Method:** re-witness, not re-implement. The ledger recorded 43 failing tests from a
2026-06-16 snapshot; the clusters have been closed piecemeal since. This proves that
closure already happened and reconciles the bookkeeping to the reality CI already shows.
No production code changed in this pass.

**Pinned witness SHA:** `13aabe4f` (current `main`).

## 1. The claim being tested

CI-RED-015 row says **43 failed** (Core CI run `27630309072` @ `c41fc656`, 2026-06-16).
Current `main` shows API Tests, api-verify, and Core CI green. Ledger and CI disagree;
this establishes which is stale — **positively, per cluster, not by suite-green inference.**

The discipline held: *a suite can be green because failing tests were deleted, skipped,
or xfail'd rather than fixed.* Green-by-suppression is a worse open item, not a close.
So the witness verifies each of the original 43 **runs and passes**, and that **none**
were suppressed.

## 2. Authoritative evidence

**CI (aggregate), on `13aabe4f`:**
- `Core CI (Consolidated)` — run **`28755048990`** — success (event: push to main).
- `API Tests` — run **`28755048968`** — success.

**Local targeted re-run of the exact 43, on a clean worktree off `13aabe4f`:**
- The 43 node IDs were recovered from the stale run's own failed-job log (`--log-failed`),
  so every one is traceable, not reconstructed.
- Re-ran the 17 test files that contain the 43: **464 passed, 1 skipped, 0 failed, 0 errors**
  (382s). The single skip is `test_morphology_spine_e2e.py::…::test_melody_maker_real_artifact_spine_flow`
  — a missing-DXF-fixture environmental skip, **not one of the 43**, and pre-existing.
- All 43 target method defs confirmed **present** in current source (0 renamed-away), and the
  parametrized `test_solve_all_supported_specs` still enumerates all four specs
  (`dreadnought, cuatro_venezolano, stratocaster, jumbo`).

## 3. Anti-suppression proof (the load-bearing check)

Static diff of every one of the 17 test files, `c41fc656 → 13aabe4f`:
- **No test files deleted.**
- **No new blanket suppression.** Pre-existing skip/xfail markers in
  `morphology_spine_e2e` (17), `body_export_bridge` (7), `rmos_runs_e2e` (1) are **unchanged**
  — and because all 43 were *failing* (not skipped) at `c41fc656`, a stable marker count
  proves none of the 43 were converted to a skip.
- **One marker added** — `test_operation_capability_registry.py` gained a *conditional helper
  skip* (fires only if no registry-valid DXF translator exists). The affected test,
  `test_registered_operation_works`, **ran and PASSED** — the skip did not fire. Flag cleared.

Conclusion: the 43 are genuinely resolved, not hidden. **43 → 0.**

## 4. Per-cluster resolution (each of the 43 traced to its fix)

| Cluster | n | Resolved by | Mechanism |
|---|---|---|---|
| **geometry-authority** (`test_geometry_authority_references.py`) | 10 | #158 (mount) + #182 `8c5244d2` (C2 process-exclusive, RATIFIED 2026-07-04) + #193 `cf02ab71` (GOV-CONVERGE-007-A) | Router mounted (015-H, `cam_manifest.py:259`); C2 keystone ruling operationalized; legacy artifact-derived `POST /references/canonical` **retired → 410**, tests migrated to the process-approved path and reorganized into new classes. This is the *Translation→Authorization Gate* the 015-H caveat flagged as missing. |
| **body-solver / IBG** (`test_body_solver_integration.py`) | 11 | #138 `4c4e208d` | Stale test — paid-tier body-solver endpoints require auth headers; tests updated. |
| **body-geometry-repair** (`test_body_geometry_repair.py`) | 4 | #160 `a849cce2` | Phase 6A body-geometry-repair reconciliation (arc bug was a category error). |
| **lifecycle-policy** (`test_lifecycle_policy_engine.py`) | 3 | #161 `9ee58181` | Use registered translator in lifecycle-policy fixtures. |
| **morphology-spine** (`test_morphology_spine_e2e.py`) | 3 | #175 `0647df75` (Batch A) | Stale tests. |
| **singletons** | 12 | see below | mixed stale-test + real production-defect fixes |

**Singletons (12):**

| Test | Resolved by | Kind |
|---|---|---|
| `test_drilling_intent_migration::test_legacy_routes_unchanged` | #169 `eaf94add` | route introspection + Windows cwd |
| `test_pocketing_intent_migration::test_registration_and_parity` | #169 `eaf94add` | route introspection + Windows cwd |
| `test_saddle_compensation::test_cli_write_example_csv` | #169 `eaf94add` | Windows cwd |
| `test_operation_capability_registry::test_registered_operation_works` | #175 `0647df75` | stale test (Batch A) |
| `test_ibg_intake_gate::test_permissive_gate_tolerates_bypass_attempts` | #175 `0647df75` | stale test (Batch A) |
| `test_artifact_constitutional_adapter::test_poor_topology_downgrades_to_sandbox` | #172 `feef5161` | **real production defect** (Batch C) |
| `test_morphology_harvest_json_serialization::test_e2e_result_to_dict_serializes` | #172 `feef5161` | **real production defect** (Batch C) |
| `test_outline_reconstructor::test_concave_arc_direction` | #172 `feef5161` | **real production defect** (Batch C) |
| `test_ibg_morphology_primitives::test_classify_lower_bout_point` | #176 `53bbf1a2` | argmax fix (#12) |
| `test_ibg_constitutional_integration::test_rejected_candidate_stays_blocked` | #176 `53bbf1a2` (production code; no test-file edit) | **real fix** — wire `REJECT`→`REJECTED` (#7) |
| `test_body_export_bridge::test_export_without_ibg_context` | production code; no test-file edit since `c41fc656` | resolved by non-test fix |
| `test_rmos_runs_e2e::test_runs_index_with_filters` | production code; no test-file edit since `c41fc656` | resolved by non-test fix |

The bulk maps onto the api-verify standing-failures triage (#169/#172/#175/#176), plus the
cluster-specific closes (#138/#160/#161) and the C2 / geometry-authority work (#158/#182/#193).
Three singletons had **no test-side edit** since the snapshot — meaning they were fixed by
**production-code** changes, the strongest kind of resolution.

## 5. Routing of residuals (do not absorb into 015)

- **Structural endpoint debt** (1181 routes, consolidation) is a *separate real item* →
  **CI-RED-016** (stays OPEN). Closing 015 (test failures) must not absorb 016 (route sprawl).
- **Canonical-authority migration follow-up** (process-approved factory rollout, strict-RED
  timing for legacy references) → **GOV-CONVERGE-007** (stays OPEN; 007-A items 1 & 2 CLOSED).
  015-H's *governance* dependency is resolved by the C2 ratification; the ongoing *migration*
  is its own tracked lane.

## 6. Verdict

CI-RED-015 (and sub-item 015-H) close as **test-suite reconciliation complete**: the 43
recorded failures run and pass on `13aabe4f`, each traceable to the PR/mechanism that
resolved it, none suppressed. This is a re-witness, not new implementation — it proves the
work already landed and reconciles the ledger to CI. Remaining board items are the genuine
residuals: CI-RED-016 (endpoint consolidation) and CI-RED-021 (enforcement, partial).

---

### Appendix — reproduction

Recover the 43: `gh run view 27630309072 --log-failed | grep -oE "FAILED [^ ]+::[^ ]+"`.
Re-run on a clean worktree off `origin/main`:
`python -m pytest <17 files> -rsxX -v` from `services/api`. Expect 464 passed / 1 unrelated skip.
Aggregate CI witness: runs `28755048990` (Core CI) + `28755048968` (API Tests) on `13aabe4f`.
