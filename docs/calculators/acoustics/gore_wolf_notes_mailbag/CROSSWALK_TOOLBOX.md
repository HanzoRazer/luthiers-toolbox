# Crosswalk — Wolf Notes Mailbag → Toolbox / Tap Tone Pi

Extends Shop Talk #20 packet **C2** (mid-scale target & wolf-avoidance) with an operational diagnosis/remediation lab. Point IDs: `W01`–`W09` in `ANNOTATED_LECTURE_NOTES.md`.

---

## A. Status vs current stack

| IDs | Topic | Today | Gap | Destinations |
|-----|-------|-------|-----|--------------|
| W01–W03 | Ear + tuner + pitch-class diagnosis | Thin — WSI/wolf metrics exist; no guided listening/tuner-flutter SOP | High | **LAB**, **KB** |
| W04 | 10-tap FRF + peak→note/harmonic map | Partial — spectrum ingest; harmonic-of-pitch-class overlay weak | High | **LAB**, **MEAS** |
| W05 | ½-semitone / mid-scale clearance | Partial — philosophy in ST#20 notes; not a first-class rule constant | High | **RULE**, **EMP** |
| W06 | Air levers (compliance + soundhole Ø) | **Strong** soundhole/A0 stack | Low (wire-up) | **LAB** calling existing calcs |
| W07 | Top mass/stiffness levers | Partial — brace/mass trackers; no wolf decision tree | Medium | **LAB**, **EMP** |
| W08 | Coordinated multi-peak plan | Missing | High | **RULE**, **LAB** |
| W09 | Pedagogy / KB framing | This pack | — | **DOC** |

---

## B. Guided lab outline (product)

**Name (suggested):** `Wolf Note Diagnosis & Clearance`

1. Select suspect pitch class (e.g. A / 110 Hz).  
2. Listening checklist (W01) + optional tuner flutter capture (W02).  
3. Ingest / measure FRF (Tap Tone Pi preferred; VA appendix OK).  
4. Overlay peaks vs pitch-class fundamentals **and** 2× harmonics (W04).  
5. Compute clearance in **cents**; flag if < ~50 cents (W05).  
6. If air-flagged: offer soundhole Ø directionality + box-softening notes (W06) via existing soundhole tools.  
7. If top-flagged: offer mass/stiffness direction menu (W07); link brace-height / mass-add procedures.  
8. If both: force coordinated plan UI (W08); warn about cross-effects.  
9. Re-measure; accept when clearances and ear/tuner checks pass.

**NO-CALC:** Do not auto-emit a single “resize soundhole to X mm” as the only fix from one wolf flag.

---

## C. Constants / empirics to add (small)

| Item | Proposal | Home |
|------|----------|------|
| Clearance target | `min_clearance_cents = 50` (½ semitone), configurable | voicing / design_advisor |
| Failure example profile | A-wolf demo: air≈110, top≈220 (documentation + test fixture narrative) | docs + optional reference library |
| Harmonic check depth | At least fundamental + 2× for flagged pitch class | analyzer interpret |

Reconcile with ST#20 `gore_mid_scale_triad_v1` (100/180/226): triad = **design targets**; W05 = **acceptance clearance** against whatever scale grid the instrument uses.

---

## D. Ownership

| Concern | Owner |
|---------|-------|
| FRF capture, peak picking | tap_tone_pi |
| Cents-to-nearest-note, harmonic overlay, advice | Toolbox analyzer / guided workflow |
| Soundhole diameter predictions | Existing soundhole calculators |
| Top Δk/Δm shop edits | EMP corpus + plate/voicing guidance — not a new physics engine |

---

## E. Implementation priority (after Pack 1 knowledge merge)

1. Peak↔scale-tone **cents** clearance in analyzer interpret (W05)  
2. Harmonic-aware wolf candidate flags (W04/W08)  
3. Guided lab wiring soundhole + top lever menus (W06/W07)  
4. Tuner-flutter / listening checklist copy (W01–W03) — docs/UX first  
