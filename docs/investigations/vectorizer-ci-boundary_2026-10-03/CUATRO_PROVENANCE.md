# Cuatro provenance — two byte-identical paths, roles unresolved

**Disposition for both paths: `ROLE_UNRESOLVED`.** Nothing in this increment deletes, moves,
rewrites or deduplicates either file. Neither carries manufacturing authority.

## The two files

Measured on `origin/main` `aaf38e4a0437b20d2ad4191f06cb7368a348f9c7`, both by `ezdxf` modelspace
iteration and by a raw R12 `0\nLINE` token count (the two agree):

| Path (under `services/api/app/instrument_geometry/reference_dxf/cuatro/`) | Bytes | SHA-256 | DXF | Entities | Layers |
|---|---:|---|---|---|---|
| `simple_extract/cuatro_puertoriqueño_simple.dxf` | 16,264,730 | `41e62ec08c1c748681f43d05c1abab305978b5cce6ef1278a6ddc36be639613a` | AC1009 (R12) | 128,997 `LINE` | `CONTOURS` |
| `Cuatro_DXF_Simple_Package/cuatro_puertoriqueño_simple.dxf` | 16,264,730 | `41e62ec08c1c748681f43d05c1abab305978b5cce6ef1278a6ddc36be639613a` | AC1009 (R12) | 128,997 `LINE` | `CONTOURS` |

The handoff's expected size, hash and count all matched. Byte identity is recorded; it is **not**
evidence that the two paths serve the same role (frozen decision 6).

A third file in the same folder, `cuatro puertoriqueño.dxf` (729,456 bytes, 4,605 `LINE`, six
feature layers), is a different artifact and is out of scope here.

## Candidate roles — both unproven

| Candidate role | Status | What would prove it | Found |
|---|---|---|---|
| benchmark witness | candidate, unproven | a committed record naming one of these **paths** as the measured anchor | none — see below |
| plan-package artifact | candidate, unproven | a committed package manifest, companion set, or delivery record for `Cuatro_DXF_Simple_Package/` | none |

Folder names were not used as evidence of role.

## History

| Fact | Evidence |
|---|---|
| Both paths entered git in the **same commit** | `8d91c4c7ecefe5a275341bc5edf1ebe03569d017`, 2026-04-05 17:31 −05:00, "fix(vectorizer): Phase 5 classified mode fixes" — a 4,553-file commit whose message does not mention either file |
| No renames, no later edits | `git log --follow` on each path returns only `8d91c4c7` |
| Companions arrived with each, and were later deleted | 8 sibling `*_simple.dxf` files in each folder; deleted as unreferenced debris by `791b8d971f8bc7fcfa09b6c0d76563a863fab537` (PR #379, 2026-09-15), manifest `.cbsp21/patches/dxf-catalog-debris-removal-001.json` |
| Why these two survived #379 | That manifest: "The three cuatro traces that tests read are kept." `docs/investigations/dxf_catalog_census_2026-09-15.md:52-56` names exactly these two plus `cuatro puertoriqueño.dxf` |
| The folders pre-date the commit, outside git | `9d75d69289b6ae8616abd91fea7b70829ba02f94` (2026-03-06 16:52) gitignored `Cuatro/simple_extract/` among others — `docs/audit/VECTORIZER_PROVENANCE_FORENSIC_2026-09-17.md` §4.1 |
| Origin of the content | Same audit, §4.1 (VERIFIED): the ten `_simple.dxf` files were created on `G:\My Drive\El Cuatro` on 2026-03-06 23:08, copied into `Guitar Plans/El Cuatro/` on 04-01, and listed in `simple_extract/` and `Cuatro_DXF_Simple_Package/` by an inventory on 04-16 |
| Date discrepancy, unresolved | The #379 census says the cuatro files "arrived on 2026-03-04"; git says 2026-04-05. The census date is most likely a filesystem date; not adjudicated here |

## Who names the 128,997-entity anchor

| Record | What it names |
|---|---|
| `docs/audit/VECTORIZER_PROVENANCE_FORENSIC_2026-09-17.md` §4.2 | "Anchor `cuatro_puertoriqueño_simple.dxf`" — **filename only, no folder**; all 11 recorded fields match both paths |
| `docs/dxf_svg_generation_architecture.md:137` | "`cuatro_puertoriqueno_simple.dxf` (15.5MB, 129,000 LINE entities)" — filename only, approximate |

No record names one path as the anchor over the other.

## Current references

| Consumer | Reads | Path-specific? |
|---|---|---|
| Runtime application code | nothing | — |
| `tests/test_dxf_catalog_registry.py:48` | enumerates every catalog `*.dxf` by `rglob` to check classification | no |
| `tests/test_dxf_runtime_authority.py:191,198` | enumerates by `rglob`; asserts no asset is manufacturing-authorized | no |
| `.github/workflows/dxf_validation.yml`, `dxf_validation_gate.yml` | parse every catalog DXF, but only when a `.dxf` under `instrument_geometry/` changes | no; not required checks |
| `reports/archaeology/vec_archaeo_001/sessions.json` | historical session record listing the package folder | archival, not a consumer |

The two `rglob` tests take milliseconds on CI. **Neither file contributes to the observed default-pytest
delay** — see `TEST_RUNTIME_CENSUS.md`.

## Regeneration

**In this repository:** no committed command regenerates either file, and the source plan
(`cuatro puertoriqueño.pdf`) is not committed here.

**In vectorizer-sandbox:** the anchor's content has been reproduced, not byte-for-byte.
`docs/audit/VECTORIZER_PROVENANCE_FORENSIC_2026-09-17.md` §12: `scripts/light_line.py` (sandbox
PR #104, merged 2026-09-18 as `003562c73cd29a2574e99932b698bea3a6d53177`, present on the sandbox
default branch) produced 128,997 `LINE` entities at render 400 / 0.1 mm/px, with ten of eleven
recorded fields exact and the file size differing by +72 bytes. That reproduces the anchor's
content; it does not reproduce these bytes and does not say which path is the anchor.

Regeneration authority in this repository: **none**.

## Authority

No manufacturing authority. `tests/test_dxf_runtime_authority.py::test_no_catalog_asset_is_manufacturing_authorized_today`
asserts that no catalog DXF resolves to `ALLOWED`. Storage under `instrument_geometry/` grants nothing.
Neither file inherits `CAM_READY` status (see `SANDBOX_BOUNDARY.md`).

## What tests should use

Neither path. No test in this increment reads either file. A future benchmark that needs the
anchor should pin it by SHA-256 (`41e62ec0…`), not by folder, until the role is adjudicated.
