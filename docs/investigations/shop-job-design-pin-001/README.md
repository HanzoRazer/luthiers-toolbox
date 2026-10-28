# SHOP-JOB-DESIGN-PIN-001

Immutable LTB design snapshot pinned to a CNC-Production-Shop `job_id`.

| | |
|---|---|
| **Date** | 2026-10-28 |
| **Base** | `origin/main` `cc8e13ae` (merge of PR #464). SHOP-OPERATING-LOOP-RECOVERY-001 is an ancestor. |
| **Code** | `services/api/app/design_snapshots/` |
| **Status** | Draft library. No route. |

## What it is

`capture_design_snapshot` copies the dict from `serialize_design_state` into `ltb_design_snapshot` 1.0, binds the caller-supplied CNC `job_id` as `UNVERIFIED_EXTERNAL_REFERENCE`, and stores one immutable JSON file. A later design change is a new snapshot id and a new digest. The mutable project save path is untouched.

The source decision is `SOURCE_STATE.md`. Field rules are `CONTRACT.md`. What the snapshot cannot decide is `AUTHORITY_BOUNDARY.md`.

## Discovery

No canonical immutable design snapshot existed for the routed project. Rosette, art-studio, and RMOS design snapshots are other products. Open PRs #465 (shop-operation hardening) and #456 (validation policy) do not own this surface and were not edited.

CNC-Production-Shop `main` at `ef4d6e31` (read-only) has `CncJobQuoteManifestV1` and `CncJobQuoteManifestV2`. `sources[].role` does not include an LTB project or design snapshot. This package does not modify that repository. `fixtures/cnc_consumer_conformance.json` is a portable witness for a later consumer order.

## Limits

One writer per directory. Job verification waits for `SHOP-JOB-REFERENCE-RESOLVER-001`. No route, UI, quote, operation record, cost, CAM execution, or physical policy.

## Results

`pytest` of the design-snapshot suite, shop-operation records, project observation and artifact association, evidence-artifact contract, and OpenAPI: 136 passed. OpenAPI still loads 143 routers. Manufacturing inventory `--check` stayed at 239 candidates, live=1157. Complexity, file size, bare except, fence checker (2 passed), duplication (0 clone groups), and execution-class passed. No baseline was raised.

## Rerun

```bash
cd services/api
python -m pytest tests/design_snapshots tests/shop_operations tests/test_analyzer_project_observation.py tests/projects/test_project_artifact_association.py tests/physical_engineering/test_evidence_artifact_v1.py tests/test_openapi.py -q --no-cov
```

From the repo root:

```bash
python scripts/ci/check_cbsp21_gate.py --changed-files $(git diff --name-only origin/main...HEAD)
python scripts/ci/check_cbsp21_patch_input.py --base origin/main --head HEAD
```
