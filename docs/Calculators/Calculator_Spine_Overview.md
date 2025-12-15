# 📘 Calculator Spine Overview

**Luthier's ToolBox — Unified Calculator Architecture**

| Version | Audience |
|---------|----------|
| 1.0 | Backend developers, RMOS 2.0 contributors, Saw Lab maintainers, Art Studio integrators |

---

## 1. 🎯 Purpose of the Calculator Spine

The **Calculator Spine** is the single source of truth for all technical, mathematical, physics-based, or domain-specific computations in the Luthier's ToolBox ecosystem.

Before Wave 8–9, calculators were scattered across:

- `server/pipelines/`
- Legacy Art Studio folders
- Saw Lab scratch space
- Front-end TypeScript utilities
- RMOS feasibility logic
- Inline code inside routers
- Untracked documents & sandbox sessions

This fragmentation caused:

- ❌ Loss of critical algorithms
- ❌ Inconsistency between components
- ❌ Hard-to-reproduce results
- ❌ Difficulty training GitHub Copilot or AI agents
- ❌ Breakage when migrating to new architectures (RMOS 2.0, Art Studio 2.0)

**The Calculator Spine solves this.**

---

## 2. 🧠 What the Calculator Spine Is

A backend-centered, highly structured directory + API that:

- ✔ Centralizes calculators from all subsystems
- ✔ Exposes clean façade functions (via `calculator_service`)
- ✔ Feeds RMOS feasibility models
- ✔ Powers Art Studio risk overlays (Wave 9)
- ✔ Feeds the Saw Lab physics engine
- ✔ Supplies instrument geometry to UI and toolpath generators
- ✔ Keeps frontend math simple, backend math canonical

**Every important calculation must pass through this spine.**

---

## 3. 🗂 Directory Structure (Authoritative)

This directory is located at:

```
services/api/app/calculators/
```

And contains the following structure:

```
calculators/
│
├── __init__.py
├── service.py                        # Central façade — called by all subsystems
│
├── physics/                          # Router-bit & general cutting physics
│   ├── __init__.py
│   ├── chipload.py
│   ├── heat.py
│   ├── deflection.py
│   ├── rim_speed.py
│   └── engagement.py                 # Optional (radial/axial engagement factors)
│
├── instrument/                       # Guitar geometry (delegates to instrument_geometry/)
│   ├── __init__.py
│   └── ... (adapters to instrument_geometry package)
│
├── saw/                              # Saw Lab integration layer
│   ├── __init__.py
│   ├── bite_per_tooth_adapter.py
│   ├── heat_adapter.py
│   ├── deflection_adapter.py
│   ├── rim_speed_adapter.py
│   └── kickback_adapter.py
│
├── wiring/                           # Electronics calculators
│   ├── __init__.py
│   ├── treble_bleed.py
│   ├── switch_validator.py
│   └── impedance_math.py
│
└── business/                         # ROI & financial calculators
    ├── __init__.py
    ├── roi.py
    ├── amortization.py
    └── machine_throughput.py
```

**Plus:**

```
services/api/app/routers/
└── calculators_router.py             # FastAPI endpoints for calculator access

services/api/app/tests/calculators/
├── __init__.py
├── test_service_basic.py
├── test_physics_chipload.py
├── test_saw_adapters.py
├── test_wiring.py
└── test_business_roi.py
```

---

## 4. 🧩 Calculator Spine: Layer Overview

The Spine operates in four internal layers:

### 4.1 ⭐ Layer A — Calculator Façade (`service.py`)

All subsystems call this file instead of calling calculators directly.

It provides:

| Function | Purpose |
|----------|---------|
| `evaluate_cut_operation()` | Unified router-bit + saw-blade interface |
| `evaluate_string_spacing()` | String spacing calculations |
| `evaluate_scale_length()` | Scale length and fret positions |
| `evaluate_fretboard_outline()` | Fretboard geometry |
| `evaluate_roi()` | Business ROI calculations |
| `compute_switch_validation()` | Wiring circuit validation |

**Every calculator call should pass through the façade.**

### 4.2 ⭐ Layer B — Physics Calculators

These compute physical machining phenomena:

| Calculator | Purpose |
|------------|---------|
| Chipload | `feed / (rpm × flutes)` |
| Heat generation | Thermal risk from friction |
| Deflection | Tool deflection under load |
| Rim speed | Surface velocity of rotating tools |
| Tool engagement | Radial/axial engagement factors |
| Kickback risk | (via saw adapters) |

**These feed:**
- RMOS feasibility scoring
- Art Studio Wave 9 risk overlays
- Saw Lab physics debug views
- Toolpath planners

### 4.3 ⭐ Layer C — Instrument Geometry Calculators

These compute lutherie math essential to guitar design:

| Calculator | Purpose |
|------------|---------|
| Scale length | Fret positions (12th-root-of-2 or historical models) |
| String spacing | Linear, compensated, multi-scale |
| Bridge location | Compensation, action height |
| Radius profiles | Compound or fixed radii |
| Bracing | Mass & stiffness estimates |

**These feed:**
- Art Studio instrument CAD panels
- RMOS toolpath generation
- Manufacturing geometry (DXF export)

> **Note:** Instrument geometry is implemented in `app/instrument_geometry/` package. The `calculators/instrument/` directory contains adapters to that package.

### 4.4 ⭐ Layer D — Domain-Specific Calculators

#### Saw Lab
Adapts Saw Lab 2.0 physics models into the Spine.

#### Wiring
Calculates:
- Treble bleed resistor/capacitor values
- Pot/tone network impedance
- Valid switch configurations

#### Business / ROI
Provides:
- CNC amortization
- Shop throughput modeling
- Material cost analysis

---

## 5. 🔌 How Subsystems Connect to the Spine

| Subsystem | Calls Spine For | Functions Used |
|-----------|-----------------|----------------|
| **RMOS 2.0** | Feasibility | `evaluate_cut_operation`, instrument methods |
| **Art Studio 2.0** | Geometry preview, risk overlay | `evaluate_cut_operation`, instrument geometry |
| **Saw Lab 2.0** | Physics adapters | Calls physics calculators directly |
| **Toolpath Engine** | Engagement factors, deflection | chipload, deflection |
| **DXF Export** | Geometry precision | instrument geometry |
| **Wiring Workbench** | Circuit math | `treble_bleed`, `switch_validator` |
| **ROI Dashboard** | Finances | `roi.evaluate_roi()` |

---

## 6. 🛠 APIs Exposed to the Front-End

The following FastAPI routers mirror the calculator façade:

```
/api/calculators/evaluate-cut
/api/calculators/string-spacing
/api/calculators/fret-positions
/api/calculators/fretboard
/api/calculators/bridge
/api/calculators/radius-profile
/api/calculators/roi
/api/calculators/wiring/*
```

This ensures:
- Art Studio stays thin
- All math is backend source-of-truth
- Copilot can reason about a consistent API

---

## 7. 🔒 Safety & Consistency Rules

### Rule 1 — Calculators MUST NOT live in UI

Simple helpers (such as inch→mm) are OK, but all lutherie math must live in Python.

### Rule 2 — Every subsystem MUST use `service.py`

No backdoor imports into physics calculators.

### Rule 3 — All calculators MUST be unit-testable

Every calculator module must have a corresponding test file:

```
tests/calculators/test_scale_length.py
tests/calculators/test_chipload.py
tests/calculators/test_rim_speed.py
...
```

### Rule 4 — All tool/material data comes from Tool Library

Never hardcode:
- chipload ranges
- max RPM
- kerf
- flute count

### Rule 5 — Every calculator must document assumptions

Inside each calculator, include:

```python
# MODEL NOTES:
# - Assumes perfectly sharp tool
# - Assumes dry cutting (Air)
# - Assumes 2-flute bit unless OVERRIDE
```

---

## 8. 🧬 RMOS Feasibility + Calculator Spine

RMOS feasibility works like this:

```
Design → geometry engine → (paths)
        → for each toolpath:
            → CutOperationSpec
            → evaluate_cut_operation()
            → collect:
                chipload
                heat
                deflection
                rim-speed (if saw)
                kickback (if saw)
        → overall score
        → per-path risk map (Wave 9)
        → Art Studio overlays
```

This is why the calculator spine exists — without centralized, consistent physics/math, RMOS cannot meaningfully score a design.

---

## 9. 🔎 Migration Status

### ✔ Already migrated or scaffolded

- Saw Lab calculators (Wave 7–8)
- Feasibility façade
- Tool Library
- Instrument Geometry package (`instrument_geometry/`)
- ROI calculators (identified)

### ⚠ Requires migration into Calculator Spine

- Rosette calculators
- Bracing calculators
- String spacing calculators
- Existing front-end math in TS
- Legacy Art Studio geometry helpers
- Wiring & treble bleed
- Blocked-off calculators in `server/pipelines/`

### ❌ Missing entirely in repo

- Some router-bit geometry calculators
- Some saw-blade technical models (but you have local copies)
- Several missing instrument geometry scripts (confirmed)

---

## 10. 📜 Developer Workflow Using the Calculator Spine

When a developer needs a calculation:

### 1) They never import modules directly

❌ **Wrong:**
```python
from app.saw_lab.calculators.deflection_model import compute_deflection
```

✅ **Correct:**
```python
from app.calculators.service import evaluate_cut_operation
```

### 2) They create a `CutOperationSpec` or instrument-specific request

Then call the façade.

### 3) They get a structured result for RMOS, UI, or debugging.

### 4) They optionally inspect raw calculators for debugging only.

---

## 11. 🏁 Next Steps

| Step | Action |
|------|--------|
| **1** | Move remaining calculators into `calculators/` |
| **2** | Write unit tests for each module |
| **3** | Update RMOS feasibility to return path-level risk |
| **4** | Remove all duplicate or legacy calculators |
| **5** | Merge Saw Lab 2.0 adapters fully |

---

## 12. ✔ Summary

The Calculator Spine ensures:

- ✅ One location for all math and physics
- ✅ One API surface for RMOS, Art Studio, and Saw Lab
- ✅ Long-term maintainability
- ✅ Consistent manufacturing outcomes
- ✅ Prevents knowledge loss across patches and sandboxes

**It is the central nervous system for all manufacturing logic in the Luthier's ToolBox.**

---

## 📚 See Also

- [Instrument Geometry Package](../../services/api/app/instrument_geometry/README.md)
- [Saw Lab 2.0 Overview](../SawLab/SAW_LAB_OVERVIEW.md)
- [RMOS Feasibility System](../RMOS/FEASIBILITY.md)
- [Art Studio Wave 9 - Risk Overlay](../ArtStudio/Wave_9_Feasibility_Overlay.md)
