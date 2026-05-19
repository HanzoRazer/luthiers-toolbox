# Instrument Completeness Audit
Generated: 2026-03-25

## Executive Summary

This audit compares the three primary instruments across all completeness dimensions:
- **Smart Guitar** - Proprietary flagship (headless, embedded computing)
- **Gibson Les Paul** - Reference instrument #1 (most complete traditional electric)
- **Fender Stratocaster** - Reference instrument #2 (classic double-cutaway)

**Status Rating:**
- Smart Guitar: **COMPLETE** (registry status)
- Les Paul: **COMPLETE** (registry status)
- Stratocaster: **PARTIAL** (registry status)

---

## Summary Matrix

| Dimension | Smart Guitar | Les Paul | Stratocaster |
|-----------|:---:|:---:|:---:|
| **A. Body Geometry** | | | |
| Body DXF | ✅ Smart-Guitar-v1_preliminary.dxf | ✅ LesPaul_body.dxf + LesPaul_CAM_Closed.dxf | ✅ Stratocaster_body.dxf |
| DXF Entity Count | 12 entities | 1 + 26 entities | 1 entity |
| Body outline point count | 21 pts (DXF) / 60 pts (traced) | 669 pts (JSON catalog) | ~250 pts (generator) |
| Traced outline JSON | ✅ 60 pts + 3 voids | ❌ None | ❌ None |
| Void/chamber definitions | ✅ 3 voids (11, 12, 21 pts) | N/A (solid mahogany) | N/A (solid body) |
| Python outline file | ✅ smart_guitar_traced_outline.py | ✅ les_paul.py | ✅ stratocaster_body_generator.py |
| **B. Spec JSON** | | | |
| JSON spec file | ✅ smart_guitar_v1.json (759 lines) | ✅ gibson_les_paul.json (585 lines) | ✅ stratocaster.json (147 lines) |
| Body dimensions | ✅ Complete | ✅ Complete | ✅ Complete |
| Neck pocket spec | ✅ Full bolt-on with bolts | ✅ Set-neck long tenon | ✅ Bolt-on basic |
| Pickup route spec | ✅ HH detailed | ✅ HH detailed | ✅ SSS basic |
| Electronics cavity spec | ✅ Pi 5 + Arduino detailed | ✅ Rear cavity detailed | ⚠️ Front-routed basic |
| Hardware geometry | ✅ Headless bridge detailed | ✅ TOM + stoptail detailed | ✅ Tremolo basic |
| Scale length | ✅ 628.65mm | ✅ 628.65mm | ✅ 648.0mm |
| Neck taper/profile | ✅ Modern C | ✅ Fat C with binding | ✅ C/Modern C |
| Variants defined | 1 | 2 (1959 Standard, 1956 Goldtop) | 3 (vintage, modern, 24fret) |
| **C. CAM / Generator** | | | |
| Generator script | ✅ generate_smart_guitar_full_build.py | ✅ generate_les_paul_full_build.py | ✅ stratocaster_body_generator.py |
| Generator LOC | 1,632 total | 1,389 total | 632 lines |
| G-code phases | ✅ 2 phases (front/rear) | ✅ 2 phases | ⚠️ Class-based (no explicit OP codes) |
| Operations count | ✅ 17 ops (OP10-OP71) | ✅ 21 ops (OP10-OP93) | ⚠️ Method-based ops |
| Tool library | ✅ T1-T3 defined | ✅ T1-T11 defined | ✅ Via config |
| CNC operations spec in JSON | ❌ None | ✅ Full cnc_operations section | ❌ None |
| **D. DXF Quality** | | | |
| DXF version | AC1024 (2010) | AC1015 (2000) | AC1015 (2000) |
| Audit status | ✅ CLEAN | ✅ CLEAN | ✅ CLEAN |
| Bounding box | 414.6 x 570.0 mm | 383.5 x 269.2 mm | 322.3 x 458.8 mm |
| Layers defined | 4 (BODY_OUTLINE, CENTERLINE, REFERENCE, ANNOTATIONS) | 1 (BODY_OUTLINE) / 8 (CAM file) | 1 (BODY_OUTLINE) |
| CAM-ready DXF | ❌ Missing | ✅ LesPaul_CAM_Closed.dxf | ❌ Missing |
| **E. Tests** | | | |
| Test file count | 5 tests | 10+ tests (cross-referenced) | 10+ tests (cross-referenced) |
| Dedicated test files | test_smart_guitar_*.py | lespaul references in many | strat references in many |
| **F. Documentation** | | | |
| Pre-cut checklist | ⚠️ In spec notes | ⚠️ In spec notes | ❌ None |
| Build chronicle | ❌ None | ❌ None | ❌ None |
| Reference documents | ✅ Source images listed | ✅ 14 PDFs + 2 CAM DXFs listed | ✅ PDF references listed |

---

## Smart Guitar - Known Issues (from DXF Diagnostic)

### DXF File: Smart-Guitar-v1_preliminary.dxf

**Critical Issues:**
1. **Centerline offset: -21.94mm** - Body is NOT centered on origin. The X centerline should be at 0, but the bounding box shows X range -229.3 to 185.4mm (asymmetric by ~22mm)
2. **Body outline only 21 points** - The DXF LWPOLYLINE has only 21 points, but the traced outline JSON has 60 points. The higher-resolution traced outline is NOT wired into the DXF.
3. **Stray entity** - CENTERLINE extends beyond body bounds (0, -254) to (0, 254) - 508mm length vs body length 444.5mm

**Warnings:**
4. **SPLINE entity present** - Body outline layer contains a SPLINE in addition to LWPOLYLINE. This may cause CAM interpretation issues.
5. **Annotations outside bounds** - TEXT entities at Y=-280 to -315 are well below body bounds

**Missing:**
6. **No CAM-ready version** - Unlike Les Paul which has LesPaul_CAM_Closed.dxf with 8 layers (CUTOUT, NECK_MORTISE, PICKUP_CAVITY, etc.), Smart Guitar only has the preliminary outline file
7. **Cavity geometry not in DXF** - All cavity specs are in JSON but not drawn in DXF

### Traced Outline vs DXF Mismatch

| Source | Body Points | Voids |
|--------|-------------|-------|
| DXF (preliminary) | 21 pts | None |
| traced_outline.json | 60 pts | 3 voids (11+12+21 pts) |
| traced_outline.py | ~105 coordinate pairs | Unknown |

**Action Required:** Generate new DXF from traced 60-point outline with void cutouts.

---

## Stratocaster - Gap to Smart Guitar Parity

| Missing Item | Priority | Notes |
|--------------|----------|-------|
| **Traced outline JSON** | HIGH | No body_pts_mm / voids_mm JSON file |
| **CAM-ready DXF** | HIGH | Need multi-layer DXF with NECK_POCKET, PICKUP_CAVITIES, CONTROL_CAVITY, TREMOLO_ROUTE layers |
| **Explicit OP codes in generator** | MEDIUM | Generator is class-based, not script-based. Works but differs from LP/SG pattern |
| **CNC operations in spec JSON** | MEDIUM | No cnc_operations section in stratocaster.json |
| **Electronics cavity detailed spec** | MEDIUM | Only basic front-routed mention |
| **Spring cavity spec** | MEDIUM | Strat-specific rear spring cavity not detailed |
| **Tremolo route spec** | MEDIUM | Basic dimensions only |
| **Pre-cut checklist** | LOW | Not documented |
| **Build chronicle/history** | LOW | Not documented |

**Gap Count: 9 items**

---

## Les Paul - Gap to Smart Guitar Parity

| Missing Item | Priority | Notes |
|--------------|----------|-------|
| **Traced outline JSON format** | LOW | Has 669-pt outline in body_outlines.json, not separate traced file |
| **Smart features section** | N/A | Not applicable (traditional instrument) |
| **Grid mapping (STEM)** | LOW | No stem_grid_mapping section |
| **Live wiring channel paths** | LOW | Wiring channels documented but not as detailed coordinate paths |

**Gap Count: 3 items** (mostly N/A differences)

**Les Paul is the most complete traditional instrument spec.**

---

## Priority Order for Next 8 Instruments

Based on existing partial data in the instrument_model_registry.json:

| Rank | Instrument | Current Status | Existing Assets | Effort to Complete |
|------|------------|----------------|-----------------|-------------------|
| 1 | **Melody Maker** | COMPLETE | Full | Ready |
| 2 | **Cuatro** | COMPLETE | Full | Ready |
| 3 | **Telecaster** | PARTIAL | Generator, outline | Medium - needs spec JSON |
| 4 | **Explorer** | PARTIAL | Generator | Medium - has generate_explorer_full_build.py |
| 5 | **Flying V** | PARTIAL | CAM ops | Medium |
| 6 | **OM/000** | PARTIAL | CAM ops | Medium - acoustic complexity |
| 7 | **Klein** | PARTIAL | CAM ops | Medium - ergonomic reference for SG |
| 8 | **Carlos Jumbo** | PARTIAL | CAM ops | Medium-High - acoustic |

**Recommended Path to 10-instrument POC:**
1. Smart Guitar ✅ (flagship)
2. Les Paul ✅ (Tier 1 reference)
3. Stratocaster (needs CAM DXF, spec enrichment)
4. Melody Maker (already COMPLETE)
5. Cuatro (already COMPLETE)
6. Telecaster (close to Strat, leverage work)
7. Explorer (has full build script)
8. Flying V (angular, validates complex outlines)
9. OM/000 (acoustic representative)
10. Klein (ergonomic validation, informs SG design)

---

## Spec JSON Completeness Comparison

### Field Coverage by Section

| Section | Smart Guitar | Les Paul | Stratocaster |
|---------|:---:|:---:|:---:|
| instrument/model metadata | ✅ | ✅ | ✅ |
| body.dimensions | ✅ | ✅ | ⚠️ ranges only |
| body.materials | ✅ | ✅ | ❌ |
| body.contour/cutaway | ✅ detailed | ✅ | ✅ flags only |
| cavities.neck_pocket | ✅ bolt pattern | ✅ long tenon | ✅ basic |
| cavities.pickup_routes | ✅ HH grid-mapped | ✅ HH detailed | ✅ SSS basic |
| cavities.electronics | ✅ Pi 5 + Arduino | ✅ rear cavity | ⚠️ control_cavity implicit |
| cavities.wiring_channels | ✅ 4 paths detailed | ✅ channels section | ❌ |
| cavities.output_jack | ✅ angled bore | ⚠️ in hardware | ⚠️ in hardware |
| neck.* | ✅ headless | ✅ set-neck | ✅ bolt-on |
| hardware.* | ✅ | ✅ | ⚠️ partial |
| bridge.* | ✅ headless | ✅ TOM+stoptail | ✅ tremolo |
| cnc_operations | ❌ | ✅ 12 ops | ❌ |
| fret_positions | ❌ | ✅ 22 positions | ❌ |
| binding_and_purfling | ❌ | ✅ detailed | ❌ |
| stock dimensions | ❌ | ✅ | ❌ |
| carved_top | N/A | ✅ detailed | N/A |
| smart_features | ✅ | N/A | N/A |
| stem_grid_mapping | ✅ | ❌ | ❌ |
| design_heritage | ✅ | ⚠️ implicit | ❌ |

**Unique to Smart Guitar:**
- smart_features section
- stem_grid_mapping (24x32 grid)
- design_heritage (Explorer + Klein)
- signal_chain (audio path A/B)
- arduino_preamp_pocket (I/O coprocessor)
- antenna_recess (WiFi)
- usb_c_port (charging)

**Unique to Les Paul:**
- cnc_operations (full OP list with tools)
- fret_positions (22 calculated)
- binding_and_purfling (two-tier channel)
- carved_top (compound radius dome)
- stock (mahogany back, maple top)
- reference_plans (14 PDFs)
- gcode_stats

---

## Raw Inventory Output

### DXF Files Found

```
Smart Guitar:
  ./services/api/app/instrument_geometry/body/dxf/electric/Smart-Guitar-v1_preliminary.dxf
  ./services/api/data/smart_guitar_combined.dxf
  ./services/api/data/smart_guitar_corrected.dxf
  ./services/api/data/smart_guitar_v2_complete.dxf
  ./services/api/data/smart_guitar_v3_from_spec.dxf
  ./Guitar Plans/Smart Guitar_1_*.dxf (2 files)

Les Paul:
  ./services/api/app/instrument_geometry/body/dxf/electric/LesPaul_body.dxf
  ./services/api/app/instrument_geometry/body/dxf/electric/LesPaul_CAM_Closed.dxf

Stratocaster:
  ./services/api/app/instrument_geometry/body/dxf/electric/Stratocaster_body.dxf
```

### DXF Entity Analysis

```
Smart-Guitar-v1_preliminary.dxf:
  DXF version: AC1024
  Total entities: 12
  Layers: ANNOTATIONS(6), BODY_OUTLINE(2), CENTERLINE(1), REFERENCE(3)
  Bounding box: 414.6 x 570.0 mm
  Audit: CLEAN

LesPaul_body.dxf:
  DXF version: AC1015
  Total entities: 1
  Layers: BODY_OUTLINE(1)
  Bounding box: 383.5 x 269.2 mm
  Audit: CLEAN

LesPaul_CAM_Closed.dxf:
  DXF version: AC1015
  Total entities: 26
  Layers: CUTOUT(1), ELECTRONIC_CAVITIES(1), NECK_MORTISE(1),
          PICKUP_CAVITY(2), POT_HOLES(4), SCREWS(10), STUDS(4),
          WIRING_CHANNEL(3)
  Bounding box: 383.5 x 269.2 mm
  Audit: CLEAN

Stratocaster_body.dxf:
  DXF version: AC1015
  Total entities: 1
  Layers: BODY_OUTLINE(1)
  Bounding box: 322.3 x 458.8 mm
  Audit: CLEAN
```

### Generator Scripts

```
Smart Guitar:
  scripts/generate_smart_guitar_full_build.py (1099 lines)
  scripts/generate_smart_guitar_dxf.py (265 lines)
  scripts/generate_smart_guitar_v3_dxf.py (268 lines)
  Total: 1632 lines
  Operations: OP10-OP71 (17 operations)

Les Paul:
  scripts/generate_les_paul_full_build.py (1259 lines)
  services/api/app/generators/lespaul_body_generator.py (130 lines)
  services/api/app/generators/lespaul_gcode/ (module)
  Total: 1389+ lines
  Operations: OP10-OP93 (21 operations)

Stratocaster:
  services/api/app/generators/stratocaster_body_generator.py (632 lines)
  Class-based generator, no explicit OP codes
  CAM operations via methods
```

---

## Recommendations

### Immediate Actions (Pre-Production Cut)

1. ~~**Fix Smart Guitar DXF centerline offset**~~ ✅ DONE (2026-03-25)
2. ~~**Generate Smart Guitar CAM DXF**~~ ✅ DONE - `Smart-Guitar-v1_CAM.dxf`
3. ~~**Wire traced 60-point outline into DXF**~~ ✅ DONE - replaced 21-point preliminary
4. ~~**Add void cutouts to Smart Guitar DXF**~~ ✅ DONE - 3 Klein-style voids added

**Smart Guitar DXF FIX SUMMARY:**
- Generated: `Smart-Guitar-v1_CAM.dxf` (services/api/app/instrument_geometry/body/dxf/electric/)
- Script: `scripts/generate_smart_guitar_cam_dxf.py`
- Recentering offset applied: X = +9.03mm, Y = +71.09mm
- Final X centerline offset: 0.00mm ✅
- Layers: BODY_OUTLINE(1), VOIDS(3), NECK_POCKET(1), PICKUP_CAVITIES(2), BRIDGE_ROUTE(1), ELECTRONICS_CAVITY(1), ARDUINO_POCKET(1), CENTERLINE(1), ANNOTATIONS(3)
- Audit: CLEAN

### Short-Term (Stratocaster Parity)

5. **Create stratocaster_traced_outline.json** - Mirror Smart Guitar format
6. **Create Stratocaster_CAM_Closed.dxf** - Mirror Les Paul format
7. **Add cnc_operations section to stratocaster.json**

### Medium-Term (10-Instrument POC)

8. Finalize Telecaster spec (leverage Strat work)
9. Finalize Explorer spec (has full_build script)
10. Finalize Flying V spec
11. Add acoustic representative (OM/000)

---

## Gibson J-45 Verification (2026-03-25)

**Status: NEAR-COMPLETE** ✅

### Summary

| Dimension | Status | Details |
|-----------|:------:|---------|
| **Spec JSON** | ✅ | 126 lines - comprehensive |
| **DXF Files** | ✅ | 5 files including layered construction drawing |
| **Body dimensions** | ✅ | 398.5 x 504.8 mm, full bout/waist specs |
| **Back bracing** | ✅ | BB-1 through BB-4 with positions |
| **Top bracing** | ✅ | X-brace pattern, TB-1 through TB-8 |
| **Fret positions** | ✅ | 20 positions calculated |
| **Cross-section** | ✅ | Purfling, kerf lining, binding |
| **Generator script** | ⚠️ | None found |
| **Tests** | ⚠️ | None found |

### DXF Assets

```
Guitar Plans/J 45 Plans/J45 DIMS.dxf          (source construction drawing)
Guitar Plans/J 45 Plans/J45_DIMS_Layered.dxf  (1222 entities, 10 layers)
Guitar Plans/J 45 Plans/J45_Bracing_Only.dxf  (bracing geometry only)
acoustic/J45_body_outline.dxf                 (399.0 x 504.8 mm, CLEAN)
acoustic/J45_body_outline_dense.dxf           (high-resolution outline)
```

**J45_DIMS_Layered.dxf Layers:**
- ANNOTATIONS, BACK_BRACING, BODY_OUTLINE, BRACES, CENTERLINE
- CROSS_HATCHING, DIMENSIONS, KERF_LINES, SOUNDHOLE, TOP_BRACING

### Gap to COMPLETE

| Missing Item | Priority | Notes |
|--------------|----------|-------|
| Generator script | MEDIUM | No generate_j45_full_build.py |
| Dedicated test file | LOW | No test_j45_*.py |
| CAM operations in spec | LOW | Optional - acoustic builds differ from CNC electric |

**Gap Count: 3 items** (minor - J-45 is production-ready for acoustic builds)

---

## Benedetto 17" Archtop Verification (2026-03-25)

**Status: SPEC-COMPLETE / DXF-PENDING** ⚠️

### Summary

| Dimension | Status | Details |
|-----------|:------:|---------|
| **Spec JSON** | ✅✅ | 356 lines - EXCEPTIONAL detail |
| **Model JSON** | ✅ | 117 lines - AI-extracted dimensions |
| **Body dimensions** | ✅ | 431.8 x 482.6 mm (17" lower bout) |
| **Variants** | ✅ | venetian_cutaway, non_cutaway |
| **Binding spec** | ✅✅ | Spanish rope binding with 11-step fabrication |
| **Binding continuity** | ✅ | Body → neck → headstock (3 miter joints) |
| **Neck spec** | ✅ | Full with binding details |
| **Headstock spec** | ✅ | With binding wrap |
| **F-holes spec** | ✅ | 101.6mm length |
| **Carved top/back** | ✅ | Graduation specs with apex/edge thickness |
| **DXF Files** | ❌ | NONE - marked phantom/pending |
| **Generator script** | ❌ | None found |
| **Tests** | ❌ | None found |

### Spec JSON Assets

```
specs/benedetto_archtop_rope.json   (356 lines - Spanish rope binding fabrication)
models/benedetto_17.json            (117 lines - AI-extracted blueprint dimensions)
```

### Notable Spec Features

**Spanish Rope Binding Fabrication (11-step process):**
1. Prepare veneer strips (ebony/maple, 1.0mm wide, 0.6mm thick)
2. Glue strip stack per matrix rows
3. Cross-cut into chips at 2.0mm intervals
4. Reassemble with column_sequence [1,2,2,1,3,4,5,4,3]
5. Heat-bend to body contour
6. Rout purfling channel (6.0mm x 2.0mm)
7. Glue into channel with outer/inner strips
8. Continue for neck edges (2.5mm x 1.5mm)
9. Miter at heel joint
10. Continue around headstock
11. Final scrape and level

**Critical Joints Documented:**
- heel_cap: 45° miter (body to neck)
- nut: 45° miter (neck to headstock)
- cutaway_horn: ~15mm radius bend
- waist: ~50mm radius compound bend
- headstock_tip: ~20mm radius bend

### Gap to COMPLETE

| Missing Item | Priority | Notes |
|--------------|----------|-------|
| **body_outline.dxf** | HIGH | Required for CNC routing |
| **f_holes.dxf** | HIGH | Required for F-hole routing |
| **graduation_map.json** | MEDIUM | Hand graduation reference |
| Generator script | MEDIUM | No generate_benedetto_full_build.py |
| Test file | LOW | No test_benedetto_*.py |

**Gap Count: 5 items** (DXF creation is blocking)

### Recommendation

The Benedetto spec is exceptionally detailed—possibly the most comprehensive binding fabrication spec in the entire registry. **DXF extraction from blueprints is the only blocker.** The spec notes indicate vectorizer extraction was planned but not completed.

**Action Required:**
1. Run photo vectorizer on `Guitar Plans/Benedetto/Benedetto Front.jpg`
2. Generate body_outline.dxf and f_holes.dxf
3. Validate against spec dimensions (431.8mm lower bout)

---

## Updated Priority Order for 10-Instrument POC

Based on verification results:

| Rank | Instrument | Status | Blocking Items |
|------|------------|--------|----------------|
| 1 | Smart Guitar | ✅ COMPLETE | DXF needs fixes (centerline, voids) |
| 2 | Les Paul | ✅ COMPLETE | None |
| 3 | **Gibson J-45** | ✅ NEAR-COMPLETE | Generator script (optional) |
| 4 | Melody Maker | ✅ COMPLETE | None |
| 5 | Cuatro | ✅ COMPLETE | None |
| 6 | Stratocaster | ⚠️ PARTIAL | CAM DXF, spec enrichment |
| 7 | **Benedetto 17"** | ⚠️ SPEC-COMPLETE | DXF extraction required |
| 8 | Telecaster | ⚠️ PARTIAL | Spec JSON needed |
| 9 | Explorer | ⚠️ PARTIAL | Has full_build script |
| 10 | OM/000 | ⚠️ PARTIAL | Acoustic complexity |

**Revised 10-Instrument Path:**
- 5 COMPLETE: Smart Guitar, Les Paul, J-45, Melody Maker, Cuatro
- 2 close: Stratocaster (CAM DXF), Benedetto (DXF extraction)
- 3 partial: Telecaster, Explorer, OM/000

---

*Audit generated by Claude Code - 2026-03-25*
*J-45 and Benedetto verification appended - 2026-03-25*
