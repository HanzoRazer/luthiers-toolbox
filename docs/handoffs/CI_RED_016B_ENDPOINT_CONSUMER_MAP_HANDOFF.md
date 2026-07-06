# CI-RED-016-B Endpoint Consumer Map Handoff

Date: 2026-07-05
Status: Dev-ready handoff
Base observed: `origin/main` at `706f910c`
Lane: CI-RED-016 / Endpoint consolidation

## One-line objective

Turn CI-RED-016 from "1181 routes scary" into a structured, evidence-backed consumer map without deleting, renaming, consolidating, or re-baselining any endpoint.

## Current ground truth

The old API-test red surface is no longer the blocker:

- CI-RED-015 is CLOSED by #200.
- Latest green witnesses cited by #200:
  - API Tests run `28755048968`
  - Core CI run `28755048990`
- CI-RED-004 is CLOSED with `Fence Checks (Blocking)` required.
- CI-RED-021 remains intentionally PARTIAL/OPEN pending reviewer topology.

CI-RED-016 remains open:

- Static endpoint audit still records `total=1181`, `baseline=942`, `delta=+239`.
- The known route-count pressure is structural, not an active failing test-suite red.
- CI-RED-016-A already landed the manifest-discipline bleed-stop: net-new unmanifested router files now fail, but the known historical set is grandfathered.
- `docs/ROUTER_MAP.md` is stale; do not use it as source of truth.

Existing utilities and artifacts:

- `services/api/app/ci/inventory_endpoints.py` introspects mounted FastAPI/OpenAPI endpoints.
- `services/api/scripts/audit_endpoints.py` counts static `@router.*` decorators and writes `services/api/metrics/endpoint_audit_current.json`.
- `services/api/scripts/diff_endpoints_baseline.py` compares static endpoint growth against a historical baseline.
- `services/api/app/data/endpoint_truth.json` exists but is narrow/stale relative to the full mounted app.
- Frontend and SDK consumers live mainly under:
  - `packages/client/src/api/`
  - `packages/client/src/sdk/endpoints/`
  - `packages/client/src/**`
- Test consumers live under:
  - `services/api/tests/`
  - `packages/client/src/**/__tests__/`

## Scope

In scope:

- Build a deterministic endpoint consumer-map utility.
- Inventory mounted endpoints from the actual FastAPI app/OpenAPI, not only decorator text.
- Scan first-party consumers for endpoint literals and client wrappers.
- Classify endpoints by consumer evidence and lane.
- Produce a committed JSON map and a human-readable audit document.
- Update `SPRINTS.md` to record CI-RED-016-B completion, while keeping CI-RED-016 open.

Out of scope:

- Endpoint deletion.
- Endpoint rename.
- Router consolidation.
- Route-count baseline changes.
- Manifest baseline changes.
- CODEOWNERS/ruleset changes.
- Closing CI-RED-016.
- Treating "no first-party consumer found" as proof that an endpoint is safe to delete.

## Core Decisions

### Decision 1: Source of truth

Use live mounted FastAPI inventory as the endpoint source of truth.

Static decorator counts are still useful for debt context, but they can overcount or misrepresent mounted behavior because they do not resolve `include_router` composition.

Implementation resolution: generate from a pinned API environment (`requirements.txt`, FastAPI 0.137.x). Use `app.routes` as the primary source by flattening FastAPI 0.137 `_IncludedRouter` wrappers, then cross-check the resulting operation set against `app.openapi()`. Record the static-vs-mounted gap as a methodology note instead of silently dropping it.

### Decision 2: Consumer evidence classes

Every endpoint should receive one primary consumer class:

```text
frontend_product
frontend_sdk
backend_internal
test_only
ci_governance
docs_only
external_or_unknown
no_first_party_consumer_found
```

Important: `no_first_party_consumer_found` is a candidate label, not a deletion ruling.

### Decision 3: Endpoint lane classes

Every endpoint should also receive one lane class:

```text
mvp_runtime
cam_operation
cam_governance
authority_reference
rmos_runtime
art_studio
instrument_geometry
saw_lab
health_meta
legacy_migration
test_debug_dev
unknown
```

Lane class should be heuristic but explainable. Prefer prefix + router module + tags over guesswork.

### Decision 4: Preservation rule

Governance, audit, authority, provenance, and review endpoints must not be treated as dead merely because frontend code does not call them.

They may be low-frequency control-plane surfaces rather than product UI routes.

### Decision 5: Output is a map, not a verdict

The deliverable should produce follow-up candidates, not implementation changes.

The first implementation sprint after the map may pick one narrow family, such as legacy migration endpoints or duplicate CAM convenience wrappers, but that is not part of CI-RED-016-B.

## Structured Map Schema

The JSON output should be deterministic and shaped approximately like:

```json
{
  "schema": "ci_red_016_endpoint_consumer_map_v1",
  "base_commit": "706f910c",
  "endpoint_count": 0,
  "summary": {
    "by_consumer_class": {},
    "by_lane_class": {},
    "by_prefix_family": {}
  },
  "endpoints": [
    {
      "method": "GET",
      "path": "/api/example",
      "operation_id": "example",
      "tags": ["Example"],
      "router_module": "app.routers.example_router",
      "lane_class": "unknown",
      "consumer_class": "no_first_party_consumer_found",
      "consumer_hits": [
        {
          "kind": "frontend_product",
          "path": "packages/client/src/api/example.ts",
          "line": 12,
          "literal": "/api/example"
        }
      ],
      "notes": []
    }
  ],
  "follow_up_candidates": [
    {
      "family": "/api/example",
      "reason": "No first-party consumer found",
      "risk": "medium",
      "recommended_next_step": "manual owner review"
    }
  ]
}
```

Do not include a volatile timestamp in committed output unless the tests intentionally normalize it.

## File-by-file Patch Plan

### `services/api/scripts/build_endpoint_consumer_map.py`

Purpose: Generate the structured consumer map.

Implementation plan:

- Import the FastAPI app from the pinned API environment.
- Flatten FastAPI 0.137 `_IncludedRouter` wrappers from `app.routes` and collect mounted operations.
- Cross-check against `app.openapi()` for operationId/tags and record route-object/OpenAPI gaps.
- Capture method, path, operationId, tags, route name, router module, and router file.
- Scan consumer roots:
  - `packages/client/src/api`
  - `packages/client/src/sdk/endpoints`
  - `packages/client/src`
  - `services/api/tests`
  - `packages/client/src/**/__tests__`
  - `docs`
- Extract endpoint-like literals with conservative regexes:
  - `/api/...`
  - `/health`
  - `/openapi.json` only if explicitly needed
- Normalize path templates:
  - `{id}` and `${...}` dynamic segments should become wildcard/template markers.
  - Query strings should be stripped for matching but retained in consumer evidence.
- Match consumer literals to endpoints:
  - exact method-agnostic path match when method is unknown;
  - prefix/template match for dynamic calls;
  - unresolved literals stay in an `unmatched_consumers` section.
- Classify consumer hits by file root.
- Classify endpoint lanes by prefix, tags, and module path.
- Emit:
  - JSON map to `services/api/metrics/endpoint_consumer_map.json`;
  - Markdown summary to `docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md`.

Guardrails:

- Read-only inventory only.
- No endpoint registration changes.
- No route sorting based on filesystem order; sort output by `(path, method)`.
- Return non-zero only on tool errors, not because endpoints are unconsumed.

### `services/api/tests/test_endpoint_consumer_map_builder.py`

Purpose: Unit coverage for the builder's parsing and classification logic.

Test plan:

- endpoint literal extraction from `fetch`, `axios`, and `fetchJson` examples.
- query-string stripping.
- template/dynamic segment normalization.
- consumer-class classification by file path.
- lane-class classification by prefix/tag/module.
- deterministic output ordering.
- "no consumer found" is classified but not treated as a failure.

Keep tests fixture-based; do not import the full FastAPI app unless a thin smoke test is cheap and already reliable in CI.

### `services/api/metrics/endpoint_consumer_map.json`

Purpose: Machine-readable generated artifact.

Rules:

- Deterministic.
- Committed only after generation from current `origin/main`.
- Contains summary counts and endpoint rows.
- Must not contain absolute local paths.
- Must not contain timestamps unless normalized.

### `docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md`

Purpose: Human-readable map and next-step queue.

Required sections:

- Summary counts.
- Methodology.
- Consumer class definitions.
- Lane class definitions.
- Top endpoint families by count.
- Frontend/SKD-consumed families.
- Test-only families.
- Governance/audit/reference families to preserve.
- `no_first_party_consumer_found` candidates.
- Follow-up implementation candidates.
- Explicit non-goals.

Recommended table columns:

```text
Family | Endpoint count | Consumer class | Lane class | Evidence | Risk | Next action
```

### `SPRINTS.md`

Purpose: Record CI-RED-016-B completion without closing CI-RED-016.

Suggested text:

```text
CI-RED-016-B (2026-07-XX): Endpoint consumer map created. The 1181-route surface is now classified by mounted endpoint, first-party consumer evidence, and lane. This does not delete or consolidate routes; it creates the implementation queue for future CI-RED-016-C/D work.
```

### `.cbsp21/patches/ci-red-016b-endpoint-consumer-map.json`

Purpose: Per-PR CBSP21 manifest.

Scope only:

- `services/api/scripts/build_endpoint_consumer_map.py`
- `services/api/tests/test_endpoint_consumer_map_builder.py`
- `services/api/metrics/endpoint_consumer_map.json`
- `docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md`
- `SPRINTS.md`
- `.cbsp21/patches/ci-red-016b-endpoint-consumer-map.json`

## Utilities

Endpoint inventory:

```powershell
cd services/api
python -m app.ci.inventory_endpoints --out metrics/live_endpoints.json
```

Static decorator audit:

```powershell
cd services/api
python scripts/audit_endpoints.py
python scripts/diff_endpoints_baseline.py
```

Consumer scans:

```powershell
rg -n '["''](/api/[^"'']+)' packages/client/src services/api/tests docs
rg -n 'fetch\\(|axios\\.|fetchJson\\(|api\\(' packages/client/src services/api/tests
```

Generated map:

```powershell
cd services/api
python scripts/build_endpoint_consumer_map.py --json metrics/endpoint_consumer_map.json --markdown ../../docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md
```

Validation:

```powershell
python -m json.tool services/api/metrics/endpoint_consumer_map.json
python -m pytest services/api/tests/test_endpoint_consumer_map_builder.py -q
python scripts/ci/check_cbsp21_patch_input.py --base origin/main --head HEAD
python scripts/ci/check_cbsp21_gate.py --changed-files <changed-files-list>
```

## Test Cases

### Test 1: Literal extraction

Input fixture:

```ts
fetch("/api/cam/sim/upload")
axios.post(`/api/cam/jobs/${jobId}/risk_timeline`)
fetchJson("/api/art/patterns?limit=10")
```

Expected:

- `/api/cam/sim/upload`
- `/api/cam/jobs/{dynamic}/risk_timeline`
- `/api/art/patterns`

### Test 2: Consumer class by root

Expected:

- `packages/client/src/api/foo.ts` -> `frontend_product`
- `packages/client/src/sdk/endpoints/foo.ts` -> `frontend_sdk`
- `services/api/tests/test_foo.py` -> `test_only`
- `docs/foo.md` -> `docs_only`

### Test 3: Lane class by prefix/module

Expected examples:

- `/api/cam/...` -> `cam_operation` or `cam_governance` depending on tags/module.
- `/api/cam/geometry-authority/...` -> `authority_reference`.
- `/api/rmos/...` -> `rmos_runtime`.
- `/health`, `/api/health`, `/_meta` -> `health_meta`.

### Test 4: No consumer found is non-failing

An endpoint with no hits should be emitted with:

```text
consumer_class = no_first_party_consumer_found
```

The script should exit zero.

### Test 5: Deterministic output

Repeated runs over the same fixtures should produce identical JSON and Markdown.

### Test 6: Unmatched consumer literals

If client code references a path not present in mounted endpoints, the output should include it under `unmatched_consumers` for follow-up.

Do not fail in CI unless the PR explicitly chooses to promote unmatched consumers to a gate later.

## Rollout Order

1. Create an isolated worktree from current `origin/main`.
2. Add the builder with fixture-only unit tests.
3. Run local unit tests.
4. Generate `endpoint_consumer_map.json` and the Markdown audit.
5. Review top families manually for obvious misclassification.
6. Update `SPRINTS.md` with CI-RED-016-B progress.
7. Add the CBSP21 manifest.
8. Run CBSP21 gates.
9. Open PR titled:

```text
docs(ci): CI-RED-016 endpoint consumer map
```

10. Merge only after CI passes.

## Stop-and-Ask Conditions

Stop and ask before proceeding if:

- The builder needs to change endpoint registration or app startup behavior.
- Mounted endpoint inventory fails because app import fails on current `main`.
- Consumer scan finds active frontend references to endpoints thought to be legacy/dead.
- The map suggests deleting or renaming any endpoint.
- The generated output is too large to review meaningfully.
- The route count differs materially from `1181` and the difference is not explained by mounted-vs-static methodology.
- A governance/authority endpoint appears unconsumed but carries review, provenance, C2, C24, RMOS, or audit semantics.

## Acceptance Bar

CI-RED-016-B is complete when:

- The repo contains a generated endpoint consumer map.
- The map distinguishes mounted endpoints from static decorator debt.
- Each endpoint has a consumer class and lane class.
- Frontend/SDK/test/governance/no-consumer buckets are summarized.
- The document identifies follow-up candidates for future consolidation.
- No endpoint behavior changes.
- CI-RED-016 remains open with a clearer next implementation queue.

## Recommended Follow-up After CI-RED-016-B

Pick one narrow CI-RED-016-C target from the map, such as:

- legacy/migration endpoints with no first-party consumer;
- duplicate CAM convenience wrappers with identical downstream implementation;
- test-only dev/probe endpoints;
- stale docs/SDK references to unmounted endpoints.

Do not start CI-RED-016-C until the map is reviewed.
