# Changelog

All notable changes to this project are documented here. This file follows [Keep a Changelog](https://keepachangelog.com/) style and [Semantic Versioning](https://semver.org/).

## [2.0.0] — 2026-02-05

### Breaking Changes
- **Package restructure** — consolidated package namespace from `tap_tone` to `tap_tone_pi`
- Import paths changed: `from tap_tone.analysis import analyze_tap` → `from tap_tone_pi.core.analysis import analyze_tap`
- Deprecation stubs provided for backward compatibility (one release cycle)

### Fixed
- **Bug 2: WAV write argument transposition** — `storage.py:57` had `write_wav_mono(path, sample_rate, audio)` instead of `write_wav_mono(path, audio, sample_rate)`. All Phase 1 captures now produce valid WAV files.

### Added
- Regression test for storage.py WAV write path (`test_storage_wav_roundtrip.py`)
- Unified CLI entry points: `ttp` (short) and `tap-tone` (discoverable)
- Schema location documented: `contracts/schemas/` is canonical (per `schema_registry.json`)

### Changed
- Removed 64 stale measurement files from git tracking (`out/` directory)
- GUI rewritten to use direct imports instead of subprocess calls
- GUI binding bug fixed (form values now captured at callback time, not construction)
- **Matplotlib spectrum viewer** — inline visualization with peak annotations (Phase 6)
- Deleted `tap-tone-lab/` directory (49 files, content migrated to `tap_tone_pi/`)

[2.0.0]: https://github.com/HanzoRazer/tap_tone_pi/compare/analyzer-v1.2.0...analyzer-v2.0.0

---

## [1.2.0] — 2026-01-21

### Added
- **Auto-Trigger Capture** — hands-free impulse detection for `tap_tone gold-run`:
  - `--auto-trigger` flag enables automatic tap detection
  - EMA noise floor estimation during warmup
  - Trigger conditions: peak > noise×10, RMS > noise×3 (configurable)
  - Debounce to avoid glitches (consecutive frames required)
  - Pre-roll (50ms default) + post-roll (1500ms default) capture windowing
  - Clipping detection with reject/accept option
  - Full provenance tracking: `noise_rms`, `trigger_peak`, `snr_est_db`, etc.
- New module: `tap_tone/capture/auto_trigger.py`
  - `AutoTriggerConfig` — all detection parameters
  - `AutoTriggerDetector` — stateful detector with state machine
  - `RingBuffer` — pre-roll audio buffering
  - `capture_one_impulse_stream()` — hardware-agnostic capture
  - `capture_one_impulse_sounddevice()` — sounddevice integration
- 22 unit tests for auto-trigger (synthetic waveforms, no hardware)

### CLI Options (auto-trigger group)
```
--auto-trigger          Enable auto-trigger mode
--warmup-s 0.5          Noise floor estimation period
--peak-mult 10          Peak threshold multiplier
--rms-mult 3            RMS threshold multiplier
--debounce-frames 2     Consecutive trigger frames
--pre-ms 50             Pre-roll before trigger
--post-ms 1500          Post-roll after trigger
--reject-clipping       Reject clipped captures (default)
--no-reject-clipping    Accept with warning
--min-impulse-ms 2      Ignore ultra-short glitches
```

[1.2.0]: https://github.com/HanzoRazer/tap_tone_pi/compare/analyzer-v1.1.0...analyzer-v1.2.0

---

## [1.1.0] — 2026-01-21

### Added
- **`tap_tone gold-run`** CLI command — one-command Gold Standard Run:
  - Capture N points → export viewer pack → validate → optional ingest
  - `--dry-run` mode for preview without hardware
  - `--json` output for machine-readable results
  - Exit codes: 0=success, 2=validation failed, 3=capture failed, 4=device error, 5=unexpected
  - Makefile targets: `gold-run`, `gold-run-dry`
- **`tap_tone/__main__.py`** — enables `python -m tap_tone` invocation
- Developer experience documentation:
  - [INSTRUMENT_SCOPE.md](docs/INSTRUMENT_SCOPE.md)
  - [QUICKSTART.md](docs/QUICKSTART.md)
  - [FIRST_MEASUREMENT_CHECKLIST.md](docs/FIRST_MEASUREMENT_CHECKLIST.md)
  - [GOLD_STANDARD_EXAMPLE_RUN.md](docs/GOLD_STANDARD_EXAMPLE_RUN.md)
  - [GOLD_RUN_COMMAND_SPEC.md](docs/GOLD_RUN_COMMAND_SPEC.md)
- Reference comparison dataset (`examples/reference/run_a_dry`, `examples/reference/run_b_humid`)

### Changed
- Pre-commit workflow now runs on all branches and PRs

[1.1.0]: https://github.com/HanzoRazer/tap_tone_pi/compare/analyzer-v1.0.0...analyzer-v1.1.0

---

## [1.0.0] — 2026-01-18

### Added
- Same feature set as 1.0.0-rc1 promoted to stable:
  - **Schema Registry** (`contracts/schema_registry.json`) with contracts:
    `tap_peaks`, `moe_result`, `measurement_manifest`, `chladni_run`,
    and Phase-2: `phase2_ods_snapshot`, `phase2_wolf_candidates`.
  - **Registry-driven validator** (`scripts/validate_schemas.py`).
  - **Hardware-free demos**: Chladni v1, Phase-2 mini run, MOE.
  - **Canonical WAV I/O** (`modes/_shared/wav_io.py`) + CI guard.
  - **Chladni mismatch policy** (warn+keep; fail if `delta_hz` exceeds tolerance).
  - **Run-level manifest append** for Chladni (idempotent).
  - **Local CI dry run** (`make ci-dry-run`).

### CI / Quality Gates
- Pytest + **coverage ≥ 80%** (merge-blocking).
- **WAV I/O guard** (no direct `scipy.io.wavfile` outside `_shared`).
- **Schema-bump guard** (registry version bump required).
- **PR title linter** for schema edits (`schema: …`).
- **Schema validation** for demo artifacts.
- **CODEOWNERS** for `contracts/**` and `modes/_shared/**`.

### Notes
- Analyzer remains **measurement-only** (facts, not advisories). ToolBox handles interpretation.

[1.0.0]: https://github.com/HanzoRazer/tap_tone_pi/releases/tag/analyzer-v1.0.0

---

## [1.0.0-rc1] — 2026-01-18

### Added
- **Schema Registry** at `contracts/schema_registry.json` and **contracts** for:
  - `tap_peaks`, `moe_result`, `measurement_manifest`, `chladni_run`
  - Phase-2: `phase2_ods_snapshot`, `phase2_wolf_candidates`
- **Registry-driven validator**: `scripts/validate_schemas.py` (consumes registry; no hardcoded maps).
- **Hardware-free demos**:
  - **Chladni v1**: `examples/chladni/` (WAV → peaks → image index → `chladni_run.json`) + manifest append.
  - **Phase-2 mini**: `examples/phase2/` with canonical filenames under `runs_phase2/DEMO/session_0001/`.
  - **MOE**: `examples/moe/` producing a valid `moe_result.json`.
- **Canonical WAV I/O**: `modes/_shared/wav_io.py` (float32 in ±1, PCM16 out).
- **Chladni mismatch policy**: warn+keep with `delta_hz`; **fail** if worst `delta_hz` exceeds `CHLADNI_FREQ_TOLERANCE_HZ` (default 5 Hz).
- **Run-level manifest append** for Chladni: `modes/chladni/manifest_utils.py` (idempotent).
- **Local CI dry run**: `make ci-dry-run` (tests → coverage → demos → schema validation).
- **Pre-export validator**: `tap_tone/validate/viewer_pack_v1.py` for staged directory validation.

### Changed
- All readers/writers route through canonical WAV I/O; removed ad-hoc `/32767` scaling.
- Docs: Governance and Measurement README updated with policy, demos, and local CI instructions.

### CI / Quality Gates
- **pytest** + **coverage ≥ 80%** (merge-blocking).
- **WAV I/O guard**: disallow `scipy.io.wavfile` outside `modes/_shared/wav_io.py`.
- **Schema-bump guard**: changes to `contracts/schemas/*.schema.json` must bump versions in the registry.
- **PR title linter** for schema edits (`schema: …` prefix).
- **Schema validation** in CI for `out/**` and Phase-2 demo.
- **CODEOWNERS** for `contracts/**` and `modes/_shared/**`.

### Tests
- Chladni policy unit tests (warn vs fail).
- Manifest test asserts expected entries + SHA-256 hashes and idempotency.
- Pre-export validator tests (15 rules across M/S/P/W/A/O categories).

### Notes
- This release is **Analyzer-only** ("facts, not opinions"). Design/CAM interpretation remains out-of-scope.

[1.0.0-rc1]: https://github.com/HanzoRazer/tap_tone_pi/releases/tag/analyzer-v1.0.0-rc1
