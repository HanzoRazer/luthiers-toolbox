# Tab-by-tab evaluation — MB Sound / TPC panel laboratory workbooks

**Date:** 2026-08-04  
**Method:** openpyxl read of every sheet in all six session lab uploads; ZIP inspection of `xl/media`; recomputed batch stats from Specimen Master (Batch Statistics formulas uncached).  
**Scope:** Structural + functional evaluation (purpose, I/O, issues). Not a re-derivation of Nicoletti TPC equations (**G-MB05**).  
**Point:** **MB28**  
**Sibling session corpus:** Holmberg guitar engines → [`../holmberg_gore_modeling_spreadsheets/TAB_BY_TAB_EVALUATION.md`](../holmberg_gore_modeling_spreadsheets/TAB_BY_TAB_EVALUATION.md)

---

## Files evaluated

| File | Tabs | Specimens | Media JPEGs |
|------|-----:|----------:|------------:|
| Alpine Spruce Complete Lab | 7 | 22 | 44 |
| Red Cedar Complete Lab | 7 | 22 | 44 |
| Torrefied Adirondack Complete Lab | 7 | 21 | 44 |
| Red Cedar 30-Year Drying Complete Lab | 6 | 49 | 98 |
| 30-Year Aged Red Cedar MB Sound (compact) | 4 | 17 | 0 |
| 30-Year Aged Red Cedar MB Sound `*_864b` | 4 | 17 | 0 (= duplicate SHA) |

---

## A. Complete Laboratory Record — shared tabs

### 1. `README`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Dataset scope, primary-source rule, raw-data limitation, discrepancy policy |
| **Inputs** | None (documentation) |
| **Outputs** | Human contract for the rest of the book |
| **Verdict** | Always read first. Establishes detailed-analyzer primacy and “do not fabricate” rule. |

### 2. `Specimen Master`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Canonical numeric table: geometry + TPC scalars per specimen |
| **Key columns** | L/W/t, mass, ρ, nodal mm, \(f\), τ, log dec, Q, fit %, \(E\) GPa, radiation coeff, recording meta |
| **30-year delta** | Adds Displayed vs Calculated density/radiation; Review Notes; more acquisition flags on-row |
| **Verdict** | **Primary data surface** for Toolbox plate intake / corpus import planning. Prefer detailed values here over summary cards. |

### 3. `Acquisition Procedure`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Per-specimen capture metadata + availability flags |
| **Key fields** | Software/method string (`Tonewood parameters characterization – Rev 1.5 – Giuliano Nicoletti`), Signal 1 / Mono, plot Present flags, lengths, peak dBFS, **Raw Audio / Numeric Waveform / FFT / IR = No**, env/calibration = No |
| **Verdict** | SOP evidence that this is screenshot metrology, not a raw measurement archive. Lab UI must not pretend arrays exist. |

### 4. `Summary vs Detailed` *(Alpine, Red Cedar, Torrefied only)*

| Field | Evaluation |
|-------|------------|
| **Purpose** | Audit: summary-card vs detailed-analyzer for ρ, \(E\), \(f\), Q, radiation |
| **Findings** | Alpine: **0** mismatches. Red: Q −1.6 on 000005; \(f\) +0.1 Hz on 000021. Torrefied: Q −0.2 on 000004; radiation −0.3 on 000014 |
| **Verdict** | Correct pattern for corpus ingestion — retain both, never silent-reconcile. **Absent** on 30-year complete book (**G-MB06**). |

### 5. `Capture Audit`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Issue register with severity + disposition |
| **Critical items** | Torrefied **CAP-001** missing 000002; **CAP-002** invalid 000008 pair; 30-year ARC duplicate summary; universal “plots only / no env metadata” |
| **Verdict** | Treat as authoritative provenance. Any import pipeline must honor exclusions (missing / invalid pairs). |

### 6. `Batch Statistics`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Cohort MIN / AVERAGE / MAX / STDEV over master metrics |
| **Issue** | Formulas present but **cached values empty** in all complete books when read `data_only` (**G-MB01**). Specimen counts / ID ranges are stored as literals. |
| **Verdict** | Recompute from Specimen Master (done in WORKBOOK_INVENTORY). Do not trust blank cached stats. |

### 7. `Spectral Sheet Archive`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Paired summary + detailed screenshot archive with labels per specimen |
| **Media** | JPEG drawings under `xl/media` (44 / 44 / 44 / 98). openpyxl `_images` may report 0 — ZIP confirms media present. |
| **Verdict** | Visual evidence only. Large files (~1.5–2.5 MB) are mostly images. Compact book has **no** archive. |

---

## B. Compact 30-year Red Cedar — every tab

### 1. `30-Year Red Cedar`

| Field | Evaluation |
|-------|------------|
| **Purpose** | 17-row specimen table (000024–000040) — same column family as complete master |
| **Verdict** | Useful quick view; **superseded** by complete 49-row book for corpus work. |

### 2. `Batch Summary`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Formula stats over H/J/M/O/P columns |
| **Verdict** | Same uncached-formula issue as complete books; recompute if needed. |

### 3. `Source Pairing`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Maps Sample ID → summary PNG filename + detailed PNG filename |
| **Verdict** | Provenance index for the original screenshot set (filenames dated 2026-08-02). |

### 4. `Notes`

| Field | Evaluation |
|-------|------------|
| **Purpose** | Four dataset caveats (primary source, no numeric series, no env/calibration, faint names preserved) |
| **Verdict** | Aligns with complete-book README policy. |

---

## C. Book-to-book deltas

| Topic | Alpine | Red Cedar | Torrefied ADK | 30-yr complete | Compact |
|-------|--------|-----------|---------------|----------------|---------|
| Tabs | 7 | 7 | 7 | **6** (no Summary vs Detailed) | 4 |
| n | 22 | 22 | **21** (missing 000002) | **49** | 17 ⊂ 49 |
| Name prefixes | ABA-C/W | CED-C/W | ADT-C/W | CA* | CA* |
| Software string on Acquisition | Yes | Yes | Yes | Mostly flags only | — |
| Avg ρ | ~409 | ~342 | ~438 | ~312 | ~310 |
| Avg \(f\) Hz | ~65 | ~55 | ~81 | ~57 | ~59 |
| Avg Q | ~153 | ~148 | ~185 | ~216 | ~214 |
| Avg \(E\) GPa | ~11.1 | ~6.3 | ~13.0 | ~6.2 | ~5.8 |
| Image archive | 44 | 44 | 44 | 98 | none |

**EO observation (not a target):** Torrefied Adirondack shows higher mean \(f\), Q, and \(E\) than Alpine in this capture set; 30-year red cedar shows lower ρ and higher Q than the non-aged red cedar book — treat as batch anecdotes pending controlled re-measure (**G-MB07**).

---

## D. Issues found in this tab audit

| ID | Issue | Where | Severity |
|----|-------|-------|----------|
| **G-MB01** | Batch Statistics formulas uncached (blank `data_only`) | All complete + compact Batch sheets | Medium |
| **G-MB02** | No raw audio / FFT / IR numeric arrays | Acquisition flags all books | High (for DSP lab) |
| **G-MB03** | Torrefied specimen 000002 missing | Capture Audit CAP-001 | High (completeness) |
| **G-MB04** | Compact book duplicates + subset of complete 30-year | `*_0323` / `*_864b` | Low |
| **G-MB05** | TPC Rev 1.5 equations not re-derived here | Analyzer-derived \(E\), SRC, Q | Medium |
| **G-MB06** | No Summary vs Detailed on 30-year complete | Tab missing | Low |
| **G-MB07** | Cross-species / aging comparisons uncontrolled | Batch deltas | Medium |
| **G-MB08** | Radiation coeff blank on 12 of 49 aged specimens | Review Notes | Medium |

---

## E. Port priority (from tab evaluation)

1. **Specimen Master schema** → plate intake fields (ρ, \(f\), Q, \(E\), SRC/RC, geometry)  
2. **Acquisition Procedure flags** → honesty about missing arrays / env  
3. **Capture Audit** → import exclusions  
4. **Summary vs Detailed** → dual-value retention pattern  
5. **Batch Statistics** → recompute server-side; do not rely on Excel cache  
6. **Spectral archive** — optional evidence UI only  

---

## F. Coverage statement

**Yes — every tab in every submitted MB Sound / TPC laboratory workbook was opened and classified**, including the byte-identical compact duplicate. Deep numeric sampling covered all Specimen Master rows for batch scalars; Capture Audit and Summary vs Detailed mismatches enumerated. Holmberg session workbooks are evaluated separately in the Holmberg pack.
