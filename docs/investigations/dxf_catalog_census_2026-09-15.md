# DXF catalog census and debris removal (2026-09-15)

**Status:** census complete; this PR deletes the debris it identified.
**Scope:** every DXF stored under `services/api/app/instrument_geometry/`, as of `f089f570`
(the merge of DXF-CATALOG-GATE-001, PR #378).
**Method:** provenance from the first commit that added each file
(`git log --diff-filter=A --follow`); contents read with the merged catalog policy
(`app/ci/dxf_catalog_geometry.py`); references from `git grep` over code and data, excluding
docs, the archaeology reports under `reports/`, and the registry itself. Body dimensions are
measured from the geometry on the declared outline layers, never taken from a manifest.

## What was there: 95 files in six groups

| Group | Files | What they are | Nothing reads |
|---|---|---|---|
| Curated body outlines | 17 | One closed outline per file; measured size agrees with `body/catalog.json`. Stored R2000/R2010 against the R12 ruling | 0 |
| Cuatro reference traces | 62 | Two vectorizer runs over the same two cuatro plans: 20 contour traces, 20 primitive dumps, ~20 feature-layer extractions | 59 |
| Vectorizer page dumps | 6 | Whole blueprint sheets, not bodies: title text, bracing, kerfing, hardware, neck and headstock on their own layers | 3 |
| AI-vision extractions | 5 | Added 2026-03-04 by AI vision passes; four measure nothing like their catalog entry | 0 |
| Smart Guitar design files | 4 | Own design, v1 and v6 front/back; outline measures 377 x 439 mm | 3 |
| CAM template | 1 | `LesPaul_CAM_Closed.dxf`, loaded at runtime by the Les Paul G-code generator | 0 |

**65 of the 95 were referenced by no code and no data.** 21 of the 33 body files entered in one
commit on 2025-12-14 ("Recover remaining modules"); the AI-vision set and the Melody Maker and
Cuatro files arrived on 2026-03-04.

## Finding: the catalog advertises sizes the files do not have

`body/catalog.json` states dimensions per body. Five disagree with the geometry in the file it
points at:

| Catalog entry | Claimed | Measured on the outline layer |
|---|---|---|
| `jaguar` | 330 x 450 mm | **20.9 x 25.6 mm** |
| `mustang` | 310 x 420 mm | **39.7 x 40.8 mm** |
| `jazzmaster` | 272 x 423 mm | **158.0 x 104.1 mm** |
| `carlos_jumbo` | 400 x 520 mm | 400.0 x 360.0 mm |
| `octave_mandolin` | 280 x 350 mm | 364.8 x 408.3 mm |

`jazzmaster_body.dxf` **passes** both gates: a wrong-sized outline is still a closed, simple,
preflight-valid outline. Dimensions against spec are outside the gate contract by ruling, and this
is what that exclusion costs.

**These five files are not touched by this PR** (owner instruction, 2026-09-15): each is wired into
`catalog.json`, and three into specs or scripts, so removing them changes what the body catalog
serves. That is a separate decision.

## Deleted here: 62 files

Every file below is referenced by no code and no data, and none is in `body/catalog.json`.

- **59 cuatro reference traces** under `reference_dxf/cuatro/` — all of
  `Cuatro_DXF_Simple_Package/`, `regenerated_v3/`, `simple_extract/` and `test_raw/` except the
  three files tests still read (`cuatro puertoriqueño.dxf`,
  `Cuatro_DXF_Simple_Package/cuatro_puertoriqueño_simple.dxf`,
  `simple_extract/cuatro_puertoriqueño_simple.dxf`).
- **3 vectorizer page dumps**: `acoustic/orchestra_model_body_view.dxf` (1,946 entities, 913 x 769 mm
  sheet, no outline layer), `electric/flying_v_full.dxf` (whole instrument: neck, headstock,
  hardware), `electric/flying_v_body_phase3.dxf` (superseded by `flying_v_body.dxf`, which the
  catalog points at).

Their three quarantine records are removed from `dxf_catalog_registry.json` in the same commit; a
record for a missing asset fails both gates by design.

## Gate result after removal

Both gates, exit 0: **33 files, 6 PASS, 27 QUARANTINED, 0 FAIL** (was 95 / 65 / 30 / 0). The drop in
PASS is the 59 deleted reference traces, which passed the reference contract; the drop in
QUARANTINED is the three deleted records.

## Adjudication closed for the files that remain

**Owner ruling, 2026-09-15:** the catalog files that code or data still reference need no further
adjudication. They will be replaced at some point. The 27 quarantine records stay, because they are
what keeps the gates honest about known nonconformance, but they are not a work queue and nobody
owes a disposition against them. That includes the five whose measured size contradicts
`body/catalog.json`, the three page dumps the catalog still points at, and
`LesPaul_CAM_Closed.dxf`, which is `UNADJUDICATED` in the registry only because its layer roles were
never demonstrated.

This closes the adjudication step of the DXF order. It does not change any gate behaviour: a
recorded file is still QUARANTINED, not passed, and manufacturing authority is still recorded in CI
only - no runtime path reads the registry.

## Left for whoever replaces these files

- The five wired files above, and their `catalog.json` entries.
- The three page dumps the catalog still points at (`orchestra_model_clean.dxf`,
  `Gibson-Melody-Maker_phase3_primitives.dxf`) and `Gibson-Melody-Maker_phase3.dxf`, whose
  `BODY_OUTLINE` layer is a clean closed chain inside a full-sheet dump.
- Spec files for deleted or suspect assets (`specs/carlos_jumbo.json` and similar) — this PR
  removes DXFs only.
- The 15 `NONCONFORMING_VERSION` records: R2000/R2010 storage awaiting regeneration as R12.
