# Annotated Engineering Lecture Notes  
## Trevor Gore + Rick Mallaloy — Shop Talk Live Stream #51

**Host:** Robbie O’Brien (Luther Academy / O’Brien Guitars)  
**Guests:** Trevor Gore; Rick Mallaloy (Celestial Instruments)  
**Scope:** Substantive teaching + tool demo; sponsors, giveaways, class logistics lightly noted only where they affect toolchain (Carrico jig, 1 kg weight)  
**Companions:** Pack 3 (mobility measurement); Pack 5 (objectives / altitude / 4DOF); Pack 2 (wolves); Pack 4/7 (side mass / 4DOF origin); Pack 6 (analysis course — still partial)

---

## 0. Session architecture

Remote livestream (~1 hour). Highest-density themes:

1. **Gore ~2008 program** — put resonances in the right place + get responsiveness (monopole mobility) right; material properties → plate thickness + brace design → measure → correct  
2. **Spreadsheets → Mallaloy web apps** — same math, usable by non-spreadsheet luthiers  
3. **Five-tool suite** end-to-end demo (FFT → plate thickness → mobility → 4DOF + environment → flexural rigidity)  
4. **4DOF origin** restated (3DOF inadequate; sides = rest-of-structure mass)  
5. **\(Y\) vs tone** independence; wolf **played-note** visualization; pre-war Martin question left open  

---

## 1. Gore program motivation (~2008 → course → apps)

### 1.1 Two things that really mattered  
**Timestamps:** ~13:29–14:16  

Gore wanted more rigor (~2008). Things that mattered:

1. **Resonances in the right place** — govern timbre  
2. **Responsiveness** — measured as **monopole mobility**

| Field | Value |
|-------|-------|
| Classification | **TG**/**EP** (matches Pack 5 objective spine) |
| Toolbox destination | **RULE** guided voicing priority |
| Link | Pack 5 R01; Pack 1 priority stack |

**Point ID:** A01  

---

### 1.2 Measurement → placement → correction loop  
**Timestamps:** ~14:16–15:20  

To place resonances: measure them; figure how big braces / how thick top; research → **formula for top (and back) thickness**. Build → see how close → modifications to hit original target.

| Field | Value |
|-------|-------|
| Classification | **TG** process |
| Toolbox destination | **LAB** stage gates; plate + brace tools |
| Gap | Exact thickness formula not spoken here (book / spreadsheet) |

**Point ID:** A02  

---

### 1.3 Inputs for plate thickness  
**Timestamps:** ~14:48–15:08  

Need Young’s modulus **along and across**, density of the panel, and size of the guitar you’re using it on → figure frequency it will resonate at on the guitar.

| Field | Value |
|-------|-------|
| Classification | **TG**/**EP** |
| Toolbox destination | Materials / plate-thickness calculator inputs |
| Link | Pack 6 Module C (wood modes — SOP still missing) |

**Point ID:** A03  

---

### 1.4 Bracewood properties (wood or wood+CF)  
**Timestamps:** ~15:20–15:38  

Measure bracewood properties; design braces to right stiffness — wooden or wooden + carbon-fiber braces.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | Flexural rigidity / brace designer (**RM** tool #5) |

**Point ID:** A04  

---

### 1.5 Condense complex analysis → simple formulas + spreadsheets  
**Timestamps:** ~15:43–16:23  

Initial analysis complex; condensed to relatively simple formulas and spreadsheets historically issued at the modal tuning course.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | **KB** provenance: course spreadsheets = canonical math source |

**Point ID:** A05  

---

### 1.6 Audience beyond scientific backgrounds → Mallaloy apps  
**Timestamps:** ~16:23–17:49  

More people without math/spreadsheet skill set interested. Mallaloy took much of the maths out: still enter data; apps do hard work for brace design, material properties, top/back thickness, resonant-frequency measurement. Gore tried some tools and matched answers to original work.

| Field | Value |
|-------|-------|
| Classification | **TG** endorsement; **RM** productization |
| Toolbox destination | **KB** external free tools; do not assume Toolbox hosts these |
| Caveat | Beta; bugs shown on stream |

**Point ID:** A06  

---

## 2. Five-tool suite (Mallaloy)

### 2.1 Named tools  
**Timestamps:** ~19:37–21:44  

| # | Tool | Role (as stated) |
|---|------|------------------|
| 1 | **Four degrees of freedom (4DOF / “40 UF”) model** | Book 4DOF + **environment** (altitude/air) |
| 2 | **Plate thickness calculator** | How thick to make plates |
| 3 | **Resonance reader** | FFT-based modal resonances of plates, tops, notes; can forward modes to plate thickness (later: flexural rigidity) |
| 4 | **Monopole mobility reader/calculator** | From Carrico-style jig inputs → score + **effective stiffness** + **effective mass** (feeds 4DOF) |
| 5 | **Flexural rigidity calculator** | Explore top/braces; build custom braces; compare effective stiffnesses |

| Field | Value |
|-------|-------|
| Classification | **RM** architecture |
| Toolbox destination | **KB** tool map; integration candidates below |
| Gap | Stable URLs / version pins (**G-A01**) |

**Point ID:** A07  

---

### 2.2 Where to find them (beta packaging)  
**Timestamps:** ~19:43–20:07; ~50:23–50:49; ~51:14–51:33  

Luther Academy site → scroll to bottom → **Resources** (no main-nav tab while beta). Free to Academy (Mallaloy’s intent: benefit community, not subscription). When bugs settled, link moves to main menu.

| Field | Value |
|-------|-------|
| Classification | **RO**/**RM** |
| Toolbox destination | **KB** external links only |
| Gap | Exact page URL not spoken as a full URL |

**Point ID:** A08  

---

## 3. Resonance reader (FFT)

### 3.1 Transport + laptop mic sufficiency for frequency  
**Timestamps:** ~22:57–24:19  

Controls: record / play / stop / import / list / clear. Live preview. Demo uses **laptop microphone**. For **frequencies**, fancy mics not required (phone/laptop tuning analogy). For **Q / volume-sensitive** metrics, better mics can matter.

| Field | Value |
|-------|-------|
| Classification | **RM**/**EO** |
| Toolbox destination | **LAB** mic quality tiers by metric |
| Link | Pack 6 Module A (mic setup — SOP missing) |

**Point ID:** A09  

---

### 3.2 Plate mode labeling; transverse hardest  
**Timestamps:** ~24:19–24:57  

Plate mode dropdown; detects cross and long. **Transverse mode hardest** to measure; may need manual peak pick. Modes listed; can drag markers if wrong.

| Field | Value |
|-------|-------|
| Classification | **RM**/**EO** |
| Toolbox destination | **LAB** plate-mode picking UX |

**Point ID:** A10  

---

### 3.3 Forward to plate thickness calculator  
**Timestamps:** ~24:57–25:37  

Open plate thickness calculator from resonance reader → modes carried. Demo Pacific Rim top (not surfaced — accuracy caveat):

| Input | Value |
|-------|-------|
| Length | 542 mm |
| Width | 220 mm |
| Mass | 212 g |
| Thickness | 4.1 mm |
| Result (demo) | **~2.58 mm** target thickness |

Presets: Robbie / Trevor steel-string / Martin OM — thickness changes little between Trevor vs Robbie in demo (~2.57). Targets differ for classical and live backs.

| Field | Value |
|-------|-------|
| Classification | **RM** demo; presets **TG**/**RO** |
| Toolbox destination | Plate thickness calc; preset profiles |
| Caveat | Unsurfaced plate → not fully accurate reading |

**Point ID:** A11  

---

### 3.4 Book-matched math  
**Timestamps:** ~26:05–26:23  

Checked exhaustively against examples in Trevor’s book so math matches; Gore’s later check “seemed to work” for that reason.

| Field | Value |
|-------|-------|
| Classification | **RM** verification claim; **TG** spot-check |
| Toolbox destination | **TEST** fixture: book example corpus |
| Gap | Which edition/examples not listed on stream |

**Point ID:** A12  

---

## 4. Closed-box / instrument FFT + tone generator

### 4.1 Unfinished OM box taps  
**Timestamps:** ~27:24–29:40  

Guitar without bridge yet; air ≈ **103 Hz**, top ≈ **207 Hz**; back peak initially mislabeled — actually higher (tone-gen confirmation). Yellow window selects tap region; instrument mode vs plate mode.

| Field | Value |
|-------|-------|
| Classification | **EO** (one unfinished OM) |
| Toolbox destination | **EMP** stage = boxed, no bridge |
| Link | Pack 1 free-top / stage warnings |

**Point ID:** A13  

---

### 4.2 Built-in tone generator  
**Timestamps:** ~29:40–30:36  

Tone generator in the tool; Mallaloy uses Spark USB / Bluetooth 4″ amp. Stream could not play shared-screen audio to viewers — local confirmation only.

| Field | Value |
|-------|-------|
| Classification | **RM** practice |
| Toolbox destination | **LAB** excitation path |

**Point ID:** A14  

---

### 4.3 Overlay 4DOF on measured FRF  
**Timestamps:** ~30:36–31:16  

Can overlay dashed orange 4DOF model on spectrum; auto-solve/snap failed live → **beta bug** acknowledged.

| Field | Value |
|-------|-------|
| Classification | **RM** feature + known defect |
| Toolbox destination | Do not treat live demo as pass criteria for Toolbox 4DOF |

**Point ID:** A15  

---

### 4.4 Altitude / environment coupling (Robbie build example)  
**Timestamps:** ~31:30–32:07; ~46:00–46:24  

Guitar built with Robbie at **~6000 ft** vs brought home: not the same. Air e.g. ~93 → ~90; top also moved (~172 → ~176 in what-if narrative). Matches Pack 5 altitude theme.

| Field | Value |
|-------|-------|
| Classification | **EO**/**EP** |
| Link | Pack 5 R22; Pack 5 G-R11 |
| Toolbox destination | **EMP** environment inputs on 4DOF |

**Point ID:** A16  

---

### 4.5 Target suggestions + pickup mass  
**Timestamps:** ~32:13–32:55  

Set air target 90 / back 170 → suggestions (e.g. **+5 g** near bridge — “a lot”). Wavefile pre–K&K; K&K mics ~**3 g**; ~**1.5 g** poster putty used to dial in.

| Field | Value |
|-------|-------|
| Classification | **RM** tool behavior; **EO** mass levers |
| Toolbox destination | **LAB** mass-near-bridge suggestions; pickup mass accounting |
| Caveat | Multi-target solver buggy later in demo |

**Point ID:** A17  

---

## 5. Monopole mobility calculator → 4DOF fit

### 5.1 Defaults = Robbie-build guitar; weight 1.02 → 1.00 kg  
**Timestamps:** ~33:41–34:09  

Mobility tool defaults were the guitar Mallaloy built with Robbie. Old weight **1.02 kg**; new Carrico weights **1.00 kg** — Mallaloy updating default.

| Field | Value |
|-------|-------|
| Classification | **RM**/**RO** toolchain |
| Link | Pack 3 1 kg SOP; Pack 5 ~1 kg |
| Toolbox destination | `unit_profile` / mass calibration (**blocker** with δ conflict) |
| Gap | Confirm which mass Carrico ships vs app default history |

**Point ID:** A18  

---

### 5.2 Effective stiffness and mass from mobility  
**Timestamps:** ~34:09–34:24; ~35:08–35:40  

Spoken demo numbers: **~533 N·m** (units as spoken — treat as effective top stiffness \(k\); SI clarification **G-A05**) and **~60.1 g** effective mass. Entering effective mass + stiffness into 4DOF **fit my guitar** hits frequencies with more information than frequencies alone. Plans to measure mobility on **back** too for better fits.

| Field | Value |
|-------|-------|
| Classification | **RM** practice; **TG** quantities |
| Toolbox destination | Mobility → \(k_\mathrm{eff}\), \(m_\mathrm{eff}\) → 4DOF prior |
| Link | Pack 3 \(Y=1/\sqrt{km}\) |

**Point ID:** A19  

---

### 5.3 Fit frequencies typed when autofill failed  
**Timestamps:** ~34:38–35:08  

Autofill from resonance reader failed live. Typed **91.2**, **174**, and **~253**. Enter as little or as much as you have.

| Field | Value |
|-------|-------|
| Classification | **EO** demo session |
| Toolbox destination | Partial-data fit UX |

**Point ID:** A20  

---

### 5.4 Compare / what-if: soundhole, altitude (~3 Hz)  
**Timestamps:** ~35:58–36:49  

Compare mode: change parameters one at a time (soundhole area bigger/smaller; altitude 6000→3000 ft-ish). Demo: numbers changed; top down ~**3 Hz**; air also reduced (coupled).

| Field | Value |
|-------|-------|
| Classification | **RM** UX; altitude **EP** |
| Toolbox destination | 4DOF what-if lab |
| Gap | Exact altitude conversion / NASA air tables not shown |

**Point ID:** A21  

---

### 5.5 Drag peaks for what-ifs; build DOF stack  
**Timestamps:** ~36:49–37:40  

Grab peaks and slide (touchy) → what-ifs to get there. Can start air → add top → add back → add sides to build to 4DOF.

| Field | Value |
|-------|-------|
| Classification | **RM** pedagogy |
| Toolbox destination | **LAB** progressive DOF reveal |
| Link | A22 (why sides matter) |

**Point ID:** A22  

---

## 6. What “four degrees of freedom” means (Elaine Q)

### 6.1 From inadequate 3DOF to 4DOF with sides  
**Timestamps:** ~37:53–42:43  

**Historical 3DOF:** top stiffness, back stiffness, air movement; sides presumed **rigid**. Output effective \(k\)/\(m\) bore **no relation to reality** → model minimally useful.

**Reality:** sides never rigid (obvious in **T112** with side motion). Gore extended model to include sides = **rest of structure** (sides + neck + attached).

**Motivation experiment:** guitar in mold vs out — top/back tap freqs different. Covered sides with Blu-tack + Australian 50¢ coins = **mass without stiffness** → same effect as mold → **side mass** mattered more than side stiffness for that difference. Model written to check whether behavior was general; analysis matched.

**Later use:** add other resonances / sound sources to match higher FRF peaks. Predictive use always felt a **stretch** to Gore; he didn’t push it; others (including Mallaloy) did — “where we’re at now.”

| Field | Value |
|-------|-------|
| Classification | **TG** history/**EP**; predictive stretch **OH**/caution |
| Link | Pack 4 S08–S09; Pack 7 U05 |
| Toolbox destination | **EMP** 4DOF with side DOF; **KB** 3DOF inadequacy |

**Point ID:** A23  

---

## 7. High vs low monopole mobility and tone (Tony Q)

### 7.1 Largely independent if resonances match  
**Timestamps:** ~42:57–45:14  

No real functional relationship between monopole mobility and **timbre**. Old adage “given volume, then tone” — linkage that way, not a physical tone formula.

- High stiffness + high mass → low \(Y\)  
- Higher mass alone → lower resonances  
- If mass **and** stiffness raised so resonant frequencies **stay the same** (\(f \propto \sqrt{k/m}\)), \(Y\) drops mainly as **volume**; timbre doesn’t change much  

High-\(Y\) vs low-\(Y\) guitars with **same** resonant frequencies: sound much the same tonally; one significantly louder. “Volume = tone” in many listeners = **psychoacoustic**, not physical.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Link | Pack 5 “right \(Y\)” / conspiracy framing |
| Toolbox destination | **RULE**: do not equate louder with better timbre in scoring UI |

**Point ID:** A24  

---

## 8. Multi-target what-ifs + wolf played-note view

### 8.1 Systems suggestions (beta fragile)  
**Timestamps:** ~46:24–47:05  

Multiple targets interesting; systems approach can suggest soundhole diameter ± and stiffness/mass changes. Live demo failed again — more bugs to fix.

| Field | Value |
|-------|-------|
| Classification | **RM** intent; reliability **gap** |
| Toolbox destination | Treat as aspirational until stable |

**Point ID:** A25  

---

### 8.2 Played-note mode for wolf visualization  
**Timestamps:** ~47:13–50:04  

Separate “played note” view: body air/top/back markers vs note + partials. Demo guitar bought to show wolves. G♯2 air mode **~3 cents** off → high wolf likelihood. Timeline (~3 s): wolf note volume drops ~1 s; non-wolf G2 sustains ~2.5 s. Shows relative energy in fundamental vs partials vs body modes. Also useful when tuning tops/bodies — watch how resonances move over time, not only note names.

| Field | Value |
|-------|-------|
| Classification | **RM** visualization; wolf **EP** |
| Link | Pack 2 W01–W09; Pack 1 P03 |
| Toolbox destination | **LAB** wolf spectrogram / cents-to-mode clearance |

**Point ID:** A26  

---

## 9. Ecosystem, market readiness, pre-war Martins

### 9.1 Beta / Timber to Tunes / free distribution  
**Timestamps:** ~50:55–51:33  

Changing daily; used at Timber to Tunes (La Conner). Free to Luther Academy — contrast with subscription models elsewhere.

| Field | Value |
|-------|-------|
| Classification | **RO**/**RM** |
| Toolbox destination | **KB** product posture; no paywall assumption |

**Point ID:** A27  

---

### 9.2 Pre-war Martins / “holy grail”  
**Timestamps:** ~51:50–53:38  

Gore has never measured a pre-war Martin. First ask: loud? exceptional tone? both? Nearest wooden-only X-brace analogs he has measured tend toward **lower monopole mobility**, with typical dread character — “holy grail” depends on whether you like that sound (subjectivity). Happy to measure one if offered.

| Field | Value |
|-------|-------|
| Classification | **TG**/**OH** (corpus gap) |
| Toolbox destination | **EMP** vintage corpus — empty until measured |
| Gap | No pre-war FRF/\(Y\) numbers in this source |

**Point ID:** A28  

---

### 9.3 Carrico monopole mobility jig (product context)  
**Timestamps:** ~8:50–9:19; ~54:28–54:58  

Dan Langhoffer (carico.com): monopole mobility deflection jig + **1 kg** weight in custom cup on dial indicator; used with formula Rick demos. Also binding-cutter organizer, convex radius dish, vacuum clamps (context only).

| Field | Value |
|-------|-------|
| Classification | **RO** shop tooling |
| Link | Pack 3 Carrico path |
| Toolbox destination | **KB** hardware links; still need geometry/δ calibration |

**Point ID:** A29  

---

## 10. Point index

| ID | Topic | Class |
|----|-------|-------|
| A01 | Resonances + monopole mobility as rigor pair | TG/EP |
| A02 | Measure → thickness/braces → build → correct | TG |
| A03 | \(E_\parallel\), \(E_\perp\), density, body size → thickness | TG/EP |
| A04 | Brace stiffness design (wood / wood+CF) | TG |
| A05 | Spreadsheets / simple formulas from complex analysis | TG |
| A06 | Mallaloy apps strip spreadsheet math | TG/RM |
| A07 | Five named tools | RM |
| A08 | Luther Academy Resources footer; free beta | RO/RM |
| A09 | Laptop mic OK for frequency | RM/EO |
| A10 | Plate modes; transverse hardest | RM/EO |
| A11 | FFT → plate thickness; demo ~2.58 mm | RM |
| A12 | Book-example math verification | RM/TG |
| A13 | Boxed OM air~103 / top~207 | EO |
| A14 | Tone generator + Bluetooth amp | RM |
| A15 | 4DOF overlay on FRF (beta bugs) | RM |
| A16 | Altitude shifts coupled modes | EO/EP |
| A17 | Target suggestions; pickup/putty mass | RM/EO |
| A18 | Mobility defaults; 1.02→1.00 kg weight | RM/RO |
| A19 | \(k_\mathrm{eff}\), \(m_\mathrm{eff}\) into 4DOF fit | RM/TG |
| A20 | Partial-frequency fit (91.2 / 174 / 253) | EO |
| A21 | What-if soundhole / altitude ~3 Hz | RM/EP |
| A22 | Drag peaks; progressive DOF build-up | RM |
| A23 | 3DOF→4DOF; mold / Blu-tack / coins | TG/EP |
| A24 | High vs low \(Y\): volume ≠ timbre if \(f\) match | TG |
| A25 | Multi-target systems suggestions (fragile) | RM |
| A26 | Played-note wolf visualization | RM/EP |
| A27 | Free Academy distribution; event use | RO/RM |
| A28 | Pre-war Martins unmeasured; wooden X often lower \(Y\) | TG/OH |
| A29 | Carrico 1 kg mobility jig ecosystem | RO |

---

## 11. Conflicts / calibration notes (do not paper over)

1. **Deflection δ:** Pack 3 spoken **~27 mm** @ 1 kg vs Pack 5 PowerPoint **~0.15 mm** @ ~1 kg remains unresolved. This stream adds **1.00 vs 1.02 kg** weight metadata and app \(k\)/\(m\) outputs but **does not** restate deflection magnitude — still **no** mobility threshold UI until Carrico/Gore `unit_profile` calibrated.  
2. **Spoken stiffness units:** “533 Newton meters” — likely \(k\) in N/m mis-spoken; pin against app/UI and book before encoding.  
3. **Beta reliability:** autofill, 4DOF snap, multi-target solver failed on camera — document as product state, not as Toolbox requirements frozen from demo.
