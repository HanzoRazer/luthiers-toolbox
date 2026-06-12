# Pre-Governance-Sprint Build Reconstruction — Forensic Audit

**Created:** 2026-06-01
**Author context:** READ-ONLY forensic reconstruction. No commits, edits, stash pops/drops,
branch deletions, gc, or prune were performed. This document is itself **untracked by design**
(it inventories recovery candidates; it must not ride into a feature PR). Delete after the
codeowner has executed the recovery decisions in §4.
**Repo:** `C:\Users\thepr\Downloads\luthiers-toolbox`
**Method:** `git log --all`, `git fsck --no-reflogs --lost-found`, `git stash show --stat
--include-untracked`, `git show -s` — all read-only plumbing.

> **Honesty contract (per the audit prompt):** "not found" means not found, never "didn't
> exist." Recovery confidence is tagged per item: **COMMITTED** (durable) / **STASHED**
> (recoverable) / **DANGLING** (reflog/fsck-only, fragile) / **UNTRACKED-ON-DISK** (fragile) /
> **NOT FOUND**.

---

## 1. Timeline anchor

| | |
|---|---|
| **Anchor event** | Governance sprint registered in `SPRINTS.md` (the "GOVERNANCE CONVERGENCE" parking lot) |
| **Anchor commit** | `464920f1` — *"docs: add GOV-CONVERGE parking lot to SPRINTS (governance sprint tail)"* |
| **Anchor date** | **2026-05-28 15:30:57 -0500** |
| **Window** | **[2026-05-14 00:00 → 2026-05-28 15:31]** (anchor − 14 days → anchor) |

Corroborating markers inside the window: first CI-RED-015 registration `6f3bacbe` (05-28 09:40),
first CI-RED-015-D-a wire audit `d9d51f5f` (boundary), GOV-CONVERGE tighten `35267e0a` (05-28 15:56,
just past anchor). The anchor is unambiguous: GOV-CONVERGE did not exist in `SPRINTS.md` before
`464920f1`.

> **Caveat on `--since/--until`:** git filters by commit date. Rebased/cherry-picked work can
> carry author dates outside the window; a few items below are placed by author date and noted.

---

## 2. The sprints active in the window — honest count

The prompt frames "three sprints." **The evidence shows more than three concurrent threads**
in this window. Forced bucketing would violate the honesty contract, so the threads are listed
in full; the **three dominant, build-philosophy-distinct lines** (the comparison subjects) are
marked ★. The governance-convergence line is the sprint being *born* at the anchor, not one that
preceded it.

| Thread | Marker IDs | Dominant state |
|---|---|---|
| ★ **CI-RED — CI hygiene** | CI-RED-001, 005–015 | COMMITTED (PRs #51–#72) |
| ★ **DXF-lifecycle / IBG provenance** | DO_75–DO_80, R2 export wrapper | COMMITTED + several STASHED "wip-unrelated" |
| ★ **Governance inventory / convergence** | build_governance_inventory, unified-gate-blocking, guard_status Phase 2B | **heavily STASHED/DANGLING — largely never landed** |
| Vectorizer / three-loop semantic migration (**CROSS-REPO**) | Tier-A relocation `dcabee7c`, research wave-1c | partial; full diffs live in **`vectorizer-sandbox`** (see §6) |
| MRP-5X runtime-boundary / capability guard | `dde5480b`, `124ad198` | STASHED/DANGLING |
| Confidence-envelope interoperability | `4a20b1a2`, `8c259392`, DEV_ORDER_NAMESPACE_SUMMARY | STASHED |
| Acoustic-jumbo business layer | PR #58, stash@{0} | COMMITTED; stash is scratch only |

**Unassignable / cannot bucket without guessing:** `564b4559` (bare "Merge branch 'main'",
05-27), `71cee0a1` ("docs(audit): FRET-A … completion verification", 05-27 — FRET sprint, not
one of the three), stash@{8}/@{9} (ingest-audit-log: `.claude` settings + large binary image
blobs — asset junk, not sprint work).

---

## 3. Per-sprint reconstruction

### 3.1 ★ CI-RED — CI hygiene remediation

**Build philosophy (from SPRINTS.md entries + commit cadence):** tightest discipline of the
three. Numbered atomic items (CI-RED-001…015), **one-cause-per-PR**, explicit
**Restore trigger** (done-condition) per entry, "honest probe log" commits when fighting flaky
auth (`149e9c7a` "honest CI-RED-001 probe log"; `1cddcbd8` "probe 5 — re-run after token
rotation"). Dev-order structure: `Status / last_verified / Why open / Restore trigger`.
Detail dev order also exists as `docs/handoffs/CI_RED_015D_OPEN_DECISIONS.md` ("DEV ORDER —
DO-015D-CLOSE-01").

**Committed work (COMMITTED — durable):** the dense 05-27→05-28 run, all merged via PR:
`51c9f1ed`/`1dfcca98` (#51 SG_SPEC_TOKEN), `0d41d994`/#52, `bcca38ed`/#55, `20df2966`/#57,
`c5d5b0b4`/#61, `14226599`/#62, `084c2a2c`/#63, `b77c02bc`/#64, `79b83e9f`/#65, `933cd897`/#66,
`39b66c91`/#67, `9d1ec306`/#68, `6f3bacbe`/#69, `4570a876`/#70, `95c33846`/#71, `f0d05f02`+`83e5fbb8`/#72.

**Stranded (DANGLING):** `aab69089` (05-28 11:38) *"fix(ci): resolve text-masking mask.sum
_NoValueType on CI (CI-RED-015-A tail)"* — **superseded** by the landed `95c33846` (the "isolate
numpy binding" cause-fix that replaced the symptom patch). Almost certainly the reverted
wrong-diagnosis attempt; recover only to confirm, not to land.

### 3.2 ★ DXF-lifecycle / IBG provenance (DO_75–DO_80)

**Build philosophy (from `DO_78_IBG_PROVENANCE_R_NAMESPACE_HANDOFF.md` + siblings):** formal
**`DO_NN_*.md` dev-order documents** with phase tables, **acceptance criteria**, and **repo
verification commands** (`088b6200`: "Align phase table, acceptance criteria, and repo
verification commands"). Higher ceremony than CI-RED, gated by named phases (3A/3A2/3A4/3B).
Dev orders located: `DO_75_DXF_LIFECYCLE_PHASE_3A2`, `DO_76…3A4`, `DO_77…3B`,
`DO_78_IBG_PROVENANCE_R_NAMESPACE`, `DO_80_IBG_PROVENANCE_R2_ROLLOUT_ANNOTATED`,
`MRP_6C_IBG_PROVENANCE_RATIFICATION_PREP`. (DO_79 referenced in commits `918f84d9`/`2c64a733`
but **no `DO_79_*.md` file found** — NOT FOUND as a standalone doc; the R2 wrapper work itself
did land in `918f84d9`.)

**Committed (COMMITTED):** `6cf6f6b6`/`088b6200` (DO 78 handoff), `918f84d9` (DO 79 R2 wrapper),
`a8e0c18a`/#45 (Phase D provenance bridge), `cb3b94b1`/#46 (CamIntent restore), `f25bb949`/#54+#56
(jumbo dimension alignment), `088b6200` on branch `feat/dxf-lifecycle-phase-3b`.

**Stranded (STASHED):**
- `stash@{1}` (05-25, on `feat/dxf-lifecycle-phase-3a-2`, *"wip-unrelated-3a3"*) — **mislabeled
  "unrelated": it contains a full external-repo doc import** (`docs/audit-sources/CAM-Assist-Blueprint/`:
  README +536, CLAUDE.md, `ADOPTED_CAM_CAPABILITIES.md` +238, taxonomy +223, a `schema_validation.yml`
  workflow). This is cross-repo audit material parked mid-DXF-work. Recoverable; assess against
  whether CAM-Assist-Blueprint is wanted in-repo (cf. GOV-CONVERGE-003/D2, which chose *gitignore*
  for `docs/audit-sources/`).
- `stash@{2}` (05-25, on `feat/confidence-envelope-interoperability`, *"wip-before-dxf-3a"*) —
  `DEV_ORDER_NAMESPACE_SUMMARY_2026-05-25.md` (+77). A dev-order governance artifact stranded.
- `577bd114` (DANGLING, 05-25, "On feat/dxf-lifecycle-phase-3a: unrelated-wip-before-do75"),
  `9fdb441f` (DANGLING, 05-25, "wip-unrelated-3a3") — stash plumbing for the above.

### 3.3 ★ Governance inventory / convergence

**Build philosophy:** the *least*-landed, *most*-stranded of the three — its hallmark is work
done then **stashed/abandoned rather than committed to a branch**. Tooling-centric
(`build_governance_inventory.py`, `governance_inventory.json/.md`, ontology scanner, unified
gate "blocking mode", `guard_status` lifecycle-matrix Phase 2B). No clean `DO_NN` doc series
found for this line in the window — its "dev order" was apparently in-session, which is exactly
why it stranded.

**Committed (COMMITTED):** little landed *in-window* on a durable branch. `reports/governance/
governance_inventory.md` **is** tracked on `main` today, so some of this graduated later —
**diff stranded versions against current `main` before resurrecting** (may be superseded).

**Stranded (DANGLING — most fragile, real abandoned commits, not stash plumbing):**
- `43b07017` (05-20) *"feat(governance): add governance document inventory"*
- `d1677e98` (05-20) *"feat(governance): promote unified governance gate to blocking mode"*
- `c35c4ff9` (05-20) *"fix(governance): ensure deterministic output from inventory scanner"*
- `ac9f70ee` (05-20) *"feat(governance): normalize ontology script output format"*
- `f89e77a1` / `45a472a6` (05-21) *"feat(governance): add guard_status tracking to lifecycle matrix (Phase 2B)"*

**Stranded (STASHED):**
- `stash@{4}` (05-20) acoustics `index.ts` (+11) — trivial.
- `stash@{5}` (05-20, "Untracked files before rebase") — `MRP_5M_RUNTIME_ADMISSION_CONTROL.md`
  (+403), `check_all_ci.json` (+155). Substantial governance doc.
- `stash@{6}` (05-20, "Linter changes to inventory files") — the big one:
  `governance_inventory.json` **+1662/−~** , `governance_inventory.md` (+618/−), `build_governance_inventory.py`
  (+38), `test_build_governance_inventory.py` (+79), `cam_manifest.py` (+7), `ApertureWorkspace.vue`.
- `stash@{7}` (05-20, `governance-execution-alignment`, "unrelated changes before PR4 branch") —
  `SPRINTS.md` (+79), `MORPHOLOGY_FAILURE_TAXONOMY.md`, acoustics components, `diagnosticSnapshot.ts`.

---

## 4. Off-state break point per sprint

| Sprint | Last ON-scope artifact | First drift / off-state signal |
|---|---|---|
| **CI-RED** | `95c33846` (#71, cause-fix for 015-A), 05-28 11:56 | `aab69089` dangling symptom-patch (same morning) was the *abandoned* wrong path; the line otherwise stayed on-scope through the anchor. **Healthiest line.** |
| **DXF-lifecycle / IBG** | `918f84d9` DO 79 R2 wrapper (05-26), merged #45/#46 | Drift = the **"wip-unrelated"** stashes on 3a/3a-2 (05-25): work parked *as* the phase advanced, incl. an entire external-repo import filed under a DXF branch. Scope bled from DXF→CAM-Assist import + dev-order-namespace. |
| **Governance inventory** | last durable graduation unclear (some landed later on `main`) | **Clearest off-state of all three:** a 05-20→05-21 burst of `feat(governance)` commits + 4 stashes that **never reached a PR**. Sessions did the work, stashed/abandoned, and the next durable governance artifact is the *anchor itself* (`464920f1`, 05-28) — i.e. the line went off-state for ~8 days and was effectively re-started as GOV-CONVERGE. |

**Session-boundary artifacts (Phase 4 cross-ref):** `*RECOVERY*.md` in the window: **NOT FOUND**
(the `PR77_RECOVERY.md` / CI-RED dead-shell handoffs are 05-29/05-30 — *after* the anchor, and
were triaged+deleted in a later session). `artifacts/recovery/recovery_report.md` exists but is
not window-dated. So for this window the **stashes and dangling commits ARE the session-death
markers** — there was no written recovery bookmark; work was preserved (if at all) by `git stash`.

---

## 5. Resurrection map — ordered by fragility (recover top items FIRST)

> **All recovery is PROPOSED, not executed.** The codeowner runs these deliberately. None of the
> commands below mutate state; the *recovery* step (cherry-pick / branch / stash apply) is left
> for explicit execution.

### Tier 1 — DANGLING (fsck-only; lost on next `git gc --prune`). **Most urgent.**
Genuine abandoned commits (not stash plumbing), governance-inventory line:
`43b07017`, `d1677e98`, `c35c4ff9`, `ac9f70ee`, `f89e77a1`/`45a472a6`, and MRP-5X `dde5480b`.
- **Propose:** tag them immediately so gc can't reap them, e.g.
  `git tag salvage/gov-inventory-43b07017 43b07017` (tagging is additive/read-safe). Then inspect
  with `git show <sha>` and decide per-commit. Do this **before** any `gc`.
- CI-RED `aab69089`: tag `salvage/ci-red-015a-superseded` for the record, then likely discard
  (superseded by `95c33846`).

### Tier 2 — STASHED (durable until explicitly dropped, but easy to lose in a stash purge).
Priority by content value:
1. `stash@{6}` — governance inventory tooling + data (largest unique footprint).
2. `stash@{5}` — `MRP_5M_RUNTIME_ADMISSION_CONTROL.md` (+403).
3. `stash@{1}` — CAM-Assist-Blueprint external-repo import (decide vs D2 gitignore policy).
4. `stash@{2}` — `DEV_ORDER_NAMESPACE_SUMMARY`.
5. `stash@{7}`, `stash@{3}` — mixed SPRINTS/acoustics WIP (diff against `main` first; likely partly landed).
- **Propose:** for each, `git stash branch salvage/<name> stash@{N}` (creates a branch from the
  stash's base + applies it **without dropping** the stash — the safest recovery). Do NOT `pop`.
- **Skip:** `stash@{0}` (test_temp scratch), `stash@{8}`/`@{9}` (binary image blobs + `.claude`).

### Tier 3 — CROSS-REPO (see §6) — needs the sibling repo to reconstruct fully.

### Tier 4 — COMMITTED (durable, no action) — all merged CI-RED / IBG / acoustic-jumbo PRs.

---

## 6. Cross-repo flag — second repo IS needed for one sprint

The **vectorizer / three-loop semantic-migration** sprint is only *partially* visible here:
- In-repo evidence: `dcabee7c` (DANGLING, 05-20) *"WIP on feat/tier-a-relocation-removal:
  4cbe56ed chore(vectorizer): remove Tier A modules relocated to vectorizer-sandbox"*, and the
  research line `efb60349`/`1790f6bb`/`stash@{3}` (wave-1c semantic artifact quality, 05-21).
- The **removal side** lives here; the **landing side** (cognitive_extractor, extract_body_grid,
  agentic_supervisor, the three-loop/AGE design) lives in the sibling **`vectorizer-sandbox`**
  (symlinked at `docs/audit-sources/vectorizer-sandbox`; migration recorded in
  `VECTORIZER_SANDBOX_CHRONOLOGY.md` — "May 20: migration begins").
- **To reconstruct that sprint's full diffs, re-run Phases 1–2 inside `vectorizer-sandbox`**
  (its own `git log`/`fsck`/`stash`). This audit deliberately did not enter the sibling repo.

---

## 7. Build-philosophy comparison (the forensic question)

| Dimension | CI-RED | DXF-lifecycle / IBG | Governance inventory |
|---|---|---|---|
| **Dev-order form** | SPRINTS.md parking-lot entries + DO-015D-CLOSE-01 | Formal `DO_NN_*.md` docs w/ phase tables | In-session, **no durable DO doc** |
| **Granularity** | Atomic, one-cause-per-PR | Phase-gated (3A/3A2/3A4/3B) | Burst of mixed feat commits |
| **Gate discipline** | Explicit **Restore trigger** per item; CI-green = DoD | **Acceptance criteria + repo verification commands** | Weakest — "blocking mode" promoted but work stashed |
| **Scope control** | Tightest; honest-probe logging when blocked | Leaky — "wip-unrelated" stashes, external-repo import under a DXF branch | Leaky — acoustics/SPRINTS edits mixed into every stash |
| **DoD rigor** | High (gate-green, verifiable) | High on paper (criteria), lower in practice (stranded WIP) | Low (never reached PR; re-started as GOV-CONVERGE) |
| **Landing rate** | **High** (≈22 commits → PRs #51–72) | Medium (core landed, edges stranded) | **Low** (mostly dangling/stashed) |

**Conclusion.** The three lines sit on a clear gradient of build discipline:
**CI-RED (highest)** — tight, atomic, gate-green, honest about failure → almost everything landed.
**DXF/IBG (middle)** — high *documented* rigor (`DO_NN` + acceptance criteria) but scope leaked
into "unrelated" stashes, so the edges stranded while the core landed.
**Governance-inventory (lowest)** — substantial real work (inventory tooling, unified gate,
guard_status) executed in-session **without a durable dev-order doc and without reaching a PR**;
it went off-state ~05-21 and was effectively re-booted as the GOV-CONVERGE parking lot at the
anchor (`464920f1`). That re-boot is the strongest signal that the governance line needed the
parking-lot discipline the other two already had.

---

## 8. Discipline statement

Read-only throughout. No commit, edit, stash pop/drop, branch deletion, `gc`, `prune`, or
state-discarding checkout was performed. Current branch at audit time:
`fix/ci-red-002-legacy-usage-gate-scope`; working tree clean. The one urgent recommendation is
**§5 Tier 1: tag the six dangling governance-inventory/MRP-5X commits before any future `git gc`**
— they are the only items that can age out. Everything else is stash- or commit-durable.

---
---

# ADDENDUM — Cross-Verification (Second Independent Audit)

**Appended:** 2026-06-01 · **By:** independent second forensic pass (read-only)
**Purpose:** Two audits were run against this repo for verification. This addendum reconciles the
second pass against the document above (hereafter "Audit-1"), correcting one material census gap
and confirming the rest. No edits to Audit-1's text; this is additive only. No commits, stash
pops/drops, branch deletions, `gc`, or `prune` were performed.

## A. Where the two audits AGREE (confirmed against repo ground truth)

- **Anchor:** `464920f1`, **2026-05-28 15:30:57 -0500**, window **[2026-05-14 → 2026-05-28]**. ✔
- **Off-state narrative:** the governance-inventory line went off-state ~05-20→05-21 (work done,
  stashed/abandoned, never PR'd) and was effectively *re-booted* as the GOV-CONVERGE parking lot at
  the anchor. ✔ Strongly corroborated by the orphaned-commit cluster below.
- **Build-philosophy gradient:** CI-RED (tightest, highest landing rate) → DXF/IBG (high documented
  rigor, leaky edges) → Governance-inventory (lowest — substantial work, no durable dev-order, mostly
  un-landed). ✔
- **Cross-repo flag:** the vectorizer/three-loop line is only partially visible here; full diffs live
  in sibling **`vectorizer-sandbox`**; a second-repo pass is required (also true of GOV-CONVERGE-005
  `tap_tone_pi`, 27 stranded commits). ✔ Three sibling git repos confirmed present:
  `CNC-Production-Shop`, `ltb-woodworking-studio`, `luthiers-toolbox`.
- **`aab69089`** (CI-RED-015-A symptom patch) is **superseded** by the landed cause-fix `95c33846`. ✔

## B. Material CORRECTION — the dangling census was UNDERCOUNTED by BOTH passes

Authoritative count from `git fsck --no-reflogs | grep "dangling commit"`:

> **42 dangling commits total; 32 fall in-window.** (Audit-1's body enumerated ~10–12; an earlier
> draft of the second pass saw only 6 — a `head -40` truncation of the fsck output. Neither is the
> full set.) Audit-1's instinct was right; the list was incomplete.

Authoritative fragility split of the 32 in-window dangling commits (`git branch --contains` +
`git reflog stash` for each):

**B.1 — TRULY ORPHANED (not on any branch, not in the current stash reflog) — most fragile.**
These survive only via the HEAD/branch reflog and will be reaped at reflog expiry (`gc.reflogExpire`,
default ~90d) on the next `git gc`. ~23 commits:

| SHA | Date | Subject | Sprint line |
|-----|------|---------|-------------|
| `43b07017` | 05-20 | feat(governance): add governance document inventory | Gov-inventory |
| `d1677e98` | 05-20 | feat(governance): promote unified governance gate to blocking mode | Gov-inventory |
| `c35c4ff9` | 05-20 | fix(governance): deterministic inventory scanner output | Gov-inventory |
| `ac9f70ee` | 05-20 | feat(governance): normalize ontology script output | Gov-inventory |
| `f89e77a1` `45a472a6` | 05-21 | feat(governance): guard_status lifecycle matrix (Phase 2B) | Gov-inventory |
| `efb60349` | 05-21 | docs(research): establish semantic artifact quality layer | Research/wave-1c |
| `124ad198` `dde5480b` | 05-23 | MRP-5X runtime capability regression guard (WIP) | MRP-5X |
| `dcabee7c` | 05-20 | WIP: remove Tier A modules relocated to vectorizer-sandbox | Vectorizer (cross-repo) |
| `4a20b1a2` | 05-25 | WIP on confidence-envelope: MRP-6D capability integration audit | DXF/MRP |
| `577bd114` | 05-25 | On dxf-lifecycle-3a: unrelated-wip-before-do75 | DXF-lifecycle |
| `6e485c05` | 05-27 | On ci-red-001: jumbo-dimension-consistency-wip | IBG-jumbo |
| `3f5cb833` | 05-27 | On jumbo-family-geometry-bug: ci-api-verify-preflight | CI-RED/IBG |
| `f8928299` | 05-27 | WIP on acoustic-jumbo-business-layer | Business |
| `aab69089` | 05-28 | CI-RED-015-A symptom patch (superseded) | CI-RED |
| `4310d56a` `cb9bcde6` | 05-14/18 | WIP on wood-shrinkage-data-integrity / C0-C1 constitutional baseline | Data-integrity |
| `8fa1244c` | 05-20 | WIP on cam-complexity-reduction: @safety_critical decorators | CAM-safety |
| `d682a13b` | 05-20 | WIP on main: technical debt audit report | Audit |
| `01f01368` | 05-21 | On runtime-boundary-2b-guard-rollout: unrelated WIP | Runtime-boundary |
| `71cee0a1` | 05-27 | docs(audit): FRET-A + FRET-CONSOLIDATION-1 verification | FRET (not one of the 3) |
| `564b4559` | 05-27 | bare "Merge branch 'main'" | unassignable |

**B.2 — STASH-REACHABLE (durable in `refs/stash` until explicitly dropped).** 7 commits, matching
Audit-1 §4 stashes: `1ed46b81` `6cc9e708` `9cc238be` (governance-inventory-scanner),
`c817e9cb` (governance-execution-alignment), `1790f6bb` (research wave-1c),
`8c259392` (confidence-envelope), `9fdb441f` (dxf-lifecycle-3a-2).

**Net effect on Audit-1's resurrection map:** §5 Tier 1 should be **broadened** from "six commits" to
the **~23 orphaned commits in B.1**. The three previously-unlisted clusters that most deserve a
salvage tag: **MRP-5X** (`124ad198`,`dde5480b`), **wood-shrinkage-data-integrity** (`4310d56a`,
`cb9bcde6` — includes a "C0/C1 constitutional foundation baseline"), and the **CAM @safety_critical
decorators** WIP (`8fa1244c`). Audit-1's recommended action (additive `git tag salvage/...` before any
`gc`) stands and now applies to the full B.1 set.

## C. Landed-status of the orphaned set (honesty: partial verification)

Spot-checks performed (others NOT verified — diff before recovery):
- `6e485c05` (jumbo WIP) → **landed**: `test_jumbo_dimension_consistency.py` is tracked on `main`
  via `f25bb949`/PR#56. Superseded.
- `aab69089` → **superseded** by `95c33846` (landed). Do not re-land.
- Governance-inventory cluster (`43b07017` …) → **partially landed**: `reports/governance/
  governance_inventory.md` is tracked on `main`, so some graduated later — the orphaned commits are
  in-session versions; **diff against `main` before resurrecting** (likely superseded in part).
- `124ad198`/`dde5480b` MRP-5X → base commits (`0f386975`, `905c19f0`) are reachable on live
  `mrp-5x-*` branches; only the **WIP delta** is orphaned. Low loss risk.
- Remaining B.1 items: landed-status **UNVERIFIED** — reported as orphaned, not as lost. Do not round
  up to "preserved."

## D. Reconciling the "three sprints" divergence

Audit-1 names the three comparison subjects **CI-RED / DXF-lifecycle-IBG / Governance-inventory** and
explicitly treats GOV-CONVERGE as *the sprint being born at the anchor, not one that preceded it.*
The second pass initially leaned toward **CI-RED / GOV-CONVERGE / MRP-reconstruction**. Reconciled
verdict: **Audit-1's split is better supported for the in-window evidence** — each of its three lines
has a *distinct stranded-work footprint* (CI-RED → near-zero strand; DXF/IBG → "wip-unrelated"
stashes; Gov-inventory → the orphaned B.1 cluster), which is exactly the build-philosophy signal the
task asks to compare. GOV-CONVERGE is correctly characterized as the **anchor-birth re-boot** of the
off-state governance line, not a fourth windowed sprint. The MRP/CAM/DXF reconstruction namespaces are
the *parent program* under which DXF-lifecycle/IBG sits. No contradiction — a labeling difference,
resolved in Audit-1's favor.

## E. NOT-FOUND items — independently confirmed

Four artifacts present as untracked (`??`) at this session's start are now **absent from disk and
were never git-tracked** (no commit, no stash, no blob): `PR77_RECOVERY.md`, `create_boe_pr.ps1`,
`docs/handoffs/CI_RED_015D_COMMIT_HANDOFF.md`, `docs/handoffs/DEV_HANDOFF_2026-05-30_CI_REMEDIATION.md`.
This is consistent with Audit-1 §4 ("*RECOVERY*.md NOT FOUND in window"): they are 05-29/30 (post-anchor)
session-death scratch, triaged and deleted in the 05-31 disentangle. **Git-unrecoverable**; only Windows
Recycle Bin / File History / editor local-history could restore the originals. Their durable substance
most plausibly survives in committed equivalents (`CI_RED_015D_OPEN_DECISIONS.md` on `main`; the CI-RED
commit chain; PR#77 merge `88d24f4a`) — **unverifiable**, so logged as a real gap.

## F. Verdict

The two audits **agree on every conclusion** (anchor, window, off-state break, build-philosophy
gradient, cross-repo flag). The only divergence is **completeness of the dangling census**: the true
in-window orphaned set is **~23 commits, not 6** — §B above is the authoritative list. Cross-verification
did its job: it caught a truncation gap that a single pass missed. **Action item unchanged in kind,
broadened in scope:** before any `git gc`, additively tag the B.1 orphaned commits (`git tag
salvage/<name> <sha>`) so the codeowner can triage them deliberately. Read-only discipline maintained
throughout both passes.
