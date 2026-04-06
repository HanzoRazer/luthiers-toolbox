# Sprint 4 Validation Artifacts

Generated: 2026-04-06

## Test Cases

### 1. Smart Guitar (AI-generated image)
- **Source:** `Smart Guitar.png` (AI-generated reference)
- **Spec:** `smart_guitar` (368 x 444 mm)
- **Pipeline:** `source_type='ai'`
- **Result:** 368.3 x 444.5 mm (W x H) ✓

Files:
- `smart_guitar_ai_v3.dxf` — AC1009 (R12) format
- `smart_guitar_ai_v3.svg` — 34 vertices

### 2. Archtop (Real photo, black background)
- **Source:** `archtop_test.jpg` (studio photo)
- **Spec:** `jumbo_archtop`
- **Pipeline:** `source_type='photo'`
- **Result:** 535.8 x 636.1 mm (full guitar with neck)
- **Background:** Dark detected, GrabCut extraction

Files:
- `archtop_photo_v2.dxf` — AC1009 (R12) format, 564 KB
- `archtop_photo_v2.svg` — detailed body + f-holes

## Fixes Validated

1. **FIX 1:** DXF now exports as R12 (AC1009) by default
2. **FIX 2:** Width constraint enforced via `min(scale_h, scale_w)`

## Commit
`51c195bf` — fix(vectorizer): enforce width constraint + R12 DXF format
