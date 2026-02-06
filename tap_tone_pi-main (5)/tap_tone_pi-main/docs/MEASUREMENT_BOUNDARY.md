# Analyzer Measurement Boundary — Tap Tone Pi

Purpose: define the measurement-only scope, file placements, namespaces, and contracts needed to integrate Analyzer outputs with the Luthier’s ToolBox, without introducing advisory logic or design optimization.

## Scope (Measurement-only)
- Capture, compute, and log: peaks, spectra, and mechanical test facts.
- Persist artifacts + provenance; no advisory, scoring, or design hints here.
- Keep analysis functions pure; CLI headless; artifact-first.

## Files To Land (paths + intent)
- modes/tap_tone/tap_fft_logger.py — tap-tone capture + FFT peak logger; outputs `tap_tone.json` and optional `spectrum.csv`.
- modes/bending_stiffness/deflection_to_moe.py — converts deflection test inputs to EI/MOE; outputs `bending_test.json`.
- modes/provenance_import/attach_grain_provenance.py — attaches grain direction/provenance to measurement bundle.
- modes/_shared/manifest.py — hashing, timestamps, run IDs; writes `manifest.json` for bundles.
- schemas/measurement/manifest.schema.json — JSON Schema for `manifest.json`.
- schemas/measurement/tap_peaks.schema.json — JSON Schema for `tap_tone.json`.
- schemas/measurement/moe_result.schema.json — JSON Schema for `bending_test.json`.
- examples/measurement/* — 1–2 small JSON/CSV examples for tap peaks and bending test.
- requirements-extra.txt — only if new tap/bending modes need deps beyond [pyproject.toml](../pyproject.toml).
- ci/no_logic_creep.yml — guardrail: block advisory imports or ToolBox coupling.

## Namespaces (must import)
- modes.tap_tone
- modes.bending_stiffness
- modes.provenance_import
- modes._shared
- schemas.measurement

Note: create `__init__.py` in each subfolder to ensure importability.

## CLI Discovery (if runner exists)
- A single CLI can discover `modes.*` via entrypoint scanning or module introspection.
- Pattern: `python -m modes.tap_tone.tap_fft_logger --device 1 --out ./captures/session_001` (or add a thin dispatcher).

## Cross-Repo Contracts
- Shared artifact names (Analyzer → ToolBox ingestion):
  - bending_test.json — EI/MOE facts
  - tap_tone.json — peaks and optional spectrum path
  - manifest.json — hashes, provenance, rig config
- ToolBox expected keys (confirm in contracts/*):
  - specimen, fixture, span_mm, force_N, deflection_mm, E_GPa, uncertainty, hashes
- Analyzer schema roots:
  - schemas/measurement/manifest.schema.json
  - schemas/measurement/tap_peaks.schema.json
  - schemas/measurement/moe_result.schema.json

## Repo Layout Assumptions
- Root-level: modes/, schemas/, docs/, examples/, ci/ (this repo)
- ToolBox: services/api/app/…, contracts/, presets/, docs/, tests/, ci/

## Implementation Guidance
- Reuse capture/analysis patterns from [tap_tone](../tap_tone):
  - Capture: sounddevice (mono v0.1), windowed recording
  - Analysis: high-pass → Hanning → rFFT → normalized mag → peak picking
  - Storage: WAV/JSON/CSV + session log; manifests (hashes, ts, run_id)
- Keep analysis functions pure (no I/O inside), headless CLI for reproducibility.
- Adopt conservative defaults; repeatability scripts and schema validation as in [scripts](../scripts) and [docs/schemas](../docs/schemas).

## Minimal Examples (to add under examples/measurement)
- tap_tone.json (example):
```json
{
  "artifact_type": "tap_tone",
  "sample_rate": 48000,
  "dominant_hz": 192.3,
  "peaks": [{"freq_hz": 192.3, "magnitude": 0.88}, {"freq_hz": 311.0, "magnitude": 0.52}],
  "spectrum_path": "./captures/session_001/capture_20250101T000000Z/spectrum.csv",
  "rms": 0.023,
  "clipped": false,
  "confidence": 0.74,
  "label": "OM_top_bridge_tap",
  "ts_utc": "2025-01-01T00:00:00Z"
}
```
- bending_test.json (example):
```json
{
  "artifact_type": "bending_test",
  "specimen": "spruce_plate_A",
  "fixture": "three_point_bend",
  "span_mm": 200.0,
  "force_N": 10.0,
  "deflection_mm": 1.25,
  "E_GPa": 11.8,
  "uncertainty": 0.12,
  "hashes": {"audio.wav": "<sha256>", "analysis.json": "<sha256>"},
  "ts_utc": "2025-01-01T00:00:00Z"
}
```
- manifest.json (example):
```json
{
  "schema_version": "0.1.0",
  "capture_dir": "./captures/session_001/capture_20250101T000000Z",
  "run_id": "run_abc123",
  "ts_utc": "2025-01-01T00:00:00Z",
  "rig": {"mic_model": "UMIK-1", "distance_mm": 300},
  "hashes": {"audio.wav": "<sha256>", "analysis.json": "<sha256>", "spectrum.csv": "<sha256>"}
}
```

## CI Guardrails
- Add `ci/no_logic_creep.yml` job to fail on:
  - imports of `advisory`, `ToolBox`, or `services/api/app` modules
  - forbidden directories writes outside modes/, schemas/, docs/, examples/

## Next Steps / Checks
- Confirm exact ToolBox `contracts/*` field names (adjust schemas accordingly).
- Create package `modes` and `schemas` skeletons with `__init__.py` for import checks.
- Wire a lightweight CLI dispatcher (optional) that runs a selected mode.
- Validate examples via the new JSON Schemas and include in CI.
