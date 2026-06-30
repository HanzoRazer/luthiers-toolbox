# api-verify / Core CI standing failures — triage

**Date:** 2026-06-29
**Source:** `api-verify` run `28359305343` on `main` (`0daeab14`) — `15 failed, 7686 passed, 113 skipped`.
**Method:** read-only parallel triage (6 Explore agents, one per cluster) over the test + the code each exercises, with `git log`/`blame` for provenance.

**Context:** these 15 were masked for ~8 commits by the `#163` pytest-collection crash (radon `sys.exit` at import). After `#166` fixed collection and rebaselined the endpoint ratchets, and `#168` fixed degraded-boot readiness, these are the residual standing reds. None are caused by the CI-plumbing chain (#163/#164/#166/#168); all predate it.

## Matrix

| # | Test | Class | Effort | Root cause → fix |
|---|------|-------|--------|------------------|
| 1 | `cam/test_drilling_intent_migration::test_legacy_routes_unchanged` | Stale-test | Quick | `{r.path for r in app.routes}` hits FastAPI 0.137 `_IncludedRouter` wrappers (no `.path`) → add `isinstance(r, APIRoute)` guard (the `app/main.py` convention) |
| 2 | `cam/test_pocketing_intent_migration::test_registration_and_parity` | Stale-test | Quick | Same as #1 → same guard |
| 3 | `mrp_spine_verification/test_morphology_spine_e2e::test_dreadnought_ibg_defaults_spine_flow` | Stale-test | Quick | `/api/body/solve-from-landmarks` gained mandatory `Depends(get_current_principal)` in IBG-2B (`70a0d3ee`); unauth `TestClient` → 401 → send `x-user-role`/`x-user-id` headers |
| 4 | `…::test_landmark_only_solve_spine_flow` | Stale-test | Quick | Same 401 → same |
| 5 | `…::test_ibg_metadata_does_not_override_boe_edits` | Stale-test | Quick | Same 401, no status-guard → `KeyError: outline_points` → auth headers + add `== 200` guard |
| 6 | `test_artifact_constitutional_adapter::test_poor_topology_downgrades_to_sandbox` | **Real bug** | Quick | `artifact_body_evidence_adapter.py:561` writes phantom `authority._current_state` (real field is `current_state`) → sandbox downgrade silently no-ops, stays `ADVISORY_CANDIDATE` → use real `.transition(SANDBOX_EXPERIMENTAL, …)`; fix same poke in `test_ibg_intake_gate.py:69` |
| 7 | `test_ibg_constitutional_integration::test_rejected_candidate_stays_blocked` | **Real bug** | **Decision** | `BodyEvidenceCandidate.record_review` propagates only APPROVE; a human REJECT leaves authority at `ADVISORY_CANDIDATE` (a later APPROVE could resurrect it) → wire REJECT→`REJECTED`, **or** relax the test if decoupling is intended |
| 8 | `test_ibg_intake_gate::test_permissive_gate_tolerates_bypass_attempts` | Stale-test | Quick | Test approves (clears `_review_required`) *before* the "bypass" → guard never fires, counter 0 (product is self-consistent) → reorder test to attempt bypass pre-approval |
| 9 | `test_morphology_harvest_json_serialization::test_e2e_result_to_dict_serializes` | **Real bug** | Quick | `e2e_spine_runner.py:27` imports `get_blueprint_adapter`/`get_photo_adapter` — neither exists; **module dead-on-import since #17** (`d8bc9ade`) → `from .adapters import get_phase4_adapter as get_blueprint_adapter`; drop unused `get_photo_adapter` |
| 10 | `test_saddle_compensation::test_cli_write_example_csv` | Hygiene | Quick | Hardcoded `cwd="C:/Users/thepr/…/services/api"` in test:559 → fails on Linux CI → `cwd=str(Path(__file__).resolve().parents[1])` |
| 11 | `test_outline_reconstructor::test_concave_arc_direction` | **Real bug** | Quick\* | `OutlineReconstructor._generate_arc` forces sweep from the `concave` flag, not geometry → traverses the major arc (midpoint `+41.59` vs intended `−2.4`). Convex arcs share the latent defect (masked by a `!= 0`-only test) → derive sweep from `arc_mid` (pick the minor arc) |
| 12 | `test_ibg_morphology_primitives::test_classify_lower_bout_point` | **Real bug** | **Decision** | Body-spanning zones + no x-gating on `centerline`/`bridge_region` → after normalization **no positional zone can exceed 0.5** (primary zone is still correct) → x-gate those zones, **or** relax the `> 0.5` threshold (weighting policy) |
| 13 | `test_rmos_runs_e2e::test_runs_index_with_filters` | Hygiene | Quick | Fixtures reset `runs_v2.store._default_store`, but the live singleton is `store_api._default_store` → stale store leaks foreign runs (`3 ≠ 1`); filter logic is correct → reset the actual singleton |
| 14 | `cam/test_operation_capability_registry::test_registered_operation_works` | Stale-test | Quick | 7C `validate_translator_registry` (`3fabb35b`) rejects the fixture's synthetic `translator_id="test_translator"` → translator stage red → use a registered id (`"dxf_r12"`) |
| 15 | `test_body_export_bridge::test_export_without_ibg_context` | Hygiene | Quick | `POST /api/export/body-outline` is `@limiter.limit("10/hour")` (in-memory singleton keyed by IP; `TestClient` = fixed IP, never reset between tests). This is the 11th `/body-outline` POST in the session → real `429` → reset limiter between tests / `RATE_LIMIT_ENABLED=0` in test env |

\* **#11** is a small change but affects convex arcs too — verify against the whole arc-reconstruction test set.

## Classification summary
- **7 stale-test + 3 hygiene = 10 test-only fixes** (no product behavior change).
- **5 real product issues:** 3 quick code fixes (#6, #9, #11) + 2 needing a product decision (#7, #12).

## Cross-cutting
- **#1–#2** share one root cause (FastAPI 0.137 `_IncludedRouter`); **#3–#5** share one (IBG-2B auth gate).
- **#13 and #15 are the same class** — module-level singletons (RMOS store, rate-limiter) with no per-test reset leaking across the session. One autouse conftest reset pattern fixes both; the limiter reset also likely stabilizes the IBG-2B auth tests.
- **#6, #7, #9, #12** live in IBG / morphology-harvest code that is governance-prep / R&D (`BLOCKED_PROVENANCE` posture). Fixing them buys honest green CI, not a shipping feature. **#11** (outline-reconstructor geometry) is the closest to a user-facing path (feeds DXF/CAM) and the most worth fixing on merit.

## Suggested batching (clears 13/15 with no decisions)
- **PR A — stale-test sweep** (test-only): #1, #2, #3, #4, #5, #8, #14.
- **PR B — test isolation** (conftest/fixtures): #10, #13, #15 (limiter + store-singleton resets, path fix); likely de-flakes other suites too.
- **PR C — real quick bugs** (product code): #6, #9 (trivial, contained) and #11 (geometry; separate commit, verify arc suite).
- **Open decisions (no PR until decided):**
  - **#7** — should a human REJECT lock authority to `REJECTED` (enforce "no resurrection"), or is the review decision intentionally decoupled from authority state?
  - **#12** — should the zone classifier x-gate centerline/bridge zones so a clear lower-bout point scores `> 0.5`, or is fuzzy multi-zone overlap intended (relax the test)?

After A + B + C: `api-verify` / Core CI go from **15 → 2** reds, both parked on explicit product decisions rather than unknowns.
