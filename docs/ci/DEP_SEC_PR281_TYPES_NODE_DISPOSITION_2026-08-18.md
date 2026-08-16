# DEP-SEC — PR #281 `@types/node` 25 → 26 disposition

**Date:** 2026-08-18  
**Subject:** [PR #281](https://github.com/HanzoRazer/luthiers-toolbox/pull/281) — bump `@types/node` 25.0.9 → 26.2.0 (`undici-types` ~7.16.0 → ~8.3.0)  
**Parent program:** `DEP-SEC-001` / `MAINT-DEFER-004`  
**Disposition:** **LAND via human-authored PR** (close Dependabot #281) — types-only, proven no-op on `vue-tsc`

---

## 1. Scoped risk assessment (Copilot partial → completed)

Inputs used:

| Source | Signal |
|--------|--------|
| Copilot PR review | Low runtime risk; browser-first client; `skipLibCheck: true`; watch `vite.config.ts` / fetch wrappers |
| Copilot CI drill | Claimed 12 failed checks; attributed most to SG_SPEC / architecture / baseline TS debt |
| Live `gh pr checks 281` (2026-08-18) | **`lint-build` PASS**; Railway client deploy PASS; remaining fails are secret/container family (R-11) |
| Local witness (this change) | `vue-tsc` diagnostic set **identical** to `main` (150 keys, 0 delta); `tsc -p tsconfig.node.json` exit 0; `npm test` 756 pass; `npm run build` exit 0 |

### Corrections to the Copilot CI narrative

1. **`lint-build` is green on #281**, not red. Type-check/lint steps use `continue-on-error: true` (BR-021); tests + build determine job success. The large TS/ESLint problem counts are baseline BR-021 debt, not a job failure caused by this bump.
2. Failures that remain (`proxy-adaptive`, `proxy-parity`, `Containers`, `build-and-test`, `server-env-check`, summary rollups) match **DEP-SEC R-11**: Dependabot-authored PRs lack repository secrets (`SG_SPEC_TOKEN`). They are **not** evidence against the types bump.
3. Therefore: do **not** merge Dependabot #281 itself. Re-land the same lockfile change on a human branch so secret-bearing workflows can run.

### Risk table

| ID | Risk | Severity | Outcome |
|----|------|----------|---------|
| C1 | Major typings bump surfaces new TS errors | Medium (theoretical) | **Refuted** — 150/150 identical `vue-tsc` keys vs `main`; no `main.ts` / `sdk/http.ts` / `vite.config.ts` / fetch / undici deltas |
| C2 | DOM vs Node `fetch` ambient overlap via `undici-types@8` | Medium (theoretical) | **Not evidenced** — app `types: ["vite/client"]` + DOM libs; `skipLibCheck: true` |
| C3 | `vite.config.ts` Node globals break | Low | **Refuted** — only `node:url`; `tsc -p tsconfig.node.json` exit 0 |
| C4 | Invalid Dependabot labels | Low (hygiene) | Fixed separately in #285 (`dependabot.yml` label removal) |
| C5 | `@types/node@26` vs CI Node 20 | Low (policy) | Already true at `@types/node@25` on Node 20 CI; bump continues existing skew. Documented; not a merge blocker for typings-only |

**Verdict:** Safe to land as hygiene. Runtime unchanged. Typecheck witness is a proven no-op.

---

## 2. Fixes executed

1. Human-authored bump: `packages/client/package.json` + `package-lock.json` (`@types/node` ^26.2.0 / resolved 26.2.0; `undici-types` 8.3.0).
2. Evidence table recorded (below).
3. Close Dependabot #281 with durable comment pointing here (R-11: do not merge the bot PR).
4. Labels issue tracked/fixed in #285 (not re-done here).

### Evidence — proven no-op on pinned toolchain

`vue-tsc` diagnostics compared as sorted `file(line,col): error TSnnnn` keys:

| | exit | diagnostic keys | hotspot deltas (`main.ts` / `http.ts` / `vite.config` / fetch / undici) |
|---|---|---|---|
| `main` (`@types/node@25.0.9`) | 2 | 150 | — |
| this PR (`@types/node@26.2.0`) | 2 | 150 | **0** |

`diff` of the two sorted key sets: **empty**.

Also: `npx tsc -p tsconfig.node.json --noEmit` exit 0 · `npm test` 756 passed · `npm run build` exit 0.

---

## 3. Additional issues found

| Item | Notes | Action |
|------|-------|--------|
| #285 | Removes invalid Dependabot labels; ignores `@vitejs/plugin-vue` majors | Merge independently |
| #280 | `typescript` → 7.0.2 unlandable (#284) | Keep closed/deferred; not this PR |
| #282 / #283 | eslint / typescript-eslint majors | Tranche B; do not merge as freestanding Dependabot PRs |
| BR-021 | Soft-fail type-check/lint still masks baseline red | Unrelated; do not use as reason to block types hygiene |
| R-11 | Dependabot PRs structurally fail secret-gated jobs | Why this land is human-authored |
| Node pin vs types major | CI `node-version: 20`; types already at 25, now 26 | Acceptable for Vite config typings; tighten only if/when Node runtime is bumped |

---

## 4. Policy note — `@types/node` majors

For `packages/client`:

- App TS is browser-scoped (`lib` DOM, `types: ["vite/client"]`).
- `@types/node` primarily serves `vite.config.ts` / tooling via project references.
- Majors may land when witnesses show **identical** (or improved) `vue-tsc` key sets and green `tsc -p tsconfig.node.json`, tests, and build.
- Prefer human-authored PRs over merging Dependabot heads (R-11).

---

## 5. References

- Copilot review thread (owner-provided) for #281
- Parent residual: `docs/ci/DEP_SEC_001_RESIDUAL_DISPOSITION_2026-08-10.md` (R-11, Tranche B)
- Sibling: `docs/ci/DEP_SEC_PR279_PLUGIN_VUE_DISPOSITION_2026-08-18.md` (#279 defer)
- Labels fix: PR #285
