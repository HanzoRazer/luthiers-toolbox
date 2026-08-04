# Source transcript (working copy) — Nicoletti tonewood parameters webinar

**Title (as supplied):** Acoustic guitar Tonewood parameters measurement and selection - French Guitar Luthiers  
**Event:** 2nd technical webinar for European Guitar Builders / French guitar luthiers (PLG)  
**Ingested:** Full supplied session (~0:00–~1:44); music/aside noise trimmed; Q&A condensed where repetitive  
**ASR / cleanup:** tonewood (not “100”); Schelleng; Caldersmith; Room EQ Wizard; UMIK/miniDSP; Lucchi meter; Chladni; dipoles/tripoles; fan bracing; archtop; Orchestra; live back; wolf; plectrum; hygrometry; Blu-tack/putty; Claudio Pagelli (audience magnets). “50 GPa” at 460 kg/m³ treated as probable **15 GPa** ASR (noted in gaps).

---

## Why a technical approach (~0:15–2:48)

Not necessary to build excellent instruments (decades of FFT-free excellence). Reasons to adopt: **consistency** (diagnose/compensate early; right wood for project; always good guitars with different characters); **learning/improvement**; **responsibility** (precious wood — make the most of it); **fun** / addictive different perspective.

## Dual role of tonewood (~2:48–4:15)

Structural: hold ~**70 kg** static string load for life. Acoustic: efficient vibrating machine from tiny string energy. Functions oppose each other — structural design important but **out of scope today**; focus vibro-acoustic tonewood parameters.

## Density (~4:15–5:33)

\(\rho\) = mass/volume. Simple but critical: impedance match/mismatch soundboard ↔ sides/back → radiating surfaces. Also “filter” / low-pass — especially bridge and bridge plate mass as small **EQ**.

## Stiffness + radiation coefficient (~5:33–10:13)

Young’s modulus \(E\) with density = two most important tonewood params → enter **radiation coefficient** (Schelleng **1963**, ~60 years). Defines energy needed to excite a plate; density appears inverse and **cubed** → density dominates radiating quality for soundboards.

Pacific Rim Tonewoods \(E\) vs \(\rho\) scatter: huge dispersion; grading helps but insufficient. Trend: higher \(E\) with higher density — do they compensate via thinner plate?

Spreadsheet simulations (spoken):
- ~**12 GPa**, **360** kg/m³ → target thickness / panel mass ~**136 g**, SRC ~**16**
- ~**15?** GPa (ASR “50”), **460** kg/m³ → similar thickness but **much higher** panel mass; SRC ~**14** (not compensating)
- To match mass at 2.2 mm would need ~**24 GPa** — off-trend / nonexistent  

Conclusion: for spruce soundboards, **density** may be the single most important parameter.

## Orthotropy (~10:13–12:57)

Long-grain stiffness usually ≥ **10×** cross-grain. Isotropic vs orthotropic spruce simulation: cross-bending dipole is **5th** mode isotropic vs **3rd** real orthotropic — Chladni confirms. Without measuring cross-grain stiffness, monopole \(f\) may match while dipole/tripole frequencies diverge → character changes. Select wood with 3D/orthotropic properties in mind.

## Damping / Q (~12:57–16:15)

Viscoelastic; appears under **vibration**, not static load. Coil+damper analogy; dissipated as heat. Spruce impulse Q ~**80** still ringing ~2 s; mahogany Q ~**30** largely gone ~1 s. Damping = inverse of Q. Efficient resonators want low damping in critical parts (string energy small).

## Mode Q&A — what dipoles sound like (~16:37–21:30)

Orchestra/Martin-like FRF example: air **T11**; monopoles involving soundboard/back (**live back**); dipoles ~**350** and **~450** Hz (cross vs long — order design-dependent); long tripole still important radiator; peaks can approach monopole SPL (~84 vs ~83 dB) → characterize timbre strongly.

X-brace + tone bars: cross/long dipoles often close ~350–400 Hz. Classical fan bracing + lower bridge: long dipole nearer monopole ~**250** Hz. Archtop projection: focus energy on monopole, less higher-mode SPL. Fingerstyle: more higher modes (overtones/beauty) vs projection — compromise. No single “best” dipole emphasis for steel-string.

Finished guitar: can measure FRF + Chladni to map peaks↔modes (not today’s main subject).

## How to measure (~23:12–30:02)

**Density:** dimensions + weight; thickness uniform.

**Stiffness:** center-weight deflection simple but static + limited orthotropic/shear info. Prefer **mic + FFT** near working frequencies. Tools: **Room EQ Wizard**; **UMIK / miniDSP** USB mic. Procedure in Nicoletti manual/articles; originated with **Graham Caldersmith**. Hold on **nodal lines**, tap **antinodes**; separate setups for long bending, cross bending, twist/shear. Chladni if unsure.

Spreadsheet (available with book): from mode frequencies → vibrational stiffness, target soundboard thickness & mass, SRC. **Vibrational stiffness** attributed to **Trevor Gore** (*Contemporary Acoustic Guitar Design and Build*, 2011/2013): imagine braces removed, board on infinite-mass chassis — target resonance anticipating final behavior. Heavy sides/back (IRW/ebony) → lower board \(f\); light mahogany → higher — impedance matching. Calibrate vibrational-stiffness target from your builds/side type. Time at start reduces end problems.

## Spectral “tap graphics” (~30:10–34:28)

Long-grain FRF is graphic of what tap hears. Cedar vs spruce: different mode density/overtones (after host correction: spruce clearer highs/attack; cedar smoother). Ebony B&S-like: stiff, high-Q low modes, few high harmonics → dark. Mahogany: richer mid high-order modes, higher damping than ebony, lighter → different character. Store spectra as wood library, not only equation inputs.

## Measuring damping (~34:35–45:12)

**Lucchi meter:** common but limited — ultrasonic (wrong band; damping frequency-dependent); measures system not pure material. Prefer FFT:

1. **Half-power bandwidth** on peak — needs high frequency resolution (avoid phone apps; free desktop software OK)  
2. **Logarithmic decrement** in time — precise; Nicoletti developing import/filter software (fitting error); not yet recommended without care  

Damping rises with frequency (example Q 25 @62 Hz vs 80 @330 Hz on same piece — as spoken). Marble + elastics on nodal lines can match expensive laser interferometer if setup good.

**Use of damping:** strumming → a bit more damping for headroom/precision under loud attack; fingerpicking → high Q / low damping for detail. Density+\(E\) already powerful; damping is fine-tuning, “not necessary” today for everyone.

**Headroom (Q&A):** how hard you can drive before soundboard saturates into unpleasant distortion (esp. high-mobility light tops + plectrum).

## Supplier / process Q&A (~45:35–1:03:48)

Tap-feel needs ~**3.5–4 mm** worked thickness; thicker plates hard to judge. Measure **half-plates** before joining (full thin joined plate \(f\) too low). Workflow: clean to ~4 mm → density + three modes → spreadsheet node positions → insert \(f\) values → set vibrational stiffness → target thickness/mass; batch measurement days. Aging: main \(E\)/\(\rho\) little change; high-frequency structure changes; **humidity** dominates (~**45%** RH target); uncontrolled RH invalidates comparisons. Spreadsheet speed of sound = \(\sqrt{E/\rho}\) — habit, **not** damping-related.

## Using data in the build (~1:03:55–1:18:22)

Three approaches:
1. Buy high-SRC wood (supplier-measured OK)  
2. Plan: set monopole targets → predict thickness/mass; denser wood for hard players, lower density for soft/fingerstyle  
3. Measure through build  

**Top-on-sides in mold (no back):** same mold always (mold mass affects \(f\)). Example fan design: shave central bars 220→**190** Hz monopole without moving dipoles/tripoles. For this model+mold, 190 at this stage returns to ~190 finished after excursions (close box ↑~220, bridge ↓, finish/saddle/pins/strings ↓) — **coincidence for this setup**, not universal. Shoot a bit stiff; hard to add stiffness later.

**Closed box:** A0 + top + back coupled; optionally tune opening; Chladni; bridge changes mode shapes (R&D).

**Finished:** wolf hard; **ETS** example **200 g** → ~**5 Hz** monopole shift, places monopole ~**170 Hz** clear of wolf. Spec sheet to customer: FRF, monopole mobility, equivalent mass, three main mode frequencies — relationship + lifetime reference + marketing; call for community **standards**.

## Late Q&A highlights (~1:19–1:44)

- Prefers impact mic over static plate deflection; won’t specify deflection weight  
- Tap location: completed guitar near **saddle** for full FRF; antinode for specific mode; monopole near bridge center / where bridge will be  
- Identify modes with Chladni if unknown  
- Brace tuning = small (couple mm headroom); don’t remove half a brace  
- Repair intake: check A0/monopole balance, higher-mode peaks, **wolves** (also partials; intonation; often 5th or 3rd/4th strings)  
- Spoken wolf search bands: air ~**90–120 Hz**; monopole ~**170–220 Hz**  
- Remedies: small mass/stiffness, bridge-pin material (couple grams), magnets (audience), putty on hot spots (~3 g); can’t erase resonances without killing sound; overbuilt commercial guitars hide wolves but sound boring  

---

*[End of supplied webinar extract.]*
