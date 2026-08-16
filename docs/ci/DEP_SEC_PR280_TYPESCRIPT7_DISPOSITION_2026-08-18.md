# DEP-SEC — PR #280 `typescript` 5.9.3 → 7.0.2 disposition

**Date:** 2026-08-18  
**Subject:** [PR #280](https://github.com/HanzoRazer/luthiers-toolbox/pull/280) — bump `typescript` 5.9.3 → 7.0.2  
**Parent program:** `DEP-SEC-001` / `MAINT-DEFER-004`  
**Disposition:** **CLOSE — BLOCK TS7**; keep future **`typescript@6`** path open (#284 prep)

---

## 1. Scoped risk assessment (Copilot partial → completed)

| Source | Signal |
|--------|--------|
| Copilot review | Do not merge; TS7 breaks client toolchain; Railway client build failed |
| Copilot subpath trace | No repo-local `typescript/lib/tsc` import; likely `vue-tsc` → `@volar/typescript` |
| Copilot eslint | `@typescript-eslint` v6 fails (`Intrinsic` / `ts-api-utils`) |
| PR #284 (merged) | Explicitly: #280 unlandable; `baseUrl` removal only clears TS6 config blocker |
| Lockfile on `main` | `vue-tsc@2.2.12` → `@volar/typescript@2.4.15`; `@typescript-eslint/*@^6.21.0`; `typescript@5.9.3` |

### Blocking incompatibilities (confirmed class)

| Failure | Likely culprit | Standalone Dependabot fix? |
|---------|----------------|----------------------------|
| `ERR_PACKAGE_PATH_NOT_EXPORTED` … `'./lib/tsc'` | `vue-tsc` / `@volar/typescript` vs TS7 package `exports` | **No** |
| `Failed to load plugin '@typescript-eslint'` … `Intrinsic` | `@typescript-eslint` v6 + `ts-api-utils` vs TS7 | **No** |
| Vue SFC / Vitest / container compile regressions | Downstream compiler/package-shape change | **No** |

**Verdict:** Close #280. Do **not** attempt a lockfile-only land. TS7 requires a coordinated migration PR (tooling + witnesses), not Dependabot fan-out.

### Labels note

Invalid `dependencies` / `javascript` labels were already removed in #285. No further label work in this change.

---

## 2. Fixes executed

1. **Ignore only `typescript` `>=7.0.0`** in `.github/dependabot.yml` — stops regeneration of TS7 bumps **without** blocking an intentional `typescript@6.x` upgrade prepared by #284.
2. **Close #280** with durable deferral comment pointing here.
3. Record coordinated migration landing criteria (below).

No `packages/client` version/lockfile mutation in this change (TS stays on 5.9.3).

---

## 3. Additional issues found

| Item | Notes | Action |
|------|-------|--------|
| #282 / #283 | `@typescript-eslint` 6→8 and `eslint` 8→10 majors | Still open; **required companions** for any TS major that needs a new eslint stack — defer to Tranche B / coordinated migration, do not merge alone |
| `vue-tsc` peer | Declares `typescript: '>=5.0.0'` but **runtime** breaks on TS7 `exports` | Peer range is insufficient evidence of compatibility |
| TS6 vs TS7 | #284 cleared `baseUrl` for **TS6**; Dependabot jumped to **TS7** | Ignore `>=7` preserves TS6 intake |
| R-11 | Dependabot PRs withhold secrets | Irrelevant to close decision — #280 fails on **client** tooling before secret gates matter |
| Tranche C | `vite` / `vitest` / `@vitejs/plugin-vue` majors | Separate lane; may eventually couple with a later TS bump, but TS7 is blocked independently today |

---

## 4. Landing criteria (future coordinated migration)

Authorize only via explicit Dev Order / human PR (not by reopening #280).

Minimum companions (order may vary; all must witness green):

1. `vue-tsc` (and thus `@volar/typescript` / `@vue/language-core`) versions that support the target TypeScript major’s `exports`.
2. `@typescript-eslint/parser` + `eslint-plugin` (and eslint major if required) compatible with that TypeScript.
3. Client `type-check`, `lint`, `test`, and `build` green **without** relying on “soft-fail means pass” for new regressions.
4. Prefer **`typescript@6.0.x` first** (path prepared by #284) before considering TS7.
5. When ready for TS7 specifically: remove or narrow the `versions: [">=7.0.0"]` ignore in the same PR that lands the coordinated upgrade.

---

## 5. References

- Merged prep: PR #284 — drop deprecated `baseUrl` (TS6 path)
- Labels + plugin-vue defer: PR #285 / `docs/ci/DEP_SEC_PR279_PLUGIN_VUE_DISPOSITION_2026-08-18.md`
- Types hygiene land: PR #286 / `docs/ci/DEP_SEC_PR281_TYPES_NODE_DISPOSITION_2026-08-18.md`
- Parent residual: `docs/ci/DEP_SEC_001_RESIDUAL_DISPOSITION_2026-08-10.md`
