# CI-RED-016-C — Legacy DXF Export Cluster Disposition

**Date:** 2026-07-07
**Lane:** CI-RED-016 endpoint consolidation
**Base commit:** `ba3c8565` (current `origin/main`)
**Status of CI-RED-016:** OPEN (this slice calibrates the map and records a disposition; it does not close the lane)

---

## Purpose

CI-RED-016-B materialized the endpoint consumer map. This is the first *disposition*
step: pick one narrow candidate cluster from that map, correct the evidence for it,
and record a retain / defer / migrate decision — **without deleting, renaming, or
unmounting any endpoint.**

This packet does that for the first candidate: the **legacy DXF export compatibility
surface** (`/exports/*`).

---

## Cluster

**Name:** Legacy DXF export compatibility surface
**Router:** `services/api/app/routers/legacy_dxf_exports_router.py`
**Lane in map:** `legacy_migration`

Endpoints in cluster (all six `/exports/*` operations):

| Method | Path |
|--------|------|
| POST | `/exports/polyline_dxf` |
| POST | `/exports/biarc_dxf` |
| GET | `/exports/dxf/health` |
| GET | `/exports/history` |
| GET | `/exports/history/{entry_id}` |
| GET | `/exports/history/{entry_id}/file/{filename}` |

---

## Why the map needed correcting first

The CI-RED-016-B scanner (`services/api/scripts/build_endpoint_consumer_map.py`)
recognized endpoint references only under the roots `/api`, `/health`, `/ws`, and
`/instrument`, and only when the path literal immediately followed the opening quote.
The legacy export surface is mounted at `/exports` (no `/api` prefix), and its frontend
consumer calls it through a template literal with a variable base
(`` `${API_BASE}/exports/polyline_dxf` ``). Both facts made the cluster invisible to the
scan, so all six endpoints were reported `no_first_party_consumer_found` even though three
of them have a real product consumer.

CI-RED-016-C fixes the scanner conservatively:

- Adds `/exports` to the recognized endpoint roots (root-relative literals).
- Recognizes the template-base suffix form (`` `${BASE}/exports/...` ``) **for the
  `/exports` surface only**.

The template-base blind spot also affects `/api` routes, but generalizing the fix there
would reclassify ~13 unrelated `/api` endpoints and widen this PR beyond the legacy
export cluster. That generalization is intentionally split into a follow-up (see below);
this PR stays surgical.

---

## Consumer evidence (regenerated map, base `ba3c8565`)

### Product-used routes — real frontend consumers

| Endpoint | Primary class | Primary evidence |
|----------|---------------|------------------|
| `POST /exports/polyline_dxf` | `frontend_product` | `packages/client/src/utils/curvemath_dxf.ts` (`downloadOffsetDXF`) |
| `POST /exports/biarc_dxf` | `frontend_product` | `packages/client/src/utils/curvemath_dxf.ts` (`downloadBiarcDXF`) |
| `GET /exports/dxf/health` | `frontend_product` | `packages/client/src/utils/curvemath_dxf.ts` (`checkDXFHealth`) |

These three are corroborated by additional `docs_only` / `ci_governance` / `test_only`
references (governance matrix, the map artifacts themselves, and the builder's regression
test), but the **decisive** evidence is the first-party frontend helper.

### History routes — no first-party product/runtime consumer found

| Endpoint | Primary class |
|----------|---------------|
| `GET /exports/history` | `no_first_party_consumer_found` |
| `GET /exports/history/{entry_id}` | `no_first_party_consumer_found` |
| `GET /exports/history/{entry_id}/file/{filename}` | `no_first_party_consumer_found` |

No frontend, CI, or docs string reference calls these three. **This is review evidence,
not deletion authority** — absence of a first-party string reference is not proof that no
consumer (external caller, manual tooling, runtime integration) exists.

### CI coverage (whole cluster)

`.github/workflows/api_dxf_tests.yml` exercises the legacy DXF export routes in CI, so the
cluster has automated behavioral coverage independent of the frontend helper.

### Governance posture

- `docs/governance/LEGACY_EXPORT_EXEMPTION_POLICY.md` — `app.routers.legacy_dxf_exports_router`
  is classified `legacy_api_compat`, **sunset `2026-09-01`**.
- `docs/governance/EXPORT_PATH_MIGRATION_MATRIX.md` — router marked `LEGACY`, priority `P3`,
  exemption `EXEMPT`.

---

## Disposition

**RETAIN for now as `legacy_api_compat`. Do not delete, rename, redirect, or unmount in
CI-RED-016-C.**

- The three product-used routes have real frontend consumers; removing them breaks the
  client DXF export helper.
- The three history routes lack a first-party string consumer, but that is triage
  evidence only — not disposal authority. They stay mounted.
- Revisit the cluster at or before the recorded **`2026-09-01`** sunset date. This PR does
  **not** change that sunset date.

---

## Follow-up candidates (not this PR)

1. **Deprecation headers.** The exemption policy requires a deprecation signal for
   `legacy_api_compat` endpoints. Adding explicit deprecation response headers to the
   `/exports/*` routes is a separate, owner-approved change (dev order defers it here).
2. **Replacement `/api/export/...` mapping.** If product decides to migrate off the legacy
   surface, add a governed replacement route and a client migration guide before
   `2026-09-01`.
3. **History-endpoint audit.** Retire the three `history` endpoints only after external /
   CI / client usage is audited separately — no-first-party-string ≠ no-consumer.
4. **Generalize template-base matching to `/api`.** The scanner improvement that recognizes
   `` `${BASE}/api/...` `` template fetches is real and strictly better (it removes ~7
   false `no_first_party_consumer_found` classifications from genuine CI/frontend
   consumers). It is split out of this PR to keep CI-RED-016-C scoped to the legacy export
   cluster; it should land as its own reviewed consumer-map improvement.

---

## Safety statement

- Reachability evidence is not disposal authority.
- No first-party string evidence is **not** proof of no consumer.
- CI-RED-016 remains **OPEN**. This slice records one cluster's disposition; it does not
  close the lane or change any route/router baseline.
