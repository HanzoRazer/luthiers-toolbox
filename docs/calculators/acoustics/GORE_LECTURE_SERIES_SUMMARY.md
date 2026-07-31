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

## Pack 5 — Responsive Guitar Objectives (PowerPoint session) (this addition)

**Path:** [`gore_shop_talk_responsive_objectives/`](./gore_shop_talk_responsive_objectives/)  
**Form:** Prepared PowerPoint + dense Q&A (~1 hour)  
**Primary deliverable:** [`ANNOTATED_LECTURE_NOTES.md`](./gore_shop_talk_responsive_objectives/ANNOTATED_LECTURE_NOTES.md) (R01–R25)  
**Gaps:** [`GAPS_NOT_RECORDED.md`](./gore_shop_talk_responsive_objectives/GAPS_NOT_RECORDED.md)

### What it adds

| Theme | Takeaway |
|-------|----------|
| Objective spine | **Right** \(Y\) (not max) + evenness + musicality (peak density + ET intonation) |
| Mobility demo | Bridge jig; ~**0.15 mm** @ ~1 kg (**conflicts Pack 3’s 27 mm** — calibration blocker) |
| \(Y\) bands | Classical ~20 / ~30s; steel ~10–12 / low 20s; “conspiracy against guitarists” |
| Wolf table | ±50¢ outer columns; no exact T111–T112 octave; 4 semitone T112–T113 |
| Peak density | Matthews/Kohut: 20–30 peaks to 5 kHz; live back for peaks |
| SRC / Q | SRC \(\sqrt{E/\rho^3}\) by guitar intent; Q blind tests often null |
| Build path | Spectrogram stages boxed → edge thin → strung → side mass (e.g. → ~91/170/224) |
| Other | Bridge mass vs headroom; harmonic bar; tertiaries; altitude/4DOF; trial mass for “banjo” |

---

## Pack 6 — Guitar Analysis & Testing course (**PARTIAL**)

**Path:** [`gore_guitar_analysis_testing/`](./gore_guitar_analysis_testing/)  
**Form:** Workshop measurement-setup course  
**Ingest:** Introduction only — five modules announced; SOPs not yet transcribed  
**Gaps:** [`GAPS_NOT_RECORDED.md`](./gore_guitar_analysis_testing/GAPS_NOT_RECORDED.md)

**Action needed:** paste Modules A–E body (especially mobility SOP vs Packs 3 & 5 δ conflict).

---

## Pack 7 — Shop Talk Live Stream #44 (this addition)

**Path:** [`gore_shop_talk_44/`](./gore_shop_talk_44/)  
**Form:** ~1 hour in-shop Q&A during masterclass week  
**Primary deliverable:** [`ANNOTATED_LECTURE_NOTES.md`](./gore_shop_talk_44/ANNOTATED_LECTURE_NOTES.md) (U01–U23)  
**Gaps:** [`GAPS_NOT_RECORDED.md`](./gore_shop_talk_44/GAPS_NOT_RECORDED.md)

### What it adds

| Theme | Takeaway |
|-------|----------|
| Mobility vs rotation | Hear mobility; 2° is structural ceiling, not fetish target |
| Side-mass mechanism | T112 concentric-dipole node outboard → louder + trims f |
| Dread falcate | Prefer T112 **170/180**; large guitars stiffer than 2° |
| Construction | Brace tuck ~+25% K; heavy linings → standing-wave volume; scallop→symmetry |
| Definitions | Modal tuning; better guitar = playability + structure + musicality |
| Conspiracy | High Street ~50% of potential; banjo floor if too light/floppy |

---

## How the packs fit the priority stack

```text
1. Resonances off scale tones     ← Packs 1, 2, 4, 5, 7
2. Right monopole mobility        ← Packs 1, 3, 5, 7 (U04: mobility �2, 4, 5, 7
2. Right monopole mobility        ← Packs 1, 3, 5, 7 (U04: mobility ≫ rotation vanity)
3. Musicality + intonation        ← Packs 5, 7 (responsive harder to intonate)
4. Measurement setup chain        ← Pack 6 (partial)
```

Do not ship max-\(Y\) optimization that ignores clearance or intonation.

---

## Recommended reading order

1. This summary  
2. **Pack 5** objectives spine + **Pack 7** U04/U05 (mobility priority + side-mass why)  
3. **Pack 5 / Pack 3 gaps** — resolve **0.15 mm vs 27 mm** before mobility UI  
4. **Pack 6** when complete (setup SOPs)  
5. **Pack 4** Shop Talk #25  
6. **Pack 2** wolf lab  
7. **Pack 1** Shop Talk #20  
8. All crosswalks before code work  

---

## Known absence (do not paper over)

| Register | Focus |
|----------|--------|
| [`gore_guitar_analysis_testing/GAPS_NOT_RECORDED.md`](./gore_guitar_analysis_testing/GAPS_NOT_RECORDED.md) | Course SOPs incomplete |
| [`gore_shop_talk_responsive_objectives/GAPS_NOT_RECORDED.md`](./gore_shop_talk_responsive_objectives/GAPS_NOT_RECORDED.md) | **G-R01** δ conflict |
| [`gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md`](./gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md) | Jig geometry / unit profile |
| [`gore_shop_talk_25/GAPS_NOT_RECORDED.md`](./gore_shop_talk_25/GAPS_NOT_RECORDED.md) | Humidity Δaction, book F-number map |
| [`gore_shop_talk_44/GAPS_NOT_RECORDED.md`](./gore_shop_talk_44/GAPS_NOT_RECORDED.md) | Side-mass quantitative model; +25% tuck assumptions |

**Until blockers close:** no mobility threshold badges; SI only if `si_raw`; no invented falcate geometry or Win7 click-paths; guided labs may use `unknown` metadata.

---

## Shared classification legend

| Tag | Meaning |
|-----|---------|
| **EP** | Established principle |
| **EO** | Empirical observation |
| **TG** | Trevor Gore recommendation / practice |
| **RO** | Robbie O’Brien shop practice / on-camera thresholds |
| **OH** | Open hypothesis / taste / opinion |
