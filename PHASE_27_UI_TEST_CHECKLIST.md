# Phase 27 UI Testing Checklist

**Test URL:** http://localhost:5173/art-studio/rosette/compare  
**Backend:** http://localhost:8000 ✅ Running  
**Frontend:** http://localhost:5173 ✅ Running  
**Test Data:** 4 snapshots created (26.7%, 25.5%, 55%, 80% risk)

---

## 🧪 Manual UI Test Steps

### **Phase 27.2: Risk Snapshot Saving**

**Test 1: Save Snapshot Button**
- [ ] Select Job A: "test_rosette_B" (Aggressive preset)
- [ ] Select Job B: "test_rosette_A" (Safe preset)
- [ ] Click "Compare A ↔ B" button
- [ ] Verify comparison results display (diff summary panel)
- [ ] Verify "💾 Save to Risk Timeline" button appears
- [ ] Click "Save to Risk Timeline"
- [ ] Verify success message shows with calculated risk score
- [ ] Check message format: "✓ Saved to Risk Timeline (risk: XX.X%)"

**Expected:** Button appears after comparison, shows loading state, displays success message

---

### **Phase 27.3: History Sidebar & Sparklines**

**Test 2: Show/Hide History Sidebar**
- [ ] After comparison, verify "Show History" button appears
- [ ] Click "Show History"
- [ ] Verify sidebar appears (320px width, gray background)
- [ ] Verify "Export CSV" button at top of sidebar
- [ ] Click "Hide History"
- [ ] Verify sidebar disappears

**Test 3: Snapshot Cards Display**
- [ ] Open history sidebar
- [ ] Verify 4 snapshot cards are displayed
- [ ] Each card should show:
  - [ ] Timestamp in format "Nov 19, HH:MM AM/PM"
  - [ ] Risk score badge (color-coded: green/yellow/red)
  - [ ] Inline SVG sparkline (3-point polyline)
  - [ ] Seg Δ value
  - [ ] Inner Δ value (2 decimal places)
  - [ ] Outer Δ value (2 decimal places)
  - [ ] Lane label (if present)
- [ ] Verify sparkline colors match risk level:
  - Green for low risk (<40%)
  - Yellow for medium risk (40-70%)
  - Red for high risk (>70%)

**Test 4: CSV Export**
- [ ] Click "Export CSV" button in sidebar
- [ ] Verify new tab opens with CSV download
- [ ] Open downloaded file
- [ ] Verify 11 columns present
- [ ] Verify 5 rows (header + 4 data rows)
- [ ] Check data matches snapshot cards

**Expected:** 
- Sidebar slides in from right
- 4 cards visible with correct data
- CSV downloads with proper format

---

### **Phase 27.4: Preset Grouping Toggle**

**Test 5: Group by Preset Checkbox**
- [ ] In history sidebar, locate "Group by Preset" checkbox
- [ ] Verify checkbox is initially unchecked
- [ ] Verify flat list of 4 snapshots displayed

**Test 6: Enable Preset Grouping**
- [ ] Check "Group by Preset" checkbox
- [ ] Verify display changes to grouped view
- [ ] Verify group appears: "Aggressive vs Safe"
- [ ] Verify group header shows:
  - [ ] Preset pair name
  - [ ] Snapshot count: "4 comparisons"
  - [ ] Average risk: "Avg risk: 46.8%"
  - [ ] Expand/collapse arrow (▶)

**Test 7: Expand/Collapse Groups**
- [ ] Click group header
- [ ] Verify arrow changes to ▼
- [ ] Verify 4 snapshot cards appear inside group
- [ ] Click header again
- [ ] Verify arrow changes back to ▶
- [ ] Verify cards collapse/hide

**Test 8: Uncheck Preset Grouping**
- [ ] Uncheck "Group by Preset" checkbox
- [ ] Verify display reverts to flat list
- [ ] Verify all 4 cards visible again

**Expected:**
- Smooth transition between flat and grouped views
- Group state persists during session
- Cards maintain same content in both views

---

### **Phase 27.5: Risk Metrics Bar**

**Test 9: Risk Overview Panel**
- [ ] In history sidebar, locate "Risk Overview" panel
- [ ] Verify panel appears above "Group by Preset" toggle
- [ ] Verify white background with rounded border

**Test 10: Metrics Display**
- [ ] Verify "Risk Overview" title
- [ ] Verify 2x2 grid layout with metrics:
  - [ ] **Total:** 4
  - [ ] **Avg Risk:** ~46.8% (color-coded based on value)
  - [ ] **Low (<40%):** 2 (green text)
  - [ ] **Med (40-70%):** 1 (yellow text)
  - [ ] **High (>70%):** 1 (red text)

**Test 11: Risk Distribution Bar**
- [ ] Below metrics, verify horizontal bar chart
- [ ] Verify bar height: 8px (h-2)
- [ ] Verify 3 segments:
  - [ ] Green segment (50% width = 2/4 snapshots)
  - [ ] Yellow segment (25% width = 1/4 snapshots)
  - [ ] Red segment (25% width = 1/4 snapshots)
- [ ] Verify rounded corners on bar

**Expected:**
- Clear visual hierarchy
- Color coding matches risk thresholds
- Distribution bar proportions accurate

---

### **Phase 27.6: Preset Scorecards**

**Test 12: Preset Analytics Header**
- [ ] Below Risk Overview, locate "Preset Analytics" section
- [ ] Verify section title displays
- [ ] Verify section only shows when grouped data has >1 preset pair

**Test 13: Scorecard Display**
- [ ] Verify horizontal scrolling container
- [ ] Verify one scorecard for "Aggressive vs Safe"
- [ ] Verify card width: 144px (w-36)
- [ ] Verify white background with border

**Test 14: Scorecard Content**
- [ ] Verify card title: "Aggressive vs Safe" (truncated if needed)
- [ ] Verify metrics in 2-column grid:
  - [ ] **Total:** 4
  - [ ] **Avg:** ~46.8% (color-coded)
- [ ] Verify risk breakdown (small text):
  - [ ] **Low:** 2 (green)
  - [ ] **Med:** 1 (yellow)
  - [ ] **High:** 1 (red)

**Test 15: Mini Sparkline**
- [ ] Below metrics, verify border separator
- [ ] Verify SVG sparkline (viewBox: 0 0 120 20)
- [ ] Verify sparkline shows time-based trend
- [ ] Verify line color matches avg risk (yellow for 46.8%)
- [ ] Verify line connects all 4 data points chronologically

**Test 16: Multiple Presets (Future)**
- [ ] Create comparison with different preset pair
- [ ] Verify second scorecard appears
- [ ] Verify horizontal scrolling works
- [ ] Verify each card is independent

**Expected:**
- Cards scroll horizontally on overflow
- Sparkline shows temporal trend
- Each preset pair gets own card

---

## 🎨 Visual Regression Checks

### **Layout**
- [ ] Main content area remains flex-1 (flexible width)
- [ ] Sidebar fixed at 320px when visible
- [ ] No horizontal scrollbar on main page
- [ ] Sidebar scrolls vertically if content overflows

### **Spacing & Typography**
- [ ] Consistent 10-11px base font sizes
- [ ] 9px for smaller labels
- [ ] 8px for micro text (scorecard breakdowns)
- [ ] Consistent gap-2 (8px) between elements

### **Colors**
- [ ] Risk badges use correct Tailwind colors:
  - Green: bg-green-100 text-green-800
  - Yellow: bg-yellow-100 text-yellow-800
  - Red: bg-red-100 text-red-800
- [ ] Sparklines match color scheme
- [ ] Distribution bar uses bg-green-500/yellow-500/red-500

### **Interactions**
- [ ] Buttons show hover states
- [ ] Cards have hover shadow on history items
- [ ] Checkbox is properly styled
- [ ] Loading states show during async operations

---

## 🐛 Error Scenarios

### **No Data**
- [ ] Before any snapshots: Verify empty state message
- [ ] Message: "No comparison history for these jobs yet..."

### **Loading State**
- [ ] During API call: Verify "Loading history..." message
- [ ] Disable Export CSV button during load

### **Network Errors**
- [ ] Stop backend temporarily
- [ ] Try to load history
- [ ] Verify graceful error handling (console logs)
- [ ] Snapshots array should remain empty

---

## ✅ Success Criteria

**Phase 27.2:** ✅ Backend tested, UI pending
- [x] Snapshot saving works via API
- [ ] Button appears and functions in UI
- [ ] Success message displays

**Phase 27.3:** ✅ Backend tested, UI pending
- [x] CSV export endpoint works
- [x] Proper column format
- [ ] Sidebar displays correctly
- [ ] Sparklines render
- [ ] Export button downloads CSV

**Phase 27.4:** ⏳ Frontend only
- [ ] Checkbox toggles between views
- [ ] Groups display with correct headers
- [ ] Expand/collapse works
- [ ] Avg risk calculates correctly

**Phase 27.5:** ⏳ Frontend only
- [ ] Metrics panel displays
- [ ] All counts accurate
- [ ] Distribution bar renders
- [ ] Colors match risk levels

**Phase 27.6:** ⏳ Frontend only
- [ ] Scorecard appears
- [ ] Metrics display correctly
- [ ] Sparkline shows time trend
- [ ] Horizontal scroll works

---

## 📊 Test Results

**Date:** November 19, 2025  
**Tester:** _____________  
**Browser:** _____________  
**Screen Resolution:** _____________

**Overall Status:** ⏳ PENDING

**Notes:**
- Backend: ✅ All 14 tests passing
- Frontend: ⏳ Manual UI testing in progress
- Test data: 4 snapshots with varied risk levels (26.7%, 25.5%, 55%, 80%)

---

## 🚀 Quick Test Command

```powershell
# Backend must be running on port 8000
# Frontend must be running on port 5173

# Open browser and navigate to:
http://localhost:5173/art-studio/rosette/compare

# Select jobs and test all features above
```
