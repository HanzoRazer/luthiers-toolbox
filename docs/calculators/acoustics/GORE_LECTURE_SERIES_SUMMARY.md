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

## Pack 3 — Measuring Monopole Mobility

**Path:** [`gore_monopole_mobility_measurement/`](./gore_monopole_mobility_measurement/)  
**Form:** ~9 minute bench tip; definition + measurement SOP  
**Primary deliverable:** [`ANNOTATED_LECTURE_NOTES.md`](./gore_monopole_mobility_measurement/ANNOTATED_LECTURE_NOTES.md) (M01–M12)  
**Gaps:** [`GAPS_NOT_RECORDED.md`](./gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md)

### What it adds

Outline lab for \(Y=1/\sqrt{km}\): 1 kg jig → \(k\); plugged uncoupled \(f\) → \(m\); toolchain thresholds (~11–12 / ~20) with unit-profile caveat (spoken 31.3 vs SI ~3.13).

---

## Pack 4 — Shop Talk Live Stream #25 (this addition)

**Path:** [`gore_shop_talk_25/`](./gore_shop_talk_25/)  
**Form:** ~1 hour falcate-focused Q&A  
**Primary deliverable:** [`ANNOTATED_LECTURE_NOTES.md`](./gore_shop_talk_25/ANNOTATED_LECTURE_NOTES.md) (S01–S21)  
**Gaps:** [`GAPS_NOT_RECORDED.md`](./gore_shop_talk_25/GAPS_NOT_RECORDED.md)

### What it adds

| Theme | Takeaway |
|-------|----------|
| Falcate humidity | Less cross-grain continuity → less top pump; action stable; edge-bulge optical “sunk bridge” |
| Falcate origin | Sail tape-drive stress paths + put stiffness where stress is; name = sickle-shaped |
| Frequency rescue | Aim high; stiff/light bridge to raise; mass-load down hurts responsiveness; retop if way low |
| Side mass | Coins/mold experiment; 4DOF; large side mass can greatly increase loudness (anecdote) |
| Live-back retop | B11 ≈ target T113; +few Hz when topped; 4-semitone rule |
| Marty vs falcate | Meyer “third” = long dipole under his setup; falcate uses cross-tripole / limits bridge rotation (~2°) |
| Sides / ports / scale | Solid sides tunable ~2–3 Hz air; side port shifts A0; dread braces follow span³ |

| Prior pack | Pack 4 detail |
|------------|---------------|
| ST#20 falcate / mids | Humidity mechanics + Marty contrast + naming/origin |
| ST#20 P07 / mobility | Rescue vs mass-load tension made explicit |
| ST#20 four-semitone | B11 back-only procedure |
| Wolf mid-scale | Steel 170/180/190; classical ~190 |

---

## How the packs fit the priority stack

```text
1. Resonances off scale tones     ← Packs 1, 2, 4 (targets + rescue + B11)
2. High monopole mobility         ← Packs 1, 3 (avoid heavy mass-load downs — Pack 4)
3. Intonation / compensation      ← Pack 1 (nut/saddle); separate calc stack
```

Do not ship mobility optimization that ignores Pack 2 clearance rules.

---

## Recommended reading order

1. This summary  
2. **Pack 4** Shop Talk #25 (falcate + rescue + side mass)  
3. **Pack 3** mobility measurement + its gaps register  
4. **Pack 2** wolf-notes lab  
5. **Pack 1** Shop Talk #20 full methodology  
6. All crosswalks before code work  

---

## Known absence (do not paper over)

Granularity not available from the source videos is still **knowledge**.

| Register | Focus |
|----------|--------|
| [`gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md`](./gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md) | Jig geometry, unit profile, peak-ID, thresholds (G-M01–G-M35) |
| [`gore_shop_talk_25/GAPS_NOT_RECORDED.md`](./gore_shop_talk_25/GAPS_NOT_RECORDED.md) | Humidity Δaction, side-mass mechanism, book F-number map, cube-rule worked example (G-S01–G-S15) |

**Until blockers close:** no mobility threshold badges; SI only if `si_raw`; no invented falcate geometry; guided labs may use `unknown` metadata.

---

## Shared classification legend

| Tag | Meaning |
|-----|---------|
| **EP** | Established principle |
| **EO** | Empirical observation |
| **TG** | Trevor Gore recommendation / practice |
| **RO** | Robbie O’Brien shop practice / on-camera thresholds |
| **OH** | Open hypothesis / taste / opinion |
