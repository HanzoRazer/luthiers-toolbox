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

## Pack 7 — Shop Talk Live Stream #44

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

## Pack 8 — Shop Talk Live Stream #51 (this addition)

**Path:** [`gore_shop_talk_51_luther_academy_apps/`](./gore_shop_talk_51_luther_academy_apps/)  
**Form:** ~1 hour livestream; Gore motivation + Mallaloy five-tool demo  
**Primary deliverable:** [`ANNOTATED_LECTURE_NOTES.md`](./gore_shop_talk_51_luther_academy_apps/ANNOTATED_LECTURE_NOTES.md) (A01–A29)  
**Gaps:** [`GAPS_NOT_RECORDED.md`](./gore_shop_talk_51_luther_academy_apps/GAPS_NOT_RECORDED.md)

### What it adds

| Theme | Takeaway |
|-------|----------|
| Program spine | ~2008: resonances in place + monopole mobility; \(E\)/density/size → plate thickness; brace design; measure → correct |
| Productization | Course spreadsheets → free beta Luther Academy web apps (Resources footer) |
| Five tools | 4DOF+environment; plate thickness; FFT resonance reader; mobility (\(k_\mathrm{eff}\), \(m_\mathrm{eff}\)); flexural rigidity |
| Demo numbers | Plate → ~2.58 mm; boxed OM ~103/207; fit ~91.2/174/253; \(k\)~533 (units TBD), \(m\)~60.1 g; weight **1.00** vs **1.02 kg** |
| 4DOF why | 3DOF + rigid sides inadequate; Blu-tack/coins = side **mass** |
| \(Y\) vs tone | Same resonances → similar timbre; \(Y\) mainly loudness (psychoacoustic “volume=tone”) |
| Wolves | Played-note view: cents-to-mode + sustain timeline |

| Prior pack | Pack 8 detail |
|------------|---------------|
| Pack 3 / 5 mobility | App outputs \(k_\mathrm{eff}\)/\(m_\mathrm{eff}\); 1.00 kg weight note; **δ conflict unchanged** |
| Pack 4 / 7 side mass | 4DOF origin + mold/coins restated for app audience |
| Pack 2 wolves | Visual played-note / partial energy lab |
| Pack 5 altitude | Environment what-ifs (~3 Hz) in app |

---

## How the packs fit the priority stack

```text
1. Resonances off scale tones     ← Packs 1, 2, 4, 5, 7, 8 (A26 wolf viz)
2. Right monopole mobility        ← Packs 1, 3, 5, 7, 8 (A19/A24; U04 mobility ≫ rotation)
3. Musicality + intonation        ← Packs 5, 7 (responsive harder to intonate)
4. Measurement + tool chain       ← Pack 6 (partial) + Pack 8 (Academy apps map)
```

Do not ship max-\(Y\) optimization that ignores clearance or intonation.

---

## Recommended reading order

1. This summary  
2. **Pack 5** objectives spine + **Pack 7** U04/U05 (mobility priority + side-mass why)  
3. **Pack 5 / Pack 3 gaps** — resolve **0.15 mm vs 27 mm** before mobility UI  
4. **Pack 8** for spreadsheet→app toolchain + \(k_\mathrm{eff}\)/\(m_\mathrm{eff}\)→4DOF intent (after calibration)  
5. **Pack 6** when complete (setup SOPs)  
6. **Pack 4** Shop Talk #25  
7. **Pack 2** wolf lab  
8. **Pack 1** Shop Talk #20  
9. All crosswalks before code work  

---

## Known absence (do not paper over)

| Register | Focus |
|----------|--------|
| [`gore_guitar_analysis_testing/GAPS_NOT_RECORDED.md`](./gore_guitar_analysis_testing/GAPS_NOT_RECORDED.md) | Course SOPs incomplete |
| [`gore_shop_talk_responsive_objectives/GAPS_NOT_RECORDED.md`](./gore_shop_talk_responsive_objectives/GAPS_NOT_RECORDED.md) | **G-R01** δ conflict |
| [`gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md`](./gore_monopole_mobility_measurement/GAPS_NOT_RECORDED.md) | Jig geometry / unit profile |
| [`gore_shop_talk_51_luther_academy_apps/GAPS_NOT_RECORDED.md`](./gore_shop_talk_51_luther_academy_apps/GAPS_NOT_RECORDED.md) | App URLs; \(k\) units (**G-A05**); flexural-rigidity detail; δ still open |
| [`gore_shop_talk_25/GAPS_NOT_RECORDED.md`](./gore_shop_talk_25/GAPS_NOT_RECORDED.md) | Humidity Δaction, book F-number map |
| [`gore_shop_talk_44/GAPS_NOT_RECORDED.md`](./gore_shop_talk_44/GAPS_NOT_RECORDED.md) | Side-mass quantitative model; +25% tuck assumptions |
| [`nicoletti_mb_sound_acoustic_study_set/GAPS_NOT_RECORDED.md`](./nicoletti_mb_sound_acoustic_study_set/GAPS_NOT_RECORDED.md) | Kit δ unread; software identity |
| [`nicoletti_mb_kit_interview/GAPS_NOT_RECORDED.md`](./nicoletti_mb_kit_interview/GAPS_NOT_RECORDED.md) | Spreadsheets; exact \(Y\) formula; δ still open |
| [`nicoletti_science_luthier_stories/GAPS_NOT_RECORDED.md`](./nicoletti_science_luthier_stories/GAPS_NOT_RECORDED.md) | ETS masses; TPC formulas; book reference numbers |
| [`nicoletti_tonewood_parameters_webinar/GAPS_NOT_RECORDED.md`](./nicoletti_tonewood_parameters_webinar/GAPS_NOT_RECORDED.md) | Sheet cells; SRC formula; stage-Hz calibration |

**Until blockers close:** no mobility threshold badges; SI only if `si_raw`; no invented falcate geometry or Win7 click-paths; guided labs may use `unknown` metadata.

---

## Related non-Gore source packs

These are **separate schools/workflows**. Cross-link; do not merge into Gore calculators.

| Pack | Path | What it is |
|------|------|------------|
| Somogyi 01 — Air pump / bracing / tap | [`somogyi_01_air_pump_bracing_tap_tone/`](./somogyi_01_air_pump_bracing_tap_tone/) | Primary voice: efficient air pump; stiffness/weight + Q; tap for ringing potential; X ubiquity; don’t ignore the back; energy-loop setup |
| Somogyi 02 — Top & Back | [`somogyi_02_top_and_back/`](./somogyi_02_top_and_back/) | Back A/B proof; coupled-oscillator demo; top–back frequency relationship; stiffness-by-deflection + brace reduction while listening |
| Somogyi apprentice first build | [`somogyi_apprentice_build_workflow/`](./somogyi_apprentice_build_workflow/) | Build chronicle: stiffness-sanded top, X+lattice, double sides, solid linings, post-glue tap voicing; dialect contrasts with Gore side/lining/voicing culture |
| Nicoletti / MB Acoustic Study Set | [`nicoletti_mb_sound_acoustic_study_set/`](./nicoletti_mb_sound_acoustic_study_set/) | Three-phase kit how-to: miniDSP tap FRF → Chladni → 1 kg bridge dial |
| Nicoletti / MB kit interview | [`nicoletti_mb_kit_interview/`](./nicoletti_mb_kit_interview/) | Doctrine interview: why measure; between-note tuning; SRC/Q wood pick; monopole \(f,m,k\) → mobility; Chladni mass-at-pole |
| Nicoletti Science / Luthier Stories | [`nicoletti_science_luthier_stories/`](./nicoletti_science_luthier_stories/) | Watts interview: \(c\) in wood/air; responsiveness+headroom; ETS; TPC tonewood; offset hole; active-back mobility; D28 vs Larrivée contrast |
| Nicoletti tonewood parameters webinar | [`nicoletti_tonewood_parameters_webinar/`](./nicoletti_tonewood_parameters_webinar/) | PLG/EGB webinar: \(\rho\)/\(E\)/SRC/orthotropy/Q; REW+Caldersmith; Gore vibrational stiffness; mold pretune; wolf bands |

### Somogyi 01 — what it adds

| Theme | Takeaway |
|-------|----------|
| Definition | Guitar at bottom = **air pump**; success = efficient air move per finite string energy |
| Wood | Prefer best **stiffness-to-weight**; **Q** = liveness; BR high-Q exemplar; maple lower sustain |
| Intent | Not better/worse woods — match sustain vs quick-decay (flamenco/jazz) |
| Tap | Screen **ringing potential**; hold/location changes tone; rest “takes care of itself” |
| Bracing | Spanish named dialects vs steel-string **X** ubiquity; makers obsess top, ignore back |
| Box | Top → air → back → air/top bounce; radiation via port + exterior; back necessarily involved |

### Somogyi 02 — what it adds (this intake)

| Theme | Takeaway |
|-------|----------|
| Proof | Knees-damped back vs free → **open / loud / sustaining / woody**; top–back **ping-pong** |
| Model | Rubber band + weight: top / air / back; back usually heavier/denser |
| Design object | **Resonance relationship** of plates — miss it and waste energy; years to zero in |
| Quality language | Efficient pump = live (cave/echo); ordinary = thud; one demo ~**1.5 s** sustain |
| Method | **Target stiffness** via deflection (not thickness) → braces too massive → slow reduce while listening (“stew”) |

| Prior / related | Intersection |
|-----------------|--------------|
| Pack 01 G-ES02 | **Closed** by ES17 |
| Apprentice Y03 / Y13 | Same stiffness + listen culture, less apparatus detail |
| Gore Pack 1 live back | Cousin doctrine; different meter |
| Gore Packs 3/5/8 mobility | Efficiency language cousin — do not merge |
| Gore modal triad | Related *relationship* discipline — do not invent Somogyi Hz ratios |

**Open Somogyi blockers:** G-ES09 (top–back ratio), G-ES10 (deflection targets), G-ES11 (brace-stop words). Episode 03 not available; continue with other sources or later Somogyi episodes when they exist.

### Nicoletti / MB Study Set — what it adds (this intake)

| Theme | Takeaway |
|-------|----------|
| Provenance | Giuliano Nicoletti × Maderas Barber kit from *Master in the Sound of the Acoustic Guitar* |
| Phase 1 | miniDSP USB mic (+ serial calibration file); book-QR software **RTA**; hammer taps → curve → **monopole / dipole / tripole** freqs |
| Phase 2 | BT amp **NS-01G** + precision speaker + phone frequency generator; oregano/pepper/sawdust Chladni at Phase-1 keys |
| Demo Hz | This guitar only: mono ~**236–238 Hz**; dipole trial ~**275 Hz** — not design targets |
| Phase 3 | Dial indicator on bridge; calibrated **1 kg**; Δheight = tapa deflexión / movilidad; bone strip protects bridge |
| Depth | Connectivity video only — full SOP → Nicoletti book + MB Sound playlist |

| Prior / related | Intersection |
|-----------------|--------------|
| Gore Pack 3 / 5 / G-R01 | Same **1 kg deflection** family; **no δ spoken** → does **not** close 27 mm vs ~0.15 mm |
| Gore Pack 6 | Alternate measurement toolchain (miniDSP vs Visual Analyzer) |
| Somogyi ES27 | Deflection-stiffness culture (free top) vs finished-bridge kit |
| MB Sound corpus (data PR) | Same vendor ecosystem; kit SOP ≠ panel workbook specimens |

### Nicoletti / MB kit interview — what it adds (this intake)

| Theme | Takeaway |
|-------|----------|
| Why measure | Not required for *a* great guitar; required for **consistent** greatness + diagnosis (~100% potential) |
| Finished vs build | Finished: tune only — resonances **between notes**; build: check before bridge glue vs prior instruments |
| Monopole | Central bridge region; frequency dials bass↔treble character |
| Wood (MB catalog) | Fingerstyle high SRC; stage lower SRC; flamenco med–low damping; concert high Q / low damping |
| Chladni | Shape map for dipole/tripole; nodal lines; add mass on **one pole** to shift without spoiling others |
| Parameters | Monopole **mass** ≈ 20–25 cm circle + stiffness from weight deflection + frequency → **monopole mobility** (dynamic character) |
| Style fit | Very light/high mobility saturates under hard strumming; favor lower mass for even classical / fingerstyle |
| Philosophy | Reduce dispersion; don’t clone (“180 Hz ≠ same guitar”); player experience before FRF charts |

| Prior / related | Intersection |
|-----------------|--------------|
| Study-set pack | How-to hardware; interview supplies meaning layer |
| G-N03 / G-N04 | **Partial close** via N31–N34 / N20 |
| Gore Packs 2/3/5/8 | Between-note wolves; \(f,k,m,Y\) family — **δ still unread** |
| Somogyi ES03–ES08 | Genre ↔ material properties cousin |

### Nicoletti Science / Luthier Stories — what it adds (this intake)

| Theme | Takeaway |
|-------|----------|
| Physics primer | Air ~343 m/s vs spruce ~4.5–5 km/s; multi-material wave path; rim energy split ↔ sustain |
| Responsiveness | Light-touch sensitivity **+** strum headroom; ↑ mobility → ↑ wolf risk; factory often less responsive for reliability |
| Color vs hi-fi | Guitar as multipole “distortion producer” vs linear studio monitors; tune modes to right spots |
| ETS | Lower-bout **External Tuning Slot** — swappable masses tune main board resonance |
| TPC | Tonewood jig on nodal lines + marble ramp → \(f\), damping, stiffness, SRC; build wood library |
| Iulius design | Offset soundhole (radiate + structure); 13-fret overlapping bolt-on; active back with controlled mobility via denser ebony |
| References | Book “joining the dots”: same dread shape, D28 high-\(Y\) punchy vs Larrivée lower-\(Y\) smooth |

| Prior / related | Intersection |
|-----------------|--------------|
| Kit interview N34–N35 | Headroom/saturation restated with factory/wolf tradeoff |
| Somogyi air pump | Explicit pistonic monopole = pump |
| Gore Packs 2/3/5/7 | Wolves, \(Y\), side-mass cousins of ETS |
| MB Sound corpus | TPC ≠ panel workbook SOP — cross-link culture only |

### Nicoletti tonewood webinar — what it adds (this intake)

| Theme | Takeaway |
|-------|----------|
| Parameters | \(\rho\) (impedance + bridge EQ); \(E\); Schelleng SRC (density cubed); orthotropy (\(E_L\gtrsim10 E_T\)); Q/damping |
| Density lesson | Higher \(E\) does **not** compensate denser spruce via thinner plate (PRT scatter + sheet sims) |
| Metrology | Prefer FFT (REW + UMIK/miniDSP; Caldersmith nodes/antinodes) over static deflection; Lucchi inadequate for damping |
| Gore link | Explicit **vibrational stiffness** (Gore 2011/13) → target thickness/mass/SRC; calibrate to side wood |
| Build | Top-on-sides in fixed mold; pretune monopole (e.g. 220→190) without moving dipoles; stage Hz are maker-specific |
| Finish | ETS example 200 g ≈ 5 Hz; customer sheet: FRF, \(Y\), equiv. mass, main modes |
| Wolves | Search bands air ~90–120 / monopole ~170–220 Hz; small mass/pins/putty; can’t erase resonances |

| Prior / related | Intersection |
|-----------------|--------------|
| G-N01 | **Partial** — REW named (N80) |
| Gore Design/Build | Vibrational stiffness canon cited by Nicoletti |
| TPC / kit packs | Complementary plate vs guitar-kit tooling |
| Somogyi deflection | Different purpose/stage than preferred FFT plate \(E\) |

**Open Nicoletti blockers:** G-N02 (kit δ), G-N10/G-N21–23 (sheet/SRC/targets), G-N15–17, G-N08; confirm ASR “50 GPa” (G-N22).

---

## Shared classification legend

| Tag | Meaning |
|-----|---------|
| **EP** | Established principle |
| **EO** | Empirical observation |
| **TG** | Trevor Gore recommendation / practice |
| **RO** | Robbie O’Brien shop practice / on-camera thresholds |
| **IS** | Irvin/Ervin Somogyi method (as attributed in source) |
| **AP** | Apprentice / builder deviation |
| **GN** | Giuliano Nicoletti method (as attributed in source) |
| **MB** | Maderas Barber kit / presentation practice |
| **MW** | Michael Watts / player-facing framing |
| **OH** | Open hypothesis / taste / opinion |
