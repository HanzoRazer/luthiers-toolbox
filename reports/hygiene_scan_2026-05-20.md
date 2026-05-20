# Technical Debt Audit Report

**Generated:** 2026-05-20 16:17 UTC  
**Updated:** 2026-05-20 (post-remediation)  
**Tool version:** code-analysis-tool 0.1.0  
**Project:** luthiers-toolbox  
**Commit (scan):** `18dd0932`  
**Commit (remediation):** `a9bb2fe2` (PR #24 merged)

---

## Executive Summary

| Metric | Pre-Remediation | Post-Remediation |
|--------|-----------------|------------------|
| **Confidence Score** | 0/100 (RED) | Improved |
| **CRITICAL findings** | 19 | 8 (archived/test only) |
| **Live code CRITICAL** | 11 | 0 |
| **Total findings** | 5,582 | 5,571 |

**Status:** All CRITICAL issues in production code resolved. Remaining CRITICAL findings are in archived experimental code and test files (false positives for test functions named `test_generate_gcode*`).

---

## Severity Breakdown

| Severity | Count | Notes |
|----------|------:|-------|
| CRITICAL | ~~19~~ → 8 | 11 fixed in PR #24, 8 in archive/tests |
| HIGH | 378 | Exception swallowing, high complexity |
| MEDIUM | 3,021 | Moderate complexity |
| LOW | 2,164 | Minor complexity |

## Category Breakdown

| Category | Count | Primary Issue |
|----------|------:|---------------|
| complexity | 4,933 | Functions exceeding cyclomatic thresholds |
| exceptions | 625 | Bare except, silent swallowing |
| safety | 24 | Missing `@safety_critical` decorators |

---

## Remediation Completed (PR #24)

### CRITICAL: Missing @safety_critical Decorators

**Fixed** — 11 functions across 8 CAM files now have `@safety_critical`:

| File | Functions Fixed |
|------|-----------------|
| `cam/binding/channel_toolpath.py` | `generate_gcode`, `_generate_gcode` |
| `cam/binding/purfling_ledge.py` | `generate_gcode`, `_generate_gcode` |
| `cam/drilling/peck_cycle.py` | `generate_gcode` |
| `cam/profiling/profile_toolpath.py` | `generate_gcode`, `_generate_gcode` |
| `cam/vcarve/toolpath.py` | `generate_gcode`, `_generate_gcode` |
| `cam/nut_slot_cam.py` | `validate_toolpath_integrity` |
| `cam/routers/utility/optimization_router.py` | `calculate_feeds_speeds` |
| `routers/radius_dish_router.py` | `generate_gcode` |

**Verification:** Fence checker passes (2/2).

### Remaining CRITICAL (Not Actionable)

| Location | Reason Not Fixed |
|----------|------------------|
| `archive/experimental/2026-03/...fretboard_export.py` | Archived experimental code |
| `docs/archive/photo_vectorizer_patches/fretboard_export.py` | Archived patches |
| `docs/archive/photo_vectorizer_patches/radius_dish_router.py` | Archived patches |
| `tests/test_neck_gcode_smoke.py` (4 functions) | False positive — test functions |

---

## File Hotspots

Top 10 files by finding count:

| File | Findings | Category |
|------|--------:|----------|
| `services/photo-vectorizer/photo_vectorizer_v2.py` | 126 | complexity |
| `docs/archive/.../photo_vectorizer_v2.py` | 112 | complexity (archived) |
| `services/api/tests/test_saw_lab_endpoint_smoke.py` | 55 | complexity |
| `services/api/tests/test_retract_endpoint_smoke.py` | 48 | complexity |
| `docs/archive/.../test_photo_vectorizer_v2.py` | 44 | complexity (archived) |
| `services/photo-vectorizer/test_photo_vectorizer_v2.py` | 44 | complexity |
| `docs/archive/.../test_contour_stage.py` | 42 | complexity (archived) |
| `services/photo-vectorizer/test_contour_stage.py` | 42 | complexity |
| `services/photo-vectorizer/cognitive_extractor.py` | 41 | complexity |
| `services/photo-vectorizer/cognitive_extraction_engine.py` | 39 | complexity |

**Observation:** 4 of top 10 hotspots are in `docs/archive/` — historical code not in production.

---

## HIGH Priority Findings

### Exception Swallowing (EXC-SWALLOW-001)

**Pattern:** `except: pass` or `except Exception: pass` without logging.

**Locations (sample):**
- `Guitar Plans/Gibson J 45_ Project/*.py` — 6 files
- `Guitar Plans/Les Paul_Project/*.py` — 4 files

**Recommendation:** These are user project files, not core platform code. Consider excluding `Guitar Plans/` from future scans or treating as external assets.

### High Complexity (CX-HIGH-001)

**Top offenders in core code** (from complexity baseline):

| Function | Complexity | Location |
|----------|------------|----------|
| `parse_dxf` | 50 | `app/art_studio/services/generators/inlay_import.py:33` |
| `run_manufacturing_checks` | 50 | `app/art_studio/services/rosette/rosette_manufacturing.py:183` |
| `tessellate_path_d` | 42 | `app/art_studio/services/generators/inlay_geometry_svg.py:131` |
| `record_operator_feedback_event` | 41 | `app/services/saw_lab_operator_feedback_learning_hook.py:49` |

**Status:** Tracked in complexity baseline (`complexity_baseline.json`). CI enforces no NEW violations above threshold.

---

## Signals Summary

### Red Signals (7)
- Complexity ceiling exceeded in multiple modules
- Exception handling gaps in auxiliary scripts
- Safety decorator coverage incomplete (now fixed in core)

### Yellow Signals (4)
- Moderate complexity accumulation
- Test file complexity (acceptable for test fixtures)

---

## Recommended Next Steps

1. **Exclude non-core paths from scanning:**
   - `Guitar Plans/` — user project files
   - `docs/archive/` — historical snapshots
   - `archive/experimental/` — deprecated experiments

2. **Prioritize complexity reduction:**
   - Target `parse_dxf` (complexity 50) — extract helper functions
   - Target `run_manufacturing_checks` (complexity 50) — decompose into stages

3. **Address exception swallowing:**
   - Add logging to `except` blocks in `photo-vectorizer/` modules
   - Convert bare `except:` to `except Exception as e:` with logging

4. **Update scan exclusions:**
   ```yaml
   exclude:
     - "Guitar Plans/**"
     - "docs/archive/**"
     - "archive/**"
   ```

---

*Report generated by code-audit 0.1.0 (engine engine_v1, signals signals_v5)*  
*Remediation by Claude Code — PR #24 merged 2026-05-20*
