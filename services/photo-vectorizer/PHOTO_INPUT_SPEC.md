# Photo Vectorizer Input Specification

## Version
v1.0 — 2026-04-06

## Supported Input Types

| `source_type` | Description | Best For |
|---------------|-------------|----------|
| `photo` | Product photos, studio shots | Real guitar images |
| `ai` | AI-generated renders | Concept art, design mockups |
| `silhouette` | High-contrast outlines | Pre-processed images |
| `blueprint` | Technical drawings | Scale drawings with dimensions |

## Known False Positives

### Guitar Stand (product photos)

**Issue:** When photographing guitars on display stands, the stand legs/base may:
1. Appear as separate contours below the body (filtered by FIX 2)
2. Merge with body contour making body appear taller (trimmed by FIX 3)

**Detection:**
- FIX 2: Contours with centroid Y > body_bottom + 20px are excluded
- FIX 3: Body height cap — if height > spec × 1.2, bottom is trimmed

**Workaround (recommended):**
- Lay guitar flat on contrasting background
- Suspend guitar from headstock (out of frame)
- Use photo editing to remove stand before processing

**Status:** Auto-filtered as of commits `1b7d9ee6` (FIX 2) and pending (FIX 3)

### Reflections on glossy finishes

**Issue:** Bright reflections on high-gloss lacquer may create false edges or split body contours.

**Workaround:**
- Use diffused lighting
- Matte spray for reference photos (if non-destructive)
- Photograph in overcast conditions

**Status:** Not auto-filtered — requires manual review

## Background Requirements

| Background | Quality | Notes |
|------------|---------|-------|
| Black/dark solid | Excellent | GrabCut extraction works reliably |
| White solid | Good | High contrast, watch for reflections |
| Gradient | Fair | May require manual threshold tuning |
| Busy/textured | Poor | Not recommended — extraction unreliable |

## Testing Log

| Date | Input Type | Conditions | Result |
|------|------------|------------|--------|
| 2026-04-06 | AI-generated (Smart Guitar) | Transparent bg, 368x444mm spec | Pass — 368.3 x 444.5 mm |
| 2026-04-06 | Professional product photo (v2) | Black bg, guitar on stand | Partial — 535.8 x 636.1 mm (stand included) |
| 2026-04-06 | Professional product photo (v3) | Black bg, guitar on stand, height cap | Pass — 623.8 x 535.8 mm (stand trimmed 15px) |

## File Naming Conventions

See `DEVELOPER_HANDOFF.md` Section 10 for recommended naming patterns.

**Anti-patterns to avoid:**
- `guitar.png` — too generic
- `Smart Guitar_1.png` — version suffix without context
- `IMG_20260406.jpg` — camera default names

**Recommended pattern:**
```
{instrument}_{view_or_purpose}.{ext}
```

Examples:
- `archtop_front_studio.jpg`
- `smart_guitar_concept_v3.png`
- `les_paul_body_silhouette.png`
