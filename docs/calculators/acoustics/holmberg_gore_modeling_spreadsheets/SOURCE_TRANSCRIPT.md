# Source extract — Holmberg Guitar Modeling Spreadsheets docs

**Working extract** from public Google Doc text export (not a legal archive).  
**Doc URL:** https://docs.google.com/document/d/1rRlBnYbhHHp0wK93A0Zaz6mokmCBfsiEiiuYb5ngZ9c/  
**Export captured:** 2026-08-04 via `/export?format=txt`  
**Author claims:** Copyright 2025 Gregory Holmberg; CC BY-SA 4.0; keep copyright + links when copying.  
**Book dependency:** Many modules require *Contemporary Acoustic Guitar* (Design) — compensation and frequency model especially.  
**Caveat:** Live Google Sheet formulas not re-verified here; this pack documents the *published documentation*.

---

## Identity & scope

Google Sheets implementations of Gore/Gilet equations. Calculable modules listed:

- Panel thickness, top and back (§ 4.5.3)
- Fret positions (§ 4.6.6)
- Fretboard dimensions (appendix AII 3)
- Neck shape (§ 4.6.7)
- Intonation compensation nut + saddle per string (§ 4.7.3)
- Frequency/SPL model, 4 DOF: Helmholtz air, top, back, sides (§ 2.4, AII 2)
- Sound hole size (§ 2.4.1.1)
- Brace stress and sizing, front and back (§ 4.4) — Holmberg notes experimental

Companion: Wood Properties spreadsheet (~290 species), ranked for fretboard, neck, soundboard, braces, bridge, back, sides, linings.

**Warning (author):** Not blueprints. Author has not built a guitar to prove the starter dimensions. Measure specific wood pieces and recalculate.

Version history (doc): 2024-03-11 initial; 2024-03-27 intonation redesign + classical falcate noCF; 2025-03-07 intonation-from-rig bugfix, E_nylon 2.9→28.4; 2026-03-30 falcate brace overall dims under saddle (not only 50 mm forward taper).

---

## Starter workbook presets (summary table in docs)

| Description | Braces | Top | Back/sides | Body W×L×D mm | Vol | Freq Hz | Monopole mobility | SPL dB |
|-------------|--------|-----|------------|---------------|-----|---------|-------------------|--------|
| Gore steel | Falcate KWP+CF | Engelmann | EIR | 390×490×115 | 13.9 | 90 170 214 | 17.0 | 76.8 |
| Gore steel | Falcate Yellow Poplar no CF | Engelmann | EIR | 390×490×115 | 13.9 | 90 170 214 | 16.4 | 76.6 |
| OM steel | X-braced Sitka no CF | Sitka | EIR | 381×492×106 | 13.3 | 101 170 214 | 14.2 | 76.1 |
| Classical nylon | Falcate KWP+CF | WRC | EIR | 360×490×125 | 14.1 | 97 190 233 | 23.4 | 75.3 |
| Classical nylon | Falcate Yellow Poplar no CF | WRC | EIR | 360×490×125 | 14.1 | 95 190 240 | 24.1 | 75.3 |

Metric system throughout (mm, kg, N, Pa). Green = inputs; yellow = adjustable targets; red = major results. Named cells (e.g. `t_tp`).

---

## Sheet modules (documentation order)

**summary** — name/description only; other fields mirrored.

**body** — effective top area + cavity volume (subtract blocks/linings). Enter length, lower bout, top area. Mottola “G” Thang / Sevy / weigh acrylic / CAD (Onshape examples: Gore Medium Steel-string, Martin OM).

**top_panel** — §4.5.3 thickness from square/flat panel: L, W, t, mass, long/cross/diagonal frequencies. Hold at 22.4% for long/cross; REW or similar. Vibrational stiffness target \(f\): steel top 75, steel back 55, trad classical top 60 / back 50, lattice classical top 40, flamenco back 37 (author technique — experiment). Same \(f\) → consistent frequency response across species; mass/damping still differ. Poisson averages OK (~0.377 / 0.048 tops). Master-grade steel 390×490 top mass hint &lt;170 g (book implication). Measure piece — species averages for comparison only.

**back_panel** — same method; steel \(f\)~55, classical ~50. Live-back density ceiling ~800 kg/m³; target mass often &lt;300 g.

**body (return)** — blocks, sides, linings, inactive/active areas → active areas + cavity volume → Helmholtz / bass.

**fretboard** — scale, fret count, nut width, margins, radii, saddle spread, fret height → conical FB dims, fret positions, sagitta, widths.

**neck** — depths at nut / F9, FB thickness, tumblehome; yellow shape params (§4.6.7) → printable/CAD templates.

**intonation** + **first…sixth** — §4.7.3. Common params: h_0, h_mid, string product, E_string (nylon/PVDF), neck ρ/E for parabola action model. Per string: MIDI note, h_12, L_extra, μ and k (manufacturer estimate vs measure-rig §4.7.3.1). Action models: measure all; circle+ellipse+line (book); parabola+line (**Holmberg experimental**); polynomial fit. Finger model: δ_0~0.5 mm; p_finger 75% finger / 85% flatpick. Minimize error_cents via Δn, Δs (LibreOffice solver). Targets cited: steel total &lt;6¢ all strings; nylon &lt;3¢. Nut-only-average forward + solve saddle as traditional compromise.

**model** + **freq_db** — 4-DOF FRF/SPL 60–300 Hz @ 0.5 Hz. Fit effective areas/masses to known guitar; then tune D, Kt, Kb, ms_added. Not necessarily predictive from design alone. Targets between scale notes (wolf avoidance). Exceptional steel top mobility &gt;14 (book p.1-89); back &gt;7 (p.2-41). Kt/Kb: back 2–3× top; keep uncoupled ft &lt; fb (~20–40 Hz gap). “Full monopole mobility” Holmberg extension includes air-stiffness term κAt².

**top_braces** — §4.4 stress/rigidity; **experimental** brace sizing. Composite beam I with modular ratio (author: book Table 4.4-2 wrong; Gore confirmed). Size for stress safety (~50% allowable) and Kt from model. Analyze at 50 mm forward of saddle. EI targets cited: classical 10–20, steel 45–50 N·m². Bridge rotation 2° target not successfully calculated here.

**back_braces** — size back braces to Kb; finalize soundhole + brace dims.

**Iterate after build** — refit model; adjust next guitar (depth, hole, braces).

---

## Author roadmap notes

Future hopes: tighter CAD↔model coupling; automatic resize of braces/hole from parametric CAD. Mentions Nicoletti and Rick Molloy browser tools for interactive 4-DOF intuition.
