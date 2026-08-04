# Annotated Notes  
## Holmberg — Gore/Gilet modeling spreadsheets (docs)

**Lane:** Instrument-building physics (primary) — math/equations for calculator port  
**Source:** Gregory Holmberg documentation (CC BY-SA 4.0) implementing Gore/Gilet Design volume  
**NO-CALC:** Not blueprints; measure wood; model fit≠predict; brace sheet experimental; mobility badges blocked on G-R01/G-M09

---

## 1. Identity & governance

### 1.1 Sheets implement selected Gore/Gilet Design equations  
**Classification:** **EP** / **TG** / **GH**

Modules: panel thickness, frets/FB, neck, nut+saddle compensation, 4-DOF FRF/SPL, soundhole, brace stress/sizing.

**Point ID:** HM01  

### 1.2 Spreadsheets are starting points, not cut lists  
**Classification:** **EP** / **GH**

Author has not built to prove starter dims; measure specific pieces and recalculate.

**Point ID:** HM02  

### 1.3 Book required for compensation + frequency model understanding  
**Classification:** **EP** / **GH**

Doc deliberately does not republish book theory.

**Point ID:** HM03  

### 1.4 License / attribution: CC BY-SA 4.0; keep copyright + original links  
**Classification:** **GH**

**Point ID:** HM04  

### 1.5 Companion Wood Properties sheet (~290 species) ranks parts by role  
**Classification:** **GH**

Soundboard sheet thickness→mass sort for comparison — not production thicknessing.

**Point ID:** HM05  

---

## 2. Workbook UX conventions

### 2.1 Metric SI inputs (mm, kg, N, Pa); green/yellow/red cell roles  
**Classification:** **GH**

Named cells (`t_tp`, etc.) preferred over A1 addresses.

**Point ID:** HM06  

### 2.2 Five public starter presets (Gore falcate / OM X / classical falcate ±CF)  
**Classification:** **EO** / **GH**

Carry sample triad Hz, mobility, SPL — **dialect examples**, not Toolbox globals.

**Point ID:** HM07  

---

## 3. Body geometry → cavity

### 3.1 `body` sheet: top area + cavity volume after interior subtraction  
**Classification:** **EP** / **TG**

Feeds Helmholtz / 4-DOF model.

**Point ID:** HM08  

### 3.2 Area sources: Mottola G-Thang, Sevy, weigh cutout, CAD (Onshape)  
**Classification:** **GH** / **SH**-adjacent measure tip

**Point ID:** HM09  

---

## 4. Panel thickness (§4.5.3)

### 4.1 Measure square/flat panel: L W t mass + long/cross/diagonal f  
**Classification:** **EP** / **TG**

Uniformity &lt;0.1 mm; scale ±1 g; hold at 22.4% span for long/cross; REW OK.

**Point ID:** HM10  

### 4.2 Vibrational stiffness target \(f\) sets thickness across species  
**Classification:** **EP** / **TG**

Doc examples: steel top 75 / back 55; trad classical 60/50; lattice top 40; flamenco back 37 — **author technique**; builders must calibrate to their finish targets.

**Point ID:** HM11  

### 4.3 Same \(f\) → consistent frequency response; mass/damping still differ loudness/sustain  
**Classification:** **EP** / **TG**

**Point ID:** HM12  

### 4.4 Poisson νLR/νRL weakly affect thickness (&lt;1%); use density-band averages if unknown  
**Classification:** **EP** / **GH**

**Point ID:** HM13  

### 4.5 Species-average thickness/mass tables are comparison-only — measure the billet  
**Classification:** **EP** / **TG** / **GH**

FPL CoV: density ~10%, E ~22% within species.

**Point ID:** HM14  

### 4.6 Steel 390×490 “master-grade” top mass hint &lt;170 g (book implication)  
**Classification:** **TG** / **OH** as global

Average Sitka often misses; exceptional light Sitka can compete with Engelmann.

**Point ID:** HM15  

### 4.7 Live-back density ceiling ~800 kg/m³; heavy rosewoods often too heavy/thin  
**Classification:** **TG** / **EO**

**Point ID:** HM16  

---

## 5. Fretboard & neck geometry

### 5.1 `fretboard`: scale → fret positions + conical radius/width/sagitta  
**Classification:** **EP** / **TG** (§4.6.6, AII 3)

**Point ID:** HM17  

### 5.2 `neck`: nut/F9 depths + tumblehome params → carve/CAD templates  
**Classification:** **EP** / **TG** (§4.6.7)

**Point ID:** HM18  

---

## 6. Intonation compensation (§4.7.3)

### 6.1 Need μ (mass/length) and k (unit stiffness) per string  
**Classification:** **EP** / **TG**

Manufacturer μ often inconsistent; k unpublished — steel E~207 GPa usable; nylon must be measured.

**Point ID:** HM19  

### 6.2 Prefer Gore measure-rig (§4.7.3.1) over manufacturer/literature E  
**Classification:** **EP** / **TG** / **GH**

Nylon plastic; E tension-dependent; published E sets under-compensate vs Mottola/book.

**Point ID:** HM20  

### 6.3 Action height per fret: measure (best) or model (book circle+ellipse+line / parabola / poly)  
**Classification:** **EP** / **TG** / **GH**

Parabola+line is **Holmberg experimental** (not in book); auto-adjusts with tension/neck E.

**Point ID:** HM21  

### 6.4 Finger model: δ_0≈0.5 mm; p_finger ≈75% finger / 85% flatpick  
**Classification:** **TG**

**Point ID:** HM22  

### 6.5 Minimize total cents error by Δn (offset) + Δs (tilt); solver recommended  
**Classification:** **EP** / **TG** / **GH**

Δn raises/lowers error curve; Δs tilts. LibreOffice 2-variable solver; Google solver 1-var only.

**Point ID:** HM23  

### 6.6 Cited achievable bands: steel &lt;6¢ total all strings; nylon &lt;3¢  
**Classification:** **EO** / **GH** (with full nut+saddle optimize)

Saddle-only traditional ~30¢ total; average-nut-forward + solve saddle ~5¢ — often “good enough.”

**Point ID:** HM24  

### 6.7 Worst cases: sixth string total; first fret local — optional 0.1 mm fret nudge  
**Classification:** **EO** / **GH**

**Point ID:** HM25  

---

## 7. Frequency / SPL model (§2.4)

### 7.1 Four DOF: air (Helmholtz), top, back, sides — `model` + `freq_db`  
**Classification:** **EP** / **TG**

Complex harmonic calc 60–300 Hz @ 0.5 Hz steps (slow in Google Sheets).

**Point ID:** HM26  

### 7.2 Model correctly *sensitive* when fitted; not necessarily *predictive* from design CAD  
**Classification:** **EP** / **TG** (§2.4.1.1)

Refit after build for next similar guitar.

**Point ID:** HM27  

### 7.3 Place air/top/back targets *between* scale notes (wolf avoidance)  
**Classification:** **EP** / **TG**

Use `note` sheet half-semitone IDs; avoid exact octave pairing of targets.

**Point ID:** HM28  

### 7.4 Primary knobs after fit: soundhole D, Kt, Kb, added side mass  
**Classification:** **EP** / **TG** / **GH**

Larger D → higher air f; larger V → lower air f; Kt/Kb dominate top/back; ms_added ~75 g per Hz top down + SPL effects.

**Point ID:** HM29  

### 7.5 Keep uncoupled ft &lt; fb; ~20–40 Hz gap; back stiffness ~2–3× top  
**Classification:** **EP** / **TG** / **GH**

Crossing / back-dominating peaks = bad energy steal even if “targets hit.”

**Point ID:** HM30  

### 7.6 Book “exceptional” steel mobility: top Y &gt;14; back Y &gt;7 (cited pages)  
**Classification:** **TG**

**Toolbox:** do **not** badge until unit profile locked (G-R01/G-M09).

**Point ID:** HM31  

### 7.7 “Full monopole mobility” adds air-stiffness κAt² to effective K  
**Classification:** **GH** / **OH** (usefulness TBD by author)

Implies efficiency also helped by smaller effective At and larger V.

**Point ID:** HM32  

### 7.8 Model outputs soundhole diameter + target Kt/Kb for brace sheets  
**Classification:** **EP** / **TG** / **GH**

**Point ID:** HM33  

---

## 8. Brace sizing / stress (§4.4 — experimental sheet)

### 8.1 `top_braces` sizes for (1) stress safety and (2) target Kt  
**Classification:** **GH** / **OH** (experimental vs book)

Book recommends consulting textbooks; Holmberg implements composite-beam stress/rigidity.

**Point ID:** HM34  

### 8.2 Analyze at line 50 mm forward of saddle; modular-ratio I corrected vs book Table 4.4-2  
**Classification:** **GH** / **EO** (Gore email confirmation claimed)

**Point ID:** HM35  

### 8.3 EI guidance cited: classical ~10–20; steel ~45–50 N·m²  
**Classification:** **TG** / **GH**

**Point ID:** HM36  

### 8.4 Measure brace wood E (deflection or frequency); species average unsafe  
**Classification:** **EP** / **TG**

Factory CNC tops vary ~2 semitones in one Taylor study cited — wolf risk.

**Point ID:** HM37  

### 8.5 CF overlay braces: lower mass / stress vs all-wood for same Kt; mobility benefit  
**Classification:** **EO** / **GH** / **TG**

Poplar no-CF can hit stiffness with higher mass/stress fraction.

**Point ID:** HM38  

### 8.6 Bridge rotation 2° target: measurement exists in book; calculation here failed (&lt;1°)  
**Classification:** **TG** / **GH** gap

**Point ID:** HM39  

### 8.7 `back_braces` → Kb; finalize hole + brace dims; refit after first build  
**Classification:** **EP** / **GH**

**Point ID:** HM40  

---

## 9. Cross-tool ecosystem

### 9.1 Interactive 4-DOF cousins: Nicoletti tool; Rick Molloy tool (browser)  
**Classification:** **GH** pointer

**Point ID:** HM41  

### 9.2 Long-term hope: parametric CAD areas/volumes → auto model + brace/hole resize  
**Classification:** **OH** / **GH**

**Point ID:** HM42  

---

## 10. Workbook file inventory (V4 `.xlsx` — 2026-08-04)

See [`WORKBOOK_INVENTORY.md`](./WORKBOOK_INVENTORY.md) for hashes, full tables.

### 10.1 Three guitar starters + Wood Properties V1 inventoried on disk  
**Classification:** **EO** / **GH**

Sheets match docs spine; noCF adds `deflection`; ~324–338 named ranges each.

**Point ID:** HM43  

### 10.2 Preset scalars confirmed: \(f\)=60 nylon / 75 steel; triads 95/190.5/240 vs 90/169.5/214  
**Classification:** **EO**

Mobility shown as **s/kg e-3** (top MM ~17–24 in these presets).

**Point ID:** HM44  

### 10.3 In-sheet compensation tables: classical 2.30¢; SS noCF 3.18¢; SS CF **6.84¢**  
**Classification:** **EO**

SS CF exceeds author’s steel &lt;6¢ guidance; sheets mark “ToDo: verify compensations.”

**Point ID:** HM45  

### 10.4 Wood Properties: 306 species on `All`; role sheets Top/Brace/Back/…; 27 named ranges  
**Classification:** **GH**

Comparison/ranking only — not FPL-attributed Toolbox canonical data.

**Point ID:** HM46  

### 10.5 OM SS X-brace noCF V3: Collings OM1-patterned; triad 101/169.5/214; hole 97 mm; top MM ≈14.2  
**Classification:** **EO** / **GH**

14-fret join; Sitka/Sitka no CF; triangle X brace heights (~5.75×13.8 major); compensation total 3.04¢. Contrasts falcate Medium SS (smaller hole, higher MM).

**Point ID:** HM47  

### 10.6 Classical nylon falcate noCF V4: WRC + Yellow Poplar; hole 80 mm; top MM ≈24.1; error 2.48¢  
**Classification:** **EO** / **GH**

Same body/triad as CF classical (95/190.5/240) but smaller hole than CF (80 vs 84), slightly higher MM, larger average Δn/Δs. Completes docs Get-started five-guitar set.

**Point ID:** HM48  

### 10.7 Tab-by-tab audit of all six session uploads  
**Classification:** **EO** / **GH**

Every sheet opened/classified — see [`TAB_BY_TAB_EVALUATION.md`](./TAB_BY_TAB_EVALUATION.md). Confirms measure-rig `#DIV/0!` on all string tabs; `deflection` only on Medium SS noCF; Wood Properties `Chassis` ToDo; pastel fill roles.

**Point ID:** HM49  

---

## Point index

| ID | Title |
|----|-------|
| HM01 | Implements Gore/Gilet Design equations |
| HM02 | Starting points, not cut lists |
| HM03 | Book required for hard modules |
| HM04 | CC BY-SA attribution rules |
| HM05 | Wood Properties companion sheet |
| HM06 | Metric + named green/yellow/red cells |
| HM07 | Five starter presets (examples only) |
| HM08 | Body area + cavity volume |
| HM09 | Area measurement options |
| HM10 | Panel metrology for thicknessing |
| HM11 | Vibrational stiffness target f |
| HM12 | Same f, different mass/damping |
| HM13 | Poisson weakly coupled |
| HM14 | Measure billet; averages for compare |
| HM15 | &lt;170 g steel top mass hint |
| HM16 | Live-back density ceiling ~800 |
| HM17 | Fretboard geometry module |
| HM18 | Neck shape module |
| HM19 | String μ and k required |
| HM20 | Prefer measure-rig for strings |
| HM21 | Action models incl. experimental parabola |
| HM22 | Finger pressure / δ_0 |
| HM23 | Optimize Δn + Δs |
| HM24 | Cited cents bands / compromises |
| HM25 | Sixth string / first fret worst |
| HM26 | 4-DOF FRF/SPL engine |
| HM27 | Fit-sensitive, not predictive |
| HM28 | Targets between notes |
| HM29 | Knobs D, Kt, Kb, ms_added |
| HM30 | ft&lt;fb; Kb~2–3 Kt |
| HM31 | Exceptional Y citations (badge-blocked) |
| HM32 | Full monopole mobility extension |
| HM33 | Outputs hole + Kt/Kb |
| HM34 | Experimental brace sizing goals |
| HM35 | 50 mm station; modular-ratio fix |
| HM36 | EI band citations |
| HM37 | Measure brace E |
| HM38 | CF vs all-wood brace trade |
| HM39 | Bridge rotation calc gap |
| HM40 | Back braces + post-build refit |
| HM41 | Nicoletti / Molloy interactive cousins |
| HM42 | CAD auto-coupling roadmap |
| HM43 | V4 xlsx workbooks inventoried |
| HM44 | Preset f / triad / MM scalars confirmed |
| HM45 | Compensation tables + SS CF over-band |
| HM46 | Wood Properties schema (306 spp) |
| HM47 | OM X-brace V3 preset (101 Hz air, 97 mm hole) |
| HM48 | Classical nylon falcate noCF preset |
