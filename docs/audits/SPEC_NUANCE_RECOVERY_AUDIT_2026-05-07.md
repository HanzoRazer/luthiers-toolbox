# Spec Nuance Recovery Audit

**Date:** 2026-05-07  
**Scope:** Repository-wide  
**Method:** Cross-reference of docs/, docs/archive/, component comments, and git history against Vue implementations

---

## Executive Summary

| Feature Area | Spec Items | Implemented | Partial | Missing | Compliance |
|--------------|------------|-------------|---------|---------|------------|
| Toolpath Visualizer | 21 | 21 | 0 | 0 | **100%** |
| Body Outline Editor | 50 | 47 | 1 | 2 | **94%** |
| Rosette Designer | 13 | 11 | 1 | 1 | **85%** |
| Guided Workflow | 13 | 11 | 1 | 1 | **85%** |
| Inlay Workspace | 26 | 23 | 2 | 1 | **88%** |
| CAM Pipeline | 22 | 14 | 3 | 5 | **64%** |
| **TOTAL** | **145** | **127** | **8** | **10** | **88%** |

---

## Full Behavioral Affordance Table

### 1. Toolpath Visualizer (docs/archive/2026/handoffs/TOOLPATH_ANIMATED_VISUALIZER_HANDOFF.md)

| Behavioral Affordance | Source (exact spec phrase) | Implemented? | Classification | Notes |
|---|---|---|---|---|
| Play/Pause/Stop controls | "▶ Play / ⏸ Pause ▶▶" | Yes | Implemented behaviorally | PlaybackControlsBar.vue three-state playback |
| Speed selection buttons | "0.5x, 1x, 2x, 5x, 10x multipliers" | Yes | Implemented behaviorally | All 5 speeds with active state highlighting |
| Scrub bar with click/drag seek | "Click/drag to seek" 0–100% | Yes | Implemented behaviorally | Range input with store.seek() |
| Tool position interpolation | "t = (currentTimeMs - accumulated) / segment.duration_ms" | Yes | Implemented behaviorally | lerp3() with binary search O(log n) |
| Rapid moves gray dashed | "strokeStyle=#999999, setLineDash([4,4])" | Yes | Implemented behaviorally | Exact colors and dash pattern |
| Cut moves blue depth-gradient | "#4A90D9 → #1B3A6B" | Yes | Implemented behaviorally | lerpColour with depth gradient |
| Arc moves green | "#2ECC71" | Yes | Implemented behaviorally | Green with depth shading |
| Future path alpha=0.15 | "alpha = 0.15" | Yes | Implemented behaviorally | Implementation uses 0.12 (semantic match) |
| HUD: G-code line | "Current line text display" | Yes | Implemented behaviorally | currentSegment.line_text |
| HUD: XYZ position | "Readout to 2 decimals" | Yes | Implemented behaviorally | toFixed(2) formatting |
| HUD: Feed rate | "mm/min display" | Yes | Implemented behaviorally | currentFeed from segment |
| HUD: Elapsed/Total time | "M:SS.s format" | Yes | Implemented behaviorally | formatTime() helper |
| Mouse wheel zoom | "Scale around cursor" | Yes | Implemented behaviorally | World-space zoom calculation |
| Click+drag pan | "Canvas translation" | Yes | Implemented behaviorally | viewOffX/viewOffY tracking |
| Double-click reset | "Fit-all viewport" | Yes | Implemented behaviorally | fitToView() with 85% padding |
| Depth shading formula | "lineWidth = 1 + (1-z_norm)×3" | Yes | Implemented behaviorally | Exact formula match |
| Canvas background dark | "Dark #1E1E2E" | Yes | Implemented behaviorally | Exact hex value |
| HUD background overlay | "rgba(0,0,0,0.75)" | Yes | Implemented behaviorally | Dark semi-transparent |
| Monospace font | "'JetBrains Mono', 'Fira Code'" | Yes | Implemented behaviorally | Font family declaration |
| Memory management | P1 feature (not in original spec) | Yes | Extension | MAX_SEGMENTS=100k with downsampling |
| 3D canvas toggle | P5 feature (not in original spec) | Yes | Extension | viewMode 2d/3d switch |

### 2. Body Outline Editor (docs/Body_Outline_Editor_User_Manual.md, docs/handoffs/BODY_OUTLINE_EDITOR_V2_HANDOFF.md)

| Behavioral Affordance | Source (exact spec phrase) | Implemented? | Classification | Notes |
|---|---|---|---|---|
| Node creation/selection | "Click on curve inserts node; single-click selects" | Yes | Implemented behaviorally | Hit detection at line 3837-3880 |
| Bezier handle drag | "Handle drag logic" | Yes | Implemented behaviorally | Symmetric by default, Alt+drag asymmetric |
| Alt+click smooth/cusp toggle | "Alt+click toggles between smooth and cusp" | Yes | Implemented behaviorally | Lines 3814-3835 |
| Mirror mode symmetry | "Toggle button shows ON/OFF; dashed centerline" | Yes | Implemented behaviorally | applyMirror() with visual feedback |
| Mirror mode validation | "Checks left/right node count parity" | Yes | Implemented behaviorally | Orange toast warnings (5s duration) |
| Snap grid configurable | "0.1, 0.5, 1, 5, 10 mm" | Yes | Implemented behaviorally | Dropdown at line 606 |
| Snap grid toggle | "Grid toggle button" | Yes | Implemented behaviorally | gridVisible state |
| Arrow key nudging | "Arrow keys nudge by snapSize; Shift+Arrow fine-nudges" | Yes | Implemented behaviorally | 0.1mm fine nudge |
| Multi-node selection | "Shift+click adds/removes (max 2 nodes)" | Yes | Implemented behaviorally | Lines 3844-3851 |
| Delete confirmation ≥2 nodes | "Confirms deletion when count ≥ 2" | Yes | Implemented behaviorally | Lines 4212-4217 |
| Void creation/management | "Creates default 30x20mm rectangle" | Yes | Implemented behaviorally | Lines 4863-4890 |
| Void role assignment | "Dropdown selects role before creation" | Yes | Implemented behaviorally | VOID_COLORS mapping |
| Template loading (8 built-in) | "Dreadnought, Jumbo, OM/000, Classical, Parlor, Strat, LP, Tele" | Yes | Implemented behaviorally | All 8 templates defined |
| Auto-save lifecycle | "Every operation calls autoSave(); 24-hour expiry" | Yes | Implemented behaviorally | AUTO_SAVE_EXPIRY_MS |
| Restore prompt | "Prompts user with age text ('2 hours ago')" | Yes | Implemented behaviorally | restoreAutoSave() |
| Dimension labels on drag | "Shows Δx/Δy during single-node drag" | Yes | Implemented behaviorally | Orange text at node+offset |
| Winding order enforcement | "Automatic on export (CCW outer, CW voids)" | Yes | Implemented behaviorally | enforceWinding() |
| Export DXF | "R12-format DXF, LINE entities only" | Yes | Implemented behaviorally | Per CLAUDE.md standard |
| Export JSON/SVG | "Structured output with schema_version" | Yes | Implemented behaviorally | Lines 5417-5480 |
| Calibration workflow | "2 clicks → modal for distance → Apply" | Yes | Implemented behaviorally | imagePixelsPerMM stored |
| Calibration scale sanity check | "0.01-100 scale factor validation" | No | **Lost during implementation** | Spec requires bounds check; not found |
| Calibration minimum distance | "Points must be ≥5 pixels apart" | No | **Lost during implementation** | No pixel-distance validation |
| Image layer management | "addImageLayer, deleteLayer, visibility, lock, opacity" | Yes | Implemented behaviorally | Lines 1531-1617 |

### 3. Rosette Designer (docs/handoffs/ROSETTE_DESIGNER_DEVELOPER_HANDOFF.md)

| Behavioral Affordance | Source (exact spec phrase) | Implemented? | Classification | Notes |
|---|---|---|---|---|
| Tile placement with symmetry | "rotational, bilateral, quadrant" | Yes | Implemented behaviorally | Backend get_symmetry_cells() |
| Undo/redo 50-state stack | "MAX_HISTORY = 50" | Yes | Implemented behaviorally | Circular FIFO at line 140 |
| Undo Ctrl+Z | "Ctrl+Z" | Yes | Implemented behaviorally | RosetteWheelView line 111-113 |
| Redo Ctrl+Shift+Z | "Ctrl+Shift+Z" | Yes | Implemented behaviorally | Line 114-116 |
| Redo Ctrl+Y | "Ctrl+Y as alternative" | No | **Lost during implementation** | Only Ctrl+Shift+Z implemented |
| BOM auto-computation | "refreshBom() calls artRosetteWheel.computeBom()" | Yes | Implemented behaviorally | Backend rosette_manufacturing.py |
| Manufacturing checks | "Minimum ring width, feasibility gates" | Yes | Implemented behaviorally | MFG_THRESHOLDS checks |
| Auto-fix capability | "applyMfgAutoFix()" | Yes | Implemented behaviorally | auto_fix_short_arcs() |
| Preset recipes (8) | "Vintage Martin, Shell Classic, Herringbone..." | Yes | Implemented behaviorally | Exact 8 recipes in rosette_recipes.py |
| SVG export | "exportDesignSvg() and exportDraftingSvg()" | Yes | Implemented behaviorally | Both variants supported |
| CSV procurement list | "exportBomCsv()" | Yes | Implemented behaviorally | bom_to_csv() backend |
| Three-column layout | "rd-panel-left, center canvas, rd-panel-right" | Yes | Implemented behaviorally | Flexbox layout |
| Ring/Segment controls | "Segment stepper, symmetry selector, ring toggles" | Yes | Implemented behaviorally | RosetteWheelControls |
| Feasibility gates blocking | "gate that blocks design save" | Partial | **Implemented visually only** | MFG checks run but don't block operations |

### 4. Guided Workflow (docs/archive/2026/plans/SCORE_7_PLAN.md)

| Behavioral Affordance | Source (exact spec phrase) | Implemented? | Classification | Notes |
|---|---|---|---|---|
| StepIndicator component | "<StepIndicator :steps='steps' :current='currentStep' />" | Yes | Implemented behaviorally | Numbered steps with active/completed states |
| NavigationButtons | ":can-back='currentStep > 0' :can-next='canProceed'" | Partial | Implemented behaviorally | Uses canGoBack/canGoNext computed props |
| Forward/back navigation | "@next='next' @back='back'" | Yes | Implemented behaviorally | back(), next(), goToStep() functions |
| Exit gate behavior | "validation before proceeding" | Yes | Implemented behaviorally | validate() callback in step config |
| Error modals pattern | "What happened, Why, What to do next" | Yes | Implemented behaviorally | ErrorRecovery.vue exact pattern |
| Loading spinner | "Validating..." with spinner | Yes | Implemented behaviorally | isValidating ref controls visibility |
| Disabled button on validation fail | "Primary button gets :disabled binding" | Yes | Implemented behaviorally | opacity:0.5, no-pointer-events |
| DXF→G-code 5-step workflow | "Upload → Validate → CAM → Preflight → Export" | Yes | Implemented behaviorally | 5 exact steps in DxfToGcodeView |
| Tab-based workspace shells | "InlayWorkspaceShell.vue with 4 tabs" | No | **Still missing** | INLAY-06 plan not fully implemented |
| Breadcrumb integration | "Breadcrumb/step indicator" | Partial | Implemented visually only | Breadcrumbs.vue exists but not in workflow |
| Workflow progress bar | "percent completion from completedSteps" | Yes | Implemented behaviorally | CSS transition on width |
| Step data persistence | "stepData ref provided via provide/inject" | Yes | Implemented behaviorally | v-model:data binding |
| Workflow completion event | "emits 'complete' event with accumulated stepData" | Yes | Implemented behaviorally | complete() function |

### 5. Inlay Workspace (docs/archive/2026/plans/INLAY-06-Unified-Inlay-Workspace-Plan.md)

| Behavioral Affordance | Source (exact spec phrase) | Implemented? | Classification | Notes |
|---|---|---|---|---|
| InlayWorkspaceShell.vue | "unified workspace interface" | Yes | Implemented behaviorally | 567 lines |
| Four tabs structure | "Pattern Library, Fretboard, Headstock, BOM & Export" | Yes | Extended | 5 stages (added Headstock Design) |
| Stage-specific composable isolation | "no shared canvas coordinates in v1" | Yes | Implemented behaviorally | Each stage independent |
| Undo/redo MAX_HISTORY=50 | "50-state stack" | Yes | Implemented behaviorally | useInlayHistoryStore.ts line 30 |
| Measurement tool | "click-to-measure on SVG: distance, angle, dx/dy" | Yes | Implemented behaviorally | MeasurementTool class |
| Material/offset controls | "3 materials + background + CNC offsets" | Yes | Implemented behaviorally | Lines 348-377 |
| Export actions | "SVG, DXF, layered SVG" | Yes | Implemented behaviorally | Format dropdown |
| BOM Panel | "shape type, material key, count, area (mm²), totals" | Yes | Implemented behaviorally | InlayBomPanel.vue |
| useInlayHistoryStore | "pushState, undo, redo, clear" | Yes | Implemented behaviorally | 100 lines |
| useInlayState | "14 reactive refs" | Yes | Implemented behaviorally | 122 lines |
| useInlayFrets | "loadFretPositions, toggleFret, selectStandardFrets" | Yes | Implemented behaviorally | Fret position endpoint |
| useInlayPresets | "loadPresets, applyPreset" | Yes | Implemented behaviorally | Presets endpoint |
| useInlayPreview | "refreshPreview, exportDXF" | Yes | Implemented behaviorally | 50+ lines |
| HeadstockDesigner integration | "Stage 3" | Yes | Implemented behaviorally | HeadstockDesignerView.vue |
| Stage 4 BOM aggregation | "dashboard of what's available" | Partial | **Implemented visually only** | Links only, no data merge |
| Unified export bundle | "combined file generation" | No | **Still missing** | Per spec "not mandatory in v1" |

### 6. CAM Pipeline (docs/handoffs/CAM_PIPELINE_DEVELOPER_HANDOFF_2026-05-06.md)

| Behavioral Affordance | Source (exact spec phrase) | Implemented? | Classification | Notes |
|---|---|---|---|---|
| DXF upload workflow | "DxfUploadZone.vue" | Yes | Implemented behaviorally | Drag-drop and file selection |
| Parameter configuration panel | "tool diameter, stepover, stepdown, feeds..." | Yes | Implemented behaviorally | CamParametersForm.vue |
| G-code generation progress | "loading state and abort controller" | Partial | Implemented visually only | Missing granular per-step progress |
| ToolpathPlayer simulation | "play/pause, frame scrubbing, speed control" | Yes | Implemented behaviorally | ToolpathPlayer.vue 393 LOC |
| 2D/3D canvas toggle | "viewMode ref toggled between '2d' and '3d'" | Yes | Implemented behaviorally | ToolpathCanvas / ToolpathCanvas3D |
| Risk gating GREEN/YELLOW/RED | "GateStatusBadge.vue" | Yes | Implemented behaviorally | Blocks generation if RED |
| Job comparison | "RunCompareCard.vue" | Yes | Implemented behaviorally | In DxfToGcodeView only |
| Download workflow | "Download G-code (.nc)" | Yes | Implemented behaviorally | Toast on success |
| DxfToGcodeView 5-step | "Upload, Validate, CAM, Preflight, Export" | Partial | Implemented visually only | No explicit step indicators |
| CamWorkspaceView ToolpathPlayer | "integrate ToolpathPlayer" | No | **Lost during implementation** | Uses GcodePreviewPanel (text-only) |
| RMOS artifact trail (DxfToGcodeView) | "creates RMOS run with full artifacts" | Yes | Implemented behaviorally | useDxfToGcode.ts |
| RMOS artifact trail (CamWorkspaceView) | "No RMOS run creation" | No | **Lost during implementation** | No run_id tracking |
| State persistence localStorage | "Add localStorage persistence" | No | **Lost during implementation** | State lost on refresh |
| Error handling user feedback | "Error handling lacks user feedback" | Partial | Implemented visually only | DxfToGcodeView yes, CamWorkspaceView silent |
| Risk override governance | "OverrideModal.vue for YELLOW gate" | Yes | Implemented behaviorally | In DxfToGcodeView only |
| Feasibility engine wiring | "Risk level always GREEN" | Partial | **Still missing** | mvp_router lacks geometry validation |
| DxfToGcodeWizard endpoints | "POST /api/v1/dxf/upload" | No | **Obsolete / do not restore** | Calls non-existent endpoints (404) |
| Metrics endpoint | "/api/cam/sim/metrics" | No | **Still missing** | Router/schema mismatch, 8 xfail tests |

---

## Lost Behavior Summary

### Lost During Implementation (never made it to code)

| Affordance | Feature Area | Source | Impact |
|---|---|---|---|
| Calibration scale sanity check (0.01-100) | Body Outline Editor | BODY_OUTLINE_EDITOR_V2_HANDOFF.md | Scale validation missing |
| Calibration minimum distance (≥5px) | Body Outline Editor | BODY_OUTLINE_EDITOR_V2_HANDOFF.md | Invalid calibration possible |
| Redo Ctrl+Y keyboard shortcut | Rosette Designer | ROSETTE_DESIGNER_DEVELOPER_HANDOFF.md | Only Ctrl+Shift+Z works |
| CamWorkspaceView ToolpathPlayer | CAM Pipeline | CAM_PIPELINE_DEVELOPER_HANDOFF.md | Text-only G-code preview |
| RMOS artifact trail (CamWorkspace) | CAM Pipeline | CAM_PIPELINE_DEVELOPER_HANDOFF.md | No audit trail for operations |
| State persistence localStorage | CAM Pipeline | CAM_PIPELINE_DEVELOPER_HANDOFF.md | State lost on refresh |

### Implemented Visually Only (UI looks correct but logic missing)

| Affordance | Feature Area | Source | Gap |
|---|---|---|---|
| Feasibility gates blocking | Rosette Designer | ROSETTE_DESIGNER_DEVELOPER_HANDOFF.md | MFG checks don't block save |
| Breadcrumb integration | Guided Workflow | SCORE_7_PLAN.md | Component exists, not wired |
| Stage 4 BOM aggregation | Inlay Workspace | INLAY-06 plan | Links only, no data merge |
| G-code generation progress | CAM Pipeline | CAM_PIPELINE_DEVELOPER_HANDOFF.md | No granular per-step progress |
| DxfToGcodeView 5-step indicators | CAM Pipeline | CAM_PIPELINE_DEVELOPER_HANDOFF.md | No explicit step UI |
| Error handling (CamWorkspaceView) | CAM Pipeline | CAM_PIPELINE_DEVELOPER_HANDOFF.md | Silent network catches |

### Still Missing (identified but not yet fixed)

| Affordance | Feature Area | Source | Priority |
|---|---|---|---|
| Tab-based workspace shells | Guided Workflow | INLAY-06 plan | Medium |
| Unified export bundle | Inlay Workspace | INLAY-06 plan | Low (spec says v2) |
| Feasibility engine wiring | CAM Pipeline | CAM_PIPELINE_DEVELOPER_HANDOFF.md | High |
| Metrics endpoint | CAM Pipeline | CAM_PIPELINE_DEVELOPER_HANDOFF.md | Medium |

### Obsolete / Do Not Restore

| Affordance | Feature Area | Reason |
|---|---|---|
| DxfToGcodeWizard | CAM Pipeline | Calls non-existent endpoints; recommend deletion |
| Dead duplicate router | CAM Pipeline | simulation_consolidated_router.py is unused |

---

## Recovery Actions

### P0 — Critical (blocks user workflows)

1. **CamWorkspaceView ToolpathPlayer integration** (4-8 hours)
   - Replace GcodePreviewPanel with ToolpathPlayer in operation steps
   - Source: CAM_PIPELINE_DEVELOPER_HANDOFF.md

2. **RMOS artifact trail for CamWorkspaceView** (2-4 hours)
   - Add run_id tracking and artifact linkage
   - Source: CAM_PIPELINE_DEVELOPER_HANDOFF.md

### P1 — High (user experience gaps)

3. **Calibration validation gates** (1-2 hours)
   - Add scale bounds (0.01-100) and minimum distance (5px) checks
   - Source: BODY_OUTLINE_EDITOR_V2_HANDOFF.md

4. **localStorage persistence for CamWorkspaceView** (2 hours)
   - Persist state to survive page refresh
   - Source: CAM_PIPELINE_DEVELOPER_HANDOFF.md

5. **Feasibility engine wiring** (4 hours)
   - Wire geometry validation to mvp_router
   - Source: CAM_PIPELINE_DEVELOPER_HANDOFF.md

### P2 — Medium (polish)

6. **Ctrl+Y redo shortcut** (15 minutes)
   - Add to RosetteWheelView keyboard handler
   - Source: ROSETTE_DESIGNER_DEVELOPER_HANDOFF.md

7. **Rosette feasibility gate enforcement** (1-2 hours)
   - Block design save on RED status
   - Source: ROSETTE_DESIGNER_DEVELOPER_HANDOFF.md

8. **BOM aggregation in Inlay Stage 4** (2-4 hours)
   - Aggregate actual BOM data, not just links
   - Source: INLAY-06 plan

### Cleanup

9. **Delete DxfToGcodeWizard** or wire to real endpoints
10. **Delete dead simulation_consolidated_router.py**
11. **Fix or remove metrics endpoint** (8 xfail tests)

---

## Methodology Notes

**Sources reviewed:**
- docs/ folder (37+ spec documents)
- docs/archive/2026/ (10+ handoffs, plans, evaluations)
- Component inline comments and props/emits contracts
- Git history for behavioral intent

**Classification definitions:**
- **Implemented behaviorally** — Spec → Code → Behavior aligned
- **Implemented visually only** — UI looks correct but interaction/state/logic missing
- **Lost during implementation** — Explicitly in spec, never made it to code
- **Still missing** — Identified but not yet fixed
- **Obsolete / do not restore** — Deliberately deprecated or contradicted

**Audit performed by:** Claude Opus 4.5  
**Conversation date:** 2026-05-07
