# DEP-SEC — PR #292 `@supabase/supabase-js` 2.98.0 → 2.112.3 disposition

**Date:** 2026-08-18  
**Subject:** [PR #292](https://github.com/HanzoRazer/luthiers-toolbox/pull/292) — bump `@supabase/supabase-js` 2.98.0 → 2.112.3  
**Parent program:** `DEP-SEC-001` / `MAINT-DEFER-004`  
**Disposition:** **LAND via human-authored PR** (close Dependabot #292)

---

## 1. Scoped risk assessment (Copilot partial → completed)

| Source | Signal |
|--------|--------|
| Copilot review | Medium risk; engines.node `>=22` in lockfile vs client Node **20** pins |
| Copilot CI/deploy inventory | `client_lint_build.yml`, containers, Dockerfiles, `.env.example` → Node 20 |
| Live `gh pr checks 292` | **All green** incl. `lint-build`, Containers, Railway **client** |
| Lint-build log (Node 20.20.2) | `npm ci` succeeds with **`EBADENGINE` warnings only** (not hard fail) |

### Engines claim — verified and scoped

Lockfile after bump records `engines.node: ">=22.0.0"` on:

- `@supabase/supabase-js@2.112.3`
- `@supabase/auth-js`, `functions-js`, `postgrest-js`, `realtime-js`, `storage-js` @ 2.112.3

Also adds `@supabase/phoenix@0.4.5` (realtime).

**Repo still intentionally builds client on Node 20** (workflow + Docker). That is **not** an automatic merge blocker: npm does not enforce `engines` unless `engine-strict` is enabled. CI proof:

| Environment | Node | Result on #292 |
|-------------|------|----------------|
| `client_lint_build.yml` | **20.20.2** | **pass** (`npm ci` + test + build) |
| Containers (client image `NODE_VERSION=20`) | 20 | **pass** |
| Railway `@luthiers-toolbox/client` | (Dockerfile Node 20) | **pass** |

### Usage surface (auth-centric)

Only direct import: `packages/client/src/auth/supabase.ts` → `createClient`.

Consumers: `useAuthStore` (`getSession`, `onAuthStateChange`, `signInWithPassword`, `signUp`, `signOut`, `signInWithOAuth`), `CallbackView`, auth forms. No dedicated realtime/storage call sites beyond the client SDK surface.

### Risk table

| ID | Risk | Severity | Outcome |
|----|------|----------|---------|
| S1 | Node 20 install/build hard-fail on engines | High if true | **Refuted** — Node 20 CI green; EBADENGINE warn only |
| S2 | Auth/session behavioral break | Medium | Mitigated — suite green; createClient import smoke OK |
| S3 | Docs/Docker still say Node 20 while packages declare ≥22 | Low (skew) | **Accepted residual** — track Node 22 migration separately; do not couple into this bump |
| S4 | Dependabot-only land without CBSP21/tests | Process | Human re-land |

**Verdict:** Safe to land on current Node 20 toolchain. Do **not** require a Node 22 migration in the same PR.

---

## 2. Fixes executed

1. Human-authored bump: `packages/client` `@supabase/supabase-js` → `^2.112.3` / lockfile 2.112.3 family.
2. Disposition recording Node 20 CI witness + engines skew residual.
3. Close Dependabot #292 with durable comment.

### Evidence

- PR #292 `lint-build` on **Node 20.20.2**: pass (EBADENGINE warnings present)
- Local: `npm test` 761 passed; `npm run build` exit 0; `createClient` import smoke OK

---

## 3. Additional issues found

| Item | Notes | Action |
|------|-------|--------|
| GitHub Actions Node 20 deprecation warning | Actions forcing some steps onto Node 24 while project still selects Node 20 | Separate hygiene; not introduced by Supabase |
| No `engines` field on `packages/client/package.json` | No package-level Node pin | Optional follow-up when migrating to 22 |
| No dedicated auth unit tests | Coverage is indirect (suite + CI) | Optional follow-up |
| Node 22 migration | Would align package engines metadata + clear EBADENGINE | **Out of scope** here; may couple with Tranche C later |

---

## 4. References

- Copilot review (owner-provided) for #292
- Sibling human lands: #286 (`@types/node`), #293 (`zod`)
- Parent residual: `docs/ci/DEP_SEC_001_RESIDUAL_DISPOSITION_2026-08-10.md`
