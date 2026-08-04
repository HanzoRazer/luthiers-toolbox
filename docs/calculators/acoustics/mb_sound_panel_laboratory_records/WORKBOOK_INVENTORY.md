# Workbook inventory — MB Sound / TPC panel laboratory records

**Purpose:** Inventory session-uploaded lab `.xlsx` files (hashes, sheet lists, batch scalars).  
**Captured:** 2026-08-04 · openpyxl read of uploads  
**Rule:** Binaries not committed. Prefer complete laboratory records over the compact 17-row subset.

---

## Files inventoried

| Upload filename | Role | Bytes | SHA-256 | `xl/media` |
|-----------------|------|------:|---------|----------:|
| `Alpine_Spruce_Complete_Laboratory_Record_5637.xlsx` | Alpine spruce complete lab | 1 471 659 | `fabf9e694b559bee439e0bd239ae0c55ff8748d3e8aa2e2e8c8be43594e4c481` | 44 |
| `Red_Cedar_Complete_Laboratory_Record_88af.xlsx` | Red cedar complete lab | 1 482 463 | `6bb5355da5a4402d3ddec7bdf9f428bb1e0d54a584a536aa6be5f8cfb795c291` | 44 |
| `Torrefied_Adirondack_Complete_Laboratory_Record_2e32.xlsx` | Torrefied Adirondack complete lab | 1 519 227 | `5e293e5c0bae685fc4d0b230e5bc0aaa899c7377918dad710e4f1975065b3289` | 44 |
| `Red_Cedar_30_Year_Drying_Complete_Laboratory_Record_d367.xlsx` | 30-year dried red cedar complete | 2 455 267 | `da9aeee4998405c52418c5619717a45d751db465ddf3b4759621039004c6078a` | 98 |
| `30_Year_Aged_Red_Cedar_MB_Sound_0323.xlsx` | Compact subset (17) | 12 191 | `aed223ad18b58b04277af7f31dbd39d2b37c869006751764c9d8f988eb170098` | 0 |
| `30_Year_Aged_Red_Cedar_MB_Sound_864b.xlsx` | **Duplicate** of `*_0323` | 12 191 | `aed223ad18b58b04277af7f31dbd39d2b37c869006751764c9d8f988eb170098` | 0 |

---

## 1. Complete-lab tab spine

| Tab | Present (Alpine / Red / Torr / 30yr) |
|-----|--------------------------------------|
| README | ✓ / ✓ / ✓ / ✓ |
| Specimen Master | ✓ / ✓ / ✓ / ✓ |
| Acquisition Procedure | ✓ / ✓ / ✓ / ✓ |
| Summary vs Detailed | ✓ / ✓ / ✓ / **—** |
| Capture Audit | ✓ / ✓ / ✓ / ✓ |
| Batch Statistics | ✓ / ✓ / ✓ / ✓ |
| Spectral Sheet Archive | ✓ / ✓ / ✓ / ✓ |

Compact 4-tab: `30-Year Red Cedar`, `Batch Summary`, `Source Pairing`, `Notes`.

---

## 2. Specimen Master schema (complete books)

Common columns (names vary slightly on 30-year book):

Sample ID · Analyzer Sample Name · Material · L/W/t mm · Mass g · Density kg/m³ · Nodal Lines mm · Resonance Hz · Time Constant ms · Log Decrement · Q Factor / Sustain · Fitting % · Young’s Modulus / Stiffness GPa · Radiation Coefficient · Recording Length s · Visualized Length s · Peak Amplitude dBFS  

**30-year extras:** Displayed vs Calculated Density; Displayed vs Calculated Radiation; Review Notes; acquisition flags inline on master.

---

## 3. Batch scalars (from Specimen Master; detailed-analyzer path)

`Batch Statistics` sheets hold MIN/AVERAGE/MAX/STDEV formulas that are **uncached** in these files (`data_only` → blank). Values below recomputed from master rows.

| Cohort | n | ρ avg (kg/m³) | ρ range | f avg (Hz) | f range | Q avg | E avg (GPa) | SRC/RC avg |
|--------|--:|-------------:|---------|----------:|---------|------:|------------:|-----------:|
| Alpine Spruce | 22 | 409.1 | 338.4–499.3 | 65.2 | 58.5–75.0 | 152.6 | 11.12 | 12.80 |
| Red Cedar | 22 | 342.2 | 295.6–375.7 | 55.1 | 42.9–84.1 | 147.9 | 6.28 | 12.44 |
| Torrefied Adirondack | 21 | 438.4 | 398.4–494.2 | 81.2 | 74.5–90.3 | 185.3 | 13.03 | 12.47 |
| 30-yr Red Cedar (complete) | 49 | 312.4 | 268.5–356.1 | 57.2 | 50.8–66.1 | 215.7 | 6.18 | 14.19† |
| 30-yr compact subset | 17 | 310.2 | 278.7–343.7 | 58.5 | 51.4–66.1 | 214.1 | 5.84 | 13.94 |

† Radiation n=37 on complete 30-year book (12 blank / Review Notes).  
Compact IDs 000024–000040 are the first 17 rows of the complete 49.

---

## 4. Capture anomalies (in-workbook)

| Book | Issue IDs | Highlights |
|------|-----------|------------|
| Alpine | AS-001…003 | Optional 0.1 Hz resonance display drift; no numeric arrays; no env metadata |
| Red Cedar | RC-001…004 | Q 132.8 vs 134.4 on 000005; 0.1 Hz on 000021; name OCR on 000020 |
| Torrefied | CAP-001…004 | **Missing 000002**; invalid 000008 pair; RC 12.1 vs 12.4 on 000014 |
| 30-year complete | ARC-001…004 | 99 screenshots → 49 specimens + 1 duplicate summary; faint fields blanked |
| Compact | Notes 1–4 | Same transcription caveats; no image archive |

---

## 5. Relation to other session uploads

Holmberg Gore modeling starters + Wood Properties V1 are inventoried under [`../holmberg_gore_modeling_spreadsheets/WORKBOOK_INVENTORY.md`](../holmberg_gore_modeling_spreadsheets/WORKBOOK_INVENTORY.md) — different corpus (equation engines, not TPC panel cards).
