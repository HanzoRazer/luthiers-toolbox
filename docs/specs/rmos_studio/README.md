# RMOS Studio – Specification Suite Index

**Version:** 1.0  
**Date:** November 30, 2025  
**Status:** Archived as Reference Specifications  
**Purpose:** Complete engineering documentation for aspirational rosette pattern design system

---

## 📋 Overview

This directory contains the **RMOS Studio specification suite**—a comprehensive set of engineering documents describing an aspirational rosette mosaic design and manufacturing system. These documents represent a complete software engineering vision for rosette pattern creation, distinct from the current **RMOS N8–N10 implementation**.

**Important:** These are **specification documents**, not implemented code. They serve as:
- Algorithmic reference for tile segmentation and kerf compensation
- Manufacturing planning guidelines
- Validation framework specifications
- Integration blueprints for future N11+ bundles

For the **current RMOS implementation**, see:
- `docs/RMOS_N8_N10_ARCHITECTURE.md` - Actual N8–N10 architecture
- `docs/RMOS_MASTER_TREE.md` - Development roadmap
- `projects/rmos/` - Active RMOS codebase

---

## 📚 Document Inventory

### **Core System Specifications**

#### 1. **RMOS_STUDIO.md** (~800 lines)
**Purpose:** Main system overview and user-facing functionality  
**Contents:**
- Column → Tile transformation model
- Three editing modes (preset, simplified, manual)
- Pattern families (Spanish Traditional, Herringbone, Checkerboard)
- UI region specifications (6-panel layout)
- Workflow: Design → Slice → Export

**Key Sections:**
- Section 3: Strip Column Architecture
- Section 4: Ring Configuration & Tile Mapping
- Section 5: Pattern Families & Presets
- Section 6: UI Layout (Global Bar, Column Editor, Output Preview, etc.)

**Use For:** Understanding overall RMOS Studio design philosophy and user workflow

---

#### 2. **RMOS_STUDIO_SYSTEM_ARCHITECTURE.md** (~700 lines)
**Purpose:** Technical architecture specification  
**Contents:**
- 6-layer architecture definition
  1. Presentation Layer (UI)
  2. Application Logic Layer (Controllers)
  3. Geometry Layer (Computational modules)
  4. Manufacturing Planning Layer
  5. JobLog Layer (Audit trail)
  6. Export Layer (Serialization)
- Component interaction patterns
- Data flow diagrams
- Module boundaries and responsibilities

**Key Sections:**
- Section 3: Layer-by-Layer Breakdown
- Section 4: Data Flow Patterns
- Section 5: Module Integration Rules

**Use For:** Architectural design decisions for N11 rosette designer implementation

---

#### 3. **RMOS_STUDIO_ALGORITHMS.md** (~350 lines)
**Purpose:** Mathematical algorithms for rosette geometry  
**Contents:**
- **Tile Segmentation Algorithm** (Section 4)
  - Circumference calculation: `C = 2πR`
  - Tile count computation: `N = floor(C / tile_length_mm)`
  - Effective tile length: `tile_effective = C / N`
  - Angular bounds per tile: `θ_start`, `θ_end`
- **Herringbone Calculations** (Section 5)
  - Alternating slice angles: `±herringbone_angle`
  - Pattern continuity rules
- **Kerf Compensation** (Section 6)
  - Angular loss per slice: `angle_loss = (kerf_mm / C) × 360°`
  - Cumulative drift tracking
  - Compensation strategies

**Key Sections:**
- Section 4.1–4.4: Core tile segmentation math ⭐
- Section 6: Kerf compensation formulas ⭐

**Use For:** Implementing `services/api/app/cam/rosette/tile_segmentation.py`

---

#### 4. **RMOS_STUDIO_SAW_PIPELINE.md** (~350 lines)
**Purpose:** Slicing algorithm and saw batch generation  
**Contents:**
- Ring circumference → tile segmentation workflow
- Slice angle computation (raw, twisted, herringbone, kerf-adjusted)
- Saw batch JSON structure
- Sequential slice indexing
- Material mapping per slice

**Key Sections:**
- Section 3: Slicing Algorithm Steps
- Section 4: Slice Angle Transformations
- Section 5: Saw Batch Structure

**Use For:** Implementing `services/api/app/cam/rosette/saw_batch_generator.py`

---

#### 5. **RMOS_STUDIO_MANUFACTURING_PLANNER.md** (~380 lines)
**Purpose:** Material planning and production estimation  
**Contents:**
- Strip-family requirement calculations
- Volume and mass estimation formulas
- Scrap modeling (default 5% waste factor)
- Production checklist generation
- Material efficiency metrics

**Key Sections:**
- Section 3: Material Usage Calculations ⭐
- Section 4: Volume/Mass Estimation
- Section 5: Scrap Modeling

**Use For:** Extending N9 analytics with rosette-specific material planning

---

#### 6. **RMOS_STUDIO_DATA_STRUCTURES.md** (~370 lines)
**Purpose:** Complete data schema specification  
**Contents:**
- Object definitions:
  - `Column` (strip stacks)
  - `Strip` (individual material layers)
  - `Pattern` (preset configurations)
  - `Ring` (circular bands)
  - `TileSegmentation` (computed tile layouts)
  - `Slice` (individual cut operations)
  - `SliceBatch` (complete saw job)
- JSON serialization formats
- Field constraints and validation rules

**Key Sections:**
- Section 2: Column & Strip Structures
- Section 3: Ring & Segmentation Objects
- Section 4: Slice & Batch Definitions

**Use For:** Extending `pattern_store` schema with rosette-specific fields

---

### **Integration & Operations Specifications**

#### 7. **RMOS_STUDIO_API.md** (~280 lines)
**Purpose:** REST API reference (aspirational)  
**Contents:**
- Project management endpoints
- Column/Pattern CRUD operations
- Ring configuration APIs
- Geometry calculation endpoints
- Manufacturing planner APIs
- JobLog management
- Export endpoints

**Key Sections:**
- Section 3: Pattern & Column APIs
- Section 4: Geometry & Segmentation APIs
- Section 6: Manufacturing APIs

**Use For:** Designing N11 rosette API routes under `/api/rmos/rosette/*`

---

#### 8. **RMOS_STUDIO_CNC_EXPORT.md** (~500 lines) 🆕
**Purpose:** CNC toolpath generation and G-code export  
**Contents:**
- G-code generation strategies
- Toolpath optimization
- Machine-specific post-processors
- Alignment metadata generation
- Jig offset calculations
- Export package structure (G-code + JSON + PDF)

**Key Sections:**
- Section 3: G-code Generation Patterns
- Section 4: Post-Processor Integration
- Section 5: Alignment & Jig Metadata

**Use For:** Extending Module K (multi-post export) with rosette-specific toolpaths

---

#### 9. **RMOS_STUDIO_VALIDATION.md** (~400 lines) 🆕
**Purpose:** Validation framework and constraint enforcement  
**Contents:**
- Multi-layer validation architecture
  1. Input Validation
  2. Column Validation
  3. Ring Geometry Validation
  4. Segmentation Validation
  5. Slice Generation Validation
  6. Kerf Compensation Validation
  7. Manufacturing Planner Validation
  8. JobLog Validation
  9. Export Validation
- Numerical constraints (min/max bounds)
- Geometric consistency checks
- Manufacturing feasibility rules

**Key Sections:**
- Section 3: Input Validation Rules ⭐
- Section 5: Ring Geometry Constraints ⭐
- Section 6: Segmentation Validation ⭐
- Section 8: Kerf Compensation Validation ⭐

**Use For:** Implementing validation middleware in N11 rosette endpoints

---

### **Developer & Operations Guides**

#### 10. **RMOS_STUDIO_DEVELOPER_GUIDE.md** (~390 lines) 🆕
**Purpose:** Developer integration and implementation handbook  
**Contents:**
- Environment setup requirements
- Recommended project structure
- Coding standards (PEP8, deterministic output)
- Module integration rules
- Testing strategy (unit, integration, snapshot tests)
- Performance standards (< 20 ms ring compute, < 100 ms full pipeline)
- Debugging workflow

**Key Sections:**
- Section 3: Coding Standards
- Section 4: Module Integration Rules ⭐
- Section 6: Testing Strategy
- Section 7: Performance Standards

**Use For:** Onboarding developers implementing N11 bundles

---

#### 11. **RMOS_STUDIO_OPERATIONS_GUIDE.md** (~450 lines) 🆕
**Purpose:** Shop-floor workflow and production procedures  
**Contents:**
- Roles & responsibilities (Designer, Planner, Operator, QA Inspector)
- Required shop equipment specifications
- 5-stage production workflow:
  1. Pattern & Ring Setup
  2. Slice Generation
  3. Manufacturing Plan
  4. Cutting Operations (Saw or CNC)
  5. Assembly & QA
- Operator checklists
- Common errors and prevention strategies
- Quality control procedures

**Key Sections:**
- Section 5–9: Stage-by-Stage Production Workflow ⭐
- Section 8.1: Saw-Based Cutting Mode
- Section 8.1B: CNC-Based Cutting Mode
- Section 9: Assembly & QA Procedures

**Use For:** Defining N11 JobLog structure for production tracking

---

#### 12. **RMOS_STUDIO_USER_MANUAL.md** (~450 lines) 🆕
**Purpose:** End-user operating guide  
**Contents:**
- Interface overview (6-region layout)
- Getting started tutorials
- Column & strip editing workflows
- Preset pattern usage
- Ring configuration procedures
- Tile segmentation preview
- Manufacturing workflow
- Export procedures
- Validation warnings and errors
- Tips for best results

**Key Sections:**
- Section 5: Working With Columns
- Section 6: Using Preset Patterns
- Section 7: Ring Configuration
- Section 10: Manufacturing Workflow ⭐
- Section 12: Validations & Warnings

**Use For:** Designing N11 UI/UX patterns and user workflows

---

#### 13. **RMOS_MASTER_DEVELOPMENT_TRACKER.md** (~450 lines)
**Purpose:** Project checklist and feature tracking  
**Contents:**
- N8–N10 bundle checkboxes
- MM-series analytics tracker
- CI/tooling checklist
- Documentation completeness tracker

**Use For:** Tracking N11 implementation progress

---

## 🗺️ Integration Roadmap

### **N11.0: Rosette Pattern Designer**
**Relevant Specs:**
- `RMOS_STUDIO.md` - UI layout and workflow
- `RMOS_STUDIO_SYSTEM_ARCHITECTURE.md` - Component architecture
- `RMOS_STUDIO_USER_MANUAL.md` - User interaction patterns

**Deliverables:**
- `RosettePatternDesigner.vue` component
- `useRosetteDesignerStore.ts` Pinia store
- `/rmos/rosette-designer` route

---

### **N11.1: Tile Segmentation Engine**
**Relevant Specs:**
- `RMOS_STUDIO_ALGORITHMS.md` - Core math (⭐ Section 4)
- `RMOS_STUDIO_SAW_PIPELINE.md` - Slice generation
- `RMOS_STUDIO_VALIDATION.md` - Geometry validation

**Deliverables:**
- `services/api/app/cam/rosette/tile_segmentation.py`
- `services/api/app/cam/rosette/kerf_compensation.py`
- `services/api/app/cam/rosette/herringbone.py`
- POST `/api/rmos/rosette/segment-ring` endpoint
- POST `/api/rmos/rosette/generate-slices` endpoint

---

### **N11.2: Manufacturing Planner Integration**
**Relevant Specs:**
- `RMOS_STUDIO_MANUFACTURING_PLANNER.md` - Material calculations (⭐ Section 3)
- `RMOS_STUDIO_OPERATIONS_GUIDE.md` - Production workflow
- `RMOS_STUDIO_CNC_EXPORT.md` - Export packaging

**Deliverables:**
- Extend `rmos_analytics_api.py` with rosette material requirements
- POST `/api/rmos/rosette/compute-material-usage` endpoint
- Integration with existing N9 analytics dashboard

---

## 🔍 Key Algorithms Reference

### **Tile Segmentation** (`RMOS_STUDIO_ALGORITHMS.md` Section 4)
```python
# 4.1: Compute circumference
C = 2 * π * radius_mm

# 4.2: Compute tile count
N = floor(C / tile_length_mm)
N = max(2, min(N, 300))  # Constraints

# 4.3: Effective tile length
tile_effective = C / N

# 4.4: Angular bounds
θ_start[i] = (i / N) × 360°
θ_end[i] = θ_start[i] + (360° / N)
```

### **Kerf Compensation** (`RMOS_STUDIO_ALGORITHMS.md` Section 6)
```python
# Angular loss per slice
angle_loss = (kerf_mm / C) × 360°

# Cumulative drift
total_drift = Σ angle_loss[i]

# Adjusted angles
θ_adjusted[i] = θ_raw[i] + total_drift[i]
```

### **Material Requirements** (`RMOS_STUDIO_MANUFACTURING_PLANNER.md` Section 3)
```python
# Strip length per ring
L_ring = 2 × π × radius_mm

# Total requirement with scrap
L_total = L_ring × (1 + scrap_rate)  # scrap_rate = 0.05 default
```

---

## 📐 Data Structure Reference

### **Rosette Pattern Extended Schema**
```python
{
  "pattern_id": str,
  "pattern_type": "rosette",  # NEW
  "geometry": {
    "rings": [
      {
        "ring_id": int,
        "radius_mm": float,
        "width_mm": float,
        "tile_length_mm": float,
        "twist_angle_deg": float,      # NEW (from specs)
        "slice_angle_deg": float,      # NEW (from specs)
        "column": {                    # NEW (from specs)
          "strips": [
            {
              "width_mm": float,
              "color": str,
              "material_id": str,
              "strip_family_id": str
            }
          ]
        }
      }
    ],
    "segmentation": {                  # NEW (from specs)
      "tile_count_total": int,
      "rings": [...]
    }
  }
}
```

---

## ✅ Implementation Checklist

Use this checklist when implementing N11 bundles:

### **Backend Implementation**
- [ ] Create `services/api/app/cam/rosette/` module
- [ ] Implement tile segmentation algorithm (from `RMOS_STUDIO_ALGORITHMS.md` Section 4)
- [ ] Implement kerf compensation (from `RMOS_STUDIO_ALGORITHMS.md` Section 6)
- [ ] Implement herringbone angle calculations
- [ ] Create rosette API router at `/api/rmos/rosette/*`
- [ ] Add validation middleware (from `RMOS_STUDIO_VALIDATION.md`)
- [ ] Extend PatternStore with rosette type detection
- [ ] Add rosette job types to JobLogStore

### **Frontend Implementation**
- [ ] Create `useRosetteDesignerStore.ts` Pinia store
- [ ] Create `RosettePatternDesigner.vue` main component
- [ ] Create `RingConfigPanel.vue` (per-ring parameters)
- [ ] Create `ColumnStripEditor.vue` (vertical column editing)
- [ ] Create `TilePreviewCanvas.vue` (horizontal tile preview)
- [ ] Add route `/rmos/rosette-designer`
- [ ] Integrate with existing RMOS navigation

### **Testing Implementation**
- [ ] Unit tests for tile segmentation math
- [ ] Unit tests for kerf compensation
- [ ] Integration tests for pattern save/load
- [ ] UI component tests
- [ ] End-to-end test: design → save → export → CAM

---

## 🎯 Usage Guidelines

### **For Developers Implementing N11:**
1. Start with `RMOS_N8_N10_ARCHITECTURE.md` to understand current implementation
2. Review `RMOS_STUDIO_ALGORITHMS.md` for core math (tile segmentation, kerf)
3. Use `RMOS_STUDIO_VALIDATION.md` for constraint rules
4. Reference `RMOS_STUDIO_DEVELOPER_GUIDE.md` for coding standards
5. Test against `RMOS_STUDIO_DATA_STRUCTURES.md` schema expectations

### **For UX/UI Designers:**
1. Review `RMOS_STUDIO_USER_MANUAL.md` for workflow patterns
2. Study `RMOS_STUDIO.md` for 6-region UI layout
3. Reference `RMOS_STUDIO_OPERATIONS_GUIDE.md` for shop-floor context

### **For Manufacturing/CAM Engineers:**
1. Study `RMOS_STUDIO_MANUFACTURING_PLANNER.md` for material calculations
2. Review `RMOS_STUDIO_SAW_PIPELINE.md` for slicing workflow
3. Reference `RMOS_STUDIO_CNC_EXPORT.md` for toolpath generation
4. Use `RMOS_STUDIO_OPERATIONS_GUIDE.md` for production procedures

---

## 📚 Related Documentation

**Current RMOS Implementation:**
- `docs/RMOS_N8_N10_ARCHITECTURE.md` - Current N8–N10 architecture
- `docs/RMOS_MASTER_TREE.md` - Development roadmap
- `projects/rmos/ARCHITECTURE.md` - Original RTL design (5-domain model)
- `docs/N9_0_ANALYTICS_QUICKREF.md` - Analytics engine
- `docs/N10_2_APPRENTICESHIP_MODE_QUICKREF.md` - Safety system

**Integration Planning:**
- `.github/copilot-instructions.md` - Coding conventions
- `AGENTS.md` - Agent guidance for this repository
- `CODING_POLICY.md` - Coding standards

---

## 🚀 Quick Start for N11 Implementation

1. **Read the architecture document first:**
   ```
   docs/RMOS_N8_N10_ARCHITECTURE.md
   ```

2. **Implement tile segmentation math:**
   ```python
   # Start with RMOS_STUDIO_ALGORITHMS.md Section 4
   services/api/app/cam/rosette/tile_segmentation.py
   ```

3. **Create rosette API router:**
   ```python
   # Follow patterns in rmos_stores_api.py
   services/api/app/api/routes/rmos_rosette_api.py
   ```

4. **Build UI components:**
   ```vue
   <!-- Follow patterns in MixedMaterialStripFamilyEditor.vue -->
   packages/client/src/components/rmos/RosettePatternDesigner.vue
   ```

5. **Test end-to-end:**
   ```powershell
   # Create test script following test_adaptive_l2.ps1 pattern
   scripts/test_rosette_n11.ps1
   ```

---

## 📝 Document Maintenance

**Last Updated:** November 30, 2025  
**Maintainer:** Luthier's Tool Box Team  
**Review Cycle:** Quarterly or when N11 implementation begins

**Change Log:**
- 2025-11-30: Initial creation with 13 specification documents

---

**Status:** ✅ Complete Specification Suite Archived  
**Next Steps:** Begin N11.0 implementation using this documentation as reference
