# Tap Tone Pi — AI Coding Agent Instructions

## Mission (Non-Negotiable)
**Acoustic measurement instrument** — outputs facts (peaks, coherence, phase, RMS), NOT design advice.
- ✅ FFT spectra, ODS transfer functions, Wolf Stress Index (WSI), MOE/EI values
- ❌ NO tone scoring, voicing recommendations, or optimization suggestions

> **Doctrine:** The analyzer exports evidence and derivations. It does not export conclusions.
> Any file that can influence a human to remove wood must be treated as advisory (Wave 7) and is out-of-scope.

**The analyzer produces stable, explicit, self-describing measurements. Interpretation is a human act.**

## CI Boundary — Will Fail Build
```bash
python ci/check_boundary_imports.py --preset analyzer  # Runs in CI
```
**Forbidden imports:** `app.*`, `services.*`, `packages.*` (Luthier's ToolBox namespaces)  
**Pass data via artifacts** (JSON/CSV/WAV + manifests), never Python imports.

## Architecture
```
tap_tone/            # Phase 1 CLI (frozen v1.0) — single-channel tap tone
scripts/phase2/      # Phase 2 package — 2-channel ODS, coherence, wolf metrics
  dsp.py             #   TFResult dataclass, compute_transfer_and_coherence()
  metrics.py         #   WSI curve computation
  export_viewer_pack_v1.py  # Evidence ZIP export
modes/               # Specialized measurement modes
  _shared/           #   wav_io.py (ONLY WAV I/O), emit_manifest.py
  bending_rig/       #   MOE from load+displacement
  chladni/           #   Pattern frequency indexing
  acquisition/       #   Serial sensor capture + simulators
contracts/           # Schema registry + *.schema.json output contracts
tap_tone/viewer_pack/ # Shared helpers for ZIP export/validate/diff
```
**Two packages:** `tap_tone/` is stable; `tap-tone-lab/` is experimental. Know which you're editing.

## Commands
```bash
pip install -e .                                    # Install
make test                                           # pytest suite
make test-wav-io                                    # WAV I/O roundtrip tests
python scripts/phase2_slice.py run --synthetic \    # Validate without hardware
  --grid examples/phase2_grid_mm.json --out ./runs_phase2
make help                                           # All Makefile targets

# Viewer Pack validation and comparison
python scripts/viewer_pack_validate.py pack.zip    # Validate ZIP integrity
python scripts/viewer_pack_diff.py pre.zip post.zip --out diff/  # Compare packs
```

## Code Patterns (Enforced)

### Pure DSP Functions — No I/O in Analysis
```python
# tap_tone/analysis.py — returns frozen dataclass, never writes files
def analyze_tap(audio: np.ndarray, sample_rate: int, **params) -> AnalysisResult: ...
# scripts/phase2/dsp.py — same pattern for transfer functions
def compute_transfer_and_coherence(x_ref, x_rov, fs, ...) -> TFResult: ...
```
All file writes go through `storage.py` or `modes/_shared/emit_manifest.py`.

### WAV I/O — Single Source of Truth
```python
from modes._shared.wav_io import read_wav_mono, read_wav_2ch, write_wav_mono, write_wav_2ch
# Readers: float32 [-1, 1] | Writers: accept float32, emit int16 PCM
```
**NEVER** use `scipy.io.wavfile` directly elsewhere — causes int16↔float drift.

### Frozen Dataclasses for Results
```python
@dataclass(frozen=True)
class TFResult:  # scripts/phase2/dsp.py
    freq_hz: np.ndarray
    H_mag: np.ndarray
    H_phase_deg: np.ndarray
    coherence: np.ndarray
```
Always return full spectrum arrays for downstream reprocessing.

### Provenance Tracking
DSP modules expose `get_dsp_provenance()` returning algo version + numpy/scipy versions.
Manifests include SHA-256 hashes via `modes/_shared/emit_manifest.py`.

## Evidence Pack Contract (viewer_pack_v1)
Exports must be **deterministic**: identical inputs → identical column headers, frequency bins, admissibility.

**Per-point artifacts** (`spectra/points/{POINT_ID}/`):
- `spectrum.csv` — columns: `freq_hz,H_mag,coherence,phase_deg` (monotonic bins)
- `analysis.json` — peaks as annotations, not judgments (no "strongest"/"worst")
- `audio.wav` — exact recording that produced the spectrum

**Session-level artifacts** (`wolf/`):
- `wsi_curve.csv` — columns: `freq_hz,wsi,loc,grad,phase_disorder,coh_mean,admissible`
- `wolf_candidates.json` — explicit thresholds, contributing points, no quality language

See [docs/TAP_TONE_PI_SANDBOX_HANDOFF.md](../docs/TAP_TONE_PI_SANDBOX_HANDOFF.md) for full contract.

## Artifact Outputs
Phase 2 sessions produce (`runs_phase2/session_*/`):
- `points/point_*/audio.wav` — 2-channel (ch0=reference, ch1=roving)
- `derived/ods_snapshot.json` — transfer function per point  
- `derived/wolf_candidates.json` — WSI candidates

**Schema validation:** All outputs validated against `contracts/*.schema.json`.  
**Registry:** `contracts/schema_registry.json` — bump version on schema changes.

## When Adding Features
1. **DSP:** Pure functions → frozen dataclass output → test with synthetic sine bursts
2. **New output field:** Update schema in `contracts/`, bump `schema_registry.json` version
3. **Multi-channel:** Requires shared-clock interface (not independent USB mics)
4. **Breaking change:** Document in `docs/ADR-*.md`
5. **Hardware-free validation:** Add `--synthetic` path (see `phase2_slice.py`)
6. **Evidence export:** No ranking, no "good/bad", no implicit thresholds

## Common Mistakes (Will Break Contract)

### CSV Integrity
- ❌ Changing header names/case after release
- ❌ Per-point bins that differ from session bins
- ❌ Omitting rows — use `NaN` for unknown values
- ❌ Locale decimals (`,` as decimal separator) — always use `.`

### Frequency Bin Discipline
- ❌ Varying FFT size/window across points in same session
- ❌ Silent resampling — if resampled, declare in provenance
- ❌ Snapping peaks to interpolated values without storing `bin_index`

### Provenance
- ❌ Missing `algo_id`/`algo_version` in provenance
- ❌ OS-specific absolute paths in exported metadata
- ❌ Conflating capture provenance with algorithm provenance

### Measurement-Only Language
- ❌ Labels: "strongest", "worst", "dominant", "primary"
- ❌ Notes: "good", "bad", "optimal", "problem", "wolf"
- ❌ Prescriptions: "fix", "thin", "stiffen", "remove"

### Packaging
- ❌ Files in ZIP not listed in `viewer_pack.json.files[]`
- ❌ Folder semantics without manifest
- ❌ Changing relpaths without schema version bump

## Wave 7 Boundary Violations (Forbidden)

These outputs belong in **Wave 7+ advisory** — never in the analyzer:

### Interpretation Creep
- ✅ Allow: "candidate frequency", "inadmissible due to low coherence"
- ❌ Forbid: "problem frequency", "wolf likely", "bad region"

### Comparative Scoring
- ❌ Any "score" implying quality
- ✅ If ordering needed: use `magnitude_rank` defined as sorting only

### Implied Prescriptions
- ❌ "thin here", "remove mass", "stiffen brace"
- ❌ "A0 too high", "top too stiff"

### Mode Labeling
- ❌ Automatic "A0 / T(1,1) / B1" without validated method + uncertainty
- ✅ Only: "peak_1", "peak_2", or operator-entered `user_label`

### Silent Processing
- ❌ Silent filtering, smoothing, peak "cleanup", auto-repair
- ✅ If processed: export raw + derived separately, label as `derived`

## Key References
- [docs/TAP_TONE_PI_SANDBOX_HANDOFF.md](../docs/TAP_TONE_PI_SANDBOX_HANDOFF.md) — Evidence contract
- [docs/contracts/EVIDENCE_PACK_CONTRACT_v1.md](../docs/contracts/EVIDENCE_PACK_CONTRACT_v1.md) — Full column specs
- [docs/MEASUREMENT_BOUNDARY.md](../docs/MEASUREMENT_BOUNDARY.md) — Scope policy
- [docs/MEASUREMENT_README.md](../docs/MEASUREMENT_README.md) — Bending rig quickstart
- [DEV_HANDOFF.md](../DEV_HANDOFF.md) — Architecture overview
- [contracts/schema_registry.json](../contracts/schema_registry.json) — Schema versions
