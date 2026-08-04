# Annotated Engineering Lecture Notes  
## Measuring Monopole Mobility (O’Brien tip / Gore method)

**Presenter:** Robbie O’Brien (O’Brien Guitars / Luther Academy)  
**Method origin:** Trevor Gore — term “monopole mobility” and \(Y = 1/\sqrt{km}\) framework  
**Scope:** Definition, SI-safe formulas, deflection-jig stiffness, uncoupled-top frequency, effective mass, responsiveness thresholds, tooling ecosystem  
**Companion:** Shop Talk #20 P09–P11 (mobility in the priority stack; bridge changes \(k\) and \(m\))  
**Processing rule:** Preserve the **measurement sequence** and flag **unit hazards** so Toolbox does not ship a silently wrong calculator.

---

## 0. Session architecture

Short bench tip:

1. Define monopole mobility (responsiveness / average admittance)  
2. State \(Y = 1/\sqrt{k m}\)  
3. Measure **stiffness \(k\)** with 1 kg load on a deflection jig  
4. Measure **uncoupled monopole frequency \(f\)** (soundhole plugged)  
5. Infer **effective mass \(m\)** from the spring–mass relation  
6. Compute \(Y\); interpret against steel-string / classical thresholds  
7. Point to Carrico spreadsheet + upcoming Luther Academy apps  

---

## 1. Definition

### 1.1 What monopole mobility indicates  
**Timestamps:** ~0:09–0:38  

Monopole mobility is an indicator of how **responsive** the guitar soundboard is. It is a calculation that approximates **average admittance**, often denoted \(Y\): how much **velocity** (and hence sound) you get in the soundboard from the **force** of the oscillating strings.

Robbie states the **term was invented by Trevor Gore**.

| Field | Value |
|-------|-------|
| Classification | **TG** term/framework; admittance interpretation **EP** |
| Link to ST#20 | Same \(1/\sqrt{km}\) stated in Shop Talk; here it becomes a **lab number**, not only a qualitative lever |
| Toolbox destination | **DOC** + **MEAS** — first-class quantity distinct from “monopole frequency” |
| Caveat | Responsiveness ≠ “always louder is better”; ST#20 still ranks **modal placement** co-equal (wolves) |

**Point ID:** M01  

---

## 2. Core formulas

### 2.1 Mobility  
**Timestamps:** ~0:54–1:08, ~1:25–1:35, ~6:46–7:00  

\[
Y = \frac{1}{\sqrt{k\, m}}
\]

- \(Y\) — monopole mobility (admittance-like)  
- \(k\) — stiffness  
- \(m\) — effective mass of the soundboard  

Higher \(Y\) ⇒ more responsive instrument (**RO** / **TG** as presented).

| Field | Value |
|-------|-------|
| Classification | **EP** / **TG** |
| Equivalent form | With \(m = k / (2\pi f)^2\), \(Y = 2\pi f / k\) — useful for spreadsheet checks |
| Toolbox destination | **EMP** calculator only with locked unit profile (see §6) |

**Point ID:** M02  

---

### 2.2 Force from the 1 kg test mass  
**Timestamps:** ~1:38–2:12  

- Effective mass of the soundboard measured in **kilograms**  
- Stiffness in **newtons per metre** of deflection  
- Test load: **exactly 1 kg**  
- \(F = m a = 1\,\mathrm{kg} \times 9.81\,\mathrm{m/s^2} = 9.81\,\mathrm{N}\)

| Field | Value |
|-------|-------|
| Classification | **EP** |
| Shop practice | Jig includes a 1 kg weight (**RO**) |

**Point ID:** M03  

---

### 2.3 Stiffness from deflection  
**Timestamps:** ~2:14–3:44  

\[
k = \frac{F}{\delta}
\]

Demo (as spoken on tip): deflection **27 mm** under 1 kg.

> **SOURCE-SPOKEN ONLY — not a canonical physical benchmark.**  
> Repo-wide blocker: [`../CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md`](../CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md) (**G-R01** / **G-M09**). Pack 5 ~0.15 mm and Nicoletti ~0.01–0.15 mm class contradict 27 mm for finished tops. Treat 27 mm as **transcription-dependent / ASR-risk**. The SI walkthrough below is only to show unit conversion on the *spoken* figure — **do not ship 27 mm as a lab default.**

**SI-safe computation on the spoken figure (illustrative only):**

\[
\delta = 0.027\,\mathrm{m},\quad
k = \frac{9.81\,\mathrm{N}}{0.027\,\mathrm{m}} \approx 363\,\mathrm{N/m}
\]

**Verbal hazard in the tip:** “\(k\) equals the force… 1 kilo… divided by the deflection… 27.” That phrasing invites dividing `1/27` or `9.81/27` **without converting mm→m**. Any implementation must **force millimetres → metres** (or use an explicit N/mm profile end-to-end) — and must not accept 27 mm as physical truth until **G-R01** closes.

Measurement technique (**RO**):

1. Zero digital caliper / dial indicator on the monopole mobility jig  
2. Place 1 kg in the cup on the indicator  
3. Read deflection in **millimetres**  
4. Optional cross-check: load → zero → unload → read; average if needed  

| Field | Value |
|-------|-------|
| Classification | **EP** formula; **RO** jig SOP; unit warning **KB**-critical |
| Hardware | Deflection jig by Dan Langhofer (Carrico / carico.com as spoken) — link in video description |
| Toolbox destination | **LAB** step “measure δ under 1 kg at bridge/monopole point”; **NO-CALC** without unit lock |

**Point ID:** M04  

---

### 2.4 Effective mass from uncoupled frequency  
**Timestamps:** ~3:46–4:07  

Spring–mass resonator:

\[
f = \frac{1}{2\pi}\sqrt{\frac{k}{m}}
\quad\Rightarrow\quad
m = \frac{k}{(2\pi f)^{2}}
\]

(Robbie: inversion of \( \frac{1}{2\pi}\sqrt{k/m} \).)

| Field | Value |
|-------|-------|
| Classification | **EP** |
| Requires | \(k\) from deflection **and** uncoupled monopole \(f\) from plugged-hole tap |
| Caveat | \(f\) must be the **uncoupled top** peak — not closed-box A0 / T(1,1)₂ coupled peaks |

**Point ID:** M05  

---

## 3. Measuring uncoupled monopole frequency

### 3.1 Why plug the soundhole  
**Timestamps:** ~4:14–4:37  

Measure the **uncoupled monopole frequency** so the top is **not influenced by the resonant frequency of the box or the back**.

Methods shown:

1. Loosen strings; seat an old **yogurt cup** (or similar) in the soundhole — snug, no rattle  
2. Or use a dedicated **soundhole plug** (Jeff Nor) that slides under the strings without loosening  

| Field | Value |
|-------|-------|
| Classification | **TG**/**RO** measurement boundary condition |
| Link to ST#20 | Same idea as P01 (plug hole → isolate uncoupled top) |
| Toolbox / Tap Tone | Mandatory metadata: `soundhole_plugged=true`, mode role=`uncoupled_monopole` |

**Point ID:** M06  

---

### 3.2 Capture tooling (Guitar Tap)  
**Timestamps:** ~4:52–6:18  

- App: **Guitar Tap** (David Smith, Oregon)  
- Free on PC; Mac App Store nominal fee (Apple distribution)  
- Also iPhone / iPad  
- Onboard mic OK; USB mic optional — Robbie reports both accurate  
- Excitation: fleshy thumb tap, or impact hammer (Simone & Martino / Hub of Acoustics, Italy)  
- Demo reading: **180.7 Hz** uncoupled top  

| Field | Value |
|-------|-------|
| Classification | **RO** toolchain; frequency value **EO** (one guitar) |
| Tap Tone Pi role | Preferred capture authority for Toolbox users; Guitar Tap remains valid shop path |
| Other uses mentioned | Brace/soundboard material, thickness helpers (**RO** product scope) |

**Point ID:** M07  

---

## 4. Compute and interpret \(Y\)

### 4.1 Assemble the number  
**Timestamps:** ~6:43–7:28  

With \(k\) and \(m\), compute \(Y = 1/\sqrt{k m}\).  
Demo result stated: **31.3** for that guitar (“off the charts”).

| Field | Value |
|-------|-------|
| Classification | **RO** demo result |
| Unit integrity | See §6 — treat 31.3 as a **toolchain score** until the Carrico/Gore spreadsheet unit profile is replicated exactly |
| SI cross-check | With δ=27 mm, f=180.7 Hz, pure SI \(Y = 2\pi f/k \approx 3.13\,\mathrm{s/kg}\) — **~10× below** the spoken 31.3, so do not assume raw SI equals video thresholds |

**Point ID:** M08  

---

### 4.2 Responsiveness thresholds (as stated)  
**Timestamps:** ~7:02–7:36  

| Instrument family | Threshold (as spoken) | Meaning |
|-------------------|----------------------|---------|
| Acoustic / steel-string | Above **~11–12** | Starting to enter responsive range (**RO**) |
| Classical | Above **~20** | Starting responsive realm (**RO**) |
| Gore (quoted) | Above about **20** | Very responsive instrument (**TG** via Robbie) |
| Demo guitar | **31.3** | “Basically off the charts” (**RO**) |

| Field | Value |
|-------|-------|
| Classification | **RO**/**TG** empirical bands — **not** universal physics constants |
| Caveat | Only meaningful in the **same unit/score system** as the Gore–Carrico–Luther Academy toolchain |
| Toolbox destination | **EMP** reference bands tagged with `unit_profile_id`; never hard-code without profile |

**Point ID:** M09  

---

## 5. Tooling ecosystem mentioned

| Tool | Role | Class |
|------|------|-------|
| Carrico monopole mobility jig (+ 1 kg) | Deflection under known load | **RO** |
| Carrico downloadable spreadsheet | Plug in force, deflection, uncoupled \(f\) → \(Y\) | **RO** |
| Guitar Tap (David Smith) | Uncoupled frequency capture | **RO** |
| Soundhole plug (Jeff Nor) | Isolate uncoupled top | **RO** |
| Hub of Acoustics hammer | Controlled taps | **RO** |
| Upcoming Luther Academy apps (Trevor Gore + Rick Mallaloy / Seattle) | Four degrees of freedom, wood properties, monopole mobility, more | **RO** (announced) |

**Point ID:** M10  

---

## 6. Unit & spreadsheet integrity (critical KB)

The tip correctly names SI ingredients (N, kg, N/m) but the spoken arithmetic (“1 kilo / 27”) and the reported **31.3** vs pure-SI **~3.13** show that **shop scores may use a scaled or spreadsheet-specific profile**.

**Rules for Luthier’s Toolbox:**

1. Implement mobility as a **guided lab** that records: \(F\), \(\delta\) (mm), \(f\) (Hz), jig ID, plug method, bridge present?  
2. Ship one explicit `unit_profile` matching Carrico/Gore spreadsheet outputs before showing 11/12/20 thresholds.  
3. Also expose pure SI \(Y\) [s/kg] for Tap Tone / science interop — **do not mix threshold tables across profiles**.  
4. Prefer \(Y = 2\pi f / k\) as a numeric checksum once \(k\) is in N/m.  
5. **NO-CALC** from wood species alone — this is a **measured** quantity.

**Point ID:** M11  

---

## 7. Measurement workflow (canonical SOP)

> **Fidelity:** outline SOP only. Everything *not* specified here (jig load point, support geometry, peak-ID rules, spreadsheet unit profile, etc.) is inventoried in [`GAPS_NOT_RECORDED.md`](./GAPS_NOT_RECORDED.md). Do not invent those details.

1. Mount guitar in monopole mobility **deflection jig** (bridge/load point per jig design — **G-M01/G-M02 unknown**).  
2. Zero indicator; apply **1.000 kg**; read \(\delta\) in mm (repeat load/unload average if needed).  
3. Compute \(k = 9.81 / (\delta_{\mathrm{mm}}/1000)\) [N/m] for SI path.  
4. **Plug soundhole** (cup or plug); ensure no rattle.  
5. Capture **uncoupled monopole** \(f\) (Guitar Tap / Tap Tone Pi / equivalent — **which peak: G-M17**).  
6. \(m = k / (2\pi f)^2\).  
7. \(Y = 1/\sqrt{k m}\) (or \(2\pi f/k\)); map through chosen unit profile to score (**profile: G-M13**).  
8. Interpret vs steel (~11–12) / classical (~20) bands **only under that profile** (**G-M15**).  
9. Record whether bridge/strings/neck configuration matches intended “finished responsiveness” claim (ST#20: bridge changes \(k\) and \(m\) significantly).

| Field | Value |
|-------|-------|
| Classification | Synthesis of **RO** steps + **EP** formulas + ST#20 stage caveat |
| Toolbox destination | **LAB** `Monopole Mobility Measurement` |
| Gaps | [`GAPS_NOT_RECORDED.md`](./GAPS_NOT_RECORDED.md) |

**Point ID:** M12  

---

## 8. Common misconceptions

| Misconception | Correction | IDs |
|---------------|------------|-----|
| Monopole frequency alone = mobility | Need \(k\) (or equivalent) as well | M02, M05 |
| Coupled box peak is fine for \(f\) | Must use **uncoupled** (plugged) top | M06 |
| Deflection mm can drop straight into \(F/\delta\) with \(F\) in N | Convert to metres (or commit to N/mm profile) | M04, M11 |
| Video thresholds apply to raw SI \(Y\) | Likely spreadsheet/score profile — calibrate first | M08–M09, M11 |
| Higher \(Y\) overrides modal placement | ST#20 priority stack: resonances off scale tones **and** high \(Y\) | M01 |
| Putty mass preload substitutes for finished \(k\) | ST#20: glued bridge adds stiffness; mobility stage must match build stage | (ST P07–P08) |

---

## 9. Compact point catalog

| ID | Point | Category | Class |
|----|-------|----------|-------|
| M01 | \(Y\) ≈ average admittance / responsiveness; Gore term | Theory | TG/EP |
| M02 | \(Y=1/\sqrt{km}\); higher ⇒ more responsive | Theory | EP/TG |
| M03 | 1 kg → 9.81 N test force | Measurement | EP |
| M04 | Jig deflection → \(k=F/\delta\); mm→m hazard | Measurement | EP/RO |
| M05 | \(m=k/(2\pi f)^2\) from uncoupled \(f\) | Theory | EP |
| M06 | Plug hole to isolate uncoupled top | Measurement | TG/RO |
| M07 | Guitar Tap (or equivalent) capture; demo 180.7 Hz | Measurement | RO/EO |
| M08 | Demo score 31.3; verify unit profile | Experimental | RO |
| M09 | Thresholds ~11–12 steel, ~20 classical / Gore “very responsive” | Design rule | RO/TG |
| M10 | Carrico jig/sheet; Luther Academy apps ecosystem | Tooling | RO |
| M11 | Unit-profile lock before thresholds | KB / Validation | EP/KB |
| M12 | End-to-end SOP + stage metadata | Build sequence | RO/TG |

---

## 10. Relationship to prior packs

| Prior pack | Relationship |
|------------|----------------|
| Shop Talk P09–P11 | Stated formula + bridge effect; **this pack is the measurement lab** |
| Shop Talk P01 | Plugged-hole uncoupled top — reused here for \(f\) |
| Wolf Notes W05–W08 | Modal clearance remains mandatory; high \(Y\) does not excuse a wolf |
| Series gap C1 | This pack is the primary source document to close mobility |

---

*See `CROSSWALK_TOOLBOX.md` for implementation mapping.*
