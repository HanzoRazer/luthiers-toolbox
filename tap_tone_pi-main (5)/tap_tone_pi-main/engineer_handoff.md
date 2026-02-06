# tap_tone_pi: Chief Engineer Handoff

**Date:** 2026-02-05
**Purpose:** Implementation guide for the tap_tone_pi consolidation effort
**Companion document:** `executive_summary.md` (read first for full context)

---

## How to Use This Document

This handoff is structured as a series of **decision gates**. Each gate contains:

1. **Context** — what the issue is and why it matters
2. **Decision question(s)** — what needs to be decided before proceeding
3. **Recommended path** — the suggested answer, based on analysis
4. **Action items** — concrete steps to execute

Work through the gates in order. Each gate unlocks the next phase of the consolidation.

---

## Gate 0: Pre-Flight Verification

### Context

The design review identified two critical bugs. Verification against the current repo shows Bug 1 is already resolved, but Bug 2 is still live. Before any restructuring begins, the codebase must be in a known-good state.

### Decision Questions

**Q0.1: Is the `storage.py` argument transposition (Bug 2) the correct fix?**

Current code at `tap_tone/storage.py:57`:
```python
write_wav_mono(audio_path, sample_rate, audio)
```

Canonical signature at `modes/_shared/wav_io.py`:
```python
def write_wav_mono(path, x, fs, *, pcm_bits=16)
```

The fix is:
```python
write_wav_mono(audio_path, audio, sample_rate)
```

- Have you personally verified this call site?
- Are there other callers of `write_wav_mono` that may also be transposed? (The design review only found this one, but a `grep -rn "write_wav_mono" --include="*.py"` across the repo would confirm.)
- Does this function currently have any test coverage? If not, should a regression test be added alongside the fix?

**Recommended path:** Fix immediately, add a round-trip WAV write/read test, commit as a standalone bugfix before starting consolidation.

---

**Q0.2: Which schema location is canonical — `schemas/` or `contracts/schemas/`?**

Three files exist in both locations with DIFFERENT content:
- `manifest.schema.json`
- `moe_result.schema.json`
- `tap_peaks.schema.json`

- Which version is authoritative? (Check: which version do the CI workflows validate against? Which version does ToolBox's `analyzer_ingest_smoke.py` expect?)
- Is any downstream consumer (ToolBox, viewer packs, RMOS) currently importing from `schemas/` rather than `contracts/schemas/`?
- Can the non-canonical location be deleted entirely, or does it need to remain as a symlink for backward compatibility?

**Recommended path:** `contracts/schemas/` is canonical (it's the location referenced in `schema_registry.json`). Diff the 3 files, merge any fields from `schemas/` that are missing in `contracts/schemas/`, then delete `schemas/` duplicates. Verify with `scripts/validate_schemas.py`.

---

**Q0.3: Should the 64 tracked files in `out/` be removed from git history?**

The `.gitignore` already excludes `out/`, but these files were committed before the rule. Options:
1. `git rm --cached -r out/` — stops tracking, keeps files locally, doesn't rewrite history
2. `git filter-branch` or `git filter-repo` — removes from history entirely (reduces clone size)
3. Leave as-is — accept the bloat

- Does anyone currently depend on these files being in the repo? (e.g., test fixtures that reference `out/` paths)
- Is the repo shared with external collaborators where clone size matters?

**Recommended path:** Option 1 (`git rm --cached`). Simple, non-destructive, and sufficient. History rewriting is overkill for a solo project.

---

### Action Items (Phase 0)

- [ ] Fix Bug 2 in `tap_tone/storage.py:57`
- [ ] Add WAV round-trip regression test
- [ ] Reconcile 3 duplicate schemas (decide canonical location)
- [ ] Run `git rm --cached -r out/`
- [ ] Decide on version number (consolidation plan proposes `1.1.0`)
- [ ] Create CHANGELOG.md
- [ ] Tag pre-migration commit (e.g., `v0.1.0-pre-consolidation`)
- [ ] Commit all Phase 0 changes

---

## Gate 1: Test Baseline

### Context

The consolidation plan restructures first and tests last (Step 12). This is high-risk: if moving files introduces import errors or breaks module resolution, you won't know until everything is already reorganized. Establishing a test baseline first gives you a "green bar" to return to.

### Decision Questions

**Q1.1: What is the current test pass count, and are there any known failures?**

Run `pytest tests/ -v` right now and record:
- Total tests: ___
- Passed: ___
- Failed: ___
- Skipped: ___

This number is your baseline. After every phase of the consolidation, this count must not decrease.

---

**Q1.2: Which integration tests should be added BEFORE restructuring?**

The design review identified that the critical `analyze_tap()` function has zero direct tests, the storage path has zero tests, and the GUI has zero tests. Adding integration tests before restructuring provides two benefits:
1. Catches regressions introduced by file moves
2. Verifies the current code actually works (avoiding moving broken code to a new location)

Suggested minimum integration tests:
- Phase 1 pipeline: synthetic audio -> `analyze_tap()` -> verify JSON output structure
- WAV round-trip: `write_wav_mono()` -> `read_wav_mono()` -> compare arrays
- Chladni pipeline: fixture WAV -> `peaks_from_wav` -> verify peak list not empty

Do you agree with these three, or are there other critical paths that should be covered first?

---

**Q1.3: Should hardware-dependent tests be part of the baseline?**

The repo's GOVERNANCE.md states hardware tests must not be required for PR merge. But the consolidation moves hardware capture modules (`loadcell_serial.py`, `dial_indicator_serial.py`). If these break during the move, no automated test will catch it.

Options:
1. Add mock-based hardware tests (mock serial port, verify protocol parsing)
2. Document a manual hardware verification checklist for post-migration
3. Accept the risk (hardware modules are stable, move is mechanical)

**Recommended path:** Option 2 — document a manual checklist. Mock-based serial tests are valuable but shouldn't block the consolidation effort.

---

### Action Items (Phase 1)

- [ ] Run `pytest tests/ -v`, record baseline count
- [ ] Add integration test: Phase 1 pipeline (synthetic audio -> analyze -> verify)
- [ ] Add integration test: WAV round-trip
- [ ] Add integration test: Chladni peak extraction
- [ ] Commit test additions
- [ ] Verify baseline is green

---

## Gate 2: Package Skeleton

### Context

This is the lowest-risk phase: creating empty directories and moving the canonical WAV I/O module. Nothing is deleted yet.

### Decision Questions

**Q2.1: Is `tap_tone_pi` the correct package name?**

The consolidation plan uses `tap_tone_pi`. The current repo name is `tap_tone_pi` (with underscores in the GitHub repo). The pyproject.toml currently declares `tap-tone-pi` (with hyphens) as the distribution name.

- `tap_tone_pi` = Python package (importable)
- `tap-tone-pi` = PyPI distribution name (installable)
- `ttp` = CLI command (the consolidation plan's proposed shortcut)

Are you comfortable with all three names? The CLI command `ttp` is short but potentially collides with other tools. Alternatives: `tapi`, `tonepi`, `tap-tone`.

---

**Q2.2: Should `modes/_shared/wav_io.py` be COPIED or MOVED in this phase?**

The consolidation plan says "cp" (copy). This means both locations exist temporarily. The alternative is to move immediately and update all imports in the same commit.

- Copy-first approach: safer (old code keeps working), but creates a temporary duplication window
- Move-first approach: cleaner (no duplication), but requires updating all imports atomically

**Recommended path:** Copy in this phase, verify imports work from the new location, then delete the old location in Phase 5. The temporary duplication is acceptable because `wav_io.py` is stable and unlikely to diverge in the 2-3 hours between copy and delete.

---

### Action Items (Phase 2)

- [ ] Create directory structure: `tap_tone_pi/{core,capture,io,phase1,phase2,bending,chladni,export,cli,gui}`
- [ ] Create `__init__.py` in each subdirectory
- [ ] Copy `modes/_shared/wav_io.py` -> `tap_tone_pi/io/wav.py`
- [ ] Copy `modes/_shared/manifest.py` -> `tap_tone_pi/io/manifest.py`
- [ ] Verify: `python -c "from tap_tone_pi.io.wav import read_wav_mono, write_wav_mono"`
- [ ] Commit

---

## Gate 3: Core + Capture Migration

### Context

This phase moves analysis code and hardware capture modules. The main risk is the hardware serial modules — they interact with physical devices and can't be tested without hardware.

### Decision Questions

**Q3.1: Which `analysis.py` is the source of truth?**

Two versions exist:
- `tap_tone/analysis.py` (634 LOC root package, v0.1.0)
- `tap-tone-lab/tap_tone/analysis.py` (982 LOC fork, v0.3.2, better type hints)

The consolidation plan says "take tap-tone-lab version." But:
- Has the root version received any fixes that the lab version doesn't have?
- Does the lab version have any dependencies on lab-specific infrastructure?
- Should you diff the two files before choosing?

**Recommended path:** Run `diff tap_tone/analysis.py tap-tone-lab/tap_tone/analysis.py` and review the differences. Take the lab version as the base, but cherry-pick any fixes from root that aren't in the lab.

---

**Q3.2: What is the serial protocol for loadcell and dial indicator modules?**

When `loadcell_serial.py` and `dial_indicator_serial.py` are moved to `tap_tone_pi/capture/`, their imports change. But these modules also:
- Open serial ports by device path (hard-coded or config-based?)
- Parse incoming bytes with regex patterns
- Have no input validation (noted in design review)

Questions:
- Are the serial device paths configured via `config/` files, or hard-coded?
- Do any other modules import from these files?
- Can you test these on actual hardware after the move, before merging?

---

**Q3.3: What about the simulator modules (`*_sim.py`)?**

The consolidation plan says "merge into `simulators.py`." Are these:
- Simple mock classes that return fixed data?
- Full replay engines that read recorded serial sessions?
- Something else?

The answer affects how they should be organized. If they're simple mocks, a single `simulators.py` is fine. If they're complex, they may warrant their own submodule.

---

### Action Items (Phase 3)

- [ ] Diff both `analysis.py` versions, choose canonical
- [ ] Move core analysis -> `tap_tone_pi/core/analysis.py`
- [ ] Move config -> `tap_tone_pi/core/config.py`
- [ ] Move Phase 2 DSP -> `tap_tone_pi/core/dsp.py`
- [ ] Move Phase 2 metrics, grid, viz -> `tap_tone_pi/phase2/`
- [ ] Move hardware capture -> `tap_tone_pi/capture/`
- [ ] Fix `storage.py` WAV import to use `tap_tone_pi.io.wav`
- [ ] Move bending modules -> `tap_tone_pi/bending/`
- [ ] Move Chladni modules -> `tap_tone_pi/chladni/`
- [ ] Move export modules -> `tap_tone_pi/export/`
- [ ] Update all internal imports
- [ ] Run test suite, verify baseline count maintained
- [ ] Commit

---

## Gate 4: CLI + GUI Rewrite

### Context

This is the highest-effort phase. The unified CLI is straightforward, but the GUI rewrite has hidden complexity.

### Decision Questions

**Q4.1: How much GUI investment is warranted right now?**

The design review scored aesthetics at 4/10 and suggested considering a web-based UI for the Pi deployment. The consolidation plan rewrites the Tkinter GUI to use direct imports instead of subprocess calls.

Three levels of GUI investment:
1. **Minimal:** Fix subprocess -> direct import. Fix binding bug. Ship as-is. (~3 hours)
2. **Medium:** Above + add matplotlib canvas for inline spectrum display. (~6 hours)
3. **Full:** Replace Tkinter with web UI (Flask/Dash). (~2-3 days)

Which level matches your current priorities? The CLI will be the primary interface for power users regardless.

---

**Q4.2: Should the GUI binding bug be fixed in this phase or deferred?**

The `group()` helper in `gui/app.py` captures `var.get()` at widget construction time (when the callback lambda is created), not at execution time (when the button is clicked). This means form values are always the initial defaults.

This bug exists in the current GUI and will be carried forward if not fixed during the rewrite. Fixing it during the rewrite is natural (you're already touching all the callback code), but it adds scope.

**Recommended path:** Fix during the rewrite. It's a 15-minute fix once you're already refactoring the callbacks, and leaving it creates a known-broken UI.

---

**Q4.3: What CLI command name — `ttp` or `tap-tone`?**

The consolidation plan proposes `ttp` as the primary command with `tap-tone` as backward compat. Consider:
- `ttp` is fast to type but opaque to new users
- `tap-tone` is descriptive but verbose for repeated use
- Both can coexist via `[project.scripts]`

**Recommended path:** Ship both. `ttp` for daily use, `tap-tone` for discoverability. No cost to having two entry points when they call the same function.

---

### Action Items (Phase 4)

- [ ] Build CLI dispatcher in `tap_tone_pi/cli/main.py`
- [ ] Implement subcommands: devices, record, live, analyze-wav, phase2, bend, last, sessions, export, gui
- [ ] Rewrite `gui/app.py` to import from `tap_tone_pi` (no subprocess)
- [ ] Fix GUI binding bug (capture var.get() at call time, not construction time)
- [ ] Update `pyproject.toml` with unified package config
- [ ] Run test suite
- [ ] Commit

---

## Gate 5: Cleanup + CI

### Context

This is the point of no return for directory deletion. Everything must be green before this commit.

### Decision Questions

**Q5.1: Are you confident the test suite covers all moved code paths?**

Before deleting old directories, verify:
- `pytest tests/ -v` passes (count >= Phase 1 baseline)
- `pip install -e .` works from repo root
- `ttp devices` runs without import errors
- `ttp record --device 0 --out /tmp/test --seconds 1` captures (if hardware available)
- `ttp gui` launches without errors

If ANY of these fail, do NOT delete old directories yet.

---

**Q5.2: Should deprecation stubs be temporary or permanent?**

The consolidation plan adds a `DeprecationWarning` shim in the old `tap_tone/__init__.py` that re-exports from `tap_tone_pi`. This helps any external code that imports from the old namespace.

Questions:
- Does any external code import from `tap_tone`? (ToolBox, sg-agentd, other repos?)
- If not, skip the shim and delete outright.
- If yes, keep the shim for one release cycle, then delete.

---

**Q5.3: Should all deletions be in one commit or staged?**

Options:
1. **Single commit:** Delete all old directories at once. Clean diff, easy to revert.
2. **Staged:** Delete one directory per commit. Easier to bisect if something breaks.

**Recommended path:** Single commit. You've already verified everything works. Staged deletion just creates a longer period of partial duplication.

---

### Action Items (Phase 5)

- [ ] Run full verification checklist (see consolidation plan Section 6)
- [ ] Delete: `tap_tone/`, `tap-tone-lab/`, `modes/tap_tone/`, `modes/acquisition/`, `modes/bending_stiffness/`, `modes/bending_rig/`, `modes/chladni/`, `modes/_shared/`, `modes/provenance_import/`
- [ ] Add deprecation stubs if needed (see Q5.2)
- [ ] Update CI boundary guards (`check_boundary_imports.py`, `wav-io-guard.yml`)
- [ ] Update `boundary_spec.json` for new namespace
- [ ] Run `grep -r "from modes\." tap_tone_pi/` — must return nothing
- [ ] Run `grep -r "from tap_tone\." tap_tone_pi/` — must return nothing
- [ ] Run `grep -r "scipy.io.wavfile" tap_tone_pi/` — must return only `io/wav.py`
- [ ] Commit all deletions in single commit
- [ ] Tag: `v1.1.0`

---

## Gate 6: Schema Compliance

### Context

This gate can be worked on independently of the restructuring. The design review found that pipeline outputs don't comply with their own contract schemas.

### Decision Questions

**Q6.1: What fields are missing from `wolf_candidates.json` output?**

The design review mentions `schema_version`, `wsi_threshold`, and `coherence_threshold` as missing required fields. Verify:
- Run the Phase 2 pipeline on synthetic data
- Compare output against `contracts/schemas/wolf_candidates.schema.json`
- List all missing or incorrect fields

---

**Q6.2: Should CI enforce schema compliance?**

Two options:
1. **Golden output test:** Commit a fixture output, validate new outputs match structure
2. **Schema validation test:** Validate outputs against JSON schema at runtime

**Recommended path:** Both. Golden output catches regressions. Schema validation catches new fields added without updating the contract.

---

### Action Items (Phase 6)

- [ ] Audit all pipeline outputs against their contract schemas
- [ ] Fix missing fields in wolf_candidates output
- [ ] Add CI golden-output test for Phase 2 pipeline
- [ ] Upgrade WAV I/O guard from grep-based to AST-based (or accept grep limitation)
- [ ] Commit

---

## Summary: The 10 Questions That Unlock Everything

If you answer these 10 questions before starting, every implementation decision follows naturally:

| # | Question | Unlocks |
|---|----------|---------|
| 1 | Have you verified Bug 2 and confirmed the one-line fix? | Phase 0 |
| 2 | Which schema location is canonical — `schemas/` or `contracts/schemas/`? | Phase 0 |
| 3 | What is the current test pass count? | Phase 1 baseline |
| 4 | Which `analysis.py` is the source of truth (root vs lab)? | Phase 3 |
| 5 | Are serial device paths hard-coded or config-driven? | Phase 3 risk |
| 6 | How much GUI investment is warranted right now (minimal/medium/full)? | Phase 4 scope |
| 7 | Does any external code import from `tap_tone`? | Phase 5 (deprecation stubs) |
| 8 | What fields are missing from `wolf_candidates.json`? | Phase 6 |
| 9 | Is there a Pi available for post-migration hardware testing? | Risk mitigation |
| 10 | What version number should the consolidated package use? | Versioning throughout |

---

## Dependency Graph

```
Q1 (Bug 2 fix)         ─┐
Q2 (Schema canonical)   ─┤── Phase 0 (Hygiene)
Q10 (Version number)    ─┘
                          │
Q3 (Test baseline)      ──── Phase 1 (Test Baseline)
                          │
                        ──── Phase 2 (Skeleton + WAV I/O)
                          │
Q4 (analysis.py source) ─┐
Q5 (Serial config)      ─┤── Phase 3 (Core + Capture)
                          │
Q6 (GUI investment)     ──── Phase 4 (CLI + GUI)
                          │
Q7 (External imports)   ──── Phase 5 (Cleanup)
                          │
Q8 (Missing fields)     ──── Phase 6 (Schema Compliance)
                          │
Q9 (Pi available)       ──── Hardware verification (cross-cutting)
```

---

## Final Notes

- **Tag before you restructure.** If anything goes wrong, `git checkout v0.1.0-pre-consolidation` gets you back instantly.
- **One phase per commit.** This makes `git bisect` useful if a regression surfaces later.
- **Run the test suite after every phase.** The count should never decrease.
- **The GUI can wait.** If time is short, the CLI-first approach (Phases 0-3, 5) delivers 80% of the value without touching the GUI at all.
- **Schema compliance (Phase 6) is independent.** It can be done before, during, or after the restructuring. Don't let it block the main consolidation.
