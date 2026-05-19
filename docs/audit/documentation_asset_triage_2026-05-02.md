# Documentation Asset Triage Report

**Date**: 2026-05-02  
**Purpose**: Comprehensive survey of documentation assets with proposed dispositions  
**Status**: AWAITING APPROVAL before execution

---

## Executive Summary

| Category | Count | Action Required |
|----------|-------|-----------------|
| Repo root markdown | 20 | 12 move, 8 stay |
| Repo root .txt | 17 | Extract content, then archive (separate sub-sprint) |
| Repo root .zip | 3 | Externalize 2, extract 1 |
| docs/ top-level | 118 | ~40 archive, ~78 keep |
| docs/handoffs/ | 27 | ~10 archive (pre-March), ~17 keep (recent) |
| docs/audit/ | 15 | All keep (all April 2026) |
| docs/investigations/ | 7 | All keep (all April 2026) |
| Nested repo copy | 1 dir | Delete (verified incomplete duplicate) |
| __pycache__ dirs | 20+ | Delete all |
| Python in docs/archive/ | 2 | Move to archive/code/2026/ |
| sprint_P4B bundle | 1 dir | Archive to docs/archive/2026/sprints/ |

**Estimated effort**: 5-7 days total across all phases

---

## Phase 0: Immediate Cleanup (No Approval Needed)

### Delete __pycache__ directories
All instances should be deleted - already in .gitignore but committed:
```
docs/archive/photo_vectorizer_experiment_20260321/__pycache__
docs/archive/photo_vectorizer_patches/__pycache__
docs/archive/recovered/__RECOVERED__/F_validation_tooling/__pycache__
docs/archive/toolpath_visualizer_plan/__pycache__
sandbox/arc_reconstructor/__pycache__
scripts/__pycache__
scripts/architecture/__pycache__
scripts/ci/__pycache__
scripts/utils/__pycache__
(plus ~10 more in services/api/app/)
```

### Delete nested repo copy
**Path**: `luthiers-toolbox-main/`
**Verification**: diff confirmed it's an incomplete clone - main repo has content, nested copy is nearly empty
**Action**: Delete entire directory

---

## Phase 1: Repo Root Files

### Files to KEEP at root (8 files)
| File | Reason |
|------|--------|
| SPRINTS.md | Canonical sprint registry |
| CLAUDE.md | Project instructions |
| README.md | Repo entry point |
| CHANGELOG.md | Version history |
| LUTHERIE_MATH.md | Institutional knowledge (move to docs/ but link from root?) |
| MANIFESTO.md | Institutional knowledge |
| ORIGIN_STORY.md | Institutional knowledge |
| NEXT_SESSION_SPEC.md | Active session pointer |

### Files to MOVE to docs/handoffs/ (2 files)
| File | Date | Notes |
|------|------|-------|
| SPRINT_FRET_A_PHASE_1_5_PATH_1.md | Recent | Sprint handoff at root by accident |
| SPRINT_FRET_A_PHASE_2_HANDOFF.md | Recent | Sprint handoff at root by accident |

### Files to MOVE to docs/ (10 files)
| File | Target | Notes |
|------|--------|-------|
| Agentic AI as Quality Voter_A Self-Validating Vectorization System.md | docs/methodology/ | Methodology document |
| Agentic Approach for Accurate Photo Vectorization.md | docs/methodology/ | Methodology document |
| ENGINEERING MEMO.md | docs/ | Engineering document |
| Executive Summary_AI Systems in The Production Shop.md | docs/ | Executive summary |
| Comprehensive_Migration_Plan.md | docs/archive/2026/plans/ | Superseded plan |
| GUITAR_PLANS_REFERENCE.md | docs/ | Reference document |
| Luthiers_Toolbox_Platform_Architecture.md | docs/ | Architecture (consolidate with duplicate?) |
| The Production Shop_Platform Architecture.md | docs/archive/2026/plans/ | Duplicate of above - archive |
| SVG_ARTWORK_GUIDE.md | docs/ | User guide |
| soundhole_calculator_user_guide.md | docs/ | User guide |
| benchmark_comparison.md | docs/ | Benchmark reference |
| TEST_RESULTS.md | docs/ | Test documentation |

### .txt files - SEPARATE SUB-SPRINT (17 files, ~2MB)
**Proposed action**: Read each, extract durable methodology, archive originals to `docs/archive/2026/session-notes/`

| File | Size | Content Type |
|------|------|--------------|
| Animate Toolpath Visualizer Code.txt | 125KB | Code dump |
| Archtop Tool.txt | 45KB | Tool notes |
| Bridge Compenstation Calculator.txt | 217KB | Calculator methodology |
| bandit_report.txt | 370KB | Security scan output |
| Comprehensive_Migration_Plan.txt | 89KB | Plan (duplicate of .md?) |
| Comprehensive_Migration_Plan_2.txt | 11KB | Plan variant |
| CRITICAL (7 unique) — Production Bl.txt | 10KB | Issue notes |
| Girih-5 generator—the 5_Islamic geometric tessellations.txt | 7KB | Inlay methodology |
| Hybrid Solution_Executive Summary for the Guitar Body Outliner.txt | 12KB | BOE methodology |
| INLAY_PATTERN_GENERATORS.txt | 97KB | Inlay methodology |
| Integration Architecture_Body Outline Editor_Instrument Body Generator.txt | 37KB | Architecture notes |
| Interactive_Guitar_Body_Outline_Editor.txt | 39KB | BOE notes |
| MD_INVENTORY.txt | 95KB | Inventory dump |
| Phase 3.6 Vectorizer Robustness Enhancements.txt | 83KB | Vectorizer methodology |
| Photo Vectorizer v2.0 - Enhanced Robust Version.txt | 98KB | Vectorizer methodology |
| Steps _To A-High_Level _Image Generator.txt | 6KB | Process notes |
| Vinefloral scrollwork = flowing org.txt | 12KB | Inlay design notes |
| What the L-37 tells you specificall.txt | 3KB | Reference notes |

**Recommendation**: This is 1-2 days of work. Schedule as Phase 3 sub-sprint after markdown reorganization.

### .zip files - EXTERNALIZE (3 files, 33MB total)
| File | Size | Action |
|------|------|--------|
| benchmark_files.zip | 1.2MB | Externalize to shop storage, remove from git |
| benchmark_outputs.zip | 31MB | Externalize to shop storage, remove from git |
| cirad-wood-collection-master.zip | 800KB | Extract CSVs to docs/reference/cirad/, then externalize zip |

---

## Phase 2: docs/ Top-Level Files (118 files)

### Category: KEEP - Canonical/Active Reference (~30 files)
| File | Reason |
|------|--------|
| ARCHITECTURE.md | Current architecture |
| BLUEPRINT_VECTORIZER_ARCHITECTURE.md | Current architecture |
| PHOTO_VECTORIZER_ARCHITECTURE.md | Current architecture |
| Body_Outline_Editor_User_Manual.md | User documentation |
| Body_Outline_Editor_Quick_Start.md | User documentation |
| CNC_SAW_LAB_DEVELOPER_GUIDE.md | Developer guide |
| DEV_GUARDRAILS.md | Active guardrails |
| DEVELOPMENT.md | Development guide |
| LUTHERIE_MATH.md | Institutional knowledge |
| MANIFESTO.md | Institutional knowledge |
| ORIGIN_STORY.md | Institutional knowledge |
| PRODUCT_TIERS.md | Product definition |
| PRODUCT_DEFINITION.md | Product definition |
| PRODUCT_SCOPE.md | Product definition |
| PRODUCT_BOUNDARY.md | Product definition |
| RMOS_CONCEPTS_GUIDE.md | System concepts |
| SAFETY.md | Safety documentation |
| SECURITY.md | Security documentation |
| SPRINTS_MAINTENANCE.md | Sprint process |
| TESTING_STRATEGY.md | Test strategy |
| contributing.md | Contribution guide |
| index.md | Documentation index |
| troubleshooting.md | Troubleshooting guide |
| Smart_Guitar_Body_Outline_Workflow.md | Current workflow |
| dxf_svg_generation_architecture.md | Current architecture |

### Category: KEEP - Tonewood Reference (~6 files)
All tonewood comparison documents are reference material:
| File | Date |
|------|------|
| tonewood_comparison_acoustic_top_woods.md | Apr 9 |
| tonewood_comparison_african_hardwoods_mugavu.md | Apr 27 |
| tonewood_comparison_cherry_mahogany_walnut_mesquite.md | Apr 5 |
| tonewood_comparison_mahogany_koa_family.md | Apr 28 |
| tonewood_comparison_rosewoods_ebonies_mesquite.md | Mar 10 |
| tonewood_viability_emerging_species.md | Apr 27 |

### Category: ARCHIVE - Dated Status Snapshots (~15 files)
Move to `docs/archive/2026/status/`:
| File | Date | Notes |
|------|------|-------|
| 2026-03-28_REPOSITORY_HEALTH_EVALUATION.md | Mar 28 | Status snapshot |
| MASTER_STATUS_2026_03_16.md | Mar 16 | Status snapshot |
| RECONCILED_STATUS_2026_03_19.md | Mar 19 | Status snapshot |
| SESSION_STATUS.md | Mar 16 | Status snapshot |
| AGENT_SESSION_BOOKMARK.md | Mar 16 | Session state |
| DECOMPOSITION_BACKLOG_2026_03_16.md | Mar 16 | Dated backlog |
| INSTRUMENT_BUILD_TEST_REPORT_2026_03_16.md | Mar 16 | Test report |
| DEVELOPER_HANDOFF_2026_03_16.md | Mar 16 | Dated handoff |
| RECOVERY_BASELINE.md | Apr 13 | Recovery snapshot |
| session_audit_april16_2026_phase6b.md | Apr 16 | Session audit |
| dxf_files_march20_april1_2026.md | Apr 16 | DXF inventory |
| dxf_files_april1_april18_2026.md | Apr 18 | DXF inventory |
| VECTORIZER_V36_AUDIT_april16_21_2026.md | Apr 21 | Vectorizer audit |
| STUB_DEBT_REPORT.md | Mar 15 | Debt snapshot |
| SUPABASE_INTEGRATION_STATUS.md | Mar 10 | Integration status |

### Category: ARCHIVE - Completed Remediation (~12 files)
Move to `docs/archive/2026/remediation/`:
| File | Date | Notes |
|------|------|-------|
| REMEDIATION_PLAN.md | Mar 16 | Superseded |
| REMEDIATION_PLAN_v2.md | Mar 14 | Superseded |
| REMEDIATION_MASTER_2026_03_16.md | Mar 16 | Completed |
| REMEDIATION_EXECUTIVE_SUMMARY_2026_03_19.md | Mar 19 | Completed |
| REMEDIATION_FINAL_AUDIT_2026_03_28.md | Mar 28 | Completed |
| REMEDIATION_STATUS_MARCH_2026.md | Mar 28 | Completed |
| REVIEW_REMEDIATION_PLAN.md | Mar 14 | Review doc |
| UNFINISHED_REMEDIATION_EFFORTS.md | Mar 19 | Completed tracking |
| CODE_QUALITY_EXECUTION_PLAN.md | Feb 25 | Completed |
| CODE_QUALITY_HANDOFF.md | Feb 25 | Completed |
| GENERATOR_REMEDIATION_PLAN.md | Mar 17 | Completed |
| DEAD_CODE_RECOVERY_ASSESSMENT.md | Feb 27 | Assessment complete |

### Category: ARCHIVE - Superseded Plans (~10 files)
Move to `docs/archive/2026/plans/`:
| File | Date | Notes |
|------|------|-------|
| PHASE_2_3_IMPLEMENTATION_PLAN.md | Mar 7 | Superseded |
| PHASE6_CAD_GEOMETRY_HANDOFF.md | Apr 15 | Phase complete |
| GEO_BAND_ROPE_INTEGRATION_PLAN.md | Mar 12 | Plan doc |
| ROSETTE_WHEEL_ENGINE_INTEGRATION_PLAN.md | Mar 14 | Plan doc |
| INLAY-06-Unified-Inlay-Workspace-Plan.md | Mar 16 | Plan doc |
| CU-A1-SoundholeRosetteShell-Plan.md | Mar 16 | Plan doc |
| SCORE_7_PLAN.md | Mar 19 | Plan doc |
| STORE_MIGRATION_POSTGRES.md | Mar 15 | Migration plan |
| ROUTER_CONSOLIDATION_ROADMAP.md | Feb 12 | Roadmap |
| BACKLOG.md | Mar 24 | Superseded by SPRINTS.md |

### Category: ARCHIVE - Evaluations/Assessments (~10 files)
Move to `docs/archive/2026/evaluations/`:
| File | Date | Notes |
|------|------|-------|
| ARCHITECTURE_MIGRATION_ASSESSMENT.md | Feb 23 | Assessment |
| TOOLBOX_EVALUATION.md | Feb 22 | Evaluation |
| SYSTEM_EVALUATION.md | Mar 15 | Evaluation |
| PRODUCTION_SHOP_EVALUATION.md | Mar 19 | Evaluation |
| RED_TEAM_DESIGN_REVIEW.md | Mar 19 | Review |
| INSTRUMENT_COMPLETENESS_AUDIT.md | Mar 25 | Audit |
| VECTORIZER_PIPELINE_AUDIT.md | Apr 11 | Audit |
| PHOTO_VECTORIZER_TEST_AUDIT.md | Apr 6 | Audit |
| ROSETTE_SYSTEM_AUDIT.md | Mar 16 | Audit |
| GAP_ANALYSIS_MASTER.md | Mar 28 | Analysis |

### Category: MOVE TO docs/handoffs/ (~5 files)
These are handoffs that landed at wrong location:
| File | Date |
|------|------|
| CHIEF_ENGINEER_HANDOFF.md | Mar 9 |
| ROSETTE_CONSOLIDATION_HANDOFF.md | Mar 14 |
| EDGE_DETECTION_STRATEGY_HANDOFF.md | Apr 3 |
| THIN_STROKE_PDF_HANDOFF.md | Apr 14 |

### Category: KEEP - Specs/Reference (~20 files)
Technical specifications and reference material that remain active:
| File | Notes |
|------|-------|
| ANALYZER_BOUNDARY_SPEC.md | Boundary spec |
| BLUEPRINT_READER_INPUT_SPEC.md | Input spec |
| BOUNDARY_RULES.md | Rules |
| BRIDGE_BREAK_ANGLE_DERIVATION.md | Derivation (methodology) |
| BRIDGE_COMPENSATION_LAB_CODE_BUNDLE.md | Code reference |
| BRIDGE_COMPENSATION_THEORY_CHRONICLE.md | Theory reference |
| BUSINESS_SUITE_SPEC.md | Business spec |
| CONTOUR_PLAUSIBILITY_ENGINEERING_SPEC.md | Engineering spec |
| DXF_TO_GCODE_WORKFLOW.md | Workflow |
| INSTRUMENT_ROUTER_MIGRATION_MAP.md | Migration map |
| INSTRUMENT_ROUTER_OVERLAP.md | Analysis |
| OPERATION_EXECUTION_GOVERNANCE_v1.md | Governance |
| PERSONAS.md | User personas |
| SYSTEM_MAP.md | System reference |
| ROUTER_MAP.md | Router reference |
| SAFETY_CASE.md | Safety case |
| CBSP21.md | Spec |
| DECOMPOSITION_GUIDELINES.md | Guidelines |
| VUE_DECOMPOSITION_GUIDE.md | Guide |
| LESPAUL_VS_EXPLORER_COMPARISON.md | Reference |

---

## Phase 3: docs/handoffs/ (27 files)

### 60-day rule: Keep files from March 3, 2026 onwards

### ARCHIVE - Pre-March handoffs (10 files)
Move to `docs/archive/2026/handoffs/`:
| File | Date |
|------|------|
| VECTORIZER_UPGRADE_HANDOFF.md | Mar 6 |
| BENEDETTO_ARCHTOP_ROPE_BINDING_HANDOFF.md | Mar 7 |
| BLUEPRINT_VECTORIZER_INTEGRATION_HANDOFF.md | Mar 7 |
| FLYING_V_1958_CNC_HANDOFF.md | Mar 7 |
| OM_PURFLING_CNC_HANDOFF.md | Mar 7 |
| GIBSON_EXPLORER_1958_CNC_HANDOFF.md | Mar 9 |
| LES_PAUL_1959_CNC_HANDOFF.md | Mar 9 |
| 24_FRET_STRATOCASTER_DESIGN_HANDOFF.md | Mar 12 |
| CUSTOM_INLAY_FRETBOARD_HEADSTOCK_HANDOFF.md | Mar 12 |
| J45_VINE_OF_LIFE_DESIGN_HANDOFF.md | Mar 12 |
| OM_HERRINGBONE_ACOUSTIC_HANDOFF.md | Mar 12 |
| STRATOCASTER_NECK_DESIGN_HANDOFF.md | Mar 12 |
| TOOLPATH_ANIMATED_VISUALIZER_HANDOFF.md | Mar 12 |
| SMART_GUITAR_V1_CNC_HANDOFF.md | Mar 25 |

### KEEP - Recent handoffs (13 files)
All April handoffs stay:
| File | Date |
|------|------|
| VECTORIZER_PIPELINE_HANDOFF.md | Apr 13 |
| BODY_OUTLINE_EDITOR_V2_HANDOFF.md | Apr 17 |
| FEEDBACK_LOOP_SYSTEM_HANDOFF.md | Apr 19 |
| IBG_SYSTEMS_ENGINEERING_REVIEW.md | Apr 19 |
| IBG_BACKEND_COORDINATION.md | Apr 20 |
| EDGE_TO_DXF_API_MIGRATION_HANDOFF.md | Apr 28 |
| EDGE_TO_DXF_REFINED_METHODOLOGY.md | Apr 28 |
| LWPOLYLINE_FUSION360_VERIFICATION_HANDOFF.md | Apr 28 |
| SIMPLE_EXTRACTION_METHODOLOGY.md | Apr 28 |
| BASELINE_TEST_FAILURES_HANDOFF.md | Apr 29 |
| FRET_ECOSPHERE_PHASE2_HANDOFF.md | Apr 30 |
| ROSETTE_DESIGNER_DEVELOPER_HANDOFF.md | Apr 30 |
| SPIRAL_SOUNDHOLE_DEVELOPER_HANDOFF.md | Apr 30 |

---

## Phase 4: docs/audit/ and docs/investigations/

### docs/audit/ - ALL KEEP (15 files, all April 2026)
These are all recent audits within 60-day window.

### docs/investigations/ - ALL KEEP (7 files, all April 2026)
These are all recent investigations within 60-day window.

---

## Phase 5: Existing docs/archive/ Cleanup

### Python files - Move to archive/code/2026/
| File | Action |
|------|--------|
| docs/archive/pv2_sandbox.py | Move to archive/code/2026/ |
| docs/archive/session_bracing_router_temp.py | Move to archive/code/2026/ |

### Preserve existing structure
These existing archive directories stay as-is:
- docs/archive/instrument_references/ (reference material)
- docs/archive/photo_vectorizer_experiment_20260321/
- docs/archive/photo_vectorizer_patches/
- docs/archive/recovered/
- docs/archive/rosette_designer_history/
- docs/archive/toolpath_visualizer_plan/

---

## Phase 6: Sprint Artifacts

### Archive sprint_P4B_production_shop/
Move to `docs/archive/2026/sprints/sprint_p4b/`

---

## Phase 7: JSON Documentation Files

### KEEP (runtime or active reference)
| File | Reason |
|------|--------|
| docs/rmos_bundles.json | Likely runtime config |
| docs/tests/ratios_template.json | Test fixture |

### ARCHIVE with related markdown
| File | Action |
|------|--------|
| docs/REPO_DATA_AUDIT.json | Archive with REPO_DATA_AUDIT.md |

### Already in archive (no action)
| File | Location |
|------|----------|
| docs/archive/photo_vectorizer_experiment_20260321/body_dimension_reference.json | Already archived |
| docs/archive/photo_vectorizer_patches/*.json | Already archived |

---

## Proposed Archive Structure

```
docs/archive/
├── INDEX.md                    # Archive navigator
├── 2026/
│   ├── handoffs/              # Completed handoffs
│   ├── audits/                # Addressed audits  
│   ├── evaluations/           # Completed assessments
│   ├── status/                # Point-in-time snapshots
│   ├── remediation/           # Completed remediation
│   ├── plans/                 # Superseded plans
│   ├── sprints/               # Sprint artifacts
│   │   └── sprint_p4b/
│   └── session-notes/         # Extracted .txt content (Phase 3)
├── instrument_references/      # Existing - keep
├── photo_vectorizer_experiment_20260321/  # Existing - keep
├── photo_vectorizer_patches/   # Existing - keep
├── recovered/                  # Existing - keep
├── rosette_designer_history/   # Existing - keep
└── toolpath_visualizer_plan/   # Existing - keep

archive/                        # At repo root, for code
└── code/
    └── 2026/
        ├── pv2_sandbox.py
        └── session_bracing_router_temp.py
```

---

## DO NOT TOUCH

Per scope constraints, these are explicitly excluded:
- docs/adr/ (Architecture Decision Records)
- docs/api/ (API documentation)
- docs/Guitar Plans/ (reference plans)
- production_shop_agent/ (separate project)
- sandbox/ (active development)
- services/ (codebase)
- Test fixtures in test directories
- Runtime data registries

---

## Execution Order

1. **Phase 0**: Delete __pycache__ and nested repo copy (immediate, no approval needed)
2. **Phase 1**: Root file reorganization (needs approval)
3. **Phase 2**: docs/ top-level reorganization (needs approval)
4. **Phase 3**: .txt content extraction (separate 1-2 day sub-sprint)
5. **Phase 4**: .zip externalization (needs external storage decision)
6. **Phase 5**: Archive structure creation and moves
7. **Phase 6**: Build INDEX.md files
8. **Phase 7**: Update CLAUDE.md with archive policy

---

## Approval Required

Before proceeding with Phase 1+:
1. Review proposed dispositions above
2. Flag any files that should have different disposition
3. Confirm external storage location for .zip files
4. Confirm whether .txt extraction is in-scope or deferred

Ready to execute Phase 0 (cleanup) immediately upon confirmation.
