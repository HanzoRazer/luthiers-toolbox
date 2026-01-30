# Streamlit Demo Gap Analysis

**Date:** 2026-01-30
**Purpose:** Document all incomplete/broken features in the demo
**Status:** For review when time permits

---

## Executive Summary

The Streamlit demo reveals significant gaps between UI presentation and actual functionality. Most features display controls but lack backend wiring to the real calculation/generation engines.

---

## Gap Inventory by Section

### 1. Blueprint Reader

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Image upload | Working | Working | None |
| PDF upload | Working | Needs pdf2image | Minor |
| OpenCV vectorization | Working | Working | None |
| AI analysis | UI exists | API key available | **Needs wiring** |
| DXF export | Working | Working | None |
| SVG export | Working | Working | None |
| DXF viewer | Working | Working | None |

**Priority Fixes:**
- Wire Claude AI analysis to `/api/blueprint/analyze` endpoint

---

### 2. Art Studio

#### 2.1 Rosette Builder

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Pattern presets dropdown | Working | PRESET_MATRICES exists | None |
| Pattern selection | Working | Loads matrix formula | None |
| **Visual rendering** | **BROKEN** | Draws static circles | **Critical** |
| Ring dimensions | Working | Calculates correctly | None |
| Cut list generation | UI missing | TraditionalPatternGenerator has it | **Needs UI** |
| Assembly instructions | UI missing | TraditionalPatternGenerator has it | **Needs UI** |
| DXF export | Partial | Only exports circles, not tiles | **Critical** |
| Material BOM | UI missing | pattern_generator.py has it | **Needs UI** |

**Root Cause:**
- `show_rosette_builder()` renders a static PIL image with concentric circles
- Does NOT call `TraditionalPatternGenerator.generate_pattern()`
- Does NOT use tile geometry from matrix formula
- `tile_segmentation.py` is a STUB (returns 8 fixed tiles)

**Priority Fixes:**
1. Wire pattern selection to `TraditionalPatternGenerator`
2. Render actual tile geometry (trapezoids around ring)
3. Complete `tile_segmentation.py` with real math
4. Add cut list and assembly instruction display

#### 2.2 Headstock Art

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Style selection | Working | Prompts exist | None |
| Wood selection | Working | UI only | None |
| Motif selection | Working | UI only | None |
| **AI generation** | **BROKEN** | Needs OpenAI/DALL-E | **Critical** |
| Preview display | Placeholder | No real image | **Critical** |
| DXF export | Missing | Would need vector conversion | **Future** |

**Root Cause:**
- `show_headstock_art()` displays placeholder images
- No actual AI image generation wired
- `headstock_art_prompts.py` has prompts but no API call

**Priority Fixes:**
1. Wire to image generation API (OpenAI DALL-E or similar)
2. Display actual generated images
3. Add image-to-vector pipeline for DXF export

#### 2.3 Inlay Designer

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Inlay type selection | Working | UI only | None |
| Material selection | Working | UI only | None |
| Position selection | Working | UI only | None |
| **Pattern generation** | **MISSING** | `inlay_calc.py` exists | **Critical** |
| Preview | Missing | No rendering | **Critical** |
| DXF export | Missing | inlay_calc has geometry | **Needs wiring** |

**Root Cause:**
- `show_inlay_designer()` is a placeholder with dropdowns only
- `calculators/inlay_calc.py` has full pattern generation
- Not wired to UI

**Priority Fixes:**
1. Wire to `inlay_calc.calculate_fretboard_inlays()`
2. Render fret marker positions on fretboard diagram
3. Add DXF export using `generate_inlay_dxf_string()`

---

### 3. Guitar Designer

#### 3.1 Body Designer

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Template Library mode | Working | Bodies load | None |
| Category filter | Working | Filters work | None |
| Body outline render | Working | Renders correctly | None |
| Parametric mode | Working | Generates outline | None |
| Scale adjustment | Working | Scales correctly | None |
| DXF download | Partial | Only if DXF file exists | Minor |
| JSON export | Working | Working | None |
| **Body Shape Library** | **Needs tab** | Templates exist | **Needs UI restructure** |
| **AI body generation** | **MISSING** | Vision pipeline planned | **Future** |

**Priority Fixes:**
1. Add "Body Shape Library" as explicit feature (not just mode)
2. Wire AI segmentation pipeline for photo-to-outline

#### 3.2 Fret Calculator

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Scale presets | Working | Working | None |
| Fret count | Working | Working | None |
| Position calculation | Working | Uses fret_math.py | None |
| Fretboard diagram | Working | Renders correctly | None |
| Multiscale/fan fret | Working | Working | None |
| Position table | Working | Working | None |
| JSON/CSV export | Working | Working | None |
| **Alternative temperaments** | **MISSING** | `alternative_temperaments.py` exists | **Needs UI** |

**Priority Fixes:**
1. Add temperament selection (Equal, Just, Pythagorean, Meantone)
2. Wire to `compute_just_intonation_positions()` etc.

---

### 4. CNC Studio

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Saw Lab tab | Placeholder | Full system in `/saw-lab` | **Needs wiring** |
| Operation types | Dropdown only | Backend has full operations | **Needs wiring** |
| Toolpath tab | Placeholder | `adaptive_core_l1.py` exists | **Needs wiring** |
| Strategy selection | Dropdown only | CAM engine supports all | **Needs wiring** |
| G-code tab | Placeholder | Post processors exist | **Needs wiring** |
| Post processor select | Dropdown only | Multiple posts available | **Needs wiring** |
| **Everything** | **PLACEHOLDER** | **Full backend exists** | **Critical** |

**Root Cause:**
- `show_cnc_studio()` is entirely placeholder UI
- Real CAM system exists in `app/cam/` with full functionality
- Routers exist: `/api/cam/adaptive`, `/api/cam/gcode`, etc.

**Priority Fixes:**
1. Wire DXF upload → toolpath generation
2. Wire toolpath → G-code export
3. Display toolpath preview (SVG or canvas)
4. Implement real Saw Lab operations

---

### 5. Calculator Suite

#### 5.1 Basic Calculator

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Expression input | Working | Working | None |
| Basic operations | Working | Working | None |
| Memory functions | UI exists | Backend has M+/M-/MR/MC | **Needs button wiring** |
| Clear function | Working | Working | None |

#### 5.2 Scientific Calculator

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Trig functions | Working | Working | None |
| Hyperbolic functions | Working | Working | None |
| Statistics | Partial | Backend complete | **UI incomplete** |
| Linear regression | UI exists | Backend has it | **Needs result display** |
| Constants (Pi, e, tau, phi) | Working | Working | None |
| **Sum function** | **MISSING** | Backend has stat_sum() | **Needs UI** |

#### 5.3 Fraction Calculator

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Fraction mode toggle | Working | Working | None |
| Precision selection | Working | Working | None |
| Operations | Working | Working | None |
| Display | Working | Fixed _is_constant flag | None |

#### 5.4 Financial Calculator

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| TVM calculations | Working | Working | None |
| Loan amortization | UI exists | Backend has it | **Needs table display** |
| Depreciation | UI exists | Backend has it | Minor |
| NPV/IRR | **MISSING** | Backend has it | **Needs UI** |

#### 5.5 Luthier Calculator

| Feature | UI Status | Backend Status | Gap |
|---------|-----------|----------------|-----|
| Fret position | Working | Working | None |
| Radius conversion | Working | Working | None |
| Board feet | Working | Working | None |
| Kerf spacing | Working | Working | None |
| String tension | Working | Working | None |
| **Compensation calc** | **MISSING** | Backend may have it | **Check backend** |
| **Nut/saddle calc** | **MISSING** | May need adding | **Check backend** |

---

## Summary Statistics

| Section | Features | Working | Partial | Broken | Missing |
|---------|----------|---------|---------|--------|---------|
| Blueprint Reader | 7 | 6 | 0 | 0 | 1 |
| Art Studio - Rosette | 8 | 4 | 1 | 2 | 1 |
| Art Studio - Headstock | 6 | 3 | 0 | 2 | 1 |
| Art Studio - Inlay | 5 | 3 | 0 | 0 | 2 |
| Guitar Designer - Body | 8 | 6 | 1 | 0 | 1 |
| Guitar Designer - Fret | 8 | 7 | 0 | 0 | 1 |
| CNC Studio | 7 | 0 | 0 | 0 | 7 |
| Calculator Suite | 20 | 15 | 2 | 0 | 3 |
| **TOTAL** | **69** | **44** | **4** | **4** | **17** |

**Completion Rate:** 64% working, 6% partial, 6% broken, 24% missing

---

## Priority Matrix

### P0 - Critical (Demo looks broken)
1. **Rosette visual rendering** - Pattern selection does nothing visible
2. **Headstock AI generation** - Shows placeholder, not real images
3. **CNC Studio** - Entire section is placeholder

### P1 - High (Missing key features)
1. Rosette cut list / assembly instructions
2. Inlay pattern generation and preview
3. Alternative temperaments in fret calculator
4. Blueprint AI analysis wiring

### P2 - Medium (Incomplete features)
1. Calculator memory button wiring
2. Financial calculator NPV/IRR
3. Body Shape Library as explicit feature
4. Statistics result display

### P3 - Low (Polish)
1. Loan amortization table display
2. Luthier calculator additional functions
3. DXF export for all body templates

---

## Recommended Fix Order

1. **Rosette tile rendering** (P0) - Most visible broken feature
2. **CNC Studio basic wiring** (P0) - Section is completely empty
3. **Inlay calculator wiring** (P1) - Easy win, backend exists
4. **Alternative temperaments** (P1) - Easy win, backend exists
5. **Blueprint AI wiring** (P1) - API key available
6. **Headstock AI** (P0) - Needs external API decision

---

## Notes

- Many "missing" features have complete backends - just need UI wiring
- The façade pattern (rosette_calc, inlay_calc) provides clean interfaces
- CNC Studio has the most work - entire CAM system needs frontend
- Calculator gaps are minor - mostly UI polish

---

*Document generated for gap tracking. Review and update as fixes are completed.*
