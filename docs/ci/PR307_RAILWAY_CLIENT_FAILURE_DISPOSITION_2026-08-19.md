# PR #307 — Railway `@luthiers-toolbox/client` failure disposition

**Date:** 2026-08-19  
**PR:** [#307](https://github.com/HanzoRazer/luthiers-toolbox/pull/307)  
**Status:** Railway green restored; Node 22 on this service blocked by Railway Metal

## Scoped risk assessment (review → action)

| Cited item | Disposition |
|------------|-------------|
| Railway client Build Failed (blocking) | **Fixed** by keeping `packages/client/Dockerfile` on `NODE_VERSION=20`. |
| Split `SPRINTS.md` ledger | **Deferred** (review cost; not required for Railway green). |
| README: `engines.node` SSoT | **Done**. |
| CI `npm run check:node` outside Docker | **Done** in `client_lint_build.yml`. |

## Root cause (bisected)

| Probe | Result |
|-------|--------|
| Shared-script COPY + `NODE_VERSION=22` (`c7cb9938`) | FAIL ~20s |
| Remove `engines.node` only | Still FAIL |
| Fresh PR environment recreate | Still FAIL |
| Restore `82d6c07d` Railway Dockerfile (`NODE_VERSION=20`) | **SUCCESS** |
| `NODE_VERSION=22` alpine, inline guard | FAIL ~20s |
| `NODE_VERSION=22` bookworm-slim | FAIL ~20s |

**Conclusion:** On the `@luthiers-toolbox/client` Railway service, **any `node:22-*` builder base fails before a healthy build completes**. `node:20-alpine` works. This is not a Vite/`VITE_*`/import-graph failure — local `vite build` and CI Buildx of the same tree are green.

## Fix retained on #307

- `engines.node`: `^20.19.0 || >=22.12.0` — Node 20 lane for Railway; Node 22+ lane for CI/`@supabase` preference
- `packages/client/Dockerfile`: `NODE_VERSION=20` (Railway entry point)
- Repo-root client Dockerfiles + `client_lint_build.yml`: Node **22** + `check-node-engine.mjs` / `npm run check:node`
- Drift spec: dependency coverage = at least one floor lane covers each dep; Railway Dockerfile exception documented

## Remaining debt (owner / Railway)

Railway Metal cannot currently run this service on Node 22 images. Prefer Node 22 when that unblocks; until then production client on Railway remains Node 20 (same as pre-PR `main`).

## Verification

- Local: `npm run check:node`; `nodeEngineFloor.spec.ts` 6 passed; `vite build` succeeds
- Railway bot: `@luthiers-toolbox/client` → Success after Node 20 restore
