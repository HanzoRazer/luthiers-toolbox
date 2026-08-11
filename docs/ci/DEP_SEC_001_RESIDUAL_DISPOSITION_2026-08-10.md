# DEP-SEC-001 — Residual Disposition Matrix (Post-#253)

**Program:** `DEP-SEC-001` (parent dependency-security program)  
**Sprint:** `DEP-SEC-001B` — Post-#253 Residual Consolidation & PR-Fan-Out Control  
**SPRINTS ownership:** `MAINT-DEFER-004`  
**Substrate:** `origin/main` @ `25fc189d` (includes merged PR #253)  
**Matrix date:** 2026-08-10 · **Live alert re-grounding:** 2026-08-11 (§8)  
**Posture:** Governance / evidence / disposition only. **No dependency manifests or lockfiles mutated by this sprint.**

---

## 0. Authority precedence and section kinds

### Source-of-truth precedence

For **parent-program (`DEP-SEC-001`) state and residual disposition**, this matrix is authoritative.
Where documents disagree:

```text
1. docs/ci/DEP_SEC_001_RESIDUAL_DISPOSITION_2026-08-10.md   ← authoritative: parent state + residuals
2. SPRINTS.md § MAINT-DEFER-004                             ← authoritative: SPRINTS ID, status line, ownership
3. docs/ci/DEPENDABOT_TIER1_REMEDIATION_2026-08-10.md       ← authoritative: Tier-1 / DEP-SEC-001A only
4. docs/ci/DEPENDABOT_TRIAGE_AND_DECISION_2026-08-09.md     ← evidence snapshot (2026-08-09); never current state
```

`SPRINTS.md` remains the parking-lot index and owns the registered status line; it deliberately carries
a **summary** and defers rationale here. The Tier-1 closeout is authoritative for what #253 did, and for
nothing beyond it.

### Section kinds

Each section below is one of three kinds. They are mixed by necessity but labelled so future edits do
not blur them:

| Kind | Meaning | Sections |
|---|---|---|
| **DESCRIPTIVE** | observed evidence, with its observation date | §3, §4, §5, §6, §7, §8, §15 |
| **NORMATIVE** | binding disposition or rule | §2, §9, §10, §13, §14, §16 |
| **PLANNING** | proposed sequencing; not yet authorized | §11, §12 |

Descriptive sections state what was observed **and when**. No descriptive claim in this matrix is an
eternal invariant — §8 records one advisory that appeared *after* the 2026-08-09 snapshot, which is the
standing proof of that.

---

## 1. Purpose

Establish a single authoritative residual-obligation record after PR #253 so that:

```text
PR COMPLETE  ≠  PROGRAM COMPLETE
```

Every material dependency-security obligation discovered by or generated from #252/#253 must have one durable disposition before further implementation proceeds. Generated Dependabot PRs are **evidence**, not automatic sprints.

### Execution clarification — historical boundary

DEP-SEC-001B is triggered specifically by the **PR fan-out observed after merge of PR #253** (§5: #254–#258).

The following were **already known when #253 completed**. They are **inherited** `DEP-SEC-001` obligations that must appear in this matrix, but they must **not** be characterized as newly discovered defects or failures caused by #253:

- nine archive-alert dismissals (owner UI);
- GitHub alert-ledger recalculation witness;
- residual `npm audit` surface recorded in the Tier-1 closeout;
- Python `requirements-dev.txt` alert (**OUT OF SCOPE** standing);
- Vite major deferral;
- Vitest major deferral;
- BR-021 dependency / boundary.

```text
PR #253
DEP-SEC-001 / Tier 1
STATUS: COMPLETE
```

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

### What #253 did **not** complete (parent program remains ACTIVE)

**Inherited residuals** (known at Tier-1 closeout; not new defects caused by #253):

- Parent `DEP-SEC-001` closure
- Vite/Vitest majors (held by design)
- BR-021 (boundary; not DEP-SEC implementation)
- Python `requirements-dev.txt` alert (**OUT OF SCOPE** standing)
- Archive Dependabot alert dismissals (owner UI; API 403)
- Residual `npm audit` toolchain surface (closeout witness; not a Tier-1 failure)

**Generated by #253 merge** (fan-out trigger for this sprint):

- Post-merge Dependabot version-update PRs (#254–#258) — side effect of creating intake config

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
| CI (observed 2026-08-10) | Mixed: `api-verify`, `build-and-test`, `Containers`, `proxy-adaptive`, `proxy-parity`, `server-env-check`, `Core CI Summary` FAIL; lint-build PASS on #254. **Root cause identified, not merely "infra/shared":** on #254 (`a9dc78b3`) `api-verify` fails with `SG_SPEC_TOKEN not configured — cannot clone private sg-spec` — GitHub withholds repository secrets from Dependabot-authored PRs. This is **structural for every Dependabot PR**, not a defect in these five. See **R-11** (§10). Not used as merge authorization either way |

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

## 8. Current alert relationship — DESCRIPTIVE (re-grounded 2026-08-11)

> **Correction (2026-08-11).** An earlier revision of this section recorded the Dependabot Alerts API as
> **`HTTP 403` / ledger PENDING OWNER UI WITNESS**. That was an **agent-environment credential
> limitation, not a repository fact**, and stating it unqualified overstated the block. With owner
> credentials the API reads normally (`gh api repos/HanzoRazer/luthiers-toolbox/dependabot/alerts`), and
> **the recalculation this section said was pending has already occurred.** R-02 is discharged
> accordingly (§10).

### Live witness — 2026-08-11, `main` @ `25fc189d`

| Measure | 2026-08-09 snapshot (#252) | **Observed 2026-08-11** |
|---|---|---|
| Open alerts | 65 | **32** |
| critical / high / medium / low | 1 / 28 / 35 / 1 | **1 / 15 / 16 / 0** |
| `axios` + `postcss` open alerts | 32 | **0** |

**Tier-1 is witnessed effective.** The axios and postcss clusters are closed on the live ledger, and
`follow-redirects` and `form-data` cleared transitively with the axios bump. This is the post-merge
witness #253's closeout anticipated — recorded here as observation, not inferred from the merge event.

### Residual surface as observed 2026-08-11

| Package | Alerts | Scope | Max sev | Maps to |
|---|---|---|---|---|
| `vite` | 12 | development | high | **9 archive → R-01** · **3 client → R-04** |
| `js-yaml` | 3 | development | high | R-07 / Tranche B |
| `lodash` | 3 | development | high | R-07 / Tranche B |
| `brace-expansion` | 2 | development | high | R-07 / Tranche B |
| `minimatch` | 2 | development | high | R-07 / Tranche B |
| `picomatch` | 2 | development | medium | R-07 / Tranche B |
| `ws` | 2 | **runtime** | high | R-07 / Tranche B — **only runtime-scope residual** |
| `esbuild` · `flatted` · `js-cookie` · `rollup` | 1 each | development | high/medium | R-07 / Tranche B |
| `vitest` | 1 | development | **critical** | R-05 / Tranche C |
| `pytest` | 1 | development | medium | R-03 — OUT OF SCOPE |

Partition of the 32: **9** archive (R-01, owner dismissal) · **4** Tranche C (3 client `vite` + 1
`vitest`) · **1** out-of-scope Python · **18** Tranche B candidates across 10 packages, of which
**only `ws` (2) is runtime-scope** — the other 16 are development-scope toolchain.

The single `critical` remains `vitest` GHSA-5xrq-8626-4rwp, whose precondition (Vitest UI server
listening) is not met in this repository — established in #252 and unchanged.

### Snapshots are not invariants — demonstrated

`js-yaml` moved **2 → 3** alerts between the 2026-08-09 snapshot and this witness: a new advisory
appeared with no repository change. Any count in this matrix is true as of its stated observation date
and must be re-grounded before implementation, not carried forward.

No alert is dismissed by this sprint.

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

**Origin legend:** `INHERITED` = already known when #253 completed (not a #253 failure). `FAN-OUT` = generated after #253 merge. `ONGOING` = standing ownership.

| ID | Origin | Obligation | Disposition | Trigger / notes |
|----|--------|------------|-------------|-----------------|
| R-01 | INHERITED | Archive Dependabot alerts (9 × `vite` in `archive/**`, `docs/archive/**`) | **OWNER ACTION** | **Still open — count re-confirmed at 9 on 2026-08-11 (§8).** Dismiss as unused; template in Tier-1 closeout §5. Dismissal requires write scope the read witness does not imply. Durable fix is the `.github/dependabot.yml` path exclusion (§11 item 5), which stops regeneration. |
| R-02 | INHERITED | Alert ledger recalculation witness after #253 | ~~OWNER ACTION / BLOCKED~~ → **COMPLETE (witnessed 2026-08-11)** | **Discharged.** Recalculation has occurred: **65 → 32** open; `axios` + `postcss` → **0**; `follow-redirects`/`form-data` cleared transitively. Evidence in §8. The prior `BLOCKED (on API)` status was an agent-credential limit, not a repository block — the API reads normally with owner credentials. |
| R-03 | INHERITED | Python `services/api/requirements-dev.txt` alert | **OUT OF SCOPE** (standing from #253 ruling) | Separate later disposition; not absorbed into client npm work |
| R-04 | INHERITED | `vite` major 5→6 | **DEFERRED** → **Tranche C** | Trigger: BR-021 resolved **or** explicit manual build-witness authorization |
| R-05 | INHERITED | `vitest` major 2→3 | **DEFERRED** → **Tranche C** | Same trigger; preferred order **vitest → witness → vite** |
| R-06 | INHERITED | BR-021 repair | **NOT APPLICABLE** to DEP-SEC implementation (boundary) | Remains BR lifecycle; Tier-2 must not silently bypass |
| R-07 | INHERITED | Remaining #252 triage packages after axios/postcss | **DEFERRED** → **Tranche B** | **Re-grounded 2026-08-11 (§8): 18 alerts / 10 packages** — `js-yaml` 3, `lodash` 3, `brace-expansion` 2, `minimatch` 2, `picomatch` 2, `ws` 2, `esbuild`/`flatted`/`js-cookie`/`rollup` 1 each. **Only `ws` (2) is runtime-scope**; the other 16 are development-scope toolchain. Re-ground again before implementing — `js-yaml` gained an alert after the snapshot. |
| R-08 | FAN-OUT | Version-hygiene majors/patches from #254–#258 | **DEFERRED** → **Tranche B** | Not #252 security packages; none appears in the live alert set of §8, so this is hygiene, not security. Authorize explicitly before merge |
| R-09 | ONGOING | Ongoing weekly Dependabot PR review | **ACTIVE** ownership | Already in `MAINT-DEFER-004`; PRs enter adjudication before implementation |
| R-10 | INHERITED | Residual `npm audit` surface in `packages/client` after Tier-1 patch (**21** issues at closeout witness) | **DEFERRED** → **Tranche B** / **Tranche C** as classified | Documented in Tier-1 closeout §6; **not** a Tier-1 failure criterion. Largely overlaps R-04/R-05/R-07. **Not independently re-verified here** — `npm audit` needs an install this sprint did not run, so the 21 figure remains a closeout-witness claim, not a live one |
| R-11 | FAN-OUT | **Dependabot-authored PRs structurally cannot pass `api-verify`** | **ACCEPTED CONSTRAINT** — forces consolidated-PR implementation | Observed on #254 (`a9dc78b3`): `api-verify` fails with `SG_SPEC_TOKEN not configured — cannot clone private sg-spec`. GitHub does not expose repository secrets to Dependabot-authored PRs. **Consequence: merging any Dependabot PR directly can never be CI-verified**, which makes §12's "prefer one consolidated PR" a **requirement**, not a preference. Adjacent to BR-022 (`SG_SPEC_TOKEN` env-guard rollout, `docs/ci/CI_HYGIENE_DEBT_PATCH_PLAN.md`) and CI-RED-001. Not a DEP-SEC defect; recorded so the constraint is not rediscovered |

---

## 11. Owner actions — NORMATIVE

1. Dismiss the **9** archive alerts (unused) per Tier-1 closeout template — count re-confirmed 2026-08-11 (§8).
2. ~~Witness Dependabot alert recalculation after #253~~ — **DONE 2026-08-11.** 65 → 32; `axios`/`postcss` → 0 (§8). Retained struck-through rather than deleted so the discharge is auditable.
3. Authorize Tranche B / Tranche C implementation only via explicit Dev Order (not by leaving Dependabot PRs open).
4. Do not treat Dependabot open-PR count as DEP-SEC program completeness.
5. **Add `archive/**` and `docs/archive/**` path exclusions to `.github/dependabot.yml`.** Dismissing the 9 archive alerts (action 1) clears the ledger once; the exclusion stops them regenerating and is the durable fix. Recommended in #252 §7 and not yet implemented.

---

## 12. Implementation grouping (≤2 tranches)

| Tranche | Scope | Gate |
|---------|-------|------|
| **Tranche B** — remaining bounded / residual dependency remediation | Security residuals open after the §8 witness: **18 alerts / 10 packages**, of which only `ws` (2) is runtime-scope. Optional coordinated version hygiene from #254–#258 when explicitly authorized | Owner Dev Order; no merge of Dependabot PRs solely because they exist. **One consolidated PR is required, not preferred** — per R-11 a Dependabot-authored PR can never pass `api-verify`, so it cannot be CI-verified before merge |
| **Tranche C** — major toolchain migration | `vitest` 2→3 → stabilize witness → `vite` 5→6 | **BR-021 resolved** or **explicit manual build-witness authorization** |

No third implementation tranche is opened by this consolidation. Hard incompatibility was **not** demonstrated that would require splitting further.

---

## 13. Closure conditions (parent program)

`DEP-SEC-001` may move to **COMPLETE** / **RESOLVED** only when **all** of the following hold:

1. Every row in §9 and §10 has a **terminal** disposition (`COMPLETE`, `SUPERSEDED`, `DUPLICATE`, `ACCEPTED RISK`, `NOT APPLICABLE`, or `OUT OF SCOPE` accepted as terminal by owner) — not merely `ACTIVE` prose.  
2. `DEFERRED` rows either completed or reclassified with accepted terminal disposition.  
3. Owner actions witnessed **or** explicitly terminalized (e.g. ACCEPTED RISK with date). **R-02 is
   witnessed as of 2026-08-11 (§8); R-01 remains outstanding**, and R-01 should be paired with the
   `.github/dependabot.yml` archive exclusion (§11 item 5) so it cannot recur.  
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

## 15. Evidence limitations — DESCRIPTIVE

- ~~Dependabot Alerts API **403** — cannot enumerate live open alerts.~~ **Superseded 2026-08-11.** The
  403 was scoped to one agent environment's credentials, not to the repository. The alert set was
  enumerated successfully with owner credentials and is recorded in §8. **Alert *dismissal* was still not
  performed** — that needs write scope the read witness does not imply, so R-01 stands as OWNER ACTION.
- **`npm audit` residual (R-10, "21 issues") was not independently re-verified.** It requires an install
  this sprint did not run. It remains a Tier-1 closeout-witness claim carried forward, not a live measure.
- CI reds on #254–#258 are recorded observationally and are **not** used as disposition basis. Their
  cause is now identified (R-11, missing `SG_SPEC_TOKEN` on Dependabot PRs) rather than left as
  "infra/shared".
- #252 alert counts are a **2026-08-09 snapshot**. §8 supersedes them for current state and demonstrates
  empirically that such counts drift (`js-yaml` 2 → 3 with no repository change).
- Compatibility-score badges are not treated as CVE inventories.
- `docs/audits/SPRINTS_MAINTENANCE_STOCKPILE_AUDIT_2026-08-07.md` was searched for and **does not exist**
  — not in `docs/audit/` or `docs/audits/`, not in either repository's tracked files, not in all-branch
  history (`--diff-filter=A`), not in 14 stashes, not under `C:\tmp` or `Downloads` at full depth. It is
  **confirmed absent**, not conditionally out of scope. Same class as AUDIT-002 F-11 (an analysis that
  survived only outside git). Nothing in this matrix depends on it.

---

## 16. Final program state

```text
DEP-SEC-001
STATUS: ACTIVE — TIER 1 COMPLETE
        ALL REMAINING WORK DURABLY DEFERRED/DISPOSITIONED

PR #253 / DEP-SEC-001A / Tier 1
STATUS: COMPLETE — witnessed effective 2026-08-11
        open alerts 65 -> 32; axios + postcss -> 0

Generated PRs #254–#258
STATUS: DISPOSITIONED — CLOSED / DEFERRED TO TRANCHE B
        (durable comment on each; obligations tracked here + MAINT-DEFER-004)

Residual surface (observed 2026-08-11, 32 open):
   9  archive vite        -> R-01  owner dismissal + dependabot.yml exclusion
   4  vite/vitest client  -> Tranche C
   1  pytest (python dev) -> R-03  OUT OF SCOPE
  18  toolchain/transitive-> Tranche B  (only `ws` x2 is runtime-scope)

Next implementation vehicles (at most two):
  Tranche B — residual security + authorized version hygiene
              MUST be one consolidated PR (R-11: Dependabot PRs
              cannot pass api-verify — no SG_SPEC_TOKEN)
  Tranche C — vitest -> witness -> vite (BR-021 or manual witness)
```

**Invariant:** No material residual obligation may exist only in prose, a review comment, an automated PR, or conversation history.
