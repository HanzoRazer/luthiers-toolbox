# Pixel Calibration Results Report

**Date:** 2026-03-06
**Method:** Pixel-to-inch calibration with contour analysis
**Total Blueprints:** 33

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Processed | 33 |
| Good (reasonable dims) | 0 |
| Small contour (detection issue) | 11 |
| Oversized (PPI too low) | 0 |
| Undersized (PPI too high) | 22 |
| Failed | 0 |

**Note:** Most calibration issues are due to unknown paper size or multi-view PDF layouts.

---

## Results by Quality

### Good Detections (Reasonable Dimensions)

| Blueprint | Body (in) | Pixels | PPI | Confidence |
|-----------|-----------|--------|-----|------------|
| *No good detections* | - | - | - | - |

### Small Contour Detections (Wrong element found)

These blueprints have very small pixel measurements, indicating the detector
found a small element (legend, logo, thumbnail) instead of the guitar body.

- **Fender Stratocaster 62**: 130x179px detected
- **Fender Jazzmaster**: 17x16px detected
- **Gibson Explorer**: 7x119px detected
- **Gibson Flying V 58**: 37x68px detected
- **Gretsch Billy Bo**: 65x182px detected
- **Gretsch Duo Jet**: 182x71px detected
- **Danelectro DC 59**: 135x101px detected
- **Harmony H44 Stratotone**: 8x101px detected
- **Blackmachine B7**: 100x100px detected
- **First Act Rick Nielsen**: 180x138px detected
- **Zambon Template**: 70x61px detected

### Undersized/Oversized Results

These blueprints have reasonable pixel measurements but incorrect PPI estimation.

- **Charvel 5150**: 1601x10px -> 2.5x0.0" (PPI: 645)
- **Fender Telecaster**: 3234x4861px -> 11.4x7.6" (PPI: 426)
- **Fender Mustang**: 3x2704px -> 6.3x0.0" (PPI: 432)
- **Gibson Les Paul 59**: 1452x980px -> 5.3x3.6" (PPI: 274)
- **Gibson SG JR 63**: 635x541px -> 2.1x1.8" (PPI: 306)
- **Gibson 335**: 77x216px -> 0.4x0.1" (PPI: 600)
- **Gibson Melody Maker**: 77x216px -> 0.4x0.1" (PPI: 600)
- **Gretsch Astro Jet**: 330x5058px -> 10.9x0.7" (PPI: 464)
- **Danelectro Double Cut**: 281x4px -> 0.4x0.0" (PPI: 645)
- **Epiphone Coronet 66**: 306x829px -> 2.0x0.8" (PPI: 409)
- **DBZ Bird of Prey**: 336x783px -> 1.0x0.5" (PPI: 750)
- **Washburn N4**: 545x505px -> 0.9x0.8" (PPI: 611)
- **Mosrite Ventures II**: 4828x6600px -> 11.0x8.1" (PPI: 600)
- **Squier Hypersonic**: 54x2152px -> 3.9x0.1" (PPI: 551)
- **Rick Turner Model 1**: 4707x6784px -> 11.6x8.0" (PPI: 585)
- **Blackmachine B6**: 378x5054px -> 6.3x0.5" (PPI: 801)
- **Strandberg Boden 6**: 537x1493px -> 2.1x0.7" (PPI: 725)
- **Music Man Petrucci**: 528x329px -> 0.8x0.5" (PPI: 681)
- **Brian May Red Special**: 326x751px -> 1.3x0.6" (PPI: 579)
- **Klein Guitar**: 1155x2300px -> 5.3x2.7" (PPI: 432)
- **MSK MK1HH24**: 480x1083px -> 1.8x0.8" (PPI: 611)
- **Gretsch Lap Steel**: 502x74px -> 1.1x0.2" (PPI: 468)

---

## All Extracted Dimensions

| Blueprint | Body Length | Body Width | Pixels | PPI | Quality |
|-----------|-------------|------------|--------|-----|---------|
| Charvel 5150 | 2.48" | 0.02" | 1601x10 | 645 | UNDERSIZED |
| Fender Stratocaster 62 | 0.42" | 0.31" | 130x179 | 426 | SMALL_CONTOUR |
| Fender Telecaster | 11.41" | 7.59" | 3234x4861 | 426 | UNDERSIZED |
| Fender Jazzmaster | 0.04" | 0.04" | 17x16 | 426 | SMALL_CONTOUR |
| Fender Mustang | 6.26" | 0.01" | 3x2704 | 432 | UNDERSIZED |
| Gibson Les Paul 59 | 5.31" | 3.58" | 1452x980 | 274 | UNDERSIZED |
| Gibson SG JR 63 | 2.08" | 1.77" | 635x541 | 306 | UNDERSIZED |
| Gibson 335 | 0.36" | 0.13" | 77x216 | 600 | UNDERSIZED |
| Gibson Explorer | 0.25" | 0.01" | 7x119 | 477 | SMALL_CONTOUR |
| Gibson Flying V 58 | 0.11" | 0.06" | 37x68 | 645 | SMALL_CONTOUR |
| Gibson Melody Maker | 0.36" | 0.13" | 77x216 | 600 | UNDERSIZED |
| Gretsch Astro Jet | 10.89" | 0.71" | 330x5058 | 464 | UNDERSIZED |
| Gretsch Billy Bo | 0.30" | 0.11" | 65x182 | 611 | SMALL_CONTOUR |
| Gretsch Duo Jet | 0.71" | 0.28" | 182x71 | 257 | SMALL_CONTOUR |
| Danelectro DC 59 | 0.22" | 0.17" | 135x101 | 611 | SMALL_CONTOUR |
| Danelectro Double Cut | 0.44" | 0.01" | 281x4 | 645 | UNDERSIZED |
| Harmony H44 Stratotone | 0.20" | 0.02" | 8x101 | 504 | SMALL_CONTOUR |
| Epiphone Coronet 66 | 2.03" | 0.75" | 306x829 | 409 | UNDERSIZED |
| DBZ Bird of Prey | 1.04" | 0.45" | 336x783 | 750 | UNDERSIZED |
| Washburn N4 | 0.89" | 0.83" | 545x505 | 611 | UNDERSIZED |
| Mosrite Ventures II | 11.00" | 8.05" | 4828x6600 | 600 | UNDERSIZED |
| Squier Hypersonic | 3.91" | 0.10" | 54x2152 | 551 | UNDERSIZED |
| Rick Turner Model 1 | 11.59" | 8.04" | 4707x6784 | 585 | UNDERSIZED |
| Blackmachine B6 | 6.31" | 0.47" | 378x5054 | 801 | UNDERSIZED |
| Blackmachine B7 | 0.31" | 0.31" | 100x100 | 322 | SMALL_CONTOUR |
| Strandberg Boden 6 | 2.06" | 0.74" | 537x1493 | 725 | UNDERSIZED |
| Music Man Petrucci | 0.78" | 0.48" | 528x329 | 681 | UNDERSIZED |
| Brian May Red Special | 1.30" | 0.56" | 326x751 | 579 | UNDERSIZED |
| Klein Guitar | 5.32" | 2.67" | 1155x2300 | 432 | UNDERSIZED |
| MSK MK1HH24 | 1.77" | 0.79" | 480x1083 | 611 | UNDERSIZED |
| First Act Rick Nielsen | 0.33" | 0.26" | 180x138 | 539 | SMALL_CONTOUR |
| Zambon Template | 0.23" | 0.20" | 70x61 | 300 | SMALL_CONTOUR |
| Gretsch Lap Steel | 1.07" | 0.16" | 502x74 | 468 | UNDERSIZED |

---

## Recommendations

For accurate dimension extraction from blueprints:

1. **Best approach**: Use a known scale length or ruler marking for calibration
2. **For PDFs with dimensions**: Extract text annotations (requires OCR for scanned blueprints)
3. **For multi-view PDFs**: Manually select the body view for measurement

### Blueprints Needing Manual Calibration

- Charvel 5150 (scale: 25.5")
- Fender Stratocaster 62 (scale: 25.5")
- Fender Telecaster (scale: 25.5")
- Fender Jazzmaster (scale: 25.5")
- Fender Mustang (scale: 24.0")
- Gibson Les Paul 59 (scale: 24.75")
- Gibson SG JR 63 (scale: 24.75")
- Gibson 335 (scale: 24.75")
- Gibson Explorer (scale: 24.75")
- Gibson Flying V 58 (scale: 24.75")
- Gibson Melody Maker (scale: 24.75")
- Gretsch Astro Jet (scale: 24.6")
- Gretsch Billy Bo (scale: 24.75")
- Gretsch Duo Jet (scale: 24.6")
- Danelectro DC 59 (scale: 25.0")
- Danelectro Double Cut (scale: 25.0")
- Harmony H44 Stratotone (scale: 24.0")
- Epiphone Coronet 66 (scale: 24.75")
- DBZ Bird of Prey (scale: 25.5")
- Washburn N4 (scale: 25.5")
- Mosrite Ventures II (scale: 24.75")
- Squier Hypersonic (scale: 25.5")
- Rick Turner Model 1 (scale: 24.75")
- Blackmachine B6 (scale: 25.5")
- Blackmachine B7 (scale: 26.5")
- Strandberg Boden 6 (scale: 25.5")
- Music Man Petrucci (scale: 25.5")
- Brian May Red Special (scale: 24.0")
- Klein Guitar (scale: 25.5")
- MSK MK1HH24 (scale: 24.0")
- First Act Rick Nielsen (scale: 25.5")
- Zambon Template
- Gretsch Lap Steel (scale: 22.5")

---

*Generated by Luthier's Toolbox Pixel Calibration System v4.0.0*