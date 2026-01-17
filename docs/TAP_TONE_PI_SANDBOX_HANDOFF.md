# Tap-Tone-Pi Sandbox → Evidence Viewer

## Analyzer-Side Pipeline Handoff

**Audience:** tap-tone-pi developers, lab engineers, signal analysts  
**Scope:** finishing and validating the analyzer → evidence-pack pipeline  
**Out of Scope:** UI interpretation, scoring, diagnostics (Wave 7+)  
**Last Updated:** 2026-01-16

---

## 1. Purpose of the Sandbox

The tap-tone-pi sandbox exists to answer one question:

> *Can a real physical measurement session be exported as a stable, self-describing evidence pack that downstream tools can visualize without inventing meaning?*

The Viewer assumes:

* measurements are **already complete**
* semantics are **already encoded**
* nothing downstream "fixes" or "infers" missing intent

If the sandbox exports ambiguous, unstable, or under-specified artifacts, the Viewer **cannot** compensate without crossing into interpretation.

---

## 2. End-to-End Pipeline Overview

```
Physical Tap
  ↓
Raw Audio Capture
  ↓
FFT / Transfer Function / Coherence
  ↓
Per-Point Artifacts
  - spectrum.csv
  - analysis.json (peaks)
  - audio.wav
  ↓
Session-Level Artifacts
  - wolf/wsi_curve.csv
  - provenance.json
  - session_meta.json
  ↓
Evidence ZIP (viewer_pack_v1)
```

The sandbox is responsible for **everything above the ZIP boundary**.

---

## 3. Evidence Contract (What the Viewer Trusts)

### 3.1 Determinism Is Mandatory

For identical inputs:

* same tap location
* same excitation
* same capture settings

The sandbox **must** produce:

* identical column headers
* stable frequency bins
* stable peak detection behavior
* stable `admissible` classification

Non-determinism upstream creates *false analytical affordances* downstream.

---

## 4. Per-Point Artifacts (Critical)

### 4.1 `spectra/points/{POINT_ID}/spectrum.csv`

**Role:** authoritative frequency-domain measurement for a single tap point.

**Required columns (case-insensitive):**

```
freq_hz
H_mag
coherence
phase_deg
```

**Rules**

* `freq_hz` must be numeric, monotonically increasing
* bin spacing must be consistent across points
* no smoothing or interpolation that is not documented
* missing coherence must be explicit (0 or NaN, not omitted)

**Viewer Assumption**

> Each row is a measurement, not an interpretation.

---

### 4.2 `spectra/points/{POINT_ID}/analysis.json`

**Role:** per-point annotations **derived from the spectrum**, not judgments.

**Canonical structure**

```json
{
  "peaks": [
    {
      "freq_hz": 187.5,
      "label": "Mode 1"
    }
  ]
}
```

**Rules**

* Peaks must be traceable to spectrum bins
* No ranking ("strongest", "worst", etc.)
* Labels are optional and informational only
* No cross-point reasoning

**Viewer Assumption**

> Peaks are *annotations*, not conclusions.

---

### 4.3 `audio/points/{POINT_ID}.wav`

**Role:** provenance and audit trail.

**Rules**

* Must correspond to the same tap that generated the spectrum
* No trimming or enhancement after FFT unless documented
* If missing, Viewer will warn but not compensate

---

## 5. Session-Level Artifacts (WSI Pipeline)

### 5.1 `wolf/wsi_curve.csv`

**Role:** global, session-level measurement derived from all points.

**Canonical header (MUST MATCH EXACTLY):**

```
freq_hz,wsi,loc,grad,phase_disorder,coh_mean,admissible
```

**Column semantics**

| Column | Description |
|--------|-------------|
| `freq_hz` | frequency bin (must align with spectra bins) |
| `wsi` | Wolf Stress Index (0–1, normalized upstream) |
| `coh_mean` | mean coherence across all points |
| `phase_disorder` | exported metric, not computed downstream |
| `loc`, `grad` | exporter-defined metrics (document units) |
| `admissible` | boolean classification **from analyzer**, not viewer |

**Rules**

* `admissible` is the *only* place classification appears in Wave 6
* Viewer will shade, not interpret
* No thresholds encoded implicitly (e.g., "wsi > 0.4" without field)

**Viewer Assumption**

> WSI is an exported measurement, not a recommendation.

---

## 6. Provenance & Metadata

### 6.1 `provenance.json`

Must answer:

* how data was captured
* tool versions
* FFT parameters
* windowing
* calibration assumptions

This file protects the system from **post-hoc reinterpretation**.

---

### 6.2 `session_meta.json`

Should include:

* instrument ID
* operator (if appropriate)
* environment notes
* grid definition (points used)

The Viewer surfaces this verbatim.

---

## 7. Evidence Pack Assembly Rules

When assembling the ZIP:

* Paths matter (Viewer logic depends on them)
* Kinds in the manifest must match file role
* Sibling resolution relies on:

  ```
  spectra/points/{PID}/spectrum.csv
  spectra/points/{PID}/analysis.json
  ```

**No auto-repair downstream.**
If the pack is malformed, the Viewer will surface errors.

---

## 8. Sandbox Validation Checklist (Before Lab Use)

Before running lab sessions, the analyzer team should verify:

### Determinism

- [ ] Repeated runs produce identical CSV headers
- [ ] Peak frequencies stable within expected variance
- [ ] `admissible` classification stable

### Alignment

- [ ] All spectra share identical frequency bins
- [ ] WSI bins align exactly with spectra bins

### Completeness

- [ ] Every point with a spectrum has audio
- [ ] Every spectrum has an analysis.json (even if empty)
- [ ] Session-level files present when expected

---

## 9. What the Sandbox Must NOT Do (Wave Boundary)

The analyzer must **not**:

* encode "good/bad" language
* rank frequencies or points
* compute "wolf likelihood"
* aggregate peaks into conclusions
* hide thresholds inside undocumented metrics

Those belong in **Wave 7+ interpretation**, not here.

---

## 10. Definition of "Pipeline Complete"

The pipeline is complete when:

> A lab operator can produce an evidence ZIP that a downstream analyst can explore, correlate, and question — **without the tool telling them what to think**.

At that point:

* the analyzer has done its job
* the Viewer has done its job
* interpretation remains a *human act*

---

## 11. Handoff Summary (One Sentence)

**tap-tone-pi sandbox is responsible for producing stable, explicit, self-describing measurements; the Viewer is responsible for showing them faithfully — nothing more, nothing less.**

---

## 12. Cross-Repository Boundary

This document describes artifacts that flow **from** the `tap_tone_pi` repository **to** the `luthiers-toolbox` Viewer.

Per [BOUNDARY_RULES.md](./BOUNDARY_RULES.md):

* ToolBox **interprets** and **visualizes** — never **measures**
* Analyzer **measures** and **exports** — never **judges**
* Integration is via **artifact contract** (ZIP), not Python imports

```
tap_tone_pi                    luthiers-toolbox
───────────                    ────────────────
capture → FFT → export  ──ZIP──>  ingest → view → explore
                                      ↑
                            No code dependency
```

---

## See Also

- [BOUNDARY_RULES.md](./BOUNDARY_RULES.md) — Cross-repo import boundaries
- [../FENCE_REGISTRY.json](../FENCE_REGISTRY.json) — `external_boundary` profile
- [Runs_Advisory_Integration/README.md](./Runs_Advisory_Integration/README.md) — RMOS integration patterns
