# Session handoff — 2026-06-21 — CI-RED multi-thread (body-solver, CAM replay recovery, saw-batch complexity)

**main HEAD at handoff:** `6e934218` (#143). **Open PRs:** **#144**, **#145** (both this session's work).
**Re-entry rule:** the board moves — re-verify `main` HEAD + open PRs + merge states before acting.
Quick re-verify: `git fetch && git log origin/main --oneline -6 && gh pr list --state open`.

---

## TL;DR — what to do next

**Merge #144 then #145, in that order**, then watch **debt-gates go fully green on CI** (both sub-gates).
- #144 (CI-RED-003) merges on its own merits.
- #145 depends on #144 for debt-gates to go *fully* green (see below).
- Do NOT witness debt-gates green locally — **local file-size gate lies in this checkout** (see Environment). CI is the only authoritative surface.

---

## Threads & state

### CLOSED / merged this session
- **CI-RED-015 body-solver cluster (11 failures) — CLOSED.** Mixed cluster, dug the quiet one first.
  - **#137** (`af25977a`) — sub-cause **B, real latent defect**: `ConstraintExtractor` tagged DXF landmarks `source='dxf'`, off-contract in both the `LandmarkPoint.source` vocab AND `_compute_confidence` weights → every DXF solve under-reported confidence (~0.455 vs ~0.91) since 2026-04-17. Fix = retag to canonical `vectorizer_extracted`. Witnessed Core CI **43→42**.
  - **#138** (`4c4e208d`) — sub-cause **A, stale-test** (10): paid-tier endpoints gained auth in IBG-2B; tests predated it → 401. Fix = tests *authenticate* via `x-user-role`/`x-user-id` headers (not bypass). Witnessed Core CI **43→33**. Combined expected 43→32.
- **CI-RED-023 manufacturing replay recovery — merged.**
  - **#142** (`63791b3c`) — restored the replay bundle (router+registry+observation+timeline+tests+handoff) and retired the dangling `lifecycle_promotion_router` manifest entry. Both were dangling manifest entries (files absent). Witnessed: API Wiring Gate green; bundle tests **90/0** against current models (no drift). Namespace reconciliation deliberately **backed out** → CI-RED-024.
  - **#143** (`6e934218`) — ratchet re-peg: router-count 1190→**1223** (+33 verified-real distinct routes), +2 file-size entries in **root** baseline, CBSP21 manifest.

### OPEN — needs merge (the live work)
- **#144 — CI-RED-003 saw-batch complexity tail.** Branch `codex/ci-red-003-saw-batch-complexity`.
  - The published codex patch fixed complexity but GREW `batch_router.py` 550→604, breaching the file-size sub-gate (debt-gates is an umbrella: complexity AND file-size). **Fixed the root, not blessed:** relocated the mirror helpers (`_load_saw_batch_chain` / `_saw_batch_chain_context` / `_store_rmos_batch_chain` / `_mirror_batch_chain_to_rmos`) into existing `batch_router_helpers.py`. batch_router **604→484** (<500, margin), helpers 123→253.
  - Re-pegged complexity baseline line-keys shifted by the relocation (`create_batch_plan` 69→75, `choose_batch_plan` 482→362). Updated the characterization test's monkeypatch to target `batch_router_helpers` (the code moved modules).
  - **Witnessed:** CI complexity check green; characterization test passes; batch_router off the file-size list. Merges on own merits.
- **#145 — plural file-size baseline (completes #143).** Branch `codex/ci-red-022-plural-file-size-repeg`.
  - **Finding:** there are TWO file-size baselines. #143 updated `ci/file_size_baseline.json` (root, standalone `file-size-check`) but NOT `app/ci/file_sizes_baseline.json` (plural, **debt-gates**). debt-gates red on main since #143 (green @#142 `63791b3c`, red @#143 `6e934218`); the file-size red was masked by CI-RED-003's complexity red until #144 cleared it.
  - Pegs 4 verified-real files into the plural baseline (`violation_count` 146→150): test 1154 (lean, 100 tests, precedent-matching — peg not split), registry 771, router 612, api_runs 503. batch_router NOT pegged (relocated by #144, not blessed).
  - **DEPENDS ON #144.** Merge order **#144 → #145**. On #145's own CI (main base) debt-gates still shows batch_router's reds — those are #144's. **Green witnessed only when both on main.**

---

## Standing items / findings (not blocking the merges)

- **#141's sort fix (`db991182`) never landed** — `api_runs.py` entry is misplaced (out of alphabetical order) in the **root** `ci/file_size_baseline.json`. Pre-existing, cosmetic, out of scope. One-line fix someday.
- **CI-RED-024 reserved** for the namespace reconciliation deliberately backed out of #142 (corrected DXF lifecycle vocabulary). The natural next codex follow-up.
- **Two-file-size-baseline hazard (meta):** root vs plural baselines drift; re-pegs must update BOTH, or unify them. Bit #143.
- **debt-gates umbrella masks which sub-gate fails:** complexity-red hid file-size-red hid plural-baseline staleness; clearing each unmasked the next. Structural trap.
- **CI-RED-021 (from earlier):** main has no branch protection → all gates advisory; merges proceed despite red. (That's WHY #144/#145 can merge red-on-some-gates.)

---

## Environment (this checkout is degraded — read before running anything)

- **System Python is 3.14 with broken numpy** ("cannot load module more than once"). Use the repo venv: `services/api/.venv/Scripts/python.exe` (3.11.9, working).
- **`gh` works via the Bash tool, NOT PowerShell** (PowerShell `gh` errors this session). Use Bash for all `gh`/`git`.
- **Local file-size gate LIES** — `_repo_root()` resolves to `services/api` (its `pyproject.toml`), so rel-paths don't match the baseline's keys; an untracked `services/api/services/` doubled dir also false-negatived (deleted this session). **CI is the sole authoritative file-size witness.**
- **`aiosqlite` missing** in venv → full test suite collection errors; run targeted test files with `-o addopts=""` (clears the forced coverage args).
- **Codex sandbox can't push** (no creds) → this authenticated terminal publishes its work. **Patches arrive UTF-16** — transcode to UTF-8 before `git apply` (`raw.decode('utf-16')`). Patches were generated against older main → may need `git apply --ignore-whitespace` or hand-reconcile against drift.

---

## Disciplines that held (carry them)
1. **Witness on the enforcing surface (CI), never local-through-a-pipe.** Local lied twice this session (broken venv; false-green file-size from doubled-dir pollution). When local and CI disagree, CI is authoritative — and ground the discrepancy to its mechanism, don't hand-wave.
2. **Gate red ≠ my fix failed.** Pull the *actual* failing sub-gate/log before concluding. Caught that #144's relocation worked (batch_router off the list) and the remaining red was a *separate* pre-existing failure (#143's plural gap).
3. **Fix the root, don't bless the void.** #137 retag (not add-to-weights); #144 relocate (not re-baseline 604); verify +33 routes / 1154-test are real before pegging (not auto-bless).
4. **Verify before delete / before peg.** `git grep` confirmed `lifecycle_promotion_router` had one manifest reference before retiring; counted the 1154-test (lean) and checked precedent before peg-not-split.
5. **Staging hygiene:** explicit-path `git add` only; verify `git diff --cached --name-only`; keep `router_count_baseline.json` (scratch dirt) OUT.

## Immediate next action on re-entry
1. Re-verify `main` HEAD + open PRs (board moves).
2. **Merge #144, then #145** (order matters).
3. Watch **debt-gates green on CI** (both complexity AND file-size sub-gates) on merged main — the authoritative witness.
4. Then consider: CI-RED-024 (namespace reconciliation), #141 root-baseline sort tidy.
