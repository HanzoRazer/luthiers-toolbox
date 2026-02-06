# Bending Rig — Quick Start

Bending stiffness / MOE measurement from synchronized load + displacement streams.

## Input Artifacts

| Artifact | Source | Format |
|----------|--------|--------|
| `load_series.json` | Load cell (serial/DAQ) | `{"unit": "N"\|"lbf", "data": [[t, force], ...]}` |
| `displacement_series.json` | Dial indicator (serial/DAQ) | `{"unit": "mm"\|"in", "data": [[t, disp], ...]}` |

---

## Serial Acquisition (Capture from Hardware)

### Load Cell Capture

```bash
make loadcell CFG=config/devices/loadcell_example.json OUT=out/run/load_series.json
```

Or directly:

```bash
python modes/acquisition/loadcell_serial.py \
  --config config/devices/loadcell_example.json \
  --out out/run/load_series.json
```

**Config file** (`config/devices/loadcell_example.json`):
- `port`: Serial port (COM4, /dev/ttyUSB0)
- `baud`: Baud rate (default 115200)
- `unit`: Output unit after calibration (N or lbf)
- `parse`: How to extract value from line (`csv_idx` or `regex`)
- `calibration`: Linear transform `y = a*x + b`
- `sample_rate_hz`, `duration_s`: Capture parameters

### Dial Indicator Capture

```bash
make dial PORT=/dev/ttyUSB0 OUT=out/run/displacement_series.json UNIT=mm DUR=8 RATE=20
```

Or directly:

```bash
python modes/acquisition/dial_indicator_serial.py \
  --port /dev/ttyUSB0 --baud 9600 \
  --unit mm --pattern "(-?[0-9]+\.?[0-9]*)" --scale 1.0 \
  --duration 10 --rate 20 \
  --out out/run/displacement_series.json
```

**Flags:**
- `--port`: Serial port
- `--unit`: mm or in
- `--pattern`: Regex to extract numeric value
- `--scale`: Multiply raw value (e.g., 25.4 to convert in→mm)
- `--duration`: Capture time in seconds
- `--rate`: Target sample rate (Hz)

---

## Workflow

### 1) Merge streams → pairs → derived MOE

```bash
make bend-merge-moe \
  LOAD=out/20251231_150000/load_series.json \
  DISP=out/20251231_150000/displacement_series.json \
  OUTDIR=out/20251231_150000/rig \
  METHOD=3point SPAN=400 WIDTH=20 THICKNESS=3.0 RATE=50 FLO=10 FHI=90
```

**Outputs:**
- `pairs.csv` — synchronized (t_s, force_N, disp_mm)
- `pairs_sidecar.json` — provenance + units
- `bending_moe.json` — derived MOE with fit statistics

### 2) Plot force vs displacement

```bash
make plot-fvd \
  PAIRS=out/20251231_150000/rig/pairs.csv \
  OUT=out/20251231_150000/rig/f_vs_d.png \
  FLO=10 FHI=90 TITLE="F–d — Run 20251231_150000"
```

**Output:** Scatter plot with linear fit overlay showing slope (N/mm) and R².

### 3) Emit manifest

```bash
make manifest OUT=out/20251231_150000/rig/manifest.json \
  ARTIFACTS="--artifact out/20251231_150000/load_series.json \
             --artifact out/20251231_150000/displacement_series.json \
             --artifact out/20251231_150000/rig/pairs.csv \
             --artifact out/20251231_150000/rig/pairs_sidecar.json \
             --artifact out/20251231_150000/rig/bending_moe.json \
             --artifact out/20251231_150000/rig/f_vs_d.png" \
  RIG="--rig fixture=3-point --rig span_mm=400 --rig operator=Ross" \
  NOTES="--notes Checkpoint 2025-12-31 15:11 CT"
```

**Output:** `manifest.json` with SHA-256 hashes for all artifacts.

---

## Makefile Defaults

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE` | 50 | Resample rate (Hz) |
| `METHOD` | 3point | Bending method (3point/4point) |
| `SPAN` | 400 | Support span (mm) |
| `WIDTH` | 20 | Specimen width (mm) |
| `THICKNESS` | 3.0 | Specimen thickness (mm) |
| `FLO` | 10 | Lower fit percentile |
| `FHI` | 90 | Upper fit percentile |
| `DPI` | 150 | Plot resolution |

---

## Direct Python Invocation

If you prefer not to use `make`:

```bash
# Merge + MOE
python modes/bending_rig/merge_and_moe.py \
  --load load_series.json --disp displacement_series.json \
  --out-dir ./out/rig \
  --method 3point --span 400 --width 20 --thickness 3.0 \
  --rate 50 --fit-pct-low 10 --fit-pct-high 90

# Plot
python modes/bending_rig/plot_f_vs_d.py \
  --pairs-csv ./out/rig/pairs.csv \
  --out ./out/rig/f_vs_d.png \
  --pct-low 10 --pct-high 90 --title "F–d"

# Manifest
python modes/_shared/emit_manifest.py \
  --out ./out/rig/manifest.json \
  --artifact load_series.json \
  --artifact displacement_series.json \
  --artifact ./out/rig/pairs.csv \
  --rig fixture=3-point --rig span_mm=400 \
  --notes "Test run"
```

---

## Output Schema Summary

> **Schema Registry:** All validators must source schema file locations and versions from `contracts/schema_registry.json` (no hardcoded maps).

### bending_moe.json

```json
{
  "artifact_type": "bending_moe",
  "E_GPa": 12.345,
  "method": "3point",
  "geometry": {"span_mm": 400, "width_mm": 20, "thickness_mm": 3.0},
  "fit": {"slope_N_per_mm": 5.678, "r2": 0.9987, "pct_low": 10, "pct_high": 90},
  "provenance": {"pairs_sha256": "...", "load_sha256": "...", "disp_sha256": "..."}
}
```

### manifest.json

```json
{
  "artifact_type": "measurement_manifest",
  "created_utc": "2025-12-31T21:11:00Z",
  "rig": {"fixture": "3-point", "span_mm": 400, "operator": "Ross"},
  "notes": "...",
  "artifacts": [{"path": "...", "sha256": "...", "bytes": 1234}, ...]
}
```

---

## Viewer Pack Validation & Comparison

### Validate a Viewer Pack ZIP

```bash
python scripts/viewer_pack_validate.py pack.zip
# or via make:
make validate-pack PACK=viewer_pack_session123.zip
```

Checks:
- `viewer_pack.json` exists and validates against schema
- All listed files exist in ZIP
- SHA-256 and byte counts match manifest
- bundle_sha256 integrity

### Compare Two Viewer Packs (Measurement Regression)

Use for before/after wood removal analysis:

```bash
python scripts/viewer_pack_diff.py baseline.zip after.zip --out diff_out/
# or via make:
make diff-packs BASELINE=pre.zip MODIFIED=post.zip DIFF_OUT=results/ PLOTS=1
```

Outputs (measurement-only, no interpretation):
- `delta_summary.json` — alignment info + summary statistics
- `delta_curves.csv` — per-frequency mean deltas
- `plots/*.png` — overlay visualizations (with `--plots`)

**Requirements:**
- Same grid point IDs (fails if point sets differ)
- Same frequency bins (fails if misaligned beyond 0.1 Hz)

---

## Future: Acquisition Scripts

For sensor capture (not yet implemented):

- `modes/acquisition/loadcell_serial.py` → `load_series.json`
- `modes/acquisition/dial_indicator_serial.py` → `displacement_series.json`

Say **"add capture scripts"** if you need these.

---

## WAV I/O Policy & Tests

**Canonical module:** `modes/_shared/wav_io.py`

### Policy

- Readers return **float32** in **[-1, 1]** (best effort normalization).
- `read_wav_mono()` uses **channel 0** if the file is stereo (policy knob lives here).
- Writers (`write_wav_mono`, `write_wav_2ch`) accept float32 in [-1, 1] and write **PCM int16**.
- If we ever switch to 24-bit, we will do it **only in this module**.

### Why This Matters

- Eliminates int16↔float scaling drift across tools.
- One place to adjust stereo/mono policy used by every mode.

### Tests

Run with **pytest**:

```bash
pytest -q tests/test_wav_io.py tests/test_wav_io_roundtrip.py
```

The suite verifies:

- Mono and 2-channel **round-trip** (level within ~0.2 dB, corr > 0.999)
- Mono-from-stereo **policy** (channel-0 selection)
- Import **normalization** from raw int16 WAVs
- `level_dbfs` utility sanity
- **Int16 quantization tolerance** (max abs error ≤ 2.5e-4)

---

## Quick-start Demos

### Chladni v1
```bash
make examples-chladni-demo
```
Artifacts: `out/DEMO/chladni/{capture.wav, peaks.json, F0148.png, F0226.png, chladni_run.json, manifest.json}`

### Phase-2 mini run
```bash
make examples-phase2-demo
```
Artifacts under `runs_phase2/DEMO/session_0001/` with canonical filenames.

### MOE (static bending) demo
```bash
make examples-moe-demo
```
Artifact: `out/DEMO/moe/moe_result.json` (validated against `contracts/schemas/moe_result.schema.json`).

---

## Chladni Pattern Indexing

**Module:** `modes/chladni/`

### Frequency Mismatch Policy

**Mismatch policy:** warn + keep, **fail** if `delta_hz` exceeds `CHLADNI_FREQ_TOLERANCE_HZ` (default 5 Hz).

- Each pattern record includes `nearest_detected_hz` and `delta_hz`
- Warnings are recorded in `_warnings` array
- Exit code 2 if worst delta exceeds tolerance
- Override via `--tolerance-hz` flag or `CHLADNI_FREQ_TOLERANCE_HZ` env var

### Usage

```bash
# Extract peaks from sweep WAV
python modes/chladni/peaks_from_wav.py \
  --wav out/RUN/capture.wav \
  --out out/RUN/peaks.json \
  --min-hz 50 --max-hz 2000

# Index pattern images to frequencies
python modes/chladni/index_patterns.py \
  --peaks-json out/RUN/peaks.json \
  --images out/RUN/F0148.png out/RUN/F0226.png \
  --plate-id PLATE_001 \
  --tempC 22.0 --rh 45.0 \
  --out out/RUN/chladni_run.json
```
