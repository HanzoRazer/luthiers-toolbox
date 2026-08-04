# Annotated Engineering Lecture Notes  
## Tips to Your Mailbag — Wolf Notes (Trevor Gore)

**Host:** Robbie O’Brien  
**Expert:** Trevor Gore  
**Viewer question:** Bruce (Sydney) — wolf note on the fifth string  
**Scope:** Definition, perceptual/tuner diagnosis, FRF confirmation, half-semitone clearance rule, air- and top-resonance remediation levers  
**Companion:** Shop Talk #20 §2.5 / P03 (mechanism & mid-scale philosophy). This tip is the **operational lab**.  
**Processing rule:** Preserve diagnosis sequence and *why each lever moves which resonance*.

---

## 0. Session architecture

Linear teaching tip:

1. Define wolf note (Robbie → Gore)  
2. Demonstrate on open A (perceptual)  
3. Confirm with chromatic tuner (oscillation / sharp push)  
4. Capture closed-box FRF (10 taps, Visual Analyzer)  
5. Map peaks to scale tone + harmonic (110 Hz / 220 Hz)  
6. State clearance rule (~½ semitone)  
7. List independent lever menus for **air** and **top** resonances  

This is the canonical **wolf remediation workflow** for the empirical knowledge layer.

---

## 1. Definitions

### 1.1 Host definition (mailbag framing)  
**Timestamps:** ~0:20–0:36  

A wolf note happens when the **string frequency matches a guitar natural resonance**, producing a **clunky or dead** character at that frequency.

| Field | Value |
|-------|-------|
| Classification | **EP** (match condition); perceptual labels **EO** |
| Note vs Shop Talk | ST#20 emphasized loud/short via high admittance; mailbag host also says “clunky/dead.” Both are valid listener reports of the same mismatch class — uneven vs neighbors. |
| Toolbox destination | **KB** glossary: wolf = resonance–scale-tone coincidence with uneven decay/level |

---

### 1.2 Gore definition (comparative)  
**Timestamps:** ~0:54–1:02  

A wolf note **sounds distinctly different from the notes around it** (or strings around it).

| Field | Value |
|-------|-------|
| Classification | **TG** operational definition (ear-first) |
| Design implication | Evenness across the fretboard/string set is the acceptance test — not peak SPL alone |

---

## 2. Diagnosis workflow

### 2.1 Step A — Hear the anomaly  
**Timestamps:** ~1:02–1:30  

Demo guitar: open E fine; open A **much louder** → identified as wolf. Cause stated: string frequency **A @ 110 Hz** matching a body resonance.

| Field | Value |
|-------|-------|
| Classification | **EO** demo; mechanism **EP**/**TG** |
| Caveat | Louder is one manifestation; ST#20 also describes short/drained notes. Do not require “loud” as the only signature. |
| Toolbox / Tap Tone | Guided lab step 1: comparative listening checklist |

**Point ID:** W01  

---

### 2.2 Step B — Tuner instability / pitch push  
**Timestamps:** ~1:30–2:25  

Second diagnostic: tuning the wolfy pitch is difficult. On a B-flat / chromatic tuner:

- Open E: steady, accurate  
- A on that string: plays **quite sharp** and the note is **oscillatory**  

Gore: direct indication of wolf — it **pushes the scale tone out of tune** and oscillates.

| Field | Value |
|-------|-------|
| Classification | **TG** diagnostic heuristic; pitch-coupling **EP**-adjacent |
| Common misconception | “Bad intonation setup” when the real issue is modal coincidence |
| Toolbox destination | **LAB** / **KB**: tuner-oscillation as wolf flag (not only cents-offset tables) |
| Empirical layer | Correlate tuner flutter with proximity of FRF peak to played fundamental |

**Point ID:** W02  

---

### 2.3 Step C — Expect the problem on the pitch class  
**Timestamps:** ~1:43–1:51  

Loud open A “probably means we’ve got problems on **all the A’s**.”

| Field | Value |
|-------|-------|
| Classification | **TG**/**EO** |
| Toolbox destination | **RULE**: when flagging a wolf, scan the pitch class across strings/frets, not a single fretting |

**Point ID:** W03  

---

### 2.4 Step D — Closed-box FRF (10-tap)  
**Timestamps:** ~2:27–3:42  

Procedure:

1. Guitar at the bench  
2. Soft hammer: **bouncy ball + satay stick**  
3. Tap around the **lower bout**  
4. **Visual Analyzer** (free download)  
5. After **10 taps**, inspect spectrum  

Peaks of particular interest in the demo:

| Peak | Role | Problem proximity |
|------|------|-------------------|
| Main **air** resonance | Helmholtz / A0-class | ~**110 Hz** (open A) |
| Main **top** resonance | Top monopole-class | ~**220 Hz** (A harmonic / octave) |

Gore: potentially **two** problems — hitting **two harmonics of the A note** — explaining the severity of the difference.

| Field | Value |
|-------|-------|
| Classification | **TG** measurement SOP; dual-harmonic collision **EO** on this instrument |
| Link to ST#20 | Same VA / 10-tap practice as P33; clearance philosophy as P03–P05 |
| Toolbox destination | **LAB** + **MEAS** stage `closed_box_strung` (or equivalent) with peak→note overlay |
| Tap Tone Pi | Peak list + nearest scale tone **and** nearest harmonic of flagged pitch class |

**Point ID:** W04  

---

## 3. Clearance / design rule

### 3.1 Move resonances away from scale tones  
**Timestamps:** ~4:11–4:31  

Need to move guitar resonances away from scale-note frequencies. Typical target: **half a semitone away** — as far as you can get before approaching another scale tone.

| Field | Value |
|-------|-------|
| Classification | **TG** design rule (quantifies ST#20 “midway between scale tones”) |
| Math note | Midpoint between equal-tempered semitones **is** 50 cents = ½ semitone. This tip states the clearance explicitly. |
| Caveat | Applies to the resonances you can control; dual collisions (f and 2f) may require coordinated air + top moves |
| Toolbox destination | **RULE** + scale-tone grid overlay; cents-to-nearest-note on each peak |
| Empiric | Prefer reporting clearance in **cents**, not only Hz |

**Point ID:** W05  

---

## 4. Remediation lever menus

### 4.1 Main air resonance levers  
**Timestamps:** ~4:38–5:11  

Options stated:

1. Make the **whole box a little softer** — reduce **top stiffness** and **back stiffness** → air resonance frequency **down**  
2. Change **soundhole diameter**  
   - Smaller → air resonance **down**  
   - Larger → air resonance **up**  

| Field | Value |
|-------|-------|
| Classification | **EP** (Helmholtz / compliant-wall trends) + **TG** shop menu |
| Toolbox destination | Already strong in soundhole calculators — wire into **wolf guided workflow** as lever #1/#2 with predicted direction |
| Caveat | Softening top also moves top resonance (coupling). Mode-selective skill from ST#20 P02 still required. |
| NO-CALC abuse | Do not auto-resize soundhole from a single wolf flag without checking top-peak side effects |

**Point ID:** W06  

---

### 4.2 Main top resonance levers  
**Timestamps:** ~5:13–5:40  

| Action | Effect on top resonant frequency |
|--------|----------------------------------|
| Add mass | ↓ |
| Reduce stiffness | ↓ |
| Add stiffness | ↑ |
| Reduce mass | ↑ |

“Interesting options — choose which is best suited to this job.”

| Field | Value |
|-------|-------|
| Classification | **EP** (\(f \propto \sqrt{k/m}\)) + **TG** selection framing |
| Toolbox destination | **LAB** decision tree; **EMP** which shop edits (brace height, bridge mass, etc.) map to Δk / Δm |
| Link to ST#20 | Brace-height reduction for mobility (P11) also lowers stiffness → can move top peak down — dual purpose if desired |
| NO-CALC | Menu is directional physics; magnitude needs measurement feedback |

**Point ID:** W07  

---

### 4.3 Dual-resonance problems need dual strategies  
**Timestamps:** ~4:11–4:37; implied by 4:04–4:15  

When air≈110 and top≈220, both must be moved off the A harmonic series. Choosing only a soundhole edit may leave the top wolf; only mass-loading the top may leave the air wolf.

| Field | Value |
|-------|-------|
| Classification | **TG** implied methodology |
| Toolbox destination | **RULE**: if multiple peaks collide with a pitch class or its harmonics, present a **coordinated plan**, not a single knob |

**Point ID:** W08  

---

## 5. Design philosophy (from close)

**Timestamps:** ~5:43–6:10  

Robbie: advanced / deep rabbit hole; builders need this to build the best guitar possible. Points to Trevor Gore’s books (search “Trevor Gore book”) without making the tip a full advertisement.

| Field | Value |
|-------|-------|
| Classification | **TG**/host pedagogy |
| Toolbox destination | **KB**: wolf work is core craft competence, not optional trivia |

**Point ID:** W09  

---

## 6. Common misconceptions corrected

| Misconception | Correction | IDs |
|---------------|------------|-----|
| Wolf = only a “dead” string fault or bad setup | Often modal coincidence; tuner flutter is a clue | W01–W02 |
| Fix intonation hardware first | Check box resonances vs pitch class | W02–W04 |
| One peak to move | Harmonics can recruit air **and** top | W04, W08 |
| Any direction of move is fine | Prefer ~½ semitone clearance (mid-scale) | W05 |
| Soundhole-only always enough | Top has its own mass/stiffness menu | W06–W07 |
| Louder note can’t be a wolf | Demo wolf was louder open A | W01 |

---

## 7. Validation techniques (tip order)

1. Comparative listening (neighbor notes/strings)  
2. Tuner steadiness / oscillation check  
3. Scan pitch class (all A’s, etc.)  
4. 10-tap lower-bout FRF  
5. Overlay peaks vs fundamentals **and** low harmonics  
6. Apply levers; re-measure clearance in cents  
7. Re-check ear + tuner on the former wolf pitches  

---

## 8. Compact point catalog

| ID | Point | Category | Class |
|----|-------|----------|-------|
| W01 | Ear: distinctly different / often louder | Diagnosis | TG/EO |
| W02 | Tuner: oscillatory + can push sharp | Diagnosis | TG |
| W03 | Pitch-class contamination (all A’s) | Diagnosis | TG/EO |
| W04 | 10-tap FRF; air≈110 & top≈220 dual hit | Measurement | TG/EO |
| W05 | Clearance ≈ ½ semitone from scale tones | Design rule | TG |
| W06 | Air levers: soften box; ± soundhole Ø | Construction | EP/TG |
| W07 | Top levers: ±mass / ±stiffness | Construction | EP/TG |
| W08 | Dual collisions → coordinated fixes | Methodology | TG |
| W09 | Core builder competence | Philosophy | TG |

---

## 9. Relationship to Shop Talk #20 (do not duplicate)

| Keep in ST#20 | Add from this tip |
|---------------|-------------------|
| Admittance / loud-short mechanism | Tuner-oscillation diagnostic |
| Mid-scale philosophy | Explicit **½ semitone** clearance |
| 100/180/226 good-target example | 110/220 **failure** example on A |
| Mode-selective voicing as skill | Concrete air vs top lever menus |
| Live back, falcate, free-top, mobility stack | Out of scope here |

---

*See `CROSSWALK_TOOLBOX.md` for implementation mapping.*
