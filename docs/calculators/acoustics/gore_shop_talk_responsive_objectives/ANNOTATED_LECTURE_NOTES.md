# Annotated Engineering Lecture Notes  
## Shop Talk — Responsive Guitar Objectives (Gore PowerPoint + Q&A)

**Host:** Robbie O’Brien  
**Guest:** Trevor Gore (Sydney; mobile data link)  
**Form:** Prepared PowerPoint then rapid Q&A  
**Scope:** Build objectives, mobility measurement (jig demo), wolf avoidance table, musicality/peak density, intonation, SRC/Q, construction/voicing Q&A  
**Excluded:** Giveaways, likes prompts, connectivity complaints  
**Critical cross-link:** Mobility Pack 3 demo δ≈**27 mm** vs this session δ≈**0.15 mm** under ~1 kg — see gaps register (unit/profile calibration evidence).

---

## 0. Session architecture

Gore’s stated objective stack for a new guitar (playability & structural integrity assumed):

1. **Right monopole mobility** — not necessarily *maximum*  
2. **Evenness** — major resonances off scale tones (no wolves)  
3. **Musicality** — high FRF peak density (“alluring”) + accurate equal-temperament intonation (nut + saddle)

This is the clearest single-session articulation of the priority stack referenced across Packs 1–4.

---

## 1. Build objectives framework

### 1.1 Three acoustic objectives  
**Timestamps:** ~10:29–12:13  

| Objective | Meaning (as stated) |
|-----------|---------------------|
| Right monopole mobility | Sensitivity / potential loudness; “right” ≠ always highest |
| Evenness | Avoid wolf notes — place major resonances off scale tones |
| Musicality | Alluring sound via **high peak density** in FRF + correct ET intonation |

Assumed (not covered): setup/playability; structural integrity.

| Field | Value |
|-------|-------|
| Classification | **TG** design philosophy |
| Toolbox destination | **RULE** / product north-star for Acoustics guided workflows |
| Link | ST#20 priority stack; Mobility “higher=better” tempered by “right not necessarily high” |

**Point ID:** R01  

---

## 2. Monopole mobility (presentation depth)

### 2.1 Term & hybrid measurement  
**Timestamps:** ~13:07–14:20  

Gore coined **monopole mobility**: hybrid, easy, repeatable. A more “correct” mobility measurement exists but is harder / more math-intense (not detailed).

Uses the **monopole** because it is the most effective sound radiator — proxy for overall responsiveness / sensitivity / potential loudness.

| Field | Value |
|-------|-------|
| Classification | **TG** term; radiator rationale **EP**/TG |
| Gap | Alternate “more correct” method unnamed |

**Point ID:** R02  

---

### 2.2 Measurement SOP (PowerPoint jig)  
**Timestamps:** ~14:28–17:15  

**Need:** equivalent stiffness \(K\) and equivalent mass \(M\) of the monopole mode.

**Stiffness kit:** beam across guitar; dial indicator or **tire tread depth gauge**; load through gauge onto **bridge**; platform holds ~**1 kg lead shot**.

- Convert load to newtons: 1 kg ≈ **9.81 N** (or ~10 N).  
- Measure displacement \(s\); \(K = P / s\) in N/mm or N/m.  
- **Demo reading: ~0.15 mm** deflection under that load.

**Mass:** uncoupled monopole frequency — **block soundhole** (uncouples Helmholtz; also uncouples back). Tap; measure \(f\) (Visual Analyzer or any frequency tool).

\[
f \propto \frac{1}{2\pi}\sqrt{\frac{K}{M}}
\quad\Rightarrow\quad
M = \frac{K}{(2\pi f)^{2}}
\quad\Rightarrow\quad
Y = \frac{1}{\sqrt{K M}}
\]

| Field | Value |
|-------|-------|
| Classification | **TG**/**EP** SOP |
| **Conflict** | Pack 3 tip stated **27 mm** under 1 kg and score 31.3; here **0.15 mm** — ~180× stiffer reading. Treat Pack 3 27 mm as **ASR-risk / unresolved** until spreadsheet calibration (G-M09 / G-R01). |
| Toolbox destination | **LAB**; prefer this δ magnitude for realism sanity checks |

**Point ID:** R03  

---

### 2.3 Raising \(Y\) while holding target frequency  
**Timestamps:** ~17:15–18:31  

To raise mobility: decrease \(K\) and/or \(M\). But resonant frequency depends on \(K/M\) relationship — must lower them **in proportion** to raise \(Y\) while staying on target frequency.

| Field | Value |
|-------|-------|
| Classification | **EP**/**TG** |
| Toolbox destination | **RULE** in voicing lab — coupled \(Y\) + \(f\) targets |

**Point ID:** R04  

---

### 2.4 Good / typical \(Y\) numbers + “conspiracy against guitarists”  
**Timestamps:** ~18:37–20:42  

| Family | Typical | Really good |
|--------|---------|-------------|
| Classical | ~**20** | ~**30s** (e.g. ~32); historical Spanish makers limited without CF |
| Steel-string | ~**10–12** | low **20s** (stiffer / more load) |

Commercial “best samples” still leave capability on the table vs deliberate high-\(Y\) builds — Gore’s phrase: **conspiracy against guitarists** (High Street vs what’s possible).

| Field | Value |
|-------|-------|
| Classification | **TG**/**EO** bands; rhetoric **TG** |
| Link | Pack 3 M09 thresholds — **same ballpark**; still need unit_profile lock |
| Caveat | R01: aim **right** \(Y\), not max (banjo risk — R20) |

**Point ID:** R05  

---

## 3. Evenness — wolf avoidance (table method)

### 3.1 Modes that matter  
**Timestamps:** ~20:48–21:44  

Major low-order modes: **T111, T112, T113** (air-driven, main top, top+back) — three monopole-family peaks. Keep off scale tones.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Link | Wolf pack; ST#20 P03–P05 |

**Point ID:** R06  

---

### 3.2 Mid-scale selection table (±50 cents)  
**Timestamps:** ~21:44–22:35  

Example: A = **110 Hz**; 50 cents off → **~107** or **~113 Hz**. Choose mode frequencies from **outer columns** (furthest from scale tones).

| Field | Value |
|-------|-------|
| Classification | **TG** (operationalizes ½-semitone / mid-scale) |
| Toolbox destination | **RULE** + scale-tone grid UI (Wolf W05) |

**Point ID:** R07  

---

### 3.3 Mixing constraints  
**Timestamps:** ~22:59–23:39  

- Don’t totally mix-and-match; e.g. avoid **exact octave** between T111 and T112 (**not** 90/180; prefer **95/180** or **90/190**).  
- Good rule of thumb: **four semitone** separation T112–T113.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Link | ST#20 / ST#25 four-semitone rule |
| Toolbox destination | **RULE** validators on target sets |

**Point ID:** R08  

---

## 4. Musicality

### 4.1 Peak density (Matthews & Kohut)  
**Timestamps:** ~23:51–25:07  

Alluring sound correlates with **high peak density** in FRF. Violin research (**Matthews and Kohut**): **20–30 peaks** up to **5 kHz**, irregularly spaced w.r.t. harmonics → most subjectively pleasing; works OK for guitars too. Cram peaks especially below ~1 kHz (less control above). “Irregular vs harmonics” = don’t park on scale tones.

| Field | Value |
|-------|-------|
| Classification | **EO** (cited research) + **TG** transfer to guitars |
| ASR | Names as spoken; verify spelling in literature (often **Mathews**; coauthor verify) |
| Toolbox destination | **EMP** peak-count metric 0–1 kHz / 0–5 kHz |

**Point ID:** R09  

---

### 4.2 Live back → tone; non-live → volume  
**Timestamps:** ~25:07–25:37; ~1:02:57–1:03:41  

Live back → more peaks / tone; non-live doesn’t rob top energy → louder / volume. Reiterated in Q&A as “golden” nutshell.

| Field | Value |
|-------|-------|
| Classification | **TG** (consistent Packs 1 & 4) |
| Toolbox destination | **RULE** / KB |

**Point ID:** R10  

---

### 4.3 Nut + saddle compensation  
**Timestamps:** ~25:39–28:26; ~28:31–29:56; ~31:38–33:09  

- Research (~1999, authors named on slide — not clear in ASR) preferred in-tune guitars.  
- Open + 12th perfect still leaves frets **1–3 sharp** (wider spans → more press deflection → tension rise).  
- Nut + saddle together; Gore always uses both.  
- Nut move toward frets → drop open tension → **flatter on every fret** by same cents (~**1 mm ≈ 3 cents** all frets).  
- Quick/dirty: take saddle-only total compensation (e.g. 4 mm on 6th) → **half on nut, half on saddle**. Not as good as book’s full method (~20-page chapter) but “not a bad approximation.”  
- Full method: max error ~**0.5 cent** (as stated).

| Field | Value |
|-------|-------|
| Classification | **EP**/**TG**; half-split **TG** heuristic; 1 mm→3¢ **TG**/EO |
| Toolbox destination | Existing nut/saddle calcs — add half-split helper + global-cents copy |
| Gap | 1999 citation names from slide |

**Point ID:** R11  

---

## 5. Wood selection — SRC and Q

### 5.1 Sound radiation coefficient  
**Timestamps:** ~33:24–35:17  

\[
\mathrm{SRC} \propto \sqrt{\frac{E}{\rho^{3}}}
\]

(Young’s modulus over density cubed, square root — as stated.) Good responsiveness indicator among wood-quality methods.

**Use by guitar type:**

| Intent | SRC preference |
|--------|----------------|
| Classical / max volume | High SRC (“best” wood) |
| Fingerpicking steel | Often high SRC |
| Strumming / more headroom | Lower SRC |
| Stage / pickup guitar | Avoid high SRC — “big microphone,” feedback |

| Field | Value |
|-------|-------|
| Classification | **EP**/Schelleng-class index + **TG** selection policy |
| Toolbox destination | Materials `radiation_ratio` / scorer — wire to **build-intent** presets |
| Link | ST#20 SRC vocab hazard (not a modal frequency) |

**Point ID:** R12  

---

### 5.2 Q / damping — hearability split  
**Timestamps:** ~35:17–37:48  

Gore: many hear high-Q vs low-Q difference (important to him); many cannot. Blinded anechoic listening with **Pacific Rim Tonewoods** + **University of Dresden**: **no significant detectable difference** between low-Q and high-Q guitars (paper written/submitted/likely accepted). Video on Gore site: three guitars (B/R/Y), same FRF, only top damping differs (player named in ASR as “marav tadic” — verify).

| Field | Value |
|-------|-------|
| Classification | **EO** (listening study) + **TG** personal weighting; special-guitar damping **OH** (R22) |
| Toolbox destination | **KB** / EMP — do not rank wood by Q alone as universal; optional cognoscenti flag |
| Gap | Paper citation when published |

**Point ID:** R13  

---

## 6. Construction & voicing Q&A

### 6.1 Bridge mass (~16 g) / dread / headroom  
**Timestamps:** ~38:19–39:48  

Book ~**16 g** steel-string bridge — consider whole system. Bridge is stiffest/heaviest brace: ↑stiffness → ↑T112; ↑mass → ↓T112. Heavier bridge → more headroom but need more structure stiffness to keep frequencies → \(K\) and \(M\) up → \(Y\) down. Responsive → low bridge mass; headroom → heavier bridge / lower \(Y\).

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | **RULE** bridge-mass vs mobility trade; acoustic_bridge_calc link |

**Point ID:** R14  

---

### 6.2 Lower harmonic / transverse bar (classical)  
**Timestamps:** ~40:05–42:22  

Shaving lower harmonic bar (below soundhole) **rapidly lowers T112** — useful tuning if fan bracing still controls distortion. Mainly T112; small coupled effects on T111/T113; T112 drops faster than T113 → separation increases; air drops slightly.

| Field | Value |
|-------|-------|
| Classification | **TG**/**EO** |
| Toolbox destination | **LAB** mode-selective edit menu |

**Point ID:** R15  

---

### 6.3 Falcate tertiary braces  
**Timestamps:** ~42:29–44:02  

Tertiaries = straight braces (horizontal above bridge patch; diagonal in lower bout). Provide **lateral stiffness**; lower diagonal helps **bellying** control. Primaries/secondaries take bridge torque (tension × saddle height).

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | **KB** falcate anatomy (geometry still absent) |

**Point ID:** R16  

---

### 6.4 One dead classical string  
**Timestamps:** ~45:50–46:15  

If **one** string: almost certainly a **dead string**, not bracing. Multiple strings → different answer.

| Field | Value |
|-------|-------|
| Classification | **TG** diagnostic heuristic |
| Toolbox destination | **KB** troubleshooting |

**Point ID:** R17  

---

### 6.5 Falcate pattern vs body width  
**Timestamps:** ~48:42–49:34  

Same layout essentially **390 mm down to 340 mm** lower-bout width; shuffle for bridge position; keep brace **segments about even** in size.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Link | ST#25 cube-rule for **brace size** when scaling up (dread) — pattern vs section size |

**Point ID:** R18  

---

### 6.6 Higher modes / Meyer / first-string support  
**Timestamps:** ~49:40–53:18  

Only higher body contribution that “makes a whole lot of difference”: Helmholtz **first partial** ~**350 Hz**, heard when coupled with **long dipole**. Meyer “third resonance” reconstruction (same as ST#25): long dipole under his excitation. Gore prefers **cross-tripole** as stronger radiator for classical first string.

| Field | Value |
|-------|-------|
| Classification | **TG** (consistent S16–S17) |
| Toolbox destination | **KB** |

**Point ID:** R19  

---

### 6.7 When to trust FRF: fully strung  
**Timestamps:** ~53:53–55:05  

Ultimate measurements: **fully strung, ready to play**. Intermediates guide progress. String **end mass** moves frequencies on responsive guitars — account when estimating final.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | **MEAS** stage `strung_playable` as acceptance; intermediates tagged |

**Point ID:** R20a  

---

### 6.8 Spectrogram build progression (example)  
**Timestamps:** ~55:05–57:04  

Critical stages shown:

1. **Boxed** — no bridge, no neck — T111/112/113 peaks  
2. **Edge thin** — frequencies reduce; more T111 activity  
3. **Bridge + neck + strings** — frequencies move down again (example **92 / 173 / 224**)  
4. **Side mass** to hit targets (example toward **91 / 170 / 224**; spoken ideal ~170 for middle peak)  
5. Finished: frequencies off scale tones  

Map the path so final strung+weighted condition lands on targets.

| Field | Value |
|-------|-------|
| Classification | **TG**/**EO** (one build path) |
| Toolbox destination | **LAB** voicing timeline + EMP stage deltas |
| Link | ST#25 side mass; Mobility stage metadata |

**Point ID:** R20  

---

### 6.9 Too responsive / brassy → add trial mass  
**Timestamps:** ~57:13–58:58  

Over-responsive ≈ “building a banjo.” Trial: **poster putty on bridge**; e.g. drop T112 **170 → 160** for warmer/bassier; passing **~165** hits scale tone / wolf — watch it. (Contrast Pack 1 putty ≠ glued bridge for **predicting finished \(k\)**; here putty is intentional **mass trial** only.)

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | **LAB** “mellow via mass” with wolf warnings |
| Link | R01 “right not max” mobility |

**Point ID:** R21  

---

### 6.10 Air speed / altitude  
**Timestamps:** ~59:04–1:01:04  

Sea level vs Parker **~6000 ft**: air density & speed of sound change → resonances shift (mainly air / Helmholtz, couples to all). 4DOF model with NASA classmates matched observed shift.

| Field | Value |
|-------|-------|
| Classification | **EP**/**EO**/**TG** |
| Toolbox destination | **EMP**/climate or altitude correction in Helmholtz/coupled models |
| Gap | Coefficient table / UI |

**Point ID:** R22  

---

### 6.11 Small body targets  
**Timestamps:** ~1:01:11–1:02:45  

180 Hz top possible on ~350 mm lower bout (not desperately small). Gore small classical **340 mm**: typically **~90 Hz air / ~190 Hz T112**. Keep **four semitones** T112–T113; T113 too close → muddy. Small guitars: floppier panels to lower air; harder as size shrinks.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | **EMP** body-style targets |

**Point ID:** R23  

---

### 6.12 Soundhole diameter vs T112  
**Timestamps:** ~1:03:53–1:04:42  

Soundhole mainly moves **T111** (smaller → lower air). T112 changes little via coupling. To move T112, operate on the **top** directly.

| Field | Value |
|-------|-------|
| Classification | **TG**/**EP** |
| Link | Wolf W06 air levers; mode-selective skill |

**Point ID:** R24  

---

### 6.13 Build with the end in mind; 99% vs special  
**Timestamps:** ~1:04:49–1:06:51  

Periodic spectrograms toward frequency + mobility targets → “**99% guitar**.” Beyond that, rare special instruments (~1 in 100,000) — hard to explain; Gore suspects **damping** (can measure much else). Getting major resonances + mobility right already yields a really good guitar.

| Field | Value |
|-------|-------|
| Classification | **TG**; special-guitar damping **OH** |
| Toolbox destination | **KB** expectations management; don’t overclaim Q optimization |

**Point ID:** R25  

---

## 7. Compact point catalog

| ID | Point | Class |
|----|-------|-------|
| R01 | Objectives: right \(Y\), evenness, musicality (+ intonation) | TG |
| R02 | Monopole mobility coined; monopole = best radiator proxy | TG |
| R03 | Jig SOP; ~0.15 mm @ ~1 kg demo; plug hole; \(Y=1/\sqrt{KM}\) | TG/EP |
| R04 | Lower \(K\) & \(M\) in proportion to raise \(Y\) at fixed \(f\) | EP/TG |
| R05 | Classical ~20/30s; steel ~10–12/low 20s; “conspiracy” | TG/EO |
| R06 | T111/112/113 off scale tones | TG |
| R07 | ±50¢ outer-column target table | TG |
| R08 | No exact T111–T112 octave; 4 semitone T112–T113 | TG |
| R09 | 20–30 peaks to 5 kHz (Matthews/Kohut); irregular vs harmonics | EO/TG |
| R10 | Live back = tone; non-live = volume | TG |
| R11 | Nut+saddle; 1 mm≈3¢; half-split heuristic | TG/EP |
| R12 | SRC=\(\sqrt{E/\rho^3}\); choose by guitar intent | EP/TG |
| R13 | Q: some hear / blind tests null; paper + video | EO/TG |
| R14 | Bridge mass vs headroom vs \(Y\) (~16 g book) | TG |
| R15 | Harmonic bar shave → T112 down | TG |
| R16 | Falcate tertiaries = lateral / belly control | TG |
| R17 | One dead string → replace string | TG |
| R18 | Falcate pattern ~340–390 mm; even segments | TG |
| R19 | Meyer long dipole; prefer cross-tripole | TG |
| R20a | Final FRF = fully strung; string-end mass matters | TG |
| R20 | Spectrogram path boxed→edge→strung→side mass | TG/EO |
| R21 | Too bright: trial mass on bridge; watch wolves | TG |
| R22 | Altitude/air properties shift modes; 4DOF | EP/EO |
| R23 | Small body ~90/190 classical example | TG |
| R24 | Soundhole ≈ T111 lever, not T112 | TG |
| R25 | End-in-mind → 99% guitar; ultra-special may be damping | TG/OH |

---

## 8. Relationship to prior packs

| Prior | This session |
|-------|----------------|
| Pack 3 mobility tip | Same formulas; **δ conflict 27 mm vs 0.15 mm**; thresholds align (~20 / 10–12) |
| Pack 2 wolves | Outer-column ±50¢ table; octave-avoid rule |
| Pack 1 ST#20 | Objectives formalized; peak density quantified; nut 1 mm≈3¢ |
| Pack 4 ST#25 | Side mass in spectrogram path; Meyer/cross-tripole; live back; SRC intent policy new |

---

*See `CROSSWALK_TOOLBOX.md` and `GAPS_NOT_RECORDED.md`.*
