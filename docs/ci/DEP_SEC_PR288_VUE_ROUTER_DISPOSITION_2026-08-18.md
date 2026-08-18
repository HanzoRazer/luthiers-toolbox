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

## 3a. LAB-023 severity — measured, and higher than "wrong link"

`assistantTo` feeds `<RouterLink :to="assistantTo">`. `RouterLink` calls `router.resolve()`
during render, and Vue Router **throws** on an unknown route name rather than degrading to a
dead href. Reverting the fix in a probe worktree and re-running the spec against the production
route table:

```
src/views/AppDashboardView.spec.ts (8 tests | 8 failed)
  → No match for {"name":"AiAssistantProject", ...}
```

**All eight tests fail, including the six SPINE-005 ones**, because the render of the whole
component aborts. So the pre-fix behaviour was not a mis-targeted link — **the entire Dashboard
failed to render for any user with a Project id in scope**, i.e. `?project_id=` present *or* an
Instrument Project loaded into the singleton. On a cold session with no Project the fallback
returned the bare `AiAssistant` route and the page rendered, which is why the defect survived.

The fixture route the spec previously injected was masking exactly this.

## 3b. Review pass on the fix (2026-08-18)

Reviewer caution — the second LAB-023 test was named *"without param when no Project is in the
query"* but the singleton mock was hard-coded to `SINGLETON-ID`, so the case it actually exercised
was the singleton fallback (`/ai/assistant/SINGLETON-ID`). Its assertions
(`startsWith("/ai/assistant")`, `not.toContain("/ai/assistant/project/")`) passed either way.
**Confirmed and fixed**, not merely renamed:

- The singleton mock now reads a mutable `vi.hoisted` box, reset in `afterEach`, so a genuinely
  Project-less case can be expressed at all.
- Three behavioural tests replace the vague one: query beats singleton → `/ai/assistant/A`;
  no query, singleton present → **exactly** `/ai/assistant/SINGLETON-ID`; nothing anywhere →
  **exactly** `/ai/assistant`.
- A contract test pins the route table itself: `hasRoute("AiAssistant")` true,
  `hasRoute("AiAssistantProject")` false, and both resolved path shapes.

Verified non-vacuous by mutation: deleting the `|| hubProjectId.value` fallback now fails the
singleton test (`expected '/ai/assistant' to be '/ai/assistant/SINGLETON-ID'`). Under the previous
assertions that mutation passed silently.

Also applied: the identical `route.query.project_id` parsing block was duplicated across
`assistantTo` and `instrumentHubLink`; it is now one `projectIdFromQuery()` helper. Behaviour is
unchanged and covered on both call sites (net −1 line).

**Not changed, deliberately:** the two links read the query identically but treat it differently —
the assistant falls back to the singleton, the Instrument Hub link must not (SPINE-005). That
asymmetry is now asserted rather than implied. The differing param names (`project_id` for
`AiAssistant`, `projectId` for `InstrumentHub`) match their respective route definitions and are
correct as written.

Client suite after the change: **41 files, 760 passed, 1 skipped**; `vue-tsc` 150 pre-existing
diagnostics with none in `AppDashboardView`; ESLint 0 errors on both files.

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
