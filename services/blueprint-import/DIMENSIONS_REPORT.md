# Guitar Blueprint Dimensions Report

**Date:** 2026-03-06
**Extraction Method:** PDF text extraction + pattern matching
**OCR Available:** No (pytesseract not installed)
**Total Blueprints:** 28

---

## Executive Summary

Dimensions were extracted from 28 electric guitar blueprint PDFs using embedded text analysis and regex pattern matching.

| Metric | Value |
|--------|-------|
| Total Blueprints | 28 |
| Scale Length Found | 9 (32%) |
| High Confidence | 10 (36%) |
| Body Dimensions Found | 0 |

**Note:** Many blueprints are scanned images without embedded text. Installing pytesseract (OCR) would significantly improve extraction rates.

---

## Extracted Dimensions

### Blueprints with Scale Length Detected

| Blueprint | Scale Length | mm | Brand Match |
|-----------|--------------|-----|-------------|
| Gretsch Astro Jet | 24.60" | 624.8 | Gibson (24.75") |
| Blackmachine B6 | 22.00" | 558.8 | Short scale |
| Strandberg Boden 6 | 25.50" | 647.7 | Fender |
| DBZ Bird of Prey | 25.50" | 647.7 | Fender |
| Brian May Red Special | 24.00" | 609.6 | Jaguar/Mustang |
| Klein Guitar | 30.67" | 779.0 | Custom (baritone?) |
| Klein Template | 33.00" | 838.2 | Custom (bass?) |
| MSK MK1HH24 | 24.00" | 609.6 | Jaguar/Mustang |
| Zambon | 32.00" | 812.8 | Custom |

### Nut Widths Detected

| Blueprint | Nut Width |
|-----------|-----------|
| Strandberg Boden 6 | 42mm |
| MSK MK1HH24 | 43mm |

---

## Scale Length Distribution

```
Fender (25.5")     ██  2 guitars
Jaguar (24.0")     ██  2 guitars
Gibson (24.75")    █   1 guitar
Short Scale (22")  █   1 guitar
Custom (30-33")    ███ 3 guitars (possibly mm misread)
```

---

## Pixel Measurements (All Blueprints)

The following measurements were extracted from contour analysis:

| Blueprint | Body Width (px) | Body Height (px) | Aspect Ratio |
|-----------|-----------------|------------------|--------------|
| Charvel 5150 | 668 | 1112 | 0.60 |
| Gretsch Astro Jet | 4185 | 5697 | 0.73 |
| Gretsch Billy Bo | 3006 | 4200 | 0.72 |
| Gretsch Duo Jet | 135 | 165 | 0.82 |
| Gretsch Duo Jet pt 2 | 135 | 165 | 0.82 |
| Epiphone Coronet 66 | 135 | 165 | 0.82 |
| Danelectro DC 59 | 512 | 706 | 0.73 |
| Danelectro DC 59 v2 | 512 | 706 | 0.73 |
| Danelectro Double Cut | 135 | 165 | 0.82 |
| Harmony H44 Stratotone | 135 | 165 | 0.82 |
| Blackmachine B6 | 3262 | 6173 | 0.53 |
| Blackmachine B7 | 1406 | 8900 | 0.16 |
| Blackmachine B7 Alt | 2045 | 1833 | 1.12 |
| Blackmachine B7 Headstock | 135 | 165 | 0.82 |
| Strandberg Boden 6 | 9246 | 6625 | 1.40 |
| DBZ Bird of Prey | 1075 | 1912 | 0.56 |
| Washburn N4 | 1070 | 1568 | 0.68 |
| Washburn N4 Neck | 135 | 165 | 0.82 |
| Brian May Red Special | 1581 | 3237 | 0.49 |
| Klein Guitar | 6106 | 6606 | 0.92 |
| Klein Template | 5737 | 5729 | 1.00 |
| Rick Turner Model 1 | 1650 | 3264 | 0.51 |
| Mosrite Ventures II | 135 | 165 | 0.82 |
| MSK MK1HH24 | 8748 | 8680 | 1.01 |
| Squier Hypersonic | 135 | 165 | 0.82 |
| First Act Rick Nielsen | 135 | 165 | 0.82 |
| Zambon | 708 | 1266 | 0.56 |
| Gretsch Lap Steel | 135 | 165 | 0.82 |

**Note:** Many blueprints show 135x165 pixels - these are likely thumbnail-sized or metadata images from PDFs without full-page renders.

---

## Body Shape Analysis (from Aspect Ratios)

### Standard Guitar Bodies (aspect ratio 0.5-0.8)
- Charvel 5150 (0.60)
- Gretsch Astro Jet (0.73)
- Gretsch Billy Bo (0.72)
- Danelectro DC 59 (0.73)
- Blackmachine B6 (0.53)
- DBZ Bird of Prey (0.56)
- Washburn N4 (0.68)
- Brian May Red Special (0.49)
- Rick Turner Model 1 (0.51)
- Zambon (0.56)

### Extended/Multi-Scale Bodies (aspect ratio < 0.5 or > 1.0)
- Blackmachine B7 (0.16) - likely multi-view layout
- Strandberg Boden 6 (1.40) - landscape orientation
- Klein Guitar (0.92) - nearly square
- Klein Template (1.00) - square template
- MSK MK1HH24 (1.01) - square multi-view

---

## Blueprints Without Embedded Dimensions

The following blueprints had no embedded text or no dimension patterns detected:

1. Charvel 5150
2. Gretsch Duo Jet
3. Gretsch Duo Jet pt 2
4. Epiphone Coronet 66
5. Danelectro Double Cut
6. Harmony H44 Stratotone
7. Blackmachine B7
8. Blackmachine B7 Alt
9. Blackmachine B7 Headstock
10. Washburn N4
11. Washburn N4 Neck
12. Rick Turner Model 1
13. Mosrite Ventures II
14. Squier Hypersonic
15. First Act Rick Nielsen
16. Gretsch Lap Steel

**Recommendation:** These blueprints would benefit from OCR processing with pytesseract.

---

## Known Scale Lengths (Reference)

| Scale Length | Common Guitars |
|--------------|----------------|
| 24.0" | Fender Jaguar, Mustang |
| 24.75" | Gibson Les Paul, SG, ES-335 |
| 25.0" | PRS Custom |
| 25.5" | Fender Stratocaster, Telecaster |
| 26.5" | Baritone guitars |
| 27.0" | Extended range 7-string |
| 30.0" | Bass VI |
| 34.0" | Standard bass |

---

## Technical Notes

### Extraction Methodology
1. **PDF Text Extraction:** PyMuPDF extracts embedded text from vector PDFs
2. **Pattern Matching:** Regex patterns detect dimension annotations
3. **Contour Analysis:** OpenCV measures body outlines in pixels
4. **Scale Length Filtering:** Only values 22-36" accepted as valid scale lengths

### Confidence Levels
- **High:** 5+ dimension patterns detected
- **Medium:** 2-4 dimension patterns detected
- **Low:** 0-1 dimension patterns detected

### Limitations
- No OCR available - scanned images not processed
- Body dimensions require explicit "body width/length" annotations
- Some PDFs may have dimensions in mm that appear as unrealistic inch values

---

## Files Generated

- `blueprint_dimensions.json` - Raw extraction results
- `DIMENSIONS_REPORT.md` - This report

---

*Generated by Luthier's Toolbox Blueprint Dimension Extractor v4.0.0*
