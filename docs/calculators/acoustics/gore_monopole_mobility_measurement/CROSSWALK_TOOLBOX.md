# Crosswalk — Monopole Mobility Measurement → Toolbox / Tap Tone Pi

Closes Shop Talk #20 critical gap **C1** (monopole mobility as measured quantity). Point IDs: `M01`–`M12`.

---

## A. Status vs current stack

| IDs | Topic | Today | Gap | Destinations |
|-----|-------|-------|-----|--------------|
| M01–M02 | Definition + \(Y=1/\sqrt{km}\) | Formula mentioned in ST notes / qualitatively in docs; **no first-class mobility feature** | Critical | **DOC**, **EMP**, **LAB** |
| M03–M04 | 1 kg deflection → \(k\) | Top deflection calculators exist for **structural** loads — not Gore mobility jig workflow | High | **LAB**, **MEAS** |
| M05–M07 | Uncoupled \(f\) → \(m\) | Voicing / analyzer peaks exist; plug-hole stage metadata incomplete | High | **MEAS**, Tap Tone tags |
| M08–M09 | Scores + thresholds 11–12 / 20 | Missing | High | **EMP** with `unit_profile_id` |
| M10 | Carrico / Guitar Tap / Luther Academy | External; document only | Low | **KB** links |
| M11–M12 | Unit lock + SOP | Missing — highest risk if coded naively | Critical | **RULE**, **LAB**, **NO-CALC** without profile |

---

## B. Recommended product shape

**Guided lab:** `Monopole Mobility Measurement`

Inputs: \(\delta\) mm, \(F\) (default 9.81 N / 1 kg), uncoupled \(f\) Hz, plug method, jig ID, build stage (bridge on/off).  
Outputs: SI \(k\), \(m\), \(Y_{\mathrm{SI}}\) + optional `gore_shop_score` once profile calibrated.  
Display thresholds **only** when profile ≠ `si_raw` or after explicit calibration note.

**Tap Tone Pi:** capture/tag uncoupled monopole peak; do **not** own deflection jig math.  
**Toolbox:** own \(k\), \(Y\), thresholds, guided UX.

**NO-CALC:** species→mobility; putty-bridge mobility preview; auto-threshold without unit profile.

---

## C. Calibration task before shipping thresholds

1. Reproduce Carrico spreadsheet with demo-like inputs (1 kg, 27 mm, 180.7 Hz).  
2. Confirm whether output matches ~31.3.  
3. Freeze `unit_profile: carrico_gore_v1` constants.  
4. Publish SI alongside score.  
5. Only then enable M09 bands in UI.

Until step 3 lands, docs may quote thresholds as **toolchain-relative** (this pack).

---

## D. Implementation priority

1. Docs/lab SOP (this pack) — done  
2. Measurement schema fields (δ, F, f, plugged, stage)  
3. SI calculator + checksum \(Y=2\pi f/k\)  
4. Spreadsheet profile calibration  
5. Guided UI + threshold badges  
6. Link from voicing priority stack (modes + mobility)  
