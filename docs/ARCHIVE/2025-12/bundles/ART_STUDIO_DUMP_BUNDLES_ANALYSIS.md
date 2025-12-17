# Art Studio Dump Bundles - Integration Analysis

**Date:** November 15, 2025  
**Status:** Discovered Unintegrated Bundles  
**Total Lines:** 16,603 lines across 2 files

---

## 📦 Discovered Art Studio Bundles

### **Bundle 1: ArtStudioHeadstock_vue.txt** (8,588 lines)
**Phase:** 23.0 - Art Studio Headstock Lane

**Major Components:**

1. **ArtStudioHeadstock.vue** (~600 lines)
   - Headstock logo DXF → pipeline → simulation workflow
   - Risk snapshot logging integration
   - Backplot snapshot attachment
   - Notes editor with autosave
   - Mirrored architecture from ArtStudioRosette.vue

2. **Router Integration**
   - Route: `/art/headstock`
   - Navigation breadcrumbs
   - Integration with existing Art Studio menu

**Features:**
- ✅ DXF import for headstock logos
- ✅ Adaptive pocketing pipeline
- ✅ Simulation with risk analytics
- ✅ Real-time backplot visualization
- ✅ Issue tracking and highlighting
- ✅ Notes editor with save/cancel
- ✅ Risk report generation
- ✅ Backplot snapshot attachment

**API Integration:**
```typescript
// Risk analytics endpoints
postRiskReport(payload)           // Log risk snapshot
patchRiskNotes(reportId, notes)   // Update notes
attachRiskBackplot(reportId, bp)  // Attach backplot data

// Pipeline endpoints
POST /api/cam/pipeline/run        // Execute toolpath
POST /api/cam/sim/metrics         // Simulation metrics
```

**State Management:**
```typescript
const headstockDxfPath = ref("workspace/art/headstock/demo_headstock_logo.dxf")
const results = ref<Record<string, any> | null>(null)
const selectedPathOpId = ref<string | null>("headstock_adaptive")
const selectedOverlayOpId = ref<string | null>("headstock_sim")
const lastRiskAnalytics = ref<RiskAnalytics | null>(null)
const noteEditorVisible = ref(false)
```

---

### **Bundle 2: ArtStudioHeadstock_vue 2.txt** (8,015 lines)
**Phase:** 26.2+ - Date-Range Comparison + Advanced Analytics

**Major Components:**

1. **CamRiskCompareBars.vue** (~120 lines)
   - Window-to-window risk comparison
   - Current vs previous window visualization
   - Avg risk comparison bars
   - Critical incidents delta tracking
   - Color-coded indicators (green = improvement, red = regression)

2. **RiskTimelineRelief.vue** (Enhanced)
   - Date range selector with comparison toggle
   - Automatic previous window derivation
   - Statistical analysis (avg risk, critical count, job count)
   - Visual comparison with normalized bars

**Features:**
- ✅ "Compare with previous window" toggle
- ✅ Auto-derives previous window (same length, immediately before)
- ✅ Current vs previous: Avg risk, Critical incidents
- ✅ Normalized bar charts (max value = 100%)
- ✅ Delta indicators (▲/▼) with color coding
- ✅ Signed percentage changes

**Comparison Algorithm:**
```typescript
// Calculate delta
const deltaRisk = curr.avgRisk - prev.avgRisk
const deltaCritical = curr.totalCritical - prev.totalCritical

// Normalize bars to max value
const maxRisk = Math.max(curr.avgRisk, prev.avgRisk)
const currBarW = `${(curr.avgRisk / maxRisk) * 100}%`
const prevBarW = `${(prev.avgRisk / maxRisk) * 100}%`

// Color coding
function deltaClass(d: number) {
  if (d > 0) return "text-red-600"       // Worse
  if (d < 0) return "text-emerald-600"   // Better
  return "text-gray-500"                  // Same
}
```

**Visual Design:**
```vue
<!-- Dual bar chart with overlay -->
<div class="w-full h-4 bg-gray-100 rounded relative overflow-hidden">
  <div class="h-4 bg-blue-500/70" :style="{ width: currBarW }" />    <!-- Current -->
  <div class="h-4 bg-gray-400/60 absolute top-0" :style="{ width: prevBarW }" /> <!-- Previous -->
</div>
```

---

## 🔗 Integration Dependencies

### **Existing Systems Required:**
1. **Risk Analytics API** (already exists in N18 integration)
   - `/api/cam/risk/report` - POST endpoint
   - `/api/cam/risk/report/{id}/notes` - PATCH endpoint
   - `/api/cam/risk/report/{id}/backplot` - POST endpoint

2. **Pipeline System** (already exists)
   - `CamPipelineRunner.vue` component
   - `CamBackplotViewer.vue` component
   - `CamIssuesList.vue` component

3. **Backplot Types** (already defined)
   - `BackplotLoop`, `BackplotMove`, `BackplotOverlay`
   - `BackplotFocusPoint`, `SimIssue`

### **New Components to Create:**
1. `client/src/views/art/ArtStudioHeadstock.vue` (from Bundle 1)
2. `client/src/components/cam/CamRiskCompareBars.vue` (from Bundle 2)
3. Update `client/src/views/cam/RiskTimelineRelief.vue` (from Bundle 2)

### **Router Updates:**
```typescript
// Add to router/index.ts
{
  path: '/art/headstock',
  name: 'ArtStudioHeadstock',
  component: () => import('@/views/art/ArtStudioHeadstock.vue'),
  meta: {
    title: 'Headstock Logos',
    breadcrumb: ['Art Studio', 'Headstock']
  }
}
```

---

## 📊 Feature Comparison

| Feature | Rosette (Existing) | Headstock (Bundle 1) | Comparison (Bundle 2) |
|---------|-------------------|---------------------|----------------------|
| **DXF Import** | ✅ | ✅ | N/A |
| **Pipeline Execution** | ✅ | ✅ | N/A |
| **Risk Analytics** | ✅ | ✅ | ✅ Enhanced |
| **Backplot Visualization** | ✅ | ✅ | N/A |
| **Notes Editor** | ✅ | ✅ | N/A |
| **Issue Tracking** | ✅ | ✅ | N/A |
| **Window Comparison** | ❌ | ❌ | ✅ **NEW** |
| **Delta Indicators** | ❌ | ❌ | ✅ **NEW** |
| **Normalized Bar Charts** | ❌ | ❌ | ✅ **NEW** |

---

## 🎯 Integration Priority

### **High Priority (Phase 1):**
1. **ArtStudioHeadstock.vue** - Core headstock lane
   - Estimated time: 1 hour
   - Complexity: Low (mirrors existing Rosette)
   - Dependencies: None (reuses existing components)

### **Medium Priority (Phase 2):**
2. **CamRiskCompareBars.vue** - Comparison visualization
   - Estimated time: 30 minutes
   - Complexity: Low (self-contained component)
   - Dependencies: Risk analytics API

3. **RiskTimelineRelief.vue Update** - Window comparison toggle
   - Estimated time: 45 minutes
   - Complexity: Medium (state management for dual windows)
   - Dependencies: CamRiskCompareBars.vue

---

## 🧪 Testing Scenarios

### **Scenario 1: Headstock Basic Workflow**
1. Navigate to `/art/headstock`
2. Upload headstock logo DXF
3. Click "Run Pipeline"
4. **Expected:** Adaptive pocketing executes
5. **Expected:** Backplot displays toolpath
6. **Expected:** Risk analytics calculated
7. Click "Save Risk Snapshot"
8. **Expected:** Risk report created with backplot attachment

### **Scenario 2: Notes Editor**
1. After risk snapshot saved
2. Click "Edit Notes"
3. Type notes in editor
4. Click "Save"
5. **Expected:** Notes persisted to backend
6. Refresh page
7. **Expected:** Notes still visible

### **Scenario 3: Window Comparison**
1. Navigate to RiskTimelineRelief
2. Select date range (e.g., last 7 days)
3. Enable "Compare with previous window" toggle
4. **Expected:** Previous 7 days automatically calculated
5. **Expected:** Comparison bars show current vs previous
6. **Expected:** Delta indicators show ▲ (worse) or ▼ (better)

---

## 🔧 Technical Notes

### **TypeScript Types Used:**
```typescript
interface PipelineOp { /* ... */ }
interface PipelineRunIn { /* ... */ }
interface PipelineRunOut { /* ... */ }
interface BackplotLoop { /* ... */ }
interface BackplotMove { /* ... */ }
interface BackplotOverlay { /* ... */ }
interface BackplotFocusPoint { /* ... */ }
interface SimIssue { /* ... */ }
interface RiskAnalytics {
  avgRisk: number
  totalCritical: number
  jobsCount: number
}
interface RiskBackplotMoveOut { /* ... */ }
```

### **API Endpoints:**
```typescript
// Risk endpoints (existing)
POST   /api/cam/risk/report
PATCH  /api/cam/risk/report/{id}/notes
POST   /api/cam/risk/report/{id}/backplot

// Pipeline endpoints (existing)
POST   /api/cam/pipeline/run
POST   /api/cam/sim/metrics
```

---

## 📈 Statistics

**Bundle 1 (Headstock):**
- Total lines: 8,588
- Main component: ~600 lines
- Router integration: ~50 lines
- Type definitions: ~100 lines

**Bundle 2 (Comparison):**
- Total lines: 8,015
- CamRiskCompareBars.vue: ~120 lines
- RiskTimelineRelief.vue updates: ~200 lines
- Comparison logic: ~80 lines

**Combined:**
- Total lines: 16,603
- New components: 2
- Updated components: 1
- Router entries: 1

---

## 🚀 Next Steps

### **Immediate (30 minutes):**
1. Create `ArtStudioHeadstock.vue` from Bundle 1
2. Add router entry for `/art/headstock`
3. Test basic DXF import → pipeline workflow

### **Short-term (1 hour):**
4. Create `CamRiskCompareBars.vue` from Bundle 2
5. Update `RiskTimelineRelief.vue` with comparison toggle
6. Test window-to-window comparison

### **Optional (Future):**
7. Extend headstock lane with custom V-carve parameters
8. Add preset templates (brand logos, text engraving)
9. Multi-tool support (pocket + V-carve in same job)

---

## 🎨 Visual Design

**Headstock Lane Layout:**
```
┌─────────────────────────────────────────────┐
│ Art Studio > Headstock Logos                │
├─────────────────────────────────────────────┤
│ [Upload DXF] [Run Pipeline] [Risk Snapshot] │
│                                             │
│ ┌─────────────┐ ┌─────────────────────────┐ │
│ │  Backplot   │ │  Pipeline Results       │ │
│ │  Viewer     │ │  • Operations: 3        │ │
│ │             │ │  • Issues: 0            │ │
│ │             │ │  • Risk: 12.3           │ │
│ └─────────────┘ └─────────────────────────┘ │
│                                             │
│ [Edit Notes] [Attach Backplot]              │
└─────────────────────────────────────────────┘
```

**Comparison Bars Layout:**
```
┌─────────────────────────────────────────────┐
│ Window Comparison (current vs previous)    │
├─────────────────────────────────────────────┤
│ Avg risk:          12.3 vs 14.1  ▼ -1.8    │
│ ████████████░░░░░░ (current = blue)         │
│ ██████████████████ (previous = gray)        │
│                                             │
│ Critical incidents: 2 vs 5  ▼ -3           │
│ ████░░░░░░░░░░░░░░ (current = red)          │
│ ████████████░░░░░░ (previous = gray)        │
└─────────────────────────────────────────────┘
```

---

## ✅ Ready to Integrate

Both bundles are **production-ready drop-in code** with:
- ✅ Complete TypeScript types
- ✅ Error handling
- ✅ Loading states
- ✅ Tailwind CSS styling
- ✅ Vue 3 Composition API
- ✅ API integration points

No modifications needed - just copy-paste and wire router entries.

---

**Repository:** github.com/HanzoRazer/luthiers-toolbox  
**Branch:** main  
**Integration Order:** Headstock lane first, then comparison features  
**Estimated Total Time:** 2.5 hours
