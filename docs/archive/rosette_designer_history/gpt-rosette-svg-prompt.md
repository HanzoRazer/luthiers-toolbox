# GPT Prompt: Luthier's Rosette Ring SVG with Geometric Tile Extensions

---

## MASTER PROMPT — COPY EVERYTHING BELOW THIS LINE

---

You are a precision SVG engineering assistant with expertise in geometric drafting, luthier instrument construction, and CAD illustration. Your task is to generate a complete, accurate, well-structured SVG file depicting a **guitar rosette ring layout** as seen in a professional CAD drawing, including all concentric ring channels, radial segment divisions, geometric tile extensions on the outer edges, and technical dimension annotations.

---

## DOCUMENT SPECIFICATIONS

- **SVG canvas:** 900 × 900 px
- **Viewbox:** `0 0 900 900`
- **Center point (CX, CY):** 450, 450
- **Background:** `#f5f0e8` (warm drafting paper tone)
- **Stroke color (default):** `#1a1a2e` (near-black technical ink)
- **All geometry must be mathematically precise** using SVG path arcs, not approximations
- **Include a title block** in the lower-right corner with: Title, Scale, Units, Date fields

---

## PART 1 — THE ROSETTE RING (Primary Drawing, Left/Center)

### 1A. Overall Ring Structure

Draw a **full circular rosette** consisting of **5 concentric annular ring zones**, each representing a distinct inlay channel in a guitar soundhole rosette. All measurements are in **inches**, with `1 inch = 100 SVG units` for this drawing.

**Ring Zone Table (from innermost to outermost):**

| Zone # | Name | Inner Radius (r₁) | Outer Radius (r₂) | Radial Depth | Fill Color |
|--------|------|-------------------|-------------------|--------------|------------|
| 1 | Soundhole Binding | 1.50" (150 px) | 1.90" (190 px) | 0.40" | `#d4b483` (maple cream) |
| 2 | Inner Purfling Channel | 1.90" (190 px) | 2.10" (210 px) | 0.20" | `#c8c8c8` (silver/abalone suggestion) |
| 3 | Main Rosette Channel | 2.10" (210 px) | 3.00" (300 px) | 0.90" | **Tiled — see Part 1C** |
| 4 | Outer Purfling Channel | 3.00" (300 px) | 3.20" (320 px) | 0.20" | `#c8c8c8` |
| 5 | Outer Binding | 3.20" (320 px) | 3.50" (350 px) | 0.30" | `#d4b483` |

- Draw each ring as a full closed annular shape using SVG `<path>` with arc commands
- Ring boundaries must be drawn as thin precise circles: `stroke="#1a1a2e"` `stroke-width="0.8"` `fill="none"` overlaid on the fills
- The **center soundhole** (r < 1.50" / 150 px) should be filled `#2a1f0e` (dark void/ebony)
- Label each ring zone with a radial callout leader line pointing to the midpoint arc of the ring, with the zone name in `font-size="9"` `font-family="monospace"`

### 1B. Radial Segment Divisions

Divide the entire rosette (all ring zones) into **12 equal radial segments** at **30° intervals**, beginning at 0° (top / 12 o'clock position) and rotating clockwise.

- Draw each radial spoke as a line from inner soundhole boundary (r = 150 px) to outer binding edge (r = 350 px)
- Spoke style: `stroke="#1a1a2e"` `stroke-width="0.6"` `stroke-dasharray="none"`
- Add a **30.0°** angle annotation arc between spoke 0 and spoke 1, shown as a small arc near r = 380 px with a leader and "30.0°" label in `font-size="8"`
- The angular position of each spoke shall be: `angle_n = n × 30°`, where n = 0 through 11

### 1C. Main Rosette Channel Tile Fill (Zone 3 — the primary inlay band)

The Main Rosette Channel (r₁=210px, r₂=300px, depth=0.90") is where the decorative geometric tile motif lives. Fill this zone using **alternating geometric tile segments** as follows:

**Tile pattern — Herringbone / Alternating Trapezoid:**
- Alternate between two fill colors segment by segment:
  - **Even segments (0,2,4,6,8,10):** `#4a90d9` (blue — represents abalone/shell inlay)
  - **Odd segments (1,3,5,7,9,11):** `#b0c8e8` (light blue — represents lighter material or negative space)
- Each tile segment is an **arc-bounded trapezoid** defined by:
  - Inner arc: radius 210 px, spanning 30°
  - Outer arc: radius 300 px, spanning 30°
  - Two straight radial edges connecting inner to outer at each spoke
- Each tile path uses `<path>` with SVG arc commands: `M`, `L`, `A` 
- Add a subtle diagonal hatch stroke pattern inside each tile to suggest wood grain or inlay texture (use `<pattern>` defs or simply draw 3–4 diagonal lines per cell at 45°, `opacity="0.25"`)

### 1D. Geometric Extensions on Ring Edges (CRITICAL FEATURE)

This is the defining visual feature of the drawing. Along **both the inner edge (r=210px) and the outer edge (r=300px)** of the Main Rosette Channel, draw **geometric tile tab extensions** — trapezoidal protrusions that project outward/inward from the ring boundary, mimicking the physical tile geometry used in actual rosette construction.

**Extension geometry rules:**
- At the midpoint of each 30° segment, draw a **trapezoidal tab** that projects:
  - **Outward** (into Zone 4) by 12 px from r=300 to r=312
  - **Inward** (into Zone 2) by 10 px from r=210 to r=200
- Each tab is centered on its segment's angular midpoint (at 15°, 45°, 75°, 105°, 135°, 165°, 195°, 225°, 255°, 285°, 315°, 345°)
- Tab shape: a **parallelogram** with angular width of 10° at the ring boundary, tapering or maintaining width — matching the tile's trapezoidal geometry
- Fill tabs with the same color as their parent segment tile
- Stroke tabs with `stroke="#1a1a2e"` `stroke-width="0.8"`
- These tabs represent the physical **tongue-and-groove** or **key register** geometry that locks inlay tiles into the channel during construction

---

## PART 2 — DETAIL VIEW: INDIVIDUAL TILE PIECE (Upper Right)

Draw an **orthographic 3-view detail** of a single tile piece in the upper-right quadrant of the SVG (approximately at x=620, y=80, within a 240×200 px region).

### 2A. Tile Shape Description

The tile is a **trapezoidal parallelogram** — the physical piece a luthier would cut from wood, shell, or purfling strip. It represents one segment of the main rosette channel.

**Tile dimensions (at 1:1 scale, 1 inch = 100 SVG units):**
- **Overall width (wide end):** 1.50" (150 px)
- **Overall height (depth of channel):** 2.000" (200 px) — this is the radial depth rendered vertically for clarity in the detail view
- **Side offset (parallelogram skew):** 0.75" (75 px) on each side — the piece is skewed because it must fit the arc curvature of the ring
- **Narrow end:** 0.625" (62.5 px) — the inner arc edge is shorter than the outer arc edge
- **Side walls:** angled, not perpendicular — they represent the radial spoke cuts

**Rendered as:**
- A 4-point polygon / `<polygon>` or `<path>` showing the trapezoidal profile
- Fill: `#4a90d9` with a diagonal stripe texture (`opacity="0.3"`)
- Stroke: `#1a1a2e` `stroke-width="1.2"`

### 2B. Dimension Annotations for the Detail View

Add fully dimensioned engineering callouts in standard orthographic drafting style:

| Dimension | Value | Location |
|-----------|-------|----------|
| Overall width | 1.50" | Top horizontal leader with arrows |
| Channel depth | 2.000" | Left vertical leader with arrows |
| Left offset | 0.75" | Bottom partial leader |
| Right offset | 0.75" | Bottom partial leader |
| Narrow end | 0.625" | Right side vertical, small |
| Skew angle | ~14°–18° (computed from offsets) | Arc annotation on corner |

- All dimension lines: `stroke="#333"` `stroke-width="0.7"` with arrowheads (small filled triangles, 4px)
- All dimension text: `font-family="monospace"` `font-size="9"` `fill="#1a1a2e"`
- Extension lines extend 4px beyond the geometry before meeting the dimension line
- Dimension lines are offset 18px from the geometry edge

### 2C. Isometric / Perspective Thumbnail (Lower Right of detail region)

Below the orthographic detail (approximately x=660, y=290), draw a small **isometric projection** of the same tile piece to give 3D context:
- Show the tile as a flat slab approximately 0.08" thick (8 px in this scale)
- Apply a top face fill of `#4a90d9`, a left face fill of `#2a5a90`, a right face fill of `#3a70b0`
- Stroke all edges `#1a1a2e` `stroke-width="0.8"`
- Label: "ISO VIEW" in `font-size="7"` below the shape

---

## PART 3 — DIMENSION ANNOTATIONS ON THE RING

Add the following engineering dimension callouts to the primary ring drawing:

| Annotation | Value | Placement |
|------------|-------|-----------|
| Overall outer diameter | Ø 7.00" (Ø700px) | Horizontal spanning dimension above the ring, at y = CY − 370px, with arrows touching each outer edge |
| Main channel outer diameter | Ø 6.00" (Ø600px) | Horizontal dimension line at y = CY − 320px |
| Inner soundhole diameter | Ø 3.00" (Ø300px) | Horizontal dimension inside or below the soundhole |
| Ring zone radial depths | per Ring Zone Table | Radial callout leaders pointing to each ring, right side |
| Segment angle | 30.0° | Arc annotation between segment 0 and segment 1, near outer edge |
| Circumferential note | "12 EQUAL DIVISIONS × 30°" | Text label arced or straight, below the ring at CY + 370px, centered |

---

## PART 4 — SUPPORTING GRAPHIC ELEMENTS

### 4A. Center Registration Marks
- Draw a **center crosshair** at (450, 450): horizontal and vertical lines each 30 px long, `stroke-width="0.8"` `stroke="#1a1a2e"` `stroke-dasharray="2,2"`
- Draw a small center circle: `r="4"` `fill="none"` `stroke="#1a1a2e"` `stroke-width="0.8"`

### 4B. Section Line Indicators
- Draw a horizontal section cut line (A–A) across the full ring diameter, `stroke-dasharray="8,4,2,4"` `stroke="#1a1a2e"` `stroke-width="0.8"`
- Label both ends: "A" in a small circle `r="8"` `fill="#1a1a2e"` with white text

### 4C. Title Block (Lower Right Corner)
At approximately x=620, y=760, draw a simple bordered title block containing:
```
LUTHIER'S ROSETTE LAYOUT
Scale: 1:1  |  Units: Inches
Segments: 12  |  Angle: 30° ea.
Main Channel OD: Ø6.00"
Drawing: ROSETTE-001
```
- Box style: `stroke="#1a1a2e"` `stroke-width="1"` `fill="white"` `fill-opacity="0.85"`
- Text: `font-family="monospace"` `font-size="8"` `fill="#1a1a2e"`
- Internal horizontal dividers between each line

---

## CONSTRUCTION NOTES (Embed as SVG `<desc>` or comment block)

Include this text as an SVG comment block:
```
<!-- 
  ROSETTE CONSTRUCTION NOTES:
  - All 12 tile pieces are geometrically identical (rotational symmetry)
  - Tile skew angle compensates for arc curvature of main channel
  - Wide end (1.50") seats at outer boundary r=3.00"
  - Narrow end (0.625") seats at inner boundary r=2.10"
  - 0.75" offsets define the parallelogram skew for tangential alignment
  - Physical tile thickness: approximately 0.080" (2mm)
  - Material options: herringbone purfling strip, abalone shell, MOP, figured maple
  - Extension tabs register tile position during glue-up
  - Channel routed to depth = tile thickness + 0.005" clearance
-->
```

---

## OUTPUT REQUIREMENTS

- Output **only** the complete SVG file, beginning with `<svg` and ending with `</svg>`
- Use `<defs>` for any reusable patterns, markers (arrowheads), and gradients
- Group related elements with `<g id="...">` tags:
  - `#ring-background` — filled ring zones
  - `#ring-cells` — individual tile segments
  - `#ring-extensions` — geometric tab extensions
  - `#ring-guides` — spokes, boundary circles, crosshairs
  - `#ring-dimensions` — all dimension annotations
  - `#detail-view` — tile detail orthographic drawing
  - `#title-block` — title block
- **No external fonts, no external images, no JavaScript**
- All geometry must be mathematically computed — no hand-approximated coordinates
- The SVG must render correctly in any standards-compliant SVG viewer (Inkscape, browser, Illustrator)

---

## END OF PROMPT
