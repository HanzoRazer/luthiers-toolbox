# Tab-by-tab evaluation — Holmberg workbooks (session uploads)

**Date:** 2026-08-04  
**Method:** openpyxl read of every sheet in all six uploaded files; deep content dump of a representative guitar (`Medium_SS_falcate_noCF_V4`) plus all Wood Properties tabs; cross-check sheet order / named-range counts on the other four guitars.  
**Scope:** Structural + functional evaluation (what each tab does, inputs/outputs, issues). Not a line-by-line formula proof against the Gore book (**G-HM05** still open).  
**Point:** **HM49**

---

## Files evaluated

| File | Tabs | Named ranges |
|------|-----:|-------------:|
| Classical nylon falcate CF V4 | 20 | 324 |
| Classical nylon falcate noCF V4 | 20 | 325 |
| Medium SS falcate noCF V4 | **21** (+`deflection`) | 338 |
| Medium SS falcate CF V4 | 20 | 327 |
| OM SS Xbrace noCF V3 | 20 | 311 |
| Wood Properties V1 | 21 (4 chartsheets) | 27 |

---

## Color / UX legend (actual fills observed)

Docs claim light green / yellow / red. In these `.xlsx` files the palette is pastel RGB (not theme):

| Fill (approx.) | Role in practice |
|----------------|------------------|
| `#D9EAD3` | Soft green — user / measured inputs |
| `#FFF2CC` | Soft yellow — adjustable parameters / solver knobs |
| `#F4CCCC` | Soft red — major results |
| `#CFE2F3` | Soft blue — intermediate / alternate model columns |
| `#D0E0E3` | Gray — labels / section headers |
| `#EAD1DC` / `#FCE5CD` | Accent blocks (less common) |

**Note:** Excel `max_row` often ≈1000–1100 even when content ends near row ~50–200 (used-range inflation). Evaluation below uses content banners + occupied label rows, not inflated max_row.

---

## A. Guitar workbooks — every tab

Shared spine (all five guitars). Differences called out under each tab.

### 1. `summary`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Dashboard: mirrors body, panels, model, braces into one Property/Value/Units table (+ imperial) |
| **Inputs** | Name, Description (editable identity) |
| **Outputs** | Almost all formulas from other sheets: L/W/D, volume, hole Ø, thicknesses, masses, Kt/Kb, MM, SPL, triad Hz |
| **Verdict** | Read-only cockpit. Correct place to compare presets. Do not edit numeric cells here. |

### 2. `body`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Geometry → top area + cavity volume after subtracting head/tail blocks, sides, linings |
| **Key inputs** | `l_body`, `w_lower`, `A_top`, bout/waist (posterity), depths, block dims, `t_s`, `pm_s`, lining volumes |
| **Key outputs** | `V_cs` / liters, active areas, inside depth |
| **Pulls** | `t_top` / `t_back` from panel sheets |
| **Verdict** | Core Helmholtz driver. Area must be measured/CAD; default presets are design-specific. |

### 3. `top_panel`

| Field | Evaluation |
|-------|------------|
| **Purpose** | §4.5.3 thickness from billet metrology + vibrational stiffness target `f` |
| **Inputs** | Panel L/W/t/mass; F_long/F_cross/F_diag; ν; target `f` (60 nylon / 75 steel in these files) |
| **Outputs** | ρ, E_long/E_cross, SRC, G, **`t_tp`**, plate rigidity, cut-out mass |
| **Verdict** | Primary “measure your wood” sheet. Preset G10/G16 panel IDs are example billets, not universal. |

### 4. `back_panel`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Same method as top for back; target `f` ≈55 steel / 50-class classical in these files |
| **Outputs** | **`t_bp`**, E, SRC, mass |
| **Verdict** | Parallel to top_panel. Live-back density caution still applies (docs). |

### 5. `fretboard`

| Field | Evaluation |
|-------|------------|
| **Purpose** | §4.6.6 + AII.3 conical fretboard: positions, radius, width, sagitta per fret |
| **Inputs** | Scale, n_frets, nut width, margins, radii, saddle spread, fret wire dims |
| **Outputs** | Table Ln, r, spacing for frets 0…n (+ saddle) |
| **Verdict** | Pure geometry calculator. Presets: 645.16 mm steel / 650 mm classical; OM uses 18 frets / 14-fret join noted on summary. |

### 6. `neck`

| Field | Evaluation |
|-------|------------|
| **Purpose** | §4.6.7 neck-back shape: ellipse+circle+triangle blend (α,β,γ) at nut and F9 |
| **Inputs** | Depths, FB thickness, tumblehome, blend weights (must sum 100%) |
| **Outputs** | Coordinate tables for carve/CAD templates |
| **Verdict** | Shop template generator. Heavy yellow-parameter surface. |

### 7. `intonation`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Shared neck/string params + **summary table** of Δn/Δs / errors from `first`…`sixth` |
| **Inputs** | h_0, h_mid, string product, E_string, neck ρ/E, action-model weights (α_int, β, γ) |
| **Outputs** | Fc_total, int_error_total, per-string compensation summary |
| **Verdict** | Control panel for compensation. In-sheet ToDo: “how to verify these compensations?” |

### 8. `first` … `sixth` (six tabs)

| Field | Evaluation |
|-------|------------|
| **Purpose** | Per-string §4.7.3 compensation: manufacturer μ/k path **or** measure-rig path → optimize Δn, Δs |
| **Structure** | Open note/MIDI/freq → h_12 → manufacturer block → empty measure-rig block → choose k/μ → Δn/Δs → error sums + per-fret action/error table |
| **Critical finding** | Measure-rig cells empty → `k_meas` / `μ_meas` / ΔT show **`#DIV/0!`**. All five presets use **manufacturer** path (`k_manu` / `μ_manu`). |
| **Verdict** | Functional for steel EJ16-style manufacturer data; nylon measure-rig path not populated (**G-HM07**). Tabs are clones with different string constants. |

### 9. `model`

| Field | Evaluation |
|-------|------------|
| **Purpose** | 4-DOF FRF/SPL (§2.4): fit factors + knobs D, Kt, Kb, ms_added → hit air/top/back targets |
| **Inputs** | vib/piston factors; D; Kt; Kb; damping R*; Target IDs from `note` |
| **Outputs** | Coupled peaks, SPL, MM / full MM, uncoupled ft/fb gap, Kb/Kt |
| **Verdict** | Design heart. Fit≠predict warning still stands. Yellow knobs are the iteration surface. |

### 10. `freq_db`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Engine table: 60–300 Hz @ 0.5 Hz; complex denominators; SPL constants `r_ref`, `p_ref` |
| **Verdict** | Do not edit casually. Performance bottleneck in Google Sheets (docs). LibreOffice/Excel preferred for iteration. |

### 11. `top_braces`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Experimental brace size/stress/rigidity to hit model `Kt` at 50 mm forward of saddle |
| **Inputs** | Brace species ρ/E/F/G; n_major/minor; widths; triangle ratios; panel width at station |
| **Outputs** | Stress %, EI, Kt_actual, masses/volumes back to model |
| **Dialects** | Falcate books: rectangular heights; OM X V3: **triangle** major/minor heights; n_minor usable for fan experiments |
| **Verdict** | Solver-friendly (`w_minor`). Flag as Holmberg experimental, not pure Gore. |

### 12. `back_braces`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Size back braces / center brace to hit `Kb`; arch loft FYI |
| **Outputs** | Kb_actual, EI, Is splits, brace volumes |
| **Verdict** | Parallel to top_braces; includes scooped center-brace geometry (router-bit note). |

### 13. `deflection` (**only Medium SS falcate noCF V4**)

| Field | Evaluation |
|-------|------------|
| **Purpose** | Top deflection curve vs position (% / m): slope, angle, y |
| **Verdict** | Extra analysis tab not in other four guitars. Likely bridge-rotation / beam-shape exploration. Incomplete as a documented SOP in the Google Doc. |

### 14. `note`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Equal-temperament frequencies from A4; **between-note target IDs** for model |
| **Verdict** | Wolf-avoidance index. Changing A4 retunes the world. |

### 15. `const`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Unit conversions; E_steel; **E_nylon=28.4**; E_PVDF=2.3; ρ_air; c_air; Hearmon constants |
| **Issue** | Rows for E_nylon / E_PVDF are mislabeled “Density” in column A (symbols are correct). |
| **Verdict** | Global constants. Altitude: edit ρ_air / c_air here. |

### 16. `prefix`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Documentation of naming convention (A=area, t=thickness, suffixes `_tp`, `_nk`, …) |
| **Verdict** | Reference only — no calculations. |

---

## B. Guitar-to-guitar tab deltas

| Tab | CF classical | noCF classical | SS falcate noCF | SS falcate CF | OM X V3 |
|-----|--------------|----------------|-----------------|---------------|---------|
| `deflection` | — | — | **present** | — | — |
| Sheet order | braces→freq_db | braces→freq_db | braces→**deflection**→back | **freq_db** before braces | braces→freq_db |
| Brace shape | rect falcate | rect falcate | rect (+ ratio_hw) | rect falcate | **triangle X** |
| `first`… measure-rig | empty / #DIV/0! | empty / #DIV/0! | empty / #DIV/0! | empty / #DIV/0! | empty / #DIV/0! |
| Intonation path | manu (nylon E) | manu (nylon E) | manu steel EJ16 | manu steel | manu steel |

---

## C. Wood Properties V1 — every tab

| Tab | Type | Evaluation |
|-----|------|------------|
| **All** | data | Master **306** species × 37 cols (ρ12, EL, SRC, Poisson, strength, shrink, computed top/back t & mass) |
| **Softwoods** | filter | **73** softwood rows |
| **Hardwoods** | filter | **233** hardwood rows |
| **E, R vs. ρ** | chart | E / SRC vs density |
| **Strength vs. ρ** | chart | Strength vs density |
| **Shrink vs. ρ** | chart | Shrinkage vs density |
| **Hardness vs.ρ** | chart | Hardness vs density |
| **MacBeath** | data | **56** supplier-oriented priced rows |
| **Top** | ranked | **50** top candidates (mass-after-thickness sort intent) |
| **Brace** | ranked | **29** brace candidates (KWP Gore-first) |
| **Back** | ranked | **177** back candidates |
| **Sides** | ranked | **83** side candidates |
| **Chassis** | stub | Explicit **ToDo**: implement as query → see Chassis 2; partial list (~57) |
| **Chassis 2** | data | **83** chassis-oriented rows (query replacement) |
| **Bindings** | ranked | **30** binding candidates |
| **Neck** | ranked | **91** neck candidates |
| **Bridge** | ranked | **62** bridge candidates |
| **Fretboard** | ranked | **55** fretboard candidates |
| **Constants** | params | Density band limits; Gore avg F_cross/F_diag for Engelmann; Hearmon-related named ranges |
| **onshape** | export | **~205** materials in Onshape SI units (Pa) |
| **Empty** | template | Header only — **0** species rows |

**Verdict:** Role-sorted comparison workbook. Not FPL-canonical for Toolbox `wood_species.json`. Chassis sheet is unfinished by author’s own ToDo.

---

## D. Issues found in this tab audit

| ID | Issue | Where | Severity |
|----|-------|-------|----------|
| **G-HM07** (confirmed) | Measure-rig path empty → `#DIV/0!` on k_meas/μ_meas | `first`…`sixth` all guitars | Medium |
| **G-HM12** (new) | `const` labels “Density” for E_nylon / E_PVDF rows | `const` | Low (cosmetic) |
| **G-HM13** (new) | `Chassis` sheet unfinished (ToDo) | Wood Properties | Low |
| **G-HM14** (new) | `deflection` tab only on one starter; undocumented in Google Doc spine | Medium SS noCF | Low |
| Prior | SS CF intonation over-band; CF back mass 150 g | see G-HM10/11 | Medium |

---

## E. Port priority (from tab evaluation)

1. `top_panel` / `back_panel` — billet → thickness  
2. `body` — cavity volume  
3. `model` + `freq_db` — 4-DOF targets  
4. `top_braces` / `back_braces` — Kt/Kb (experimental flag)  
5. `intonation` + `first`…`sixth` — Δn/Δs (require measure-rig UX for nylon)  
6. `fretboard` / `neck` — geometry (already closer to existing Toolbox)  
7. Wood Properties role sorts — **comparison only**

---

## F. Coverage statement

**Yes — every tab in every submitted workbook was opened and classified.** Deep numeric sampling used Medium SS falcate noCF as the representative guitar engine; the other four guitars were verified for sheet inventory, named-range counts, and known preset deltas (WORKBOOK_INVENTORY). Wood Properties: every data/chart/template tab evaluated.
