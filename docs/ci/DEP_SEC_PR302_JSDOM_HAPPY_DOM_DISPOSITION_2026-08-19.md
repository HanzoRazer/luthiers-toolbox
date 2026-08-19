# DEP-SEC — PR #302 `jsdom` → `happy-dom` disposition

**Date:** 2026-08-19  
**Subject:** [PR #302](https://github.com/HanzoRazer/luthiers-toolbox/pull/302) (closed/DIRTY) → land via [PR #303](https://github.com/HanzoRazer/luthiers-toolbox/pull/303)  
**Parent program:** `DEP-SEC-001` / `MAINT-DEFER-004`  
**Disposition:** **KEEP #302 CLOSED.** Land happy-dom migration on **#303**.

---

## 1. Scoped risk assessment (Copilot partial → completed)

| Source | Signal |
|--------|--------|
| Copilot / review of #302 | Closed, conflicting, title/body mismatch (jsdom bump vs happy-dom migrate); use #303 |
| Technical review | Package + Vitest default swap coherent; #302 incomplete without per-file `@vitest-environment` updates |
| Live `gh pr view 302` | `state: CLOSED`, `mergeable: CONFLICTING`, `mergeStateStatus: DIRTY` |
| Live `gh pr checks 303` | `lint-build` SUCCESS; CBSP21 FAILED until covering patch added (wrong auto-select of PR281 manifest) |
| Local witness (#303 branch) | `npm test` → **765 passed** / 17 todo; `npm run build` → exit 0; no `@vitest-environment jsdom` left |

### Corrections / closures of cited blockers

| Cited item | Outcome |
|------------|---------|
| #302 closed + dirty | **Stay closed.** Not a merge vehicle. |
| Title/intent mismatch on #302 | Superseded by honestly titled #303. |
| Incomplete migration (global env only) | **Fixed in #303:** four audio-analyzer specs updated to `@vitest-environment happy-dom`. Repo-wide search shows **zero** remaining jsdom env annotations or imports. |
| Misleading CI step label (`20.x` vs version 22) | **Fixed in #303:** step name is `Setup Node.js 22.x` and `node-version: 22`. |
| Stale/conflicting lockfile | **Fixed in #303:** lockfile regenerated on current `main`; jsdom package absent. |

### Why not land jsdom 30

- Node floor `^22.22.2 \|\| ^24.15.0 \|\| >=26.0.0`
- Pulls undici 8.x that breaks Vitest (`webidl.util.markAsUncloneable`)
- Copilot follow-up on #302 already abandoned the bump in favor of happy-dom

### Risk table

| ID | Risk | Severity | Outcome |
|----|------|----------|---------|
| R1 | happy-dom ≠ jsdom behavioral clone | medium | Accepted: full Vitest suite green (765) is the land gate |
| R2 | Mixed DOM environments if file overrides remain | medium | Mitigated: exhaustive `@vitest-environment` / import search clean |
| R3 | CI Node 22 vs Docker default Node 20 | low | Accepted: happy-dom is **devDependency** only; Railway client build on #303 already green under existing Dockerfile |
| R4 | Dependabot reopens jsdom majors | low | Mitigated: `jsdom` removed from `package.json` (no Dependabot target) |
| R5 | CBSP21 auto-selects unrelated patch | medium | Mitigated: covering patch `dep-sec-pr302-jsdom-happy-dom.json` |

### Additional issues found (beyond the pasted review)

1. **CBSP21 gate on #303 failed** — auto-discovered `.cbsp21/patches/dep-sec-pr281-types-node.json` (25% coverage). Fixed by adding this disposition’s covering patch.
2. **Client Dockerfile `ARG NODE_VERSION=20`** — left unchanged on purpose (test-only migration). Documented in R3.
3. **Vitest optional peer still lists `jsdom` in lockfile metadata** — peer meta only; package not installed. No action required.

---

## 2. Exact conflict cause (#302 vs `main`)

Not an application-logic conflict. Both sides rewrote overlapping regions of `packages/client/package-lock.json` while #302’s branch (Dependabot + Copilot happy-dom pivot) sat on a stale base and `main` advanced (e.g. vue 3.5.41, vue-tsc 3.3.10). Conflict hunks cited in-thread: `@csstools/*`, `@types/whatwg-mimetype`/`ws`, `data-urls`/`de-indent`, jsdom block, `ws` versions.

---

## 3. Evidence

```text
Test Files  42 passed | 1 skipped (43)
Tests       765 passed | 17 todo (782)
npm run build  ✓
rg @vitest-environment jsdom packages/client → no matches
rg from ['"]jsdom['"] packages/client → no matches
```

---

## 4. Follow-ups (out of scope)

- Broader CI Node 22 migration beyond `client_lint_build.yml`
- Dockerfile Node bump (only if production engines later require it)
- BR-021 soft-fail debt on type-check/lint steps
