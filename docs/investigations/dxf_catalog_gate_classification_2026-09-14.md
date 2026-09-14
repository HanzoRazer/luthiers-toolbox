# DXF-CATALOG-GATE-001 — declarative catalog gate: classification and records (2026-09-14)

**Status:** landed with this PR. Both DXF catalog gates read one registry,
`services/api/app/ci/dxf_catalog_registry.json`, through `services/api/app/ci/dxf_catalog_policy.py`.
**Evidence base:** `docs/investigations/dxf_gate_repair_audit_2026-09-14.md` (rule-by-rule audit of the
Copilot/Cursor repair) and `docs/investigations/dxf_topology_crlf_catalog_rerun_2026-09-14.md`.

## Owner rulings implemented

| Ruling (2026-09-13/14) | Where it lives |
|---|---|
| The Files gate is an export-readiness gate; no blanket warning downgrade | `check_dxf_files.py`: every clause failure fails, unless an explicit record covers exactly that clause |
| Folder + layer define asset class, declared rather than scattered through code | registry `class_rules`, `outline_layers`, `reference_layers`, `layer_evidence` |
| `BODY_POINTS` is reference/measurement data | registry `reference_layers`; the manufacturing view drops it before preflight and topology |
| `WIRING_CHANNEL` open paths are not declared valid until the CAM consumer is traced | not declared; `LesPaul_CAM_Closed.dxf` is `UNADJUDICATED` |
| Stored catalog DXFs are R12 only; R2000 is bucket-① paid-tier vectorizer output | registry `version_policy.approved = ["AC1009"]`; no per-file allowance |
| Quarantine records carry asset, asset_class, failed_contract, observed_evidence, disposition, reason, owner_stream, manufacturing_authority = BLOCKED, exit_condition | registry `quarantine`; `test_quarantine_records_are_complete_and_blocked` |
| Owner stream is DXF Catalog Integrity, not Ross | every record; enforced by test |
| Complexity < 15, no baseline raised | highest new function 12; `check_dxf_files.main` 29 → 11, baseline entry removed |
| Malformed witnesses must still fail | `services/api/tests/test_dxf_catalog_gate.py` |

## How a file is judged

1. The registry classifies the path: `body/dxf/*/*.dxf` = `manufacturing_body`, `reference_dxf/*` =
   `reference`. An unclassified catalog file **fails**.
2. Each clause in the class contract is evaluated (the asset gate evaluates the ezdxf-only clauses; the
   Files gate evaluates all of them). A check that crashes is a failure of that clause.
3. No failures: **PASS**. Failures with no record: **FAIL**. Failures with a record: **QUARANTINED**,
   but only if the failures are exactly the record's declared clauses. An extra failure fails the gate,
   a declared clause that now passes makes the record stale and fails the gate, and a record for a
   missing file fails the gate.

## Result on the current catalog (both gates, CI toolchains)

**95 files: 65 PASS, 30 QUARANTINED, 0 FAIL.**

- PASS: the 62 `reference_dxf/cuatro` traces; `Cuatro_Venezolano_body.dxf` and `jazzmaster_body.dxf`
  (closed R12 LINE outlines); `Gibson-Melody-Maker_phase3.dxf` (its `BODY_OUTLINE` LINE chain closes
  and bounds the layer under the corrected LINE-loop semantics).
- QUARANTINED, by disposition:

| Disposition | Count | Assets |
|---|---|---|
| `NONCONFORMING_VERSION` | 15 | stored R2000/R2010 but every geometry clause passes: classical, dreadnought, gibson_l_00, J45_body_outline, J45_body_outline_dense, Jumbo, om_000, soprano_ukulele, flying_v_body_phase3, gibson_explorer_body, JS1000, LesPaul_body, Smart-Guitar-v1_back, Smart-Guitar-v1_front, smart_guitar_back_v6_smoothed |
| `QUARANTINED` | 1 | Stratocaster_body: folded BODY_OUTLINE ring |
| `QUARANTINE_CANDIDATE` | 13 | smart_guitar_front_v6_smoothed (twist); harmony_h44, concert_ukulele, octave_mandolin (open outlines, asset intent pending); orchestra_model_body_view, orchestra_model_clean, Gibson-Melody-Maker_phase3_primitives (appear misclassified by location); flying_v_body, flying_v_full (outline role unadjudicated); carlos_jumbo, mandolin, jaguar, mustang (closed R12 POLYLINE, rejected by the runtime pre-check) |
| `UNADJUDICATED` | 1 | LesPaul_CAM_Closed (WIRING_CHANNEL and CUTOUT roles not demonstrated) |

Every record's exit condition names what would clear it. Most end in "regenerate as R12 through
`dxf_compat`", because no body file may stay stored as R2000.

## How each audited rule was resolved

| Audit rule | Resolution |
|---|---|
| F0 lazy import | on main via #372 |
| A1 closed R12 LINE loops | kept, reimplemented: pruned-graph components, 0.05 mm snap, duplicate edges ignored, ARC/open-SPLINE edges chain too. The closed contour must **bound the outline layer** (≥ 0.9 of its extents in both axes), so a small closed strip cannot stand in for the body (the Flying V case) |
| A1 CIRCLE as a body contour | dropped: CIRCLE never counts |
| A2 R2010 widening | superseded by the R12-only ruling |
| A3 no closed contour → warning | rejected: `closed_outline` is a failing clause |
| F1 numeric version compare | moot: the version clause is an explicit approved list |
| F2/F3 empty / no-geometry hard fail | kept (`nonempty`, `geometry_present`) |
| F4 open LWPOLYLINE → warning | rejected; `BODY_POINTS` exempted by declaration instead |
| F5 closed POLYLINE accepted | **reversed** (see the audit's correction note): the runtime rejects it |
| F6 self-intersection → warning | rejected; chained outlines are now also checked for crossings |
| F7 preflight crash → "skipped" | rejected: a crash is a clause failure (topology too) |
| F8 remaining preflight ERRORs block | kept, now on the manufacturing view |

## What the gate still does not check

These are out of the ruled contract. They are recorded here so a green gate is not read as more than it is:

- **Dimensions.** Nothing compares a body against its instrument spec; the asset gate's old docstring
  claimed it did, and it never did (the docstring is corrected). Observed: `jazzmaster_body.dxf`
  158 × 104 mm (PASS), `jaguar_body.dxf` 20.9 × 25.6 mm and `mustang_body.dxf` 39.7 × 40.8 mm (both
  `$INSUNITS=4`, mm), `mandolin_body.dxf` 200 × 90 mm. The last three are noted in their records.
- **Header units.** 20 of the 25 R2000/R2010 body files declare `$INSUNITS=6` (metres) while their
  coordinates are millimetres (the other 5 declare 4, mm).
- **Half-body closed by a centreline.** A half outline closed by a centreline LINE is a closed contour
  that bounds its own layer, so it passes. Only asset intent or a spec comparison can tell.
- **Title-block borders on an outline layer.** A closed border on `BODY_OUTLINE` would bound the layer;
  no catalog file does this today.
- **What CAM actually consumes.** `preflight_valid` mirrors the runtime pre-check, not every consumer;
  the CAM lanes read closed LWPOLYLINE only, and R12 cannot carry LWPOLYLINE. That is consistent with
  the tier rule (CAM input is the paid-tier vectorizer's R2000 output), but the consumers of the catalog
  files themselves (`body/outlines.py`, `catalog.json`) were not traced here.
