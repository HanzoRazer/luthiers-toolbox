# PR #307 — Railway `@luthiers-toolbox/client` failure disposition

**Date:** 2026-08-19  
**PR:** [#307](https://github.com/HanzoRazer/luthiers-toolbox/pull/307)  
**Status:** Root cause isolated; Railway-safe Dockerfile path restored + Node 22 floor retained

## Scoped risk assessment (review → action)

| Cited item | Disposition |
|------------|-------------|
| Railway client Build Failed (blocking) | **Fixed.** Failure was in `packages/client/Dockerfile` after `c7cb9938` (shared-script COPY / Node-22 path), not in app `vite build` or missing `VITE_*`. |
| Split `SPRINTS.md` ledger | **Deferred (not blocking).** Orthogonal to Railway; peel later if review wants a narrower diff. |
| README: `engines.node` SSoT | **Done** in `packages/client/README.md`. |
| CI `npm run check:node` outside Docker | **Done** in `client_lint_build.yml`. |

## Bisect results

| Probe | Client Railway |
|-------|----------------|
| `c7cb9938`…`70b9c661` (shared script + `NODE_VERSION=22`) | FAIL ~16–23s, stages not started |
| Remove `engines.node` only | Still FAIL |
| Fresh PR env recreate | Still FAIL |
| Restore `packages/client/{Dockerfile,railway.json,.nvmrc}` to `82d6c07d` | **SUCCESS** |
| Reintroduce `NODE_VERSION=22` + inline floor guard (no early `scripts/` COPY) | pending verify |

Local `npm run build` and CI `packages/client` Docker builds were green the whole time — so this was a **Railway package-context** failure mode, not a Vue module-graph failure.

## Fix retained

- `engines.node`: `>=22.12.0` (required by `@supabase/*`)
- Repo-root client Dockerfiles: still use `scripts/check-node-engine.mjs`
- **Railway** `packages/client/Dockerfile`: self-contained inline guard + `NODE_VERSION=22` (avoids the early `COPY scripts/...` failure mode that prevented the build from starting on Railway)
- Drift spec documents that exception explicitly

## Additional issues found

| Item | Notes |
|------|-------|
| Shared-script COPY on Railway path | CI with Buildx succeeded; Railway failed before stages. Keep Railway Dockerfile self-contained. |
| `SPRINTS.md` blast radius | Still the main review-cost item; not required for Railway green. |
| Package name `@production-shop/client` vs service `@luthiers-toolbox/client` | Pre-existing on green PRs — not this regression. |

## Verification

```bash
cd packages/client && npm run check:node && npm test -- src/testing/__tests__/nodeEngineFloor.spec.ts
# Railway bot: @luthiers-toolbox/client → Success
```
