# Source transcript (working copy) — EGB July 2022 measuring & tuning

**Title (as supplied):** Measuring and tuning the performances of the acoustic guitar - EGB webinar July 2022  
**Ingested:** Full supplied session (~0:15–~1:35); music/tech glitches trimmed; Q&A condensed  
**ASR / cleanup:** Room EQ Wizard; miniDSP; Chladni; monopole; dipoles; wolf; Larrivée; OM-28; Les Paul; ES-335; putty; 4DOF; Jacques Perrin / Fred Ponce / APLG as spoken organizers. Deflection spoken “zero zero one … zero zero two millimeters” → **0.01–0.02 mm**.

---

## Framing (~0:15–1:14)

Not heavy theory — books/articles on site already cover detail; PDF available (take notes optional). Instrument on hand for demos. Part 1: measurement system; Part 2: example characterizations.

## Why measure (~1:20–2:51)

Many makers treat measurement as R&D only. Nicoletti: even if already satisfied with instruments, use as **quality control** — photograph what you do; ensure each outgoing guitar performs correctly without necessarily changing the build method.

## What to measure (~2:57–4:30)

1. **Frequency response** — most important, relatively simple  
2. **Monopole mobility** — very useful, not hard  
3. **Chladni** — mostly R&D / troubleshoot  

Bridge rotation can be folded into monopole mobility (not always separate). Wood-parameter measurement interesting but **out of scope** (future webinar).

## FRF concept (~4:37–7:32)

Studio monitor: flat SPL vs f (faithful, low distortion). Guitar: peaked FRF — musical instrument, different evaluation keys. Overlay fretboard open-string intervals: main peaks sit in fretted range (centuries of optimization). Each peak = a resonance.

## Main resonances (~7:38–14:19)

Spring–mass systems. Typical peaks:
- **A0 / air** ~**100 Hz** (air spring; opening air mass)  
- **Soundboard monopole** — pistonic (FEA animation); usually second peak; most important  
- Optional **active back** peak if light and near monopole frequency  
- **Long dipole** then **cross dipole** (X-brace Martin-type; antiphase poles)  

Higher modes design-dependent; classical differs. Graph often to **1 kHz** — controllable modes; ~50 dB down from monopole already; no community standard for upper limit yet.

## FRF measurement system (~14:30–24:15)

Impact hammer (often eraser rubber) — hammer tip affects bandwidth (see article). **miniDSP** USB mic (~$100) with calibration file; lab-checked. Software: **Room EQ Wizard** (free), file database. Hold guitar by neck; mic **~25 cm** (close field: high SPL, low room reflection). Method: **~32 averages** for hand-tap repeatability (frequencies stable). Tap around **saddle** for instrument FRF; can tap elsewhere for modes. Damp strings (fingers/foam). Can go to ~1 cm for local mode hunt. Live: overlay played notes vs peaks (air ~105–106 between frets; monopole between notes).

## Mastering FRF — PLG checklist (~24:27–30:08)

Check: main-mode frequencies match project intent; wolf risk; peaks not in bad harmonic relation; presence/absence of radiating higher modes.

Example placement care: air **106**, monopole **180** vs open A 110 / harmonic 220 — good clearance; avoid stacking peaks on fundamental+octave (e.g. 212). Best playing space **between** resonances. Heavy tops hide wolves but reduce responsiveness. Higher modes always exist physically (Chladni) but may not radiate if board heavy / bracing suppresses them — big timbre effect; not better/worse universally.

## Stability / levers (~30:22–36:50)

Seasonal humidity/dome: small \(f\) shifts (dome↑ → stiffer → \(f\)↑). Aging of FRF: little change in ~5 years measuring experience (open research). A0: change soundhole volume/size (example purfling ring → **106 Hz**). Monopole: thickness, scallop braces, side mass, bridge-pin mass (~**5 g** bone vs plastic can make/break wolf). Modes **coupled** — Trevor Gore **4DOF** box simulator: changing top/back shifts air mode too.

Remove brace material / soften → peak \(f\) **down**; add mass → \(f\) down; going **up** harder (need lighter+stiffer). Don’t go too low. Edge thinning near sides also lowers \(f\).

## Monopole mobility (~40:26–42:27)

Can’t cut out monopole mass. Jig: micrometer on platform; apply ~**1 kg** at board center; measure deflection; **plug soundhole**; measure uncoupled board \(f\); simple math → equivalent mass, compliance, monopole mobility (ease of driving board).

**Spoken deflection range under ~1 kg: ~0.01–0.02 mm.** (Q&A later confirms ~1 kg; Excel available.)

## Chladni (~42:33–45:11)

Phone sine generator; ~$30 BT amp; **small** full-range speaker (focus); oregano/basil. Match FRF peak → trace mode. LED inside relates pattern to bracing — need very heavy bracing to override what the plate “wants”; shows active regions for tweaks.

## Characterizations (~45:17–55:54)

| Pair / guitar | Notes (as spoken) |
|---------------|-------------------|
| Martin D28 vs LX1E | D28 much higher SPL; A0 ~106 vs ~147; D28 strong ~380/600–700 (tone-bar asymmetry); LX heavy, few high modes (travel + feedback) |
| D28 vs Larrivée | Same outward shape/woods; equiv. mass ~**79 g** vs ~**103 g**; A0 ~106 vs ~90; Larrivée smooth, few high modes; wolf weak despite ~163 near high E |
| OM-28 vs D28 | Similar spectral layout but OM ~**6 dB** lower SPL; heavy mass like D28; scalloped more compliant (δ spoken **0.11**); mobility similar; fewer high modes; 184 near F |
| Archtop (Benedetto-style) | Maple B&S; top ~5.5–6 mm dome → 3.3–3.5 recurve; A0~135, monopole~220; mid focus; few high modes |
| Responsive X (~68 g) vs ES-335-like vs Les Paul | Solid heavy LP almost no acoustic FRF; semi-acoustic shows mid peaks |

## Selective putty fix (~56:01–57:58)

Nylon: long tripole ~**606 Hz** too hot (high E 12th); **5 g** putty far from monopole — kills that peak, rest of FRF nearly identical.

## Q&A highlights (~58:05–1:35)

- Mobility: 1 kg; δ typically **0.01–0.02 mm**; plug hole; Excel for \(m\) and \(Y\); string tension little effect  
- Standards + customer spec sheets (modes, FRF, parameters) vs industry  
- Chladni sine ≈ linear superposition of modes in practice  
- Taylor edge channel: measured δ ~**0.15** and **0.13 mm** — flexible but still fairly heavy tops; mobility not exceptional in his sample  
- Thinning: compliance↑ and mass↓ oppose — \(f\) may not fall as expected  
- Stage measuring: top glued to rims (fixed edges) before back/bridge  
- **Troughs** between peaks: cleaner sustain (away from low impedance at resonance)  
- Prefer miniDSP+REW over random condenser/phone; start by measuring finished guitars **without** changing the build  
- Semi/solid electric: acoustic hammer FRF less useful; prefer electrical/pickup measurements  

Article: *Measuring and tuning the performances of the acoustic guitar* on research page; Appendix A = software setup.
