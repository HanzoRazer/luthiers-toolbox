# OM Acoustic Purfling & Binding CNC Handoff

**Date:** 2026-03-07
**Model:** Martin OM-28 style acoustic
**Spec Source:** `services/api/app/instrument_geometry/specs/martin_om28.json`
**DXF Source:** `services/api/app/instrument_geometry/body/dxf/acoustic/om_000_body.dxf` (recovered)

---

## Materials

| Component | Material | Width (mm) | Height (mm) |
|-----------|----------|-----------|-------------|
| Binding | Walnut | 1.95 | 5.80 |
| Purfling | Abalone | 1.85 | 1.43 |

## Channel Specifications

| Channel | Width (mm) | Depth (mm) | Location |
|---------|-----------|-----------|----------|
| Binding channel | 2.10 | 5.70 | Body perimeter, offset 1.0mm inward from edge |
| Purfling ledge | 2.00 | 1.60 | Body perimeter, offset 3.1mm inward from edge |
| Neck purfling | 2.00 | 1.60 | Fretboard edges, body join to nut |
| Headstock purfling | 2.00 | 1.60 | Headstock perimeter, 82×190mm |

## G-code Files

| File | Purpose | Lines | Passes | Total Depth |
|------|---------|-------|--------|-------------|
| `exports/om_binding_channel_mach4.nc` | Body binding channel (walnut) | 1,417 | 4 × 1,446mm | 5.7mm |
| `exports/om_purfling_ledge_mach4.nc` | Body purfling ledge (abalone) | 719 | 2 × 1,429mm | 1.6mm |
| `exports/om_purfling_neck_headstock_mach4.nc` | Neck edges + headstock perimeter | 732 | 2 × 3 ops | 1.6mm |

**Total cutting distance:** ~12,300mm across all operations

## Tool & Machine Setup

| Parameter | Value |
|-----------|-------|
| Machine | Mach4_Router_4x8 |
| Tool | T1 — 2mm straight bit |
| Spindle | 18,000 RPM |
| Feed XY (body) | 600 mm/min |
| Feed XY (neck/headstock) | 400 mm/min |
| Feed Z (plunge) | 150–200 mm/min |
| Safe Z | 5.0mm |

## Coordinate System

- **Origin:** X=0 at body centerline, Y=0 at tail end
- **Z=0:** Top surface of soundboard (body files) / fretboard surface (neck file)
- **Body perimeter:** 343 points from parametric Bézier outline, 384mm wide × 495mm long
- **Neck:** 101 points per edge, linear taper from heel (57mm) to nut (44.5mm), 358mm length
- **Headstock:** 137-point rectangle with 8mm corner radii, 82mm × 190mm

## Operation Sequence

1. **Mount body** — vacuum table or registration pins, soundboard up
2. **Run binding channel** (`om_binding_channel_mach4.nc`) — 4 depth passes at 1.5/1.5/1.5/1.2mm
3. **Run purfling ledge** (`om_purfling_ledge_mach4.nc`) — 2 depth passes at 0.8/0.8mm
4. **Re-fixture for neck** — Z-zero on fretboard surface
5. **Run neck/headstock purfling** (`om_purfling_neck_headstock_mach4.nc`)
   - Right fretboard edge (heel → nut)
   - Left fretboard edge (nut → heel)
   - Headstock perimeter (closed loop)
6. **Headstock note:** 14° back-angle requires tilted fixture or separate Z-zero on headstock face

## Parametric Outline

The body outline was generated parametrically from the martin_om28.json spec, NOT extracted from the DXF scan data. The DXF (om_000_body.dxf BODY_POINTS layer, 5,451 scattered points) contains vectorized blueprint scan data unsuitable for direct CNC use.

Parametric construction used cubic Bézier curves through these control regions:
- Tail curve → lower bout (192mm half-width)
- Lower bout → waist (120.5mm half-width at Y=195)
- Waist → upper bout (143mm half-width)
- Upper bout → neck shoulder (28.5mm at Y=430)

## Pipeline Gaps (OM-PURF series)

| ID | Gap | Description | Severity |
|----|-----|-------------|----------|
| OM-PURF-01 | No binding channel CAM module | Body binding channel generated with standalone script; no `app/cam/binding/` module exists | High |
| OM-PURF-02 | No purfling ledge operation | Purfling ledge is a second-pass offset of binding channel; needs dedicated step in CAM pipeline | High |
| OM-PURF-03 | No neck purfling routing | Fretboard edge purfling channels require neck-specific fixture and zero; not in any existing workflow | Medium |
| OM-PURF-04 | Headstock angle compensation | 14° headstock angle requires either tilted fixture or 4-axis interpolation for accurate channel depth | Medium |
| OM-PURF-05 | DXF scan data unusable | BODY_POINTS layer (5,451 pts) is scattered scan segments, not a contour; parametric generation was required | Medium |
| OM-PURF-06 | No material-aware feed rate | Feed rate (600mm/min) is generic; should adapt to binding material (walnut, maple, rosewood) and top wood species | Low |
| OM-PURF-07 | No cutter compensation | Toolpath uses pre-calculated offset; native G41/G42 cutter comp not used (simpler but less flexible) | Low |
| OM-PURF-08 | No channel depth verification | No probe cycle or touch-off verification step in G-code for critical depth tolerance (±0.1mm for binding fit) | Medium |

## Vectorizer Pipeline Gap Analysis (2026-03-07)

During OM purfling development, the DXF scan data (om_000_body.dxf BODY_POINTS layer, 5,451 scattered points) was found **unusable as a CNC contour** — the points are vectorized blueprint segments, not an ordered perimeter. This triggered a full audit of the blueprint-to-CNC pipeline, revealing significant disconnections between the vectorizer phases.

### Connected Path (working end-to-end)

```
Image → Phase 2 (OpenCV) → /vectorize-geometry → DXF → CAM bridge → /to-adaptive → G-code
                                                         ↑
              Calibration → /calibrate → PPI → Phase 2 scale correction
```

This is the **only complete path** from blueprint to G-code.

### Disconnected Phases

| Gap ID | Component | Issue | Severity |
|--------|-----------|-------|----------|
| VEC-GAP-01 | Phase 3.6 Vectorizer | `Phase3Vectorizer` (ML classification, OCR, primitives, scale detection) has **no API endpoint**. Only accessible via Python import or Phase 4 CLI. | Critical |
| VEC-GAP-02 | Phase 4 Dimension Linking | `phase4/pipeline.py` is CLI-only (`run_phase4.py`). No `/api/blueprint/phase4` route exists. | High |
| VEC-GAP-03 | Phase 4 Output | `PipelineResult` (arrows detected, dimensions linked) has **no consumer** — nothing in CAM or the frontend reads it. | High |
| VEC-GAP-04 | Phase 3 → CAM bridge | CAM bridge (`extraction.py`) parses LWPOLYLINE on "GEOMETRY" layer. Phase 3 writes to the same layer, so it *should* work, but there is no integration test. | Medium |
| VEC-GAP-05 | Phase 1 → Phase 3 handoff | Phase 1 (Claude AI) returns scale + dimensions. Phase 3 has its own scale detection. No code passes Phase 1's AI-detected scale into Phase 3 as a calibration hint. | Medium |
| VEC-GAP-06 | Frontend coverage | `BlueprintImporter.vue` calls `/analyze` (Phase 1) only. No UI for Phase 2 `/vectorize-geometry`, Phase 3, or calibration. `BlueprintLab.vue` has Phase 2 panel but no Phase 3. | Medium |
| VEC-GAP-07 | Phase 3 constants.py | `constants.py` imports Phase 1 + Phase 2 but has no `PHASE3_AVAILABLE` flag or import for `Phase3Vectorizer`. | Medium |
| VEC-GAP-08 | OCR dimensions unused | Phase 3.6 OCR extracts dimension text (`ocr_dimensions` in `ExtractionResult`) but nothing downstream consumes these values. | Low |

### Impact on This Purfling Work

The om_000_body.dxf contains the **output of the vectorizer pipeline** (scattered scan segments on BODY_POINTS, simplified 10-point polygon on BODY_OUTLINE). Neither was usable for CNC binding channels because:

1. **BODY_POINTS** — 5,451 points from multiple vectorized line segments, not an ordered contour. Angular sorting fails because guitar bodies are concave at the waist.
2. **BODY_OUTLINE** — 10-point bounding polygon, far too coarse for CNC precision.

The workaround was **parametric Bézier generation** from the `martin_om28.json` spec dimensions. This produced a clean 381-point outline at ~1mm resolution, suitable for binding/purfling channel toolpaths.

If the vectorizer pipeline were connected end-to-end, the correct flow would be:
```
Blueprint PDF → Phase 3 (ML contour classification) → closed BODY_OUTLINE polyline
  → offset for binding/purfling channels → G-code
```

See also: `docs/handoffs/BLUEPRINT_VECTORIZER_INTEGRATION_HANDOFF.md` (Vectorizer Pipeline Process Path Gaps section).

## Cross-References

- **Shared gaps with OM-28 Herringbone:** OM-GAP-01 (binding CAM), OM-GAP-06 (material presets)
- **Shared gaps with Benedetto:** BEN-GAP-03 (binding channel routing), BEN-GAP-04 (multi-layer purfling)
- **Flying V:** FV-GAP-07 (post-processor cutter comp), FV-GAP-09 (probe verification)
- **Vectorizer gaps:** VEC-GAP-01 through VEC-GAP-08 (above) — shared across all blueprint-to-CNC workflows
- **Parametric outline utility:** Reusable for any acoustic body — needs extraction to `app/cam/outline/parametric.py`

## Intermediate Artifacts

| File | Purpose |
|------|---------|
| `exports/om_parametric_outline.json` | 381-point Bézier body outline with construction params |
| `exports/om_binding_body_path.json` | 343-point binding channel toolpath (1mm offset) |
| `exports/om_purfling_body_path.json` | 343-point purfling ledge toolpath (3.1mm offset) |
| `exports/om_body_points.json` | Raw 5,451-point DXF extraction (reference only) |
