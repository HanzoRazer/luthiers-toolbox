# Rosette Designer Redesign Specification

**Status:** 🎨 Design-First Pivot  
**Date:** November 10, 2025  
**Based On:** Real rosette-making practice + screenshot analysis

---

## 🎯 Core Philosophy

> **"A geometry/graphic design tool for planning decorative wood inlays, with optional channel routing export."**

**NOT:** "A CAM tool that generates adaptive pocketing toolpaths"

---

## 📊 Screenshot Analysis - What We Learned

From the YouTube screenshot showing Fusion 360 rosette design:

### What the Luthier Is Doing:
- ✅ **Designing geometric patterns** (radial blue segments)
- ✅ **Calculating wood strip dimensions** (precise measurements)
- ✅ **Planning piece arrangement** (how strips fit together)
- ✅ **Working with symmetry** (radial/circular patterns)
- ✅ **Creating visual reference** (for hand-assembly)

### What the Luthier Is NOT Doing:
- ❌ Generating CNC toolpaths for cutting the rosette
- ❌ Adaptive pocketing or clearing operations
- ❌ Complex CAM workflows

### The Tool Being Used:
- **CAD software** (Fusion 360) as a **design/geometry tool**
- Used for **planning and visualization**, not machining
- Output: Dimensional drawing for wood cutting/assembly

---

## 🎨 Redesigned Interface - Three Panels

```
┌─────────────────────────────────────────────────────────────┐
│                    🎨 Rosette Design Studio                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─ Design Canvas (Left 60%) ────────────────────────────┐  │
│  │                                                         │  │
│  │     [Interactive SVG Canvas]                            │  │
│  │                                                         │  │
│  │     - Draw/arrange wood strip shapes                    │  │
│  │     - Radial symmetry tools                             │  │
│  │     - Pattern templates                                 │  │
│  │     - Snap to angles/circles                            │  │
│  │     - Visual preview with wood textures                 │  │
│  │                                                         │  │
│  │  ◉─────────────────────────◉                           │  │
│  │ /  Blue strips arranged   \                            │  │
│  │ │   in radial pattern     │                            │  │
│  │ \  around soundhole       /                            │  │
│  │  ◉─────────────────────────◉                           │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─ Design Controls (Right 40%) ───────────────────────────┐ │
│  │                                                          │ │
│  │ 📐 DIMENSIONS                                           │ │
│  │ ├─ Soundhole Diameter: [100 mm]                        │ │
│  │ ├─ Rosette Width: [20 mm]                              │ │
│  │ ├─ Channel Depth: [1.5 mm]                             │ │
│  │ └─ Number of Segments: [16] (radial symmetry)          │ │
│  │                                                          │ │
│  │ 🎨 PATTERN                                              │ │
│  │ ├─ Template: [Custom ▼]                                │ │
│  │ │   • Herringbone                                       │ │
│  │ │   • Rope/Twist                                        │ │
│  │ │   • Celtic Knot                                       │ │
│  │ │   • Geometric Mosaic                                  │ │
│  │ └─ Symmetry: [Radial - 16 segments]                    │ │
│  │                                                          │ │
│  │ 🪵 MATERIALS                                            │ │
│  │ ├─ Strip 1: [Maple (light)] [1.0mm width]             │ │
│  │ ├─ Strip 2: [Walnut (dark)] [1.5mm width]             │ │
│  │ ├─ Strip 3: [Ebony (black)] [0.5mm width]             │ │
│  │ └─ [+ Add Strip]                                        │ │
│  │                                                          │ │
│  │ 🔧 TOOLS                                                │ │
│  │ ├─ [Draw Strip]   [Select]   [Transform]               │ │
│  │ ├─ [Radial Copy] [Mirror]    [Rotate]                  │ │
│  │ └─ [Align]       [Distribute] [Snap]                   │ │
│  │                                                          │ │
│  │ 📤 EXPORT (Secondary)                                   │ │
│  │ ├─ [📷 Export Pattern Image] (PNG/SVG for reference)   │ │
│  │ ├─ [📄 Export Dimension Sheet] (PDF for shop)          │ │
│  │ └─ [🔧 Export Channel Path] (DXF/G-code, optional)     │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Feature Breakdown

### 1. Design Canvas (Primary - 80% of interface)

**Interactive SVG Drawing Area:**
- Circular workspace showing soundhole and rosette zones
- Draw/edit individual wood strip shapes (rectangles, trapezoids, curves)
- Visual wood grain textures and colors
- Real-time preview of assembled design

**Drawing Tools:**
```javascript
// Tool palette
const tools = {
  draw: 'Draw wood strip shapes',
  select: 'Select and edit strips',
  transform: 'Move/rotate/scale',
  radialCopy: 'Copy around center (symmetry)',
  mirror: 'Mirror across axis',
  align: 'Snap to grid/angles',
}
```

**Visual Features:**
- Wood species swatches (maple = light, walnut = brown, ebony = black)
- Grain direction indicators
- Dimension annotations (strip widths, angles)
- Layer controls (show/hide components)

### 2. Pattern Templates

**Pre-built geometric patterns:**

```typescript
interface PatternTemplate {
  name: string
  description: string
  segments: number
  strips: Array<{
    shape: 'rectangle' | 'trapezoid' | 'curve'
    width: number
    angle: number
    material: string
  }>
}

const templates: PatternTemplate[] = [
  {
    name: 'Herringbone',
    description: 'Classic V-pattern',
    segments: 16,
    strips: [
      { shape: 'rectangle', width: 1.0, angle: 45, material: 'maple' },
      { shape: 'rectangle', width: 1.0, angle: -45, material: 'walnut' },
    ]
  },
  {
    name: 'Rope/Twist',
    description: 'Alternating diagonal strips',
    segments: 32,
    strips: [
      { shape: 'trapezoid', width: 0.8, angle: 30, material: 'ebony' },
    ]
  },
  // ... more templates
]
```

### 3. Materials Library

**Wood Species Database:**
```typescript
interface WoodSpecies {
  name: string
  color: string // Hex color for preview
  grain: 'straight' | 'wavy' | 'figured'
  availability: 'common' | 'specialty' | 'exotic'
  supplier: string // Stewart-MacDonald, LMI, etc.
}

const woods: WoodSpecies[] = [
  { name: 'Maple', color: '#F5E6D3', grain: 'straight', availability: 'common', supplier: 'StewMac' },
  { name: 'Walnut', color: '#5C4033', grain: 'straight', availability: 'common', supplier: 'StewMac' },
  { name: 'Ebony', color: '#0F0F0F', grain: 'straight', availability: 'specialty', supplier: 'LMI' },
  { name: 'Maple (Figured)', color: '#F5E6D3', grain: 'figured', availability: 'specialty', supplier: 'LMI' },
  { name: 'Rosewood', color: '#3E2723', grain: 'wavy', availability: 'common', supplier: 'StewMac' },
  { name: 'Bloodwood', color: '#8B0000', grain: 'straight', availability: 'exotic', supplier: 'LMI' },
]
```

### 4. Dimension Controls

**Key Parameters:**
- Soundhole diameter (typically 85-105mm)
- Rosette width (15-30mm typical)
- Channel depth (1-2mm for strip installation)
- Individual strip widths (0.5mm, 1mm, 1.5mm, 2mm standard sizes)
- Segment count (for radial symmetry: 8, 12, 16, 24, 32)

**Smart Calculations:**
```typescript
function calculateStripDimensions(
  soundholeDiameter: number,
  rosetteWidth: number,
  segmentCount: number
): {
  innerRadius: number,
  outerRadius: number,
  stripLength: number,
  anglePerSegment: number
} {
  const innerRadius = soundholeDiameter / 2
  const outerRadius = innerRadius + rosetteWidth
  const stripLength = rosetteWidth // radial strips
  const anglePerSegment = 360 / segmentCount
  
  return { innerRadius, outerRadius, stripLength, anglePerSegment }
}
```

### 5. Export Options (Secondary - 20%)

**Primary Exports (Design Focus):**
1. **Pattern Image** (PNG/SVG)
   - High-resolution visual reference
   - Shows wood colors and arrangement
   - For workshop/assembly guide

2. **Dimension Sheet** (PDF)
   - Annotated drawing with measurements
   - Material list (wood species, strip counts)
   - Assembly instructions

**Secondary Exports (Optional CAM):**
3. **Channel Path** (DXF/G-code)
   - Simple circular toolpath
   - Single pass (not adaptive)
   - For routing installation channel only

---

## 🔧 Technical Implementation

### Canvas Technology

**Option A: SVG.js (Recommended)**
```bash
npm install @svgdotjs/svg.js
```

Pros:
- Vector-based (scalable, precise)
- Easy shape manipulation
- Good for technical drawings
- Export to SVG/PDF

**Option B: Paper.js**
```bash
npm install paper
```

Pros:
- Powerful path operations
- Good for complex geometry
- Built-in vector math

### Component Structure

```
client/src/components/art-studio/
├── RosetteDesigner/
│   ├── RosetteCanvas.vue          # SVG drawing canvas
│   ├── PatternLibrary.vue         # Template selector
│   ├── MaterialPalette.vue        # Wood species picker
│   ├── DimensionControls.vue      # Numeric inputs
│   ├── DesignTools.vue            # Drawing tool palette
│   ├── SymmetryControls.vue       # Radial copy/mirror
│   └── ExportPanel.vue            # Export buttons (de-emphasized)
└── RosetteDesigner.vue            # Main container (updated)
```

### Data Flow

```typescript
// State management (lightweight, no Pinia needed)
interface RosetteDesign {
  dimensions: {
    soundholeDiameter: number
    rosetteWidth: number
    channelDepth: number
    segmentCount: number
  }
  
  strips: Array<{
    id: string
    shape: 'rectangle' | 'trapezoid' | 'arc'
    width: number
    angle: number
    position: { x: number, y: number }
    material: string
    layer: number
  }>
  
  settings: {
    symmetryMode: 'radial' | 'mirror' | 'none'
    snapToGrid: boolean
    showDimensions: boolean
    showGrain: boolean
  }
}

// Canvas interactions
const canvas = ref<SVG.Container | null>(null)
const design = ref<RosetteDesign>(defaultDesign)
const selectedTool = ref<'draw' | 'select' | 'transform'>('select')

function addStrip(strip: Strip) {
  design.value.strips.push(strip)
  
  // Apply radial symmetry if enabled
  if (design.value.settings.symmetryMode === 'radial') {
    const copies = createRadialCopies(strip, design.value.dimensions.segmentCount)
    design.value.strips.push(...copies)
  }
  
  renderCanvas()
}

function exportPatternImage() {
  const svg = canvas.value?.svg()
  const blob = new Blob([svg], { type: 'image/svg+xml' })
  downloadFile(blob, 'rosette-pattern.svg')
}

function exportChannelPath() {
  // Simple circular path (NOT adaptive pocketing)
  const { innerRadius, outerRadius } = design.value.dimensions
  const channelPath = generateCircularPath(innerRadius, outerRadius)
  
  // Export as G-code or DXF
  const gcode = `
G90 G21
G0 Z5.0
G0 X${innerRadius} Y0
G1 Z-${design.value.dimensions.channelDepth} F200
G2 X${innerRadius} Y0 I-${innerRadius} J0 F600
G0 Z5.0
M30
  `.trim()
  
  downloadFile(new Blob([gcode]), 'rosette-channel.nc')
}
```

---

## 🎨 Visual Design - Before/After

### Current (Wrong) - CAM-Focused

```
┌─────────────────────────────────────┐
│ Soundhole Diameter: [100mm]         │
│ Exposure:           [8mm]           │
│ Glue Clearance:     [1mm]           │
│ Band Width:         [3mm]           │
│ Band Thickness:     [1mm]           │
│                                     │
│ [Calculate]                         │
│                                     │
│ Result: {dimensions object}         │
│                                     │
│ [Export DXF]                        │
│ [Export G-code]                     │
│ [🔧 Send to CAM]  ← PRIMARY FOCUS  │
└─────────────────────────────────────┘
```

**Problem:** No visual design, all numeric, CAM is main action

### Redesigned (Correct) - Design-Focused

```
┌──────────────────────────────────────────────────┐
│ ┌─ Canvas ─────────────┐  ┌─ Controls ─────────┐│
│ │                       │  │                     ││
│ │    [Rosette Pattern]  │  │ Pattern: Custom    ││
│ │   Radial blue strips  │  │ Symmetry: 16x      ││
│ │   around soundhole    │  │                     ││
│ │                       │  │ Woods:              ││
│ │   (Interactive SVG)   │  │ □ Maple (light)    ││
│ │                       │  │ ■ Walnut (dark)    ││
│ │   👆 Draw/edit strips │  │ ■ Ebony (black)    ││
│ │                       │  │                     ││
│ └───────────────────────┘  │ [📷 Export Image]  ││
│                            │ [📄 Export PDF]    ││
│                            │ [🔧 Channel Path]  ││
│                            └─────────────────────┘│
└──────────────────────────────────────────────────┘
```

**Fixed:** Visual design primary, CAM export secondary

---

## 📋 Implementation Phases

### Phase 1: Core Canvas (Week 1)
- [ ] Install SVG.js / Paper.js
- [ ] Create RosetteCanvas.vue with circular workspace
- [ ] Implement basic shape drawing (rectangles)
- [ ] Add radial symmetry (copy around center)
- [ ] Material color palette (3-5 woods)

### Phase 2: Pattern Tools (Week 2)
- [ ] Pattern template library (3 templates)
- [ ] Drawing tools (draw, select, transform)
- [ ] Dimension controls (soundhole, width, segments)
- [ ] Visual preview with wood textures

### Phase 3: Export & Polish (Week 3)
- [ ] Export pattern image (SVG/PNG)
- [ ] Export dimension sheet (PDF with annotations)
- [ ] Simple channel G-code export (circular path only)
- [ ] Documentation update

### Phase 4: Advanced (Future)
- [ ] More pattern templates (Celtic, mosaic, custom)
- [ ] Advanced wood library (grain textures, figured woods)
- [ ] 3D preview (extruded rosette visualization)
- [ ] Laser cutting export (for individual wood strips)

---

## ✅ Success Criteria

### User Can:
- [ ] **Visually design** a rosette pattern (primary workflow)
- [ ] **Arrange wood strips** in geometric patterns
- [ ] **See realistic preview** with wood colors/grain
- [ ] **Calculate dimensions** for hand-assembly
- [ ] **Export reference images** for workshop
- [ ] **Optionally export** simple channel path (secondary)

### Tool Is:
- [ ] **90% design/visual** (canvas, patterns, materials)
- [ ] **10% CAM/export** (optional channel routing)
- [ ] **Aligned with real practice** (rosettes are art, not CNC)
- [ ] **Educational** (shows how rosettes are actually made)

---

## 🎯 Key Principles

1. **Design First:** Visual pattern creation is primary interface
2. **CAM Secondary:** Toolpath export is optional side feature
3. **Real Workflow:** Match how luthiers actually work (CAD for design, hand-assembly)
4. **Educational:** Teach proper rosette-making practice
5. **Artistic:** Emphasize wood selection, pattern aesthetics, visual appeal

---

**Status:** 🎨 Ready to implement  
**Priority:** High (corrects fundamental misunderstanding)  
**Next Step:** Install SVG.js and create RosetteCanvas.vue component

---

## 📚 References

- Screenshot: YouTube video showing Fusion 360 rosette geometry planning
- James Lister tutorial: Traditional rosette hand-assembly
- Riff-Mag article: Historical/artistic purpose of rosettes
- ROSETTE_REALITY_CHECK.md: Full analysis of misconception
