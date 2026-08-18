# DEP-SEC — PR #279 `@vitejs/plugin-vue` major disposition

**Date:** 2026-08-18  
**Subject:** [PR #279](https://github.com/HanzoRazer/luthiers-toolbox/pull/279) — bump `@vitejs/plugin-vue` 5.2.4 → 6.0.8  
**Parent program:** `DEP-SEC-001` / `MAINT-DEFER-004`  
**Disposition:** **CLOSE — DEFERRED TO TRANCHE C** (vite/vitest major toolchain lane)

---

## 1. Scoped risk assessment (partial → complete)

PR #279 itself carried no human review body. The actionable risk surface was reconstituted from:

| Source | Signal |
|--------|--------|
| Dependabot comment on #279 | Invalid labels `dependencies` / `javascript` in `.github/dependabot.yml` |
| Package metadata `@vitejs/plugin-vue@6.0.8` | `engines.node`: `^20.19.0 \|\| >=22.12.0`; peer `vite`: `^5 \|\| ^6 \|\| ^7 \|\| ^8` |
| Changelog (6.0.0-beta) | **Breaking:** Node floor raise + CJS build dropped; `include`/`exclude` moved off `api.options` |
| `docs/ci/DEP_SEC_001_RESIDUAL_DISPOSITION_2026-08-10.md` | `vite`/`vitest` majors already ignored → **Tranche C**; version-hygiene majors must not merge as freestanding Dependabot PRs |
| Client pins on `main` | `vite ^5`, `@vitejs/plugin-vue ^5`, CI `node-version: 20` (unpinned patch) |
| `docs/canonical/CODING_POLICY.md` | Still documents `"@vitejs/plugin-vue": "^5.0.0"` |

### Risk table

| ID | Risk | Severity | Merge #279 now? |
|----|------|----------|-----------------|
| R1 | Major plugin bump while `vite` majors are policy-held on Tranche C | High (governance) | **No** — couples toolchain without witness |
| R2 | Node engines floor `20.19+` / `22.12+` vs CI `node-version: 20` (floating) | Medium | **No** without explicit Node pin ≥20.19 |
| R3 | CJS drop + filter API change | Low here (`vue()` used with default options in `vite.config.ts` / `vitest.config.ts`) | Mitigated if landed later |
| R4 | Dependabot labels missing → noisy PR comments on every fan-out PR | Low (hygiene) | Fix config (this change) |
| R5 | Open-PR limit (5) filled by majors (#279–#283) crowding security/patch intake | Medium | Defer + ignore majors that belong in tranches |

**Verdict:** Do **not** merge #279. Treat as Tranche C companion to `vite` 5→6. Durable control: ignore `@vitejs/plugin-vue` semver-major in `dependabot.yml` (same lane as `vite`/`vitest`).

CI green on #279 (including `lint-build` and Railway) is **observational only** — same rule as DEP-SEC-001B: Dependabot PR greens are not merge authorization for deferred majors.

---

## 2. Fixes executed (this change)

1. **Removed** nonexistent `labels: [dependencies, javascript]` from `.github/dependabot.yml` (Dependabot’s cited fix).
2. **Added** ignore for `@vitejs/plugin-vue` `version-update:semver-major`.
3. **Close #279** with durable deferral comment (obligation tracked here + parent residual matrix).

No `packages/client` lockfile / version bump in this change.

---

## 3. Additional issues found (out of #279 merge scope)

| PR | Package | Assessment | Recommended disposition |
|----|---------|------------|-------------------------|
| [#280](https://github.com/HanzoRazer/luthiers-toolbox/pull/280) | `typescript` 5.9.3 → **7.0.2** | Unlandable on current stack (`vue-tsc@2` / `@typescript-eslint` / `@vue/compiler-sfc` break). #284 only cleared `baseUrl` for a future **TS6** path — not TS7. | Close; do **not** ignore all `typescript` majors (would also block intentional TS6). Prefer `@dependabot ignore this major version` on #280 or wait for a TS6-targeted PR. |
| [#281](https://github.com/HanzoRazer/luthiers-toolbox/pull/281) | `@types/node` 25 → 26 | Types-only major; lower coupling than toolchain. | Review separately; not gated by Tranche C. |
| [#282](https://github.com/HanzoRazer/luthiers-toolbox/pull/282) | `@typescript-eslint/eslint-plugin` 6 → 8 | Lint major; same class as closed #255. | Defer → Tranche B (coordinate with parser + eslint-plugin-vue). |
| [#283](https://github.com/HanzoRazer/luthiers-toolbox/pull/283) | `eslint` 8 → 10 | Lint major; pairs with #282. | Defer → Tranche B. |
| CODING_POLICY | Documents plugin-vue `^5.0.0` | Consistent with deferral; update only when Tranche C lands. | No change now. |
| CI Node pin | `node-version: 20` | Floating; may or may not be ≥20.19 on a given runner image. | When Tranche C is authorized, pin `20.19` or `22.12+` explicitly. |

---

## 4. Landing criteria (when Tranche C is authorized)

1. BR-021 resolved **or** explicit manual build-witness Dev Order.
2. Preferred order remains **vitest → witness → vite**; bring `@vitejs/plugin-vue` **with** the vite major (not ahead of it as a lone Dependabot PR).
3. Pin CI/Node engines to satisfy plugin-vue 6 `engines`.
4. Update `docs/canonical/CODING_POLICY.md` pin.
5. Re-run client `lint-build`, unit tests, and production build under the pinned Node.

---

## 5. References

- Parent residual matrix: `docs/ci/DEP_SEC_001_RESIDUAL_DISPOSITION_2026-08-10.md` (§ Tranche C / R-04)
- Tier-1 intake: `docs/ci/DEPENDABOT_TIER1_REMEDIATION_2026-08-10.md`
- Related prep (merged): PR #284 — drop deprecated `baseUrl` (TS6 path only; explicitly not #280)
