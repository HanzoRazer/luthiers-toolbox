# DEP-SEC-001 — Residual Disposition Matrix (Post-#253)

**Program:** `DEP-SEC-001` (parent dependency-security program)  
**Sprint:** `DEP-SEC-001B` — Post-#253 Residual Consolidation & PR-Fan-Out Control  
**SPRINTS ownership:** `MAINT-DEFER-004`  
**Substrate:** `origin/main` @ `25fc189d` (includes merged PR #253)  
**Matrix date:** 2026-08-10  
**Posture:** Governance / evidence / disposition only. **No dependency manifests or lockfiles mutated by this sprint.**

---

## 1. Purpose

Establish a single authoritative residual-obligation record after PR #253 so that:

```text
PR COMPLETE  ≠  PROGRAM COMPLETE
```

Every material dependency-security obligation discovered by or generated from #252/#253 must have one durable disposition before further implementation proceeds. Generated Dependabot PRs are **evidence**, not automatic sprints.

---

## 2. Parent-program state

| Field | Value |
|-------|--------|
| Program ID | `DEP-SEC-001` |
| SPRINTS ID | `MAINT-DEFER-004` |
| **Parent status** | **`ACTIVE — TIER 1 COMPLETE`** |
| Tier-1 tranche (`DEP-SEC-001A` / PR #253) | **COMPLETE** |
| Program resolved? | **No** — residuals remain with durable dispositions below |
| Final statement (this sprint) | **`ACTIVE — ALL REMAINING WORK DURABLY DEFERRED/DISPOSITIONED`** |

Required vocabulary used in this matrix (aligned to repository practice):

`ACTIVE` · `COMPLETE` · `DEFERRED` · `OWNER ACTION` · `BLOCKED` · `SUPERSEDED` · `DUPLICATE` · `ACCEPTED RISK` · `NOT APPLICABLE` · `OUT OF SCOPE`

---

## 3. #252 relationship

| Item | Evidence |
|------|----------|
| PR | [#252](https://github.com/HanzoRazer/luthiers-toolbox/pull/252) — merged `2026-08-10T02:49:32Z` |
| Artifact | `docs/ci/DEPENDABOT_TRIAGE_AND_DECISION_2026-08-09.md` |
| Role | Evidence / decision support — read-only triage of **65 open alerts → 17 packages** (snapshot **2026-08-09**) |
| Owner ruling used by #253 | **Option A** — Tier-1 now; Vite/Vitest majors held |

#252 does **not** authorize version-hygiene majors outside the triage security set.

---

## 4. #253 relationship

| Item | Evidence |
|------|----------|
| PR | [#253](https://github.com/HanzoRazer/luthiers-toolbox/pull/253) — merged `2026-08-10T16:37:37Z` → `main` @ `25fc189d` |
| Title | DEP-SEC-001A: Tier-1 dependency security (axios/postcss + Dependabot ownership) |
| Closeout | `docs/ci/DEPENDABOT_TIER1_REMEDIATION_2026-08-10.md` |
| Classification | **Tier-1 / tranche COMPLETE** — **not** parent-program COMPLETE |

### What #253 completed

- `axios` → **1.19.0**, `postcss` → **8.5.26** (within existing majors)
- Created `.github/dependabot.yml` (npm → `/packages/client` only; ignore vite/vitest majors; `open-pull-requests-limit: 5`; no auto-merge)
- Registered `MAINT-DEFER-004` ownership in `SPRINTS.md`
- Direct witnesses: `npm ci` / `npm test` / `npm run build` exit 0

### What #253 did **not** complete

- Parent `DEP-SEC-001` closure
- Vite/Vitest majors
- BR-021
- Python `requirements-dev.txt` alert
- Archive Dependabot alert dismissals (owner UI; API 403)
- Post-merge Dependabot version-update fan-out (#254–#258)

---

## 5. Generated-PR inventory (TC-01)

**Grounded fan-out:** exactly **five** PRs created after #253 merge (`createdAt` > `2026-08-10T16:37:37Z`). Conversational count matches GitHub evidence.

| PR | Title | Actor | created_at | Package | Manifest | from → to | State (at matrix) |
|----|-------|-------|------------|---------|----------|-----------|-------------------|
| [#254](https://github.com/HanzoRazer/luthiers-toolbox/pull/254) | bump `@vue/test-utils` 2.4.6 → 2.4.11 | `app/dependabot` | 2026-08-10T16:38:56Z | `@vue/test-utils` | `packages/client` | 2.4.6 → 2.4.11 | CLOSED (001B disposition) |
| [#255](https://github.com/HanzoRazer/luthiers-toolbox/pull/255) | bump `@typescript-eslint/eslint-plugin` 6.21.0 → 8.66.0 | `app/dependabot` | 2026-08-10T16:39:21Z | `@typescript-eslint/eslint-plugin` | `packages/client` | 6.21.0 → 8.66.0 | CLOSED (001B disposition) |
| [#256](https://github.com/HanzoRazer/luthiers-toolbox/pull/256) | bump `konva` 9.3.22 → 10.3.0 | `app/dependabot` | 2026-08-10T16:39:26Z | `konva` | `packages/client` | 9.3.22 → 10.3.0 | CLOSED (001B disposition) |
| [#257](https://github.com/HanzoRazer/luthiers-toolbox/pull/257) | bump `marked` 17.0.1 → 18.0.9 | `app/dependabot` | 2026-08-10T16:39:33Z | `marked` | `packages/client` | 17.0.1 → 18.0.9 | CLOSED (001B disposition) |
| [#258](https://github.com/HanzoRazer/luthiers-toolbox/pull/258) | bump `eslint-plugin-vue` 9.33.0 → 10.10.0 | `app/dependabot` | 2026-08-10T16:39:40Z | `eslint-plugin-vue` | `packages/client` | 9.33.0 → 10.10.0 | CLOSED (001B disposition) |

### Why these five exist

`.github/dependabot.yml` **did not exist before #253** (created in commit `48a30ea5` / merged via #253). Immediately after merge, Dependabot opened version-update PRs for outdated packages under `/packages/client`, capped by:

```yaml
open-pull-requests-limit: 5
```

That limit explains the exact count of five. This is **version-update fan-out from new intake config**, not five Tier-1 security defects left unfinished by #253.

**Config change in this sprint?** **No.** A PR-count alone does not justify suppressing valid updates. Vite/vitest majors are already ignored; further ignore rules would require package-specific security/hygiene evidence beyond fan-out volume.

---

## 6. Per-PR evidence

### Common facts (all five)

| Field | Value |
|-------|--------|
| Generator | Dependabot version updates (`app/dependabot`) |
| Files touched | `packages/client/package.json`, `packages/client/package-lock.json` only |
| Advisory language in PR body | Compatibility-score badge only; **no CVE/GHSA advisory list** in body |
| Overlap with #253 axios/postcss bumps | **None** (different packages) |
| Current `main` already contains proposed bump? | **No** — versions on `main` remain at “from” versions (axios/postcss already at Tier-1 targets) |
| CI (observed) | Mixed: several jobs FAIL (api-verify, containers, proxy-*, build-and-test on some); lint-build PASS on #254; failures appear **infra/shared**, not used here as merge authorization |

### Surface classification

| PR | Surface | Active vs archive |
|----|---------|-------------------|
| #254 | DEV-ONLY (`devDependencies`) | ACTIVE client workspace |
| #255 | DEV-ONLY (eslint toolchain) | ACTIVE client workspace |
| #256 | ACTIVE runtime (`dependencies`) | ACTIVE client workspace |
| #257 | ACTIVE runtime (`dependencies`) | ACTIVE client workspace |
| #258 | DEV-ONLY (eslint toolchain) | ACTIVE client workspace |

### Tier classification (relative to DEP-SEC program)

| PR | Tier map | Notes |
|----|----------|-------|
| #254 | other residual (bounded patch) | Not in #252 security package table |
| #255 | other residual (major lint toolchain) | Major 6→8; coordinate with parser + #258 |
| #256 | other residual (major app dep) | Major 9→10; not a #252 triage security package |
| #257 | other residual (major app dep) | Major 17→18; not a #252 triage security package |
| #258 | other residual (major lint toolchain) | Major 9→10; coordinate with #255 |

---

## 7. Overlap analysis

| Generated PR | Satisfied by #253? | Duplicate of #253? | Security advisory addressed by #253? |
|--------------|--------------------|--------------------|--------------------------------------|
| #254–#258 | No | No | No — #253 addressed axios/postcss clusters only |

`main` lockfile witness (`25fc189d`):

| Package | Resolved on main |
|---------|------------------|
| axios | **1.19.0** |
| postcss | **8.5.26** |
| vite | 5.4.21 |
| vitest | 2.1.9 |
| `@vue/test-utils` | 2.4.6 |
| `@typescript-eslint/eslint-plugin` | 6.21.0 |
| konva | 9.3.22 |
| marked | 17.0.1 |
| eslint-plugin-vue | 9.33.0 |

---

## 8. Current alert relationship

| Source | Status |
|--------|--------|
| Dependabot Alerts API (`GET .../dependabot/alerts`) | **HTTP 403** — `Resource not accessible by integration` (unchanged from #253) |
| Live alert ledger | **PENDING GITHUB RECALCULATION / OWNER UI WITNESS** |
| Expected residual classes after recalc + archive dismissals | Toolchain (vite/vitest + transitives), out-of-scope Python dev, any non-axios/postcss advisories still open |

No alert is blindly dismissed by this sprint.

---

## 9. Dispositions (generated PRs)

GitHub action for each: **CLOSE — DEFERRED TO CONSOLIDATED TRANCHE** (durable comment posted; PRs closed during DEP-SEC-001B).  
Do **not** merge merely to eliminate the PR.

| PR | Disposition code | GitHub action | Implementation vehicle | Underlying obligation tracked? |
|----|------------------|---------------|------------------------|--------------------------------|
| #254 | **DEFERRED** → Tranche B | CLOSED + comment | Future bounded residual PR under `DEP-SEC-001` / `MAINT-DEFER-004` | Yes — matrix row + SPRINTS |
| #255 | **DEFERRED** → Tranche B (lint majors, coordinated with #258 / parser) | CLOSED + comment | Same Tranche B vehicle | Yes |
| #256 | **DEFERRED** → Tranche B (app major; explicit auth required) | CLOSED + comment | Same Tranche B vehicle | Yes |
| #257 | **DEFERRED** → Tranche B (app major; explicit auth required) | CLOSED + comment | Same Tranche B vehicle | Yes |
| #258 | **DEFERRED** → Tranche B (lint majors, coordinated with #255) | CLOSED + comment | Same Tranche B vehicle | Yes |

**Rationale:** None is DUPLICATE/SUPERSEDED by #253. None is an automatic security defect. All are version-update evidence that must not become five parallel sprints. Closing without merge preserves sequencing ownership under the parent program.

---

## 10. Deferred work (known residuals — TC-08)

| ID | Obligation | Disposition | Trigger / notes |
|----|------------|-------------|-----------------|
| R-01 | Archive Dependabot alerts (9 × vite in `archive/**`, `docs/archive/**`) | **OWNER ACTION** | Dismiss in GitHub UI as unused; template in Tier-1 closeout §5. Agent API 403. |
| R-02 | Alert ledger recalculation witness after #253 + archive dismissals | **OWNER ACTION** / **BLOCKED** (on API) | Owner UI witness; do not invent counts |
| R-03 | Python `services/api/requirements-dev.txt` alert | **OUT OF SCOPE** (standing from #253 ruling) | Separate later disposition; not absorbed into client npm work |
| R-04 | `vite` major 5→6 | **DEFERRED** → **Tranche C** | Trigger: BR-021 resolved **or** explicit manual build-witness authorization |
| R-05 | `vitest` major 2→3 | **DEFERRED** → **Tranche C** | Same trigger; preferred order **vitest → witness → vite** |
| R-06 | BR-021 repair | **NOT APPLICABLE** to DEP-SEC implementation (boundary) | Remains BR lifecycle; Tier-2 must not silently bypass |
| R-07 | Remaining #252 triage packages after axios/postcss (toolchain/transitives: rollup/esbuild/lodash/ws/form-data/follow-redirects as still alerted) | **DEFERRED** → **Tranche B** (security residual) after owner alert witness | Snapshot-dependent; re-ground against live alerts before implementing |
| R-08 | Version-hygiene majors/patches from #254–#258 | **DEFERRED** → **Tranche B** | Not #252 security packages; authorize explicitly before merge |
| R-09 | Ongoing weekly Dependabot PR review | **ACTIVE** ownership | Already in `MAINT-DEFER-004`; PRs enter adjudication before implementation |

---

## 11. Owner actions

1. Dismiss 9 archive alerts (unused) per Tier-1 closeout template.  
2. Witness Dependabot alert recalculation after #253 (axios/postcss clusters expected closed).  
3. Authorize Tranche B / Tranche C implementation only via explicit Dev Order (not by leaving Dependabot PRs open).  
4. Do not treat Dependabot open-PR count as DEP-SEC program completeness.

---

## 12. Implementation grouping (≤2 tranches)

| Tranche | Scope | Gate |
|---------|-------|------|
| **Tranche B** — remaining bounded / residual dependency remediation | Security residuals still open after alert witness (non-vite/vitest); optional coordinated version hygiene from #254–#258 when explicitly authorized | Owner Dev Order; no merge of Dependabot PRs solely because they exist; prefer one consolidated PR |
| **Tranche C** — major toolchain migration | `vitest` 2→3 → stabilize witness → `vite` 5→6 | **BR-021 resolved** or **explicit manual build-witness authorization** |

No third implementation tranche is opened by this consolidation. Hard incompatibility was **not** demonstrated that would require splitting further.

---

## 13. Closure conditions (parent program)

`DEP-SEC-001` may move to **COMPLETE** / **RESOLVED** only when **all** of the following hold:

1. Every row in §9 and §10 has a **terminal** disposition (`COMPLETE`, `SUPERSEDED`, `DUPLICATE`, `ACCEPTED RISK`, `NOT APPLICABLE`, or `OUT OF SCOPE` accepted as terminal by owner) — not merely `ACTIVE` prose.  
2. `DEFERRED` rows either completed or reclassified with accepted terminal disposition.  
3. Owner actions R-01/R-02 witnessed **or** explicitly terminalized (e.g. ACCEPTED RISK with date).  
4. No material residual exists only in PR comments, chat, or unreferenced prose.  
5. Residual Obligations Check (§14) passes against Dev Order, closeouts, and this matrix.

Until then, parent status remains:

```text
DEP-SEC-001
ACTIVE — TIER 1 COMPLETE
```

with remaining work durably deferred/dispositioned.

---

## 14. Residual Obligations Check

Before any sprint/program under this maintenance line is marked resolved, inspect:

- Dev Order / implementation notes  
- Tests / witnesses  
- PR review threads  
- Closeout documents  
- Newly discovered findings (including Dependabot PRs opened by the merge)

for deferred, pending, out-of-scope, owner-action, follow-up, unresolved, blocked, remaining, later, or equivalent language.

**Every material residual must map to a durable child disposition** (this matrix and/or `SPRINTS.md` ID).

Repository discipline authority: `docs/SPRINTS_MAINTENANCE.md` (Rule 8 — Residual Obligations Check).

---

## 15. Evidence limitations

- Dependabot Alerts API **403** in this agent environment — cannot enumerate live open alerts or dismiss.  
- CI reds on #254–#258 are recorded observationally; not used as sole disposition basis.  
- #252 alert counts are a **2026-08-09 snapshot**, not an eternal invariant.  
- Compatibility-score badges are not treated as CVE inventories.  
- Untracked local audit copy `docs/audits/SPRINTS_MAINTENANCE_STOCKPILE_AUDIT_2026-08-07.md` (if present) is **out of scope** for this patch.

---

## 16. Final program state

```text
DEP-SEC-001
STATUS: ACTIVE — TIER 1 COMPLETE
         ALL REMAINING WORK DURABLY DEFERRED/DISPOSITIONED

PR #253 / DEP-SEC-001A / Tier 1
STATUS: COMPLETE

Generated PRs #254–#258
STATUS: DISPOSITIONED — CLOSE / DEFERRED TO TRANCHE B
        (underlying obligations tracked here + MAINT-DEFER-004)

Next implementation vehicles (at most two):
  Tranche B — residual security + authorized version hygiene
  Tranche C — vitest → witness → vite (BR-021 or manual witness)
```

**Invariant:** No material residual obligation may exist only in prose, a review comment, an automated PR, or conversation history.
