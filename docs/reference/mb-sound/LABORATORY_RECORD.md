# MB Sound laboratory procedural record (`mb_sound_lab_procedure_v1`)

> Draft intake schema for PR #244. Not materials-authority ratification.  
> Supersedes the flat “tonewood-property workbook” layout for live specimens.

## Why reorganize

The first intake workbooks optimized for **tonewood property columns** (ρ, E, f, Q, radiation).  
MB Sound frames also carry **laboratory procedure** data (geometry, nodal lines, decay fit, recording lengths, peak level, channel select, dual vendor IDs, batch context). Those extra points stay valuable even when not used by plate solvers today.

This revision keeps the six-layer contract and reorganizes `source` / `normalized` into a **complete laboratory procedural record**.

## Record markers

| Field | Value |
|-------|--------|
| `record_schema` | `mb_sound_lab_procedure_v1` |
| `record_kind` | `measured_panel` (unchanged — still a measured panel specimen) |
| `dataset_version` | `0.5.0-draft` |

## Layer contract (unchanged)

`source` → `normalized` → `derived` → `validation` → `unresolved` → `artifacts`

## `source` procedural sections

| Section | Contents |
|---------|----------|
| Identity keys | `catalog_id`, `analysis_sample_name`, `species_label_vendor` (also nested under `identity`) |
| `identity` | Dual vendor IDs, vendor species label, role, treatment, cohort |
| `specimen_geometry` | L/W/h, mass, stated density, nodal lines + null slots for MC, cutting year, grain, boundary |
| `measurement_procedure` | Method label, Nicoletti software attribution, select_source, null slots for excitation/sensor/support |
| `signal_recording` | Total/visualized recording length, peak dBFS, null slots for sample rate / bit depth |
| `vendor_surfaces.summary_card` | Verbatim MB Sound card (density, stiffness, f, Q, radiation) |
| `vendor_surfaces.detailed_analysis` | Verbatim Nicoletti analysis outputs (f, τ, logδ, Q, fit%, E, radiation) |
| `resonance_modes[]` | Vendor resonance as mode list (mn null until known) |
| `batch` | Title, stated size, sequence/timeline nulls, `artifact_id` → artifact_manifest |
| `field_provenance` | Surfaces, URL, extractor, notes, migration marker |

## `normalized` additions

Property fields keep TonewoodEntry-aligned names. Additive groups:

- `normalized.signal.*` — peak / recording lengths / select_source  
- `normalized.procedure.*` — method_label, fitting_pct, nodal_lines_mm (procedure-facing view)

Forbidden synonyms unchanged (`stiffness_gpa`, `youngs_modulus`, `moe`, …).

## Reference workbook (Torrefied Adirondack)

`source_artifacts/workbooks/Torrefied_Adirondack_Complete_Laboratory_Record.xlsx`

| Sheet | Role |
|-------|------|
| README | Scope, primary-source rule, spectral limits |
| Specimen Master | Detailed-analyzer measurements (primary numbers) |
| Acquisition Procedure | Software Rev 1.5, Signal 1, Mono, plot presence, raw-array availability, screenshot filenames |
| Summary vs Detailed | Card vs analyzer audit (retain both; no silent reconcile) |
| Capture Audit | CAP-001…004 (gap 000002, crossed 000008 pair, radiation/nodal flags) |
| Batch Statistics | Cohort aggregates |
| Spectral Sheet Archive | Embedded cropped screenshots (visual evidence only) |

**Rule:** detailed analyzer is the primary numerical source; summary-card values stay under `vendor_surfaces.summary_card` for audit.

## Migration

| Generation | Shape |
|------------|--------|
| tonewood-property workbook v1 | Flat `source.card` + `source.analysis_ui` |
| lab procedure v1 | Procedural sections above; all former leaves preserved |

Do not invent values for null procedure slots. Do not pool treatments.

## Related

- Example: [`schema/lab_procedure.example.json`](./schema/lab_procedure.example.json)  
- Staging flat projection (legacy): [`schema/panel.example.json`](./schema/panel.example.json)  
- Field glossary: [`FIELD_GLOSSARY_ES_EN.md`](./FIELD_GLOSSARY_ES_EN.md)  
- Linkage / dual IDs: [`LINKAGE.md`](./LINKAGE.md)  
