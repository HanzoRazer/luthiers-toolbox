# RMOS-AUTHORITY-MAP-001 — Stage 1 Checkpoint

**Status:** STAGE 1 COMPLETE — awaiting owner review of the capability model.  
**Date:** 2026-08-27  
**Base:** `origin/main` at execution (`93df82f3`, after #327).  
**Nature:** one-off read-only census. **This document authorizes no remediation.**

This is not an agent report. Grounding Agent v0.1 remains the only agent under
trial (`GA-TRIAL-0002`, MATCH / PROCEED). The census is an ordinary script plus
an inert JSON registry, the same shape as the GEN-5 instrument-library census.

**Presence in the registry grants no execution authority.** The file is not a
runtime consumer and must not be imported by production code.

This registry does **not** replace:

| Adjacent map | Concern |
| --- | --- |
| `docs/governance/CANONICAL_AUTHORITY_MAP.md` | semantic ownership |
| `services/api/app/cam/geometry_authority_registry.py` | 7T geometry references; no machine-output authority |
| `services/api/app/cam/ontology_authority_map.py` | 7M vocabulary; `execution_authorized = false` |

Cross-reference (do not rewrite): [`rmos_prod_audit_001.md`](rmos_prod_audit_001.md),
[`rmos_prod_output_census_001b.md`](rmos_prod_output_census_001b.md),
[`PROFILING-ROUTE-ANNOTATION-001.md`](PROFILING-ROUTE-ANNOTATION-001.md).

Dev Order: [`docs/handoffs/RMOS_AUTHORITY_MAP_001_DEV_ORDER.md`](../handoffs/RMOS_AUTHORITY_MAP_001_DEV_ORDER.md).

---

## 1. Scope (Stage 1)

Stage 1 answers: **is the capability model itself correct?**

In scope: mounted-route inventory, machine-output candidate selection, deterministic
capability grouping, seeded `UNKNOWN` / `INSUFFICIENT_EVIDENCE` registry, schema,
MAR-001–008 and MAR-021–024, this checkpoint.

Out of scope (Stage 2, only if authorized): deep authority/persistence
classification (MAR-009–020), post-#324 V-carve exposure classification,
runtime POST witnesses, any production change.

---

## 2. Methodology

Evidence order used in Stage 1:

1. Mounted FastAPI route table from `app.main:app`, **recursing**
   `_IncludedRouter` (naive `app.routes` is 155 objects / 6 `APIRoute`; walked
   unique paths are 1081; OpenAPI has 1077 paths).
2. OpenAPI path set as a completeness cross-check (format differences only;
   `{file_path:path}` vs `{file_path}`).
3. Path-pattern inclusion for machine-consumable output (G-code / `.nc` /
   operator-pack / post / wrap / helical_entry / feeds-speeds / bundles).
4. Explicit exclusion table (declared purpose: simulation, visualization,
   metadata catalogs).
5. Deterministic grouping: longest seeded path prefix, then derived path-family.

Not used in Stage 1: POST request witnesses, handler AST, evaluator call graphs,
client call sites as authority.

---

## 3. Checkpoint numbers

| Measure | Count |
| --- | ---: |
| Top-level `app.routes` objects | 155 |
| Walked HTTP operations (incl. duplicate mounts) | 1155 |
| Unique mounted operations | 1140 |
| Unique mounted paths | 1081 |
| OpenAPI paths | 1077 |
| Machine-output candidates | 67 |
| Hint matches excluded by declared purpose | 7 |
| Capabilities in the registry | 26 |
| Required seeded capabilities (all have routes) | 14 |
| Additional prefix-grouped capabilities | 4 |
| Remainder derived from path family | 8 |
| Unexplained emitters | 0 |
| Capabilities with more than one route (aliases) | 14 |
| Duplicate mounts (same path+method, de-duplicated) | 15 |

Validation: `PYTHONPATH=services/api python scripts/audit/rmos_authority_map.py --validate` → OK.

---

## 4. Capability grouping (the model under review)

### 4.1 Required seed set (14) — all mounted

| capability_id | Routes | Grouping |
| --- | ---: | --- |
| retract | 4 | `/api/cam/retract` |
| adaptive | 2 | `/api/cam/pocket/adaptive` |
| drilling | 3 | `/api/cam/drilling` (modal + pattern + intent) |
| profiling | 2 | `/api/cam/profiling` |
| vcarve | 3 | production + toolpath + intent |
| roughing | 2 | toolpath gcode + `gcode_intent` |
| helical | 1 | `/api/cam/toolpath/helical_entry` |
| rosette | 2 | `plan-toolpath` + `post-gcode` |
| probing | 17 | `/api/probe/*` (5 families × aliases) + `/api/v1/machines/probe/{corner,surface}` |
| binding | 2 | channel + purfling |
| inlay | 1 | `/api/art-studio/inlay/export-gcode` |
| radius-dish | 1 | `/api/acoustics/radius-dish/generate-gcode` |
| feeds-speeds | 1 | `/api/cam/opt/feeds-speeds` (JSON, not G-code) |
| biarc-contour | 1 | `/api/cam/toolpath/biarc/gcode` |

### 4.2 Additional prefix-grouped (4)

These are not in the original 14 but have an unambiguous path prefix, so they
were not left as a coarse derived family:

| capability_id | Routes | Why prefixed |
| --- | ---: | --- |
| pocketing | 1 | `/api/cam/pocketing/intent-gcode` |
| polygon-offset | 2 | `.nc` + `_governed.nc` aliases |
| neck-gcode | 2 | `/api/neck/gcode/{generate,download}` |
| operator-pack | 1 | `GET /api/rmos/runs_v2/{run_id}/operator-pack` |

### 4.3 Remainder derived from path family (8)

| capability_id | Routes | Note |
| --- | ---: | --- |
| cam-guitar | 7 | electric body/neck + acoustic body/soundhole/binding |
| geometry | 4 | `export_gcode` (+ governed) + bundles |
| saw-batch | 3 | GET stored toolpath G-code |
| cam-post | 1 | `/api/cam/post/post_v155` |
| rmos-wrap | 1 | `/api/rmos/wrap/mvp/dxf-to-grbl` |
| v1-dxf | 1 | `/api/v1/dxf/cam/gcode` |
| vision | 1 | `/api/vision/photo-to-gcode` |
| headstock-transition | 1 | `/api/headstock/transition/gcode` |

Retract aliases are the canonical example of D2: four URLs, one capability.

---

## 5. Excluded surfaces (hint matched, declared not machine output)

| Path | Reason |
| --- | --- |
| `/api/cam/sim/gcode` | consumes / simulates G-code; analysis |
| `/api/cam/gcode/plot.svg` | visualization |
| `/api/cam/gcode/estimate` | estimate, not emission |
| `/api/cam/gcode/simulate` | simulation |
| `/api/neck/gcode/styles` | metadata catalog |
| `/api/neck/gcode/profiles` | metadata catalog |
| `/api/neck/gcode/tools` | metadata catalog |

Drawing DXF, blueprint vectorization, and design exports were **not** pulled in
by the path-pattern inclusion rule, so they never entered the candidate set.

---

## 6. Taxonomy additions requested (do not guess)

Stage 1 stopped rather than merge these. Owner ruling wanted before Stage 2:

1. **Post / wrap.** Census 001B treated `cam/post/post_v155`,
   `rmos/wrap/mvp/dxf-to-grbl`, and `v1/dxf/cam/gcode` as one family. Stage 1
   kept three capabilities because the prefixes differ. Merging them is a
   product decision, not a path fact.
2. **Guitar body vs acoustic binding vs CAM binding.** Acoustic
   `{style}/binding/gcode` is under `cam-guitar`, not `binding`.
3. **Neck surfaces.** `neck-gcode`, `cam-guitar` `/{model_id}/neck/gcode`, and
   `headstock-transition` are three capabilities. One “neck” family would be a
   guess.
4. **Operator pack.** Retrieval of an already-persisted governed bundle vs a
   manufacturing capability of its own.
5. **Saw-batch GET G-code.** Retrieval of stored toolpaths vs generation.
6. **feeds-speeds.** Required seed, but the artifact is JSON, not G-code.
   Confirm it belongs on the manufacturing-output surface.
7. **Duplicate mounts.** 15 `(path, method)` pairs are mounted twice. Inventory
   de-duplicates them; they are not 15 extra capabilities.
8. **Adaptive plan** is not a machine-output candidate (no G-code path token).
   The capability currently holds only `gcode` + `batch_export`. Confirm that
   split is the intended model.

---

## 7. Reachability and evidence limitations

Every registered in-scope route is `reachability = MOUNTED` with
`runtime_evidence = NOT_OBTAINED_STAGE_1` and
`authority_disposition = UNKNOWN`.

That is deliberate:

- Source presence was **not** promoted to LIVE.
- Empty `client_consumers` was **not** promoted to dead (MAR-022).
- No POST was issued. Stage 1 does not deep-trace evaluators or persistence.

| Runtime witnesses attempted | none |
| Runtime witnesses withheld | all POST machine-artifact endpoints; any persist / file-export / machine-control / override path |

V-carve production is **mounted** after #324. Whether it is
`POST_MERGE_AUTHORITY_EXPOSURE` is a Stage 2 classification.

---

## 8. Tests

`services/api/tests/rmos/test_manufacturing_authority_registry.py`  
`services/api/tests/rmos/test_manufacturing_authority_discovery.py`

22 passed: MAR-001–008, MAR-021–024, plus Stage-1 “no conclusions yet” guards
and a live reconcile against `app.main:app`.

MAR-009–020 are not implemented. They require authority conclusions.

---

## 9. What this checkpoint does not authorize

- No CAM, RMOS, feasibility, route, client, persistence, or G-code change.
- No new agent, workflow, or standing mapper service.
- No Stage 2 classification.
- No remediation queue spawned from these findings.

The next manufacturing cutover, if any, should be authorized capability-by-capability
against this registry’s *before* state — after the owner accepts or amends the
grouping above.
