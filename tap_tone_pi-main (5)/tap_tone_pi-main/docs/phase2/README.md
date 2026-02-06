# Phase 2 — Roving Grid ODS + Coherence + Wolf Metrics (Measurement-Only)

Phase 2 extends tap-tone into **spatial measurement** on a guitar plate/top using:
- a reproducible excitation (recommended: speaker-air drive or controlled impulse)
- one fixed **reference** sensor/mic
- one roving sensor/mic moved point-to-point on a defined grid

This phase produces **objective measurements**:
- transfer function magnitude/phase (ODS snapshot)
- coherence (measurement quality)
- WSI (wolf suspicion index) as a heuristic **localization/instability indicator**

> **Boundary:** Phase 2 does not claim "tone quality," does not prescribe brace thinning, and does not
> infer structural remedies. It only produces measurements and heuristics. See `MEASUREMENT_BOUNDARY.md`.

---

## Canonical implementation

- CLI: `scripts/phase2_slice.py`
- Package: `scripts/phase2/`
- Canonical grid: `config/grids/guitar_top_35pt.json`

---

## Running Phase 2

**Supported method** (avoids PYTHONPATH issues):

```bash
# Synthetic validation run (no hardware)
python tools/run_phase2.py run --grid examples/phase2_grid_mm.json --out ./runs_phase2 --synthetic

# List audio devices
python tools/run_phase2.py devices

# Hardware capture
python tools/run_phase2.py run --grid config/grids/guitar_top_35pt.json --out ./runs_phase2 --device 1
```

> **Note:** Direct invocation of `scripts/phase2_slice.py` requires `PYTHONPATH` to include the project root.
> Use `tools/run_phase2.py` until the package is properly installable.

---

Legacy scripts exist but are superseded:
- `scripts/roving_grid_capture.py`
- `scripts/ods_compute.py`
- `scripts/grid_coherence.py`
- `scripts/wolf_metrics.py`

---

## Inputs

### Grid definition (`grid.json`)
A grid is a set of points with:
- `point_id` (ex: "A1")
- `x_mm`, `y_mm` coordinates
- optional labels/roles

Canonical example:
- `config/grids/guitar_top_35pt.json` (5×7, 35 points)

### Capture configuration
Per point, store `capture_meta.json` containing:
- device index/name if available
- sample rate
- channels (must be 2)
- seconds (record window length)
- channel roles (reference vs roving)
- operator/session notes (optional)

---

## Output structure (CAPDIR)

A single Phase 2 run is one CAPDIR:
`runs_phase2/session_YYYYMMDDTHHMMSSZ/`

Expected top-level:
- `grid.json` — the grid used (copied into run)
- `metadata.json` — run/session metadata
- `points/` — per-point evidence
- `derived/` — computed outputs
- `plots/` — generated visuals

Per-point folder: `points/point_<ID>/`
- `audio.wav` — 2-channel evidence (ch0 ref, ch1 roving)
- `capture_meta.json` — capture parameters/provenance
- `analysis.json` — FFT peaks summary (per channel)
- `spectrum.csv` — spectrum data for quick plotting

Derived artifacts:
- `derived/ods_snapshot.json` — transfer function snapshot(s)
- `derived/wolf_candidates.json` — WSI candidates (and quality gating in later hardening)
- `derived/wsi_curve.csv` — WSI vs frequency curve

---

## Recommended workflow

### 1) Capture
```bash
python scripts/phase2_slice.py capture \
  --device 1 \
  --grid config/grids/guitar_top_35pt.json \
  --out runs_phase2
```

### 2) Analyze (ODS/coherence/WSI)

```bash
python scripts/phase2_slice.py analyze \
  --capdir runs_phase2/session_20251231T095631Z \
  --freqs 100,150,185,220,280
```

### 3) Inspect outputs

* Start with `plots/*.png` to see coarse structure
* Check `derived/wolf_candidates.json` for candidate regions/frequencies
* Use coherence outputs (when present) as **quality gates** for admissibility

---

## Measurement quality (coherence)

Coherence γ²(f) is treated as **admissibility**:

* high coherence ⇒ the transfer function is trustworthy at that frequency
* low coherence ⇒ measurement is contaminated (noise, nonlinearity, poor coupling, reflections)

Phase 2 should **never** "promote" a candidate based on low-quality data.

---

## Non-goals (Phase 2)

Phase 2 explicitly does not:

* assign mode names (A0, T(0,0), etc.) as ground truth
* claim causation between WSI and wolf notes
* prescribe structural edits
* embed ToolBox/RMOS behavior or endpoints

That interpretive layer, if desired, belongs to **Phase 3 (optional, advisory-only)**.

---

## Contracts / schemas

Machine-readable schemas for Phase 2 JSON outputs live in:

* `contracts/phase2_*.schema.json`

Use them to validate run outputs in CI and during development.
