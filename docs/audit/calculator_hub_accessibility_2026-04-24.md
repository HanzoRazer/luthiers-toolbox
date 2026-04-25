# Calculator Hub Accessibility Checklist
**Date**: 2026-04-24
**Sprint**: Calculator Module Restoration Phase 3

## Summary

This checklist documents the accessibility status of all Vue calculator components relative to the Calculator Hub. Components are classified by their current state and Hub integration status.

---

## Hub-Integrated Components (Tier 1)

| Component | File | Hub ID | Status | Notes |
|-----------|------|--------|--------|-------|
| ScientificCalculator | `toolbox/ScientificCalculator.vue` | `scientific` | **Ready** | Contains Woodwork tab (legacy location) |
| BusinessCalculator | `toolbox/BusinessCalculator.vue` | `business-calc` | **Ready** | Costing, pricing, cash flow |
| SoundholeCalculator | `views/calculators/acoustics/SoundholeCalculator.vue` | `soundhole` | **Ready** | Helmholtz + P:A ratio |
| TensionCalculator | `toolbox/TensionCalculator.vue` | `tension` | **Ready** | Wired 2026-04-24 |
| WoodworkingCalculator | `toolbox/WoodworkingCalculator.vue` | `woodworking` | **Ready** | Wired 2026-04-24 |
| RadiusDishCalculator | `toolbox/radius-dish/RadiusDishCalculator.vue` | `radius-dish` | **Ready** | Wired 2026-04-25 |
| ArchtopCalculator | `toolbox/ArchtopCalculator.vue` | `archtop` | **Ready** | Wired 2026-04-25 |
| BridgeCalculator | `toolbox/BridgeCalculator.vue` | `bridge` | **Ready** | Wired 2026-04-25 |
| FractionCalculator | `toolbox/FractionCalculator.vue` | `fractions` | **Placeholder** | Stub only |
| CNCROICalculator | `toolbox/CNCROICalculator.vue` | `cnc-roi` | **Placeholder** | Stub only |

### Route-Based (navigateTo pattern)
| Component | Route | Status |
|-----------|-------|--------|
| Spiral Soundhole Designer | `/calculators/acoustics/spiral-soundhole` | **Ready** |

---

## Candidates for Hub Integration (Tier 2 Promotion)

All priority candidates have been integrated. Remaining candidates require implementation work first (see Stub/Placeholder section).

---

## Stub/Placeholder Components

These need implementation before Hub promotion:

| Component | File | State | Notes |
|-----------|------|-------|-------|
| FractionCalculator | `toolbox/FractionCalculator.vue` | Stub | "Under development" message |
| CNCROICalculator | `toolbox/CNCROICalculator.vue` | Stub | "Under development" message |
| BracingCalculator | `toolbox/BracingCalculator.vue` | Stub | "Implementation in progress" |

---

## Sub-Components (Internal/Composition)

These are building blocks, not standalone calculators:

| Component | File | Used By |
|-----------|------|---------|
| BasicCalculatorPad | `toolbox/calculator/BasicCalculatorPad.vue` | ScientificCalculator |
| ScientificCalculatorPad | `toolbox/calculator/ScientificCalculatorPad.vue` | ScientificCalculator |
| CalculatorDisplay | `toolbox/calculator/CalculatorDisplay.vue` | ScientificCalculator |
| UnitConverterPanel | `toolbox/calculator/UnitConverterPanel.vue` | ScientificCalculator |
| WoodworkPanel | `toolbox/calculator/WoodworkPanel.vue` | ScientificCalculator, WoodworkingCalculator |
| TensionCalculatorPanel | `toolbox/scale-length/TensionCalculatorPanel.vue` | TensionCalculator |

---

## Duplicate/Legacy Components

| Component | File | Status | Action |
|-----------|------|--------|--------|
| ScientificCalculatorV2 | `toolbox/ScientificCalculatorV2.vue` | Unknown | Verify if in use, consolidate |
| CalculatorHub (design-utilities) | `design-utilities/CalculatorHub.vue` | Duplicate | Verify routing, consolidate |
| ScientificCalculator (design-utilities/lutherie) | `design-utilities/lutherie/ScientificCalculator.vue` | Duplicate | Consolidate |
| ScientificCalculator (design-utilities/scientific) | `design-utilities/scientific/ScientificCalculator.vue` | Duplicate | Consolidate |

---

## Phase 3 Execution Completed

### Stream A: Calculator Hub Quick Wins (2026-04-25)
1. **TensionCalculatorPanel wired** - Created `TensionCalculator.vue` wrapper, added to Hub under "Lutherie" category
2. **WoodworkPanel extracted** - Created `WoodworkingCalculator.vue` wrapper, added to Hub under "Woodworking" category
3. **ArchtopCalculator wired** - Direct integration (self-contained), added to Hub under "Lutherie" category
4. **BridgeCalculator wired** - Direct integration (self-contained), added to Hub under "Lutherie" category
5. **RadiusDishCalculator wired** - Direct integration (self-contained), added to Hub under "Woodworking" category

### Stream B: Saw Lab Migration (2026-04-25)
1. **Saw adapters copied** to `ltb-woodworking-studio/woodworking_v2/services/api/app/calculators/saw/`
2. **Core safety module** created at `ltb-woodworking-studio/.../app/core/safety.py`
3. **Compatibility shim** added to `luthiers-toolbox/.../saw_adapters/__init__.py` (imports from woodworking-studio when available, falls back to local)
4. **Both repos verified** - imports work in both luthiers-toolbox (fallback) and ltb-woodworking-studio (canonical)

---

## Calculator Hub Final State (5 Categories, 10 Calculators)

| Category | Calculators |
|----------|-------------|
| Math & Precision | Scientific (ready), Fraction (placeholder) |
| Business & ROI | Business (ready), CNC ROI (placeholder) |
| Woodworking | Woodworking (ready), Radius Dish (ready) |
| Acoustics | Soundhole (ready), Spiral Soundhole (route) |
| Lutherie | Tension (ready), Archtop (ready), Bridge (ready) |

---

## Next Steps (Phase 3 Continued)

1. **Implement FractionCalculator** or remove from Hub grid
2. **Implement CNCROICalculator** or remove from Hub grid
3. **Consolidate duplicate ScientificCalculator** files
4. **Build UI wrappers** for bridges-to-nowhere (Finish, Glue Joint, Tuning, Electronics, Switch)
5. **Complete Saw Lab migration** - add ltb-woodworking-studio as build dependency, remove local saw_adapters files
