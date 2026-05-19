# 1958 Gibson Flying V — CNC Design & G-code Handoff

> **Model:** `flying_v` | **Registry Status:** `ASSETS_ONLY` → `PARTIAL` | **Session Date:** 2026-03-07

---

## Part 1 · Base Instrument

| Field | Value |
|-------|-------|
| Model ID | `flying_v` |
| Display Name | 1958 Gibson Flying V — Korina Original |
| Manufacturer | Gibson |
| Year | 1958 |
| Category | `electric_guitar` |
| Scale Length | 628.65mm (24.75") |
| Frets | 22 |
| Strings | 6 |
| Body Dimensions | 486mm W × 607mm L × 44.45mm thick |
| Body Material | Korina (Terminalia superba) |
| Neck Joint | Set-neck long tenon (38mm × 76mm × 19mm) |
| Pickups | HH — dual PAF humbuckers, direct mount |
| Bridge | String-through-body + ABR-1 tune-o-matic |
| Headstock | Split-V, 17° angle, 3+3 banjo-style Kluson |
| Registry Status | `PARTIAL` (was `ASSETS_ONLY`) |

### Variants

| Variant | Key Differences |
|---------|----------------|
| `original_1958` | Korina body, thick D neck, PAF humbuckers, bone nut, natural finish |
| `reissue_2023` | Korina body, rounded V neck, two-way truss rod, vintage Kluson tuners |

---

## Part 2 · Subsystem Status Matrix

| Subsystem | Status | Notes |
|-----------|--------|-------|
| Spec JSON | ✅ CREATED | `specs/gibson_flying_v_1958.json` — 2 variants, full CNC notes |
| Body Outline (catalog.json) | ✅ EXISTS | 486×607mm, 48 points, `electric/flying_v_body.dxf` reference |
| Body Outline (body_outlines.json) | ❌ MISSING | No coordinate data in body_outlines.json |
| Body DXF | ❌ MISSING | `flying_v_body.dxf` referenced but does not exist on disk |
| Model Stub | ✅ EXISTS | `guitars/flying_v.py` — basic MODEL_INFO |
| Registry Entry | ✅ UPDATED | `ASSETS_ONLY` → `PARTIAL`, spec JSON added to assets |
| DWG Source Files | ✅ EXISTS | 3 files: `Flying V 58.dwg`, `59.dwg`, `83.dwg` |
| Body Perimeter G-code | ✅ CREATED | `exports/flying_v_1958_body_perimeter_mach4.nc` |
| Pickup Cavity G-code | ✅ CREATED | `exports/flying_v_1958_pickup_cavities_mach4.nc` |
| Neck/Control/String G-code | ✅ CREATED | `exports/flying_v_1958_neck_control_strings_mach4.nc` |
| Pixel Calibrator | ✅ EXISTS | Entry in CalibrationPanel.vue (21.0" × 19.0") |
| Vision/AI Prompts | ✅ EXISTS | `flying_v` in segmentation and inlay prompts |
| Frontend Card | ✅ EXISTS | features.html, instrumentApi.ts |

---

## Part 3 · CNC Program Summary

### Machine & Post Processor

| Parameter | Value |
|-----------|-------|
| Machine Profile | `Mach4_Router_4x8` |
| Bed Size | 2440 × 1220 × 150mm |
| Max Spindle | 24,000 RPM |
| Max Feed XY | 15,000 mm/min |
| Post Processor | Mach4 (`G90 G17 G21 M3 S18000 G4 P2`) |
| Units | Metric (G21) |

### Bit Recommendations

| Operation | Bit | Diameter | Type | RPM | Feed | Notes |
|-----------|-----|----------|------|-----|------|-------|
| Body perimeter profiling | T1 | 1/4" (6.35mm) | 2-flute upcut spiral | 18,000 | 2,500 mm/min | 8 passes × 6mm stepdown through 44.45mm korina |
| Pickup cavity roughing | T1 | 1/4" (6.35mm) | 2-flute upcut spiral | 18,000 | 2,500 mm/min | 60% stepover zigzag pattern |
| Pickup cavity finishing | T2 | 1/8" (3.175mm) | 2-flute upcut spiral | 20,000 | 1,800 mm/min | Perimeter cleanup + spring pass for wall accuracy |
| Neck mortise roughing | T1 | 1/2" (12.7mm) | 2-flute upcut spiral | 16,000 | 3,000 mm/min | Bulk removal of tenon pocket material |
| Neck mortise finishing | T3 | 1/4" (6.35mm) | 2-flute downcut spiral | 18,000 | 2,000 mm/min | **Downcut** for clean top edge — critical for tight fit |
| Control cavity | T1 | 1/4" (6.35mm) | 2-flute upcut spiral | 18,000 | 2,500 mm/min | Route from BACK face, 7 passes × 5mm |
| String-through holes | T4 | 9/64" (3.5mm) | Brad point drill | 12,000 | 400 mm/min | G83 peck cycle, 6mm peck depth, through full body |
| Ferrule counterbores | T5 | 25/64" (10mm) | Forstner | 8,000 | 200 mm/min | 6mm depth on back face for string ferrules |

### G-code Files

| File | Operations | Lines | Tool Changes |
|------|-----------|-------|-------------|
| `flying_v_1958_body_perimeter_mach4.nc` | Body outline profiling (8 depth passes) | ~450 | 0 (single tool) |
| `flying_v_1958_pickup_cavities_mach4.nc` | Neck + bridge humbucker cavities (rough+finish) | ~300 | 3 (T1↔T2) |
| `flying_v_1958_neck_control_strings_mach4.nc` | Neck mortise, control cavity, string-through, ferrules | ~400 | 4 (T1→T3→T1→T4→T5) |

### Workpiece Orientation & Setup

1. **Body perimeter + pickup cavities + string-through holes:** Face UP, origin at body centerline V-apex (bottom center)
2. **Control cavity + ferrule counterbores:** FLIP workpiece — route from BACK face
3. **Workpiece blank:** 500mm × 620mm × 44.45mm korina slab (oversized for clamping)
4. **Workholding:** Double-sided tape + 6 holding tabs on perimeter (broken off after profiling)

---

## Part 4 · Gap Registry

| ID | Gap | Severity | Subsystem | Shared With |
|----|-----|----------|-----------|-------------|
| FV-GAP-01 | `flying_v_body.dxf` does not exist on disk despite being referenced in `catalog.json` and `outlines.py` | **CRITICAL** | Body / Vectorizer | — |
| FV-GAP-02 | No Flying V coordinate data in `body_outlines.json` — the 48-point polygon was never extracted | **HIGH** | Body / Outlines | — |
| FV-GAP-03 | No `ProfileToolpath` class exists — body perimeter profiling is hand-generated, not computed from outline | **HIGH** | CAM / Toolpath | J45 (VINE-04), OM (OM-GAP-06), Benedetto (BEN-GAP-07) |
| FV-GAP-04 | Vectorizer Phase 2 has never processed the Flying V DWGs — conversion pipeline DWG→DXF not executed | **HIGH** | Vectorizer | — |
| FV-GAP-05 | No pocket toolpath generator consumes body outline data to position pickup cavities parametrically | **MEDIUM** | CAM / Pocket | J45 (VINE-05), OM (OM-GAP-07) |
| FV-GAP-06 | String-through drilling operation has no backend API — G83 peck cycle hand-generated | **MEDIUM** | CAM / Drilling | — |
| FV-GAP-07 | No tool-change sequencing system — multi-tool programs require manual `M0` pauses | **MEDIUM** | CAM / Post | OM (OM-GAP-08) |
| FV-GAP-08 | Neck mortise pocket has no parametric generation from tenon dimensions in spec JSON | **MEDIUM** | CAM / Pocket | — |
| FV-GAP-09 | `detailed_outlines.py` has no Flying V entry — only `outlines.py` metadata exists | **LOW** | Body / Outlines | — |
| FV-GAP-10 | G-code body outline uses parametric approximation, not actual DXF-extracted coordinates | **HIGH** | CAM / Toolpath | — |

---

## Part 5 · Cross-References to Prior Builds

| Shared Gap Pattern | This Build | J45 | OM-28 | Benedetto |
|-------------------|------------|-----|-------|-----------|
| No body profiling toolpath class | FV-GAP-03 | VINE-04 | OM-GAP-06 | BEN-GAP-07 |
| No pocket positioning from spec | FV-GAP-05 | VINE-05 | OM-GAP-07 | — |
| No tool-change sequencing | FV-GAP-07 | — | OM-GAP-08 | — |
| Missing DXF from reference | FV-GAP-01 | — | — | — |
| Body outline never vectorized | FV-GAP-04 | — | — | — |

### New gaps unique to this build

- **FV-GAP-01 / FV-GAP-02 / FV-GAP-04:** The Flying V is the first design where we discovered that a catalog.json entry references a DXF that was never actually created. The Vectorizer pipeline has 3 DWG source files but Phase 2 conversion was never run for this model.
- **FV-GAP-06:** First design requiring drilling operations (string-through-body). No G83 peck cycle support exists in the CAM system.
- **FV-GAP-10:** Because the DXF doesn't exist, the G-code body outline is a parametric approximation of the V shape, not extracted geometry. This is acceptable for prototyping but not production.

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total gaps | 10 |
| Critical | 1 |
| High | 4 |
| Medium | 3 |
| Low | 2 |
| Shared with prior builds | 3 (of 10) |
| New/unique to Flying V | 7 |
| G-code files generated | 3 |
| Tool changes across all programs | 7 |
| Distinct bits required | 5 |
| Registry status change | `ASSETS_ONLY` → `PARTIAL` |
| Files created | 4 (spec JSON + 3 G-code files) |
| Files modified | 1 (instrument_model_registry.json) |
