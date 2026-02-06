# Critical Design Review: tap_tone_pi

**Date:** 2026-02-05  
**Reviewer:** Claude (Opus 4.5), acting as critical design reviewer  
**Artifact:** `tap_tone_pi-main` (snapshot from upload, ~17k Python LOC, 120+ files)  
**Version declared:** `v0.1.0` (pyproject.toml) / `v2.0-instrumentation` (Build Readiness doc)

---

## Stated Assumptions

Before scoring, I want to be transparent about what I assumed while reviewing:

1. **Target user is Ross (solo developer/luthier)**, not a team of 10. Governance documents reference "acoustics-team" and "chladni-team," but this is a single-operator project today. I'm reviewing against the solo-builder audience, not an enterprise deployment.

2. **Hardware hasn't been validated end-to-end yet.** The code contains simulators, synthetic modes, and hardware capture paths, but the `out/` directory only contains bending rig artifacts. No Phase 2 roving-grid session directories are present, suggesting the ODS pipeline has only run in synthetic/unit-test mode.

3. **tap-tone-lab is an embedded proto-repo,** not a separately maintained package. It duplicates ADRs, scripts, and module names from the parent, and its relationship to the production `tap_tone/` package is unclear at runtime.

4. **The project's self-assessment (BUILD_READINESS_EVALUATION.md) claims 92% readiness.** I'm evaluating against what the code *actually does*, not what it claims.

5. **"Measurement-only" is the north-star philosophy.** I'm taking the boundary doctrine at face value and evaluating whether the implementation actually holds to it.

---

## CRITICAL BUGS FOUND DURING REVIEW

Before scoring, two API-contract bugs that will produce runtime crashes:

### Bug 1: `peaks_from_wav.py` — return-order swap

```python
# modes/chladni/peaks_from_wav.py line 53:
meta, x = read_wav_mono(pathlib.Path(args.wav))
```

But `read_wav_mono` returns `(np.ndarray, WavMeta)` — signal first, metadata second. This assigns the numpy array to `meta` and the WavMeta dataclass to `x`. The subsequent `len(x)` will work (WavMeta has fields), but `x * w` will crash with a type error. **The Chladni peak picker is broken.**

### Bug 2: `storage.py` — transposed arguments to `write_wav_mono`

```python
# tap_tone/storage.py line 57:
write_wav_mono(audio_path, sample_rate, audio)
```

But `write_wav_mono` signature is `(path, x, fs)` — signal second, sample rate third. This passes the integer sample rate as the signal array and the numpy audio array as the sample rate. **Phase 1 capture persistence is broken** — every `tap-tone record` command will fail or silently produce garbage WAV files.

These bugs exist because the WAV I/O layer was refactored (centralized into `modes/_shared/wav_io.py`) but callers weren't updated to match. This is the exact failure mode that happens when you centralize without integration tests across all call sites.

---

## Evaluation

### 1. Purpose Clarity — 9/10

**Justification:** This is the single strongest dimension of the project. The measurement-only philosophy is articulated with unusual rigor: the GOVERNANCE.md alone runs 400+ lines defining what the system may and may not express. The ADR trail (7 decisions), the MEASUREMENT_BOUNDARY.md, the Spectral View UX contract, and the explicit "IS / IS NOT" table in the README all converge on one message: *this system captures facts; interpretation happens elsewhere.*

The boundary between "analysis" and "interpretation" is stated with a crispness that most professional engineering orgs don't achieve. The phrase "Analysis is permitted; interpretation is prohibited" is a loadbearing design principle and it's documented in at least four separate files.

**Improvements:**

- The *version identity* is confused. `pyproject.toml` says `0.1.0`. BUILD_READINESS says `v2.0-instrumentation`. The schema registry says `1.0.0` and `2.0.0` for different schemas. There's no CHANGELOG or release tag trail. An outsider can't tell what version they're holding.
- The project description in `pyproject.toml` says "Offline tap tone analyzer for Raspberry Pi" — this radically undersells the scope. It's now a multi-mode measurement toolchain with ODS, Chladni, bending rig, and wolf metrics.

---

### 2. User Fit — 6/10

**Justification:** The target user is a luthier who wants to measure acoustic properties of tonewoods and guitar plates. The domain expertise embedded here (WSI, transfer functions, Chladni patterns, bending stiffness) is authentic and deep. The *concepts* fit perfectly.

But the *interface* doesn't match the user. A luthier who wants to measure a tap tone currently needs to:

1. Install Python 3.10+, pip, venv, portaudio19-dev
2. Clone the repo, `pip install -e .`
3. Run `python -m tap_tone.main devices` to find their mic index
4. Construct a CLI command with flags: `python -m tap_tone.main record --device 1 --seconds 2.5 --out ./captures/session_001 --label "OM_top_bridge_tap"`

This is a developer workflow, not a craftsperson workflow. The GUI exists but is a Tkinter shell that constructs subprocess commands and shows messagebox dialogs — it doesn't display spectra, doesn't show live waveforms, and doesn't visualize results.

Phase 2 is even steeper: the user must understand what ODS is, know what frequencies to target, and manually manage grid JSON files.

**Improvements:**

- Ship a single-binary or single-script entry point that does device auto-detection, records, analyzes, and shows results in one step. The happy path for "I just want to tap this plate and see frequencies" should be a single command with zero flags.
- The GUI should display the spectrum plot inline rather than writing a PNG and popping a messagebox. Even a matplotlib embedded window would be a significant UX upgrade.
- Add a "first run" wizard or guided mode. The infrastructure for this exists (the config dataclasses have sensible defaults) but there's no on-ramp.
- Consider whether the target deployment (Raspberry Pi) actually benefits from Tkinter. A web-based local UI (Flask + simple HTML) would be more portable and could display plots natively.

---

### 3. Usability — 5/10

**Justification:** There are multiple competing entry points for overlapping functionality, and the relationship between them is unclear:

- `tap_tone/main.py` — Phase 1 CLI (`python -m tap_tone.main`)
- `scripts/phase2_slice.py` — Phase 2 CLI
- `gui/app.py` — Tkinter GUI that shells out to `modes/tap_tone/tap_fft_logger.py`
- `modes/tap_tone/tap_fft_logger.py` and `modes/tap_tone/offline_from_wav.py` — direct mode scripts
- `Makefile` targets — yet another entry point layer
- `tap-tone-lab/` — an entire duplicate CLI structure

A user who finds the repo is confronted with at least 4 different ways to do a tap tone capture, with no clear guidance on which to use. The README documents `python -m tap_tone.main record`, but the GUI calls `modes/tap_tone/tap_fft_logger.py`. These are different code paths with different output formats.

The Makefile is well-structured with comprehensive `help` target, but it introduces yet another interface layer. For Phase 2, the user must know which of `scripts/phase2_slice.py`, `make phase2-full`, or `tools/run_phase2.py` to use.

**Improvements:**

- Consolidate entry points. Pick ONE primary CLI (`tap-tone` from pyproject.toml scripts) and route everything through it: `tap-tone phase1 record`, `tap-tone phase2 run`, `tap-tone bend single`, `tap-tone chladni wizard`. The Makefile can remain as a developer shortcut but shouldn't be the documented workflow.
- Remove or clearly mark `tap-tone-lab/` as archived/experimental. Right now it's a full package with its own `pyproject.toml`, CLI, and duplicate ADRs sitting inside the production repo. This is confusing.
- The GUI's `group()` helper function has a binding bug: it captures `var.get()` at widget construction time, not at callback time, so the MOE single-shot form will always use the initial default values regardless of what the user types. This is a usability-breaking bug.

---

### 4. Reliability — 5/10

**Justification:** The governance documentation promises a high reliability bar — deterministic DSP, schema validation, WAV I/O guardrails. The *infrastructure* for reliability is genuinely impressive: 7 CI workflows, boundary import checking, WAV I/O centralization, schema registries.

But the implementation has holes:

- **Two critical bugs** (documented above) that would crash core workflows.
- **Test coverage is self-assessed at 55%.** There are 10 test files with ~23 tests. The critical `analyze_tap()` function has zero direct unit tests. The `storage.py` persistence path has zero tests. The GUI has zero tests.
- **No integration tests.** The WAV I/O refactoring broke two callers because there are no end-to-end tests that exercise the capture→analyze→persist pipeline.
- **The Chladni module's `peaks_from_wav.py`** was never successfully run against real data (the API mismatch proves this).
- **Schema compliance mismatch** is self-documented in BUILD_READINESS_EVALUATION.md: "The code is NOT generating output matching the contracts." The wolf_candidates.json output is missing required fields like `schema_version`, `wsi_threshold`, and `coherence_threshold`.
- **No hardware regression suite.** This is acknowledged as intentional ("hardware-dependent tests MUST NOT be required for PR merge"), but there's also no documented procedure for manual hardware validation.

The WAV I/O guardrail is clever but has a known gap: the grep-based CI check (`wav-io-guard.yml`) looks for literal strings `wavfile.read` and `wavfile.write`. Any import aliasing (`from scipy.io.wavfile import read as wav_read`) would bypass it. The test file itself uses `from scipy.io import wavfile` and is correctly excluded, but the exclusion is path-based, not semantic.

**Improvements:**

- Fix the two critical bugs immediately.
- Add integration tests: `test_phase1_pipeline()` that runs `record → analyze → persist` with synthetic audio and validates the output directory structure and JSON content. `test_chladni_pipeline()` that runs peaks extraction on a fixture WAV and validates the output.
- Add property-based checks on the WAV I/O API: any module that imports `read_wav_mono` or `write_wav_mono` should have a test that calls it, ensuring signature compatibility.
- The schema compliance gap needs a CI-enforced golden-output test: run the Phase 2 pipeline on a synthetic fixture and validate every output file against its contract schema.
- Consider `ast`-based import checking instead of grep for the WAV I/O guard and boundary check.

---

### 5. Manufacturability / Maintainability — 7/10

**Justification:** The codebase has strong maintainability foundations: frozen dataclasses throughout, pure analysis functions, explicit configuration objects, and a well-documented dependency direction (`modes/ → scripts/phase2/` via `modes/_shared/wav_io.py`). The boundary enforcement tooling (boundarygen, check_boundary_imports, no_logic_creep) is genuinely sophisticated for a solo project.

The ADR trail is excellent. Seven numbered decisions with rationale, consequences, and explicit non-goals. This is better documentation hygiene than most professional codebases.

However, several structural issues threaten long-term maintainability:

- **Dual schema locations:** `schemas/measurement/` AND `contracts/schemas/` AND `docs/schemas/` all contain JSON schemas. The schema_registry.json tries to unify this, but files exist in three places.
- **Duplicate ADRs:** `docs/ADR-0001` through `ADR-0007` exist in the root project AND in `tap-tone-lab/docs/ADR-0001` through `ADR-0007`. If one set is updated, the other drifts.
- **The `out/` directory is committed to git** with actual measurement session data (bending rig runs, session manifests). This should be `.gitignore`'d.
- **`poetry.lock` is committed** alongside `pyproject.toml` + `requirements.txt` — three dependency specification files.

**Improvements:**

- Consolidate schemas into one canonical location (`contracts/`) and symlink or delete the others.
- Remove `tap-tone-lab/` from this repo entirely, or move it to a `_lab/` or `experimental/` directory with a clear README that says "this is not production code."
- Add `out/` to `.gitignore`. Ship example outputs under `examples/` instead.
- Pick one dependency manager (poetry OR setuptools) and remove the other's artifacts.

---

### 6. Cost — 8/10

**Justification:** The BOM is minimal and well-chosen: Raspberry Pi 4/5, USB measurement mic (UMIK-1 class), and for the bending rig a load cell + dial indicator on serial. Total hardware cost is under $200. Software dependencies are all open-source (numpy, scipy, sounddevice, matplotlib, pyserial).

The processing requirements are modest — FFT on 2.5-second captures, Welch cross-spectra for Phase 2. Nothing here needs a GPU or cloud compute.

**Improvements:**

- Document the actual BOM with specific part numbers and approximate costs. The ENGINEER_HANDOFF.md mentions "UMIK-1 class" but doesn't list what's actually been tested.
- The `sounddevice` dependency pulls in PortAudio, which requires system-level packages (`portaudio19-dev`). On a fresh Raspberry Pi OS this is a manual step that could trip up a non-developer user. Consider documenting a one-liner install script or Ansible playbook.

---

### 7. Safety — 7/10

**Justification:** The measurement-only boundary doctrine IS a safety feature: by refusing to make design recommendations, the system can't give bad structural advice that leads to a collapsed guitar top or wasted tonewood.

The SHA-256 provenance hashing on artifacts provides data integrity assurance. The immutable-artifact doctrine ("downstream systems MUST NOT modify raw measurement artifacts") protects against accidental data corruption in the integration chain.

However:

- **No input validation on serial capture.** `loadcell_serial.py` and `dial_indicator_serial.py` read from serial ports with regex parsing. There's no bounds checking, timeout handling, or malformed-data rejection documented in the code.
- **The GUI shells out to subprocesses with `subprocess.check_call(shlex.split(cmd))`.** The command strings are constructed from user-entered text (StringVar values). While `shlex.split` provides some protection, the path variables from file dialogs are not sanitized.
- **No signal-level safety.** The capture module doesn't validate that `sounddevice.rec()` actually returned valid audio (it checks for NaN but not for all-zeros, which would indicate a disconnected or muted mic).

**Improvements:**

- Add a post-capture sanity check: if RMS < threshold (e.g., -60 dBFS), warn the user that no meaningful signal was detected.
- Validate serial input data against expected ranges before processing.
- In the GUI, use list-based `subprocess.check_call()` instead of string commands passed through `shlex.split()`.

---

### 8. Scalability — 6/10

**Justification:** The architecture scales well *conceptually*. The mode-based structure (`modes/tap_tone`, `modes/bending_stiffness`, `modes/chladni`) is extensible. The schema registry and contract system support versioning. The boundary enforcement tooling would catch architectural violations as the codebase grows.

But practical scalability has issues:

- **Phase 2 roving grid capture is interactive and sequential.** Each grid point requires a separate tap + capture cycle. For a 35-point grid, that's 35 manual interactions. There's no batch mode, no automation, and no way to resume a partially-completed grid.
- **Data volume isn't managed.** Each Phase 2 point produces a WAV file (~230KB at 48kHz/2ch/2s). A 35-point grid produces ~8MB per session. Over months of testing across multiple instruments, this grows fast with no archival or cleanup strategy.
- **No database or index.** Sessions are identified by filesystem timestamps. Finding "all sessions for instrument X" requires walking the directory tree.
- **The viewer pack export** (viewer_pack_v1) is the right idea for packaging results, but there's no viewer application. The pack is a ZIP with JSON — useful for archival but not for interactive review.

**Improvements:**

- Add session-resume capability for Phase 2: save grid progress to the session manifest and allow `phase2_slice.py run --resume <session_dir>`.
- Implement an SQLite index for sessions: instrument_id, build_stage, timestamp, session_dir. This doesn't violate the measurement-only boundary — it's a catalog, not an interpretation.
- Define a data retention policy. Old sessions could be zipped and moved to archival storage while keeping the manifest index.
- Build or document a viewer for the viewer_pack_v1 format (even a simple HTML+JS single-page app would suffice).

---

### 9. Aesthetics — 4/10

**Justification:** The GUI is functional but visually rudimentary. It's a single-window Tkinter form with LabelFrames, Entry widgets, and "Run" buttons — essentially a shell command builder with a graphical skin. There's no live visualization, no color, no status indicators, and the window doesn't resize gracefully.

The CLI output (`print_summary`) is clean and readable, but text-only.

The generated plots (via matplotlib) are serviceable but not styled. No consistent color palette, no branding, no figure titling conventions.

The documentation aesthetics are actually strong — the README has clear sections, the ADRs follow a consistent template, and the governance doc uses ASCII diagrams effectively. But users don't read governance docs; they see the GUI and the plot outputs.

**Improvements:**

- If sticking with Tkinter, add a matplotlib canvas for inline spectrum display. The `FigureCanvasTkAgg` widget is straightforward and would transform the GUI from "command launcher" to "measurement instrument."
- Define a plot stylesheet (matplotlib rcParams) for consistent fonts, colors, and DPI across all generated figures.
- Add a status bar or log panel to the GUI so users can see command output without switching to a terminal.
- Long-term: consider a web-based UI (Dash, Streamlit, or plain Flask+JS) for the Pi deployment. This would give you responsive layout, better plotting, and remote access.

---

## Score Summary

| Category | Score | Weight | Weighted |
|---|---|---|---|
| Purpose Clarity | 9/10 | High | ★★★★★★★★★ |
| User Fit | 6/10 | High | ★★★★★★ |
| Usability | 5/10 | High | ★★★★★ |
| Reliability | 5/10 | Critical | ★★★★★ |
| Maintainability | 7/10 | Medium | ★★★★★★★ |
| Cost | 8/10 | Medium | ★★★★★★★★ |
| Safety | 7/10 | Medium | ★★★★★★★ |
| Scalability | 6/10 | Medium | ★★★★★★ |
| Aesthetics | 4/10 | Low | ★★★★ |

**Unweighted average: 6.3/10**

---

## Top 5 Actions (Priority Order)

1. **Fix the two API-contract bugs** in `peaks_from_wav.py` and `storage.py`. These are ship-stoppers that prove the refactored WAV I/O layer was never integration-tested.

2. **Add integration tests** for each major pipeline (Phase 1 capture→persist, Phase 2 synthetic→analyze→export, Chladni peaks→index). The current 55% test coverage is concentrated on WAV I/O and schema validation but misses the actual user workflows.

3. **Consolidate entry points** into a single `tap-tone` CLI with subcommands. Kill the ambiguity between `python -m tap_tone.main`, `modes/tap_tone/tap_fft_logger.py`, `scripts/phase2_slice.py`, and Makefile targets.

4. **Resolve the schema compliance gaps** documented in BUILD_READINESS_EVALUATION.md. The wolf_candidates output is missing required fields. Add a CI golden-output test that validates pipeline output against contracts.

5. **Embed a spectrum display in the GUI.** The single change that would most dramatically improve user fit is showing the frequency spectrum inline after a capture, instead of writing a PNG and popping a messagebox.

---

## Overall Assessment

This is a project with exceptional *architectural thinking* and mediocre *execution follow-through*. The governance docs, ADR trail, boundary enforcement, and schema contracts are genuinely best-in-class for a solo project — most professional engineering teams don't document their architectural decisions this thoroughly.

But the code beneath those docs has integration gaps that the documentation itself anticipates but doesn't catch. The WAV I/O centralization was the right architectural move, but it was done without updating all callers or adding integration tests, producing two silent breakages in core workflows. The schema compliance system is well-designed but the code doesn't actually comply with its own schemas.

The measurement-only philosophy is the project's most defensible strength. Hold onto it ruthlessly. The temptation to add "just a little interpretation" will grow as the toolchain matures. The governance docs are your immune system.

*The project is ready to measure. It's not yet ready for someone else to measure with it.*
