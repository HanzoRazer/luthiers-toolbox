# Triage Inventory — Uncommitted Backlog & SPRINTS.md Parking Lot

**Date:** 2026-06-02
**Author:** Claude (read-only triage; no repo modifications)
**Scope agreed with codeowner (Ross):**
- Stashes: stat-level on all 13; full `-p` deep-diff only where files touch a kernel.
- Unidentified pile: repo-root loose files + untracked/modified-in-~30-days.
- Collisions: re-verify the existing `audit_duplicate_pairs.txt` against live repo + hot zones (do not regenerate).
- Existing audits: cross-reference for leads, **re-verify for truth** — inherit nothing.

> **Stance.** The Sprint-3 audit (2026-04-26) found 10/12 DXF migration claims false; `audit_deletion_candidates_v3.txt` carries a `_v3` because the list has been wrong twice. These prior audits are a **map of where bodies might be buried**, not a checklist of confirmed graves. Every claim below was re-dug against `git`/grep with the command cited. Where I could not confirm, the item is **UNRESOLVED**, never asserted.

---

## Baseline

| Fact | Value | Source |
|------|-------|--------|
| `SPRINTS.md` **Last updated** | **2026-05-28** (maintained by Ross Echols) | `head -2 SPRINTS.md` |
| Current branch | `feat/cam-intent-8g-vcarve` | git status |
| Working tree | **3 untracked files, 0 modified, 0 staged** | `git status --porcelain` |
| Stashes | **13** (`stash@{0}`–`stash@{12}`) | `git stash list` |

**The "uncommitted backlog" is almost entirely in stashes and in tracked-but-orphaned root files — not in the working tree.** The 3 untracked files are the prior forensic audits this triage was told to find (`docs/audit/*_2026-06-01.md`).

### Counts

| Bucket | GREEN | RED | UNRESOLVED |
|--------|------:|----:|-----------:|
| Stashes (13) | 6 | 7 | 0 |
| Untracked files (3) | 3 | 0 | 0 |
| Root unidentified pile | 3 groups | 4 (2 kernels + 2 kernel-tests) | 2 |
| Namespace collisions (4 sets) | 1 | 3 | 0 |
| Parking lot — OPEN (13) | 7 | 6 | 0 |
| Parking lot — CLOSED (re-verify) | 14 (status-reconcile) | 0 | 1 (spot-check) |

---

## Table 1 — Uncommitted / Untracked / Orphaned files

### 1A. Stashes (stat-level on all 13; deep-diff on kernel-touching)

| Stash | Subject / branch | What it is (file evidence, not subject) | Class | Evidence |
|-------|------------------|------------------------------------------|-------|----------|
| `{0}` | `wip-acoustic-jumbo` | **2 binary DXF example fixtures** (`vcarve_inlay.dxf`, 64→78 B). Subject says "acoustic" but files are DXF examples — no kernel touched. | **GREEN** | `git stash show --stat`. ⚠️ binary-opaque (won't show in a text diff) + subject/file mismatch → see UNRESOLVED Q5. |
| `{1}` | `wip-unrelated-3a3` | acoustics barrel + drift tests, drilling routers, **IBG `body_evidence_candidate.py`**, `layered_dxf_writer.py`. acoustics here = data-mgmt UI utils, **not** Helmholtz physics. | **RED** | Touches IBG provenance (`BLOCKED_PROVENANCE` is intentional) + entangled across 19 files; what-to-keep is a judgment. |
| `{2}` | `wip-before-dxf-3a` | 1 doc (`DEV_ORDER_NAMESPACE_SUMMARY`). | **GREEN** | stat: 1 file, doc-only. |
| `{3}` | `wave-1c-semantic-artifact-quality` | **Big (1585+):** `SPRINTS.md` (180 lines), acoustics `topologyVariant.ts` (QA hardening — type guards/normalization, **no math/numbers**), `cam_manifest.py`, `runtime_provenance/`, `research_index.json` (+555). | **RED** | Deep-diff: acoustics part is non-kernel data utils, **but** bundles SPRINTS.md edits + CAM manifest registration + research index — un-splitting is a merge judgment. |
| `{4}` | `Modified acoustics file` | acoustics `index.ts` barrel **re-export +11** (experimentNote/evidenceReview). | **GREEN** | Deep-diff: pure `export * from …`; diff-visible, no kernel. |
| `{5}` | `Untracked files before rebase` | 1 doc (`APERTURE_WORKSPACE_REFACTOR_STATUS`, +4). | **GREEN** | stat: doc-only. |
| `{6}` | `Linter changes to inventory files` | **Regenerated `governance_inventory.json`/`.md`** (1662/618 lines) + `build_governance_inventory.py` + its test + cam_manifest. | **RED** | The inventory is a **computed artifact** — a wrong regen hides in counts; bundled with a script change. Judgment whether the regen is correct. |
| `{7}` | `WIP: unrelated changes before PR4 branch` | **Huge (32 files):** **new `advanced_offset.py` shapely geometry engine (+283)**; `fret_math.py` + `nut_compensation_calc.py` (**type-hint-only**: `float`→`Optional[float]`, added `Dict` import); `vectorizer_phase3.py`; `morphology_harvest/adapters.py` (+436); `tool_db.py`; CAM routers. | **RED** | Deep-diff: fret/nut touches are cosmetic (verified), **but** a new geometry-offset kernel + vectorizer + morphology adapters in one entangled WIP. Wrong merge hides in geometry. |
| `{8}` | `All local changes before rebase` | `.claude/settings.local.json` (−20). | **GREEN** | stat: local editor config only. |
| `{9}` | `WIP: ingest-audit-log local changes` | `.claude/settings.local.json` (+2/−1). | **GREEN** | stat: local config. |
| `{10}` | `sprint-3b-uncommitted-pre-reconciliation` | `SPRINTS.md`; **dual `body-outline-editor.html`** (deletes `tools/` 4247 lines, edits `hostinger/`); **archtop bridge/saddle/contour DXF-writer migration** (geometry points unchanged, ezdxf→`DxfWriter`); `smart_guitar_dxf.py`; **neck export files** (collision Group 2); `blueprint_cam/`. | **RED** | Deep-diff: this **is** uncommitted Sprint-3 DXF-migration work — the exact zone of the 10 false-completion claims. Also contains the body-outline-editor.html canonical decision (Collision #3) and neck-export work (Collision #2). |
| `{11}` | `Sprint changes - before rollback to 01:25 state` | `edge_to_dxf.py`, `photo_vectorizer_v2.py` (`get_ai_spec` refactor), `layer_builder.py`, `blueprint_orchestrator.py`. | **RED** | Vectorizer pipeline = evidence-integrity (task rule), not cleanup. |
| `{12}` | `photo-vectorizer WIP` (`import-post-proc-7f310`) | `geometry_coach_v2.py` (+14) + 2 vectorizer test files. | **RED** | Vectorizer (task rule). ⚠️ Deep-diff shows a **duplicated retry-history block** (same 5 lines twice) — possible bug; do not apply blind. |

**Stash summary:** GREEN `{0,2,4,5,8,9}` (binary fixtures, doc-only, barrel re-exports, local config). RED `{1,3,6,7,10,11,12}` (IBG provenance, geometry kernel, vectorizer, regenerated computed inventory, Sprint-3 migration zone, entangled multi-stream WIP).

### 1B. Untracked files (working tree)

| Path | What it is | Class | Evidence |
|------|-----------|-------|----------|
| `docs/audit/PRE_GOVERNANCE_FORENSIC_2026-06-01.md` | Prior forensic audit (the "recent audits of orphaned material" Ross flagged). | **GREEN** | `git status --porcelain`; not gitignored (`git check-ignore` → not ignored). Doc-only. |
| `docs/audit/PROVENANCE_LEDGER_2026-06-01.md` | Provenance ledger doc. | **GREEN** | same. |
| `docs/audit/SANDBOX_DRIFT_RECONCILIATION_2026-06-01.md` | Sandbox-drift reconciliation doc. | **GREEN** | same. |

### 1C. Root "unidentified pile" (tracked unless noted)

| Path(s) | What it is | Class | Evidence |
|---------|-----------|-------|----------|
| `spiral_acoustic_model.py`, `spiral_q_fh_solver.py` | **Acoustic-kernel `.py` at repo root.** Tracked. **Zero importers** in `services/`+`packages/`; **no collision** in `services/`. | **RED + UNRESOLVED** | `git ls-files` (tracked); `grep -rln spiral_acoustic_model\|spiral_q_fh_solver services packages` → empty; `find services -name …` → empty. Orphaned-or-standalone acoustic kernel → Q1. |
| `test_spiral_acoustic_model.py`, `test_spiral_q_fh_solver.py` | Root tests pinning the above kernels' numbers. Tracked. | **RED** | Tied to acoustic kernels; a wrong move/skip hides in acoustic numbers. Classify with their kernels. |
| `test_spiral_q_fh_solver.py` (+ `spiral_q_fh_solver.py`) note: also `test_spiral_acoustic_model.py` references model | (same set as above) | — | — |
| `test_gap_close_fix.py` | Stray root pytest file. Tracked. | **GREEN** | `git ls-files` confirms tracked. Mechanical relocate to `tests/` (proposes, diff-visible). |
| **54 root `*.txt` session dumps** (e.g. `Bridge Compenstation Calculator.txt`, `Animate Toolpath Visualizer Code.txt`, `INLAY_PATTERN_GENERATORS.txt`, `MD_INVENTORY.txt`, `Comprehensive_Migration_Plan*.txt`) | Chat/session content dumps, not live code. | **GREEN** (inventory/extract) | `find . -maxdepth 1 -name "*.txt" \| wc -l` = **54** (memory noted "52"; +2 drift). Extraction was scheduled end-of-May 2026 → **now overdue**. Categorization proposes-not-decides. |
| Gitignored artifacts: `test_*_REFINED.dxf` (**GB-scale**), `test_*.dxf`, `pytest_failures.txt`, `vulture*-report.txt`, `radon_complexity_report.txt`, `bandit_report.txt`, `*.png`/`*.jpg`, `useSavedViews_v2_full_features.ts.bak`, `.coverage`, `coverage.json` | Build/scan artifacts + a `.bak`. Not in git. | **GREEN** (janitorial cleanup) | `git check-ignore` confirms `*.dxf`/reports ignored. Note ~2.1 GB of REFINED DXFs on disk. Grep-gate before deleting `.bak`/`.ts`. |

> The legitimate root files (`README.md`, `Makefile`, `docker-compose*.yml`, `CLAUDE.md`, `SPRINTS.md`, `FENCE_REGISTRY.json`, `boundary_spec.json`, `pnpm-workspace.yaml`, etc.) are **identified, in-use, not part of the backlog** — excluded from triage.

---

## Table 2 — Namespace collisions (re-verified vs `audit_duplicate_pairs.txt`, 2026-04-21)

> Diffing the old list against live is the point: a pair since-resolved is a GREEN reconcile; a pair the old list got wrong is a RED finding. **Both old groups proved stale.**

| Collision set | Live state (which is wired) | Class | Evidence for the human decision |
|---------------|----------------------------|-------|---------------------------------|
| **`validate_scale_before_export`** (audit Group 1) | Audit's "canonical" `services/api/app/services/scale_validation.py:79` has **ZERO importers** repo-wide. The live, actually-called impl is the audit's "duplicate" `services/blueprint-import/vectorizer_phase3.py:2336` (called at `:3570`). | **RED** | `grep -rln scale_validation services --include=*.py` → **empty** (nobody imports it); `scale_validation.py` defs at `:45,79,144,190` exist but unused. The audit's premise ("canonical, used by API, vectorizer should import it") is **false today** — the canonical is the orphan. Decision: make vectorizer import `scale_validation.py`, **or** delete `scale_validation.py` as the dead twin. Also vectorizer-remediation-adjacent. |
| **Neck export files** (audit Group 2) | `routers/neck/` now holds `headstock_transition_export.py`, `neck_profile_export.py`, **new `export.py`**; audit's `neck/dxf_export.py` is **gone** — `dxf_export` now at `routers/headstock/dxf_export.py`. | **RED** | `ls routers/neck/`; `business_manifest.py:51` registers `headstock_transition_export`, `:21` `legacy_dxf_exports_router`; `cam_manifest.py:330` registers `headstock.dxf_export`; **`neck_profile_export` registered in NO manifest** (`grep neck_profile_export router_registry` → empty) — audit's "Registered in business_manifest.py" is **false**. Set has shifted + a new `export.py` appeared. Uncommitted work on these sits in **stash `{10}`**. |
| **`body-outline-editor.html`** (new finding, not in audit) | **Both** `hostinger/body-outline-editor.html` and `tools/body-outline-editor.html` are live and tracked. Stash `{10}` would delete the `tools/` copy (4247 lines) and edit `hostinger/`. | **RED** | `find -name body-outline-editor.html` → 2 copies; `git ls-files` → both tracked. Which is canonical (deployment `hostinger/` vs dev `tools/`) is undecided and partly encoded in an unapplied stash → Q3. |
| **Archtop CAM** (audit Group 3) | `archtop/archtop_contour_generator.py`, `cam/archtop_bridge_generator.py`, `cam/archtop_saddle_generator.py` all exist. Audit said "NOT duplicates — complementary." | **GREEN** (reconcile) | All three exist (file test). Audit Group 3 confirmed accurate → mark "no collision, no action." (Note: in active flux — stash `{10}` migrates all three to `DxfWriter`.) |

---

## Table 3 — SPRINTS.md parking lot

### OPEN entries

| Entry | What it is | Class | One-line why |
|-------|-----------|-------|--------------|
| GOV-CONVERGE-001 | Governance tail umbrella tracker | **GREEN** | Pure status tracker; closes when 002–006 do. No decision/number. |
| GOV-CONVERGE-002 | IBG provenance chain R1→R2→CAM (BLOCKED) | **RED** | Provenance ratification + export wrapper unblocking 5 `BLOCKED_PROVENANCE` paths; intentional block, judgment-heavy. Not MVP-gating. |
| GOV-CONVERGE-003 | Codeowner decisions D1/D2/D4 (BLOCKED) | **RED** | "Not engineering work — Ross answers." Pure judgment calls → also UNRESOLVED Q2. |
| GOV-CONVERGE-004 | Art Studio design-first restore (QUEUED) | **GREEN** | Re-mount router; gated by "promotion intent test 8/8 green." Mechanical + test-verified. (Export *semantics* live in ART-STUDIO-DEFER-001 → RED.) |
| GOV-CONVERGE-005 | tap_tone_pi push (27 commits) (QUEUED) | **RED** | Outward-facing cross-repo publish requiring manual source verification; not a diffable in-repo change. |
| GOV-CONVERGE-006 | Package normalization → `contracts/` (QUEUED) | **GREEN** | Mechanical move + import rewrite, gated by governance tests; breakage shows in tests. Verify import graph. |
| ART-STUDIO-DEFER-001 | Design-first-workflow + **promotion intent export** | **RED** | Governed CAM export surface + parity policy; held out of PR #46. (Re-including `test_promotion_intent_export_endpoint.py` alone is GREEN reconcile.) |
| MAINT-DEFER-001 | SPRINTS.md CI enforcement (DEFERRED) | **GREEN** | Stable solo-dev deferral; reconcile = keep deferred, no action. |
| MAINT-DEFER-003 | Load-bearing `DO NOT REMOVE` comments (QUEUED) | **GREEN** | Comment additions; fully diff-visible. |
| CI-RED-003 | debt-gates complexity ratchet (113 violations) | **RED** | Complexity-reduction refactors can silently alter kernel behavior; **not** MVP-gating but not safely delegatable wholesale. |
| CI-RED-004 | Fence Checks frontend boundary (legacy `/api/rmos/runs` refs) | **GREEN** | Mechanical reference cleanup in client SDK/tests; fence test gates it. Not on the design→g-code→cut path. |
| CI-RED-015 | api-verify test reconciliation (72 fails) | **RED** | Buckets A/B/C/D closed; **remaining 015-E = `board_feet` + `fretboard` drift** = calculation kernels; drift fixes hide in numbers. |
| CI-RED-016 | Endpoint consolidation (1181 routes) | **GREEN** | Explicitly "documentation only until post-MVP cut"; parked, no decision now. (Eventual consolidation = RED later.) |

### CLOSED entries (status-reconcile — GREEN, spot-check recommended)

CI-RED-001, 002, 005, 006, 007, 008, 009, 010, 011, 012, 013, 014; sub-buckets 015-A/B/C/D; MAINT-DEFER-002; CAM-TPA-001 — all carry PR + verification per Rule 5 (commit hash + paths + method). **GREEN to leave closed**, but per the false-completion history these were **not independently re-verified in this pass** → UNRESOLVED Q6 names which to spot-check first.

---

## Safe to delegate first (GREEN, in dependency order)

1. **Untracked docs (1B)** — commit `docs/audit/*_2026-06-01.md` (+ this file). Zero risk, doc-only.
2. **Doc-only vectorizer-debt patches** — stale sections in `VECTORIZER_TECHNICAL_DEBT_INVENTORY.md` (lines ~107/116/167/182) and `VECTORIZER_DUPLICATION_MATRIX.md` (~102) per "Safe Remediation Lane.md" §housekeeping. Diff-visible, no code. *(Must land **after** vectorizer PR-1; the doc describes the corrected state.)*
3. **MAINT-DEFER-003** — add load-bearing `DO NOT REMOVE` comments. Comment-only.
4. **GREEN stashes** — triage/apply `{2},{4},{5},{8},{9}` (docs, acoustics barrel re-export, local config). `{0}` only after Q5 (binary fixtures).
5. **Root `.txt` extraction/categorization (54 files)** — the overdue session-dump sweep; propose archive locations, don't decide deletions.
6. **Gitignored-artifact janitorial** — grep-gated cleanup of `.bak`, scan reports, GB-scale `*_REFINED.dxf`. **Sequence after the vectorizer RED stashes/PRs** so nothing in flight depends on them.
7. **CI-RED-004** — mechanical legacy `/api/rmos/runs` reference cleanup (fence-test gated).
8. **GOV-CONVERGE-006** — package move to `contracts/` (governance-test gated).
9. **Status reconciles** — confirm CLOSED CI-RED entries; confirm archtop Group 3 = no-collision; relocate `test_gap_close_fix.py`.

---

## UNRESOLVED — needs your input

1. **Root acoustic kernels `spiral_acoustic_model.py` / `spiral_q_fh_solver.py`** — tracked, zero importers, no `services/` twin. Are these standalone analysis scripts you run by hand, or superseded by `app/calculators/soundhole_facade.py` (`SpiralParams`)? Their relationship to the canonical soundhole system determines keep-at-root vs relocate vs retire. (Acoustic-kernel → I will not move/delete without your call.)
2. **GOV-CONVERGE-003 D1/D2/D4** — (D1) branch strategy for post-governance implementation commits; (D2) persist `docs/audit-sources/` as repo / gitignore / submodule; (D4) PR grouping (per-domain vs umbrella). Pure codeowner decisions.
3. **`body-outline-editor.html` canonical** — `hostinger/` (deployment) or `tools/` (dev) the source of truth? Stash `{10}` proposes deleting the `tools/` copy — apply that intent, or keep both deliberately?
4. **`validate_scale_before_export` canonical** — the audit's "canonical" `scale_validation.py` is orphaned (0 importers); the live impl is in `vectorizer_phase3.py`. Refactor the vectorizer to import `scale_validation.py`, or delete `scale_validation.py` as dead? (Vectorizer-remediation-adjacent — sequence with the Safe Remediation Lane PRs.)
5. **Stash `{0}` subject/file mismatch** — labelled `wip-acoustic-jumbo` but contains only binary `vcarve_inlay.dxf` example fixtures (binary-opaque, won't show in a text diff). Intended example regen, or mislabeled/stale?
6. **CLOSED CI-RED spot-check** — given Sprint-3's 10 false-completion claims, which CLOSED entries do you want independently re-verified before trusting? Highest-leverage candidates: **015-D** (closure "pending one live `app.routes` dump" — never executed; api-verify auth was the blocker) and **CI-RED-002** (legacy-usage gate 131→budget).

---

*STOP — read-only triage complete. No files modified, staged, cherry-picked, merged, or deleted. No git write operations performed. This report (`docs/audit/TRIAGE_INVENTORY_2026-06-02.md`) is the only file created.*
