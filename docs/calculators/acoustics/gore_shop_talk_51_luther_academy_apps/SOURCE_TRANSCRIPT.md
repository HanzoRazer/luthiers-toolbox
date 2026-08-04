# Source Transcript (cleaned working extract)  
## Shop Talk Live Stream #51 — Gore + Mallaloy Luther Academy apps

**Host:** Robbie O’Brien  
**Guests:** Trevor Gore (Sydney); Rick Mallaloy (Tacoma / Celestial Instruments)  
**Working extract:** substantive teaching and demo; sponsors/giveaways/class logistics abbreviated  

ASR artifacts corrected lightly for readability; numbers preserved as spoken.

---

## Carrico / Academy context (abbrev.)

Robbie: Carrico products include binding-cutter bearing organizer, convex radius dish, double-sided bench vacuum clamp, bridge vacuum clamp, and **monopole mobility deflection testing jig** with **1 kg** weight in dial-indicator cup. Mobility formula Rick will demo. Online courses noted (CF mesh neck repair, etc.) — out of scope for acoustics pack.

Cesar (Brazil): giveaway of monopole mobility test jig (US only that stream). Winner: Larry Jones.

Access to tools: Luther Academy website → scroll to bottom → **Resources** (beta; not in main menu yet).

---

## Gore — program origin

Trevor (~13:11+): Cold morning Sydney (~7°C). Project started ~**2008** (~20 years). Wanted more rigor. Things that mattered: putting **resonances in the right place** (timbre) and getting **responsiveness** right — measure = **monopole mobility**. Placing resonances needed measurement, then brace size / top thickness. Formula for how thick to make top/back: need Young’s modulus along and across, density, guitar size → resonant frequency on guitar. Build, see closeness, modify to target. Bracewood properties; wood or wood+CF braces. Complex analysis condensed to simple formulas + spreadsheets issued at modal tuning courses. Broader audience lacked spreadsheet/math skill. Rick’s tools take maths out; still punch data; design braces, material properties, top/back thickness, measure resonances. Gore tried some; matched original work. Passes to Rick.

---

## Mallaloy — five tools

Rick: First heard Gore books building with Charles Fox — prescriptive/consistent. Homework at Trevor’s class at Robbie’s (≈2 years prior): plate thickness spreadsheet → wrote **web calculator** instead (dislikes spreadsheet parentheses).

Five tools:

1. **Four degrees of freedom model** (+ environment)  
2. **Plate thickness calculator**  
3. **Resonance reader** (FFT; plates/tops/notes; forward to plate thickness; later flexural rigidity)  
4. **Monopole mobility** calculator (score + effective stiffness + effective mass → into 4DOF)  
5. **Flexural rigidity calculator** (custom braces; compare effective stiffnesses)

---

## Resonance reader + plate thickness demo

Laptop mic OK for **frequencies**; fancy mics more for Q/volume. Pacific Rim top (not surfaced): measured with ruler. Four taps. Plate mode: cross/long detected; transverse hardest (~49.5 Hz in view; markers adjustable).

Open plate thickness calculator with modes. Inputs: L **542 mm**, W **220 mm**, **212 g**, **4.1 mm** thick → **~2.58 mm**. Presets: default / Trevor steel / Robbie / Martin OM; Trevor vs Robbie ≈ **2.57**. Classical / live backs different targets. Checked exhaustively vs Trevor book examples.

---

## Box measurement + tone + 4DOF overlay

Unfinished OM (no bridge yet; aiming Timber to Tunes). Taps + back tap. Instrument mode: air **103**, top **207**; back initially wrong — higher (tone generator confirms). Spark USB Bluetooth 4″ amp for tone. Overlay 4DOF dashed orange — auto-solve failed live (beta).

Robbie-build guitar file: different at **6000 ft** vs home. Targets air **90** / back **170** → suggestions e.g. **+5 g** near bridge. Pre–K&K file; K&K ~**3 g**; ~**1.5 g** poster putty to dial in.

John Parch Q: does autofill 4DOF pull plate info? On this screen: pulls **frequencies** and solves; in 4DOF page can enter monopole mobility numbers — accurate fits.

---

## Mobility → 4DOF fit

Defaults = Robbie-build guitar. Weight default **1.02 kg** (old) → set **1.00 kg** (new weights). Spoken: **533** (Newton meters as said) and **60.1 g**. Autofill failed; typed **91.2**, **174**, ~**253**. Enter effective mass + stiffness → fit my guitar. Plans back mobility too. Compare: change soundhole; altitude 6000→~3000 → ~**3 Hz** top drop; air reduced (coupled). Drag peaks for what-ifs (touchy). Progressive: air → top → back → sides.

---

## Elaine Q — what 4DOF means

Trevor: Old literature used **3DOF** (top, back, air) with sides **rigid**. Effective \(k\)/\(m\) unrelated to reality — minimal usefulness. Sides never rigid (T112 side motion). Extended to **4DOF** including sides = rest of structure (sides, neck, attached). Mold vs free: top/back freqs different. Blu-tack + 50¢ coins on sides = mass, no stiffness → same as mold → **mass of side structure** mattered. Model confirmed analytically general. Later: add sound sources for higher peaks / match FRF. Predictive use always a **stretch** for Gore; others including Rick pushed it.

---

## Tony Q — high vs low monopole mobility vs tone

Trevor: Not really tonal characteristics tied to high vs low \(Y\). “Given volume, then tone” adage — linkage, not functional tone relationship. High stiffness + high mass → low \(Y\). Raise mass and stiffness keeping \(f=\sqrt{k/m}\) same → mainly volume down; timbre similar. Same resonances, high vs low \(Y\): much same tonally; one louder. Volume=tone in minds = psychoacoustic.

---

## Wolf played-note view

Rick: What-ifs / multi-target systems approach (live buggy). Played-note view: wolf demo guitar; air/top/back; G♯2 ~**3 cents** from air → wolf likely. Timeline ~3 s: wolf dies ~1 s vs good G2 ~2.5 s; body modes visible when note off. Useful for watching resonances over time while tuning.

---

## Wrap / Drew / UK / Elaine

Robbie: beta; changing daily; Timber to Tunes; free to Academy. Elaine: apps continue on Academy site — yes.

UK Q: pre-war Martins holy grail — anyone measured? Trevor: never had hands on one. Ask: loud? tone? both? Wooden-only X analogs often **lower \(Y\)**, typical dread character; holy grail subjective. Willing to measure if offered.

Drawing: Larry Jones wins Carrico monopole mobility jig.
