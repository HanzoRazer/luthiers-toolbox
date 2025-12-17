# B21 Multi-Run Comparison - Integration Test Guide

**Status:** Ready for Testing  
**Route:** `/lab/compare-runs`  
**Date:** November 28, 2025

---

## ✅ Pre-Test Checklist

- [x] Backend API running (`uvicorn app.main:app --reload --port 8000`)
- [x] Frontend dev server running (`npm run dev` in `client/`)
- [x] Chart.js installed (`chart.js@^4.4.0` in package.json)
- [x] Route registered (geometry store CAM targets)
- [x] Component created (`packages/client/src/views/MultiRunComparisonView.vue`)

---

## 🧪 Manual Integration Tests

### **Test 1: Route Navigation**

**Steps:**
1. Open browser to `http://localhost:5173`
2. Navigate to `/lab/compare-runs` in address bar
3. Press Enter

**Expected Results:**
- ✅ MultiRunComparisonView component loads without 404
- ✅ Page title shows "Multi-Run Comparison"
- ✅ Preset selector section visible
- ✅ No console errors in DevTools

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 2: Preset Selector Loading**

**Prerequisites:** 
- Create 2-3 presets with job lineage using B19 "Clone as Preset" feature
- OR run `.\test_multi_run_comparison.ps1` to create test presets

**Steps:**
1. On `/lab/compare-runs`, observe preset selector section
2. Check that only presets with `job_source_id` appear
3. Verify empty state message if no lineage presets exist

**Expected Results:**
- ✅ Preset selector displays grid of checkboxes
- ✅ Only presets with job lineage shown (not all presets)
- ✅ Each preset shows: name, kind badge, truncated job ID
- ✅ Empty state: "Clone jobs as presets using B19 feature" if none

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 3: Multi-Select Functionality**

**Steps:**
1. Select 1 preset by clicking checkbox
2. Verify "Compare Runs" button disabled
3. Select 2nd preset
4. Verify "Compare Runs" button enabled
5. Verify selection counter shows "2 selected"
6. Click "Clear selection"
7. Verify all checkboxes unchecked

**Expected Results:**
- ✅ Single selection → Button disabled with tooltip/message
- ✅ 2+ selections → Button enabled (green)
- ✅ Counter updates dynamically: "X presets selected"
- ✅ Clear button resets all checkboxes
- ✅ Selected presets have blue background

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 4: Run Comparison**

**Steps:**
1. Select 3 presets with different sim_time_s values
2. Click "Compare Runs" button
3. Wait for API call to complete
4. Observe results display

**Expected Results:**
- ✅ Loading spinner appears during API call
- ✅ No error messages
- ✅ Summary stats cards display (4 cards):
   - Runs Compared: 3
   - Avg Time: [value]s
   - Avg Energy: [value]J
   - Avg Moves: [value]
- ✅ Trend badges show (if applicable):
   - Time trend: Green (improving) / Red (degrading) / Gray (stable)
   - Energy trend: similar color coding
- ✅ Recommendations panel displays with bullet points
- ✅ Comparison table shows all 3 runs (8 columns)
- ✅ Best run highlighted green with 🏆 trophy
- ✅ Worst run highlighted red with ⚠️ warning

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 5: Chart.js Bar Chart**

**Steps:**
1. After comparison completes, scroll to chart section
2. Verify bar chart renders
3. Hover over bars to see tooltips
4. Check bar colors

**Expected Results:**
- ✅ Bar chart displays with Y-axis "Time (seconds)"
- ✅ 3 bars (one per preset)
- ✅ Bar colors:
   - Best run: Green
   - Worst run: Red
   - Others: Blue
- ✅ Tooltip shows time value on hover (e.g., "95.80s")
- ✅ Chart responsive (scales with window resize)

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 6: Efficiency Score Progress Bars**

**Steps:**
1. In comparison table, check "Efficiency" column
2. Verify progress bars display
3. Check color coding

**Expected Results:**
- ✅ Each row has progress bar (0-100)
- ✅ Color by score:
   - Green: ≥70
   - Yellow: 40-69
   - Red: <40
- ✅ Score text displays next to bar (e.g., "85/100")

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 7: CSV Export**

**Steps:**
1. After comparison, click "📥 Export as CSV" button
2. Wait for file download
3. Open CSV file in Excel/text editor

**Expected Results:**
- ✅ CSV file downloads with timestamp name
- ✅ Headers: Preset Name, Time (s), Energy (J), Moves, Issues, Strategy, Feed XY, Efficiency Score
- ✅ 3 data rows (one per preset)
- ✅ Values match table display
- ✅ Numeric formatting correct (2 decimals for time, 0 for energy)

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 8: State Persistence (localStorage)**

**Steps:**
1. Select 2 presets
2. Run comparison
3. Open DevTools → Application → Local Storage
4. Verify keys exist:
   - `multirun.selectedPresets`
   - `multirun.lastComparison`
   - `multirun.lastUpdated`
5. Refresh page (F5)
6. Verify state restored

**Expected Results:**
- ✅ localStorage keys populated after comparison
- ✅ `selectedPresets` is JSON array of IDs
- ✅ `lastComparison` contains full result object
- ✅ `lastUpdated` is Unix timestamp (ms)
- ✅ After reload: checkboxes re-checked
- ✅ After reload: comparison table/chart restored
- ✅ After reload: no API call made (cached)

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 9: New Comparison Reset**

**Steps:**
1. After comparison, click "🔄 New Comparison" button
2. Observe state reset
3. Check localStorage in DevTools

**Expected Results:**
- ✅ Comparison results cleared (table/chart hidden)
- ✅ All checkboxes unchecked
- ✅ "Compare Runs" button disabled
- ✅ localStorage keys removed (all 3)
- ✅ No error messages

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 10: Error Handling**

**Steps:**
1. Select only 1 preset
2. Click "Compare Runs" button
3. Observe error handling

**Expected Results:**
- ✅ Button disabled (can't click)
- ✅ OR: Error message displays: "Please select at least 2 presets"
- ✅ No crash or console errors

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 11: Backend API Integration**

**Steps:**
1. Open Network tab in DevTools
2. Run comparison
3. Inspect API call

**Expected Results:**
- ✅ POST request to `/api/presets/compare-runs`
- ✅ Request body contains:
   - `preset_ids`: array of 2+ IDs
   - `include_trends`: true
   - `include_recommendations`: true
- ✅ Response status: 200 OK
- ✅ Response contains:
   - `runs[]` array
   - `avg_time_s`, `min_time_s`, `max_time_s`
   - `time_trend`, `energy_trend`
   - `best_run_id`, `worst_run_id`
   - `recommendations[]` array

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

### **Test 12: Navigation Integration**

**Steps:**
1. Navigate to a different page (e.g., Preset Hub)
2. Use geometry store to navigate: `sendToCAM('compare-runs')`
3. Or: Look for navigation link in sidebar/toolbar
4. Click link

**Expected Results:**
- ✅ Navigation link visible with 📊 icon
- ✅ Link labeled "Multi-Run Comparison"
- ✅ Clicking link routes to `/lab/compare-runs`
- ✅ Component loads correctly

**Actual Results:**
```
[ ] Pass
[ ] Fail - Error: ___________________________
```

---

## 🐛 Known Issues / Limitations

- [ ] No cross-tab localStorage sync (requires storage event listener)
- [ ] Comparison cache TTL fixed at 24h (not configurable)
- [ ] No energy trend chart (only time chart implemented)
- [ ] No parameter sensitivity analysis
- [ ] No PDF export (CSV only)
- [ ] Best/worst highlighting requires at least 2 runs

---

## 📊 Test Results Summary

**Date Tested:** _________________  
**Tester:** _____________________  
**Environment:** _________________

| Test | Status | Notes |
|------|--------|-------|
| 1. Route Navigation | ⬜ Pass / ⬜ Fail | |
| 2. Preset Selector | ⬜ Pass / ⬜ Fail | |
| 3. Multi-Select | ⬜ Pass / ⬜ Fail | |
| 4. Run Comparison | ⬜ Pass / ⬜ Fail | |
| 5. Chart.js Chart | ⬜ Pass / ⬜ Fail | |
| 6. Efficiency Bars | ⬜ Pass / ⬜ Fail | |
| 7. CSV Export | ⬜ Pass / ⬜ Fail | |
| 8. State Persistence | ⬜ Pass / ⬜ Fail | |
| 9. New Comparison | ⬜ Pass / ⬜ Fail | |
| 10. Error Handling | ⬜ Pass / ⬜ Fail | |
| 11. API Integration | ⬜ Pass / ⬜ Fail | |
| 12. Navigation | ⬜ Pass / ⬜ Fail | |

**Overall Status:** ⬜ All Pass / ⬜ Some Failures  
**Ready for Production:** ⬜ Yes / ⬜ No (see issues)

---

## 🚀 Next Steps After Testing

If all tests pass:
1. ✅ Mark B21 as 100% complete in status tracker
2. ✅ Update UNIFIED_PRESET_INTEGRATION_STATUS.md
3. ✅ Create production deployment plan
4. ✅ Consider Option F (Extension Validation) or other enhancements

If tests fail:
1. Document issues in "Known Issues" section above
2. Create GitHub issues for each failure
3. Prioritize fixes by severity
4. Re-test after fixes

---

## 📚 Documentation References

- [B21_MULTI_RUN_COMPARISON_COMPLETE.md](./B21_MULTI_RUN_COMPARISON_COMPLETE.md) – Full feature documentation
- [B21_MULTI_RUN_COMPARISON_QUICKREF.md](./B21_MULTI_RUN_COMPARISON_QUICKREF.md) – Quick reference
- [B21_ROUTE_REGISTRATION_GUIDE.md](./B21_ROUTE_REGISTRATION_GUIDE.md) – Route setup guide
- [STATE_PERSISTENCE_QUICKREF.md](./STATE_PERSISTENCE_QUICKREF.md) – localStorage implementation
- [test_multi_run_comparison.ps1](./test_multi_run_comparison.ps1) – Backend API tests

---

**Test Guide Version:** 1.0  
**Last Updated:** November 28, 2025
