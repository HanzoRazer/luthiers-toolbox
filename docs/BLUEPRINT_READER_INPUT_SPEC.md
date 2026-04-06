# Blueprint Reader — Input Specification

**Version:** 1.0-draft  
**Status:** Living document — updated as testing continues  
**Repo:** HanzoRazer/blueprint-reader  

---

## Overview

The Blueprint Reader accepts four input types: scanned PDFs, photographs of physical instruments or templates, AI-generated renders, and hand-drawn sketches. Each input type has different requirements and produces different accuracy results.

This document defines what makes a good input, what to avoid, and how to photograph or generate an image that will produce the best DXF output.

---

## Section 1 — Input Types

| Input Type | Source Type Flag | Recommended | Notes |
|---|---|---|---|
| Flatbed scan (300-600 DPI) | `photo` | ✅ Best | Most accurate |
| Clean PDF blueprint | `blueprint` | ✅ Best | Single view only |
| AI render (solid background) | `ai` + `spec_name` | ✅ Good | 500× faster than photo path |
| Phone photo (good light) | `photo` | ⚠️ Acceptable | See Section 3 |
| Phone photo (outdoors) | `photo` | ⚠️ Testing | Results pending |
| Hand-drawn sketch | `photo` | ⚠️ Testing | Results pending |
| Photo with complex background | `photo` | ❌ Poor | May fail |
| Gloss finish instrument photo | `photo` | ❌ Poor | Reflections confuse edge detection |

---

## Section 2 — Best Results (Guaranteed)

Follow these guidelines for the most reliable DXF output.

### 2.1 Flatbed Scanner (Highest Accuracy)

- **DPI:** 300 minimum, 400-600 preferred
- **Background:** Scanner bed (white or black)
- **Orientation:** Instrument flat on bed, no angle
- **Lighting:** Built-in scanner light only — no additional lighting
- **File format:** PNG or TIFF preferred over JPEG
- **Expected accuracy:** ±3-8% of true dimensions

### 2.2 PDF Blueprints

- **Version:** Any — vectorizer handles multiple DXF/DWG versions
- **Layout:** Single body view preferred
- **Annotations:** Dimension lines and text are acceptable — the vectorizer isolates the body outline
- **Multi-view blueprints:** May produce multiple contours — use `source_type: "blueprint"` flag
- **Expected accuracy:** ±2-7% of true dimensions

### 2.3 AI Renders (Fastest Processing)

- **Background:** Solid color — white, black, or neutral gray preferred
- **Contrast:** High contrast between instrument and background
- **Orientation:** Portrait (body vertical) preferred — auto-rotate handles landscape
- **Required flag:** `source_type: "ai"` AND `spec_name: "<instrument>"` 
- **Available spec names:** `stratocaster`, `telecaster`, `les_paul`, `es335`, `dreadnought`, `om_000`, `jumbo`, `smart_guitar`, `jumbo_archtop`, `classical`, `j45`, `flying_v`, `bass_4string`, `gibson_sg`
- **Processing time:** ~286ms (vs 141 seconds for photo path)
- **Expected accuracy:** Matches spec dimensions exactly (instrument_spec scale source)

---

## Section 3 — Acceptable Inputs (Usually Works)

### 3.1 Phone Photography — Controlled Conditions

**DO:**
- Lay instrument flat on a solid-color surface (white sheet, kraft paper, concrete floor)
- Shoot directly overhead — camera parallel to instrument surface
- Use even diffuse lighting — overcast daylight or softbox
- Fill the frame with the instrument
- Keep the instrument fully in frame with some margin
- Use the highest resolution your phone supports

**DON'T:**
- Shoot at an angle — perspective distortion degrades accuracy
- Allow shadows across the instrument body
- Use flash directly — creates hotspots and reflection
- Include hands, straps, cases, or other objects in frame

**Expected accuracy:** ±8-20% depending on conditions

### 3.2 Phone Photography — Outdoor (Testing in Progress)

Results pending systematic testing. Known variables:

| Variable | Expected Impact | Tested |
|---|---|---|
| Direct sunlight | High — glare and harsh shadows | ❌ |
| Overcast daylight | Low — diffuse even light | ❌ |
| Grass background | High — complex texture | ❌ |
| Concrete background | Medium — neutral texture | ❌ |
| Asphalt background | Medium — dark neutral | ❌ |
| Shadow patterns on instrument | High — false edges | ❌ |

*Update this table as tests are completed.*

---

## Section 4 — Not Recommended

### 4.1 Complex Backgrounds

The photo vectorizer uses background removal algorithms (GrabCut, threshold) that require contrast between the instrument edge and the background. Complex backgrounds with similar colors or textures to the instrument cause edge detection failures.

**Problematic backgrounds:**
- Patterned rugs or fabric
- Woodgrain tables (similar color to wooden instruments)
- Cluttered workbenches
- Grass, leaves, or outdoor vegetation
- Other instruments in the frame

**Workaround:** Place a solid-color sheet under the instrument before photographing.

### 4.2 Gloss and Reflective Finishes

High-gloss instrument finishes reflect light sources back to the camera, creating bright spots that the edge detector misidentifies as body edges.

**Affected finishes:** Mirror gloss, metallic flake, high-gloss nitrocellulose lacquer

**Less affected:** Satin finish, matte finish, raw wood, painted solid colors

**Workaround:** Photograph under diffuse overcast light or use a polarizing filter on the camera lens to reduce reflections.

### 4.3 Dark Instruments Against Dark Backgrounds

Contrast between instrument edge and background is required for edge detection. A dark sunburst or black instrument against a dark background will fail.

**Workaround:** Use a white or light gray background sheet.

---

## Section 5 — Will Fail (Documented Failures)

| Condition | Failure Mode | Workaround |
|---|---|---|
| No background contrast | 0 contours detected | Use solid contrasting background |
| Multiple instruments in frame | Wrong instrument elected as body | One instrument per image |
| Extreme perspective angle | Distorted dimensions | Shoot overhead only |
| Image resolution below 300px | No usable edges | Minimum 800×600px recommended |
| Heavily annotated PDF (dense) | Multiple contours, wrong election | Request single-view PDF from source |

---

## Section 6 — How to Shoot a Good Photo

### The Two-Minute Setup

```
1. Find a solid-color surface:
   White sheet, kraft paper, concrete floor, or
   large piece of cardboard — anything solid and
   contrasting with your instrument color

2. Lay the instrument flat:
   Body flat on the surface
   No neck support — let the headstock rest naturally

3. Position your camera:
   Directly overhead — phone held parallel to floor
   Instrument centered in frame
   Full body visible with 5-10% margin on all sides

4. Check the light:
   No direct sun creating harsh shadows
   No flash — turn it off
   Even light from all directions preferred

5. Shoot:
   Highest resolution
   One shot directly overhead
   Check that the full body is in frame
```

### Quick Reference Card

```
✅ Solid background
✅ Overhead shot only
✅ Even diffuse light
✅ Full instrument in frame
✅ Highest resolution
✅ No flash

❌ Angled shots
❌ Shadows on instrument
❌ Complex backgrounds
❌ Flash
❌ Multiple instruments
❌ Cropped body
```

---

## Section 7 — AI Render Requirements

When generating reference images with an AI image generator (Midjourney, DALL-E, Stable Diffusion, etc.) for use with `source_type: "ai"`:

### Required Prompt Elements

```
"[instrument name], flat lay, overhead view, 
solid white background, no shadows, 
product photography style, centered, 
full body visible"
```

### Recommended Prompt Elements

```
"studio lighting, white seamless background,
isolated on white, top-down view,
no neck visible [if body-only spec]"
```

### What to Avoid in AI Prompts

```
❌ "dramatic lighting" — creates shadows
❌ "lifestyle photo" — adds background elements  
❌ "hands holding" — obstructs body edges
❌ "close-up" — may crop the body
❌ "vintage photo" — adds noise and artifacts
```

### Pairing with spec_name

Always pair AI renders with the correct `spec_name` for accurate dimensions:

```
AI render of a Les Paul → spec_name: "les_paul"
AI render of a Strat   → spec_name: "stratocaster"
AI render of a Dread   → spec_name: "dreadnought"
```

Without `spec_name`, the AI path cannot apply known instrument dimensions and will fall back to less accurate scale estimation.

---

## Section 8 — Accuracy Reference

Validated test results as of Sprint 4:

| Instrument | Source Type | Width Error | Height Error | Rating |
|---|---|---|---|---|
| Smart Guitar (AI render) | `ai` | — | — | instrument_spec |
| Les Paul (AI render) | `ai` | — | — | instrument_spec |
| Dreadnought (AI render) | `ai` | — | — | instrument_spec |
| Stratocaster (AI render) | `ai` | — | — | instrument_spec |
| Dreadnought (flatbed scan) | `photo` | 7.1% | 2.5% | Excellent |
| Gibson Les Paul 59 (scan) | `photo` | 16.5% | 19.7% | Acceptable |
| Cuatro (scan) | `photo` | 2.6% | 2.6% | Excellent |

*AI path dimensions match instrument spec exactly when spec_name is provided.*  
*Photo path accuracy varies by blueprint complexity — see VECTORIZER_ACCURACY.md for full technical details.*

---

## Section 9 — Testing Log

Use this section to record results as new input types are tested.

| Date | Input Type | Conditions | Result | Notes |
|---|---|---|---|---|
| 2026-04-06 | AI render (Smart Guitar) | solid bg, source_type:ai | ✅ Pass | 368×444mm exact spec |
| 2026-04-06 | AI render (4 specs) | les_paul, strat, dread, smart_guitar | ✅ Pass | all exact |
| 2026-04-06 | Product photo (archtop) | black bg, guitar on stand | ⚠️ Partial | body extracted, stand merged, f-holes missing (sunburst) |
| 2026-04-06 | Wrong source file | Smart Guitar_1.png vs Smart Guitar.png | ❌ Fail | user error — naming convention |
| — | Phone photo outdoors | Overcast | ❓ Pending | — |
| — | Phone photo outdoors | Direct sun | ❓ Pending | — |
| — | Dark instrument dark background | — | ❓ Pending | — |
| — | Gloss finish instrument | — | ❓ Pending | — |
| — | Hand-drawn sketch | — | ❓ Pending | — |
| — | Physical template on floor | — | ❓ Pending | — |

---

## Document Maintenance

This document is updated when:
- New input types are tested
- New failure modes are discovered
- Vectorizer pipeline changes affect input requirements
- User feedback identifies undocumented edge cases

File location: `docs/BLUEPRINT_READER_INPUT_SPEC.md`  
Related: `docs/VECTORIZER_ACCURACY.md`
