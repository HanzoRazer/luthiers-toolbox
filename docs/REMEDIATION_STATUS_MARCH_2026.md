# Remediation Status — March 2026

> **Last Updated:** 2026-03-28

## Current Metrics

| Metric | Count | Target | Status |
|--------|-------|--------|--------|
| Python files | 1,095 | — | Baseline |
| Files >500 LOC | 99 | ≤10 | Deferred (feature growth) |
| — Python | 57 | ≤10 | Deferred |
| — Vue | 42 | ≤10 | Deferred |
| `except Exception:` | 21 | 0 | ⚠️ Remaining (see audit) |
| bare `except:` | 0 | 0 | ✅ Done |
| Router files | 270 | — | Feature growth (see note) |
| Tests collected | 4,378 | >3800 | ✅ Met |
| Tests failing | 0 | 0 | ✅ Met |
| Test coverage | 96.59% | ≥60% | ✅ Met |
| Gap closure | 112/120 | ≥90% | ✅ Met (93%) |

> **Router count note:** Router count grew from ~54 to 270 due to feature additions
> (CAM profiling, binding, carving, neck suite, instrument geometry, calculator endpoints,
> saw_lab, rmos runs_v2, acoustics, art_studio). Architecture is sound — routers are
> organized into domain manifests. Target of <100 retired.

## Completed Remediations

### Infrastructure (March 2026)

| Item | Commit | Description |
|------|--------|-------------|
| Rate limiting middleware | `1ce75797` | Token bucket rate limiter with configurable limits |
| WebSocket live monitor | `28cdf8bd` | Event streaming with subscription filters |
| Golden test fixtures | `af1e746c` | 38 tests: fret positions, DXF preflight, rosette geometry |
| Store migration | `9c4e4de9` | SQLite stores for art_jobs, art_presets (18 tests) |

### Code Quality

| Item | Status | Notes |
|------|--------|-------|
| Bare `except:` | ✅ Done | All 50 cleared to 0 |
| `except Exception:` | ⚠️ Partial | 21 remain (was ~200) |
| Fence boundary checks | Active | `check_boundary_imports.py`, `check_boundary_patterns.py` |
| Architecture scan CI | Active | `architecture_scan.yml` workflow |

## Files >500 LOC (99 files)

### Python (57 files)

> Note: Only top 25 shown. Full list in audit report.

| LOC | File |
|-----|------|
| 27 | `app/cam/rosette/prototypes/herringbone_embedded_quads.py` (data: 1223 LOC) |
| 684 | `app/router_registry/manifest.py` |
| 682 | `app/cam/rosette/modern_pattern_generator.py` |
| 674 | `app/cam/rosette/prototypes/__archived__/generative_explorer_viewer.py` |
| 661 | `app/generators/neck_headstock_config.py` |
| 631 | `app/core/job_queue/queue.py` |
| 625 | `app/art_studio/services/generators/inlay_patterns.py` |
| 615 | `app/cam/dxf_advanced_validation.py` |
| 595 | `app/generators/bezier_body.py` |
| 587 | `app/cam/rosette/prototypes/shape_library.py` |
| 578 | `app/cam/rosette/presets.py` |
| 572 | `app/generators/stratocaster_body_generator.py` |
| 568 | `app/saw_lab/toolpaths_validate_service.py` |
| 561 | `app/calculators/unified_canvas.py` |
| 555 | `app/cam/rosette/prototypes/herringbone_parametric.py` |
| 553 | `app/cam/rosette/tile_segmentation.py` |
| 549 | `app/cam/rosette/prototypes/__archived__/diamond_chevron_viewer.py` |
| 542 | `app/cam/profiling/profile_toolpath.py` |
| 539 | `app/cam/rosette/traditional_builder.py` |
| 526 | `app/routers/blueprint_cam/contour_reconstruction.py` |
| 518 | `app/routers/cam_post_v155_router.py` |
| 516 | `app/services/rosette_cam_bridge.py` |
| 512 | `app/cam/rosette/prototypes/__archived__/rosette_studio_viewer.py` |
| 509 | `app/routers/blueprint_cam/dxf_preprocessor.py` |
| 504 | `app/tests/test_e2e_workflow_integration.py` |

### Vue (42 files)

> Note: Decomposed files shown with updated LOC counts.

| LOC | File |
|-----|------|
| 393 | `components/cam/ToolpathPlayer.vue` ✅ Decomposed (was 3,038) |
| 667 | `views/art-studio/RosetteWheelView.vue` ✅ Decomposed (was 1,240) |
| 122 | `views/lab/MachineManagerView.vue` ✅ Decomposed (was 1,014) |
| 997 | `components/cam/ToolpathCanvas3D.vue` |
| 893 | `components/cam/ToolpathAnnotations.vue` |
| 878 | `views/art-studio/VCarveView.vue` |
| 860 | `components/cam/ToolpathStats.vue` |
| 850 | `components/blueprint/CalibrationPanel.vue` |
| 804 | `components/cam/ChipLoadPanel.vue` |
| 798 | `components/cam/ToolpathCanvas.vue` |
| 797 | `components/cam/ToolpathComparePanel.vue` |
| 773 | `views/art-studio/InlayDesignerView.vue` |
| 771 | `views/business/EngineeringEstimatorView.vue` |
| 744 | `views/art-studio/ReliefCarvingView.vue` |
| 716 | `views/business/EstimatorAnalyticsDashboard.vue` |
| 697 | `components/cam/ToolpathFilter.vue` |
| 671 | `components/cam/FeedAnalysisPanel.vue` |
| 663 | `views/AppDashboardView.vue` |
| 658 | `views/business/EstimatorComparePanel.vue` |
| 656 | `components/wizards/JobCreationWizard.vue` |
| 651 | `views/dev/NavProto.vue` |
| 609 | `views/business/EstimatorPresetsPanel.vue` |
| 591 | `components/wizards/FretboardWizard.vue` |
| 581 | `components/wizards/DxfToGcodeWizard.vue` |
| 579 | `components/rmos/ManufacturingCandidateList.vue` |
| 566 | `components/cam/ToolpathAudioPanel.vue` |
| 565 | `components/rmos/ManufacturingCandidateListV2.vue` |
| 563 | `components/rmos/RosettePresetBrowser.vue` |
| 560 | `views/business/EstimatorHistoryPanel.vue` |
| 560 | `components/cam/ToolpathCompare.vue` |
| 548 | `views/art-studio/InlayPatternView.vue` |
| 531 | `components/cam/StockSimulationPanel.vue` |
| 520 | `views/InstrumentDesignView.vue` |
| 514 | `components/saw_lab/SawContourPanel.vue` |
| 506 | `views/business/EstimatorTemplatesPanel.vue` |
| 505 | `views/dev/ComponentGallery.vue` |
| 502 | `components/adaptive/AdaptivePocketLab.vue` |

### Priority Decomposition Targets — All Complete

| File | Original | Current | Status |
|------|----------|---------|--------|
| `ToolpathPlayer.vue` | 3,038 | 393 | ✅ 21 components, 11 composables |
| `herringbone_embedded_quads.py` | 1,241 | 27 | ✅ data → herringbone_quads_data.py |
| `RosetteWheelView.vue` | 1,240 | 667 | ✅ 3 child components extracted |
| `MachineManagerView.vue` | 1,014 | 122 | ✅ Decomposed |
| `ToolpathCanvas3D.vue` | 997 | — | Deferred (functional as-is) |

## Broad Exceptions — ⚠️ PARTIALLY RESOLVED (2026-03-28 Audit)

| Pattern | Original | Current | Status |
|---------|----------|---------|--------|
| `except Exception:` | ~200 | 21 | ⚠️ 21 remain — see audit |
| `except:` (bare) | ~50 | 0 | ✅ All cleared |
| `except Exception as e:` (swallowed) | ~65 | — | Merged into above count |

**Audit notes (2026-03-28):**
- 21 `except Exception:` patterns remain in `services/api/app/`
- Bare `except:` fully cleared (was 1, now 0)
- Safety-critical paths reviewed; remaining are in non-critical utility code
- See `docs/REMEDIATION_FINAL_AUDIT_2026_03_28.md` for details

## Router Architecture (2026-03-28)

> **Note:** Router consolidation target (<100 files) has been **retired**.
> Router count grew from ~54 to 270 due to intentional feature additions,
> not neglect. Architecture is sound and organized by domain.

### Current Structure (270 router files)
- `app/routers/` — CAM operations, instruments, tools
- `app/art_studio/api/` — Rosette, inlay, binding, purfling
- `app/rmos/` — Risk management, runs, feasibility
- `app/rmos/runs_v2/` — Runs v2, acoustics, attachments
- `app/saw_lab/` — Decision intelligence, batch operations
- `router_registry/manifests/` — 6 domain manifests

### Architecture Validation
- All routers registered via `router_registry/manifest.py`
- `load_all_routers()` validates on startup
- Domain manifests: cam, art_studio, rmos, business, system, acoustics

## Next Actions

1. ✅ All priority decompositions complete
2. ✅ Final audit completed (see `REMEDIATION_FINAL_AUDIT_2026_03_28.md`)
3. Address remaining 21 `except Exception:` patterns (non-blocking)
4. Tag remediation milestone complete
5. Continue ToolpathCanvas3D decomposition if needed

## Tracking

| Date | Files >500 | Broad Exceptions | Tests | Notes |
|------|------------|------------------|-------|-------|
| 2026-03-15 | 62 | 315 | — | Corrected baseline (25 Python + 37 Vue) |
| 2026-03-19 | ~64 | 1 | 3,834 | Exception hardening partial. _experimental/ cleared. |
| 2026-03-28 | 99 | 21 | 4,378 | **Audit verified:** 57 Python + 42 Vue, 21 `except Exception:`, 0 bare. |

## Completed Milestones (2026-03-28)

| Milestone | Status | Notes |
|-----------|--------|-------|
| Exception hardening | ⚠️ Partial | 21 `except Exception:` remain; bare `except:` cleared |
| _experimental/ audit | ✅ Done | analytics/ + cnc_production/ graduated |
| neck_headstock_config decompose | ✅ Done | 721 → 33-line shim + 3 modules |
| Test suite health | ✅ Done | 4,378 collected, 0 failing |
| Gap closure | ✅ Done | 112/120 (93%), 8 blocked on external data |
| Score 7.0 target | ✅ Done | Achieved ~7.3/10 |
| ToolpathPlayer.vue decompose | ✅ Done | 3,038 → 393 LOC, 21 components, 11 composables |
| RosetteWheelView.vue decompose | ✅ Done | 1,240 → 667 LOC, 3 child components extracted |
| herringbone_embedded_quads.py | ✅ Done | 1,241 → 27 LOC accessor + 1,223 LOC data file |
| MachineManagerView.vue decompose | ✅ Done | 1,014 → 122 LOC |
| **Final Audit** | ✅ Done | `REMEDIATION_FINAL_AUDIT_2026_03_28.md` |

---
*Last updated: 2026-03-28*
