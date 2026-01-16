# Acceptance Test Spec: Linked Cursor + WSI Renderer (Wave 6A + 6B.1)

## Scope

Locks the following behaviors:

* Spectrum peak click emits a selection and fills "Selection Details"
* Cursor pill reflects selected frequency and can clear cursor without clearing selection context
* WSI curve renders as a chart (not table), supports cursor + click-to-select
* WSI click sets **freq only** (pointId stays null) and "Selection Details" shows WSI fields
* Viewer passes `selected-freq-hz` as `null` when cursor is cleared (NaN-safe)

## Definitions

* **Selection**: the viewer's current selection object (derived from `onPeakSelected` payload)
* **Cursor**: the linked frequency cursor (the pill + the vertical chart line), keyed by `freq_hz`
* **Spectrum selection**: selection originating from `spectra/points/{PID}/spectrum.csv`
* **WSI selection**: selection originating from `wolf/wsi_curve.csv`

---

## Test Data Requirements (minimal pack)

Evidence ZIP must contain at least:

* `spectra/points/A1/spectrum.csv` (kind: `spectrum_csv`)
* `spectra/points/A1/analysis.json` (kind: `analysis_peaks`) with at least 1 peak `{ freq_hz: number }`
* `wolf/wsi_curve.csv` (kind: `wsi_curve`) with schema columns:
  `freq_hz,wsi,loc,grad,phase_disorder,coh_mean,admissible`
* `audio/points/A1.wav` (kind: `audio_wav`) (for jump verification)

---

## Acceptance Cases

### A1 — Spectrum peak click populates Selection Details and cursor

**Given** the pack is loaded and `spectra/points/A1/spectrum.csv` is previewed
**And** peaks are visible (toggle on by default)
**When** user clicks a peak marker
**Then** "Selection Details" panel shows:

* `source = spectrum`
* `point = A1`
* `freq_hz = <clicked peak freq>`
* `file = spectra/points/A1/spectrum.csv`
* `analysis = spectra/points/A1/analysis.json`
* "Raw selection JSON" exists and is non-empty

**And** the header cursor pill appears showing `<freq> Hz`
**And** Spectrum chart shows a vertical cursor line at that frequency.

Pass/Fail notes:

* Cursor line can be exact `freq_hz` (no snapping requirement).
* `analysis` line must appear for spectrum selection.

---

### A2 — "Open point audio" switches to expected audio relpath

**Given** A1 passed (spectrum selection exists with pointId "A1")
**When** user clicks "▶ Open point audio"
**Then** the active preview switches to relpath `audio/points/A1.wav`
**And** no error toast/message is shown.

**If audio missing** (negative path test):

* The preview does not switch
* The panel shows warning: `Audio missing for point A1: expected audio/points/A1.wav`

---

### A3 — Cursor pill clear removes cursor without clearing selection context

**Given** A1 passed and cursor pill is visible
**When** user clicks the pill "✕" (clear cursor only)
**Then** cursor pill disappears
**And** Spectrum chart cursor line disappears
**And** "Selection Details" still shows:

* `source = spectrum`
* `point = A1`
* `file = spectra/points/A1/spectrum.csv`
  **And** `freq_hz` displays as `—` (or equivalent null display)

**Invariant:** The viewer must pass `selected-freq-hz = null` when cursor is cleared (NaN-safe).

---

### B1 — WSI curve renders as chart with traces + admissible shading toggle

**Given** user previews `wolf/wsi_curve.csv`
**Then** renderer is a chart (canvas) with:

* X axis = `freq_hz`
* Y axis range includes `[0,1]` (or at minimum clamps to 0..1)
* Default visible traces include **WSI** and (if non-zero data exists) **coh_mean** and **phase_disorder**
* "Admissible shading" toggle exists and changes background shading on/off

**And** "Raw rows (first 25)" exists (details block) and is parseable JSON.

---

### B2 — WSI click-to-select sets freq only and updates Selection Details

**Given** WSI chart is visible
**When** user clicks at some frequency on the WSI chart
**Then** selection updates such that:

* `source = wsi`
* `point = —` (null / empty)
* `file = wolf/wsi_curve.csv`
* `analysis` row is absent (no analysis relpath shown for WSI selection)

**And** "WSI row fields" block is visible, showing:

* `wsi`
* `coh_mean`
* `phase_disorder`
* `loc`
* `grad`
* `admissible` (true/false)

**And** "Raw selection JSON" equals the selected row object (or contains it).

---

### B3 — Cursor persists across file switches

**Given** user selects a frequency on WSI (B2) and cursor pill is visible
**When** user switches preview back to Spectrum or Transfer Function (any frequency-domain chart)
**Then** cursor pill remains visible (same frequency)
**And** the chart renders a cursor line at the selected frequency.

(If the renderer does not support cursor yet, it may ignore it—but Spectrum and WSI must show it.)

---

## Non-goals (explicitly out of scope)

* Cross-point peak aggregation
* Wolf scoring / "risk" inference
* Auto-seek audio by frequency
* Any derived "interpretation" logic beyond displaying exported fields

---

## Optional "Guardrail" Review Checklist (human, 30 seconds)

* Selection state contains **only**: pointId? freqHz? source? raw evidence? relpaths?
  (No computed "score", "risk", "rank", etc.)
* Any shading uses exporter-provided `admissible` field only.
