# Blueprint Vectorizer Benchmark Comparison

Generated: 1776090037.483265

## Summary

| File | Mode | Dims (mm) | Entities | Score | Margin | Action | Page-like | Body-like |
|------|------|-----------|----------|-------|--------|--------|-----------|-----------|
| Gibson-Melody-Maker.pdf | refined | 647x500 | 24,097 | 0.09 | 0.09 | REJECT | - | YES |
| Gibson-Melody-Maker.pdf | restored_baseline | 647x500 | 343,399 | 0.69 | 0.11 | REVIEW | - | YES |

## Mode Comparison

### Gibson-Melody-Maker.pdf

**refined**: PASS
- Dimensions: 647 x 500 mm
- Entities: 24,097
- Selection score: 0.086
- Winner margin: 0.086
- Action: RecommendationAction.REJECT
- Fallback tier: 5

**restored_baseline**: PASS
- Dimensions: 647 x 500 mm
- Entities: 343,399
- Selection score: 0.690
- Winner margin: 0.114
- Action: RecommendationAction.REVIEW

## Recommendations

Based on the benchmark results:

- Results are comparable between modes