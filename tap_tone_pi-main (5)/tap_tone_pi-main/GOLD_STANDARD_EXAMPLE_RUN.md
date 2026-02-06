# GOLD_STANDARD_EXAMPLE_RUN — tap-tone-pi

## Purpose

This document defines a **single canonical example run** that demonstrates the instrument end-to-end:

**capture → verify → export → validate → re-open**

This is not a benchmark for "tone." It is a **proof-of-instrument** dataset specification.

---

## What This Example Proves

A successful Gold Standard run proves:

* The audio device is configured correctly
* The capture pipeline produces a clean impulse response
* The FFT/spectrum output is stable and interpretable
* Peaks are aligned to the spectrum frequency grid
* Export produces a valid `viewer_pack_v1`
* Validation gate passes (`validation_report.json: passed=true`)
* The exported pack can be re-opened and inspected reliably

---

## Recommended Specimen

Choose a specimen that is easy to excite and repeat:

### Preferred

* **Flat wooden plate**

  * ~3–6 mm thickness
  * ~150–250 mm width
  * any tonewood or plywood is fine
* OR **small rigid panel** (acrylic, aluminum)

### Avoid (for this Gold Standard)

* Fully assembled instruments (too many uncontrolled variables)
* Very soft/foam materials
* Objects that rattle or buzz

---

## Geometry and Setup (Must Be Repeatable)

**Support method**

* Two soft foam blocks under the plate near the lower corners
* Plate should be free to vibrate, not clamped hard

**Microphone**

* Distance: **20 cm**
* Angle: aimed roughly at center area
* Position: do not move between runs

**Impulse location**

* Tap at ~**30% of width** from one edge (pick one location and keep it)
* Avoid tapping directly above foam supports

---

## Environment Requirements

* Quiet room
* No HVAC blast / fans pointed at specimen
* Minimize desk vibration
* No clipping / no AGC / no "enhancements"

---

## Run Configuration (Use Defaults)

Use the instrument defaults for a first gold run. The goal is not optimization—only repeatability.

Record these fields in your session metadata (or notes):

* specimen_id: `gold_plate_A1` (or similar)
* mic_model (optional)
* interface name
* sample_rate
* FFT params (whatever defaults are)

---

## What the Data Should Look Like

### Time domain (impulse response)

A good capture shows:

* One sharp impulse spike
* Clean decay tail
* No "double-hit"
* No flat tops (clipping)

### Spectrum

A good spectrum shows:

* One or more prominent peaks
* Peaks are stable across 3 taps
* No chaotic broadband noise dominating

**Stability target (practical)**

* Dominant peak frequency should vary by **≤ 1–2 bins** across taps (depending on FFT resolution)

---

## Procedure (Gold Standard Run Steps)

### Step 1 — Dry tap verification

1. Start the instrument
2. Do one test tap
3. Adjust input gain until:

   * impulse is strong
   * no clipping

### Step 2 — Capture 3 taps (same specimen, same geometry)

Capture **three** clean taps as separate points (or separate runs, depending on workflow). Aim for repeatability.

Label them:

* `A1`
* `A2`
* `A3`

### Step 3 — Quick sanity checks (before export)

For each point:

* spectrum exists
* analysis json exists (even if peaks list is empty)
* audio exists if you require it (or warnings are understood)

### Step 4 — Export viewer pack

Export the viewer pack ZIP (Phase 2 export).

Expected outcomes:

* `validation_report.json` written at pack root
* `validation_report.json.passed == true`
* ZIP contains `viewer_pack.json` at root

### Step 5 — Re-open the ZIP

Open the exported ZIP in your Viewer pipeline.

Verify:

* manifest loads
* all points show spectra
* peaks load and align
* no missing file errors

---

## "Pass/Fail" Criteria (Hard)

This run is considered **Gold Standard PASS** only if:

* Export completed without error
* `validation_report.json` exists in the ZIP root
* `validation_report.json: passed == true`
* Viewer loads the ZIP and displays spectra for all points
* No missing manifest or missing spectrum errors

---

## Expected ZIP Contents (Minimum)

A valid minimal gold pack includes:

* `viewer_pack.json`
* `validation_report.json`
* `spectra/points/A1/spectrum.csv`
* `spectra/points/A1/analysis.json`
* `spectra/points/A2/...`
* `spectra/points/A3/...`
* (optional) `audio/points/A1.wav`, etc., depending on your policy
* (optional) `wolf/wsi_curve.csv` if present in your configuration

---

## What to Save as a Permanent Reference

After a PASS, archive the ZIP as your canonical example:

Suggested name:

```
gold_standard_viewer_pack_v1_<YYYY-MM-DD>.zip
```

Store it somewhere stable (and ideally in ToolBox as an ingested artifact) so you can use it for:

* regressions
* demos
* onboarding
* hardware sanity checks

---

## Troubleshooting (Fast)

If validation fails, open `validation_report.json` and fix the first error. Common fixes:

| Error | Fix |
|-------|-----|
| Missing `viewer_pack.json` | Export stage wrote wrong filename |
| `S-006` spectrum grid mismatch | Inconsistent FFT params across points |
| `P-003` peak not on grid | Analysis using different freq list than spectrum |
| `W-001` missing WSI column | Wrong CSV header |
| `W-003` WSI freq mismatch | WSI curve generated on different grid |

---

## Reference from FIRST_MEASUREMENT_CHECKLIST

After completing the First Measurement Checklist, use this Gold Standard run as your:

* "instrument confidence" proof
* demo pack
* regression pack

---

## Related Documents

* [FIRST_MEASUREMENT_CHECKLIST.md](FIRST_MEASUREMENT_CHECKLIST.md) — Step-by-step operator checklist
* [QUICKSTART.md](QUICKSTART.md) — 5-minute first measurement
* [INSTRUMENT_SCOPE.md](INSTRUMENT_SCOPE.md) — What this instrument does and does not claim
* [examples/reference/](examples/reference/) — Before/after comparison example

---

### Version

Gold Standard Example Run v1.0
