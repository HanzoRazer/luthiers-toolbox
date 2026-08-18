# DEP-SEC — PR #287 `zod` 3.25.76 → 4.4.3 disposition

**Date:** 2026-08-18  
**Subject:** [PR #287](https://github.com/HanzoRazer/luthiers-toolbox/pull/287) — bump `zod` 3.25.76 → 4.4.3  
**Parent program:** `DEP-SEC-001` / `MAINT-DEFER-004`  
**Disposition:** **LAND via human-authored PR** (close Dependabot #287)

---

## 1. Scoped risk assessment (Copilot partial → completed)

| Source | Signal |
|--------|--------|
| Copilot review | Medium risk major; tiny diff; verify Zod call sites; hold if CI red |
| Copilot CI drill | Claimed `lint-build` failing with TS/ESLint — treat as merge blocker |
| Copilot usage trace | Single runtime site: `packages/client/src/cam/compare/compare_types.ts` |
| Live `gh pr checks 287` (2026-08-18) | **All relevant checks PASS**, including `lint-build`, Railway client, containers, api-verify |
| Local witness (this change) | Focused schema tests green on Zod 3 **and** Zod 4; full suite 761 pass; build exit 0 |

### Corrections to the Copilot CI narrative

1. **`lint-build` is green on #287.** Type-check/lint steps use `continue-on-error: true` (BR-021). The large TS/ESLint problem counts are baseline debt, not a job failure caused by Zod 4.
2. Failures Copilot attributed to this PR are **not present** on the current check rollup (33 SUCCESS). Do not use a stale/soft-fail log as a Zod blocker.
3. Prefer human-authored land over merging Dependabot head when policy prefers R-11 hygiene — same vehicle as #286.

### Zod usage (exhaustive import search)

| Path | Role |
|------|------|
| `src/cam/compare/compare_types.ts` | **Only** `import { z } from "zod"` in `packages/client` |
| `src/cam/compare/compare_storage.ts` | Type-only import from `compare_types` (no Zod runtime) |

APIs used (all standard): `z.object`, `z.array`, `z.tuple`, `z.union`, `z.number`/`string`/`boolean`/`enum`, `.optional()`, `.default()`, `.min()`, `safeParse`, `z.infer`.

**Not used:** `preprocess`, `transform`, `catch`, `superRefine`, discriminated unions, custom error maps.

### Risk table

| ID | Risk | Severity | Outcome |
|----|------|----------|---------|
| Z1 | Zod 4 breaks compare schemas (defaults/unions/tuples) | Medium (theoretical) | **Refuted** — focused tests pass on 3.25.76 and 4.4.3 |
| Z2 | Hidden advanced Zod call sites | Medium if present | **Not found** — only one `from "zod"` import |
| Z3 | Copilot “lint-build failed” | Operational | **Incorrect** for current checks — job passes |
| Z4 | Exact `error.message` string changes | Low | Acceptable; parsers throw generic `Error` |

**Verdict:** Safe to land. Runtime surface is one schema module; witnesses green.

---

## 2. Fixes executed

1. Human-authored bump: `packages/client/package.json` + lockfile (`zod` ^4.4.3 / 4.4.3).
2. Added `src/cam/compare/__tests__/compare_types.test.ts` — defaults, move union, loops min-3, DiffResult defaults (Copilot “smoke test” improvement).
3. Close Dependabot #287 with durable comment pointing here.

### Evidence

| Check | Zod 3.25.76 | Zod 4.4.3 |
|-------|-------------|-----------|
| `compare_types.test.ts` | 5/5 pass | 5/5 pass |
| `npm test` | — | 761 passed / 17 todo |
| `npm run build` | — | exit 0 |
| PR #287 `lint-build` | — | **pass** (GitHub) |

---

## 3. Additional issues found

| Item | Notes | Action |
|------|-------|--------|
| BR-021 soft-fail | Makes Copilot-style “TS/lint failed” logs look blocking while job still passes | Do not treat soft-fail step red as Zod regression without main delta |
| No prior schema tests | compare_types had zero coverage | Added in this PR |
| Dependabot labels on #287 | Review text shows `dependencies`/`javascript`; repo yml omits invalid labels (#285) | No further action unless labels were created externally |
| Other open Dependabot majors | Already dispositioned (#279/#280/#282/#283) | Out of scope |

---

## 4. References

- Copilot review thread (owner-provided) for #287
- Sibling human land: PR #286 (`@types/node`)
- Parent residual: `docs/ci/DEP_SEC_001_RESIDUAL_DISPOSITION_2026-08-10.md`
