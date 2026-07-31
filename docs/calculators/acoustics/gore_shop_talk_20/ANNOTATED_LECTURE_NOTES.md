# Annotated Engineering Lecture Notes  
## Trevor Gore — Shop Talk Live Stream #20

**Host:** Robbie O’Brien  
**Guest:** Trevor Gore  
**Context:** Post modal-tuning masterclass (two sessions, 27 students total); falcate-bracing video filmed the same week  
**Scope of this document:** Substantive teaching content only — explanations, heuristics, caveats, design philosophy. Giveaways, sponsor banter, and travel small-talk excluded.  
**Processing rule:** Preserve *why*, not only *what*. Formulae appear only when Gore stated them or when they are required to make a teaching point actionable.

---

## 0. Session architecture (what kind of knowledge this is)

This stream is not a linear lecture. It is a **masterclass Q&A + closed-box FRF demo** after an in-person modal-tuning week. The knowledge density is highest in:

1. Measurement method comments over class photos (uncoupled top, Chladni, monopole mobility)
2. Q&A answers that restate Gore’s priority stack for a “finished” guitar
3. The Visual Analyzer demo on the falcate body (targets 100 / 180 / 226 Hz)
4. Design-philosophy asides (live back, X vs falcate, free-top tuning, Spanish makers)

Treat each answer as a **unit of practice**: question → Gore’s reasoning → classification → Toolbox destination.

---

## 1. Modal analysis principles

### 1.1 Isolate the uncoupled top before interpreting body modes  
**Source timestamps:** ~9:36–9:53  

**Teaching point.** Plugging the soundhole and tapping into a spectrum analyzer isolates the **uncoupled top resonance**. That is a different measurement object from the closed-box coupled system (top + air + back + sides).

| Field | Value |
|-------|-------|
| Classification | **EP** + **TG** measurement procedure |
| Caveat | Do not confuse uncoupled-top peaks with finished-guitar A0 / T(1,1)₂ / T(1,1)₃ peaks |
| Toolbox destination | Measurement procedure + guided lab step (“isolate uncoupled top”) |
| Tap Tone Pi destination | Capture mode with metadata: `soundhole_plugged=true`, stage=`uncoupled_top` |

**Why it matters.** Much amateur “top tuning” collapses these stages. Gore’s workflow keeps them distinct so design moves act on the right degree of freedom.

---

### 1.2 Tune one mode without moving another  
**Source timestamps:** ~10:17–10:40  

**Teaching point.** A core final-tuning skill is **moving one modal frequency while leaving another alone**, specifically so box resonances do not land on scale tones.

| Field | Value |
|-------|-------|
| Classification | **TG** practical methodology grounded in **EP** modal independence heuristics |
| Caveat | Independence is approximate; cross-coupling always exists once the box is closed |
| Toolbox destination | Guided laboratory workflow + design rule (“mode-selective voicing”) |
| Empirical layer | Which brace edits move which modes — shop corpus, not a calculator |

**Design philosophy.** Final voicing is not “raise everything until loud.” It is selective surgery against a scale-tone map.

---

### 1.3 Chladni frequencies and FRF peaks are the same physical modes  
**Source timestamps:** ~24:10–25:20  

**Question (Stanley):** How does SRC relate to frequency analysis of tops?  
**Clarification in chat:** Sound Radiation Coefficient (SRC), not “spectrum response curve.”

**Gore’s answer (as stated):** Interpreting the intent as “do Chladni pattern frequencies correlate with spectrum-analyzer FRF peaks?” — **yes, strongly**. Frequencies where Chladni patterns appear most strongly should match FRF peaks from tap testing.

| Field | Value |
|-------|-------|
| Classification | **EP** (mode identity across visualization methods) |
| Caveat | SRC itself is a *material / radiation* index, not a frequency. The verbal confusion in chat is itself a knowledge-base hazard — keep SRC and modal frequency vocabularies separate. |
| Toolbox destination | Documentation clarification + lab cross-check procedure |
| Note | Schelleng-style radiation ratio already exists in materials scoring; do not overload that field with modal-frequency meaning |

---

### 1.4 Chladni symmetry is not a virtue by itself  
**Source timestamps:** ~23:42–24:08  

**Teaching point.** Chladni patterns **do not have to be symmetrical** to be “effective.” Asymmetric bracing (Martin-style X; classical fan) produces asymmetric Chladni patterns. If you want symmetry, the easiest path is a **symmetric bracing scheme** — do not fight the structure you built.

| Field | Value |
|-------|-------|
| Classification | **TG** recommendation + **EO** structural consequence |
| Common misconception addressed | “Symmetrical Chladni = better guitar” |
| Toolbox destination | Knowledge-base entry under Chladni interpretation; bracing design rule |
| Empirical layer | Pattern family → expected nodal asymmetry (X / fan / falcate / lattice) |

---

### 1.5 Cross-dipole / cross-tripole often “look after themselves”  
**Source timestamps:** ~1:00:15–1:01:17  

**Teaching point.** Gore does **not** usually target specific frequencies for cross-dipole and cross-tripole on his steel-strings. They fall out of the bracing pattern and typically do not create wolf problems.

**Classical exception.** First-string sound is often supported by a resonance near the first-string frequency range; the **cross-tripole** is especially useful there. If that support exists, “you’re going to be doing okay.”

| Field | Value |
|-------|-------|
| Classification | **TG** practice; classical support role is **EO** / **TG** |
| Caveat | “No target” ≠ “no importance.” It means *don’t micromanage* those modes the way you micromanage A0 / T(1,1)₂ |
| Toolbox destination | Design rule with instrument-family switch (steel vs classical) |
| Empirical layer | Observed cross-tripole bands that support first-string response |

---

### 1.6 Neck mass/stiffness barely moves body resonances (on Gore’s bolt-on tilt necks)  
**Source timestamps:** ~36:36–37:35  

**Teaching point.** Adding the neck structure does not seem to alter body resonant frequencies much. Neck modal frequencies (from neck stiffness and mass) don’t dominate body resonances. Priorities: neck strong enough under string pull, geometry correct — not “tune the neck to a frequency.”

| Field | Value |
|-------|-------|
| Classification | **EO** / **TG** (stated for his construction system) |
| Caveat | May not transfer blindly to glued Spanish heels, different mass ratios, or extreme light necks |
| Toolbox destination | Knowledge-base caveat near neck/body coupling models |
| Not a calculator | Do not invent a neck-frequency optimizer from this remark |

---

## 2. Guitar acoustics theory

### 2.1 Monopole mobility: \(1/\sqrt{km}\)  
**Source timestamps:** ~25:26–26:06  

**Teaching point.** Bridge attachment changes closed-box readings **significantly** because the bridge adds **both stiffness and mass**. Monopole mobility is:

\[
\mu_{\text{monopole}} \propto \frac{1}{\sqrt{k\,m}}
\]

Adding the bridge increases \(k\) and \(m\), so mobility drops.

| Field | Value |
|-------|-------|
| Classification | **EP** (as stated by Gore); **TG** shop consequence |
| Caveat | Measuring FRF / mobility on a closed box **without** the bridge is informative but not final |
| Toolbox destination | **Missing first-class concept today** — empirical model + measurement procedure, not just “monopole frequency” |
| Tap Tone Pi | Prefer driving-point / bridge-region mobility capture with stage tags `no_bridge` / `bridge_on` |

**Design philosophy.** Loudness potential is not “thin top.” It is high mobility at the right frequencies without landing on scale tones.

---

### 2.2 Live back vs non-live back: tone vs volume trade  
**Source timestamps:** ~28:21–29:07  

**Teaching point (nutshell).**

- A **live back** tends to produce **more peaks** in the FRF from roughly **300–1000 Hz**, which Gore associates with more “alluring” / satisfying tone.
- A live back also **absorbs some energy from the top**, yielding a **slight volume loss**.
- A **non-live (stiffer / less radiating) back** tends to give **more volume**, less of that mid/upper modal richness.

| Field | Value |
|-------|-------|
| Classification | **TG** recommendation framed as **EO** trade-off |
| OH component | Aesthetic preference (“vanilla” vs “alluring”) is taste |
| Toolbox destination | Design rule + guided decision workflow (tone-first vs volume-first) |
| Code gap | Coupled 2-osc / 3-osc models exist; builder-facing live-back methodology is thin |

---

### 2.3 Lattice bracing and “vanilla” high-frequency response  
**Source timestamps:** ~27:18–27:56  

**Teaching point.** Lattice-braced guitars often show strong low modes and **little activity in the upper FRF** (curve tapers down). That can mean a “vanilla” sounding guitar. That can be desirable — e.g. John Williams / Smallman lattice intent: sound from technique, not from an active instrument spectrum.

| Field | Value |
|-------|-------|
| Classification | **EO** / **TG** interpretation; historical example **EO** |
| Caveat | “Vanilla” is descriptive, not pejorative in Gore’s framing |
| Toolbox destination | Knowledge-base entry: bracing family → spectral character heuristic |
| Empirical layer | FRF peak density 300–1000 Hz by bracing family |

---

### 2.4 X-bracing scoops mids; falcate restores them  
**Source timestamps:** ~37:41–39:52  

**Teaching point (broad brush, Gore’s words).** Traditional asymmetric X-bracing tends to **suppress cross-dipole, cross-tripole, and long-dipole**, thinning the midrange → “scooped mids.” Symmetric designs (falcate is principally symmetric) operate differently and put mid frequencies back into the sound; flatter FR more like classical evenness.

| Field | Value |
|-------|-------|
| Classification | **TG** / **EO** (explicitly “broad brush”) |
| Historical note | Martin popularized asymmetric X when gut→steel; copied because it worked and people liked it |
| Toolbox destination | Design philosophy doc + bracing pattern knowledge; **falcate geometry is currently missing** |
| Empirical layer | Spectral mid energy X vs falcate vs fan |

---

### 2.5 Wolf notes = high admittance on a scale tone  
**Source timestamps:** ~43:42–45:13  

**Teaching point.** If a main resonance (main air or main top) lands on a scale tone, you get a **wolf note**: at that frequency the top has **high admittance** to string energy. Energy drains from the string quickly → **loud but short** note that breaks evenness across the fretboard.

**Avoidance rule.** Tune main resonances **midway between two scale-tone frequencies**.

| Field | Value |
|-------|-------|
| Classification | **EP** mechanism + **TG** design rule |
| Common misconception | “High admittance is always good” — good for coupling, bad when it creates a local wolf |
| Toolbox destination | Design rule + guided lab (scale-tone collision map). WSI ingest exists; **scale-tone avoidance as primary design practice is the gap** |
| Tap Tone Pi | Peak report + nearest scale-tone distance / wolf candidate flags |

---

### 2.6 Closed-box coupling changes everything  
**Source timestamps:** ~32:24–34:51  

**Teaching point.** Between free top and finished instrument, multiple large changes occur:

1. Gluing top to sides/back assembly (boundary condition change)
2. Adding the bridge (mass + stiffness)
3. Closing the box → **coupling among top, air, back, sides**

Therefore free-top tap tuning is, “to all intents and purposes,” **pointless** for hitting finished targets — unless the receiving assembly is *identical* in stiffness, mass, weight, and glue-up every time (which almost nobody achieves).

| Field | Value |
|-------|-------|
| Classification | **TG** strong recommendation grounded in **EP** coupling |
| Caveat | Free-plate measurements still useful for *material / process control* and γ calibration — Gore’s claim is about **tuning-to-pitch as a finished-guitar proxy** |
| Toolbox destination | First-class knowledge page + voicing-stage UX warnings (`braced_free_plate` ≠ `assembled_in_box`) |
| Empirical layer | Stage-to-stage frequency deltas from shop corpus |

---

### 2.7 Bridge adds stiffness *and* mass; putty cannot fake it  
**Source timestamps:** ~1:01:23–1:02:06  

**Teaching point.** Poster putty (or a taped-on bridge) at bridge mass **cannot** imitate finished frequencies before finishing. Putty/tape adds **mass only**. A glued bridge adds **stiffness and mass**. No rigid connection ⇒ no stiffness contribution.

| Field | Value |
|-------|-------|
| Classification | **EP** + **TG** lab caveat |
| Common misconception | “Preload with clay to preview bridge-on frequencies” |
| Toolbox destination | Measurement procedure “don’ts”; empirical model of Δf from bridge install |
| Related demo observation | Bridge-on drops T(1,1)₂ on the order of **~10–12 Hz** in the falcate demo case (**EO**) |

---

### 2.8 Aging / playing-in timeline  
**Source timestamps:** ~13:14–14:20  

**Teaching point.**

- Short term: quite rapid tonal change as a new guitar goes under tension — first **minutes** (usually only the builder hears this).
- Begins to stabilize after about a **week**.
- Changes slow drastically afterward.
- Longer-term studies exist (Gore recalled University of New South Wales work; could not name papers on air).

| Field | Value |
|-------|-------|
| Classification | **EO** (timeline); literature pointer **OH** pending citation recovery |
| Toolbox destination | Knowledge-base / experimental-drift notes; not a calculator |
| Empirical layer | Time-series FRF archives (already philosophically aligned with acoustics measurement archive types) |

---

### 2.9 Terrified / torrefied wood  
**Source timestamps:** ~12:01–13:13  

**Teaching point.** Torrefied wood is essentially **pre-aged**: somewhat more brittle, somewhat stiffer, somewhat less dense — a fast path toward “old wood” behavior. Downside: harder to glue, glue-failure risk. Gore’s practice: he does **not** use it; plain wood gives “plenty good enough” response.

| Field | Value |
|-------|-------|
| Classification | **EO** material effects; **TG** personal practice; comparative preference **OH** |
| Toolbox destination | Materials KB caveat (glueability / process risk), not an acoustic superiority claim |
| Forbidden inference | Do not encode “torrefied = better” as a design rule |

---

### 2.10 Double tops under Gore analysis  
**Source timestamps:** ~10:41–11:13  

**Teaching point.** Gore has not personally applied his analysis suite to double tops; others have using his course techniques. Principle: a double top still has to behave as a guitar — otherwise it would not sound like one.

| Field | Value |
|-------|-------|
| Classification | **OH** / **TG** boundary of experience; principle of modal homology **EP**-adjacent |
| Toolbox destination | Knowledge-base: transferable principles, non-claims about double-top specifics |

---

## 3. Practical tuning methodology

### 3.1 Gore’s priority stack for a “nice guitar”  
**Source timestamps:** ~30:10–31:15 (bridge-rotation question)

When asked how to change bracing to move bridge rotation from 1.5° to 2°, Gore reframed:

1. **Resonant frequencies in the right places — not on scale tones**
2. **High monopole mobility**
3. **Intonation / compensation so it plays in tune**

If those are right, **do not worry about 1.5° vs 2° bridge rotation** — you don’t hear that; you *do* hear resonances, mobility, and intonation.

If the top is still too stiff (mobility too low): **lower brace height** (fastest). Carbon-fiber-capped braces make that hard — look for other methods.

| Field | Value |
|-------|-------|
| Classification | **TG** design philosophy (priority stack); brace-height edit **TG** heuristic |
| Toolbox destination | Guided workflow decision tree; design rules ranked |
| Anti-pattern | Optimizing secondary geometry metrics while primary acoustic targets are unmet |

---

### 3.2 Design first, then closed-box trim  
**Source timestamps:** ~34:51–35:21  

**Teaching point.** Do the tuning work:

1. **In design** — so frequencies land *more or less* right initially  
2. **After the box is closed** — using Gore’s book techniques to bring resonances to targets  

Not on the free top.

| Field | Value |
|-------|-------|
| Classification | **TG** methodology |
| Toolbox destination | Build-sequence recommendation + voicing stage gates |
| Empirical layer | “As-designed vs as-closed” residual distributions |

---

### 3.3 Canonical target triad from the demo (mid-scale-tone)  
**Source timestamps:** ~50:00–52:04  

On the falcate demo body **without bridge**, Gore read approximately:

| Peak | Role (Gore’s labels) | Demo reading | Intended finished neighborhood |
|------|----------------------|--------------|--------------------------------|
| 1 | Main air / Helmholtz | ~102 Hz | ~100 Hz |
| 2 | Main top T(1,1)₂ | ~192 Hz | ~180 Hz after bridge (~−10–12 Hz) |
| 3 | Back+top T(1,1)₃ | ~226 Hz | ~226 Hz (4-semitone separation from ~180) |

**Idealized “good numbers” he stated for this box (taste-dependent but “almost ideal”):**  
**100 Hz / 180 Hz / 226 Hz** — each nearly midway between scale tones.

Also: lowering the top peak by adding the bridge **cross-couples** and tends to pull the air peak down slightly (toward ~100 Hz).

Four-semitone separation between main top and the next (back-involved) peak is the spacing heuristic he used on-air.

| Field | Value |
|-------|-------|
| Classification | **TG** target set for this body/context; scale-tone midpoints **EP**+**TG**; Δf≈10–12 Hz bridge drop **EO** |
| Caveat | “Ideal is to your own taste” — do not freeze 100/180/226 as universal law for all body sizes |
| Toolbox destination | Consolidate into plate/voicing calibration tables as a **named Gore mid-scale triad**, distinct from other style targets already in code |
| Empirical layer | Body-style variants of the triad; bridge-install deltas |

---

### 3.4 Selective stiffening of upper-bout back  
**Source timestamps:** ~42:53–43:37  

**Teaching point.** With Gore’s standard back bracing, the **upper bout of the back does not move much**. He has not needed special isolation of live-back activity to the lower bout. If upper back interferes with design intent, stiffen it (height/mass of early back braces is one approach suggested by the questioner; Gore blesses stiffening if needed).

| Field | Value |
|-------|-------|
| Classification | **EO** / **TG** for his system |
| Toolbox destination | Live-back lab note; back-brace design heuristic |

---

## 4. Measurement workflows

### 4.1 Closed-box FRF with Visual Analyzer (demo SOP)  
**Source timestamps:** ~46:19–52:12  

**Procedure as demonstrated:**

1. Use **Visual Analyzer** (Silent Soft; Gore uses early **v9.0.6**).
2. Setup details on Gore’s website / book / online course.
3. Hit **Capture Spectrum**.
4. Tap the box ~**10 times** (10 buffers).
5. Inspect especially the first **~1 kHz**.
6. Identify peaks: air, T(1,1)₂, T(1,1)₃ (back-coupled).
7. Interpret **before bridge** as a *challenge preview*, not finished values.
8. Watch for “grass” (noise / double-hits filling buffers).

**Platform caveat:** Visual Analyzer is Windows-oriented. Mac: limited native options (Audacity weaker); Wine/emulator workaround mentioned.

| Field | Value |
|-------|-------|
| Classification | **TG** measurement workflow |
| Toolbox destination | Guided laboratory workflow (software-agnostic steps + recommended stack) |
| Tap Tone Pi destination | Primary modern measurement authority replacing ad-hoc Visual Analyzer for Toolbox users — **same stage semantics** |
| Docs destination | Lab SOP under `docs/calculators/acoustics/` |

---

### 4.2 Monopole mobility measurement context  
**Source timestamps:** ~9:14–9:19; ~25:26–26:06  

Class photos included monopole-mobility measurement of the top. Combined with §2.1: always annotate whether bridge/neck are attached.

| Field | Value |
|-------|-------|
| Classification | **TG** workflow requirement |
| Toolbox / Tap Tone Pi | Mandatory metadata on mobility samples |

---

### 4.3 Chladni excitation hardware (DIY sig gen)  
**Source timestamps:** ~1:04:24–1:06:37  

**Parts list (principle):**

- Variable frequency generator module  
- Frequency counter / display module  
- ~30 W Class-D amplifier  
- Power supply  
- Loudspeaker: ~4 in / 100 mm, 30 W RMS, free-air capable (car-audio sources suggested)  

Instructions historically on **ANZLF** (“DIY SIG GEN” search). Kits change over time; principle remains.

| Field | Value |
|-------|-------|
| Classification | **TG** lab hardware recipe |
| Toolbox destination | Measurement procedure appendix (optional hardware path alongside shaker/speaker modern setups) |

---

### 4.4 Historical ear method (Fleta example)  
**Source timestamps:** ~1:02:07–1:04:16  

Spanish makers without formal science still avoided scale-tone resonances — by ear / trial-and-error. Gore’s Fleta (~1962) example: tap response lands **exactly between scale tones**; internal evidence of sanding fan-brace tops; presumed matching against a reference string tuned to the midpoint.

| Field | Value |
|-------|-------|
| Classification | **EO** historical instrument evidence; method reconstruction **OH**/plausible **TG** inference |
| Toolbox destination | Design philosophy / pedagogy: scientific methods formalize what great ears already hunted |
| Validation technique | Compare modern FRF targets to documented historical instruments |

---

## 5. Design philosophy

### 5.1 Acoustic specification over timber-cutter specification  
**Source timestamps:** ~29:25–29:59  

Gore’s two-volume *Contemporary Acoustic Guitar Design and Build*:

- **Vol. 1:** acoustic theory — what must be true for a guitar to sound good  
- **Vol. 2:** build methods that hit an **acoustical specification**, not a lumber-cutting specification  

| Field | Value |
|-------|-------|
| Classification | **TG** design philosophy |
| Toolbox destination | Product north-star language for Acoustics / Voicing / Plate Design surfaces |
| Governance note | Aligns with “empirical knowledge layer” over proliferating geometry-only calculators |

---

### 5.2 Hear the guitar before optimizing secondary metrics  
**Source timestamps:** ~30:16–31:15  

Bridge-rotation Q is the exemplar: secondary geometric KPIs are subordinated to audible modal/mobility/intonation outcomes.

| Field | Value |
|-------|-------|
| Classification | **TG** |
| Toolbox destination | Guided workflow: “listen / measure primary targets first” |

---

### 5.3 Transferable vibration principles across guitar types  
**Source timestamps:** ~40:12–41:05  

Gore does not build archtops; still argues the vibration principles transfer to hollow-body instruments. Archtop builders have reported the books useful.

| Field | Value |
|-------|-------|
| Classification | **TG** / **OH** on transfer completeness |
| Toolbox destination | Knowledge-base: principle transfer vs pattern transfer (do not auto-apply falcate to archtops without corpus) |

---

### 5.4 Tilt neck ≈ elevated board (functional analogy)  
**Source timestamps:** ~21:41–22:37  

No falcate classical with elevated fingerboard in his shop, but small-body classicals with **tilt neck** (user-adjustable neck angle via wheel through soundhole) are “not dissimilar” functionally to elevated fretboard geometry goals.

| Field | Value |
|-------|-------|
| Classification | **TG** analogy |
| Toolbox destination | Neck design KB; not an acoustics calculator |

---

## 6. Construction heuristics

| ID | Heuristic | Class | Notes |
|----|-----------|-------|-------|
| H1 | Lower brace height to raise monopole mobility when top is too stiff | **TG** | Fastest stiffness reduction if brace design allows |
| H2 | CF-capped braces block easy height reduction | **EO**/**TG** | Choose alternate stiffness-reduction paths |
| H3 | Want symmetric Chladni → start with symmetric bracing | **TG** | Don’t sand asymmetry into a deliberately asymmetric structure expecting miracles |
| H4 | Want scooped-mid steel-string dialect → asymmetric X is the historical path | **EO** | Cultural/market path dependence, not destiny |
| H5 | Want mids back / flatter FR → consider symmetric (e.g. falcate) | **TG** | Broad brush |
| H6 | Live back for tone/peak density; non-live for volume | **TG** | Explicit trade |
| H7 | Don’t torrefy expecting magic; accept glue risk | **TG** practice | Materials process caveat |
| H8 | Upper back usually quiet in Gore back systems; stiffen only if it interferes | **EO**/**TG** | |
| H9 | Nut + saddle compensation together for low intonation error | **TG** | See §7 |
| H10 | Hit targets by design + closed-box trim; not free-top pitch matching | **TG** | |

---

## 7. Nut compensation (intonation physics in the stream)

**Source timestamps:** ~18:30–21:21; demo ~52:56–55:43  

### Mechanism
Guitars often play sharp on frets **1–2–3** even when open strings and 12th-fret intonation are correct. Cause: larger fret spacing near the nut → pressing the string deflects a longer span → tension rise → sharp notes. Pressing lighter avoids sharp but kills clean fretting.

### Nut compensation effect (critical teaching point)
Moving the nut toward the first fret shortens the string → you **drop open-string tension** to restore open pitch → that lower tension **affects all frets**, not only 1–2. So nut compensation is **global**, not a first-fret-only patch. Combined with saddle compensation → very small frequency error across the board. Once heard, hard to go back.

Capo demo claim: capo at 7th still stays in tune without drastic retuning on a compensated instrument.

| Field | Value |
|-------|-------|
| Classification | **EP** deflection/tension mechanism; **TG** strong recommendation; “hard to go back” **EO**/**OH** |
| Toolbox destination | Already has nut/saddle compensation calculators & theory docs — add this **global-tension explanation** to builder-facing copy |
| Not missing as math | Missing as *guided why* in places |

---

## 8. Common misconceptions (explicitly corrected in-stream)

| Misconception | Correction | Class |
|---------------|------------|-------|
| Free-top tuned to a note survives assembly | It generally does not; coupling + bridge dominate | **TG**/**EP** |
| Chladni must be symmetrical | No; match bracing intent | **TG** |
| High admittance on a played note is always good | Produces wolf (loud/short) if on scale tone | **EP**/**TG** |
| Nut compensation only fixes frets 1–2 | Affects whole fingerboard via tension reset | **EP**/**TG** |
| Clay/putty bridge preview = glued bridge | Mass-only ≠ mass+stiffness | **EP**/**TG** |
| Optimize bridge rotation angle as a primary goal | Prioritize modal placement, mobility, intonation | **TG** |
| More low-mode amplitude always better | May indicate weak high-mode structure / “vanilla” spectrum | **TG** interpretation |
| Torrefied wood is required for excellence | Gore: plain wood sufficient; glue downside | **TG** practice |
| Neck should be tuned to a target frequency | Geometry/strength first; body modes barely shift | **EO**/**TG** |
| Scientific modal work is alien to traditional makers | Historical instruments show intentional mid-scale placement | **EO** |

---

## 9. Experimental observations (from demo + anecdotes)

1. **Falcate demo body (no bridge):** ~102 / 192 / 226 Hz → predicted easy path to ~100 / 180 / 226 after bridge and coupling (**EO** on one instrument).  
2. **Bridge install Δf on T(1,1)₂:** order of **10–12 Hz** down (**EO**).  
3. **Cross-coupling:** dropping top peak also reduces air peak somewhat (**EO**/**EP**).  
4. **Four-semitone** spacing heuristic between ~180 and ~226 (**TG** spacing rule used on-air).  
5. **Fleta ~1962:** mid-scale main resonances + sanded fan braces (**EO** on that instrument).  
6. **Playing-in:** minutes → ~1 week → slow (**EO**).  
7. **Lattice upper FRF:** often sparse (**EO** class observation).  

---

## 10. Build sequence recommendations (derived)

Recommended sequence consistent with Gore’s answers (not a verbatim checklist from one monologue):

1. **Design** plate/bracing/air targets so closed-box modes land near mid-scale goals for the body style.  
2. Build back/sides to controlled stiffness/mass (repeatability matters if any free-plate correlation is expected).  
3. Close the box; measure FRF (10-tap averaged spectrum).  
4. Identify A0, T(1,1)₂, T(1,1)₃; map vs scale tones.  
5. Apply **mode-selective** voicing (change one mode with minimal collateral).  
6. Install bridge knowing **mass+stiffness** shift; re-measure; expect ~10 Hz-class movement on main top (order-of-magnitude from demo).  
7. Confirm monopole mobility adequate; if not, reduce brace height if possible.  
8. Choose live vs non-live back intentionally (tone peak density vs volume).  
9. Complete nut + saddle compensation for temperament accuracy.  
10. Validate evenness (no wolfy scale tones) and spectral character to taste.

| Field | Value |
|-------|-------|
| Classification | Synthesis of **TG** points (sequence is editorial assembly of his rules) |
| Toolbox destination | Guided laboratory / build-sequence workflow |

---

## 11. Validation techniques

| Technique | Purpose | Class |
|-----------|---------|-------|
| Plug-hole uncoupled top tap | Isolate top DOF | **TG** |
| Closed-box 10-buffer FRF | Peak ID + grass rejection | **TG** |
| Chladni at FRF peak frequencies | Mode shape confirmation | **EP**/**TG** |
| Scale-tone midpoint check | Wolf avoidance | **TG** |
| Pre/post bridge FRF | Quantify mass+stiffness shift | **TG**/**EO** |
| Mobility with documented boundary conditions | Loudness potential | **TG** |
| Historical instrument FRF | Pedagogy / sanity | **EO** |
| Time-series after stringing | Playing-in characterization | **EO** |

---

## 12. Point catalog (compact index)

Each ID is stable for crosswalk referencing.

| ID | Point (short) | Category | Class |
|----|---------------|----------|-------|
| P01 | Uncoupled top via plugged soundhole | Modal / Measurement | EP/TG |
| P02 | Mode-selective final tuning | Modal / Tuning | TG |
| P03 | Avoid scale-tone resonances (wolves) | Theory / Tuning | EP/TG |
| P04 | Mid-scale targets; demo triad 100/180/226 | Tuning / Validation | TG/EO |
| P05 | Four-semitone A0–adjacent spacing heuristic | Tuning | TG |
| P06 | Bridge Δf ~10–12 Hz on T(1,1)₂ | Experimental | EO |
| P07 | Bridge = mass + stiffness | Theory | EP |
| P08 | Putty cannot simulate glued bridge | Misconception | EP/TG |
| P09 | Monopole mobility \(1/\sqrt{km}\) | Theory | EP |
| P10 | Mobility & modal placement outrank bridge-rotation angle | Philosophy | TG |
| P11 | Lower brace height to raise mobility | Construction | TG |
| P12 | Free-top pitch tuning largely useless as finished proxy | Theory / Misconception | TG/EP |
| P13 | Design then closed-box trim | Build sequence | TG |
| P14 | Live back → more 300–1000 Hz peaks, more tone, less volume | Theory | TG/EO |
| P15 | Non-live back → more volume | Theory | TG/EO |
| P16 | Lattice often “vanilla” upper spectrum | Experimental | EO/TG |
| P17 | X scoops mids via dipole/tripole suppression | Theory | TG/EO |
| P18 | Falcate/symmetric restores mids | Theory | TG |
| P19 | Chladni need not be symmetric | Modal | TG |
| P20 | Chladni freqs ≡ FRF peaks | Modal | EP |
| P21 | SRC ≠ modal frequency (vocab hazard) | Misconception | EP |
| P22 | Cross-dipole/tripole usually not explicitly targeted (steel) | Tuning | TG |
| P23 | Classical first-string support via cross-tripole | Tuning | TG/EO |
| P24 | Neck add-on barely shifts body modes (his system) | Experimental | EO/TG |
| P25 | Nut compensation is global via tension | Theory | EP/TG |
| P26 | Nut + saddle for low error | Construction | TG |
| P27 | Torrefaction: stiffer/lighter/brittle; glue risk; Gore skips | Materials | EO/TG |
| P28 | Playing-in: minutes → week → slow | Experimental | EO |
| P29 | Double-top: principles transfer; Gore limited personal data | Philosophy | OH/TG |
| P30 | Archtop: principles transferable; not his product line | Philosophy | TG/OH |
| P31 | Tilt neck functional cousin to elevated FB | Construction | TG |
| P32 | Upper-back isolation usually unnecessary in his backs | Construction | EO/TG |
| P33 | Visual Analyzer 10-tap FRF SOP | Measurement | TG |
| P34 | DIY Chladni sig-gen architecture | Measurement | TG |
| P35 | Traditional makers hit mid-scale by ear (Fleta) | Validation / History | EO |
| P36 | Acoustic spec > timber-cutter spec | Philosophy | TG |
| P37 | High low-mode amplitude with weak highs ⇒ interpret spectrum | Modal | TG |
| P38 | Mac spectrum tooling limited vs Visual Analyzer | Measurement | EO |

---

## 13. What this stream is *not*

- Not a complete substitute for Gore & Gilet Vol. 1–2.  
- Not a universal constant table for all body sizes.  
- Not a license to automate taste (live vs non-live, falcate vs X).  
- Not tap_tone_pi measurement protocol detail — only shop-demo practice.

Use it as an **empirical knowledge and methodology layer** that tells the Toolbox *what to guide* and *what not to reduce to a single number*.

---

## 14. Suggested reading / external pointers mentioned

- Trevor Gore & Gerard Gilet, *Contemporary Acoustic Guitar Design and Build* (2 vols.)  
- Gore website: Visual Analyzer setup notes; books; courses  
- Online course: Guitar Analysis and Testing (filmed with Robbie O’Brien)  
- Silent Soft Visual Analyzer v9.0.6 (Gore’s preferred early build)  
- ANZLF: DIY SIG GEN instructions  
- UNSW: long-term guitar aging studies (citation not recovered in-stream)  
- Falcate bracing process video (filmed that week; includes live back / closed-box measurement)

---

*End of annotated lecture notes. See `CROSSWALK_TOOLBOX.md` for implementation mapping.*
