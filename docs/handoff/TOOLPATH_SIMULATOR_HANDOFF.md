# Toolpath Simulator - Developer Handoff

**Status:** Stub UI complete, needs 3D rendering engine
**Priority:** P1
**Route:** `/cam/simulator`
**File:** `packages/client/src/views/cam/ToolpathSimulatorView.vue`

---

## What Exists

### UI Components (Complete)
- File upload (`.nc`, `.gcode`, `.tap`, `.ngc`)
- View mode selector (3D, Top, Front, Side)
- Display toggles (Toolpath, Stock, Rapids)
- Playback controls (Play, Pause, Reset, Step, Scrubber)
- Speed control (0.1x - 10x)
- Statistics panel (distances, time, tool changes)
- G-code preview (first 20 lines)

### State Management (Complete)
```typescript
gcodeFile: File | null       // Uploaded file
gcodeText: string            // Raw G-code content
viewMode: '3d' | 'top' | 'front' | 'side'
showToolpath: boolean
showStock: boolean
showRapids: boolean
simulationSpeed: number      // 0.1 - 10
currentLine: number          // Playback position
totalLines: number
isPlaying: boolean
stats: { totalDistance, cuttingDistance, rapidDistance, estimatedTime, toolChanges }
```

---

## What Needs Building

### 1. G-code Parser Service
**Location:** `packages/client/src/services/gcodeParser.ts`

```typescript
interface GCodeMove {
  type: 'rapid' | 'linear' | 'arc_cw' | 'arc_ccw'
  from: Vector3
  to: Vector3
  feedRate?: number
}

interface ParsedGCode {
  moves: GCodeMove[]
  bounds: { min: Vector3, max: Vector3 }
  stats: SimulationStats
}

function parseGCode(text: string): ParsedGCode
```

**Must handle:**
- G0 (rapid), G1 (linear), G2/G3 (arcs)
- Absolute (G90) vs Incremental (G91)
- Units: G20 (inch) / G21 (mm)
- Tool changes (M6 Txx)
- Comments (parentheses and semicolon)

### 2. 3D Renderer
**Recommended:** Three.js or Babylon.js

```typescript
interface ToolpathRenderer {
  init(container: HTMLElement): void
  loadToolpath(moves: GCodeMove[]): void
  setViewMode(mode: 'perspective' | 'top' | 'front' | 'side'): void
  setCurrentLine(line: number): void
  toggleLayer(layer: 'toolpath' | 'stock' | 'rapids', visible: boolean): void
  dispose(): void
}
```

**Visual requirements:**
- Toolpath lines: Blue for cutting, Red for rapids
- Stock: Semi-transparent gray box
- Tool position indicator (cone or cylinder)
- Grid floor with axis indicators
- Orbit controls for 3D, pan-only for ortho views

### 3. Simulation Engine
```typescript
interface SimulationEngine {
  play(): void
  pause(): void
  reset(): void
  stepForward(): void
  setSpeed(multiplier: number): void
  onFrame(callback: (lineNumber: number) => void): void
}
```

**Features:**
- Animate tool along path at correct feed rates
- Highlight current G-code line in preview
- Update stats in real-time during playback

### 4. API Integration (Optional)
**Endpoints:** (documented in view file)
- `POST /api/cam/simulate/preview` - Get parsed moves from server
- `POST /api/cam/simulate/analyze` - Get detailed analysis

Use these if client-side parsing is too slow for large files.

---

## Implementation Order

1. **G-code parser** - Parse to move list, calculate stats
2. **Static renderer** - Display full toolpath, no animation
3. **View modes** - Camera presets for top/front/side
4. **Playback** - Animate tool position along path
5. **Stock removal** - CSG subtraction (stretch goal)

---

## Libraries to Consider

| Library | Use Case | Size |
|---------|----------|------|
| **three.js** | 3D rendering | ~150kb |
| **@babylonjs/core** | 3D rendering (heavier, more features) | ~800kb |
| **gcode-preview** | npm package, Three.js based | ~50kb |

**Recommendation:** Start with `gcode-preview` npm package - it handles parsing and basic Three.js rendering out of the box.

```bash
npm install gcode-preview three
```

---

## File Structure (Suggested)

```
packages/client/src/
├── views/cam/
│   └── ToolpathSimulatorView.vue    # Existing
├── components/cam/
│   ├── GCodeViewer3D.vue            # Three.js canvas component
│   ├── PlaybackControls.vue         # Extract from view
│   └── SimulationStats.vue          # Extract from view
├── services/
│   ├── gcodeParser.ts               # Parse G-code to moves
│   └── simulationEngine.ts          # Playback timing logic
└── composables/
    └── useToolpathSimulation.ts     # State + logic combined
```

---

## Test Files

Sample G-code files for testing are in:
- `services/api/tests/testdata/` - Various `.nc` files
- `services/api/tests/golden/` - Known-good outputs

---

## Questions for Product

1. Support for 4/5-axis visualization? (A/B/C rotary)
2. Stock removal simulation priority? (CSG is complex)
3. Maximum file size to support client-side?
4. Need measurement tools? (distance, angle)

---

*Created: 2026-03-06*
*Author: Claude Code*
