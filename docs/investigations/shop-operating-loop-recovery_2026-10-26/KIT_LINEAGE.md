# Kit lineage (track C)

**Finding:** no reusable, versioned commercial kit exists in any scoped repo
(SOL-C08 MISSING). What exists falls into three categories, each with a
different authority:
- **Sales configuration:**
  - CNC-PS `InstrumentProductV2` (SOL-C07)
  - LTB estimator presets in localStorage (inside SOL-B01)
- **Commercial cost templates:** LTB BOM/COGS templates (SOL-C01)
- **Design inputs and takeoffs:**
  - instrument spec JSONs (SOL-C02)
  - the photo-vectorizer material BOM (SOL-C03)
  - the species catalog (SOL-C06)

| Row | Kind | Reusable | Versioned | Substitutions recorded | Qty and units explicit | Job pins a revision |
|---|---|---|---|---|---|---|
| SOL-C01 BOM/COGS templates | Commercial cost template | Yes (by `InstrumentType`) | **No.** Class dict, no id. | No | **Yes** (`quantity`, `unit`, `unit_cost`) | No. Nothing links a BOM to a project or job. |
| SOL-C07 CNC-PS `InstrumentProductV2` | Sales/product configuration | Yes (`product_id`) | Schema-versioned only. Records carry `status`, no revision chain. | No | Partial (`components` lists) | No. No quote or job references a product. |
| SOL-C02 instrument spec JSONs | Design input | Yes | Git history only; registry `version: 1.1.0` | Prose only ("X or Y") | No | No |
| SOL-C03 material BOM (photo-vectorizer) | Design takeoff per outline | Per run | No | No | Area units with waste factor | No |
| SOL-C06 wood species catalog | Material identity (species) | Yes | Git + sourcing policy | n/a | n/a | No. Species, not a physical board. |
| SOL-C04 InventoryView / OrdersView | UI mock | — | — | — | — | — |
| SOL-C05 archtop "contour kits" | Concept (measurement kits) | — | — | — | — | — |

## Lineage notes

- `services/photo-vectorizer/material_bom.py` (`1f409640…`) descends from
  `files - 2026-03-14T134741.895/patch_08_material_bom.py` (`c32da040…`,
  deleted in `1f4b9b30`, pre-rewrite). The content differs, so they are a
  lineage, not duplicates.
- Plans for "BOM templates by instrument type" are in
  `docs/BUSINESS_SUITE_SPEC.md:65,161`. They shipped as SOL-C01, without
  versioning.

## Authority boundary

None of these artifacts decides anything about manufacturing:
- the BOM and product records are commercial
- the specs are design references
- the species catalog governs material properties under the CLAUDE.md
  sourcing policy, not stock

A kit that a job pins would be commercial authority only. It must not carry
or imply CAM readiness.

**Owner question R3:** should a future kit be built on SOL-C01 (LTB templates)
or on SOL-C07 (CNC-PS product records)? It should be decided before any kit
work, and no kit work is recommended next.
