# Gore Lecture Knowledge Series — Executive Summary

Living index for annotated lecture packs derived from Robbie O’Brien / Trevor Gore teaching video. Processing template: full-content review → classified teaching points → Toolbox / Tap Tone Pi crosswalk (empirical knowledge layer preferred over new calculators).

---

## Pack 1 — Shop Talk Live Stream #20 (Q&A + FRF demo)

**Path:** [`gore_shop_talk_20/`](./gore_shop_talk_20/)  
**Form:** ~1 hour livestream; methodology breadth  
**Primary deliverable:** [`ANNOTATED_LECTURE_NOTES.md`](./gore_shop_talk_20/ANNOTATED_LECTURE_NOTES.md) (38 points, P01–P38)

### What it established

| Theme | Takeaway |
|-------|----------|
| Priority stack | Modes off scale tones → high monopole mobility → intonation; secondary geometry (e.g. bridge rotation) is subordinate |
| Wolf principle | Resonance on scale tone → high admittance → loud/short uneven note; prefer **mid-scale** placement |
| Demo targets | Closed-box preview toward **100 / 180 / 226 Hz** (taste-dependent; mid-scale for that body) |
| Free top | Pitch-tuning a free top is a poor finished-guitar proxy |
| Live back | More FRF peaks ~300–1000 Hz / more tone; slight volume cost vs non-live |
| Bridge | Adds **mass + stiffness**; putty/tape ≠ glued bridge |
| Mobility | \(\mu \propto 1/\sqrt{km}\); measure with stage metadata |
| Philosophy | Acoustic specification over timber-cutter specification |

### Critical Toolbox gaps called out

1. Monopole **mobility** as first-class measured quantity  
2. Named mid-scale triad + scale-tone collision **design practice**  
3. Free-top prohibition / stage gates in UX  
4. FRF lab pack + stage taxonomy  
5. Live-back methodology on existing 2-/3-osc models  
6. Falcate as KB first (geometry later)

---

## Pack 2 — Tips to Your Mailbag: Wolf Notes (this addition)

**Path:** [`gore_wolf_notes_mailbag/`](./gore_wolf_notes_mailbag/)  
**Form:** ~6 minute focused tip; diagnosis + remediation depth  
**Primary deliverable:** [`ANNOTATED_LECTURE_NOTES.md`](./gore_wolf_notes_mailbag/ANNOTATED_LECTURE_NOTES.md)

### How it extends Pack 1

Shop Talk #20 stated the **why** of wolves (admittance / mid-scale rule). This tip supplies the **shop procedure**:

1. **Hear it** — note/string sounds distinctly different (often louder)  
2. **Confirm on tuner** — wolfy pitch is unsteady / oscillatory and can push the scale tone sharp  
3. **Measure box FRF** — 10-tap Visual Analyzer; identify air + main top peaks  
4. **Map to scale tones / harmonics** — example: open A @ 110 Hz and harmonic @ 220 Hz both near resonances  
5. **Move resonances ≥ ~½ semitone** from scale tones (maximum distance before approaching the next tone)  
6. **Choose levers** — air: soften box (top/back stiffness) or change soundhole diameter; top: ±mass / ±stiffness  

### Relationship map

| Pack 1 point | Pack 2 detail |
|--------------|---------------|
| P03 mid-scale avoidance | Operational target: **half-semitone** clearance |
| P04 100/180/226 | Concrete failure mode: air≈110, top≈220 (A and 2×A) |
| P02 mode-selective tuning | Explicit dual-resonance problem (air **and** top) |
| P33 FRF SOP | Rubber-ball / satay-stick hammer; lower-bout taps; 10 averages |
| Soundhole / plate calcs | Remediation menu now specified for guided workflow |

---

## Recommended reading order

1. This summary  
2. Pack 2 wolf-notes notes (tight lab)  
3. Pack 1 full notes (broader methodology)  
4. Both crosswalks before any code work  

---

## Shared classification legend

| Tag | Meaning |
|-----|---------|
| **EP** | Established principle |
| **EO** | Empirical observation |
| **TG** | Trevor Gore recommendation / practice |
| **OH** | Open hypothesis / taste / opinion |
