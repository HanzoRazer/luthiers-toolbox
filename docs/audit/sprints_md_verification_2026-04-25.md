# SPRINTS.md Verification Audit — 2026-04-25

## Methodology

For every completion claim in SPRINTS.md (✅, complete, migrated, done, shipped, EXISTS, RESOLVED):
1. Identify what files or features the claim references
2. Verify code state matches the claim
3. Check git log for actual work in the claimed time window
4. Surface discrepancies

---

## CRITICAL FINDING: Sprint 3 DXF Migration Claims

**SPRINTS.md claims "12/12 DXF generators migrated" — Reality: 2/12 migrated**

| # | File | SPRINTS.md Claim | DxfWriter Import | ezdxf.new Calls | Verified |
|---|------|------------------|------------------|-----------------|----------|
| 1 | `soundhole/spiral_geometry.py` | ✅ Re-migrated 2026-04-23 | YES | 0 | **TRUE** |
| 2 | `bridge/archtop_floating_bridge.py` | ✅ Re-migrated 2026-04-23 | YES | 0 | **TRUE** |
| 3 | `headstock/dxf_export.py` | ✅ Migrated 2026-04-23 | NO | 1 | **FALSE** |
| 4 | `blueprint_cam/dxf_preprocessor.py` | ✅ Migrated 2026-04-23 | NO | 1 | **FALSE** |
| 5 | `blueprint_cam/contour_reconstruction.py` | ✅ Migrated 2026-04-23 | NO | 2 | **FALSE** |
| 6 | `export/curve_export_router.py` | ✅ Migrated 2026-04-23 | NO | 1 | **FALSE** |
| 7 | `body/smart_guitar_dxf.py` | ✅ Migrated 2026-04-23 | NO | 1 | **FALSE** |
| 8 | `neck/headstock_transition_export.py` | ✅ Migrated 2026-04-23 | NO | 1 | **FALSE** |
| 9 | `neck/neck_profile_export.py` | ✅ Migrated 2026-04-23 | NO | 1 | **FALSE** |
| 10 | `archtop/archtop_contour_generator.py` | ✅ Migrated 2026-04-23 | NO | 2 | **FALSE** |
| 11 | `cam/archtop_bridge_generator.py` | ✅ Migrated 2026-04-23 | NO | 1 | **FALSE** |
| 12 | `cam/archtop_saddle_generator.py` | ✅ Migrated 2026-04-23 | NO | 1 | **FALSE** |

**Git verification for files 3-12:** No commits touched these files on 2026-04-23. The migration claims were entered without work being performed.

**Impact:** Sprint 3 "CLOSED" status is based on false claims. The claim "12/12 DXF generators migrated" in the NEXT SESSION OPENS WITH section is false.

---

## CRITICAL FINDING: BOE Backend Endpoint Does Not Exist

| Claim | Location | Verification | Actual State | Discrepancy |
|-------|----------|--------------|--------------|-------------|
| "BOE routes through backend endpoint POST /api/editor/export-dxf" | Line 14, Line 161 | Grep for endpoint in routers/ | No such endpoint exists | **FALSE** |
| "POST /api/editor/export-dxf: BOE backend endpoint" | Line 768 (COMPLETED section) | Grep for endpoint | No such endpoint exists | **FALSE** |

**Verification:** `grep -r "/editor/\|editor.*export" services/api/app/routers/` returns no matches.

---

## Sprint 1 — Vectorizer Reconciliation: VERIFIED

| Claim | Commit | Git Verification | Status |
|-------|--------|------------------|--------|
| Phase 1 | 04735bd4 | Commit exists | **TRUE** |
| Phase 2 | 72bfffc9 | Commit exists | **TRUE** |
| Phase 3 | 059cf5b0 | Commit exists | **TRUE** |
| Phase 4 | a76102c2 | Commit exists | **TRUE** |
| Phase 4b | 5a145e90 | Commit exists | **TRUE** |
| Phase 4c | ebffbd53 | Commit exists | **TRUE** |
| Phase 5 | 722cc03d | Commit exists | **TRUE** |
| Phase 5G | cb0761ed | Commit exists | **TRUE** |
| Ceiling reversal | 3db07c62 | Commit exists | **TRUE** |

**Sprint 1 claims: All verified TRUE**

---

## Sprint 2 — Repo Split: PARTIAL

| Claim | Verification Method | Actual State | Discrepancy |
|-------|---------------------|--------------|-------------|
| `docs/VECTORIZER_ACCURACY.md` RESOLVED | File exists check | File exists (3721 bytes, 2026-04-05) | **TRUE** |
| `specs/gibson_flying_v_1958.json` RESOLVED | File exists check | File exists at `instrument_geometry/specs/` | **TRUE** |

**Note:** Cannot verify external repos (HanzoRazer/ltb-*) from this audit.

---

## Sprint 3 — Remediation: MOSTLY FALSE

| Claim | Verification Method | Actual State | Discrepancy |
|-------|---------------------|--------------|-------------|
| dxf_writer.py built (4c4f1a52) | Commit + file exists | Commit exists, file exists (5916 bytes) | **TRUE** |
| PatternRenderer fix (a7f0f614) | Commit exists | Commit exists | **TRUE** |
| FastAPI regex fix (131b1cfd) | Commit exists | Commit exists | **TRUE** |
| WeasyPrint Docker (ff958c9a) | Commit exists | Commit exists | **TRUE** |
| json_to_dxf_r12.py verified working | File at root | File NOT at root; exists only in archive folder | **PARTIAL** |
| 12/12 DXF generators migrated | Import check + ezdxf.new count | 2/12 migrated | **FALSE** |
| BOE backend endpoint | Endpoint grep | No such endpoint | **FALSE** |
| SPRINTS.md Phase 1-4 audit cleanup | File exists | docs/audit/sprints_audit_2026-04-23.md exists | **TRUE** |
| docs/SPRINTS_MAINTENANCE.md created | File exists | File exists (3105 bytes) | **TRUE** |

---

## Sprint 4 — Photo Vectorizer: VERIFIED

| Claim | Commit | Git Verification | Status |
|-------|--------|------------------|--------|
| spec_name wire-up | 5de45310 | Commit exists | **TRUE** |
| Auto-rotate for AI | d45e213a | Commit exists | **TRUE** |
| Dimension swap fix | d45e213a | Commit exists | **TRUE** |

---

## Sprint 5 — Scale Validation: VERIFIED

| Claim | Verification Method | Actual State | Discrepancy |
|-------|---------------------|--------------|-------------|
| Commits db713cc7, 3b18e852 | Git verification | Both commits exist | **TRUE** |
| instrument_specs.py single source | File exists | 363 lines, exists | **TRUE** |
| curvature_correction.py consolidated | File exists | 8905 bytes, exists | **TRUE** |
| DEV_GUARDRAILS.md | File exists | 3974 bytes, exists | **TRUE** |

---

## Sprint 6 — Arc Reconstructor Sandbox: VERIFIED

| Claim | Verification Method | Actual State | Discrepancy |
|-------|---------------------|--------------|-------------|
| sandbox/arc_reconstructor/ files exist | Directory listing | 8 .py files present | **TRUE** |
| arc_reconstructor.py | File check | 50921 bytes | **TRUE** |
| reference_outline_bridge.py | File check | 16152 bytes | **TRUE** |

---

## Sprint 7 — Repository Data Audit: VERIFIED

| Claim | Verification Method | Actual State | Discrepancy |
|-------|---------------------|--------------|-------------|
| docs/REPO_DATA_AUDIT.json | File exists | 57494 bytes, exists | **TRUE** |

---

## Sprint 7.5 — Supersession Audit: VERIFIED

| Claim | Verification Method | Actual State | Discrepancy |
|-------|---------------------|--------------|-------------|
| docs/audits/SUPERSESSION_AND_ORPHAN_AUDIT_RESULTS_v3.md | File exists | 12390 bytes, exists | **TRUE** |

---

## Sprint 8 — Instrument Library JSON: NOT VERIFIED

Claims reference JSON files in `app/instrument_geometry/models/` — would require individual file verification. Not in scope for this audit.

---

## Sprint 9 — IBG Scaffolded: VERIFIED

| Claim | Verification Method | Actual State | Discrepancy |
|-------|---------------------|--------------|-------------|
| sandbox/arc_reconstructor/instrument_body_generator.py | File exists | 14914 bytes | **TRUE** |
| services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py | File exists | 14820 bytes | **TRUE** |
| services/api/app/instrument_geometry/body/ibg/body_contour_solver.py | File exists | 31514 bytes | **TRUE** |
| services/api/app/instrument_geometry/body/ibg/arc_reconstructor.py | File exists | 49491 bytes | **TRUE** |

---

## Archtop Free Tier — VERIFIED (file existence only)

| Claim | Verification Method | Actual State | Discrepancy |
|-------|---------------------|--------------|-------------|
| archtop_stiffness_map.py EXISTS | File check | 14217 bytes at cam/archtop/ | **TRUE** |
| archtop_surface_tools.py EXISTS | File check | 12066 bytes at cam/archtop/ | **TRUE** |
| archtop_modal_analysis.py EXISTS | File check | 19356 bytes at cam/archtop/ | **TRUE** |

---

## TECH DEBT — PARTIAL

| Claim | Verification Method | Actual State | Discrepancy |
|-------|---------------------|--------------|-------------|
| spiral_geometry.py FIXED (re-migrated) | DxfWriter import check | Imports DxfWriter, 0 ezdxf.new | **TRUE** |
| archtop_floating_bridge.py FIXED (re-migrated) | DxfWriter import check | Imports DxfWriter, 0 ezdxf.new | **TRUE** |

---

## Summary of Discrepancies

### Category 1: False Completion Claims (work never performed)

| Claim | Impact |
|-------|--------|
| 10 of 12 DXF migrations (lines 205-214) | Sprint 3 "CLOSED" status invalid |
| BOE backend endpoint (lines 14, 161, 768) | Feature does not exist |

### Category 2: Partial/Mislocated

| Claim | Impact |
|-------|--------|
| json_to_dxf_r12.py at root | File exists in archive folder only |

### Category 3: All Verified TRUE

- Sprint 1 (all phases)
- Sprint 4 (commits verified)
- Sprint 5 (files and commits verified)
- Sprint 6 (files verified)
- Sprint 7 (file verified)
- Sprint 7.5 (file verified)
- Sprint 9 (files verified)
- Archtop Free Tier (files exist)
- TECH DEBT re-migrations (2 files verified)

---

## Root Cause Analysis

### Pattern 1: Status entries without verification
The DXF migration table (lines 199-214) contains 10 false claims. No commits touched these files on the claimed date. Status was entered as "done" without performing or verifying the work.

### Pattern 2: Feature documentation without implementation
The BOE backend endpoint is documented in multiple places as complete, but the endpoint does not exist in the codebase. This suggests documentation was written for planned work, then marked complete without implementation.

### Pattern 3: Commits verified, claims accurate
Where claims reference specific commit hashes, verification consistently passes. The failure mode is claims without commit references.

---

## Recommendations

1. **Require commit hash for completion claims.** A "migrated" or "complete" status without a verifiable commit is aspirational, not reportorial.

2. **Sprint 3 must be reopened.** The "CLOSED" status is based on 10/12 false claims.

3. **BOE DXF endpoint must be de-documented or implemented.** Current state is documentation debt — the feature is described but doesn't exist.

4. **Recurring verification audit.** Before any sprint closeout, mechanically verify completion claims against code state.

---

*Audit completed: 2026-04-25*
*Verification method: Git commit existence, file presence, import grep, ezdxf.new call count*
