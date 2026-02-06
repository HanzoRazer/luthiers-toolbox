# Developer Handoff — Tap Tone PI (Desktop)

**Goal:** Provide a reliable, offline, desktop measurement utility for acoustic tap response: record audio, compute FFT-based peak summary, store artifacts.

## What it does

- Captures short audio window from configured input device (USB mic recommended).
- Runs simple analysis:
  - DC removal + optional high-pass
  - windowing
  - FFT magnitude spectrum
  - peak picking with guardrails (prominence + min spacing)
- Writes artifacts to a local folder per capture.

## Inputs

- Audio input device index (ALSA/PortAudio)
- Sample rate, channels
- Recording window length (seconds)
- Optional label (tap point name)
- Output directory

## Outputs

Per capture folder:
- `audio.wav`
- `analysis.json`
- `spectrum.csv`

And per session directory:
- `session.jsonl` (append-only event log)

## Architecture

- `capture.py`: audio recording (sounddevice → numpy)
- `analysis.py`: DSP + peak detection
- `storage.py`: writes files, session log
- `ui_simple.py`: text output + formatting
- `main.py`: CLI entrypoint

## Edge cases

- No mic / wrong device index → explicit error
- Clipped audio → flag in analysis.json
- Low signal/no peaks → returns confidence low, empty peaks list
- Varying sample rates → uses actual stream rate

## Observability / testing

- Designed to be deterministic given recorded .wav.
- Next steps for tests:
  - unit tests for FFT/peaks on canned wav fixtures
  - CLI smoke test in CI using generated synthetic signals (sine burst)

## Operational risks

- Device driver setup on Pi (ALSA/USB mic)
- Room noise can dominate if gain too high
- Tap location/support conditions dominate results — MUST document measurement protocol later

## Future integration (RMOS)

This tool writes artifacts already in "Run attachment" shape:
- `audio.wav` and `analysis.json` can be uploaded later into runs_v2 attachments store.
- Add a future "export" step to create a RunArtifact payload (not implemented here).
