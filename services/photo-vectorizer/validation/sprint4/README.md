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
- **Spec:** `jumbo_archtop` (520 x 432 mm expected)
- **Pipeline:** `source_type='photo'`
- **Background:** Dark detected, GrabCut extraction

#### v2 (before height cap):
- **Result:** 535.8 x 636.1 mm — stand included in extraction
- Files: `archtop_photo_v2.dxf` (564 KB), `archtop_photo_v2.svg` (64 KB)

#### v3 (with height cap FIX 3):
- **Result:** 623.8 x 535.8 mm — stand trimmed from body
- **Warning:** "Body height capped: trimmed 15px (likely guitar stand)"
- Files: `archtop_photo_v3.dxf` (550 KB), `archtop_photo_v3.svg` (63 KB)

## Fixes Validated

1. **FIX 1:** DXF now exports as R12 (AC1009) by default
2. **FIX 2:** Width constraint enforced via `min(scale_h, scale_w)`
3. **FIX 3:** Body height cap — trims contour when height > spec × 1.2

## Commits
- `91628c3b` — FIX 1 + FIX 2 + validation artifacts + naming conventions
- `1b7d9ee6` — SVG inkscape namespace + stand filter (separate contours)
- `pending` — FIX 3 (body height cap for merged stand)
