# Smart Guitar v3 — Pre-Cut Verification Checklist

**DXF Source:** `services/api/data/smart_guitar_v3_from_spec.dxf`
**Spec Source:** `services/api/app/instrument_geometry/body/specs/smart_guitar_v1.json`

---

## Pre-Cut Verification

- [ ] **Print DXF at 1:1 scale**
  - Lay on body blank — verify silhouette matches Explorer-Klein hybrid design
  - Body outline is parametric (not traced from tooling drawing)
  - Confirm 444.5 × 368.3mm overall dimensions

- [ ] **Select headless bridge model**
  - Options: Hipshot, ABM, Steinberger
  - Measure actual bridge height above body surface
  - Verify mounting hole spacing matches DXF (80 × 35mm pattern, 4× M3.5)

- [ ] **Confirm neck pocket angle**
  - Spec: 4.5° (Explorer reference, Les Paul is 4.0°)
  - Shim after first string-up if action adjustment needed

- [ ] **Confirm fretboard radius**
  - Spec: 304.8mm (12")
  - Required before neck build, not body cut

- [ ] **Resolve output jack angle**
  - Current spec: 15° angled bore, 12.7mm diameter, 25mm depth
  - Options:
    - Angled fixture for 15° bore
    - Redesign to straight edge-mount (simpler toolpath)

- [ ] **Test cut on scrap material**
  - Verify all toolpaths before production blank
  - Check corner radii, pocket depths, hole positions

---

## Blocking Items (Before BCAM Run)

| Item | Status | Notes |
|------|--------|-------|
| Bridge model selection | ⏳ | Affects mounting hole positions |
| Output jack fixture | ⏳ | 15° angled bore vs straight edge-mount |
| 1:1 print verification | ⏳ | Body outline is parametric approximation |

## Non-Blocking (Before Assembly)

| Item | Status | Notes |
|------|--------|-------|
| Fretboard radius | ⏳ | 304.8mm (12") — neck build requirement |
| Neck angle shim | ⏳ | Evaluate after first string-up |

---

## Cavity Summary (from spec)

| Layer | Depth | Dimensions | Position |
|-------|-------|------------|----------|
| NECK_POCKET | 15.9mm | 76.2 × 55.9mm | Centered, 53.3mm from top |
| NECK_PICKUP | 19.0mm | 92 × 40mm | Centered, 167.6mm from top |
| BRIDGE_PICKUP | 19.0mm | 92 × 40mm | Centered, 294.6mm from top |
| REAR_ELECTRONICS | 22.0mm | 95 × 65mm | x=36.8, y=275.7mm |
| ARDUINO_POCKET | 20.0mm | 80 × 60mm | x=36.8, y=133.5mm |
| BRIDGE_MOUNTING | surface | 95 × 42mm, 4× M3.5 | Centered, y=320mm |
| CONTROL_PLATE | surface | 100 × 50mm, 3× pots | x=55.2, y=346.7mm |
| USB_PORT | 7.0mm | 12 × 6.5mm slot | Edge mount, y=239.4mm |
| OUTPUT_JACK | 25.0mm | Ø12.7mm bore | x=110.4, y=391.2mm |

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| CAM Programmer | | | |
| Shop Lead | | | |

---

*Generated from Smart Guitar v1 spec. Body outline is parametric — verify against physical template before production cut.*
