# Reference Comparison — Canonical Example

This directory contains a **gold-standard before/after comparison** demonstrating the instrument's core capability: detecting frequency shifts in the same specimen under different conditions.

---

## Specimen

| Property | Value |
|----------|-------|
| Type | Spruce plate (bookmatched) |
| Dimensions | 200 × 150 × 3 mm |
| Support | Free-free (foam blocks at nodal lines) |
| Tap location | Center, marked with pencil |

---

## Comparison: Before vs After Humidity Exposure

### Conditions

| Run | Label | Temp | RH | Notes |
|-----|-------|------|----|----|
| A | `run_a_dry/` | 22°C | 35% | Baseline, conditioned 48h |
| B | `run_b_humid/` | 22°C | 65% | After 24h in humidity chamber |

### Key Observation

| Metric | Run A (Dry) | Run B (Humid) | Delta |
|--------|-------------|---------------|-------|
| Mode 1 | 187.5 Hz | 182.0 Hz | −5.5 Hz |
| Mode 2 | 312.0 Hz | 305.5 Hz | −6.5 Hz |
| Mode 3 | 498.0 Hz | 489.0 Hz | −9.0 Hz |

**Interpretation (human, not instrument):** Increased moisture content reduces stiffness-to-mass ratio, lowering all modal frequencies proportionally.

---

## Files

```
reference/
├── README.md              (this file)
├── run_a_dry/
│   ├── audio.wav
│   ├── analysis.json
│   └── spectrum.csv
├── run_b_humid/
│   ├── audio.wav
│   ├── analysis.json
│   └── spectrum.csv
└── comparison_screenshot.png
```

---

## How to Reproduce

1. Condition specimen at 35% RH for 48 hours
2. Capture run A: `python -m tap_tone.main --device 2 --out ./run_a_dry --label "dry_baseline"`
3. Expose specimen to 65% RH for 24 hours
4. Capture run B: `python -m tap_tone.main --device 2 --out ./run_b_humid --label "humid_24h"`
5. Compare `analysis.json` peak frequencies

---

## What This Demonstrates

| Capability | Evidence |
|------------|----------|
| **Sensitivity** | 5–9 Hz shift detected reliably |
| **Repeatability** | Same tap location, same protocol |
| **Comparability** | Artifacts are directly comparable |
| **Traceability** | Full provenance in each run |

---

## Screenshot

![Comparison Screenshot](comparison_screenshot.png)

*Overlay of Run A (blue) and Run B (orange) spectra. Frequency shift is visible at all major peaks.*

---

## Note on Interpretation

The instrument **measures** the frequency shift.  
The instrument **does not claim** the cause.

Humidity is the documented variable. The causal link is inferred by the operator based on experimental design, not by the software.

> **Doctrine:** The analyzer exports evidence. Interpretation is a human act.
