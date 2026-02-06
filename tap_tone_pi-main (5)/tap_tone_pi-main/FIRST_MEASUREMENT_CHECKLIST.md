# tap-tone-pi — First Measurement Checklist

**Goal:** Obtain one clean, valid, repeatable acoustic measurement and export it successfully.

This checklist defines the minimum path to success. If you can complete every step on this page, the instrument is working correctly.

---

## 0. What "Success" Looks Like (Read This First)

A successful first measurement means:

- You capture a clean impulse response
- A stable resonant peak is visible in the spectrum
- A run completes without errors
- A viewer pack exports and passes validation
- You can reload and inspect the measurement later

You are **not** trying to optimize tone, judge quality, or compare instruments yet.

---

## 1. Physical Setup (Before Powering On)

### Specimen

- Choose a simple, rigid specimen (flat plate preferred)
- Avoid fully assembled instruments for the first run
- Ensure the specimen is:
  - dry
  - not clamped rigidly unless intentionally testing boundary conditions
  - free to vibrate

### Support

- Support the specimen lightly:
  - foam blocks, elastic cord, or fingertips at nodal regions
- Avoid hard contact surfaces

### Excitation Tool

- Use a small, hard impulse source:
  - light wooden dowel
  - small plastic hammer
- Avoid fingernails or soft mallets

---

## 2. Microphone & Audio Interface

### Microphone

- Any decent condenser mic is sufficient
- No calibration required for relative measurement
- Place mic:
  - 10–30 cm from specimen
  - aimed consistently across runs
  - not touching the specimen

### Audio Interface

- Confirm the OS sees the device
- Disable:
  - automatic gain control
  - noise suppression
  - "enhancement" features
- Set sample rate consistently (e.g. 44.1 kHz or 48 kHz)

---

## 3. Environment Check

- Perform measurement in a quiet space
- Avoid:
  - HVAC noise
  - conversations
  - desk vibrations
- Ambient noise should be at least 20 dB below the impulse peak

If in doubt: do a test tap and look at the waveform.

---

## 4. Launch the Instrument

From the repo root:

```bash
python -m tap_tone.main --list-devices
```

Confirm:

- No import errors
- Audio devices are listed
- Default parameters load

**If the instrument does not start cleanly, stop here and fix that first.**

---

## 5. Configure the Measurement Session

### Session Metadata

- Assign a clear session name
- Use a simple specimen ID (e.g. `plate_A1`)
- Do not over-annotate yet

### FFT Parameters

- Use defaults for first run
- Do not change:
  - windowing
  - bin size
  - overlap
- Consistency matters more than optimization

---

## 6. Perform a Test Tap (Dry Run)

Before recording:

1. Tap the specimen once
2. Observe:
   - waveform spike
   - decay tail
   - no clipping

**Good sign:**
- Single sharp impulse
- Clean decay
- No flat-topped waveform

**Bad sign:**
- Clipping
- Double taps
- Long noise tail

Adjust input gain if needed.

---

## 7. Capture the Measurement

When ready:

1. Start capture
2. Tap once with a firm, repeatable strike
3. Wait for capture to complete
4. Do not touch the specimen during decay

Repeat if necessary until you get:

- One clean impulse
- Stable spectrum

---

## 8. Inspect the Spectrum (Immediate Feedback)

After capture, verify:

- A clear magnitude spectrum appears
- At least one dominant peak is visible
- Peak frequency is stable across repeat taps

You are not judging "good" or "bad" — only **repeatability**.

---

## 9. Complete the Run

- End the session cleanly
- Ensure no warnings indicate corrupted capture
- Confirm the run directory is created

At this point, the measurement exists as raw evidence.

---

## 10. Export Viewer Pack

Run the export command (Phase 2):

```bash
python scripts/phase2/export_viewer_pack_v1.py --session-dir <session_dir> --out ./export --zip
```

Confirm:

- Export completes without error
- Validation runs automatically
- `validation_report.json` is written
- `passed: true`

**If export fails:**

- Read the error message
- Open `validation_report.json`
- Fix the indicated issue before proceeding

---

## 11. Verify the Export

Open the exported ZIP in the Viewer:

- Confirm spectrum loads
- Confirm peak data appears
- Confirm metadata matches the session

This proves the full **measurement → export → inspection** pipeline works.

---

## 12. Repeat Once (Confidence Check)

Repeat the measurement one more time under the same conditions.

You should see:

- Similar peak locations
- Minor variance only
- No structural differences

If results differ wildly, investigate:

- Tap location
- Support method
- Microphone placement

---

## Common First-Run Pitfalls

| Pitfall | Fix |
|---------|-----|
| Tapping too softly (low SNR) | Tap harder, move mic closer |
| Tapping twice accidentally | Practice single clean strikes |
| Clipping input | Reduce gain, move mic back |
| Moving mic between runs | Mark position, use fixed mount |
| Changing FFT parameters prematurely | Use defaults until stable |
| Expecting interpretation instead of measurement | This tool measures, not evaluates |

All of these are normal and correctable.

---

## Completion Criteria (Checklist)

You are finished when:

- [ ] Instrument launches cleanly
- [ ] One clean impulse captured
- [ ] Spectrum shows stable peaks
- [ ] Viewer pack exports successfully
- [ ] Validation passes
- [ ] Second run produces similar results

At that point, the instrument is ready for real work.

---

## Final Reminder

> **This instrument measures response. Interpretation comes later.**

If you can complete this checklist, you are operating tap-tone-pi correctly.

---

## Reference

- [QUICKSTART.md](QUICKSTART.md) — 5-minute first measurement
- [INSTRUMENT_SCOPE.md](INSTRUMENT_SCOPE.md) — What this instrument does and does not claim
- [examples/reference/](examples/reference/) — Gold-standard comparison example
