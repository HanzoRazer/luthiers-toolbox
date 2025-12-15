# RMOS Phase 3: Vue Components Documentation

**Status:** ⏸️ Code Provided, Not Yet Created  
**Total:** 6 files, ~680 lines  
**Dependencies:** Vue 3, Pinia, TypeScript, nanoid

---

## 📋 Overview

These are the **Phase 3 frontend UI components** that complete the RMOS MVP. All code has been provided by the user but files have not yet been created in the repository.

**Purpose:** Provide a fully functional RMOS sandbox UI with pattern management, batch operation configuration, risk analysis, manufacturing planning, and job logging.

---

## 🎨 Component Architecture

### **Component Dependency Tree**

```
RosettePipelineView (main view)
├── RosettePatternLibrary
│   └── useRosettePatternStore
├── RosetteTemplateLab
│   ├── nanoid (for ring IDs)
│   └── derives SawSliceBatchOpCircle
├── RosetteMultiRingOpPanel
│   └── /rmos/saw-ops/batch/preview API
├── RosetteManufacturingPlanPanel
│   └── useManufacturingPlanStore
│       └── /rmos/rosette/manufacturing-plan API
└── JobLogMiniList
    └── useJobLogStore
        └── /rmos/joblog API
```

---

## 📁 Component Details

### **1. RosetteTemplateLab.vue**

**Path:** `packages/client/src/components/rmos/RosetteTemplateLab.vue`  
**Size:** ~180 lines  
**Type:** Pattern Editor Component

#### **Purpose**
Main pattern editor with live batch operation preview. Allows users to design multi-ring rosette patterns with configurable parameters.

#### **Features**
- **Pattern metadata editor**
  - Pattern name input
  - Center coordinates (X/Y mm)
  - Default settings (slice thickness, passes, workholding, tool)

- **Ring band table editor**
  - Dynamic add/remove rings
  - Per-ring editable properties:
    - `radius_mm` - Ring radius
    - `width_mm` - Ring width
    - `strip_family_id` - Wood species/pattern family
    - `slice_angle_deg` - Rotation angle (0-45°)
    - `tile_length_override_mm` - Optional tile length override
    - `color_hint` - Visual identification color

- **Live batch operation derivation**
  - Automatically converts pattern → `SawSliceBatchOpCircle`
  - Real-time preview for batch operations
  - Emits updates to parent component

#### **Props**
```typescript
props: {
  pattern: Object  // RosettePattern
}
```

#### **Emits**
```typescript
emits: {
  'update:pattern': (pattern: RosettePattern) => void
  'update:batchOp': (batchOp: SawSliceBatchOpCircle) => void
}
```

#### **Dependencies**
- `nanoid` - For generating unique ring IDs
- Vue 3 Composition API

#### **Key UI Sections**
1. **Pattern Metadata Form**
   - Name input field
   - Center X/Y coordinate inputs
   - Default settings group

2. **Ring Bands Table**
   - Index column (read-only, 0 = outermost)
   - Radius input (mm)
   - Width input (mm)
   - Strip family selector
   - Slice angle input (degrees)
   - Tile length override (optional)
   - Color hint input
   - Delete button per row
   - Add ring button

3. **Default Settings**
   - Slice thickness (mm)
   - Number of passes
   - Workholding method dropdown
   - Tool ID selector

#### **Usage Example**
```vue
<RosetteTemplateLab
  :pattern="selectedPattern"
  @update:pattern="handlePatternUpdate"
  @update:batchOp="handleBatchOpUpdate"
/>
```

---

### **2. RosetteMultiRingOpPanel.vue**

**Path:** `packages/client/src/components/rmos/RosetteMultiRingOpPanel.vue`  
**Size:** ~150 lines  
**Type:** Batch Operation Configuration Component

#### **Purpose**
Configure and preview multi-ring saw batch operations with real-time risk analysis and G-code generation.

#### **Features**
- **Batch operation configuration form**
  - Tool selection (dropdown from saw tools)
  - Material type (hardwood, softwood, plywood, acrylic, aluminum, MDF)
  - Workholding method (vacuum, tape, clamps, jig)
  - Radial step (mm between rings)
  - Number of rings to cut

- **Preview functionality**
  - Button triggers API call to `/rmos/saw-ops/batch/preview`
  - Real-time risk analysis
  - G-code generation

- **Risk analysis display**
  - Per-slice/ring risk table
  - Color-coded risk grades (GREEN/YELLOW/RED)
  - Detailed metrics per ring:
    - Index, kind, offset (mm)
    - Risk grade, rim speed (m/min)
    - DOC grade, gantry grade

- **G-code viewer**
  - Scrollable monospace textarea
  - Shows generated G-code
  - Line count statistics

#### **Props**
```typescript
props: {
  batchOp: Object  // SawSliceBatchOpCircle
}
```

#### **API Integration**
```typescript
POST /rmos/saw-ops/batch/preview
Body: {
  id: string,
  op_type: "saw_slice_batch",
  tool_id: string,
  geometry_source: "circle_param",
  base_circle: { center_x_mm, center_y_mm, radius_mm },
  num_rings: number,
  radial_step_mm: number,
  radial_sign: number,
  slice_thickness_mm: number,
  passes: number,
  material: string,
  workholding: string
}

Response: {
  op_id: string,
  tool_id: string,
  mode: string,
  material: string,
  workholding: string,
  num_slices: number,
  overall_risk_grade: "GREEN" | "YELLOW" | "RED",
  slice_risks: Array<{
    index: number,
    kind: string,
    offset_mm: number,
    risk_grade: string,
    rim_speed_m_min: number,
    doc_grade: string,
    gantry_grade: string
  }>,
  gcode: string
}
```

#### **Key UI Sections**
1. **Configuration Form**
   - Tool selector dropdown
   - Material dropdown
   - Workholding dropdown
   - Radial step input (mm)
   - Number of rings input
   - Preview button (triggers API)

2. **Risk Analysis Table**
   | Index | Kind | Offset (mm) | Risk Grade | Rim Speed | DOC Grade | Gantry Grade |
   |-------|------|-------------|------------|-----------|-----------|--------------|
   | 0     | ring | 0.0         | GREEN      | 45.2      | GREEN     | GREEN        |
   | 1     | ring | 3.0         | GREEN      | 48.1      | GREEN     | GREEN        |

3. **Overall Risk Badge**
   - Color-coded (green/yellow/red)
   - Shows aggregate risk grade

4. **G-code Display**
   - Monospace textarea
   - Read-only
   - Shows generated G-code
   - Line count: `X lines`

#### **Usage Example**
```vue
<RosetteMultiRingOpPanel
  :batch-op="currentBatchOp"
/>
```

---

### **3. RosettePatternLibrary.vue**

**Path:** `packages/client/src/components/rmos/RosettePatternLibrary.vue`  
**Size:** ~80 lines  
**Type:** Pattern CRUD Interface Component

#### **Purpose**
Manage saved rosette patterns with library view, selection, deletion, and quick creation.

#### **Features**
- **Pattern list display**
  - Shows all saved patterns
  - Pattern name
  - Ring count badge
  - Created/modified timestamps (optional)

- **Pattern selection**
  - Click to select/load pattern
  - Visual highlight for selected pattern
  - Emits `pattern-selected` event to parent

- **Pattern deletion**
  - Delete button per pattern
  - Confirmation dialog: "Are you sure you want to delete this pattern?"
  - Calls `DELETE /rmos/rosette/patterns/{id}`

- **Quick create dialog**
  - Modal dialog for new pattern creation
  - Input pattern name
  - Set initial center coordinates
  - Create with default ring configuration
  - Calls `POST /rmos/rosette/patterns`

- **Empty state**
  - Shows message when no patterns exist
  - "No patterns saved yet. Create your first pattern!"

#### **Store Integration**
```typescript
const patternStore = useRosettePatternStore()

// Fetch all patterns
await patternStore.fetchPatterns()

// Delete pattern
await patternStore.deletePattern(patternId)

// Create pattern
await patternStore.createPattern(newPattern)
```

#### **Emits**
```typescript
emits: {
  'pattern-selected': (pattern: RosettePattern) => void
}
```

#### **Key UI Sections**
1. **Header**
   - "Pattern Library" title
   - "New Pattern" button (opens create dialog)
   - Pattern count badge

2. **Pattern List**
   - Scrollable list
   - Each pattern card shows:
     - Pattern name
     - Ring count: `N rings`
     - Select button
     - Delete button (trash icon)
   - Selected pattern: highlighted background

3. **Create Dialog**
   - Modal overlay
   - Pattern name input
   - Center X/Y inputs
   - "Create" button
   - "Cancel" button

4. **Empty State**
   - Centered message
   - Icon (optional)
   - "Create your first pattern" link

#### **Usage Example**
```vue
<RosettePatternLibrary
  @pattern-selected="handlePatternSelected"
/>
```

---

### **4. RosetteManufacturingPlanPanel.vue**

**Path:** `packages/client/src/components/rmos/RosetteManufacturingPlanPanel.vue`  
**Size:** ~120 lines  
**Type:** Manufacturing Planning Component

#### **Purpose**
Generate and display manufacturing plans with tile requirements, strip calculations, and stick estimates.

#### **Features**
- **Input form**
  - Number of guitars (integer)
  - Tile length (mm, float)
  - Scrap factor (percentage, 0-100%)
  - Record to JobLog checkbox

- **Generate plan button**
  - Calls `POST /rmos/rosette/manufacturing-plan`
  - Creates `rosette_plan` JobLog entry if enabled

- **Ring requirements table**
  - Per-ring breakdown
  - Columns:
    - Ring index
    - Strip family ID
    - Radius (mm)
    - Width (mm)
    - Circumference (mm)
    - Tiles per guitar
    - Total tiles

- **Strip family plans table**
  - Aggregated by `strip_family_id`
  - Columns:
    - Strip family ID
    - Color hint
    - Slice angle (degrees)
    - Total tiles needed (with scrap)
    - Strip length (meters)
    - Sticks needed
    - Ring indices using this family

- **Notes display**
  - Optional manufacturing notes
  - Special instructions
  - Material requirements

#### **API Integration**
```typescript
POST /rmos/rosette/manufacturing-plan
Body: {
  pattern_id: string,
  guitars: number,
  tile_length_mm: number,
  scrap_factor: number,  // 0.12 = 12%
  record_joblog: boolean
}

Response: {
  pattern: RosettePatternInDB,
  guitars: number,
  ring_requirements: Array<{
    ring_index: number,
    strip_family_id: string,
    radius_mm: number,
    width_mm: number,
    circumference_mm: number,
    tiles_per_guitar: number,
    total_tiles: number,
    tile_length_mm: number
  }>,
  strip_plans: Array<{
    strip_family_id: string,
    color_hint: string | null,
    slice_angle_deg: number,
    tile_length_mm: number,
    total_tiles_needed: number,
    tiles_per_meter: number,
    total_strip_length_m: number,
    suggested_stick_length_mm: number,
    sticks_needed: number,
    ring_indices: number[]
  }>,
  notes: string | null
}
```

#### **Store Integration**
```typescript
const planStore = useManufacturingPlanStore()

await planStore.fetchPlan({
  pattern_id: selectedPattern.id,
  guitars: 4,
  tile_length_mm: 8.0,
  scrap_factor: 0.12,
  record_joblog: true
})
```

#### **Key UI Sections**
1. **Input Form**
   - Pattern selector (or auto-filled from context)
   - Guitars input: `<input type="number" min="1" />`
   - Tile length input: `<input type="number" step="0.1" />` mm
   - Scrap factor input: `<input type="number" min="0" max="100" />` %
   - JobLog checkbox: "Record plan to JobLog"
   - Generate button

2. **Ring Requirements Table**
   | Ring | Family | Radius | Width | Circumference | Tiles/Guitar | Total |
   |------|--------|--------|-------|---------------|--------------|-------|
   | 0    | bw_checker | 45mm | 2mm | 282.7mm | 35 | 140 |
   | 1    | bw_checker | 48mm | 2mm | 301.6mm | 38 | 152 |

3. **Strip Family Plans Table**
   | Family | Color | Angle | Tiles | Strip Length | Sticks | Rings |
   |--------|-------|-------|-------|--------------|--------|-------|
   | bw_checker | - | 0° | 292 | 2.34m | 8 | [0,1] |

4. **Manufacturing Notes**
   - Text area or display box
   - Shows pattern-specific notes
   - Special requirements

#### **Usage Example**
```vue
<RosetteManufacturingPlanPanel
  :pattern-id="selectedPattern?.id"
/>
```

---

### **5. JobLogMiniList.vue**

**Path:** `packages/client/src/components/rmos/JobLogMiniList.vue`  
**Size:** ~70 lines  
**Type:** Job Log Viewer Component

#### **Purpose**
Display compact JobLog entries with type-specific formatting and refresh capability.

#### **Features**
- **Entry list display**
  - All JobLog entries sorted by newest first
  - Compact card format
  - Color-coded by job type

- **Type-specific rendering**
  - **rosette_plan jobs**:
    - Pattern ID
    - Number of guitars
    - Total tiles
    - Summary risk grade
  - **saw_slice_batch jobs**:
    - Tool ID
    - Material
    - Number of slices
    - Overall risk grade
    - Operator notes

- **Timestamp formatting**
  - Human-readable dates
  - Example: "Nov 21, 2025 2:45 PM"
  - Relative time (optional): "5 minutes ago"

- **Refresh functionality**
  - Manual refresh button
  - Reloads JobLog from server
  - Shows loading state

- **Entry count badge**
  - Total number of logged jobs
  - Type breakdown (optional)

#### **Store Integration**
```typescript
const jobLogStore = useJobLogStore()

// Fetch all entries
await jobLogStore.fetchJobLog()

// Access entries
const entries = jobLogStore.entries
```

#### **Display Format**

**Rosette Plan Job:**
```
┌─────────────────────────────────────────────┐
│ [rosette_plan] rosette_plan_ci_rosette_... │
│                                             │
│ Pattern: ci_rosette_1732198765              │
│ Guitars: 4                                  │
│ Total tiles: 2,246                          │
│ Risk: GREEN                                 │
│                                             │
│ Created: Nov 21, 2025 2:30 PM              │
└─────────────────────────────────────────────┘
```

**Saw Slice Batch Job:**
```
┌─────────────────────────────────────────────┐
│ [saw_slice_batch] saw_batch_ci_batch_...   │
│                                             │
│ Tool: saw_default                           │
│ Material: hardwood                          │
│ Slices: 2                                   │
│ Risk: YELLOW                                │
│                                             │
│ Notes: Review blade sharpness               │
│ Created: Nov 21, 2025 2:45 PM              │
└─────────────────────────────────────────────┘
```

#### **Key UI Sections**
1. **Header**
   - "Job Log" title
   - Entry count badge: `N entries`
   - Refresh button (icon)

2. **Entry Cards**
   - Job type badge (colored)
   - Job ID (truncated)
   - Type-specific fields
   - Timestamp
   - Scrollable container

3. **Empty State**
   - "No jobs logged yet"
   - Icon (optional)

4. **Loading State**
   - Spinner during fetch
   - "Loading job log..."

#### **Usage Example**
```vue
<JobLogMiniList />
```

---

### **6. RosettePipelineView.vue**

**Path:** `packages/client/src/views/RosettePipelineView.vue`  
**Size:** ~80 lines  
**Type:** Main Integrated View

#### **Purpose**
Complete integrated RMOS view combining all components in a responsive 3-column layout.

#### **Features**
- **3-column responsive layout**
  - Left: Pattern library + JobLog
  - Middle: Template lab + batch operation panel
  - Right: Manufacturing plan panel

- **Component orchestration**
  - Manages shared state between components
  - Handles pattern selection flow
  - Synchronizes updates across components

- **Event handling**
  - Pattern selection from library → updates template lab
  - Template lab changes → updates batch op
  - Batch op changes → triggers risk preview
  - Plan generation → logs to JobLog

- **State management**
  - Selected pattern tracking
  - Current batch operation state
  - Manufacturing plan state
  - JobLog refresh triggers

#### **Layout Structure**

```
┌─────────────────────────────────────────────────────────────┐
│                    RMOS Pipeline View                       │
├──────────────┬──────────────────────┬──────────────────────┤
│              │                      │                      │
│  Library     │  Template Lab        │  Manufacturing       │
│              │                      │     Plan             │
│ ┌──────────┐ │ ┌──────────────────┐ │ ┌──────────────────┐│
│ │ Pattern  │ │ │ Pattern Metadata │ │ │ Input Form       ││
│ │ List     │ │ │ • Name           │ │ │ • Guitars        ││
│ │          │ │ │ • Center X/Y     │ │ │ • Tile length    ││
│ │ • Select │ │ │                  │ │ │ • Scrap factor   ││
│ │ • Delete │ │ │ Ring Bands Table │ │ │                  ││
│ │ • Create │ │ │ • Radius         │ │ │ Generate Button  ││
│ │          │ │ │ • Width          │ │ │                  ││
│ └──────────┘ │ │ • Strip family   │ │ │ Ring Reqs Table  ││
│              │ │ • Slice angle    │ │ │ • Per-ring tiles ││
│ ┌──────────┐ │ │                  │ │ │                  ││
│ │ Job Log  │ │ │ Add/Remove Rings │ │ │ Strip Plans      ││
│ │          │ │ └──────────────────┘ │ │ • By family      ││
│ │ Entries: │ │                      │ │ • Strip length   ││
│ │ • Plans  │ │ ┌──────────────────┐ │ │ • Sticks needed  ││
│ │ • Batches│ │ │ Batch Op Config  │ │ │                  ││
│ │          │ │ │ • Tool           │ │ │ Notes            ││
│ │ Refresh  │ │ │ • Material       │ │ │                  ││
│ └──────────┘ │ │ • Workholding    │ │ └──────────────────┘│
│              │ │ • Radial step    │ │                      │
│              │ │ • Num rings      │ │                      │
│              │ │                  │ │                      │
│              │ │ Preview Button   │ │                      │
│              │ │                  │ │                      │
│              │ │ Risk Table       │ │                      │
│              │ │ • Per-ring risk  │ │                      │
│              │ │                  │ │                      │
│              │ │ G-code Display   │ │                      │
│              │ └──────────────────┘ │                      │
│              │                      │                      │
└──────────────┴──────────────────────┴──────────────────────┘
```

#### **Component Integration**
```vue
<template>
  <div class="rmos-pipeline-view">
    <!-- Left column -->
    <div class="left-panel">
      <RosettePatternLibrary
        @pattern-selected="handlePatternSelected"
      />
      <JobLogMiniList />
    </div>

    <!-- Middle column -->
    <div class="middle-panel">
      <RosetteTemplateLab
        :pattern="selectedPattern"
        @update:pattern="handlePatternUpdate"
        @update:batchOp="handleBatchOpUpdate"
      />
      <RosetteMultiRingOpPanel
        :batch-op="currentBatchOp"
      />
    </div>

    <!-- Right column -->
    <div class="right-panel">
      <RosetteManufacturingPlanPanel
        :pattern-id="selectedPattern?.id"
      />
    </div>
  </div>
</template>
```

#### **State Management**
```typescript
const selectedPattern = ref<RosettePattern | null>(null)
const currentBatchOp = ref<SawSliceBatchOpCircle | null>(null)

function handlePatternSelected(pattern: RosettePattern) {
  selectedPattern.value = pattern
  // Auto-update batch op based on pattern
  deriveBatchOpFromPattern(pattern)
}

function handlePatternUpdate(pattern: RosettePattern) {
  selectedPattern.value = pattern
  // Save to store
  patternStore.updatePattern(pattern.id, pattern)
}

function handleBatchOpUpdate(batchOp: SawSliceBatchOpCircle) {
  currentBatchOp.value = batchOp
}
```

#### **Responsive Behavior**
- **Desktop (>1200px)**: 3 columns side-by-side
- **Tablet (768px-1200px)**: 2 columns (left + middle), right wraps below
- **Mobile (<768px)**: Single column, stacked vertically

#### **Usage Example**
```vue
<!-- In router -->
{
  path: '/rmos/pipeline',
  name: 'RosettePipeline',
  component: RosettePipelineView
}
```

---

## 🔌 Required Dependencies

### **npm Packages**

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "nanoid": "^5.0.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0"
  }
}
```

### **Installation Command**

```bash
npm install nanoid
```

*(Other dependencies already installed in Phase 1-2)*

---

## 🔗 Integration Requirements

### **1. Router Configuration**

Add route in `packages/client/src/router/index.ts`:

```typescript
{
  path: '/rmos/pipeline',
  name: 'RosettePipeline',
  component: () => import('@/views/RosettePipelineView.vue'),
  meta: {
    title: 'RMOS Pipeline',
    requiresAuth: false
  }
}
```

### **2. Backend Dependencies**

These components require the following backend endpoints (already created in Phase 1-2):

- `GET /rmos/rosette/patterns` - List patterns
- `POST /rmos/rosette/patterns` - Create pattern
- `PUT /rmos/rosette/patterns/{id}` - Update pattern
- `DELETE /rmos/rosette/patterns/{id}` - Delete pattern
- `POST /rmos/rosette/manufacturing-plan` - Generate plan
- `GET /rmos/joblog` - List JobLog entries
- `POST /rmos/saw-ops/batch/preview` - Batch operation preview

### **3. Pinia Store Initialization**

Ensure stores are registered in `packages/client/src/main.ts`:

```typescript
import { createPinia } from 'pinia'
import { useRosettePatternStore } from '@/stores/useRosettePatternStore'
import { useManufacturingPlanStore } from '@/stores/useManufacturingPlanStore'
import { useJobLogStore } from '@/stores/useJobLogStore'

const pinia = createPinia()
app.use(pinia)
```

---

## 🧪 Testing Strategy

### **Component Tests** (Optional, but recommended)

```typescript
// RosetteTemplateLab.spec.ts
describe('RosetteTemplateLab', () => {
  it('generates unique ring IDs using nanoid', () => {
    // Test ring ID generation
  })

  it('emits pattern updates when ring is modified', () => {
    // Test pattern update emission
  })

  it('derives batch op from pattern correctly', () => {
    // Test batch op derivation
  })
})

// RosetteMultiRingOpPanel.spec.ts
describe('RosetteMultiRingOpPanel', () => {
  it('calls batch preview API with correct payload', async () => {
    // Mock axios, test API call
  })

  it('displays risk table with correct grades', () => {
    // Test risk table rendering
  })
})
```

### **Integration Tests**

```bash
# Manual end-to-end test
1. Navigate to /rmos/pipeline
2. Create new pattern with 2 rings
3. Configure batch operation
4. Click "Preview" → verify risk table appears
5. Generate manufacturing plan → verify calculations
6. Check JobLog → verify entries logged
```

---

## 🎯 End-to-End User Workflow

### **Scenario: Create and Analyze 4-Guitar Rosette Job**

**Step 1: Create Pattern**
1. Navigate to `/rmos/pipeline`
2. Click "New Pattern" in library
3. Enter name: "Black/White Checker 4-ring"
4. Set center: X=0, Y=0
5. Add 4 rings:
   - Ring 0: radius=40mm, width=2mm, family=bw_checker_main
   - Ring 1: radius=43mm, width=2mm, family=bw_checker_main
   - Ring 2: radius=46mm, width=2mm, family=ebony_black
   - Ring 3: radius=49mm, width=2mm, family=maple_white
6. Save pattern

**Step 2: Configure Batch Operation**
1. Select pattern from library
2. In Batch Op Panel:
   - Tool: saw_default
   - Material: hardwood
   - Workholding: vacuum
   - Radial step: 3mm
   - Num rings: 4
3. Click "Preview"
4. Review risk table:
   - Ring 0: GREEN, 37.7 m/min
   - Ring 1: GREEN, 40.5 m/min
   - Ring 2: YELLOW, 43.3 m/min (close to limit)
   - Ring 3: YELLOW, 46.1 m/min
5. Review G-code (156 lines)

**Step 3: Generate Manufacturing Plan**
1. In Manufacturing Panel:
   - Guitars: 4
   - Tile length: 8.0mm
   - Scrap factor: 12%
   - Record to JobLog: ✓
2. Click "Generate"
3. Review Ring Requirements:
   - Ring 0: 32 tiles/guitar = 128 total
   - Ring 1: 34 tiles/guitar = 136 total
   - Ring 2: 36 tiles/guitar = 144 total
   - Ring 3: 38 tiles/guitar = 152 total
4. Review Strip Plans:
   - bw_checker_main: 264 tiles, 2.11m, 8 sticks, rings [0,1]
   - ebony_black: 144 tiles, 1.15m, 4 sticks, rings [2]
   - maple_white: 152 tiles, 1.22m, 5 sticks, rings [3]
5. Total: 560 tiles, 4.48m strip length, 17 sticks

**Step 4: Verify JobLog**
1. Check JobLog Mini List
2. See new entry:
   - Type: rosette_plan
   - Pattern: Black/White Checker 4-ring
   - Guitars: 4
   - Total tiles: 560
   - Created: [timestamp]

**Result:** Complete rosette job planned, risk analyzed, materials calculated, and logged for audit trail.

---

## 📊 Component Statistics

| Component | Lines | Props | Emits | API Calls | Store Usage |
|-----------|-------|-------|-------|-----------|-------------|
| RosetteTemplateLab | ~180 | 1 | 2 | 0 | 0 |
| RosetteMultiRingOpPanel | ~150 | 1 | 0 | 1 | 0 |
| RosettePatternLibrary | ~80 | 0 | 1 | 3 | Pattern |
| RosetteManufacturingPlanPanel | ~120 | 1 | 0 | 1 | Plan |
| JobLogMiniList | ~70 | 0 | 0 | 1 | JobLog |
| RosettePipelineView | ~80 | 0 | 0 | 0 | All |
| **Total** | **~680** | **3** | **3** | **6** | **3** |

---

## ✅ Completion Checklist

**Before creating files:**
- [ ] Backend routers registered (joblog, rosette_patterns, manufacturing, saw_ops)
- [ ] Pinia stores created (useRosettePatternStore, useManufacturingPlanStore, useJobLogStore)
- [ ] `nanoid` package installed
- [ ] TypeScript models created (rmos.ts)

**File creation:**
- [ ] Create `packages/client/src/components/rmos/` directory
- [ ] Create `RosetteTemplateLab.vue`
- [ ] Create `RosetteMultiRingOpPanel.vue`
- [ ] Create `RosettePatternLibrary.vue`
- [ ] Create `RosetteManufacturingPlanPanel.vue`
- [ ] Create `JobLogMiniList.vue`
- [ ] Create `packages/client/src/views/RosettePipelineView.vue`

**Integration:**
- [ ] Add route to router: `/rmos/pipeline`
- [ ] Test backend endpoints with smoke test script
- [ ] Verify Pinia stores work with API
- [ ] Test complete workflow end-to-end

**Post-creation validation:**
- [ ] All components render without errors
- [ ] API calls succeed (200 responses)
- [ ] State updates propagate correctly
- [ ] JobLog entries created
- [ ] Manufacturing calculations accurate
- [ ] Risk analysis displays correctly

---

## 🚀 Next Steps After Creation

1. **Run smoke test**:
   ```bash
   .\scripts\Test-RMOS-Full.ps1 -Verbose
   ```

2. **Test UI manually**:
   - Navigate to `http://localhost:5173/rmos/pipeline`
   - Create test pattern
   - Preview batch operation
   - Generate manufacturing plan
   - Verify JobLog entries

3. **Production readiness**:
   - Add error boundaries
   - Implement loading skeletons
   - Add form validation
   - Add undo/redo for pattern editing (optional)
   - Add export to CSV for manufacturing plans (optional)

4. **Phase 2 features** (future):
   - SQLite persistence (replace in-memory stores)
   - Multi-user support
   - Pattern versioning
   - Advanced risk profiles
   - Real-time collaboration

---

**Status:** Ready to create files  
**Estimated creation time:** 15-20 minutes  
**Estimated testing time:** 30-45 minutes  
**Total Phase 1 completion:** 95% → 100% after component creation
