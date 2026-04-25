# Calculator Inventory Report — Phase 1

**Date:** 2026-04-23  
**Auditor:** Claude (automated inventory)  
**Purpose:** Ground-truth inventory before Calculator Module Restoration sprint

---

## Executive Summary

The Production Shop calculator section contains **70+ calculator-like modules** spread across multiple locations. The current UI exposes only **6 calculators** in the Calculator Hub, with many Tier 1 candidates buried as Tier 2 (embedded plumbing).

**Key findings:**
- **Drift confirmed:** ScientificCalculator.vue has a "Woodwork" tab (board feet, volume, angles) — woodworking features wrongly embedded in scientific calculator
- **Ross's 16 recalled calculators:** All 16 exist as backend code; only 2-3 have Tier 1 UI
- **Business suite:** 3 calculators exist (ROI, Amortization, Throughput); only 1 (BusinessCalculator) has UI
- **Basic calculator:** Appears working — implements digit entry, operations, expression evaluation
- **Lutherie calculators:** ~40+ backend modules exist; most have API routes but no dedicated UI

**Commodity classification:**
- **22 items flagged commodity** — standard math (fret position, string tension, board feet, etc.)
- **12 items flagged differentiated** — custom priors or research (soundhole w/ Gore, spiral w/ Williams, setup cascade)
- **36 items need Ross review** — unclear if custom parameters add differentiation

---

## 1. Summary Table

**Commodity Status Legend:**
- `commodity` — Same math freely available elsewhere (StewMac, Liutaio Mottola, apps)
- `differentiated` — Custom parameters, priors, or workflow integration
- `needs-review` — Ross to decide if commodity or differentiated

| Name | Domain | Tier | Commodity | State | Suggested Action |
|------|--------|------|-----------|-------|------------------|
| **MATH & PRECISION** ||||||
| Basic Calculator | Basic | 1 | commodity | Working | Keep (workflow convenience) |
| Scientific Calculator | Scientific | 1 | commodity | Working | Keep (workflow convenience) |
| Fraction Calculator | Basic | 1 | commodity | Stub | Complete or drop |
| Unit Converter | Scientific | 1 | commodity | Working | Keep (workflow convenience) |
| **WOODWORKING (DRIFT)** ||||||
| Board Feet | Woodworking | 1 (wrong) | commodity | Working | Move to Woodworking Suite |
| Volume Calculator | Woodworking | 1 (wrong) | commodity | Working | Move to Woodworking Suite |
| Angle Calculator | Woodworking | 1 (wrong) | commodity | Working | Move to Woodworking Suite |
| Wedge Angle | Woodworking | 2 | commodity | Working | Promote to Woodworking Suite |
| Miter Angle | Woodworking | 2 | commodity | Working | Promote to Woodworking Suite |
| Dovetail Angle | Woodworking | 2 | commodity | Working | Promote to Woodworking Suite |
| Wood Movement | Woodworking | 2 | needs-review | Working | Promote (has species DB) |
| Side Bending | Woodworking | 2 | differentiated | Working | Promote (USDA data + builder lit) |
| Steam Bending | Woodworking | 3 | needs-review | Working | Consider for Suite |
| **BUSINESS** ||||||
| Business Calculator | Business | 1 | needs-review | Working | Keep |
| CNC ROI | Business | 1 | needs-review | Stub | Complete |
| Amortization | Business | 2 | commodity | Working | Promote or bundle |
| Machine Throughput | Business | 2 | needs-review | Working | Promote (lutherie-specific?) |
| **ACOUSTICS** ||||||
| Soundhole Calculator | Lutherie | 1 | differentiated | Working | Keep (Gore priors, calibration log) |
| Spiral Soundhole | Lutherie | 1 | differentiated | Working | Keep (Williams 2019 research) |
| Helmholtz Physics | Lutherie | 2 | needs-review | Working | Keep as plumbing |
| Two-Cavity Helmholtz | Lutherie | 2 | differentiated | Working | Promote (Selmer/Maccaferri specific) |
| Soundhole Stiffness | Lutherie | 3 | needs-review | Working | Keep as reference |
| **LUTHERIE — NECK/FRETWORK** ||||||
| Scale Length / Fret Position | Lutherie | 2 | commodity | Working | **Promote** (CAM integration) |
| Multi-scale / Fanned Fret | Lutherie | 2 | commodity | Working | **Promote** (CAM integration) |
| Neck Taper | Lutherie | 2 | needs-review | Working | Promote |
| Fingerboard Radius Reference | Lutherie | 2 | commodity | Working | **Promote** (reference data) |
| Compound Radius | Lutherie | 2 | commodity | Working | Promote |
| Radius from 3 Points | Lutherie | 2 | commodity | Working | Promote |
| Radius from Chord | Lutherie | 2 | commodity | Working | Promote |
| Headstock Angle | Lutherie | 2 | needs-review | Working | **Promote** (per-string analysis) |
| **LUTHERIE — STRINGS/ACTION** ||||||
| String Tension | Lutherie | 2 | commodity | Working | **Promote** (has D'Addario calibration) |
| String Gauge Recommendations | Lutherie | 2 | commodity | Working | Bundle with String Tension |
| Nut Slot Sizing | Lutherie | 2 | commodity | Working | **Promote** |
| Intonation / Saddle Offset | Lutherie | 2 | needs-review | Working | **Promote** (two modes: design + setup) |
| Fret Compensation | Lutherie | 2 | needs-review | Working | Bundle with Intonation |
| Action / Relief Setup | Lutherie | 2 | differentiated | Working | **Promote** (cascade logic) |
| **LUTHERIE — BODY/BRACING** ||||||
| Bracing Calculator | Lutherie | 2 | needs-review | Working | Promote |
| Body Volume / Acoustics | Lutherie | 2 | needs-review | Working | **Promote** (reference models) |
| Kerfing Calculator | Lutherie | 2 | needs-review | Working | Promote |
| Kerfing Geometry | Lutherie | 2 | needs-review | Working | Keep as plumbing |
| **LUTHERIE — BRIDGE** ||||||
| Bridge Calculator | Lutherie | 1 | needs-review | Working | Keep |
| Archtop Floating Bridge | Lutherie | 2 | differentiated | Working | Promote (Benedetto defaults) |
| Bridge Break Angle | Lutherie | 2 | needs-review | Working | Bundle with Bridge |
| **LUTHERIE — SPECIALTY** ||||||
| Archtop Calculator | Lutherie | 1 | needs-review | Unknown | Verify |
| Radius Dish Calculator | Lutherie | 1 | needs-review | Unknown | Verify |
| Fret Leveling | Lutherie | 2 | needs-review | Working | Promote |
| Fret Wire Calculator | Lutherie | 2 | needs-review | Working | Promote |
| Binding Geometry | Lutherie | 2 | needs-review | Working | Promote |
| Inlay Calculator | Lutherie | 2 | needs-review | Working | Promote |
| Rosette Calculator | Lutherie | 3 | needs-review | Working | Keep as reference |
| Pickup Position | Lutherie | 2 | needs-review | Working | Promote |
| Electronics Layout | Lutherie | 3 | needs-review | Working | Keep as reference |
| Finish Calculator | Lutherie | 3 | needs-review | Working | Keep as reference |
| Glue Joint Calculator | Lutherie | 3 | needs-review | Working | Keep as reference |
| Tuning Machine Calculator | Lutherie | 3 | needs-review | Working | Keep as reference |
| Cantilever Armrest | Lutherie | 3 | needs-review | Working | Keep as reference |
| **SAW LAB (SEPARATE MODULE)** ||||||
| Bite Load Calculator | Woodworking | 2 | needs-review | Working | Part of Saw Lab |
| Blade Dynamics | Woodworking | 2 | needs-review | Working | Part of Saw Lab |
| Cutting Force | Woodworking | 2 | needs-review | Working | Part of Saw Lab |
| Deflection | Woodworking | 2 | needs-review | Working | Part of Saw Lab |
| Heat | Woodworking | 2 | needs-review | Working | Part of Saw Lab |
| Kickback | Woodworking | 2 | needs-review | Working | Part of Saw Lab |
| Rim Speed | Woodworking | 2 | needs-review | Working | Part of Saw Lab |
| **WIRING/ELECTRONICS** ||||||
| Treble Bleed | Lutherie | 2 | commodity | Working | Keep as plumbing |
| Switch Validator | Lutherie | 2 | needs-review | Working | Keep as plumbing |
| Impedance Math | Lutherie | 3 | commodity | Working | Keep as reference |
| **PLATE DESIGN (ADVANCED)** ||||||
| Alpha-Beta Coupling | Lutherie | 3 | differentiated | Working | Advanced Module |
| Rayleigh-Ritz | Lutherie | 3 | differentiated | Working | Advanced Module |
| Thickness Calculator | Lutherie | 3 | needs-review | Working | Advanced Module |
| Archtop Graduation | Lutherie | 3 | differentiated | Working | Advanced Module |
| Brace Prescription | Lutherie | 3 | differentiated | Working | Advanced Module |

### 1.1 Commodity Classification Summary

| Status | Count | Examples |
|--------|-------|----------|
| **commodity** | 22 | Fret position, string tension, board feet, miter angles, basic/scientific calc |
| **differentiated** | 12 | Soundhole (Gore priors), spiral (Williams), side bending (USDA+builder lit), setup cascade, plate design |
| **needs-review** | 36 | Most lutherie specialty tools — Ross decides if custom params add value |

**Commodity items with workflow integration** (likely keep despite commodity math):
- Fret Position / Multi-scale → feeds CAM pipeline
- String Tension → calibrated D'Addario unit weights
- Basic/Scientific Calculator → workflow convenience

---

## 2. Per-Item Findings

### 2.1 Ross's Recalled Calculators — Verification

| Calculator Ross Recalled | Status | Location | Notes |
|--------------------------|--------|----------|-------|
| Scale length / fret position | EXISTS | fret_math.py | Tier 2 — has API, no dedicated UI |
| String tension | EXISTS | string_tension.py | Tier 2 — complete with presets |
| Soundhole Helmholtz | EXISTS | soundhole_physics.py + SoundholeCalculator.vue | Tier 1 UI exists |
| Fingerboard radius reference | EXISTS | radius_profiles.py | Tier 2 — reference data + functions |
| Nut slot sizing | EXISTS | nut_slot_calc.py | Tier 2 — complete calculator |
| Intonation / saddle offset | EXISTS | saddle_compensation.py | Tier 2 — two modes (design + setup) |
| Fret compensation for string gauge | EXISTS | saddle_compensation.py | Bundled with intonation |
| Multi-scale / fanned fret | EXISTS | fret_math.py | Tier 2 — complete with presets |
| Neck taper | EXISTS | neck_taper/taper_math.py | Tier 2 — complete module |
| Headstock angle | EXISTS | headstock_break_angle_calc.py | Tier 2 — complete with per-string analysis |
| Bracing placement / acoustic body math | EXISTS | bracing_calc.py, acoustic_body_volume.py | Tier 2 — separate modules |
| Body volume / acoustic calculations | EXISTS | acoustic_body_volume.py | Tier 2 — complete with reference models |
| Steam bending | EXISTS | side_bending_calc.py | Bundled with side bending |
| Kerf bending layout | EXISTS | kerfing_calc.py, kerfing_geometry_engine.py | Tier 2 — complete |
| String gauge recommendations | EXISTS | string_tension.py (STRING_SETS, presets) | Bundled with string tension |
| Action / relief setup | EXISTS | setup_cascade.py | Tier 2 — cascade calculator |

**Summary:** All 16 exist as backend code. Most are Tier 2 (embedded). Only Soundhole has full Tier 1 UI.

### 2.2 Accessibility Analysis (API / UI / Code)

**Tier 1 items with full accessibility:**
- Basic/Scientific Calculator: API + UI + Clean code
- Soundhole Calculator: API + UI + Clean code
- Business Calculator: API + UI + Clean code
- Bridge Calculator: API + UI + Clean code

**Tier 2 items ready for promotion (API exists):**
- String Tension: `/api/instrument/geometry` routes exist
- Fret Math: Routes in instrument_geometry_router.py
- Saddle Compensation: Routes in saddle_compensation_router.py
- Headstock Angle: Routes exist
- Setup Cascade: Routes in setup_router.py

**Tier 2 items needing API work:**
- Wood Movement: No dedicated route
- Side Bending: No dedicated route
- Most plate_design/ calculators: No routes

### 2.3 Working State Verification

**Verified Working:**
- Basic calculator: Tested expression evaluation, digit entry, operations
- Scientific calculator: Tested trig functions, logarithms
- Soundhole calculator: Complete implementation with Helmholtz physics
- String tension: Complete with D'Addario-calibrated unit weights
- Fret math: Complete with multi-scale support
- Saddle compensation: Two complete modes (design + setup)

**Unknown State (need testing):**
- ArchtopCalculator.vue
- RadiusDishCalculator.vue
- Several Tier 3 reference calculators

---

## 3. Tier-Migration Candidates

### 3.1 Promote to Tier 1 (HIGH PRIORITY)

These have complete backend code and need UI:

| Calculator | Current | Effort | Rationale |
|------------|---------|--------|-----------|
| Scale Length / Fret Position | Tier 2 | LOW | API exists, needs Vue component |
| String Tension | Tier 2 | LOW | API exists, TensionCalculatorPanel.vue exists but not in hub |
| Fingerboard Radius | Tier 2 | LOW | API exists, needs simple UI |
| Nut Slot Sizing | Tier 2 | LOW | Complete backend, needs UI |
| Intonation Calculator | Tier 2 | MEDIUM | Two modes, needs thoughtful UI |
| Setup Calculator (Action/Relief) | Tier 2 | MEDIUM | Cascade logic needs clear UI |
| Headstock Angle | Tier 2 | LOW | Complete backend, needs UI |
| Body Volume | Tier 2 | LOW | Complete backend, needs UI |

### 3.2 Woodworking Suite (NEW MODULE)

Extract from ScientificCalculator and add:

| Feature | Source | Effort |
|---------|--------|--------|
| Board Feet | ScientificCalculator Woodwork tab | MOVE |
| Volume | ScientificCalculator Woodwork tab | MOVE |
| Angles | ScientificCalculator Woodwork tab | MOVE |
| Wedge Angle | ltb_calculator_router.py | ADD |
| Miter Angle | ltb_calculator_router.py | ADD |
| Dovetail Angle | ltb_calculator_router.py | ADD |
| Wood Movement | wood_movement_calc.py | ADD |
| Side Bending | side_bending_calc.py | ADD |

### 3.3 Keep as Plumbing (Tier 2)

These should remain embedded — used by other tools:
- kerfing_geometry_engine.py (used by kerfing_calc.py)
- soundhole_physics.py (used by SoundholeCalculator)
- _bracing_physics.py (used by bracing_calc.py)
- wiring/ modules (used by electronics tools)

### 3.4 Keep as Reference (Tier 3)

These are edge-case or documentation use:
- rosette_calc.py
- finish_calc.py
- glue_joint_calc.py
- tuning_machine_calc.py
- cantilever_armrest_calc.py
- plate_design/ advanced modules

---

## 4. Drift Indicators

### 4.1 ScientificCalculator Woodwork Tab — PRIMARY DRIFT

**Location:** `packages/client/src/components/toolbox/ScientificCalculator.vue`  
**Lines:** 69-73

```vue
<!-- WOODWORK TAB -->
<WoodworkPanel
  v-else-if="activeTab === 'Woodwork'"
  v-model:active-category="woodworkCategory"
  :categories="woodworkCategories"
/>
```

**Problem:** Woodworking features (board feet, volume, angles) embedded in scientific calculator.  
**Fix:** Extract to new Woodworking Suite module.

### 4.2 LTB Calculator Router — Mixed Domains

**Location:** `services/api/app/routers/ltb_calculator_router.py`

This router mixes:
- Scientific (expression evaluation)
- Financial (TVM calculations)
- Woodworking (board feet, wedge, miter, dovetail)
- Lutherie (radius calculations)

**Fix:** Split into domain-specific routers or keep as utility router separate from domain modules.

### 4.3 Duplicate Implementations

| Math | Locations | Notes |
|------|-----------|-------|
| Radius from chord | ltb_calculator_router.py, radius_profiles.py | Should consolidate |
| Fret position | fret_math.py, fret_slots_cam.py | CAM version may have CNC-specific additions |
| Helmholtz | soundhole_physics.py, soundhole_resonator.py | Resonator may be deprecated |

---

## 5. Damage Report — Basic/Scientific Calculators

### 5.1 Basic Calculator

**Status:** WORKING

**Implementation:** `packages/client/src/components/toolbox/calculator/BasicCalculatorPad.vue`

**Features verified:**
- Digit entry (0-9, decimal point)
- Operations (+, -, ×, ÷)
- Clear / All Clear
- Backspace
- Equals / calculate
- Toggle sign

**No damage found.** The basic calculator appears functional.

### 5.2 Scientific Calculator

**Status:** WORKING (with drift)

**Implementation:** `packages/client/src/components/toolbox/ScientificCalculator.vue`

**Features verified:**
- All basic operations
- Trig functions (sin, cos, tan)
- Inverse trig (asin, acos, atan)
- Logarithms (log, ln)
- Powers (x², √, ^)
- Constants (π, e)
- Angle mode toggle (deg/rad)
- History

**Drift issue:** Contains Woodwork tab that should be separate module.

**No functional damage found.** Scientific features work; issue is organizational (woodworking embedded).

### 5.3 Root Cause Analysis

The consolidation event Ross mentioned appears to have:
1. Merged woodworking features INTO the scientific calculator UI
2. Left backend calculators as Tier 2 without promoting to UI
3. Not actually broken basic/scientific math — just misplaced woodworking

---

## 6. Business Suite State

### 6.1 Current Components

| Calculator | File | State | UI |
|------------|------|-------|-----|
| CNC ROI | business/roi.py | Working | CNCROICalculator.vue (stub) |
| Amortization | business/amortization.py | Working | No UI |
| Machine Throughput | business/machine_throughput.py | Working | No UI |
| Business Calculator | BusinessCalculator.vue | Working | Yes |

### 6.2 BusinessCalculator.vue

Present in Calculator Hub, marked "Ready". Needs verification of what features it exposes vs. what's available in backend.

### 6.3 Missing from UI

- Amortization calculator (backend exists)
- Machine throughput estimator (backend exists)
- ROI calculator shows "Coming Soon" placeholder

---

## 7. Recommendations for Phase 2 Triage

### 7.1 Immediate Actions (Quick Wins)

1. **Extract Woodwork tab** from ScientificCalculator to new Woodworking Suite
2. **Connect TensionCalculatorPanel.vue** to Calculator Hub (component exists, not wired)
3. **Complete CNCROICalculator.vue** — backend exists, UI is stub

### 7.2 High-Priority Promotions

Ross should decide: promote these from Tier 2 to Tier 1?

| Calculator | Effort | User Value |
|------------|--------|------------|
| String Tension | LOW | HIGH — every builder needs this |
| Fret Position | LOW | HIGH — fundamental tool |
| Nut Slot Sizing | LOW | MEDIUM — setup tool |
| Intonation | MEDIUM | HIGH — setup tool |
| Setup Cascade | MEDIUM | HIGH — comprehensive setup |
| Body Volume | LOW | MEDIUM — acoustic design |

### 7.3 New Module: Woodworking Suite

Contents (extracted + promoted):
- Board Feet (from Scientific)
- Volume (from Scientific)
- Angles (from Scientific)
- Wedge Angle (from API)
- Miter Angle (from API)
- Dovetail Angle (from API)
- Wood Movement (new UI)
- Side Bending (new UI)

### 7.4 Tier 3 Decisions

Ross to decide: keep as reference, deprecate, or promote?
- plate_design/ modules (advanced acoustics)
- rosette_calc.py
- finish_calc.py
- glue_joint_calc.py

### 7.5 Do Not Touch

- Saw Lab calculators (separate module, working)
- _bracing_physics.py (internal plumbing)
- kerfing_geometry_engine.py (internal plumbing)
- wiring/ modules (working, used by electronics tools)

### 7.6 Commodity Decisions (Phase 2)

Ross to decide per-item whether commodity status warrants deletion:

**Commodity + No workflow integration + Low usage → Deletion candidates:**
- Fraction Calculator (stub, never completed)
- Amortization (generic TVM math)
- Basic woodworking angles (miter, dovetail — extremely generic)

**Commodity + Workflow integration → Likely keep:**
- Fret Position / Multi-scale — feeds CAM pipeline
- String Tension — has D'Addario-calibrated unit weights
- Basic/Scientific Calculator — workflow convenience, used by other tools

**Commodity + Reference data value → Likely keep:**
- Fingerboard Radius Reference — convenient lookup table
- Scale Lengths Reference — same
- String Gauge Presets — same

**Differentiated → Keep:**
- Soundhole Calculator (Gore priors, builder calibration log)
- Spiral Soundhole (Williams 2019 research)
- Side Bending (USDA + builder literature integration)
- Setup Cascade (dependency chain logic)
- Plate Design modules (Rayleigh-Ritz, alpha-beta — advanced acoustics)
- Archtop Floating Bridge (Benedetto defaults)

**needs-review → Ross decides:**
The 36 items marked `needs-review` require Ross to assess whether the implementation adds value beyond commodity math. Key questions:
1. Does it use custom parameters or priors not available elsewhere?
2. Does it integrate with Production Shop workflows?
3. Is the UI/UX meaningfully better than free alternatives?

---

## Appendix A: File Locations

### Backend Calculators
```
services/api/app/calculators/
├── business/
│   ├── amortization.py
│   ├── machine_throughput.py
│   └── roi.py
├── plate_design/
│   ├── alpha_beta.py
│   ├── archtop_graduation.py
│   ├── brace_prescription.py
│   ├── rayleigh_ritz.py
│   └── thickness_calculator.py
├── saw_adapters/
├── wiring/
├── acoustic_body_volume.py
├── bracing_calc.py
├── fret_leveling_calc.py
├── fret_wire_calc.py
├── headstock_break_angle_calc.py
├── kerfing_calc.py
├── nut_slot_calc.py
├── saddle_compensation.py
├── setup_cascade.py
├── side_bending_calc.py
├── soundhole_physics.py
├── string_tension.py
├── wood_movement_calc.py
└── [~40 more files]
```

### Geometry Calculators
```
services/api/app/instrument_geometry/
├── neck/
│   ├── fret_math.py
│   ├── radius_profiles.py
│   └── neck_profiles.py
├── neck_taper/
│   └── taper_math.py
├── bridge/
│   └── archtop_floating_bridge.py
```

### Frontend Components
```
packages/client/src/components/toolbox/
├── CalculatorHub.vue
├── ScientificCalculator.vue (DRIFT: has Woodwork tab)
├── FractionCalculator.vue
├── BusinessCalculator.vue
├── CNCROICalculator.vue
├── BridgeCalculator.vue
├── ArchtopCalculator.vue
├── BracingCalculator.vue
├── calculator/
│   ├── BasicCalculatorPad.vue
│   ├── ScientificCalculatorPad.vue
│   └── WoodworkPanel.vue (should be separate module)
├── radius-dish/
│   └── RadiusDishCalculator.vue
└── scale-length/
    ├── TensionCalculatorPanel.vue (not in hub)
    └── TensionCalculatorTab.vue
```

### API Routers
```
services/api/app/routers/
├── ltb_calculator_router.py (mixed domains)
├── saddle_compensation_router.py
├── instrument_geometry/
│   ├── string_tension_router.py
│   ├── nut_fret_router.py
│   ├── geometry_calculator_router.py
│   ├── setup_router.py
│   └── bridge_router.py
```

---

## Appendix B: Verification Checklist

Marked items verified during this audit:

- [x] Basic calculator — digit entry, operations, calculate
- [x] Scientific calculator — trig, log, powers, constants
- [x] String tension — complete implementation
- [x] Fret math — scale length, multi-scale
- [x] Saddle compensation — design + setup modes
- [x] Soundhole — Helmholtz physics
- [x] Side bending — species database, physics
- [x] Wood movement — shrinkage coefficients
- [x] Headstock angle — complete with thresholds
- [x] Nut slot — complete with presets
- [x] Bracing — section area, mass estimation
- [x] Kerfing — types, dimensions, schedules
- [x] Body volume — reference models
- [x] Setup cascade — parameter evaluation
- [ ] ArchtopCalculator.vue — needs testing
- [ ] RadiusDishCalculator.vue — needs testing
- [ ] BusinessCalculator.vue features — needs testing

---

*End of Phase 1 Inventory Report*
