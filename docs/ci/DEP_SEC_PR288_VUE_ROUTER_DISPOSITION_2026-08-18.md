# DEP-SEC — PR #288 `vue-router` 4.6.3 → 5.2.0 disposition

**Date:** 2026-08-18  
**Subject:** [PR #288](https://github.com/HanzoRazer/luthiers-toolbox/pull/288) — bump `vue-router` 4.6.3 → 5.2.0  
**Parent program:** `DEP-SEC-001` / `MAINT-DEFER-004`  
**Disposition:** **CLOSE — DEFERRED TO TRANCHE C** (coordinated Vue/Vite/Pinia stack upgrade)

---

## 1. Scoped risk assessment (Copilot partial → completed)

| Source | Signal |
|--------|--------|
| Copilot review | Do not merge; peers ahead of declared stack; Railway client fail |
| Copilot audit | Guards/query casts; **LAB-023** `AiAssistantProject` mismatch |
| Live CI on #288 | `lint-build` **FAIL** — `npm ci` **ERESOLVE** (not soft-fail noise) |
| Declared stack (`main`) | `vue ^3.4`, `pinia ^2.1.7`, `vite ^5`, `vue-router ^4.2.5` |

### Blocking incompatibilities (confirmed)

| Failure | Evidence | Standalone Dependabot fix? |
|---------|----------|----------------------------|
| Peer conflict | `vue-router@5.2.0` peerOptional `pinia@^3.0.4 \|\| ^4.0.2` vs installed `pinia@2.3.1` → `ERESOLVE` on `npm ci` | **No** |
| Peer expectations | Also wants `vue ^3.5.34+`, `vite ^7.3+`, `@vue/compiler-sfc ^3.5.34+` | **No** |
| Railway `@luthiers-toolbox/client` | Deployment failed | Matches install/build break |
| Transitive Vue 3.5.25→3.5.41 drag | Lockfile expands far beyond router | Reinforces “stack upgrade in disguise” |

**Verdict:** Close #288. `vue-router` majors join Tranche C with `vite` / `vitest` / `@vitejs/plugin-vue` / `pinia`.

### LAB-023 (cited independent defect — fixed in this change)

Dashboard used nonexistent route name `AiAssistantProject` with param `projectId`, while production defines only:

```text
/ai/assistant/:project_id?  →  name: AiAssistant
```

Tests previously injected a fake route to paper over the mismatch.

---

## 2. Fixes executed

1. **Ignore** `vue-router` and `pinia` semver-majors in `.github/dependabot.yml`.
2. **Close #288** with durable deferral comment.
3. **Fix LAB-023:** `AppDashboardView.vue` → always navigate to `AiAssistant` with `params.project_id` when a Project id is known; remove fake route from `AppDashboardView.spec.ts`; add LAB-023 href assertions.

No `vue-router` version bump in this change.

---

## 3. Additional issues found

| Item | Notes | Action |
|------|-------|--------|
| Callback-style guards (`router/guards.ts`) | Upgrade-sensitive; not broken on v4 | Defer to coordinated migration |
| Query cast/sync hotspots | `RmosRunsDiffView`, `useRiskFilters`, `AssistantView` | Regression suite when Tranche C lands |
| Nullable `run_id` push | `useAssetAttachment.ts` | Review under typed router later |
| Container/proxy reds on #288 | May mix R-11 secrets with install failure | Irrelevant once PR closed |

---

## 4. Landing criteria (future)

Authorize only via Dev Order / human PR that moves together:

1. `vue` (≥3.5.34 as required by target router) + compiler packages  
2. `vite` / `@vitejs/plugin-vue` (Tranche C)  
3. `pinia` 3/4  
4. `vue-router` 5  
5. CI Node pin if engines rise  
6. Smoke: auth guards, query-driven views, named-route nav (incl. AI Assistant + Instrument Hub)

Remove the Dependabot ignores in the same PR that lands the stack.

---

## 5. References

- Copilot / agent audit for #288 (owner-provided)
- Tranche C siblings: #279 disposition, `docs/ci/DEP_SEC_001_RESIDUAL_DISPOSITION_2026-08-10.md`
- LAB-023 / SPINE-005 notes in prior `AppDashboardView.spec.ts` comments
