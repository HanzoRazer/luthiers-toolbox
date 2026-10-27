# Spot check and continuation pass (2026-10-26)

Discovery used four read-only search agents. Their findings were model output,
so before and after the first commit every load-bearing claim was re-checked
by direct reads in this session. This file records that second pass.

## 1. Citation spot check: 26 of 26 hold

A script read each cited range at `02032884` and searched it for the claimed
token. **0 misses.** These checks confirm *location*; three claims needed
*meaning* and were read directly:

| Claim | Method | Result |
|---|---|---|
| `WorkflowSession.approve()` has no role check (SOL-E05) | Read state_machine.py:295-317 | Confirmed. It checks feasibility present, RED override and min score. `actor: ActorRole` is recorded, never authorized. |
| `/estimate/quote` has no client caller (SOL-B01) | `grep -rn "estimate/quote" packages/client/src` | Confirmed: 0 |
| CNC-PS product records are unconsumed (SOL-C07) | Traced `tests/workflows/*`, then `business/workflows/loading.py` | **Refuted for `guitar_product_definition_v1`.** Corrected below. |

Checked ranges:
- **A rows:** store.py 195-232; JobCreationWizard.vue 280-295; REMEDIATION_EXECUTIVE_SUMMARY 205-215; projects/router.py 244.
- **B rows:** business/router.py 80; estimatorStore.ts 18-30; cost_attribution/models.py.
- **C rows:** bom_service.py 175-190; business/schemas.py 84-91; strat.py 25-35; pocket_generator.py 20-30; InventoryView.vue 12-30; archtop discovery 295-320.
- **D rows:** batch_router_schemas.py 200-220; feedback/schemas.py 33-96; system_manifest.py 49.
- **E rows:** proposal_v1.py; beginner_proposal_harness.py; router/index.ts 465; InstrumentHubShell.vue 290-312; state_machine.py 290-300 and 450-460; PRODUCTION_SHOP_EVALUATION 135-198; instrument_project.py 583-587 and 757-761.

## 2. Correction: SOL-C07

- **Before:** the row cited `schemas/products/instrument_product_v2.schema.json`. It said no quote or job references a product record and no kit revision is pinned. It was classed BUILT_DISCONNECTED / NONE.
- **Found:** the CNC-PS job-quote pipeline loads a *different* product schema, `guitar_product_definition_v1`:
  - It loads the record as role `product` (business/workflows/loading.py:49, :385).
  - It refuses a `product_id` mismatch (:404).
  - It records the record in the job manifest's `sources[]` with role, record_id, snapshot_ref and sha256 (job_quote_manifest_v1.schema.json:28).
- **After:** the row now covers CNC-PS product records as one subsystem. Its primary path is `guitar_product_definition_v1.schema.json`, classed LIVE_LIBRARY / PARTIAL / COMMERCIAL, still OWNER_RULING_REQUIRED (R3). The sibling `instrument_product_v2` still has 0 consumers.

Effects:
- **MVS S2:** BUILD → **ADAPT**. A job can already pin a reusable *configuration* by content. A BOM-style kit (quantities, units, substitutions) is still missing (SOL-C08).
- **JOB_IDENTITY_MAP:** new PROVEN link, CNC-PS job → product configuration (by content).
- **Counts:** LIVE_LIBRARY 3→4, BUILT_DISCONNECTED 9→8, COMMERCIAL 4→5, NONE 21→20. MVS steps: ADAPT 2→3, BUILD 6→5.
- **The recommendation is unchanged.** The missing seam (S7–S9 operation record) is untouched by this correction.

**Why it was missed:** the first pass grepped `business/` for the schema
*name* `instrument_product_v2`. The pipeline references products through the
role table and `product_ref` instead. A name search cannot prove a negative
consumer; tracing the test fixtures into the loader did.

## 3. R4 severity: latent, not live

The first pass left open whether any project G-code route passes readiness.
Answered:
- Of the 10 records in the readiness registry, only `les_paul_body` is `GOVERNED_BY_ASSET_AUTHORITY` (generator_readiness.py:242). That state is a delegation, not an authorization. All others are BLOCKED or REVIEW_REQUIRED.
- On that route the sequence is:
  1. `_readiness_gate` delegates
  2. `_parse_design_state_or_422` checks the self-asserted status, which only refuses `draft`
  3. `LesPaulBodyGenerator.from_project` calls `require_manufacturing_authority` (lespaul_body_generator.py:45)
- A read-only call of `resolve_manufacturing_authority` on `instrument_geometry/body/dxf/electric/LesPaul_CAM_Closed.dxf` returned `BLOCKED, registered=True, disposition=UNADJUDICATED`. The reason is a quarantine record from the owner ruling of 2026-09-14.

**Conclusion:** no project G-code route reaches emission today, so R4 is
latent. It becomes the only project-level gate when that DXF is cleared.
R4 should be ruled on before that happens.

## 4. CI on PR #462: the red is an existing flake, not this diff

The first CI run had 4 red jobs (API Tests ×2, api-verify ×2) plus the 2 Core
CI Summary jobs that aggregate them. Every failure is in one file:

| Run / job | Failing tests | Totals |
|---|---|---|
| 40437007694 / API Tests | `test_sqlite_art_stores.py::TestSQLiteArtPresetsStore::test_search_by_name` | 1 failed, 9598 passed |
| 40437040091 / API Tests | `…::test_list_by_lane`, `…::test_search_by_name` | 2 failed, 9597 passed |
| 40437007717 / api-verify | `…::test_search_by_name` | 1 failed, 9888 passed |
| 40437040142 / api-verify | `…::test_search_by_name` | 1 failed, 9888 passed |

**Cause:** `services/api/app/stores/sqlite_art_presets_store.py:134` builds the
primary key as `f"{lane}_preset_{int(time.time() * 1000)}"`. The tests create
two presets in the same lane back to back, so a same-millisecond call raises
`UNIQUE constraint failed: art_presets.id`. The file was last changed in
`8d91c4c7` (April 2026). `main` passed at `02032884` by timing.

This flake is not recorded in `SPRINTS.md`, `docs/ci/` or `docs/investigations/`.
It is **not fixed here**, because this order permits no production change. It
needs its own CI-RED entry. The failed jobs were re-run once to obtain a clean
witness.
