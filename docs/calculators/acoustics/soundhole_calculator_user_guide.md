# Soundhole Calculator User Guide

**Version:** 1.0
**Route:** `/app/calculators/acoustics/soundhole`
**localStorage key:** `soundhole_cal_log`

A calculator for acoustic guitar soundhole design combining Helmholtz resonance physics with P:A (Perimeter-to-Area) ratio analysis.

---

## Table of Contents

1. [Overview](#overview)
2. [Design Mode](#design-mode)
3. [Calibration Mode](#calibration-mode)
4. [Physics Background](#physics-background)
5. [Gore End-Correction Factor (α)](#gore-end-correction-factor-α)
6. [Williams P:A Ratio Research](#williams-pa-ratio-research)
7. [Measuring A0 with Audacity](#measuring-a0-with-audacity)
8. [References](#references)

---

## Overview

The Soundhole Calculator helps luthiers design soundholes by predicting the **Helmholtz resonance frequency (A0)** — the primary air resonance that gives acoustic guitars their characteristic "boom."

Two complementary metrics are calculated:

| Metric | Purpose |
|--------|---------|
| **A0 (Hz)** | Predicted Helmholtz resonance frequency |
| **P:A Ratio** | Soundhole efficiency indicator (perimeter ÷ area) |

---

## Design Mode

Design mode lets you explore how soundhole geometry affects resonance.

### Input Parameters

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| **Soundhole Diameter** | Circular opening diameter | 80–110 mm |
| **Body Volume** | Internal air volume of guitar body | 12–18 litres |
| **Top Thickness** | Soundboard thickness at soundhole edge | 2.5–3.5 mm |
| **Alpha (α)** | End-correction factor (system property) | 0.6–0.85 |

### Output Metrics

- **Predicted A0**: Helmholtz resonance in Hz
- **Musical Note**: Nearest pitch (e.g., "G2", "F#2")
- **P:A Ratio**: Efficiency indicator with Williams threshold assessment

### Design Workflow

1. Enter your guitar's body volume (measure or estimate from plans)
2. Set soundboard thickness at the soundhole location
3. Adjust soundhole diameter to target your desired A0
4. Select an α value from Gore's published priors (or your calibrated value)
5. Check P:A ratio — values ≥ 0.10 indicate significant acoustic gain

---

## Calibration Mode

Calibration mode lets you derive α from a completed instrument by measuring its actual A0.

### Why Calibrate?

Gore's α is a **system property**, not a material constant. It depends on:

- Soundhole geometry (round, oval, multiple holes)
- Bracing pattern and stiffness
- Top/back coupling
- Air leakage at joints

Calibrating with your actual builds gives you personalized α values.

### Calibration Workflow

1. **Build the guitar** with known geometry
2. **Measure actual A0** using Audacity (see procedure below)
3. **Enter measured values** in Calibration mode:
   - Soundhole diameter (mm)
   - Body volume (litres)
   - Top thickness (mm)
   - Measured A0 (Hz)
4. **Calculator derives α** that produces the measured A0
5. **Log the calibration** to build your personal priors table

### Calibration Log

Logged calibrations are stored in browser localStorage (`soundhole_cal_log`). Each entry records:

- Date/time
- All input parameters
- Derived α value
- Optional notes (guitar model, wood species, bracing style)

Export your log periodically for backup — localStorage can be cleared by browser settings.

---

## Physics Background

### Helmholtz Resonance

A guitar body acts as a **Helmholtz resonator** — an air cavity with a single opening. The resonance frequency depends on:

- **A**: Soundhole area (m²)
- **V**: Body volume (m³)
- **L_eff**: Effective length of the air plug in the soundhole

The Helmholtz equation:

```
f₀ = (c / 2π) × √(A / (V × L_eff))
```

Where:
- `c` = speed of sound ≈ 343 m/s at 20°C
- `L_eff` = t + α × √(A/π)
- `t` = top thickness (physical depth of the hole)
- `α` = end-correction factor

### Effective Length

The air in the soundhole doesn't just vibrate through the physical thickness of the top. It extends beyond both surfaces as an "air plug." The end-correction factor α accounts for this extension:

```
L_eff = t + α × r_eff
```

Where `r_eff = √(A/π)` is the effective radius.

For a circular hole in an infinite baffle, theoretical α ≈ 1.7 (0.85 per side). Real guitars have lower values due to the finite soundboard and acoustic coupling.

---

## Gore End-Correction Factor (α)

Trevor Gore's research provides empirically-derived α values for different guitar body styles:

| Body Style | α Value | Typical A0 Range |
|------------|---------|------------------|
| Classical | 0.61 | 95–105 Hz |
| Jumbo | 0.70 | 90–100 Hz |
| OM (Orchestra Model) | 0.73 | 100–110 Hz |
| Dreadnought | 0.76 | 95–105 Hz |
| Parlour | 0.83 | 110–125 Hz |

### Using Gore's Priors

1. **New design**: Start with the α for your body style
2. **After calibration**: Use your measured α for that specific build
3. **Averaging**: After several calibrations, average your α values per body style

Gore emphasizes that α is influenced by the entire acoustic system, not just the soundhole geometry.

---

## Williams P:A Ratio Research

Simon Williams (2019) investigated soundhole efficiency using the **Perimeter-to-Area ratio**:

```
P:A = Perimeter / Area
```

For a circle: `P:A = 2πr / πr² = 2/r`

### Key Findings

| P:A Ratio | Assessment |
|-----------|------------|
| ≥ 0.10 | **Significant gain** — measurable acoustic improvement |
| 0.08–0.10 | **Approaching threshold** — modest benefit |
| < 0.08 | **Below threshold** — diminishing returns |

### Implications for Design

- **Smaller holes** have higher P:A ratios (more efficient per unit area)
- **Multiple small holes** can achieve same area with higher total P:A
- **Oval/elongated holes** have higher P:A than circles of same area

The calculator displays P:A with a visual gauge showing the Williams thresholds.

---

## Measuring A0 with Audacity

### Equipment Needed

- Computer with Audacity (free, open-source)
- USB microphone or audio interface + condenser mic
- Quiet room

### Procedure

1. **Setup**
   - Position microphone 15–30 cm from soundhole, slightly off-axis
   - Ensure room is quiet (A0 is low frequency, easily masked)

2. **Excitation**
   - Tap the bridge firmly with knuckle or soft mallet
   - Alternatively: sing/hum near the soundhole and sweep pitch until resonance

3. **Recording**
   - Record several taps in Audacity
   - Select a clean tap decay (avoid string noise)

4. **Analysis**
   - Select the decay region
   - **Analyze → Plot Spectrum**
   - Set Size to 4096 or higher for frequency resolution
   - Look for the lowest prominent peak — this is A0

5. **Verification**
   - A0 typically falls between 85–130 Hz for steel-string guitars
   - Classical guitars: 90–110 Hz
   - The peak should be broad and dominant

### Tips

- Mute strings with foam or cloth to isolate body resonance
- Multiple measurements improve accuracy
- Temperature affects speed of sound (~0.6 Hz per °C)

---

## References

1. **Gore, T. & Gilet, G.** (2011). *Contemporary Acoustic Guitar Design and Build*. Trevor Gore.
   - Chapter 4: Air resonance and soundhole design
   - Appendix: Measured α values for production guitars

2. **Williams, S.** (2019). "Soundhole Geometry and Acoustic Efficiency." *American Lutherie*, No. 138.
   - P:A ratio analysis
   - Multiple soundhole configurations

3. **Fletcher, N. & Rossing, T.** (1998). *The Physics of Musical Instruments*. Springer.
   - Chapter 9: Guitar acoustics
   - Helmholtz resonator theory

4. **Jansson, E.** (2002). *Acoustics for Violin and Guitar Makers*. KTH Stockholm.
   - Online resource: http://www.speech.kth.se/music/acviguit4/

5. **Elejabarrieta, M.J., Ezcurra, A., & Santamaría, C.** (2002). "Coupled modes of the resonance box of the guitar." *Journal of the Acoustical Society of America*, 111(5).
   - Air-top coupling analysis

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-30 | Initial release with Design + Calibration modes |

---

*Part of The Production Shop acoustic calculator module.*
