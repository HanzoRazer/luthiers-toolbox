# AI Schema and File Namespace Scan Report

**Generated:** 2025-12-15
**Repository:** luthiers-toolbox

---

## Executive Summary

This report documents the AI schema definitions and file namespace organization discovered in the Luthier's Toolbox repository. The project is a comprehensive guitar-building software suite with CNC/CAM integration, featuring an AI-driven rosette manufacturing optimization system (RMOS).

---

## 1. AI Schema Architecture

### 1.1 Core AI Schemas

| File | Location | Purpose |
|------|----------|---------|
| `ai_core_generators.py` | Root | Candidate generator factory for RMOS AI search loops |
| `ai_core_generator_constraints.py` | Root | Constraint definitions for AI generation |
| `ai_graphics_schemas.py` | Root | AI graphics schema definitions (bundle documentation) |
| `ai_graphics_schemas_ai_schemas.py` | Root | Extended AI schema models |
| `ai_graphics_sessions.py` | Root | AI session management |
| `ai_rmos_constraint_profiles.yaml` | Root | YAML constraint profiles for AI |
| `ai_rmos_generator_snapshot.py` | Root | Generator snapshot utilities |
| `constraint_profiles_ai.py` | Root | Python constraint profile definitions |

### 1.2 AI Schema Models (Pydantic)

The AI system uses structured Pydantic models for:

```
AiRosettePromptInput      - Natural language rosette prompts
AiRingSummary             - Per-ring feasibility summary
AiFeasibilitySnapshot     - RMOS feasibility scoring
AiRosetteSuggestion       - Full AI suggestion with params + feasibility
AiRosetteSuggestionBatch  - Batch of ranked suggestions
RosetteParamSpec          - Parametric rosette design specification
RmosContext               - Material/tool/machine context
SearchBudgetSpec          - Search loop constraints (attempts, time, scores)
```

### 1.3 AI Generator Pipeline

```
LLM Prompt --> Raw Candidates --> RMOS Evaluation --> Ring Diagnostics
     |                                    |
     v                                    v
Refinement Loop <-- Ring-Aware Mutation <-- Score Below Target
     |
     v
Final Ranked Suggestions (sorted by ai_score)
```

---

## 2. Data Registry Schema System

### 2.1 Master Schema Location
`services/api/app/data_registry/schemas/all_schemas.json`

### 2.2 Registered Schema Domains

| Domain | Description | Key Properties |
|--------|-------------|----------------|
| **tools** | CNC tool library | id, name, type, diameter_mm, flutes, material, chipload |
| **machines** | Machine profiles | id, name, work_envelope (x,y,z), spindle (rpm, power) |
| **materials** | Wood species | id, name, janka_hardness, density_kg_m3 |
| **empirical** | Machining limits | chipload_multiplier, feed_clamp (roughing, finishing, plunge) |
| **instruments** | Guitar geometry | bodies, profiles, scales |
| **references** | Reference data | scales, formulas |

### 2.3 Instrument Schema (Detailed)

Location: `assets_staging/packages/registry_extracted/data/instruments/_schema.json`

```json
{
  "type": ["solid_body_electric", "semi_hollow", "hollow_body",
           "acoustic_dreadnought", "acoustic_jumbo", "acoustic_concert",
           "acoustic_parlor", "classical", "bass"],
  "dimensions": {
    "body_length_mm", "body_width_mm", "body_thickness_mm",
    "upper_bout_mm", "lower_bout_mm", "waist_mm",
    "scale_length_mm", "scale_length_inches"
  },
  "features": {
    "neck_pocket", "pickup_cavities", "control_cavity",
    "tremolo_cavity", "arm_contour", "belly_contour"
  }
}
```

---

## 3. File Namespace Structure

### 3.1 Primary Service Namespace
```
services/
└── api/
    └── app/
        ├── data_registry/           # Central data registry
        │   ├── schemas/             # JSON Schema definitions
        │   ├── system/              # System-level data
        │   │   ├── instruments/     # Body templates, neck profiles
        │   │   ├── materials/       # Wood species
        │   │   ├── tools/           # Router bits
        │   │   └── references/      # Scale lengths, fret formulas
        │   └── edition/             # Edition-specific data
        │       ├── pro/             # Pro edition features
        │       ├── parametric/      # Parametric templates
        │       ├── neck_designer/
        │       ├── headstock_designer/
        │       ├── bridge_designer/
        │       ├── fingerboard_designer/
        │       └── cnc_blueprints/
        ├── data/posts/              # CNC post processors
        │   ├── grbl.json
        │   ├── mach4.json
        │   ├── pathpilot.json
        │   ├── linuxcnc.json
        │   └── masso.json
        └── assets/                  # Asset files
```

### 3.2 Module-Specific Schemas

| Module | Schema Files |
|--------|-------------|
| **WiringWorkbench** | `wiring_diagram.schema.json`, `component_library.schema.json` |
| **FinishPlanner** | `finish_schedule.schema.json`, `finish_material.schema.json` |
| **MVP Bracing** | `bracing_schema.json` |
| **MVP Hardware** | `hardware_schema.json` |
| **OM Project** | `schema.json` |

### 3.3 Legacy/Staging Namespaces

Multiple version snapshots exist:
- `ToolBox_All_Scripts_Consolidated_v2` through `v7`
- `ToolBox_Patch_N*` series (N0 through N12+)
- `files (17)` through `files (51)` extraction folders
- `Luthiers Tool Box/MVP Build_*` dated builds

---

## 4. Schema Validation Summary

### 4.1 JSON Schema Standards
- Draft-07 compliance for instrument schemas
- Custom validation for domain-specific constraints
- Type enums for categorical data (tool types, instrument types)

### 4.2 Tool Type Enums
```
flat_endmill, ball_endmill, upcut_spiral, downcut_spiral,
compression, v_bit, drill
```

### 4.3 Material Enums
```
carbide, hss, cobalt
```

---

## 5. AI Integration Points

### 5.1 RMOS (Rosette Manufacturing OS) Integration

The AI system integrates with RMOS through:
1. **Context Building** - `_build_context_for_ai()` creates RmosContext from presets
2. **Feasibility Scoring** - `compute_feasibility()` evaluates designs
3. **Ring Diagnostics** - Per-ring risk assessment (GREEN/YELLOW/RED)
4. **Mutation Engine** - `_mutate_design_from_feasibility()` improves designs

### 5.2 Safety Constraints

AI generation is bounded by:
- Ring width vs tool diameter ratios
- Material-specific chipload multipliers
- Feed rate clamps (roughing, finishing, plunge)
- Global policy caps via `apply_global_policy_to_constraints()`

---

## 6. Recommendations

1. **Schema Consolidation** - Multiple schema locations should be unified under `services/api/app/data_registry/schemas/`

2. **Legacy Cleanup** - Consider archiving `ToolBox_*` and `files (*)` staging directories

3. **AI Schema Documentation** - The Pydantic models in `ai_graphics_schemas.py` should be extracted into proper module structure

4. **Version Control** - Schema versioning via `_meta.version` should be enforced across all data files

---

## 7. File Counts by Category

| Category | Count |
|----------|-------|
| Schema Files (`*.schema.json`) | 7 |
| AI Python Modules | 8 |
| Data Registry JSON | 40+ |
| Post Processor Configs | 5 |
| Total JSON Files | 100+ |

---

*Report generated by Claude Code AI Schema Scanner*
