# Annotated Engineering Lecture Notes  
## Trevor Gore — Shop Talk Live Stream #25

**Host:** Robbie O’Brien  
**Guest:** Trevor Gore (Sydney; not in workshop — better broadband)  
**Scope:** Substantive Q&A only — falcate humidity/origins, frequency rescue, side mass, retop/back tuning, laminated sides, epoxy, classical targets, live-back braces, Marty radial vs falcate, body damping, dread sizing, sound ports, spreadsheet philosophy  
**Excluded:** Giveaways, promo codes, sponsor rolls, travel banter  
**Companions:** ST#20 (P04 triad, live back, bridge mass+stiffness); Wolf pack (clearance); Mobility pack (\(Y\) vs mass-loading warning)

---

## 0. Session architecture

Focused falcate + closed-box voicing Q&A after the falcate course launch era. Highest density:

1. Humidity behavior of falcate vs X / lattice  
2. Rescue paths when T(1,1)₂ is too low/high after close  
3. Side-mass discovery (coins) + loudness anecdote  
4. Live-back B11 → T113 procedure when retopping  
5. Design philosophy clash: falcate vs Marty radial / Meyer “third resonance”  
6. Practical build choices: laminated sides, epoxy, sound ports, dread cube-rule bracing  

---

## 1. Falcate bracing — humidity & structure

### 1.1 Build humidity  
**Timestamps:** ~11:26–11:51  

Keep the build under humidity control — typically **40–45% RH** — for any guitar, falcate included.

| Field | Value |
|-------|-------|
| Classification | **TG** shop rule |
| Toolbox destination | **RULE** / build-climate KB |

**Point ID:** S01  

---

### 1.2 Post-build humidity: falcate less “pump” than X or lattice  
**Timestamps:** ~11:57–13:45  

Major structural difference: falcate has **fewer continuous braces going directly across the grain**.

- **X-bracing:** X braces span the width of the guitar.  
- **Falcate:** essentially the **bridge** is the main cross-width member.  

**Consequence:** as humidity changes, the top **pumps up and down much less** than X- or lattice-braced guitars.

**Extreme humidity visual:** top can *look* dipped; actually **outboard edges** rise where secondary falcates run across the grain — two bulges beside the bridge make the bridge *look* sunk. Bridge itself has not sunk.

**Playability:** action **hardly changes** — falcate described as fairly **impervious to humidity** for playability.

| Field | Value |
|-------|-------|
| Classification | **TG** / **EO** structural humidity behavior |
| Common misconception | “Bridge sank” under humidity — often edge bulge optical |
| Toolbox destination | **KB** / falcate design notes; climate→action model (**EMP**, not a new calc yet) |
| Gap | Quantitative Δaction vs RH for falcate vs X — not given |

**Point ID:** S02  

---

## 2. Falcate — naming & design origin

### 2.1 Name: falcate = sickle-shaped  
**Timestamps:** ~14:16–16:42  

Michael Timothy (photo in build book; worked with Gerard Gilet at Botany) suggested **falcate** after being asked for a name. Means **sickle-shaped** (also used for curved leaves). Preferred over obvious “boomerang bracing.”

| Field | Value |
|-------|-------|
| Classification | **TG** provenance / nomenclature |
| Toolbox destination | **KB** glossary |

**Point ID:** S03  

---

### 2.2 Design genesis: sail tape-drive + stress-path efficiency  
**Timestamps:** ~16:49–18:39  

- Sailing: **tape-drive** sail reinforcement (Ole Coleus; precursor ideas to North 3DL-class sails) — high-modulus (Kevlar) tapes along stress paths, curved from sail corners.  
- Engineering critique of **X-bracing:** why that layout? Put material where **maximum stress** is; rationalize for an efficient structure.  
- Falcate shape = curved stress-path thinking + put stiffness where most required.

| Field | Value |
|-------|-------|
| Classification | **TG** design philosophy / historical origin |
| Toolbox destination | **KB** / bracing design narrative (falcate still geometry-absent in code) |
| Link | ST#20 P17–P18 (X scoops mids; falcate restores) — complementary |

**Point ID:** S04  

---

## 3. Practical tuning methodology — frequency rescue

### 3.1 Good T(1,1)₂ neighborhoods (mid-scale)  
**Timestamps:** ~21:13–21:48  

Frequencies that work well are those **exactly between scale tones**.

| Family | Good T(1,1)₂ examples (as stated) |
|--------|-----------------------------------|
| Steel-string | **170 / 180 / 190 Hz** |
| Classical | Usually a bit higher; **190 Hz** a really good number |

| Field | Value |
|-------|-------|
| Classification | **TG** (extends ST#20 mid-scale / 100–180–226 family) |
| Toolbox destination | **EMP** target bands by family |

**Point ID:** S05  

---

### 3.2 Top resonance too low after closing the box  
**Timestamps:** ~21:54–23:55  

Depends how low:

1. Bridge adds **stiffness and mass**. To **raise** frequency: add stiffness or reduce mass.  
2. Removing material from an already-low top removes **stiffness faster than mass** → wrong direction.  
3. Rescue path: **very stiff, very light bridge** — possibly slightly **wider**; **carbon fiber laminate** in bridge; **low-density** wood; thin the back edge.  
4. Way too low: **cut losses — replace the top**.  
5. Size examples: 170 Hz T112 on a 000 can sound nice; **160 Hz** on that size often **muddy** / problematic.

**General rules:**

- Easier to **go down** than up → **aim a little high**.  
- Coming down a **long** way via **mass loading** is a bad idea if you want a light, responsive top (mobility conflict — Pack 3).

| Field | Value |
|-------|-------|
| Classification | **TG** methodology; muddy@160 **EO**/TG; mass-load warning **TG** |
| Toolbox destination | **LAB** rescue decision tree; **RULE** aim-high; link mobility pack |
| Gaps | Exact “how low is too low” by body size beyond 000 examples |

**Point ID:** S06  

---

### 3.3 Classical aiming 180 / back 226 — stiffness numbers  
**Timestamps:** ~40:33–41:41  

Viewer: top 180, back 226; book vibrational stiffness 60 & 50?

Gore:

- **Think hard about 180** for classical — on the low side (still OK if intentional).  
- Prefer keep book **F number**, change **brace height** (more flexible braces) rather than a different top.  
- If top already stiff enough for string tension, reaching 180 often means **mass loading** rather than reducing stiffness — another reason to reconsider.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | **KB** / plate design guidance; do not blindly lower top stiffness targets |
| Gap | Mapping “vibrational stiffness” spreadsheet cells to Toolbox fields needs book crosswalk |

**Point ID:** S07  

---

## 4. Side mass

### 4.1 Discovery: mold mass vs stiffness  
**Timestamps:** ~24:57–26:52  

Guitar in outside mold (~4–5 kg around sides): top frequency **lower** than out of mold. Two hypotheses: mold adds **mass** or **stiffness**.

Experiment: many Australian **50-cent coins** Blu-Tacked on sides → top resonance **down** → **mass effect**, not stiffness.

Also modeled in the **four-degree-of-freedom** model with sides included — mathematics confirmed the effect.

| Field | Value |
|-------|-------|
| Classification | **EO** discovery + **TG** model confirmation |
| Toolbox destination | **EMP** / 4DOF side-mass term; **KB** experiment narrative |
| Code gap | Side-mass as adjustable design/voicing parameter |

**Point ID:** S08  

---

### 4.2 Loudness anecdote (classical teacher / coins)  
**Timestamps:** ~26:57–29:31  

Teacher filled bag of coins in lower bout for lap balance. Gore permanently mounted comparable side mass (~**300–400 g** recalled) on a wooden block (block alone ≈ no sonic change). Result: ~**twice as loud**; estimated **+6 to +10 dB** (vs ~3 dB just-noticeable). Works on **any** guitar, not falcate-specific. Deep mechanism deferred unless asked.

| Field | Value |
|-------|-------|
| Classification | **EO** single-instrument anecdote; magnitude **OH**/recall |
| Toolbox destination | **KB** / EMP seed — not a loudness calculator from grams alone |
| Gap | Mechanism explanation not given in-stream (**G-S** register) |

**Point ID:** S09  

---

## 5. Retop / back-only tuning (live back)

### 5.1 Vibrational stiffness vs T112  
**Timestamps:** ~31:42–32:16  

“Vibrational stiffness value” (e.g. 60) is for **build repeatability**, not a direct prescription of a particular T112. Same F-process → same frequencies if aimed consistently.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | **KB** — separate process-control metric from modal targets |

**Point ID:** S10  

---

### 5.2 B11 → T113 four-semitone procedure  
**Timestamps:** ~32:22–34:03  

Example classical live-back path:

1. Aim T112 ≈ **190 Hz**.  
2. Want T113 **four semitones higher** (~**240 Hz**).  
3. Back on, **no top**: tap → **B11** (main back resonance).  
4. B11 comes in **a little lower** than finished T113.  
5. Tune B11 to **240 Hz**; after top on expect ~**242–243 Hz**; brace-trim down to 240.  
6. Use other methods to land top at 190.

| Field | Value |
|-------|-------|
| Classification | **TG** measurement/voicing SOP |
| Link | ST#20 four-semitone spacing; Wolf/ST mid-scale |
| Toolbox destination | **LAB** retop / live-back staging; Tap Tone stage `back_only` |
| Gap | Full “other methods” for top landing — book/course |

**Point ID:** S11  

---

## 6. Sides, Helmholtz, lamination

### 6.1 Laminated sides trade-offs  
**Timestamps:** ~34:15–38:09  

- Laminating: more **stiffness** and **dimensional stability**; usually a bit more **mass** (thicker).  
- Discrete **side masses** remain adjustable; laminated rim mass is what it is.  
- Side masses still affect things the same way.  
- Body is a Helmholtz resonator with **flexible** walls (not rigid brass/glass sphere) → flexible top/back **lower** Helmholtz frequency.  
- Very stiff laminated sides limit tuning air resonance via side flexibility.  
- Solid sides: thickness / side-stiffness changes can shift main air resonance ~**2–3 Hz** (~**semitone or more** vs stiff build) — as stated.  
- Gore: laminated prep effort usually **not worth it**; prefers **solid wood** sides despite losing some flatness/stability benefits of laminate.

| Field | Value |
|-------|-------|
| Classification | **TG** / **EO** (~2–3 Hz); preference **TG** |
| Toolbox destination | **RULE**/KB; acoustic_body / Helmholtz side-compliance caveat |
| Gap | Quantitative side-compliance model parameters |

**Point ID:** S12  

---

## 7. Live back, player damping, bevels

### 7.1 Secondary 45° / star braces on live back  
**Timestamps:** ~41:41–42:24  

How they influence **higher** modes / is symmetry critical?

Gore: **does not know** from hard study. **Suspects** they **suppress** higher modes — goal is back moving **as one unit**; star braces help that.

| Field | Value |
|-------|-------|
| Classification | **OH** (explicitly untested by him here) |
| Toolbox destination | **KB** with hypothesis flag — not a design rule |
| Gap | Empiric higher-mode study |

**Point ID:** S13  

---

### 7.2 Live back against the body  
**Timestamps:** ~50:35–51:48  

Pressing back to the body **dampens** live-back response but does **not kill** it. Analogous to arm on top/bridge damping.

For best acoustic effect: **armrest** + classical position with **back away from body**.

| Field | Value |
|-------|-------|
| Classification | **TG** / **EO** |
| Toolbox destination | **KB** / playing-position guidance (not a calc) |

**Point ID:** S14  

---

### 7.3 Top bevel “armrest” can be counterproductive  
**Timestamps:** ~51:48–52:36  

Bevels help circulation but bring forearm **closer to the top** → more damping → **counterproductive** acoustically. Stick-on armrests that **keep the arm away** are better if maximizing acoustic benefit.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | **KB** ergonomics vs acoustics |

**Point ID:** S15  

---

## 8. Falcate vs Marty radial / Meyer third resonance

### 8.1 Reconstructing Meyer’s “third resonance”  
**Timestamps:** ~42:30–45:57  

Jürgen Meyer (Germany, ~1980s): listening tests favored guitars with a prominent **“third resonance.”** Violin-ordered mode labels mislead on guitars.

Typical low→high counting Gore uses:

1. Main air (Helmholtz)  
2. Main top  
3. Main back / T113  
4. Cross-dipole  
5. Long dipole  

Meyer excited **on the centerline** → never saw **cross-dipole** (node). Non-live-back → no T113. So Meyer’s “third” was actually the **long dipole**.

| Field | Value |
|-------|-------|
| Classification | **TG** historical/method reconstruction (**EO** on Meyer setup as understood) |
| Toolbox destination | **KB** mode-label hazard; analyzer labeling |

**Point ID:** S16  

---

### 8.2 Marty radial intent vs falcate  
**Timestamps:** ~46:02–50:04  

Simon Marty (physics PhD, Sydney Uni; no personal overlap with Gore): radial bracing **discontinuous under the bridge** → appears aimed at a very **active long dipole** / more **bridge rotation** (Meyer-influenced, Gore’s suspicion).

Conflict with structural reality: string torque wants to rotate the bridge; Gore targets ~**2°** bridge rotation; limiting rotation is primary. Marty guitars (as Gore has seen) tend toward **more** than that.

**Falcate is almost the opposite:** stiffness **under the bridge** to **stop** rotation.

Long dipole often near classical **first-string** range (~300–400 Hz / E) but:

- Weak radiator (dipole cancellation)  
- Driven largely by **tension change** — wrong tool to energize first string  

**Better:** **cross-tripole** — asymmetric, stronger radiator; falcate places cross-tripole in first-string range for treble response.

| Field | Value |
|-------|-------|
| Classification | Marty intent **OH**/TG suspicion; radiator physics **EP**; falcate strategy **TG**; ~2° **TG** |
| Link | ST#20 P22–P23 (cross-tripole / first string); P10 (don’t obsess bridge angle if modes+mobility OK — here ~2° is a **structural** target, not the 1.5→2 vanity metric) |
| Toolbox destination | **KB** bracing dialect; falcate vs radial design rules |
| Gap | Direct Marty confirmation; quantitative rotation corpus |

**Point ID:** S17  

---

## 9. Construction heuristics

### 9.1 Dreadnought falcate sizing — cube rule  
**Timestamps:** ~52:42–53:47  

Same **F numbers** / book equation **4.5.7** can keep top thickness targeting OK. But simply-supported beam deflection ∝ **span³** and ∝ **1/thickness³**. As body grows in length **and** width, **size bracing up by the cube rule**.

| Field | Value |
|-------|-------|
| Classification | **EP** beam scaling + **TG** application |
| Toolbox destination | **RULE** in bracing prescription when body scale changes |
| Gap | Exact brace dimension tables for dread vs OM in Toolbox |

**Point ID:** S18  

---

### 9.2 Side sound port vs top soundhole  
**Timestamps:** ~54:34–55:48  

Expect different frequencies: port **position** and **size** both shift air resonance. Side port **instead of** top hole needs area of **similar order of magnitude** for similar overall sound. Player hears well; **less out front** (radiation toward player). Air change couples → top resonance also moves.

| Field | Value |
|-------|-------|
| Classification | **EP**/**TG** |
| Toolbox destination | Soundhole/multiport stack — **LAB** “port vs hole” scenario |
| Link | Existing multiport Helmholtz tools |

**Point ID:** S19  

---

### 9.3 Epoxy / West 105–207  
**Timestamps:** ~38:15–40:26; ~58:36–1:00:16  

- Other epoxies can work; Gore standardized on **West 105 + 207** (non-bloom clear-coat hardener; boat-building heritage; **3:1** vs typical **5:1**). Uses 207 for gluing, laminating, coating — one hardener.  
- Grain fill: need non-blooming system + proper surface prep.  
- **Why epoxy with carbon:** industry-standard composite pairing; professional builds need century-scale confidence — Gore has ~**40 years** epoxy/CF experience. Alternate adhesive/fiber mixes need a lifetime trial.

| Field | Value |
|-------|-------|
| Classification | **TG** process practice; longevity argument **TG**/**EO** |
| Toolbox destination | **KB** / materials process — not acoustics calculator |

**Point ID:** S20  

---

### 9.4 Spreadsheets: toolbox not black box  
**Timestamps:** ~55:54–58:31  

Unlikely to release pre-made book spreadsheets — support burden; learning value of writing your own; books are a **toolbox** of design principles; complex math leads to simple algebraic spreadsheet entries. Get help from a mate/offspring if needed.

| Field | Value |
|-------|-------|
| Classification | **TG** pedagogy |
| Toolbox destination | Aligns with **guided understanding** over opaque oracles; **NO-CALC** cargo-cult |
| Tension | Luther Academy apps (mobility pack M10) are a different product surface — document both stances |

**Point ID:** S21  

---

## 10. Compact point catalog

| ID | Point | Category | Class |
|----|-------|----------|-------|
| S01 | Build RH ~40–45% | Construction | TG |
| S02 | Falcate humidity: less pump; edge bulge optical; action stable | Theory / EO | TG/EO |
| S03 | Name falcate = sickle-shaped (Michael Timothy) | Philosophy | TG |
| S04 | Origin: sail tape-drive + stress-path efficiency | Philosophy | TG |
| S05 | Mid-scale T112: steel 170/180/190; classical ~190 | Tuning | TG |
| S06 | Too-low rescue: stiff/light bridge; else retop; aim high; avoid heavy mass-load | Tuning | TG |
| S07 | Classical 180: prefer brace height not weaker top / mass-load path | Tuning | TG |
| S08 | Side mass lowers top f; coins/mold experiment; 4DOF | Theory / EO | EO/TG |
| S09 | Large side mass can greatly increase loudness (anecdote) | Experimental | EO |
| S10 | Vibrational stiffness = repeatability, not T112 itself | Measurement | TG |
| S11 | Back-only B11≈ target T113; +few Hz when topped; 4 semitone rule | Measurement | TG |
| S12 | Laminated sides: stability vs tunable compliance (~2–3 Hz air); Gore prefers solid | Construction | TG/EO |
| S13 | Live-back star braces may suppress high modes (untested) | Hypothesis | OH |
| S14 | Body contact dampens live back; doesn’t kill | Practical | TG |
| S15 | Top bevel can increase forearm damping | Practical | TG |
| S16 | Meyer “third resonance” = long dipole under his excitation | Theory / History | TG |
| S17 | Marty radial ≠ falcate; cross-tripole > long dipole for 1st string | Design philosophy | TG/OH |
| S18 | Larger bodies: brace by span³ cube rule | Construction | EP/TG |
| S19 | Side port shifts A0; needs comparable area; less out-front | Theory | EP/TG |
| S20 | West 105/207 practice; CF+epoxy longevity argument | Construction | TG |
| S21 | Write your own sheets; books as toolbox | Philosophy | TG |

---

## 11. Relationship to prior packs

| Prior | This stream |
|-------|-------------|
| ST#20 P04 / P05 | S05–S06, S11 reinforce mid-scale + 4-semitone back spacing |
| ST#20 P07–P08 / P11 | S06 bridge stiff/light rescue; mass-load vs mobility |
| ST#20 P14–P15 | S13–S15 live-back practical damping |
| ST#20 P17–P18 / falcate gap | S02–S04, S17 — richest falcate content yet (still no geometry pack) |
| Wolf W05–W08 | S05 mid-scale neighborhoods |
| Mobility M09 / mass warning | S06 mass-loading down from too-high fights responsiveness |

---

*See `CROSSWALK_TOOLBOX.md` and `GAPS_NOT_RECORDED.md`.*
