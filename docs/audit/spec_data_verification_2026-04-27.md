# Instrument specification data verification audit

**Date:** 2026-04-27  
**Scope:** Potentially fabricated or unverifiable dimensional data in instrument JSON specs.  
**Constraint:** Read-only audit; no spec files were modified.

---

## Methodology

1. **Inventory** — Enumerated JSON files under:
   - `services/api/app/instrument_geometry/specs/` (19 files)
   - `services/api/app/instrument_geometry/body/specs/` (3 files)
   - `services/api/app/instrument_geometry/models/` — all `*_spec.json` files (7 files) plus additional per-model geometry JSON files that define body/neck dimensions (`cuatro_puertorriqueno.json`, `cuatro_venezolano.json`, `flying_v_1958.json`, `benedetto_17.json`, `gibson_melody_maker.json`).
   - **Also reviewed (not a dimensional spec):** `services/api/app/instrument_geometry/instrument_model_registry.json` — used as a cross-reference for asset paths and model `status` (e.g. `STUB`, `PARTIAL`); it does not contain pickup/body dimension tables and is **not** repeated as one row per instrument below.

2. **Source tracing** — For each file, recorded the top-level `source`, `blueprint_source`, `plan_source`, `source_document`, `construction_source`, or equivalent. Checked whether cited paths exist under the workspace root, especially `Guitar Plans/`, `docs/archive/`, and `services/api/app/instrument_geometry/body/dxf/`.

3. **Fabrication heuristics** (as requested):
   - **Duplicate cavity/pickup tuples** — Compared `route_length_mm` / `route_width_mm` / `route_depth_mm` across electric specs.
   - **Overly round numbers** — Flagged long runs of `.0` mm where extraction from scans would often yield fractional values (without claiming proof of fabrication).
   - **Published-standard patterns** — Many Gibson-style specs share inch-exact conversions (e.g. 73.99 mm bridge spacing, 82.55 mm tailpiece spacing) consistent with catalog references rather than independent measurement.
   - **Extraction metadata** — Preferred specs with DXF/PDF artifacts, per-field `*_source` notes, or vectorizer provenance; flagged “verified from spec sheet” prose without file pointers.

4. **Verification limit** — This audit did **not** open each PDF/DXF to numerically reconcile every dimension. Categories reflect **repository evidence and plausibility**, not a full dimensional redline of every drawing.

5. **Conservative bias** — Where provenance was thin or dimensions looked templated, the row was categorized as **suspect** or **unverifiable** and the uncertainty called out in **Notes**.

---

## Inventory — paths discovered

| Location | Count | Notes |
|----------|------:|-------|
| `services/api/app/instrument_geometry/specs/*.json` | 19 | Includes `stratocaster.json`, `fender_stratocaster.json`, `all_extractions.json`. |
| `services/api/app/instrument_geometry/body/specs/*.json` | 3 | Smart Guitar + Gibson L-1 1928 setup-style data. |
| `services/api/app/instrument_geometry/models/*_spec.json` | 7 | Grellier-derived acoustics, Selmer, Fesselier jumbo, cuatro extraction specs. |
| `services/api/app/instrument_geometry/models/` (selected geometry JSON) | 5 | `cuatro_*.json` (non-`_spec`), `flying_v_1958.json`, `benedetto_17.json`, `gibson_melody_maker.json`. |
| `services/api/app/instrument_geometry/instrument_model_registry.json` | 1 | Registry / CAM metadata only (see Methodology). |
| `Guitar Plans/` | — | Present at repo root; primary location for PDFs/DXFs referenced by specs. |

---

## Findings (cross-cutting)

1. **Duplicate humbucker route envelope** — Identical **71.0 × 40.0 × 19.05** (or **19.0**) mm neck/bridge humbucker routes appear in **`gibson_les_paul.json`**, **`gibson_explorer.json`**, **`gibson_flying_v_1958.json`**, and **`klein_guitar.json`**. The Klein design uses direct-mount humbuckers; reuse of the same triple as carved-top Gibsons is **unlikely to be four independent extractions** — strong **template / reference** pattern.

2. **Dual Stratocaster specs** — **`stratocaster.json`** and **`fender_stratocaster.json`** both use `model_id` / display name for the Stratocaster with overlapping intent. **`stratocaster.json`** references blueprint PDFs that project docs state were **not committed** (`docs/archive/recovered/__RECOVERED__/README.md`), while CAM-oriented assets live under `Guitar Plans/Fender Stratocaster_Project/`. Risk: **drift** or **mixed authority** between the two files.

3. **`all_extractions.json` bounding-box cache** — Entry for **Gibson SG** shows **905.3 × 340.4 mm** width/height — implausible for a real SG body and consistent with a **scale/vectorization error** (similar failure mode to known vectorizer issues elsewhere in the project). Treat this file as **diagnostic output**, not ground truth.

4. **Carlos Jumbo / electric-style scale reference** — **`carlos_jumbo.json`** documents use of a **single-coil route** (89.9 → 85.0 mm) as a scale reference on an **acoustic** plan set; the spec itself notes the reference may be inappropriate. Flagged for **methodological suspicion**, not for round numbers alone.

5. **Cuatro path naming** — **`cuatro_puertorriqueno.json`** cites `Cuatro/...` paths; the actual plans in this workspace live under **`Guitar Plans/El Cuatro/`** (with `cuatro puertorriqueño.pdf` and DXF derivatives). **`cuatro_puertorriqueno_spec.json`** cites `cuatro_puertorriqueno.pdf` (filename approximation). Sources **exist** but **string paths in JSON do not match disk layout** — complicates auditability.

6. **Gibson L-00 grellier spec** — **`gibson_l00.json`** cites a **grellier.fr** 2008 plan; no matching PDF was located under `Guitar Plans/` in this audit (may be web-only or omitted from the clone). Treated as **missing local source**.

7. **Transparent estimates (good practice)** — **`gibson_l1_1928.json`** explicitly labels nulls and **“estimated”** fields (`waist_width_source`, `shoulder_depth_source`, IBG defaults). This is **not fabrication** but **incomplete verifiability** for those fields.

8. **AI extraction without numeric cross-check** — **`benedetto_17.json`** documents **AI vision** from JPG plans with **very clean inch-derived mm** (e.g. 19.0 in, 11.0 in). **`benedetto_archtop_rope.json`** inherits that geometry. Requires **manual comparison** to drawings.

9. **Manufacturer prose without artifacts** — Several electrics state **“Verified specifications from manufacturer data”** or **“spec sheet 2026-03-29”** without a committed PDF/DXF pointer in the same JSON. Treated as **UNVERIFIABLE-NO-SOURCE** at the file level (the dimensions may still be correct).

---

## Per-instrument table

Columns: **Instrument** (logical name) | **Spec file** (repo-relative) | **Source claimed** | **Source found in repo** | **Category** | **Evidence** | **Notes**

| Instrument | Spec file | Source claimed | Source found | Category | Evidence | Notes |
|------------|-----------|----------------|--------------|----------|----------|-------|
| Aggregate DXF bbox log | `services/api/app/instrument_geometry/specs/all_extractions.json` | Implicit: various `*_body.dxf` | Some DXFs under `body/dxf/` / exports; not all names resolved | UNVERIFIABLE-NO-SOURCE | Gibson SG **905.3 mm** width — inconsistent with real instrument; likely bad scale | Not a construction spec; do not feed CAM without validation. |
| Benedetto 17 rope binding | `services/api/app/instrument_geometry/specs/benedetto_archtop_rope.json` | Custom; geometry from `models/benedetto_17.json` | `models/benedetto_17.json` exists; JPGs under `Guitar Plans/Benedetto/` | REFERENCE-DERIVED | AI-extracted base; rope trim is design overlay | Same dimensional risk as `benedetto_17.json`. |
| Carlos Jumbo (flat-top jumbo) | `services/api/app/instrument_geometry/specs/carlos_jumbo.json` | `JUMBO-CARLOS-*-3.pdf` + vectorizer + catalog | **Yes** — `Guitar Plans/Jumbo Carlos/` PDFs + large `*_gapclose0.dxf` | SUSPECT-ROUND-NUMBERS | Reuses **190 / 85 / 90** style headstock blocks seen elsewhere; acoustic scale ref from **single_coil_route** documented in-file | Self-aware notes; still **high manual verification** priority. |
| Epiphone Spartan archtop | `services/api/app/instrument_geometry/specs/epiphone_spartan.json` | AGP-11 Stoll plan | **Yes** — `Guitar Plans/Archtop Measurements/Epiphone_Spartan_2.jpg`; sheet refs | VERIFIED | `edge_to_dxf` + `source_image` + OCR scale note | Project history: prior Spartan error **corrected**; still recommend spot-check vs AGP-11. |
| Fender Stratocaster (extended doc) | `services/api/app/instrument_geometry/specs/fender_stratocaster.json` | Fender spec sheets / blueprint archive | DXFs under `Guitar Plans/Fender Stratocaster_Project/`; blueprint PDFs **not in repo** per recovered docs | REFERENCE-DERIVED | Many **241.3 / 304.8 / 647.7** mm = inch-exact | Labeled as reference-style data; overlaps `stratocaster.json`. |
| Fender Telecaster | `services/api/app/instrument_geometry/specs/fender_telecaster.json` | Telecaster ’72 Custom Deluxe spec sheet | No PDF cited in JSON; Tele CAM via generators / outlines | REFERENCE-DERIVED | Inch-precise neck depths **20.0 / 22.0**; **647.7** scale | No single committed drawing ID in file. |
| Gibson ES-335 | `services/api/app/instrument_geometry/specs/gibson_es_335.json` | “Manufacturer data” / spec sheet 2026-03-29 | No plan path in JSON | UNVERIFIABLE-NO-SOURCE | Bridge **73.99 / 82.55** mm matches common **2.913" / 3.25"** references | Neck depth **21.59 / 24.13** (0.85 / 0.95 in) — reference-like. |
| Gibson Explorer | `services/api/app/instrument_geometry/specs/gibson_explorer.json` | Factory + LonelyStar blueprint | **Yes** — `services/api/app/instrument_geometry/body/dxf/electric/gibson_explorer_body.dxf` (spec text cites archive path; file exists here) | SUSPECT-DUPLICATE-VALUES | **71 × 40 × 19.05** mm humbucker routes **match Les Paul** | Outline may be traced; cavities likely **shared template**. |
| Gibson Flying V 1958 | `services/api/app/instrument_geometry/specs/gibson_flying_v_1958.json` | Factory + `catalog.json` + Flying V DWG refs | DWG not searched exhaustively; body outline from internal catalog | SUSPECT-DUPLICATE-VALUES | **71 × 40 × 19.0** humbucker tuple **matches** LP/Explorer | **190 × 85** headstock block like other Gibsons — possible template. |
| Gibson J-45 | `services/api/app/instrument_geometry/specs/gibson_j45.json` | `J45 DIMS.dxf` | **Yes** — `Guitar Plans/Gibson J 45_ Project/J45 DIMS.dxf` | VERIFIED | `extracted_dxf` subtree; bracing + fret sourcing from DXF | Strongest **local ground-truth** chain in the electric/acoustic set. |
| Gibson L-00 | `services/api/app/instrument_geometry/specs/gibson_l00.json` | grellier.fr CC plan 2008 | **No** — PDF not found under `Guitar Plans/` in this workspace | UNVERIFIABLE-MISSING-SOURCE | Dimensions may be accurate but **cannot be checked** against local plan | If grellier is web-only, add URL or vendor path for auditability. |
| Gibson Les Paul | `services/api/app/instrument_geometry/specs/gibson_les_paul.json` | Factory drawings; `catalog.json` outline; Guitar Plans PDFs | Partial — Les Paul project folders exist under `Guitar Plans/Les Paul_Project/` | SUSPECT-DUPLICATE-VALUES | **71 × 40 × 19.05** mm routes; **~7.8 / 140** carve note looks computed | Rich CAM notes; humbucker envelope still **template suspect** vs independent extract. |
| Gibson Melody Maker | `services/api/app/instrument_geometry/specs/gibson_melody_maker.json` | Manufacturer / spec sheet 2026-03-29 | No drawing in JSON | UNVERIFIABLE-NO-SOURCE | **25.4 mm** at 12th on ’65 variant = **1.000 in** exact | See also `models/gibson_melody_maker.json` for vectorizer path. |
| Gibson SG | `services/api/app/instrument_geometry/specs/gibson_sg.json` | Spec sheet + `DXF-00-Gibson-SG.dxf` | **Yes** — `docs/archive/instrument_references/gibson_sg/DXF-00-Gibson-SG.dxf` | REFERENCE-DERIVED | Neck/headstock inch-exact; **no pickup cavity block** in this file | Body thickness **38.1 mm** = **1.5 in** exact. |
| Jumbo archtop (hybrid) | `services/api/app/instrument_geometry/specs/jumbo_archtop.json` | **Hybrid** Carlos scale + Benedetto methods + knowledge base | Synthetic / multi-source | REFERENCE-DERIVED | Explicitly **not a reproduction** | Dimensions are **design intent**, not shop extraction — acceptable if users understand label. |
| Klein electric | `services/api/app/instrument_geometry/specs/klein_guitar.json` | `Klein-Guitar-Plan.pdf` + vectorizer | **Yes** — `Guitar Plans/Klein/Klein-Guitar-Plan.pdf` | SUSPECT-DUPLICATE-VALUES | Body from Phase 3.6; **71 × 40 × 19** humbuckers **match Gibson template** | Hardware BOM cites **StewMac / LMI / Musician’s Friend** — commercial references. |
| Martin D-28 1937 | `services/api/app/instrument_geometry/specs/martin_d28_1937.json` | John Arnold technical drawings | **No** Arnold files located in audit | UNVERIFIABLE-NO-SOURCE | Rich fractional-inch side profile — could be faithful transcription **or** typed summary | Manual compare to Arnold publication if available. |
| Martin OM-28 | `services/api/app/instrument_geometry/specs/martin_om28.json` | Martin production + grellier plan + calculators | grellier OM: **Yes** — `Guitar Plans/OM_acoustic_guitar*.pdf|dxf` | REFERENCE-DERIVED | Mixes **brand production** language with **CC plan** | Multi-source; grellier portion auditable locally. |
| Fender Stratocaster (compact spec) | `services/api/app/instrument_geometry/specs/stratocaster.json` | American Standard + named PDFs | PDFs **not committed** (per internal README) | UNVERIFIABLE-MISSING-SOURCE | **Trem route 89 × 56** mm; **85.0** mm pocket width — round | Prefer `fender_stratocaster.json` + `Guitar Plans` DXFs for CAM authority. |
| Gibson L-1 1928 | `services/api/app/instrument_geometry/body/specs/gibson_l1_1928.json` | Luthier listing / verified setup | No blueprint; photo reference described | VERIFIED | Primary bout/length/depth from **luthier listing**; **explicit** nulls/estimates elsewhere | **Not fabrication** — honest partial data. |
| Smart Guitar v1 | `services/api/app/instrument_geometry/body/specs/smart_guitar_v1.json` | Hand-traced outline from render; Explorer/LP heritage | **Yes** — traced JSON/DXF paths under `body/` tree | REFERENCE-DERIVED | Declared **original ergonomic** body; parent dimensions **420 × 460** reference | Intentional **composite design** — not claimed as shop extraction. |
| Smart Guitar setup | `services/api/app/instrument_geometry/body/specs/smart_guitar_setup_spec.json` | Derived from LP / Explorer / Klein | Parent specs exist | REFERENCE-DERIVED | Documents **per-parameter** inheritance | Setup doc; not a blueprint extraction. |
| Acoustic 00 (Grellier) | `services/api/app/instrument_geometry/models/acoustic_00_spec.json` | `Acoustic_guitar_00_en.pdf` + `.dxf` | **Yes** — `Guitar Plans/Acoustic_guitar_00*` | VERIFIED | Claims DIMENSION/MTEXT extraction; **362.1 / 478.9** style values | Strong **DXF-first** methodology text. |
| Cuatro Puertorriqueño (geometry JSON) | `services/api/app/instrument_geometry/models/cuatro_puertorriqueno.json` | `Cuatro/*.pdf` | **Yes** under `Guitar Plans/El Cuatro/` (paths differ) | UNVERIFIABLE-MISSING-SOURCE | `dimensions_source: "traditional_reference"`; **380 / 280 / 85** mm round | **Explicitly non-extracted** body block; paths don’t match folder names. |
| Cuatro Puertorriqueño (extraction spec) | `services/api/app/instrument_geometry/models/cuatro_puertorriqueno_spec.json` | `cuatro_puertorriqueno.pdf` | **Yes** — PR cuatro PDF/DXF in `Guitar Plans/El Cuatro/` | UNVERIFIABLE-NO-SOURCE | `status: PARTIAL_SPEC`; fret table extracted per metadata | Filename mismatch only; **body outline still pending** per metadata. |
| Cuatro Venezolano (geometry JSON) | `services/api/app/instrument_geometry/models/cuatro_venezolano.json` | `Cuatro/plano cuatro venezolano.pdf` | **Yes** — `Guitar Plans/El Cuatro/plano cuatro venezolano.pdf` | VERIFIED | **321.6 × 234.6** matches vector summary in `_spec` | OpenCV contour method cited. |
| Cuatro Venezolano (extraction spec) | `services/api/app/instrument_geometry/models/cuatro_venezolano_spec.json` | El Cuatro 1–8 PDFs | **Yes** | VERIFIED | Complete 8-sheet extraction metadata | cm→mm conversion documented. |
| Benedetto 17 (AI model) | `services/api/app/instrument_geometry/models/benedetto_17.json` | JPG blueprints + AI vision | **Yes** — `Guitar Plans/Benedetto/` images | SUSPECT-ROUND-NUMBERS | Body **19 / 11 / 17 / 9** in → clean mm | Needs **numeric redline** vs drawing. |
| Flying V 1958 (tier model) | `services/api/app/instrument_geometry/models/flying_v_1958.json` | `Gibson58FlyingV.pdf` + supervisor specs | **No** PDF found under `Guitar Plans/` in quick search | UNVERIFIABLE-MISSING-SOURCE | `validated: false` | Ranges only — not a CNC-ready verified spec. |
| Gibson L-0 (Grellier-style PDF spec) | `services/api/app/instrument_geometry/models/gibson_l0_spec.json` | `Gibson-L0-IN.pdf` | **Yes** — `Guitar Plans/Gibson-L0-IN.pdf` | VERIFIED | Per-field sheet citations; fractional inch annotations | High internal documentation quality. |
| Gibson Melody Maker (vectorizer model) | `services/api/app/instrument_geometry/models/gibson_melody_maker.json` | `Guitar Plans/Gibson-Melody-Maker.pdf` | **Yes** | VERIFIED | **434.3 × 325.4 × 44.5** body — non-integer variety | Complements thin manufacturer JSON spec. |
| Jumbo Fesselier | `services/api/app/instrument_geometry/models/jumbo_fesselier_spec.json` | `Guitar-Jumbo-MM-A0/A4.pdf` | **Yes** — PDFs + `Guitar-Jumbo-MM.dxf` under `Guitar Plans/` | VERIFIED | Page-level citations (e.g. **40.3** nut width appears twice) | Mixed **integer and fractional** — credible extract. |
| OM acoustic (Grellier) | `services/api/app/instrument_geometry/models/om_acoustic_spec.json` | `OM_acoustic_guitar_en.pdf` + `.dxf` | **Yes** | VERIFIED | **645.1 / 380.5 / 492.0** from DXF cluster notes | Explicit comparison to “standard OM” sizes. |
| Selmer–Maccaferri D-hole | `services/api/app/instrument_geometry/models/selmer_maccaferri_d_hole_spec.json` | `Selmer-Maccaferri-D-hole-MM-01/02.pdf` | **Yes** — under `Guitar Plans/` | VERIFIED | Bilingual sheet references; many **non-round** mm | Strong audit trail in-file. |

---

## Summary statistics

_Counts are by **primary category** assigned in the table (N = **34** instrument-definition files). Some rows could fairly carry a secondary tag (e.g. REFERENCE-DERIVED + SUSPECT-ROUND-NUMBERS); only one primary was stored._

| Category | Count |
|----------|------:|
| VERIFIED | 11 |
| REFERENCE-DERIVED | 8 |
| SUSPECT-ROUND-NUMBERS | 2 |
| SUSPECT-DUPLICATE-VALUES | 4 |
| UNVERIFIABLE-NO-SOURCE | 5 |
| UNVERIFIABLE-MISSING-SOURCE | 4 |
| EXPLICIT-PLACEHOLDER | 0 |

*`all_extractions.json` is counted under **UNVERIFIABLE-NO-SOURCE** (stale/invalid bbox output, not a cited plan extraction). **SUSPECT-DUPLICATE-VALUES** = four electric specs sharing the **71 × 40 × 19.x** mm humbucker tuple (Les Paul, Explorer, Flying V, Klein).*

**`instrument_model_registry.json`:** Reviewed for `STUB` / `PARTIAL` / asset path patterns — **not counted** in the table above (aggregate metadata, not a dimension spec).

---

## Recommendations — manual verification priority

1. **Humbucker route template (highest duplication risk)** — **`gibson_les_paul.json`**, **`gibson_explorer.json`**, **`gibson_flying_v_1958.json`**, **`klein_guitar.json`**: Confirm **71 × 40 × 19.x** against each instrument’s real plan or OEM drawing. If Klein truly shares that envelope, document **why** in the spec.

2. **Carlos Jumbo** — Re-derive scale from **acoustic** references only; re-check body outline page vs **`JUMBO-CARLOS-*-3.pdf`** now that methodology doubt is recorded in-file.

3. **Strat authority** — Reconcile **`stratocaster.json`** vs **`fender_stratocaster.json`**; retire or clearly mark one as **legacy**; commit or permanently link **Fender-Stratocaster-62.pdf** / **Strat-Body-Front.pdf** if they remain cited.

4. **`all_extractions.json`** — Fix or quarantine **SG** (and any other **>700 mm** “width” entries); exclude from production pipelines until bounded.

5. **Manufacturer-only electrics** — **`gibson_es_335.json`**, **`gibson_melody_maker.json`** (specs folder), **`gibson_sg.json`** (cavity-free): attach **one** canonical PDF or export per file, or retitle sources as **“compiled reference”** rather than extraction.

6. **Benedetto AI path** — Manual numeric check of **`benedetto_17.json`** against **`Benedetto Front.jpg` / `Back.jpg`** before relying on rope or archtop CAM.

7. **Gibson L-00** — Obtain **local** grellier PDF or equivalent, or change `source` to a **URL + checksum** so future audits can fetch the same document.

---

## Audit artifacts

- **Report path:** `docs/audit/spec_data_verification_2026-04-27.md`
- **Workspace examined:** `c:\Users\thepr\Downloads\luthiers-toolbox`
- **No spec JSON files were modified** during this audit.
