# Art Studio Quick Integration - Quick Reference

**Status:** ✅ Phase 23.0 + 26.2 Complete  
**Last Updated:** December 2024

---

## 📋 At a Glance

| Component | Lines | Status | Route |
|-----------|-------|--------|-------|
| **ArtStudioHeadstock.vue** | 512 | ✅ Integrated | /art/headstock |
| **CamRiskCompareBars.vue** | 132 | ✅ Created | Component only |
| **RiskTimelineRelief.vue** | TBD | ⏳ Pending | Update needed |

**Total Integrated:** 644 lines  
**Bundle Sources:** ArtStudioHeadstock_vue.txt (8,588 lines), ArtStudioHeadstock_vue 2.txt (8,015 lines)

---

## 🚀 Quick Start

### **Navigate to Headstock Lane:**
```
http://localhost:5173/art/headstock
```

### **Pipeline Defaults:**
- Tool: 1.5mm end mill
- Stepover: 30% (0.3 × tool_d)
- Stepdown: 0.4mm per pass
- Feed: 600 mm/min
- Safe Z: 3mm
- Cutting Depth: -0.8mm

### **Risk Comparison Usage:**
```vue
<CamRiskCompareBars
  :curr="{ jobsCount: 5, avgRisk: 12.5, totalCritical: 3 }"
  :prev="{ jobsCount: 5, avgRisk: 10.0, totalCritical: 2 }"
/>
```

---

## 🔑 Key Features

### **Headstock Lane (Phase 23.0)**
✅ DXF logo import  
✅ 4-stage pipeline (adaptive → helix → post → sim)  
✅ Risk analytics with snapshot logging  
✅ Backplot visualization  
✅ Notes editor with autosave  
✅ Issue tracking with focus points

### **Risk Comparison (Phase 26.2)**
✅ Window-to-window delta analysis  
✅ Normalized bar charts  
✅ Color-coded improvements/regressions  
✅ Avg risk + critical incidents metrics  
⏳ RiskTimelineRelief integration pending

---

## 📂 File Locations

```
client/src/
├── views/art/ArtStudioHeadstock.vue ✅
├── components/cam/CamRiskCompareBars.vue ✅
└── router/index.ts (route registered) ✅
```

---

## 🧪 Testing Commands

### **1. Test Headstock Route:**
```typescript
// Navigate to:
http://localhost:5173/art/headstock

// Expected:
- "Art Studio – Headstock Logo" header
- DXF path: workspace/art/headstock/demo_headstock_logo.dxf
- Pipeline runner with 4 operations
- "Run Pipeline" button
```

### **2. Test Pipeline Execution:**
```typescript
// Click "Run Pipeline"
// Expected sequence:
1. Adaptive pocketing (LOGO layer)
2. Helical entry (ramp_angle_deg: 3.0)
3. Post-processing (GRBL preset)
4. Simulation (stock_thickness: 3.0)

// After success:
- Risk score displayed (e.g., "12.5")
- Extra time shown (e.g., "2 min 30 s")
- Issue count (e.g., "8")
- Snapshot ID (8-char prefix)
```

### **3. Test Notes Editor:**
```typescript
// Click "Attach / edit note"
// Type: "Test note"
// Click "Save note"
// Expected: No error, editor closes
```

### **4. Test Risk Comparison:**
```vue
<!-- Add to test view -->
<script setup>
import CamRiskCompareBars from '@/components/cam/CamRiskCompareBars.vue'

const curr = { jobsCount: 5, avgRisk: 12.5, totalCritical: 3 }
const prev = { jobsCount: 5, avgRisk: 10.0, totalCritical: 2 }
</script>

<template>
  <CamRiskCompareBars :curr="curr" :prev="prev" />
</template>

<!-- Expected output:
  Avg risk: 12.50 vs 10.00 ▲+2.50 (red)
  Critical incidents: 3 vs 2 ▲+1 (red)
  Blue/gray bars normalized to max values
-->
```

---

## 🔧 Next Integration Step

**System 8: RiskTimelineRelief Comparison Toggle**

**Source:** Bundle 2 lines 160-360

**Changes:**
1. Import CamRiskCompareBars
2. Add toggle: "Compare with previous window"
3. Compute previous window logic
4. Render comparison component

**Estimated Time:** 20 minutes

---

## 📊 Bundle Inventory

### **Bundle 1 (ArtStudioHeadstock_vue.txt)**
- ✅ Phase 23.0: Headstock Lane (lines 30-650)
- ⏳ Phase 24.0: Relief Lane (lines 700-1300)
- ⏳ Router examples (lines 1300+)

### **Bundle 2 (ArtStudioHeadstock_vue 2.txt)**
- ✅ Phase 26.2: CamRiskCompareBars (lines 20-160)
- ⏳ Phase 26.2: RiskTimelineRelief patch (lines 160-360)
- ⏳ Router: /cam/risk/compare (lines 760-780)

---

## 🐛 Common Issues

### **Issue:** Route not found
**Solution:** Verify router registration:
```typescript
// client/src/router/index.ts
import ArtStudioHeadstock from '@/views/art/ArtStudioHeadstock.vue'

{
  path: '/art/headstock',
  name: 'ArtStudioHeadstock',
  component: ArtStudioHeadstock
}
```

### **Issue:** Component import error
**Solution:** Check file exists:
```bash
ls client/src/views/art/ArtStudioHeadstock.vue
ls client/src/components/cam/CamRiskCompareBars.vue
```

### **Issue:** API errors
**Solution:** Verify endpoints exist:
- `postRiskReport()` - POST /cam/risk/report
- `patchRiskNotes()` - PATCH /cam/risk/report/:id/notes
- `attachRiskBackplot()` - PATCH /cam/risk/report/:id/backplot

---

## 📚 Documentation Links

- [Full Integration Summary](./ART_STUDIO_QUICK_INTEGRATION_COMPLETE.md)
- [Bundle Analysis](./ART_STUDIO_DUMP_BUNDLES_ANALYSIS.md)
- [Art Studio v16.1](./ART_STUDIO_V16_1_HELICAL_INTEGRATION.md)
- [Adaptive Pocketing](./ADAPTIVE_POCKETING_MODULE_L.md)

---

## ✅ Completion Checklist

**Phase 23.0 (Headstock Lane):**
- [x] ArtStudioHeadstock.vue created (512 lines)
- [x] /art/headstock route registered
- [x] Dependencies verified (CamBackplotViewer, CamPipelineRunner, CamIssuesList)
- [x] API endpoints verified (postRiskReport, patchRiskNotes, attachRiskBackplot)

**Phase 26.2 (Risk Comparison):**
- [x] CamRiskCompareBars.vue created (132 lines)
- [ ] RiskTimelineRelief.vue updated with comparison toggle
- [ ] /cam/risk/compare route added
- [ ] Compare CSV export implemented

**Testing:**
- [ ] Navigate to /art/headstock
- [ ] Run pipeline successfully
- [ ] Test notes editor
- [ ] Test backplot visualization
- [ ] Test CamRiskCompareBars with mock data

---

**Quick Reference Version:** 1.0  
**Integration Status:** 66% Complete (2 of 3 components)  
**Next Priority:** RiskTimelineRelief comparison toggle
