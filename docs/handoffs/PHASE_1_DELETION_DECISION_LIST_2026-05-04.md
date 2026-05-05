# Phase 1 Deletion Decision List

**Date:** 2026-05-04  
**Status:** Awaiting approval  
**Source:** PHASE_1_MODULE_CLASSIFICATION_2026-05-04.md

---

## Summary

No files deleted in this phase. This document converts the Phase 1 classification report into approval-ready cleanup decisions.

**Totals:**
- Safe Delete: 5 modules
- Archive First: 2 modules
- Absorb Later: 0 modules
- Keep: 0 modules

---

## Safe Delete

| Path | Reason | Evidence | Risk |
|------|--------|----------|------|
| `files - 2026-03-31T002554.594/` | Spiral soundhole prototype; code absorbed into `SpiralSoundholeDesigner.vue` and `soundhole_router.py` | Main app has production version at `packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue` | None — snapshot is historical only |
| `files - 2026-04-14T102549.923/` | Body side arc solver + CSV data; algorithm integrated into `arc_reconstructor.py` | Referenced in comments only at `arc_reconstructor.py:1161` | None — verification data, not production dependency |
| `files - 2026-04-16T160551.956/` | Guitar spec JSONs (acoustic_00, gibson_l0, om_acoustic); staging data | No imports found; production specs should be in `services/api/app/instrument_geometry/specs/` | None — orphan staging data |
| `files - 2026-04-16T161657.416/` | Guitar spec JSONs (jumbo_fesselier, selmer_maccaferri_d_hole); staging data | No imports found | None — orphan staging data |
| `files - 2026-04-23T090806.069/` | DXF conversion script + output + sprint prompt | One-off script, not production | None — sprint artifact |

---

## Archive First

| Path | Reason | Archive Destination | Risk |
|------|--------|---------------------|------|
| `Interactive_Headstock_Generator/` | Historical reference for headstock design approach; 23 files across 4 timestamped subdirs + 4 HTML demos | `archive/experimental/2026-03/Interactive_Headstock_Generator/` | Low — main app has `HeadstockDesignerView.vue` with different APIs |
| `Interactive_Neck and Cam _Modules/` | Historical CAM panel development; contains `CAM_SURVEY.md` survey document; 95 files across 18 subdirs | `archive/experimental/2026-03/Interactive_Neck_and_Cam_Modules/` | Low — main app has production `cam/neck/` components |

---

## Absorb Later

None identified. All useful code has already been absorbed into the main app:

| Original | Absorbed Into |
|----------|---------------|
| Spiral soundhole | `packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue` |
| Body side arc solver | `services/api/app/instrument_geometry/body/ibg/arc_reconstructor.py` |
| CAM panels | `packages/client/src/components/cam/neck/*.vue` |
| DXF import/export | `packages/client/src/composables/useDxfImport.ts`, `useExportDxf.ts` |
| Headstock designer | `packages/client/src/views/art-studio/HeadstockDesignerView.vue` |

---

## Keep

None identified. All 7 modules are detached from the main app and superseded by production code.

---

## Explicit Non-Actions

- No deletion performed.
- No source movement performed.
- No refactor performed.
- No NECK-A work performed.

---

## Approval Required

Deletion may proceed only after human approval of this document.

**Approval options:**
1. Approve Safe Delete only — delete 5 snapshot directories
2. Approve Safe Delete + Archive First — delete 5 snapshots, move 2 prototypes to archive
3. Defer all — keep everything pending further review
4. Modify list — adjust categorization before proceeding

---

*End of deletion decision list*
