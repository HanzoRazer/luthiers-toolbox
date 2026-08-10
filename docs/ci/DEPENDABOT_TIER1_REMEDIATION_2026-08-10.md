# Dependabot Tier-1 Remediation — 2026-08-10

**Program:** DEP-SEC-001A  
**SPRINTS ownership:** `MAINT-DEFER-004`  
**Upstream evidence:** PR #252 / `docs/ci/DEPENDABOT_TRIAGE_AND_DECISION_2026-08-09.md`  
**Owner ruling:** Option A authorized 2026-08-10 (Tier-1 now; Vite/Vitest majors held)  
**Branch:** `cursor/dep-sec-001a-tier1-42de`

---

## 1. Baseline (pre-patch)

| Surface | Value |
|---------|--------|
| Substrate | `origin/main` @ `6ccc664e` (includes #252) |
| Triage snapshot | **2026-08-09** — 65 open alerts / 17 packages (not an eternal invariant) |
| `packages/client` axios (declared / resolved) | `^1.13.2` / `1.13.2` |
| `packages/client` postcss (declared / resolved) | `^8.5.8` / `8.5.8` |
| vite / vitest majors | 5.x / 2.x |
| `services/api/requirements.txt` | untouched (0 alerts at triage) |
| Alert API in this agent | **403** — `Resource not accessible by integration` |

---

## 2. Tier-1 patches applied

| Package | Triage floor | Implemented (latest compatible in major) | Resolved in lockfile |
|---------|--------------|------------------------------------------|----------------------|
| `axios` | 1.18.0 | `^1.19.0` | **1.19.0** |
| `postcss` | 8.5.18 | `^8.5.26` | **8.5.26** |

**Unchanged majors:** `vite` **5.4.21**, `vitest` **2.1.9**.  
**Python:** `services/api/requirements.txt` and `requirements-dev.txt` byte-unchanged by this sprint.

```text
OUT OF SCOPE — PYTHON DEV DEPENDENCY ALERT REMAINS
```

(`services/api/requirements-dev.txt` — separate later disposition.)

---

## 3. Direct witnesses (mandatory — BR-021 makes CI green insufficient)

Working directory: `packages/client`. Environment: Node v22.14.0 / npm 10.9.7.

| Step | Command | Exit code |
|------|---------|----------:|
| Frozen install | `npm ci --ignore-scripts` | **0** |
| Unit tests | `npm test` (`vitest run`) | **0** (756 passed / 17 todo / 1 file skipped) |
| Production build | `npm run build` (`vite build`) | **0** (built in ~12.4s) |
| Major guard | vite major=5, vitest major=2 | **0** |
| Bundle purity (proxy agents) | `rg 'HttpsProxyAgent\|https-proxy-agent\|agent-base' dist` after build | **0 matches** |

Axios import inventory re-witness: **20** files under `packages/client/src` import axios (matches triage browser-only posture).

---

## 3a. Lockfile transitive review (axios / postcss) — PR #253 review follow-up

Top-level declared changes are only `axios` and `postcss`. Lockfile regenerated with **npm 10.9.7**.

### Expected / explained (not blockers)

| Change | Resolved | Assessment |
|--------|----------|------------|
| New under axios: `https-proxy-agent` + nested `agent-base` | 5.0.1 / 6.0.2 | **Expected** for axios 1.19.x Node adapter/proxy support. Client usage is browser-only (20 `src/` imports). Vite production `dist/` contains **no** `HttpsProxyAgent` / `https-proxy-agent` / `agent-base` strings — Node proxy path is not shipped in the browser bundle. |
| `debug` / `ms` lose `dev: true` | 4.4.3 / 2.1.3 | **Expected reclassification** — now reachable via the axios→https-proxy-agent→agent-base→debug chain in the lockfile graph. Does not imply these run in the browser bundle (see purity check above). |
| `proxy-from-env` | 1.1.0 → **2.1.0** | Axios-tree update; Node/`engines: >=10` only. Low risk for browser SPA; relevant only if axios is later used in Node tooling/SSR. Not used that way today. |
| `follow-redirects` / `form-data` / `hasown` / `nanoid` | patch bumps | Normal axios/postcss fallout. |
| Widespread `peer: true` metadata removals | n/a | Lockfile metadata normalization under npm 10.9.7; no matching toolchain version jumps (vite/vitest majors unchanged). |

### Not observed (reassuring)

- No Vite/Vitest major movement  
- No unrelated top-level dependency additions  
- No native modules or foreign ecosystem packages  
- PostCSS side limited to postcss + nanoid patch drift  

---

## 4. Dependabot intake boundary

Created `.github/dependabot.yml`:

- ecosystem: `npm`
- directory: `/packages/client` only
- weekly schedule; `open-pull-requests-limit: 5`
- **no auto-merge**
- ignore semver-major for `vite` and `vitest` (Tier-2)

Archived manifests are **not** listed. They remain on disk as historical evidence:

```text
archive/experimental/2026-03/Interactive_Headstock_Generator/files - 2026-03-17T091407.113/package.json
archive/experimental/2026-03/Interactive_Neck and Cam _Modules/files - 2026-03-17T091407.113/package.json
docs/archive/photo_vectorizer_patches/package.json
```

Reachability: not referenced by `pnpm-workspace.yaml` (`packages/*` only), not imported by active client/API build paths.

---

## 5. Archive alert dismissals — owner UI action

Platform Dependabot **alerts** still enumerate all `package.json` files; directory scoping stops update PRs, not security-alert filing. Per owner ruling **B**, the 9 dead-archive alerts (all `vite` in the three paths above) must be dismissed in the GitHub UI.

**This agent cannot dismiss them:** Dependabot Alerts API returns HTTP 403 for the integration token.

```text
PENDING GITHUB RECALCULATION / OWNER UI WITNESS
```

**Dismissal template (repeat per alert / path):**

> Reason: **Not used**  
> Comment: `DEP-SEC-001A / MAINT-DEFER-004 — unused archival surface. Manifest path: <EXACT_PATH> is under archive/** or docs/archive/**, excluded from pnpm-workspace and active client/API build/runtime/workspace execution. Historical evidence retained; not an active dependency.`

No repository Commit 3 was manufactured; archive disposition is configuration (Commit 1) + external GitHub dismissals.

---

## 6. Post-patch alert state

```text
PENDING GITHUB RECALCULATION / OWNER UI WITNESS
```

Expected after GitHub recalculation + archive dismissals (not forced):

- axios cluster closed via 1.19.0
- postcss cluster closed via 8.5.26
- 9 archive vite alerts dismissed as unused
- remaining open alerts = toolchain/transitive residual (incl. vite/vitest majors) + out-of-scope Python dev alert

`npm audit` after patch still reported **21** issues in the client tree — residual toolchain surface; not a Tier-1 failure criterion.

---

## 7. Tier-2 still deferred

```text
vite major 5→6 — HELD
vitest major 2→3 — HELD
```

Restore trigger (from `MAINT-DEFER-004`): BR-021 resolution **or** explicit manual build-witness authorization. Preferred order: vitest → witness → vite.

---

## 8. Commits

1. `chore(deps): establish dependency-security maintenance baseline` — dependabot.yml + MAINT-DEFER-004  
2. `fix(deps): patch axios and postcss security advisories` — versions + lockfile  
3. *(omitted)* — no repo patch for archive dismissals  
4. This closeout + CBSP21 manifest
