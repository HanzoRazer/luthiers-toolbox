# Annotated notes — MB Sound / TPC panel laboratory records

**Point prefix:** `MB`  
**Lane:** Physics (lab corpus / plate-intake schema)  
**Source:** Session `.xlsx` laboratory records (see SOURCE_TRANSCRIPT)

---

## MB01 — Corpus is screenshot transcription, not raw DSP archive

Analyzer UI screenshots → Excel. Plots embedded as JPEG; Acquisition flags mark raw audio / waveform / FFT bins / IR arrays **unavailable**.

## MB02 — Detailed analyzer is primary numerical source

README / Notes across books: detailed Tonewood Parameters Characterization screen wins; summary cards kept for audit only.

## MB03 — Nicoletti TPC Rev 1.5 method string

Acquisition Procedure records software/method as *Tonewood parameters characterization – Rev 1.5 – Giuliano Nicoletti* (Alpine / Red / Torrefied). Cross-link webinar pack N69–N99.

## MB04 — Signal 1 / Mono capture convention

All detailed screens in these books use Signal 1, Mono source selection.

## MB05 — Specimen Master is the import surface

Geometry (L/W/t), mass, ρ, nodal mm, resonance \(f\), time constant, log decrement, Q, fit %, \(E\) GPa, radiation coefficient, peak dBFS.

## MB06 — Alpine Spruce batch (n=22)

IDs 000001–000022 (ABA-C / ABA-W). Mean ρ≈409 kg/m³, \(f\)≈65 Hz, Q≈153, \(E\)≈11.1 GPa, RC≈12.8. Summary vs Detailed: all match.

## MB07 — Red Cedar batch (n=22)

IDs 000001–000022 (CED-C / CED-W). Mean ρ≈342, \(f\)≈55, Q≈148, \(E\)≈6.3, RC≈12.4. Retained mismatches: Q 132.8 vs 134.4 (000005); \(f\) 50.5 vs 50.4 (000021).

## MB08 — Torrefied Adirondack batch (n=21)

Expected 000001–000022; **000002 missing** (CAP-001). Mean ρ≈438, \(f\)≈81, Q≈185, \(E\)≈13.0, RC≈12.5. Invalid 000008 pair discarded (CAP-002).

## MB09 — 30-year naturally dried Red Cedar complete (n=49)

MB IDs 000024–000072. Mean displayed ρ≈312, \(f\)≈57, Q≈216, \(E\)≈6.2; radiation n=37 (blanks flagged). No Summary vs Detailed tab.

## MB10 — Compact 30-year book is subset of complete

17 specimens 000024–000040; first 17 rows of the 49-specimen master. Prefer complete book.

## MB11 — Duplicate compact upload

`30_Year_Aged_Red_Cedar_MB_Sound_864b.xlsx` SHA-256 identical to `*_0323.xlsx`.

## MB12 — Do not fabricate unreadable fields

30-year Review Notes leave faint radiation / mass / peak blank (14 specimens with notes). Policy: blank + flag, never invent.

## MB13 — Env / calibration metadata absent

Across books: environmental conditions, calibration records, mic placement, support tolerances not visible → recorded unavailable.

## MB14 — Summary vs Detailed retention pattern

Small card/analyzer differences preserved with assessment labels (“Match / display rounding”, “Small run/display variation”). Import UX should dual-store.

## MB15 — Batch Statistics formulas uncached

MIN/AVERAGE/MAX/STDEV cells blank under `data_only`; recompute from Specimen Master (WORKBOOK_INVENTORY).

## MB16 — Spectral Sheet Archive is visual evidence

Complete books embed paired summary/detail JPEGs (`xl/media`). Not a substitute for numeric series.

## MB17 — C vs W analyzer name prefixes

Alpine/Red/Torrefied use `*-C-*` and `*-W-*` name families (likely cut / width or stock groups). Do not invent meaning without vendor glossary (**G-MB** open).

## MB18 — Fitting % quality gate present

Master includes Fitting (%) / Fit Quality — candidate intake QC field (Alpine mean ~95%; Red ~92%; Torr ~94%; 30yr ~94%).

## MB19 — Radiation coefficient schema splits on aged book

30-year master has Displayed vs Calculated radiation; Calculated density column entirely blank in this file (**G-MB08** related).

## MB20 — Kit SOP ≠ panel workbook SOP

`nicoletti_mb_sound_acoustic_study_set` is finished-guitar kit connectivity; these books are half-plate / billet TPC cards. Cross-link culture only.

## MB21 — Not FPL / wood_species.json authority

Transcribed vendor analyzer densities and moduli must not overwrite FPL_GTR282 / CIRAD / wood_database_meier per-field attribution policy.

## MB22 — Torrefied vs Alpine anecdote only

In this capture, torrefied ADK shows higher mean \(f\), Q, \(E\) than Alpine — uncontrolled batch comparison; do not ship as treatment effect (**G-MB07**).

## MB23 — Aged vs non-aged red cedar anecdote only

30-year batch: lower mean ρ, higher mean Q than non-aged red cedar book — same caution as MB22.

## MB24 — Source Pairing filenames dated 2026-08-02

Compact book maps each ID to summary/detail PNG names — provenance for original ZIP screenshots.

## MB25 — Capture Audit is mandatory ingest gate

AS/RC/CAP/ARC issue IDs document missing specimens, invalid pairs, OCR ambiguity — pipeline must skip/flag accordingly.

## MB26 — Session dual corpus

Same session also uploaded Holmberg Gore modeling `.xlsx` (equation engines). Separate pack; do not merge schemas.

## MB27 — Hashes recorded; binaries not in git

WORKBOOK_INVENTORY SHA-256 for all six lab uploads (five unique hashes).

## MB28 — Full tab-by-tab evaluation complete

Every sheet opened/classified — see [`TAB_BY_TAB_EVALUATION.md`](./TAB_BY_TAB_EVALUATION.md).

## MB29 — Universal wiring through LUTHERIE_MATH (no parallel engine)

MB Specimen Master fields are **inputs** to [`docs/LUTHERIE_MATH.md`](../../../LUTHERIE_MATH.md) §12 / §13 (Appendix B) and existing `plate_design/*` solvers. Do not recreate TPC/Holmberg equation runtimes in product.

---

## Point index

| ID | Title |
|----|-------|
| MB01 | Screenshot corpus not raw DSP |
| MB02 | Detailed analyzer primary |
| MB03 | TPC Rev 1.5 method |
| MB04 | Signal 1 / Mono |
| MB05 | Specimen Master import surface |
| MB06 | Alpine batch scalars |
| MB07 | Red Cedar batch + mismatches |
| MB08 | Torrefied batch + missing 000002 |
| MB09 | 30-year complete n=49 |
| MB10 | Compact ⊂ complete |
| MB11 | Duplicate compact SHA |
| MB12 | No fabricate blanks |
| MB13 | Env/calibration absent |
| MB14 | Dual-value retention |
| MB15 | Uncached batch formulas |
| MB16 | Spectral archive visual only |
| MB17 | C/W name prefixes unknown |
| MB18 | Fitting % QC field |
| MB19 | Displayed vs calculated splits |
| MB20 | Kit ≠ panel SOP |
| MB21 | Not FPL authority |
| MB22 | Torrefied anecdote only |
| MB23 | Aging anecdote only |
| MB24 | Source pairing filenames |
| MB25 | Capture Audit ingest gate |
| MB26 | Dual session corpus |
| MB27 | Hashes; no binaries in git |
| MB28 | Tab-by-tab evaluation |
| MB29 | Wire via LUTHERIE_MATH Appendix B |
