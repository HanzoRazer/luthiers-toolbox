# Appendix A — Analyzer Failure Modes → Viewer Symptoms

**Purpose:**
Help sandbox / analyzer developers quickly identify whether an observed Viewer issue is:

* a Viewer bug (rare at this stage), or
* an upstream analyzer/export problem (more common in lab conditions).

This appendix assumes the Viewer is operating in **Wave 6A / 6B.1 measurement-only mode**.

**Last Updated:** 2026-01-16

---

## A.1 Frequency & Spectrum Issues

### FM-01: Inconsistent frequency bins across points

**Analyzer mistake**

* FFT binning differs per point (window length, zero padding, sample rate drift).

**Viewer symptom**

* Cursor aligns in Spectrum for one point but appears "between bins" or off-grid in another.
* WSI cursor line does not visually line up with Spectrum peaks.

**What to check upstream**

* FFT parameters identical across all points.
* `freq_hz` arrays are bit-identical across all `spectrum.csv` files.

---

### FM-02: Non-monotonic or duplicated `freq_hz`

**Analyzer mistake**

* CSV rows out of order or duplicated frequencies.

**Viewer symptom**

* Chart renders strangely (zig-zag or folded look).
* Tooltips show unexpected frequency jumps.

**What to check upstream**

* Ensure `freq_hz` is strictly increasing.
* Sort rows before export.

---

### FM-03: Implicit smoothing or undocumented interpolation

**Analyzer mistake**

* Spectrum is smoothed or interpolated without recording parameters.

**Viewer symptom**

* Peaks appear broader or shifted relative to expectations.
* Users report "this looks different from raw FFT."

**What to check upstream**

* Confirm whether smoothing is applied.
* Document it explicitly in `provenance.json`.

---

## A.2 Peak Annotation Issues (`analysis.json`)

### FM-04: Peaks not aligned to spectrum bins

**Analyzer mistake**

* Peak detection returns interpolated frequencies not present in `spectrum.csv`.

**Viewer symptom**

* Peak markers appear slightly offset from visible magnitude maxima.
* Cursor snap feels "off."

**What to check upstream**

* Ensure peak `freq_hz` corresponds to an actual spectrum bin or is clearly documented as interpolated.

---

### FM-05: Missing or empty `analysis.json`

**Analyzer mistake**

* Peak file omitted for a point, or empty file written incorrectly.

**Viewer symptom**

* Spectrum renders, but "Peaks" toggle is missing or shows zero peaks.
* Selection Details lacks `analysis` relpath.

**What to check upstream**

* Always emit `analysis.json`, even if `{ "peaks": [] }`.

---

### FM-06: Semantic labels implying interpretation

**Analyzer mistake**

* Peak labels like `"problem mode"` or `"wolf frequency"`.

**Viewer symptom**

* Users assume the Viewer is diagnosing issues.
* Governance violation risk.

**What to check upstream**

* Labels must be neutral (e.g., "Mode 1", "Peak A").
* Interpretation belongs in Wave 7+, not exporter labels.

---

## A.3 WSI Curve Issues

### FM-07: WSI frequency bins do not match spectra bins

**Analyzer mistake**

* WSI computed on a different frequency grid.

**Viewer symptom**

* Cursor aligns in WSI but not in Spectrum (or vice versa).
* Nearest-sample marker jumps unexpectedly.

**What to check upstream**

* WSI `freq_hz` must align exactly with spectra bins.

---

### FM-08: `admissible` field unstable across runs

**Analyzer mistake**

* Classification depends on non-deterministic inputs or thresholds not fixed.

**Viewer symptom**

* Admissible shading changes between identical lab runs.
* Users distrust the visualization.

**What to check upstream**

* Make `admissible` deterministic for identical inputs.
* Record thresholds in `provenance.json`.

---

### FM-09: Hidden thresholds baked into WSI

**Analyzer mistake**

* WSI values clipped, scaled, or thresholded without documentation.

**Viewer symptom**

* Users infer "good/bad" behavior even though Viewer doesn't label it.
* Hard-to-explain WSI plateaus or cliffs.

**What to check upstream**

* Export raw metrics and normalization rules.
* Avoid encoding judgment invisibly.

---

## A.4 Audio Provenance Issues

### FM-10: Audio not corresponding to analyzed tap

**Analyzer mistake**

* Audio file trimmed, normalized, or replaced after FFT.

**Viewer symptom**

* Listening to audio does not "match" the spectrum intuitively.
* Analysts question measurement integrity.

**What to check upstream**

* Ensure FFT and audio come from the same raw capture.
* Document any preprocessing.

---

### FM-11: Missing audio files

**Analyzer mistake**

* Audio omitted for some points.

**Viewer symptom**

* "Open point audio" shows warning.
* No crash, but user confusion.

**What to check upstream**

* Ensure audio export is consistent.
* If audio is optional, document that expectation.

---

## A.5 Evidence Pack Assembly Issues

### FM-12: Incorrect relpaths

**Analyzer mistake**

* Files placed in unexpected directories.

**Viewer symptom**

* Sibling resolution fails (no peaks shown).
* Files appear in Viewer but don't "connect."

**What to check upstream**

* Paths must follow:

  ```
  spectra/points/{PID}/spectrum.csv
  spectra/points/{PID}/analysis.json
  audio/points/{PID}.wav
  wolf/wsi_curve.csv
  ```

---

### FM-13: Kind mismatch in manifest

**Analyzer mistake**

* Manifest kind does not match file content.

**Viewer symptom**

* Wrong renderer used (CSV table instead of chart, etc.).

**What to check upstream**

* Ensure manifest `kind` matches schema expectations exactly.

---

## A.6 Human-Factor Failure Modes (Most Important)

### FM-14: Users believe the Viewer is "judging"

**Analyzer contribution**

* Upstream artifacts contain implicit conclusions or loaded terminology.

**Viewer symptom**

* Users ask: "Is this bad?" "Is this the wolf frequency?"

**What to check upstream**

* Remove judgmental language.
* Keep exporter outputs descriptive, not prescriptive.

---

### FM-15: Users expect recommendations

**Analyzer contribution**

* Exporter previously provided diagnostic output in other tools.

**Viewer symptom**

* Users search for "answers" instead of exploring data.

**What to check upstream**

* This is a signal for **Wave 7 design**, not a Viewer or analyzer bug.
* Capture these questions as lab feedback.

---

## A.7 Key Diagnostic Principle

> **If the Viewer looks confusing, ask first: "Is the evidence ambiguous?"**

The Viewer is intentionally dumb:

* it does not infer
* it does not correct
* it does not explain

When something looks wrong, the answer is almost always **upstream**.

---

## A.8 When to Escalate

Escalate to Viewer changes **only if**:

* Raw CSV/JSON is correct
* Frequency grids align
* Provenance is documented
* Symptoms persist across multiple packs

Otherwise, fix the analyzer.

---

## A.9 Quick Reference Table

| Code | Category | Analyzer Mistake | Viewer Symptom |
|------|----------|------------------|----------------|
| FM-01 | Spectrum | Inconsistent FFT bins | Cursor misalignment |
| FM-02 | Spectrum | Non-monotonic freq_hz | Zig-zag chart |
| FM-03 | Spectrum | Undocumented smoothing | Shifted peaks |
| FM-04 | Peaks | Peaks off-grid | Markers offset |
| FM-05 | Peaks | Missing analysis.json | No peaks toggle |
| FM-06 | Peaks | Judgmental labels | User confusion |
| FM-07 | WSI | Bin mismatch | Cursor jumps |
| FM-08 | WSI | Unstable admissible | Shading changes |
| FM-09 | WSI | Hidden thresholds | Unexplained cliffs |
| FM-10 | Audio | Wrong audio file | Spectrum/audio mismatch |
| FM-11 | Audio | Missing audio | Warning shown |
| FM-12 | Assembly | Wrong paths | Sibling resolution fails |
| FM-13 | Assembly | Kind mismatch | Wrong renderer |
| FM-14 | Human | Loaded terminology | "Is this bad?" questions |
| FM-15 | Human | Expectation mismatch | Users want answers |

---

## Final Reminder

This appendix is not a bug list.
It is a **map of responsibility**.

If the analyzer exports clean, explicit, deterministic evidence,
the Viewer will tell the truth — and nothing more.

---

## See Also

- [TAP_TONE_PI_SANDBOX_HANDOFF.md](./TAP_TONE_PI_SANDBOX_HANDOFF.md) — Main handoff document
- [BOUNDARY_RULES.md](./BOUNDARY_RULES.md) — Cross-repo import boundaries
