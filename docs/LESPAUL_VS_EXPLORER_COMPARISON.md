# Les Paul vs Explorer — Design Spec Completeness Comparison

Generated: 2026-03-26

## Summary

| Dimension | Les Paul | Explorer |
|-----------|:--------:|:--------:|
| **Spec JSON Lines** | 585 | 324 |
| **Completeness** | COMPLETE | PARTIAL |

---

## Body Geometry

| Spec | Les Paul | Explorer |
|------|----------|----------|
| **Shape** | Single cutaway | Angular asymmetric |
| **Length (mm)** | 444.0 | 460.0 |
| **Width (mm)** | 330.0 | 475.0 |
| **Thickness (mm)** | 50.8 | 44.45 |
| **Material (back)** | Honduran mahogany | Korina (limba) |
| **Material (top)** | Figured maple cap | Flat (no cap) |
| **Construction** | Maple cap glued to mahogany | Solid body flat top |
| **Outline Points** | 669 pts (refined) | 24 pts (coarse) |
| **DXF Status** | CAM-ready | Needs refinement |
| **Carved Top** | Compound radius dome | N/A (flat) |

---

## Neck & Scale

| Spec | Les Paul | Explorer |
|------|----------|----------|
| **Scale Length (mm)** | 628.65 | 628.65 |
| **Fret Count** | 22 | 22 |
| **Nut Width (mm)** | 43.0 | 43.0 |
| **Neck Profile** | Fat C | Thick C to D |
| **Fretboard Radius (mm)** | 304.8 | 304.8 |
| **Fretboard Wood** | Brazilian rosewood | Rosewood |
| **Neck Wood** | Mahogany | Korina (limba) |
| **Body Join Fret** | 16 | 22 |
| **Neck Angle (deg)** | 4.0 | 4.5 |
| **Binding** | Single ply cream | Single ply cream |
| **Inlays** | Trapezoid pearloid | Dot pearloid |

---

## Neck Pocket

| Spec | Les Paul | Explorer |
|------|----------|----------|
| **Joint Type** | Set neck long tenon | Set neck long tenon |
| **Tenon Width (mm)** | 53.0 | 55.0 |
| **Tenon Length (mm)** | 89.0 | 95.0 |
| **Tenon Depth (mm)** | 16.0 | 16.0 |
| **Mortise Tolerance (mm)** | 0.15 | 0.15 |

---

## Headstock

| Spec | Les Paul | Explorer |
|------|----------|----------|
| **Style** | Gibson open-book | Split-V |
| **Angle (deg)** | 17.0 | 17.0 |
| **Length (mm)** | 190.5 | 215.0 |
| **Width (mm)** | 94.0 | 105.0 |
| **Tuner Layout** | 3+3 | 6-inline split |

---

## Pickups

| Spec | Les Paul | Explorer |
|------|----------|----------|
| **Layout** | HH | HH |
| **Type** | PAF humbucker | PAF humbucker |
| **Route Length (mm)** | 71.0 | 71.0 |
| **Route Width (mm)** | 40.0 | 40.0 |
| **Route Depth (mm)** | 19.05 | 19.05 |
| **Neck PU Center from Bridge (mm)** | 155.0 | 152.4 |
| **Bridge PU Center from Bridge (mm)** | 20.0 | 25.4 |

---

## Bridge & Tailpiece

| Spec | Les Paul | Explorer |
|------|----------|----------|
| **Bridge Type** | ABR-1 Tune-O-Matic | ABR-1 Tune-O-Matic |
| **Stud Spacing (mm)** | 74.0 | 74.0 |
| **Stud Diameter (mm)** | 11.1 | 11.1 |
| **Stud Depth (mm)** | 19.05 | 19.05 |
| **String Spacing (mm)** | 52.5 | 52.5 |
| **Tailpiece Type** | Stoptail | Stoptail |
| **Tailpiece Stud Spacing (mm)** | 82.5 | 82.5 |

---

## Control Cavity & Electronics

| Spec | Les Paul | Explorer |
|------|----------|----------|
| **Location** | Rear lower bout | Rear lower body |
| **Length (mm)** | 108.0 | 108.0 |
| **Width (mm)** | 64.0 | 64.0 |
| **Depth (mm)** | 31.75 | 31.75 |
| **Pot Count** | 4 (2V, 2T) | 3 (2V, 1T) |
| **Toggle Location** | Upper bout | Upper horn (treble) |
| **Output Jack** | Lower bout rim | Lower body edge |

---

## CNC Operations

| Spec | Les Paul | Explorer |
|------|----------|----------|
| **Operations Defined** | 12 ops (OP20-OP63) | 18 ops (OP10-OP65) |
| **Tool Library** | T1-T3 | T1-T3 |
| **G-code Stats** | 18,394 lines | Not generated |
| **Estimated Cut Time** | 10.6 min | Unknown |
| **Perimeter Tabs** | 6 | 8 |

---

## Variants

| Spec | Les Paul | Explorer |
|------|----------|----------|
| **Variants Defined** | 2 | 2 |
| **Primary** | 1959 Standard | 1958 Original |
| **Secondary** | 1956 Goldtop | 1976 Reissue |

---

## Documentation & Assets

| Asset | Les Paul | Explorer |
|-------|----------|----------|
| **Spec JSON** | 585 lines | 324 lines |
| **DXF Body Outline** | CAM-ready | Coarse 24-pt |
| **DXF CAM Layers** | 8 layers | Missing |
| **Generator Script** | 1,389 LOC | Has script |
| **Fret Positions** | 22 frets | 22 frets |
| **Reference Plans** | 14 PDFs | Implicit |
| **Binding Spec** | Detailed (2-tier) | Basic |
| **Carved Top Spec** | Full (compound radius) | N/A |

---

## Gap Summary

**Les Paul: COMPLETE** — Production-ready spec with full CAM DXF and detailed documentation.

**Explorer: PARTIAL** — Core dimensions complete, but DXF is coarse and lacks CAM layers.

---

## Explorer Completion Roadmap

### Priority 1: HIGH (Blocking for CNC Production)

| Task | Description | Effort | Deliverable |
|------|-------------|--------|-------------|
| **1.1 High-Resolution Body Outline** | Current DXF has only 24 vertices — far too coarse for CNC. Need 300+ point outline with proper curves on horn tips and transitions. | Medium | `gibson_explorer_body_refined.dxf` |
| **1.2 CAM-Ready Multi-Layer DXF** | Create layered DXF matching Les Paul format with separate layers for each routing operation. | Medium | `Explorer_CAM_Closed.dxf` |
| **1.3 DXF Format Conversion** | Convert from AC1024 (AutoCAD 2010) to R12/AC1009 per project conventions for maximum compatibility. | Low | Updated DXF files |

**Required CAM DXF Layers:**
- CUTOUT (body perimeter)
- NECK_MORTISE (neck pocket)
- PICKUP_CAVITY (2x humbucker routes)
- ELECTRONIC_CAVITIES (control cavity)
- WIRING_CHANNEL (pickup-to-cavity, toggle-to-cavity, jack channel)
- POT_HOLES (3x pot shaft holes)
- STUDS (bridge + tailpiece stud holes)
- TOGGLE_SWITCH (upper horn hole)
- OUTPUT_JACK (edge-mounted jack bore)

---

### Priority 2: MEDIUM (Production Quality)

| Task | Description | Effort | Deliverable |
|------|-------------|--------|-------------|
| **2.1 G-code Generation** | Run generator script and capture stats (line count, cut distance, estimated time). | Low | Update `cnc_operations.gcode_stats` in spec |
| **2.2 Binding & Purfling Spec** | Document binding channel dimensions if applicable to Explorer variants (original '58 had binding). | Low | Add `binding_and_purfling` section |
| **2.3 Reference Plans Inventory** | List available blueprint PDFs from Guitar Plans archive. | Low | Add `reference_plans` section |
| **2.4 Traced Outline JSON** | Create `explorer_traced_outline.json` with body points and any void definitions. | Medium | JSON file in `body/traced_outlines/` |

---

### Priority 3: LOW (Documentation & Polish)

| Task | Description | Effort | Deliverable |
|------|-------------|--------|-------------|
| **3.1 Headstock Outline Points** | Add detailed headstock outline to spec (Explorer split-V is distinctive). | Low | Add `headstock_outline_points` field |
| **3.2 Pickguard Geometry** | Document angular pickguard shape and mounting holes. | Low | Add `pickguard` section with geometry |
| **3.3 Weight & Balance** | Add typical weight range and balance point for korina vs mahogany versions. | Low | Add `weight_kg` and `balance_point_mm` fields |
| **3.4 Test Coverage** | Create `test_explorer_*.py` unit tests for spec validation. | Medium | Test files |

---

## Estimated Effort to COMPLETE Status

| Priority | Tasks | Total Effort |
|----------|-------|--------------|
| HIGH | 3 tasks | ~4-6 hours |
| MEDIUM | 4 tasks | ~2-3 hours |
| LOW | 4 tasks | ~2-3 hours |
| **TOTAL** | **11 tasks** | **~8-12 hours** |

---

## Recommended Sequence

1. **Source high-resolution Explorer blueprint** — Check Guitar Plans archive for `Gibson-Explorer-1958.pdf` or similar
2. **Run photo vectorizer** on blueprint to extract refined body outline
3. **Generate Explorer_CAM_Closed.dxf** with all routing layers
4. **Convert DXF to R12 format** using ezdxf or LibreCAD
5. **Run G-code generator** and capture stats
6. **Update gibson_explorer.json** with missing sections
7. **Add to instrument_model_registry.json** with status: "COMPLETE"

---

## Files to Create/Update

| File | Action | Location |
|------|--------|----------|
| `gibson_explorer_body_refined.dxf` | CREATE | `body/dxf/electric/` |
| `Explorer_CAM_Closed.dxf` | CREATE | `body/dxf/electric/` |
| `explorer_traced_outline.json` | CREATE | `body/traced_outlines/` |
| `gibson_explorer.json` | UPDATE | `specs/` |
| `instrument_model_registry.json` | UPDATE | `instrument_geometry/` |
| `test_explorer_spec.py` | CREATE | `tests/` |

---

*Generated by Claude Code — 2026-03-26*
