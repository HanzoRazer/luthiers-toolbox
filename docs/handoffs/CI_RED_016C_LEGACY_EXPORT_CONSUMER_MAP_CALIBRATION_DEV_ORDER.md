# CI-RED-016-C Legacy Export Consumer-Map Calibration Dev Order

Status: Dev-ready handoff
Date: 2026-07-07
Base: current `origin/main` observed as `acadef99`; CI-RED-016-B map generated from `706f910c`
Lane: CI-RED-016 endpoint consolidation

## Purpose

Turn the first CI-RED-016-B consumer-map candidate into a safe, narrow consolidation decision.

The initial candidate cluster is the legacy DXF export surface:

- `POST /exports/polyline_dxf`
- `POST /exports/biarc_dxf`
- `GET /exports/dxf/health`
- `GET /exports/history`
- `GET /exports/history/{entry_id}`
- `GET /exports/history/{entry_id}/file/{filename}`

The CI-RED-016-B map currently classifies these six endpoints as `no_first_party_consumer_found`, but grounding found that classification is incomplete: `packages/client/src/utils/curvemath_dxf.ts` directly calls three of these routes through template literals such as `${API_BASE}/exports/polyline_dxf`.

Therefore CI-RED-016-C is not an endpoint-removal PR. It is a map-calibration and disposition PR:

1. Fix the consumer-map scanner so legacy `/exports/*` route literals are recognized.
2. Regenerate the machine-readable and Markdown endpoint consumer map.
3. Add a small disposition packet for the legacy DXF export cluster.
4. Keep all routes mounted and behavior unchanged.

## Grounding

Source artifacts:

- `services/api/metrics/endpoint_consumer_map.json`
- `docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md`
- `services/api/scripts/build_endpoint_consumer_map.py`
- `services/api/tests/test_endpoint_consumer_map_builder.py`
- `services/api/app/routers/legacy_dxf_exports_router.py`
- `packages/client/src/utils/curvemath_dxf.ts`
- `docs/governance/LEGACY_EXPORT_EXEMPTION_POLICY.md`
- `docs/governance/EXPORT_PATH_MIGRATION_MATRIX.md`

Current map summary:

- Mounted endpoint operations: 1132
- Static decorators: 1181
- Mounted-vs-static gap: 49
- Endpoints with no first-party consumer found: 293
- `legacy_migration` no-consumer bucket: 6

Important finding:

`build_endpoint_consumer_map.py` uses an endpoint-literal regex scoped to `/api`, `/health`, `/ws`, and `/instrument`. It omits the mounted legacy namespace `/exports`, and it does not normalize template-prefix fetches like `${API_BASE}/exports/polyline_dxf` into `/exports/polyline_dxf`. That makes the legacy export cluster look consumer-free even though the frontend DXF helper calls it.

Existing governance posture:

- `docs/governance/LEGACY_EXPORT_EXEMPTION_POLICY.md` marks `app.routers.legacy_dxf_exports_router` as `legacy_api_compat`.
- Sunset date is recorded as `2026-09-01`.
- `docs/governance/EXPORT_PATH_MIGRATION_MATRIX.md` marks the router as `LEGACY`, priority `P3`, exemption `EXEMPT`.

## Decisions

1. Scope is map correction plus disposition, not route removal.
2. `/exports/*` is a valid mounted namespace and must be included in consumer detection.
3. Template-literal fetches with a variable base URL should count as first-party consumer evidence when the path suffix is static.
4. Absence of first-party consumers remains triage evidence only, never deletion authority.
5. Existing legacy export behavior, request schemas, response formats, and history storage are unchanged.
6. Do not change the 2026-09-01 sunset date in this PR.
7. Do not migrate this router to `/api/...` in this PR.
8. Do not reduce endpoint count or router count in this PR. This is the first safe consolidation decision: retain/defer the legacy cluster with corrected evidence.

## Non-Goals

- No endpoint deletion.
- No endpoint rename.
- No redirect behavior.
- No deprecation headers unless a separate owner decision explicitly requests them.
- No DXF writer migration.
- No changes to `legacy_dxf_exports_router.py` behavior.
- No router-count baseline change.
- No claim that CI-RED-016 is closed.

## File-by-File Patch Plan

### `services/api/scripts/build_endpoint_consumer_map.py`

Update endpoint-literal extraction.

Required behavior:

- Recognize normal literals beginning with `/exports`.
- Recognize static suffixes inside template literals where the path follows an interpolated base, for example:
  - `${API_BASE}/exports/polyline_dxf`
  - `${API_BASE}/exports/biarc_dxf`
  - `${API_BASE}/exports/dxf/health`
- Return the normalized path suffix, not the base expression.
- Keep the extractor conservative. Do not start treating arbitrary root-relative assets as API endpoints.
- Update the methodology text emitted into the JSON and Markdown artifacts so it names supported mounted roots, including `/exports`.

Suggested implementation shape:

- Replace the single regex with either:
  - one regex that supports both root-relative and template-base path forms, or
  - two small regexes, one for root-relative literals and one for template-base suffixes.
- Prefer a named constant such as `ENDPOINT_ROOTS = ("api", "health", "ws", "instrument", "exports")` if it keeps the regex readable.
- Preserve sorted, unique output from `extract_endpoint_literals`.

### `services/api/tests/test_endpoint_consumer_map_builder.py`

Add focused regression coverage.

Required tests:

- `/exports/polyline_dxf` is extracted from a normal quoted string.
- `${API_BASE}/exports/biarc_dxf` is extracted as `/exports/biarc_dxf`.
- `${API_BASE}/exports/dxf/health` is extracted as `/exports/dxf/health`.
- Existing `/api`, `/health`, and template `/api/rmos/runs/${runId}` cases still pass.
- A non-endpoint asset path such as `/assets/logo.svg` is not extracted.

If practical, add a matching test:

- `reference_matches_endpoint("/exports/history/abc", "/exports/history/{entry_id}")` returns true.

### `services/api/metrics/endpoint_consumer_map.json`

Regenerate with the corrected scanner.

Expected changes:

- The six legacy export endpoints should no longer be treated as map-blind by the extractor.
- At minimum:
  - `POST /exports/polyline_dxf` has `frontend_product` evidence from `packages/client/src/utils/curvemath_dxf.ts`.
  - `POST /exports/biarc_dxf` has `frontend_product` evidence from `packages/client/src/utils/curvemath_dxf.ts`.
  - `GET /exports/dxf/health` has `frontend_product` evidence from `packages/client/src/utils/curvemath_dxf.ts`.
- Workflow and docs references may also attach `ci_governance` or `docs_only` evidence to the cluster. That is acceptable.
- Summary counts will change. Do not hand-edit them.

### `docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md`

Regenerate with the corrected scanner.

Required review:

- The methodology notes should no longer imply only `/api`-style endpoint literals are covered.
- The `legacy_migration` no-consumer count should reflect regenerated evidence.
- The sample review targets should not present the legacy DXF export routes as consumer-free if evidence exists.

### `docs/audit/CI_RED_016C_LEGACY_EXPORT_CLUSTER_DISPOSITION.md`

Add a short disposition packet for the selected cluster.

Required contents:

- Cluster name: Legacy DXF export compatibility surface.
- Endpoints in cluster: all six `/exports/*` operations.
- Consumer evidence:
  - Frontend product calls for polyline, biarc, and health.
  - CI workflow coverage from `.github/workflows/api_dxf_tests.yml`.
  - Governance exemption policy and migration matrix references.
- Disposition:
  - Retain for now as `legacy_api_compat`.
  - Do not delete or rename in CI-RED-016-C.
  - Revisit at or before the recorded 2026-09-01 sunset date.
- Follow-up options:
  - Add explicit deprecation headers in a later PR.
  - Add replacement `/api/export/...` route mapping if product needs migration.
  - Retire history endpoints only after external/CI/client usage is audited separately.
- Safety statement:
  - Reachability evidence is not disposal authority.
  - No first-party string evidence is not proof of no consumer.

### `SPRINTS.md`

Add a short CI-RED-016-C progress note under the CI-RED-016 detail block.

Suggested wording:

```text
CI-RED-016-C (2026-07-07): first candidate cluster selected from the map: legacy DXF `/exports/*` compatibility surface. Grounding found the 016-B scanner missed `/exports` template-literal frontend consumers, so this slice calibrates the map and records a retain/defer disposition rather than deleting routes. CI-RED-016 remains OPEN.
```

Do not close CI-RED-016.

### `.cbsp21/patches/ci-red-016c-legacy-export-map-calibration.json`

Add a per-PR manifest covering only the files above.

Expected paths in scope:

- `services/api/scripts/`
- `services/api/tests/`
- `services/api/metrics/`
- `docs/audit/`
- `SPRINTS.md`
- `.cbsp21/patches/`

Risk level: low to medium.

Reason: no product behavior change, but the generated audit artifact changes endpoint-consumer classifications and will influence future consolidation decisions.

## Utility Notes

Main utility:

```text
services/api/scripts/build_endpoint_consumer_map.py
```

Expected invocation from `services/api`:

```text
python scripts/build_endpoint_consumer_map.py --write
python scripts/build_endpoint_consumer_map.py --check
```

If the actual CLI differs, inspect `--help` and use the existing documented flags. Do not rewrite the utility interface unless necessary.

## Test Cases

Run focused tests first:

```text
pytest tests/test_endpoint_consumer_map_builder.py -q
```

Required assertions:

- Literal extraction includes `/exports` roots.
- Template-base extraction normalizes `${API_BASE}/exports/...` to `/exports/...`.
- Existing `/api` and `/health` extraction still works.
- Non-endpoint root assets are ignored.
- Parameterized matching still handles `/exports/history/{entry_id}`.

Then run generated-artifact checks:

```text
python scripts/build_endpoint_consumer_map.py --check
```

Then run the relevant gates:

```text
python scripts/ci/check_cbsp21_patch_input.py
python scripts/ci/check_cbsp21_gate.py
```

If local command paths differ, use the existing CI commands as source of truth.

## Rollout Order

1. Create a fresh worktree from current `origin/main`.
2. Update `build_endpoint_consumer_map.py`.
3. Add/update tests in `test_endpoint_consumer_map_builder.py`.
4. Run the focused test file.
5. Regenerate `endpoint_consumer_map.json` and `CI_RED_016_ENDPOINT_CONSUMER_MAP.md`.
6. Inspect the six `/exports/*` endpoints in the regenerated JSON.
7. Add `CI_RED_016C_LEGACY_EXPORT_CLUSTER_DISPOSITION.md`.
8. Add the CI-RED-016-C note to `SPRINTS.md`.
9. Add the per-PR CBSP21 manifest.
10. Run focused tests and CBSP21 gates.
11. Open PR as `CI-RED-016-C: calibrate legacy export consumer map`.
12. Hold merge for review.

## Acceptance Criteria

- No endpoint behavior changes.
- No route count change.
- No router-count baseline change.
- `POST /exports/polyline_dxf` has frontend consumer evidence in the regenerated map.
- `POST /exports/biarc_dxf` has frontend consumer evidence in the regenerated map.
- `GET /exports/dxf/health` has frontend consumer evidence in the regenerated map.
- The disposition packet says retain/defer, not delete.
- `SPRINTS.md` records progress without closing CI-RED-016.
- Focused tests pass.
- CBSP21 gates pass.

## Stop and Ask

Stop before proceeding if:

- Any implementation requires deleting, redirecting, renaming, or unmounting an endpoint.
- The regenerated map shows large unexpected classification churn outside `/exports` and obvious newly recognized `/exports` references.
- The scanner must become broad enough to treat arbitrary root paths as endpoints.
- The legacy export sunset date is changed.
- The PR would need to alter frontend DXF behavior.
- The PR would need to change branch protection, CODEOWNERS, or governance settings.

## Follow-Up Candidates

After CI-RED-016-C lands:

- CI-RED-016-D: choose a second candidate from the corrected no-consumer map.
- Legacy export follow-up: add deprecation headers or a replacement route guide before 2026-09-01.
- Consumer-map follow-up: support generated SDK route references if future candidates reveal another blind spot.

