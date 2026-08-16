# PR #307 — Railway `@luthiers-toolbox/client` failure disposition

**Date:** 2026-08-19  
**PR:** [#307](https://github.com/HanzoRazer/luthiers-toolbox/pull/307)  
**Status:** Mitigation landed (config-as-code + env recreation); await Railway rebuild signal

## Scoped risk assessment (review → action)

| Cited item | Disposition |
|------------|-------------|
| Railway client Build Failed (blocking) | **Actioned.** Local `npm run build` and CI Docker builds of `packages/client/Dockerfile` are green; failure is PR-environment / pre-build specific to #307. |
| Split `SPRINTS.md` ledger | **Deferred (not blocking Railway).** Ledger remains in #307; split to a follow-up PR if review still wants narrower diff after Railway is green. |
| README: `engines.node` SSoT | **Done** in `packages/client/README.md`. |
| CI `npm run check:node` outside Docker | **Done** in `client_lint_build.yml`. |

## Evidence ranking (Railway client red)

| Commit | Client Railway | Notes |
|--------|----------------|-------|
| `82d6c07d` | SUCCESS | engines `^20.19.0 \|\| >=22.12.0`, `NODE_VERSION=20`, inline guard |
| `c7cb9938` → `70b9c661` | FAILURE (~23s) | engines `>=22.12.0`, `NODE_VERSION=22`, shared script guard |
| Sibling PRs #305/#306/#308/#309 | SUCCESS | **no** `engines.node` on those heads |

CI on #307 builds all four client Dockerfiles **green**, including the Railway entry point (`context: packages/client`). Local Vite production build **succeeds**.

Therefore the red signal is **not** explained by unresolved Vue imports, missing `VITE_*`, or a broken Dockerfile COPY of `check-node-engine.mjs`. Strongest remaining causes:

1. Stale / corrupt Railway PR environment `luthiers-toolbox-pr-307` (author's own closing hypothesis after the `.nvmrc` experiment).
2. Dashboard builder override diverging from `railway.json` (Railpack/Nixpacks vs Dockerfile).

## Fixes executed

1. `packages/client/railway.toml` — config-as-code pinning `builder = "DOCKERFILE"` + `dockerfilePath = "Dockerfile"` so a stale UI override cannot silently switch builders.
2. `railway.json` — watch `railway.toml`.
3. Dockerfile — explicit `COPY package.json package-lock.json` + single-file script COPY (clearer fail mode).
4. `client_lint_build.yml` — `npm run check:node` before `npm ci`.
5. README — engines SSoT note.
6. Root `railway.toml` comment — Node 20 → Node 22.
7. Close/reopen #307 after push to force Railway to recreate the PR environment.

## Additional issues found

| Item | Notes |
|------|-------|
| `engines.node` correlation | Only #307 declares engines; siblings without it deploy green. Floor itself is still correct for `@supabase/*` (>=22). Do **not** remove it to chase Railway — recreate the env instead. |
| Package name vs service name | Manifest is `@production-shop/client`; Railway service is `@luthiers-toolbox/client`. Pre-existing on green PRs — not this regression. |
| `SPRINTS.md` blast radius | Still the main review-cost item; orthogonal to Railway. |

## Verification

```bash
cd packages/client && npm run check:node && npm test -- src/testing/__tests__/nodeEngineFloor.spec.ts
# + CI containers.yml Railway entry-point job (already green on branch)
```

Awaiting Railway bot: `@luthiers-toolbox/client` → Success on the post-reopen deploy.
