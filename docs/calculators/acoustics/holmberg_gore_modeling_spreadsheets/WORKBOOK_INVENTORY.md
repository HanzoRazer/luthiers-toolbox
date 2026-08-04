# Workbook inventory — Holmberg V4 `.xlsx` files

**Purpose:** Close **G-HM01** / **G-HM02** by inventorying the attached workbooks (sheet lists, named ranges, preset scalars, Wood Properties schema).  
**Captured:** 2026-08-04 · openpyxl `data_only` read of uploaded files  
**License (in-file):** © 2025 Gregory Holmberg · CC BY-SA 4.0  
**Rule:** Preset numbers are **examples in the workbook**, not Toolbox defaults (HM02). Binaries not committed to git (hashes below).

---

## Files inventoried

| Upload filename | Role | Bytes | SHA-256 |
|-----------------|------|------:|---------|
| `Classical_nylon_falcate_CF_V4_c015.xlsx` | Classical nylon falcate + CF braces | 1 789 931 | `d702c59978272f828facaafe423627fd72327dd558b82cb59058cc5185160b02` |
| `Medium_SS_falcate_noCF_V4_632b.xlsx` | Medium SS falcate, Yellow Poplar, no CF | 1 871 403 | `acad045a1aab0ffd361c60b0cbbdd429efd5e57b1f7c6f59964c8be1b94b44c7` |
| `Medium_SS_falcate_CF_V4_cdac.xlsx` | Medium SS falcate, KWP+CF | 1 799 126 | `1638c661b3aab3cc1686cb1dadf5d442c5fbcd1e6dd677828151a2823b547ef1` |
| `Wood_Properties_V1_cb3a.xlsx` | Companion species database | 2 413 969 | `3f55942d3605944343da60cf4effb67feb684f7d837c000747aa0b4efba18476` |

**Not in this upload set (still open as G-HM01 residual):** OM steel X-braced Sitka starter from the public docs table; second classical “Yellow Poplar no CF” starter if distinct from Medium SS noCF.

---

## 1. Guitar workbook structure

### Common sheets (all three)

`summary`, `body`, `top_panel`, `back_panel`, `fretboard`, `neck`, `intonation`, `model`, `top_braces`, `back_braces`, `freq_db`, `first`…`sixth`, `note`, `const`, `prefix`

### Variant sheets

| Workbook | Extra / order notes |
|----------|---------------------|
| Classical nylon CF | Standard set; `top_braces` before `freq_db` |
| Medium SS noCF | Extra **`deflection`** sheet; 338 named ranges |
| Medium SS CF | `freq_db` before `top_braces`; 327 named ranges |

### Named ranges

| Workbook | Count (approx.) |
|----------|----------------:|
| Classical nylon CF | 324 |
| Medium SS noCF | 338 |
| Medium SS CF | 327 |

Examples: `l_body`, `w_lower`, `V_cs`, `t_tp`, `f_air`/`f_top`/`f_back`, `Kt_actual`, `w_minor`/`w_major`, `δ_nk`, `p_Finger`, `E_nylon`, `db_average`, `l_scale`, …

---

## 2. Preset summary scalars (from `summary` + named cells)

| Field | Classical nylon CF | Medium SS noCF | Medium SS CF |
|-------|-------------------:|---------------:|-------------:|
| Name | Neo-classical flat-top | Medium SS flat-top | Medium SS flat-top |
| Description | 360 mm nylon falcate | OOO steel falcate | OOO steel falcate |
| Body L×W×D mm | 490×360×126 | 490×390×115 | 490×390×115 |
| Volume L | 14.06 | 13.86 | 13.85 |
| Soundhole Ø mm | **84** | **77** | **76** |
| Top species | WRC | Engelmann (note: exceptional) | Engelmann (exceptional) |
| Top braces | KBP+CF (named `KBP+CF` / ρ 411) | Yellow Poplar | KWP+CF |
| Back | EIR | EIR | EIR |
| Back braces | Sitka | Yellow Poplar | Sitka |
| Vibrational \(f\) top (Hz) | **60** | **75** | **75** |
| \(t_{tp}\) mm | 2.490 | 2.695 | 2.695 |
| Top mass g (summary) | 116.8 | 190.7 | 192.7 |
| \(K_t\) N/m | 41 447 | 48 706 | 49 346 |
| Top MM (book) s/kg·e-3 | **23.80** | **17.18** | **16.98** |
| Full MM top | 20.33 | 14.67 | 14.52 |
| Avg SPL dB | 75.32 | 76.94 | 76.75 |
| \(t_{bp}\) mm | 2.079 | 2.403 | 2.403 |
| Back mass g | 190.0 | 230.0 | **150.0*** |
| \(K_b\) N/m | 149 027 | 131 037 | 129 187 |
| \(K_b/K_t\) | 3.17 | 2.70 | 2.61 |
| Back MM | 9.00 | 8.73 | 8.85 |
| Target triad Hz (model) | 95 / 190.5 / 240 | 90 / 169.5 / 214 | 90 / 169.5 / 214 |
| Target IDs | 3 / 15 / 19 | 2 / 13 / 17 | 2 / 13 / 17 |
| Scale mm | 650 | 645.16 | 645.16 |
| Major brace w×h mm | 5.0 × 3.88 | 3.38 × 8.33 | 5.0 × 6.90 |
| Minor brace w×h mm | 5.0 × 2.58 | 3.38 × 5.55 | 5.0 × 4.60 |
| Safety factor | 0.5 | 0.5 | 0.5 |
| \(E_{nylon}\) / \(E_{PVDF}\) | 28.4 / 2.3 | 28.4 / 2.3 | 28.4 / 2.3 |

\*Medium SS CF `summary` back mass **150 g** looks like a manual override vs noCF’s ~230 g — treat as suspicious until verified (**G-HM10**).

Mobility units in-sheet: **`s/kg e-3`** (explicit) — still do not badge in Toolbox until G-R01/G-M09 / **G-HM04** closed.

---

## 3. Intonation compensation tables (from `intonation`)

Author note in-sheet: *“ToDo: how to verify these compensations?”*

### Classical nylon CF — total error **2.30 ¢** (under nylon &lt;3 ¢ claim)

| String | h₁₂ mm | Δn mm | Δs mm | Error ¢ |
|--------|-------:|------:|------:|--------:|
| first | 3.0 | 0.202 | 0.454 | 0.24 |
| second | 3.2 | 0.204 | 0.515 | 0.30 |
| third | 3.5 | 0.253 | 0.780 | 0.39 |
| fourth | 3.7 | 0.093 | 0.209 | 0.42 |
| fifth | 3.8 | 0.081 | 0.162 | 0.45 |
| sixth | 4.0 | 0.082 | 0.171 | 0.50 |
| **avg/total** | — | **0.153** | **0.382** | **2.30** |

### Medium SS noCF — total **3.18 ¢** (under steel &lt;6 ¢)

| String | h₁₂ | Δn | Δs | Error ¢ |
|--------|----:|---:|---:|--------:|
| first | 2.0 | 0.609 | 0.564 | 0.15 |
| second | 2.2 | 1.059 | 1.258 | 0.31 |
| third | 2.4 | 0.537 | 0.756 | 0.36 |
| fourth | 2.6 | 0.709 | 1.198 | 0.57 |
| fifth | 2.7 | 0.886 | 1.633 | 0.74 |
| sixth | 2.8 | 1.234 | 2.470 | 1.05 |
| **avg/total** | — | **0.839** | **1.313** | **3.18** |

### Medium SS CF — total **6.84 ¢** (**above** author’s steel &lt;6 ¢ band)

| String | h₁₂ | Δn | Δs | Error ¢ |
|--------|----:|---:|---:|--------:|
| first | 2.0 | 0.631 | 0.556 | 0.85 |
| second | 2.2 | 1.100 | 1.243 | 1.59 |
| third | 2.4 | 0.537 | 0.756 | 0.36 |
| fourth | 2.6 | 0.739 | 1.187 | 1.30 |
| fifth | 2.7 | 0.925 | 1.619 | 1.67 |
| sixth | 2.8 | 1.230 | 2.470 | 1.07 |
| **avg/total** | — | **0.860** | **1.305** | **6.84** |

→ CF steel preset may need re-solve before citing as “optimized” (**G-HM11**).

---

## 4. Wood Properties V1 — schema (**G-HM02** closed)

### Sheets

| Sheet | Type | Role |
|-------|------|------|
| `All` | data | Master table — **306** species rows (header rows 1–4) |
| `Softwoods` / `Hardwoods` | data | Filtered views |
| `E, R vs. ρ` / `Strength vs. ρ` / `Shrink vs. ρ` / `Hardness vs.ρ` | **chartsheets** | Scatter plots |
| `MacBeath` | data | Supplier-oriented notes/prices |
| `Top` / `Brace` / `Back` / `Sides` / `Bindings` / `Neck` / `Bridge` / `Fretboard` | data | Role-ranked / filtered species lists |
| `Chassis` | stub | “ToDo: implement as query” → see `Chassis 2` |
| `Chassis 2` | data | Chassis candidate list |
| `Constants` | params | Density band limits, Gore avg cross-freq, etc. |
| `onshape` | export | CAD material table (SI Pa) |
| `Empty` | template | Blank species layout |

### Named ranges (27)

`AllSpecies`, `PlateLength`, `PlateWidth`, `PlateThickness`, `TopFrequency`, `BackFrequency`, `TopArea`, `BodyLength`, `BodyWidth`, `AreaRatio`, `VolumeOfChassis`, `V_chassis`, `TopMass_Standard`, `FcrossTops`, `FdiagTops`, `FcrossBacks`, `FdiagBacks`, `VlrTop`, `VrlTop`, `VlrBack`, `VrlBack`, `StartBacks`, `EndTops`, `HearmonC1`, `HearmonC2`, `LS0_DouglasFir`, `LS_max`

### `All` column symbols (row 4)

`scientific`, `soft`, `native`, `cites`, `iucn`, `price`, `bend`, `J`, `ρ12`, `EL`, `RL`, `𝜈LR`, `𝜈RL`, `FL`, `CL`, `SR0`, `ST0`, `SV0`, `SL0`, `ΔLS0`, `λ`, `YMC`, `FC`, `EC`, `ELEC`, `FD`, `G`, plus computed `t`/`DL`/`Mt`/`Mb` for top & back target thickness/mass at fixed plate geometry.

### `Constants` samples

- Highest density for tops: **530 kg/m³**  
- Lowest density for backs: **450 kg/m³**  
- Freq. cross for tops: **88 Hz** (note: “Gore avg for Engelmann Spruce”)

**Toolbox policy:** do **not** import these averages into `wood_species.json` as FPL-attributed values — Holmberg aggregate / mixed sources; comparison-only (HM05 / HM14).

---

## 5. Implications for calculator port

1. Sheet spine in PROCESS_WORKFLOW matches real workbooks.  
2. Mobility display unit in presets is **s/kg × 10⁻³** — record for unit-profile work; still badge-blocked.  
3. Classical nylon compensation looks “solved”; Medium SS CF compensation exceeds author’s own steel band — do not ship those Δn/Δs as golden.  
4. Wood Properties is a **role-sorted species workbook**, not a substitute for per-billet measurement.  
5. OM X-braced starter still missing from this file set.

---

## Point cross-links

| Finding | Point / gap |
|---------|-------------|
| Workbooks inventoried | HM43 |
| Preset triad/mobility/SPL extracted | HM44 |
| Compensation tables extracted | HM45 |
| Wood Properties schema | HM46 |
| Medium SS CF total error &gt;6¢ | G-HM11 |
| CF back mass 150 g suspicious | G-HM10 |
| OM X / 2nd classical starter missing | G-HM01 residual |
