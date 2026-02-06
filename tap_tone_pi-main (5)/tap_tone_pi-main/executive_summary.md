# tap_tone_pi: Annotated Executive Summary

**Date:** 2026-02-05
**Prepared by:** Claude (Opus 4.5) — cross-referencing design review, consolidation plan, and verified repo state
**Source documents:**
- `tap_tone_pi_design_review.md` (274 lines, scored 6.3/10)
- `consolidation_plan.md` + `dependency_diagram.mermaid` (from `files (83).zip`)
- Live repo state: `github.com/HanzoRazer/tap_tone_pi` (HEAD as of 2026-02-05)

---

## 1. Bug Status

Two critical bugs were identified in the design review. Verification against the current repo HEAD:

| Bug | File | Design Review Claim | Verified Status | Evidence |
|-----|------|-------------------|-----------------|----------|
| Bug 1 | `modes/chladni/peaks_from_wav.py:53` | `meta, x = read_wav_mono(...)` — return-order swap | **RESOLVED** | Current code reads `x, meta = read_wav_mono(pathlib.Path(args.wav))` — correct order |
| Bug 2 | `tap_tone/storage.py:57` | `write_wav_mono(audio_path, sample_rate, audio)` — transposed args | **STILL LIVE** | Confirmed: passes `sample_rate` where signal `x` is expected, and `audio` where `fs` is expected. Canonical signature is `write_wav_mono(path, x, fs)`. One-line fix. |

**Implication:** The design review was working from a slightly stale snapshot for Bug 1 (it has since been fixed). Bug 2 remains a ship-stopper for Phase 1 capture persistence. Every `tap-tone record` command will produce corrupted WAV files.

---

## 2. Cross-Reference Matrix: Design Review Findings vs. Consolidation Plan Coverage

| Design Review Finding | Severity | Consolidation Plan Addresses It? | Gap? |
|-----------------------|----------|--------------------------------|------|
| Bug 1: peaks_from_wav return order | Critical | Step 5 mentions storage fix only | Moot (already resolved in repo) |
| Bug 2: storage.py transposed args | Critical | Step 5 explicitly fixes this | Covered |
| 4+ competing entry points | High | Steps 7-8 (GUI rewrite + unified CLI) | Covered |
| WAV I/O bypass in tap-tone-lab | High | Step 5 (route through canonical wav.py) | Covered |
| Dual pyproject.toml (silent conflict) | High | Step 9 (single pyproject.toml) | Covered |
| GUI subprocess shelling | High | Step 7 (rewrite to direct imports) | Covered |
| Schema compliance gaps (wolf_candidates) | High | NOT addressed | **GAP** |
| Duplicate schema locations (3 places) | Medium | Section 3.3 says "keep both schemas/ and contracts/" | **GAP** (contradicts own diagnosis) |
| `out/` tracked in git (64 files) | Medium | Section 3.3 says "keep `out/`" | **GAP** (plan doesn't `git rm --cached`) |
| 55% test coverage, no integration tests | Medium | Step 12 runs tests but adds none | **GAP** |
| No version identity (0.1.0 vs 2.0 vs 1.1.0) | Medium | Step 9 declares 1.1.0 | Partially covered (no CHANGELOG) |
| GUI binding bug (var.get() at construction) | Medium | NOT addressed | **GAP** |
| Serial input validation | Low | NOT addressed | Deferred (acceptable) |
| Aesthetics (Tkinter, plot styling) | Low | NOT addressed | Deferred (acceptable) |

**Summary:** The consolidation plan covers the structural issues well (entry point unification, WAV I/O, package layout) but has 5 gaps in data hygiene, testing, and schema compliance.

---

## 3. Consolidation Plan Internal Gaps

Five issues within the consolidation plan itself:

### Gap A: Schema Duplication Not Resolved

The plan's Section 3.3 says "keep `schemas/` and `contracts/`." But verified repo state shows **3 duplicate schemas with DIFFERENT content** between `schemas/` and `contracts/schemas/`:

- `manifest.schema.json` — different in both locations
- `moe_result.schema.json` — different in both locations
- `tap_peaks.schema.json` — different in both locations

Keeping both directories perpetuates the divergence. One location must be declared canonical and the other deleted or symlinked.

### Gap B: `out/` Directory Not Cleaned from Git

The `.gitignore` already excludes `out/`, but 64 files were committed before the rule was added. The consolidation plan says "keep `out/`" without noting that `git rm --cached out/` is needed to stop tracking these files. Without this, every clone ships ~8MB of stale measurement data.

### Gap C: Test-Before-Restructure Missing

The plan restructures first (Steps 1-10), then runs tests last (Step 12). This is backwards for a codebase with known integration bugs. If Step 7 (GUI rewrite) introduces a regression, Step 12 may not catch it because there are no integration tests for the GUI path. The plan should add a "freeze test baseline" step before any file moves.

### Gap D: GUI Rewrite Underestimated

Step 7 estimates 1.5 hours for the GUI rewrite. The current GUI (`gui/app.py`) has:
- 5 `subprocess.check_call` invocations to different mode scripts
- A binding bug in `group()` that captures `var.get()` at construction time
- No error display (errors go to terminal stdout, not the GUI)
- File dialog paths passed unsanitized into shell commands

Rewriting this to use direct imports, fix the binding bug, and add inline error display is closer to 3-4 hours. The plan also doesn't mention the binding bug at all.

### Gap E: No Rollback Strategy

The plan deletes 8+ directories (Section 3.2) with no rollback strategy. If the migration stalls mid-way (e.g., serial hardware modules don't work when moved), the repo is in a half-migrated state. The plan should specify: "All deletions happen in a single commit AFTER the full test suite passes against the new layout."

---

## 4. Unified Resolution Plan

Merging the design review's recommendations with the consolidation plan, correcting for the gaps above:

### Phase 0: Hygiene (before any restructuring)

1. **Fix Bug 2** — one-line change in `tap_tone/storage.py:57`:
   ```python
   # FROM: write_wav_mono(audio_path, sample_rate, audio)
   # TO:   write_wav_mono(audio_path, audio, sample_rate)
   ```
2. **Reconcile schemas** — diff the 3 duplicated schemas, declare `contracts/schemas/` canonical, delete or symlink `schemas/`.
3. **Clean `out/` from git** — `git rm --cached -r out/` (keeps files locally, removes from tracking).
4. **Establish version** — pick one version number (the plan's `1.1.0` is reasonable), add a CHANGELOG.md, tag the pre-migration commit.

### Phase 1: Test Baseline (before restructuring)

5. **Add integration smoke tests** for each major pipeline:
   - Phase 1: synthetic audio -> `analyze_tap()` -> verify JSON output fields
   - Chladni: fixture WAV -> `peaks_from_wav` -> verify peak count and frequency range
   - Storage: round-trip WAV write/read -> verify signal integrity
6. **Record current test pass count** as the baseline (currently ~23 tests).

### Phase 2: Package Skeleton + WAV I/O (consolidation Steps 1-2)

7. Create `tap_tone_pi/` directory structure as specified in the consolidation plan.
8. Move canonical WAV I/O (`modes/_shared/wav_io.py` -> `tap_tone_pi/io/wav.py`).

### Phase 3: Core + Capture Migration (consolidation Steps 3-6)

9. Move core analysis from `tap-tone-lab` (better type hints).
10. Move Phase 2 DSP, hardware capture modules.
11. Fix `storage.py` to import from `tap_tone_pi.io.wav`.

### Phase 4: CLI + GUI Rewrite (consolidation Steps 7-9)

12. Build unified CLI dispatcher (`ttp` command).
13. Rewrite GUI to use direct imports (fix binding bug in same pass).
14. Update `pyproject.toml` to single package.

### Phase 5: Cleanup + CI (consolidation Steps 10-12)

15. Delete old directories in a SINGLE commit after full test suite passes.
16. Add deprecation stubs for `tap_tone/` namespace.
17. Update CI boundary guards.

### Phase 6: Schema Compliance (from design review, not in consolidation plan)

18. Fix `wolf_candidates.json` output to include required fields (`schema_version`, `wsi_threshold`, `coherence_threshold`).
19. Add CI golden-output test: run Phase 2 pipeline on synthetic fixture, validate all outputs against contract schemas.
20. Upgrade WAV I/O guard from grep-based to AST-based import checking.

### Deferred (post-consolidation)

- Serial input validation and bounds checking
- GUI aesthetics (matplotlib canvas, status bar)
- Session SQLite index
- Phase 2 resume capability
- Single-command "quick tap" UX shortcut
- Web-based UI consideration for Pi deployment

---

## 5. Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Serial hardware modules break when moved | Medium | High (blocks bending rig) | Test on actual Pi hardware before deleting old paths; keep `modes/` in git history |
| GUI rewrite takes 2x longer than estimated | High | Medium (delays but doesn't block) | GUI rewrite is independent of CLI/package migration; can be done in parallel or deferred |
| `tap-tone-lab` has code not in root `tap_tone/` | Medium | Medium (lost functionality) | Diff both packages file-by-file before deleting; the exporter.py is already called out |
| Schema reconciliation reveals incompatible consumers | Low | High (breaks downstream) | Check ToolBox's `scripts/analyzer_ingest_smoke.py` against both schema versions first |
| Migration stalls mid-way, repo in half-state | Medium | High | All deletions in single commit after tests pass; tag pre-migration commit for easy revert |

---

## 6. Key Corrections to Source Documents

| Document | Claim | Correction |
|----------|-------|------------|
| Design Review | Bug 1 (peaks_from_wav) is a live crash | **Already resolved.** Current repo has correct argument order. |
| Design Review | References BUILD_READINESS_EVALUATION.md | **File does not exist** in current repo HEAD. May have been removed or renamed. |
| Consolidation Plan | "keep `schemas/`" (Section 3.3) | **Should reconcile, not keep both.** Three schemas have divergent content between `schemas/` and `contracts/schemas/`. |
| Consolidation Plan | "keep `out/`" (Section 3.3) | **Should `git rm --cached`.** 64 files are tracked despite `.gitignore`. |
| Consolidation Plan | Step 7 GUI rewrite: 1.5 hours | **Underestimate.** Binding bug, 5 subprocess paths, error handling = 3-4 hours. |
| Consolidation Plan | Step 12 runs tests last | **Should be Phase 1.** Establish test baseline before restructuring, not after. |

---

## 7. Recommended Sequencing

```
Phase 0 (Hygiene)           ← Can be done TODAY, no restructuring needed
    |
Phase 1 (Test Baseline)     ← MUST happen before any file moves
    |
Phase 2 (Skeleton + WAV)    ← Foundation layer, zero risk
    |
Phase 3 (Core + Capture)    ← Medium risk (serial modules)
    |
Phase 4 (CLI + GUI)         ← GUI is highest effort, can be parallelized
    |
Phase 5 (Cleanup + CI)      ← Single commit: delete old, update guards
    |
Phase 6 (Schema Compliance) ← Can be done independently at any point
```

**Total estimated effort:** 8-10 hours (vs. the consolidation plan's 6-hour estimate), primarily due to the GUI rewrite correction and the addition of Phases 0, 1, and 6.
