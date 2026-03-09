# GridZoneClassifier Batch Test Report

**Date:** 2026-03-06
**Test Version:** 4.0.0
**Classifier:** GridZoneClassifier with ELECTRIC_GUITAR_GRID

---

## Executive Summary

The GridZoneClassifier was tested against a diverse collection of 28 electric guitar blueprints spanning multiple manufacturers and body styles. The classifier demonstrated strong performance with **100% processing success rate** and **89% confident classifications**.

| Metric | Value |
|--------|-------|
| Total Blueprints | 28 |
| Successfully Processed | 28 (100%) |
| Confident Classifications | 25 (89%) |
| Average Symmetry Score | 0.690 |

---

## Test Collection

The following blueprints were processed:

| # | Blueprint | Manufacturer | Style |
|---|-----------|--------------|-------|
| 1 | Charvel 5150 | Charvel | Superstrat |
| 2 | Gretsch Astro Jet | Gretsch | Jet |
| 3 | Gretsch Billy Bo Jupiter Thunderbird | Gretsch | Offset |
| 4 | Gretsch Duo Jet | Gretsch | Jet |
| 5 | Gretsch Duo Jet pt 2 | Gretsch | Jet |
| 6 | Epiphone Coronet 66 | Epiphone | Single Cut |
| 7 | Danelectro DC 59 | Danelectro | Double Cut |
| 8 | Danelectro DC 59 v2 | Danelectro | Double Cut |
| 9 | Danelectro Double Cut | Danelectro | Double Cut |
| 10 | Harmony H44 Stratotone | Harmony | Vintage |
| 11 | Blackmachine B6 | Blackmachine | Modern |
| 12 | Blackmachine B7 | Blackmachine | Modern 7-string |
| 13 | Blackmachine B7 Alt | Blackmachine | Modern 7-string |
| 14 | Blackmachine B7 Headstock | Blackmachine | Detail |
| 15 | Strandberg Boden 6 | Strandberg | Headless Ergonomic |
| 16 | DBZ Bird of Prey | DBZ | Extreme |
| 17 | Washburn N4 | Washburn | Superstrat |
| 18 | Washburn N4 Neck | Washburn | Detail |
| 19 | Brian May Red Special | Custom | Semi-hollow |
| 20 | Klein Guitar | Klein | Ergonomic |
| 21 | Klein Template | Klein | Ergonomic |
| 22 | Rick Turner Model 1 | Rick Turner | Boutique |
| 23 | Mosrite Ventures II | Mosrite | Vintage |
| 24 | MSK MK1HH24 | MSK Guitars | Modern |
| 25 | Squier Hypersonic | Squier | Offset |
| 26 | First Act Rick Nielsen | First Act | Signature |
| 27 | Zambon | Zambon | Custom |
| 28 | Gretsch Lap Steel | Gretsch | Lap Steel |

---

## Classification Results

### Detailed Results Table

| # | Blueprint | Category | Symmetry | Confident | Notes |
|---|-----------|----------|----------|-----------|-------|
| 1 | Charvel 5150 | BODY_OUTLINE | 0.70 | Yes | Standard superstrat shape |
| 2 | Gretsch Astro Jet | BODY_OUTLINE | 0.90 | Yes | Well-centered jet body |
| 3 | Gretsch Billy Bo | BODY_OUTLINE | 0.69 | Yes | Offset thunderbird shape |
| 4 | Gretsch Duo Jet | BODY_OUTLINE | 0.63 | Yes | Classic jet proportions |
| 5 | Gretsch Duo Jet pt 2 | BODY_OUTLINE | 1.00 | Yes | Perfect symmetry |
| 6 | Epiphone Coronet 66 | BODY_OUTLINE | 0.24 | No | Single cutaway - asymmetric |
| 7 | Danelectro DC 59 | BODY_OUTLINE | 0.91 | Yes | Symmetric double cut |
| 8 | Danelectro DC 59 v2 | BODY_OUTLINE | 0.91 | Yes | Symmetric double cut |
| 9 | Danelectro Double Cut | BODY_OUTLINE | 0.74 | Yes | Classic Dano shape |
| 10 | Harmony H44 Stratotone | BODY_OUTLINE | 0.79 | Yes | Vintage proportions |
| 11 | Blackmachine B6 | BODY_OUTLINE | 0.92 | Yes | Modern symmetric |
| 12 | Blackmachine B7 | BODY_OUTLINE | 0.39 | Yes | Extended range offset |
| 13 | Blackmachine B7 Alt | UPPER_BOUT | 0.80 | Yes | Headstock detail view |
| 14 | Blackmachine B7 Headstock | BODY_OUTLINE | 0.61 | Yes | Partial body visible |
| 15 | Strandberg Boden 6 | UPPER_BOUT | 0.17 | Yes | Headless ergonomic |
| 16 | DBZ Bird of Prey | BODY_OUTLINE | 0.52 | Yes | Extreme offset design |
| 17 | Washburn N4 | UNKNOWN | 0.16 | No | Multi-view layout |
| 18 | Washburn N4 Neck | BODY_OUTLINE | 0.17 | No | Neck detail focus |
| 19 | Brian May Red Special | BODY_OUTLINE | 0.92 | Yes | Symmetric semi-hollow |
| 20 | Klein Guitar | BODY_OUTLINE | 0.52 | Yes | Ergonomic offset |
| 21 | Klein Template | BODY_OUTLINE | 0.66 | Yes | Body template |
| 22 | Rick Turner Model 1 | BODY_OUTLINE | 1.00 | Yes | Perfect symmetry |
| 23 | Mosrite Ventures II | BODY_OUTLINE | 1.00 | Yes | Perfect symmetry |
| 24 | MSK MK1HH24 | BODY_OUTLINE | 0.93 | Yes | Modern symmetric |
| 25 | Squier Hypersonic | BODY_OUTLINE | 0.78 | Yes | Offset body |
| 26 | First Act Rick Nielsen | NECK_POCKET | 0.88 | Yes | Neck pocket detail |
| 27 | Zambon | BRIDGE_ROUTE | 0.99 | Yes | Bridge template |
| 28 | Gretsch Lap Steel | BODY_OUTLINE | 0.41 | Yes | Non-standard proportions |

### Category Distribution

```
BODY_OUTLINE  ████████████████████████  23 (82%)
UPPER_BOUT    ██                         2 (7%)
NECK_POCKET   █                          1 (4%)
BRIDGE_ROUTE  █                          1 (4%)
UNKNOWN       █                          1 (4%)
```

---

## Symmetry Analysis

### Most Symmetric Bodies (Score >= 0.90)

These blueprints show classic, well-centered double-cutaway or symmetric single-cutaway designs:

| Blueprint | Symmetry Score | Body Style |
|-----------|----------------|------------|
| Gretsch Duo Jet pt 2 | 1.000 | Classic Jet |
| Rick Turner Model 1 | 1.000 | Boutique symmetric |
| Mosrite Ventures II | 1.000 | Vintage offset |
| Zambon | 0.992 | Custom template |
| MSK MK1HH24 | 0.928 | Modern superstrat |
| Blackmachine B6 | 0.920 | Modern 6-string |
| Brian May Red Special | 0.920 | Semi-hollow |
| Danelectro DC 59 | 0.910 | Double cutaway |
| Danelectro DC 59 v2 | 0.910 | Double cutaway |
| Gretsch Astro Jet | 0.900 | Jet body |

### Least Symmetric Bodies (Score < 0.50)

These represent offset, ergonomic, or asymmetric designs:

| Blueprint | Symmetry Score | Design Rationale |
|-----------|----------------|------------------|
| Washburn N4 | 0.159 | Multi-view blueprint layout |
| Strandberg Boden 6 | 0.174 | Headless ergonomic design |
| Washburn N4 Neck | 0.167 | Neck detail (not body) |
| Epiphone Coronet 66 | 0.238 | Single cutaway asymmetry |
| Blackmachine B7 | 0.386 | Extended range offset |
| Gretsch Lap Steel | 0.410 | Non-guitar proportions |

---

## Wing Extension Analysis

The classifier tracks how far body contours extend into the left and right "wing limit" zones:

| Category | Count | Description |
|----------|-------|-------------|
| Balanced | 25 | Equal wing extension (< 0.05 difference) |
| Right-heavy | 3 | More extension to right wing |
| Left-heavy | 0 | More extension to left wing |

**Observation:** Most guitar bodies are symmetric or nearly symmetric in their wing extensions, which aligns with traditional guitar design principles.

---

## Edge Cases & Learnings

### 1. Detail Views vs Full Body
Blueprints showing detail views (neck pocket, headstock, bridge) are classified by their position within the grid:
- **First Act Rick Nielsen** → NECK_POCKET (shows neck area)
- **Zambon** → BRIDGE_ROUTE (bridge template)
- **Blackmachine B7 Alt** → UPPER_BOUT (headstock detail)

### 2. Multi-Page/Multi-View Layouts
Some blueprints contain multiple views on a single page:
- **Washburn N4** → UNKNOWN (0.16 symmetry) - classifier detected combined layout

### 3. Non-Standard Body Shapes
Ergonomic and headless designs show expected low symmetry:
- **Strandberg Boden 6** (0.17) - intentionally asymmetric ergonomic design
- **Klein Guitar** (0.52) - offset ergonomic body

### 4. Single Cutaway Detection
Single cutaway bodies show moderate asymmetry:
- **Epiphone Coronet 66** (0.24) - offset toward treble side

---

## ML Feature Extraction

The classifier extracts 27 features for each contour, enabling downstream ML training:

### Feature Categories

1. **Position Features**
   - `center_x_norm`, `center_y_norm`
   - `width_norm`, `height_norm`
   - `aspect_ratio`, `area_norm`

2. **Symmetry Features**
   - `symmetry_score`
   - `offset_from_center`
   - `wing_extend_left`, `wing_extend_right`
   - `wing_balance`

3. **Zone Overlap Features**
   - `zone_body_canvas_overlap`
   - `zone_neck_pocket_overlap`
   - `zone_bridge_zone_overlap`
   - `zone_upper_bout_left_overlap`
   - `zone_upper_bout_right_overlap`
   - `zone_wing_limit_left_overlap`
   - `zone_wing_limit_right_overlap`
   - (+ additional zone overlaps)

4. **Confidence Features**
   - `zone_count`
   - `primary_zone_confidence`
   - `zone_ambiguity`

---

## Recommendations

### For Training Data Collection
1. Include more single-cutaway designs to balance dataset
2. Add acoustic body outlines for cross-category testing
3. Consider multi-page blueprints as separate training samples

### For Classifier Improvements
1. Add contour shape analysis (not just bounding box)
2. Implement multi-contour voting for complex layouts
3. Consider page layout detection before body extraction

### For Production Use
1. Use confidence threshold of 0.5 for automated classification
2. Flag low-symmetry results for human review
3. Combine with contour-based classifiers for higher accuracy

---

## Appendix: Raw JSON Results

Full results are available in:
- `batch_classification_results.json`

---

*Report generated by GridZoneClassifier v4.0.0*
*The Production Shop Blueprint Import Service*
