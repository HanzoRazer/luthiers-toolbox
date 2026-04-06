# Blueprint Vectorizer — Accuracy Disclaimer

## Dimensional Accuracy of Extracted Contours

The Production Shop blueprint vectorizer extracts instrument
body outlines from scanned PDF blueprints and photographic
sources. Extracted dimensions should be treated as a **working
reference**, not a precision measurement. Users should verify
critical dimensions against physical templates or original
specification documents before committing to CNC toolpaths.

## Expected Accuracy Range

Validated against three Tier 1 reference instruments at 400 DPI:

| Instrument | Body Type | Width Error | Height Error | Rating |
|---|---|---|---|---|
| Dreadnought | Acoustic steel | 7.1% | 2.5% | Excellent |
| Gibson Les Paul 59 | Electric solid | 16.5% | 19.7% | Acceptable |
| Cuatro Puertorriqueño | Latin American | 2.6% | 2.6% | Excellent |

Typical accuracy range: **±3% to ±20%** of true body dimensions.

## Technical Factors Affecting Accuracy

**1. Source document quality**
PDF blueprints scanned from physical drawings introduce
rasterization noise, paper distortion, and perspective
artifacts. A blueprint scanned at a slight angle can introduce
5-10mm of dimensional error across a 500mm body before the
vectorizer runs.

**2. Blueprint layout complexity**
Blueprints containing multiple views, dimension annotations,
hardware details, or neck geometry on the same page require
the classifier to distinguish body outline from surrounding
elements. Complex electric guitar layouts with multi-view
drawings are the most challenging case and carry the highest
error margin.

**3. Scale calibration**
Dimensional accuracy depends on correct scale detection.
When the BlueprintAnalyzer AI scale pre-pass is unavailable
(no API key configured), the vectorizer falls back to
spec-based inference using known instrument dimensions.
This fallback is accurate for known instrument families
but may produce higher errors on custom or unusual designs.

**4. Body contour election**
The classifier elects the most likely body outline from all
detected contours using a multi-factor scoring model (aspect
ratio, solidity, size, position, symmetry). For instruments
with symmetric, uncluttered outlines the election is highly
reliable. For complex layouts the elected contour may include
adjacent geometry such as neck extensions, producing a
systematic height overestimate.

**5. Physical resolution limit**
At 400 DPI rasterization, one pixel represents approximately
0.063mm. The physical noise floor of a scanned document limits
achievable precision to approximately ±5-10mm regardless of
algorithm quality.

## Recommended Workflow

1. Extract contour using Blueprint Lab (raw mode for maximum fidelity)
2. Open DXF in CAM software (Fusion 360, VCarve, FreeCAD)
3. Measure extracted body dimensions against known spec
4. Apply uniform scale correction if required
5. Verify critical features against physical template before cutting

## What the Vectorizer Is and Is Not

IS      → A rapid digitization tool for analog blueprints
and physical templates
IS      → A starting point for CAM work that would otherwise
require manual tracing or professional scanning
IS NOT  → A precision measurement instrument
IS NOT  ��� A substitute for physical template verification
before first cut
IS NOT  → Guaranteed accurate for blueprints with multiple
views, heavy annotation, or non-standard layouts

## Improving Accuracy

Accuracy improves significantly with:
- Clean single-view blueprints (body outline only, no annotations)
- Flatbed scans at 300-600 DPI (preferred over phone photographs)
- Known instrument family specified via --type flag
- ANTHROPIC_API_KEY configured for AI-assisted scale detection

---
