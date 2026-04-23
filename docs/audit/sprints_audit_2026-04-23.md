# SPRINTS.md Mechanical Audit
**Date:** 2026-04-23
**Auditor:** Claude Code (automated)
**Scope:** Status verification against actual repo state

---

## Executive Summary

SPRINTS.md contains 9 active sprints, 9 queued sprints, and 3 tech debt items. Audit found **2 confirmed tech debt regressions** (spiral_geometry.py and archtop_floating_bridge.py still use ezdxf.new("R2000") despite being marked migrated), **1 sprint with inflated status** (Sprint 8 claims docs/instrument_library/ location that does not exist), and **several queued sprints that may be partially completed or superseded**. Sprint 1, Sprint 3, Sprint 5, Sprint 7, and Sprint 7.5 statuses are accurate. Sprint 2 has stale open items that have been resolved.

---

## Per-Sprint Findings

### ACTIVE SPRINTS

| Sprint | Claimed Status | Verified Status | Discrepancies |
|--------|---------------|-----------------|---------------|
| **Sprint 1** (Vectorizer Reconciliation) | COMPLETE | **ACCURATE** | All commit SHAs verified: 04735bd4, 72bfffc9, 059cf5b0, a76102c2, 5a145e90, ebffbd53, 722cc03d, cb0761ed, 3db07c62 |
| **Sprint 2** (Repo Split) | In progress | **PARTIALLY STALE** | flying_v phantom entry now resolved (gibson_flying_v_1958.json exists at specs/). VECTORIZER_ACCURACY.md exists. Archtop scripts exist. Some open items resolved but not marked. |
| **Sprint 3** (Remediation) | In progress | **TECH DEBT ACTIVE** | dxf_writer.py exists (4c4f1a52). BOE endpoint exists (editor_export_router.py). **BUT**: spiral_geometry.py line 270 still has `ezdxf.new("R2000")`. archtop_floating_bridge.py line 220 still has `ezdxf.new("R2000")`. These are marked migrated in the compliance table but are NOT compliant. |
| **Sprint 4** (Photo Vectorizer) | PARTIALLY SUSPENDED | **ACCURATE** | photo_vectorizer_v2.py exists at services/photo-vectorizer/. light_line_body_extractor.py exists. Status accurately reflects blueprint path LIVE, photo/AI paths suspended. |
| **Sprint 5** (Scale Validation Gate) | COMPLETE | **ACCURATE** | Commits db713cc7, 3b18e852 verified. instrument_specs.py exists. curvature_correction.py exists at correct location. DEV_GUARDRAILS.md exists. |
| **Sprint 6** (Arc Reconstructor Sandbox) | IN PROGRESS | **ACCURATE** | sandbox/arc_reconstructor/ exists with 70+ files. SESSION_AUDITS.md exists and is maintained. reference_outline_bridge.py, arc_reconstructor.py, body_contour_solver.py all present. |
| **Sprint 7** (Repository Data Audit) | COMPLETE | **ACCURATE** | docs/REPO_DATA_AUDIT.json exists (1329 lines as claimed). |
| **Sprint 7.5** (Supersession Audit) | COMPLETE | **ACCURATE** | docs/audits/SUPERSESSION_AND_ORPHAN_AUDIT_RESULTS_v3.md exists. |
| **Sprint 8** (Instrument Library JSON) | IN PROGRESS | **LOCATION MISMATCH** | JSON files exist but NOT at docs/instrument_library/ (directory does not exist). Files are at services/api/app/instrument_geometry/models/: cuatro_venezolano_spec.json, cuatro_puertorriqueno_spec.json, gibson_l0_spec.json, acoustic_00_spec.json, om_acoustic_spec.json, selmer_maccaferri_d_hole_spec.json, jumbo_fesselier_spec.json. cuatro_instrument_library.json does NOT exist (was supposed to be split into two files - this task is complete). |
| **Sprint 9** (InstrumentBodyGenerator) | PLANNED | **SCAFFOLDED** | instrument_body_generator.py exists at BOTH sandbox/arc_reconstructor/ AND services/api/app/instrument_geometry/body/ibg/. More progress than "PLANNED" implies. |

---

## Tech Debt Status

| Item | Claimed Location | Verified | Status |
|------|------------------|----------|--------|
| **Bi-arc joining math** | docs/reference/curvature_correction_unmerged.py | **EXISTS** | File exists at stated location. 467 lines of unmerged code confirmed. **STILL OPEN** |
| **DXF migration regression (spiral_geometry.py)** | instrument_geometry/soundhole/spiral_geometry.py | **CONFIRMED** | Line 270: `doc = ezdxf.new(dxfversion="R2000")`. Marked migrated 2026-04-16 but regression is real. **STILL OPEN** |
| **DXF migration regression (archtop_floating_bridge.py)** | instrument_geometry/bridge/archtop_floating_bridge.py | **CONFIRMED** | Line 220: `doc = ezdxf.new("R2000", setup=True)`. Marked migrated 2026-04-16 but regression is real. **STILL OPEN** |

---

## Queued Sprints Evaluation

| Sprint | Current Relevance | Recommendation |
|--------|-------------------|----------------|
| **tap_tone_pi Real-Time** | STILL RELEVANT | No changes detected in repo. Genuinely queued. |
| **tap_tone_pi Mass-Frequency** | STILL RELEVANT | No changes detected. Genuinely queued. |
| **tap_tone_pi Reference Overlay** | STILL RELEVANT | daquisto_graduation_measurements.json exists at two locations. Partial prerequisite met. |
| **LUTHERIE_MATH.md Completion** | STILL RELEVANT | docs/LUTHERIE_MATH.md exists. 10 sections still missing per sprint description. |
| **Archtop Free Tier Phase 1** | **PARTIALLY SUPERSEDED** | archtop_stiffness_map.py, archtop_surface_tools.py, archtop_modal_analysis.py ALL exist at services/api/app/cam/archtop/. Re-upload task is DONE. Only API endpoint wiring remains. Recommend status update. |
| **GEN-5 Data Consolidation** | STILL RELEVANT | Five conflicting registries still exist. No instrument_library.json created. |
| **GEN-1 Project Seeding** | STILL RELEVANT | No evidence of implementation. |
| **ML Design Layer Consumer** | STILL RELEVANT | Blocked by IBG extraction per sprint description. IBG now scaffolded. |

---

## Sprint 2 Open Items Detail

| Item | Claimed Status | Actual Status |
|------|---------------|---------------|
| flying_v_1958.json schema mismatch | Open | **NEEDS VERIFICATION** - file exists at models/flying_v_1958.json |
| flying_v phantom entry | Open | **RESOLVED** - specs/gibson_flying_v_1958.json now exists |
| VECTORIZER_ACCURACY.md | Open | **RESOLVED** - docs/VECTORIZER_ACCURACY.md exists |
| Archtop scripts re-upload | Implied open | **RESOLVED** - all three files exist in cam/archtop/ |

---

## Sprint 3 DXF Compliance Table Accuracy

The table at lines 188-203 claims ALL 12 files migrated. Verification results:

| File | Table Status | Actual Status |
|------|--------------|---------------|
| spiral_geometry.py | Migrated | **FALSE** - ezdxf.new("R2000") at line 270 |
| archtop_floating_bridge.py | Migrated | **FALSE** - ezdxf.new("R2000") at line 220 |
| headstock/dxf_export.py | Migrated | **TRUE** - imports dxf_writer, docstring confirms |
| blueprint_cam/dxf_preprocessor.py | Migrated | **TRUE** - imports dxf_writer |
| blueprint_cam/contour_reconstruction.py | Migrated | **TRUE** - imports dxf_writer |
| curve_export_router.py | Migrated | **TRUE** - imports dxf_writer |
| smart_guitar_dxf.py | Migrated | **TRUE** - no ezdxf.new found |
| neck/headstock_transition_export.py | Migrated | **TRUE** - imports dxf_writer |
| neck/neck_profile_export.py | Migrated | **TRUE** - imports dxf_writer |
| archtop/archtop_contour_generator.py | Migrated | **TRUE** - imports dxf_writer |
| cam/archtop_bridge_generator.py | Migrated | **TRUE** - imports dxf_writer |
| cam/archtop_saddle_generator.py | Migrated | **TRUE** - imports dxf_writer |

**Summary:** 10/12 correctly migrated. 2/12 have tech debt regression (marked migrated but still use ezdxf directly).

---

## Architectural Decisions Log

| Decision | Still Valid | Notes |
|----------|-------------|-------|
| R12 DXF standard | **YES** | dxf_writer.py enforces this |
| dxf_writer.py blocks new generators | **YES** | Per CLAUDE.md |
| BlueprintAnalyzer in-memory PNG | **YES** | No conflicting implementation |
| Standalone repos as moat | **YES** | Strategy unchanged |
| Instrument catalog tiered schema | **YES** | No conflicting implementation |
| Blueprint vectorizer ceiling REVERSED | **YES** | Commit 3db07c62 restored capability per ADR |
| System 1/System 2 separation | **YES** | arc_reconstructor remains in sandbox |
| cuatro_venezolano 420mm scale is wrong | **YES** | cuatro_venezolano_spec.json uses 556.5mm scale_length_mm |

---

## Recommendations

### Immediate Actions

1. **Re-migrate spiral_geometry.py** - Replace ezdxf.new("R2000") with dxf_writer.py call
2. **Re-migrate archtop_floating_bridge.py** - Replace ezdxf.new("R2000") with dxf_writer.py call
3. **Update Sprint 2** - Mark flying_v phantom entry and archtop scripts as resolved
4. **Update Sprint 8** - Correct location from "docs/instrument_library/" to "services/api/app/instrument_geometry/models/"
5. **Update Sprint 9** - Change status from PLANNED to IN PROGRESS (scaffolded)
6. **Update Archtop Free Tier** - Note that scripts already exist, only endpoint wiring needed

### Tech Debt Priority

1. **HIGH**: spiral_geometry.py and archtop_floating_bridge.py DXF regressions - these are production files claiming compliance but violating the R12 standard
2. **MEDIUM**: curvature_correction_unmerged.py - 467 lines of useful math not integrated
3. **LOW**: Sprint 2 cleanup - cosmetic but improves document accuracy

---

## Verification Commands Used

```bash
# Commit verification
git log --oneline | grep -E "04735bd|72bfffc|..." 

# DXF compliance check
grep -r "ezdxf\.new" services/api/app/instrument_geometry/

# File existence
glob pattern matching for all claimed deliverables
```

---

**Audit complete.** Document accurate overall but contains 2 critical tech debt items requiring immediate attention and several stale status claims.
