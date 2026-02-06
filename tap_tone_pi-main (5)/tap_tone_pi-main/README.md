# tap_tone_pi — Instrumentation (Measurement-Only)

This repo is a **measurement instrument toolchain** for luthier lab work:
- Phase 1: single-mic tap tone capture + FFT peaks
- Phase 2: roving-grid 2-channel capture + ODS (transfer functions) + coherence + wolf metrics (WSI)
- Bending rig: bending stiffness measurements (EI / k) with defensible metadata

> **Boundary:** This project measures and summarizes signals. It does **not** interpret "tone quality"
> or prescribe structural modifications. See `docs/MEASUREMENT_BOUNDARY.md`.

---

## What this repo is (and is not)

### ✅ IS
- evidence capture (WAV + capture metadata)
- deterministic DSP summaries (FFT peaks, transfer function H(f), coherence γ²(f))
- robust bundle persistence (session folders, derived artifacts)
- schemas and validation contracts for outputs

### ❌ IS NOT
- "design optimizer"
- "tone grader"
- structural modification advisor
- ToolBox/RMOS backend (interop is export-only)

---

## Quickstart

### Install (Pi or desktop)
```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-dev
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -U pip
pip install -e .
```

---

## Phase 1 — Single-mic tap tone

List audio devices:
```bash
python -m tap_tone.main devices
```

Record + analyze:
```bash
python -m tap_tone.main record \
  --device 1 \
  --seconds 2.5 \
  --out ./captures/session_001 \
  --label "OM_top_bridge_tap"
```

Live mode (simple loop):
```bash
python -m tap_tone.main live --device 1 --out ./captures/live
```

### Outputs

Each capture produces:

* `audio.wav`
* `analysis.json` (peaks, dominant frequency, confidence)
* `spectrum.csv` (freq_hz, magnitude)
* `session.jsonl` (append-only log)

---

## Phase 2 — Roving-grid ODS + coherence + wolf metrics

### Canonical Phase 2 CLI

**Main executable:** `scripts/phase2_slice.py`
**Canonical package:** `scripts/phase2/`
**Canonical grid:** `config/grids/guitar_top_35pt.json`

```bash
python scripts/phase2_slice.py --help
```

### Typical run directory

```
runs_phase2/
  session_YYYYMMDDTHHMMSSZ/
    grid.json
    metadata.json
    points/
      point_A1/
        audio.wav
        capture_meta.json
        analysis.json
        spectrum.csv
    derived/
      ods_snapshot.json
      wolf_candidates.json
      wsi_curve.csv
    plots/
      *.png
```

### Common workflow

```bash
# Synthetic validation (no hardware)
python scripts/phase2_slice.py run \
  --grid examples/phase2_grid_mm.json \
  --out ./runs_phase2 \
  --synthetic

# Hardware capture
python scripts/phase2_slice.py devices
python scripts/phase2_slice.py run \
  --grid config/grids/guitar_top_35pt.json \
  --out ./runs_phase2 \
  --device 1
```

See `docs/phase2/README.md` for full documentation.

---

## Bending rig workflow

Bending stiffness measurements are documented in `docs/MEASUREMENT_README.md`.

### Simulated demo (no hardware)

```bash
make sim-load OUT=out/DEMO/load_series.json SIM_AMP_F=12 SIM_BASE_F=0.5 SEED=1337
make sim-dial OUT=out/DEMO/displacement_series.json SIM_AMP_D=0.8 SEED=1337

make bend-merge-moe LOAD=out/DEMO/load_series.json DISP=out/DEMO/displacement_series.json \
  OUTDIR=out/DEMO/rig METHOD=3point SPAN=400 WIDTH=20 THICKNESS=3.0

make plot-fvd PAIRS=out/DEMO/rig/pairs.csv OUT=out/DEMO/rig/f_vs_d.png
```

---

## Validation & Contracts

Machine-readable output contracts live in `contracts/`.

Key Phase 2 schemas:
* `contracts/phase2_grid.schema.json`
* `contracts/phase2_session_meta.schema.json`
* `contracts/phase2_point_capture_meta.schema.json`
* `contracts/phase2_ods_snapshot.schema.json`
* `contracts/phase2_wolf_candidates.schema.json`

---

## Policies / governance

* Measurement boundary: `docs/MEASUREMENT_BOUNDARY.md`
* Agent guidance: `.github/copilot-instructions.md`
* ADR trail: `docs/ADR-0001-measurement-scope.md` … `docs/ADR-0007_PHASE2_ODS_COHERENCE.md`

---

## Failure playbook (Analyzer)

1. **Schema validation fails**
   - Run: `make validate-schemas` (or `python scripts/validate_schemas.py --out-root out`)
   - Read the error paths/messages and fix the offending JSON producer.

2. **Chladni tolerance exceeded**
   - The run fails if worst `delta_hz` > `CHLADNI_FREQ_TOLERANCE_HZ` (default 5 Hz).
   - Re-check your excitation, mounting, or set a stricter/looser env value explicitly.

3. **WAV guard trips in CI**
   - Direct `scipy.io.wavfile` usage is blocked outside `modes/_shared/wav_io.py`.
   - Import `read_wav_mono/2ch` or `write_wav_mono/2ch` from that module instead.

4. **Viewer pack export fails**
   - Check `validation_report.json` for specific rule violations.
   - Common issues: missing manifest, frequency grid mismatch, peak off-grid.

---

## Run IDs & retention

- Use `from modes._shared.run_id import new_run_dir` to create timestamped run folders,
  e.g., `out/2026-01-20T17-22-31Z_ab12cd/`.
- Add a brief retention/backup policy as needed (e.g., sync `out/**` to S3 with SHA256).

---

## Contributing

See `CONTRIBUTING.md`.

