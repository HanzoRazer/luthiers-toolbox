# Source provenance — MB Sound panel laboratory records

**Capture date (session uploads):** 2026-08-04  
**Source type:** Excel workbooks built from paired **summary-card** + **detailed Tonewood Parameters Characterization (Rev 1.5, Giuliano Nicoletti)** screenshots (MB Sound / Maderas Barber analyzer UI)  
**ASR caveat:** N/A — not a lecture transcript; values are screenshot transcriptions with in-workbook Capture Audit dispositions  
**Binaries:** Session uploads under agent uploads path; **not committed** to git (hashes in WORKBOOK_INVENTORY)

## Workbook families

### A. Complete Laboratory Procedural Records (7-tab template)

Shared spine: `README` → `Specimen Master` → `Acquisition Procedure` → (`Summary vs Detailed`) → `Capture Audit` → `Batch Statistics` → `Spectral Sheet Archive`

| Material | Specimens | MB / analyzer IDs | Notes |
|----------|----------:|-------------------|-------|
| Alpine Spruce | 22 | 000001–000022 · ABA-C / ABA-W | Summary vs Detailed: all match |
| Red Cedar | 22 | 000001–000022 · CED-C / CED-W | Q and 0.1 Hz resonance mismatches retained |
| Torrefied Adirondack Spruce | 21 | 000001–000022 minus **000002** · ADT-C / ADT-W | Missing 000002; invalid 000008 pair discarded |
| 30-Year Naturally Dried Red Cedar | 49 | 000024–000072 · CA* names | No Summary vs Detailed tab; radiation blanks on many rows |

### B. Compact MB Sound transcription (4-tab)

| File | Specimens | Role |
|------|----------:|------|
| 30-Year Aged Red Cedar MB Sound | 17 | IDs 000024–000040 — **subset** of complete 49-specimen book |
| Duplicate `*_864b` | 17 | Byte-identical to `*_0323` |

## Transcription policy (from in-file README / Notes)

1. Detailed analyzer screens are the **primary** numerical source.  
2. Summary cards retained for audit comparison when the 7-tab template includes `Summary vs Detailed`.  
3. Unreadable fields left blank + Review Notes — no fabricated values.  
4. Environmental conditions, calibration records, mic placement, support tolerances: **not visible** → recorded unavailable.  
5. Graphs preserved as embedded JPEG media on `Spectral Sheet Archive` (complete books); numeric waveform/FFT/IR arrays absent.
