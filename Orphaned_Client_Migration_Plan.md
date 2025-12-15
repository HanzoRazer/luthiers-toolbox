✅ 1. Orphaned_Client_Migration_Plan.md

(Drop this directly into the repo under docs/Client/)

# Orphaned Client Migration Plan
### Luthier’s ToolBox — Front-End Consolidation Strategy  
**Version:** 1.0  
**Status:** Approved for implementation  
**Author:** Ross  

---

# 1. Purpose

This document defines the plan to merge the legacy front-end code tree:



client/src/


into the canonical, monorepo-aligned front-end:



packages/client/src/


The legacy `client/src` tree contains:
- Tool calculators  
- Compare engine  
- Art Studio dashboards  
- Wiring + hardware workbench  
- CAM & G-Code tools  
- SawLab UI  
- Instrument geometry utilities  
- View/layout systems  
- Markdown documentation  

These were *never committed* to the monorepo and now exist in an orphaned state.  
This plan safely migrates all code, resolves conflicts, and retires the legacy tree.

---

# 2. Rules of Migration

1. **Canonical Frontend = `packages/client/src/`**  
2. **Legacy client = staging/merge source ONLY**  
3. **Nothing in `client/` should remain after migration**  
4. **No direct overwrites without comparison**  
5. **Zero data loss — everything must be absorbed or archived**  
6. **Back-end APIs (RMOS, Calculators, Saw Lab, CAM) remain unchanged**  
7. **Every migrated module must resolve imports before final commit**  
8. **Each migration is committed as a *logical bundle* (not one giant commit)**  

---

# 3. Migration Phases

---

## Phase 0 — Safety & Inventory

### Tasks:
- [ ] Zip entire `client/` folder → `client_legacy_backup.zip`
- [ ] Commit the Orphaned Files Inventory  
- [ ] Work from `feature/client-migration` branch  

Outcome:  
A “locked” snapshot exists, and work proceeds on a safe branch.

---

## Phase 1 — Establish Canonical Structure

Ensure the following exist in `packages/client/src/`:



components/toolbox/
components/compare/
views/
utils/
utils/math/
labs/
router/


Create any missing folders.

---

## Phase 2 — Toolbox Calculators Migration (38 components)

Copy from:



client/src/components/toolbox/


to:



packages/client/src/components/toolbox/


Files include (examples):

- `ArchtopCalculator.vue`
- `BridgeCalculator.vue`
- `BracingCalculator.vue`
- `CNCROICalculator.vue`
- `ScientificCalculator.vue`
- `RosetteDesigner.vue`
- `ScaleLengthDesigner.vue`
- `HardwareWorkbench.vue`

### Tasks:
- [ ] Copy all calculator components  
- [ ] Fix internal imports as needed  
- [ ] Add route entries for Toolbox hub  

Commit message:



feat(client): migrate toolbox calculators from legacy client


---

## Phase 3 — Compare Engine Migration (19 files)

Migrate the compare subsystem:



client/src/components/compare/
client/src/composables/useCompareState.ts
client/src/utils/compareReportBuilder.ts


### Tasks:
- [ ] Compare each file with packages version  
- [ ] Copy missing components, merge differences  
- [ ] Reconnect tests into monorepo test runner  

Commit:



feat(client): consolidate compare engine into packages/client


---

## Phase 4 — Utilities & Math Migration

Move orphaned utilities such as:



client/src/utils/curvemath*.ts
client/src/utils/curveRadius.ts
client/src/utils/compoundRadius.ts
client/src/utils/neck_generator.ts
client/src/utils/switch_validator.ts
client/src/utils/treble_bleed.ts


Copy into:



packages/client/src/utils/
packages/client/src/utils/math/


Commit:



feat(client): migrate instrument geometry & wiring utilities


---

## Phase 5 — Key Views & Dashboards Migration

Migrate essential dashboards:

- `ArtStudioDashboard.vue`
- `CamDashboard.vue`
- `SawLabDashboard.vue`
- `PresetHubView.vue`
- `LabsIndex.vue`
- `GCodeExplainer.vue`
- `DXFCleaner.vue`
- `RosetteDesignerView.vue`

Copy into:



packages/client/src/views/


Then update routes:



/toolbox
/saw-lab
/cam/dashboard
/art/dashboard
/compare


Commit:



feat(client): restore dashboards and labs views


---

## Phase 6 — G-Code & DXF Tools Migration

Files from:



client/src/components/cam/
client/src/utils/dxf_cleaner.ts
client/src/utils/gcode_parser.ts


Move into:



packages/client/src/components/toolbox/
packages/client/src/utils/


Commit:



feat(client): migrate gcode/dxf utilities and connect to CAM endpoints


---

## Phase 7 — Legacy Cleanup & Removal

After verification:

- [ ] Ensure all required files migrated  
- [ ] Delete `client/` folder from working tree  
- [ ] Regenerate TypeScript import maps  
- [ ] Run build + test suite  

Commit:



chore(client): remove legacy client tree (fully migrated)


---

# 4. Post-Migration Checks

- [ ] All routes resolve  
- [ ] Vite builds with no missing imports  
- [ ] Compare engine working  
- [ ] Toolbox calculators render  
- [ ] Saw Lab UI working  
- [ ] CAM tools interaction OK  
- [ ] G-Code Explainer connected to Wave 11 backend  
- [ ] Instrument geometry displays accurate previews  

---

# 5. Completion Criteria

Migration is **complete** when:

- No `.vue`, `.ts`, `.js`, `.md` files remain in `client/src/`  
- All calculators & UIs work under `packages/client/src/`  
- CI build is green  
- All tests pass  
- Art Studio, SawLab, Toolbox, CAM dashboards load  
- Previews + comparisons operate normally  

---

# 6. Next Steps (Post-Merge)

## Wave 12 Front-End

- AI-assisted CAM interface  
- G-Code annotation overlay  
- DXF cleanup visualizer  
- Smart Tool Selector (using Tool Library)  
- Material warning badges  
- Physics Advisor Panel (chipload, heat, deflection)  

---

# End of Document