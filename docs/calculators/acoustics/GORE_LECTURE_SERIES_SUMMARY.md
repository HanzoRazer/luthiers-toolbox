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

### Critical Toolbox gaps (original callout)

1. Monopole **mobility** as first-class measured quantity → **addressed by Pack 3 (measurement SOP); code still open**  
2. Named mid-scale triad + scale-tone collision **design practice** → Pack 2 operationalizes clearance  
3. Free-top prohibition / stage gates in UX  
4. FRF lab pack + stage taxonomy  
5. Live-back methodology on existing 2-/3-osc models  
6. Falcate as KB first (geometry later)

---

## Pack 2 — Tips to Your Mailbag: Wolf Notes

**Path:** [`gore_wolf_notes_mailbag/`](./gore_wolf_notes_mailbag/)  
**Form:** ~6 minute focused tip; diagnosis + remediation  
**Primary deliverable:** [`ANNOTATED_LECTURE_NOTES.md`](./gore_wolf_notes_mailbag/ANNOTATED_LECTURE_NOTES.md) (W01–W09)

### What it adds

Shop procedure for wolves: ear → tuner flutter → 10-tap FRF → map to pitch class + harmonics → **½-semitone clearance** → air levers (soften box / ± soundhole Ø) + top levers (±mass / ±stiffness) → coordinated multi-peak plans.

| Pack 1 point | Pack 2 detail |
|--------------|---------------|
| P03 mid-scale avoidance | Operational target: **half-semitone** clearance |
| P04 100/180/226 | Failure mode example: air≈110, top≈220 (A and 2×A) |
| P02 mode-selective tuning | Explicit dual-resonance problem (air **and** top) |

---

## Pack 3 — Measuring Monopole Mobility (this addition)

**Path:** [`gore_monopole_mobility_measurement/`](./gore_monopole_mobility_measurement/)  
**Form:** ~9 minute bench tip; definition + full measurement SOP  
**Primary deliverable:** [`ANNOTATED_LECTURE_NOTES.md`](./gore_monopole_mobility_measurement/ANNOTATED_LECTURE_NOTES.md) (M01–M12)

### What it adds

1. **Definition:** \(Y\) approximates average admittance / soundboard responsiveness (Gore term)  
2. **Formula:** \(Y = 1/\sqrt{k m}\) with \(k=F/\delta\), \(m=k/(2\pi f)^2\), \(F=9.81\,\mathrm{N}\) for 1 kg  
3. **Stiffness SOP:** Carrico-style deflection jig; 1 kg load; δ in mm (demo 27 mm)  
4. **Uncoupled \(f\):** plug soundhole (yogurt cup or dedicated plug); Guitar Tap / equivalent (demo 180.7 Hz)  
5. **Thresholds (toolchain-relative):** steel ~11–12 “starting responsive”; classical / Gore “very responsive” ~20; demo score 31.3  
6. **Critical caveat:** spoken score vs pure SI (~3.13 s/kg for those inputs) ⇒ lock a **unit profile** before shipping threshold UI  

| Pack 1 point | Pack 3 detail |
|--------------|---------------|
| P09 \(1/\sqrt{km}\) | Full lab: measure \(k\), \(f\) → \(m\) → \(Y\) |
| P01 plugged uncoupled top | Required boundary condition for mobility \(f\) |
| P10–P11 mobility priority / brace height | Now has a number to optimize against — still co-equal with wolf clearance |

---

## How the three packs fit the priority stack

```text
1. Resonances off scale tones     ← Pack 1 philosophy + Pack 2 lab
2. High monopole mobility         ← Pack 1 priority + Pack 3 measurement
3. Intonation / compensation      ← Pack 1 (nut/saddle); separate calc stack
```

Do not ship mobility optimization that ignores Pack 2 clearance rules.

---

## Recommended reading order

1. This summary  
2. **Pack 3** mobility measurement (tight lab + unit warning)  
3. **Pack 3 gaps register** — [`gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md`](./gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md)  
4. **Pack 2** wolf-notes lab  
5. **Pack 1** full methodology notes  
6. All three crosswalks before code work  

---

## Known absence (do not paper over)

Granularity not available from the source videos is still **knowledge**. Primary register:

- [`gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md`](./gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md) — jig geometry, unit profile, peak-ID, stage matrix, threshold provenance (G-M01–G-M35)

**Until blockers close:** no product threshold badges for mobility; SI output only if labeled `si_raw`; guided labs must allow `unknown` metadata rather than fabricated defaults.

---

## Shared classification legend

| Tag | Meaning |
|-----|---------|
| **EP** | Established principle |
| **EO** | Empirical observation |
| **TG** | Trevor Gore recommendation / practice |
| **RO** | Robbie O’Brien shop practice / on-camera thresholds |
| **OH** | Open hypothesis / taste / opinion |
