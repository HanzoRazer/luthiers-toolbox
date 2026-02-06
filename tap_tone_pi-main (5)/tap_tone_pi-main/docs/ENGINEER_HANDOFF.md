# Engineer Handoff — Tap Tone Pi

> **Executive Summary**: Acoustic measurement instrumentation for luthiers.  
> **Scope**: Facts-only measurement (peaks, spectra, coherence, MOE). No design advice.  
> **Target**: Raspberry Pi 4/5 + USB measurement mic (UMIK-1 class).

---

## 1. Repository Structure

```
tap_tone_pi/
├── tap_tone/              # Phase 1: Core single-channel CLI (FROZEN baseline)
├── scripts/               # Phase 2+: Multi-channel, ODS, coherence, wolf metrics
│   └── phase2/            # Phase 2 vertical slice package
├── modes/                 # Specialized measurement modes
│   ├── _shared/           # ★ CANONICAL shared utilities (wav_io.py)
│   ├── acquisition/       # Serial capture (loadcell, dial indicator)
│   ├── bending_rig/       # MOE from load+displacement
│   ├── chladni/           # Nodal pattern indexing
│   └── tap_tone/          # Offline WAV analysis
├── config/                # Device and grid configurations
│   ├── devices/           # loadcell_example.json, dial_indicator_example.json
│   └── grids/             # guitar_top_35pt.json (ODS grid definitions)
├── contracts/             # JSON schemas for cross-repo artifact validation
├── docs/                  # ADRs, schemas, measurement boundary docs
│   └── schemas/           # JSON schemas for bundle validation
├── tests/                 # pytest suite
│   └── _util/             # Test utilities (gen_tone.py)
├── gui/                   # Tkinter GUI (optional)
├── Makefile               # ★ Primary task router
└── pyproject.toml         # Package definition
```

### Two Packages Exist

| Package | Path | Status | Purpose |
|---------|------|--------|---------|
| `tap_tone` | `tap_tone/` | **Frozen v1.0** | Phase 1 baseline — do not modify |
| `tap-tone-lab` | `tap-tone-lab/` | Experimental | Research sandbox — separate repo |

---

## 2. Namespace Map

### Import Paths

```python
# Phase 1 CLI (frozen)
from tap_tone import capture, analysis, storage

# Canonical WAV I/O (★ ALL WAV reads/writes go through here)
from modes._shared.wav_io import read_wav_mono, read_wav_2ch, write_wav_mono, write_wav_2ch

# Phase 2 package
from scripts.phase2 import io_wav, dsp, metrics, viz

# Measurement modes
from modes.bending_rig import merge_and_moe, plot_f_vs_d
from modes.acquisition import loadcell_serial, dial_indicator_serial
from modes.chladni import peaks_from_wav, index_patterns
```

### Package `__init__.py` Requirements

Every folder under `modes/` and `scripts/` that needs to be importable **must** have an `__init__.py`:

```
modes/
├── __init__.py
├── _shared/
│   └── __init__.py
├── acquisition/
│   └── __init__.py
├── bending_rig/
│   └── __init__.py
└── chladni/
    └── __init__.py
```

---

## 3. Router Configuration (Makefile)

The `Makefile` is the **primary CLI router** for all measurement tasks.

### Key Targets

| Target | Description | Example |
|--------|-------------|---------|
| `grid-capture` | Interactive 2-ch grid capture | `make grid-capture DEVICE=1 GRID=config/grids/guitar_top_35pt.json OUT=out/grid_001` |
| `ods-compute` | Compute transfer functions H(f) | `make ods-compute CAPDIR=out/grid_001 FREQS=100,150,185,220,280` |
| `grid-coherence` | γ²(f) coherence analysis | `make grid-coherence CAPDIR=out/grid_001 FREQS=100,150,185` |
| `wolf-metrics` | WSI(f) wolf stress index | `make wolf-metrics CAPDIR=out/grid_001 WSI_THRESH=0.6` |
| `phase2-analyze` | Full Phase 2 pipeline | `make phase2-analyze CAPDIR=out/grid_001 FREQS=100,150,185,220,280` |
| `bend-merge-moe` | Bending rig: merge + MOE | `make bend-merge-moe LOAD=... DISP=... OUTDIR=... METHOD=3point SPAN=400` |
| `plot-fvd` | Force vs displacement plot | `make plot-fvd PAIRS=out/rig/pairs.csv OUT=out/rig/f_vs_d.png` |
| `manifest` | Emit SHA-256 manifest | `make manifest OUT=... ARTIFACTS="--artifact ..."` |
| `chladni-peaks` | Extract Chladni peaks | `make chladni-peaks WAV=... OUT=... MIN_HZ=50 MAX_HZ=2000` |
| `chladni-index` | Index nodal patterns | `make chladni-index PEAKS=... IMAGES=... OUT=...` |

### Default Variables

```makefile
RATE      ?= 50       # Resample rate (Hz)
METHOD    ?= 3point   # Bending method
SPAN      ?= 400      # Support span (mm)
WIDTH     ?= 20       # Specimen width (mm)
THICKNESS ?= 3.0      # Specimen thickness (mm)
FLO       ?= 10       # Lower fit percentile
FHI       ?= 90       # Upper fit percentile
DPI       ?= 150      # Plot resolution
```

---

## 4. WAV I/O Policy (Critical)

### Canonical Module

**`modes/_shared/wav_io.py`** — ALL WAV reads/writes MUST use this module.

### API Signatures

```python
# Readers return (signal, metadata) or (ref, rov, metadata)
read_wav_mono(path: Path) -> Tuple[np.ndarray, WavMeta]
read_wav_2ch(path: Path)  -> Tuple[np.ndarray, np.ndarray, WavMeta]

# Writers: (path, signal(s), sample_rate)
write_wav_mono(path: Path, x: np.ndarray, fs: int) -> None
write_wav_2ch(path: Path, x_ref: np.ndarray, x_rov: np.ndarray, fs: int) -> None
```

### Policy

- **Input**: Readers normalize to `float32` in `[-1, 1]`
- **Output**: Writers accept `float32`, write PCM int16
- **Stereo→Mono**: Uses channel 0 (policy knob lives in `read_wav_mono`)
- **24-bit**: Not yet supported; if needed, modify only this module

### CI Guardrail

`.github/workflows/wav-io-guard.yml` fails if `wavfile.read` or `wavfile.write` appears outside the canonical module.

---

## 5. Artifact Contracts

### Per-Capture Bundle Structure

```
capture_20251231T120000Z/
├── audio.wav           # PCM int16, mono or 2-channel
├── analysis.json       # ts_utc, dominant_hz, peaks[], rms, clipped, confidence
├── spectrum.csv        # freq_hz,magnitude (for reprocessing)
└── session.jsonl       # Append-only session log (at parent dir)
```

### Phase 2 Grid Capture Structure

```
grid_run_001/
├── grid.json                   # Grid definition (copied from config/)
├── points/                     # Per-point captures
│   ├── A1/audio.wav            # 2-channel: ref + roving
│   ├── A1/capture_meta.json
│   └── ...
└── derived/                    # Computed outputs
    ├── ods/ods_summary.json
    ├── coherence/coherence_summary.json
    └── wolf/wolf_candidates.json
```

### Schema Versions

| Artifact | Schema | Location |
|----------|--------|----------|
| `ods_snapshot.json` | `phase2_ods_snapshot_v2` | `contracts/phase2_ods_snapshot.schema.json` |
| `wolf_candidates.json` | `phase2_wolf_candidates_v2` | `contracts/phase2_wolf_candidates.schema.json` |
| `bending_moe.json` | `moe_result` | `contracts/moe_result.schema.json` |
| `manifest.json` | `measurement_manifest` | `contracts/measurement_manifest.schema.json` |
| `tap_tone.json` | `tap_peaks` | `contracts/tap_peaks.schema.json` |

### Provenance Requirements

Every derived artifact **must** include SHA-256 hashes of source artifacts:

```json
{
  "provenance": {
    "audio_sha256": "abc123...",
    "grid_sha256": "def456...",
    "script_version": "0.2.1"
  }
}
```

---

## 6. DSP Patterns

### Pure Functions

Analysis code **must** be pure — no I/O inside DSP functions:

```python
# ✅ Good: Pure function
def analyze_tap(audio: np.ndarray, sample_rate: int) -> AnalysisResult:
    ...

# ❌ Bad: I/O mixed with analysis
def analyze_and_save(audio, path):
    ...
```

### Standard Pipeline

```python
# 1. High-pass filter (20 Hz, 2nd-order Butterworth)
x = highpass(x - np.mean(x), fs, hz=20.0)

# 2. Window (Hanning)
w = np.hanning(len(x))
x_windowed = x * w

# 3. FFT
X = np.fft.rfft(x_windowed)
freqs = np.fft.rfftfreq(len(x), 1.0 / fs)
mag = np.abs(X) / (len(x) / 2.0)

# 4. Peak detection
from scipy.signal import find_peaks
peaks, _ = find_peaks(mag, prominence=threshold)
```

### Coherence (Phase 2)

```python
from scipy.signal import coherence
f_coh, coh = coherence(ref, rov, fs=fs, nperseg=4096)
```

### Transfer Function (ODS)

```python
H = FFT(roving) / FFT(reference)  # Complex transfer function
magnitude = np.abs(H)
phase = np.angle(H)
```

---

## 7. Configuration Files

### Device Config (`config/devices/`)

```json
{
  "device_type": "loadcell",
  "port": "COM4",
  "baud": 115200,
  "unit": "N",
  "parse": {"method": "csv_idx", "idx": 1},
  "calibration": {"a": 1.0, "b": 0.0},
  "sample_rate_hz": 50,
  "duration_s": 10
}
```

### Grid Config (`config/grids/`)

```json
{
  "name": "guitar_top_35pt",
  "units": "mm",
  "origin": "bridge_center",
  "points": [
    {"id": "A1", "x": 0, "y": 0},
    {"id": "A2", "x": 50, "y": 0},
    ...
  ]
}
```

---

## 8. Testing

### Run Tests

```bash
pytest -q tests/                                    # All tests
pytest -q tests/test_wav_io.py                      # WAV I/O tests
pytest -q tests/test_wav_io_roundtrip.py            # Round-trip tolerance
```

### Test Utilities

```python
from tests._util.gen_tone import sine_tone, rms, db

# Generate test signal
x = sine_tone(fs=48000, dur_s=1.0, freq_hz=440.0, amp=0.25)
```

### Fixtures

- `tmp_path` (pytest built-in) — use for temporary WAV files
- Synthetic signals via `sine_tone()` — no hardware needed

---

## 9. CI Workflows

| Workflow | File | Purpose |
|----------|------|---------|
| WAV I/O Guard | `.github/workflows/wav-io-guard.yml` | Fail if direct `wavfile` usage outside canonical module |

### Future CI (recommended)

```yaml
# .github/workflows/test.yml
name: test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.10' }
      - run: pip install -e .[dev]
      - run: pytest -q tests/
```

---

## 10. Measurement Boundary (Non-Negotiable)

### ✅ This Repo Does

- Capture audio (single/multi-channel)
- Compute FFT, peaks, coherence, phase, transfer functions
- Output facts: frequencies, magnitudes, RMS, WSI, MOE
- Store artifacts with SHA-256 provenance

### ❌ This Repo Does NOT

- Recommend design changes
- Score or rank tone quality
- Suggest wood selection or bracing patterns
- Provide optimization advice

See [MEASUREMENT_BOUNDARY.md](MEASUREMENT_BOUNDARY.md) for full policy.

---

## 11. Quick Start for New Features

### Adding a New Measurement Mode

1. Create folder: `modes/<mode_name>/`
2. Add `__init__.py`
3. Implement CLI script with `argparse`
4. Use canonical WAV I/O: `from modes._shared.wav_io import ...`
5. Add Makefile target
6. Add schema to `contracts/` if new artifact type
7. Add tests to `tests/`

### Example: New Mode Skeleton

```python
#!/usr/bin/env python3
"""modes/example/my_mode.py"""
from __future__ import annotations
import argparse
from pathlib import Path
from modes._shared.wav_io import read_wav_mono

def main() -> None:
    ap = argparse.ArgumentParser(description="Example mode")
    ap.add_argument("--wav", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    
    x, meta = read_wav_mono(Path(args.wav))
    # ... process ...
    # ... write output ...

if __name__ == "__main__":
    main()
```

### Makefile Target

```makefile
example-mode:
	python modes/example/my_mode.py --wav $(WAV) --out $(OUT)
```

---

## 12. Key Files Reference

| Purpose | File |
|---------|------|
| **WAV I/O** | `modes/_shared/wav_io.py` |
| **Phase 1 CLI** | `tap_tone/main.py` |
| **Phase 2 Vertical Slice** | `scripts/phase2/phase2_slice.py` |
| **ODS Compute** | `scripts/ods_compute.py` |
| **Coherence** | `scripts/grid_coherence.py` |
| **Wolf Metrics** | `scripts/wolf_metrics.py` |
| **Bending MOE** | `modes/bending_rig/merge_and_moe.py` |
| **Manifest Generator** | `modes/_shared/emit_manifest.py` |
| **Grid Capture** | `scripts/roving_grid_capture.py` |
| **Chladni Peaks** | `modes/chladni/peaks_from_wav.py` |
| **Chladni Index** | `modes/chladni/index_patterns.py` |
| **Loadcell Capture** | `modes/acquisition/loadcell_serial.py` |
| **Dial Indicator** | `modes/acquisition/dial_indicator_serial.py` |

---

## 13. Contact & Ownership

- **Baseline Frozen**: 2025-12-25
- **Owner**: Ross Echols
- **Governance**: Changes to `tap_tone/` require major version increment

---

*Document generated: 2025-12-31*
