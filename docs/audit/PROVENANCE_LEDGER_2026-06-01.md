# Provenance Ledger — Loose-Artifact Preservation (luthiers-toolbox)

**Created:** 2026-06-01
**Scope:** Conservative, ADDITIVE preservation of loose artifacts around the governance-sprint
anchor (`464920f1`, 2026-05-28). Pre-sprint window **[2026-05-14 → 2026-05-28]**.
**Discipline:** additive only — `git tag` / `git branch` (from stashes, no pop) / read-only
inspection. No commit (except this ledger), no stash pop/drop, no branch -D, no gc/prune/reset/rebase.
**This file is untracked by design** (scratch; must not ride a feature PR). Delete once the
codeowner has sorted the salvage set.
**Disposition policy:** every row is **KEEP — undecided**. Nothing is recommended for discard,
even apparently-landed items; those are flagged "LANDED?, review later" but the handle stays.

> **Greppable set:** `git tag -l 'salvage/*'` · `git branch --list 'salvage/*'`.
> Remote: pushed to `origin` (one exception — see §0 stash8).

---

## 0. What this pass created + state

| | Count | Notes |
|---|---|---|
| Tags created this pass | **23** | orphaned in-window real commits |
| Branches created this pass | **8** | in-window stashes with real work (additive `git branch <name> stash@{N}` — stashes NOT dropped) |
| Pre-existing salvage tags (prior session) | 2 | `salvage/topology-1790f6bb`, `salvage/aperture-c817e9cb` — overlap stash@{3}/@{7} W-commits |
| External salvage tags (added concurrently, NOT by this pass) | 2 | `salvage/cam-intent-8G-vcarve`, `salvage/cam-intent-8H-profile` — **not on origin**; left as-is (not mine to push) |
| Stashes | **13, all intact** | none popped/dropped |
| Working tree | clean | only untracked audit docs |

**Push status:** 25 tags + 7 branches on `origin`. **`salvage/other-stash8-ingest-audit-binaries`
did NOT push** — silent failure; the stash carries `~14MB` binary blobs **and `.claude/settings*`
(possible secrets)**. Per discipline I stopped rather than force it. **Codeowner decision (§5-D1):**
review for secrets, then push or keep local-only. Local handle + stash are intact, so nothing is lost.

**Excluded from tagging (per agreed scope — listed, not silently dropped):**
- *This-session merged-then-pruned* danglers (landed on `main` under squash SHAs): `13b11020`→PR#80,
  `511c1222`→PR#81, `61feb1f7`→PR#82, `a10d5455`→PR#85, `7ceeadcc` (old toolpath tip). Durable on `main`; no handle needed.
- *Out-of-window, no clear pre-sprint signal:* stash@{10} (04-25 sprint-3b), stash@{11} (04-14 rollback),
  stash@{12} (03-16 photo-vectorizer) — **stash-durable already**, not branched. Plus orphaned commits
  `94f80142` (05-04, experimental-module classification) and `763907d8` (05-11, CAM-6H capability registry)
  — **FRAGILE orphaned real commits just outside the window; NOT tagged per scope.** See §5-D2.
- *Stash plumbing:* index/untracked parent commits are covered by branching the stash W-commit; not separately tagged.

---

## 1. Reachability inventory (Phase 1)

| Class | Count | Meaning |
|---|---|---|
| ON-BRANCH | (all merged PRs) | already safe on `main` / feature branches |
| STASH-REACHABLE | 13 stashes | in `refs/stash` (entry @{0} via ref; @{1+} via reflog — appear "dangling" under `--no-reflogs`) |
| TRULY-ORPHANED | 23 tagged + 2 deferred (§5-D2) | fsck-only dangling real commits; gc-reapable until tagged |
| **Total dangling commits** | **42** | = stash W-commits (13) + orphaned real (23) + this-session merged debris (5) + out-of-window orphaned (1: `8fa1244c` counted in 23) — see §0 exclusions |

---

## 2. Provenance ledger — TAGS (orphaned in-window real commits)

| handle (tag) | sha | date | sprint line | what it was for (from diff+msg) | landed | disp. |
|---|---|---|---|---|---|---|
| salvage/govinv-43b07017-doc-inventory | 43b07017 | 05-20 | governance-inventory | **159 files / +53690** — bulk governance/architecture document inventory dump | PARTIAL? (`governance_inventory.md` on main) | KEEP |
| salvage/govinv-d1677e98-unified-gate-blocking | d1677e98 | 05-20 | governance-inventory | flip `governance_unified.yml` gate to **blocking mode** (1 file) | UNVERIFIED | KEEP |
| salvage/govinv-c35c4ff9-inventory-determinism | c35c4ff9 | 05-20 | governance-inventory | regenerate `governance_inventory.json/.md` deterministically via `build_governance_inventory.py` | PARTIAL? | KEEP |
| salvage/govinv-ac9f70ee-ontology-output | ac9f70ee | 05-20 | governance-inventory | normalize ontology script output (`audit_authority_chains`, `detect_semantic_drift`, `list_semantic_owners`) | UNVERIFIED | KEEP |
| salvage/govinv-cb9bcde6-c0c1-constitutional | cb9bcde6 | 05-18 | governance-inventory | **+1962** — add C0/C1 constitutional foundation baseline (dropped stash on wood-shrinkage branch) | UNVERIFIED | KEEP |
| salvage/govinv-f89e77a1-guard-status-phase2b | f89e77a1 | 05-21 | governance-inventory / DXF | guard_status Phase 2B — DXF save lifecycle guard + export-lifecycle-classification-matrix + validator | UNVERIFIED | KEEP |
| salvage/govinv-45a472a6-guard-status-phase2b-dup | 45a472a6 | 05-21 | governance-inventory / DXF | **identical diff to f89e77a1** (amend/dup pair) | UNVERIFIED | KEEP |
| salvage/mrp5x-dde5480b-regression-guard | dde5480b | 05-23 | MRP-5X | `test_runtime_capability_regression_guard.py` (MRP-5X regression guard) | UNVERIFIED | KEEP |
| salvage/mrp5x-124ad198-capability-guard | 124ad198 | 05-23 | MRP-5X | MRP-5X capability guard test + aperture/acoustics/experimentalDrift bits | UNVERIFIED | KEEP |
| salvage/mrp5x-01f01368-rb2b-guard-rollout | 01f01368 | 05-21 | MRP-5X (label) / **acoustics (content)** | **label-vs-content mismatch:** branch=runtime-boundary-2b, diff=`ExperimentalDriftTimelinePanel.vue`+`experimentalDrift.ts/test` (acoustics drift UI, +533) | UNVERIFIED | KEEP |
| salvage/vectorizer-dcabee7c-tier-a-relocation | dcabee7c | 05-20 | vectorizer (**CROSS-REPO**) | Tier-A relocation docs (`MANIFEST_INDEX`, `VECTORIZER_CANONICAL_PATHS`) for modules moved to vectorizer-sandbox | UNVERIFIED | KEEP |
| salvage/vectorizer-efb60349-semantic-artifact-quality | efb60349 | 05-21 | vectorizer / research | **+742** — research docs: CONTOUR_OWNERSHIP / MORPHOLOGY_CONTINUITY / PRIMITIVE_SURVIVABILITY semantic-quality layer | UNVERIFIED | KEEP |
| salvage/confenv-4a20b1a2-mrp6d-integration-audit | 4a20b1a2 | 05-25 | confidence-envelope | MRP-6D runtime capability integration audit + `DEV_ORDER_NAMESPACE_SUMMARY` + convergence report (+655) | UNVERIFIED | KEEP |
| salvage/dxfibg-577bd114-3a-before-do75 | 577bd114 | 05-25 | DXF-IBG | pre-DO75 WIP — MULTI_REPO_GOVERNANCE_CONVERGENCE + CROSS_REPO_AUTHORITY_CROSSWALK + aperture (+1146) | UNVERIFIED | KEEP |
| salvage/cired-aab69089-015a-masksum-superseded | aab69089 | 05-28 | CI-RED | text-masking `mask.sum` `_NoValueType` fix (015-A) — **SUPERSEDED** by landed `95c33846` (numpy-isolation cause-fix) | LANDED (as different fix) | KEEP |
| salvage/cired-3f5cb833-jumbo-ci-preflight | 3f5cb833 | 05-27 | CI-RED | CBSP21 `patch_input.json` + `api_verify.yml` + `SG_SPEC_TOKEN.md` (CI-RED-001 preflight WIP) | LANDED? (CI-RED-001 closed) | KEEP |
| salvage/cired-6e485c05-jumbo-dim-consistency | 6e485c05 | 05-27 | CI-RED (label) / **IBG (content)** | **label-vs-content mismatch:** branch=ci-red-001, diff=`body-outline-editor.html`+`body_contour_solver.py`+`instrument_body_generator.py` (IBG body solver, +153) | UNVERIFIED | KEEP |
| salvage/other-4310d56a-wood-shrinkage-wip | 4310d56a | 05-14 | other (wood-data) | dropped stash on wood-shrinkage branch but diff = governance arch docs (APERTURE, CAM_GOVERNED_EXPORT, AUTHORITY_HIERARCHY, +491) — **intent unclear** | UNVERIFIED | KEEP |
| salvage/other-8fa1244c-cam-safety-decorators | 8fa1244c | 05-20 | other (cam-refactor label) | WIP labeled cam-complexity-reduction but diff = APERTURE status + acoustics `index.ts` + `ApertureWorkspace.vue` | UNVERIFIED | KEEP |
| salvage/other-d682a13b-tech-debt-audit | d682a13b | 05-20 | other | **identical diff to 8fa1244c** — same WIP stashed from `main` context (dup) | UNVERIFIED | KEEP |
| salvage/other-71cee0a1-fret-completion-verify | 71cee0a1 | 05-27 | other (FRET) | `FRET_A_COMPLETION_VERIFICATION_2026-05-04.md` (+471) | LANDED? (FRET-A marked complete) | KEEP |
| salvage/other-f8928299-acoustic-jumbo-audit-sources | f8928299 | 05-27 | other (acoustic-jumbo) | **binary-only, 0/0 text** — two `vcarve_inlay.dxf` no-ops; effectively scratch | UNVERIFIED (likely empty) | KEEP |
| salvage/unassignable-564b4559-orphan-merge | 564b4559 | 05-27 | UNASSIGNABLE | orphaned merge of `main` carrying CI-RED files (patch_input/api_verify/SG_SPEC_TOKEN, +320) — merge, not unique authored work | UNVERIFIED | KEEP |

---

## 3. Provenance ledger — BRANCHES (in-window stashes, real work)

| handle (branch) | stash | date | sprint line | what it was for (from --stat) | landed | disp. |
|---|---|---|---|---|---|---|
| salvage/govinv-stash6-inventory-tooling | @{6} | 05-20 | governance-inventory | `governance_inventory.json` **+1662** + `build_governance_inventory.py` + tests + `cam_manifest.py` | PARTIAL? (inventory on main) | KEEP |
| salvage/govinv-stash5-mrp5m-admission | @{5} | 05-20 | governance-inventory | `MRP_5M_RUNTIME_ADMISSION_CONTROL.md` **+403** + `check_all_ci.json` | UNVERIFIED | KEEP |
| salvage/govinv-stash7-exec-alignment | @{7} | 05-20 | governance-inventory | SPRINTS +79 + MORPHOLOGY_FAILURE_TAXONOMY + acoustics (also pre-tagged `salvage/aperture-c817e9cb`) | UNVERIFIED | KEEP |
| salvage/govinv-stash4-acoustics-index | @{4} | 05-20 | governance-inventory | acoustics `index.ts` (+11) — minor | UNVERIFIED | KEEP |
| salvage/dxfibg-stash1-camassist-convergence | @{1} | 05-25 | DXF-IBG (parked) | **external-repo import:** `docs/audit-sources/CAM-Assist-Blueprint/` (README +536, CLAUDE.md, taxonomy) + convergence report | UNVERIFIED | KEEP |
| salvage/confenv-stash2-devorder-namespace | @{2} | 05-25 | confidence-envelope | `DEV_ORDER_NAMESPACE_SUMMARY_2026-05-25.md` (+77) | UNVERIFIED | KEEP |
| salvage/vectorizer-stash3-wave1c-semantic | @{3} | 05-21 | vectorizer / research | SPRINTS +180, `RUNTIME_BOUNDARY_INVENTORY` +338, acoustics (also pre-tagged `salvage/topology-1790f6bb`) | UNVERIFIED | KEEP |
| salvage/other-stash8-ingest-audit-binaries | @{8} | 05-14 | other (ingest-audit) | **`.claude/settings*` + ~14MB binary images** (Benedetto jpgs, ChatGPT pngs) — mostly scratch; may bury real ingest-audit code | UNVERIFIED | KEEP (**not on origin — §5-D1**) |

---

## 4. Sprint-shaped summary (the insight layer)

| Sprint line | Loose artifacts preserved | Reachability | Provenance gap |
|---|---|---|---|
| **governance-inventory** | **11** (7 tags + 4 branches) | mostly TRULY-ORPHANED + STASH | **CAN explain partially** — work is self-describing (inventory tooling, unified gate, guard_status) but had **no durable `DO_NN` dev-order doc**; intent reconstructable from diffs, not from a written order. Largest stranded footprint. |
| **MRP-5X / runtime-boundary** | 3 tags | TRULY-ORPHANED | Partly explainable (regression/capability guard) but one (`01f01368`) is mislabeled acoustics-drift work — intent ambiguous. |
| **vectorizer (CROSS-REPO)** | 3 (2 tags + 1 branch) | ORPHANED + STASH | Explainable as the *removal* side of the Tier-A → vectorizer-sandbox migration; **full intent lives in the sibling repo** (run this prompt there). |
| **DXF-IBG** | 2 (1 tag + 1 branch) | ORPHANED + STASH | Best-documented sprint (formal `DO_75–DO_80`), yet its strays are "unrelated-wip" parked mid-phase — scope leak, not lost intent. |
| **CI-RED** | 3 tags | ORPHANED | Fully explainable (highest dev-order discipline); strays are superseded/duplicate attempts. |
| **confidence-envelope** | 2 (1 tag + 1 branch) | ORPHANED + STASH | Explainable (MRP-6D audit + dev-order-namespace summary). |
| **other / UNASSIGNABLE** | 6 + 1 | ORPHANED + STASH | **CANNOT cleanly explain** several — `4310d56a` (gov docs on a wood branch), `8fa1244c`/`d682a13b` dup WIP, `564b4559` bare merge, `f8928299` empty. Intent died with the session. |

**Provenance gap verdict.** Sprints with durable dev-order docs (**CI-RED**, **DXF-IBG**) left strays
whose intent is still legible — they're scope-leak or superseded attempts, low-mystery. The
**governance-inventory** line left the *most* stranded work with the *least* written order: substantial,
self-describing tooling that never reached a PR and had no `DO_NN`. The **other/UNASSIGNABLE** bucket is
where intent genuinely died with the session.

**First reconstruction target: `governance-inventory`.** Highest stranded-wanted-to-clear-intent ratio —
~11 artifacts, self-describing content (inventory tooling + unified gate + guard_status), and it's the
very line the anchor (`464920f1` GOV-CONVERGE) re-booted, so reconstructing it directly serves the live
sprint. Second: `vectorizer` (but needs the cross-repo sweep first).

---

## 5. Codeowner decisions (recorded, NOT executed)

- **D1 — `salvage/other-stash8-ingest-audit-binaries` remote push.** Failed silently; stash holds
  `.claude/settings*` (possible secrets) + ~14MB binaries. **Decide:** scrub/confirm no secrets → push,
  or keep local-only. Local handle + intact stash mean no loss either way. (A secret-scanning rejection
  here would be *correct* — do not force.)
- **D2 — two FRAGILE out-of-window orphaned commits NOT tagged** (per agreed scope): `94f80142` (05-04,
  "experimental modules detached") and `763907d8` (05-11, "CAM operation capability registry 6H"). They
  are gc-reapable real commits just before the window. **Decide:** tag them too (one command each:
  `git tag salvage/other-94f80142-exp-modules 94f80142` / `git tag salvage/other-763907d8-cam-6h 763907d8`)
  or accept the risk. Recommendation leans tag (cheap, additive, prevents loss).
- **D3 — two external `salvage/cam-intent-8G/8H` tags** observed in the set, not on origin, not created by
  this pass. **Decide:** push them with the rest, or leave.
- **D4 — duplicates** (`8fa1244c`≡`d682a13b`, `f89e77a1`≡`45a472a6`) and the **empty** `f8928299`
  (binary no-op) are kept per the no-discard policy; flag for cleanup once sprints are reconstructed.

---

## 6. Cross-repo note

This pass covered **luthiers-toolbox only**. The same prompt must be run against **`vectorizer-sandbox`**
(the Tier-A migration / three-loop landing side — `dcabee7c`/`efb60349` are only the *removal* side here)
and **`tap_tone_pi`**. Those repos' loose artifacts are out of scope for this ledger.

---

## 7. Discipline statement

Additive only. 23 tags + 8 branches created; 13 stashes intact; no pop/drop/gc/prune/reset/rebase/-D.
Working tree clean apart from untracked audit docs. Current branch at run time:
`fix/ci-red-002-legacy-usage-gate-scope`. Nothing discarded; nothing decided; everything preserved and
explained — the codeowner sorts later.
